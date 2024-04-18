from plone.exportimport import interfaces
from zope.component import getAdapter

import pytest


try:
    from plone.exportimport.exporters import portlets
except ImportError:
    HAVE_PORTLETS = False
else:
    HAVE_PORTLETS = True


@pytest.mark.skipif(not HAVE_PORTLETS, reason="plone.app.portlets is not installed")
class TestExporterPortlets:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.src_portal = portal
        self.exporter = portlets.PortletsExporter(portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.src_portal, interfaces.INamedExporter, "plone.exporter.portlets"
        )
        assert isinstance(adapter, portlets.PortletsExporter)

    def test_output_is_list(self, export_path):
        exporter = self.exporter
        result = exporter.export_data(base_path=export_path)
        assert isinstance(result, list)

    @pytest.mark.parametrize(
        "path",
        [
            "portlets.json",
        ],
    )
    def test_portlets_is_exported(self, export_path, paths_as_relative, path):
        exporter = self.exporter
        result = paths_as_relative(
            export_path, exporter.export_data(base_path=export_path)
        )
        assert isinstance(result, list)
        assert path in result
        assert (export_path / path).exists() is True
        assert (export_path / path).is_file() is True

    @pytest.mark.parametrize(
        "key,value_type",
        [
            ["@id", str],
            ["portlets", dict],
            ["UID", str],
        ],
    )
    def test_portlets_content(self, export_path, load_json, key, value_type):
        exporter = self.exporter
        exporter.export_data(base_path=export_path)
        data = load_json(base_path=export_path, path="portlets.json")
        assert isinstance(data, list)
        portlet = data[0]
        assert key in portlet
        assert isinstance(portlet[key], value_type)
