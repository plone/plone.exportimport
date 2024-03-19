from plone.exportimport import interfaces
from plone.exportimport.exporters import principals
from zope.component import getAdapter

import pytest


class TestExporterPrincipals:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual):
        self.src_portal = portal_multilingual
        self.exporter = principals.PrincipalsExporter(portal_multilingual)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.src_portal, interfaces.INamedExporter, "plone.exporter.principals"
        )
        assert isinstance(adapter, principals.PrincipalsExporter)

    def test_output_is_list(self, export_path):
        exporter = self.exporter
        result = exporter.export_data(base_path=export_path)
        assert isinstance(result, list)

    @pytest.mark.parametrize(
        "path",
        [
            "principals.json",
        ],
    )
    def test_principals_is_exported(self, export_path, paths_as_relative, path):
        exporter = self.exporter
        result = paths_as_relative(
            export_path, exporter.export_data(base_path=export_path)
        )
        assert isinstance(result, list)
        assert path in result
        assert (export_path / path).exists() is True
        assert (export_path / path).is_file() is True
