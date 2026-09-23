from plone.exportimport.cli import exporter_cli

import pytest


class TestExporterCLI:
    @pytest.fixture(autouse=True)
    def _init(self, portal, dummy_content, run_cli, zopeconf, export_path, load_json):
        self.portal = portal
        self.uid = dummy_content.UID()
        run_cli(
            exporter_cli,
            ["plone-exporter", str(zopeconf), portal.getId(), str(export_path)],
        )
        self.data = load_json(export_path, f"content/{self.uid}/data.json")

    def test_content_exported(self):
        assert self.data["@type"] == "DummyContent"
        assert self.data["UID"] == self.uid

    @pytest.mark.parametrize(
        "field,expected",
        [
            ["secure_field", "A secure value"],
            ["secure_setting", False],
        ],
    )
    def test_protected_field_value(self, field: str, expected):
        assert field in self.data
        assert self.data[field] == expected


class TestExporterCLISiteRoot:
    @pytest.fixture(autouse=True)
    def _init(self, site_settings, run_cli, zopeconf, export_path, load_json):
        run_cli(
            exporter_cli,
            ["plone-exporter", str(zopeconf), site_settings.getId(), str(export_path)],
        )
        self.data = load_json(export_path, "content/plone_site_root/data.json")

    @pytest.mark.parametrize(
        "field,expected",
        [
            ["secure_field", "A secure site value"],
            ["secure_setting", False],
        ],
    )
    def test_protected_behavior_field_value(self, field: str, expected):
        assert field in self.data
        assert self.data[field] == expected
