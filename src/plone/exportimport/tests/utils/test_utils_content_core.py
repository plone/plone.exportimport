from plone import api
from plone.exportimport.utils.content import core

import pytest


class TestUtilsContentCore:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.portal = portal
        with api.env.adopt_roles(["Manager"]):
            self.folder = api.content.create(
                container=portal,
                id="a-folderish",
                type="Document",
                title="A Folderish document",
                description="A simple folder",
            )
            self.link = api.content.create(
                container=self.folder,
                id="a-link",
                type="Link",
                title="Link Content",
                description="A simple folder",
                remoteUrl="https://plone.org/",
            )
        self.folder_uid = core.get_uid(self.folder)
        self.link_uid = core.get_uid(self.link)

    @pytest.mark.parametrize(
        "obj_path,expected",
        [
            ["/", True],
            ["/a-folderish", True],
            ["/a-folderish/a-link", False],
        ],
    )
    def test_is_folderish(self, obj_path: str, expected: bool):
        func = core.is_folderish
        content = api.content.get(path=obj_path)
        assert func(content) is expected

    @pytest.mark.parametrize(
        "obj_path,expected",
        [
            ["/", True],
            ["/a-folderish", False],
            ["/a-folderish/a-link", False],
        ],
    )
    def test_is_site_root(self, obj_path: str, expected: bool):
        func = core.is_site_root
        content = api.content.get(path=obj_path)
        assert func(content) is expected

    @pytest.mark.parametrize(
        "obj_path,length",
        [
            ["/", 15],
            ["/a-folderish", 32],
            ["/a-folderish/a-link", 32],
        ],
    )
    def test_get_uid(self, obj_path: str, length: int):
        func = core.get_uid
        content = api.content.get(path=obj_path)
        result = func(content)
        assert isinstance(result, str)
        assert len(result) == length

    def test_object_from_uid(self):
        from plone.dexterity.content import DexterityContent

        func = core.object_from_uid
        result = func(self.folder_uid)
        assert isinstance(result, DexterityContent)
        assert result.portal_type == "Document"

    def test_get_portal_languages(self):
        from plone.exportimport import types

        func = core.get_portal_languages
        result = func()
        assert isinstance(result, types.PortalLanguages)
        assert result.default == "en"

    @pytest.mark.parametrize(
        "obj_path,parent_id",
        [
            ["/", None],
            ["/a-folderish", "plone"],
            ["/a-folderish/a-link", "a-folderish"],
        ],
    )
    def test_get_parent_ordered(self, obj_path: str, parent_id: str):
        func = core.get_parent_ordered
        content = api.content.get(path=obj_path)
        result = func(content)
        if parent_id:
            assert result.id == parent_id
        else:
            assert result is None

    def test_get_all_fields(self):
        func = core.get_all_fields
        results = func(self.link)
        assert isinstance(results, dict)
        assert "title" in results
        assert "remoteUrl" in results

    def test_get_all_fields_filter_filter(self):
        from zope.schema.interfaces import ITuple

        func = core.get_all_fields
        # Filter by ITuple interface
        results = func(self.link, [ITuple])
        assert isinstance(results, dict)
        assert "subjects" in results
        assert "title" not in results
        assert "remoteUrl" not in results
