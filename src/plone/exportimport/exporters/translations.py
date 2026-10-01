from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport.utils import translations as utils
from zope.interface import implementer


@implementer(interfaces.INamedExporter)
class TranslationsExporter(BaseExporter):
    name: str = "translations"

    def dump(self) -> list[Path]:
        """Serialize object and dump it to disk."""
        content = self.exported_content()
        uids = set(content) if content is not None else None
        translations = utils.get_translations(uids=uids)
        filepath = self._dump(translations, self.filepath)
        logger.debug(
            f"- Translations: Wrote {len(translations)} translations to {filepath}"
        )
        return [filepath]
