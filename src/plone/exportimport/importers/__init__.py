from .base import BaseImporter
from pathlib import Path
from plone import api
from plone.exportimport import interfaces
from plone.exportimport import logger
from Products.CMFPlone.Portal import PloneSite
from typing import Dict
from typing import List
from zope.component import getAdapter
from zope.component import hooks
from zope.component import queryAdapter
from zope.interface import implementer


ImporterMapping = Dict[str, BaseImporter]


@implementer(interfaces.IImporter)
class Importer:
    """Import content into a Plone Site."""

    importer_names = (
        "plone.importer.content",
        "plone.importer.principals",
        "plone.importer.redirects",
        "plone.importer.relations",
        "plone.importer.translations",
        "plone.importer.discussions",
    )
    importers: ImporterMapping

    def __init__(self, site):
        self.site = site
        self.importers = self.all_importers()

    def all_importers(self) -> List[BaseImporter]:
        """Return all importers."""
        importers = {}
        for importer_name in self.importer_names:
            importer = queryAdapter(
                self.site, interfaces.INamedImporter, name=importer_name
            )
            if importer:
                importers[importer_name] = importer
        return importers

    def import_site(self, path: Path) -> List[str]:
        """Import the given site from the filesystem."""
        report = []
        with hooks.site(self.site):
            for importer_name, importer in self.importers.items():
                logger.debug(
                    f"Importing from {path} to {self.site} with {importer_name}"
                )
                report.append(importer.import_data(path))
        return report


def get_importer(site: PloneSite = None) -> Importer:
    """Get the importer."""
    if site is None:
        site = api.portal.get()
    return getAdapter(site, interfaces.IImporter)
