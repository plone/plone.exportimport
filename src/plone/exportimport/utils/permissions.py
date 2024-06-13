from AccessControl.Permission import Permission
from plone import api
from plone.dexterity.content import DexterityContent
from plone.exportimport import types
from Products.CMFPlone.WorkflowTool import WorkflowTool
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition


def get_workflow_permissions(context: DexterityContent) -> list[str]:
    """List permissions managed by content workflow."""
    all_permissions = set()
    workflow_tool: WorkflowTool = api.portal.get_tool("portal_workflow")
    chains = workflow_tool.getChainFor(context)
    for chain in chains:
        workflow: DCWorkflowDefinition = workflow_tool[chain]
        for permission_name in workflow.permissions:
            all_permissions.add(permission_name)
    return list(all_permissions)


def get_local_permissions(
    context: DexterityContent, config: types.ExporterConfig = None
) -> dict:
    """Return a dictionary with permissions set in a context."""
    # TODO: Filter permissions managed by workflow
    valid_roles = context.valid_roles()
    managed_permissions = get_workflow_permissions(context)
    permissions = {}
    for perm in context.ac_inherited_permissions(1):
        name = perm[0]
        if name in managed_permissions:
            # Do not export permissions managed by a workflow
            continue
        p = Permission(name, perm[1], context)
        roles = p.getRoles(default=[])
        acquire = isinstance(roles, list)  # tuple means don't acquire
        roles = [r for r in roles if r in valid_roles]
        if not acquire:
            permissions[name] = {"acquire": acquire, "roles": roles}
    return permissions


def set_local_permissions(context: DexterityContent, permissions: dict) -> bool:
    """Set permissions in a context."""
    for permission_name, permission in permissions.items():
        acquire = permission.get("acquire")
        roles = permission.get("roles")
        context.manage_permission(permission_name, roles=roles, acquire=acquire)
    return True
