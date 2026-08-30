from plone.exportimport.utils import redirects

import pytest


class TestUtilsRedirects:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.portal = portal
        # Create one redirect
        storage = redirects._get_storage()
        storage.add("/foo", "/bar")

    def test__get_storage(self):
        from plone.app.redirector.storage import RedirectionStorage

        storage = redirects._get_storage()
        assert isinstance(storage, RedirectionStorage)

    def test_get_redirects(self):
        all_redirects = redirects.get_redirects()
        assert isinstance(all_redirects, dict)
        assert len(all_redirects) == 1
        assert all_redirects["/foo"] == "/bar"

    def test_set_redirects(self):
        all_redirects = redirects.get_redirects()
        total_before = len(all_redirects)
        new_redirects = {
            "/foobar": "/barfoo",
            "/whois": "https://plone.org",
        }
        # Add new redirects
        redirects.set_redirects(new_redirects)
        all_redirects = redirects.get_redirects()
        total_after = len(all_redirects)
        assert total_after > total_before
        assert total_after == 3
        assert all_redirects["/whois"] == "https://plone.org"
