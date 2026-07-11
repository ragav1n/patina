from __future__ import annotations

import numpy as np
import pytest
from PIL import Image, ImageFilter

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


def test_saturate_toward_gray():
    arr = np.zeros((4, 4, 3), dtype=np.float32)
    arr[..., 0] = 200.0  # pure red
    out = effects.saturate(arr, 0.0)  # full desaturation -> luma everywhere
    assert np.allclose(out[..., 0], out[..., 1])
    assert np.allclose(out[..., 1], out[..., 2])
    assert out[0, 0, 0] == pytest.approx(200 * 0.299, rel=0.01)


def test_bloom_bleeds_highlights_into_neighbors():
    arr = np.full((100, 100, 3), 60.0, dtype=np.float32)
    arr[40:60, 40:60] = 255.0  # hot white square
    out = effects.bloom(arr.copy(), threshold=168, radius_ratio=0.05, strength=0.6)
    assert out[50, 35].mean() > 70.0  # glow reaches OUTSIDE the square
    assert out[50, 5].mean() == pytest.approx(60.0, abs=1.0)  # far away untouched
    dark = np.full((100, 100, 3), 60.0, dtype=np.float32)
    assert effects.bloom(dark.copy(), 168, 0.05, 0.6).mean() == pytest.approx(60.0, abs=0.5)


def test_fade_lifts_blacks_and_caps_whites():
    arr = np.zeros((4, 4, 3), dtype=np.float32)
    assert effects.fade(arr, black=22, white=238).mean() == pytest.approx(22.0)
    arr = np.full((4, 4, 3), 255.0, dtype=np.float32)
    assert effects.fade(arr, black=22, white=238).mean() == pytest.approx(238.0)


def test_mono_grain_is_luma_only():
    arr = np.full((32, 32, 3), 128.0, dtype=np.float32)
    out = effects.add_grain(arr, 10, rng=np.random.default_rng(0), mono=True)
    assert np.array_equal(out[..., 0], out[..., 1])  # same noise on every channel
    assert np.array_equal(out[..., 1], out[..., 2])


def test_render_width_processes_small_but_returns_original_size():
    big = Image.new("RGB", (2000, 1500), (120, 120, 120))
    out = effects.apply_preset(big, {"render_width": 500, "grain_sigma": 10})
    assert out.size == (2000, 1500)
    # Grain was added at 500px and upscaled: neighboring pixels correlate,
    # so per-pixel noise variance is well below sigma at full resolution.
    arr = np.asarray(out, dtype=np.float32)
    assert 1.0 < arr.std() < 10.0
    small = Image.new("RGB", (300, 200), (120, 120, 120))
    assert effects.apply_preset(small, {"render_width": 500}).size == (300, 200)


def test_y2k_camcorder_is_washed_and_soft(gradient_image):
    src = _arr(gradient_image)
    out = _arr(effects.apply_preset(gradient_image, PRESETS["y2k_camcorder"]))
    assert out.min() > 5.0  # no true black anywhere: lifted floor
    # Whites capped for the bulk of the frame; a blown sliver is authentic.
    luma = out @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    assert np.percentile(luma, 95) < 250.0
    # Desaturated: per-pixel channel spread shrinks.
    spread = lambda a: np.abs(a - a.mean(axis=-1, keepdims=True)).mean()
    assert spread(out) < spread(src) * 0.85
    # Cool cast: blue gains on red versus the source.
    assert out[..., 2].mean() / max(out[..., 0].mean(), 1) > \
        src[..., 2].mean() / src[..., 0].mean()


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


def test_sharpen_raises_edge_contrast():
    # A blurred step edge regains slope (with overshoot) after sharpening.
    arr = np.zeros((40, 40, 3), dtype=np.uint8)
    arr[:, 20:] = 200
    soft = Image.fromarray(arr, "RGB").filter(ImageFilter.GaussianBlur(2))
    sharp = effects.sharpen(soft, radius=2.0, amount=1.6)
    grad = lambda img: np.abs(np.diff(_arr(img)[20, :, 0])).max()
    assert grad(sharp) > grad(soft) * 1.3


def test_chroma_bleed_smears_color_not_luma():
    # A saturated red/green boundary at constant luma: color should smear
    # across it while a pure-luma edge stays put.
    arr = np.zeros((40, 80, 3), dtype=np.float32)
    arr[:, :40, 0] = 150.0  # red left half
    arr[:, 40:, 1] = 150.0  # green right half
    out = effects.chroma_bleed(arr.copy(), radius_ratio=0.05)
    # Red now reaches past the boundary into the green half.
    assert out[20, 44, 0] > arr[20, 44, 0] + 10
    # Luma is preserved (bleed redistributes color, not brightness).
    luma_w = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    assert np.abs((out @ luma_w) - (arr @ luma_w)).mean() < 2.0


def test_jpeg_artifacts_keeps_size_and_alters_pixels(gradient_image):
    out = effects.jpeg_artifacts(gradient_image, quality=30)
    assert out.size == gradient_image.size
    assert out.mode == "RGB"
    diff = np.abs(_arr(out) - _arr(gradient_image))
    assert 0.1 < diff.mean() < 20.0  # visibly touched, not destroyed


def test_motion_blur_smears_along_the_angle():
    arr = np.zeros((30, 60, 3), dtype=np.float32)
    arr[:, 30, :] = 255.0  # vertical white line
    out = effects.motion_blur(arr.copy(), distance_ratio=0.1, angle=0)
    # Horizontal smear spreads the line sideways without losing energy.
    assert out[15, 28].mean() > 20.0 and out[15, 32].mean() > 20.0
    assert out.sum() == pytest.approx(arr.sum(), rel=0.02)
    # At 90 degrees the smear runs down the line instead: columns stay clean.
    vertical = effects.motion_blur(arr.copy(), distance_ratio=0.1, angle=90)
    assert vertical[15, 28].mean() == pytest.approx(0.0, abs=1.0)


def test_blurry_aesthetic_is_much_softer_than_source(gradient_image):
    # A checkerboard has maximal fine detail; the preset should flatten it.
    checker = Image.fromarray(
        (np.indices((120, 160)).sum(axis=0) % 2 * 255).astype(np.uint8)
    ).convert("RGB")
    out = _arr(effects.apply_preset(checker, PRESETS["blurry_aesthetic"]))
    assert out.std() < _arr(checker).std() * 0.4


def test_disposable_flash_is_warm_punchy_and_vignetted(gradient_image):
    src = _arr(gradient_image)
    out = _arr(effects.apply_preset(gradient_image, PRESETS["disposable_flash"]))
    # Warm cast: red gains relative to blue versus the source.
    assert out[..., 0].mean() / max(out[..., 2].mean(), 1) > \
        src[..., 0].mean() / src[..., 2].mean()
    # Dark corners from the heavy vignette.
    assert out[:8, :8].mean() < src[:8, :8].mean()


def test_digicam_2000s_is_sharpened_and_vivid(gradient_image):
    # Real detail (a checkerboard), identical grain: only the unsharp mask
    # differs between the two runs.
    checker = Image.fromarray(
        (np.indices((60, 80)).sum(axis=0) % 8 // 4 * 200 + 30).astype(np.uint8)
    ).convert("RGB")
    rng = np.random.default_rng
    out = _arr(effects.apply_preset(checker, PRESETS["digicam_2000s"], rng=rng(0)))
    reduce_only = dict(PRESETS["digicam_2000s"])
    del reduce_only["sharpen"]
    soft = _arr(effects.apply_preset(checker, reduce_only, rng=rng(0)))
    edge_energy = lambda a: np.abs(np.diff(a.mean(axis=-1), axis=1)).mean()
    assert edge_energy(out) > edge_energy(soft)
    # Vivid: channel spread grows versus the source.
    src = _arr(gradient_image)
    vivid = _arr(effects.apply_preset(gradient_image, PRESETS["digicam_2000s"]))
    spread = lambda a: np.abs(a - a.mean(axis=-1, keepdims=True)).mean()
    assert spread(vivid) > spread(src)


def test_vhs_tape_is_washed_and_scanlined(gradient_image):
    src = _arr(gradient_image)
    out = _arr(effects.apply_preset(gradient_image, PRESETS["vhs_tape"]))
    assert out.min() > 2.0  # lifted floor from fade
    spread = lambda a: np.abs(a - a.mean(axis=-1, keepdims=True)).mean()
    assert spread(out) < spread(src)  # desaturated


def test_cctv_is_near_monochrome_and_green(gradient_image):
    src = _arr(gradient_image)
    out = _arr(effects.apply_preset(gradient_image, PRESETS["cctv"]))
    spread = lambda a: np.abs(a - a.mean(axis=-1, keepdims=True)).mean()
    # Most of the source color collapses; the remainder is the green tint.
    assert spread(out) < spread(src) * 0.4
    assert out[..., 1].mean() > out[..., 0].mean()  # green-leaning
    assert out[..., 1].mean() > out[..., 2].mean()


def test_lomo_xpro_is_saturated_with_dark_corners(gradient_image):
    src = _arr(gradient_image)
    out = _arr(effects.apply_preset(gradient_image, PRESETS["lomo_xpro"]))
    spread = lambda a: np.abs(a - a.mean(axis=-1, keepdims=True)).mean()
    assert spread(out) > spread(src)  # punchier color than the source
    assert out[:6, :6].mean() < src[:6, :6].mean() * 0.6  # heavy vignette


def test_instant_film_is_warm_and_milky(gradient_image):
    src = _arr(gradient_image)
    out = _arr(effects.apply_preset(gradient_image, PRESETS["instant_film"]))
    assert out.min() > 15.0  # milky lifted blacks
    # Warm cream cast: red gains relative to blue versus the source.
    assert out[..., 0].mean() / max(out[..., 2].mean(), 1) > \
        src[..., 0].mean() / src[..., 2].mean()


def test_presets_visually_distinct(gradient_image):
    outs = {
        name: _arr(effects.apply_preset(gradient_image, preset))
        for name, preset in PRESETS.items()
    }
    src = _arr(gradient_image)
    for name, a in outs.items():
        assert np.abs(a - src).mean() > 5, name
    done = []
    for name, a in outs.items():
        for other in done:
            assert np.abs(a - outs[other]).mean() > 5, (name, other)
        done.append(name)
