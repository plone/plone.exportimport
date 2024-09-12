from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from typing import List
from zope.interface import implementer


try:
    import plone.app.discussion  # noqa
except ImportError:
    HAS_DISCUSSION = False
else:
    HAS_DISCUSSION = True


@implementer(interfaces.INamedExporter)
class DiscussionsExporter(BaseExporter):
    name: str = "discussions"

    def dump(self) -> List[Path]:
        """Serialize object and dump it to disk."""
        if not HAS_DISCUSSION:
            logger.debug("- Discussions: Skipping (plone.app.discussion not installed)")
            return []

        from plone.exportimport.utils import discussions as utils

        discussions = utils.get_discussions()
        filepath = self._dump(discussions, self.filepath)
        logger.debug(
            f"- Discussions: Wrote {len(discussions)} discussions to {filepath}"
        )
        return [filepath]
