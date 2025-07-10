from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.users import system as user
from pathlib import Path
from plone.restapi.interfaces import IPloneRestapiLayer
from Products.CMFPlone.Portal import PloneSite
from Testing.makerequest import makerequest
from typing import Optional
from Zope2.Startup.run import make_wsgi_app
from zope.globalrequest import setRequest
from zope.interface import directlyProvidedBy
from zope.interface import directlyProvides

import logging
import sys
import Zope2


def _process_path(path: str) -> Optional[Path]:
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


def get_site(app, site_id: str, logger: logging.Logger) -> Optional[PloneSite]:
    """Get Plone Site"""
    try:
        return app.unrestrictedTraverse(site_id)
    except KeyError:
        logger.error(f"Plone site with id '{site_id}' does not exist, aborting export.")
        sys.exit(1)
