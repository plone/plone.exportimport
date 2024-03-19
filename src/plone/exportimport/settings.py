from typing import Tuple


SITE_ROOT_UID = "plone_site_root"

EXPORT_CONTENT_FILEPATH = "{UID}/data.json"
EXPORT_CONTENT_BLOB_FILEPATH = "{UID}/{fieldname}/{filename}"
EXPORT_CONTENT_METADATA_KEY = "blob_export_list"

EXPORT_PATH_KEY = "content_export_directory"
IMPORT_PATH_KEY = "content_import_directory"


SERIALIZER_CONSTRAINS_KEY = "exportimport.constrains"

PLACEHOLDERS_LANGUAGE = "##DEFAULT##"

AUTO_GROUPS: Tuple[str] = ("AuthenticatedUsers",)
AUTO_ROLES: Tuple[str] = ("Authenticated",)
