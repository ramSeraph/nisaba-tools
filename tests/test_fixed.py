from __future__ import annotations

from pathlib import Path
import struct
import tempfile

import pytest
from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import (
    FixedTransliterator,
    fixed_transliterate,
)
from nisaba_tools.far_assets import DEFAULT_FIXED_FAR_URL

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


def test_fixed_transliterate_returns_native_text(tmp_path: Path) -> None:
    fixed_far = tmp_path / "fixed.far"
    _write_far(fixed_far, [("MLYM", _const_bytes(_mapping_fst("m", "മ")))])

    result = FixedTransliterator().transliterate(
        "m", language="ml", fixed_far=fixed_far
    )

    assert result.supported is True
    assert result.output_text == "മ"
    assert result.fixed_key == "MLYM"
    assert result.resolved_language == "ml"
    assert result.scheme == "Mozhi"


def test_fixed_transliterate_accepts_script_tag_alias(tmp_path: Path) -> None:
    fixed_far = tmp_path / "fixed.far"
    _write_far(fixed_far, [("MLYM", _const_bytes(_mapping_fst("m", "മ")))])

    assert fixed_transliterate("m", language="und-Mlym", fixed_far=fixed_far) == "മ"


def test_fixed_transliterate_accepts_explicit_mozhi_scheme(tmp_path: Path) -> None:
    fixed_far = tmp_path / "fixed.far"
    _write_far(fixed_far, [("MLYM", _const_bytes(_mapping_fst("m", "മ")))])

    result = FixedTransliterator().transliterate(
        "m",
        language="ml",
        scheme="mozhi",
        fixed_far=fixed_far,
    )

    assert result.output_text == "മ"
    assert result.scheme == "Mozhi"


def test_fixed_transliterate_rejects_mismatched_scheme(tmp_path: Path) -> None:
    fixed_far = tmp_path / "fixed.far"
    _write_far(fixed_far, [("MLYM", _const_bytes(_mapping_fst("m", "മ")))])

    with pytest.raises(ValueError, match="does not match target script"):
        FixedTransliterator().transliterate(
            "m",
            language="ml",
            scheme="itrans",
            fixed_far=fixed_far,
        )


def test_fixed_transliterate_requires_explicit_language() -> None:
    with pytest.raises(ValueError, match="requires an explicit language or script"):
        FixedTransliterator().fixed_transliterate("m", language=None)


def test_default_fixed_url_uses_combined_asset() -> None:
    assert DEFAULT_FIXED_FAR_URL.endswith("/fixed.far")
