from __future__ import annotations

from pathlib import Path
import struct
import tempfile

from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import (
    NaturalDeromanizer,
    natural_deromanize,
    natural_deromanize_to_iso,
)
from nisaba_tools.far_assets import default_natural_deroman_far_url

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


def test_natural_deromanize_uses_native_script_asset(tmp_path: Path) -> None:
    derom_far = tmp_path / "hi_deva.far"
    _write_far(derom_far, [("DEVA", _const_bytes(_mapping_fst("namaste", "नमस्ते")))])

    result = NaturalDeromanizer().transliterate(
        "namaste",
        language="hi",
        derom_far=derom_far,
    )

    assert result.supported is True
    assert result.output_text == "नमस्ते"
    assert result.derom_key == "DEVA"


def test_natural_deromanize_to_iso_uses_iso_asset(tmp_path: Path) -> None:
    derom_far = tmp_path / "ta_iso.far"
    _write_far(derom_far, [("ISO", _const_bytes(_mapping_fst("vanakkam", "vaṉakkam")))])

    result = NaturalDeromanizer().transliterate_to_iso(
        "vanakkam",
        language="ta",
        derom_far=derom_far,
    )

    assert result.supported is True
    assert result.output_text == "vaṉakkam"
    assert result.derom_key == "ISO"


def test_natural_deromanize_rejects_script_only_tags(tmp_path: Path) -> None:
    derom_far = tmp_path / "hi_deva.far"
    _write_far(derom_far, [("DEVA", _const_bytes(_mapping_fst("namaste", "नमस्ते")))])

    result = NaturalDeromanizer().transliterate(
        "namaste",
        language="und-Deva",
        derom_far=derom_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "explicit language code" in result.reason


def test_natural_deromanize_rejects_unsupported_language(tmp_path: Path) -> None:
    derom_far = tmp_path / "ml_deva.far"
    _write_far(derom_far, [("MLYM", _const_bytes(_mapping_fst("namaste", "നമസ്തേ")))])

    result = NaturalDeromanizer().transliterate(
        "namaste",
        language="ml",
        derom_far=derom_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "not currently available" in result.reason


def test_natural_deromanize_rejects_non_brahmic_language(tmp_path: Path) -> None:
    derom_far = tmp_path / "ur_iso.far"
    _write_far(derom_far, [("ISO", _const_bytes(_mapping_fst("urdu", "urdu")))])

    result = NaturalDeromanizer().transliterate_to_iso(
        "urdu",
        language="ur",
        derom_far=derom_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "Brahmic" in result.reason


def test_natural_deromanize_reports_invalid_input(tmp_path: Path) -> None:
    derom_far = tmp_path / "hi_deva.far"
    _write_far(derom_far, [("DEVA", _const_bytes(_mapping_fst("namaste", "नमस्ते")))])

    result = NaturalDeromanizer().transliterate(
        "zzz",
        language="hi",
        derom_far=derom_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "valid Latin text" in result.reason


def test_natural_deromanize_string_helpers(tmp_path: Path) -> None:
    script_far = tmp_path / "hi_deva.far"
    iso_far = tmp_path / "hi_iso.far"
    _write_far(script_far, [("DEVA", _const_bytes(_mapping_fst("namaste", "नमस्ते")))])
    _write_far(iso_far, [("ISO", _const_bytes(_mapping_fst("namaste", "namaste")))])

    assert (
        natural_deromanize(
            "namaste",
            language="hi",
            derom_far=script_far,
            disk_cache=False,
        )
        == "नमस्ते"
    )
    assert (
        natural_deromanize_to_iso(
            "namaste",
            language="hi",
            derom_far=iso_far,
            disk_cache=tmp_path / "cache",
        )
        == "namaste"
    )


def test_default_deroman_url_uses_target_asset() -> None:
    assert default_natural_deroman_far_url("hi", "script").endswith("/hi_deva.far")
    assert default_natural_deroman_far_url("ta", "iso").endswith("/ta_iso.far")
