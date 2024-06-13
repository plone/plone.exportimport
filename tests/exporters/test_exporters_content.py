from plone import api
from plone.exportimport import interfaces
from plone.exportimport.exporters import content
from zope.component import getAdapter
from zope.component.hooks import setSite

import pytest


@pytest.fixture
def local_permissions() -> dict:
    return {
        "35661c9bb5be42c68f665aa1ed291418": {
            "name": "plone.app.contenttypes: Add Image",
            "roles": ["Manager"],
            "acquire": False,
        },
        "e7359727ace64e609b79c4091c38822a": {
            "name": "plone.app.contenttypes: Add Image",
            "roles": ["Member"],
            "acquire": False,
        },
    }


@pytest.fixture()
def portal_permissions(portal, local_permissions):
    """Plone portal with permissions set on some content."""
    setSite(portal)
    for uid, permission in local_permissions.items():
        obj = api.content.get(UID=uid)
        obj.manage_permission(
            permission["name"], roles=permission["roles"], acquire=permission["acquire"]
        )
    yield portal


class TestExporterContent:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.src_portal = portal
        self.exporter = content.ContentExporter(portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.src_portal, interfaces.INamedExporter, "plone.exporter.content"
        )
        assert isinstance(adapter, content.ContentExporter)

    def test_output_is_list(self, export_path):
        exporter = self.exporter
        result = exporter.export_data(base_path=export_path)
        assert isinstance(result, list)

    @pytest.mark.parametrize(
        "path",
        [
            "content/__metadata__.json",
            "content/3e0dd7c4b2714eafa1d6fc6a1493f953/data.json",
            "content/70844f7bec1843b8ab2796c972c9ebfe/data.json",
            "content/90b11c863598495ba699b22ca76b1041/data.json",
            "content/7c1393f615c4447c80db0d784390c5b7/data.json",
            "content/5d77cd5686184ec49ab077017b1fbc3a/data.json",
            "content/e7359727ace64e609b79c4091c38822a/data.json",
            "content/45b0b46f17104a7b8fa7bb94d3dd5bd9/data.json",
            "content/35661c9bb5be42c68f665aa1ed291418/data.json",
            "content/plone_site_root/data.json",
        ],
    )
    def test_content_is_exported(self, export_path, paths_as_relative, path):
        exporter = self.exporter
        result = paths_as_relative(
            export_path, exporter.export_data(base_path=export_path)
        )
        assert isinstance(result, list)
        assert path in result
        assert (export_path / path).exists() is True
        assert (export_path / path).is_file() is True


class TestExporterContentMetadata:
    @pytest.fixture(autouse=True)
    def _init(self, portal, export_path):
        exporter = content.ContentExporter(portal)
        exporter.export_data(base_path=export_path)
        self.base_path = export_path

    @pytest.mark.parametrize(
        "key,instance",
        [
            ("_blob_files_", list),
            ("_data_files_", list),
            ("default_page", dict),
            ("local_permissions", dict),
            ("local_roles", dict),
            ("ordering", dict),
        ],
    )
    def test_content_metadata(self, load_json, key, instance):
        metadata = load_json(self.base_path, "content/__metadata__.json")
        assert key in metadata
        assert isinstance(metadata[key], instance)


class TestExporterLocalPermissions:
    @pytest.fixture(autouse=True)
    def _init(self, portal_permissions, load_json, export_path):
        exporter = content.ContentExporter(portal_permissions)
        exporter.export_data(base_path=export_path)
        self.base_path = export_path
        self.permissions_metadata = load_json(
            self.base_path, "content/__metadata__.json"
        )["local_permissions"]

    def test_local_permission_is_defined(self, local_permissions):
        for uid, item in local_permissions.items():
            assert uid in self.permissions_metadata
            assert item["name"] in self.permissions_metadata[uid]
            permission = self.permissions_metadata[uid][item["name"]]
            assert permission["roles"] == item["roles"]
            assert permission["acquire"] == item["acquire"]


class TestExporterMultilingual:

    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual, export_path):
        self.src_portal = portal_multilingual
        self.exporter = content.ContentExporter(portal_multilingual)

    def test_content_is_exported(self, export_path, paths_as_relative, load_json):
        exporter = self.exporter
        paths_as_relative(export_path, exporter.export_data(base_path=export_path))

        metadata = load_json(
            export_path, "content/20737423549c43a88488242ec629e087/data.json"
        )
        assert "language" in metadata
        assert metadata["language"] == "es"
