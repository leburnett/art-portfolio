# Laura Elizabeth Burnett — portfolio site

Five hand-written HTML pages, one stylesheet, one small script. No build step, no
framework, no dependencies to update. Open any `.html` file in a browser and it works.

```
index.html            Hero, the two collection tiles, newsletter bar
oil-pastels.html      Gallery
relief-printing.html  Gallery
misc.html             Gallery — anything outside the other two themes
about.html            Statement, bio, contact
assets/css/style.css  All styling. Variables at the top control the whole site.
assets/js/lightbox.js Click an artwork to enlarge it
assets/images/        Web-resolution images (committed to git on purpose)
serve.py              Local preview: python3 serve.py → http://localhost:4321
```

Everything marked **FILLER** in the HTML is placeholder text for you to replace.
Every image in `assets/images/` is a generated grey placeholder.

---

## Preview it locally

```bash
python3 serve.py
```

Then open <http://localhost:4321>. Use this rather than double-clicking the file —
`file://` URLs behave differently from a real server.

## Adding a work to a gallery

1. Export the image at about **1600 px on the long edge**, JPEG quality ~75. That lands
   around 200–400 KB, which is the right size for the web and far too small for anyone
   to print from.
2. Save it into `assets/images/`.
3. In the gallery page, copy one `<figure class="piece">` block and change three things:
   the `src`, the `alt` text, and the caption.

Write real alt text — "a low horizon in burnt orange, the sky scraped back to white" —
not "oil pastel print". It is what a screen reader announces, and it is most of your
image SEO.

## Changing the look

Everything is in the `:root` block at the top of `assets/css/style.css`:
the ink and grey values, the font stack, the page gutter. The hero name is sized with
`clamp()` on `.hero__name`, so it scales smoothly with the window instead of needing
breakpoints — widen or narrow that middle `vw` value to make it fill more or less.

## Wiring up the newsletter

The form in `index.html` currently posts nowhere. Pick a provider and paste its endpoint
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
