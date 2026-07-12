"""Guided, arrow-key walkthrough for when ``patina`` is run with no flags.

Aimed at people who don't want to memorise flags: point at a file, pick a
look, optionally add a timestamp, and go. The prompting (questionary) is kept
separate from the logic (``_build_args``) so the logic stays unit-testable
without a pseudo-terminal, and ``questionary`` is imported lazily so a missing
copy can never break ordinary ``patina photo.jpg`` usage.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Optional

from patina import overlays, ui
from patina.presets import PRESETS

# Menu value standing in for "-all". A NUL keeps it from ever colliding with a
# real preset name.
_ALL = "\x00all-looks"

# questionary Style tokens, themed from the shared verdigris/copper palette.
_STYLE_TOKENS = [
    ("qmark", f"fg:{ui.PATINA} bold"),
    ("question", "bold"),
    ("answer", f"fg:{ui.COPPER} bold"),
    ("pointer", f"fg:{ui.COPPER} bold"),
    ("highlighted", f"fg:{ui.COPPER} bold"),
    ("selected", f"fg:{ui.PATINA}"),
    ("instruction", f"fg:{ui.DIM} italic"),
    ("separator", f"fg:{ui.DIM}"),
    ("disabled", "fg:#666 italic"),
]
_QMARK = "◆"


def _clean_path(raw: str) -> str:
    """Normalise a typed/dragged path: trim whitespace, drop the quotes macOS
    wraps a dragged-in file in, and expand ``~``."""
    return str(Path(raw.strip().strip('"').strip("'")).expanduser())


def _validate_path(raw: str):
    """questionary validator: True when the path exists, else a message."""
    if not raw.strip():
        return "Please enter a path (or drag a file into the terminal)."
    if Path(_clean_path(raw)).exists():
        return True
    return "No file or folder at that path — try again."


def _build_args(parser: argparse.ArgumentParser, answers: dict) -> argparse.Namespace:
    """Turn gathered answers into a fully-populated argparse Namespace.

    Pure (no I/O) so it can be unit-tested. Starts from the parser's own
    defaults so every attribute exists — including any flag added later — and
    only overrides the handful the walkthrough asks about.
    """
    args = parser.parse_args([])
    args.input = answers["input"]

    look = answers["look"]
    if look == _ALL:
        args.all_presets = True
    else:
        args.preset = look

    mode = answers.get("timestamp", "none")
    if mode == "now":
        args.timestamp = overlays.default_timestamp_text()
    elif mode == "custom":
        args.timestamp = answers.get("timestamp_text") or ""
    else:
        args.timestamp = None

    output = (answers.get("output") or "").strip()
    args.output = output or None
    return args


def _command_string(args: argparse.Namespace, ts_mode: str) -> str:
    """The equivalent one-liner, so the user learns the flags for next time."""
    parts = ["patina", shlex.quote(args.input)]
    if args.all_presets:
        parts.append("-all")
    elif args.preset:
        parts.append(f"--preset {args.preset}")
    if ts_mode == "now":
        parts.append("--timestamp")
    elif ts_mode == "custom" and args.timestamp:
        parts.append(f"--timestamp {shlex.quote(args.timestamp)}")
    if args.output:
        parts.append(f"-o {shlex.quote(args.output)}")
    return " ".join(parts)


def run(parser: argparse.ArgumentParser) -> Optional[argparse.Namespace]:
    """Prompt the user and return a ready-to-dispatch Namespace, or None if
    they bail (Ctrl-C / Esc) or questionary isn't installed."""
    try:
        import questionary
    except ImportError:
        print("note: the guided menu needs the 'questionary' package.", file=sys.stderr)
        print("      reinstall patina to pull it in:  "
              "uv tool install --reinstall .", file=sys.stderr)
        parser.print_help()
        return None

    style = questionary.Style(_STYLE_TOKENS)
    ui.banner()

    raw_path = questionary.path(
        "Which photo, video, or folder?", validate=_validate_path,
        style=style, qmark=_QMARK,
    ).ask()
    if raw_path is None:
        return None

    width = max(len(name) for name in list(PRESETS) + ["all looks"])
    look_choices = [
        questionary.Choice(
            title=ui.choice_title(name, PRESETS[name]["description"], width),
            value=name,
        )
        for name in sorted(PRESETS)
    ]
    look_choices.append(
        questionary.Choice(
            title=ui.choice_title("all looks", "apply every preset (one file each)", width),
            value=_ALL,
        )
    )
    look = questionary.select(
        "Pick a look:", choices=look_choices, style=style, qmark=_QMARK,
        pointer="❯", instruction="↑/↓ then Enter", show_description=False,
    ).ask()
    if look is None:
        return None

    ts_mode = questionary.select(
        "Add a corner timestamp?",
        choices=[
            questionary.Choice("No", value="none"),
            questionary.Choice("Current date & time", value="now"),
            questionary.Choice("Custom text…", value="custom"),
        ],
        style=style, qmark=_QMARK, pointer="❯",
    ).ask()
    if ts_mode is None:
        return None

    ts_text = ""
    if ts_mode == "custom":
        ts_text = questionary.text(
            "Timestamp text:", default=overlays.default_timestamp_text(),
            style=style, qmark=_QMARK,
        ).ask()
        if ts_text is None:
            return None

    output = questionary.text(
        "Save as (blank = auto-name next to the input):",
        style=style, qmark=_QMARK,
    ).ask()
    if output is None:
        return None

    answers = {
        "input": _clean_path(raw_path),
        "look": look,
        "timestamp": ts_mode,
        "timestamp_text": ts_text,
        "output": output,
    }
    args = _build_args(parser, answers)
    ui.command_panel(_command_string(args, ts_mode))
    return args
