from DateTime import DateTime
from plone import api
from plone.exportimport.importers import get_importer
from plone.exportimport.importers import Importer
from Products.CMFCore.indexing import processQueue

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
            "plone.importer.final",
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
            "FinalImporter: Updated 9 objects",
        ],
    )
    def test_import_site(self, base_import_path, msg: str):
        results = self.importer.import_site(base_import_path)
        assert isinstance(results, list)
        # One entry per importer
        assert len(results) >= 6
        assert msg in results

    @pytest.mark.parametrize(
        "uid,method_name,value",
        [
            [
                "35661c9bb5be42c68f665aa1ed291418",
                "created",
                "2024-02-13T18:16:04+00:00",
            ],
            [
                "35661c9bb5be42c68f665aa1ed291418",
                "modified",
                "2024-02-13T18:16:04+00:00",
            ],
            [
                "e7359727ace64e609b79c4091c38822a",
                "created",
                "2024-02-13T18:15:56+00:00",
            ],
            # The next one would fail without the final importer.
            [
                "e7359727ace64e609b79c4091c38822a",
                "modified",
                "2024-02-13T20:51:06+00:00",
            ],
        ],
    )
    def test_date_is_set(self, base_import_path, uid, method_name, value):
        from plone.exportimport.utils.content import object_from_uid

        self.importer.import_site(base_import_path)
        content = object_from_uid(uid)
        assert getattr(content, method_name)() == DateTime(value)

    def test_final_contents(self, base_import_path):
        self.importer.import_site(base_import_path)

        # First test that some specific contents were created.
        image = api.content.get(path="/bar/2025.png")
        assert image is not None
        assert image.portal_type == "Image"
        assert image.title == "2025 logo"

        page = api.content.get(path="/foo/another-page")
        assert page is not None
        assert page.portal_type == "Document"
        assert page.title == "Another page"

        # Now do general checks on all contents.
        catalog = api.portal.get_tool("portal_catalog")

        # getAllBrains does not yet process the indexing queue before it starts.
        # It probably should.  We call it explicitly here, otherwise the tests fail:
        # Some brains will have a modification date of today, even though if you get
        # the object, its actual modification date has been reset to 2024.
        processQueue()
        brains = list(catalog.getAllBrains())
        assert len(brains) >= 9
        for brain in brains:
            if brain.portal_type == "Plone Site":
                continue
            # All created and modified dates should be in the previous year
            # (or earlier).
            assert not brain.created.isCurrentYear()
            assert not brain.modified.isCurrentYear()
            # Given what we see with getAllBrains, let's check the actual content
            # items as well.
            obj = brain.getObject()
            assert not obj.created().isCurrentYear()
            assert not obj.modified().isCurrentYear()
