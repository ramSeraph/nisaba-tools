from __future__ import annotations

from pathlib import Path
import struct
import tempfile

import pytest
from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import (
    ReadingNormalizer,
    reading_normalize,
)
from nisaba_tools.far_assets import (
    DEFAULT_READING_NORM_FAR_URL,
    default_reading_norm_far_url,
)

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


def test_hindi_uses_language_specific_reading_norm_key(tmp_path: Path) -> None:
    reading_norm_far = tmp_path / "reading_norm.far"
    _write_far(
        reading_norm_far,
        [
            ("HI", _const_bytes(_mapping_fst("क", "ख"))),
            ("DEVA", _const_bytes(_mapping_fst("क", "ग"))),
        ],
    )
    visual_norm_far = tmp_path / "visual_norm.far"
    _write_far(visual_norm_far, [("DEVA", _const_bytes(_mapping_fst("क़", "क")))])

    result = ReadingNormalizer().normalize(
        "क़",
        language="hi",
        reading_norm_far=reading_norm_far,
        visual_norm_far=visual_norm_far,
    )

    assert result.supported is True
    assert result.normalized_text == "ख"
    assert result.resolved_language == "hi"
    assert result.reading_norm_key == "HI"
    assert result.visual_norm_applied is True
    assert result.visual_norm_key == "DEVA"
    assert result.visual_norm_far == visual_norm_far.resolve()


def test_bengali_script_defaults_to_script_level_reading_norm(tmp_path: Path) -> None:
    reading_norm_far = tmp_path / "reading_norm.far"
    _write_far(reading_norm_far, [("BENG", _const_bytes(_mapping_fst("ড়", "ড")))])

    assert (
        reading_normalize(
            "ড়",
            language="bn",
            reading_norm_far=reading_norm_far,
            apply_visual_norm=False,
        )
        == "ড"
    )


def test_unsupported_default_reading_norm_language_reports_unsupported() -> None:
    result = ReadingNormalizer().normalize("క", language="te")

    assert result.supported is False
    assert result.reason is not None


def test_reading_normalizer_raises_for_unsupported_default_language() -> None:
    with pytest.raises(ValueError, match="No default reading_norm FAR asset"):
        ReadingNormalizer().reading_normalize("క", language="te")


def test_reading_normalize_can_skip_visual_norm(tmp_path: Path) -> None:
    reading_norm_far = tmp_path / "reading_norm.far"
    _write_far(reading_norm_far, [("HI", _const_bytes(_mapping_fst("क़", "ग")))])

    result = ReadingNormalizer().normalize(
        "क़",
        language="hi",
        reading_norm_far=reading_norm_far,
        apply_visual_norm=False,
    )

    assert result.supported is True
    assert result.normalized_text == "ग"
    assert result.visual_norm_applied is False
    assert result.visual_norm_key is None
    assert result.visual_norm_far is None


def test_abjad_reading_normalize_uses_visual_prepass(tmp_path: Path) -> None:
    reading_norm_far = tmp_path / "reading_norm.far"
    visual_norm_far = tmp_path / "visual_norm.far"
    _write_far(reading_norm_far, [("UR", _const_bytes(_mapping_fst("ک", "گ")))])
    _write_far(visual_norm_far, [("UR", _const_bytes(_mapping_fst("ك", "ک")))])

    result = ReadingNormalizer().normalize(
        "ك",
        language="ur",
        reading_norm_far=reading_norm_far,
        visual_norm_far=visual_norm_far,
    )

    assert result.supported is True
    assert result.normalized_text == "گ"
    assert result.reading_norm_key == "UR"
    assert result.visual_norm_key == "UR"


def test_abjad_reading_normalization_requires_explicit_language(tmp_path: Path) -> None:
    reading_norm_far = tmp_path / "reading_norm.far"
    _write_far(reading_norm_far, [("UR", _const_bytes(_mapping_fst("ک", "گ")))])

    result = ReadingNormalizer().normalize("ك", reading_norm_far=reading_norm_far)

    assert result.supported is False
    assert result.reason is not None
    assert "explicit language" in result.reason


def test_default_reading_norm_url_uses_standalone_assets() -> None:
    assert default_reading_norm_far_url("BENG").endswith("/reading_norm.Beng.far")
    assert default_reading_norm_far_url("HI").endswith("/reading_norm.Deva.hi.far")
    assert default_reading_norm_far_url("LEPC").endswith("/reading_norm.Lepc.far")
    assert default_reading_norm_far_url("MLYM").endswith("/reading_norm.Mlym.far")
    assert default_reading_norm_far_url("UR").endswith("/reading_norm.Arab.ur.far")
    assert default_reading_norm_far_url("FA").endswith("/reading_norm.Arab.fa.far")
    assert DEFAULT_READING_NORM_FAR_URL.endswith("/reading_norm.far")
