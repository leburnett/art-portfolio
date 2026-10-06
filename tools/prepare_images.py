#!/usr/bin/env python3
"""Turn archive images into web-ready JPEGs for the portfolio site.

    # one image, default size (1600px long edge) -> assets/images/
    python3 tools/prepare_images.py ~/Documents/ART/SCAN/300DPI/IMG_0001.jpg

    # a whole folder, same settings
    python3 tools/prepare_images.py ~/Documents/ART/PHONE

    # crops for the two landing-page grids (600x750, cropped to 4:5)
    python3 tools/prepare_images.py --grid ~/Documents/ART/SCAN/300DPI/owl.jpg

    # see what would happen, write nothing
    python3 tools/prepare_images.py --dry-run ~/Documents/ART/PHONE

What it does to every image:
  * converts to JPEG (HEIC included, via the macOS `sips` tool)
  * resizes: 1600px on the long edge by default, or exactly 600x750 with --grid
  * strips ALL metadata, EXIF GPS included
  * converts to sRGB so browsers render the colour correctly
  * burns a white watermark into the lower left
  * saves progressive, quality 78

Your source files are never touched. Reads are read-only, and a guard refuses
any write that would land inside a folder you passed as input.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageCms, ImageDraw, ImageFilter, ImageFont
except ImportError:
    sys.exit("Pillow is required:  python3 -m pip install --user Pillow")

# ---------------------------------------------------------------- settings

GRID_SIZE   = (600, 750)        # 4:5, ~2x the 252x315 the tile cells render at
DEFAULT_LONG_EDGE = 1600        # covers the gallery at 2x and the lightbox at 1x
QUALITY     = 78
WATERMARK   = "Laura Elizabeth Burnett"

READABLE = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp",
            ".heic", ".heif"}
HEIC     = {".heic", ".heif"}

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Baskerville.ttc",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/Library/Fonts/Arial.ttf",
]

# ---------------------------------------------------------------- loading


def load(path: Path) -> Image.Image:
    """Open an image read-only. HEIC goes via sips into a temp file."""
    if path.suffix.lower() in HEIC:
        if not shutil.which("sips"):
            raise RuntimeError("HEIC needs the macOS `sips` tool, which wasn't found")
        tmpdir = tempfile.mkdtemp(prefix="prep-heic-")
        tmp = Path(tmpdir) / "converted.jpg"
        try:
            subprocess.run(
                ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "100",
                 str(path), "--out", str(tmp)],
                check=True, capture_output=True,
            )
            with Image.open(tmp) as im:
                return im.copy()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"sips could not read it: {e.stderr.decode()[:120]}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    with Image.open(path) as im:      # 'rb' only; never modified
        im.load()
        return im.copy()


def to_srgb(im: Image.Image) -> Image.Image:
    """Browsers assume sRGB. A wide-gamut file renders dull and colour-shifted,
    which matters more on a portfolio of colour work than file size does."""
    profile = im.info.get("icc_profile")
    if profile:
        try:
            src = ImageCms.ImageCmsProfile(__import__("io").BytesIO(profile))
            im = ImageCms.profileToProfile(
                im, src, ImageCms.createProfile("sRGB"), outputMode="RGB")
        except Exception:
            pass                      # unreadable profile: assume sRGB already
    if im.mode != "RGB":
        im = im.convert("RGB")
    return im


# ---------------------------------------------------------------- resizing


def fit_long_edge(im: Image.Image, px: int) -> Image.Image:
    w, h = im.size
    if max(w, h) <= px:
        return im                     # never upscale; it only adds bytes
    scale = px / max(w, h)
    return im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)


def crop_to_ratio(im: Image.Image, size) -> Image.Image:
    """Centre-crop to the target ratio, then resize. The grid cells are 4:5 and
    crop with object-fit: cover anyway — doing it here means you control it."""
    tw, th = size
    target = tw / th
    w, h = im.size
    if w / h > target:                # too wide: trim the sides
        new_w = round(h * target)
        box = ((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h)
    else:                             # too tall: trim top and bottom
        new_h = round(w / target)
        box = (0, (h - new_h) // 2, w, (h - new_h) // 2 + new_h)
    return im.crop(box).resize(size, Image.LANCZOS)


# ---------------------------------------------------------------- watermark


def pick_font(px: int):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, px)
            except Exception:
                continue
    return ImageFont.load_default()


def tracked(draw, xy, text, font, fill, track, stroke=0, stroke_fill=None):
    """Draw with letter-spacing. Pillow has no tracking, so step per glyph —
    it matches the spaced-out lettering used on the site."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill,
                  stroke_width=stroke, stroke_fill=stroke_fill)
        x += draw.textlength(ch, font=font) + track


def watermark(im: Image.Image, text: str) -> Image.Image:
    """White, lower left.

    White alone disappears on pale work — and pastel paintings are usually
    pale. So the strength of the dark outline and shadow behind the glyphs is
    chosen from how bright the image actually is right there, measured before
    anything is drawn. The text stays white either way.
    """
    w, h = im.size
    size  = max(11, round(h * 0.028))
    pad_x = round(w * 0.035)
    pad_y = round(h * 0.032)
    track = max(0.5, size * 0.07)
    font  = pick_font(size)

    text_h = size * 1.2
    pos = (pad_x, h - pad_y - text_h)

    # how light is the area the text will sit on?
    patch = im.convert("L").crop((
        pad_x, int(pos[1]),
        min(w, pad_x + int(w * 0.55)), min(h, int(pos[1] + text_h * 1.3))))
    luma = sum(patch.getdata()) / max(1, len(patch.getdata()))

    if luma > 170:          # pale: needs a real outline to be visible at all
        stroke_a, shadow_a, blur_k = 165, 190, 0.10
    elif luma > 110:        # mid
        stroke_a, shadow_a, blur_k = 120, 150, 0.12
    else:                   # dark: white already reads, keep it light
        stroke_a, shadow_a, blur_k = 70, 110, 0.14

    stroke_w = max(1, round(size * 0.055))

    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    tracked(ImageDraw.Draw(shadow), (pos[0], pos[1] + max(1, size * 0.05)),
            text, font, (0, 0, 0, shadow_a), track,
            stroke=stroke_w, stroke_fill=(0, 0, 0, shadow_a))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(1.2, size * blur_k)))

    top = Image.new("RGBA", im.size, (0, 0, 0, 0))
    tracked(ImageDraw.Draw(top), pos, text, font, (255, 255, 255, 242), track,
            stroke=stroke_w, stroke_fill=(0, 0, 0, stroke_a))

    out = Image.alpha_composite(im.convert("RGBA"), shadow)
    return Image.alpha_composite(out, top).convert("RGB")


# ---------------------------------------------------------------- safety


def guard(dest: Path, inputs):
    """Refuse to write inside anything the user handed us as a source."""
    dest = dest.resolve()
    for src in inputs:
        src = src.resolve()
        root = src if src.is_dir() else src.parent
        if dest == src:
            raise RuntimeError(f"refusing to overwrite the source file: {src}")
        # dest == root is the dangerous one: output lands in the source folder
        # and, because names are kept, a --force run would overwrite originals
        if dest == root or root in dest.parents or root == dest.parent:
            raise RuntimeError(
                f"refusing to write into a source folder: {root}\n"
                f"  pass -o with somewhere else")


# ---------------------------------------------------------------- driver


def gather(inputs, recursive):
    files = []
    for raw in inputs:
        p = Path(raw).expanduser()
        if not p.exists():
            print(f"  skip (not found): {p}")
            continue
        if p.is_dir():
            it = p.rglob("*") if recursive else p.glob("*")
            files += sorted(f for f in it
                            if f.is_file() and f.suffix.lower() in READABLE)
        elif p.suffix.lower() in READABLE:
            files.append(p)
        else:
            print(f"  skip (not an image): {p.name}")
    return files


def main():
    here = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(
        description="Convert images to web-ready JPEGs for the portfolio site.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", metavar="FILE_OR_FOLDER")
    ap.add_argument("-o", "--out", default=str(here / "assets" / "images"),
                    help="output folder (default: assets/images/)")
    ap.add_argument("--grid", action="store_true",
                    help=f"landing-page tile crops: exactly {GRID_SIZE[0]}x{GRID_SIZE[1]}, "
                         "centre-cropped to 4:5")
    ap.add_argument("--size", type=int, default=DEFAULT_LONG_EDGE, metavar="PX",
                    help=f"long edge for non-grid images (default {DEFAULT_LONG_EDGE})")
    ap.add_argument("--quality", type=int, default=QUALITY, metavar="N")
    ap.add_argument("--prefix", default="", help="prepend to each output filename")
    ap.add_argument("--no-watermark", action="store_true")
    ap.add_argument("--watermark-text", default=WATERMARK)
    ap.add_argument("-f", "--force", action="store_true", help="overwrite existing output")
    ap.add_argument("-r", "--recursive", action="store_true")
    ap.add_argument("-n", "--dry-run", action="store_true")
    a = ap.parse_args()

    inputs = [Path(i).expanduser() for i in a.inputs]
    outdir = Path(a.out).expanduser()

    files = gather(a.inputs, a.recursive)
    if not files:
        if not a.recursive and any(Path(i).expanduser().is_dir() for i in a.inputs):
            sys.exit("no images found at the top level — try -r to search subfolders")
        sys.exit("no images found")

    mode = (f"grid {GRID_SIZE[0]}x{GRID_SIZE[1]} (4:5 crop)"
            if a.grid else f"long edge {a.size}px")
    print(f"\n{len(files)} image(s) -> {outdir}")
    print(f"  {mode}, quality {a.quality}, metadata stripped, "
          f"watermark {'off' if a.no_watermark else 'on'}\n")

    if not a.dry_run:
        try:
            guard(outdir, inputs)
        except RuntimeError as e:
            sys.exit(f"STOPPED: {e}")
        outdir.mkdir(parents=True, exist_ok=True)

    done = skipped = failed = 0
    for src in files:
        dest = outdir / f"{a.prefix}{src.stem}.jpg"
        if dest.exists() and not a.force and not a.dry_run:
            print(f"  exists, skipping: {dest.name}  (use -f to overwrite)")
            skipped += 1
            continue
        try:
            im = load(src)
            before = im.size
            im = to_srgb(im)
            im = crop_to_ratio(im, GRID_SIZE) if a.grid else fit_long_edge(im, a.size)
            if not a.no_watermark:
                im = watermark(im, a.watermark_text)

            if a.dry_run:
                print(f"  would write {dest.name:34} {before[0]}x{before[1]} "
                      f"-> {im.size[0]}x{im.size[1]}")
            else:
                # a fresh save with no exif= and no icc_profile= argument is
                # what strips the metadata, GPS included
                im.save(dest, "JPEG", quality=a.quality, optimize=True,
                        progressive=True, subsampling=2)
                kb = dest.stat().st_size / 1024
                print(f"  {dest.name:34} {before[0]}x{before[1]} "
                      f"-> {im.size[0]}x{im.size[1]}  {kb:6.0f} KB")
            done += 1
        except Exception as e:
            print(f"  FAILED {src.name}: {e}")
            failed += 1

    print(f"\n{done} done, {skipped} skipped, {failed} failed")
    if a.dry_run:
        print("(dry run — nothing was written)")


if __name__ == "__main__":
    main()
