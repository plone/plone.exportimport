from pathlib import Path
from plone.exportimport import types
from plone.exportimport.utils import content as utils
from plone.exportimport.utils import path as path_utils
from Products.CMFPlone.Portal import PloneSite
from typing import Any
from typing import Callable
from typing import List
from zope.globalrequest import getRequest

import json


class BaseExporter:
    name: str
    base_path: Path
    errors: list = None
    request: types.HTTPRequest = None
    data_hooks: List[Callable] = None
    obj_hooks: List[Callable] = None

    def __init__(
        self,
        site: PloneSite = None,
    ):
        self.site = site
        self.errors = []
        self.request = getRequest()

    @property
    def filepath(self) -> Path:
        """Filepath to be used during export."""
        filename = f"{self.name}.json"
        return self.base_path / filename

    def _serializer(self, obj: Any) -> Callable:
        """Serializer for object."""
        return utils.get_serializer(obj, self.request)

    def _dump(self, data: dict, filepath: Path = None) -> Path:
        """Dump serialized data to disk."""
        filepath = filepath if filepath else self.filepath
        # Create container, if it does not exist
        path_utils.get_parent_folder(filepath)
        with open(filepath, "w") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
        return filepath

    def dump(self) -> List[Path]:
        """Serialize objects."""
        return []

    def export_data(
        self,
        base_path: Path,
        data_hooks: List[Callable] = None,
        obj_hooks: List[Callable] = None,
    ) -> List[Path]:
        """Write data to filesystem."""
        if not base_path.exists():
            base_path.mkdir(parents=True)
        self.base_path = base_path
        self.data_hooks = self.data_hooks or data_hooks or []
        self.obj_hooks = self.obj_hooks or obj_hooks or []
        paths = self.dump()
        return paths
