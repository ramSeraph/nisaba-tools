from __future__ import annotations

import atexit
from functools import lru_cache
import hashlib
import os
from pathlib import Path
import shutil
import sys
from typing import Sequence
import struct
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen

from rustfst import ConstFst, Tr, VectorFst
from rustfst.algorithms.project import ProjectType

STTABLE_MAGIC = 0x7EB2F35C
STTABLE_VERSION = 1
ENTRY_COUNT_BYTES = 8
KEY_LENGTH_BYTES = 4
DiskCacheSetting = bool | str | os.PathLike[str]


def default_cache_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "nisaba-tools"
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / "nisaba-tools"
    root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return root / "nisaba-tools"


@lru_cache(maxsize=1)
def _temporary_process_cache_dir() -> Path:
    path = Path(tempfile.mkdtemp(prefix="nisaba-tools-"))
    atexit.register(shutil.rmtree, path, ignore_errors=True)
    return path


def resolve_disk_cache_dir(
    disk_cache: DiskCacheSetting = True,
) -> Path:
    if isinstance(disk_cache, bool):
        if disk_cache:
            return default_cache_dir()
        return _temporary_process_cache_dir()

    return Path(disk_cache).expanduser().resolve()


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def cache_filename(url: str) -> str:
    parsed = urlparse(url)
    basename = Path(parsed.path).name or "downloaded.far"
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{digest}-{basename}"


def download_to_cache(url: str, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    destination = cache_dir / cache_filename(url)
    if destination.exists():
        return destination
    with urlopen(url) as response:
        data = response.read()
    temp_path: Path | None = None
    try:
        if destination.exists():
            return destination
        with tempfile.NamedTemporaryFile(
            dir=cache_dir,
            prefix=f"{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(data)
            temp_path = Path(temp_file.name)
        temp_path.replace(destination)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return destination


def resolve_far_path(
    location: str | Path | None, default_url: str, cache_dir: Path
) -> Path:
    if location is None:
        return download_to_cache(default_url, cache_dir)
    if isinstance(location, Path):
        path = location.expanduser()
    else:
        if is_url(location):
            return download_to_cache(location, cache_dir)
        path = Path(location).expanduser()
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"FAR file not found: {resolved}")
    return resolved


def validate_far_variant(path: Path) -> None:
    if path.name.endswith("_utf8.far"):
        raise ValueError(
            f"{path.name} is a UTF-8 FAR. This API expects byte-mode FAR assets."
        )


@lru_cache(maxsize=8)
def read_far_bytes(path_str: str) -> bytes:
    return Path(path_str).read_bytes()


@lru_cache(maxsize=8)
def far_index(path_str: str) -> dict[str, tuple[int, int]]:
    data = read_far_bytes(path_str)
    if len(data) < 16:
        raise ValueError(f"{path_str} is too small to be a FAR archive")

    magic, version = struct.unpack_from("<II", data, 0)
    if magic != STTABLE_MAGIC:
        raise ValueError(f"{path_str} does not look like an STTable FAR archive")
    if version != STTABLE_VERSION:
        raise ValueError(f"Unsupported FAR version {version} in {path_str}")

    entry_count = struct.unpack_from("<q", data, len(data) - ENTRY_COUNT_BYTES)[0]
    trailer_start = len(data) - ENTRY_COUNT_BYTES * (entry_count + 2)
    if trailer_start < 8:
        raise ValueError(f"Corrupt FAR trailer in {path_str}")

    leading_count = struct.unpack_from("<q", data, trailer_start)[0]
    if leading_count != entry_count:
        raise ValueError(f"Corrupt FAR index count in {path_str}")

    positions = list(
        struct.unpack_from(f"<{entry_count}q", data, trailer_start + ENTRY_COUNT_BYTES)
    )
    index: dict[str, tuple[int, int]] = {}
    for index_offset, position in enumerate(positions):
        if position < 8 or position >= trailer_start:
            raise ValueError(f"Corrupt FAR entry offset {position} in {path_str}")
        next_position = (
            positions[index_offset + 1]
            if index_offset + 1 < len(positions)
            else trailer_start
        )
        key_length = struct.unpack_from("<i", data, position)[0]
        if key_length < 0:
            raise ValueError(f"Negative FAR key length in {path_str}")
        key_start = position + KEY_LENGTH_BYTES
        key_end = key_start + key_length
        if key_end > next_position:
            raise ValueError(f"Corrupt FAR key bounds in {path_str}")
        key = data[key_start:key_end].decode("utf-8")
        index[key] = (key_end, next_position)
    return index


def extract_entry_payload(path: Path, key: str) -> bytes:
    path_str = str(path)
    start, end = far_index(path_str)[key]
    return read_far_bytes(path_str)[start:end]


def select_far_key(path: Path, candidates: list[str]) -> str:
    available = far_index(str(path))
    for candidate in candidates:
        if candidate in available:
            return candidate
    raise KeyError(
        f"None of the requested FAR keys were present in {path}: {', '.join(candidates)}"
    )


def load_const_fst(payload: bytes) -> ConstFst:
    file_descriptor, temp_name = tempfile.mkstemp(suffix=".fst")
    try:
        with os.fdopen(file_descriptor, "wb") as temp_file:
            temp_file.write(payload)
        return ConstFst.read(temp_name)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def const_to_vector(source: ConstFst) -> VectorFst:
    destination = VectorFst()
    source_start = source.start()
    if source_start is None:
        return destination

    pending_states = [source_start]
    state_map: dict[int, int] = {}
    while pending_states:
        state = pending_states.pop(0)
        if state in state_map:
            continue
        state_map[state] = destination.add_state()
        for transition in source.trs(state):
            if transition.next_state not in state_map:
                pending_states.append(transition.next_state)

    destination.set_start(state_map[source_start])
    for source_state, destination_state in state_map.items():
        if source.is_final(source_state):
            destination.set_final(destination_state, source.final(source_state))
        for transition in source.trs(source_state):
            destination.add_tr(
                destination_state,
                Tr(
                    transition.ilabel,
                    transition.olabel,
                    transition.weight,
                    state_map[transition.next_state],
                ),
            )
    return destination


@lru_cache(maxsize=64)
def load_vector_fst(path_str: str, key: str) -> VectorFst:
    payload = extract_entry_payload(Path(path_str), key)
    return const_to_vector(load_const_fst(payload))


def load_far_fst(path: Path, key: str) -> VectorFst:
    return load_vector_fst(str(path), key).copy()


def resolve_far_transducer(
    location: str | Path | None,
    *,
    default_url: str,
    cache_dir: Path,
    key_candidates: Sequence[str],
) -> tuple[Path, str, VectorFst]:
    path = resolve_far_path(location, default_url, cache_dir)
    validate_far_variant(path)
    key = select_far_key(path, list(key_candidates))
    return path, key, load_far_fst(path, key)


def byte_string_fst(text: str) -> VectorFst:
    fst = VectorFst()
    current_state = fst.add_state()
    fst.set_start(current_state)
    for byte in text.encode("utf-8"):
        next_state = fst.add_state()
        fst.add_tr(current_state, Tr(byte, byte, 0.0, next_state))
        current_state = next_state
    fst.set_final(current_state, 0.0)
    return fst


def is_accepting(fst: VectorFst) -> bool:
    start_state = fst.start()
    if start_state is None:
        return False
    return any(fst.is_final(state) for state in fst.states())


def extract_projected_text(fst: VectorFst) -> str:
    connected = fst.copy().connect()
    # Some failed compositions produce an empty or non-accepting FST. Guard here
    # before walking transitions so invalid transliteration/normalization inputs
    # fail cleanly with ValueError instead of tripping lower-level rustfst access.
    if connected.num_states() == 0 or not is_accepting(connected):
        raise ValueError("No output path was produced.")
    path_fst = connected.shortest_path()
    start_state = path_fst.start()
    if start_state is None or path_fst.num_states() == 0:
        raise ValueError("No output path was produced.")

    output_bytes = bytearray()
    current_state = start_state
    visited_states: set[int] = set()
    while True:
        if current_state in visited_states:
            raise ValueError("Normalized output path is cyclic.")
        visited_states.add(current_state)

        transition_count = path_fst.num_trs(current_state)
        if transition_count == 0:
            if path_fst.is_final(current_state):
                break
            raise ValueError("Output path ended before a final state.")
        if transition_count != 1:
            raise ValueError("Output path is not linear.")
        transitions = list(path_fst.trs(current_state))

        transition = transitions[0]
        if transition.ilabel != 0:
            output_bytes.append(transition.ilabel)
        current_state = transition.next_state

    return output_bytes.decode("utf-8")


def transduce_input_fst(input_fst: VectorFst, transducer: VectorFst) -> str:
    return extract_projected_text(
        input_fst.compose(transducer).project(ProjectType.PROJECT_OUTPUT)
    )


def transduce_text(text: str, transducer: VectorFst) -> str:
    return transduce_input_fst(byte_string_fst(text), transducer)


def compose_text_fst(text: str, transducer: VectorFst) -> VectorFst:
    return byte_string_fst(text).compose(transducer)


def normalized_output_fst(text: str, visual_norm_fst: VectorFst) -> VectorFst:
    return compose_text_fst(text, visual_norm_fst).project(
        ProjectType.PROJECT_OUTPUT
    )
