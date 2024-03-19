from plone.exportimport.utils.principals import members as members_utils

import pytest


@pytest.fixture
def members_payload():
    return [
        {
            "description": "Plonista Brasileiro",
            "email": "joao.silva@plone.org.br",
            "fullname": "João da Silva",
            "groups": ["plone_brasil", "Reviewers"],
            "home_page": "https://plone.org.br",
            "location": "Brasília, DF",
            "password": "{SSHA}h0uWiIeI5N0XhQDxLgbybJk9VKTBMri5/7F/",
            "roles": ["Member"],
            "username": "joao.silva",
        }
    ]


class TestUtilsPrincipalsMembers:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.portal = portal

    def test_export_members(self, add_users_groups):
        # Create users and members
        add_users_groups()
        func = members_utils.export_members
        result = func()
        assert isinstance(result, list)
        assert len(result) == 3

    def test_import_members(self, members_payload):
        func = members_utils.import_members
        result = func(members_payload)
        assert isinstance(result, list)
        assert len(result) == 1
