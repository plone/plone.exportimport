from .base import BaseImporter
from pathlib import Path
from plone.dexterity.content import DexterityContent
from plone.exportimport import logger
from plone.exportimport import settings
from plone.exportimport import types
from plone.exportimport.interfaces import IExportImportRequestMarker
from plone.exportimport.utils import content as content_utils
from plone.exportimport.utils import request_provides
from typing import Callable
from typing import Generator
from typing import List
from typing import Optional

import json


class ContentImporter(BaseImporter):
    name: str = "content"
    metadata: Optional[types.ExportImportMetadata] = None
    languages: Optional[types.PortalLanguages] = None
    dropped: set[str] = set()

    def _cleanse_ordering(self, raw_data: dict[str, int]) -> dict[str, int]:
        """Prepare ordering data before deserialization.

        Given a dict in the format::
            {
                "35661c9bb5be42c68f665aa1ed291418": 0,
                "45b0b46f17104a7b8fa7bb94d3dd5bd9": 1
            }

        return a dict sorted by position in parent.
        """
        # We need to sort the ordering data by position in parent
        data = dict(sorted(raw_data.items(), key=lambda x: x[1]))
        return data

    def all_objects(self) -> Generator:
        """Return all objects to be serialized."""
        all_files = self.metadata._data_files_ if self.metadata else []
        logger.info(f"Importing {len(all_files)} content items")
        for filepath in all_files:
            path = self.base_path / filepath
            data = self._read(path)
            logger.debug(f"Read data from {path}")
            yield data

    def deserialize(
        self, data: dict, obj: DexterityContent, config: types.ImporterConfig
    ) -> DexterityContent:
        """Return all objects to be serialized."""
        deserializer = self._deserializer(obj)
        kwargs = {"validate_all": False}
        if obj.portal_type == "Plone Site":
            self.request["BODY"] = json.dumps(data)
        else:
            kwargs["data"] = data
        try:
            obj = deserializer(**kwargs)
        except Exception as exc:
            logger.error(
                f"{config.logger_prefix} Error deserializing {obj}", exc_info=exc
            )
        return obj

    def construct(self, item: dict) -> Optional[DexterityContent]:
        """Serialize object."""
        item_path = item["@id"]
        config = types.ImporterConfig(
            site=self.site,
            site_root_uid=self.site.UID(),
            languages=self.languages,
            request=self.request,
            logger_prefix=f"- {item_path}:",
        )

        # Pre-process payload
        for processor in content_utils.processors():
            logger.debug(f"{config.logger_prefix} Running {processor.name} on payload")
            item = processor.func(item, config)

        # Apply data hooks
        for func in self.data_hooks:
            logger.debug(
                f"{config.logger_prefix} Running data hook {func.__name__} on payload"
            )
            item = func(item, config)

        # Get or Create object instance
        new = content_utils.get_obj_instance(item, config)
        if not new:
            logger.warning(f"Skipping {item_path} creation")
            return None

        # Apply pre_deserialize hooks
        pre_deserialize_hooks = self.pre_deserialize_hooks or []
        for func in pre_deserialize_hooks:
            logger.debug(
                f"{config.logger_prefix} Running pre_deserialize hook {func.__name__} on payload"
            )
            item, new = func(item, new)

        # Deserialize
        new = self.deserialize(data=item, obj=new, config=config)

        # Handle constraints
        constraints = item.pop(settings.SERIALIZER_CONSTRAINS_KEY, {})
        if constraints:
            item_uid = item["UID"]
            self.metadata.constraints[item_uid] = constraints

        # Updaters
        for updater in content_utils.updaters():
            logger.debug(f"{config.logger_prefix} Running {updater.name} for {new}")
            new = updater.func(item, new)

        # Apply obj hooks
        for func in self.obj_hooks:
            logger.debug(
                f"{config.logger_prefix} Running object hook {func.__name__} on payload"
            )
            new = func(item, new)

        return new

    def do_import(self) -> str:
        objs: dict[str, str] = {}
        modified: set[str] = set()
        name = self.__class__.__name__
        request = self.request
        if not request:
            logger.warning(f"{name}: No request found, skipping final import step")
            return f"{name}: No request found, skipping import step"

        with request_provides(request, IExportImportRequestMarker):
            for index, item in enumerate(self.all_objects(), start=1):
                item_path = item["@id"]
                item_type = item["@type"]
                item_uid = item.get("UID", "")
                logger.info(f"{index:07d} - {item_path} - ({item_type}) - ({item_uid})")
                obj = self.construct(item)
                if obj:
                    obj_path = "/".join(obj.getPhysicalPath())
                    objs[item_uid] = obj_path
                else:
                    self.dropped.add(item_path)
                if self.intermediate_commits and not index % self.commit_after:
                    self._commit(f"Created {self.commit_after} objects")
                    logger.info(f"{name}: Handled {index} items... (Commit)")
                elif not index % self.savepoint_after:
                    self._savepoint()
                    logger.info(f"{name}: Handled {index} items...")
            for setter in content_utils.metadata_setters():
                data = getattr(self.metadata, setter.name)
                cleanse_func = getattr(self, f"_cleanse_{setter.name}", None)
                if cleanse_func:
                    # Cleanse data before processing
                    data = cleanse_func(data)
                logger.info(f"Processing {setter.name}: {len(data)} entries")
                for index, uid in enumerate(data, start=index):
                    # Pass the path as a fallback in case the object was not found by UID
                    path = objs.get(uid) or ""
                    value = data[uid]
                    if setter.func(uid, value, path):
                        modified.add(uid)
                    if not index % self.savepoint_after:
                        self._savepoint()
                    if not index % settings.IMPORTER_REPORT:
                        logger.info(f"{setter.name}: Handled {index} items...")
            # Reindex objects
            idxs = [
                "allowedRolesAndUsers",
                "getObjPositionInParent",
                "is_default_page",
                "modified",
                "created",
            ]
            content_utils.recatalog_uids(list(modified), idxs=idxs)
        total_objects = len(objs)
        msg = f"Imported {total_objects} objects"
        if self.intermediate_commits:
            # Commit changes after importing all the content
            self._commit(msg)
            logger.info(f"{name}: Committed changes")
        return f"{name}: {msg}"

    def import_data(
        self,
        base_path: Path,
        data_hooks: Optional[List[Callable]] = None,
        pre_deserialize_hooks: Optional[List[Callable]] = None,
        obj_hooks: Optional[List[Callable]] = None,
    ) -> str:
        """Import content into a site."""
        base_path = base_path / self.name
        self.request[settings.IMPORT_PATH_KEY] = base_path
        metadata_path = base_path / "__metadata__.json"
        metadata = self._read(metadata_path)
        if metadata is None:
            return f"{self.__class__.__name__}: No data to import"
        self.metadata = types.ExportImportMetadata(**self._read(metadata_path))
        self.languages = content_utils.get_portal_languages()
        self.start()
        result = super().import_data(
            base_path, data_hooks, pre_deserialize_hooks, obj_hooks
        )
        self.finish()
        # Report items that were dropped during the import
        dropped = sorted(self.dropped)
        if dropped:
            logger.warning("List of items dropped during import")
            for item_path in dropped:
                logger.warning(f" - {item_path}")
        return result

    def start(self):
        """Hook to do something before import starts."""

    def finish(self):
        """Hook to do something after import finishes."""
