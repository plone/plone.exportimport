from typing import Tuple

import os


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

# Savepoint and commit changes
IMPORTER_COMMIT_DISABLE: bool = bool(os.environ.get("IMPORTER_COMMIT_DISABLE", 0))
IMPORTER_COMMIT_AFTER = int(os.environ.get("IMPORTER_COMMIT_AFTER", 1000))
IMPORTER_SAVEPOINT_AFTER = int(os.environ.get("IMPORTER_SAVEPOINT_AFTER", 100))
IMPORTER_REPORT = int(os.environ.get("IMPORTER_REPORT", 100))
