from pathlib import Path
from plone.exportimport.utils import path

import pytest


@pytest.fixture()
def base_path(tmp_path) -> Path:
    """Base Path."""
    for name in ("one", "two", "three"):
        sub_folder = tmp_path / name
        sub_folder.mkdir(exist_ok=True, parents=True)
    return tmp_path


@pytest.fixture()
def blob_file_path(base_import_path) -> Path:
    """Path to a blob file."""
    contents = base_import_path / "content"
    return contents / "90b11c863598495ba699b22ca76b1041" / "image" / "2025.png"


@pytest.mark.parametrize(
    "filepath,create,expected",
    [
        ["one/data.json", False, "one"],
        ["two/data.json", False, "two"],
        ["three/data.json", False, "three"],
        ["four/data.json", True, "four"],
        ["four/data.json", False, ""],
    ],
)
def test_get_parent_folder(base_path, filepath: str, create: bool, expected: str):
    func = path.get_parent_folder
    filepath = base_path / filepath
    if expected:
        expected = base_path / expected
        assert func(filepath, create) == expected
    else:
        with pytest.raises(ValueError) as exc:
            func(filepath, create)
        assert "does not exist" in str(exc)


def test_encode_file_contents(blob_file_path):
    func = path.encode_file_contents
    result = func(blob_file_path)
    assert isinstance(result, bytes)
