from __future__ import annotations

from pathlib import Path
import struct
import tempfile

import pytest
from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import (
    IsoTransliterator,
    from_iso,
)
from nisaba_tools.far_assets import DEFAULT_ISO_FAR_URL

STTABLE_MAGIC = 0x7EB2F35C
STTABLE_VERSION = 1


def _mapping_fst(source_text: str, target_text: str) -> VectorFst:
    source_bytes = source_text.encode("utf-8")
    target_bytes = target_text.encode("utf-8")

    fst = VectorFst()
    current_state = fst.add_state()
    fst.set_start(current_state)
    for index in range(max(len(source_bytes), len(target_bytes))):
        next_state = fst.add_state()
        input_label = source_bytes[index] if index < len(source_bytes) else 0
        output_label = target_bytes[index] if index < len(target_bytes) else 0
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


def test_to_iso_applies_visual_norm_by_default(tmp_path: Path) -> None:
    iso_far = tmp_path / "iso.far"
    visual_norm_far = tmp_path / "visual_norm.far"
    _write_far(
        iso_far,
        [
            ("FROM_DEVA", _const_bytes(_mapping_fst("क", "K"))),
            ("TO_DEVA", _const_bytes(_mapping_fst("K", "क"))),
        ],
    )
    _write_far(visual_norm_far, [("DEVA", _const_bytes(_mapping_fst("क़", "क")))])

    result = IsoTransliterator().transliterate_to_iso(
        "क़",
        language="hi",
        iso_far=iso_far,
        visual_norm_far=visual_norm_far,
    )

    assert result.supported is True
    assert result.output_text == "K"
    assert result.iso_key == "FROM_DEVA"
    assert result.visual_norm_applied is True
    assert result.visual_norm_key == "DEVA"
    assert result.visual_norm_far == visual_norm_far.resolve()


def test_to_iso_can_skip_visual_norm(tmp_path: Path) -> None:
    iso_far = tmp_path / "iso.far"
    _write_far(iso_far, [("FROM_DEVA", _const_bytes(_mapping_fst("क़", "Q")))])

    result = IsoTransliterator().transliterate_to_iso(
        "क़",
        language="hi",
        iso_far=iso_far,
        apply_visual_norm=False,
    )

    assert result.supported is True
    assert result.output_text == "Q"
    assert result.visual_norm_applied is False


def test_to_iso_guesses_script_when_language_is_omitted(tmp_path: Path) -> None:
    iso_far = tmp_path / "iso.far"
    _write_far(iso_far, [("FROM_DEVA", _const_bytes(_mapping_fst("क", "K")))])

    result = IsoTransliterator().transliterate_to_iso(
        "क",
        iso_far=iso_far,
        apply_visual_norm=False,
    )

    assert result.supported is True
    assert result.guessed is True
    assert result.resolved_language == "und-Deva"


def test_to_iso_requires_script_specific_key(tmp_path: Path) -> None:
    iso_far = tmp_path / "iso.far"
    _write_far(iso_far, [("FROM_BRAHMIC", _const_bytes(_mapping_fst("क", "K")))])

    with pytest.raises(KeyError, match="FROM_DEVA"):
        IsoTransliterator().transliterate_to_iso(
            "क",
            language="hi",
            iso_far=iso_far,
            apply_visual_norm=False,
        )


def test_from_iso_returns_native_text(tmp_path: Path) -> None:
    iso_far = tmp_path / "iso.far"
    _write_far(iso_far, [("TO_DEVA", _const_bytes(_mapping_fst("K", "क")))])

    assert from_iso("K", language="und-Deva", iso_far=iso_far) == "क"


def test_from_iso_requires_explicit_language() -> None:
    with pytest.raises(ValueError, match="requires an explicit language or script"):
        IsoTransliterator().from_iso("K", language=None)


def test_default_iso_url_uses_combined_asset() -> None:
    assert DEFAULT_ISO_FAR_URL.endswith("/iso.far")
