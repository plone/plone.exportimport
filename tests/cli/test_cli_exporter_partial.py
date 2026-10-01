from plone import api
from plone.exportimport.cli import exporter_cli

import pytest


@pytest.fixture()
def content_tree(portal):
    """Two top level folderish documents, each with one document inside."""
    contents = {}
    with api.env.adopt_roles(["Manager"]):
        for folder_id in ("section-a", "section-b"):
            folder = api.content.create(
                container=portal, type="Document", id=folder_id, title=folder_id
            )
            document = api.content.create(
                container=folder, type="Document", id="page", title="Page"
            )
            contents[f"/{folder_id}"] = folder.UID()
            contents[f"/{folder_id}/page"] = document.UID()
    return contents


@pytest.fixture()
def export_cli(portal, run_cli, zopeconf, export_path, load_json):
    """Run the exporter CLI with extra arguments and return the exported files."""

    def func(*extra: str) -> list[str]:
        args = ["plone-exporter", str(zopeconf), portal.getId(), str(export_path)]
        run_cli(exporter_cli, args + list(extra))
        metadata = load_json(export_path, "content/__metadata__.json")
        return metadata["_data_files_"]

    return func


class TestExporterCLIPartial:
    @pytest.fixture(autouse=True)
    def _init(self, content_tree):
        self.uids = content_tree

    def _files(self, *paths: str) -> set[str]:
        return {f"{self.uids[path]}/data.json" for path in paths}

    def test_path_option(self, export_cli):
        files = export_cli("--path", "/section-a")
        assert set(files) == self._files("/section-a", "/section-a/page")

    def test_path_option_repeated(self, export_cli):
        files = export_cli("--path", "/section-a/page", "--path", "section-b/page")
        assert set(files) == self._files("/section-a/page", "/section-b/page")

    def test_paths_file(self, export_cli, tmp_path):
        paths_file = tmp_path / "paths.txt"
        paths_file.write_text("# Sections to export\n\n/section-b\n")
        files = export_cli("--paths", str(paths_file))
        assert set(files) == self._files("/section-b", "/section-b/page")

    def test_path_and_paths_file_are_merged(self, export_cli, tmp_path):
        paths_file = tmp_path / "paths.txt"
        paths_file.write_text("/section-b/page\n")
        files = export_cli("--paths", str(paths_file), "--path", "/section-a/page")
        assert set(files) == self._files("/section-a/page", "/section-b/page")

    def test_missing_path_is_skipped(self, export_cli):
        files = export_cli("--path", "/section-a/page", "--path", "/not-here")
        assert set(files) == self._files("/section-a/page")

    def test_no_path_with_content_aborts(self, export_cli):
        with pytest.raises(SystemExit) as exc:
            export_cli("--path", "/not-here")
        assert exc.value.code == 1

    def test_missing_paths_file_aborts(self, export_cli, tmp_path):
        with pytest.raises(SystemExit) as exc:
            export_cli("--paths", str(tmp_path / "missing.txt"))
        assert exc.value.code == 1

    def test_without_paths_exports_everything(self, export_cli):
        files = export_cli()
        assert self._files(*self.uids) <= set(files)
        assert "plone_site_root/data.json" in files
