from .base import BaseImporter
from plone.exportimport import logger
from plone.exportimport.utils import relations as utils


class RelationsImporter(BaseImporter):
    name: str = "relations"

    def do_import(self) -> dict:
        """Import relations into a Plone Site."""
        data = self._read()
        if data is None:
            return f"{self.__class__.__name__}: No data to import"
        logger.debug(f"- Relations: Read {len(data)} from {self.filepath}")
        results = utils.set_relations(data)
        return f"{self.__class__.__name__}: Imported {len(results)} relations"
