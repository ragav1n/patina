# patina

A small CLI tool I use to make my photos and videos look like they came off an old digicam or camcorder. Everything runs on your own machine: no uploads, no accounts, nothing phones home.

Twelve looks are built in:

| Preset | What you get |
|---|---|
| `flash_night` | harsh flash photo at night: cool blue cast, bright center, near-black corners, heavy grain |
| `cyberpunk` | neon cyberpunk night: cool base pushed hard to magenta-pink, punchy crisp contrast, glowing highlights, dark corners |
| `low_shine` | dark moody flash: desaturated cool tones, deep contrast, a bright glowing subject against near-black surroundings |
| `camcorder_warm` | photo of a camcorder's LCD: warm brown cast, milky blacks, faint scanlines |
| `y2k_camcorder` | y2k home-video still: washed cool colors, lifted blacks, hazy highlight bloom, soft detail |
| `disposable_flash` | cheap disposable film camera with the flash on: warm punchy color, hot center, dark corners, chunky grain |
| `digicam_2000s` | early-2000s compact digicam indoors, no flash: dim muted color, murky shadows, dingy whites, mushy detail |
| `vhs_tape` | worn VHS tape: color bleeding past edges, washed contrast, scanlines, heavy tape noise |
| `cctv` | surveillance camera: green-gray near-monochrome, crushed contrast, blooming lights, heavy noise |
| `lomo_xpro` | cross-processed lomography: acid green-yellow cast, punchy saturation, heavy dark vignette |
| `instant_film` | instant film print: white paper frame, warm soft image, capped whites, dreamy out-of-focus detail |
| `blurry_aesthetic` | intentionally blurry shot: out-of-focus softness, handheld motion smear, lights melting into glow |

## Install

### 1. You need Python 3.9 or newer

Check what you have:

```
python3 --version        # Windows: py --version
```

If that prints 3.9 or higher, you're set. If it errors or prints something ancient:

- macOS: `brew install python` (get Homebrew from [brew.sh](https://brew.sh) if you don't have it), or grab the installer from [python.org/downloads](https://www.python.org/downloads/)
- Debian/Ubuntu: `sudo apt install python3 python3-pip python3-venv`
- Windows: install from [python.org/downloads](https://www.python.org/downloads/) and tick **"Add Python to PATH"** during setup

### 2. Get the code

```
git clone https://github.com/ragav1n/patina.git
cd patina
```

No git? Click **Code → Download ZIP** on the GitHub page, unzip it, and `cd` into the folder in a terminal.

### 3. Install patina

The easy way — [pipx](https://pipx.pypa.io) or [uv](https://docs.astral.sh/uv/) installs it as a normal command you can run from anywhere, no venv juggling:

```
pipx install .          # or: uv tool install .
```

Or the classic way, inside a virtual environment (you'll need to re-run the `activate` line whenever you open a new terminal):

```
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install .
```

Either way, check it worked:

```
patina --list-presets
```

You should see the twelve looks listed. That's it for photos.

### 4. For videos only: ffmpeg

Videos additionally need ffmpeg on your PATH; photos work without it.

- macOS: `brew install ffmpeg`
- Debian/Ubuntu: `sudo apt install ffmpeg`
- Windows: `choco install ffmpeg` (or `winget install Gyan.FFmpeg`)

Then reopen the terminal and check with `ffmpeg -version`.

## Use it

New to command-line flags? Just run `patina` with nothing after it:

```
patina
```

In a terminal it opens a guided menu — pick a file (drag it in), arrow-key through the looks, optionally add a timestamp, and go. It even prints the equivalent one-line command at the end, so you'll know the flags for next time.

Or drive it directly. Point it at a photo, a video, or a folder of photos:

```
patina photo.HEIC
patina clip.mp4 --preset y2k_camcorder
patina vacation/
```

Not sure which look you want? Run them all and pick by eye:

```
patina photo.HEIC -all
```

Output lands next to the input as `<name>_<preset><ext>`, so `photo.HEIC` becomes `photo_flash_night.HEIC`. A folder becomes `vacation/nostalgia_<preset>/` with the same filenames inside.

It reads `.jpg .jpeg .png .bmp .tiff .webp .heic .heif` images and `.mp4 .mov .avi .mkv .webm .m4v` videos. iPhone HEIC photos keep their rotation, and HEIC in means HEIC out.

Every flag, with an example:

```
patina photo.jpg                            # default preset (flash_night)
patina photo.jpg --preset y2k_camcorder     # pick a look
patina photo.jpg -all                       # every look at once: photo_<preset>.jpg each
patina photo.jpg -all -o looks/             # same, but collected into a folder
patina photo.jpg -o retro.png               # choose output path; extension picks the format
patina photo.jpg --timestamp                # amber corner timestamp, current date/time
patina photo.jpg --timestamp "26/02/'23  02:52"    # or your own text
patina photo.jpg --rec                      # red REC dot + counter, top left
patina photo.jpg --rec --rec-counter 01:23:45      # custom counter text (images only)
patina photo.jpg --frame-counter 100-0085   # clip index, top right (images only)
patina clip.mp4 --rec --max-width 1280      # video: downscale first, much faster
patina --list-presets                       # names + descriptions
```

Keep flags after the filename: `patina --timestamp photo.jpg` reads `photo.jpg` as the timestamp text.

### What happens with video

patina pulls every frame into a temp folder with ffmpeg, filters each frame through the same pipeline as photos, reencodes with H.264, and copies the original audio into the result. If the audio codec does not fit the output container (PCM in `.mp4`, say), it reencodes the audio to AAC and tells you. With `--rec`, the counter follows the clip: frame 300 of a 25 fps video reads `REC 00:00:12`.

Budget around half a gigabyte of temp disk per minute of 1080p30 footage. The temp folder is deleted when the run ends, Ctrl-C included. WebM input works, but H.264 is not allowed inside `.webm`, so the output switches to `.mp4` with a printed note.

## Making your own preset

Every look is a plain dict in `src/patina/presets.py`. Add an entry, and the CLI and `--list-presets` pick it up on the next run. Nothing else needs to change.

```python
"washed_daylight": {
    "description": "Overexposed daylight digicam shot.",
    "render_width": 960,        # process at video resolution, scales to any photo size
    "reduce_scale": 0.6,        # detail loss: smaller = mushier
    "color": {"r_mult": 1.05, "g_mult": 1.0, "b_mult": 0.95,
              "brightness": 1.1, "contrast": 0.9},
    "saturation": 0.7,          # 1 = unchanged, 0 = grayscale
    "vignette_strength": 0.2,   # 0 = none, 1 = black corners
    "bloom": {"threshold": 170, "radius_ratio": 0.02, "strength": 0.5},
    "fade": {"black": 20, "white": 240},   # lifted blacks, capped whites
    "aberration_shift": 1,      # R/B channel offset in pixels
    "grain_sigma": 6,           # noise strength
    "grain_mono": True,         # tape-style luma grain instead of color noise
    # "flash_hotspot": {"cx_ratio": 0.5, "cy_ratio": 0.42,
    #                   "radius_ratio": 0.55, "strength": 0.32},
    # "scanlines": {"spacing": 3, "opacity": 32},
},
```

Skip any key and that step is skipped. The engine always runs steps in the same order (resize, detail, sharpen, motion blur, color, saturation, chroma bleed, hotspot, vignette, bloom, fade, aberration, grain, scanlines, JPEG artifacts, instant frame), so the dict order does not matter. The full key list with comments is at the top of `presets.py` — the newer steps (`sharpen`, `motion_blur`, `chroma_bleed`, `jpeg_quality`, `instant_frame`) all appear in the shipped presets if you want live examples.

## When something breaks

- **`python3: command not found`**: Python isn't installed (or on Windows it's `py` instead of `python3`). See step 1 of the install section.
- **`patina: command not found`**: with the venv install, run `source .venv/bin/activate` first — it's per-terminal. With pipx, run `pipx ensurepath` once and reopen the terminal.
- **"ffmpeg and ffprobe not found on PATH"**: install ffmpeg (commands above) and reopen the terminal. Only video needs it.
- **"HEIC support requires the pillow-heif package"**: `pip install pillow-heif`.
- **"could not read video ... file may be corrupt"**: ffprobe gave up on the file; its actual error is in the parentheses.
- **Grain looks weaker in JPEG output**: JPEG compression smooths noise. patina saves JPEGs at quality 92, or write a PNG with `-o out.png` to keep every speck.
- **Changed the code but the global command behaves the same**: `pipx`/`uv tool` installs are a snapshot — reinstall with `pipx reinstall patina` or `uv tool install --reinstall .`

## Hacking on it

```
pip install -e ".[dev]"
pytest
```

The test suite generates all of its own media (gradients and ffmpeg test patterns), so the repo holds no photos or clips. Video tests skip themselves when ffmpeg is missing.
