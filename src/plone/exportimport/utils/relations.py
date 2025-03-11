from .content.core import get_all_fields
from .content.core import get_obj_path
from operator import itemgetter
from plone import api
from plone.dexterity.content import DexterityContent
from Products.CMFPlone import relationhelper
from typing import List
from z3c.relationfield.index import RelationCatalog
from z3c.relationfield.interfaces import IRelationChoice
from z3c.relationfield.interfaces import IRelationList
from zc.relation.interfaces import ICatalog
from zope.component import getUtility


RELATIONS_TO_IGNORE = [
    "translationOf",  # old LinguaPlone
    "internal_references",  # obsolete
    "link",  # tab
    "link1",  # extranetfrontpage
    "link2",  # extranetfrontpage
    "link3",  # extranetfrontpage
    "link4",  # extranetfrontpage
    "box3_link",  # shopfrontpage
    "box1_link",  # shopfrontpage
    "box2_link",  # shopfrontpage
    "source",  # remotedisplay
    "internally_links_to",  # DoormatReference
]


def relation_fields_for_content(obj: DexterityContent) -> dict:
    """Return a dictionary with relation fields for a content."""
    items = get_all_fields(obj, [IRelationChoice, IRelationList])
    return items


def get_relation_catalog() -> RelationCatalog:
    """Return the relation catalog for a site."""
    relation_catalog = getUtility(ICatalog)
    return relation_catalog


def _relation_with_debug_information(rel: dict) -> dict:
    """Process the relation data and add debug information to it."""
    from_obj = api.content.get(UID=rel["from_uuid"])
    to_obj = api.content.get(UID=rel["to_uuid"])
    rel["from_path"] = get_obj_path(from_obj, True)
    rel["to_path"] = get_obj_path(to_obj, True)
    return rel


def _should_export_relation(rel: dict, include_linkintegrity: bool) -> bool:
    """Check if relation data should be exported."""
    is_linkintegrity = rel["from_attribute"] == "isReferencing"
    from_uuid = rel.get("from_uuid")
    to_uuid = rel.get("to_uuid")
    status = bool(from_uuid and to_uuid)
    return status and (not is_linkintegrity or include_linkintegrity)


def _relation_sort_key(rel: dict) -> tuple:
    return rel.get("from_uuid"), rel.get("from_attribute"), rel.get("to_uuid")


def get_relations(
    debug: bool = False, include_linkintegrity: bool = True
) -> List[dict]:
    results = []
    all_relations: List[dict] = relationhelper.get_all_relations()
    for rel in all_relations:
        if not _should_export_relation(rel, include_linkintegrity):
            continue
        if debug:
            rel = _relation_with_debug_information(rel)
        results.append(rel)
    return sorted(results, key=_relation_sort_key)


def _prepare_relations_to_import(data: List[dict]) -> List[dict]:
    """Prepare relations data to be imported into a Plone site.

    - Filter relations that should not be imported.
    - Sort relations by uuid and relation attribute.
    """
    relations = []
    # Filter data
    for rel in data:
        if rel["from_attribute"] in RELATIONS_TO_IGNORE:
            continue
        from_obj = api.content.get(UID=rel["from_uuid"])
        to_obj = api.content.get(UID=rel["to_uuid"])
        if from_obj and to_obj:
            relations.append(rel)
    all_fixed_relations = sorted(
        relations, key=itemgetter("from_uuid", "from_attribute")
    )
    return all_fixed_relations


def set_relations(data: List[dict]) -> List[dict]:
    """Import relations listed in data into the current Plone site."""
    all_fixed_relations = _prepare_relations_to_import(data)
    relationhelper.purge_relations()
    relationhelper.cleanup_intids()
    relationhelper.restore_relations(all_relations=all_fixed_relations)
    return all_fixed_relations
