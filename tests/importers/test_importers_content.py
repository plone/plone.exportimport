from collections.abc import Callable
from pathlib import Path
from plone import api
from plone.exportimport import interfaces
from plone.exportimport import settings
from plone.exportimport.importers import content
from zope.component import getAdapter

import json
import logging
import os
import pytest
import re
import shutil
import unicodedata


class TestImporterContent:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual_content):
        self.portal = portal_multilingual_content
        self.importer = content.ContentImporter(self.portal)

    def test_adapter_is_registered(self):
        adapter = getAdapter(
            self.portal, interfaces.INamedImporter, "plone.importer.content"
        )
        assert isinstance(adapter, content.ContentImporter)

    def test_output_is_str(self, multilingual_import_path):
        importer = self.importer
        result = importer.import_data(base_path=multilingual_import_path)
        assert isinstance(result, str)
        assert result == "ContentImporter: Imported 19 objects"

    def test_empty_import_path(self, empty_import_path):
        importer = self.importer
        result = importer.import_data(base_path=empty_import_path)
        assert isinstance(result, str)
        assert result == "ContentImporter: No data to import"


class TestImporterLocalPermissions:
    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path):
        self.portal = portal
        importer = content.ContentImporter(portal)
        importer.import_data(base_path=base_import_path)

    @pytest.mark.parametrize(
        "uid,permission_name,roles",
        [
            [
                "35661c9bb5be42c68f665aa1ed291418",
                "plone.app.contenttypes: Add Image",
                ["Manager"],
            ],
            [
                "e7359727ace64e609b79c4091c38822a",
                "plone.app.contenttypes: Add Image",
                ["Member"],
            ],
        ],
    )
    def test_permission_is_set(self, uid, permission_name, roles):
        from plone.exportimport.utils.content import object_from_uid

        content = object_from_uid(uid)
        for role in roles:
            all_permissions = [p["name"] for p in content.permissionsOfRole(role)]
            assert permission_name in all_permissions


class TestImporterParent:
    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path):
        self.portal = portal
        importer = content.ContentImporter(portal)
        importer.import_data(base_path=base_import_path)

    @pytest.mark.parametrize(
        "data,path",
        [
            [
                {"@id": "/", "@type": "Plone Site"},
                "/",
            ],
            [
                {"@id": "/bar"},
                "/plone",
            ],
            [
                {"@id": "/bar/2025.png"},
                "/plone/bar",
            ],
            [
                {"@id": "/bar/2025.png/parent-is-not-folderish"},
                None,
            ],
            [
                {"@id": "/foo/not-yet-created"},
                "/plone/foo",
            ],
            [
                {"@id": "/spaghetti/bolognese"},
                None,
            ],
        ],
    )
    def test_get_parent_from_item(self, data, path):
        from plone.exportimport.utils.content.import_helpers import get_parent_from_item

        parent = get_parent_from_item(data)
        found_path = parent.absolute_url_path() if parent is not None else None
        assert found_path == path


class TestImporterConstrains:
    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path):
        self.portal = portal
        importer = content.ContentImporter(portal)
        importer.import_data(base_path=base_import_path)

    @pytest.mark.parametrize(
        "uid,method,types",
        [
            [
                "35661c9bb5be42c68f665aa1ed291418",
                "getImmediatelyAddableTypes",
                ["Image"],
            ],
            [
                "35661c9bb5be42c68f665aa1ed291418",
                "getLocallyAllowedTypes",
                ["Document", "Image"],
            ],
        ],
    )
    def test_constrain_is_set(self, uid, method, types):
        from plone.base.interfaces.constrains import ISelectableConstrainTypes
        from plone.exportimport.utils.content import object_from_uid

        content = object_from_uid(uid)
        with api.env.adopt_roles(["Manager", "Site Administrator"]):
            behavior = ISelectableConstrainTypes(content, None)
            constrains = getattr(behavior, method)()
        for type_ in types:
            assert type_ in constrains


class TestImporterOrdering:
    """Test the ordering of imported items is correctly applied"""

    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path):
        self.portal = portal
        importer = content.ContentImporter(portal)
        importer.import_data(base_path=base_import_path)
        # Search for the items at Portal root ordering by position in parent
        brains = api.content.find(
            context=portal, depth=1, sort_on="getObjPositionInParent"
        )
        self.items: list[str] = [b.UID for b in brains]

    @pytest.mark.parametrize(
        "uid,idx",
        [
            ["3e0dd7c4b2714eafa1d6fc6a1493f953", 0],
            ["70844f7bec1843b8ab2796c972c9ebfe", 1],
            ["e7359727ace64e609b79c4091c38822a", 2],
        ],
    )
    def test_ordering_preserved(self, uid: str, idx: int):
        """Test that each item is at the expected index within the Portal root."""
        items: list[str] = self.items
        assert items.index(uid) == idx


class TestImporterProgressLogging:
    """Per-setter progress counter must reset between setter phases.

    Regression test for #92: ``enumerate(data, start=index)`` carried the
    counter across setters, so ``{setter}: Handled N items...`` reported a
    cumulative count instead of items handled by that setter.
    """

    HANDLED_RE = re.compile(r"^(?P<setter>\w+): Handled (?P<count>\d+) items")

    @pytest.fixture(autouse=True)
    def _init(self, portal, base_import_path, monkeypatch, caplog):
        monkeypatch.setattr(settings, "IMPORTER_REPORT", 1)
        caplog.set_level(logging.INFO, logger="plone.exportimport")
        content.ContentImporter(portal).import_data(base_path=base_import_path)
        self.handled = self._collect_handled(caplog.records)

    def _collect_handled(self, records) -> dict[str, list[int]]:
        seen: dict[str, list[int]] = {}
        for record in records:
            match = self.HANDLED_RE.match(record.getMessage())
            if not match:
                continue
            seen.setdefault(match["setter"], []).append(int(match["count"]))
        return seen

    def test_setters_logged(self):
        """At least two setters should have produced progress logs."""
        setter_logs = {k: v for k, v in self.handled.items() if k != "ContentImporter"}
        assert (
            len(setter_logs) >= 2
        ), f"Expected progress logs from ≥2 setters, got: {sorted(setter_logs)}"

    def test_each_setter_counter_resets(self):
        """First 'Handled N' line for each setter should start at 1."""
        for setter, counts in self.handled.items():
            if setter == "ContentImporter":
                continue
            assert counts[0] == 1, (
                f"Setter '{setter}' first reported count was {counts[0]}, "
                f"expected 1 (counter not reset between setters)."
            )


IMAGE_UID = "90b11c863598495ba699b22ca76b1041"
IMAGE_PATH = "/bar/2025.png"


@pytest.fixture()
def byte_exact_exists(monkeypatch):
    """Make Path.exists compare file names byte for byte, as Linux does.

    macOS filesystems find a file under either normalization form of its
    name, which would hide a mismatch between the two.
    """
    original = Path.exists

    def exists(self, *args, **kwargs) -> bool:
        if not original(self, *args, **kwargs):
            return False
        if not self.name:
            return True
        return self.name in os.listdir(self.parent)

    monkeypatch.setattr(Path, "exists", exists)


@pytest.fixture()
def blob_import_path(tmp_path, base_import_path) -> Path:
    """Writable copy of the base import."""
    path = tmp_path / "import"
    shutil.copytree(base_import_path, path)
    return path


@pytest.fixture()
def set_image_blob(blob_import_path) -> Callable:
    """Store the image blob of IMAGE_UID under a new name."""

    def func(blob_name: str, file_name: str | None) -> Path:
        item_path = blob_import_path / "content" / IMAGE_UID
        blob_dir = item_path / "image"
        blob_file = blob_dir / "2025.png"
        if file_name is None:
            blob_file.unlink()
        else:
            blob_file.rename(blob_dir / file_name)
        data_file = item_path / "data.json"
        data = json.loads(data_file.read_text())
        data["image"]["blob_path"] = f"{IMAGE_UID}/image/{blob_name}"
        data["image"]["filename"] = blob_name
        data_file.write_text(json.dumps(data))
        return blob_dir / blob_name

    return func


class TestImporterBlobs:
    @pytest.fixture(autouse=True)
    def _init(self, portal, blob_import_path):
        self.portal = portal
        self.base_path = blob_import_path
        self.importer = content.ContentImporter(portal)

    def test_blob_path_nfd_file_nfc(self, byte_exact_exists, set_image_blob):
        name = "Logotipo versão 3 (1-1.png"
        nfc = unicodedata.normalize("NFC", name)
        nfd = unicodedata.normalize("NFD", name)
        assert nfc != nfd
        blob_path = set_image_blob(nfd, nfc)
        # The export records NFD, the file on disk is NFC
        assert blob_path.exists() is False
        self.importer.import_data(base_path=self.base_path)
        obj = api.content.get(UID=IMAGE_UID)
        assert obj.image is not None
        assert obj.image.getSize() == 40383
        assert obj.image.filename == nfd
        assert self.importer.incomplete == {}

    def test_missing_blob_is_incomplete(self, set_image_blob, caplog):
        set_image_blob("2025.png", None)
        self.importer.import_data(base_path=self.base_path)
        obj = api.content.get(UID=IMAGE_UID)
        assert obj is not None
        assert obj.image is None
        assert self.importer.incomplete == {IMAGE_PATH: ["image"]}
        assert IMAGE_PATH not in self.importer.dropped
        messages = [record.getMessage() for record in caplog.records]
        assert "List of items imported with errors" in messages
        assert f" - {IMAGE_PATH} (fields: image)" in messages

    def test_complete_import(self):
        self.importer.import_data(base_path=self.base_path)
        assert self.importer.incomplete == {}
        assert self.importer.dropped == set()

    def test_reports_are_per_instance(self):
        other = content.ContentImporter(self.portal)
        self.importer.dropped.add("/foo")
        self.importer.incomplete["/foo"] = []
        assert other.dropped == set()
        assert other.incomplete == {}
