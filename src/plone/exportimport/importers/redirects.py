from .base import BaseImporter
from plone.exportimport import logger
from plone.exportimport.utils import redirects as utils


class RedirectsImporter(BaseImporter):
    name: str = "redirects"

    def do_import(self) -> str:
        """Import redirects into a Plone Site."""
        data = self._read()
        if data is None:
            return f"{self.__class__.__name__}: No data to import"
        logger.debug(f"- Redirects: Read {len(data)} from {self.filepath}")
        results = utils.set_redirects(data)
        return f"{self.__class__.__name__}: Imported {len(results)} redirects"
