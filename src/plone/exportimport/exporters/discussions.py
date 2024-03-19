from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport.utils import discussions as utils
from typing import List
from zope.interface import implementer


@implementer(interfaces.INamedExporter)
class DiscussionsExporter(BaseExporter):
    name: str = "discussions"

    def dump(self) -> List[Path]:
        """Serialize object and dump it to disk."""
        discussions = utils.get_discussions()
        filepath = self._dump(discussions, self.filepath)
        logger.debug(
            f"- Discussions: Wrote {len(discussions)} discussions to {filepath}"
        )
        return [filepath]
