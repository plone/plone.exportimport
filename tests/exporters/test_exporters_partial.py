from pathlib import Path
from plone.exportimport.exporters import content

import pytest

# objects in `base_import`
FOO = "e7359727ace64e609b79c4091c38822a"  # /plone/foo
FOO_BAR = "35661c9bb5be42c68f665aa1ed291418"  # /plone/foo/bar
FOO_ANOTHER = "45b0b46f17104a7b8fa7bb94d3dd5bd9"  # /plone/foo/another-page
BAR = "70844f7bec1843b8ab2796c972c9ebfe"  # /plone/bar
BAR_NEWS = "7c1393f615c4447c80db0d784390c5b7"  # /plone/bar/an-important-news
SITE_ROOT = "plone_site_root"  # /plone

FOO_PATH = "/plone/foo"
FOO_BAR_PATH = "/plone/foo/bar"
BAR_NEWS_PATH = "/plone/bar/an-important-news"


def exported_uids(export_path: Path) -> set:
    """Return the set of UID directories that hold a serialized object."""
    content_dir = Path(export_path) / "content"
    if not content_dir.is_dir():
        return set()
    return {path.parent.name for path in content_dir.glob("*/data.json")}


class TestPartialContentExporter:
    """The content exporter only serializes the explicitly selected objects."""

    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.portal = portal
        self.exporter = content.ContentExporter(portal)

    def test_only_selected_object_is_exported(self, export_path):
        # Only includes the objects specified in the paths list.
        self.exporter.export_data(
            base_path=export_path, paths_list=[FOO_PATH, BAR_NEWS_PATH]
        )
        assert exported_uids(export_path) == {FOO, BAR_NEWS}

    def test_children_objects_are_not_exported(self, export_path):
        # Unless the export paths include the child paths, they are not exported.
        self.exporter.export_data(base_path=export_path, paths_list=[FOO_PATH])
        uids = exported_uids(export_path)
        assert FOO_BAR not in uids
        assert FOO_ANOTHER not in uids

    def test_sibling_objects_are_not_exported(self, export_path):
        # Unless the export paths include the sibling object paths, they are not exported.
        self.exporter.export_data(base_path=export_path, paths_list=[FOO_PATH])
        assert BAR not in exported_uids(export_path)

    def test_parent_and_root_are_not_exported(self, export_path):
        # Selecting a child must not drag in its parent or the site root.
        self.exporter.export_data(base_path=export_path, paths_list=[FOO_BAR_PATH])
        uids = exported_uids(export_path)
        assert uids == {FOO_BAR}
        assert FOO not in uids
        assert SITE_ROOT not in uids

    def test_metadata_lists_only_selected(self, export_path, load_json):
        # The metadata should only list the selected objects.
        self.exporter.export_data(base_path=export_path, paths_list=[FOO_PATH])
        metadata = load_json(export_path, "content/__metadata__.json")
        assert metadata["_data_files_"] == [f"{FOO}/data.json"]

    def test_duplicate_paths_are_written_once(self, export_path, load_json):
        # Even if a path is specified multiple times, it should only be written once.
        self.exporter.export_data(
            base_path=export_path, paths_list=[FOO_PATH, FOO_PATH]
        )
        assert exported_uids(export_path) == {FOO}
        metadata = load_json(export_path, "content/__metadata__.json")
        assert metadata["_data_files_"] == [f"{FOO}/data.json"]

    def test_unknown_path_is_skipped(self, export_path):
        # An unresolvable paths are skipped; valid paths are still exported.
        self.exporter.export_data(
            base_path=export_path, paths_list=["/plone/does-not-exist", FOO_PATH]
        )
        assert exported_uids(export_path) == {FOO}

    def test_empty_paths_list_exports_everything(self, export_path):
        # An empty list behaves like a full export.
        self.exporter.export_data(base_path=export_path, paths_list=[])
        uids = exported_uids(export_path)
        assert {FOO, BAR, FOO_BAR, BAR_NEWS, SITE_ROOT} <= uids
