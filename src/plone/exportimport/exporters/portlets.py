from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport.utils import portlets as utils
from zope.interface import implementer


@implementer(interfaces.INamedExporter)
class PortletsExporter(BaseExporter):
    name: str = "portlets"

    def dump(self) -> list[Path]:
        """Serialize object and dump it to disk."""
        content = self.exported_content()
        uids = set(content) if content is not None else None
        portlets = utils.get_portlets(uids=uids)
        filepath = self._dump(portlets, self.filepath)
        logger.debug(f"- Portlets: Wrote {len(portlets)} portlets to {filepath}")
        return [filepath]
