import pytest
import transaction


@pytest.fixture()
def portal_multilingual(app, setup_multilingual_site):
    """Plone portal with multilingual support."""
    portal = app["plone"]
    with transaction.manager:
        setup_multilingual_site(portal, "en", ["en", "de", "es"])
    yield portal


@pytest.fixture()
def portal_multilingual_content(portal_multilingual, multilingual_import_path):
    """Multilingual portal with content."""
    from plone.exportimport.importers import content

    portal = portal_multilingual
    importer = content.ContentImporter(portal_multilingual)
    importer.import_data(base_path=multilingual_import_path)
    yield portal
