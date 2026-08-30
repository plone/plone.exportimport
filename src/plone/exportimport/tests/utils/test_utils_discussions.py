from plone.exportimport.utils import discussions as discussions_utils

import pytest


@pytest.fixture
def prepare_discussion_payload():
    def func(content) -> dict:
        from plone.exportimport.utils.content.core import get_obj_path

        content_path = get_obj_path(content, True)
        data = {
            content.UID(): {
                "items": [
                    {
                        "@id": f"/{content_path}/@comments/1707855876188968",
                        "@type": "Discussion Item",
                        "@parent": None,
                        "comment_id": "1707855876188968",
                        "in_reply_to": None,
                        "text": {"data": "One Comment", "mime-type": "text/plain"},
                        "user_notification": False,
                        "author_username": "admin",
                        "author_name": "admin",
                        "author_image": None,
                        "creation_date": "2024-02-13T20:24:36+00:00",
                        "modification_date": "2024-02-13T20:24:36+00:00",
                        "is_editable": False,
                        "is_deletable": True,
                        "can_reply": False,
                    },
                    {
                        "@id": f"/{content_path}/@comments/1707855883837698",
                        "@type": "Discussion Item",
                        "comment_id": "1707855889398074",
                        "in_reply_to": "1707855883837698",
                        "text": {"data": "Bar Foo", "mime-type": "text/plain"},
                        "user_notification": False,
                        "author_username": "admin",
                        "author_name": "admin",
                        "author_image": None,
                        "creation_date": "2024-02-13T20:24:49+00:00",
                        "modification_date": "2024-02-13T20:24:49+00:00",
                        "is_editable": False,
                        "is_deletable": True,
                        "can_reply": False,
                    },
                ]
            }
        }
        return data

    return func


class TestUtilsDiscussions:
    @pytest.fixture(autouse=True)
    def _init(self, portal, setup_discussion, create_example_content):
        from plone.exportimport.utils.content.core import get_obj_path

        self.portal = portal
        # Enable discussion for pages
        setup_discussion(["Document"])
        example_content = create_example_content(portal)
        contents = {
            get_obj_path(content, True): content for content in example_content.values()
        }
        self.page_01 = contents["/a-folderish/a-page"]
        self.page_02 = contents["/a-folderish/another-page"]

    def test_get_relations(self):
        func = discussions_utils.get_discussions
        results = func()
        assert isinstance(results, dict)
        assert len(results) == 0

    def test_set_relations(self, prepare_discussion_payload):
        before = discussions_utils.get_discussions()
        data = prepare_discussion_payload(self.page_01)
        func = discussions_utils.set_discussions
        results = func(data)
        assert isinstance(results, list)
        assert len(results) == 1
        assert len(discussions_utils.get_discussions()) > len(before)

    def test_set_relations_empty_items(self, prepare_discussion_payload):
        data = prepare_discussion_payload(self.page_01)
        data = {k: {"items": []} for k in data}
        func = discussions_utils.set_discussions
        results = func(data)
        assert isinstance(results, list)
        assert len(results) == 0
