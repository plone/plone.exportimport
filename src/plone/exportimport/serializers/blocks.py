from plone.exportimport.interfaces import IExportImportRequestMarker
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.dxfields import DefaultFieldSerializer
from plone.schema import IJSONField
from zope.component import adapter
from zope.interface import implementer


@adapter(IJSONField, IBlocks, IExportImportRequestMarker)
@implementer(IFieldSerializer)
class ExportImportBlocksSerializer(DefaultFieldSerializer):
    """We skip the subscribers that serialize the blocks for the frontend.
    We only need the raw data.
    """
