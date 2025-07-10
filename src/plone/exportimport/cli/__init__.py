from plone import api
from plone.exportimport import logger as package_logger
from plone.exportimport.exporters import get_exporter
from plone.exportimport.importers import get_importer
from plone.exportimport.utils import cli as cli_helpers
from zope.component import hooks

import argparse
import sys
import transaction


CLI_SPEC = {
    "exporter": {
        "description": "Export Plone Site content",
        "options": {
            "zopeconf": "Path to zope.conf",
            "site": "Plone site ID or path to site to export the content from",
            "path": "Path to export the content",
            "--include-revisions": "Include revision history",
        },
    },
    "importer": {
        "description": "Import content into a Plone Site",
        "options": {
            "zopeconf": "Path to zope.conf",
            "site": "Plone site ID or path to site to import the content to",
            "path": "Path to import the content from",
            "--quiet": "Do not report items being imported",
        },
    },
}


def _parse_args(description: str, options: dict, args: list):
    parser = argparse.ArgumentParser(description=description)
    for key, help in options.items():
        if key.startswith("-"):
            parser.add_argument(key, action="store_true", help=help)
        else:
            parser.add_argument(key, help=help)
    namespace, _ = parser.parse_known_args(args[1:])
    return namespace


def exporter_cli(args=sys.argv):
    """Export a Plone site."""
    logger = cli_helpers.get_logger("Exporter")
    exporter_cli = CLI_SPEC["exporter"]
    # We get an argparse.Namespace instance.
    namespace = _parse_args(exporter_cli["description"], exporter_cli["options"], args)
    app = cli_helpers.get_app(namespace.zopeconf)
    path = cli_helpers._process_path(namespace.path)
    if not path:
        logger.error(f"{namespace.path} does not exist, please create it first.")
        sys.exit(1)
    site = cli_helpers.get_site(app, namespace.site, logger)
    with api.env.adopt_roles(["Manager"]):
        results = get_exporter(site).export_site(path, options=namespace)
    logger.info(f" Using path {path} to export content from Plone site at /{site.id}")
    for item in results[1:]:
        logger.info(f" Wrote {item}")


def importer_cli(args=sys.argv):
    """Import content to a Plone site."""
    logger = cli_helpers.get_logger("Importer")
    importer_cli = CLI_SPEC["importer"]
    namespace = _parse_args(importer_cli["description"], importer_cli["options"], args)
    app = cli_helpers.get_app(namespace.zopeconf)
    path = cli_helpers._process_path(namespace.path)
    if not path:
        logger.error(f"{namespace.path} does not exist, aborting import.")
        sys.exit(1)
    # Unless explicitly set, we report object creation
    if not namespace.quiet:
        cli_helpers.setup_logger_console(package_logger)
    site = cli_helpers.get_site(app, namespace.site, logger)
    with hooks.site(site), api.env.adopt_roles(["Manager"]):
        logger.info(f" Using path {path} to import content to Plone site at /{site.id}")
        results = get_importer(site).import_site(path)
        for item in results:
            logger.info(f" - {item}")
        transaction.commit()
