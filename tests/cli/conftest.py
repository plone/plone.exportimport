from collections.abc import Callable
from pathlib import Path
from plone import api
from plone.exportimport.utils import cli as cli_helpers
from zope.component import hooks
from zope.globalrequest import getRequest
from zope.globalrequest import setRequest

import pytest
import Zope2


@pytest.fixture()
def app(functional):
    """Zope application from the functional layer.

    ``importer_cli`` commits the transaction, so these tests need the
    per-test storage isolation of the functional layer.
    """
    return functional["app"]


@pytest.fixture()
def portal(functional):
    """Plone Site from the functional layer."""
    return functional["portal"]


@pytest.fixture()
def cli_import_path() -> Path:
    """Import Path with values for permission-protected fields."""
    return Path(__file__).parent.parent / "_resources" / "cli_import"


@pytest.fixture()
def zopeconf(tmp_path) -> Path:
    """Placeholder zope.conf, never parsed as WSGI startup is patched out."""
    path = tmp_path / "zope.conf"
    path.write_text("")
    return path


@pytest.fixture()
def patch_zope_startup(app, monkeypatch):
    """Make the CLI use the test layer application instead of starting Zope."""
    monkeypatch.setattr(cli_helpers, "make_wsgi_app", lambda *args: None)
    monkeypatch.setattr(Zope2, "app", lambda: app)


@pytest.fixture()
def run_cli(portal, patch_zope_startup) -> Callable:
    """Run a CLI entry point the way a fresh process would.

    A fresh process has no local site hook set, so we clear it before
    calling the CLI and restore it, and the global request, afterwards.
    """

    def func(cli: Callable, args: list[str]):
        request = getRequest()
        hooks.setSite(None)
        try:
            return cli(args)
        finally:
            hooks.setSite(portal)
            setRequest(request)

    return func


@pytest.fixture()
def dummy_content(portal):
    """DummyContent with values set on its permission-protected fields."""
    with api.env.adopt_roles(["Manager"]):
        content = api.content.create(
            container=portal,
            type="DummyContent",
            id="dummy",
            title="A Dummy content",
            secure_field="A secure value",
            secure_setting=False,
        )
    return content


@pytest.fixture()
def site_settings(portal):
    """Plone Site with values set on the dummy_settings behavior fields."""
    from plone.exportimport.testing.content.dummy import IDummySettings

    with api.env.adopt_roles(["Manager"]):
        settings = IDummySettings(portal)
        settings.secure_field = "A secure site value"
        settings.secure_setting = False
    return portal
