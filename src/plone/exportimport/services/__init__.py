"""REST API endpoints for export/import operations."""

from io import BytesIO
from plone import api
from plone.exportimport.exporters import get_exporter
from plone.exportimport.importers import get_importer
from plone.exportimport.utils import zip_utils
from plone.restapi.services import Service

import shutil


class ExportService(Service):
    """REST API endpoint to export site data as a ZIP file.

    POST /plone/@export
    """

    def render(self):
        """Handle POST request to export site data."""

        # Get the exporter for the current site
        site = api.portal.get()
        exporter = get_exporter(site)

        # Export to a temporary directory
        export_paths = exporter.export_site()
        export_path = export_paths[0]  # First path is the root export directory

        # Create a ZIP file from the export
        zip_data = zip_utils.export_to_zip(export_path)

        # Clean up the temporary export directory
        shutil.rmtree(export_path)

        # Return the ZIP file as a response
        self.request.response.setHeader("Content-Type", "application/zip")
        self.request.response.setHeader(
            "Content-Disposition",
            'attachment; filename="plone_export.zip"',
        )

        return zip_data.getvalue()


class ImportService(Service):
    """REST API endpoint to import site data from a ZIP file.

    POST /plone/@import
    """

    def reply(self):
        """Handle POST request to import site data."""

        # Get the uploaded ZIP file from the request
        if "file" not in self.request.form:
            self.request.response.setStatus(400)
            return {"error": "No file provided"}

        uploaded_file = self.request.form["file"]

        # Handle different file object types
        if hasattr(uploaded_file, "read"):
            zip_data = BytesIO(uploaded_file.read())
        else:
            self.request.response.setStatus(400)
            return {"error": "Invalid file format"}

        # Extract the ZIP file to a temporary directory
        import_path = zip_utils.import_from_zip(zip_data)

        try:
            # Get the importer for the current site
            site = api.portal.get()
            importer = get_importer(site)

            # Import the data
            report = importer.import_site(import_path)

            return {
                "status": "success",
                "report": report,
            }

        finally:
            # Clean up the temporary import directory
            shutil.rmtree(import_path)
