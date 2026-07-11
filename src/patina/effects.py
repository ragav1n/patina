"""The effects engine: the per-frame pipeline behind every preset.

`apply_preset` is the single place the pipeline order lives. Each step runs
only if its key is present in the preset dict, so presets can include, skip,
and tune steps but never reorder them.

The image is converted to float32 once, processed without intermediate
clipping (the flash hotspot and grain are allowed to overshoot, which clips
like sensor saturation), and converted back to uint8 once at the end.
"""

from __future__ import annotations

import functools
import io
from typing import Any, Mapping, Optional

import numpy as np
from PIL import Image, ImageFilter

# Falloff exponent for the vignette: higher = cleaner center, harder corner crush.
_VIGNETTE_POWER = 2.5

# Rec. 601 luma weights, used by saturation and bloom.
_LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float32)


def apply_preset(
    img: Image.Image,
    preset: Mapping[str, Any],
    rng: Optional[np.random.Generator] = None,
) -> Image.Image:
    """Run the pipeline steps defined by ``preset`` on ``img`` in the fixed order."""
    img = img.convert("RGB")
    orig_size = img.size
    if "render_width" in preset and img.width > preset["render_width"]:
        # Work at a video-native resolution so softness, grain, and bloom look
        # the same on a 12 MP photo as on a small frame; upscaled back at the end.
        scale = preset["render_width"] / img.width
        img = img.resize(
            (preset["render_width"], max(1, round(img.height * scale))),
            Image.Resampling.BILINEAR,
        )
    if "reduce_scale" in preset:
        img = reduce_detail(img, preset["reduce_scale"])
    if "sharpen" in preset:
        img = sharpen(img, **preset["sharpen"])
    arr = np.asarray(img, dtype=np.float32)
    if "color" in preset:
        arr = color_grade(arr, **preset["color"])
    if "saturation" in preset:
        arr = saturate(arr, preset["saturation"])
    if "chroma_bleed" in preset:
        arr = chroma_bleed(arr, **preset["chroma_bleed"])
    if "flash_hotspot" in preset:
        arr = flash_hotspot(arr, **preset["flash_hotspot"])
    if "vignette_strength" in preset:
        arr = vignette(arr, preset["vignette_strength"])
    if "bloom" in preset:
        arr = bloom(arr, **preset["bloom"])
    if "fade" in preset:
        arr = fade(arr, **preset["fade"])
    if "aberration_shift" in preset:
        arr = chromatic_aberration(arr, preset["aberration_shift"])
    if "grain_sigma" in preset:
        arr = add_grain(arr, preset["grain_sigma"], rng=rng,
                        mono=preset.get("grain_mono", False))
    if "scanlines" in preset:
        arr = scanlines(arr, **preset["scanlines"])
    out = Image.fromarray(np.clip(arr, 0.0, 255.0).astype(np.uint8), "RGB")
    if "jpeg_quality" in preset:
        # Compress at render resolution so the block artifacts get upscaled
        # with the frame, the way a low-quality in-camera JPEG really looks.
        out = jpeg_artifacts(out, preset["jpeg_quality"])
    if out.size != orig_size:
        out = out.resize(orig_size, Image.Resampling.BILINEAR)
    return out


def reduce_detail(img: Image.Image, scale: float) -> Image.Image:
    """Downsample then upsample to mimic a small, low-resolution sensor."""
    w, h = img.size
    small = img.resize(
        (max(1, round(w * scale)), max(1, round(h * scale))),
        Image.Resampling.BILINEAR,
    )
    return small.resize((w, h), Image.Resampling.BILINEAR)


def sharpen(img: Image.Image, radius: float, amount: float) -> Image.Image:
    """Unsharp mask with visible halos, like an eager in-camera sharpener.

    Runs right after ``reduce_detail`` so it sharpens the noise-reduced frame
    the way compact digicams did: soft detail with crunchy, ringing edges.
    """
    return img.filter(
        ImageFilter.UnsharpMask(radius=radius, percent=int(amount * 100), threshold=2)
    )


def chroma_bleed(arr: np.ndarray, radius_ratio: float) -> np.ndarray:
    """Smear color past luma edges, like composite video / VHS chroma.

    Luma keeps its resolution; the color difference signal is blurred
    horizontally-and-vertically and re-added, so saturated regions bleed
    over their outlines while edges stay put.
    """
    w = arr.shape[1]
    luma = arr @ _LUMA
    radius = max(1.0, w * radius_ratio)
    for c in range(3):
        # Pillow can only blur uint8 planes, so the signed difference rides
        # on a half-scale +128 carrier; the quantization is invisible here.
        diff_img = Image.fromarray(
            np.clip((arr[..., c] - luma) * 0.5 + 128.0, 0.0, 255.0).astype(np.uint8),
            "L",
        )
        blurred = np.asarray(
            diff_img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32
        )
        arr[..., c] = luma + (blurred - 128.0) * 2.0
    return arr


def jpeg_artifacts(img: Image.Image, quality: int) -> Image.Image:
    """Round-trip through an in-memory JPEG to bake in real block artifacts."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=int(quality))
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def color_grade(
    arr: np.ndarray,
    r_mult: float,
    g_mult: float,
    b_mult: float,
    brightness: float,
    contrast: float,
) -> np.ndarray:
    """Per-channel gain, then brightness, then contrast pivoted at mid-gray.

    The pivot is a fixed 128 rather than the image mean so the grade is
    content-independent and identical across every frame of a video.
    """
    arr *= np.array([r_mult, g_mult, b_mult], dtype=np.float32) * np.float32(brightness)
    arr -= 128.0
    arr *= np.float32(contrast)
    arr += 128.0
    return arr


@functools.lru_cache(maxsize=8)
def _hotspot_mask(
    w: int, h: int, cx_ratio: float, cy_ratio: float, radius_ratio: float
) -> np.ndarray:
    xx = np.arange(w, dtype=np.float32)[None, :]
    yy = np.arange(h, dtype=np.float32)[:, None]
    d = np.sqrt((xx - np.float32(cx_ratio * w)) ** 2 + (yy - np.float32(cy_ratio * h)) ** 2)
    d /= np.float32(radius_ratio * max(w, h))
    return np.clip(1.0 - d, 0.0, 1.0) ** 2


def flash_hotspot(
    arr: np.ndarray,
    cx_ratio: float,
    cy_ratio: float,
    radius_ratio: float,
    strength: float,
) -> np.ndarray:
    """Additive radial glow — a flash adds light, so even dark pixels bloom."""
    h, w = arr.shape[:2]
    mask = _hotspot_mask(w, h, cx_ratio, cy_ratio, radius_ratio)
    arr += np.float32(strength * 255.0) * mask[..., None]
    return arr


@functools.lru_cache(maxsize=8)
def _vignette_mask(w: int, h: int, strength: float) -> np.ndarray:
    cx, cy = w / 2.0, h / 2.0
    xx = np.arange(w, dtype=np.float32)[None, :]
    yy = np.arange(h, dtype=np.float32)[:, None]
    # Elliptical distance: 0 at center, 1.0 at the exact corners.
    d = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / np.float32(np.sqrt(2.0))
    return np.clip(1.0 - np.float32(strength) * d ** np.float32(_VIGNETTE_POWER), 0.0, 1.0)


def vignette(arr: np.ndarray, strength: float) -> np.ndarray:
    h, w = arr.shape[:2]
    arr *= _vignette_mask(w, h, float(strength))[..., None]
    return arr


def _shift_columns(channel: np.ndarray, shift: int) -> np.ndarray:
    """Shift columns by ``shift`` px (positive = right), repeating the edge column.

    Edge-clamped on purpose: np.roll would wrap the opposite edge into frame.
    """
    if shift == 0 or abs(shift) >= channel.shape[1]:
        return channel
    out = np.empty_like(channel)
    if shift > 0:
        out[:, shift:] = channel[:, :-shift]
        out[:, :shift] = channel[:, :1]
    else:
        out[:, :shift] = channel[:, -shift:]
        out[:, shift:] = channel[:, -1:]
    return out


def chromatic_aberration(arr: np.ndarray, shift: int) -> np.ndarray:
    """Offset R and B channels a few pixels in opposite directions."""
    shift = int(shift)
    arr[..., 0] = _shift_columns(arr[..., 0], shift)
    arr[..., 2] = _shift_columns(arr[..., 2], -shift)
    return arr


def saturate(arr: np.ndarray, amount: float) -> np.ndarray:
    """Scale color away from (amount > 1) or toward (amount < 1) per-pixel luma."""
    luma = arr @ _LUMA
    arr *= np.float32(amount)
    arr += (np.float32(1.0 - amount) * luma)[..., None]
    return arr


def bloom(
    arr: np.ndarray, threshold: float, radius_ratio: float, strength: float
) -> np.ndarray:
    """Halation: bright areas glow and bleed into their surroundings.

    Luma above ``threshold`` is extracted, Gaussian-blurred, and screened back
    toward white — blown skies melt outward, highlights haze over their edges.
    """
    w = arr.shape[1]
    luma = arr @ _LUMA
    highlights = np.clip(
        (luma - threshold) / max(1.0, 255.0 - threshold), 0.0, 1.0
    )
    hl_img = Image.fromarray((highlights * 255.0).astype(np.uint8), "L")
    radius = max(1.0, w * radius_ratio)
    glow = np.asarray(
        hl_img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32
    ) / 255.0
    mask = np.clip(glow * np.float32(strength), 0.0, 1.0)
    arr += (255.0 - arr) * mask[..., None]
    return arr


def fade(arr: np.ndarray, black: float, white: float) -> np.ndarray:
    """Compress [0, 255] into [black, white]: lifted milky blacks, capped whites."""
    arr *= np.float32((white - black) / 255.0)
    arr += np.float32(black)
    return arr


def add_grain(
    arr: np.ndarray,
    sigma: float,
    rng: Optional[np.random.Generator] = None,
    mono: bool = False,
) -> np.ndarray:
    """Gaussian pixel noise, fresh on every call so video grain moves per frame.

    ``mono`` applies the same noise to all three channels (luma-only grain,
    video-tape-like) instead of independent per-channel chroma noise.
    """
    if rng is None:
        rng = np.random.default_rng()
    shape = arr.shape[:2] + ((1,) if mono else (3,))
    arr += rng.standard_normal(shape, dtype=np.float32) * np.float32(sigma)
    return arr


def scanlines(arr: np.ndarray, spacing: int, opacity: int) -> np.ndarray:
    """Darken every ``spacing``-th row by ``opacity``/255."""
    arr[:: int(spacing)] *= np.float32(1.0 - opacity / 255.0)
    return arr
