"""Hand landmarker is downloaded on first use when the .task file is missing."""

from pathlib import Path

import pytest

from handgame.recognition.hand_landmarker import HAND_LANDMARKER_URL, ensure_hand_landmarker


def test_ensure_hand_landmarker_keeps_an_existing_file(tmp_path):
    path = tmp_path / "hand_landmarker.task"
    path.write_bytes(b"already-there")
    calls: list[tuple[str, str]] = []

    def fetch(url: str, dest: str) -> None:
        calls.append((url, dest))

    assert ensure_hand_landmarker(path, fetch=fetch) == path
    assert path.read_bytes() == b"already-there"
    assert calls == []


def test_ensure_hand_landmarker_downloads_when_missing(tmp_path):
    path = tmp_path / "models" / "hand_landmarker.task"

    def fetch(url: str, dest: str) -> None:
        assert url == HAND_LANDMARKER_URL
        Path(dest).write_bytes(b"task-bytes")

    assert ensure_hand_landmarker(path, fetch=fetch) == path
    assert path.read_bytes() == b"task-bytes"
    assert not path.with_suffix(path.suffix + ".part").exists()


def test_ensure_hand_landmarker_raises_when_download_fails(tmp_path):
    path = tmp_path / "hand_landmarker.task"

    def fetch(url: str, dest: str) -> None:
        Path(dest).write_bytes(b"partial")
        raise OSError("offline")

    with pytest.raises(FileNotFoundError, match="download from"):
        ensure_hand_landmarker(path, fetch=fetch)
    assert not path.exists()
    assert not path.with_suffix(path.suffix + ".part").exists()
