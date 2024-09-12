from plone import api
from plone.app.portlets.interfaces import IPortletTypeInterface
from plone.app.textfield.value import RichTextValue
from plone.dexterity.content import DexterityContent
from plone.exportimport import logger
from plone.exportimport.settings import SITE_ROOT_UID
from plone.portlets.constants import CONTENT_TYPE_CATEGORY
from plone.portlets.constants import CONTEXT_CATEGORY
from plone.portlets.constants import GROUP_CATEGORY
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletAssignmentSettings
from plone.portlets.interfaces import IPortletManager
from plone.restapi.interfaces import IFieldDeserializer
from plone.restapi.serializer.converters import json_compatible
from typing import List
from typing import Optional
from typing import Union
from z3c.relationfield import RelationValue
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.component.interfaces import IFactory
from zope.container.interfaces import INameChooser
from zope.globalrequest import getRequest
from zope.interface import providedBy

import warnings


def portlets_in_context(
    context: DexterityContent, uid: Optional[str] = None
) -> Union[dict, None]:
    """Collect portlet registrations in a context."""
    result = {}
    uid = uid if uid else api.content.get_uuid(context, None)
    if not uid:
        return

    portlets = export_local_portlets(context)
    if portlets:
        result["portlets"] = portlets
    disallowlist = export_portlets_disallowlist(context)
    if disallowlist:
        result["disallowlist_status"] = disallowlist
    if result:
        result.update(
            {
                "@id": context.absolute_url(),
                "UID": uid,
            }
        )
    return result


def get_portlets() -> List[dict]:
    """Return a list of all portlet assignments on the site."""
    results = []
    portal = api.portal.get()
    portal_uid = portal.UID()

    def collect_portlets(obj, path):
        try:
            uid = api.content.get_uuid(obj)
        except TypeError:
            uid = None
        if not uid:
            return
        if uid == portal_uid:
            uid = SITE_ROOT_UID
        result = portlets_in_context(obj, uid)
        if result:
            results.append(result)

    portal.ZopeFindAndApply(portal, search_sub=True, apply_func=collect_portlets)
    collect_portlets(portal, portal_uid)
    return results


def export_local_portlets(obj: DexterityContent) -> dict:
    """Serialize portlets for one content object.

    Code mostly taken from https://github.com/plone/plone.restapi/pull/669
    """
    portlets_schemata = {
        iface: name for name, iface in getUtilitiesFor(IPortletTypeInterface)
    }
    items = {}
    for manager_name, manager in getUtilitiesFor(IPortletManager):
        mapping = queryMultiAdapter((obj, manager), IPortletAssignmentMapping)
        if mapping is None:
            continue
        mapping = mapping.__of__(obj)
        for name, assignment in mapping.items():
            portlet_type = None
            schema = None
            for schema in providedBy(assignment).flattened():
                portlet_type = portlets_schemata.get(schema, None)
                if portlet_type is not None:
                    break
            if portlet_type is None:
                continue
            assignment = assignment.__of__(mapping)
            settings = IPortletAssignmentSettings(assignment)
            if manager_name not in items:
                items[manager_name] = []
            values = {}
            for name in schema.names(all=True):
                value = getattr(assignment, name, None)
                if RelationValue is not None and isinstance(value, RelationValue):
                    value = value.to_object.UID()
                elif isinstance(value, RichTextValue):
                    value = {
                        "data": json_compatible(value.raw),
                        "content-type": json_compatible(value.mimeType),
                        "encoding": json_compatible(value.encoding),
                    }
                value = json_compatible(value)
                values[name] = value
            items[manager_name].append(
                {
                    "type": portlet_type,
                    "visible": settings.get("visible", True),
                    "assignment": values,
                }
            )
    return items


def export_portlets_disallowlist(obj: DexterityContent) -> List[dict]:
    """Export portlets disallowlist for one content object."""
    results = []
    for manager_name, manager in getUtilitiesFor(IPortletManager):
        assignable = queryMultiAdapter((obj, manager), ILocalPortletAssignmentManager)
        if assignable is None:
            continue
        for category in (
            USER_CATEGORY,
            GROUP_CATEGORY,
            CONTENT_TYPE_CATEGORY,
            CONTEXT_CATEGORY,
        ):
            obj_results = {}
            status = assignable.getBlacklistStatus(category)
            if status is True:
                obj_results["status"] = "block"
            elif status is False:
                obj_results["status"] = "show"

            if obj_results:
                obj_results["manager"] = manager_name
                obj_results["category"] = category
                results.append(obj_results)
    return results


def _has_new_registrations(base: dict, registrations: dict) -> bool:
    """Are the new registrations additions/changes to the current ones?

    This is for both portlets and disallowlists.
    The import code does not handle removals, so we are not interested in those.
    """
    key = "portlets"
    current = base.get(key, {})
    to_register = registrations.get(key, {})
    for manager_id, assignments in to_register.items():
        if manager_id not in current:
            return True
        manager = current[manager_id]
        for assignment in assignments:
            if assignment not in manager:
                return True

    key = "disallowlist_status"
    current = base.get(key, [])
    to_register = registrations.get(key, [])
    for new_reg in to_register:
        # Each new_reg is a dict with keys category, manager and status.
        # Try to find the same registration in the current registrations.
        found = False
        for old_reg in current:
            same = True
            for key, value in new_reg.items():
                if old_reg.get(key) != value:
                    same = False
                    break
            if same:
                # All keys/values are the same.
                found = True
                break
        if not found:
            # We did not find a duplicate in the current registrations,
            # so there is a difference.
            return True

    # no changes
    return False


def set_portlets(data: list) -> int:
    """Set portlets for context."""
    results = 0
    for item in data:
        item_uid = item["UID"]
        obj = api.content.get(UID=item_uid)
        if not obj:
            if item_uid == SITE_ROOT_UID:
                obj = api.portal.get()
            else:
                logger.info(
                    f"Could not find object to set portlet on UUID: {item['UID']}"
                )
                continue
        existing_registrations = portlets_in_context(obj, item_uid)
        old_key = "blacklist_status"
        new_key = "disallowlist_status"
        if old_key in item and new_key not in item:
            warnings.warn(
                f"{old_key} is deprecated, please use {new_key}.", DeprecationWarning
            )
            item[new_key] = item.pop(old_key)
        new_registrations = _has_new_registrations(existing_registrations, item)
        if new_registrations:
            registered_portlets = import_local_portlets(obj, item)
            results += registered_portlets
    return results


def import_local_portlets(obj: DexterityContent, item: dict) -> int:
    """Register portlets from one object.

    Code adapted from plone.app.portlets.exportimport.portlets.PortletsXMLAdapter
    """
    site = api.portal.get()
    request = getRequest()
    results = 0

    for manager_name, portlets in item.get("portlets", {}).items():
        manager = queryUtility(IPortletManager, manager_name)
        if not manager:
            logger.info(f"No portlet manager {manager_name}")
            continue
        mapping = queryMultiAdapter((obj, manager), IPortletAssignmentMapping)
        namechooser = INameChooser(mapping)
        for portlet_data in portlets:
            # 1. Create the assignment
            assignment_data = portlet_data["assignment"]
            portlet_type = portlet_data["type"]
            portlet_factory = queryUtility(IFactory, name=portlet_type)
            if not portlet_factory:
                logger.info(f"No factory for portlet {portlet_type}")
                continue

            assignment = portlet_factory()

            name = namechooser.chooseName(None, assignment)
            mapping[name] = assignment

            # aq-wrap it so that complex fields will work
            assignment = assignment.__of__(site)

            # set visibility setting
            visible = portlet_data.get("visible")
            if visible is not None:
                settings = IPortletAssignmentSettings(assignment)
                settings["visible"] = visible

            # 2. Apply portlet settings
            portlet_interface = getUtility(IPortletTypeInterface, name=portlet_type)
            for property_name, value in assignment_data.items():
                field = portlet_interface.get(property_name, None)
                if field is None:
                    continue
                field = field.bind(assignment)
                # deserialize data (e.g. for RichText)
                deserializer = queryMultiAdapter(
                    (field, assignment, request), IFieldDeserializer
                )
                if deserializer is not None:
                    try:
                        value = deserializer(value)
                    except Exception as e:
                        logger.info(
                            f"Could not import portlet data {value} for field "
                            f"{field} on {obj.absolute_url()}: {str(e)}"
                        )
                        continue
                field.set(assignment, value)

            logger.info(
                f"Added {portlet_type} '{name}' to {manager_name} of {obj.absolute_url()}"
            )
            results += 1

    for disallowlist_status in item.get("disallowlist_status", []):
        status: bool = disallowlist_status["status"].lower() == "block"
        manager_name = disallowlist_status["manager"]
        category = disallowlist_status["category"]
        manager = queryUtility(IPortletManager, manager_name)
        if not manager:
            logger.info(f"No portlet manager {manager_name}")
            continue
        assignable = queryMultiAdapter((obj, manager), ILocalPortletAssignmentManager)
        assignable.setBlacklistStatus(category, status)
        logger.info(
            f"Added disallowlist entry {category} ({status}) to {manager_name} of {obj.absolute_url()}"
        )
        results += 1

    return results
