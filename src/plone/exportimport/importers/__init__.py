from .base import BaseImporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from Products.CMFPlone.Portal import PloneSite
from typing import List
from zope.component import queryAdapter
from zope.component.hooks import setSite
from zope.interface import implementer


@implementer(interfaces.IImporterUtility)
class ImporterUtility:
    """Import content into a Plone Site."""

    importer_names = (
        "plone.importer.content",
        "plone.importer.principals",
        "plone.importer.redirects",
        "plone.importer.relations",
        "plone.importer.translations",
        "plone.importer.discussions",
    )

    @staticmethod
    def _prepare_site(site: PloneSite) -> PloneSite:
        """Use setSite to register the site with global site manager."""
        setSite(site)
        return site

    def all_importers(self, site: PloneSite) -> List[BaseImporter]:
        """Return all importers."""
        importers = {}
        for importer_name in self.importer_names:
            importer = queryAdapter(site, interfaces.INamedImporter, name=importer_name)
            if importer:
                importers[importer_name] = importer
        return importers

    def import_site(self, site: PloneSite, path: Path) -> List[str]:
        """Import  the given site to the filesystem."""
        report = []
        site = self._prepare_site(site)
        all_importers = self.all_importers(site)
        for importer_name, importer in all_importers.items():
            logger.debug(f"Importing from {path} to {site} with {importer_name}")
            report.append(importer.import_data(path))
        return report
