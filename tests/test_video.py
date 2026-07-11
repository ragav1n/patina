from __future__ import annotations

import os
import shutil
import subprocess
import sys

import numpy as np
import pytest
from fractions import Fraction
from pathlib import Path
from PIL import Image

from patina import video
from patina.errors import PatinaError
from patina.render import RenderOptions

from conftest import requires_ffmpeg, ffprobe_streams, ffprobe_format

OPTS = RenderOptions(preset="flash_night")


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "patina", *args], capture_output=True, text=True
    )


# ---- units that need no ffmpeg ----------------------------------------------

def test_parse_rate():
    assert video._parse_rate("30000/1001") == Fraction(30000, 1001)
    assert video._parse_rate("25") == Fraction(25)
    assert video._parse_rate("0/0") is None
    assert video._parse_rate("") is None
    assert video._parse_rate(None) is None
    assert video._parse_rate("garbage") is None


def test_format_hms():
    assert video._format_hms(0) == "00:00:00"
    assert video._format_hms(6.4) == "00:00:06"
    assert video._format_hms(3725) == "01:02:05"


def test_missing_ffmpeg_message(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(PatinaError) as exc:
        video._require_ffmpeg()
    msg = str(exc.value)
    assert "brew install ffmpeg" in msg
    assert "apt install ffmpeg" in msg
    assert "choco install ffmpeg" in msg


def test_webm_default_output_becomes_mp4():
    out = video.default_output_path(Path("clip.webm"), "flash_night")
    assert out.name == "clip_flash_night.mp4"


def test_explicit_webm_output_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/" + name)
    src = tmp_path / "clip.mp4"
    src.write_bytes(b"x")
    with pytest.raises(PatinaError, match="webm"):
        video.process_video(src, tmp_path / "out.webm", OPTS)


# ---- end-to-end with real ffmpeg --------------------------------------------

@requires_ffmpeg
def test_video_end_to_end_preserves_audio(sample_video, tmp_path):
    out = tmp_path / "out.mp4"
    proc = run_cli(str(sample_video), "-o", str(out), "--rec",
                   "--preset", "camcorder_warm")
    assert proc.returncode == 0, proc.stderr
    assert "processing frame 24/24" in proc.stdout
    streams = ffprobe_streams(out)
    kinds = {s["codec_type"] for s in streams}
    assert kinds == {"video", "audio"}  # original audio came along
    vstream = next(s for s in streams if s["codec_type"] == "video")
    assert vstream["codec_name"] == "h264"
    assert vstream["pix_fmt"] == "yuv420p"
    assert float(ffprobe_format(out)["duration"]) == pytest.approx(2.0, abs=0.3)
    assert int(vstream.get("nb_frames", 24)) == pytest.approx(24, abs=2)


@requires_ffmpeg
def test_video_frames_are_filtered(sample_video, tmp_path):
    out = tmp_path / "out.mp4"
    assert run_cli(str(sample_video), "-o", str(out)).returncode == 0

    def first_frame(path):
        png = tmp_path / (path.stem + "_frame.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path),
                        "-frames:v", "1", str(png)], check=True)
        return np.asarray(Image.open(png).convert("RGB"), dtype=np.float32)

    src, filt = first_frame(sample_video), first_frame(out)
    assert np.abs(src - filt).mean() > 10  # visibly changed
    # flash_night: corners crushed toward black.
    assert filt[:20, :20].mean() < src[:20, :20].mean() * 0.6


@requires_ffmpeg
def test_default_video_naming(sample_video):
    out = sample_video.with_name("sample_flash_night.mp4")
    proc = run_cli(str(sample_video))
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    out.unlink()


@requires_ffmpeg
def test_max_width_downscales(sample_video, tmp_path):
    out = tmp_path / "small.mp4"
    proc = run_cli(str(sample_video), "-o", str(out), "--max-width", "160")
    assert proc.returncode == 0, proc.stderr
    vstream = next(s for s in ffprobe_streams(out) if s["codec_type"] == "video")
    assert vstream["width"] == 160
    assert vstream["height"] % 2 == 0


@requires_ffmpeg
def test_max_width_never_upscales(sample_video, tmp_path):
    out = tmp_path / "same.mp4"
    proc = run_cli(str(sample_video), "-o", str(out), "--max-width", "9999")
    assert proc.returncode == 0, proc.stderr
    vstream = next(s for s in ffprobe_streams(out) if s["codec_type"] == "video")
    assert vstream["width"] == 320  # unchanged


@requires_ffmpeg
def test_silent_video_ok(sample_video_silent, tmp_path):
    out = tmp_path / "out.mp4"
    proc = run_cli(str(sample_video_silent), "-o", str(out))
    assert proc.returncode == 0, proc.stderr
    assert all(s["codec_type"] != "audio" for s in ffprobe_streams(out))


@requires_ffmpeg
def test_pcm_audio_falls_back_to_aac(sample_video_pcm_mov, tmp_path):
    out = tmp_path / "out.mp4"  # PCM is not allowed in .mp4 -> AAC retry path
    proc = run_cli(str(sample_video_pcm_mov), "-o", str(out))
    assert proc.returncode == 0, proc.stderr
    audio = [s for s in ffprobe_streams(out) if s["codec_type"] == "audio"]
    assert len(audio) == 1  # audio survived, whatever the codec


@requires_ffmpeg
def test_mov_output_container(sample_video_pcm_mov, tmp_path):
    proc = run_cli(str(sample_video_pcm_mov))
    assert proc.returncode == 0, proc.stderr
    out = sample_video_pcm_mov.with_name("pcm_flash_night.mov")
    assert out.exists()
    audio = [s for s in ffprobe_streams(out) if s["codec_type"] == "audio"]
    assert len(audio) == 1
    out.unlink()


@requires_ffmpeg
def test_webm_input_writes_mp4_with_note(sample_video_webm):
    proc = run_cli(str(sample_video_webm))
    assert proc.returncode == 0, proc.stderr
    assert "note: .webm" in proc.stdout
    out = sample_video_webm.with_name("sample_flash_night.mp4")
    assert out.exists()
    out.unlink()


@requires_ffmpeg
def test_corrupt_video_is_one_line_error(tmp_path):
    fake = tmp_path / "fake.mp4"
    fake.write_bytes(os.urandom(1024))
    proc = run_cli(str(fake))
    assert proc.returncode == 1
    assert proc.stderr.count("\n") == 1
    assert "Traceback" not in proc.stderr


@requires_ffmpeg
def test_temp_dir_cleaned_up(sample_video, tmp_path):
    import tempfile

    before = set(Path(tempfile.gettempdir()).glob("patina_*"))
    assert run_cli(str(sample_video), "-o", str(tmp_path / "o.mp4")).returncode == 0
    after = set(Path(tempfile.gettempdir()).glob("patina_*"))
    assert after <= before  # nothing new left behind
