from plone.exportimport.utils.principals import groups as groups_utils

import pytest


@pytest.fixture
def groups_payload():
    return [
        {
            "description": "Group of Plone Brasil Users",
            "email": "gov@plone.org.br",
            "groupid": "plone_brasil",
            "groups": [],
            "principals": ["joao.silva"],
            "roles": ["Member"],
            "title": "Plone Brasil",
        }
    ]


class TestUtilsPrincipalsGroups:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.portal = portal

    def test_export_groups(self, add_users_groups):
        # Create users and groups
        add_users_groups()
        func = groups_utils.export_groups
        result = func()
        assert isinstance(result, list)
        assert len(result) == 5

    def test_import_groups(self, groups_payload):
        func = groups_utils.import_groups
        result = func(groups_payload)
        assert isinstance(result, list)
        assert len(result) == 1
