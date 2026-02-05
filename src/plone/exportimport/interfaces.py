"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface


class IExportImportRequestMarker(Interface):
    """A marker interface to override default serializers."""


class IExporter(Interface):
    """Component to export content from a Plone Site."""


class IImporter(Interface):
    """Component to import content from a Plone Site."""


class INamedExporter(Interface):
    """Component to export content from a Plone Site."""


class INamedImporter(Interface):
    """Component to import content from a Plone Site."""
