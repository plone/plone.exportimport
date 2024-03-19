from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport import PACKAGE_NAME
from Products.CMFPlone.Portal import PloneSite
from tempfile import mkdtemp
from typing import List
from typing import Optional
from zope.component import queryAdapter
from zope.component.hooks import setSite
from zope.interface import implementer


@implementer(interfaces.IExporterUtility)
class ExporterUtility:
    """Export content from a Plone Site."""

    exporter_names = (
        "plone.exporter.content",
        "plone.exporter.principals",
        "plone.exporter.redirects",
        "plone.exporter.relations",
        "plone.exporter.translations",
        "plone.exporter.discussions",
    )

    @staticmethod
    def _prepare_site(site: PloneSite) -> PloneSite:
        """Use setSite to register the site with global site manager."""
        setSite(site)
        return site

    @staticmethod
    def _prepare_path(path: Optional[Path] = None) -> Path:
        """Return a valid path to use for the export.

        If base_path is not given, create a temporary directory to export
        the content.
        """
        valid_path = path.is_dir() if path else False
        if not valid_path:
            path = Path(mkdtemp(prefix=PACKAGE_NAME))
        return path

    def all_exporters(self, site: PloneSite) -> List[BaseExporter]:
        """Return all exporters."""
        exporters = {}
        for exporter_name in self.exporter_names:
            exporter = queryAdapter(site, interfaces.INamedExporter, name=exporter_name)
            if exporter:
                exporters[exporter_name] = exporter
        return exporters

    def export_site(self, site: PloneSite, path: Optional[Path] = None) -> List[Path]:
        """Export the given site to the filesystem."""
        site = self._prepare_site(site)
        path = self._prepare_path(path)
        paths: List[Path] = [path]
        all_exporters = self.all_exporters(site)
        for exporter_name, exporter in all_exporters.items():
            logger.debug(f"Exporting {site} with {exporter_name} to {path}")
            paths.extend(exporter.export_data(path))
        return paths
