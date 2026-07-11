from plone.exportimport.importers import get_importer

import pytest
import transaction


@pytest.fixture()
def portal(app, base_import_path, add_users_groups):
    """Plone portal with imported content."""
    portal = app["plone"]

    importer = get_importer(portal)
    importer.import_site(path=base_import_path)
    # Create new users and groups
    add_users_groups()
    yield portal


@pytest.fixture()
def portal_multilingual(
    app,
    setup_multilingual_site,
    multilingual_import_path,
    add_users_groups,
):
    """Plone portal with imported content."""
    portal = app["plone"]
    with transaction.manager:
        setup_multilingual_site(portal, "en", ["en", "de", "es"])
    importer = get_importer(portal)
    importer.import_site(path=multilingual_import_path)
    # Create new users and groups
    add_users_groups()
    yield portal
