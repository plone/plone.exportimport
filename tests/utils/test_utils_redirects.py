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


class TestUtilsRedirectsPortalRelative:
    """Paths round-trip portal-relative, and are stored physical.

    plone.app.redirector's 404 handler looks a path up by its Zope-physical
    path (``/Plone/old``). Writing that into an export makes the one file in
    the archive that cannot be imported into a site with a different id --
    every other path in an export is portal-relative. So the storage keeps
    physical paths and the export carries relative ones.
    """

    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.portal = portal
        self.portal_path = "/".join(portal.getPhysicalPath())
        self.storage = redirects._get_storage()

    def test_export_is_portal_relative(self):
        self.storage.add(f"{self.portal_path}/old", f"{self.portal_path}/new")
        assert redirects.get_redirects() == {"/old": "/new"}

    def test_import_stores_physical(self):
        redirects.set_redirects({"/old": "/new"})
        assert self.storage.get(f"{self.portal_path}/old") == f"{self.portal_path}/new"

    def test_round_trip_is_stable(self):
        redirects.set_redirects({"/old": "/new"})
        assert redirects.get_redirects() == {"/old": "/new"}

    def test_an_older_archive_still_imports(self):
        # Physical paths, as releases before this one wrote them. Prefixing
        # them again would store /Plone/Plone/old, which nothing looks up.
        redirects.set_redirects({f"{self.portal_path}/old": f"{self.portal_path}/new"})
        assert self.storage.get(f"{self.portal_path}/old") == f"{self.portal_path}/new"
        assert redirects.get_redirects() == {"/old": "/new"}

    def test_an_external_target_is_left_alone(self):
        redirects.set_redirects({"/whois": "https://plone.org"})
        assert self.storage.get(f"{self.portal_path}/whois") == "https://plone.org"
        assert redirects.get_redirects() == {"/whois": "https://plone.org"}

    def test_the_site_root_itself(self):
        self.storage.add(f"{self.portal_path}/old", self.portal_path)
        assert redirects.get_redirects() == {"/old": "/"}

    def test_paths_filter_still_matches_physical_paths(self):
        # `paths` comes from exported_content(), which yields physical paths,
        # so the filter has to run before anything is made relative.
        self.storage.add(f"{self.portal_path}/old", f"{self.portal_path}/kept")
        self.storage.add(f"{self.portal_path}/gone", f"{self.portal_path}/dropped")
        assert redirects.get_redirects(paths={f"{self.portal_path}/kept"}) == {
            "/old": "/kept"
        }
