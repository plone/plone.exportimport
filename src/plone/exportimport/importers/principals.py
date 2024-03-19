from .base import BaseImporter
from plone.exportimport import logger
from plone.exportimport.utils import principals as principals_utils
from typing import List


class PrincipalsImporter(BaseImporter):
    name: str = "principals"

    def _import_groups(self, groups=List[dict]) -> int:
        logger.debug(f"- Principals: Read {len(groups)} groups from {self.filepath}")
        total = len(principals_utils.import_groups(groups))
        logger.debug(f"- Principals: Imported {total} groups")
        return total

    def _import_members(self, members=List[dict]) -> int:
        logger.debug(f"- Principals: Read {len(members)} groups from {self.filepath}")
        total = len(principals_utils.import_members(members))
        logger.debug(f"- Principals: Imported {total} members")
        return total

    def do_import(self) -> str:
        """Import groups and members into a Plone Site."""
        data = self._read()
        if data is None:
            return f"{self.__class__.__name__}: No data to import"
        groups = data.get("groups", [])
        total_groups = self._import_groups(groups)
        members = data.get("members", [])
        total_members = self._import_members(members)
        return (
            f"{self.__class__.__name__}: Imported {total_groups} groups and "
            f"{total_members} members"
        )
