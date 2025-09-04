from plone import api
from plone.exportimport import types
from plone.exportimport.settings import PLACEHOLDERS_LANGUAGE
from plone.exportimport.utils.content import export_helpers

import pytest


PORTAL_URL = "http://nohost/plone"


@pytest.fixture
def exporter_config(portal, http_request) -> types.ExporterConfig:
    return types.ExporterConfig(
        site=portal,
        site_root_uid=api.content.get_uuid(portal),
        request=http_request,
        serializer=None,
        logger_prefix="test",
    )


class TestUtilsContentExportHelpers:

    @pytest.fixture(autouse=True)
    def _init(self, exporter_config):
        self.config = exporter_config

    @pytest.mark.parametrize(
        "item,expected",
        [
            [{}, PLACEHOLDERS_LANGUAGE],
            [{"language": ""}, PLACEHOLDERS_LANGUAGE],
            [{"language": "en"}, PLACEHOLDERS_LANGUAGE],
            [{"language": "es"}, "es"],
            [{"language": "pt-br"}, "pt-br"],
            [{"language": {"token": "es"}}, "es"],
            [{"language": {"token": "pt-br"}}, "pt-br"],
        ],
    )
    def test_fix_language(self, item: dict, expected: str):
        func = export_helpers.fix_language
        result = func(item, None, self.config)
        assert result["language"] == expected

    @pytest.mark.parametrize(
        "item,portal_url,expected",
        [
            [{"@id": f"{PORTAL_URL}/news"}, PORTAL_URL, {"@id": "/news"}],
            [{"@id": f"{PORTAL_URL}/"}, PORTAL_URL, {"@id": "/"}],
            [{"@id": f"{PORTAL_URL}"}, PORTAL_URL, {"@id": "/"}],
            [{"@parent": f"{PORTAL_URL}/news"}, PORTAL_URL, {"@parent": "/news"}],
            [{"@parent": f"{PORTAL_URL}/"}, PORTAL_URL, {"@parent": "/"}],
            [{"@parent": f"{PORTAL_URL}"}, PORTAL_URL, {"@parent": "/"}],
            [{"remoteUrl": f"{PORTAL_URL}/news"}, PORTAL_URL, {"remoteUrl": "/news"}],
            [{"remoteUrl": f"{PORTAL_URL}/"}, PORTAL_URL, {"remoteUrl": "/"}],
            [{"remoteUrl": f"{PORTAL_URL}"}, PORTAL_URL, {"remoteUrl": "/"}],
            [{"url": f"{PORTAL_URL}/news"}, PORTAL_URL, {"url": "/news"}],
            [{"url": f"{PORTAL_URL}/"}, PORTAL_URL, {"url": "/"}],
            [{"url": f"{PORTAL_URL}"}, PORTAL_URL, {"url": "/"}],
        ],
    )
    def test_rewrite_site_root(self, item: dict, portal_url: str, expected: dict):
        func = export_helpers.rewrite_site_root
        result = func(item, portal_url)
        assert result == expected
