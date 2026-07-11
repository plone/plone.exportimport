from plone.exportimport.utils.content import revisions as revisions_utils

import pytest


class TestUtilsContentRevisions:
    @pytest.fixture(autouse=True)
    def _init(self, portal, create_example_content):
        from plone.exportimport.utils.content.core import get_obj_path

        self.portal = portal
        example_content = create_example_content(portal)
        contents = {
            get_obj_path(content, True): content for content in example_content.values()
        }
        self.folder = contents["/a-folderish"]
        self.link = contents["/a-folderish/a-link"]

    def test_revision_history(self):
        func = revisions_utils.revision_history
        revisions = func(self.link)
        assert isinstance(revisions, list)
        assert len(revisions) == 1
        version = revisions[0]
        assert isinstance(version, dict)
