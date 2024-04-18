from plone import api
from plone.app.portlets.interfaces import IPortletTypeInterface
from plone.app.textfield.value import RichTextValue
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
from plone.uuid.interfaces import IUUID
from z3c.relationfield import RelationValue
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.component.interfaces import IFactory
from zope.container.interfaces import INameChooser
from zope.globalrequest import getRequest
from zope.interface import providedBy


def get_portlets():
    results = []
    portal = api.portal.get()
    portal_uid = portal.UID()

    def collect_portlets(obj, path):
        uid = IUUID(obj, None)
        if not uid:
            return
        if uid == portal_uid:
            uid = SITE_ROOT_UID

        result = {}
        portlets = export_local_portlets(obj)
        if portlets:
            result["portlets"] = portlets
        blacklist = export_portlets_blacklist(obj)
        if blacklist:
            result["blacklist_status"] = blacklist
        if result:
            result.update(
                {
                    "@id": obj.absolute_url(),
                    "UID": uid,
                }
            )
            results.append(result)

    portal.ZopeFindAndApply(portal, search_sub=True, apply_func=collect_portlets)
    collect_portlets(portal, portal_uid)
    return results


def export_local_portlets(obj):
    """Serialize portlets for one content object
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


def export_portlets_blacklist(obj):
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


def set_portlets(data):
    results = 0
    for item in data:
        obj = api.content.get(UID=item["UID"])
        if not obj:
            if item["UID"] == SITE_ROOT_UID:
                obj = api.portal.get()
            else:
                logger.info(
                    f"Could not find object to set portlet on UUID: {item['UID']}"
                )
                continue
        registered_portlets = import_local_portlets(obj, item)
        results += registered_portlets
    return results


def import_local_portlets(obj, item):
    """Register portlets from one object
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

    for blacklist_status in item.get("blacklist_status", []):
        status = blacklist_status["status"]
        manager_name = blacklist_status["manager"]
        category = blacklist_status["category"]
        manager = queryUtility(IPortletManager, manager_name)
        if not manager:
            logger.info(f"No portlet manager {manager_name}")
            continue
        assignable = queryMultiAdapter((obj, manager), ILocalPortletAssignmentManager)
        if status.lower() == "block":
            assignable.setBlacklistStatus(category, True)
        elif status.lower() == "show":
            assignable.setBlacklistStatus(category, False)

    return results
