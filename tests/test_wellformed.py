from __future__ import annotations

from pathlib import Path
import struct
import tempfile
import pytest
from rustfst import ConstFst, Tr, VectorFst

from nisaba_tools import WellFormednessChecker
from nisaba_tools.far_assets import (
    DEFAULT_WELLFORMED_FAR_URL,
    default_visual_norm_far_url,
)
import nisaba_tools.wellformed as wellformed_module

STTABLE_MAGIC = 0x7EB2F35C
STTABLE_VERSION = 1


def _linear_acceptor(text: str) -> VectorFst:
    fst = VectorFst()
    current_state = fst.add_state()
    fst.set_start(current_state)
    for byte in text.encode("utf-8"):
        next_state = fst.add_state()
        fst.add_tr(current_state, Tr(byte, byte, 0.0, next_state))
        current_state = next_state
    fst.set_final(current_state, 0.0)
    return fst


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


def test_explicit_bengali_uses_language_specific_visual_norm_key(
    tmp_path: Path,
) -> None:
    visual_norm_far = tmp_path / "visual_norm.far"
    wellformed_far = tmp_path / "wellformed.far"

    _write_far(
        visual_norm_far,
        [
            ("BN", _const_bytes(_mapping_fst("x", "y"))),
            ("BENG", _const_bytes(_mapping_fst("x", "x"))),
        ],
    )
    _write_far(
        wellformed_far,
        [
            ("BENG", _const_bytes(_linear_acceptor("y"))),
        ],
    )

    checker = WellFormednessChecker(
        visual_norm_far=visual_norm_far,
        wellformed_far=wellformed_far,
    )

    bengali_result = checker.check("x", language="bn")
    assert bengali_result.is_wellformed is True
    assert bengali_result.resolved_language == "bn"
    assert bengali_result.visual_norm_key == "BN"
    assert bengali_result.wellformed_key == "BENG"

    script_only_result = checker.check("x", language="beng")
    assert script_only_result.is_wellformed is False
    assert script_only_result.resolved_language == "und-Beng"
    assert script_only_result.visual_norm_key == "BENG"
    assert script_only_result.wellformed_key == "BENG"


def test_guesses_devanagari_when_language_is_omitted(tmp_path: Path) -> None:
    visual_norm_far = tmp_path / "visual_norm.far"
    wellformed_far = tmp_path / "wellformed.far"

    _write_far(
        visual_norm_far,
        [("DEVA", _const_bytes(_mapping_fst("क", "क")))],
    )
    _write_far(
        wellformed_far,
        [("DEVA", _const_bytes(_linear_acceptor("क")))],
    )

    checker = WellFormednessChecker(
        visual_norm_far=visual_norm_far,
        wellformed_far=wellformed_far,
    )

    result = checker.check("क")
    assert result.is_wellformed is True
    assert result.supported is True
    assert result.guessed is True
    assert result.resolved_language == "und-Deva"
    assert result.resolved_script == "DEVA"


def test_accepts_bcp47_script_tag_alias(tmp_path: Path) -> None:
    visual_norm_far = tmp_path / "visual_norm.far"
    wellformed_far = tmp_path / "wellformed.far"

    _write_far(
        visual_norm_far,
        [("DEVA", _const_bytes(_mapping_fst("क", "क")))],
    )
    _write_far(
        wellformed_far,
        [("DEVA", _const_bytes(_linear_acceptor("क")))],
    )

    checker = WellFormednessChecker(
        visual_norm_far=visual_norm_far,
        wellformed_far=wellformed_far,
    )

    result = checker.check("क", language="und-Deva")
    assert result.is_wellformed is True
    assert result.resolved_language == "und-Deva"


def test_returns_unsupported_for_non_brahmic_guess(tmp_path: Path) -> None:
    visual_norm_far = tmp_path / "visual_norm.far"
    wellformed_far = tmp_path / "wellformed.far"

    _write_far(
        visual_norm_far,
        [("DEVA", _const_bytes(_mapping_fst("क", "क")))],
    )
    _write_far(
        wellformed_far,
        [("DEVA", _const_bytes(_linear_acceptor("क")))],
    )

    checker = WellFormednessChecker(
        visual_norm_far=visual_norm_far,
        wellformed_far=wellformed_far,
    )

    result = checker.check("latin")
    assert result.is_wellformed is False
    assert result.supported is False
    assert result.reason is not None


def test_rejects_utf8_far_names(tmp_path: Path) -> None:
    visual_norm_far = tmp_path / "visual_norm_utf8.far"
    wellformed_far = tmp_path / "wellformed_utf8.far"

    _write_far(visual_norm_far, [])
    _write_far(wellformed_far, [])

    checker = WellFormednessChecker(
        visual_norm_far=visual_norm_far,
        wellformed_far=wellformed_far,
    )

    with pytest.raises(ValueError):
        checker.check("क", language="deva")


def test_default_visual_norm_url_uses_standalone_assets() -> None:
    assert default_visual_norm_far_url("DEVA").endswith("/visual_norm.Deva.far")
    assert default_visual_norm_far_url("BENG").endswith("/visual_norm.Beng.far")
    assert default_visual_norm_far_url("BN").endswith("/visual_norm.Beng.bn.far")
    assert default_visual_norm_far_url("AS").endswith("/visual_norm.Beng.as.far")
    assert DEFAULT_WELLFORMED_FAR_URL.endswith("/wellformed.far")


def test_default_wellformed_resolver_fallback_is_used_when_checker_omits_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str | Path | None] = {}

    class _FakeAccepted:
        def compose(self, other):
            return self

    def fake_resolve_wellformed_path(wellformed_far, *, cache_dir):
        captured["wellformed_far"] = wellformed_far

    monkeypatch.setattr(
        wellformed_module,
        "resolve_visual_norm_path",
        lambda visual_norm_far, default_visual_norm_far, key, *, cache_dir: Path(
            "/tmp/visual_norm.far"
        ),
    )
    monkeypatch.setattr(
        wellformed_module, "resolve_wellformed_path", fake_resolve_wellformed_path
    )
    monkeypatch.setattr(wellformed_module, "load_far_fst", lambda path, key: key)
    monkeypatch.setattr(
        wellformed_module,
        "normalized_output_fst",
        lambda text, visual_norm_fst: _FakeAccepted(),
    )
    monkeypatch.setattr(wellformed_module, "is_accepting", lambda accepted: True)

    result = WellFormednessChecker().check("क", language="hi")

    assert result.is_wellformed is True
    assert captured["wellformed_far"] is None
