from Acquisition import aq_base
from Acquisition import aq_parent
from OFS.interfaces import IOrderedContainer
from OFS.OrderedFolder import OrderSupport
from plone import api
from plone.base.interfaces import IPloneSiteRoot
from plone.dexterity.content import DexterityContent
from plone.dexterity.utils import iterSchemata
from plone.exportimport import settings
from plone.exportimport import types
from plone.uuid.interfaces import IUUID
from typing import List
from typing import Optional
from zope.interface.interface import InterfaceClass
from zope.schema import getFields


def is_folderish(obj: DexterityContent) -> bool:
    """Check if the given obj is folderish."""
    return bool(getattr(aq_base(obj), "isPrincipiaFolderish", False))


def is_site_root(obj: DexterityContent) -> bool:
    """Check if the given obj is a Plone Site Root."""
    return IPloneSiteRoot.providedBy(obj)


def get_uid(obj: DexterityContent) -> Optional[str]:
    """Return the uid for the given object.

    If obj is a Plone Site Root, return a constant
    defined in `plone.exportimport.settings.SITE_ROOT_UID`.
    """
    return settings.SITE_ROOT_UID if is_site_root(obj) else IUUID(obj, None)


def get_obj_path(obj: DexterityContent, relative_to_site_root: bool = False) -> str:
    """Return the path for the given obj."""
    obj_path = "/".join(obj.getPhysicalPath())
    if relative_to_site_root:
        prefix = len(get_obj_path(api.portal.get()))
        obj_path = obj_path[prefix:]
    return obj_path


def object_from_uid(uid: str) -> Optional[DexterityContent]:
    """Return an object for a given uid."""
    if uid == settings.SITE_ROOT_UID:
        return api.portal.get()
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog.unrestrictedSearchResults(UID=uid)
    return brains[0].getObject() if brains else None


def get_portal_languages() -> types.PortalLanguages:
    """Return configured languages in a Plone Site."""
    default = api.portal.get_registry_record("plone.default_language", default="en")
    available = api.portal.get_registry_record(
        "plone.available_languages", default=["en"]
    )
    return types.PortalLanguages(default, available)


def get_parent_ordered(obj: DexterityContent) -> Optional[OrderSupport]:
    """Get the OrderedContainer implementation of the parent of the given obj."""
    parent = aq_parent(obj)
    return IOrderedContainer(parent, None) if is_folderish(parent) else None


def get_all_fields(obj: DexterityContent, filter: List[InterfaceClass] = None) -> dict:
    """Return a dictionary with all fields defined for the given object."""
    fields = {}
    filter = filter if filter else []
    for schema in iterSchemata(obj):
        for name, field in getFields(schema).items():
            available = False if filter else True
            for iface in filter:
                available = available or iface.providedBy(field)
            if available:
                fields[name] = field
    return fields
