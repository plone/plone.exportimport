from pathlib import Path
from plone import api
from plone.app.multilingual.browser.setup import SetupMultilingualSite
from plone.exportimport.testing import INTEGRATION_TESTING
from pytest_plone import fixtures_factory
from typing import Callable
from typing import List

import json
import pytest


pytest_plugins = ["pytest_plone"]


globals().update(fixtures_factory(((INTEGRATION_TESTING, "integration"),)))


@pytest.fixture()
def base_import_path():
    """Base content import Path."""
    return Path(__file__).parent / "_resources" / "base_import"


@pytest.fixture()
def multilingual_import_path():
    """Multilingual content import path."""
    return Path(__file__).parent / "_resources" / "multilingual_import"


@pytest.fixture()
def empty_import_path():
    """Empty import Path."""
    return Path(__file__).parent / "_resources" / "empty_import"


@pytest.fixture()
def invalid_import_path():
    """Invalid import Path."""
    return Path(__file__).parent / "_resources" / "404_import"


@pytest.fixture()
def export_path(tmp_path) -> Path:
    """Base export Path."""
    return tmp_path


@pytest.fixture
def paths_as_relative():
    def func(base_path: Path, paths: List[Path]) -> List[str]:
        return [str(path.relative_to(base_path)) for path in paths]

    return func


@pytest.fixture
def load_json():
    def func(base_path: Path, path: Path) -> dict | list:
        with open(base_path / path) as fh:
            data = json.load(fh)
        return data

    return func


@pytest.fixture
def get_exporter():
    from plone.exportimport import interfaces
    from zope.component import getUtility

    return getUtility(interfaces.IExporterUtility, "plone.importer")


@pytest.fixture
def get_importer():
    from plone.exportimport import interfaces
    from zope.component import getUtility

    return getUtility(interfaces.IImporterUtility, "plone.importer")


@pytest.fixture
def create_example_content():
    def func(container, language="en"):
        contents = {}
        with api.env.adopt_roles(["Manager"]):
            folder = api.content.create(
                container=container,
                id="a-folderish",
                type="Document",
                title="A Folderish document",
                description="A simple folder",
                language=language,
            )
            contents[folder.UID()] = folder
            link = api.content.create(
                container=folder,
                id="a-link",
                type="Link",
                title="Link Content",
                description="Visit Plone.org",
                remoteUrl="https://plone.org/",
                language=language,
            )
            contents[link.UID()] = link
            document_one = api.content.create(
                container=folder,
                id="a-page",
                type="Document",
                title="A Page in the site",
                description="A simple page in the site",
                language=language,
            )
            contents[document_one.UID()] = document_one
            document_two = api.content.create(
                container=folder,
                id="another-page",
                type="Document",
                title="Another Page in the site",
                description="A simple page in the site",
                language=language,
            )
            api.relation.create(
                source=document_two, target=document_one, relationship="relatedItems"
            )
            contents[document_two.UID()] = document_two
        return contents

    return func


@pytest.fixture
def setup_discussion():
    def func(types: List[str]):
        types_tool = api.portal.get_tool("portal_types")
        prefix = "plone.app.discussion.interfaces.IDiscussionSettings"
        api.portal.set_registry_record(f"{prefix}.globally_enabled", True)
        # Enable behavior
        # Iterate through all Dexterity content type, except the site root
        all_ftis = types_tool.listTypeInfo()
        dx_ftis = (fti for fti in all_ftis if fti.getId() in types)
        for fti in dx_ftis:
            # Enable discussion
            fti._updateProperty("allow_discussion", True)

    return func


@pytest.fixture
def setup_multilingual_site():
    def func(site, default_language, available_languages):
        site_portal_type = site.portal_type
        setup_tool = api.portal.get_tool("portal_setup")
        types_tool = api.portal.get_tool("portal_types")
        # Set languages in the registru
        api.portal.set_registry_record("plone.default_language", default_language)
        api.portal.set_registry_record("plone.available_languages", available_languages)
        # Install p.a.multilingual
        setup_tool.runAllImportStepsFromProfile(
            "profile-plone.app.multilingual:default"
        )
        sms = SetupMultilingualSite(site)
        sms.setupSite(site)
        # Enable behavior
        # Iterate through all Dexterity content type, except the site root
        all_ftis = types_tool.listTypeInfo()
        dx_ftis = (
            fti
            for fti in all_ftis
            if getattr(fti, "behaviors", False) and fti.getId() != site_portal_type
        )
        for fti in dx_ftis:
            # Enable translatable behavior for all types
            behaviors = list(fti.behaviors)
            if "plone.translatable" not in behaviors:
                behaviors.append("plone.translatable")
                fti._updateProperty("behaviors", tuple(behaviors))

    return func


@pytest.fixture
def portal_multilingual(portal, setup_multilingual_site):
    setup_multilingual_site(portal, "en", ["en", "de", "es"])
    yield portal


@pytest.fixture()
def groups() -> List[dict]:
    """New groups."""
    return [
        {
            "groupname": "developers",
            "title": "Plone Developers",
            "description": "Group of Plone Developers",
            "roles": ["Member"],
            "groups": [],
        },
        {
            "groupname": "release_managers",
            "title": "Plone Release Managers",
            "description": "Group of Plone Release Managers",
            "roles": ["Editor", "Reviewer", "Member"],
            "groups": ["developers"],
        },
    ]


@pytest.fixture()
def users() -> List[dict]:
    """New users."""
    return [
        {
            "email": "j.silva@plone.org",
            "username": "j.silva",
            "properties": {
                "fullname": "Joana da Silva",
                "location": "Brasília, DF",
                "home_page": "https://plone.org.br",
            },
            "groups": ["release_managers"],
        },
        {
            "email": "m.mustermann@plone.org",
            "username": "m.mustermann",
            "properties": {
                "fullname": "Max Mustermann",
                "location": "München",
                "home_page": "https://plone.de",
            },
            "groups": ["developers"],
        },
    ]


@pytest.fixture()
def add_users_groups(groups, users) -> Callable:
    def func():
        for group_info in groups:
            api.group.create(**group_info)
        for user_info in users:
            groupnames = user_info.pop("groups", [])
            user = api.user.create(**user_info)
            for groupname in groupnames:
                api.group.add_user(groupname=groupname, user=user)

    return func
