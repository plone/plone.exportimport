from .blocks import parse_blocks
from .core import get_parent_ordered
from .core import get_uid
from .core import is_folderish
from .revisions import revision_history
from Acquisition import aq_base
from Acquisition import aq_parent
from plone import api
from plone.app.discussion.interfaces import IConversation
from plone.base.interfaces.constrains import ENABLED
from plone.base.interfaces.constrains import ISelectableConstrainTypes
from plone.dexterity.content import DexterityContent
from plone.exportimport import settings
from plone.exportimport import types
from plone.exportimport.utils.relations import relation_fields_for_content
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.converters import json_compatible
from Products.CMFEditions.ZVCStorageTool import ShadowHistory
from typing import Callable
from typing import List
from zope.component import getMultiAdapter

import json


def get_serializer(obj, request) -> Callable:
    return getMultiAdapter((obj, request), ISerializeToJson)


def rewrite_site_root(item: dict, portal_url: str) -> dict:
    """Fix site root"""
    item_str = json.dumps(item)
    replacements = [
        (f'"@id": "{portal_url}/', '"@id": "/'),
        (f'"@id": "{portal_url}"', '"@id": "/"'),
        (f'"@parent": "{portal_url}/', '"@parent": "/'),
        (f'"@parent": "{portal_url}"', '"@parent": "/"'),
        (f'"url": "{portal_url}/', '"url": "/'),
    ]
    for pattern, replace in replacements:
        item_str = item_str.replace(pattern, replace)
    return json.loads(item_str)


def cleanup_export_data(item: dict, config: types.ExporterConfig) -> dict:
    """Update serialized data to optimize use with exportimport.

    1. Drop unused data
    2. Fix site root

    """
    # 1. Drop unused data
    item.pop("@components", None)
    item.pop("next_item", None)
    item.pop("batching", None)
    item.pop("items", None)
    item.pop("previous_item", None)
    item.pop("immediatelyAddableTypes", None)
    item.pop("locallyAllowedTypes", None)

    # 2. Fix site root
    item = rewrite_site_root(item, config.site.absolute_url())
    return item


def fix_id(item: dict, obj: DexterityContent, config: types.ExporterConfig) -> dict:
    """Fix the @id in an serialized object.

    Mostly relevant for collections, where the id is set to “@@export-content”
    because of the HypermediaBatch in plone.restapi
    """
    obj_url = obj.absolute_url()
    parent_url = aq_parent(obj).absolute_url()
    if item["@id"] != obj_url:
        item["@id"] = obj_url
    if obj.portal_type == "Plone Site":
        # To avoid a conflict between @id and id
        item["@id"] = f"/{item['id']}"
    if "@id" in item.get("parent", {}) and item["parent"]["@id"] != parent_url:
        item["parent"]["@id"] = parent_url
    return item


def fix_parent_uid(
    item: dict, obj: DexterityContent, config: types.ExporterConfig
) -> dict:
    parent = aq_parent(obj)
    if item.get("parent"):
        item["parent"]["UID"] = get_uid(parent)
    return item


def fix_relation_fields(
    item: dict, obj: DexterityContent, config: types.ExporterConfig
) -> dict:
    """Remove relation fields."""
    for fieldname in relation_fields_for_content(obj):
        item.pop(fieldname, None)
    return item


def fix_blocks(item: dict, obj: DexterityContent, config: types.ExporterConfig) -> dict:
    """Fix blocks information."""
    blocks = item.get("blocks", {})
    if blocks:
        blocks = parse_blocks(blocks)
        item["blocks"] = blocks
    return item


def fix_language(
    item: dict, obj: DexterityContent, config: types.ExporterConfig
) -> dict:
    """Fix language information."""
    placeholder = settings.PLACEHOLDERS_LANGUAGE
    default_portal_language = config.site.language
    if isinstance(item.get("language", {}), str):
        lang = placeholder
    else:
        token = item.get("language", {}).get("token", placeholder)
        lang = placeholder if token == default_portal_language else token
    item["language"] = lang
    return item


def fix_root_uid(
    item: dict, obj: DexterityContent, config: types.ExporterConfig
) -> dict:
    """Fix references to site root uid."""
    item_str = json.dumps(item)
    item_str = item_str.replace(config.site_root_uid, settings.SITE_ROOT_UID)
    return json.loads(item_str)


def add_constrains_info(obj: DexterityContent, config: types.ExporterConfig) -> dict:
    """Return constrains info for an object."""
    key = settings.SERIALIZER_CONSTRAINS_KEY
    results = {key: {}}
    constrains = ISelectableConstrainTypes(obj, None)
    if constrains and constrains.getConstrainTypesMode() == ENABLED:
        results[key] = {
            "locally_allowed_types": constrains.getLocallyAllowedTypes(),
            "immediately_addable_types": constrains.getImmediatelyAddableTypes(),
        }
    return results


def add_workflow_history(obj: DexterityContent, config: types.ExporterConfig) -> dict:
    """Return workflow history for an object."""
    results = {"workflow_history": {}}
    workflow_history = getattr(aq_base(obj), "workflow_history", {})
    for workflow, history in workflow_history.items():
        results["workflow_history"][workflow] = json_compatible(history)
    return results


def add_conversation(obj: DexterityContent, config: types.ExporterConfig) -> dict:
    """Return conversation (comments) for an item."""
    key = "exportimport.conversation"
    request = config.request
    results = {key: []}
    conversation = IConversation(obj, None)
    if conversation:
        serializer = get_serializer(conversation, request)
        data = serializer()
        results[key] = data["items"] if data else []
    return results


def add_revisions_history(obj: DexterityContent, config: types.ExporterConfig) -> dict:
    """Return revisions history for an object."""
    item = {"exportimport.versions": {}}
    serializer = config.serializer
    repo_tool = api.portal.get_tool("portal_repository")
    history = revision_history(obj)
    if not history or len(history) == 1:
        return item
    history_metadata = repo_tool.getHistoryMetadata(obj)
    last_entry = (
        history_metadata.retrieve(-1)
        if isinstance(history_metadata, ShadowHistory)
        else history_metadata[-1]
    )["metadata"]
    # don't export the current version again
    for history_item in history[1:]:
        version_id = history_item["version_id"]
        item_version = serializer(include_items=False, version=version_id)
        item_version = cleanup_export_data(item_version, config)
        item["exportimport.versions"][version_id] = item_version
    # current changenote
    item["changeNote"] = last_entry["sys_metadata"]["comment"]
    item["changeActor"] = last_entry["sys_metadata"]["principal"]
    return item


def default_page_info(
    obj: DexterityContent, config: types.ExporterConfig
) -> dict | None:
    """Default page for a given obj.

    We use a simplified method to only get index_html
    and the property default_page on the object.
    We don't care about other cases
    - obj is folderish, check for a index_html in it
    - Check attribute 'default_page'
    """
    result = {}
    if not is_folderish(obj):
        return None
    default_page = (
        "index_html"
        if "index_html" in obj
        else getattr(aq_base(obj), "default_page", [])
    )
    default_page_obj = (
        obj.get(default_page) if default_page and default_page in obj else None
    )
    if default_page_obj:
        default_page_uid = get_uid(default_page_obj)
        result = {
            "default_page": default_page,
            "default_page_uuid": default_page_uid,
        }
    return result if result else None


def get_position_in_parent(
    obj: DexterityContent, config: types.ExporterConfig
) -> int | None:
    ordered = get_parent_ordered(obj)
    return ordered.getObjectPosition(obj.getId()) if ordered else None


def get_local_roles(obj: DexterityContent, config: types.ExporterConfig) -> dict | None:
    item = {}
    local_roles = None
    block = None
    obj = aq_base(obj)
    if getattr(obj, "__ac_local_roles__", None) is not None:
        local_roles = obj.__ac_local_roles__
    if getattr(obj, "__ac_local_roles_block__", False):
        block = obj.__ac_local_roles_block__
    if local_roles or block:
        if local_roles:
            item["local_roles"] = local_roles
        if block:
            item["block"] = 1
    return item if item else None


def fixers() -> List[types.ExportImportHelper]:
    fixers = []
    funcs = [
        fix_relation_fields,
        fix_id,
        fix_parent_uid,
        fix_blocks,
        fix_language,
        fix_root_uid,
    ]
    for func in funcs:
        fixers.append(
            types.ExportImportHelper(
                func=func,
                name=func.__name__,
                description=func.__doc__,
            )
        )
    return fixers


def enrichers() -> List[types.ExportImportHelper]:
    enrichers = []
    funcs = [
        add_constrains_info,
        add_workflow_history,
        add_revisions_history,
        add_conversation,
    ]
    for func in funcs:
        enrichers.append(
            types.ExportImportHelper(
                func=func,
                name=func.__name__,
                description=func.__doc__,
            )
        )
    return enrichers


def cleaners() -> List[types.ExportImportHelper]:
    cleaners = []
    funcs = [
        cleanup_export_data,
    ]
    for func in funcs:
        cleaners.append(
            types.ExportImportHelper(
                func=func,
                name=func.__name__,
                description=func.__doc__,
            )
        )
    return cleaners


def metadata_helpers() -> List[types.ExportImportHelper]:
    helpers = []
    funcs = [
        (default_page_info, "default_page"),
        (get_position_in_parent, "ordering"),
        (get_local_roles, "local_roles"),
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
