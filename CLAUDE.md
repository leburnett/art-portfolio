# Laura Elizabeth Burnett — artist portfolio site

Handoff notes, written 23 October 2026. Read this to get up to speed on the
project without the original chat.

---

## What this is

A static portfolio website for an artist working in **oil pastel** and **relief
print (linocut)**. Four hand-written HTML pages, one stylesheet, one small
script. **No build step, no framework, no dependencies.** Open any `.html` in a
browser and it works.

It does **not** sell anything. That was a deliberate decision — a shop may come
later, but v1 is a portfolio only.

### Where everything lives

| | |
|---|---|
| **Site code** | `~/Documents/GitHub/art-portfolio` |
| **GitHub** | `github.com/leburnett/art-portfolio` — **private** |
| **Source photographs** | `~/Documents/ART_PORTFOLIO/{grid_images, linocut_images, oil_pastel_images}` |
| **Instagram** | [@elbe.elbe.elbe](https://www.instagram.com/elbe.elbe.elbe/) — linked from an inline-SVG icon at the end of every navbar |
| **About portrait source** | `~/Documents/ART_PORTFOLIO/portrait-v2.jpg` — the retouched cut-out, already flattened onto white. The older `portrait.png` is superseded. |
| **Catalogue database** | `~/Documents/ART/books` — a 13-table Grist catalogue (SKUs, print runs, stock, UK bookkeeping). Read its `SCHEMA.md`. |
| **Original research + plan** | `~/Documents/ART/Website/PLAN.md` |
| **Image archives** | `~/Documents/ART/SCAN` (JPEG scans) and `~/Documents/ART/PHONE` (163 HEIC) — treated as **read-only archives** |

The source photographs are **not in the repo**. Web-resolution derivatives
are, on purpose — a static host serves what's in the repository, so
gitignoring images would deploy an empty site.

---

## Site structure

```
index.html             Hero + the two collection tiles + newsletter bar
oil-pastels.html       Gallery
relief-printing.html   Gallery
about.html             Statement, bio, contact
assets/css/style.css   All styling. Variables at the top drive everything.
assets/js/lightbox.js  Click an artwork to enlarge (~40 lines, no deps)
assets/images/         Web-resolution images, committed deliberately
serve.py               Local preview
tools/prepare_images.py   Archive photo -> web-ready JPEG
tools/grid-recipe.txt     How the 8 tile crops were made, and why
```

### Local preview

```bash
cd ~/Documents/GitHub/art-portfolio && python3 serve.py        # port 4321
python3 serve.py 4322                                          # another port
```

`serve.py` is **threaded on purpose** and sends `Cache-Control: no-store`. The
stdlib's single-threaded `TCPServer` wedges when a browser holds a keep-alive
socket open — the server appears dead and the browser keeps showing a stale
page. That happened and cost time to diagnose. Don't "simplify" it back.

### Deploying (not done yet)

Cloudflare Pages or GitHub Pages: connect the repo, **leave the build command
blank**, output directory `/`. A push is a deploy. Cloudflare is preferred —
unlimited static bandwidth against GitHub's metered 100 GB/month.

---

## Design

White background (`#fff` — it has always been pure white; any "cream" look has
come from placeholder image tones). Minimal, gallery-like, left-aligned.

**Type**: Bebas Neue for anything that *names* something — hero title, the two
grid titles, page headings. EB Garamond for everything you *read* — body copy,
captions, the About prose. Small system sans for UI chrome: nav links, "VIEW",
the Subscribe button, and **the navbar's name mark** — that was Garamond, so
the bar is now set in one face throughout. One variable,
`--display`, controls the display face everywhere.

**Bebas has one weight and no lowercase.** Always `font-weight: 400`; asking
for 700 makes the browser fake it and it looks smeared. Lowercase input renders
as capitals and cannot be changed.

### Landing page layout

Three columns: **oil pastel tile | text | relief tile**, tiles vertically
centred against the text block.

```css
grid-template-columns: minmax(0, 1fr) min-content minmax(0, 1fr);
```

The middle column is `min-content`, so it sizes itself to the widest
unbreakable thing in it — "ELIZABETH", which is **3.258 em** wide in Bebas.
The tiles take everything left over. This is why the layout is self-adjusting:
make the title bigger and the text column follows, with the tiles absorbing the
difference.

Tiles are **portrait 4:5** (`aspect-ratio: 4 / 5`), not square. That was the
fix for "bigger tiles" without stealing row width — height grows instead.

They also carry a **viewport height cap**:

```css
--tile-h-max: calc(100dvh - 2 * var(--bar-h) - 2 * var(--hero-pad-y));
width: min(100%, calc(var(--tile-h-max) * 4 / 5));
```

Tile height is otherwise a pure function of window *width*, so a wide-but-short
window — any laptop, once the browser's own chrome is subtracted — made the
hero taller than the viewport and the landing page scrolled. With the cap the
height leads and the width follows, and the page fits at every size tested from
1280x700 up. `--hero-pad-y` exists only so the padding and the cap cannot drift
apart.

At 1512 × 982: tiles **477 × 596**, a 65px channel each side of the text, 21px
clear of the screen edge. At 1512 × 800 the cap bites and they are 439 × 549.

Below 1200px it stacks: text on top, two square tiles side by side beneath.
Below 680px, single column.

### The newsletter bar

A slim bar on the bottom edge of the landing page, deliberately the **same
height as the navbar** (`--bar-h: 4.6rem`), carrying the copyright on the left
and the signup on the right — mirroring the nav's mark-left/links-right. The
landing page is `min-height: 100dvh` as a flex column so the bar lands on the
bottom edge on load. **Every page now ends with this bar** — the old `.foot`
footer is gone entirely, markup and CSS. On the interior pages the bar is not
pinned to the viewport; it just closes the content, with
`body:not(.home) .newsbar { margin-top: … }` giving it air.

### Vertical space is measured in vh

`.page-head` padding, `.about` bottom padding and the news bar's top margin are
all `vh`-based, not `vw`. Vertical space should answer to how tall the window
is; the vw version spent 152px on air above the prose and tipped the About page
into a scroll on a short window. Every page is also a `100dvh` flex column with
`body > main { flex: 1 1 auto }`, so the bar sits on the bottom edge whenever
the content is shorter than the window.

The About page now fits down to about **820px of viewport height**. Below that
it scrolls, and the only way further is to cut words or type size — the prose
block alone is ~450px.

**The form posts nowhere.** `action="#"` needs replacing with a provider
endpoint. Buttondown is the suggestion (free to 100 subscribers, exports
cleanly) and the exact URL format is in a comment above the form.

---

### The About portrait

Top and bottom flush with the prose block. `align-self` alone cannot do this —
the portrait is the taller item (625px against 450px of text), so it sets the
row height. Instead the photo column is given a **definite width**
(`clamp(13rem, 23vw, 22rem)`) and the `<img>` is `position: absolute; inset: 0`
with `object-fit: cover`, so it contributes no intrinsic size and the row is
set by the prose alone. The cost is a crop: **`object-position: 50% 30%`** is
the one value to turn — the second number is what survives vertically, 0% keeps
the top of the photo, 100% the bottom. Below 680px the photo returns to normal
flow at its own aspect ratio.

Column one is `minmax(0, var(--measure))`, not a round `38rem`. At 38rem the
column was 608px against 492px of text, leaving 116px of dead space between the
words and the photo that no `gap` value could close.

---

## Four gotchas that cost real time

These are not obvious and will bite again if the code is "tidied".

**1. The tiles collapse to nothing if you change how they're sized.**
Both children of `.tile` (`.tile__grid` and `.tile__label`) are
`position: absolute`, so a tile has **no in-flow content and zero intrinsic
width**. Combined with `aspect-ratio`, zero width means zero height — the tiles
vanish while still being in the DOM. Anything that switches a grid item from
stretching to content-based sizing triggers it. It happened twice:

- `justify-self: end` on the container — content-based sizing, collapsed.
- `max-width` + `margin-inline: auto` on `.hero` — **auto inline margins on a
  grid item disable stretch**, so `.hero` shrank to fit its content (597px of
  1512px), the `1fr` tracks got no free space, and the tiles rendered as their
  1px borders. Computed tracks read `2px 385.75px 2px`.

The fix in both cases is a **definite width**: `width: 100%` on the tile, and
`width: min(100%, 96rem)` on the hero instead of `max-width`. Those look like
pointless indirection and are commented accordingly. Leave them.

**2. The title band hides 11% of every grid cell.**
The white band lies across the tile's middle and covers the **bottom** of the
two top cells and the **top** of the two bottom cells — measured as 33px of a
296px cell, hence `BAND_HIDE = 0.111` in `prepare_images.py`. A perfectly
centred crop therefore looks off-centre on the page: top cells appear to sit
low, bottom cells appear to sit high. `--cell top|bottom` corrects it
automatically; `--vshift` is the manual override.

If the band's padding or font size ever changes, that 0.111 is wrong.

**3. A crop shift does nothing unless the box has slack.**
The maximal centred crop usually fills one axis of the original entirely, so
there's nothing to shift into. The first version of `--cell` ran, printed
`vshift +0.056`, and produced a **pixel-identical image**. `crop_to_ratio` now
shrinks the box just enough to create the slack and then moves it, at the cost
of a little zoom. Only caught by measuring; eyeballing the before/after missed
it.

**4. Shift values belong to the photograph, not the grid position.**
When `lino2` was reshot, the same slot went from needing `-0.038` to `-0.068`,
because the new frame was a different shape. **Always re-measure after a
reshoot.** Roughly 0.045 moves a subject about 27px on screen at 1512px wide.

---

## Image pipeline

`tools/prepare_images.py` converts archive photos to web-ready JPEGs. It
strips **all** metadata including EXIF GPS (studio photos otherwise publish a
home address), converts to sRGB, and never touches the source — a guard
refuses any write that would land inside a folder passed as input. That guard
had a bug where the output folder being *the same as* the source folder slipped
through; since filenames are preserved, a `--force` run would have overwritten
originals. Fixed and tested, but worth knowing it existed.

```bash
python3 tools/prepare_images.py path/to/img.jpg          # 1600px long edge
python3 tools/prepare_images.py ~/some/folder            # whole folder
python3 tools/prepare_images.py -r ~/some/folder         # + subfolders
python3 tools/prepare_images.py --grid ...               # 600x750, 4:5 crop
```

Options: `--grid`, `--size`, `--quality`, `--prefix`, `--no-watermark`,
`--watermark-text`, `--cell top|bottom`, `--vshift`, `--hshift`, `-f`, `-n`.

**HEIC works via the macOS `sips` tool** — `pillow-heif` is not installed and
isn't needed. No browser can display HEIC, so every phone photo must be
converted before it can go on the site.

### Sizes, measured from what the layout actually renders

| Use | Displays at | Export at |
|---|---|---|
| Grid tile crops | 252 × 315 max | **600 × 750** (4:5) |
| Gallery + lightbox | 589px wide max; lightbox to ~1180px tall | **1200px long edge**, quality 72 |
| About portrait | 348 × 450 (cropped by `object-fit`) | **732 × 1300**, quality 72 — 59 KB |

Roughly 2× display size, which is what Retina needs. The lightbox serves the
*same file* as the gallery thumbnail, so one size does both jobs.

### EXIF orientation must be baked in before metadata is stripped

`upright()` runs `ImageOps.exif_transpose()` on load. A phone does not rotate
the sensor data — it stores a portrait photo as 5712x4284 *landscape* plus
"rotate 90" in EXIF tag 274 and leaves the viewer to turn it. This script
strips metadata, so that instruction was being discarded and **28 of the 49
relief prints landed on the page on their side**. Rotating the pixels at load
time is the only way to keep the orientation once the tag is gone. `sips`
preserves the tag through HEIC decoding rather than applying it, so the HEIC
path needs this just as much as the JPEG path.

### Transparency must be flattened before JPEG

`flatten()` composites any alpha onto white (`FLATTEN_BG`) before the colour
conversion. Without it, `.convert("RGB")` on a cut-out PNG does not blend —
it drops the alpha channel and leaves whatever RGB sat underneath, which is
usually black. The About portrait arrived on a black rectangle because of this.
It has to run *before* `profileToProfile(outputMode="RGB")`, which would itself
discard the alpha.

### The watermark

"Laura Elizabeth Burnett", white, lower left, letter-spaced. It is
**adaptive**: it measures the brightness of the patch it's about to sit on and
picks the dark outline and shadow strength from that. Plain white alone was
nearly invisible on pale pastel work — which is most of it.

**Grid crops are made with `--no-watermark`**, a deliberate decision: at a
252 × 315 cell the text is illegible and it would repeat four times per tile.
Gallery images are the place for it.

### The two galleries

| Page | Web images | Originals (gitignored) | Count |
|---|---|---|---|
| `relief-printing.html` | `assets/images/relief/` | `assets/images/prints/` | 49 |
| `oil-pastels.html` | `assets/images/pastels/` | `assets/images/oilpastels/` | 36 |

**Rebuilding a page is one command:**

```bash
python3 tools/build_gallery.py pastels     # or relief, all
```

`tools/build_gallery.py` converts the originals, numbers them, deletes any
image whose number no longer exists, and rewrites the page's gallery block.
Run it whenever the originals change — added, removed, replaced or
**renumbered**. Renumbering the originals is how the page is reordered.

It exists because three things must agree and are easy to let drift: the image
files, the `width`/`height` on each `<img>`, and the `--ar` on each `<figure>`.
A stale `--ar` throws no error; the rows just quietly stop lining up. The
script regenerates all three together.

It touches only the gallery block and the output image folder. Headings, intro
copy, navbar and news bar are never read or rewritten. It does **discard
captions and written alt text**, since the figures are rebuilt from scratch —
it checks first and stops to ask (`-y` skips the prompt). When captions are
finally written, delete the generated-block comment and the page becomes
ordinary hand-edited HTML again.

Underneath it calls `prepare_images.py --no-watermark --size 1200 --quality
72`, then copies files in with the number **zero-padded to two digits**, so
filename order and numeric order are the same thing — the originals mixed `01` with `010`,
which sorts wrongly as text. Numbering has gaps (no 13 or 18 in the prints, and
several missing in the pastels); nothing is lost, the source numbering skips.

182 MB of HEIC in, 11.6 MB of JPEG out. **The originals are gitignored** —
`prints/` and `oilpastels/`. Only the derivatives are committed.

**Both originals folders have since been deleted from the working copy**, so a
plain rebuild will skip with a message. Either put the originals back, or use
`--html-only`, which leaves the images alone and rebuilds just the page markup
from the web JPEGs already on disk. That flag is also the right one after
changing `ROW_TARGETS`.

Captions are not written yet; the page has none at all rather than 49 copies of
the word FILLER. The comment above the gallery shows where a `<figcaption>`
goes, and the lightbox picks one up automatically if present.

Both galleries are built from **explicit justified rows**. Each `.gallery__row`
is a flex line stretched across the full width, and inside it every figure is

```css
flex: var(--ar) var(--ar) 0;     /* --ar is written inline per <figure> */
```

A basis of zero with grow proportional to the aspect ratio means the whole
available width is shared out in proportion to the ratios, so width ∝ ratio, so
every image in the row lands on exactly the same height with nothing cropped,
and the right edge comes out flush.

Row height is about `(width - gaps) / (sum of the row's ratios)`, so **how many
images a row holds is what sets its height**. `ROW_TARGETS` in
`build_gallery.py` varies that sum from row to row, which is what stops the
page reading as a grid.

Three approaches were tried and discarded first — the reasons matter, because
each looks like it should work:

- **CSS multi-column** (`columns`) spaces evenly but fills each column to the
  bottom before starting the next, so 1, 2, 3 read *downwards*.
- **CSS grid** reads left to right, but every cell in a row is the same width,
  so a portrait and a landscape cannot both fill their cell.
- **A per-image size weight** on a single wrapping flex container. This is the
  subtle one. `flex-grow` shares out only the *leftover* space, not the total
  width, so a width is proportional to its ratio **only while every item in the
  row carries the same weight**. Per-image weights broke the justification and
  scattered the heights inside each row — and it measured as fine, because
  `align-items: stretch` makes the `<figure>` boxes equal even when the images
  inside them are not. **Measure the `<img>`, not the `<figure>`.**

The last row is a remainder and is not justified — it keeps a fixed
`--row-h` and stops short of the right edge, instead of blowing two images up
to full width.

Measured at 1512px: uniform 16px gaps, every full row flush to the same right
edge, zero height spread within each row, row heights ranging 288–534px.

**If you regenerate the images, regenerate the markup with them** — a stale
`--ar` breaks the row maths silently. `build_gallery.py` does both together.

### On protecting the work

Low resolution does **not** stop viewing or copying — anything on screen can be
screenshotted, and right-click blocking is bypassed instantly and annoys real
visitors. What it does stop is **printing**: 1200px at 300 dpi prints 4 inches,
so a thief could make a postcard, not a saleable A3. Keep the 300/600 dpi
masters off the web. Stripping EXIF matters more than resolution, and the real
deterrent to *reuse* (as opposed to reprinting) is the watermark, which the
galleries currently do not use.

---

## State as of 23 October 2026

**Done**: all layout and typography; four pages; real artwork in
both landing-page tiles with per-image crop tuning; hover lift and shadow on
the tiles; the image pipeline and its recipe file.

**Not done**:

- **All body text is still `FILLER`** — marked as such in every HTML file. The
  tagline, both gallery intros, the whole About page, and the contact email
  (`you@example.com`). This is the real bottleneck, and it is writing, not code.
- **Gallery and About images are still grey placeholders.** Only the 8 landing-
  page tile crops are real. `linocut_images/` (164) and `oil_pastel_images/`
  (80) are waiting to be processed at 1600px.
- **Newsletter form posts nowhere.**
- **Not deployed.** No domain, no host connected.
- **`main` is 1 commit ahead of `origin/main`** — commit `f7da2e5` is local
  only and needs pushing.

### Alt text

Every image needs real descriptive alt text — "a low horizon in burnt orange,
the sky scraped back to white", not "linocut print". It is what a screen reader
announces and it is most of the image SEO for an image-only business. Currently
all placeholder.

---

## Working preferences

- **Never kill or restart a process without asking.** A broad
  `pkill -f "Google Chrome"` once killed a live browser session with critical
  work in another window. Match narrowly, and ask first.
- **Measure, don't eyeball.** Several bugs here looked fine in a screenshot and
  were only caught by reading computed styles or counting pixels. Headless
  Chrome is available at
  `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` with
  `--headless --screenshot --dump-dom`.
- **`timeout` does not exist on this machine.** Wrapping a command in it fails
  with "command not found" and returns nothing, which looks exactly like a hung
  process. Use `curl --max-time` instead.
- Prefers a plain explanation of *why* something broke over a silent fix.
- Likes small, reversible changes and being told which single value to turn.
