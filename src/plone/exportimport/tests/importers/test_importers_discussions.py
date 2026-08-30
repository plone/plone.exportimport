from plone.exportimport import interfaces
from plone.exportimport.importers import discussions
from zope.component import getAdapter

import pytest


class TestImporterDiscussions:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual_content):
        self.portal = portal_multilingual_content
        self.importer = discussions.DiscussionsImporter(self.portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.portal, interfaces.INamedImporter, "plone.importer.discussions"
        )
        assert isinstance(adapter, discussions.DiscussionsImporter)

    def test_output_is_str(self, multilingual_import_path):
        importer = self.importer
        result = importer.import_data(base_path=multilingual_import_path)
        assert isinstance(result, str)
        assert result == "DiscussionsImporter: Imported 2 conversations"

    def test_empty_import_path(self, empty_import_path):
        importer = self.importer
        result = importer.import_data(base_path=empty_import_path)
        assert isinstance(result, str)
        assert result == "DiscussionsImporter: No data to import"

    def test_invalid_import_path(self, invalid_import_path):
        importer = self.importer
        result = importer.import_data(base_path=invalid_import_path)
        assert isinstance(result, str)
        assert result == "DiscussionsImporter: Import path does not exist"
