"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface


class IExportImportBlobsMarker(Interface):
    """A marker interface to override default serializers."""


class IExporterUtility(Interface):
    """Component to export content from a Plone Site."""


class IImporterUtility(Interface):
    """Component to import content from a Plone Site."""


class INamedExporter(Interface):
    """Component to export content from a Plone Site."""


class INamedImporter(Interface):
    """Component to export content from a Plone Site."""
