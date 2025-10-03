from .base import BaseDatalessImporter
from plone import api
from plone.exportimport import logger
from plone.exportimport.interfaces import IExportImportRequestMarker
from plone.exportimport.utils import content as content_utils
from plone.exportimport.utils import request_provides
from Products.CMFCore.indexing import processQueue

import transaction


class FinalImporter(BaseDatalessImporter):
    # name: str = ""

    def do_import(self) -> str:
        count = 0
        name = self.__class__.__name__
        with request_provides(self.request, IExportImportRequestMarker):
            catalog = api.portal.get_tool("portal_catalog")
            # getAllBrains does not yet process the indexing queue before it starts.
            # It probably should.  Let's call it explicitly here.
            processQueue()
            for brain in catalog.getAllBrains():
                obj = brain.getObject()
                logger_prefix = f"- {brain.getPath()}:"
                for updater in content_utils.final_updaters():
                    logger.debug(f"{logger_prefix} Running {updater.name} for {obj}")
                    updater.func(obj)

                    # Apply obj hooks
                    for func in self.obj_hooks:
                        logger.debug(
                            f"{logger_prefix} Running object hook {func.__name__}"
                        )
                        obj = func(obj)

                count += 1
                if not count % 100:
                    transaction.savepoint()
                    logger.info(f"{name}: Handled {count} items...")

        report = f"{name}: Updated {count} objects"
        logger.info(report)
        return report
