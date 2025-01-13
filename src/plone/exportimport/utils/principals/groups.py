from .helpers import get_all_groups
from .helpers import get_roles_for_group
from plone import api
from plone.restapi.serializer.converters import json_compatible
from Products.PlonePAS.tools.groupdata import GroupData
from typing import List


def export_groups() -> List[dict]:
    """Return all groups."""
    data = []
    all_groups = get_all_groups()
    for group in all_groups:
        roles = get_roles_for_group(group)
        groups = sorted([g.id for g in get_all_groups(group=group)])
        item = {"groupid": group.id, "groups": groups, "roles": roles}
        for prop in group.getProperties():
            item[prop] = json_compatible(group.getProperty(prop))
        # export all principals (incl. groups and ldap-users)
        plone_group = group.getGroup()
        item["principals"] = sorted(plone_group.getMemberIds())
        data.append(item)
    return data


def import_groups(data: List[dict]) -> List[GroupData]:
    """Import groups."""
    groups = []
    acl = api.portal.get_tool("acl_users")
    groupsIds = {item["id"] for item in acl.searchGroups()}
    for item in data:
        groupid = item["groupid"]
        principals = item.pop("principals", [])
        if groupid not in groupsIds:
            group = api.group.create(
                groupname=groupid,
                title=item["title"],
                description=item["description"],
                roles=item["roles"],
            )
            groups.append(group)
        else:
            group = api.group.get(groupname=groupid)
        # add all principals, even if they are not stored in plone (e.g. LDAP)
        for principal in principals:
            try:
                api.group.add_user(group=group, username=principal)
            except api.exc.UserNotFoundError:
                pass
    return groups
