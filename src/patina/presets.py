"""Preset definitions. To add a new look, add an entry here — nothing else.

Recognized keys (the engine applies them in a fixed order; omit a key to skip
that step):

    reduce_scale        float   downsample/upsample factor (small-sensor softness)
    color               dict    r_mult, g_mult, b_mult, brightness, contrast
    flash_hotspot       dict    cx_ratio, cy_ratio, radius_ratio, strength
    vignette_strength   float   0 = none, 1 = black corners
    aberration_shift    int     R/B channel offset in pixels
    grain_sigma         float   Gaussian noise strength
    scanlines           dict    spacing (rows), opacity (0-255)

"description" is metadata shown by --list-presets only.
"""

from __future__ import annotations

from typing import Any, Dict

PRESETS: Dict[str, Dict[str, Any]] = {
    "flash_night": {
        "description": "Indoor night photo with harsh on-camera flash: cool blue-purple "
                       "cast, bright center hotspot, near-black vignetted edges, heavy grain.",
        "reduce_scale": 0.42,
        "color": {"r_mult": 0.90, "g_mult": 1.00, "b_mult": 1.20,
                  "brightness": 0.82, "contrast": 1.18},
        "flash_hotspot": {"cx_ratio": 0.5, "cy_ratio": 0.42,
                          "radius_ratio": 0.55, "strength": 0.32},
        "vignette_strength": 0.78,
        "aberration_shift": 2,
        "grain_sigma": 13,
    },
    "camcorder_warm": {
        "description": "Photo of a camcorder's LCD during playback: warm brown cast, "
                       "milky low contrast, faint horizontal scanlines, soft detail.",
        "reduce_scale": 0.5,
        "color": {"r_mult": 1.12, "g_mult": 1.02, "b_mult": 0.86,
                  "brightness": 1.02, "contrast": 0.90},
        "vignette_strength": 0.32,
        "aberration_shift": 1,
        "grain_sigma": 8,
        "scanlines": {"spacing": 3, "opacity": 32},
    },
}
