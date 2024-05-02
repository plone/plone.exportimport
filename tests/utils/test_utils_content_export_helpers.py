from plone import api
from plone.exportimport import types
from plone.exportimport.settings import PLACEHOLDERS_LANGUAGE
from plone.exportimport.utils.content import export_helpers

import pytest


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
            [{"language": {"token": "es"}}, "es"],
            [{"language": {"token": "pt-br"}}, "pt-br"],
        ],
    )
    def test_fix_language(self, item: dict, expected: str):
        func = export_helpers.fix_language
        result = func(item, None, self.config)
        assert result["language"] == expected
