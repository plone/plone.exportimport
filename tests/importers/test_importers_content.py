from plone.exportimport import interfaces
from plone.exportimport.importers import content
from zope.component import getAdapter

import pytest


class TestImporterContent:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual_content):
        self.portal = portal_multilingual_content
        self.importer = content.ContentImporter(self.portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.portal, interfaces.INamedImporter, "plone.importer.content"
        )
        assert isinstance(adapter, content.ContentImporter)

    def test_output_is_str(self, multilingual_import_path):
        importer = self.importer
        result = importer.import_data(base_path=multilingual_import_path)
        assert isinstance(result, str)
        assert result == "ContentImporter: Imported 19 objects"

    def test_empty_import_path(self, empty_import_path):
        importer = self.importer
        result = importer.import_data(base_path=empty_import_path)
        assert isinstance(result, str)
        assert result == "ContentImporter: No data to import"
