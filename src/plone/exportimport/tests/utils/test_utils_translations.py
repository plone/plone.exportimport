from plone.exportimport.utils import translations as translations_utils

import pytest


@pytest.fixture
def translate_content():
    def func(all_contents: dict, canonical: str, translation: str, language: str):
        translations_utils.link_translations(
            canonical_obj=all_contents[canonical],
            translation_obj=all_contents[translation],
            language=language,
        )

    return func


@pytest.fixture
def translate_all_content():
    def func(content_by_language: dict):
        en_content = content_by_language["en"]
        for path, canonical in en_content.items():
            for language in ("es", "de"):
                translation_path = path.replace("/en/", f"/{language}/")
                translation = content_by_language[language][translation_path]
                translations_utils.link_translations(
                    canonical_obj=canonical,
                    translation_obj=translation,
                    language=language,
                )

    return func


class TestUtilsTranslationsWithoutPAM:
    @pytest.fixture(autouse=True)
    def _init(self, portal):
        self.portal = portal

    def test_has_translation_support(self):
        func = translations_utils.has_translation_support
        results = func(self.portal.portal_catalog)
        assert results is False

    def test__get_all_translation_groups(self):
        func = translations_utils._get_all_translation_groups
        results = func(self.portal.portal_catalog)
        assert isinstance(results, tuple)
        assert len(results) == 0


class TestUtilsTranslationsWithPAM:
    @pytest.fixture(autouse=True)
    def _init(self, portal_multilingual, create_example_content):
        from plone.exportimport.utils.content.core import get_obj_path

        self.portal = portal_multilingual
        all_contents = {}
        content_by_language = {}
        for language in ("en", "es", "de"):
            content_by_language[language] = {}
            lrf = self.portal[language]
            example_content = create_example_content(lrf, language)
            for content in example_content.values():
                content_path = get_obj_path(content, True)
                all_contents[content_path] = content
                content_by_language[language][content_path] = content
        self.all_contents = all_contents
        self.content_by_language = content_by_language

    def test_has_translation_support(self):
        func = translations_utils.has_translation_support
        results = func(self.portal.portal_catalog)
        assert results is True

    def test__get_all_translation_groups(self):
        func = translations_utils._get_all_translation_groups
        results = func(self.portal.portal_catalog)
        assert isinstance(results, tuple)
        assert len(results) > 0

    @pytest.mark.parametrize(
        "canonical,translation,language,expected",
        [
            ["/en/a-folderish", "/de/a-folderish", "de", True],
            ["/en/a-folderish", "/es/a-folderish", "es", True],
            ["/en/a-folderish", "/es/a-folderish", "en", False],
        ],
    )
    def test_link_translations(
        self, canonical: str, translation: str, language: str, expected: bool
    ):
        func = translations_utils.link_translations
        canonical = self.all_contents[canonical]
        translation = self.all_contents[translation]
        results = func(
            canonical_obj=canonical, translation_obj=translation, language=language
        )
        assert results is expected

    def test_get_translations_without_content_translations(self):
        func = translations_utils.get_translations
        results = func()
        assert isinstance(results, list)
        # LRF
        assert len(results) == 1
        translation = results[0]
        assert "canonical" in translation
        assert "translations" in translation

    def test_get_translations_with_content_translations(
        self, translate_all_content, export_path
    ):
        # Map translations
        translate_all_content(self.content_by_language)
        func = translations_utils.get_translations
        results = func()
        assert isinstance(results, list)
        # One translation group per english content item + the language root folder
        assert len(results) == (len(self.content_by_language["en"]) + 1)
        translation = results[0]
        assert "canonical" in translation
        assert "translations" in translation

    def test_set_translations(self):
        func = translations_utils.set_translations
        data = [
            {
                "canonical": self.all_contents["/en/a-folderish"].UID(),
                "translations": {
                    "es": self.all_contents["/es/a-folderish"].UID(),
                    "de": self.all_contents["/de/a-folderish"].UID(),
                },
            }
        ]
        results = func(data)
        assert isinstance(results, list)
        tg = results[0]
        assert isinstance(tg, dict)
        assert tg["canonical"] == "/en/a-folderish"
        assert "es" in tg["translations"]
        assert "de" in tg["translations"]
