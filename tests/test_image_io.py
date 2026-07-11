from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from patina import image_io
from patina.errors import PatinaError
from patina.render import RenderOptions

from conftest import gradient_array

OPTS = RenderOptions(preset="flash_night")


def test_default_output_naming(jpg_path):
    out = image_io.process_image(jpg_path, None, OPTS)
    assert out == jpg_path.with_name("photo_flash_night.jpg")
    assert out.exists()


def test_output_format_matches_input(png_path):
    out = image_io.process_image(png_path, None, OPTS)
    assert out.suffix == ".png"
    with Image.open(out) as img:
        assert img.format == "PNG"


def test_explicit_output_overrides_format(jpg_path, tmp_path):
    out = image_io.process_image(jpg_path, tmp_path / "retro.png", OPTS)
    with Image.open(out) as img:
        assert img.format == "PNG"


def test_output_to_existing_directory(jpg_path, tmp_path):
    target = tmp_path / "outdir"
    target.mkdir()
    out = image_io.process_image(jpg_path, target, OPTS)
    assert out == target / "photo_flash_night.jpg"
    assert out.exists()


def test_exif_orientation_is_applied(tmp_path):
    path = tmp_path / "rotated.jpg"
    img = Image.fromarray(gradient_array(w=100, h=60), "RGB")
    exif = Image.Exif()
    exif[0x0112] = 6  # "rotate 90 CW to display"
    img.save(path, exif=exif)
    loaded = image_io.load_image(path)
    assert loaded.size == (60, 100)  # transposed on load


def test_rgba_and_palette_inputs_normalize(tmp_path):
    rgba = Image.new("RGBA", (40, 30), (200, 10, 10, 128))
    rgba_path = tmp_path / "img.png"
    rgba.save(rgba_path)
    assert image_io.load_image(rgba_path).mode == "RGB"
    pal = Image.new("P", (40, 30))
    pal_path = tmp_path / "pal.png"
    pal.save(pal_path)
    assert image_io.load_image(pal_path).mode == "RGB"


def test_heic_round_trip(tmp_path):
    pytest.importorskip("pillow_heif")
    src = tmp_path / "photo.heic"
    Image.fromarray(gradient_array(), "RGB").save(src)
    out = image_io.process_image(src, None, OPTS)
    assert out == tmp_path / "photo_flash_night.heic"
    with Image.open(out) as img:
        assert img.size == (160, 120)


def test_unreadable_image_is_clean_error(tmp_path):
    bad = tmp_path / "fake.jpg"
    bad.write_bytes(b"not an image at all")
    with pytest.raises(PatinaError, match="cannot read image"):
        image_io.load_image(bad)


def test_batch_directory(tmp_path):
    for name in ("a.jpg", "b.png", "c.jpg"):
        Image.fromarray(gradient_array(), "RGB").save(tmp_path / name)
    (tmp_path / "notes.txt").write_text("skip me")
    (tmp_path / ".hidden.jpg").write_bytes(b"skip me too")
    written = image_io.process_directory(tmp_path, None, OPTS)
    out_dir = tmp_path / "nostalgia_flash_night"
    assert out_dir.is_dir()
    assert sorted(p.name for p in written) == ["a.jpg", "b.png", "c.jpg"]
    assert all(p.parent == out_dir for p in written)


def test_batch_skips_corrupt_file_and_continues(tmp_path, capsys):
    Image.fromarray(gradient_array(), "RGB").save(tmp_path / "good.jpg")
    (tmp_path / "bad.jpg").write_bytes(b"garbage")
    written = image_io.process_directory(tmp_path, None, OPTS)
    assert [p.name for p in written] == ["good.jpg"]
    assert "skipped bad.jpg" in capsys.readouterr().err


def test_batch_empty_directory_errors(tmp_path):
    with pytest.raises(PatinaError, match="no supported images"):
        image_io.process_directory(tmp_path, None, OPTS)


def test_overlays_reach_the_saved_file(jpg_path):
    with_chrome = RenderOptions(
        preset="camcorder_warm", rec=True, rec_counter="00:00:06",
        frame_counter="100-0085", timestamp_text="26/02/'23  02:52",
    )
    out = image_io.process_image(jpg_path, None, with_chrome)
    arr = np.asarray(Image.open(out).convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    corner = arr[: h // 4, : w // 3]
    redness = corner[..., 0] - (corner[..., 1] + corner[..., 2]) / 2
    assert redness.max() > 80  # REC dot survived the save
