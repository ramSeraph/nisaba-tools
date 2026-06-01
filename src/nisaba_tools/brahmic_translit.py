from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nisaba_tools._far_fst import DiskCacheSetting
from nisaba_tools._result_utils import output_text_or_raise
from nisaba_tools.iso import IsoTransliterator
from nisaba_tools.languages import resolve_explicit_language, resolve_language
from nisaba_tools.reading_norm import ReadingNormalizer


@dataclass(frozen=True)
class BrahmicTransliterationResult:
    text: str
    output_text: str | None
    supported: bool
    source_guessed: bool
    source_language: str | None
    source_script: str | None
    target_language: str | None
    target_script: str | None
    iso_text: str | None
    iso_key: str | None
    iso_far: Path | None
    reading_norm_applied: bool
    reading_norm_key: str | None
    reading_norm_far: Path | None
    visual_norm_applied: bool
    visual_norm_key: str | None
    visual_norm_far: Path | None
    reason: str | None = None


def _unsupported_result(
    text: str,
    *,
    source_guessed: bool = False,
    source_language: str | None = None,
    source_script: str | None = None,
    target_language: str | None = None,
    target_script: str | None = None,
    iso_text: str | None = None,
    iso_key: str | None = None,
    iso_far: Path | None = None,
    reading_norm_applied: bool = False,
    reading_norm_key: str | None = None,
    reading_norm_far: Path | None = None,
    visual_norm_applied: bool = False,
    visual_norm_key: str | None = None,
    visual_norm_far: Path | None = None,
    reason: str,
) -> BrahmicTransliterationResult:
    return BrahmicTransliterationResult(
        text=text,
        output_text=None,
        supported=False,
        source_guessed=source_guessed,
        source_language=source_language,
        source_script=source_script,
        target_language=target_language,
        target_script=target_script,
        iso_text=iso_text,
        iso_key=iso_key,
        iso_far=iso_far,
        reading_norm_applied=reading_norm_applied,
        reading_norm_key=reading_norm_key,
        reading_norm_far=reading_norm_far,
        visual_norm_applied=visual_norm_applied,
        visual_norm_key=visual_norm_key,
        visual_norm_far=visual_norm_far,
        reason=reason,
    )


class BrahmicTransliterator:
    def __init__(
        self,
        iso_far: str | Path | None = None,
        reading_norm_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._iso = IsoTransliterator(
            iso_far=iso_far,
            visual_norm_far=visual_norm_far,
            disk_cache=disk_cache,
        )
        self._reading = ReadingNormalizer(
            reading_norm_far=reading_norm_far,
            visual_norm_far=visual_norm_far,
            disk_cache=disk_cache,
        )

    def transliterate(
        self,
        text: str,
        source_language: str | None = None,
        target_language: str | None = None,
        iso_far: str | Path | None = None,
        reading_norm_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
        apply_reading_norm: bool = False,
    ) -> BrahmicTransliterationResult:
        resolved_source = resolve_language(source_language, text)
        if resolved_source is None:
            return _unsupported_result(
                text,
                reason="Could not infer a supported Brahmic script from the text.",
            )
        resolved_target = resolve_explicit_language(
            target_language,
            purpose="Brahmic transliteration",
        )
        if resolved_source.family != "brahmic" or resolved_target.family != "brahmic":
            return _unsupported_result(
                text,
                source_guessed=resolved_source.guessed,
                source_language=resolved_source.language,
                source_script=resolved_source.script_key,
                target_language=resolved_target.language,
                target_script=resolved_target.script_key,
                reason="Brahmic transliteration is only supported for Brahmic scripts.",
            )

        reading_result = None
        if apply_reading_norm:
            reading_result = self._reading.normalize(
                text,
                language=resolved_source.language,
                reading_norm_far=reading_norm_far,
                visual_norm_far=visual_norm_far,
                apply_visual_norm=apply_visual_norm,
            )
            if not reading_result.supported or reading_result.normalized_text is None:
                return _unsupported_result(
                    text,
                    source_guessed=resolved_source.guessed,
                    source_language=resolved_source.language,
                    source_script=resolved_source.script_key,
                    target_language=resolved_target.language,
                    target_script=resolved_target.script_key,
                    reading_norm_applied=True,
                    reason=reading_result.reason
                    or "Could not normalize the text for reading.",
                )
            iso_result = self._iso.transliterate_to_iso(
                reading_result.normalized_text,
                language=resolved_source.language,
                iso_far=iso_far,
                apply_visual_norm=False,
            )
        else:
            iso_result = self._iso.transliterate_to_iso(
                text,
                language=resolved_source.language,
                iso_far=iso_far,
                visual_norm_far=visual_norm_far,
                apply_visual_norm=apply_visual_norm,
            )

        if not iso_result.supported or iso_result.output_text is None:
            return _unsupported_result(
                text,
                source_guessed=resolved_source.guessed,
                source_language=resolved_source.language,
                source_script=resolved_source.script_key,
                target_language=resolved_target.language,
                target_script=resolved_target.script_key,
                reading_norm_applied=reading_result is not None,
                reading_norm_key=(
                    reading_result.reading_norm_key
                    if reading_result is not None
                    else None
                ),
                reading_norm_far=(
                    reading_result.reading_norm_far
                    if reading_result is not None
                    else None
                ),
                visual_norm_applied=(
                    reading_result.visual_norm_applied
                    if reading_result is not None
                    else iso_result.visual_norm_applied
                ),
                visual_norm_key=(
                    reading_result.visual_norm_key
                    if reading_result is not None
                    else iso_result.visual_norm_key
                ),
                visual_norm_far=(
                    reading_result.visual_norm_far
                    if reading_result is not None
                    else iso_result.visual_norm_far
                ),
                reason=iso_result.reason or "Could not transliterate the text to ISO.",
            )

        target_result = self._iso.transliterate_from_iso(
            iso_result.output_text,
            language=resolved_target.language,
            iso_far=iso_far,
        )
        if not target_result.supported or target_result.output_text is None:
            return _unsupported_result(
                text,
                source_guessed=resolved_source.guessed,
                source_language=resolved_source.language,
                source_script=resolved_source.script_key,
                target_language=resolved_target.language,
                target_script=resolved_target.script_key,
                iso_text=iso_result.output_text,
                iso_key=iso_result.iso_key,
                iso_far=iso_result.iso_far,
                reading_norm_applied=reading_result is not None,
                reading_norm_key=(
                    reading_result.reading_norm_key
                    if reading_result is not None
                    else None
                ),
                reading_norm_far=(
                    reading_result.reading_norm_far
                    if reading_result is not None
                    else None
                ),
                visual_norm_applied=(
                    reading_result.visual_norm_applied
                    if reading_result is not None
                    else iso_result.visual_norm_applied
                ),
                visual_norm_key=(
                    reading_result.visual_norm_key
                    if reading_result is not None
                    else iso_result.visual_norm_key
                ),
                visual_norm_far=(
                    reading_result.visual_norm_far
                    if reading_result is not None
                    else iso_result.visual_norm_far
                ),
                reason=target_result.reason
                or "Could not transliterate the ISO text to the target script.",
            )

        return BrahmicTransliterationResult(
            text=text,
            output_text=target_result.output_text,
            supported=True,
            source_guessed=resolved_source.guessed,
            source_language=resolved_source.language,
            source_script=resolved_source.script_key,
            target_language=resolved_target.language,
            target_script=resolved_target.script_key,
            iso_text=iso_result.output_text,
            iso_key=iso_result.iso_key,
            iso_far=iso_result.iso_far,
            reading_norm_applied=reading_result is not None,
            reading_norm_key=(
                reading_result.reading_norm_key if reading_result is not None else None
            ),
            reading_norm_far=(
                reading_result.reading_norm_far if reading_result is not None else None
            ),
            visual_norm_applied=(
                reading_result.visual_norm_applied
                if reading_result is not None
                else iso_result.visual_norm_applied
            ),
            visual_norm_key=(
                reading_result.visual_norm_key
                if reading_result is not None
                else iso_result.visual_norm_key
            ),
            visual_norm_far=(
                reading_result.visual_norm_far
                if reading_result is not None
                else iso_result.visual_norm_far
            ),
        )

    def brahmic_transliterate(
        self,
        text: str,
        source_language: str | None = None,
        target_language: str | None = None,
        iso_far: str | Path | None = None,
        reading_norm_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
        apply_reading_norm: bool = False,
    ) -> str:
        return output_text_or_raise(
            self.transliterate(
                text,
                source_language=source_language,
                target_language=target_language,
                iso_far=iso_far,
                reading_norm_far=reading_norm_far,
                visual_norm_far=visual_norm_far,
                apply_visual_norm=apply_visual_norm,
                apply_reading_norm=apply_reading_norm,
            ),
            "Could not transliterate the text between Brahmic scripts.",
        )


def brahmic_transliterate(
    text: str,
    source_language: str | None = None,
    target_language: str | None = None,
    iso_far: str | Path | None = None,
    reading_norm_far: str | Path | None = None,
    visual_norm_far: str | Path | None = None,
    apply_visual_norm: bool = True,
    apply_reading_norm: bool = False,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return BrahmicTransliterator(disk_cache=disk_cache).brahmic_transliterate(
        text,
        source_language=source_language,
        target_language=target_language,
        iso_far=iso_far,
        reading_norm_far=reading_norm_far,
        visual_norm_far=visual_norm_far,
        apply_visual_norm=apply_visual_norm,
        apply_reading_norm=apply_reading_norm,
    )


__all__ = [
    "brahmic_transliterate",
    "BrahmicTransliterationResult",
    "BrahmicTransliterator",
]
