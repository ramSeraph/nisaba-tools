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
    resolve_supported_deromanization_language,
)
from nisaba_tools._result_utils import output_text_or_raise
from nisaba_tools.far_assets import default_natural_deroman_far_url


@dataclass(frozen=True)
class NaturalDeromanizationResult:
    text: str
    output_text: str | None
    supported: bool
    direction: str
    resolved_language: str | None
    resolved_script: str | None
    derom_key: str | None
    derom_far: Path | None
    reason: str | None = None


def _unsupported_result(
    text: str,
    *,
    direction: str,
    resolved_language: str | None = None,
    resolved_script: str | None = None,
    derom_far: Path | None = None,
    reason: str,
) -> NaturalDeromanizationResult:
    return NaturalDeromanizationResult(
        text=text,
        output_text=None,
        supported=False,
        direction=direction,
        resolved_language=resolved_language,
        resolved_script=resolved_script,
        derom_key=None,
        derom_far=derom_far,
        reason=reason,
    )


class NaturalDeromanizer:
    def __init__(
        self,
        derom_far: str | Path | None = None,
        iso_derom_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_derom_far = derom_far
        self._default_iso_derom_far = iso_derom_far

    def transliterate(
        self,
        text: str,
        language: str,
        derom_far: str | Path | None = None,
    ) -> NaturalDeromanizationResult:
        resolved_language, reason = resolve_supported_deromanization_language(
            language,
            purpose="Natural deromanization",
            feature_name="Natural deromanization",
        )
        if reason is not None:
            return _unsupported_result(
                text,
                direction="natural_deromanize",
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                reason=reason,
            )

        resolved_far, derom_key, derom_fst = resolve_far_transducer(
            derom_far or self._default_derom_far,
            default_url=default_natural_deroman_far_url(
                resolved_language.language,
                "script",
            ),
            cache_dir=self._cache_dir,
            key_candidates=[resolved_language.script_key],
        )
        try:
            output_text = transduce_text(text, derom_fst)
        except ValueError:
            return _unsupported_result(
                text,
                direction="natural_deromanize",
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                derom_far=resolved_far,
                reason=(
                    "Input is not valid Latin text for the selected natural "
                    "deromanization grammar."
                ),
            )

        return NaturalDeromanizationResult(
            text=text,
            output_text=output_text,
            supported=True,
            direction="natural_deromanize",
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            derom_key=derom_key,
            derom_far=resolved_far,
        )

    def transliterate_to_iso(
        self,
        text: str,
        language: str,
        derom_far: str | Path | None = None,
    ) -> NaturalDeromanizationResult:
        resolved_language, reason = resolve_supported_deromanization_language(
            language,
            purpose="Natural deromanization to ISO",
            feature_name="Natural deromanization",
        )
        if reason is not None:
            return _unsupported_result(
                text,
                direction="natural_deromanize_to_iso",
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                reason=reason,
            )

        resolved_far, derom_key, derom_fst = resolve_far_transducer(
            derom_far or self._default_iso_derom_far,
            default_url=default_natural_deroman_far_url(
                resolved_language.language,
                "iso",
            ),
            cache_dir=self._cache_dir,
            key_candidates=["ISO"],
        )
        try:
            output_text = transduce_text(text, derom_fst)
        except ValueError:
            return _unsupported_result(
                text,
                direction="natural_deromanize_to_iso",
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                derom_far=resolved_far,
                reason=(
                    "Input is not valid Latin text for the selected natural "
                    "deromanization grammar."
                ),
            )

        return NaturalDeromanizationResult(
            text=text,
            output_text=output_text,
            supported=True,
            direction="natural_deromanize_to_iso",
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            derom_key=derom_key,
            derom_far=resolved_far,
        )

    def natural_deromanize(
        self,
        text: str,
        language: str,
        derom_far: str | Path | None = None,
    ) -> str:
        return output_text_or_raise(
            self.transliterate(
                text,
                language=language,
                derom_far=derom_far,
            ),
            "Could not deromanize the text with the selected natural grammar.",
        )

    def natural_deromanize_to_iso(
        self,
        text: str,
        language: str,
        derom_far: str | Path | None = None,
    ) -> str:
        return output_text_or_raise(
            self.transliterate_to_iso(
                text,
                language=language,
                derom_far=derom_far,
            ),
            "Could not deromanize the text to ISO with the selected natural grammar.",
        )


def natural_deromanize(
    text: str,
    language: str,
    derom_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return NaturalDeromanizer(
        disk_cache=disk_cache,
    ).natural_deromanize(
        text,
        language=language,
        derom_far=derom_far,
    )


def natural_deromanize_to_iso(
    text: str,
    language: str,
    derom_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return NaturalDeromanizer(
        disk_cache=disk_cache,
    ).natural_deromanize_to_iso(
        text,
        language=language,
        derom_far=derom_far,
    )


__all__ = [
    "natural_deromanize",
    "natural_deromanize_to_iso",
    "NaturalDeromanizationResult",
    "NaturalDeromanizer",
]
