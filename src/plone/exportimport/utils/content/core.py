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
from plone.uuid.interfaces import ATTRIBUTE_NAME
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.Portal import PloneSite
from zope.interface.interface import InterfaceClass
from zope.schema import getFields


def is_folderish(obj: DexterityContent) -> bool:
    """Check if the given obj is folderish."""
    return bool(getattr(aq_base(obj), "isPrincipiaFolderish", False))


def is_site_root(obj: DexterityContent) -> bool:
    """Check if the given obj is a Plone Site Root."""
    return IPloneSiteRoot.providedBy(obj)


def get_uid(obj: DexterityContent) -> str | None:
    """Return the stored uid for the given object.

    The stored uid is the ``_plone.uuid`` attribute. It is not the uid
    reported by ``IUUID``: plone.app.multilingual reports the uid of a content
    inside a language-independent folder with the language root id appended.

    If obj is a Plone Site Root, return a constant
    defined in `plone.exportimport.settings.SITE_ROOT_UID`.
    """
    if is_site_root(obj):
        return settings.SITE_ROOT_UID
    stored = getattr(aq_base(obj), ATTRIBUTE_NAME, None)
    return stored if stored is not None else IUUID(obj, None)


def language_codes() -> list[str]:
    """Return the language codes of the site, the ids of its language roots."""
    languages = get_portal_languages()
    return sorted({languages.default, *languages.available})


def strip_language_suffix(uid: str, codes: list[str] | None = None) -> str:
    """Return the stored uid for a uid that may carry a language suffix.

    :param uid: A uid as reported by ``IUUID`` or the catalog.
    :param codes: Language codes to look for, default is :func:`language_codes`.
    :returns: The uid without the ``-<language code>`` suffix, if it has one.
    """
    codes = language_codes() if codes is None else codes
    for code in codes:
        suffix = f"-{code}"
        if uid and uid.endswith(suffix):
            return uid[: -len(suffix)]
    return uid


def _in_language_root(brain) -> bool:
    """Return True if the brain sits in the language root of its language."""
    segments = brain.getPath().split("/")
    return len(segments) > 2 and segments[2] == brain.Language


def unique_brains(brains) -> list:
    """Return one catalog brain per stored uid.

    A content inside a language-independent folder has one copy per language
    root, all sharing the stored uid. The copy in its own language root is
    kept, otherwise the first one found.

    :param brains: Catalog brains.
    :returns: Brains in their original order, without duplicated stored uids.
    """
    codes = language_codes()
    chosen: dict[str, object] = {}
    for brain in brains:
        key = strip_language_suffix(brain.UID, codes)
        current = chosen.get(key)
        if current is None or (
            _in_language_root(brain) and not _in_language_root(current)
        ):
            chosen[key] = brain
    kept = {id(brain) for brain in chosen.values()}
    return [brain for brain in brains if id(brain) in kept]


def get_obj_path(obj: DexterityContent, relative_to_site_root: bool = False) -> str:
    """Return the path for the given obj."""
    obj_path = "/".join(obj.getPhysicalPath())
    if relative_to_site_root:
        prefix = len(get_obj_path(api.portal.get()))
        obj_path = obj_path[prefix:]
    return obj_path


def content_query(query: dict) -> dict:
    """Return a copy of a catalog query restricted, by default, to content.

    :param query: Catalog query. It is not modified.
    :returns: A new query, with ``object_provides`` set to
        ``IDexterityContent`` unless the query already sets it.
    """
    query = {**query}
    if "object_provides" not in query:
        query["object_provides"] = "plone.dexterity.interfaces.IDexterityContent"
    return query


def get_content_paths(query: dict) -> dict[str, str]:
    """Return the UID and physical path of the content matching a query.

    Only catalog brains are used, so no object is woken up.

    :param query: Catalog query, processed by :func:`content_query`.
    :returns: Mapping of UID to physical path.
    """
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog.unrestrictedSearchResults(**content_query(query))
    codes = language_codes()
    return {
        strip_language_suffix(brain.UID, codes): brain.getPath()
        for brain in unique_brains(brains)
    }


def object_from_uid(uid: str) -> DexterityContent | None:
    """Return an object for a given stored uid.

    The stored uid is tried first. A content inside a language-independent
    folder is catalogued with the language root id appended, so the
    ``-<language code>`` forms are tried next, as plone.app.multilingual does.
    A uid that already carries the suffix (exports made by earlier versions)
    is found by the first lookup.
    """
    if uid == settings.SITE_ROOT_UID:
        return api.portal.get()
    catalog = api.portal.get_tool("portal_catalog")
    candidates = [uid] + [f"{uid}-{code}" for code in language_codes()]
    for candidate in candidates:
        brains = catalog.unrestrictedSearchResults(UID=candidate)
        if brains:
            return brains[0].getObject()
    return None


def object_from_uid_or_path(uid: str, path: str = "") -> DexterityContent | None:
    """Return an object for a given uid or given path."""
    obj = None
    if path:
        # Try first to get the object by its path
        portal: PloneSite = api.portal.get()
        obj = portal.unrestrictedTraverse(path, default=None)
        # Check if the found object has the expected uid
        obj = obj if obj and get_uid(obj) == uid else None
    if not obj:
        obj = object_from_uid(uid)
    return obj


def get_portal_languages() -> types.PortalLanguages:
    """Return configured languages in a Plone Site."""
    default = api.portal.get_registry_record("plone.default_language", default="en")
    available = api.portal.get_registry_record(
        "plone.available_languages", default=["en"]
    )
    return types.PortalLanguages(default, available)


def get_parent_ordered(obj: DexterityContent) -> OrderSupport | None:
    """Get the OrderedContainer implementation of the parent of the given obj."""
    parent = aq_parent(obj)
    return IOrderedContainer(parent, None) if is_folderish(parent) else None


def get_all_fields(
    obj: DexterityContent, filter: list[type[InterfaceClass]] | None = None
) -> dict:
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
