from plone import api
from plone.exportimport.settings import AUTO_GROUPS
from plone.exportimport.settings import AUTO_ROLES
from Products.PlonePAS.tools.groupdata import GroupData
from typing import List
from typing import Optional


def get_roles_for_group(group: GroupData, filter: bool = True) -> list:
    """Return a list of roles for a given group."""
    roles = [r for r in api.group.get_roles(group=group)]
    if filter:
        roles = [r for r in roles if r not in AUTO_ROLES]
    return sorted(roles)


def get_roles_for_member(member, filter: bool = True) -> List[str]:
    """Return a list of roles for a given member."""
    roles = [r for r in member.getRoles()]
    if filter:
        roles = [r for r in roles if r not in AUTO_ROLES]
    return sorted(roles)


def get_all_groups(
    username: str = "", group: Optional[GroupData] = None, filter: bool = True
) -> List[GroupData]:
    """Get groups."""
    payload = {}
    if username:
        payload["username"] = username
    elif group:
        payload["user"] = group
    groups = [g for g in api.group.get_groups(**payload)]
    if filter:
        groups = [g for g in groups if g.id not in AUTO_GROUPS]
    return groups
