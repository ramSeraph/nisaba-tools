from __future__ import annotations

from pathlib import Path
import struct
import tempfile

import pytest
from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import (
    NaturalRomanTransliterator,
    natural_romanize,
    natural_romanize_from_iso,
)
from nisaba_tools.far_assets import default_natural_roman_far_url

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


def test_natural_romanize_from_iso_defaults_to_nat(tmp_path: Path) -> None:
    roman_far = tmp_path / "hi_iso_nat.far"
    _write_far(
        roman_far, [("ISO_TO_NAT", _const_bytes(_mapping_fst("āṭīna", "ateen")))]
    )

    result = NaturalRomanTransliterator().transliterate_iso(
        "āṭīna",
        language="hi",
        roman_far=roman_far,
    )

    assert result.supported is True
    assert result.output_text == "ateen"
    assert result.roman_key == "ISO_TO_NAT"
    assert result.input_was_iso is True
    assert result.iso_text == "āṭīna"


@pytest.mark.parametrize(
    ("scheme", "far_key", "expected"),
    [
        ("psac", "ISO_TO_PSAC", "atin"),
        ("psaf", "ISO_TO_PSAF", "aatiin"),
    ],
)
def test_natural_romanize_from_iso_uses_selected_scheme(
    tmp_path: Path,
    scheme: str,
    far_key: str,
    expected: str,
) -> None:
    roman_far = tmp_path / f"hi_iso_{scheme}.far"
    _write_far(roman_far, [(far_key, _const_bytes(_mapping_fst("āṭīna", expected)))])

    result = NaturalRomanTransliterator().transliterate_iso(
        "āṭīna",
        language="hi",
        scheme=scheme,
        roman_far=roman_far,
    )

    assert result.supported is True
    assert result.output_text == expected
    assert result.roman_key == far_key


def test_natural_romanize_composes_native_to_iso_first(tmp_path: Path) -> None:
    iso_far = tmp_path / "iso.far"
    visual_norm_far = tmp_path / "visual_norm.far"
    roman_far = tmp_path / "hi_iso_nat.far"
    _write_far(
        iso_far,
        [
            ("FROM_DEVA", _const_bytes(_mapping_fst("क", "K"))),
            ("TO_DEVA", _const_bytes(_mapping_fst("K", "क"))),
        ],
    )
    _write_far(visual_norm_far, [("DEVA", _const_bytes(_mapping_fst("क़", "क")))])
    _write_far(roman_far, [("ISO_TO_NAT", _const_bytes(_mapping_fst("K", "ka")))])

    result = NaturalRomanTransliterator().transliterate(
        "क़",
        language="hi",
        scheme="natural",
        iso_far=iso_far,
        visual_norm_far=visual_norm_far,
        roman_far=roman_far,
    )

    assert result.supported is True
    assert result.output_text == "ka"
    assert result.iso_text == "K"
    assert result.visual_norm_applied is True
    assert result.visual_norm_key == "DEVA"
    assert result.iso_far == iso_far.resolve()


def test_natural_romanize_rejects_script_only_tags(tmp_path: Path) -> None:
    roman_far = tmp_path / "hi_iso_nat.far"
    _write_far(roman_far, [("ISO_TO_NAT", _const_bytes(_mapping_fst("K", "ka")))])

    result = NaturalRomanTransliterator().transliterate_iso(
        "K",
        language="und-Deva",
        roman_far=roman_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "explicit language code" in result.reason


def test_natural_romanize_rejects_unsupported_brahmic_language(tmp_path: Path) -> None:
    roman_far = tmp_path / "si_iso_nat.far"
    _write_far(roman_far, [("ISO_TO_NAT", _const_bytes(_mapping_fst("a", "a")))])

    result = NaturalRomanTransliterator().transliterate_iso(
        "a",
        language="si",
        roman_far=roman_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "not currently available" in result.reason


def test_natural_romanize_rejects_non_brahmic_language(tmp_path: Path) -> None:
    roman_far = tmp_path / "ur_iso_nat.far"
    _write_far(roman_far, [("ISO_TO_NAT", _const_bytes(_mapping_fst("a", "a")))])

    result = NaturalRomanTransliterator().transliterate_iso(
        "a",
        language="ur",
        roman_far=roman_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "Brahmic" in result.reason


def test_natural_romanize_reports_invalid_iso_input(tmp_path: Path) -> None:
    roman_far = tmp_path / "hi_iso_nat.far"
    _write_far(roman_far, [("ISO_TO_NAT", _const_bytes(_mapping_fst("K", "ka")))])

    result = NaturalRomanTransliterator().transliterate_iso(
        "Q",
        language="hi",
        roman_far=roman_far,
    )

    assert result.supported is False
    assert result.reason is not None
    assert "valid ISO transliteration" in result.reason


def test_natural_romanize_string_helpers(tmp_path: Path) -> None:
    iso_far = tmp_path / "iso.far"
    roman_far = tmp_path / "hi_iso_psaf.far"
    _write_far(
        iso_far,
        [
            ("FROM_DEVA", _const_bytes(_mapping_fst("क", "K"))),
            ("TO_DEVA", _const_bytes(_mapping_fst("K", "क"))),
        ],
    )
    _write_far(roman_far, [("ISO_TO_PSAF", _const_bytes(_mapping_fst("K", "kaa")))])

    assert (
        natural_romanize_from_iso(
            "K", language="hi", scheme="psaf", roman_far=roman_far
        )
        == "kaa"
    )
    assert (
        natural_romanize(
            "क",
            language="hi",
            scheme="psaf",
            iso_far=iso_far,
            roman_far=roman_far,
            apply_visual_norm=False,
        )
        == "kaa"
    )


def test_default_natural_roman_url_uses_language_and_scheme_asset() -> None:
    assert default_natural_roman_far_url("hi", "nat").endswith("/hi_iso_nat.far")
