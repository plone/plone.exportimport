from pathlib import Path
from plone.exportimport.exporters import Exporter
from plone.exportimport.exporters import get_exporter

import pytest


class TestExporter:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.src_portal = portal
        self.exporter = get_exporter(self.src_portal)

    def test_exporter_is_correct_instance(self):
        assert isinstance(self.exporter, Exporter)

    def test_all_exporters(self):
        exporters = self.exporter.all_exporters()
        assert isinstance(exporters, dict)
        assert len(exporters) == 6

    @pytest.mark.parametrize(
        "exporter_name",
        [
            "plone.exporter.content",
            "plone.exporter.principals",
            "plone.exporter.redirects",
            "plone.exporter.relations",
            "plone.exporter.translations",
            "plone.exporter.discussions",
        ],
    )
    def test_exporter_present(self, exporter_name: str):
        exporters = self.exporter.all_exporters()
        assert exporter_name in exporters

    def test_export_site(self, export_path):
        results = self.exporter.export_site(export_path)
        assert isinstance(results, list)
        # First item is always the export path
        path = results[0]
        assert isinstance(path, Path)
        assert path.resolve() == export_path.resolve()

    @pytest.mark.parametrize(
        "path,is_dir,is_file",
        [
            [".", True, False],
            ["principals.json", False, True],
            ["redirects.json", False, True],
            ["relations.json", False, True],
            ["translations.json", False, True],
            ["discussions.json", False, True],
            ["content/__metadata__.json", False, True],
            ["content/70844f7bec1843b8ab2796c972c9ebfe/data.json", False, True],
            ["content/90b11c863598495ba699b22ca76b1041/data.json", False, True],
            ["content/7c1393f615c4447c80db0d784390c5b7/data.json", False, True],
            ["content/5d77cd5686184ec49ab077017b1fbc3a/data.json", False, True],
            ["content/e7359727ace64e609b79c4091c38822a/data.json", False, True],
            ["content/45b0b46f17104a7b8fa7bb94d3dd5bd9/data.json", False, True],
            ["content/35661c9bb5be42c68f665aa1ed291418/data.json", False, True],
            ["content/plone_site_root/data.json", False, True],
        ],
    )
    def test_export_site_has_file(
        self, export_path, paths_as_relative, path: str, is_dir: bool, is_file: bool
    ):
        results = paths_as_relative(export_path, self.exporter.export_site(export_path))
        assert path in results
        filepath = (export_path / path).resolve()
        assert filepath.is_dir() is is_dir
        assert filepath.is_file() is is_file


class TestExporterMultilingual:

    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.src_portal = portal
        self.exporter = get_exporter(self.src_portal)

    def test_exporter_is_correct_instance(self):
        assert isinstance(self.exporter, Exporter)

    def test_all_exporters(self):
        exporters = self.exporter.all_exporters()
        assert isinstance(exporters, dict)
        assert len(exporters) == 6
