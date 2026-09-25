from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.users import system as user
from pathlib import Path
from plone.restapi.interfaces import IPloneRestapiLayer
from Products.CMFPlone.Portal import PloneSite
from Testing.makerequest import makerequest
from Zope2.Startup.run import make_wsgi_app
from zope.globalrequest import setRequest
from zope.interface import directlyProvidedBy
from zope.interface import directlyProvides

import logging
import sys
import Zope2


def _process_path(path: str) -> Path | None:
    """Process path."""
    path = Path(path).resolve()
    return path if path.exists() else None


def setup_logger_console(logger: logging.Logger) -> None:
    """Return a logger."""
    logging.basicConfig(format="%(message)s")
    logger.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Return a logger."""
    logger = logging.getLogger(name)
    setup_logger_console(logger)
    return logger


def get_app(zopeconf: Path):
    """Get Zope Application root."""
    if not _process_path(zopeconf):
        sys.exit(1)
    make_wsgi_app({}, zopeconf)
    app = Zope2.app()
    app = makerequest(app)
    request = app.REQUEST
    app.REQUEST["PARENTS"] = [app]
    setRequest(app.REQUEST)
    ifaces = [IPloneRestapiLayer]
    try:
        from plone.app.discussion.interfaces import (
            IDiscussionLayer,  # Needed by plone.restapi
        )
    except ImportError:
        pass
    else:
        ifaces.append(IDiscussionLayer)
    ifaces += list(directlyProvidedBy(request))

    directlyProvides(request, *ifaces)
    newSecurityManager(None, user)
    return app


def read_paths_file(path: Path) -> list[str]:
    """Read content paths from a file, one per line.

    :param path: File to read.
    :returns: The paths, without empty lines and lines starting with ``#``.
    """
    lines = (line.strip() for line in path.read_text().splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def _content_exists(site: PloneSite, path: str) -> bool:
    """Check if the catalog has content at a physical path.

    Traversal is not used, as acquisition would find objects outside the path.
    """
    catalog = site.portal_catalog
    brains = catalog.unrestrictedSearchResults(path={"query": path, "depth": 0})
    return bool(brains)


def get_export_query(
    site: PloneSite,
    include_paths: list[str] | None,
    paths_file: str | None,
    logger: logging.Logger,
) -> dict | None:
    """Return the catalog query for a partial export.

    Paths are relative to the site root. Each one selects that content and
    everything inside it. Paths with no content are skipped with a warning.

    :param site: Plone site being exported.
    :param include_paths: Paths given with ``--path``.
    :param paths_file: File given with ``--paths``.
    :param logger: Logger used to report problems.
    :returns: The catalog query, or ``None`` when no path was given.
    :raises SystemExit: If the file does not exist, or no path has content.
    """
    paths = list(include_paths or [])
    if paths_file:
        file_path = _process_path(paths_file)
        if not file_path:
            logger.error(f"{paths_file} does not exist, aborting export.")
            sys.exit(1)
        paths.extend(read_paths_file(file_path))
    if not paths:
        return None
    site_path = "/".join(site.getPhysicalPath())
    physical_paths = []
    for path in paths:
        relative = path.strip().strip("/")
        physical = f"{site_path}/{relative}" if relative else site_path
        if physical in physical_paths:
            continue
        if relative and not _content_exists(site, physical):
            logger.warning(f"No content at {path}, skipping it.")
            continue
        physical_paths.append(physical)
    if not physical_paths:
        logger.error("None of the given paths has content, aborting export.")
        sys.exit(1)
    return {"path": {"query": physical_paths}}


def get_site(app, site_id: str, logger: logging.Logger) -> PloneSite:
    """Get Plone Site"""
    site = app.unrestrictedTraverse(site_id, None)
    if not site:
        logger.error(f"Plone site at path '{site_id}' does not exist, aborting export.")
        sys.exit(1)
    return site
