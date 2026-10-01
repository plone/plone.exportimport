from plone import api
from plone.exportimport.cli import importer_cli
from plone.exportimport.testing.content.dummy import IDummySettings

import pytest
import shutil


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


class TestImporterCLIIncomplete:
    uid = "90b11c863598495ba699b22ca76b1041"

    @pytest.fixture(autouse=True)
    def _init(self, portal, run_cli, zopeconf, base_import_path, tmp_path):
        self.portal = portal
        import_path = tmp_path / "import"
        shutil.copytree(base_import_path, import_path)
        # Remove the blob of an image
        (import_path / "content" / self.uid / "image" / "2025.png").unlink()
        with pytest.raises(SystemExit) as exc:
            run_cli(
                importer_cli,
                [
                    "plone-importer",
                    str(zopeconf),
                    portal.getId(),
                    str(import_path),
                    "--quiet",
                ],
            )
        self.exit_code = exc.value.code

    def test_exit_code(self):
        assert self.exit_code == 1

    def test_content_imported(self):
        content = api.content.get(UID=self.uid)
        assert content is not None
        assert content.image is None
