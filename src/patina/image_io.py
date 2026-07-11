"""Image loading, saving, output naming, and batch directory processing."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageOps, UnidentifiedImageError

from patina.errors import PatinaError
from patina.presets import PRESETS
from patina.render import RenderOptions, render_frame

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()  # registers both open and save for .heic/.heif
    _HEIF_OK = True
except ImportError:  # pragma: no cover - pillow-heif is a declared dependency
    _HEIF_OK = False

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".heic", ".heif"}
_HEIF_EXTENSIONS = {".heic", ".heif"}
_HEIF_MISSING_MSG = (
    "HEIC support requires the pillow-heif package (pip install pillow-heif)"
)


def load_image(path: Path) -> Image.Image:
    if path.suffix.lower() in _HEIF_EXTENSIONS and not _HEIF_OK:
        raise PatinaError(_HEIF_MISSING_MSG)
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)  # phones store rotation in EXIF
        return img.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise PatinaError(f"cannot read image '{path.name}': {exc}") from None


def save_image(img: Image.Image, path: Path) -> None:
    ext = path.suffix.lower()
    if ext in _HEIF_EXTENSIONS and not _HEIF_OK:
        raise PatinaError(_HEIF_MISSING_MSG)
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if ext in (".jpg", ".jpeg"):
        kwargs = {"quality": 92}  # lower would smooth away the grain we just added
    elif ext == ".webp":
        kwargs = {"quality": 90}
    try:
        img.save(path, **kwargs)
    except (OSError, ValueError, KeyError) as exc:
        raise PatinaError(f"cannot write '{path.name}': {exc}") from None


def default_output_path(in_path: Path, preset: str) -> Path:
    """``photo.jpg`` + ``flash_night`` -> ``photo_flash_night.jpg`` next to the input."""
    return in_path.with_name(f"{in_path.stem}_{preset}{in_path.suffix}")


def process_image(
    in_path: Path, out_path: Optional[Path], options: RenderOptions
) -> Path:
    img = load_image(in_path)
    out = render_frame(
        img,
        PRESETS[options.preset],
        timestamp_text=options.timestamp_text,
        rec_text=options.rec_counter if options.rec else None,
        frame_text=options.frame_counter,
    )
    if out_path is None:
        out_path = default_output_path(in_path, options.preset)
    elif out_path.is_dir():
        out_path = out_path / default_output_path(in_path, options.preset).name
    save_image(out, out_path)
    return out_path


def process_directory(
    in_dir: Path, out_dir: Optional[Path], options: RenderOptions
) -> List[Path]:
    files = sorted(
        p
        for p in in_dir.iterdir()
        if p.is_file()
        and not p.name.startswith(".")  # .DS_Store and friends
        and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not files:
        raise PatinaError(f"no supported images found in '{in_dir}'")
    if out_dir is None:
        out_dir = in_dir / f"nostalgia_{options.preset}"
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for i, path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {path.name}")
        try:
            written.append(process_image(path, out_dir / path.name, options))
        except PatinaError as exc:
            print(f"  warning: skipped {path.name}: {exc}", file=sys.stderr)
    if not written:
        raise PatinaError(f"all {len(files)} images in '{in_dir}' failed to process")
    return written
