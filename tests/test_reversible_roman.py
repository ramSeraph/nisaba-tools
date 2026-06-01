from __future__ import annotations

from pathlib import Path
import struct
import tempfile

from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import (
    ReversibleRomanTransliterator,
    from_reversible_roman,
    to_reversible_roman,
)
from nisaba_tools.far_assets import DEFAULT_REVERSIBLE_ROMAN_FAR_URL

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


def test_to_reversible_roman_preserves_spacing_and_punctuation(tmp_path: Path) -> None:
    roman_far = tmp_path / "reversible_roman.far"
    _write_far(
        roman_far,
        [
            ("FROM_ARAB", _const_bytes(_mapping_fst("اردو", "ârdv"))),
            ("TO_ARAB", _const_bytes(_mapping_fst("ârdv", "اردو"))),
        ],
    )

    result = ReversibleRomanTransliterator().transliterate_to_roman(
        "اردو، اردو!",
        roman_far=roman_far,
    )

    assert result.supported is True
    assert result.output_text == "ârdv، ârdv!"
    assert result.guessed is True
    assert result.resolved_language == "und-Arab"
    assert result.roman_key == "FROM_ARAB"


def test_from_reversible_roman_defaults_to_arab_script(tmp_path: Path) -> None:
    roman_far = tmp_path / "reversible_roman.far"
    _write_far(
        roman_far,
        [
            ("FROM_ARAB", _const_bytes(_mapping_fst("اردو", "ârdv"))),
            ("TO_ARAB", _const_bytes(_mapping_fst("ârdv", "اردو"))),
        ],
    )

    result = ReversibleRomanTransliterator().transliterate_from_roman(
        "ârdv، ârdv!",
        roman_far=roman_far,
    )

    assert result.supported is True
    assert result.output_text == "اردو، اردو!"
    assert result.resolved_language == "und-Arab"
    assert result.resolved_script == "ARAB"
    assert result.roman_key == "TO_ARAB"


def test_to_reversible_roman_rejects_non_abjad_language(tmp_path: Path) -> None:
    roman_far = tmp_path / "reversible_roman.far"
    _write_far(roman_far, [("FROM_ARAB", _const_bytes(_mapping_fst("اردو", "ârdv")))])

    result = ReversibleRomanTransliterator().transliterate_to_roman(
        "क",
        language="hi",
        roman_far=roman_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "abjad/alphabet" in result.reason


def test_from_reversible_roman_rejects_non_abjad_language(tmp_path: Path) -> None:
    roman_far = tmp_path / "reversible_roman.far"
    _write_far(roman_far, [("TO_ARAB", _const_bytes(_mapping_fst("ârdv", "اردو")))])

    result = ReversibleRomanTransliterator().transliterate_from_roman(
        "ârdv",
        language="hi",
        roman_far=roman_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "abjad/alphabet" in result.reason


def test_from_reversible_roman_reports_invalid_input(tmp_path: Path) -> None:
    roman_far = tmp_path / "reversible_roman.far"
    _write_far(roman_far, [("TO_ARAB", _const_bytes(_mapping_fst("ârdv", "اردو")))])

    result = ReversibleRomanTransliterator().transliterate_from_roman(
        "plain latin",
        roman_far=roman_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "valid reversible romanization" in result.reason


def test_string_helpers_round_trip(tmp_path: Path) -> None:
    roman_far = tmp_path / "reversible_roman.far"
    _write_far(
        roman_far,
        [
            ("FROM_ARAB", _const_bytes(_mapping_fst("آب", "ʼ͟āb"))),
            ("TO_ARAB", _const_bytes(_mapping_fst("ʼ͟āb", "آب"))),
        ],
    )

    romanized = to_reversible_roman("آب", language="ur", roman_far=roman_far)

    assert romanized == "ʼ͟āb"
    assert from_reversible_roman(romanized, roman_far=roman_far) == "آب"


def test_default_reversible_roman_url_uses_combined_abjad_asset() -> None:
    assert DEFAULT_REVERSIBLE_ROMAN_FAR_URL.endswith("/reversible_roman.far")
