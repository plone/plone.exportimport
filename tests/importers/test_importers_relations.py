from plone.exportimport import interfaces
from plone.exportimport.importers import relations
from zope.component import getAdapter

import pytest


class TestImporterRelations:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual_content):
        self.portal = portal_multilingual_content
        self.importer = relations.RelationsImporter(self.portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.portal, interfaces.INamedImporter, "plone.importer.relations"
        )
        assert isinstance(adapter, relations.RelationsImporter)

    def test_output_is_str(self, multilingual_import_path):
        importer = self.importer
        result = importer.import_data(base_path=multilingual_import_path)
        assert isinstance(result, str)
        assert result == "RelationsImporter: Imported 3 relations"

    def test_empty_import_path(self, empty_import_path):
        importer = self.importer
        result = importer.import_data(base_path=empty_import_path)
        assert isinstance(result, str)
        assert result == "RelationsImporter: No data to import"

    def test_invalid_import_path(self, invalid_import_path):
        importer = self.importer
        result = importer.import_data(base_path=invalid_import_path)
        assert isinstance(result, str)
        assert result == "RelationsImporter: Import path does not exist"
