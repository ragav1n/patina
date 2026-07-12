"""Preset definitions. To add a new look, add an entry here — nothing else.

Recognized keys (the engine applies them in a fixed order; omit a key to skip
that step):

    render_width        int     process at this width (video-native resolution;
                                effects scale the same on any size photo)
    reduce_scale        float   downsample/upsample factor (small-sensor softness)
    sharpen             dict    radius, amount — unsharp mask with halos
                                (eager in-camera digicam sharpening)
    motion_blur         dict    distance_ratio, angle — directional smear
                                (camera shake during a slow exposure)
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
    instant_frame       dict    thickness_ratio, bottom_ratio — mount on
                                instant-print paper (grows the canvas)

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
        "color": {"r_mult": 1.02, "g_mult": 1.02, "b_mult": 0.94,
                  "brightness": 1.00, "contrast": 1.22},
        "saturation": 1.25,
        "flash_hotspot": {"cx_ratio": 0.5, "cy_ratio": 0.45,
                          "radius_ratio": 0.60, "strength": 0.28},
        "vignette_strength": 0.60,
        "bloom": {"threshold": 205, "radius_ratio": 0.015, "strength": 0.30},
        "grain_sigma": 9,
    },
    "digicam_2000s": {
        "description": "Early-2000s compact digicam indoors, no flash: dim muted "
                       "color, murky shadows, dingy capped whites, soft mushy detail.",
        "render_width": 1024,
        "reduce_scale": 0.60,
        "sharpen": {"radius": 1.5, "amount": 0.5},
        "color": {"r_mult": 0.955, "g_mult": 1.02, "b_mult": 1.05,
                  "brightness": 0.96, "contrast": 1.10},
        "saturation": 0.82,
        "fade": {"black": 18, "white": 208},
        "aberration_shift": 1,
        "grain_sigma": 5,
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
        "grain_sigma": 9,
        "grain_mono": True,
        "scanlines": {"spacing": 3, "opacity": 40},
    },
    "cctv": {
        "description": "Surveillance camera: green-gray near-monochrome, crushed "
                       "contrast, blooming lights, heavy noise, scanlines.",
        "render_width": 640,
        "reduce_scale": 0.60,
        # The strong green cast is mostly cancelled by the desaturation that
        # follows it — these gains are sized so ~30% survives as the tint.
        "color": {"r_mult": 0.82, "g_mult": 1.22, "b_mult": 0.88,
                  "brightness": 1.05, "contrast": 1.25},
        "saturation": 0.30,
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
        # Saturation runs after the grade and amplifies the cast with it, so
        # the tilt stays modest here to land green-yellow, not orange.
        "color": {"r_mult": 0.98, "g_mult": 1.10, "b_mult": 0.93,
                  "brightness": 1.02, "contrast": 1.28},
        "saturation": 1.35,
        "vignette_strength": 0.80,
        "aberration_shift": 2,
        "grain_sigma": 7,
    },
    "instant_film": {
        "description": "Instant film print: white paper frame, warm soft image, "
                       "capped whites, dreamy out-of-focus detail.",
        "render_width": 960,
        "reduce_scale": 0.50,
        "color": {"r_mult": 1.09, "g_mult": 1.00, "b_mult": 0.95,
                  "brightness": 1.00, "contrast": 1.02},
        "saturation": 0.90,
        "vignette_strength": 0.12,
        "bloom": {"threshold": 200, "radius_ratio": 0.025, "strength": 0.35},
        "fade": {"black": 16, "white": 210},
        "grain_sigma": 4,
        "instant_frame": {"thickness_ratio": 0.07, "bottom_ratio": 0.24},
    },
    "blurry_aesthetic": {
        "description": "Intentionally blurry night shot: out-of-focus softness, "
                       "handheld motion smear, lights melting into glow.",
        "render_width": 960,
        "reduce_scale": 0.50,
        "motion_blur": {"distance_ratio": 0.028, "angle": 18},
        "color": {"r_mult": 1.02, "g_mult": 1.00, "b_mult": 1.00,
                  "brightness": 0.94, "contrast": 1.12},
        "saturation": 1.05,
        "bloom": {"threshold": 165, "radius_ratio": 0.035, "strength": 0.75},
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
    "cyberpunk": {
        "description": "Neon cyberpunk night: cool base shoved hard to magenta-pink, "
                       "punchy crisp contrast, glowing highlights, dark corners.",
        # Warmth -100 (cool) + Tint +100 (magenta) from the recipe -> drop green,
        # lift blue; saturation runs after the grade and amplifies the cast.
        "render_width": 1280,
        "sharpen": {"radius": 1.4, "amount": 0.6},
        "color": {"r_mult": 1.02, "g_mult": 0.80, "b_mult": 1.22,
                  "brightness": 1.06, "contrast": 1.22},
        "saturation": 1.20,
        "vignette_strength": 0.45,
        "bloom": {"threshold": 180, "radius_ratio": 0.02, "strength": 0.35},
        "fade": {"black": 10, "white": 232},
        "aberration_shift": 2,
        "grain_sigma": 4,
    },
    "low_shine": {
        "description": "Dark moody flash: desaturated cool tones, deep contrast, a "
                       "bright glowing flash-lit subject against near-black surroundings.",
        # flash_hotspot only brightens, so it's paired with a vignette to sink the
        # surround; highlights +100 in the recipe -> bloom the lit subject.
        "render_width": 1080,
        "sharpen": {"radius": 1.6, "amount": 0.8},
        "color": {"r_mult": 0.96, "g_mult": 1.00, "b_mult": 1.08,
                  "brightness": 0.78, "contrast": 1.34},
        "saturation": 0.72,
        "flash_hotspot": {"cx_ratio": 0.5, "cy_ratio": 0.45,
                          "radius_ratio": 0.55, "strength": 0.28},
        "vignette_strength": 0.42,
        "bloom": {"threshold": 160, "radius_ratio": 0.02, "strength": 0.52},
        "fade": {"black": 12, "white": 255},
        "grain_sigma": 6,
    },
}
