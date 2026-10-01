from plone import api
from plone.exportimport.exporters import get_exporter

import argparse
import pytest

# UIDs from tests/_resources/multilingual_import
UIDS = {
    "/es": "f98b033fa8ce46f487ca8923ddae7480",
    "/es/a-folderish": "1cbf4ae73c74459485d3fd6cb9714e43",
    "/es/a-folderish/a-link": "ddb27456033d4b86a78f3ec783874b63",
    "/es/a-folderish/a-page": "cecc6f7007344d3cbac68f1da4bd084a",
    "/es/a-folderish/another-page": "85a60611c2744e7abe53e3f356df236a",
    "/es/recursos": "20737423549c43a88488242ec629e087",
    "/en/a-folderish/a-page": "f40d3a236b464aa487b715adf3c0be92",
    "/en/a-folderish/another-page": "fbcd98e2d1a741e2a90b8f0389203530",
    "/de/a-folderish/a-page": "2be023c76b3e4e0aa9908c70f19a14df",
}


def _options(portal, *paths: str) -> argparse.Namespace:
    """Options for a partial export of the given site relative paths."""
    site_path = "/".join(portal.getPhysicalPath())
    query = {"path": {"query": [f"{site_path}{path}" for path in paths]}}
    return argparse.Namespace(query=query)


@pytest.fixture()
def export_partial(portal_multilingual, export_path, load_json):
    """Export the site, limited to the given paths, and return the data."""

    def func(*paths: str) -> dict:
        options = _options(portal_multilingual, *paths) if paths else None
        get_exporter(portal_multilingual).export_site(export_path, options=options)
        names = ("relations", "translations", "discussions", "portlets", "redirects")
        data = {name: load_json(export_path, f"{name}.json") for name in names}
        metadata = load_json(export_path, "content/__metadata__.json")
        data["content"] = metadata["_data_files_"]
        return data

    return func


class TestPartialExportContent:
    def test_only_subtree_is_exported(self, export_partial):
        data = export_partial("/es")
        expected = {
            f"{UIDS[path]}/data.json"
            for path in UIDS
            if path == "/es" or path.startswith("/es/")
        }
        assert set(data["content"]) == expected

    def test_site_root_is_not_exported(self, export_partial):
        data = export_partial("/es/a-folderish")
        assert "plone_site_root/data.json" not in data["content"]

    def test_multiple_paths(self, export_partial):
        data = export_partial("/en/a-folderish/a-page", "/es/a-folderish/another-page")
        assert set(data["content"]) == {
            f"{UIDS['/en/a-folderish/a-page']}/data.json",
            f"{UIDS['/es/a-folderish/another-page']}/data.json",
        }

    def test_full_export_without_query(self, export_partial):
        data = export_partial()
        assert "plone_site_root/data.json" in data["content"]


class TestPartialExportRelations:
    def test_relation_inside_export_is_kept(self, export_partial):
        data = export_partial("/es")
        assert [(rel["from_uuid"], rel["to_uuid"]) for rel in data["relations"]] == [
            (UIDS["/es/a-folderish/another-page"], UIDS["/es/a-folderish/a-page"])
        ]

    def test_relation_to_content_not_exported_is_dropped(self, export_partial):
        data = export_partial("/es/a-folderish/another-page")
        assert data["relations"] == []

    def test_full_export_keeps_all_relations(self, export_partial):
        data = export_partial()
        assert len(data["relations"]) == 3


class TestPartialExportTranslations:
    def test_group_with_one_exported_item_is_dropped(self, export_partial):
        data = export_partial("/es")
        assert data["translations"] == []

    def test_group_keeps_only_exported_items(self, export_partial):
        data = export_partial("/en/a-folderish/a-page", "/de/a-folderish/a-page")
        assert data["translations"] == [
            {
                "canonical": UIDS["/en/a-folderish/a-page"],
                "translations": {"de": UIDS["/de/a-folderish/a-page"]},
            }
        ]


class TestPartialExportDiscussions:
    def test_discussions_on_exported_content(self, export_partial):
        data = export_partial("/es/a-folderish/another-page")
        assert list(data["discussions"]) == [UIDS["/es/a-folderish/another-page"]]

    def test_no_discussions_outside_export(self, export_partial):
        data = export_partial("/en")
        assert data["discussions"] == {}


class TestPartialExportPortlets:
    def test_full_export_has_site_root_portlets(self, export_partial):
        data = export_partial()
        assert "plone_site_root" in [item["UID"] for item in data["portlets"]]

    def test_site_root_portlets_not_exported(self, export_partial):
        data = export_partial("/es")
        assert "plone_site_root" not in [item["UID"] for item in data["portlets"]]


class TestPartialExportRedirects:
    @pytest.fixture(autouse=True)
    def _rename(self, portal_multilingual):
        site_path = "/".join(portal_multilingual.getPhysicalPath())
        with api.env.adopt_roles(["Manager"]):
            content = api.content.get(path="/es/a-folderish/a-link")
            api.content.rename(obj=content, new_id="renamed-link")
        self.old_path = f"{site_path}/es/a-folderish/a-link"
        self.new_path = f"{site_path}/es/a-folderish/renamed-link"

    def test_redirect_to_exported_content_is_kept(self, export_partial):
        data = export_partial("/es")
        assert data["redirects"][self.old_path] == self.new_path

    def test_redirect_to_content_not_exported_is_dropped(self, export_partial):
        data = export_partial("/en")
        assert self.old_path not in data["redirects"]
