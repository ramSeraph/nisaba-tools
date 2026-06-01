from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nisaba_tools._far_fst import (
    DiskCacheSetting,
    is_accepting,
    load_far_fst,
    normalized_output_fst,
    resolve_disk_cache_dir,
)
from nisaba_tools._far_paths import resolve_visual_norm_path, resolve_wellformed_path
from nisaba_tools.languages import resolve_language


@dataclass(frozen=True)
class WellFormednessResult:
    text: str
    is_wellformed: bool
    supported: bool
    guessed: bool
    resolved_language: str | None
    resolved_script: str | None
    visual_norm_key: str | None
    wellformed_key: str | None
    visual_norm_far: Path | None
    wellformed_far: Path | None
    reason: str | None = None


class WellFormednessChecker:
    def __init__(
        self,
        visual_norm_far: str | Path | None = None,
        wellformed_far: str | Path | None = None,
        disk_cache: DiskCacheSetting = True,
    ) -> None:
        self._cache_dir = resolve_disk_cache_dir(disk_cache)
        self._default_visual_norm_far = visual_norm_far
        self._default_wellformed_far = wellformed_far

    def check(
        self,
        text: str,
        language: str | None = None,
        visual_norm_far: str | Path | None = None,
        wellformed_far: str | Path | None = None,
    ) -> WellFormednessResult:
        resolved_language = resolve_language(language, text)
        if resolved_language is None:
            return WellFormednessResult(
                text=text,
                is_wellformed=False,
                supported=False,
                guessed=False,
                resolved_language=None,
                resolved_script=None,
                visual_norm_key=None,
                wellformed_key=None,
                visual_norm_far=None,
                wellformed_far=None,
                reason="Could not infer a supported Brahmic script from the text.",
            )
        if resolved_language.family != "brahmic":
            return WellFormednessResult(
                text=text,
                is_wellformed=False,
                supported=False,
                guessed=resolved_language.guessed,
                resolved_language=resolved_language.language,
                resolved_script=resolved_language.script_key,
                visual_norm_key=None,
                wellformed_key=None,
                visual_norm_far=None,
                wellformed_far=None,
                reason="Well-formedness checks are only supported for Brahmic scripts.",
            )

        visual_norm_path = resolve_visual_norm_path(
            visual_norm_far or self._default_visual_norm_far,
            None,
            resolved_language.visual_norm_key,
            cache_dir=self._cache_dir,
        )
        wellformed_path = resolve_wellformed_path(
            wellformed_far or self._default_wellformed_far,
            cache_dir=self._cache_dir,
        )
        visual_norm_fst = load_far_fst(
            visual_norm_path, resolved_language.visual_norm_key
        )
        wellformed_fst = load_far_fst(wellformed_path, resolved_language.wellformed_key)
        accepted = normalized_output_fst(text, visual_norm_fst).compose(wellformed_fst)

        return WellFormednessResult(
            text=text,
            is_wellformed=is_accepting(accepted),
            supported=True,
            guessed=resolved_language.guessed,
            resolved_language=resolved_language.language,
            resolved_script=resolved_language.script_key,
            visual_norm_key=resolved_language.visual_norm_key,
            wellformed_key=resolved_language.wellformed_key,
            visual_norm_far=visual_norm_path,
            wellformed_far=wellformed_path,
        )


def is_wellformed(
    text: str,
    language: str | None = None,
    visual_norm_far: str | Path | None = None,
    wellformed_far: str | Path | None = None,
    disk_cache: DiskCacheSetting = True,
) -> bool:
    return (
        WellFormednessChecker(disk_cache=disk_cache)
        .check(
            text,
            language=language,
            visual_norm_far=visual_norm_far,
            wellformed_far=wellformed_far,
        )
        .is_wellformed
    )
