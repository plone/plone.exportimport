"""Tests for the import REST API endpoint."""

import io
import pytest
import zipfile


def _zip_contents(data: io.BytesIO) -> dict[str, bytes]:
    """Return the name and content of each file in a ZIP archive."""
    with zipfile.ZipFile(data, "r") as zipf:
        return {name: zipf.read(name) for name in zipf.namelist()}


class TestExportImportServices:
    """Tests for the @export and @import endpoints."""

    @pytest.fixture(autouse=True)
    def _setup(self, api_session_manager):
        self.api_session = api_session_manager

    def test_export_requires_permission(self, api_session_anonymous):
        """Test that the export endpoint requires the export permission."""
        response = api_session_anonymous.post(
            "/@export",
        )
        assert response.status_code == 401

    def test_import_requires_permission(self, api_session_anonymous):
        """Test that the import endpoint requires the import permission."""
        response = api_session_anonymous.post(
            "/@import",
        )
        assert response.status_code == 401

    def test_export_import_roundtrip(self):
        """Test exporting and then importing data."""
        # Export
        """Test that data is exported as a zip file."""
        response = self.api_session.post(
            "/@export",
        )
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/zip"
        data1 = io.BytesIO(response.content)

        # Verify ZIP contents
        with zipfile.ZipFile(data1, "r") as zipf:
            namelist = zipf.namelist()
            assert len(namelist) > 0

        # Import
        response = self.api_session.post(
            "/@import",
            files={"file": ("plone_export.zip", data1.getvalue(), "application/zip")},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Export again to verify it's unchanged
        response = self.api_session.post(
            "/@export",
        )
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/zip"
        data2 = io.BytesIO(response.content)
        # Compare the files inside the archives, not the archives themselves:
        # each entry stores the file modification time, which differs between
        # two exports made a few seconds apart.
        assert _zip_contents(data1) == _zip_contents(data2)
