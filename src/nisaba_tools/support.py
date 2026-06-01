from __future__ import annotations

from dataclasses import dataclass

from nisaba_tools.far_assets import (
    default_reading_norm_far_url,
    default_visual_norm_far_url,
)
from nisaba_tools.fixed import _DEFAULT_FIXED_SCHEME_BY_SCRIPT
from nisaba_tools.languages import (
    CANONICAL_RESOLVED_LANGUAGES,
    SUPPORTED_DEROMANIZATION_LANGUAGES,
    SUPPORTED_ENGLISH_SPELLOUT_LANGUAGES,
    SUPPORTED_IPA_LANGUAGES,
    SUPPORTED_NATURAL_ROMAN_LANGUAGES,
    normalized_alias,
    resolve_explicit_language,
)
from nisaba_tools.reading_norm import _default_reading_norm_key


@dataclass(frozen=True)
class ApiSupport:
    api: str
    languages: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    schemes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApiSupportMatrix:
    apis: tuple[ApiSupport, ...]

    def support_for_api(self, api: str) -> ApiSupport:
        alias = normalized_alias(api)
        for support in self.apis:
            if alias == normalized_alias(support.api) or alias in {
                normalized_alias(candidate) for candidate in support.aliases
            }:
                return support
        raise ValueError(f"Unsupported API name: {api}")

    def languages_for_api(self, api: str) -> tuple[str, ...]:
        return self.support_for_api(api).languages

    def apis_for_language(self, language: str) -> tuple[str, ...]:
        resolved_language = resolve_explicit_language(
            language,
            purpose="API support queries",
        )
        return tuple(
            support.api
            for support in self.apis
            if resolved_language.language in support.languages
        )


def _supports_default_visual_norm(key: str) -> bool:
    try:
        default_visual_norm_far_url(key)
    except ValueError:
        return False
    return True


def _supports_default_reading_norm(key: str) -> bool:
    try:
        default_reading_norm_far_url(key)
    except ValueError:
        return False
    return True


def _sorted_languages(values: set[str]) -> tuple[str, ...]:
    return tuple(sorted(values))


_CANONICAL_LANGUAGES = CANONICAL_RESOLVED_LANGUAGES
_BRAHMIC_LANGUAGES = {
    resolved_language.language
    for resolved_language in _CANONICAL_LANGUAGES
    if resolved_language.family == "brahmic"
}
_ABJAD_LANGUAGES = {
    resolved_language.language
    for resolved_language in _CANONICAL_LANGUAGES
    if resolved_language.family == "abjad"
}
_EXPLICIT_ABJAD_LANGUAGES = {
    language for language in _ABJAD_LANGUAGES if not language.startswith("und-")
}
_VISUAL_NORM_LANGUAGES = _sorted_languages(
    {
        resolved_language.language
        for resolved_language in _CANONICAL_LANGUAGES
        if _supports_default_visual_norm(resolved_language.visual_norm_key)
        and (
            resolved_language.family == "brahmic"
            or not resolved_language.language.startswith("und-")
        )
    }
)
_READING_NORM_LANGUAGES = _sorted_languages(
    {
        resolved_language.language
        for resolved_language in _CANONICAL_LANGUAGES
        if (
            resolved_language.family == "brahmic"
            and _default_reading_norm_key(
                resolved_language.language,
                resolved_language.script_key,
            )
            is not None
        )
        or (
            resolved_language.family == "abjad"
            and not resolved_language.language.startswith("und-")
            and _supports_default_reading_norm(resolved_language.visual_norm_key)
        )
    }
)
_FIXED_LANGUAGES = _sorted_languages(
    {
        resolved_language.language
        for resolved_language in _CANONICAL_LANGUAGES
        if resolved_language.family == "brahmic"
        and resolved_language.script_key in _DEFAULT_FIXED_SCHEME_BY_SCRIPT
    }
)

_API_SUPPORT = ApiSupportMatrix(
    apis=(
        ApiSupport(
            api="visual_normalize",
            languages=_VISUAL_NORM_LANGUAGES,
        ),
        ApiSupport(
            api="reading_normalize",
            languages=_READING_NORM_LANGUAGES,
        ),
        ApiSupport(
            api="to_iso",
            languages=_sorted_languages(set(_BRAHMIC_LANGUAGES)),
        ),
        ApiSupport(
            api="from_iso",
            languages=_sorted_languages(set(_BRAHMIC_LANGUAGES)),
        ),
        ApiSupport(
            api="brahmic_transliterate",
            languages=_sorted_languages(set(_BRAHMIC_LANGUAGES)),
        ),
        ApiSupport(
            api="is_wellformed",
            languages=_sorted_languages(
                {
                    resolved_language.language
                    for resolved_language in _CANONICAL_LANGUAGES
                    if resolved_language.family == "brahmic"
                    and _supports_default_visual_norm(resolved_language.visual_norm_key)
                }
            ),
        ),
        ApiSupport(
            api="fixed_transliterate",
            languages=_FIXED_LANGUAGES,
            schemes=("Mozhi",),
        ),
        ApiSupport(
            api="to_reversible_roman",
            languages=_sorted_languages(set(_ABJAD_LANGUAGES)),
        ),
        ApiSupport(
            api="from_reversible_roman",
            languages=_sorted_languages(set(_ABJAD_LANGUAGES)),
        ),
        ApiSupport(
            api="natural_romanize",
            languages=tuple(sorted(SUPPORTED_NATURAL_ROMAN_LANGUAGES)),
            schemes=("nat", "psac", "psaf"),
        ),
        ApiSupport(
            api="natural_romanize_from_iso",
            languages=tuple(sorted(SUPPORTED_NATURAL_ROMAN_LANGUAGES)),
            schemes=("nat", "psac", "psaf"),
        ),
        ApiSupport(
            api="to_ipa",
            languages=tuple(sorted(SUPPORTED_IPA_LANGUAGES)),
        ),
        ApiSupport(
            api="to_ipa_from_iso",
            languages=tuple(sorted(SUPPORTED_IPA_LANGUAGES)),
        ),
        ApiSupport(
            api="natural_deromanize",
            languages=tuple(sorted(SUPPORTED_DEROMANIZATION_LANGUAGES)),
        ),
        ApiSupport(
            api="natural_deromanize_to_iso",
            languages=tuple(sorted(SUPPORTED_DEROMANIZATION_LANGUAGES)),
        ),
        ApiSupport(
            api="english_spellout",
            languages=tuple(sorted(SUPPORTED_ENGLISH_SPELLOUT_LANGUAGES)),
        ),
    )
)


def api_support() -> ApiSupportMatrix:
    return _API_SUPPORT


__all__ = ["api_support", "ApiSupport", "ApiSupportMatrix"]
