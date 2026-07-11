# patina

Applies an old digicam / camcorder look to photos and videos from the command line. Nothing leaves your machine: no uploads, no telemetry. The dependencies are Pillow, NumPy, pillow-heif, and, for video only, the ffmpeg binaries.

Two looks ship with it:

- `flash_night`: an indoor photo taken at night with on-camera flash. Cool blue-purple cast, a bright hotspot mid-frame, corners falling off to near-black, heavy grain, optional amber timestamp.
- `camcorder_warm`: a photo of a camcorder's flip-out LCD during playback. Warm brown cast, milky blacks, faint horizontal scanlines, soft detail, optional REC dot and clip counter.

## Install

Requires Python 3.9 or newer.

    git clone https://github.com/ragav1n/patina.git
    cd patina
    python3 -m venv .venv && source .venv/bin/activate
    pip install .

Video processing also needs ffmpeg and ffprobe on your PATH:

| OS | Command |
|---|---|
| macOS | `brew install ffmpeg` |
| Debian/Ubuntu | `sudo apt install ffmpeg` |
| Windows | `choco install ffmpeg` (or `winget install Gyan.FFmpeg`) |

Photos work without ffmpeg.

## Usage

    patina INPUT [options]

`INPUT` is an image (`.jpg .jpeg .png .bmp .tiff .webp .heic .heif`), a video (`.mp4 .mov .avi .mkv .webm .m4v`), or a folder of images. Output lands next to the input as `<name>_<preset><ext>` unless you pass `-o`. Run `patina` with no arguments for the full help.

One example per flag:

    patina photo.jpg                            # flash_night -> photo_flash_night.jpg
    patina photo.heic --preset camcorder_warm   # pick the look; HEIC in, HEIC out
    patina photo.jpg -o retro.png               # choose the output path and format
    patina vacation/                            # folder -> vacation/nostalgia_flash_night/
    patina photo.jpg --timestamp                # stamp the current date/time
    patina photo.jpg --timestamp "26/02/'23  02:52"    # stamp custom text
    patina photo.jpg --rec                      # red REC dot + counter, top left
    patina photo.jpg --rec --rec-counter 01:23:45      # custom counter (images only)
    patina photo.jpg --frame-counter 100-0085   # clip index, top right (images only)
    patina clip.mp4 --rec --max-width 1280      # video: downscale first for speed
    patina --list-presets                       # names and descriptions of the looks

Keep flags after the filename. `patina --timestamp photo.jpg` reads `photo.jpg` as the timestamp text.

### Video notes

patina extracts every frame to a temp folder, filters each one through the same pipeline as photos, reencodes with H.264, and copies the original audio into the result. If the audio codec does not fit the output container (PCM in `.mp4`, for example), patina reencodes the audio to AAC and prints a note. With `--rec`, the counter runs with the clip: frame 300 of a 25 fps video reads `REC 00:00:12`.

Expect around half a gigabyte of temp disk per minute of 1080p30 footage. patina removes the temp folder when processing ends, including on Ctrl-C.

WebM input works, but H.264 is not allowed inside a `.webm` file, so the default output switches to `.mp4` and patina prints a note.

## Adding a preset

Open `src/patina/presets.py` and add an entry to `PRESETS`. That is the whole job: the CLI accepts the new name on the next run and `--list-presets` shows it.

```python
"washed_daylight": {
    "description": "Overexposed daylight digicam shot.",
    "reduce_scale": 0.5,        # detail loss: smaller = mushier
    "color": {"r_mult": 1.05, "g_mult": 1.0, "b_mult": 0.95,
              "brightness": 1.15, "contrast": 0.85},
    "vignette_strength": 0.2,   # 0 = none, 1 = black corners
    "aberration_shift": 1,      # R/B channel offset in pixels
    "grain_sigma": 6,           # noise strength
    # "flash_hotspot": {"cx_ratio": 0.5, "cy_ratio": 0.42,
    #                   "radius_ratio": 0.55, "strength": 0.32},
    # "scanlines": {"spacing": 3, "opacity": 32},
},
```

Omit a key and the engine skips that step. Steps run in a fixed order regardless of how you write the entry: detail reduction, color grade, flash hotspot, vignette, chromatic aberration, grain, scanlines.

## Troubleshooting

**"ffmpeg and ffprobe not found on PATH"**: install ffmpeg (commands above) and reopen your terminal. Photos do not need it.

**"HEIC support requires the pillow-heif package"**: run `pip install pillow-heif`. Wheels exist for macOS, Linux, and Windows.

**"could not read video ... file may be corrupt"**: ffprobe could not parse the file. The underlying ffmpeg error rides along in parentheses.

**Grain looks smoother than expected in JPEG output**: JPEG compression eats fine noise. patina saves JPEGs at quality 92; write PNG with `-o out.png` if you want the grain untouched.

## Development

    pip install -e ".[dev]"
    pytest

The test suite generates all of its own media (gradient images and ffmpeg test patterns), so no photos or clips live in the repo. Video tests skip when ffmpeg is absent.
