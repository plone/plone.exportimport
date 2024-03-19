from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport.utils import redirects as utils
from typing import List
from zope.interface import implementer


@implementer(interfaces.INamedExporter)
class RedirectsExporter(BaseExporter):
    name: str = "redirects"

    def dump(self) -> List[Path]:
        """Serialize object and dump it to disk."""
        redirects = utils.get_redirects()
        filepath = self._dump(redirects, self.filepath)
        logger.debug(f"- Redirects: Wrote {len(redirects)} redirects to {filepath}")
        return [filepath]
