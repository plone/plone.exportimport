from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport import PACKAGE_NAME
from Products.CMFPlone.Portal import PloneSite
from tempfile import mkdtemp
from typing import Dict
from typing import List
from typing import Optional
from zope.component import getAdapter
from zope.component import hooks
from zope.component import queryAdapter
from zope.interface import implementer


ExporterMapping = Dict[str, BaseExporter]


@implementer(interfaces.IExporter)
class Exporter:
    """Export content from a Plone Site."""

    exporter_names = (
        "plone.exporter.content",
        "plone.exporter.principals",
        "plone.exporter.redirects",
        "plone.exporter.relations",
        "plone.exporter.translations",
        "plone.exporter.discussions",
    )
    exporters: ExporterMapping

    def __init__(self, site):
        self.site = site
        self.exporters = self.all_exporters()

    def all_exporters(self) -> ExporterMapping:
        """Return all exporters."""
        exporters = {}
        for exporter_name in self.exporter_names:
            exporter = queryAdapter(
                self.site, interfaces.INamedExporter, name=exporter_name
            )
            if exporter:
                exporters[exporter_name] = exporter
        return exporters

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

    def export_site(self, path: Optional[Path] = None) -> List[Path]:
        """Export the given site to the filesystem."""
        path = self._prepare_path(path)
        paths: List[Path] = [path]
        with hooks.site(self.site):
            for exporter_name, exporter in self.exporters.items():
                logger.debug(f"Exporting {self.site} with {exporter_name} to {path}")
                paths.extend(exporter.export_data(path))
        return paths


def get_exporter(site: PloneSite = None) -> Exporter:
    """Get the exporter."""
    return getAdapter(site, interfaces.IExporter)
