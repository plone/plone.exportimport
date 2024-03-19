from plone.exportimport import interfaces
from plone.exportimport.importers import translations
from zope.component import getAdapter

import pytest


class TestImporterTranslations:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual_content):
        self.portal = portal_multilingual_content
        self.importer = translations.TranslationsImporter(self.portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.portal, interfaces.INamedImporter, "plone.importer.translations"
        )
        assert isinstance(adapter, translations.TranslationsImporter)

    def test_output_is_str(self, multilingual_import_path):
        importer = self.importer
        result = importer.import_data(base_path=multilingual_import_path)
        assert isinstance(result, str)
        assert result == "TranslationsImporter: Imported 5 translations"

    def test_empty_import_path(self, empty_import_path):
        importer = self.importer
        result = importer.import_data(base_path=empty_import_path)
        assert isinstance(result, str)
        assert result == "TranslationsImporter: No data to import"

    def test_invalid_import_path(self, invalid_import_path):
        importer = self.importer
        result = importer.import_data(base_path=invalid_import_path)
        assert isinstance(result, str)
        assert result == "TranslationsImporter: Import path does not exist"
