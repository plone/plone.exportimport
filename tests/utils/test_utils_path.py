from pathlib import Path
from plone.exportimport.utils import path

import pytest
import unicodedata


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


@pytest.mark.parametrize(
    "filename,expected",
    [
        ["2025.png", "2025.png"],
        ["Logotipo (1-1.png", "Logotipo (1-1.png"],
        ["../../etc/passwd", ".._.._etc_passwd"],
        ["folder/image.png", "folder_image.png"],
        ["folder\\image.png", "folder_image.png"],
        ['a<b>c:d"e|f?g*h.txt', "a_b_c_d_e_f_g_h.txt"],
        ["tab\there.txt", "tab_here.txt"],
        ["report. ", "report"],
        ["report.pdf...", "report.pdf"],
        ["CON", "_CON"],
        ["con.txt", "_con.txt"],
        ["LPT1.tar.gz", "_LPT1.tar.gz"],
        ["CONSOLE.txt", "CONSOLE.txt"],
        [".htaccess", ".htaccess"],
        ["", path.DEFAULT_FILENAME],
        [None, path.DEFAULT_FILENAME],
        [".", path.DEFAULT_FILENAME],
        ["..", path.DEFAULT_FILENAME],
        ["   ", path.DEFAULT_FILENAME],
    ],
)
def test_normalize_filename(filename: str | None, expected: str):
    func = path.normalize_filename
    assert func(filename) == expected


def test_normalize_filename_nfc():
    name = "Logotipo versão 3 (1-1.png"
    nfc = unicodedata.normalize("NFC", name)
    nfd = unicodedata.normalize("NFD", name)
    # Both forms render the same, but differ byte for byte
    assert nfc != nfd
    func = path.normalize_filename
    assert func(nfd) == nfc
    assert func(nfc) == nfc


@pytest.mark.parametrize(
    "filename,suffix",
    [
        ["a" * 300 + ".png", ".png"],
        ["ã" * 300 + ".png", ".png"],
        ["a" * 300, ""],
        ["a" * 100 + "." + "b" * 200, ""],
    ],
)
def test_normalize_filename_length(filename: str, suffix: str):
    result = path.normalize_filename(filename)
    assert len(result.encode("utf-8")) <= 255
    assert result.endswith(suffix)
    assert filename.startswith(result.removesuffix(suffix))
