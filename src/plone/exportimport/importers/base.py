from pathlib import Path
from plone.exportimport import types
from plone.exportimport.utils import content as utils
from Products.CMFPlone.Portal import PloneSite
from typing import Any
from typing import Callable
from typing import List
from typing import Optional
from typing import Union
from zope.globalrequest import getRequest

import json


class BaseImporter:
    name: str
    base_path: Path
    site: PloneSite
    errors: Optional[list] = None
    request: Optional[types.HTTPRequest] = None
    data_hooks: Optional[List[Callable]] = None
    pre_deserialize_hooks: Optional[List[Callable]] = None
    obj_hooks: Optional[List[Callable]] = None

    def __init__(
        self,
        site: PloneSite,
    ):
        self.request = getRequest()
        self.site = site

    @property
    def filepath(self) -> Path:
        """Filepath to be used during import."""
        filename = f"{self.name}.json"
        return self.base_path / filename

    def _deserializer(self, obj: Any) -> Callable:
        """Deserializer for object."""
        return utils.get_deserializer(obj, self.request)

    def _read(self, filepath: Optional[Path] = None) -> Union[dict, list, None]:
        """Read data from file."""
        filepath = filepath if filepath else self.filepath
        if filepath.exists() and filepath.is_file():
            with open(filepath) as fh:
                data = json.load(fh)
            return data

    def do_import(self) -> str:
        """Deserialize objects."""
        return ""

    def import_data(
        self,
        base_path: Path,
        data_hooks: Optional[List[Callable]] = None,
        pre_deserialize_hooks: Optional[List[Callable]] = None,
        obj_hooks: Optional[List[Callable]] = None,
    ) -> str:
        """Import data into a Plone site."""
        if not base_path.exists():
            return f"{self.__class__.__name__}: Import path does not exist"
        self.base_path = base_path
        self.data_hooks = self.data_hooks or data_hooks or []
        pre_deserialize_hooks = (
            self.pre_deserialize_hooks or pre_deserialize_hooks or []
        )
        self.obj_hooks = self.obj_hooks or obj_hooks or []
        report = self.do_import()
        return report


class BaseDatalessImporter(BaseImporter):
    """Base for an import that does not read json data files.

    Generally this would iterate over all existing content objects and do
    some updates.
    """

    def import_data(
        self,
        base_path: Path,
        data_hooks: Optional[List[Callable]] = None,
        pre_deserialize_hooks: Optional[List[Callable]] = None,
        obj_hooks: Optional[List[Callable]] = None,
    ) -> str:
        """Import data into a Plone site.

        Note that we ignore the json data related arguments.
        """
        self.obj_hooks = self.obj_hooks or obj_hooks or []
        return self.do_import()
