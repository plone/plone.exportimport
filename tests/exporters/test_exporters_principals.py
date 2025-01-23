from plone.exportimport import interfaces
from plone.exportimport.exporters import principals
from zope.component import getAdapter

import json
import pytest


class TestExporterPrincipals:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual):
        self.src_portal = portal_multilingual
        self.exporter = principals.PrincipalsExporter(portal_multilingual)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.src_portal, interfaces.INamedExporter, "plone.exporter.principals"
        )
        assert isinstance(adapter, principals.PrincipalsExporter)

    def test_output_is_list(self, export_path):
        exporter = self.exporter
        result = exporter.export_data(base_path=export_path)
        assert isinstance(result, list)

    @pytest.mark.parametrize(
        "path",
        [
            "principals.json",
        ],
    )
    def test_principals_is_exported(self, export_path, paths_as_relative, path):
        exporter = self.exporter
        result = paths_as_relative(
            export_path, exporter.export_data(base_path=export_path)
        )
        assert isinstance(result, list)
        assert path in result
        full_path = export_path / path
        assert full_path.exists() is True
        assert full_path.is_file() is True
        contents = json.loads(full_path.read_bytes())
        assert isinstance(contents, dict)
        assert sorted(contents.keys()) == ["groups", "members"]
        group_ids = [group["groupid"] for group in contents["groups"]]
        assert "Site Administrators" in group_ids
        usernames = [member["username"] for member in contents["members"]]
        assert "joao.silva" in usernames
        for group in contents["groups"]:
            assert group["groups"] == sorted(group["groups"])
            assert group["principals"] == sorted(group["principals"])
            assert group["roles"] == sorted(group["roles"])
        for member in contents["members"]:
            assert member["groups"] == sorted(member["groups"])
            assert member["roles"] == sorted(member["roles"])
