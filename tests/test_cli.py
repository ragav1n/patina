from __future__ import annotations

import subprocess
import sys

import pytest
from PIL import Image

from patina import cli
from patina.presets import PRESETS

from conftest import gradient_array


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "patina", *args],
        capture_output=True, text=True, cwd=cwd,
    )


def test_no_args_prints_help():
    proc = run_cli()
    assert proc.returncode == 0
    assert "usage:" in proc.stdout
    assert "--preset" in proc.stdout
    assert "examples:" in proc.stdout  # the epilog with per-flag examples


def test_help_flag_documents_every_flag():
    proc = run_cli("--help")
    assert proc.returncode == 0
    for flag in ("--output", "--preset", "--timestamp", "--rec", "--rec-counter",
                 "--frame-counter", "--max-width", "--list-presets"):
        assert flag in proc.stdout, flag


def test_list_presets_is_distinct_from_help():
    proc = run_cli("--list-presets")
    assert proc.returncode == 0
    assert "flash_night" in proc.stdout
    assert "camcorder_warm" in proc.stdout
    assert "usage:" not in proc.stdout  # not a help dump
    help_out = run_cli().stdout
    assert proc.stdout != help_out


def test_missing_input_is_one_line_error():
    proc = run_cli("no_such_file.jpg")
    assert proc.returncode == 1
    assert proc.stderr.count("\n") == 1
    assert "input not found" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_unsupported_extension_names_supported_ones(tmp_path):
    bad = tmp_path / "document.txt"
    bad.write_text("hello")
    proc = run_cli(str(bad))
    assert proc.returncode == 1
    assert "unsupported file type" in proc.stderr
    assert ".jpg" in proc.stderr and ".mp4" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_bad_preset_uses_argparse_error(jpg_path):
    proc = run_cli(str(jpg_path), "--preset", "vhs")
    assert proc.returncode == 2  # argparse's own choice validation
    assert "invalid choice" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_image_end_to_end_with_all_overlays(jpg_path):
    proc = run_cli(str(jpg_path), "--preset", "camcorder_warm", "--rec",
                   "--rec-counter", "00:01:23", "--frame-counter", "100-0085",
                   "--timestamp", "26/02/'23  02:52")
    assert proc.returncode == 0, proc.stderr
    assert (jpg_path.parent / "photo_camcorder_warm.jpg").exists()


def test_bare_timestamp_flag_stamps_current_time(jpg_path):
    proc = run_cli(str(jpg_path), "--timestamp")
    assert proc.returncode == 0, proc.stderr


def test_output_flag_respected(jpg_path, tmp_path):
    target = tmp_path / "custom" / "retro.png"
    proc = run_cli(str(jpg_path), "-o", str(target))
    assert proc.returncode == 0, proc.stderr
    assert target.exists()


def test_batch_via_cli(tmp_path):
    for name in ("a.jpg", "b.jpg"):
        Image.fromarray(gradient_array(), "RGB").save(tmp_path / name)
    proc = run_cli(str(tmp_path), "--preset", "camcorder_warm")
    assert proc.returncode == 0, proc.stderr
    out_dir = tmp_path / "nostalgia_camcorder_warm"
    assert sorted(p.name for p in out_dir.iterdir()) == ["a.jpg", "b.jpg"]


def test_max_width_on_image_warns_but_succeeds(jpg_path):
    proc = run_cli(str(jpg_path), "--max-width", "500")
    assert proc.returncode == 0
    assert "note: --max-width" in proc.stderr


def test_new_preset_needs_only_config(monkeypatch, jpg_path, capsys):
    """Acceptance criterion: a new look = one presets.py entry, nothing else."""
    monkeypatch.setitem(PRESETS, "test_sepia", {
        "description": "test-only sepia look",
        "color": {"r_mult": 1.2, "g_mult": 1.0, "b_mult": 0.7,
                  "brightness": 1.0, "contrast": 1.0},
        "grain_sigma": 5,
    })
    assert cli.main([str(jpg_path), "--preset", "test_sepia"]) == 0
    assert (jpg_path.parent / "photo_test_sepia.jpg").exists()
    assert cli.main(["--list-presets"]) == 0
    assert "test_sepia" in capsys.readouterr().out
