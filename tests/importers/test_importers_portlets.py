from plone.exportimport import interfaces
from zope.component import getAdapter

import pytest


try:
    from plone.exportimport.importers import portlets
except ImportError:
    HAVE_PORTLETS = False
else:
    HAVE_PORTLETS = True


@pytest.mark.skipif(not HAVE_PORTLETS, reason="plone.app.portlets is not installed")
class TestImporterPortlets:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.portal = portal
        self.importer = portlets.PortletsImporter(self.portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.portal, interfaces.INamedImporter, "plone.importer.portlets"
        )
        assert isinstance(adapter, portlets.PortletsImporter)

    def test_only_default_portlets_to_import(self, base_import_path):
        importer = self.importer
        result = importer.import_data(base_path=base_import_path)
        assert isinstance(result, str)
        assert result == "PortletsImporter: Imported 0 registrations"

    def test_additional_portlets(self, portlets_import_path):
        importer = self.importer
        result = importer.import_data(base_path=portlets_import_path)
        assert isinstance(result, str)
        assert result == "PortletsImporter: Imported 3 registrations"

    def test_empty_import_path(self, empty_import_path):
        importer = self.importer
        result = importer.import_data(base_path=empty_import_path)
        assert isinstance(result, str)
        assert result == "PortletsImporter: No data to import"

    def test_invalid_import_path(self, invalid_import_path):
        importer = self.importer
        result = importer.import_data(base_path=invalid_import_path)
        assert isinstance(result, str)
        assert result == "PortletsImporter: Import path does not exist"
