from plone.exportimport import interfaces
from plone.exportimport.importers import redirects
from zope.component import getAdapter

import pytest


class TestImporterRedirects:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual_content):
        self.portal = portal_multilingual_content
        self.importer = redirects.RedirectsImporter(self.portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.portal, interfaces.INamedImporter, "plone.importer.redirects"
        )
        assert isinstance(adapter, redirects.RedirectsImporter)

    def test_output_is_str(self, multilingual_import_path):
        importer = self.importer
        result = importer.import_data(base_path=multilingual_import_path)
        assert isinstance(result, str)
        assert result == "RedirectsImporter: Imported 2 redirects"

    def test_empty_import_path(self, empty_import_path):
        importer = self.importer
        result = importer.import_data(base_path=empty_import_path)
        assert isinstance(result, str)
        assert result == "RedirectsImporter: No data to import"

    def test_invalid_import_path(self, invalid_import_path):
        importer = self.importer
        result = importer.import_data(base_path=invalid_import_path)
        assert isinstance(result, str)
        assert result == "RedirectsImporter: Import path does not exist"
