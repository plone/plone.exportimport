from .base import BaseExporter
from collections.abc import Callable
from collections.abc import Generator
from pathlib import Path
from plone import api
from plone.base.interfaces import IPloneSiteRoot
from plone.dexterity.content import DexterityContent
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport import settings
from plone.exportimport import types
from plone.exportimport.interfaces import IExportImportRequestMarker
from plone.exportimport.utils import content as content_utils
from plone.exportimport.utils import request_provides
from typing import Any
from zope.component import getAdapter
from zope.interface import implementer

import argparse


class ObjectsExporter:

    def __init__(self, obj) -> None:
        self.obj = obj

    def get_objects(self, query, errors) -> Generator:
        """Return all objects to be serialized."""
        catalog = api.portal.get_tool("portal_catalog")
        brains = catalog.unrestrictedSearchResults(**content_utils.content_query(query))
        logger.info(f"Exporting {len(brains)}")
        for index, brain in enumerate(brains, start=1):
            try:
                obj = brain.getObject()
            except Exception:
                brain_path = brain.getPath()
                msg = f"Error getting object {brain_path} from brain"
                errors.append({"path": brain_path, "message": msg})
                logger.exception(msg, exc_info=True)
            else:
                yield obj

            if not index % 100:
                logger.info(f"Content Exporter: Handled {index} items...")


@implementer(interfaces.INamedExporter)
class ContentExporter(BaseExporter):
    name: str = "content"
    query: dict = None
    filename_fmt: str = settings.EXPORT_CONTENT_FILEPATH
    metadata: types.ExportImportMetadata = None
    default_site_language: str = "en"

    def all_objects(self) -> Generator:
        """Return all objects to be serialized."""
        adapter = getAdapter(self.site, interfaces.IObjectsExporter)
        yield from adapter.get_objects(self.query, self.errors)

    def serialize(self, obj: DexterityContent) -> dict:
        """Serialize object."""
        obj_uid = content_utils.get_uid(obj)
        obj_path = content_utils.get_obj_path(obj)
        config = types.ExporterConfig(
            site=self.site,
            site_root_uid=self.site.UID(),
            request=self.request,
            serializer=self._serializer(obj),
            logger_prefix=f"- {obj_path}:",
        )
        kwargs = {}
        is_site_root = IPloneSiteRoot.providedBy(obj)
        is_folderish = content_utils.is_folderish(obj)
        if is_folderish:
            if not is_site_root:
                kwargs["include_items"] = False
        # Process metadata
        for helper in content_utils.metadata_helpers():
            logger.debug(f"{config.logger_prefix} Updating metadata {helper.name}")
            value = helper.func(obj, config)
            if value is not None:
                getattr(self.metadata, helper.name)[obj_uid] = value

        # Apply object hooks
        for func in self.obj_hooks:
            logger.debug(
                f"{config.logger_prefix} Running object hook {func.__name__} on object"
            )
            obj = func(obj, config)

        # Serialize
        data = config.serializer(**kwargs)

        # Fix serialized data
        for fixer in content_utils.fixers():
            logger.debug(
                f"{config.logger_prefix} Running {fixer.name} on serialized data"
            )
            data = fixer.func(data, obj, config)

        # Enrich
        for enricher in content_utils.enrichers(
            include_revisions=self.get_option("include_revisions")
        ):
            logger.debug(f"{config.logger_prefix} Running {enricher.name}")
            additional = enricher.func(obj, config)
            if additional:
                data.update(additional)

        # Apply data hooks
        for func in self.data_hooks:
            logger.debug(
                f"{config.logger_prefix} Running data hook {func.__name__} on payload"
            )
            data = func(data, obj, config)

        # Cleanup data
        for cleaner in content_utils.cleaners():
            logger.debug(
                f"{config.logger_prefix} Running {cleaner.name} on serialized data"
            )
            data = cleaner.func(data, config)
        return data

    def dump_one(self, obj: DexterityContent) -> Path:
        """Serialize object and dump it to disk."""
        obj_path = content_utils.get_obj_path(obj)
        # Serialize object
        data = self.serialize(obj)
        base_path = self.base_path
        filepath = base_path / self.filename_fmt.format(**data)
        filepath = self._dump(data, filepath)
        logger.debug(f"- {obj_path}: Wrote serialized data to {filepath}")
        # Add to list of files
        self.metadata._all_[obj_path] = str(filepath.relative_to(base_path).as_posix())
        return filepath

    def dump_metadata(self) -> Path:
        metadata = self.metadata.export()
        filepath = self.base_path / "__metadata__.json"
        return self._dump(metadata, filepath)

    def dump(self) -> list[Path]:
        """Serialize contents and dump them to disk."""
        paths = []
        with request_provides(self.request, IExportImportRequestMarker):
            for obj in self.all_objects():
                path = self.dump_one(obj)
                if path:
                    paths.append(path)
            # Add list of blobs to serialization
            paths.insert(0, self.dump_metadata())
        return paths

    def _prepare_query(
        self, query: dict | None = None, options: argparse.Namespace | None = None
    ) -> dict:
        """Return the catalog query used to select the content to export.

        An explicit ``query`` takes precedence over ``options.query``. When
        neither is set, all content in the site is selected.

        :param query: Explicit catalog query.
        :param options: Export options, checked for a ``query`` attribute.
        :returns: The catalog query to use.
        """
        query = query or getattr(options, "query", None)
        return query if query else {"path": content_utils.get_obj_path(self.site)}

    def export_data(
        self,
        base_path: Path,
        data_hooks: list[Callable] | None = None,
        obj_hooks: list[Callable] | None = None,
        options: argparse.Namespace | None = None,
        query: dict | None = None,
        **kwargs: Any,
    ) -> list[Path]:
        """Export content to a ``content`` folder inside ``base_path``.

        Arguments other than ``base_path`` should be passed by keyword, as
        ``query`` comes after ``options`` in this signature.

        :param base_path: Directory where the export is written.
        :param data_hooks: Callables applied to the serialized data.
        :param obj_hooks: Callables applied to each object before serialization.
        :param options: Export options; ``options.query`` is used when no
            ``query`` is passed.
        :param query: Catalog query selecting the content to export. It takes
            precedence over ``options.query``. Defaults to all content in the site.
        :returns: Paths of the files written.
        """
        # Content in a subpath of base_path
        base_path = base_path / self.name
        site = self.site
        self.query = self._prepare_query(query, options)
        metadata = types.ExportImportMetadata()
        self.metadata = metadata
        self.request[settings.EXPORT_CONTENT_METADATA_KEY] = metadata
        self.request[settings.EXPORT_PATH_KEY] = base_path
        self.default_site_language = site.language
        return super().export_data(base_path, data_hooks, obj_hooks, options=options)
