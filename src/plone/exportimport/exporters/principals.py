from .base import BaseExporter
from pathlib import Path
from plone.exportimport import interfaces
from plone.exportimport import logger
from plone.exportimport.utils import principals as principals_utils
from typing import List
from zope.interface import implementer


@implementer(interfaces.INamedExporter)
class PrincipalsExporter(BaseExporter):
    name: str = "principals"

    def dump(self) -> List[Path]:
        """Serialize object and dump it to disk."""
        data = {
            "groups": principals_utils.export_groups(),
            "members": principals_utils.export_members(),
        }
        filepath = self._dump(data, self.filepath)
        logger.debug(
            f"- Principals: Wrote {len(data['groups'])} groups and {len(data['members'])} members to {filepath}"
        )
        return [filepath]
