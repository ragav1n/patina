"""Preset definitions. To add a new look, add an entry here — nothing else.

Recognized keys (the engine applies them in a fixed order; omit a key to skip
that step):

    render_width        int     process at this width (video-native resolution;
                                effects scale the same on any size photo)
    reduce_scale        float   downsample/upsample factor (small-sensor softness)
    sharpen             dict    radius, amount — unsharp mask with halos
                                (eager in-camera digicam sharpening)
    color               dict    r_mult, g_mult, b_mult, brightness, contrast
    saturation          float   1 = unchanged, 0 = grayscale
    chroma_bleed        dict    radius_ratio — color smears past luma edges
                                (composite video / VHS chroma)
    flash_hotspot       dict    cx_ratio, cy_ratio, radius_ratio, strength
    vignette_strength   float   0 = none, 1 = black corners
    bloom               dict    threshold (luma 0-255), radius_ratio, strength —
                                hazy glow bleeding out of highlights
    fade                dict    black, white — remap [0,255] into [black,white]
                                (lifted milky blacks, capped whites)
    aberration_shift    int     R/B channel offset in pixels
    grain_sigma         float   Gaussian noise strength
    grain_mono          bool    luma-only grain (video tape) vs chroma noise
    scanlines           dict    spacing (rows), opacity (0-255)
    jpeg_quality        int     re-encode at this JPEG quality for real block
                                artifacts (applied at render resolution)

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
    "y2k_camcorder": {
        "description": "Y2K home-video still: washed cool-cast color, lifted "
                       "milky blacks, hazy highlight bloom, soft low-res detail.",
        "render_width": 960,
        "reduce_scale": 0.72,
        "color": {"r_mult": 0.88, "g_mult": 1.05, "b_mult": 1.24,
                  "brightness": 1.02, "contrast": 1.10},
        "saturation": 0.85,
        "vignette_strength": 0.16,
        "bloom": {"threshold": 168, "radius_ratio": 0.02, "strength": 0.55},
        "fade": {"black": 32, "white": 240},
        "aberration_shift": 1,
        "grain_sigma": 6,
        "grain_mono": True,
    },
    "disposable_flash": {
        "description": "Cheap disposable film camera with the flash on: warm punchy "
                       "color, hot center, dark corners, chunky film grain.",
        "render_width": 1280,
        "reduce_scale": 0.85,
        "color": {"r_mult": 1.06, "g_mult": 1.01, "b_mult": 0.93,
                  "brightness": 1.05, "contrast": 1.12},
        "saturation": 1.15,
        "flash_hotspot": {"cx_ratio": 0.5, "cy_ratio": 0.45,
                          "radius_ratio": 0.60, "strength": 0.18},
        "vignette_strength": 0.45,
        "bloom": {"threshold": 205, "radius_ratio": 0.015, "strength": 0.30},
        "grain_sigma": 9,
    },
    "digicam_2000s": {
        "description": "Early-2000s compact digicam: oversharpened halo edges, vivid "
                       "CCD color, purple fringing, blown flash whites, JPEG blocks.",
        "render_width": 1280,
        "reduce_scale": 0.80,
        "sharpen": {"radius": 2.0, "amount": 1.6},
        "color": {"r_mult": 0.99, "g_mult": 1.00, "b_mult": 1.04,
                  "brightness": 1.06, "contrast": 1.12},
        "saturation": 1.25,
        "bloom": {"threshold": 215, "radius_ratio": 0.012, "strength": 0.50},
        "aberration_shift": 2,
        "grain_sigma": 4,
        "jpeg_quality": 68,
    },
    "vhs_tape": {
        "description": "Worn VHS tape: color bleeding past edges, washed contrast, "
                       "scanlines, heavy tape noise, smeared low-res detail.",
        "render_width": 720,
        "reduce_scale": 0.55,
        "color": {"r_mult": 1.03, "g_mult": 1.00, "b_mult": 0.97,
                  "brightness": 1.00, "contrast": 0.90},
        "saturation": 0.80,
        "chroma_bleed": {"radius_ratio": 0.012},
        "fade": {"black": 24, "white": 235},
        "aberration_shift": 2,
        "grain_sigma": 10,
        "grain_mono": True,
        "scanlines": {"spacing": 3, "opacity": 40},
    },
    "cctv": {
        "description": "Surveillance camera: green-gray near-monochrome, crushed "
                       "contrast, blooming lights, heavy noise, scanlines.",
        "render_width": 640,
        "reduce_scale": 0.60,
        "color": {"r_mult": 0.96, "g_mult": 1.08, "b_mult": 0.98,
                  "brightness": 1.05, "contrast": 1.25},
        "saturation": 0.12,
        "vignette_strength": 0.25,
        "bloom": {"threshold": 190, "radius_ratio": 0.018, "strength": 0.50},
        "grain_sigma": 14,
        "grain_mono": True,
        "scanlines": {"spacing": 2, "opacity": 28},
    },
    "lomo_xpro": {
        "description": "Lomography cross-process: oversaturated punchy color with a "
                       "warm-green tilt, deep blacks, heavy dark vignette.",
        "reduce_scale": 0.90,
        "color": {"r_mult": 1.05, "g_mult": 1.03, "b_mult": 0.90,
                  "brightness": 1.02, "contrast": 1.30},
        "saturation": 1.45,
        "vignette_strength": 0.80,
        "aberration_shift": 2,
        "grain_sigma": 7,
    },
    "instant_film": {
        "description": "Instant film print: warm cream cast, milky lifted blacks, "
                       "low contrast, soft glow, gentle grain.",
        "reduce_scale": 0.80,
        "color": {"r_mult": 1.08, "g_mult": 1.00, "b_mult": 0.88,
                  "brightness": 1.06, "contrast": 0.82},
        "saturation": 0.75,
        "vignette_strength": 0.12,
        "bloom": {"threshold": 180, "radius_ratio": 0.02, "strength": 0.40},
        "fade": {"black": 30, "white": 232},
        "grain_sigma": 5,
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
