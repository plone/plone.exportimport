from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport.utils import portlets as utils
from typing import List
from zope.interface import implementer


@implementer(interfaces.INamedExporter)
class PortletsExporter(BaseExporter):
    name: str = "portlets"

    def dump(self) -> List[Path]:
        """Serialize object and dump it to disk."""
        portlets = utils.get_portlets()
        filepath = self._dump(portlets, self.filepath)
        logger.debug(f"- Portlets: Wrote {len(portlets)} portlets to {filepath}")
        return [filepath]
