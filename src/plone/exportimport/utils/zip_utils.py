"""Utilities for ZIP file handling during export/import operations."""

from pathlib import Path
from typing import BinaryIO
from typing import Optional

import tempfile
import zipfile


def export_to_zip(
    export_path: Path,
    output_file: Optional[BinaryIO] = None,
) -> BinaryIO:
    """Compress an export directory into a ZIP file.

    Args:
        export_path: Path to the directory containing exported data
        output_file: Optional file object to write ZIP to. If None, a BytesIO
                     object is created and returned.

    Returns:
        The file object containing the ZIP data (positioned at the start)
    """
    if not export_path.is_dir():
        raise ValueError(f"Export path must be a directory: {export_path}")

    if output_file is None:
        from io import BytesIO

        output_file = BytesIO()

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk the export directory and add all files to the ZIP
        for file_path in export_path.rglob("*"):
            if file_path.is_file():
                # Calculate the archive name relative to the export_path
                arcname = file_path.relative_to(export_path)
                zipf.write(file_path, arcname=arcname)

    # Reset file pointer to the beginning
    output_file.seek(0)
    return output_file


def import_from_zip(
    zip_file: BinaryIO,
    import_path: Optional[Path] = None,
) -> Path:
    """Extract a ZIP file into a directory for import.

    Args:
        zip_file: File object containing ZIP data
        import_path: Optional directory to extract to. If None, a temporary
                     directory is created.

    Returns:
        Path to the directory containing extracted data
    """
    if import_path is None:
        import_path = Path(tempfile.mkdtemp(prefix="plone_exportimport_"))
    else:
        import_path = Path(import_path)
        import_path.mkdir(parents=True, exist_ok=True)

    # Reset file pointer to the beginning
    zip_file.seek(0)

    with zipfile.ZipFile(zip_file, "r") as zipf:
        zipf.extractall(import_path)

    return import_path
