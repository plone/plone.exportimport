from plone import api
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.app.redirector.storage import RedirectionStorage
from plone.exportimport import logger
from zope.component import getUtility


def _get_storage() -> RedirectionStorage:
    """Get the redirection storage."""
    return getUtility(IRedirectionStorage)


def _portal_path() -> str:
    """Physical path of the portal, e.g. ``/Plone``."""
    return "/".join(api.portal.get().getPhysicalPath())


def _to_relative(path: str, portal_path: str) -> str:
    """Strip the portal's physical path from a path inside the site.

    Anything that is not under the portal is returned unchanged, which leaves
    an external target (``https://plone.org``) alone.
    """
    if path == portal_path:
        return "/"
    if path.startswith(f"{portal_path}/"):
        return path[len(portal_path) :]
    return path


def _to_physical(path: str, portal_path: str) -> str:
    """Prefix a portal-relative path with the portal's physical path.

    A path that is already physical is returned unchanged, so an archive
    exported by an older release still imports correctly. Anything that is not
    a path at all -- an external target -- is left alone.
    """
    if path == portal_path or path.startswith(f"{portal_path}/"):
        return path
    if path.startswith("/"):
        return f"{portal_path}{path}"
    return path


def get_redirects(paths: set[str] | None = None) -> dict[str, str]:
    """Get a mapping of all redirects in a Plone site.

    Paths are returned portal-relative (``/old``), as every other path in an
    export is, so the data imports into a site with any id.

    :param paths: If given, only redirects pointing to one of these physical
        paths are returned.
    :returns: Mapping of old path to new path.
    """
    redirects = {}
    storage = _get_storage()
    portal_path = _portal_path()
    for key, value in storage._paths.items():
        if isinstance(value, tuple) and len(value) == 3:
            value = value[0]
        # `paths` holds physical paths (exported_content), so filter before
        # making anything relative.
        if paths is not None and value not in paths:
            continue
        redirects[_to_relative(key, portal_path)] = _to_relative(value, portal_path)
    return redirects


def set_redirects(redirects: dict[str, str]) -> dict[str, str]:
    """Set a mapping of redirects in a Plone site.

    Portal-relative paths are stored against the portal's physical path, which
    is what plone.app.redirector's 404 handler looks up. Paths that are already
    physical are stored as they are, so an archive written by an older release
    keeps importing correctly.
    """
    storage = _get_storage()
    portal_path = _portal_path()
    for key, value in redirects.items():
        key, value = (
            _to_physical(key, portal_path),
            _to_physical(value, portal_path),
        )
        storage.add(key, value)
        logger.debug(f"- Redirects: Added redirect from {key} to {value}")
    return redirects
