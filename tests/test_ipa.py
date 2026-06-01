from __future__ import annotations

from pathlib import Path
import struct
import tempfile

from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import (
    IpaTranscriber,
    to_ipa,
    to_ipa_from_iso,
)
from nisaba_tools.far_assets import default_ipa_far_url

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


def test_to_ipa_from_iso_uses_iso_to_ipa_key(tmp_path: Path) -> None:
    ipa_far = tmp_path / "hi_iso_ipa.far"
    _write_far(ipa_far, [("ISO_TO_IPA", _const_bytes(_mapping_fst("āṭīna", "aːʈiːn̪")))])

    result = IpaTranscriber().transcribe_iso(
        "āṭīna",
        language="hi",
        ipa_far=ipa_far,
    )

    assert result.supported is True
    assert result.output_text == "aːʈiːn̪"
    assert result.ipa_key == "ISO_TO_IPA"
    assert result.input_was_iso is True
    assert result.iso_text == "āṭīna"


def test_to_ipa_composes_native_to_iso_first(tmp_path: Path) -> None:
    iso_far = tmp_path / "iso.far"
    visual_norm_far = tmp_path / "visual_norm.far"
    ipa_far = tmp_path / "hi_iso_ipa.far"
    _write_far(
        iso_far,
        [
            ("FROM_DEVA", _const_bytes(_mapping_fst("क", "K"))),
            ("TO_DEVA", _const_bytes(_mapping_fst("K", "क"))),
        ],
    )
    _write_far(visual_norm_far, [("DEVA", _const_bytes(_mapping_fst("क़", "क")))])
    _write_far(ipa_far, [("ISO_TO_IPA", _const_bytes(_mapping_fst("K", "kə")))])

    result = IpaTranscriber().transcribe(
        "क़",
        language="hi",
        iso_far=iso_far,
        visual_norm_far=visual_norm_far,
        ipa_far=ipa_far,
    )

    assert result.supported is True
    assert result.output_text == "kə"
    assert result.iso_text == "K"
    assert result.visual_norm_applied is True
    assert result.visual_norm_key == "DEVA"
    assert result.iso_far == iso_far.resolve()


def test_to_ipa_rejects_script_only_tags(tmp_path: Path) -> None:
    ipa_far = tmp_path / "hi_iso_ipa.far"
    _write_far(ipa_far, [("ISO_TO_IPA", _const_bytes(_mapping_fst("K", "kə")))])

    result = IpaTranscriber().transcribe_iso(
        "K",
        language="und-Deva",
        ipa_far=ipa_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "explicit language code" in result.reason


def test_to_ipa_rejects_unsupported_brahmic_language(tmp_path: Path) -> None:
    ipa_far = tmp_path / "si_iso_ipa.far"
    _write_far(ipa_far, [("ISO_TO_IPA", _const_bytes(_mapping_fst("a", "a")))])

    result = IpaTranscriber().transcribe_iso(
        "a",
        language="si",
        ipa_far=ipa_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "not currently available" in result.reason


def test_to_ipa_rejects_non_brahmic_language(tmp_path: Path) -> None:
    ipa_far = tmp_path / "ur_iso_ipa.far"
    _write_far(ipa_far, [("ISO_TO_IPA", _const_bytes(_mapping_fst("a", "a")))])

    result = IpaTranscriber().transcribe_iso(
        "a",
        language="ur",
        ipa_far=ipa_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "Brahmic" in result.reason


def test_to_ipa_reports_invalid_iso_input(tmp_path: Path) -> None:
    ipa_far = tmp_path / "hi_iso_ipa.far"
    _write_far(ipa_far, [("ISO_TO_IPA", _const_bytes(_mapping_fst("K", "kə")))])

    result = IpaTranscriber().transcribe_iso(
        "Q",
        language="hi",
        ipa_far=ipa_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "valid ISO transliteration" in result.reason


def test_to_ipa_string_helpers(tmp_path: Path) -> None:
    iso_far = tmp_path / "iso.far"
    ipa_far = tmp_path / "hi_iso_ipa.far"
    _write_far(
        iso_far,
        [
            ("FROM_DEVA", _const_bytes(_mapping_fst("क", "K"))),
            ("TO_DEVA", _const_bytes(_mapping_fst("K", "क"))),
        ],
    )
    _write_far(ipa_far, [("ISO_TO_IPA", _const_bytes(_mapping_fst("K", "kə")))])

    assert to_ipa_from_iso("K", language="hi", ipa_far=ipa_far) == "kə"
    assert (
        to_ipa(
            "क",
            language="hi",
            iso_far=iso_far,
            ipa_far=ipa_far,
            apply_visual_norm=False,
        )
        == "kə"
    )


def test_default_ipa_url_uses_language_asset() -> None:
    assert default_ipa_far_url("hi").endswith("/hi_iso_ipa.far")
