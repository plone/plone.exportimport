from contextlib import contextmanager
from plone import api
from plone.app.users.browser.userdatapanel import getUserDataSchema
from plone.exportimport import logger
from plone.exportimport.utils.principals import helpers
from plone.restapi.serializer.converters import json_compatible
from Products.CMFPlone.RegistrationTool import RegistrationTool
from Products.PlonePAS.tools.memberdata import MemberData
from typing import List
from zope.schema import getFieldNames


@contextmanager
def _run_as_manager(context: RegistrationTool):
    """Grant the current user the role of Manager on portal_registration.

    We use this because api.env.adopt_roles does not work for
    this specific use case.
    """
    current_user = api.user.get_current()
    local_roles = current_user.getRolesInContext(context)
    has_manager = "Manager" in local_roles
    if not has_manager:
        msg = f"the role Manager to user {current_user.getUser()} on {context}"
        logger.debug(f"Grant {msg}")
        context.manage_setLocalRoles(
            current_user.getId(), list(local_roles) + ["Manager"]
        )
    try:
        yield
    finally:
        if not has_manager:
            logger.debug(f"Revoke {msg}")
            context.manage_setLocalRoles(current_user.getId(), list(local_roles))


def _get_user_schema_fields() -> List[str]:
    """List of fields/properties used in User Schema."""
    schema = getUserDataSchema()
    fields = [name for name in getFieldNames(schema)]
    return fields


def _get_user_password(member: MemberData):
    user_id = member.getUserId()
    acl_users = api.portal.get_tool("acl_users")
    users = acl_users.source_users
    passwords = users._user_passwords
    password = passwords.get(user_id, "")
    return password.decode("utf-8") if isinstance(password, bytes) else password


def _get_user_properties(member: MemberData, fields: List[str]) -> dict:
    props = {}
    for prop in fields:
        if prop in ("portrait", "pdelete"):
            continue
        props[prop] = json_compatible(member.getProperty(prop))
    return props


def _get_base_user_data(member: MemberData):
    user_id = member.getUserId()
    groups = []
    member_groups = helpers.get_all_groups(username=user_id)
    _group_roles = []
    # Drop groups in which the user is a transitive member
    for group in member_groups:
        plone_group = group.getGroup()
        if user_id in plone_group.getMemberIds():
            groups.append(group.id)
            _group_roles.extend(helpers.get_roles_for_group(group))

    roles = helpers.get_roles_for_member(member)
    if _group_roles:
        # Remove inherited roles
        roles = [r for r in roles if r not in _group_roles]
    # username, groups, roles
    props = {
        "username": user_id,
        "roles": json_compatible(roles),
        "groups": json_compatible(groups),
    }
    return props


def export_members() -> List[dict]:
    """Serialize all members as a list of dictionaries."""
    acl_users = api.portal.get_tool("acl_users")
    fields = _get_user_schema_fields()
    data = []
    users = [
        user
        for user in acl_users.searchUsers()
        if not user["pluginid"] == "mutable_properties"
    ]
    for user in users:
        user_id = user["userid"]
        member = api.user.get(user_id)
        # Base data
        user_data = _get_base_user_data(member)
        # Password
        user_data["password"] = _get_user_password(member)
        user_data["login_name"] = member.getUserName()
        # Properties
        user_data.update(_get_user_properties(member, fields))
        data.append(user_data)
    return data


def import_members(data: List[dict]) -> MemberData:
    """Import member information from the provided list of dictionaries."""
    members = []
    pr = api.portal.get_tool("portal_registration")
    pas = api.portal.get_tool("acl_users")
    with _run_as_manager(pr):
        for item in data:
            username = item["username"]
            email = item["email"]
            if api.user.get(username=username) is not None:
                logger.error(f"Skipping: User {username} already exists!")
                continue
            elif not email:
                logger.info(f"Skipping user {username} without email: {item}")
                continue
            password = item.pop("password")
            roles = item.pop("roles", [])
            groups = item.pop("groups", [])
            login_name = item.pop("login_name", None)
            try:
                pr.addMember(username, password, roles, [], item)
            except ValueError:
                logger.info(f"ValueError {username} : {item}")
                continue
            else:
                user = api.user.get(username=username)
            if login_name:
                pas.updateLoginName(username, login_name)
            for groupname in groups:
                try:
                    api.group.add_user(groupname=groupname, user=user)
                except (api.exc.GroupNotFoundError, KeyError):
                    pass
            members.append(user)

    return members


def get_history_user_info(userid: str) -> dict:
    """Return basic user information in the format used by history."""
    actor = {"fullname": userid}
    mt = api.portal.get_tool("portal_membership")
    info = mt.getMemberInfo(userid)
    if info is not None:
        actor["fullname"] = info.get("fullname", userid) or userid

    return {"actor": actor, "actor_home": ""}
