from __future__ import annotations

from pathlib import Path

import pytest

import nisaba_tools._far_fst as far_fst


class _FakeResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return self._data


def test_resolve_disk_cache_dir_uses_explicit_path(tmp_path: Path) -> None:
    cache_dir = far_fst.resolve_disk_cache_dir(tmp_path / "shared-cache")

    assert cache_dir == (tmp_path / "shared-cache").resolve()


def test_resolve_disk_cache_dir_reuses_process_temp_dir() -> None:
    cache_dir = far_fst.resolve_disk_cache_dir(False)

    assert cache_dir == far_fst.resolve_disk_cache_dir(False)
    assert cache_dir.name.startswith("nisaba-tools-")


def test_download_to_cache_reuses_existing_file_and_cleans_temp_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_urlopen(url: str) -> _FakeResponse:
        nonlocal calls
        calls += 1
        assert url == "https://example.com/test.far"
        return _FakeResponse(b"far-bytes")

    monkeypatch.setattr(far_fst, "urlopen", fake_urlopen)

    downloaded = far_fst.download_to_cache("https://example.com/test.far", tmp_path)
    downloaded_again = far_fst.download_to_cache(
        "https://example.com/test.far",
        tmp_path,
    )

    assert downloaded == downloaded_again
    assert downloaded.read_bytes() == b"far-bytes"
    assert calls == 1
    assert list(tmp_path.glob("*.tmp")) == []
