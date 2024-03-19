from .base import BaseImporter
from plone.exportimport import logger
from plone.exportimport.utils import translations as utils


class TranslationsImporter(BaseImporter):
    name: str = "translations"

    def do_import(self) -> str:
        """Import translations into a Plone Site."""
        data = self._read()
        if data is None:
            return f"{self.__class__.__name__}: No data to import"
        logger.debug(f"- Translations: Read {len(data)} from {self.filepath}")
        results = utils.set_translations(data)
        return f"{self.__class__.__name__}: Imported {len(results)} translations"
