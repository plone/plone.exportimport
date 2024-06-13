from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from Products.CMFPlone.Portal import PloneSite
from typing import Callable
from typing import Dict
from typing import List
from ZPublisher.HTTPRequest import HTTPRequest


@dataclass
class PortalLanguages:
    """Languages configuration in a portal."""

    default: str
    available: List[str]


@dataclass
class ExportImportMetadata:
    """Export import metadata info."""

    default_page: dict = field(default_factory=dict)
    ordering: dict = field(default_factory=dict)
    local_roles: dict = field(default_factory=dict)
    local_permissions: dict = field(default_factory=dict)
    relations: list = field(default_factory=list)
    __version__: str = "1.0.0"
    _data_files_: List[str] = field(default_factory=list)
    _blob_files_: List[str] = field(default_factory=list)
    _all_: Dict[str, str] = field(default_factory=dict)

    def export(self) -> dict:
        dump = asdict(self)
        files = dump.pop("_all_", {})
        dump["_data_files_"] = [v for _, v in sorted(files.items())]
        return dump


@dataclass
class ExportImportHelper:
    """Helper functions."""

    func: Callable
    name: str
    description: str


@dataclass
class ExporterConfig:
    """Export configuration used by helper functions ."""

    site: PloneSite
    site_root_uid: str
    request: HTTPRequest
    serializer: Callable
    logger_prefix: str


@dataclass
class ImporterConfig:
    """Import configuration used by helper functions ."""

    site: PloneSite
    site_root_uid: str
    languages: PortalLanguages
    request: HTTPRequest
    logger_prefix: str
