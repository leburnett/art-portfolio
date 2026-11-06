#!/usr/bin/env python3
"""Rebuild a gallery page from a folder of original photographs.

One command does the whole job: converts the originals to web JPEGs, numbers
them, and rewrites the <section class="gallery"> block of the page so the
markup always matches the files on disk.

    python3 tools/build_gallery.py pastels
    python3 tools/build_gallery.py relief
    python3 tools/build_gallery.py all

Run it from the repository root. It is safe to run as often as you like — it
rebuilds from the originals every time, so the result does not depend on what
was there before.

WHEN YOU NEED IT
----------------
Any time the contents of an originals folder change: a photo added, removed,
replaced or RENUMBERED. The page lists images in the numeric order of the
source filenames, so renumbering is how you reorder the page.

WHAT IT KEEPS IN STEP
---------------------
Three things have to agree for a page to look right, and keeping them in step
by hand is where mistakes creep in:

  * the image files and their numbering;
  * width/height on every <img>, which reserve the right space while the image
    loads so the page does not jump;
  * --ar on every <figure>, the aspect ratio the justified rows are built from.

A stale --ar does not throw an error. It just quietly stops the rows lining up,
which is easy to miss and hard to explain later. This script regenerates all
three together, so they cannot drift apart.

WHAT IT DOES NOT TOUCH
----------------------
Everything outside the gallery block: the page heading, the intro paragraph,
the navbar and the news bar are all left exactly as they are. Captions and alt
text are NOT preserved, because the figures are rebuilt from scratch — see the
warning the script prints if it is about to overwrite any.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("This needs Pillow:  python3 -m pip install --user Pillow")

ROOT = Path(__file__).resolve().parent.parent
PREPARE = ROOT / "tools" / "prepare_images.py"

# Web export settings. These match the rest of the site: 1200px is about twice
# the largest size the gallery ever displays, which is what a Retina screen
# needs and no more than that — see CLAUDE.md, "On protecting the work".
LONG_EDGE = 1200
QUALITY = 72

GALLERIES = {
    "relief": {
        "src": "assets/images/prints",
        "out": "assets/images/relief",
        "page": "relief-printing.html",
        "noun": "relief prints",
        "caption": "Linocut, 2026 &middot; 297 &times; 420 mm",
    },
    "pastels": {
        "src": "assets/images/oilpastels",
        "out": "assets/images/pastels",
        "page": "oil-pastels.html",
        "noun": "oil pastel pieces",
        "caption": "Oil pastel on paper, 2026 &middot; 300 &times; 300 mm",
    },
}

ALT_PLACEHOLDER = "FILLER — describe this piece: subject, colours, mood."

# How full each row is, as a running total of aspect ratios, applied in order
# and repeating.
#
# A row is justified across the full width, so its HEIGHT is roughly
#     (width - gaps) / (sum of the row's aspect ratios).
# A row holding little width-per-height — two portraits, say — comes out tall;
# a row of several landscapes comes out short. Varying this total is therefore
# how the page stops looking like a grid, and it is the ONLY safe place to vary
# it: every image inside a row must stay the same height, which happens only
# when they all share one target.
#
# An earlier attempt gave each IMAGE its own size weight. That cannot work.
# flex-grow shares out the leftover space, not the total width, so a width is
# proportional to its aspect ratio only when every item in the row carries the
# same weight. With per-image weights the row stopped being justified and the
# heights inside it scattered.
#
# Fixed, not random, so rebuilding twice gives the same page. Lower = taller
# row, higher = shorter row. Roughly 2.0 to 4.6 is the usable range.
ROW_TARGETS = [3.0, 2.2, 3.9, 2.7, 4.4, 2.4, 3.4, 3.0, 2.1, 4.1, 2.8, 3.6]


def number_of(path: Path) -> int:
    """The leading number in a filename, which sets the order on the page.

    Zero padding in the source is inconsistent — 01 next to 010 — so the name
    is read as a NUMBER rather than sorted as text, where '010' would land
    between '01' and '02'.
    """
    m = re.match(r"0*(\d+)", path.stem)
    if not m:
        raise SystemExit(f"{path.name}: filename does not start with a number")
    return int(m.group(1))


def convert(src: Path, scratch: Path) -> None:
    """Hand the originals to prepare_images.py, which owns all the image work:
    HEIC decoding, EXIF orientation, sRGB, metadata stripping, resizing."""
    cmd = [sys.executable, str(PREPARE), "--no-watermark",
           "--size", str(LONG_EDGE), "--quality", str(QUALITY),
           "-o", str(scratch), str(src)]
    print("  " + " ".join(cmd[1:]))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit("prepare_images.py failed; nothing was changed")


def install(scratch: Path, out: Path) -> list[Path]:
    """Copy the converted files into place under a two-digit number.

    The output folder is emptied of .jpg first, so a number removed from the
    originals does not leave an orphan behind. Only this folder is touched, and
    only files this script generates.
    """
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.jpg"):
        stale.unlink()
    installed = []
    for p in sorted(scratch.glob("*.jpg"), key=number_of):
        target = out / f"{number_of(p):02d}.jpg"
        shutil.copy2(p, target)
        installed.append(target)
    return installed


def group_into_rows(images: list[Path]) -> list[list[tuple[Path, float]]]:
    """Chop the ordered images into rows, filling each to its own target.

    Greedy and strictly in order, so the numbering still reads left to right
    and then down. A row is closed as soon as it reaches its target, which is
    why rows end up holding anywhere from two to six images and why their
    heights differ.
    """
    rows, row, total, n = [], [], 0.0, 0
    for p in images:
        w, h = Image.open(p).size
        ar = w / h
        row.append((p, ar))
        total += ar
        target = ROW_TARGETS[n % len(ROW_TARGETS)]
        # A single image is never a row of its own: justified, it would fill
        # the whole width and tower over everything around it.
        if (total >= target and len(row) >= 2) or len(row) >= 6:
            rows.append(row)
            row, total, n = [], 0.0, n + 1
    if row:
        rows.append(row)          # the remainder; not justified, see below
    return rows


def figures(row: list[tuple[Path, float]], last: bool) -> str:
    out = []
    for p, ar in row:
        w, h = Image.open(p).size
        out.append(
            f'      <figure class="piece" style="--ar: {ar:.4f}">\n'
            f'        <img src="{p.relative_to(ROOT).as_posix()}" loading="lazy" '
            f'width="{w}" height="{h}"\n'
            f'             alt="{ALT_PLACEHOLDER}">\n'
            f'      </figure>'
        )
    cls = "gallery__row gallery__row--last" if last else "gallery__row"
    return f'    <div class="{cls}">\n' + "\n".join(out) + "\n    </div>"


def gallery_html(cfg: dict, images: list[Path]) -> str:
    rows = group_into_rows(images)
    return (
        '  <!-- ===================================================================\n'
        f'       {len(images)} {cfg["noun"]} in {len(rows)} rows, in the numeric order of\n'
        f'       the source filenames in {cfg["src"]}/.\n'
        '\n'
        '       THIS BLOCK IS GENERATED. Do not hand-edit it — the next build\n'
        '       will overwrite whatever you put here. To change what appears,\n'
        '       change the originals and run:\n'
        '\n'
        f'         python3 tools/build_gallery.py {cfg["key"]}\n'
        '\n'
        '       To reorder, renumber the originals. To remove a piece, take it\n'
        '       out of the source folder. Both then rebuild cleanly.\n'
        '\n'
        '       CAPTIONS are not written yet. When you want them, the honest\n'
        '       way is to stop generating this block: delete this comment, and\n'
        '       the file becomes ordinary hand-edited HTML again. A caption\n'
        '       goes inside the figure, after the <img>:\n'
        f'         <figcaption><strong>Title</strong><br>{cfg["caption"]}</figcaption>\n'
        '       The lightbox picks it up automatically.\n'
        '       =================================================================== -->\n'
        '  <section class="gallery wrap">\n\n'
        + "\n\n".join(
            figures(row, last=(i == len(rows) - 1 and len(rows) > 1))
            for i, row in enumerate(rows))
        + '\n\n  </section>'
    )


def splice(page: Path, block: str) -> None:
    """Replace the gallery block, leaving the rest of the page untouched.

    The replaced region runs from the start of the HTML comment immediately
    above <section class="gallery"> — if one is there, which is how the
    generated block is marked — through its closing </section>. Anything
    further up the page (heading, intro paragraph, navbar) is not read, not
    rewritten, and cannot be lost.
    """
    s = page.read_text()
    open_tag = s.find('<section class="gallery')
    if open_tag == -1:
        raise SystemExit(f'{page.name}: no <section class="gallery"> to replace')
    close_tag = s.index("</section>", open_tag) + len("</section>")

    start = s.rfind("\n", 0, open_tag) + 1      # default: the section's own line
    end_of_comment = s.rfind("-->", 0, open_tag)
    if end_of_comment != -1 and s[end_of_comment + 3:open_tag].strip() == "":
        begin = s.rfind("<!--", 0, end_of_comment)
        if begin != -1:
            start = s.rfind("\n", 0, begin) + 1

    page.write_text(s[:start] + block + s[close_tag:])


def warn_about_losses(page: Path, assume_yes: bool) -> None:
    s = page.read_text()
    # Comments are stripped first. The generated block carries an EXAMPLE
    # <figcaption> in its comment to show where one goes, and counting that as
    # real work would make this warning cry wolf on every single run.
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    captions = s.count("<figcaption>")
    real_alt = len(re.findall(r'alt="(?!FILLER)[^"]{3,}"', s))
    if captions:
        print(f"  ! {page.name} has {captions} <figcaption>(s). Rebuilding "
              "discards them.")
    if real_alt:
        print(f"  ! {page.name} has {real_alt} image(s) with written alt text. "
              "Rebuilding discards it.")
    if (captions or real_alt) and not assume_yes:
        print("    Stop now if that is not what you want, or copy them "
              "somewhere first.")
        input("    Press return to continue, ctrl-C to abort: ")


def build(key: str, assume_yes: bool = False, html_only: bool = False) -> None:
    cfg = dict(GALLERIES[key], key=key)
    src, out, page = (ROOT / cfg["src"]), (ROOT / cfg["out"]), (ROOT / cfg["page"])

    print(f"\n{key}: {cfg['src']} -> {cfg['out']} -> {cfg['page']}")
    originals = []
    if not html_only:
        if not src.is_dir():
            print(f"  skipped: {cfg['src']} does not exist. The originals are "
                  f"not kept in the repo —\n           put them back, or pass "
                  f"--html-only to rebuild the markup from\n           the web "
                  f"images already in {cfg['out']}.")
            return
        originals = [p for p in src.iterdir()
                     if p.is_file() and not p.name.startswith(".")]
        if not originals:
            print(f"  skipped: {cfg['src']} is empty")
            return

    warn_about_losses(page, assume_yes)

    if html_only:
        images = sorted(out.glob("*.jpg"), key=number_of)
        if not images:
            print(f"  skipped: {cfg['out']} has no images to rebuild from")
            return
        print(f"  --html-only: reusing the {len(images)} images already in "
              f"{cfg['out']}")
    else:
        with tempfile.TemporaryDirectory(prefix="gallery-") as tmp:
            scratch = Path(tmp)
            convert(src, scratch)
            images = install(scratch, out)

    splice(page, gallery_html(cfg, images))
    total = sum(p.stat().st_size for p in images) / 1e6
    if originals:
        source = sum(p.stat().st_size for p in originals) / 1e6
        print(f"  {len(images)} images, {source:.0f} MB -> {total:.1f} MB")
    else:
        print(f"  {len(images)} images, {total:.1f} MB")
    print(f"  numbers: {', '.join(p.stem for p in images)}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Rebuild a gallery page from its folder of originals.",
        epilog="Run from the repository root.")
    ap.add_argument("which", nargs="+", choices=list(GALLERIES) + ["all"],
                    help="which gallery to rebuild")
    ap.add_argument("--html-only", action="store_true",
                    help="do not touch the images; rebuild the page's markup "
                         "from the web images already on disk. Use this when "
                         "the originals are no longer around, or after "
                         "changing how rows are grouped.")
    ap.add_argument("-y", "--yes", action="store_true",
                    help="do not stop to confirm when captions or written alt "
                         "text are about to be discarded")
    a = ap.parse_args()

    keys = list(GALLERIES) if "all" in a.which else a.which
    for key in keys:
        build(key, a.yes, a.html_only)
    print("\nDone. Check the page, then commit the new images and HTML.")


if __name__ == "__main__":
    main()
