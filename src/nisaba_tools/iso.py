from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nisaba_tools._far_fst import (
    DiskCacheSetting,
    byte_string_fst,
    load_far_fst,
    normalized_output_fst,
    resolve_disk_cache_dir,
    resolve_far_transducer,
    transduce_input_fst,
    transduce_text,
)
from nisaba_tools._far_paths import resolve_visual_norm_path
from nisaba_tools._result_utils import output_text_or_raise
from nisaba_tools.far_assets import DEFAULT_ISO_FAR_URL
from nisaba_tools.languages import resolve_explicit_language, resolve_language


@dataclass(frozen=True)
class IsoTransliterationResult:
    text: str
    output_text: str | None
    supported: bool
    guessed: bool
    direction: str
    resolved_language: str | None
    resolved_script: str | None
    iso_key: str | None
    iso_far: Path | None
    visual_norm_applied: bool
    visual_norm_key: str | None
    visual_norm_far: Path | None
    reason: str | None = None


class IsoTransliterator:
    def __init__(
        self,
        iso_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_iso_far = iso_far
        self._default_visual_norm_far = visual_norm_far

    def transliterate_to_iso(
        self,
        text: str,
        language: str | None = None,
        iso_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
    ) -> IsoTransliterationResult:
        resolved_language = resolve_language(language, text)
        if resolved_language is None:
            return IsoTransliterationResult(
                text=text,
                output_text=None,
                supported=False,
                guessed=False,
                direction="to_iso",
                resolved_language=None,
                resolved_script=None,
                iso_key=None,
                iso_far=None,
                visual_norm_applied=False,
                visual_norm_key=None,
                visual_norm_far=None,
                reason="Could not infer a supported Brahmic script from the text.",
            )
        if resolved_language.family != "brahmic":
            return IsoTransliterationResult(
                text=text,
                output_text=None,
                supported=False,
                guessed=resolved_language.guessed,
                direction="to_iso",
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                iso_key=None,
                iso_far=None,
                visual_norm_applied=False,
                visual_norm_key=None,
                visual_norm_far=None,
                reason="ISO transliteration is only supported for Brahmic scripts.",
            )

        resolved_far, iso_key, iso_fst = resolve_far_transducer(
            iso_far or self._default_iso_far,
            default_url=DEFAULT_ISO_FAR_URL,
            cache_dir=self._cache_dir,
            key_candidates=[f"FROM_{resolved_language.script_key}"],
        )

        visual_norm_path = None
        visual_norm_key = None
        input_fst = byte_string_fst(text)
        if apply_visual_norm:
            visual_norm_path = resolve_visual_norm_path(
                visual_norm_far or self._default_visual_norm_far,
                None,
                resolved_language.visual_norm_key,
                cache_dir=self._cache_dir,
            )
            visual_norm_key = resolved_language.visual_norm_key
            visual_norm_fst = load_far_fst(visual_norm_path, visual_norm_key)
            input_fst = normalized_output_fst(text, visual_norm_fst)

        return IsoTransliterationResult(
            text=text,
            output_text=transduce_input_fst(input_fst, iso_fst),
            supported=True,
            guessed=resolved_language.guessed,
            direction="to_iso",
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            iso_key=iso_key,
            iso_far=resolved_far,
            visual_norm_applied=apply_visual_norm,
            visual_norm_key=visual_norm_key,
            visual_norm_far=visual_norm_path,
        )

    def transliterate_from_iso(
        self,
        text: str,
        language: str | None,
        iso_far: str | Path | None = None,
    ) -> IsoTransliterationResult:
        resolved_language = resolve_explicit_language(
            language,
            purpose="ISO deromanization",
        )
        if resolved_language.family != "brahmic":
            return IsoTransliterationResult(
                text=text,
                output_text=None,
                supported=False,
                guessed=False,
                direction="from_iso",
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                iso_key=None,
                iso_far=None,
                visual_norm_applied=False,
                visual_norm_key=None,
                visual_norm_far=None,
                reason="ISO transliteration is only supported for Brahmic scripts.",
            )
        resolved_far, iso_key, iso_fst = resolve_far_transducer(
            iso_far or self._default_iso_far,
            default_url=DEFAULT_ISO_FAR_URL,
            cache_dir=self._cache_dir,
            key_candidates=[f"TO_{resolved_language.script_key}"],
        )
        return IsoTransliterationResult(
            text=text,
            output_text=transduce_text(text, iso_fst),
            supported=True,
            guessed=False,
            direction="from_iso",
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            iso_key=iso_key,
            iso_far=resolved_far,
            visual_norm_applied=False,
            visual_norm_key=None,
            visual_norm_far=None,
        )

    def to_iso(
        self,
        text: str,
        language: str | None = None,
        iso_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
    ) -> str:
        return output_text_or_raise(
            self.transliterate_to_iso(
                text,
                language=language,
                iso_far=iso_far,
                visual_norm_far=visual_norm_far,
                apply_visual_norm=apply_visual_norm,
            ),
            "Could not transliterate the text to ISO.",
        )

    def from_iso(
        self,
        text: str,
        language: str | None,
        iso_far: str | Path | None = None,
    ) -> str:
        return output_text_or_raise(
            self.transliterate_from_iso(
                text,
                language=language,
                iso_far=iso_far,
            ),
            "Could not transliterate the ISO text to Brahmic script.",
        )


def to_iso(
    text: str,
    language: str | None = None,
    iso_far: str | Path | None = None,
    visual_norm_far: str | Path | None = None,
    apply_visual_norm: bool = True,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return IsoTransliterator(disk_cache=disk_cache).to_iso(
        text,
        language=language,
        iso_far=iso_far,
        visual_norm_far=visual_norm_far,
        apply_visual_norm=apply_visual_norm,
    )


def from_iso(
    text: str,
    language: str | None,
    iso_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return IsoTransliterator(disk_cache=disk_cache).from_iso(
        text,
        language=language,
        iso_far=iso_far,
    )


__all__ = [
    "from_iso",
    "to_iso",
    "IsoTransliterationResult",
    "IsoTransliterator",
]
