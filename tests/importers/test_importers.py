from plone.exportimport import interfaces
from plone.exportimport.importers import ImporterUtility
from zope.component import getUtility

import pytest


class TestImporterUtility:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.src_portal = portal
        self.utility = getUtility(interfaces.IImporterUtility, "plone.importer")

    def test_utility_is_correct_instance(self):
        assert isinstance(self.utility, ImporterUtility)

    def test_utility_all_importers(self):
        importers = self.utility.all_importers(self.src_portal)
        assert isinstance(importers, dict)
        assert len(importers) == 6

    @pytest.mark.parametrize(
        "importer_name",
        [
            "plone.importer.content",
            "plone.importer.principals",
            "plone.importer.redirects",
            "plone.importer.relations",
            "plone.importer.translations",
            "plone.importer.discussions",
        ],
    )
    def test_utility_importer_present(self, importer_name: str):
        importers = self.utility.all_importers(self.src_portal)
        assert importer_name in importers

    @pytest.mark.parametrize(
        "msg",
        [
            "ContentImporter: Imported 9 objects",
            "PrincipalsImporter: Imported 2 groups and 1 members",
            "RedirectsImporter: Imported 0 redirects",
        ],
    )
    def test_utility_import_site(self, base_import_path, msg: str):
        results = self.utility.import_site(self.src_portal, base_import_path)
        assert isinstance(results, list)
        # One entry per importer
        assert len(results) == 6
        assert msg in results
