from DateTime import DateTime
from plone.exportimport import interfaces
from plone.exportimport.importers import content
from zope.component import getAdapter

import pytest


class TestImporterContent:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual_content):
        self.portal = portal_multilingual_content
        # The contentfinal importer is an enhancement on the content importer.
        # That one needs to run first.
        self.content_importer = content.ContentImporter(self.portal)
        self.importer = content.ContentFinalImporter(self.portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.portal, interfaces.INamedImporter, "plone.importer.contentfinal"
        )
        assert isinstance(adapter, content.ContentFinalImporter)

    def test_output_is_str(self, multilingual_import_path):
        self.content_importer.import_data(base_path=multilingual_import_path)
        importer = self.importer
        result = importer.import_data(base_path=multilingual_import_path)
        assert isinstance(result, str)
        assert result == "ContentFinalImporter: Updated 19 objects"

    def test_empty_import_path(self, empty_import_path):
        importer = self.importer
        result = importer.import_data(base_path=empty_import_path)
        assert isinstance(result, str)
        assert result == "ContentFinalImporter: No data to import"


class TestImporterDates:
    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path, load_json):
        self.portal = portal
        content_importer = content.ContentImporter(self.portal)
        content_importer.import_data(base_path=base_import_path)
        importer = content.ContentFinalImporter(portal)
        importer.import_data(base_path=base_import_path)

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
                "3e0dd7c4b2714eafa1d6fc6a1493f953",
                "created",
                "2024-03-19T19:02:18+00:00",
            ],
            [
                "3e0dd7c4b2714eafa1d6fc6a1493f953",
                "modified",
                "2024-03-19T19:02:18+00:00",
            ],
            [
                "e7359727ace64e609b79c4091c38822a",
                "created",
                "2024-02-13T18:15:56+00:00",
            ],
            # Note: this would fail without the contentfinal importer, because this
            # is a folder that gets modified later when a document is added.
            [
                "e7359727ace64e609b79c4091c38822a",
                "modified",
                "2024-02-13T20:51:06+00:00",
            ],
        ],
    )
    def test_date_is_set(self, uid, method_name, value):
        from plone.exportimport.utils.content import object_from_uid

        content = object_from_uid(uid)
        assert getattr(content, method_name)() == DateTime(value)
