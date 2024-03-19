from plone import api
from plone.dexterity.content import DexterityContent
from plone.exportimport.utils.principals.members import get_history_user_info
from typing import List


def _format_as_history(vdata: dict, version_id: int) -> dict:
    """Transform version data to the format of history entries."""
    meta = vdata["metadata"]["sys_metadata"]
    userid = meta["principal"]
    info = {
        "type": "versioning",
        "action": "Edited",
        "transition_title": "Edited",
        "actorid": userid,
        "time": meta["timestamp"],
        "comments": meta["comment"],
        "version_id": version_id,
        "preview_url": "",
        "revert_url": None,
    }
    info.update(get_history_user_info(userid))
    return info


def revision_history(obj: DexterityContent) -> List[dict]:
    """Return revision history for an object."""
    raw_history = []
    results = []
    rt = api.portal.get_tool("portal_repository")
    versionable = bool(rt.isVersionable(obj) if rt else False)
    if versionable:
        raw_history = rt.getHistoryMetadata(obj)

    # History may be an empty list
    if raw_history:
        retrieve = raw_history.retrieve
        getId = raw_history.getVersionId
        # Count backwards from most recent to least recent
        for i in range(raw_history.getLength(countPurged=False) - 1, -1, -1):
            version_data = retrieve(i, countPurged=False)
            version_id = getId(i, countPurged=False)
            results.append(_format_as_history(version_data, version_id))

    return results
