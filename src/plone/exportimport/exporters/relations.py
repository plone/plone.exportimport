from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport.utils import relations as utils
from typing import List
from zope.interface import implementer


@implementer(interfaces.INamedExporter)
class RelationsExporter(BaseExporter):
    name: str = "relations"

    def dump(self) -> List[Path]:
        """Serialize object and dump it to disk."""
        relations = utils.get_relations()
        filepath = self._dump(relations, self.filepath)
        logger.debug(f"- Relations: Wrote {len(relations)} relations to {filepath}")
        return [filepath]
