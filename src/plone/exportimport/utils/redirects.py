from plone.app.redirector.interfaces import IRedirectionStorage
from plone.app.redirector.storage import RedirectionStorage
from plone.exportimport import logger
from typing import Dict
from zope.component import getUtility


def _get_storage() -> RedirectionStorage:
    """Get the redirection storage."""
    return getUtility(IRedirectionStorage)


def get_redirects() -> Dict[str, str]:
    """Get a mapping of all redirects in a Plone site."""
    redirects = {}
    storage = _get_storage()
    for key, value in storage._paths.items():
        if isinstance(value, tuple) and len(value) == 3:
            value = value[0]
        redirects[key] = value
    return redirects


def set_redirects(redirects: Dict[str, str]) -> Dict[str, str]:
    """Set a mapping of redirects in a Plone site."""
    storage = _get_storage()
    for key, value in redirects.items():
        storage.add(key, value)
        logger.debug(f"- Redirects: Added redirect from {key} to {value}")
    return redirects
