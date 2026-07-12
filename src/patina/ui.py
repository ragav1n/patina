"""Presentation layer: the verdigris/copper theme and all styled terminal output.

Keeping this in one module lets ``cli.py`` and ``interactive.py`` stay about
logic. ``rich`` is imported defensively — if it's missing (e.g. a globally
installed tool that hasn't been reinstalled since ``rich`` was added), every
helper falls back to a plain ``print`` so ordinary usage never crashes. ``rich``
also drops color automatically when stdout isn't a terminal, so pipes and the
test suite see clean plain text.

Palette rationale: *patina* is the blue-green verdigris that grows on aged
copper and bronze — so the theme pairs verdigris (primary) with a copper accent,
the metal and its patina together.
"""

from __future__ import annotations

import shutil
from typing import Dict, List, Tuple

# --- palette -----------------------------------------------------------------
PATINA = "#5FA893"   # verdigris green — primary: borders, question mark, wordmark
COPPER = "#C8823C"   # warm accent — answers, pointer, highlighted rows
DIM = "#9AA0A6"      # descriptions, taglines, secondary text
RED = "#D06B5C"      # muted terracotta — warnings

try:
    from rich import box
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    HAVE_RICH = True
    _console = Console()
except ImportError:  # pragma: no cover - exercised only without rich installed
    HAVE_RICH = False
    _console = None


def banner() -> None:
    """The double-boxed filmstrip wordmark shown at the top of the guided menu."""
    if not HAVE_RICH:
        print("patina — old-camera looks · fully offline\n")
        return
    word = Text(justify="center")
    word.append("▓▒░  ", style=COPPER)
    word.append("P A T I N A", style=f"bold {PATINA}")
    word.append("  ░▒▓", style=COPPER)
    tagline = Text("photos, aged to taste", style=f"italic {DIM}",
                   justify="center")
    _console.print(Panel(Group(word, tagline), box=box.DOUBLE,
                         border_style=PATINA, padding=(0, 4), expand=False))


def space() -> None:
    """A single blank line, to give each prompt some breathing room."""
    if not HAVE_RICH:
        print()
        return
    _console.print()


def hint(message: str) -> None:
    """A dim, secondary tip line (e.g. the drag-and-drop nudge)."""
    if not HAVE_RICH:
        print(message)
        return
    _console.print(Text(message, style=f"italic {DIM}"))


def command_panel(cmd: str) -> None:
    """Show the equivalent one-line command the guided run is about to execute."""
    if not HAVE_RICH:
        print(f"\nrunning:  {cmd}\n")
        return
    _console.print(Panel(Text(cmd, style=COPPER), title="your command",
                         title_align="left", border_style=DIM, box=box.ROUNDED,
                         padding=(0, 1), expand=False))


def done(message: str) -> None:
    """A finished-writing confirmation, e.g. ``✓ wrote out.jpg``."""
    if not HAVE_RICH:
        print(message)
        return
    line = Text()
    line.append("✓ ", style=f"bold {PATINA}")
    line.append(message)
    _console.print(line)


def progress(index: int, total: int, name: str) -> None:
    """One line of an ``-all`` sweep, e.g. ``[3/12] cyberpunk``."""
    if not HAVE_RICH:
        print(f"[{index}/{total}] {name}")
        return
    line = Text()
    line.append(f"[{index}/{total}] ", style=DIM)
    line.append(name, style=COPPER)
    _console.print(line)


def list_presets(presets: Dict[str, dict]) -> None:
    """The ``--list-presets`` output: a look/description table."""
    if not HAVE_RICH:
        width = max(len(name) for name in presets)
        for name in sorted(presets):
            print(f"{name:<{width}}  {presets[name]['description']}")
        return
    table = Table(box=box.SIMPLE_HEAD, header_style=f"bold {PATINA}",
                  pad_edge=False, padding=(0, 3, 0, 0))
    table.add_column("look", style=COPPER, no_wrap=True)
    table.add_column("what you get", style=DIM)
    for name in sorted(presets):
        table.add_row(name, presets[name]["description"])
    _console.print(table)


def choice_title(name: str, desc: str, name_width: int) -> List[Tuple[str, str]]:
    """Formatted-text title for a questionary menu row: copper name + dim,
    single-line description truncated to the terminal so rows never wrap.

    Pure (no rich needed) — questionary renders a list of (style, text) tuples
    by splicing the tokens, letting the name and description carry different
    styles on one line.
    """
    gap = "  "
    columns = shutil.get_terminal_size((80, 24)).columns
    # leave room for questionary's pointer/indent (~2) plus a small safety margin
    avail = max(12, columns - (2 + name_width + len(gap)) - 2)
    if len(desc) > avail:
        desc = desc[: avail - 1].rstrip() + "…"
    return [
        ("class:answer", name.ljust(name_width)),
        ("class:instruction", gap + desc),
    ]
