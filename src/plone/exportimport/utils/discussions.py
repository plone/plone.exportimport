from .content.core import get_uid
from .content.core import object_from_uid
from .content.export_helpers import get_serializer
from .content.export_helpers import rewrite_site_root
from .dates import parse_datetime
from Acquisition import aq_base
from BTrees.LLBTree import LLSet
from plone import api
from plone.app.discussion.comment import Comment
from plone.app.discussion.conversation import Conversation
from plone.app.discussion.interfaces import IConversation
from plone.exportimport import logger
from Products.CMFCore.interfaces import IContentish
from Products.PortalTransforms.TransformEngine import TransformTool
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from zope.annotation.interfaces import IAnnotations
from zope.globalrequest import getRequest


DISCUSSION_ANNOTATION_KEY = "plone.app.discussion:conversation"


def _get_all_content_support_conversation() -> List[Tuple[str, Conversation]]:
    catalog = api.portal.get_tool("portal_catalog")
    results = []
    brains = catalog.unrestrictedSearchResults(
        object_provides=IContentish.__identifier__, sort_on="path"
    )
    for brain in brains:
        content = brain.getObject()
        obj = IConversation(content, None)
        if obj:
            content_uid = get_uid(content)
            results.append((content_uid, obj))
    return results


def get_discussions() -> Dict[str, Any]:
    """Get all discussions."""
    request = getRequest()
    portal_url = api.portal.get().absolute_url()
    all_objects = _get_all_content_support_conversation()
    results = {}
    for content_uid, conversation in all_objects:
        serializer = get_serializer(conversation, request)
        data = serializer()
        if data:
            # Remove conversation @id
            data.pop("@id", "")
            # Rewrite site root
            results[content_uid] = rewrite_site_root(data, portal_url)
    return results


def _extract_text(
    text: Union[dict, str], target_mime_type: str, transforms: TransformTool
) -> str:
    """Transform text data."""
    result = text
    if isinstance(text, dict):
        data = text.get("data", "")
        source_mime_type = text.get("mime-type", "text/plain")
        transform = transforms.convertTo(
            target_mime_type, data, mimetype=source_mime_type
        )
        result = transform.getData()
    return result


def _create_comment(item: dict, text: str) -> Comment:
    """Create a comment from a dictionary."""
    comment = Comment()
    comment.comment_id = int(item["comment_id"])
    comment.creation_date = parse_datetime(item["creation_date"])
    comment.modification_date = parse_datetime(item["modification_date"])
    comment.author_name = item["author_name"]
    comment.author_username = item["author_username"]
    comment.creator = item["author_username"]
    comment.text = text
    comment.user_notification = item.get("user_notification", True)
    if item.get("in_reply_to"):
        comment.in_reply_to = int(item["in_reply_to"])
    return comment


def set_discussions(data: dict) -> List[dict]:
    """Set all discussions."""
    results = []
    transforms = api.portal.get_tool("portal_transforms")
    prefix = "plone.app.discussion.interfaces.IDiscussionSettings"
    text_transform = api.portal.get_registry_record(
        f"{prefix}.text_transform", default="text/plain"
    )
    for obj_uid, conversation in data.items():
        conversation_items = conversation.get("items", [])
        if not conversation_items:
            logger.debug(f"- Discussions: No conversation items for object {obj_uid}")
            continue
        obj = object_from_uid(obj_uid)
        # Conversation
        conversation = IConversation(obj)
        base_conversation = aq_base(conversation)
        annotations = IAnnotations(obj)
        if DISCUSSION_ANNOTATION_KEY not in annotations:
            annotations[DISCUSSION_ANNOTATION_KEY] = base_conversation

        total = 0
        for item in conversation_items:
            # Process text
            text = _extract_text(item["text"], text_transform, transforms)
            # Create comment
            comment = _create_comment(item, text)
            comment_id = comment.comment_id
            commentator = comment.author_username
            conversation._comments[comment.comment_id] = comment
            comment.__parent__ = base_conversation
            if commentator:
                if commentator not in conversation._commentators:
                    conversation._commentators[commentator] = 0
                conversation._commentators[commentator] += 1

            # Handle reply
            reply_to = comment.in_reply_to
            if not reply_to:
                # top level comments are in reply to the faux id 0
                comment.in_reply_to = reply_to = 0
            if reply_to not in conversation._children:
                conversation._children[reply_to] = LLSet()
            conversation._children[reply_to].insert(comment_id)

            total += 1
        results.append({"uid": obj_uid, "total": total})
    return results
