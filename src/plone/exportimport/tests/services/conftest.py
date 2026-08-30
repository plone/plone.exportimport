from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.restapi.testing import RelativeSession

import pytest


@pytest.fixture()
def portal(functional):
    yield functional["portal"]


@pytest.fixture()
def request_api_factory(portal):
    def factory():
        url = portal.absolute_url()
        api_session = RelativeSession(f"{url}/++api++")
        return api_session

    return factory


@pytest.fixture()
def api_session_anonymous(request_api_factory):
    request = request_api_factory()
    yield request


@pytest.fixture()
def api_session_manager(request_api_factory):
    request = request_api_factory()
    request.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
    yield request
    request.auth = ()
