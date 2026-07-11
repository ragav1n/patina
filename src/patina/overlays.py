"""Corner overlay chrome: timestamp, REC indicator, frame counter.

Everything here is built from plain shapes and system monospace text —
deliberately generic, not modeled on any camera maker's actual UI.

Corner assignments (so all three overlays can coexist):
    REC indicator  -> top-left
    frame counter  -> top-right
    timestamp      -> bottom-right
"""

from __future__ import annotations

import functools
from datetime import datetime
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

AMBER = (255, 176, 0)
AMBER_SHADOW = (50, 25, 0)
WHITE = (245, 245, 245)
DARK_SHADOW = (20, 20, 20)
REC_RED = (220, 40, 40)

_FONT_CANDIDATES = (
    # macOS
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    # Windows
    "C:\\Windows\\Fonts\\consola.ttf",
    "C:\\Windows\\Fonts\\cour.ttf",
    # Bare names: Pillow searches common system font directories itself.
    "DejaVuSansMono.ttf",
    "consola.ttf",
)


@functools.lru_cache(maxsize=8)
def load_mono_font(size: int) -> "ImageFont.FreeTypeFont | ImageFont.ImageFont":
    """Best available monospace font; never raises on a font-less system."""
    for candidate in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)  # Pillow >= 10.1: scalable default
    except TypeError:
        return ImageFont.load_default()  # last resort: tiny bitmap font


def default_timestamp_text(now: Optional[datetime] = None) -> str:
    """Digital-clock style, e.g. ``26/02/'23  02:52``."""
    return (now or datetime.now()).strftime("%d/%m/'%y  %H:%M")


def _metrics(img: Image.Image) -> Tuple["ImageFont.FreeTypeFont | ImageFont.ImageFont", int, int, int]:
    size = max(14, img.height // 28)
    margin = max(12, img.width // 40)
    shadow = max(1, size // 14)
    return load_mono_font(size), size, margin, shadow


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[float, float],
    text: str,
    font,
    fill: Tuple[int, int, int],
    shadow_fill: Tuple[int, int, int],
    shadow_offset: int,
) -> None:
    x, y = xy
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_fill)
    draw.text((x, y), text, font=font, fill=fill)


def add_timestamp(img: Image.Image, text: Optional[str] = None) -> Image.Image:
    """Amber digital-clock timestamp in the bottom-right corner."""
    if text is None:
        text = default_timestamp_text()
    font, _, margin, shadow = _metrics(img)
    draw = ImageDraw.Draw(img)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    x = img.width - margin - (right - left)
    y = img.height - margin - (bottom - top)
    _draw_text(draw, (x, y), text, font, AMBER, AMBER_SHADOW, shadow)
    return img


def add_rec_indicator(img: Image.Image, counter: str = "00:00:06") -> Image.Image:
    """Red dot + white ``REC HH:MM:SS`` in the top-left corner."""
    text = "REC " + counter
    font, size, margin, shadow = _metrics(img)
    draw = ImageDraw.Draw(img)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    dot = max(6, int(size * 0.7))
    gap = max(4, size // 2)
    text_x = margin + dot + gap
    text_y = margin
    # Center the dot on the text line.
    center_y = text_y + (top + bottom) / 2.0
    box = (margin, center_y - dot / 2.0, margin + dot, center_y + dot / 2.0)
    draw.ellipse([c + shadow for c in box], fill=DARK_SHADOW)
    draw.ellipse(box, fill=REC_RED)
    _draw_text(draw, (text_x, text_y), text, font, WHITE, DARK_SHADOW, shadow)
    return img


def add_frame_counter(img: Image.Image, text: str) -> Image.Image:
    """White clip/frame index (e.g. ``100-0085``) in the top-right corner."""
    font, _, margin, shadow = _metrics(img)
    draw = ImageDraw.Draw(img)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    x = img.width - margin - (right - left)
    _draw_text(draw, (x, margin), text, font, WHITE, DARK_SHADOW, shadow)
    return img
