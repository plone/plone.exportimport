from plone.exportimport import interfaces
from plone.exportimport.exporters import discussions
from zope.component import getAdapter

import pytest


class TestExporterDiscussions:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual):
        self.src_portal = portal_multilingual
        self.exporter = discussions.DiscussionsExporter(portal_multilingual)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.src_portal, interfaces.INamedExporter, "plone.exporter.discussions"
        )
        assert isinstance(adapter, discussions.DiscussionsExporter)

    def test_output_is_list(self, export_path):
        exporter = self.exporter
        result = exporter.export_data(base_path=export_path)
        assert isinstance(result, list)

    @pytest.mark.parametrize(
        "path",
        [
            "discussions.json",
        ],
    )
    def test_discussions_is_exported(self, export_path, paths_as_relative, path):
        exporter = self.exporter
        result = paths_as_relative(
            export_path, exporter.export_data(base_path=export_path)
        )
        assert isinstance(result, list)
        assert path in result
        assert (export_path / path).exists() is True
        assert (export_path / path).is_file() is True

    @pytest.mark.parametrize(
        "uid,key,value_type",
        [
            ["1cbf4ae73c74459485d3fd6cb9714e43", "items_total", int],
            ["1cbf4ae73c74459485d3fd6cb9714e43", "items", list],
        ],
    )
    def test_discussions_content(self, export_path, load_json, uid, key, value_type):
        exporter = self.exporter
        exporter.export_data(base_path=export_path)
        data = load_json(base_path=export_path, path="discussions.json")
        assert isinstance(data, dict)
        conversation = data[uid]
        assert key in conversation
        assert isinstance(conversation[key], value_type)
