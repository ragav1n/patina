from __future__ import annotations

from patina.presets import PRESETS

RECOGNIZED_KEYS = {
    "description", "reduce_scale", "color", "flash_hotspot",
    "vignette_strength", "aberration_shift", "grain_sigma", "scanlines",
}


def test_two_presets_ship():
    assert set(PRESETS) == {"flash_night", "camcorder_warm"}


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


def test_signature_steps():
    assert "flash_hotspot" in PRESETS["flash_night"]
    assert "scanlines" not in PRESETS["flash_night"]
    assert "scanlines" in PRESETS["camcorder_warm"]
    assert "flash_hotspot" not in PRESETS["camcorder_warm"]
