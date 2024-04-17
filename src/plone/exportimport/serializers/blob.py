from pathlib import Path
from plone.dexterity.content import DexterityContent
from plone.dexterity.interfaces import IDexterityContent
from plone.exportimport import logger
from plone.exportimport import settings
from plone.exportimport import types
from plone.exportimport.interfaces import IExportImportRequestMarker
from plone.exportimport.utils import content as content_utils
from plone.exportimport.utils import path as path_utils
from plone.namedfile.interfaces import INamedBlobFileField
from plone.namedfile.interfaces import INamedBlobImageField
from plone.namedfile.interfaces import INamedFileField
from plone.namedfile.interfaces import INamedImageField
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.dxfields import DefaultFieldSerializer
from zope.component import adapter
from zope.globalrequest import getRequest
from zope.interface import implementer


@adapter(INamedBlobFileField, IDexterityContent, IExportImportRequestMarker)
@implementer(IFieldSerializer)
class ExportImportFileFieldSerializer(DefaultFieldSerializer):
    def __call__(self):
        namedfile = self.field.get(self.context)
        if namedfile:
            blob_path = export_blob(
                self.context, self.field.__name__, namedfile.filename, namedfile.data
            )
            result = {
                "filename": namedfile.filename,
                "content-type": namedfile.contentType,
                "size": namedfile.getSize(),
                "blob_path": str(blob_path),
            }
            return json_compatible(result)


@adapter(INamedFileField, IDexterityContent, IExportImportRequestMarker)
@implementer(IFieldSerializer)
class ExportImportSimpleFileFieldSerializer(ExportImportFileFieldSerializer):
    """Same as above but less specific field interface"""


@adapter(INamedBlobImageField, IDexterityContent, IExportImportRequestMarker)
@implementer(IFieldSerializer)
class ExportImportImageFieldSerializer(DefaultFieldSerializer):
    def __call__(self):
        namedfile = self.field.get(self.context)
        if namedfile is None:
            return None
        blob_path = export_blob(
            self.context, self.field.__name__, namedfile.filename, namedfile.data
        )
        width, height = namedfile.getImageSize()
        result = {
            "filename": namedfile.filename,
            "content-type": namedfile.contentType,
            "size": namedfile.getSize(),
            "width": width,
            "height": height,
            "blob_path": str(blob_path),
        }
        return json_compatible(result)


@adapter(INamedImageField, IDexterityContent, IExportImportRequestMarker)
@implementer(IFieldSerializer)
class ExportImportSimpleImageFieldSerializer(ExportImportImageFieldSerializer):
    """Same as above but less specific field interface"""


def export_blob(
    obj: DexterityContent, fieldname: str, filename: str, data: dict
) -> Path:
    """Store blob data in a way that makes it easier to edit by hand.

    Root path: settings.EXPORT_PATH_KEY
    File path: settings.EXPORT_CONTENT_BLOB_FILEPATH
    """
    request = getRequest()
    # Metadata
    metadata: types.ExportImportMetadata = request[settings.EXPORT_CONTENT_METADATA_KEY]
    uid = settings.SITE_ROOT_UID if content_utils.is_site_root(obj) else obj.UID()
    content_export_path = Path(request[settings.EXPORT_PATH_KEY])
    blob_path = settings.EXPORT_CONTENT_BLOB_FILEPATH.format(
        UID=uid, fieldname=fieldname, filename=filename
    )
    target_file = content_export_path / blob_path
    # Create target directory
    target_directory = path_utils.get_parent_folder(target_file)
    logger.debug(f"{uid}: Field {fieldname} blob directory set to {target_directory}")
    # Write file
    with open(target_file, "wb") as f:
        f.write(data)
    logger.debug(f"{uid}: Field {fieldname} blob written to {target_file}")
    relative_path = target_file.relative_to(content_export_path)
    metadata._blob_files_.append(str(relative_path))
    return relative_path
