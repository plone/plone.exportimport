from plone import api
from plone.exportimport.utils import cli as cli_helpers

import logging
import pytest


@pytest.fixture()
def logger() -> logging.Logger:
    return logging.getLogger("test_utils_cli")


class TestReadPathsFile:
    @pytest.mark.parametrize(
        "content,expected",
        [
            ["/a\n/b\n", ["/a", "/b"]],
            ["  /a  \n\n\n/b", ["/a", "/b"]],
            ["# comment\n/a\n  # indented comment\n", ["/a"]],
            ["", []],
        ],
    )
    def test_read_paths_file(self, tmp_path, content: str, expected: list[str]):
        path = tmp_path / "paths.txt"
        path.write_text(content)
        assert cli_helpers.read_paths_file(path) == expected


class TestGetExportQuery:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.portal = portal
        self.site_path = "/".join(portal.getPhysicalPath())
        with api.env.adopt_roles(["Manager"]):
            folder = api.content.create(
                container=portal, type="Document", id="folder", title="Folder"
            )
            api.content.create(
                container=portal, type="Document", id="page", title="Page"
            )
            api.content.create(
                container=folder, type="Document", id="inner", title="Inner"
            )

    def _query(self, *paths: str) -> dict:
        return {"path": {"query": [f"{self.site_path}{path}" for path in paths]}}

    def test_no_paths(self, logger):
        assert cli_helpers.get_export_query(self.portal, None, None, logger) is None

    @pytest.mark.parametrize(
        "paths,expected",
        [
            [["/folder"], ["/folder"]],
            [["folder/"], ["/folder"]],
            [["/folder", "/folder/inner"], ["/folder", "/folder/inner"]],
            [["/folder", "folder"], ["/folder"]],
            [["/"], [""]],
        ],
    )
    def test_paths(self, logger, paths: list[str], expected: list[str]):
        query = cli_helpers.get_export_query(self.portal, paths, None, logger)
        assert query == self._query(*expected)

    def test_acquired_path_is_skipped(self, logger, caplog):
        """page is reachable from folder by acquisition, but it is not there."""
        query = cli_helpers.get_export_query(
            self.portal, ["/folder/page", "/folder"], None, logger
        )
        assert query == self._query("/folder")
        assert "No content at /folder/page" in caplog.text

    def test_paths_file(self, logger, tmp_path):
        paths_file = tmp_path / "paths.txt"
        paths_file.write_text("/page\n")
        query = cli_helpers.get_export_query(
            self.portal, ["/folder"], str(paths_file), logger
        )
        assert query == self._query("/folder", "/page")

    def test_no_content_exits(self, logger):
        with pytest.raises(SystemExit):
            cli_helpers.get_export_query(self.portal, ["/missing"], None, logger)

    def test_missing_paths_file_exits(self, logger, tmp_path):
        with pytest.raises(SystemExit):
            cli_helpers.get_export_query(
                self.portal, None, str(tmp_path / "missing.txt"), logger
            )
