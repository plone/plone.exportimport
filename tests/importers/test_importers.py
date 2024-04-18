from plone.exportimport.importers import get_importer
from plone.exportimport.importers import Importer

import pytest


class TestImporter:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.src_portal = portal
        self.importer = get_importer(self.src_portal)

    def test_importer_is_correct_class(self):
        assert isinstance(self.importer, Importer)

    def test_all_importers(self):
        importers = self.importer.all_importers()
        assert isinstance(importers, dict)
        assert len(importers) >= 6

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
    def test_importer_present(self, importer_name: str):
        importers = self.importer.all_importers()
        assert importer_name in importers

    @pytest.mark.parametrize(
        "msg",
        [
            "ContentImporter: Imported 9 objects",
            "PrincipalsImporter: Imported 2 groups and 1 members",
            "RedirectsImporter: Imported 0 redirects",
        ],
    )
    def test_import_site(self, base_import_path, msg: str):
        results = self.importer.import_site(base_import_path)
        assert isinstance(results, list)
        # One entry per importer
        assert len(results) >= 6
        assert msg in results
