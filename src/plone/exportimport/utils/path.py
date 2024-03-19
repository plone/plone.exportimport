from base64 import b64encode
from pathlib import Path


def get_parent_folder(path: Path, create: bool = True) -> Path:
    """Return the folder containing a path.

    If `create` is set to True, the folder will be created if it does not exist.
    """
    folder = path.parent
    if folder.exists():
        return folder
    elif create:
        folder.mkdir(parents=True, exist_ok=True)
        return folder
    raise ValueError(f"Folder at {folder} does not exist")


def encode_file_contents(path: Path) -> bytes:
    """Encode contents of file at given path as base64 bytes."""
    return b64encode(path.read_bytes())
