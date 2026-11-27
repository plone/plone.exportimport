from plone import api
from plone.base.interfaces.constrains import DISABLED
from plone.base.interfaces.constrains import ISelectableConstrainTypes
from plone.dexterity.utils import createContentInContainer
from plone.exportimport.exporters.content import ContentExporter
from plone.exportimport.importers.content import ContentImporter
from plone.namedfile.file import NamedBlobImage
from plone.uuid.interfaces import ATTRIBUTE_NAME

import base64
import json
import pytest
import re

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _exported_items(export_path, uid: str) -> list[dict]:
    """Return the exported data.json items whose UID starts with ``uid``."""
    items = []
    for path in (export_path / "content").glob("*/data.json"):
        data = json.loads(path.read_text())
        if data.get("UID", "").startswith(uid):
            items.append(data)
    return items


def _to_pre_fix_format(export_path, uid: str):
    """Rewrite a current export the way earlier versions wrote it.

    Earlier versions exported one item per language copy, each under its
    reported UID (``<uid>-<language>``). Only the English copy is kept here.
    """
    content = export_path / "content"
    meta_path = content / "__metadata__.json"
    meta = json.loads(meta_path.read_text())
    copies = re.compile(rf"/{re.escape(uid)}-(?!en/)")
    meta["_data_files_"] = [
        filepath for filepath in meta["_data_files_"] if not copies.search(filepath)
    ]
    meta_path.write_text(json.dumps(meta))
    pattern = re.compile(rf"{re.escape(uid)}(?!-)")
    for path in export_path.rglob("*.json"):
        path.write_text(pattern.sub(f"{uid}-en", path.read_text()))
    if (content / uid).exists():
        (content / uid).rename(content / f"{uid}-en")


class TestImporterContentLIF:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual, export_path):
        self.portal = portal_multilingual
        self.export_path = export_path

    def _create_lif_image(self):
        portal = self.portal
        ISelectableConstrainTypes(portal["en"]).setConstrainTypesMode(DISABLED)
        with api.env.adopt_roles(["Manager"]):
            lif = createContentInContainer(
                portal["en"],
                "LIF",
                checkConstraints=False,
                id="assets-lif",
                title="Assets",
            )
            image = api.content.create(
                container=lif,
                type="Image",
                id="pic",
                title="Picture",
                image=NamedBlobImage(data=PNG, filename="pic.png"),
                language="en",
            )
        return lif, image

    def test_lif_object_is_exported_once_and_resolves_after_import(self):
        lif, image = self._create_lif_image()
        uid = getattr(image, ATTRIBUTE_NAME)
        ContentExporter(self.portal).export_data(base_path=self.export_path)
        items = _exported_items(self.export_path, uid)
        assert len(items) == 1
        assert items[0]["UID"] == uid

        with api.env.adopt_roles(["Manager"]):
            api.content.delete(obj=lif, check_linkintegrity=False)
        ContentImporter(self.portal).import_data(base_path=self.export_path)

        en_obj = api.content.get(UID=f"{uid}-en")
        de_obj = api.content.get(UID=f"{uid}-de")
        assert en_obj is not None
        assert de_obj is not None
        assert "/en/" in "/".join(en_obj.getPhysicalPath())
        assert "/de/" in "/".join(de_obj.getPhysicalPath())
        assert api.content.get(UID=f"{uid}-en-en") is None

    def test_export_from_earlier_version_still_imports(self):
        lif, image = self._create_lif_image()
        uid = getattr(image, ATTRIBUTE_NAME)
        ContentExporter(self.portal).export_data(base_path=self.export_path)
        _to_pre_fix_format(self.export_path, uid)
        with api.env.adopt_roles(["Manager"]):
            api.content.delete(obj=lif, check_linkintegrity=False)
        ContentImporter(self.portal).import_data(base_path=self.export_path)

        obj = self.portal.unrestrictedTraverse("en/assets-lif/pic")
        # The suffixed UID from the old export is stored as it was written.
        assert getattr(obj, ATTRIBUTE_NAME).startswith(f"{uid}-")
