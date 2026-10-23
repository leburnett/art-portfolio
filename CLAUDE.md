# Laura Elizabeth Burnett — artist portfolio site

Handoff notes, written 23 October 2026. Read this to get up to speed on the
project without the original chat.

---

## What this is

A static portfolio website for an artist working in **oil pastel** and **relief
print (linocut)**. Five hand-written HTML pages, one stylesheet, one small
script. **No build step, no framework, no dependencies.** Open any `.html` in a
browser and it works.

It does **not** sell anything. That was a deliberate decision — a shop may come
later, but v1 is a portfolio only.

### Where everything lives

| | |
|---|---|
| **Site code** | `~/Documents/GitHub/art-portfolio` |
| **GitHub** | `github.com/leburnett/art-portfolio` — **private** |
| **Source photographs** | `~/Documents/ART_PORTFOLIO/{grid_images, linocut_images, oil_pastel_images, misc_images}` |
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
misc.html              Gallery — anything outside the other two themes
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
captions, the About prose, and the navbar's name mark. Small system sans for UI
chrome: nav links, "VIEW", the Subscribe button, the footer line. One variable,
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

At a 1512px window: tiles **477 × 596**, a 65px channel each side of the text,
21px clear of the screen edge.

Below 1200px it stacks: text on top, two square tiles side by side beneath.
Below 680px, single column.

### The newsletter bar

A slim bar on the bottom edge of the landing page, deliberately the **same
height as the navbar** (`--bar-h: 4.6rem`), carrying the copyright on the left
and the signup on the right — mirroring the nav's mark-left/links-right. The
landing page is `min-height: 100dvh` as a flex column so the bar lands on the
bottom edge on load. The landing page has **no separate footer**; the other
pages keep theirs.

**The form posts nowhere.** `action="#"` needs replacing with a provider
endpoint. Buttondown is the suggestion (free to 100 subscribers, exports
cleanly) and the exact URL format is in a comment above the form.

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
| Gallery + lightbox | 589px wide max; lightbox to ~1180px tall | **1600px long edge** |
| About portrait | ~450px wide | 900px wide |

Roughly 2× display size, which is what Retina needs. The lightbox serves the
*same file* as the gallery thumbnail, so one size does both jobs.

### The watermark

"Laura Elizabeth Burnett", white, lower left, letter-spaced. It is
**adaptive**: it measures the brightness of the patch it's about to sit on and
picks the dark outline and shadow strength from that. Plain white alone was
nearly invisible on pale pastel work — which is most of it.

**Grid crops are made with `--no-watermark`**, a deliberate decision: at a
252 × 315 cell the text is illegible and it would repeat four times per tile.
Gallery images are the place for it.

### On protecting the work

Low resolution does **not** stop viewing or copying — anything on screen can be
screenshotted, and right-click blocking is bypassed instantly and annoys real
visitors. What it does stop is **printing**: 1600px at 300 dpi prints 5.3
inches, so a thief could make a postcard, not a saleable A3. Keep the 300/600
dpi masters off the web. Stripping EXIF matters more than resolution.

---

## State as of 23 October 2026

**Done**: all layout and typography; five pages; the Misc page; real artwork in
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
