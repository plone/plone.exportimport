from .content.core import get_obj_path
from .content.core import get_portal_languages
from plone import api
from plone.dexterity.content import DexterityContent
from plone.exportimport import logger
from Products.CMFPlone.CatalogTool import CatalogTool
from typing import List
from typing import Tuple

try:
    from plone.app.multilingual.interfaces import ITranslationManager
except ImportError:
    HAS_MULTILINGUAL = False
else: HAS_MULTILINGUAL = True

TRANSLATION_INDEX = "TranslationGroup"


def has_translation_support(portal_catalog: CatalogTool) -> bool:
    """Check if this site has translation support."""
    has_translation_support = TRANSLATION_INDEX in portal_catalog.indexes()
    if not has_translation_support:
        logger.debug(
            "- Translation: No index TranslationGroup (p.a.multilingual not installed)"
        )
    return has_translation_support


def _get_all_translation_groups(portal_catalog: CatalogTool) -> Tuple[str]:
    """Return a list of all translation groups uid in the catalog."""
    if not has_translation_support(portal_catalog):
        return ()
    portal_catalog = api.portal.get_tool("portal_catalog")
    return portal_catalog.uniqueValuesFor("TranslationGroup")


def _prepare_translation_group(default_language: str, translations: dict) -> dict:
    canonical = translations.pop(default_language)
    if not canonical:
        first_key = [key for key in translations][0]
        canonical = translations.pop(first_key)
    return {"canonical": canonical, "translations": translations}


def get_translations(paths_to_drop: List[str] = None) -> List[dict]:
    """Get all translations."""
    paths_to_drop = paths_to_drop if paths_to_drop else []
    results = []
    portal_catalog: CatalogTool = api.portal.get_tool("portal_catalog")
    languages = get_portal_languages()
    default_language = languages.default
    for uid in _get_all_translation_groups(portal_catalog):
        query = {"TranslationGroup": uid}
        brains = portal_catalog.unrestrictedSearchResults(query)
        total_translations = len(brains)
        if total_translations < 2:
            logger.debug(
                f"- Translation: Skipping group with {uid} because it has {total_translations} content"
            )
            continue
        skip = False
        translations = {}
        for brain in brains:
            brain_path = brain.getPath()
            brain_uid = brain.UID
            language = brain.Language
            skip = bool([p for p in paths_to_drop if p in brain_path])
            if not skip and language in translations:
                duplicate = translations[language]
                logger.warning(
                    f"- Translation: Translation group {uid}, duplication for language {language}"
                    f"({duplicate}, {brain_uid}), will use {brain_uid}"
                )
            translations[language] = brain_uid

        if len(translations) > 1:
            results.append(_prepare_translation_group(default_language, translations))
    return results


def _parse_translation_group(translation_group: dict) -> dict:
    """Parse a translation group information."""
    canonical = api.content.get(UID=translation_group["canonical"])
    translations = {}
    for lang, uid in translation_group["translations"].items():
        obj = api.content.get(UID=uid)
        translations[lang] = obj
    return {"canonical": canonical, "translations": translations}


def link_translations(
    canonical_obj: DexterityContent, translation_obj: DexterityContent, language: str
) -> bool:
    """Link src_obj and dst_obj as translations for the given language."""
    if canonical_obj is translation_obj or canonical_obj.language == language:
        logger.info(
            f"- Translation: Not linking {get_obj_path(canonical_obj)} to {get_obj_path(translation_obj)} "
            f"(using language {language})"
        )
        return False
    try:
        ITranslationManager(canonical_obj).register_translation(
            language, translation_obj
        )
    except TypeError as exc:
        logger.warning(
            f"- Translation: Item is not translatable: {get_obj_path(canonical_obj)}",
            exc_info=exc,
        )
        return False
    return True


def set_translations(data: List[dict]) -> List[dict]:
    """Process a list of translations and add them to the Plone site."""
    if not HAS_MULTILINGUAL:
        logger.warning("- Translation: Skipping (plone.app.multilingual not installed)")
        return
    results = []
    for item in data:
        translation_group = _parse_translation_group(item)
        canonical = translation_group["canonical"]
        translations = translation_group["translations"]
        if not canonical:
            logger.warning(
                f"- Translation: Ignoring translation group as it has no valid canonical object {item}"
            )
            continue
        elif len(translations) == 0:
            logger.warning(
                f"- Translation: Ignoring translation group as it has no valid translations {item}"
            )
            continue
        linked = {}
        for language, dst_obj in translations.items():
            if link_translations(canonical, dst_obj, language):
                linked[language] = get_obj_path(dst_obj, True)
        results.append(
            {"canonical": get_obj_path(canonical, True), "translations": linked}
        )
    return results
