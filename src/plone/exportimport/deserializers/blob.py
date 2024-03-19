from pathlib import Path
from plone.dexterity.interfaces import IDexterityContent
from plone.exportimport import settings
from plone.exportimport.interfaces import IExportImportBlobsMarker
from plone.exportimport.utils import path as path_utils
from plone.namedfile.interfaces import INamedField
from plone.restapi.deserializer.dxfields import DefaultFieldDeserializer
from plone.restapi.interfaces import IFieldDeserializer
from zope.component import adapter
from zope.globalrequest import getRequest
from zope.interface import implementer

import codecs


def load_blob(path: str) -> bytes:
    """Load blob from fs and encode it as base64."""
    request = getRequest()
    content_import_path = Path(request[settings.IMPORT_PATH_KEY])
    path = content_import_path / path
    if not path.exists():
        raise ValueError(f"Blob not found at {path}")
    data = path_utils.encode_file_contents(path)
    return codecs.decode(data, "base64")


@adapter(INamedField, IDexterityContent, IExportImportBlobsMarker)
@implementer(IFieldDeserializer)
class ExportImportNamedFieldDeserializer(DefaultFieldDeserializer):
    def __call__(self, value):
        result = None
        blob_path = value.pop("blob_path", "")
        content_type = value.get("content-type", "application/octet-stream")
        filename = value.get("filename", None)
        data = load_blob(blob_path)
        # Convert if we have data
        if data:
            result = self.field._type(
                data=data, contentType=content_type, filename=filename
            )

        # Always validate to check for required fields
        self.field.validate(result)
        return result
