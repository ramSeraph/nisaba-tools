from __future__ import annotations

from pathlib import Path
import struct
import tempfile

import pytest
from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import (
    VisualNormalizer,
    visual_normalize,
)
from nisaba_tools.far_assets import default_visual_norm_far_url

STTABLE_MAGIC = 0x7EB2F35C
STTABLE_VERSION = 1


def _mapping_fst(source_text: str, target_text: str) -> VectorFst:
    source_bytes = source_text.encode("utf-8")
    target_bytes = target_text.encode("utf-8")
    assert len(source_bytes) == len(target_bytes)

    fst = VectorFst()
    current_state = fst.add_state()
    fst.set_start(current_state)
    for input_label, output_label in zip(source_bytes, target_bytes):
        next_state = fst.add_state()
        fst.add_tr(current_state, Tr(input_label, output_label, 0.0, next_state))
        current_state = next_state
    fst.set_final(current_state, 0.0)
    return fst


def _const_bytes(fst: VectorFst) -> bytes:
    const_fst = ConstFst.from_vector_fst(fst)
    with tempfile.NamedTemporaryFile(suffix=".fst", delete=False) as temp_file:
        temp_name = temp_file.name
    try:
        const_fst.write(temp_name)
        return Path(temp_name).read_bytes()
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _write_far(path: Path, entries: list[tuple[str, bytes]]) -> None:
    payload = bytearray(struct.pack("<II", STTABLE_MAGIC, STTABLE_VERSION))
    positions: list[int] = []
    for key, fst_bytes in entries:
        positions.append(len(payload))
        key_bytes = key.encode("utf-8")
        payload.extend(struct.pack("<i", len(key_bytes)))
        payload.extend(key_bytes)
        payload.extend(fst_bytes)
    payload.extend(struct.pack("<q", len(entries)))
    for position in positions:
        payload.extend(struct.pack("<q", position))
    payload.extend(struct.pack("<q", len(entries)))
    path.write_bytes(payload)


def test_visual_normalize_returns_normalized_text(tmp_path: Path) -> None:
    visual_norm_far = tmp_path / "visual_norm.far"
    _write_far(visual_norm_far, [("DEVA", _const_bytes(_mapping_fst("क़", "क")))])

    result = VisualNormalizer().normalize(
        "क़", language="hi", visual_norm_far=visual_norm_far
    )

    assert result.supported is True
    assert result.normalized_text == "क"
    assert result.resolved_language == "hi"
    assert result.visual_norm_key == "DEVA"


def test_visual_normalize_string_helper_returns_string(tmp_path: Path) -> None:
    visual_norm_far = tmp_path / "visual_norm.far"
    _write_far(visual_norm_far, [("DEVA", _const_bytes(_mapping_fst("क़", "क")))])

    assert (
        visual_normalize("क़", language="und-Deva", visual_norm_far=visual_norm_far)
        == "क"
    )


def test_visual_normalizer_object_api_raises_for_unsupported_text(
    tmp_path: Path,
) -> None:
    visual_norm_far = tmp_path / "visual_norm.far"
    _write_far(visual_norm_far, [("DEVA", _const_bytes(_mapping_fst("क़", "क")))])

    normalizer = VisualNormalizer(visual_norm_far=visual_norm_far)

    with pytest.raises(ValueError, match="Could not infer"):
        normalizer.visual_normalize("latin")


def test_visual_normalize_supports_abjad_language_keys(tmp_path: Path) -> None:
    visual_norm_far = tmp_path / "visual_norm.far"
    _write_far(visual_norm_far, [("UR", _const_bytes(_mapping_fst("ك", "ک")))])

    result = VisualNormalizer().normalize(
        "ك", language="ur", visual_norm_far=visual_norm_far
    )

    assert result.supported is True
    assert result.normalized_text == "ک"
    assert result.resolved_language == "ur"
    assert result.visual_norm_key == "UR"


def test_abjad_visual_normalization_requires_explicit_language(tmp_path: Path) -> None:
    visual_norm_far = tmp_path / "visual_norm.far"
    _write_far(visual_norm_far, [("UR", _const_bytes(_mapping_fst("ك", "ک")))])

    result = VisualNormalizer().normalize("ك", visual_norm_far=visual_norm_far)

    assert result.supported is False
    assert result.reason is not None
    assert "explicit language" in result.reason


def test_default_visual_norm_url_uses_abjad_standalone_assets() -> None:
    assert default_visual_norm_far_url("UR").endswith("/visual_norm.Arab.ur.far")
    assert default_visual_norm_far_url("FA").endswith("/visual_norm.Arab.fa.far")
