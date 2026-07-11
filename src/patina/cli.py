"""Command-line interface: argument parsing, dispatch, and error reporting."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from patina import __version__, image_io, overlays, video
from patina.errors import PatinaError
from patina.presets import PRESETS
from patina.render import RenderOptions

# Sentinel for "--timestamp given with no text": stamp the current date/time.
_TS_NOW = object()

_DEFAULT_PRESET = "flash_night"

_DESCRIPTION = (
    "Apply a nostalgic digicam/camcorder look to photos and videos. "
    "Runs fully offline."
)

_EPILOG = """\
supported inputs:
  images  .jpg .jpeg .png .bmp .tiff .webp .heic .heif   (or a folder of images)
  videos  .mp4 .mov .avi .mkv .webm .m4v   (needs ffmpeg on PATH; audio is kept)

examples:
  patina photo.jpg                          flash_night look -> photo_flash_night.jpg
  patina photo.heic --preset camcorder_warm warm camcorder look, HEIC in and out
  patina vacation/                          every image -> vacation/nostalgia_flash_night/
  patina photo.jpg -o retro.png             pick the output path (and format)
  patina photo.jpg -all                     every look at once -> photo_<preset>.jpg
                                            each (works for videos too, just slower)
  patina photo.jpg --timestamp              stamp the current date/time
  patina photo.jpg --timestamp "26/02/'23  02:52"
                                            stamp custom text (keep flag after the file)
  patina photo.jpg --rec --frame-counter 100-0085
                                            camcorder REC dot + clip counter
  patina clip.mp4 --rec --max-width 1280    filter a video; REC timer runs with the clip
  patina --list-presets                     show the available looks
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patina",
        description=_DESCRIPTION,
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input", nargs="?", metavar="INPUT",
        help="image file, video file, or folder of images",
    )
    parser.add_argument(
        "-o", "--output", metavar="PATH", default=None,
        help="output file (or directory for folder input); "
             "default: <name>_<preset><ext> next to the input",
    )
    parser.add_argument(
        "--preset", choices=sorted(PRESETS), default=None,
        help=f"which look to apply (default: {_DEFAULT_PRESET})",
    )
    parser.add_argument(
        "-all", "--all", dest="all_presets", action="store_true",
        help="apply every preset; each output gets its usual _<preset> suffix",
    )
    parser.add_argument(
        "--timestamp", nargs="?", const=_TS_NOW, default=None, metavar="TEXT",
        help="corner timestamp; bare flag stamps the current date/time, "
             "with TEXT stamps that instead",
    )
    parser.add_argument(
        "--rec", action="store_true",
        help="add the camcorder REC dot + counter",
    )
    parser.add_argument(
        "--rec-counter", default="00:00:06", metavar="TEXT",
        help="counter text next to the REC dot, images only — video computes "
             "its own from elapsed time (default: %(default)s)",
    )
    parser.add_argument(
        "--frame-counter", default=None, metavar="TEXT",
        help="clip/frame index in the top-right corner, e.g. 100-0085 (images only)",
    )
    parser.add_argument(
        "--max-width", type=int, default=None, metavar="N",
        help="video only: downscale to at most N px wide before filtering (faster)",
    )
    parser.add_argument(
        "--list-presets", action="store_true",
        help="list the available presets and exit",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}",
    )
    return parser


def _note(msg: str) -> None:
    print(f"note: {msg}", file=sys.stderr)


def _process_one(
    path: Path, out: Optional[Path], args: argparse.Namespace,
    options: RenderOptions, multi: bool, show_notes: bool,
) -> None:
    """Run one preset over the input; ``multi`` = part of an -all sweep
    (``show_notes`` silences the one-time flag warnings on repeat passes)."""
    suffix = path.suffix.lower()
    if path.is_dir() or suffix in image_io.IMAGE_EXTENSIONS:
        if args.max_width is not None and show_notes:
            _note("--max-width applies to video only; ignoring")
        if path.is_dir():
            # In an -all sweep a single -o directory would collide across
            # presets; give each preset its own subdirectory.
            out_dir = out / options.preset if (multi and out) else out
            written = image_io.process_directory(path, out_dir, options)
            print(f"wrote {len(written)} images to {written[0].parent}")
        else:
            print(f"wrote {image_io.process_image(path, out, options)}")
    elif suffix in video.VIDEO_EXTENSIONS:
        if args.frame_counter is not None and show_notes:
            _note("--frame-counter applies to images only; ignoring")
        if args.rec_counter != "00:00:06" and show_notes:
            _note("--rec-counter applies to images only; video computes its own counter")
        # process_video can't write into a bare directory itself.
        out_file = (
            out / video.default_output_path(path, options.preset).name
            if (multi and out) else out
        )
        print(f"wrote {video.process_video(path, out_file, options)}")
    else:
        raise PatinaError(
            f"unsupported file type '{path.suffix or path.name}' — supported "
            f"images: {' '.join(sorted(image_io.IMAGE_EXTENSIONS))}; "
            f"videos: {' '.join(sorted(video.VIDEO_EXTENSIONS))}"
        )


def _dispatch(args: argparse.Namespace) -> None:
    path = Path(args.input)
    if not path.exists():
        raise PatinaError(f"input not found: {path}")
    out = Path(args.output) if args.output else None
    timestamp_text = (
        overlays.default_timestamp_text()
        if args.timestamp is _TS_NOW
        else args.timestamp
    )
    if args.all_presets:
        if args.preset is not None:
            _note(f"--preset {args.preset} is ignored with -all (every preset runs)")
        if out is not None and not path.is_dir():
            # One fixed path can't hold every preset's output — fill it as a
            # directory of <name>_<preset><ext> files instead.
            out.mkdir(parents=True, exist_ok=True)
        names = sorted(PRESETS)
    else:
        names = [args.preset or _DEFAULT_PRESET]
    for i, name in enumerate(names):
        if args.all_presets:
            print(f"[{i + 1}/{len(names)}] {name}")
        options = RenderOptions(
            preset=name,
            timestamp_text=timestamp_text,
            rec=args.rec,
            rec_counter=args.rec_counter,
            frame_counter=args.frame_counter,
            max_width=args.max_width,
        )
        _process_one(path, out, args, options,
                     multi=args.all_presets, show_notes=i == 0)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_presets:
        width = max(len(name) for name in PRESETS)
        for name in sorted(PRESETS):
            print(f"{name:<{width}}  {PRESETS[name]['description']}")
        return 0
    if args.input is None:
        parser.print_help()
        return 0
    try:
        _dispatch(args)
        return 0
    except PatinaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
