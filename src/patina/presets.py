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
    "attack_on_titan": {
        "description": "Viral anime-sky edit: rich teal-blue sky, blown-out glowing "
                       "clouds, punchy contrast and saturation.",
        # Recipe (Snapseed): Selective Color -> Blue, Hue -11; Tune Image ->
        # Brightness +38, Contrast +27, Saturation +83; Bloom Strength +14;
        # Glamour Glow +100. No selective-hue tool here, so the blue push rides
        # on the channel gains instead; the two glow passes fold into one wide,
        # low-threshold bloom.
        "color": {"r_mult": 0.97, "g_mult": 1.02, "b_mult": 1.10,
                  "brightness": 1.18, "contrast": 1.20},
        "saturation": 1.75,
        "bloom": {"threshold": 150, "radius_ratio": 0.045, "strength": 0.60},
    },
    "dark_fantasy": {
        "description": "Moody cinematic Lightroom grade: deep blue-violet sky and "
                       "foliage, glowing warm accents on lit subjects, soft painterly "
                       "detail, coarse grain.",
        # Recipe (Lightroom): Temp 4550K/Tint +20 (cool, slightly magenta WB);
        # Exposure -0.90/Contrast +20/Highlights -8/Shadows +24; Color Grading
        # pushes blue (hue ~240) into shadows, midtones, and highlights alike;
        # Color Mix pulls saturation out of red/orange/yellow/green while
        # lifting cyan; Texture -30/Clarity -30/Dehaze -10; Grain 49/Size
        # 42/Roughness 56. No per-tonal-range grading or per-hue mixer here,
        # so the blue push rides on the channel gains and the warm-hue
        # desaturation rides on the global saturation instead.
        # Retuned against 4 real "after" reference photos (silhouette-at-dusk,
        # cornfield, house-at-dusk, wildflower field): the sky/water/foliage
        # read as rich saturated blue-violet while sunlit surfaces (a house
        # facade, a backlit rim, a pine tree) stay warm pink/cream/rust rather
        # than getting swallowed into the same blue — so the blue push was
        # eased back (b_mult 1.25->1.20, r/g 0.85->0.87/0.88) to leave more of
        # that warmth on lit surfaces, and saturation raised out of "muted"
        # territory (0.95->1.08) since the blues in the refs are vivid, not
        # pastel. Bloom nudged up for the glowing backlit-sun/water-glint look.
        "reduce_scale": 0.82,
        "color": {"r_mult": 0.88, "g_mult": 0.87, "b_mult": 1.20,
                  "brightness": 0.85, "contrast": 1.28},
        "saturation": 1.08,
        "bloom": {"threshold": 195, "radius_ratio": 0.025, "strength": 0.20},
        "fade": {"black": 26, "white": 240},
        "grain_sigma": 12,
        "grain_mono": True,
    },
    "fujifilm": {
        "description": "Warm Fujifilm-style Lightroom recipe: punchy saturated color "
                       "mounted on a white print border, crisp sharpening, fine grain.",
        # Recipe (Lightroom): WB Temp 6600K/Tint +7; Vibrance +25/Saturation +40;
        # Color Grading -> Highlights hue 48/sat 32, Shadows hue 66/sat 30, both
        # Blending 100 (warm yellow-orange highlights, yellow-green shadows);
        # Color Mix -> Yellow hue -5, Orange hue -10 (nudged toward red);
        # Sharpening 40/Radius 1.0/Detail 25; Color noise reduction 25/Detail
        # 50/Smoothness 55; Grain 40/Size 25/Roughness 25. No per-tonal-range
        # grading or per-hue mixer here, so the warm cast rides on the channel
        # gains and the vibrance/saturation boost rides on the global
        # saturation instead.
        # Retuned against 3 real "after" reference photos (a harbor lighthouse,
        # a moored boat, sodas on a shelf): all three are mounted on a uniform
        # white print border, which the recipe screenshots never showed, so
        # `instant_frame` was added with equal side/bottom ratios (unlike
        # `instant_film`'s thick-bottom Polaroid look, this one is even on all
        # sides). The blue cut was also eased (b_mult 0.88->0.93) — the refs'
        # sky and water keep a visible teal-blue undertone rather than going
        # fully warm, the warmth mostly shows up in whites/wood/highlights.
        "sharpen": {"radius": 1.0, "amount": 0.4},
        "color": {"r_mult": 1.05, "g_mult": 1.04, "b_mult": 0.93,
                  "brightness": 1.03, "contrast": 1.12},
        "saturation": 1.30,
        "grain_sigma": 7,
        "grain_mono": True,
        "instant_frame": {"thickness_ratio": 0.045, "bottom_ratio": 0.045},
    },
    "matrix": {
        "description": "Bullet-time Matrix green: heavy green-yellow cast over deep "
                       "crushed shadows, hazy soft detail, coarse grain.",
        # Recipe (Lightroom): WB Tint -40 (green); Color Grading -> Shadows hue
        # 113/sat 100, Midtones hue 67/sat 100, Highlights hue 78/sat 100 (all
        # maxed-out green-yellow), Global hue 58/sat 42; Texture 0/Clarity
        # -37/Dehaze 0; Tone Curve pulls the black point in hard (crushed
        # shadows) with the Green channel curve pulled even harder; Noise
        # Reduction 55; Color Mix -> Yellow hue +66 (toward green), Orange hue
        # -3/sat -24. No per-luminance color grading or per-channel curve
        # here, so the tint rides on the channel gains and the crush rides on
        # brightness+contrast instead.
        # Fit directly against 3 real before/after reference photos (a
        # portrait, a roofline against sky, a building facade): sampling
        # matching patches gave r/g/b gains, brightness, and contrast that
        # reproduce the shadow/midtone crush and the green-yellow cast closely.
        # One thing that fit couldn't explain: both "after" skies started as a
        # similar blue and one lands near-black while the other flips to deep
        # red — that's not reachable by any per-channel linear gain (a fixed
        # r/g/b multiplier can't send the same input hue two different ways),
        # so it's likely a localized sky edit in the source recipe rather than
        # a global setting. Left as green here, like the rest of the frame.
        "reduce_scale": 0.85,
        "color": {"r_mult": 1.00, "g_mult": 1.40, "b_mult": 0.35,
                  "brightness": 0.88, "contrast": 1.22},
        "saturation": 0.90,
        "grain_sigma": 9,
        "grain_mono": True,
    },
    "blue_hour": {
        "description": "Instagram blue-hour Lightroom recipe: any photo pushed into a "
                       "deep saturated blue-cyan cast with glowing highlights and moody "
                       "punchy contrast.",
        # Recipe (Lightroom): WB Temp 5050K/Tint +18/Vibrance 0; Color Grading
        # pushes Shadows (hue 225/sat 62), Midtones (hue 226/sat 75), and
        # Highlights (hue 221/sat 73) all toward the same blue, plus a faint
        # green Global tint (hue 117/sat 14); Color Mix -> Aqua hue+72/sat+39/
        # lum-1, Blue hue+19/sat+22/lum-2; a brightening tone curve (lifted
        # shadows, rolled-off highlights). No per-tonal-range grading or
        # per-hue mixer here, so the all-tonal-range blue push rides on the
        # channel gains — green held near-neutral rather than crushed
        # alongside red, for the cyan-blue lean the Aqua/Global-green pushes
        # give it (vs. dark_fantasy's more even r/g suppression, which reads
        # violet-blue) — and the curve's brightening/rolloff rides on fade.
        "color": {"r_mult": 0.58, "g_mult": 0.82, "b_mult": 1.60,
                  "brightness": 0.88, "contrast": 1.25},
        "saturation": 1.30,
        "bloom": {"threshold": 205, "radius_ratio": 0.02, "strength": 0.30},
        "fade": {"black": 14, "white": 245},
    },
    "dreamcore": {
        "description": "Hazy pastel dreamcore Lightroom recipe: faded cyan-blue cast "
                       "over milky lifted blacks and muted whites, soft hazy detail, "
                       "coarse grain.",
        # Recipe (Lightroom): Temp -52/Tint -11 (cool, faint green); Exposure
        # -0.86/Contrast +17/Highlights -7/Shadows +21/Whites -86/Blacks +58 —
        # a deep flat tone curve, easily the strongest whites-pull of any recipe
        # here, giving muted highlights and milky lifted blacks; Vibrance +24/
        # Saturation +9; Texture -26/Clarity -26/Dehaze -9 (soft and hazy);
        # Vignette -16/Midpoint 26/Roundness +55; Color Grading -> Shadows hue
        # ~325 at high sat (pink-magenta), Midtones hue ~180 (cyan), Highlights
        # hue ~215 (blue), Global hue ~215 at lower sat (blue); Grain 42/Size
        # 42/Roughness 56 (near-identical to dark_fantasy's grain, so grain_sigma
        # is calibrated off that same 12). No per-tonal-range grading here, so
        # the shadows' pink-magenta pull — the opposite direction from the
        # cyan/blue pushed into midtones, highlights, and global alike — can't
        # ride on one flat channel gain; the majority cyan-blue direction wins,
        # with red left less suppressed than a pure blue-violet grade (c.f.
        # dark_fantasy) so some magenta/warmth stays reachable in the shadows.
        # The whites/blacks curve rides on fade, and the clarity/dehaze softness
        # rides on reduce_scale plus a faint bloom.
        "reduce_scale": 0.85,
        "color": {"r_mult": 0.90, "g_mult": 1.03, "b_mult": 1.25,
                  "brightness": 0.94, "contrast": 1.15},
        "saturation": 1.15,
        "vignette_strength": 0.20,
        "bloom": {"threshold": 200, "radius_ratio": 0.025, "strength": 0.18},
        "fade": {"black": 50, "white": 195},
        "grain_sigma": 11,
        "grain_mono": True,
    },
}
