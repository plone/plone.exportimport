from base64 import b64encode
from pathlib import Path

import re
import unicodedata

# Characters not allowed in a file name on at least one of the supported
# filesystems (Windows forbids <>:"/\|?*, all of them forbid / and NUL).
_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
# Device names reserved by Windows, regardless of the extension.
_RESERVED_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{idx}" for idx in range(1, 10)]
    + [f"LPT{idx}" for idx in range(1, 10)]
)
# Most filesystems limit a file name to 255 bytes.
_MAX_FILENAME_BYTES = 255
# Longest suffix kept when a file name is truncated.
_MAX_SUFFIX_BYTES = 16
DEFAULT_FILENAME = "blob"


def _truncate(value: str, max_bytes: int) -> str:
    """Truncate a string to at most ``max_bytes`` UTF-8 bytes.

    :param value: String to truncate.
    :param max_bytes: Maximum length, in bytes, of the encoded string.
    :returns: The longest prefix of ``value`` that fits, never splitting a
        character.
    """
    return value.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")


def normalize_filename(filename: str | None) -> str:
    """Return a version of ``filename`` that is safe to write on any filesystem.

    The name is normalized to Unicode NFC, so the bytes written to disk do not
    depend on how the original name was composed. Path separators, control
    characters and characters invalid on Windows are replaced with ``_``,
    trailing dots and spaces are removed, Windows reserved device names are
    prefixed with ``_``, and the result is truncated to 255 UTF-8 bytes,
    preserving the extension.

    :param filename: Original file name, as stored in the field.
    :returns: Normalized file name, or :data:`DEFAULT_FILENAME` when nothing
        usable is left.
    """
    name = unicodedata.normalize("NFC", filename or "")
    name = _INVALID_CHARS.sub("_", name).rstrip(". ")
    if not name:
        return DEFAULT_FILENAME
    stem, dot, suffix = name.rpartition(".")
    if not stem:
        # No extension, or a name starting with a dot (".htaccess")
        stem, dot, suffix = name, "", ""
    if stem.split(".")[0].upper() in _RESERVED_NAMES:
        stem = f"_{stem}"
    name = f"{stem}{dot}{suffix}"
    if len(name.encode("utf-8")) > _MAX_FILENAME_BYTES:
        ending = f"{dot}{suffix}"
        if len(ending.encode("utf-8")) > _MAX_SUFFIX_BYTES:
            # Not a real extension: truncate the name as a whole
            stem, ending = name, ""
        max_stem = _MAX_FILENAME_BYTES - len(ending.encode("utf-8"))
        name = f"{_truncate(stem, max_stem).rstrip('. ')}{ending}"
    return name


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
