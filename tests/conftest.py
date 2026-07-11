"""Shared fixtures. All test media is synthetic — generated here, never checked in."""

from __future__ import annotations

import shutil
import subprocess

import numpy as np
import pytest
from PIL import Image

HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
requires_ffmpeg = pytest.mark.skipif(
    not HAS_FFMPEG, reason="ffmpeg/ffprobe not on PATH"
)


def gradient_array(w: int = 160, h: int = 120) -> np.ndarray:
    """Horizontal red ramp, vertical green ramp, flat blue: every effect leaves a
    measurable, direction-specific trace on it."""
    x = np.linspace(0, 255, w, dtype=np.float32)[None, :]
    y = np.linspace(0, 255, h, dtype=np.float32)[:, None]
    r = np.broadcast_to(x, (h, w))
    g = np.broadcast_to(y, (h, w))
    b = np.full((h, w), 128.0, dtype=np.float32)
    return np.stack([r, g, b], axis=-1).astype(np.uint8)


@pytest.fixture
def gradient_image() -> Image.Image:
    return Image.fromarray(gradient_array(), "RGB")


@pytest.fixture
def jpg_path(tmp_path):
    path = tmp_path / "photo.jpg"
    Image.fromarray(gradient_array(), "RGB").save(path, quality=95)
    return path


@pytest.fixture
def png_path(tmp_path):
    path = tmp_path / "photo.png"
    Image.fromarray(gradient_array(), "RGB").save(path)
    return path


def _lavfi_video(path, *, audio: bool, acodec: str = "aac") -> None:
    cmd = ["ffmpeg", "-y", "-nostdin", "-loglevel", "error",
           "-f", "lavfi", "-i", "testsrc2=duration=2:size=320x240:rate=12"]
    if audio:
        cmd += ["-f", "lavfi", "-i", "sine=frequency=440:duration=2"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if audio:
        cmd += ["-c:a", acodec, "-shortest"]
    subprocess.run(cmd + [str(path)], check=True)


@pytest.fixture(scope="session")
def sample_video(tmp_path_factory):
    if not HAS_FFMPEG:
        pytest.skip("ffmpeg/ffprobe not on PATH")
    path = tmp_path_factory.mktemp("video") / "sample.mp4"
    _lavfi_video(path, audio=True)
    return path


@pytest.fixture(scope="session")
def sample_video_silent(tmp_path_factory):
    if not HAS_FFMPEG:
        pytest.skip("ffmpeg/ffprobe not on PATH")
    path = tmp_path_factory.mktemp("video") / "silent.mp4"
    _lavfi_video(path, audio=False)
    return path


@pytest.fixture(scope="session")
def sample_video_pcm_mov(tmp_path_factory):
    if not HAS_FFMPEG:
        pytest.skip("ffmpeg/ffprobe not on PATH")
    path = tmp_path_factory.mktemp("video") / "pcm.mov"
    _lavfi_video(path, audio=True, acodec="pcm_s16le")
    return path


@pytest.fixture(scope="session")
def sample_video_webm(tmp_path_factory):
    if not HAS_FFMPEG:
        pytest.skip("ffmpeg/ffprobe not on PATH")
    path = tmp_path_factory.mktemp("video") / "sample.webm"
    subprocess.run(
        ["ffmpeg", "-y", "-nostdin", "-loglevel", "error",
         "-f", "lavfi", "-i", "testsrc2=duration=2:size=320x240:rate=12",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
         "-c:v", "libvpx", "-c:a", "libvorbis", "-shortest", str(path)],
        check=True,
    )
    return path


def ffprobe_streams(path) -> list:
    """Return the stream dicts of a media file (test helper)."""
    import json

    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-of", "json", "-show_streams", "-show_format",
         str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(proc.stdout)["streams"]


def ffprobe_format(path) -> dict:
    import json

    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-of", "json", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(proc.stdout)["format"]
