---
card: webdev
gi: 96
slug: responsive-images-the-picture-element
title: Responsive images & the picture element
---

## 1. What it is

`<picture>` is a container element that provides multiple image sources for different situations. It wraps one or more `<source>` elements and a fallback `<img>`:

```html
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img src="hero.jpg" alt="A mountain landscape at dusk" width="1200" height="800">
</picture>
```

The browser tries each `<source>` in order, picks the first one it supports, and renders it in the `<img>`. If no `<source>` matches, it falls back to the `<img src>`. The `<img>` is always required — it provides the `alt`, `width`, `height`, and fallback.

## 2. Why & when

`<picture>` solves two problems that `<img srcset>` cannot:

**1. Format switching (type negotiation):** A browser that supports AVIF (60–80% smaller than JPEG) should get the AVIF; one that doesn't should get WebP or JPEG. `srcset` on `<img>` only lets you vary resolution, not file format. `<source type="image/avif">` handles format.

**2. Art direction (crop/composition switching):** A wide landscape photo looks great on desktop but becomes a tiny squint on mobile. With `<picture>`, you can serve a zoomed-in portrait crop for mobile and the full landscape for desktop — completely different image compositions per breakpoint.

Use `<picture>` when:
- You want to serve modern formats (AVIF, WebP) with JPEG/PNG fallback.
- The image composition should change at different breakpoints (art direction).
- You need both format and resolution control simultaneously.

Use `<img srcset>` alone when you just need resolution variants of the same crop in the same format.

## 3. Core concept

Think of `<picture>` like a **menu with substitutions**. The waiter (browser) reads down the list of options, picks the first item you can make (supported format + matching media query), and serves it. If nothing on the list works, they default to the house special (the `<img>`).

**Format negotiation pattern:**

```html
<picture>
  <!-- Best compression: try AVIF first -->
  <source srcset="image.avif" type="image/avif">
  <!-- Good compression, wide support: try WebP second -->
  <source srcset="image.webp" type="image/webp">
  <!-- Universal fallback: JPEG -->
  <img src="image.jpg" alt="Description" width="800" height="600">
</picture>
```

Order matters: the browser picks the FIRST `<source>` whose `type` it supports. If AVIF comes second, it's never used on AVIF-capable browsers — they already matched the first source.

**Art direction pattern:**

```html
<picture>
  <!-- Desktop: wide landscape crop -->
  <source
    media="(min-width: 800px)"
    srcset="wide-landscape.jpg 1200w, wide-landscape@2x.jpg 2400w"
  >
  <!-- Mobile default: portrait/square crop -->
  <img
    src="portrait-crop.jpg"
    srcset="portrait-crop.jpg 400w, portrait-crop@2x.jpg 800w"
    sizes="100vw"
    alt="City skyline"
    width="400"
    height="400"
  >
</picture>
```

The `media` attribute on `<source>` works like a `@media` query. The browser matches the first `<source>` whose `media` condition is true.

**Combined: format + art direction:**

```html
<picture>
  <source media="(min-width: 800px)" srcset="wide.avif" type="image/avif">
  <source media="(min-width: 800px)" srcset="wide.webp" type="image/webp">
  <source media="(min-width: 800px)" srcset="wide.jpg">
  <source srcset="narrow.avif" type="image/avif">
  <source srcset="narrow.webp" type="image/webp">
  <img src="narrow.jpg" alt="Description" width="400" height="400">
</picture>
```

This can get verbose. A CSS `background-image` with media queries or `content` is sometimes cleaner for purely decorative art direction.

**AVIF vs WebP vs JPEG comparison:**

| Format | Browser support | Compression advantage |
|--------|----------------|----------------------|
| JPEG | Universal | Baseline |
| PNG | Universal | Lossless baseline |
| WebP | 97%+ (all modern browsers) | ~30% smaller than JPEG |
| AVIF | 93%+ (Chrome 85+, Firefox 93+, Safari 16+) | ~50–60% smaller than JPEG |

## 4. Diagram

<svg viewBox="0 0 640 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Browser reading picture element sources from top to bottom, picking the first matching source type or media condition">
  <defs>
    <marker id="arr96g" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr96r" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>

  <!-- picture element -->
  <rect x="10" y="10" width="280" height="240" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="145" y="32" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">&lt;picture&gt;</text>

  <rect x="25" y="45" width="250" height="40" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="150" y="60" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">&lt;source type="image/avif"&gt;</text>
  <text x="150" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">try first</text>

  <rect x="25" y="93" width="250" height="40" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="150" y="108" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">&lt;source type="image/webp"&gt;</text>
  <text x="150" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">try second</text>

  <rect x="25" y="141" width="250" height="40" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="156" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">&lt;img src="image.jpg" alt="…"&gt;</text>
  <text x="150" y="172" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fallback — always required</text>

  <text x="145" y="228" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">&lt;/picture&gt;</text>

  <!-- Browser A (supports AVIF) -->
  <rect x="330" y="10" width="140" height="110" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="400" y="30" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Chrome / Firefox</text>
  <text x="400" y="48" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">supports AVIF</text>
  <text x="400" y="68" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">✓ picks AVIF</text>
  <text x="400" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">~50% smaller than JPEG</text>
  <text x="400" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">skips WebP and JPEG</text>
  <line x1="292" y1="65" x2="328" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr96g)"/>

  <!-- Browser B (no AVIF) -->
  <rect x="330" y="136" width="140" height="110" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="400" y="156" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Older Safari</text>
  <text x="400" y="174" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no AVIF → tries WebP</text>
  <text x="400" y="194" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">✓ picks WebP</text>
  <text x="400" y="212" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">~30% smaller than JPEG</text>
  <text x="400" y="228" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">skips JPEG fallback</text>
  <line x1="292" y1="161" x2="328" y2="161" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr96g)"/>

  <!-- Fallback -->
  <rect x="490" y="73" width="140" height="75" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="560" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">IE / legacy</text>
  <text x="560" y="113" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no source matches</text>
  <text x="560" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ &lt;img src&gt; fallback</text>
  <line x1="472" y1="115" x2="488" y2="115" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3" marker-end="url(#arr96r)"/>
</svg>

`<picture>` scans `<source>` elements top-to-bottom; the first match wins; `<img>` is the universal fallback.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>picture Element</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; padding: 1rem; background: #1c2430; color: #e6edf3; }
    h2 { color: #6db33f; }

    .demo { margin-bottom: 2rem; }
    .demo picture { display: block; }
    .demo img { width: 100%; max-width: 600px; height: auto; border-radius: 8px; border: 2px solid #6db33f; }

    .info { font-family: monospace; font-size: 0.8rem; color: #79c0ff; margin-top: 0.5rem; }
  </style>
</head>
<body>

  <h1>picture element demos</h1>

  <!-- Demo 1: Format switching (AVIF → WebP → JPEG) -->
  <div class="demo">
    <h2>1. Format negotiation</h2>
    <picture>
      <!-- Note: using same PNG for demo; real usage would use actual avif/webp files -->
      <source srcset="https://httpbin.org/image/png" type="image/png">
      <img
        src="https://httpbin.org/image/jpeg"
        alt="Sample photo demonstrating format negotiation"
        width="600"
        height="400"
        id="format-img"
      >
    </picture>
    <p class="info" id="format-info">Detecting chosen format…</p>
  </div>

  <!-- Demo 2: Art direction (different crop per breakpoint) -->
  <div class="demo">
    <h2>2. Art direction (resize window to see crop change)</h2>
    <picture>
      <!-- Wide screens: landscape orientation -->
      <source
        media="(min-width: 700px)"
        srcset="https://httpbin.org/image/jpeg"
        width="1200"
        height="600"
      >
      <!-- Small screens: square/portrait orientation -->
      <img
        src="https://httpbin.org/image/png"
        alt="City skyline — landscape on desktop, portrait on mobile"
        width="400"
        height="400"
        id="art-img"
      >
    </picture>
    <p class="info" id="art-info">Source selected: detecting…</p>
  </div>

  <script>
    function showSrc(img, infoEl) {
      function update() {
        infoEl.textContent = "currentSrc: " + (img.currentSrc || img.src).split("/").pop();
      }
      if (img.complete) update();
      else img.addEventListener("load", update);
    }

    showSrc(document.getElementById("format-img"), document.getElementById("format-info"));
    showSrc(document.getElementById("art-img"), document.getElementById("art-info"));

    // Resize listener to show art direction switching
    window.addEventListener("resize", () => {
      const artImg = document.getElementById("art-img");
      document.getElementById("art-info").textContent =
        `Viewport: ${window.innerWidth}px → currentSrc: ${(artImg.currentSrc || artImg.src).split("/").pop()}`;
    });
  </script>
</body>
</html>
```

**How to run:** save as `picture.html`, open in a browser. Resize the browser window and watch the "art-info" paragraph update as the browser switches between sources.

## 6. Walkthrough

- `<source type="image/png">` before `<img src="...jpeg">` — the browser checks if it supports PNG (it does), so it picks the first `<source>`. The `<img>` JPEG fallback is skipped. In a real site, replace these with actual `.avif` and `.webp` URLs generated by your build process.
- `<source media="(min-width: 700px)">` — evaluated against the viewport, just like CSS `@media`. On a 800px viewport, this source matches; on 400px, it doesn't, and the browser falls through to `<img>`.
- `img.currentSrc` — the property (read-only) that reflects which URL the browser chose. Different from `img.src` which is the `<img>` fallback URL.
- The resize listener calls `artImg.currentSrc` again after the window changes. Browsers re-evaluate `<source media>` on resize and switch sources if needed — the element is responsive, not just the initial load.
- The `<img>` element inside `<picture>` is the one that renders. All `width`, `height`, `alt`, `loading`, `decoding`, `class` — everything — goes on `<img>`, not on `<source>` or `<picture>`.

## 7. Gotchas & takeaways

> **The `<img>` inside `<picture>` is mandatory.** It provides the accessible `alt`, the fallback URL, and the rendered output. Without `<img>`, `<picture>` renders nothing.

> **Source order is critical for format switching.** The browser picks the FIRST `<source>` whose `type` and `media` match. AVIF must come before WebP, WebP before JPEG. Reversed order means modern browsers use the old format.

> **Generate AVIF and WebP at build time.** Sharp (Node.js), ImageMagick, Squoosh, or your CDN (Cloudflare, Fastly, Cloudinary) can generate all format variants. Don't do it at request time.

- `<picture>` = `<source>` elements (conditions) + `<img>` (fallback + the actual rendered element).
- Format negotiation: order AVIF → WebP → JPEG. Browser picks first supported type.
- Art direction: `<source media="(min-width:...)">` serves different crops per breakpoint.
- `alt`, `width`, `height`, `loading` all go on `<img>`, not `<source>` or `<picture>`.
- `img.currentSrc` reflects the actually chosen URL (may differ from `img.src`).
- Generate AVIF/WebP at build time; don't rely on on-the-fly conversion in production.
