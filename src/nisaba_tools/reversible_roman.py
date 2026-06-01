from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import unicodedata

from nisaba_tools._far_fst import (
    DiskCacheSetting,
    resolve_disk_cache_dir,
    resolve_far_transducer,
    transduce_text,
)
from nisaba_tools._result_utils import output_text_or_raise
from nisaba_tools.far_assets import DEFAULT_REVERSIBLE_ROMAN_FAR_URL
from nisaba_tools.languages import resolve_explicit_language, resolve_language


@dataclass(frozen=True)
class ReversibleRomanizationResult:
    text: str
    output_text: str | None
    supported: bool
    guessed: bool
    direction: str
    resolved_language: str | None
    resolved_script: str | None
    roman_key: str | None
    roman_far: Path | None
    reason: str | None = None


def _is_arabic_script_content(character: str) -> bool:
    category = unicodedata.category(character)
    return unicodedata.name(character, "").startswith("ARABIC") and category[
        :1
    ] not in {"N", "P", "S", "Z"}


def _is_roman_passthrough(character: str) -> bool:
    category = unicodedata.category(character)
    return category[:1] in {"N", "P", "S", "Z"}


def _segment_text(
    text: str, *, should_transduce: Callable[[str], bool]
) -> list[tuple[bool, str]]:
    if not text:
        return []

    segments: list[tuple[bool, str]] = []
    segment_start = 0
    current_mode = should_transduce(text[0])
    for index, character in enumerate(text[1:], start=1):
        next_mode = should_transduce(character)
        if next_mode == current_mode:
            continue
        segments.append((current_mode, text[segment_start:index]))
        segment_start = index
        current_mode = next_mode
    segments.append((current_mode, text[segment_start:]))
    return segments


def _segmented_transduction(
    text: str,
    transducer,
    *,
    should_transduce: Callable[[str], bool],
    normalize_input: bool = False,
) -> str:
    output_parts: list[str] = []
    for transduce_segment, segment in _segment_text(
        text, should_transduce=should_transduce
    ):
        if not transduce_segment:
            output_parts.append(segment)
            continue
        normalized_segment = (
            unicodedata.normalize("NFC", segment) if normalize_input else segment
        )
        output_parts.append(transduce_text(normalized_segment, transducer))
    return "".join(output_parts)


def _unsupported_result(
    text: str,
    *,
    direction: str,
    guessed: bool = False,
    resolved_language: str | None = None,
    resolved_script: str | None = None,
    reason: str,
    roman_far: Path | None = None,
) -> ReversibleRomanizationResult:
    return ReversibleRomanizationResult(
        text=text,
        output_text=None,
        supported=False,
        guessed=guessed,
        direction=direction,
        resolved_language=resolved_language,
        resolved_script=resolved_script,
        roman_key=None,
        roman_far=roman_far,
        reason=reason,
    )


class ReversibleRomanTransliterator:
    def __init__(
        self,
        roman_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_roman_far = roman_far

    def transliterate_to_roman(
        self,
        text: str,
        language: str | None = None,
        roman_far: str | Path | None = None,
    ) -> ReversibleRomanizationResult:
        resolved_language = resolve_language(language, text)
        if resolved_language is None:
            return _unsupported_result(
                text,
                direction="to_reversible_roman",
                reason="Could not infer a supported abjad/alphabet script from the text.",
            )
        if resolved_language.family != "abjad":
            return _unsupported_result(
                text,
                direction="to_reversible_roman",
                guessed=resolved_language.guessed,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                reason=(
                    "Reversible romanization is only supported for abjad/alphabet scripts."
                ),
            )

        resolved_far, roman_key, roman_fst = resolve_far_transducer(
            roman_far or self._default_roman_far,
            default_url=DEFAULT_REVERSIBLE_ROMAN_FAR_URL,
            cache_dir=self._cache_dir,
            key_candidates=["FROM_ARAB"],
        )
        try:
            output_text = _segmented_transduction(
                text,
                roman_fst,
                should_transduce=_is_arabic_script_content,
                normalize_input=True,
            )
        except ValueError:
            return _unsupported_result(
                text,
                direction="to_reversible_roman",
                guessed=resolved_language.guessed,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                roman_far=resolved_far,
                reason="Input contains abjad/alphabet segments that the reversible romanizer could not analyze.",
            )

        return ReversibleRomanizationResult(
            text=text,
            output_text=output_text,
            supported=True,
            guessed=resolved_language.guessed,
            direction="to_reversible_roman",
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            roman_key=roman_key,
            roman_far=resolved_far,
        )

    def transliterate_from_roman(
        self,
        text: str,
        language: str | None = None,
        roman_far: str | Path | None = None,
    ) -> ReversibleRomanizationResult:
        if language is None:
            resolved_language_value = "und-Arab"
            resolved_script = "ARAB"
            guessed = False
        else:
            resolved_language = resolve_explicit_language(
                language,
                purpose="Reversible deromanization",
            )
            if resolved_language.family != "abjad":
                return _unsupported_result(
                    text,
                    direction="from_reversible_roman",
                    resolved_language=resolved_language.language,
                    resolved_script=resolved_language.script_key,
                    reason=(
                        "Reversible romanization is only supported for abjad/alphabet scripts."
                    ),
                )
            resolved_language_value = resolved_language.language
            resolved_script = resolved_language.script_key
            guessed = False

        resolved_far, roman_key, roman_fst = resolve_far_transducer(
            roman_far or self._default_roman_far,
            default_url=DEFAULT_REVERSIBLE_ROMAN_FAR_URL,
            cache_dir=self._cache_dir,
            key_candidates=["TO_ARAB"],
        )
        try:
            output_text = _segmented_transduction(
                text,
                roman_fst,
                should_transduce=lambda character: not _is_roman_passthrough(character),
            )
        except ValueError:
            return _unsupported_result(
                text,
                direction="from_reversible_roman",
                guessed=guessed,
                resolved_language=resolved_language_value,
                resolved_script=resolved_script,
                roman_far=resolved_far,
                reason=(
                    "Input is not valid reversible romanization for the abjad/alphabet TO_ARAB grammar."
                ),
            )

        return ReversibleRomanizationResult(
            text=text,
            output_text=output_text,
            supported=True,
            guessed=guessed,
            direction="from_reversible_roman",
            resolved_language=resolved_language_value,
            resolved_script=resolved_script,
            roman_key=roman_key,
            roman_far=resolved_far,
        )

    def to_reversible_roman(
        self,
        text: str,
        language: str | None = None,
        roman_far: str | Path | None = None,
    ) -> str:
        return output_text_or_raise(
            self.transliterate_to_roman(
                text,
                language=language,
                roman_far=roman_far,
            ),
            "Could not transliterate the text to reversible romanization.",
        )

    def from_reversible_roman(
        self,
        text: str,
        language: str | None = None,
        roman_far: str | Path | None = None,
    ) -> str:
        return output_text_or_raise(
            self.transliterate_from_roman(
                text,
                language=language,
                roman_far=roman_far,
            ),
            "Could not transliterate the reversible romanization to Arabic script.",
        )


def to_reversible_roman(
    text: str,
    language: str | None = None,
    roman_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return ReversibleRomanTransliterator(
        disk_cache=disk_cache,
    ).to_reversible_roman(
        text,
        language=language,
        roman_far=roman_far,
    )


def from_reversible_roman(
    text: str,
    language: str | None = None,
    roman_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return ReversibleRomanTransliterator(
        disk_cache=disk_cache,
    ).from_reversible_roman(
        text,
        language=language,
        roman_far=roman_far,
    )


__all__ = [
    "from_reversible_roman",
    "to_reversible_roman",
    "ReversibleRomanizationResult",
    "ReversibleRomanTransliterator",
]
