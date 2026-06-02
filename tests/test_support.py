from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re

import pytest

import nisaba_tools._far_fst as far_fst
from nisaba_tools import api_support
from nisaba_tools.far_assets import (
    DEFAULT_EN_SPELLOUT_FAR_URL,
    DEFAULT_FIXED_FAR_URL,
    DEFAULT_ISO_FAR_URL,
    DEFAULT_REVERSIBLE_ROMAN_FAR_URL,
    DEFAULT_WELLFORMED_FAR_URL,
    default_english_spellout_far_key,
    default_ipa_far_url,
    default_natural_deroman_far_url,
    default_natural_roman_far_url,
)
from nisaba_tools.fixed import _FIXED_SCHEME_TO_SCRIPT
from nisaba_tools.languages import (
    CANONICAL_RESOLVED_LANGUAGES,
    LANGUAGE_DEFINITION_BY_LANGUAGE,
    SCRIPT_BY_KEY,
)

_NATURAL_ROMAN_ASSET_RE = re.compile(
    r"^(?P<language>[a-z0-9-]+)_iso_(?P<scheme>nat|psac|psaf)\.far$"
)
_IPA_ASSET_RE = re.compile(r"^(?P<language>[a-z0-9-]+)_iso_ipa\.far$")
_DEROMAN_ASSET_RE = re.compile(r"^(?P<language>[a-z0-9-]+)_(?P<target>[a-z0-9]+)\.far$")


def _manifest_url(far_url: str) -> str:
    return f"{far_url.rsplit('/', 1)[0]}/manifest.json"


@lru_cache(maxsize=16)
def _manifest_files(manifest_url: str, cache_dir_str: str) -> tuple[dict[str, object], ...]:
    manifest_path = far_fst.download_to_cache(manifest_url, Path(cache_dir_str))
    manifest = json.loads(manifest_path.read_text())
    return tuple(manifest["files"])


@lru_cache(maxsize=16)
def _manifest_file_keys(manifest_url: str, cache_dir_str: str) -> dict[str, tuple[str, ...]]:
    return {
        file_info["url"]: tuple(file_info["keys"])
        for file_info in _manifest_files(manifest_url, cache_dir_str)
    }


def _far_keys(url: str, cache_dir: Path) -> set[str]:
    file_keys = _manifest_file_keys(_manifest_url(url), str(cache_dir))
    if url not in file_keys:
        raise AssertionError(f"{url} was not present in {_manifest_url(url)}")
    return set(file_keys[url])


def test_support_matrix_rejects_removed_check_api_aliases() -> None:
    with pytest.raises(ValueError, match="Unsupported API name"):
        api_support().languages_for_api("check_to_ipa")


def test_support_matrix_lists_expected_brahmic_script_support() -> None:
    support = api_support()

    assert "und-Deva" in support.languages_for_api("to_iso")
    assert "und-Deva" in support.languages_for_api("is_wellformed")
    assert "und-Deva" not in support.languages_for_api("to_ipa")


def test_support_matrix_lists_expected_abjad_support() -> None:
    support = api_support()

    assert "ur" in support.languages_for_api("visual_normalize")
    assert "und-Arab" not in support.languages_for_api("visual_normalize")
    assert "und-Arab" in support.languages_for_api("to_reversible_roman")


def test_support_matrix_lists_expected_language_features() -> None:
    support = api_support()

    tamil_apis = set(support.apis_for_language("ta"))
    assert {
        "visual_normalize",
        "to_iso",
        "from_iso",
        "brahmic_transliterate",
        "is_wellformed",
        "natural_romanize",
        "to_ipa",
    }.issubset(tamil_apis)
    assert "reading_normalize" not in tamil_apis

    assert support.apis_for_language("und-Deva") == (
        "visual_normalize",
        "to_iso",
        "from_iso",
        "brahmic_transliterate",
        "is_wellformed",
    )


def test_support_matrix_lists_default_fixed_support_only() -> None:
    support = api_support()

    assert support.languages_for_api("fixed_transliterate") == ("ml", "und-Mlym")
    assert support.support_for_api("fixed_transliterate").schemes == ("Mozhi",)


def test_support_matrix_rejects_unknown_api() -> None:
    with pytest.raises(ValueError, match="Unsupported API name"):
        api_support().languages_for_api("missing_api")


def test_combined_default_far_support_lists_match_far_keys() -> None:
    support = api_support()
    cache_dir = far_fst.resolve_disk_cache_dir(True)
    canonical_languages = CANONICAL_RESOLVED_LANGUAGES

    iso_keys = _far_keys(DEFAULT_ISO_FAR_URL, cache_dir)
    expected_to_iso = tuple(
        sorted(
            {
                resolved_language.language
                for resolved_language in canonical_languages
                if resolved_language.family == "brahmic"
                and f"FROM_{resolved_language.script_key}" in iso_keys
            }
        )
    )
    expected_from_iso = tuple(
        sorted(
            {
                resolved_language.language
                for resolved_language in canonical_languages
                if resolved_language.family == "brahmic"
                and f"TO_{resolved_language.script_key}" in iso_keys
            }
        )
    )
    assert support.languages_for_api("to_iso") == expected_to_iso
    assert support.languages_for_api("from_iso") == expected_from_iso

    wellformed_keys = _far_keys(DEFAULT_WELLFORMED_FAR_URL, cache_dir)
    expected_wellformed = tuple(
        sorted(
            {
                resolved_language.language
                for resolved_language in canonical_languages
                if resolved_language.family == "brahmic"
                and resolved_language.wellformed_key in wellformed_keys
            }
        )
    )
    assert support.languages_for_api("is_wellformed") == expected_wellformed

    english_spellout_keys = _far_keys(DEFAULT_EN_SPELLOUT_FAR_URL, cache_dir)
    expected_english_spellout = tuple(
        sorted(
            {
                resolved_language.language
                for resolved_language in canonical_languages
                if not resolved_language.language.startswith("und-")
                and resolved_language.family in {"abjad", "brahmic"}
                and (
                    default_english_spellout_far_key(resolved_language.language)
                    in english_spellout_keys
                    if LANGUAGE_DEFINITION_BY_LANGUAGE[
                        resolved_language.language
                    ].translit_support.english_spellout
                    else False
                )
            }
        )
    )
    assert support.languages_for_api("english_spellout") == expected_english_spellout

    fixed_keys = _far_keys(DEFAULT_FIXED_FAR_URL, cache_dir)
    expected_fixed = tuple(
        sorted(
            {
                resolved_language.language
                for resolved_language in canonical_languages
                if resolved_language.family == "brahmic"
                and resolved_language.script_key in fixed_keys
            }
        )
    )
    expected_fixed_schemes = tuple(
        sorted(
            {
                scheme
                for scheme, script_key in _FIXED_SCHEME_TO_SCRIPT.items()
                if script_key in fixed_keys
            }
        )
    )
    assert support.languages_for_api("fixed_transliterate") == expected_fixed
    assert (
        support.support_for_api("fixed_transliterate").schemes == expected_fixed_schemes
    )

    reversible_keys = _far_keys(DEFAULT_REVERSIBLE_ROMAN_FAR_URL, cache_dir)
    expected_to_reversible = tuple(
        sorted(
            {
                resolved_language.language
                for resolved_language in canonical_languages
                if resolved_language.family == "abjad"
                and "FROM_ARAB" in reversible_keys
            }
        )
    )
    expected_from_reversible = tuple(
        sorted(
            {
                resolved_language.language
                for resolved_language in canonical_languages
                if resolved_language.family == "abjad" and "TO_ARAB" in reversible_keys
            }
        )
    )
    assert support.languages_for_api("to_reversible_roman") == expected_to_reversible
    assert (
        support.languages_for_api("from_reversible_roman") == expected_from_reversible
    )


def test_language_specific_default_far_support_lists_match_far_keys() -> None:
    support = api_support()
    cache_dir = far_fst.resolve_disk_cache_dir(True)
    cache_dir_str = str(cache_dir)

    natural_schemes = {
        "nat": "ISO_TO_NAT",
        "psac": "ISO_TO_PSAC",
        "psaf": "ISO_TO_PSAF",
    }
    natural_manifest_url = _manifest_url(default_natural_roman_far_url("hi", "nat"))
    natural_languages_by_scheme = {scheme: set() for scheme in natural_schemes}
    for file_info in _manifest_files(natural_manifest_url, cache_dir_str):
        path = Path(str(file_info["path"])).name
        if path.endswith("_utf8.far"):
            continue
        match = _NATURAL_ROMAN_ASSET_RE.fullmatch(path)
        if match is None:
            continue
        scheme = match.group("scheme")
        if natural_schemes[scheme] in set(file_info["keys"]):
            natural_languages_by_scheme[scheme].add(match.group("language"))
    expected_natural_roman_languages = tuple(
        sorted(set.intersection(*(languages for languages in natural_languages_by_scheme.values())))
    )
    assert support.languages_for_api("natural_romanize") == expected_natural_roman_languages
    for language in support.languages_for_api("natural_romanize"):
        for scheme, key in natural_schemes.items():
            assert key in _far_keys(
                default_natural_roman_far_url(language, scheme), cache_dir
            )

    ipa_manifest_url = _manifest_url(default_ipa_far_url("hi"))
    expected_ipa_languages = tuple(
        sorted(
            {
                match.group("language")
                for file_info in _manifest_files(ipa_manifest_url, cache_dir_str)
                if not Path(str(file_info["path"])).name.endswith("_utf8.far")
                and (match := _IPA_ASSET_RE.fullmatch(Path(str(file_info["path"])).name))
                and "ISO_TO_IPA" in set(file_info["keys"])
            }
        )
    )
    assert support.languages_for_api("to_ipa") == expected_ipa_languages
    for language in support.languages_for_api("to_ipa"):
        assert "ISO_TO_IPA" in _far_keys(default_ipa_far_url(language), cache_dir)

    deroman_manifest_url = _manifest_url(default_natural_deroman_far_url("hi", "script"))
    deroman_iso_languages: set[str] = set()
    deroman_script_languages: set[str] = set()
    for file_info in _manifest_files(deroman_manifest_url, cache_dir_str):
        path = Path(str(file_info["path"])).name
        if path == "en_spellout.far" or path.endswith("_utf8.far"):
            continue
        match = _DEROMAN_ASSET_RE.fullmatch(path)
        if match is None:
            continue
        language = match.group("language")
        target = match.group("target")
        file_keys = set(file_info["keys"])
        if target == "iso":
            if "ISO" in file_keys:
                deroman_iso_languages.add(language)
            continue
        if not any(key != "ISO" for key in file_keys):
            continue
        deroman_script_languages.add(language)
        definition = LANGUAGE_DEFINITION_BY_LANGUAGE.get(language)
        if definition is not None:
            assert target == SCRIPT_BY_KEY[definition.script_key].script_subtag.lower()
            assert definition.script_key in file_keys
    expected_deromanization_languages = tuple(
        sorted(deroman_iso_languages & deroman_script_languages)
    )
    assert support.languages_for_api("natural_deromanize") == expected_deromanization_languages
    for language in support.languages_for_api("natural_deromanize"):
        resolved_language = next(
            resolved
            for resolved in CANONICAL_RESOLVED_LANGUAGES
            if resolved.language == language
        )
        assert resolved_language.script_key in _far_keys(
            default_natural_deroman_far_url(language, "script"),
            cache_dir,
        )
        assert "ISO" in _far_keys(
            default_natural_deroman_far_url(language, "iso"),
            cache_dir,
        )
