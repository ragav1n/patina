"""Video processing via the ffmpeg/ffprobe command-line binaries.

Frames are extracted to a temp directory, run through the exact same
per-image pipeline as photos, reassembled with libx264, and the original
audio track is muxed back in — plain subprocess calls, no OpenCV/moviepy.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import List, Optional

from PIL import Image

from patina.errors import PatinaError
from patina.presets import PRESETS
from patina.render import RenderOptions, render_frame

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
_FASTSTART_EXTENSIONS = {".mp4", ".mov", ".m4v"}

_INSTALL_HINT = (
    "install it and retry — macOS: 'brew install ffmpeg' | Debian/Ubuntu: "
    "'sudo apt install ffmpeg' | Windows: 'choco install ffmpeg'"
)


def _missing_msg(names: List[str]) -> str:
    return (
        f"{' and '.join(names)} not found on PATH (required for video only); "
        + _INSTALL_HINT
    )


def _require_ffmpeg() -> None:
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        raise PatinaError(_missing_msg(missing))


def _run(
    cmd: List[str], what: str, failure: Optional[str] = None
) -> "subprocess.CompletedProcess[str]":
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        raise PatinaError(_missing_msg([cmd[0]])) from None
    if proc.returncode != 0:
        lines = [l.strip() for l in proc.stderr.strip().splitlines() if l.strip()]
        tail = " | ".join(lines[-3:])[-400:]
        msg = failure or f"{cmd[0]} failed while {what}"
        raise PatinaError(f"{msg} ({tail or 'no error output'})")
    return proc


@dataclasses.dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    fps: Fraction
    has_audio: bool
    est_frames: Optional[int]

    @property
    def fps_str(self) -> str:
        """Exact rational (e.g. ``30000/1001``) — no float drift at reassembly."""
        return f"{self.fps.numerator}/{self.fps.denominator}"


def _parse_rate(value: Optional[str]) -> Optional[Fraction]:
    if not value:
        return None
    try:
        rate = Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None
    return rate if rate > 0 else None


def _probe(path: Path) -> VideoInfo:
    corrupt = (
        f"could not read video '{path.name}' — file may be corrupt or not a real video"
    )
    proc = _run(
        ["ffprobe", "-v", "error", "-of", "json", "-show_streams", "-show_format",
         str(path)],
        f"probing {path.name}",
        failure=corrupt,
    )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise PatinaError(corrupt) from None
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise PatinaError(f"no video stream found in '{path.name}'")
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    # avg_frame_rate = frames/duration, which keeps reassembled duration (and the
    # audio sync) exact; r_frame_rate can be wildly high for VFR phone footage.
    fps = _parse_rate(video.get("avg_frame_rate")) or _parse_rate(
        video.get("r_frame_rate")
    )
    if width <= 0 or height <= 0 or fps is None:
        raise PatinaError(corrupt)
    duration = 0.0
    for raw in (data.get("format", {}).get("duration"), video.get("duration")):
        try:
            duration = float(raw)
            break
        except (TypeError, ValueError):
            continue
    nb_frames = video.get("nb_frames")
    if isinstance(nb_frames, str) and nb_frames.isdigit():
        est = int(nb_frames)
    elif duration > 0:
        est = round(duration * float(fps))
    else:
        est = None
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    return VideoInfo(width, height, fps, has_audio, est)


def _extract_frames(
    in_path: Path, tmpdir: Path, max_width: Optional[int]
) -> List[Path]:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
           "-i", str(in_path), "-map", "0:v:0", "-vsync", "0"]
    if max_width:
        # min() only ever downscales; trunc(../2)*2 and -2 keep both dimensions
        # even, which yuv420p requires at reassembly.
        cmd += ["-vf", f"scale='trunc(min(iw,{int(max_width)})/2)*2':-2"]
    cmd += ["-qscale:v", "2", str(tmpdir / "frame_%06d.jpg")]
    _run(
        cmd,
        f"extracting frames from {in_path.name}",
        failure=f"could not extract frames from '{in_path.name}' — file may be corrupt",
    )
    frames = sorted(tmpdir.glob("frame_*.jpg"))
    if not frames:
        raise PatinaError(f"no frames could be extracted from '{in_path.name}'")
    return frames


def _format_hms(seconds: float) -> str:
    hours, rem = divmod(int(seconds), 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _assemble(pattern: Path, original: Path, out_path: Path, fps_str: str) -> None:
    """Reassemble frames and mux the original audio in one ffmpeg pass."""
    base = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-framerate", fps_str, "-start_number", "1", "-i", str(pattern),
            "-i", str(original),
            "-map", "0:v:0", "-map", "1:a:0?",  # '?' tolerates audio-less input
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p",
            # Even dimensions for yuv420p; out_range converts the full-range JPEG
            # intermediates to standard limited-range video (not full-range yuvj).
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2:out_range=tv,format=yuv420p"]
    if out_path.suffix.lower() in _FASTSTART_EXTENSIONS:
        base += ["-movflags", "+faststart"]
    try:
        _run(base + ["-c:a", "copy", "-shortest", str(out_path)],
             f"writing {out_path.name}")
    except PatinaError:
        # Typical cause: the original audio codec isn't allowed in the output
        # container (e.g. PCM in .mp4). Re-encode the audio once and retry.
        print(f"note: original audio codec is not compatible with "
              f"'{out_path.suffix}' — re-encoding audio to AAC")
        _run(base + ["-c:a", "aac", "-b:a", "192k", "-shortest", str(out_path)],
             f"writing {out_path.name}")


def default_output_path(in_path: Path, preset: str) -> Path:
    # WebM can't legally hold H.264 — fall over to .mp4 (process_video prints a note).
    suffix = ".mp4" if in_path.suffix.lower() == ".webm" else in_path.suffix
    return in_path.with_name(f"{in_path.stem}_{preset}{suffix}")


def process_video(
    in_path: Path, out_path: Optional[Path], options: RenderOptions
) -> Path:
    _require_ffmpeg()
    if out_path is None:
        out_path = default_output_path(in_path, options.preset)
        if in_path.suffix.lower() == ".webm":
            print(f"note: .webm cannot hold H.264 video — writing "
                  f"'{out_path.name}' instead")
    elif out_path.suffix.lower() == ".webm":
        raise PatinaError(
            "cannot write .webm output (H.264 is not allowed in WebM) — "
            "use .mp4, .mov, or .mkv"
        )
    info = _probe(in_path)
    preset = PRESETS[options.preset]
    fps = float(info.fps)
    tmpdir = Path(tempfile.mkdtemp(prefix="patina_"))
    try:
        print(f"extracting frames from {in_path.name} ...")
        frames = _extract_frames(in_path, tmpdir, options.max_width)
        total = len(frames)
        for idx, frame_path in enumerate(frames):
            rec_text = _format_hms(idx / fps) if options.rec else None
            with Image.open(frame_path) as im:
                frame = im.convert("RGB")
            out = render_frame(
                frame, preset,
                timestamp_text=options.timestamp_text,
                rec_text=rec_text,
            )
            out.save(frame_path, quality=95)
            print(f"\rprocessing frame {idx + 1}/{total}", end="", flush=True)
        print()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        _assemble(tmpdir / "frame_%06d.jpg", in_path, out_path, info.fps_str)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return out_path
