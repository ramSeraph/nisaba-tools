from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nisaba_tools._far_fst import (
    DiskCacheSetting,
    resolve_disk_cache_dir,
    resolve_far_transducer,
    transduce_text,
)
from nisaba_tools._natural_translit import (
    resolve_supported_english_spellout_language,
)
from nisaba_tools._result_utils import output_text_or_raise
from nisaba_tools.far_assets import (
    DEFAULT_EN_SPELLOUT_FAR_URL,
    default_english_spellout_far_key,
)


@dataclass(frozen=True)
class EnglishSpelloutResult:
    text: str
    output_text: str | None
    supported: bool
    direction: str
    resolved_language: str | None
    resolved_script: str | None
    spellout_key: str | None
    spellout_far: Path | None
    reason: str | None = None


def _unsupported_result(
    text: str,
    *,
    resolved_language: str | None = None,
    resolved_script: str | None = None,
    spellout_far: Path | None = None,
    reason: str,
) -> EnglishSpelloutResult:
    return EnglishSpelloutResult(
        text=text,
        output_text=None,
        supported=False,
        direction="english_spellout",
        resolved_language=resolved_language,
        resolved_script=resolved_script,
        spellout_key=None,
        spellout_far=spellout_far,
        reason=reason,
    )


class EnglishSpelloutTransliterator:
    def __init__(
        self,
        spellout_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_spellout_far = spellout_far

    def transliterate(
        self,
        text: str,
        language: str,
        spellout_far: str | Path | None = None,
    ) -> EnglishSpelloutResult:
        resolved_language, reason = resolve_supported_english_spellout_language(
            language,
            purpose="English spellout",
            feature_name="English spellout",
        )
        if reason is not None:
            return _unsupported_result(
                text,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                reason=reason,
            )

        resolved_far, spellout_key, spellout_fst = resolve_far_transducer(
            spellout_far or self._default_spellout_far,
            default_url=DEFAULT_EN_SPELLOUT_FAR_URL,
            cache_dir=self._cache_dir,
            key_candidates=[
                default_english_spellout_far_key(resolved_language.language)
            ],
        )
        try:
            output_text = transduce_text(text, spellout_fst)
        except ValueError:
            return _unsupported_result(
                text,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                spellout_far=resolved_far,
                reason=(
                    "Input is not valid Latin text for the selected English "
                    "spellout grammar."
                ),
            )

        return EnglishSpelloutResult(
            text=text,
            output_text=output_text,
            supported=True,
            direction="english_spellout",
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            spellout_key=spellout_key,
            spellout_far=resolved_far,
        )

    def english_spellout(
        self,
        text: str,
        language: str,
        spellout_far: str | Path | None = None,
    ) -> str:
        return output_text_or_raise(
            self.transliterate(
                text,
                language=language,
                spellout_far=spellout_far,
            ),
            "Could not spell out the English text with the selected grammar.",
        )


def english_spellout(
    text: str,
    language: str,
    spellout_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return EnglishSpelloutTransliterator(
        disk_cache=disk_cache,
    ).english_spellout(
        text,
        language=language,
        spellout_far=spellout_far,
    )


__all__ = [
    "english_spellout",
    "EnglishSpelloutResult",
    "EnglishSpelloutTransliterator",
]
