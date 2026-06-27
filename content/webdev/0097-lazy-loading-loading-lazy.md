---
card: webdev
gi: 97
slug: lazy-loading-loading-lazy
title: Lazy loading (loading=lazy)
---

## 1. What it is

The **`loading` attribute** on `<img>` and `<iframe>` tells the browser when to fetch the resource relative to its position in the page:

```html
<!-- Load immediately (default for above-the-fold content) -->
<img src="hero.jpg" alt="Hero image" loading="eager">

<!-- Defer loading until near the viewport -->
<img src="photo.jpg" alt="Photo" loading="lazy">

<!-- Same for iframes -->
<iframe src="https://maps.example.com/embed" loading="lazy"></iframe>
```

With `loading="lazy"`, the browser skips fetching the image until the user scrolls near it (typically within ~1200px below the current viewport, adjusted by network speed). This is called **native lazy loading** — no JavaScript library required.

## 2. Why & when

A typical blog article page may have 20–40 images. If all are loaded on page open, the browser fires 40 network requests simultaneously. The user sees the page load slowly and pays for bandwidth they may never use (they might not scroll to the bottom).

Lazy loading:
- **Saves bandwidth** — images never scrolled to are never downloaded.
- **Improves initial page load** — fewer simultaneous requests means the hero content loads faster.
- **Improves Core Web Vitals** — specifically Largest Contentful Paint (LCP) for above-the-fold content and Time to Interactive.

**When to use `loading="lazy"`:**
- Any image below the fold (not visible on initial page load).
- Iframes embedding maps, videos, social widgets.

**When NOT to use `loading="lazy"`:**
- The hero image or any image visible on initial page load — eager-loading these improves LCP.
- Images near the top of the page that will almost certainly be visible immediately.

A common pattern: `loading="eager"` (or omit it) for the first 1–2 images, `loading="lazy"` for everything else.

## 3. Core concept

Think of lazy loading like a **just-in-time delivery service**. Instead of having all the furniture delivered before you move in, you call for each piece only when you're ready to put it in place. The living room furniture arrives first (above the fold); the guest room furniture arrives only when you're actually setting up that room (scrolling there).

**`loading` attribute values:**

| Value | Behaviour |
|-------|----------|
| `eager` | Load immediately, regardless of position. Default for `<img>`. |
| `lazy` | Defer until near viewport. Threshold depends on browser and network conditions. |

**The threshold:**
Browsers don't load `lazy` images at the exact moment they enter the viewport — they start loading a bit before (Chrome's threshold is roughly 1250px below the viewport on fast connections, 2500px on slow ones). This pre-fetch window prevents a gap where the image hasn't arrived yet when the user scrolls to it.

**Preventing CLS with lazy loading:**
Lazy images that have no declared dimensions cause layout shift when they load. Always include `width` and `height`:

```html
<!-- Bad: no dimensions — causes CLS when image loads -->
<img src="photo.jpg" alt="..." loading="lazy">

<!-- Good: browser reserves space before image arrives -->
<img src="photo.jpg" alt="..." width="800" height="600" loading="lazy">
```

**Intersection Observer (JS alternative):**
Before native lazy loading, developers used `IntersectionObserver` to detect when an image entered the viewport and then set `img.src` from a `data-src` attribute. Native `loading="lazy"` is simpler and more performant — no JavaScript needed — but the JS approach still allows finer-grained control (custom thresholds, callbacks on load, etc.).

**`fetchpriority` — companion attribute:**
While `loading` controls *when*, `fetchpriority` controls *how urgently*:

```html
<!-- Hero: load immediately, high priority -->
<img src="hero.jpg" alt="Hero" loading="eager" fetchpriority="high">

<!-- Below-fold thumbnails: lazy + low priority -->
<img src="thumb.jpg" alt="Thumbnail" loading="lazy" fetchpriority="low">
```

## 4. Diagram

<svg viewBox="0 0 600 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Viewport with images above the fold loaded eagerly and images below the fold deferred with lazy loading, showing the threshold zone">
  <!-- Viewport rectangle -->
  <rect x="180" y="10" width="240" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="30" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">↑ Viewport (visible area) ↑</text>

  <!-- Above-fold images -->
  <rect x="195" y="40" width="210" height="40" rx="4" fill="#6db33f" opacity="0.7"/>
  <text x="300" y="55" fill="white" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Hero img  loading="eager"</text>
  <text x="300" y="70" fill="white" font-size="8" text-anchor="middle" font-family="sans-serif">loaded immediately ✓</text>

  <rect x="195" y="88" width="210" height="35" rx="4" fill="#79c0ff" opacity="0.6"/>
  <text x="300" y="104" fill="white" font-size="9" text-anchor="middle" font-family="sans-serif">2nd image  loading="eager"</text>
  <text x="300" y="117" fill="white" font-size="8" text-anchor="middle" font-family="sans-serif">loaded immediately ✓</text>

  <!-- Fold line -->
  <line x1="160" y1="152" x2="440" y2="152" stroke="#f85149" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="448" y="156" fill="#f85149" font-size="9" font-family="sans-serif">↑ fold</text>

  <!-- Threshold zone -->
  <rect x="180" y="152" width="240" height="40" rx="0" fill="#ffeb3b" opacity="0.1" stroke="#ffeb3b" stroke-width="0.5" stroke-dasharray="3,3"/>
  <text x="300" y="177" fill="#ffeb3b" font-size="8" text-anchor="middle" font-family="sans-serif">threshold zone (~1250px) — loading starts here</text>

  <!-- Below-fold images -->
  <rect x="180" y="152" width="240" height="250" rx="0" fill="none"/>

  <rect x="195" y="200" width="210" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="300" y="218" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">img  loading="lazy"</text>
  <text x="300" y="232" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">deferred — not yet fetched</text>

  <rect x="195" y="250" width="210" height="40" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="300" y="268" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">img  loading="lazy"</text>
  <text x="300" y="258" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif" dy="10">not fetched until scrolled near</text>

  <!-- Legend -->
  <rect x="10" y="40" width="155" height="130" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="87" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Network requests</text>
  <rect x="20" y="65" width="12" height="12" rx="2" fill="#6db33f"/>
  <text x="40" y="76" fill="#e6edf3" font-size="8" font-family="sans-serif">eager (immediate)</text>
  <rect x="20" y="85" width="12" height="12" rx="2" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="40" y="96" fill="#e6edf3" font-size="8" font-family="sans-serif">lazy (deferred)</text>
  <text x="20" y="118" fill="#8b949e" font-size="8" font-family="sans-serif">On page load:</text>
  <text x="20" y="132" fill="#6db33f" font-size="8" font-family="sans-serif">2 requests (eager)</text>
  <text x="20" y="147" fill="#8b949e" font-size="8" font-family="sans-serif">0 requests (lazy)</text>
  <text x="20" y="162" fill="#8b949e" font-size="8" font-family="sans-serif">until user scrolls</text>
</svg>

Eager images load immediately; lazy images wait until they're near the viewport — saving initial page-load requests.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lazy Loading Demo</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 1rem; }
    img  { width: 100%; height: auto; border-radius: 8px; margin: 0.5rem 0; border: 2px solid #6db33f; }
    .label { font-size: 0.8rem; font-family: monospace; color: #6db33f; margin-bottom: 0.25rem; }
    .section { margin: 2rem 0; padding: 1rem; background: #1c2430; color: #e6edf3; border-radius: 6px; }
    #load-log { font-family: monospace; font-size: 0.75rem; background: #0d1117; color: #e6edf3; padding: 0.5rem; border-radius: 4px; max-height: 150px; overflow-y: auto; }
  </style>
</head>
<body>

  <h1>Lazy Loading</h1>

  <div id="load-log">Load log:</div>

  <div class="section">
    <div class="label">Above fold — loading="eager" (default)</div>
    <img
      src="https://httpbin.org/image/png"
      alt="Hero image loaded immediately"
      width="600"
      height="300"
      loading="eager"
      fetchpriority="high"
      id="hero"
    >
  </div>

  <p style="text-align:center;padding:1rem;background:#f5f5f5;border-radius:6px">
    ↓ Scroll down to trigger lazy loading ↓
  </p>

  <!-- Spacer to push lazy images below viewport -->
  <div style="height: 400px; display:flex; align-items:center; justify-content:center; color:#888;">
    [scroll space]
  </div>

  <div class="section">
    <div class="label">Below fold — loading="lazy" (deferred)</div>
    <img
      src="https://httpbin.org/image/jpeg"
      alt="Photo loaded when scrolled near"
      width="600"
      height="300"
      loading="lazy"
      id="lazy1"
    >
  </div>

  <div class="section">
    <div class="label">Even further below — loading="lazy"</div>
    <img
      src="https://httpbin.org/image/png"
      alt="Another lazy-loaded photo"
      width="600"
      height="300"
      loading="lazy"
      id="lazy2"
    >
  </div>

  <script>
    const log = document.getElementById("load-log");

    function addLog(msg) {
      const line = document.createElement("div");
      line.textContent = `${new Date().toISOString().slice(11, 23)} — ${msg}`;
      log.appendChild(line);
      log.scrollTop = log.scrollHeight;
    }

    // Log each image load event
    document.querySelectorAll("img").forEach(img => {
      const label = img.id || img.alt.slice(0, 20);
      if (img.complete) {
        addLog(`${label}: already loaded`);
      } else {
        img.addEventListener("load", () => addLog(`${label}: loaded ✓`));
      }
    });

    // Observe when lazy images enter the viewport
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          addLog(`${e.target.id}: entering viewport`);
          observer.unobserve(e.target);
        }
      });
    }, { rootMargin: "0px" });

    document.querySelectorAll("img[loading='lazy']").forEach(img => observer.observe(img));
  </script>
</body>
</html>
```

**How to run:** save as `lazy.html`, open in a browser. Watch the load log at the top — the hero loads immediately; the lazy images load as you scroll toward them. Check DevTools → Network to confirm the timing.

## 6. Walkthrough

- `loading="eager" fetchpriority="high"` on the hero — tells the browser: load this immediately and prioritise it over other pending resources. This is the pattern for LCP images.
- `loading="lazy"` on the below-fold images — the browser skips these in the initial request waterfall. They only fire when the user scrolls near them (within the threshold distance).
- `img.complete` check — images loaded from the browser cache may already be complete when the script runs. The `complete` property is `true` for already-loaded images; in that case, `load` won't fire again.
- `IntersectionObserver` with `rootMargin: "0px"` observes the exact viewport boundary. This is tighter than the browser's own lazy-loading threshold (which is ~1250px). You'll see "entering viewport" in the log slightly after (or simultaneously with) the browser's load event.
- DevTools Network tab: filter to "Img". You'll see the hero load immediately; the lazy images appear only after you scroll. This proves the lazy loading is working.

## 7. Gotchas & takeaways

> **Never lazy-load the LCP (Largest Contentful Paint) image.** This is the most common `loading="lazy"` mistake. If the hero image is lazy-loaded, the browser defers it until it's "near" the viewport — but it's already in the viewport. The result is a delay before the LCP element loads, directly harming Core Web Vitals.

> **Always set `width` and `height` on lazy images.** Without dimensions, the layout doesn't know how much space to reserve. When the image finally loads, the page shifts (CLS). `width` + `height` lets the browser calculate the aspect ratio and reserve the right space even before the image arrives.

> **Lazy loading doesn't work without JavaScript in some older environments.** Native `loading="lazy"` is supported in all modern browsers (Chrome 77+, Firefox 75+, Safari 15.4+). For older Safari, consider a polyfill or `IntersectionObserver` fallback.

- `loading="lazy"` = defer fetch until user scrolls near; zero JS needed.
- `loading="eager"` (or omit) = load immediately. Use for the hero and above-fold images.
- Never lazy-load the LCP image — it hurts Core Web Vitals.
- Always include `width` and `height` to prevent CLS on lazy images.
- `fetchpriority="high"` = boost the hero image in the browser's request queue.
- Check lazy loading worked in DevTools Network tab (filter Img, see request timing).
