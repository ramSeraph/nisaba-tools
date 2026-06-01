from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from nisaba_tools._far_fst import (
    DiskCacheSetting,
    resolve_disk_cache_dir,
    resolve_far_transducer,
    transduce_text,
)
from nisaba_tools._natural_translit import resolve_supported_natural_roman_language
from nisaba_tools._result_utils import output_text_or_raise
from nisaba_tools.far_assets import default_natural_roman_far_url
from nisaba_tools.iso import IsoTransliterator

_SCHEME_ALIASES = {
    "nat": "nat",
    "natural": "nat",
    "natural-romanization": "nat",
    "psac": "psac",
    "pan-south-asian-coarse": "psac",
    "coarse": "psac",
    "psaf": "psaf",
    "pan-south-asian-fine": "psaf",
    "fine": "psaf",
}

_SCHEME_TO_FAR_KEY = {
    "nat": "ISO_TO_NAT",
    "psac": "ISO_TO_PSAC",
    "psaf": "ISO_TO_PSAF",
}


@dataclass(frozen=True)
class NaturalRomanizationResult:
    text: str
    output_text: str | None
    supported: bool
    direction: str
    resolved_language: str | None
    resolved_script: str | None
    scheme: str | None
    roman_key: str | None
    roman_far: Path | None
    input_was_iso: bool
    iso_text: str | None
    iso_far: Path | None
    visual_norm_applied: bool
    visual_norm_key: str | None
    visual_norm_far: Path | None
    reason: str | None = None


def _resolve_scheme(scheme: str) -> str:
    normalized = scheme.strip().lower().replace("_", "-")
    if normalized not in _SCHEME_ALIASES:
        raise ValueError(
            f"Unsupported natural romanization scheme: {scheme}. "
            "Use one of: nat, psac, psaf."
        )
    return _SCHEME_ALIASES[normalized]


def _unsupported_result(
    text: str,
    *,
    direction: str,
    scheme: str | None,
    input_was_iso: bool,
    resolved_language: str | None = None,
    resolved_script: str | None = None,
    roman_far: Path | None = None,
    iso_text: str | None = None,
    iso_far: Path | None = None,
    visual_norm_applied: bool = False,
    visual_norm_key: str | None = None,
    visual_norm_far: Path | None = None,
    reason: str,
) -> NaturalRomanizationResult:
    return NaturalRomanizationResult(
        text=text,
        output_text=None,
        supported=False,
        direction=direction,
        resolved_language=resolved_language,
        resolved_script=resolved_script,
        scheme=scheme,
        roman_key=None,
        roman_far=roman_far,
        input_was_iso=input_was_iso,
        iso_text=iso_text,
        iso_far=iso_far,
        visual_norm_applied=visual_norm_applied,
        visual_norm_key=visual_norm_key,
        visual_norm_far=visual_norm_far,
        reason=reason,
    )


class NaturalRomanTransliterator:
    def __init__(
        self,
        roman_far: str | Path | None = None,
        iso_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_roman_far = roman_far
        self._iso = IsoTransliterator(
            iso_far=iso_far,
            visual_norm_far=visual_norm_far,
            disk_cache=self._cache_dir,
        )

    def transliterate_iso(
        self,
        text: str,
        language: str,
        scheme: str = "nat",
        roman_far: str | Path | None = None,
    ) -> NaturalRomanizationResult:
        resolved_scheme = _resolve_scheme(scheme)
        resolved_language, reason = resolve_supported_natural_roman_language(
            language,
            purpose="Natural romanization from ISO",
            feature_name="Natural romanization",
        )
        if reason is not None:
            return _unsupported_result(
                text,
                direction="natural_romanize_iso",
                scheme=resolved_scheme,
                input_was_iso=True,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                reason=reason,
            )

        resolved_far, roman_key, roman_fst = resolve_far_transducer(
            roman_far or self._default_roman_far,
            default_url=default_natural_roman_far_url(
                resolved_language.language,
                resolved_scheme,
            ),
            cache_dir=self._cache_dir,
            key_candidates=[_SCHEME_TO_FAR_KEY[resolved_scheme]],
        )
        try:
            output_text = transduce_text(text, roman_fst)
        except ValueError:
            return _unsupported_result(
                text,
                direction="natural_romanize_iso",
                scheme=resolved_scheme,
                input_was_iso=True,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                roman_far=resolved_far,
                reason=(
                    "Input is not valid ISO transliteration for the selected "
                    "natural romanization grammar."
                ),
            )

        return NaturalRomanizationResult(
            text=text,
            output_text=output_text,
            supported=True,
            direction="natural_romanize_iso",
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            scheme=resolved_scheme,
            roman_key=roman_key,
            roman_far=resolved_far,
            input_was_iso=True,
            iso_text=text,
            iso_far=None,
            visual_norm_applied=False,
            visual_norm_key=None,
            visual_norm_far=None,
        )

    def transliterate(
        self,
        text: str,
        language: str,
        scheme: str = "nat",
        roman_far: str | Path | None = None,
        iso_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
    ) -> NaturalRomanizationResult:
        resolved_scheme = _resolve_scheme(scheme)
        resolved_language, reason = resolve_supported_natural_roman_language(
            language,
            purpose="Natural romanization",
            feature_name="Natural romanization",
        )
        if reason is not None:
            return _unsupported_result(
                text,
                direction="natural_romanize",
                scheme=resolved_scheme,
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
                direction="natural_romanize",
                scheme=resolved_scheme,
                input_was_iso=False,
                resolved_language=iso_result.resolved_language,
                resolved_script=iso_result.resolved_script,
                iso_far=iso_result.iso_far,
                visual_norm_applied=iso_result.visual_norm_applied,
                visual_norm_key=iso_result.visual_norm_key,
                visual_norm_far=iso_result.visual_norm_far,
                reason=iso_result.reason or "Could not transliterate the text to ISO.",
            )

        roman_result = self.transliterate_iso(
            iso_result.output_text,
            language=resolved_language.language,
            scheme=resolved_scheme,
            roman_far=roman_far,
        )
        if not roman_result.supported:
            return replace(
                roman_result,
                text=text,
                direction="natural_romanize",
                input_was_iso=False,
                iso_text=iso_result.output_text,
                iso_far=iso_result.iso_far,
                visual_norm_applied=iso_result.visual_norm_applied,
                visual_norm_key=iso_result.visual_norm_key,
                visual_norm_far=iso_result.visual_norm_far,
            )

        return replace(
            roman_result,
            text=text,
            direction="natural_romanize",
            input_was_iso=False,
            iso_text=iso_result.output_text,
            iso_far=iso_result.iso_far,
            visual_norm_applied=iso_result.visual_norm_applied,
            visual_norm_key=iso_result.visual_norm_key,
            visual_norm_far=iso_result.visual_norm_far,
        )

    def natural_romanize_iso(
        self,
        text: str,
        language: str,
        scheme: str = "nat",
        roman_far: str | Path | None = None,
    ) -> str:
        return output_text_or_raise(
            self.transliterate_iso(
                text,
                language=language,
                scheme=scheme,
                roman_far=roman_far,
            ),
            "Could not romanize the ISO text with the selected natural grammar.",
        )

    def natural_romanize(
        self,
        text: str,
        language: str,
        scheme: str = "nat",
        roman_far: str | Path | None = None,
        iso_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
    ) -> str:
        return output_text_or_raise(
            self.transliterate(
                text,
                language=language,
                scheme=scheme,
                roman_far=roman_far,
                iso_far=iso_far,
                visual_norm_far=visual_norm_far,
                apply_visual_norm=apply_visual_norm,
            ),
            "Could not romanize the text with the selected natural grammar.",
        )


def natural_romanize_from_iso(
    text: str,
    language: str,
    scheme: str = "nat",
    roman_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return NaturalRomanTransliterator(
        disk_cache=disk_cache,
    ).natural_romanize_iso(
        text,
        language=language,
        scheme=scheme,
        roman_far=roman_far,
    )


def natural_romanize(
    text: str,
    language: str,
    scheme: str = "nat",
    roman_far: str | Path | None = None,
    iso_far: str | Path | None = None,
    visual_norm_far: str | Path | None = None,
    apply_visual_norm: bool = True,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return NaturalRomanTransliterator(
        disk_cache=disk_cache,
    ).natural_romanize(
        text,
        language=language,
        scheme=scheme,
        roman_far=roman_far,
        iso_far=iso_far,
        visual_norm_far=visual_norm_far,
        apply_visual_norm=apply_visual_norm,
    )


__all__ = [
    "natural_romanize",
    "natural_romanize_from_iso",
    "NaturalRomanizationResult",
    "NaturalRomanTransliterator",
]
