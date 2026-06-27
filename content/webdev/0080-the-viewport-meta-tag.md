---
card: webdev
gi: 80
slug: the-viewport-meta-tag
title: The viewport meta tag
---

## 1. What it is

The **viewport meta tag** tells mobile browsers how to scale a web page:

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

Without it, mobile browsers pretend the viewport is ~980 pixels wide (to fit old desktop pages), then shrink the result to fit the screen. Text becomes tiny and the page is unreadable without zooming. With the tag, the browser renders at the device's actual CSS pixel width and at 1:1 scale.

Every responsive web page needs this tag. It's one of the two mandatory `<meta>` tags (the other is `charset`).

## 2. Why & when

When the iPhone launched in 2007, the web was full of desktop-only pages. Safari Mobile solved the rendering problem by pretending it had a 980 px viewport, rendering the full desktop layout, then scaling it down. This worked for read-only content but produced tiny, pinch-to-zoom experiences.

The `viewport` meta tag was Apple's solution: let developers opt in to mobile-first rendering by declaring their pages are designed for small screens. Other browsers adopted it. When CSS media queries arrived, the two features together enabled **responsive design** — layouts that adapt to any screen size.

Include this tag whenever:
- Your page has any CSS layout (essentially always).
- You're writing a responsive design (absolutely always).

Omit it only for internal pages that genuinely target only desktop browsers.

## 3. Core concept

Think of the viewport like a **camera zoom lens**. By default, mobile browsers zoom out to show the whole "desktop stage" (980 px) even on a 390 px physical screen. The viewport tag tells the browser to stop zooming out — use the actual screen width as the stage size.

**The `content` attribute** is a comma-separated list of key-value pairs:

| Property | Common values | Effect |
|----------|--------------|--------|
| `width` | `device-width` or a number (e.g. `320`) | Sets the viewport width in CSS pixels |
| `initial-scale` | `1` (most common), `0.5`, `2` | Zoom level on first load |
| `minimum-scale` | `0.1`–`10` | Minimum pinch-to-zoom level allowed |
| `maximum-scale` | `0.1`–`10` | Maximum pinch-to-zoom level (avoid `1` — blocks accessibility) |
| `user-scalable` | `yes` / `no` | Whether the user can pinch-zoom (avoid `no` — blocks accessibility) |

**Standard responsive tag:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

- `width=device-width` — viewport width = the device's CSS pixel width (390 px on iPhone 14, 360 px on Pixel 7, etc.).
- `initial-scale=1` — load at 1:1 (no zoom in or out).

**CSS pixels vs physical pixels:**
Retina/high-DPI displays pack multiple physical pixels into each CSS pixel (device pixel ratio = 2, 3, or even 4). CSS and the viewport always deal in CSS pixels, not physical pixels. `device-width` on a 390-physical-pixel-wide iPhone 14 Pro is 390 CSS pixels (DPR=3, so 1170 physical pixels are actually lighting up).

**What media queries see:**
After setting `width=device-width`, `@media (max-width: 768px)` matches the CSS pixel width, not the physical pixel width. This is what makes media queries predictable across devices.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without viewport tag: browser renders 980px layout then scales down, making text tiny. With viewport tag: renders at device width, text is readable">
  <!-- Without -->
  <rect x="10" y="10" width="300" height="235" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="160" y="34" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Without viewport meta</text>

  <!-- "980px" virtual viewport -->
  <rect x="30" y="48" width="260" height="100" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">virtual 980 px viewport</text>
  <!-- tiny desktop layout inside -->
  <rect x="35" y="75" width="250" height="10" rx="1" fill="#8b949e" opacity="0.5"/>
  <rect x="35" y="90" width="200" height="8" rx="1" fill="#8b949e" opacity="0.3"/>
  <rect x="35" y="103" width="220" height="8" rx="1" fill="#8b949e" opacity="0.3"/>
  <rect x="35" y="116" width="180" height="8" rx="1" fill="#8b949e" opacity="0.3"/>
  <text x="160" y="142" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">← scaled DOWN to fit 390px screen →</text>

  <text x="160" y="175" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Result: tiny text, must pinch-zoom</text>
  <text x="160" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">media queries: @media(max-width:980px)</text>
  <text x="160" y="208" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">matches at 980px, not device width</text>
  <text x="160" y="228" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">responsive design broken</text>

  <!-- With -->
  <rect x="350" y="10" width="300" height="235" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">With viewport meta</text>

  <!-- 390px device viewport -->
  <rect x="370" y="48" width="260" height="100" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="500" y="68" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">device-width (e.g. 390 px)</text>
  <!-- mobile layout -->
  <rect x="375" y="75" width="250" height="16" rx="2" fill="#6db33f" opacity="0.6"/>
  <rect x="375" y="96" width="250" height="12" rx="2" fill="#79c0ff" opacity="0.4"/>
  <rect x="375" y="113" width="250" height="12" rx="2" fill="#79c0ff" opacity="0.3"/>
  <rect x="375" y="130" width="250" height="10" rx="2" fill="#8b949e" opacity="0.3"/>
  <text x="500" y="142" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">rendered at 1:1 scale</text>

  <text x="500" y="175" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Result: readable text at normal size</text>
  <text x="500" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">media queries: @media(max-width:768px)</text>
  <text x="500" y="208" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">correctly matches device CSS px width</text>
  <text x="500" y="228" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">responsive design works</text>
</svg>

Without the viewport tag, mobile browsers render a shrunk desktop view; with it, they render at the device's true CSS width.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <!-- Remove this tag and open on a phone to see the difference -->
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Viewport Demo</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: sans-serif; padding: 1rem; }

    .hero {
      background: #1c2430;
      color: #e6edf3;
      padding: 2rem;
      border-radius: 8px;
      text-align: center;
    }

    /* Mobile-first: single column */
    .cards { display: flex; flex-direction: column; gap: 1rem; margin-top: 1rem; }
    .card  { background: #6db33f; color: white; padding: 1rem; border-radius: 6px; }

    /* Tablet+: two columns */
    @media (min-width: 600px) {
      .cards { flex-direction: row; flex-wrap: wrap; }
      .card  { flex: 1 1 calc(50% - 0.5rem); }
    }

    /* Desktop: three columns */
    @media (min-width: 900px) {
      .card { flex: 1 1 calc(33% - 0.67rem); }
    }
  </style>
</head>
<body>
  <div class="hero">
    <h1>Responsive Page</h1>
    <p>Viewport: <strong id="vw">?</strong> × <strong id="vh">?</strong> CSS px</p>
    <p>Device Pixel Ratio: <strong id="dpr">?</strong></p>
  </div>

  <div class="cards">
    <div class="card">Card One</div>
    <div class="card">Card Two</div>
    <div class="card">Card Three</div>
  </div>

  <script>
    function update() {
      document.getElementById("vw").textContent = window.innerWidth;
      document.getElementById("vh").textContent = window.innerHeight;
      document.getElementById("dpr").textContent = window.devicePixelRatio;
    }
    update();
    window.addEventListener("resize", update);
  </script>
</body>
</html>
```

**How to run:** save as `viewport.html`, open in a browser. Use DevTools "Toggle Device Toolbar" (Ctrl+Shift+M / Cmd+Shift+M) to simulate different devices and watch the viewport dimensions and card layout change.

## 6. Walkthrough

- `width=device-width` — sets `window.innerWidth` to the CSS pixel width of the device (e.g. 390 for iPhone 14). Without this, `window.innerWidth` would be 980 on mobile.
- `initial-scale=1` — renders at 100% zoom. Without it, browsers may infer a different initial zoom based on the viewport width setting.
- `@media (min-width: 600px)` — fires when the CSS viewport is ≥ 600 CSS pixels. With the viewport tag, this is the actual device width. Without it, a phone would always see the desktop layout because its viewport appears to be 980 px.
- `window.devicePixelRatio` — shows the ratio of physical to CSS pixels. On a Retina display this is 2; on a Super Retina it's 3. Images specified at CSS dimensions display at this multiple of physical pixels.
- The `<strong id="vw">` display updates on resize — try dragging your browser window to watch the numbers and layout change live.

## 7. Gotchas & takeaways

> **Never set `user-scalable=no` or `maximum-scale=1`.** Locking zoom prevents users from increasing text size for readability — it's an accessibility failure. WCAG 1.4.4 requires zoom to at least 200% without loss of content. Many browsers now ignore `user-scalable=no` for this reason.

> **The viewport meta tag does not affect desktop browsers.** Desktop screens are always wider than any `min-width` media query you'd write for mobile, so the tag's effect is invisible on desktop. It only matters for mobile and tablet browsers.

> **`width=device-width` ≠ screen resolution.** A 1440×900 Mac may have a CSS viewport of 1440 px. An iPhone 14 Pro has 1179×2556 physical pixels but a CSS viewport of 393×852 px. CSS pixels and physical pixels are different units.

- Every responsive page needs `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- Without it: mobile renders at 980 px, scales down, media queries fire wrong.
- With it: CSS pixels = device CSS pixel width, media queries work correctly.
- Never disable user zoom (`user-scalable=no`, `maximum-scale=1`) — it blocks accessibility.
- CSS pixels and physical pixels differ on high-DPI displays; `window.devicePixelRatio` shows the ratio.
