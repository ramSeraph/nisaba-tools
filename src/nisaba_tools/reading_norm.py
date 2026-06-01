from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rustfst import VectorFst

from nisaba_tools._far_fst import (
    DiskCacheSetting,
    byte_string_fst,
    load_far_fst,
    normalized_output_fst,
    resolve_disk_cache_dir,
    select_far_key,
    transduce_input_fst,
)
from nisaba_tools._far_paths import (
    resolve_reading_norm_path,
    resolve_visual_norm_path,
)
from nisaba_tools.languages import resolve_language


def _reading_norm_candidates(language: str | None, script_key: str) -> list[str]:
    candidates: list[str] = []
    if language is not None and "-" not in language:
        candidates.append(language.upper())
    candidates.append(script_key)
    return candidates


def _default_reading_norm_key(language: str | None, script_key: str) -> str | None:
    if language == "hi":
        return "HI"
    if script_key in {"BENG", "LEPC", "MLYM"}:
        return script_key
    return None


@dataclass(frozen=True)
class ReadingNormalizationResult:
    text: str
    normalized_text: str | None
    supported: bool
    guessed: bool
    resolved_language: str | None
    resolved_script: str | None
    reading_norm_key: str | None
    reading_norm_far: Path | None
    visual_norm_applied: bool
    visual_norm_key: str | None
    visual_norm_far: Path | None
    reason: str | None = None


def _compose_reading_norm(
    text: str,
    reading_norm_fst: VectorFst,
    *,
    visual_norm_fst: VectorFst | None,
) -> str:
    input_fst = (
        normalized_output_fst(text, visual_norm_fst)
        if visual_norm_fst is not None
        else byte_string_fst(text)
    )
    return transduce_input_fst(input_fst, reading_norm_fst)


def _unsupported_result(
    text: str,
    *,
    guessed: bool = False,
    resolved_language: str | None = None,
    resolved_script: str | None = None,
    reason: str,
) -> ReadingNormalizationResult:
    return ReadingNormalizationResult(
        text=text,
        normalized_text=None,
        supported=False,
        guessed=guessed,
        resolved_language=resolved_language,
        resolved_script=resolved_script,
        reading_norm_key=None,
        reading_norm_far=None,
        visual_norm_applied=False,
        visual_norm_key=None,
        visual_norm_far=None,
        reason=reason,
    )


class ReadingNormalizer:
    def __init__(
        self,
        reading_norm_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_reading_norm_far = reading_norm_far
        self._default_visual_norm_far = visual_norm_far

    def normalize(
        self,
        text: str,
        language: str | None = None,
        reading_norm_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
    ) -> ReadingNormalizationResult:
        resolved_language = resolve_language(language, text)
        if resolved_language is None:
            return _unsupported_result(
                text,
                reason="Could not infer a supported language or script from the text.",
            )
        if (
            resolved_language.family == "abjad"
            and resolved_language.language.startswith("und-")
        ):
            return _unsupported_result(
                text,
                guessed=resolved_language.guessed,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                reason=(
                    "Arabic-script reading normalization requires an explicit language "
                    "code such as ur, fa, or ckb."
                ),
            )

        if resolved_language.family == "brahmic":
            default_key = _default_reading_norm_key(
                resolved_language.language,
                resolved_language.script_key,
            )
            if (
                default_key is None
                and reading_norm_far is None
                and self._default_reading_norm_far is None
            ):
                return _unsupported_result(
                    text,
                    guessed=resolved_language.guessed,
                    resolved_language=resolved_language.language,
                    resolved_script=resolved_language.script_key,
                    reason=(
                        "No default reading_norm FAR asset is available for "
                        f"{resolved_language.language}."
                    ),
                )
            if default_key is None:
                default_key = resolved_language.script_key
        else:
            default_key = resolved_language.visual_norm_key

        resolved_far = resolve_reading_norm_path(
            reading_norm_far,
            self._default_reading_norm_far,
            default_key,
            cache_dir=self._cache_dir,
        )
        if resolved_language.family == "brahmic":
            reading_norm_key = select_far_key(
                resolved_far,
                _reading_norm_candidates(
                    resolved_language.language,
                    resolved_language.script_key,
                ),
            )
        else:
            reading_norm_key = select_far_key(
                resolved_far, [resolved_language.visual_norm_key]
            )
        reading_norm_fst = load_far_fst(resolved_far, reading_norm_key)
        visual_norm_path = None
        visual_norm_key = None
        visual_norm_fst = None
        if apply_visual_norm:
            if resolved_language.family == "brahmic":
                visual_norm_path = resolve_visual_norm_path(
                    visual_norm_far or self._default_visual_norm_far,
                    None,
                    resolved_language.visual_norm_key,
                    cache_dir=self._cache_dir,
                )
                visual_norm_key = resolved_language.visual_norm_key
            else:
                visual_norm_path = resolve_visual_norm_path(
                    visual_norm_far,
                    self._default_visual_norm_far,
                    resolved_language.visual_norm_key,
                    cache_dir=self._cache_dir,
                )
                visual_norm_key = select_far_key(
                    visual_norm_path, [resolved_language.visual_norm_key]
                )
            visual_norm_fst = load_far_fst(visual_norm_path, visual_norm_key)

        normalized_text = _compose_reading_norm(
            text,
            reading_norm_fst,
            visual_norm_fst=visual_norm_fst,
        )
        return ReadingNormalizationResult(
            text=text,
            normalized_text=normalized_text,
            supported=True,
            guessed=resolved_language.guessed,
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            reading_norm_key=reading_norm_key,
            reading_norm_far=resolved_far,
            visual_norm_applied=apply_visual_norm,
            visual_norm_key=visual_norm_key,
            visual_norm_far=visual_norm_path,
        )

    def reading_normalize(
        self,
        text: str,
        language: str | None = None,
        reading_norm_far: str | Path | None = None,
        visual_norm_far: str | Path | None = None,
        apply_visual_norm: bool = True,
    ) -> str:
        result = self.normalize(
            text,
            language=language,
            reading_norm_far=reading_norm_far,
            visual_norm_far=visual_norm_far,
            apply_visual_norm=apply_visual_norm,
        )
        if not result.supported or result.normalized_text is None:
            if result.reason is not None:
                raise ValueError(result.reason)
            raise ValueError("Could not normalize the text for reading.")
        return result.normalized_text


def reading_normalize(
    text: str,
    language: str | None = None,
    reading_norm_far: str | Path | None = None,
    visual_norm_far: str | Path | None = None,
    apply_visual_norm: bool = True,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return ReadingNormalizer(disk_cache=disk_cache).reading_normalize(
        text,
        language=language,
        reading_norm_far=reading_norm_far,
        visual_norm_far=visual_norm_far,
        apply_visual_norm=apply_visual_norm,
    )


__all__ = [
    "reading_normalize",
    "ReadingNormalizationResult",
    "ReadingNormalizer",
]
