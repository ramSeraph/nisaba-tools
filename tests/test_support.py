from __future__ import annotations

from pathlib import Path

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
    SUPPORTED_DEROMANIZATION_LANGUAGES,
    SUPPORTED_ENGLISH_SPELLOUT_LANGUAGES,
    SUPPORTED_IPA_LANGUAGES,
    SUPPORTED_NATURAL_ROMAN_LANGUAGES,
)


def _far_keys(url: str, cache_dir: Path) -> set[str]:
    path = far_fst.resolve_far_path(None, url, cache_dir)
    return set(far_fst.far_index(str(path)))


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
                    if resolved_language.language
                    in SUPPORTED_ENGLISH_SPELLOUT_LANGUAGES
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

    natural_schemes = {
        "nat": "ISO_TO_NAT",
        "psac": "ISO_TO_PSAC",
        "psaf": "ISO_TO_PSAF",
    }
    assert support.languages_for_api("natural_romanize") == tuple(
        sorted(SUPPORTED_NATURAL_ROMAN_LANGUAGES)
    )
    assert support.languages_for_api("to_ipa") == tuple(sorted(SUPPORTED_IPA_LANGUAGES))
    for language in support.languages_for_api("natural_romanize"):
        for scheme, key in natural_schemes.items():
            assert key in _far_keys(
                default_natural_roman_far_url(language, scheme), cache_dir
            )

    for language in support.languages_for_api("to_ipa"):
        assert "ISO_TO_IPA" in _far_keys(default_ipa_far_url(language), cache_dir)

    assert support.languages_for_api("natural_deromanize") == tuple(
        sorted(SUPPORTED_DEROMANIZATION_LANGUAGES)
    )
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
