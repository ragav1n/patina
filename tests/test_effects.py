from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from patina import effects
from patina.presets import PRESETS

from conftest import gradient_array


def _arr(img: Image.Image) -> np.ndarray:
    return np.asarray(img, dtype=np.float32)


def test_empty_preset_is_identity(gradient_image):
    out = effects.apply_preset(gradient_image, {"description": "nothing"})
    assert np.array_equal(np.asarray(out), np.asarray(gradient_image))


def test_reduce_detail_softens_but_keeps_size(gradient_image):
    out = effects.reduce_detail(gradient_image, 0.42)
    assert out.size == gradient_image.size
    # A checkerboard would be flattened; a smooth gradient survives mostly intact.
    checker = Image.fromarray(
        (np.indices((64, 64)).sum(axis=0) % 2 * 255).astype(np.uint8)
    ).convert("RGB")
    soft = effects.reduce_detail(checker, 0.42)
    assert _arr(soft).std() < _arr(checker).std() * 0.7


def test_reduce_detail_tiny_image():
    img = Image.new("RGB", (2, 2), (100, 100, 100))
    out = effects.reduce_detail(img, 0.1)  # would round to 0 without the guard
    assert out.size == (2, 2)


def test_color_grade_channel_gains():
    arr = np.full((10, 10, 3), 100.0, dtype=np.float32)
    out = effects.color_grade(arr, r_mult=0.5, g_mult=1.0, b_mult=2.0,
                              brightness=1.0, contrast=1.0)
    assert out[..., 0].mean() == pytest.approx(50.0)
    assert out[..., 1].mean() == pytest.approx(100.0)
    assert out[..., 2].mean() == pytest.approx(200.0)


def test_color_grade_contrast_pivots_at_128():
    arr = np.full((4, 4, 3), 128.0, dtype=np.float32)
    out = effects.color_grade(arr, 1.0, 1.0, 1.0, brightness=1.0, contrast=0.5)
    assert out.mean() == pytest.approx(128.0)  # pivot itself never moves
    dark = np.zeros((4, 4, 3), dtype=np.float32)
    out = effects.color_grade(dark, 1.0, 1.0, 1.0, brightness=1.0, contrast=0.9)
    assert out.mean() == pytest.approx(12.8, abs=0.1)  # milky blacks


def test_flash_hotspot_brightens_center_additively():
    arr = np.zeros((100, 100, 3), dtype=np.float32)  # pure black
    out = effects.flash_hotspot(arr, cx_ratio=0.5, cy_ratio=0.42,
                                radius_ratio=0.55, strength=0.32)
    assert out[42, 50].mean() == pytest.approx(0.32 * 255, rel=0.01)  # blooms even black
    assert out[0, 0].mean() == pytest.approx(0.0, abs=1.0)  # corners untouched


def test_vignette_crushes_corners_not_center():
    arr = np.full((100, 100, 3), 200.0, dtype=np.float32)
    out = effects.vignette(arr, 0.78)
    assert out[50, 50].mean() > 195  # center essentially untouched
    assert out[0, 0].mean() < 55  # corners near-black at strength 0.78
    arr2 = np.full((100, 100, 3), 200.0, dtype=np.float32)
    subtle = effects.vignette(arr2, 0.32)
    assert subtle[0, 0].mean() > 125  # gentle at camcorder strength


def test_chromatic_aberration_shifts_r_and_b_oppositely():
    arr = np.zeros((5, 9, 3), dtype=np.float32)
    arr[:, 4, :] = 255.0  # single vertical white line
    out = effects.chromatic_aberration(arr, 2)
    assert out[0, 6, 0] == 255.0 and out[0, 4, 0] == 0.0  # R moved right
    assert out[0, 2, 2] == 255.0 and out[0, 4, 2] == 0.0  # B moved left
    assert out[0, 4, 1] == 255.0  # G untouched


def test_chromatic_aberration_clamps_edges():
    arr = np.zeros((3, 6, 3), dtype=np.float32)
    arr[:, 0, 0] = 250.0  # bright red on the LEFT edge
    out = effects.chromatic_aberration(arr, 2)
    # np.roll would have wrapped the right edge into view; clamping repeats the edge.
    assert out[0, 0, 0] == 250.0 and out[0, 1, 0] == 250.0 and out[0, 2, 0] == 250.0
    assert out[0, 5, 0] == 0.0


def test_add_grain_deterministic_with_rng():
    a = np.full((32, 32, 3), 128.0, dtype=np.float32)
    b = a.copy()
    out_a = effects.add_grain(a, 13, rng=np.random.default_rng(0))
    out_b = effects.add_grain(b, 13, rng=np.random.default_rng(0))
    assert np.array_equal(out_a, out_b)
    assert out_a.std() == pytest.approx(13.0, rel=0.1)


def test_add_grain_fresh_noise_each_call():
    a = effects.add_grain(np.zeros((32, 32, 3), np.float32), 10)
    b = effects.add_grain(np.zeros((32, 32, 3), np.float32), 10)
    assert not np.array_equal(a, b)


def test_scanlines_darken_spaced_rows():
    arr = np.full((9, 4, 3), 200.0, dtype=np.float32)
    out = effects.scanlines(arr, spacing=3, opacity=32)
    expected = 200.0 * (1.0 - 32 / 255.0)
    assert out[0].mean() == pytest.approx(expected, rel=1e-4)
    assert out[3].mean() == pytest.approx(expected, rel=1e-4)
    assert out[1].mean() == pytest.approx(200.0)
    assert out[2].mean() == pytest.approx(200.0)


def test_flash_night_is_cool_and_dark(gradient_image):
    src = _arr(gradient_image)
    out = _arr(effects.apply_preset(gradient_image, PRESETS["flash_night"]))
    # Cool cast: blue gains relative to red versus the source.
    assert out[..., 2].mean() / max(out[..., 0].mean(), 1) > \
        src[..., 2].mean() / src[..., 0].mean()
    # Darker overall (brightness 0.82 + vignette), despite the hotspot.
    assert out.mean() < src.mean()
    # Corners crushed toward black.
    assert out[:8, :8].mean() < src[:8, :8].mean() * 0.5


def test_camcorder_warm_is_warm_and_milky():
    dark = Image.new("RGB", (120, 90), (5, 5, 5))
    out = _arr(effects.apply_preset(dark, PRESETS["camcorder_warm"]))
    # Milky blacks: a near-black input is lifted well off the floor.
    assert out.mean() > 8.0
    grad = Image.fromarray(gradient_array(), "RGB")
    src = _arr(grad)
    warm = _arr(effects.apply_preset(grad, PRESETS["camcorder_warm"]))
    # Warm cast: red gains relative to blue versus the source.
    assert warm[..., 0].mean() / max(warm[..., 2].mean(), 1) > \
        src[..., 0].mean() / src[..., 2].mean()


def test_presets_visually_distinct(gradient_image):
    a = _arr(effects.apply_preset(gradient_image, PRESETS["flash_night"]))
    b = _arr(effects.apply_preset(gradient_image, PRESETS["camcorder_warm"]))
    src = _arr(gradient_image)
    assert np.abs(a - src).mean() > 10
    assert np.abs(b - src).mean() > 5
    assert np.abs(a - b).mean() > 10
