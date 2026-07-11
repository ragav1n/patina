from __future__ import annotations

import re
from datetime import datetime

import numpy as np
from PIL import Image

from patina import overlays
from patina.presets import PRESETS
from patina.render import render_frame


def _gray(w=320, h=240):
    return Image.new("RGB", (w, h), (90, 90, 90))


def _diff_region(before: Image.Image, after: Image.Image):
    return np.abs(
        np.asarray(after, dtype=np.float32) - np.asarray(before, dtype=np.float32)
    ).sum(axis=-1)


def test_default_timestamp_format():
    text = overlays.default_timestamp_text(datetime(2023, 2, 26, 2, 52))
    assert text == "26/02/'23  02:52"
    assert re.fullmatch(r"\d{2}/\d{2}/'\d{2}  \d{2}:\d{2}",
                        overlays.default_timestamp_text())


def test_timestamp_lands_bottom_right():
    img = _gray()
    out = overlays.add_timestamp(img.copy(), "26/02/'23  02:52")
    diff = _diff_region(img, out)
    h, w = diff.shape
    assert diff[h // 2:, w // 2:].sum() > 0  # bottom-right quadrant touched
    assert diff[: h // 2, :].sum() == 0  # top half untouched
    assert diff[:, : w // 4].sum() == 0  # left quarter untouched


def test_timestamp_is_amber():
    img = _gray()
    out = overlays.add_timestamp(img.copy(), "26/02/'23  02:52")
    arr = np.asarray(out, dtype=np.float32)
    changed = _diff_region(img, out) > 30
    assert changed.any()
    r, g, b = (arr[..., i][changed].mean() for i in range(3))
    assert r > g > b  # amber: strong red, mid green, low blue


def test_rec_indicator_lands_top_left_with_red_dot():
    img = _gray()
    out = overlays.add_rec_indicator(img.copy(), "00:00:06")
    diff = _diff_region(img, out)
    h, w = diff.shape
    assert diff[: h // 2, : w // 2].sum() > 0  # top-left quadrant touched
    assert diff[h // 2:, :].sum() == 0  # bottom half untouched
    arr = np.asarray(out, dtype=np.float32)
    corner = arr[: h // 4, : w // 3]
    redness = corner[..., 0] - (corner[..., 1] + corner[..., 2]) / 2
    assert redness.max() > 100  # a strongly red dot exists


def test_frame_counter_lands_top_right():
    img = _gray()
    out = overlays.add_frame_counter(img.copy(), "100-0085")
    diff = _diff_region(img, out)
    h, w = diff.shape
    assert diff[: h // 2, w // 2:].sum() > 0
    assert diff[h // 2:, :].sum() == 0
    assert diff[:, : w // 2].sum() == 0


def test_all_three_overlays_coexist():
    img = _gray()
    out = overlays.add_rec_indicator(img.copy(), "00:00:06")
    out = overlays.add_frame_counter(out, "100-0085")
    out = overlays.add_timestamp(out, "26/02/'23  02:52")
    diff = _diff_region(img, out)
    h, w = diff.shape
    assert diff[: h // 3, : w // 2].sum() > 0  # REC
    assert diff[: h // 3, w // 2:].sum() > 0  # frame counter
    assert diff[2 * h // 3:, w // 2:].sum() > 0  # timestamp


def test_overlays_scale_with_image_size():
    small = overlays.add_timestamp(_gray(160, 120), "26/02/'23  02:52")
    large = overlays.add_timestamp(_gray(3200, 2400), "26/02/'23  02:52")
    small_touched = (_diff_region(_gray(160, 120), small) > 0).sum()
    large_touched = (_diff_region(_gray(3200, 2400), large) > 0).sum()
    assert large_touched > small_touched * 10  # font grew with the canvas


def test_font_loader_never_raises_and_caches():
    a = overlays.load_mono_font(24)
    b = overlays.load_mono_font(24)
    assert a is b


def test_render_frame_applies_effects_and_overlays():
    img = _gray()
    plain = render_frame(img, PRESETS["camcorder_warm"])
    chromed = render_frame(
        img, PRESETS["camcorder_warm"],
        timestamp_text="26/02/'23  02:52", rec_text="00:00:06",
        frame_text="100-0085",
    )
    assert plain.size == img.size
    # Overlays add pixels the plain render doesn't have (grain differs everywhere,
    # so compare against the source instead: chrome corners must differ strongly).
    diff = _diff_region(img, chromed)
    h, w = diff.shape
    assert diff[: h // 4, : w // 3].max() > 150  # REC dot region
