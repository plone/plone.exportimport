from copy import deepcopy
from plone import api
from plone.exportimport.utils import relations as relations_utils

import pytest


@pytest.fixture
def get_existing_relations():
    """Existing relations in a site."""

    def func():
        return relations_utils.get_relations()

    return func


class TestUtilsRelations:
    @pytest.fixture(autouse=True)
    def _init(self, portal, create_example_content):
        from plone.exportimport.utils.content.core import get_obj_path

        self.portal = portal
        example_content = create_example_content(portal)
        contents = {
            get_obj_path(content, True): content for content in example_content.values()
        }
        self.folder = contents["/a-folderish"]
        self.page_01 = contents["/a-folderish/a-page"]
        self.page_02 = contents["/a-folderish/another-page"]
        self.link = contents["/a-folderish/a-link"]

    @pytest.mark.parametrize(
        "obj_path,expected",
        [
            ["/a-folderish", True],
            ["/a-folderish/a-link", False],
            ["/a-folderish/a-page", True],
            ["/a-folderish/another-page", True],
        ],
    )
    def test_relation_fields_for_content(self, obj_path: str, expected: bool):
        func = relations_utils.relation_fields_for_content
        content = api.content.get(path=obj_path)
        results = func(content)
        assert isinstance(results, dict)
        assert ("relatedItems" in results) is expected

    def test_get_relation_catalog(self):
        from z3c.relationfield.index import RelationCatalog

        func = relations_utils.get_relation_catalog
        catalog = func()
        assert isinstance(catalog, RelationCatalog)

    def test_get_relations(self):
        func = relations_utils.get_relations
        results = func()
        assert isinstance(results, list)
        assert len(results) == 1

    @pytest.mark.parametrize(
        "debug,key",
        [
            [False, "from_attribute"],
            [False, "from_uuid"],
            [False, "to_uuid"],
            [True, "from_attribute"],
            [True, "from_uuid"],
            [True, "to_uuid"],
            [True, "from_path"],
            [True, "to_path"],
        ],
    )
    def test_get_relations_key_is_present(self, debug: bool, key: str):
        func = relations_utils.get_relations
        result = func(debug=debug)[0]
        assert isinstance(result, dict)
        assert key in result

    def test_set_relations(self, get_existing_relations):
        func = relations_utils.set_relations
        relations = deepcopy(get_existing_relations())
        total_before = len(relations)
        # Add a new relation to the list
        relations.append(
            {
                "from_uuid": self.page_01.UID(),
                "to_uuid": self.folder.UID(),
                "from_attribute": "relatedItems",
            }
        )
        results = func(relations)
        # Test report
        assert isinstance(results, list)
        assert len(results) == 2
        # Check if we have another relation
        total_after = len(get_existing_relations())
        assert total_after > total_before

    @pytest.mark.parametrize(
        "from_attribute",
        [
            "translationOf",  # old LinguaPlone
            "isReferencing",  # linkintegrity
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
        ],
    )
    def test__prepare_relations_to_import_should_filter_attribute(
        self, from_attribute: str
    ):
        data = [
            {
                "from_uuid": self.folder.UID(),
                "to_uuid": self.page_01.UID(),
                "from_attribute": from_attribute,
            }
        ]
        func = relations_utils._prepare_relations_to_import
        results = func(data)
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "from_uuid",
        [
            "invalid-uuid",
        ],
    )
    def test__prepare_relations_to_import_should_filter_from_uuid(self, from_uuid: str):
        data = [
            {
                "from_uuid": from_uuid,
                "to_uuid": self.page_01.UID(),
                "from_attribute": "relatedItems",
            }
        ]
        func = relations_utils._prepare_relations_to_import
        results = func(data)
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.parametrize(
        "to_uuid",
        [
            "invalid-uuid",
        ],
    )
    def test__prepare_relations_to_import_should_filter_to_uuid(self, to_uuid: str):
        data = [
            {
                "from_uuid": self.folder.UID(),
                "to_uuid": to_uuid,
                "from_attribute": "relatedItems",
            }
        ]
        func = relations_utils._prepare_relations_to_import
        results = func(data)
        assert isinstance(results, list)
        assert len(results) == 0
