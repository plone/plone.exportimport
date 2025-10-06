from .base import BaseDatalessImporter
from plone import api
from plone.exportimport import logger
from plone.exportimport import settings
from plone.exportimport.interfaces import IExportImportRequestMarker
from plone.exportimport.utils import content as content_utils
from plone.exportimport.utils import request_provides
from Products.CMFCore.indexing import processQueue


class FinalImporter(BaseDatalessImporter):
    # name: str = ""

    def do_import(self) -> str:
        count = 0
        name = self.__class__.__name__
        request = self.request
        if not request:
            logger.warning(f"{name}: No request found, skipping final import step")
            return f"{name}: No request found, skipping final import step"
        with request_provides(request, IExportImportRequestMarker):
            site = api.portal.get()
            catalog = api.portal.get_tool("portal_catalog")
            # getAllBrains does not yet process the indexing queue before it starts.
            # It probably should.  Let's call it explicitly here.
            processQueue()
            to_reindex = (brain.getPath() for brain in catalog.getAllBrains())
            for path in to_reindex:
                logger_prefix = f"- {path}:"
                obj = site.unrestrictedTraverse(path)
                if obj is None:
                    logger.warning(f"{logger_prefix} Did not find object at {path}")
                    continue
                for updater in content_utils.final_updaters():
                    logger.debug(f"{logger_prefix} Running {updater.name} for {obj}")
                    updater.func(obj)
                    # Apply obj hooks
                    obj_hooks = self.obj_hooks or []
                    for func in obj_hooks:
                        logger.debug(
                            f"{logger_prefix} Running object hook {func.__name__}"
                        )
                        obj = func(obj)

                count += 1
                if not count % self.commit_after:
                    self._commit(f"Reindexed {self.commit_after} objects")
                    logger.info(f"{name}: Handled {count} items... (Commit)")
                elif not count % self.savepoint_after:
                    self._savepoint()
                if not count % settings.IMPORTER_REPORT:
                    logger.info(f"{name}: Handled {count} items...")

        if self.intermediate_commits and (last_batch := count % self.commit_after):
            self._commit(f"Reindexed {last_batch} objects")
            logger.info(f"{name}: Handled {count} items... (Commit)")

        report = f"{name}: Updated {count} objects"
        logger.info(report)
        return report
