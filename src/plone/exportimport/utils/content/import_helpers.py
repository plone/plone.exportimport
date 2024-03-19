from .core import get_obj_path
from .core import get_parent_ordered
from .core import object_from_uid
from Acquisition import aq_base
from Acquisition import aq_parent
from Persistence import PersistentMapping
from plone import api
from plone.base.interfaces.constrains import ENABLED
from plone.base.interfaces.constrains import ISelectableConstrainTypes
from plone.base.utils import unrestricted_construct_instance
from plone.dexterity.content import DexterityContent
from plone.exportimport import logger
from plone.exportimport import settings
from plone.exportimport import types
from plone.exportimport.utils.dates import parse_date
from plone.restapi.interfaces import IDeserializeFromJson
from typing import Callable
from typing import List
from urllib.parse import unquote
from zope.component import getMultiAdapter


def get_deserializer(data: dict, request) -> Callable:
    return getMultiAdapter((data, request), IDeserializeFromJson)


def get_parent_from_item(data: dict) -> DexterityContent:
    portal = api.portal.get()
    parent_info = data.get("parent", {})
    parent_uid = parent_info.get("UID")
    parent_path = parent_info.get("@id")
    parent = None
    if data.get("@type") == "Plone Site":
        parent = aq_parent(api.portal.get())
    elif parent_info.get("@type") == "Plone Site":
        parent = portal
    elif parent_uid:
        parent = object_from_uid(parent_uid)
        if not parent:
            # Try to get from path
            parent = api.content.get(path=parent_path)
    if not parent:
        logger.warning(f"Container for {data['@id']} not found")
    elif not getattr(aq_base(parent), "isPrincipiaFolderish", False):
        logger.warning(f"Container for {data['@id']} is not folderish")
        parent = None
    return parent


def process_id(item: dict, config: types.ImporterConfig) -> dict:
    portal_id = config.site.getId()
    item_path = item["@id"]
    if item["@type"] == "Plone Site":
        item["id"] = portal_id
    else:
        new_id = unquote(item_path).split("/")[-1]
        if new_id != item["id"]:
            logger.info(
                f"Conflicting ids in url ({new_id}) and id ({item['id']}). Using {new_id}"
            )
            item["id"] = new_id
    return item


def process_language(item: dict, config: types.ImporterConfig) -> dict:
    """Process language field."""
    placeholder = settings.PLACEHOLDERS_LANGUAGE
    default_language = config.languages.default
    available_languages = config.languages.available
    language = item.get("language", {})
    if isinstance(language, dict):
        # Format with token
        language = language.get("token", placeholder)
    # Use default
    if language == placeholder or language not in available_languages:
        language = default_language
    item["language"] = language
    return item


def process_root_uid(item: dict, config: types.ImporterConfig) -> dict:
    portal_uid = config.site_root_uid
    if item["@type"] == "Plone Site":
        item["UID"] = portal_uid
    return item


def processors() -> List[types.ExportImportHelper]:
    """Return processors to be used by the importer."""
    processors = []
    funcs = [
        process_id,
        process_language,
        process_root_uid,
    ]
    for func in funcs:
        processors.append(
            types.ExportImportHelper(
                func=func,
                name=func.__name__,
                description=func.__doc__,
            )
        )
    return processors


def get_obj_instance(item: dict, config: types.ImporterConfig) -> DexterityContent:
    # Get container
    container = get_parent_from_item(item)
    # Check if we will update an item
    update_existing = item["id"] in container
    if update_existing:
        new = container[item["id"]]
        logger.debug(f"{config.logger_prefix} Will update {new}")
    else:
        new = unrestricted_construct_instance(item["@type"], container, item["id"])
        logger.debug(f"{config.logger_prefix} Created {new}")
    return new


def update_uid(item: dict, obj: DexterityContent) -> DexterityContent:
    """Set UID from data on the new object."""
    uuid = item.get("UID")
    if not uuid or uuid == settings.SITE_ROOT_UID:
        return obj.UID()
    setattr(obj, "_plone.uuid", uuid)
    obj.reindexObject(idxs=["UID"])
    return obj


def update_constrains(item: dict, obj: DexterityContent) -> DexterityContent:
    """Update constrains in object."""
    item_id = item["@id"]
    item_constrains = item.get(settings.SERIALIZER_CONSTRAINS_KEY)
    if not item_constrains:
        return obj
    constrains = ISelectableConstrainTypes(obj, None)
    if constrains:
        constrains.setConstrainTypesMode(ENABLED)
        for key, func in (
            ("locally_allowed_types", constrains.setLocallyAllowedTypes),
            ("immediately_addable_types", constrains.setImmediatelyAddableTypes),
        ):
            value = item_constrains.get(key)
            try:
                func(value)
            except ValueError:
                logger.warning(f"Cannot set {key} on {item_id}", exc_info=True)

    return obj


def update_review_state(item: dict, obj: DexterityContent) -> DexterityContent:
    """Update review state on the object."""
    portal_workflow = api.portal.get_tool("portal_workflow")
    review_state = item.get("review_state")
    chain = portal_workflow.getChainFor(obj)
    if chain and review_state:
        try:
            api.content.transition(to_state=review_state, obj=obj)
        except api.exc.InvalidParameterError as exc:
            logger.info(exc)
    return obj


def update_workflow_history(item: dict, obj: DexterityContent) -> DexterityContent:
    """Update workflow history on the object."""
    workflow_history = item.get("workflow_history", {})
    result = {}
    for key, value in workflow_history.items():
        # The time needs to be deserialized
        for history_item in value:
            if "time" in history_item:
                history_item["time"] = parse_date(history_item["time"])
        result[key] = value
    if result:
        obj.workflow_history = PersistentMapping(result.items())
    return obj


def update_dates(item: dict, obj: DexterityContent) -> DexterityContent:
    """Update creation and modification dates on the object."""
    created = item.get("created", item.get("creation_date", None))
    modified = item.get("modified", item.get("modification_date", None))
    idxs = []
    for attr, idx, value in (
        ("creation_date", "created", created),
        ("modification_date", "modified", modified),
    ):
        value = parse_date(value)
        if not value:
            continue
        setattr(obj, attr, value)
        idxs.append(idx)
    obj.reindexObject(idxs=idxs)
    return obj


def updaters() -> List[types.ExportImportHelper]:
    """Return updaters to be used by the importer."""
    updaters = []
    funcs = [
        update_uid,
        update_constrains,
        update_review_state,
        update_workflow_history,
        update_dates,
    ]
    for func in funcs:
        updaters.append(
            types.ExportImportHelper(
                func=func,
                name=func.__name__,
                description=func.__doc__,
            )
        )
    return updaters


def set_default_page(uid: str, value: dict) -> bool:
    """Set default page on object with the given uid."""
    obj = object_from_uid(uid)
    if not obj:
        logger.info(f"{uid}: Could not find object to set default page")
        return False
    obj_path = get_obj_path(obj)
    default_page_uuid = value.get("default_page_uuid", None)
    default_page_obj = object_from_uid(default_page_uuid) if default_page_uuid else None
    default_page = (
        default_page_obj.getId()
        if default_page_obj
        else value.get("default_page", None)
    )
    status = False
    if default_page not in obj:
        logger.info(f"{obj_path}: Default page '{default_page}' not found")
    elif default_page == "index_html":
        # index_html is automatically used as default page
        logger.debug(f"{obj_path}: Using {default_page}")
        status = True
    else:
        obj.setDefaultPage(default_page)
        logger.debug(f"{obj_path}: Set default page {default_page}")
        status = True
    return status


def set_local_roles(uid: str, value: dict) -> bool:
    """Set local roles from metadata."""
    obj = object_from_uid(uid)
    if not obj:
        logger.info(f"{uid}: Could not find object to set local roles")
        return False
    obj_path = get_obj_path(obj)
    local_roles = value.get("local_roles")
    if local_roles:
        for userid in local_roles:
            obj.manage_setLocalRoles(userid=userid, roles=local_roles[userid])
        logger.debug(f"{obj_path}: Set local roles {local_roles}")
    block = value.get("block")
    if block:
        obj.__ac_local_roles_block__ = 1
        logger.debug(f"{obj_path}: Disables acquisition of local roles")
    return True


def set_ordering(uid: str, value: int) -> bool:
    obj = object_from_uid(uid)
    if not obj:
        logger.info(f"{uid}: Could not find object to set ordering")
        return False
    ordered = get_parent_ordered(obj)
    status = False
    if ordered:
        ordered.moveObjectToPosition(obj.getId(), value)
        status = True
    return status


def metadata_setters() -> List[types.ExportImportHelper]:
    helpers = []
    funcs = [
        (set_default_page, "default_page"),
        (set_ordering, "ordering"),
        (set_local_roles, "local_roles"),
    ]
    for func, attr in funcs:
        helpers.append(
            types.ExportImportHelper(
                func=func,
                name=attr,
                description=func.__doc__,
            )
        )
    return helpers


def recatalog_uids(uids: List[str], idxs: List[str]):
    logger.info(f"Reindexing catalog indexes {', '.join(idxs)} for {len(uids)} objects")
    for uid in uids:
        obj = object_from_uid(uid)
        if not obj:
            continue
        obj.reindexObject(idxs)
