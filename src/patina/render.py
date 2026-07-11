"""The single shared per-frame path: effects pipeline, then overlay chrome.

Both still images and every extracted video frame go through `render_frame`,
so photos and video are guaranteed the exact same look.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Mapping, Optional

from PIL import Image

from patina import effects, overlays


@dataclasses.dataclass(frozen=True)
class RenderOptions:
    """Resolved CLI options that travel with a processing run."""

    preset: str
    timestamp_text: Optional[str] = None  # None = no timestamp
    rec: bool = False
    rec_counter: str = "00:00:06"
    frame_counter: Optional[str] = None
    max_width: Optional[int] = None


def render_frame(
    img: Image.Image,
    preset: Mapping[str, Any],
    *,
    timestamp_text: Optional[str] = None,
    rec_text: Optional[str] = None,
    frame_text: Optional[str] = None,
) -> Image.Image:
    """Apply the preset pipeline, then requested overlays in the fixed order
    REC indicator -> frame counter -> timestamp."""
    out = effects.apply_preset(img, preset)
    if rec_text is not None:
        out = overlays.add_rec_indicator(out, rec_text)
    if frame_text is not None:
        out = overlays.add_frame_counter(out, frame_text)
    if timestamp_text is not None:
        out = overlays.add_timestamp(out, timestamp_text)
    return out
