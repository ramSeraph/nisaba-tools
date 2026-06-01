from __future__ import annotations

from nisaba_tools.languages import (
    ResolvedLanguage,
    SUPPORTED_DEROMANIZATION_LANGUAGES,
    SUPPORTED_ENGLISH_SPELLOUT_LANGUAGES,
    SUPPORTED_IPA_LANGUAGES,
    SUPPORTED_NATURAL_ROMAN_LANGUAGES,
    resolve_explicit_language,
)


def _supported_language_examples(supported_languages: frozenset[str]) -> str:
    examples = sorted(supported_languages)
    if len(examples) == 1:
        return f"'{examples[0]}'"
    if len(examples) == 2:
        return f"'{examples[0]}' or '{examples[1]}'"

    sample_indexes = (0, len(examples) // 2, len(examples) - 1)
    sampled_examples = list(dict.fromkeys(examples[index] for index in sample_indexes))
    return (
        ", ".join(f"'{language}'" for language in sampled_examples[:-1])
        + f", or '{sampled_examples[-1]}'"
    )


def _resolve_supported_release_language(
    language: str,
    *,
    purpose: str,
    feature_name: str,
    supported_languages: frozenset[str],
    brahmic_only: bool,
) -> tuple[ResolvedLanguage, str | None]:
    resolved_language = resolve_explicit_language(language, purpose=purpose)
    if brahmic_only and resolved_language.family != "brahmic":
        return resolved_language, (
            f"{feature_name} is only supported for Brahmic scripts."
        )
    if resolved_language.language.startswith("und-"):
        return resolved_language, (
            f"{feature_name} requires an explicit language code such as "
            f"{_supported_language_examples(supported_languages)} because the "
            "release assets are "
            "language-specific."
        )
    if resolved_language.language not in supported_languages:
        return resolved_language, (
            f"{feature_name} is not currently available for language "
            f"{resolved_language.language} in the published release assets."
        )
    return resolved_language, None


def resolve_supported_natural_roman_language(
    language: str,
    *,
    purpose: str,
    feature_name: str,
) -> tuple[ResolvedLanguage, str | None]:
    return _resolve_supported_release_language(
        language,
        purpose=purpose,
        feature_name=feature_name,
        supported_languages=SUPPORTED_NATURAL_ROMAN_LANGUAGES,
        brahmic_only=True,
    )


def resolve_supported_ipa_language(
    language: str,
    *,
    purpose: str,
    feature_name: str,
) -> tuple[ResolvedLanguage, str | None]:
    return _resolve_supported_release_language(
        language,
        purpose=purpose,
        feature_name=feature_name,
        supported_languages=SUPPORTED_IPA_LANGUAGES,
        brahmic_only=True,
    )


def resolve_supported_deromanization_language(
    language: str,
    *,
    purpose: str,
    feature_name: str,
) -> tuple[ResolvedLanguage, str | None]:
    return _resolve_supported_release_language(
        language,
        purpose=purpose,
        feature_name=feature_name,
        supported_languages=SUPPORTED_DEROMANIZATION_LANGUAGES,
        brahmic_only=True,
    )


def resolve_supported_english_spellout_language(
    language: str,
    *,
    purpose: str,
    feature_name: str,
) -> tuple[ResolvedLanguage, str | None]:
    return _resolve_supported_release_language(
        language,
        purpose=purpose,
        feature_name=feature_name,
        supported_languages=SUPPORTED_ENGLISH_SPELLOUT_LANGUAGES,
        brahmic_only=False,
    )
