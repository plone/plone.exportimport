from .base import BaseImporter
from plone.exportimport import logger


class DiscussionsImporter(BaseImporter):
    name: str = "discussions"

    def do_import(self) -> str:
        """Import discussions into a Plone Site."""
        data = self._read()
        if data is None:
            return f"{self.__class__.__name__}: No data to import"

        try:
            from plone.exportimport.utils import discussions as utils
        except ImportError:
            logger.warning(
                "- Discussions: Skipping (plone.app.discussion not installed)"
            )
            return ""

        logger.debug(f"- Discussions: Read {len(data)} from {self.filepath}")
        results = utils.set_discussions(data)
        return f"{self.__class__.__name__}: Imported {len(results)} conversations"
