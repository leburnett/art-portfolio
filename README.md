# Laura Elizabeth Burnett — portfolio site

Four hand-written HTML pages, one stylesheet, one small script. No build step, no
framework, no dependencies to update. Open any `.html` file in a browser and it works.

```
index.html            Hero, the two collection tiles, newsletter bar
oil-pastels.html      Gallery
relief-printing.html  Gallery
about.html            Statement, bio, contact
assets/css/style.css  All styling. Variables at the top control the whole site.
assets/js/lightbox.js Click an artwork to enlarge it
assets/images/        Web-resolution images (committed to git on purpose)
assets/images/relief/   49 relief prints, numbered 01..49
assets/images/pastels/  36 oil pastels, numbered 01..36
tools/build_gallery.py  Regenerates the two gallery pages (see below)
tools/prepare_images.py Downsamples + strips metadata from a folder of originals
serve.py              Local preview: python3 serve.py → http://localhost:4321
```

The `alt` text on every gallery image is still marked **FILLER** — that is the one
piece of placeholder content left, and `build_gallery.py` warns you about it on
every run.

---

## Preview it locally

```bash
python3 serve.py
```

Then open <http://localhost:4321>. Use this rather than double-clicking the file —
`file://` URLs behave differently from a real server.

## Adding a work to a gallery

The two gallery pages are **generated**, not hand-edited — anything you type into the
`<section class="gallery">` block is overwritten on the next build.

1. Drop the full-resolution original into `assets/images/prints/` (relief) or
   `assets/images/oilpastels/` (pastels). Name it with a leading number; that number
   is the running order on the page. Those two folders are gitignored.
2. Run the build:

   ```bash
   python3 tools/build_gallery.py all
   ```

   It downsamples to 1200 px / quality 72, strips every scrap of metadata (EXIF
   location included), writes `assets/images/relief/` and `assets/images/pastels/`,
   and rewrites the gallery markup in both pages.
3. Replace the FILLER `alt` text it leaves behind.

If the originals are no longer on this machine, `--html-only` rebuilds the markup from
the web JPEGs already committed and leaves the images untouched:

```bash
python3 tools/build_gallery.py all --html-only
```

Row heights vary on purpose, so the page does not read as a grid. `ROW_TARGETS` near
the top of `build_gallery.py` controls it — a smaller number means fewer images in that
row, so a taller row. Edit it and re-run with `--html-only`.

Write real alt text — "a low horizon in burnt orange, the sky scraped back to white" —
not "oil pastel print". It is what a screen reader announces, and it is most of your
image SEO.

## Changing the look

Everything is in the `:root` block at the top of `assets/css/style.css`:
the ink and grey values, the font stack, the page gutter. The hero name is sized with
`clamp()` on `.hero__name`, so it scales smoothly with the window instead of needing
breakpoints — widen or narrow that middle `vw` value to make it fill more or less.

## Wiring up the newsletter

The form at the foot of **all four pages** currently posts nowhere (`action="#"`),
so pressing Subscribe silently does nothing. Fix it on all four. Pick a provider and paste its endpoint
into the `action` attribute — the comment above the form has the Buttondown example.
[Buttondown](https://buttondown.email) is free to 100 subscribers and exports cleanly,
which matters: the list is the one asset here you genuinely own.

---

## Deploying

Commit the whole folder, images included, and point a host at it.

**Cloudflare Pages** (recommended) — connect the GitHub repo, leave the build command
blank, set the output directory to the repo root. Free, unlimited bandwidth, custom
domain included.

**GitHub Pages** — Settings → Pages → deploy from `main` / root. Also free, but metered
bandwidth (100 GB/month soft limit) and no edge functions if you ever want them.

Either way a push is a deploy. There is nothing to build.

## A note on images and git

Web-resolution images **belong in this repo**. A static host serves what is in the
repository, so anything in `.gitignore` is simply absent from the live site. At
1600 px / ~300 KB each, a hundred works is about 30 MB — nowhere near GitHub's 1 GB
soft limit, and a repo you can clone to a new laptop and deploy from immediately.

What stays out: the 300/600 DPI masters in `../../SCAN/`, the HEIC originals in
`../../PHONE/`, and any TIFF or PSD. Those are archives, not website assets, and
`.gitignore` already blocks them by extension as a safety net.
