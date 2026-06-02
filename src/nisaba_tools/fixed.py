from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nisaba_tools._far_fst import (
    DiskCacheSetting,
    load_far_fst,
    resolve_disk_cache_dir,
    resolve_far_path,
    select_far_key,
    transduce_text,
    validate_far_variant,
)
from nisaba_tools._result_utils import output_text_or_raise
from nisaba_tools.far_assets import DEFAULT_FIXED_FAR_URL
from nisaba_tools.languages import resolve_explicit_language

_FIXED_SCHEME_ALIASES = {
    "mozhi": "Mozhi",
}

_DEFAULT_FIXED_SCHEME_BY_SCRIPT = {
    "MLYM": "Mozhi",
}

_FIXED_SCHEME_TO_SCRIPT = {
    "Mozhi": "MLYM",
}


@dataclass(frozen=True)
class FixedTransliterationResult:
    text: str
    output_text: str | None
    supported: bool
    resolved_language: str | None
    resolved_script: str | None
    scheme: str | None
    fixed_key: str | None
    fixed_far: Path | None
    reason: str | None = None


def _canonical_scheme(scheme: str) -> str:
    normalized = scheme.strip().lower()
    if normalized not in _FIXED_SCHEME_ALIASES:
        raise ValueError(f"Unsupported fixed transliteration scheme: {scheme}")
    return _FIXED_SCHEME_ALIASES[normalized]


def _resolve_fixed_scheme(script_key: str, scheme: str | None) -> str:
    if scheme is None:
        default_scheme = _DEFAULT_FIXED_SCHEME_BY_SCRIPT.get(script_key)
        if default_scheme is None:
            raise ValueError(
                "Fixed transliteration requires an explicit scheme for this "
                f"script: {script_key}"
            )
        return default_scheme

    canonical_scheme = _canonical_scheme(scheme)
    expected_script = _FIXED_SCHEME_TO_SCRIPT[canonical_scheme]
    if expected_script != script_key:
        raise ValueError(
            f"Fixed scheme {canonical_scheme} does not match target script {script_key}"
        )
    return canonical_scheme


class FixedTransliterator:
    def __init__(
        self,
        fixed_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_fixed_far = fixed_far

    def transliterate(
        self,
        text: str,
        language: str | None,
        scheme: str | None = None,
        fixed_far: str | Path | None = None,
    ) -> FixedTransliterationResult:
        resolved_language = resolve_explicit_language(
            language,
            purpose="Fixed transliteration",
        )
        if resolved_language.family != "brahmic":
            raise ValueError(
                "Fixed transliteration is only supported for Brahmic scripts."
            )
        resolved_scheme = _resolve_fixed_scheme(resolved_language.script_key, scheme)
        using_default_far = fixed_far is None and self._default_fixed_far is None
        resolved_far = resolve_far_path(
            fixed_far or self._default_fixed_far,
            DEFAULT_FIXED_FAR_URL,
            self._cache_dir,
        )
        validate_far_variant(resolved_far)

        try:
            fixed_key = select_far_key(resolved_far, [resolved_language.script_key])
        except KeyError:
            if not using_default_far:
                raise
            return FixedTransliterationResult(
                text=text,
                output_text=None,
                supported=False,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                scheme=resolved_scheme,
                fixed_key=None,
                fixed_far=resolved_far,
                reason=(
                    "No default fixed FAR entry is available for "
                    f"{resolved_language.language}."
                ),
            )

        fixed_fst = load_far_fst(resolved_far, fixed_key)
        return FixedTransliterationResult(
            text=text,
            output_text=transduce_text(text, fixed_fst),
            supported=True,
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            scheme=resolved_scheme,
            fixed_key=fixed_key,
            fixed_far=resolved_far,
        )

    def fixed_transliterate(
        self,
        text: str,
        language: str | None,
        scheme: str | None = None,
        fixed_far: str | Path | None = None,
    ) -> str:
        return output_text_or_raise(
            self.transliterate(
                text,
                language=language,
                scheme=scheme,
                fixed_far=fixed_far,
            ),
            "Could not transliterate the text with fixed rules.",
        )


def fixed_transliterate(
    text: str,
    language: str | None,
    scheme: str | None = None,
    fixed_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return FixedTransliterator(disk_cache=disk_cache).fixed_transliterate(
        text,
        language=language,
        scheme=scheme,
        fixed_far=fixed_far,
    )


__all__ = [
    "fixed_transliterate",
    "FixedTransliterationResult",
    "FixedTransliterator",
]
