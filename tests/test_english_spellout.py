from __future__ import annotations

from pathlib import Path
import struct
import tempfile

from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import (
    EnglishSpelloutTransliterator,
    english_spellout,
)
from nisaba_tools.far_assets import (
    DEFAULT_EN_SPELLOUT_FAR_URL,
    default_english_spellout_far_key,
)

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


def test_english_spellout_uses_language_specific_key(tmp_path: Path) -> None:
    spellout_far = tmp_path / "en_spellout.far"
    _write_far(
        spellout_far,
        [
            ("HI_DEVA", _const_bytes(_mapping_fst("ATM", "एटीएम"))),
            ("UR_ARAB", _const_bytes(_mapping_fst("ATM", "اے ٹی ایم"))),
        ],
    )

    result = EnglishSpelloutTransliterator().transliterate(
        "ATM",
        language="hi",
        spellout_far=spellout_far,
    )

    assert result.supported is True
    assert result.output_text == "एटीएम"
    assert result.spellout_key == "HI_DEVA"


def test_english_spellout_supports_abjad_languages(tmp_path: Path) -> None:
    spellout_far = tmp_path / "en_spellout.far"
    _write_far(
        spellout_far,
        [("UR_ARAB", _const_bytes(_mapping_fst("ATM", "اے ٹی ایم")))],
    )

    result = EnglishSpelloutTransliterator().transliterate(
        "ATM",
        language="ur",
        spellout_far=spellout_far,
    )

    assert result.supported is True
    assert result.output_text == "اے ٹی ایم"
    assert result.spellout_key == "UR_ARAB"


def test_english_spellout_rejects_script_only_tags(tmp_path: Path) -> None:
    spellout_far = tmp_path / "en_spellout.far"
    _write_far(
        spellout_far,
        [("HI_DEVA", _const_bytes(_mapping_fst("ATM", "एटीएम")))],
    )

    result = EnglishSpelloutTransliterator().transliterate(
        "ATM",
        language="und-Deva",
        spellout_far=spellout_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "explicit language code" in result.reason


def test_english_spellout_rejects_unsupported_language(tmp_path: Path) -> None:
    spellout_far = tmp_path / "en_spellout.far"
    _write_far(
        spellout_far,
        [("HI_DEVA", _const_bytes(_mapping_fst("ATM", "एटीएम")))],
    )

    result = EnglishSpelloutTransliterator().transliterate(
        "ATM",
        language="fa",
        spellout_far=spellout_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "not currently available" in result.reason


def test_english_spellout_reports_invalid_input(tmp_path: Path) -> None:
    spellout_far = tmp_path / "en_spellout.far"
    _write_far(
        spellout_far,
        [("HI_DEVA", _const_bytes(_mapping_fst("ATM", "एटीएम")))],
    )

    result = EnglishSpelloutTransliterator().transliterate(
        "CAB",
        language="hi",
        spellout_far=spellout_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "valid Latin text" in result.reason


def test_english_spellout_string_helper(tmp_path: Path) -> None:
    spellout_far = tmp_path / "en_spellout.far"
    _write_far(
        spellout_far,
        [("TA_TAML", _const_bytes(_mapping_fst("ATM", "ஏடிஎம்")))],
    )

    assert english_spellout("ATM", language="ta", spellout_far=spellout_far) == "ஏடிஎம்"


def test_default_english_spellout_assets() -> None:
    assert DEFAULT_EN_SPELLOUT_FAR_URL.endswith("/en_spellout.far")
    assert default_english_spellout_far_key("hi") == "HI_DEVA"
