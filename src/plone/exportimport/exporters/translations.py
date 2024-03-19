from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport.utils import translations as utils
from typing import List
from zope.interface import implementer


@implementer(interfaces.INamedExporter)
class TranslationsExporter(BaseExporter):
    name: str = "translations"

    def dump(self) -> List[Path]:
        """Serialize object and dump it to disk."""
        translations = utils.get_translations()
        filepath = self._dump(translations, self.filepath)
        logger.debug(
            f"- Translations: Wrote {len(translations)} translations to {filepath}"
        )
        return [filepath]
