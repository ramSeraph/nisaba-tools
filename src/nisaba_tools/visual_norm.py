from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nisaba_tools._far_fst import (
    DiskCacheSetting,
    extract_projected_text,
    load_far_fst,
    normalized_output_fst,
    resolve_disk_cache_dir,
    select_far_key,
)
from nisaba_tools._far_paths import resolve_visual_norm_path
from nisaba_tools.languages import resolve_language


@dataclass(frozen=True)
class VisualNormalizationResult:
    text: str
    normalized_text: str | None
    supported: bool
    guessed: bool
    resolved_language: str | None
    resolved_script: str | None
    visual_norm_key: str | None
    visual_norm_far: Path | None
    reason: str | None = None


def _normalized_text_or_raise(result: VisualNormalizationResult) -> str:
    if not result.supported or result.normalized_text is None:
        if result.reason is not None:
            raise ValueError(result.reason)
        raise ValueError("Could not normalize the text.")
    return result.normalized_text


def _unsupported_result(
    text: str,
    *,
    guessed: bool = False,
    resolved_language: str | None = None,
    resolved_script: str | None = None,
    reason: str,
) -> VisualNormalizationResult:
    return VisualNormalizationResult(
        text=text,
        normalized_text=None,
        supported=False,
        guessed=guessed,
        resolved_language=resolved_language,
        resolved_script=resolved_script,
        visual_norm_key=None,
        visual_norm_far=None,
        reason=reason,
    )


class VisualNormalizer:
    def __init__(
        self,
        visual_norm_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_visual_norm_far = visual_norm_far

    def normalize(
        self,
        text: str,
        language: str | None = None,
        visual_norm_far: str | Path | None = None,
    ) -> VisualNormalizationResult:
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
                    "Arabic-script visual normalization requires an explicit language "
                    "code such as ur, fa, or ckb."
                ),
            )

        if resolved_language.family == "brahmic":
            resolved_path = resolve_visual_norm_path(
                visual_norm_far or self._default_visual_norm_far,
                None,
                resolved_language.visual_norm_key,
                cache_dir=self._cache_dir,
            )
            visual_norm_key = resolved_language.visual_norm_key
        else:
            resolved_path = resolve_visual_norm_path(
                visual_norm_far,
                self._default_visual_norm_far,
                resolved_language.visual_norm_key,
                cache_dir=self._cache_dir,
            )
            visual_norm_key = select_far_key(
                resolved_path, [resolved_language.visual_norm_key]
            )

        visual_norm_fst = load_far_fst(resolved_path, visual_norm_key)
        normalized_text = extract_projected_text(
            normalized_output_fst(text, visual_norm_fst)
        )
        return VisualNormalizationResult(
            text=text,
            normalized_text=normalized_text,
            supported=True,
            guessed=resolved_language.guessed,
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            visual_norm_key=visual_norm_key,
            visual_norm_far=resolved_path,
        )

    def visual_normalize(
        self,
        text: str,
        language: str | None = None,
        visual_norm_far: str | Path | None = None,
    ) -> str:
        return _normalized_text_or_raise(
            self.normalize(
                text,
                language=language,
                visual_norm_far=visual_norm_far,
            )
        )


def visual_normalize(
    text: str,
    language: str | None = None,
    visual_norm_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> str:
    return VisualNormalizer(disk_cache=disk_cache).visual_normalize(
        text,
        language=language,
        visual_norm_far=visual_norm_far,
    )


__all__ = [
    "visual_normalize",
    "VisualNormalizationResult",
    "VisualNormalizer",
]
