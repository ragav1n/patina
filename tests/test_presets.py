from __future__ import annotations

from patina.presets import PRESETS

RECOGNIZED_KEYS = {
    "description", "render_width", "reduce_scale", "sharpen", "color",
    "saturation", "chroma_bleed", "flash_hotspot", "vignette_strength",
    "bloom", "fade", "aberration_shift", "grain_sigma", "grain_mono",
    "scanlines", "jpeg_quality",
}


def test_shipping_presets():
    assert set(PRESETS) == {
        "flash_night", "camcorder_warm", "y2k_camcorder",
        "disposable_flash", "digicam_2000s", "vhs_tape",
        "cctv", "lomo_xpro", "instant_film",
    }


def test_every_preset_has_a_description():
    for name, preset in PRESETS.items():
        assert preset.get("description"), name


def test_no_unrecognized_keys():
    """A typo'd key would be silently skipped by the engine — catch it here."""
    for name, preset in PRESETS.items():
        assert set(preset) <= RECOGNIZED_KEYS, name


def test_sub_dicts_have_exact_parameter_names():
    for preset in PRESETS.values():
        if "color" in preset:
            assert set(preset["color"]) == {
                "r_mult", "g_mult", "b_mult", "brightness", "contrast"}
        if "flash_hotspot" in preset:
            assert set(preset["flash_hotspot"]) == {
                "cx_ratio", "cy_ratio", "radius_ratio", "strength"}
        if "scanlines" in preset:
            assert set(preset["scanlines"]) == {"spacing", "opacity"}
        if "bloom" in preset:
            assert set(preset["bloom"]) == {"threshold", "radius_ratio", "strength"}
        if "fade" in preset:
            assert set(preset["fade"]) == {"black", "white"}
        if "sharpen" in preset:
            assert set(preset["sharpen"]) == {"radius", "amount"}
        if "chroma_bleed" in preset:
            assert set(preset["chroma_bleed"]) == {"radius_ratio"}


def test_signature_steps():
    assert "flash_hotspot" in PRESETS["flash_night"]
    assert "scanlines" not in PRESETS["flash_night"]
    assert "scanlines" in PRESETS["camcorder_warm"]
    assert "flash_hotspot" not in PRESETS["camcorder_warm"]
    assert "flash_hotspot" in PRESETS["disposable_flash"]
    assert "fade" not in PRESETS["disposable_flash"]  # film keeps deep blacks
    assert "sharpen" in PRESETS["digicam_2000s"]
    assert "jpeg_quality" in PRESETS["digicam_2000s"]
    assert "chroma_bleed" in PRESETS["vhs_tape"]
    assert "scanlines" in PRESETS["vhs_tape"]
    assert PRESETS["cctv"]["saturation"] < 0.3  # near-monochrome
    assert PRESETS["lomo_xpro"]["vignette_strength"] >= 0.6
    assert "fade" in PRESETS["instant_film"]  # milky lifted blacks
