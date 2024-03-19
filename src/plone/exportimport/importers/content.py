from .base import BaseImporter
from pathlib import Path
from plone.dexterity.content import DexterityContent
from plone.exportimport import logger
from plone.exportimport import settings
from plone.exportimport import types
from plone.exportimport.interfaces import IExportImportBlobsMarker
from plone.exportimport.utils import content as content_utils
from plone.exportimport.utils import request_provides
from typing import Callable
from typing import Generator
from typing import List

import json
import transaction


class ContentImporter(BaseImporter):
    name: str = "content"
    metadata: types.ExportImportMetadata = None
    languages: types.PortalLanguages = None

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

    def construct(self, item: dict) -> DexterityContent:
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

        # Deserialize
        new = self.deserialize(data=item, obj=new, config=config)

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
        with request_provides(self.request, IExportImportBlobsMarker):
            with transaction.manager as tm:
                for index, item in enumerate(self.all_objects(), start=1):
                    obj = self.construct(item)
                    obj_path = "/".join(obj.getPhysicalPath())
                    objs.append(obj_path)
                    if not index % 100:
                        tm.savepoint()
                        logger.info(f"Handled {index} items...")
                for setter in content_utils.metadata_setters():
                    data = getattr(self.metadata, setter.name)
                    logger.info(f"Processing {setter.name}: {len(data)} entries")
                    for index, uid in enumerate(data, start=index):
                        value = data[uid]
                        if setter.func(uid, value):
                            modified.add(uid)
                        if not index % 100:
                            tm.savepoint()
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
        return super().import_data(base_path, data_hooks, obj_hooks)
