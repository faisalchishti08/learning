---
card: webdev
gi: 95
slug: images-img-alt-srcset-sizes
title: Images (img, alt, srcset, sizes)
---

## 1. What it is

The `<img>` element embeds images. Four attributes are essential:

- **`src`** — the image URL (required for basic use).
- **`alt`** — text alternative; required for accessibility.
- **`srcset`** — a list of image sources at different resolutions or widths.
- **`sizes`** — tells the browser how wide the image will be at different viewport widths, so it can pick the best `srcset` candidate.

```html
<img
  src="photo-800.jpg"
  alt="A hiker standing on a ridge at sunrise"
  srcset="photo-400.jpg 400w, photo-800.jpg 800w, photo-1600.jpg 1600w"
  sizes="(max-width: 600px) 100vw, (max-width: 1200px) 50vw, 800px"
  width="800"
  height="533"
  loading="lazy"
>
```

`srcset` and `sizes` together enable **responsive images** — the browser automatically downloads the appropriately-sized image for the user's screen and connection, saving bandwidth without sacrificing quality.

## 2. Why & when

A 4000×3000 pixel photo is 4–8 MB. Serving it on a 360px mobile screen wastes 95% of those bytes. `srcset` + `sizes` lets the browser choose the right image variant automatically:
- Small screen? Download the small file.
- Retina display? Download the 2x version.
- Slow connection? Browser can downgrade.

`alt` is mandatory for accessibility. Without it, screen readers announce the filename (or "image"). With a good `alt`, they announce a description that gives equivalent information to a sighted user.

You use `<img>` for every meaningful image in a page. Use CSS `background-image` for purely decorative images (no `alt` needed there).

## 3. Core concept

**`alt` text rules:**

| Image type | `alt` content |
|-----------|-------------|
| Informative photo | Describe what's important: `alt="Red double-decker bus on London Bridge"` |
| Functional image (icon, button image) | Describe the action: `alt="Search"`, `alt="Close dialog"` |
| Decorative | Empty string: `alt=""` — tells AT to skip it |
| Image of text | Copy the text exactly: `alt="Summer Sale — 50% off"` |
| Complex (chart, diagram) | Brief description + longer text nearby |

Empty `alt=""` is correct for decorative images. Missing `alt` is never correct — AT tools report it as an error.

**`srcset` with width descriptors (`w`):**

```html
srcset="small.jpg 400w, medium.jpg 800w, large.jpg 1600w"
```

Each entry is `URL widthW`. The `w` descriptor gives the image's intrinsic pixel width. The browser divides each candidate's width by the display size (from `sizes`) to find the best density match. Always use `w` descriptors with `sizes`; they're more flexible than `x` descriptors.

**`srcset` with pixel density descriptors (`x`):**

```html
srcset="photo.jpg 1x, photo@2x.jpg 2x, photo@3x.jpg 3x"
```

Simpler than `w` descriptors. Use when the image always displays at the same CSS size but you want high-DPI versions. No `sizes` needed here — density descriptors already encode the resolution relationship.

**`sizes`:**

Tells the browser the rendered width of the image *before it loads CSS*. Browsers parse HTML before stylesheets, so they can't compute layout yet. `sizes` gives them the hint:

```
sizes="(max-width: 600px) 100vw,   ← on screens ≤600px: image is full-viewport-width
       (max-width: 1200px) 50vw,    ← on screens ≤1200px: image is half-viewport-width
       800px"                        ← otherwise: image is 800px wide
```

The browser picks the `srcset` candidate closest to: `sizes-declared-width × devicePixelRatio`.

**`width` and `height` attributes:** Always include them. They allow the browser to reserve space in the layout before the image loads, preventing **cumulative layout shift (CLS)** — the sudden page jump when images pop in.

```html
<img src="photo.jpg" alt="..." width="800" height="533">
```

These are the intrinsic dimensions in CSS pixels. The CSS can resize the image; the attributes just establish the aspect ratio for space reservation.

## 4. Diagram

<svg viewBox="0 0 640 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Browser choosing between srcset candidates based on screen width and device pixel ratio, with sizes hint">
  <defs>
    <marker id="arr95g" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- srcset candidates -->
  <rect x="10" y="10" width="185" height="170" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="102" y="32" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">srcset candidates</text>
  <text x="25" y="55" fill="#79c0ff" font-size="9" font-family="monospace">photo-400.jpg  400w</text>
  <text x="25" y="73" fill="#79c0ff" font-size="9" font-family="monospace">photo-800.jpg  800w</text>
  <text x="25" y="91" fill="#6db33f" font-size="9" font-family="monospace">photo-1600.jpg 1600w</text>
  <text x="25" y="115" fill="#8b949e" font-size="8" font-family="sans-serif">sizes hint:</text>
  <text x="25" y="130" fill="#8b949e" font-size="8" font-family="monospace">(max-w:600px) 100vw</text>
  <text x="25" y="145" fill="#8b949e" font-size="8" font-family="monospace">(max-w:1200px) 50vw</text>
  <text x="25" y="160" fill="#8b949e" font-size="8" font-family="monospace">800px</text>

  <!-- Browser decision -->
  <rect x="220" y="10" width="200" height="250" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="32" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser picks</text>
  <text x="240" y="56" fill="#8b949e" font-size="9" font-family="sans-serif">Screen: 360px, DPR 2</text>
  <text x="240" y="72" fill="#8b949e" font-size="9" font-family="sans-serif">sizes → 100vw = 360px</text>
  <text x="240" y="88" fill="#8b949e" font-size="9" font-family="sans-serif">need: 360×2 = 720px</text>
  <text x="240" y="112" fill="#6db33f" font-size="9" font-family="sans-serif">→ picks photo-800.jpg ✓</text>

  <line x1="320" y1="130" x2="320" y2="148" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <text x="240" y="168" fill="#8b949e" font-size="9" font-family="sans-serif">Screen: 1400px, DPR 1</text>
  <text x="240" y="184" fill="#8b949e" font-size="9" font-family="sans-serif">sizes → 800px</text>
  <text x="240" y="200" fill="#8b949e" font-size="9" font-family="sans-serif">need: 800×1 = 800px</text>
  <text x="240" y="224" fill="#6db33f" font-size="9" font-family="sans-serif">→ picks photo-800.jpg ✓</text>
  <text x="240" y="242" fill="#8b949e" font-size="8" font-family="sans-serif">or photo-1600 for DPR 2</text>

  <!-- arrows from srcset to browser -->
  <line x1="197" y1="80" x2="218" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr95g)"/>

  <!-- Network savings -->
  <rect x="440" y="10" width="190" height="170" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="32" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Network savings</text>
  <text x="455" y="55" fill="#8b949e" font-size="9" font-family="sans-serif">1x desktop (800px):</text>
  <text x="455" y="70" fill="#6db33f" font-size="9" font-family="sans-serif">→ 800w file (~120 KB)</text>
  <text x="455" y="93" fill="#8b949e" font-size="9" font-family="sans-serif">2x desktop (800px):</text>
  <text x="455" y="108" fill="#6db33f" font-size="9" font-family="sans-serif">→ 1600w file (~320 KB)</text>
  <text x="455" y="131" fill="#8b949e" font-size="9" font-family="sans-serif">Mobile (360px, 2x):</text>
  <text x="455" y="146" fill="#6db33f" font-size="9" font-family="sans-serif">→ 800w file (~120 KB)</text>
  <text x="535" y="168" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">vs 1600w for all = waste</text>

  <!-- CLS note -->
  <rect x="10" y="196" width="185" height="58" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="102" y="216" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Prevent CLS:</text>
  <text x="25" y="232" fill="#8b949e" font-size="8" font-family="monospace">&lt;img width="800" height="533"&gt;</text>
  <text x="102" y="248" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reserves space before load</text>
</svg>

The browser picks the `srcset` candidate whose width best matches `sizes × devicePixelRatio`, downloading only what's needed.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Responsive Images</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; margin: 0; padding: 1rem; }
    .hero  { width: 100%; max-width: 900px; margin: 0 auto; }
    .hero img { width: 100%; height: auto; border-radius: 8px; }
    .grid  { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem; }
    .grid img { width: 100%; height: 150px; object-fit: cover; border-radius: 6px; }
    .info  { font-family: monospace; font-size: 0.8rem; color: #6db33f; margin-top: 0.25rem; }
  </style>
</head>
<body>

  <!-- Hero: srcset with width descriptors -->
  <div class="hero">
    <img
      src="https://httpbin.org/image/png"
      srcset="https://httpbin.org/image/png 400w,
              https://httpbin.org/image/png 800w,
              https://httpbin.org/image/png 1600w"
      sizes="(max-width: 600px) 100vw,
             (max-width: 1200px) 90vw,
             900px"
      alt="Abstract network topology diagram"
      width="900"
      height="600"
      loading="eager"
    >
    <p class="info" id="hero-info"></p>
  </div>

  <!-- Grid: density descriptors for fixed-size thumbnails -->
  <div class="grid">
    <div>
      <img
        src="https://httpbin.org/image/png"
        srcset="https://httpbin.org/image/png 1x,
                https://httpbin.org/image/png 2x"
        alt="Server rack in data centre"
        width="400"
        height="300"
        loading="lazy"
      >
      <p class="info">Server rack — density srcset</p>
    </div>

    <!-- Decorative image: alt="" -->
    <div>
      <img
        src="https://httpbin.org/image/png"
        alt=""
        width="400"
        height="300"
        loading="lazy"
        aria-hidden="true"
      >
      <p class="info">Decorative: alt="" + aria-hidden</p>
    </div>
  </div>

  <script>
    // Show which src the browser chose
    const heroImg = document.querySelector(".hero img");
    heroImg.addEventListener("load", () => {
      document.getElementById("hero-info").textContent =
        `Loaded: ${heroImg.currentSrc || heroImg.src}`;
    });

    // currentSrc reflects the chosen srcset candidate
    if (heroImg.complete) {
      document.getElementById("hero-info").textContent =
        `Loaded: ${heroImg.currentSrc || heroImg.src}`;
    }

    // DevTools tip: in console, check img.currentSrc vs img.src
    console.log("Viewport:", window.innerWidth + "px, DPR:", window.devicePixelRatio);
    console.log("Hero currentSrc:", heroImg.currentSrc);
    console.log("Hero src:", heroImg.src);
  </script>
</body>
</html>
```

**How to run:** save as `images.html`, open in a browser. Open DevTools → Network → Img filter to see which source file was downloaded. Use DevTools "Toggle Device Toolbar" to simulate mobile devices.

## 6. Walkthrough

- `srcset="... 400w, ... 800w, ... 1600w"` — three candidates. The browser doesn't request all three; it picks one based on the viewport and DPR.
- `sizes="(max-width: 600px) 100vw, (max-width: 1200px) 90vw, 900px"` — tells the browser: on small screens the image is full-width, on medium screens it's 90% wide, on large screens it's exactly 900px. Without `sizes`, the browser assumes the image is 100vw and may download an unnecessarily large file.
- `width="900" height="600"` — the browser uses these to reserve a 900:600 (3:2) aspect ratio box in the layout before the image arrives. Without them, other page content jumps when the image loads (CLS).
- `alt="Abstract network topology diagram"` — descriptive, specific alt text for the hero. A screen reader reads this and the user gets equivalent information to a sighted user seeing the image.
- `alt=""` on the decorative image — tells AT to skip this image entirely. `aria-hidden="true"` reinforces this for frameworks that might generate implicit alt announcements.
- `heroImg.currentSrc` — the actual URL chosen by the browser from the `srcset`. May differ from `src` if the browser selected a higher-resolution candidate.

## 7. Gotchas & takeaways

> **Omitting `sizes` when using `w` descriptors causes the browser to assume `100vw`.** If your image is actually displayed at `50vw` on desktop, the browser downloads a 2× larger file than needed. Always write `sizes` when using `w` descriptors.

> **Missing `width` and `height` causes CLS.** Google's Core Web Vitals penalise CLS. Images without dimensions create unknown-size placeholders that cause content to shift when the image loads.

> **`alt` should describe the image, not "image of" or "photo of".** Screen readers already announce "image" before the alt text. Writing `alt="Photo of a dog"` causes the announcement "image, photo of a dog" — redundant. Write `alt="Golden retriever puppy playing in leaves"`.

- `alt` = required; empty string for decorative; describe function for icon images.
- `srcset` + `sizes` = responsive images; the browser picks the right candidate.
- `w` descriptors need `sizes`; `x` descriptors don't.
- `width` + `height` attributes prevent CLS — always include them.
- `img.currentSrc` shows which srcset candidate the browser chose.
- Use `loading="lazy"` for below-the-fold images; `loading="eager"` (or omit) for the hero image.
