from __future__ import annotations

from pathlib import Path

from nisaba_tools._far_fst import resolve_far_path, validate_far_variant
from nisaba_tools.far_assets import (
    DEFAULT_WELLFORMED_FAR_URL,
    default_reading_norm_far_url,
    default_visual_norm_far_url,
)


def resolve_visual_norm_path(
    visual_norm_far: str | Path | None,
    default_visual_norm_far: str | Path | None,
    key: str,
    *,
    cache_dir: Path,
) -> Path:
    path = resolve_far_path(
        visual_norm_far or default_visual_norm_far,
        default_visual_norm_far_url(key),
        cache_dir,
    )
    validate_far_variant(path)
    return path


def resolve_reading_norm_path(
    reading_norm_far: str | Path | None,
    default_reading_norm_far: str | Path | None,
    key: str,
    *,
    cache_dir: Path,
) -> Path:
    path = resolve_far_path(
        reading_norm_far or default_reading_norm_far,
        default_reading_norm_far_url(key),
        cache_dir,
    )
    validate_far_variant(path)
    return path


def resolve_wellformed_path(
    wellformed_far: str | Path | None,
    *,
    cache_dir: Path,
) -> Path:
    path = resolve_far_path(
        wellformed_far,
        DEFAULT_WELLFORMED_FAR_URL,
        cache_dir,
    )
    validate_far_variant(path)
    return path
