from plone import api
from plone.exportimport.cli import importer_cli
from plone.exportimport.testing.content.dummy import IDummySettings

import pytest


class TestImporterCLI:
    @pytest.fixture(autouse=True)
    def _init(self, portal, run_cli, zopeconf, cli_import_path):
        self.portal = portal
        run_cli(
            importer_cli,
            [
                "plone-importer",
                str(zopeconf),
                portal.getId(),
                str(cli_import_path),
                "--quiet",
            ],
        )

    def test_content_imported(self):
        content = api.content.get(UID="0e1d9d4a2c3b4f5e8a7b6c5d4e3f2a1b")
        assert content is not None
        assert content.portal_type == "DummyContent"

    @pytest.mark.parametrize(
        "field,expected",
        [
            ["secure_field", "A secure value"],
            ["secure_setting", False],
        ],
    )
    def test_protected_field_value(self, field: str, expected):
        content = api.content.get(UID="0e1d9d4a2c3b4f5e8a7b6c5d4e3f2a1b")
        assert getattr(content, field) == expected

    @pytest.mark.parametrize(
        "field,expected",
        [
            ["secure_field", "A secure site value"],
            ["secure_setting", False],
        ],
    )
    def test_protected_behavior_field_value(self, field: str, expected):
        settings = IDummySettings(self.portal)
        assert getattr(settings, field) == expected
