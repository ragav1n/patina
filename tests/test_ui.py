from __future__ import annotations

import shutil

from patina import ui
from patina.presets import PRESETS


def test_choice_title_keeps_name_and_never_wraps():
    tokens = ui.choice_title("flash_night", "a very long description " * 25, 16)
    assert isinstance(tokens, list) and all(len(t) == 2 for t in tokens)
    assert tokens[0][0] == "class:answer" and tokens[1][0] == "class:instruction"
    rendered = "".join(text for _cls, text in tokens)
    assert "flash_night" in rendered            # name survives intact
    cols = shutil.get_terminal_size((80, 24)).columns
    assert len(rendered) <= cols                # single line, never wraps
    assert rendered.rstrip().endswith("…")      # long description was truncated


def test_choice_title_short_desc_untouched():
    rendered = "".join(t for _c, t in ui.choice_title("cctv", "surveillance look", 16))
    assert "surveillance look" in rendered
    assert "…" not in rendered


def test_ui_helpers_run_and_emit_text(capsys):
    ui.banner()
    ui.list_presets(PRESETS)
    ui.command_panel("patina photo.jpg --preset cyberpunk")
    ui.done("wrote photo_cyberpunk.jpg")
    ui.progress(3, len(PRESETS), "cyberpunk")
    out = capsys.readouterr().out
    assert "flash_night" in out and "cyberpunk" in out   # the presets table
    assert "photo.jpg" in out                            # the command panel
    assert "wrote" in out                                # the done() line
