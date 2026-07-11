from plone.exportimport import interfaces
from plone.exportimport.exporters import translations
from zope.component import getAdapter

import pytest


class TestExporterTranslations:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual):
        self.src_portal = portal_multilingual
        self.exporter = translations.TranslationsExporter(portal_multilingual)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.src_portal, interfaces.INamedExporter, "plone.exporter.translations"
        )
        assert isinstance(adapter, translations.TranslationsExporter)

    def test_output_is_list(self, export_path):
        exporter = self.exporter
        result = exporter.export_data(base_path=export_path)
        assert isinstance(result, list)

    @pytest.mark.parametrize(
        "path",
        [
            "translations.json",
        ],
    )
    def test_translations_is_exported(self, export_path, paths_as_relative, path):
        exporter = self.exporter
        result = paths_as_relative(
            export_path, exporter.export_data(base_path=export_path)
        )
        assert isinstance(result, list)
        assert path in result
        assert (export_path / path).exists() is True
        assert (export_path / path).is_file() is True

    @pytest.mark.parametrize(
        "key,value_type",
        [
            ["canonical", str],
            ["translations", dict],
        ],
    )
    def test_translations_content(self, export_path, load_json, key, value_type):
        exporter = self.exporter
        exporter.export_data(base_path=export_path)
        data = load_json(base_path=export_path, path="translations.json")
        assert isinstance(data, list)
        translation_group = data[0]
        assert key in translation_group
        assert isinstance(translation_group[key], value_type)
