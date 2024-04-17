from plone.exportimport.interfaces import IExportImportRequestMarker
from plone.restapi.behaviors import IBlocks
from plone.restapi.deserializer.dxfields import DefaultFieldDeserializer
from plone.restapi.interfaces import IFieldDeserializer
from plone.schema import IJSONField
from zope.component import adapter
from zope.interface import implementer


@implementer(IFieldDeserializer)
@adapter(IJSONField, IBlocks, IExportImportRequestMarker)
class ExportImportBlocksDeserializer(DefaultFieldDeserializer):
    """We skip the subscribers that deserialize the blocks from the frontend.
    We only need the raw data.
    """
