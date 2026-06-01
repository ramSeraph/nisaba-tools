from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from nisaba_tools._far_fst import (
    DiskCacheSetting,
    resolve_disk_cache_dir,
    resolve_far_transducer,
    transduce_text,
)
from nisaba_tools._natural_translit import resolve_supported_ipa_language
from nisaba_tools._result_utils import output_text_or_raise
from nisaba_tools.far_assets import default_ipa_far_url
from nisaba_tools.iso import IsoTransliterator


@dataclass(frozen=True)
class IpaTranscriptionResult:
    text: str
    output_text: str | None
    supported: bool
    direction: str
    resolved_language: str | None
    resolved_script: str | None
    ipa_key: str | None
    ipa_far: Path | None
    input_was_iso: bool
    iso_text: str | None
    iso_far: Path | None
    visual_norm_applied: bool
    visual_norm_key: str | None
    visual_norm_far: Path | None
    reason: str | None = None


def _unsupported_result(
    text: str,
    *,
    direction: str,
    input_was_iso: bool,
    resolved_language: str | None = None,
    resolved_script: str | None = None,
    ipa_far: Path | None = None,
    iso_text: str | None = None,
    iso_far: Path | None = None,
    visual_norm_applied: bool = False,
    visual_norm_key: str | None = None,
    visual_norm_far: Path | None = None,
    reason: str,
) -> IpaTranscriptionResult:
    return IpaTranscriptionResult(
        text=text,
        output_text=None,
        supported=False,
        direction=direction,
        resolved_language=resolved_language,
        resolved_script=resolved_script,
        ipa_key=None,
        ipa_far=ipa_far,
        input_was_iso=input_was_iso,
        iso_text=iso_text,
        iso_far=iso_far,
        visual_norm_applied=visual_norm_applied,
        visual_norm_key=visual_norm_key,
        visual_norm_far=visual_norm_far,
        reason=reason,
    )


class IpaTranscriber:
    def __init__(
        self,
        ipa_far: str | Path | None = None,
        iso_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_ipa_far = ipa_far
        self._iso = IsoTransliterator(
            iso_far=iso_far,
            visual_norm_far=visual_norm_far,
            disk_cache=self._cache_dir,
        )

    def transcribe_iso(
        self,
        text: str,
        language: str,
        ipa_far: str | Path | None = None,
    ) -> IpaTranscriptionResult:
        resolved_language, reason = resolve_supported_ipa_language(
            language,
            purpose="IPA transcription from ISO",
            feature_name="IPA transcription",
        )
        if reason is not None:
            return _unsupported_result(
                text,
                direction="to_ipa_from_iso",
                input_was_iso=True,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                reason=reason,
            )

        resolved_far, ipa_key, ipa_fst = resolve_far_transducer(
            ipa_far or self._default_ipa_far,
            default_url=default_ipa_far_url(resolved_language.language),
            cache_dir=self._cache_dir,
            key_candidates=["ISO_TO_IPA"],
        )
        try:
            output_text = transduce_text(text, ipa_fst)
        except ValueError:
            return _unsupported_result(
                text,
                direction="to_ipa_from_iso",
                input_was_iso=True,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                ipa_far=resolved_far,
                reason=(
                    "Input is not valid ISO transliteration for the selected "
                    "IPA transcription grammar."
                ),
            )

        return IpaTranscriptionResult(
            text=text,
            output_text=output_text,
            supported=True,
            direction="to_ipa_from_iso",
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            ipa_key=ipa_key,
            ipa_far=resolved_far,
            input_was_iso=True,
            iso_text=text,
            iso_far=None,
            visual_norm_applied=False,
            visual_norm_key=None,
            visual_norm_far=None,
        )

    def transcribe(
        self,
        text: str,
        language: str,
        ipa_far: str | Path | None = None,
        iso_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
    ) -> IpaTranscriptionResult:
        resolved_language, reason = resolve_supported_ipa_language(
            language,
            purpose="IPA transcription",
            feature_name="IPA transcription",
        )
        if reason is not None:
            return _unsupported_result(
                text,
                direction="to_ipa",
                input_was_iso=False,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                reason=reason,
            )

        iso_result = self._iso.transliterate_to_iso(
            text,
            language=resolved_language.language,
            iso_far=iso_far,
            visual_norm_far=visual_norm_far,
            apply_visual_norm=apply_visual_norm,
        )
        if not iso_result.supported or iso_result.output_text is None:
            return _unsupported_result(
                text,
                direction="to_ipa",
                input_was_iso=False,
                resolved_language=iso_result.resolved_language,
                resolved_script=iso_result.resolved_script,
                iso_far=iso_result.iso_far,
                visual_norm_applied=iso_result.visual_norm_applied,
                visual_norm_key=iso_result.visual_norm_key,
                visual_norm_far=iso_result.visual_norm_far,
                reason=iso_result.reason or "Could not transliterate the text to ISO.",
            )

        ipa_result = self.transcribe_iso(
            iso_result.output_text,
            language=resolved_language.language,
            ipa_far=ipa_far,
        )
        if not ipa_result.supported:
            return replace(
                ipa_result,
                text=text,
                direction="to_ipa",
                input_was_iso=False,
                iso_text=iso_result.output_text,
                iso_far=iso_result.iso_far,
                visual_norm_applied=iso_result.visual_norm_applied,
                visual_norm_key=iso_result.visual_norm_key,
                visual_norm_far=iso_result.visual_norm_far,
            )

        return replace(
            ipa_result,
            text=text,
            direction="to_ipa",
            input_was_iso=False,
            iso_text=iso_result.output_text,
            iso_far=iso_result.iso_far,
            visual_norm_applied=iso_result.visual_norm_applied,
            visual_norm_key=iso_result.visual_norm_key,
            visual_norm_far=iso_result.visual_norm_far,
        )

    def to_ipa_from_iso(
        self,
        text: str,
        language: str,
        ipa_far: str | Path | None = None,
    ) -> str:
        return output_text_or_raise(
            self.transcribe_iso(
                text,
                language=language,
                ipa_far=ipa_far,
            ),
            "Could not transcribe the ISO text to IPA.",
        )

    def to_ipa(
        self,
        text: str,
        language: str,
        ipa_far: str | Path | None = None,
        iso_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
    ) -> str:
        return output_text_or_raise(
            self.transcribe(
                text,
                language=language,
                ipa_far=ipa_far,
                iso_far=iso_far,
                visual_norm_far=visual_norm_far,
                apply_visual_norm=apply_visual_norm,
            ),
            "Could not transcribe the text to IPA.",
        )


def to_ipa_from_iso(
    text: str,
    language: str,
    ipa_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return IpaTranscriber(disk_cache=disk_cache).to_ipa_from_iso(
        text,
        language=language,
        ipa_far=ipa_far,
    )


def to_ipa(
    text: str,
    language: str,
    ipa_far: str | Path | None = None,
    iso_far: str | Path | None = None,
    visual_norm_far: str | Path | None = None,
    apply_visual_norm: bool = True,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return IpaTranscriber(disk_cache=disk_cache).to_ipa(
        text,
        language=language,
        ipa_far=ipa_far,
        iso_far=iso_far,
        visual_norm_far=visual_norm_far,
        apply_visual_norm=apply_visual_norm,
    )


__all__ = [
    "to_ipa",
    "to_ipa_from_iso",
    "IpaTranscriber",
    "IpaTranscriptionResult",
]
