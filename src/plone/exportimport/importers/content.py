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
import transaction


class ContentImporter(BaseImporter):
    name: str = "content"
    metadata: types.ExportImportMetadata = None
    languages: types.PortalLanguages = None
    dropped: set = set()

    def all_objects(self) -> Generator:
        """Return all objects to be serialized."""
        all_files = self.metadata._data_files_
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
        objs = []
        modified = set()
        with request_provides(self.request, IExportImportRequestMarker):
            for index, item in enumerate(self.all_objects(), start=1):
                item_path = item["@id"]
                item_type = item["@type"]
                item_uid = item.get("UID", "")
                logger.info(f"{index:07d} - {item_path} - ({item_type}) - ({item_uid})")
                obj = self.construct(item)
                if obj:
                    obj_path = "/".join(obj.getPhysicalPath())
                    objs.append(obj_path)
                else:
                    self.dropped.add(item_path)
                if not index % 100:
                    transaction.savepoint()
                    logger.info(f"Handled {index} items...")
            for setter in content_utils.metadata_setters():
                data = getattr(self.metadata, setter.name)
                logger.info(f"Processing {setter.name}: {len(data)} entries")
                for index, uid in enumerate(data, start=index):
                    value = data[uid]
                    if setter.func(uid, value):
                        modified.add(uid)
                    if not index % 100:
                        transaction.savepoint()
                        logger.info(f"Handled {index} items...")
            # Reindex objects
            idxs = [
                "allowedRolesAndUsers",
                "getObjPositionInParent",
                "is_default_page",
                "modified",
                "created",
            ]
            content_utils.recatalog_uids(modified, idxs=idxs)
        return f"{self.__class__.__name__}: Imported {len(objs)} objects"

    def import_data(
        self,
        base_path: Path,
        data_hooks: List[Callable] = None,
        pre_deserialize_hooks: List[Callable] = None,
        obj_hooks: List[Callable] = None,
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
                logger.warning({item_path})
        return result

    def start(self):
        """Hook to do something before import starts."""

    def finish(self):
        """Hook to do something after import finishes."""
