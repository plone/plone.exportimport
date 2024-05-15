from .base import BaseImporter
from plone.exportimport import logger
from plone.exportimport.utils import portlets as utils


class PortletsImporter(BaseImporter):
    name: str = "portlets"

    def do_import(self) -> dict:
        """Import portlets into a Plone Site."""
        data = self._read()
        if data is None:
            return f"{self.__class__.__name__}: No data to import"
        logger.debug(f"- Portlets: Read {len(data)} from {self.filepath}")
        count = utils.set_portlets(data)
        return f"{self.__class__.__name__}: Imported {count} registrations"
