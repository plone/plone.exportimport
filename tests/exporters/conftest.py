import pytest
import transaction


@pytest.fixture()
def portal(app, base_import_path, get_importer, add_users_groups):
    """Plone portal with imported content."""
    portal = app["plone"]

    importer = get_importer
    importer.import_site(site=portal, path=base_import_path)
    # Create new users and groups
    add_users_groups()
    yield portal


@pytest.fixture()
def portal_multilingual(
    app,
    setup_multilingual_site,
    multilingual_import_path,
    get_importer,
    add_users_groups,
):
    """Plone portal with imported content."""
    portal = app["plone"]
    with transaction.manager:
        setup_multilingual_site(portal, "en", ["en", "de", "es"])
    importer = get_importer
    importer.import_site(site=portal, path=multilingual_import_path)
    # Create new users and groups
    add_users_groups()
    yield portal
