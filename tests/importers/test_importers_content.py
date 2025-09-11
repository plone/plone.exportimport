from plone import api
from plone.exportimport import interfaces
from plone.exportimport.importers import content
from zope.component import getAdapter

import pytest


class TestImporterContent:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual_content):
        self.portal = portal_multilingual_content
        self.importer = content.ContentImporter(self.portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.portal, interfaces.INamedImporter, "plone.importer.content"
        )
        assert isinstance(adapter, content.ContentImporter)

    def test_output_is_str(self, multilingual_import_path):
        importer = self.importer
        result = importer.import_data(base_path=multilingual_import_path)
        assert isinstance(result, str)
        assert result == "ContentImporter: Imported 19 objects"

    def test_empty_import_path(self, empty_import_path):
        importer = self.importer
        result = importer.import_data(base_path=empty_import_path)
        assert isinstance(result, str)
        assert result == "ContentImporter: No data to import"


class TestImporterLocalPermissions:
    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path):
        self.portal = portal
        importer = content.ContentImporter(portal)
        importer.import_data(base_path=base_import_path)

    @pytest.mark.parametrize(
        "uid,permission_name,roles",
        [
            [
                "35661c9bb5be42c68f665aa1ed291418",
                "plone.app.contenttypes: Add Image",
                ["Manager"],
            ],
            [
                "e7359727ace64e609b79c4091c38822a",
                "plone.app.contenttypes: Add Image",
                ["Member"],
            ],
        ],
    )
    def test_permission_is_set(self, uid, permission_name, roles):
        from plone.exportimport.utils.content import object_from_uid

        content = object_from_uid(uid)
        for role in roles:
            all_permissions = [p["name"] for p in content.permissionsOfRole(role)]
            assert permission_name in all_permissions


class TestImporterParent:
    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path):
        self.portal = portal
        importer = content.ContentImporter(portal)
        importer.import_data(base_path=base_import_path)

    @pytest.mark.parametrize(
        "data,path",
        [
            [
                {"@id": "/", "@type": "Plone Site"},
                "/",
            ],
            [
                {"@id": "/bar"},
                "/plone",
            ],
            [
                {"@id": "/bar/2025.png"},
                "/plone/bar",
            ],
            [
                {"@id": "/bar/2025.png/parent-is-not-folderish"},
                None,
            ],
            [
                {"@id": "/foo/not-yet-created"},
                "/plone/foo",
            ],
            [
                {"@id": "/spaghetti/bolognese"},
                None,
            ],
        ],
    )
    def test_get_parent_from_item(self, data, path):
        from plone.exportimport.utils.content.import_helpers import get_parent_from_item

        parent = get_parent_from_item(data)
        found_path = parent.absolute_url_path() if parent is not None else None
        assert found_path == path


class TestImporterConstrains:
    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path):
        self.portal = portal
        importer = content.ContentImporter(portal)
        importer.import_data(base_path=base_import_path)

    @pytest.mark.parametrize(
        "uid,method,types",
        [
            [
                "35661c9bb5be42c68f665aa1ed291418",
                "getImmediatelyAddableTypes",
                ["Image"],
            ],
            [
                "35661c9bb5be42c68f665aa1ed291418",
                "getLocallyAllowedTypes",
                ["Document", "Image"],
            ],
        ],
    )
    def test_constrain_is_set(self, uid, method, types):
        from plone.base.interfaces.constrains import ISelectableConstrainTypes
        from plone.exportimport.utils.content import object_from_uid

        content = object_from_uid(uid)
        with api.env.adopt_roles(["Manager", "Site Administrator"]):
            behavior = ISelectableConstrainTypes(content, None)
            constrains = getattr(behavior, method)()
        for type_ in types:
            assert type_ in constrains


class TestImporterOrdering:
    """Test the ordering of imported items is correctly applied"""

    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path):
        self.portal = portal
        importer = content.ContentImporter(portal)
        importer.import_data(base_path=base_import_path)
        # Search for the items at Portal root ordering by position in parent
        brains = api.content.find(
            context=portal, depth=1, sort_on="getObjPositionInParent"
        )
        self.items: list[str] = [b.UID for b in brains]

    @pytest.mark.parametrize(
        "uid,idx",
        [
            ["3e0dd7c4b2714eafa1d6fc6a1493f953", 0],
            ["70844f7bec1843b8ab2796c972c9ebfe", 1],
            ["e7359727ace64e609b79c4091c38822a", 2],
        ],
    )
    def test_ordering_preserved(self, uid: str, idx: int):
        """Test that each item is at the expected index within the Portal root."""
        items: list[str] = self.items
        assert items.index(uid) == idx
