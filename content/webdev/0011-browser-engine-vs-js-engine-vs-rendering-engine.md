---
card: webdev
gi: 11
slug: browser-engine-vs-js-engine-vs-rendering-engine
title: Browser engine vs JS engine vs rendering engine
---

## 1. What it is

A browser is several specialised "engines" working together. Three names get mixed up:

- **Rendering engine** (a.k.a. **layout/browser engine**) — turns **HTML + CSS** into pixels on screen. It parses markup, builds the DOM and CSSOM, computes layout, and paints. Examples: **Blink** (Chrome/Edge), **WebKit** (Safari), **Gecko** (Firefox).
- **JavaScript engine** — executes **JavaScript** (and WebAssembly). It parses, compiles, and runs your scripts fast. Examples: **V8** (Chrome/Edge/Node), **JavaScriptCore** (Safari), **SpiderMonkey** (Firefox).
- **Browser engine** — loosely, the **core that ties it together** (the rendering engine plus glue: networking, the event loop, coordinating the JS engine). In common usage "browser engine" and "rendering engine" are often used interchangeably.

Short version: **rendering engine = HTML/CSS → pixels; JS engine = runs JavaScript; browser engine = the coordinating core.**

## 2. Why & when

Knowing which engine does what explains a lot of real behaviour:

- **Compatibility** — "works in Chrome, breaks in Safari" usually means a **rendering-engine** difference (Blink vs WebKit). On iOS, *every* browser is forced to use WebKit, so Chrome-on-iOS behaves like Safari.
- **Performance** — JavaScript speed is about the **JS engine** (V8's optimisations); smooth scrolling/animation is about the **rendering engine** (layout/paint/compositing).
- **Node.js** — Node is **V8 (a JS engine) without a rendering engine**. That's why there's no `document` or `window` in Node: no rendering engine, no DOM.

You care when testing across browsers, debugging a "jank" (rendering) vs a "slow script" (JS), or understanding why server-side JS has no DOM.

## 3. Core concept

Picture the browser as a pipeline with two cooperating engines:

1. **Networking** fetches the HTML.
2. The **rendering engine** parses HTML → **DOM tree**, parses CSS → **CSSOM**, combines them into a **render tree**, computes **layout** (positions/sizes), then **paints** and **composites** layers into pixels.
3. When it hits a `<script>`, it hands the code to the **JS engine**, which compiles and runs it. JavaScript can **read and change the DOM** (via the `document` API the rendering engine exposes), which can force the rendering engine to re-layout and repaint.
4. The **event loop** (part of the browser core) coordinates: it runs JS tasks, handles events, and schedules rendering — one main thread, taking turns.

Crucial relationships:

- The DOM is the **bridge**. The rendering engine builds it; the JS engine manipulates it. Neither "owns" JavaScript-on-the-page alone — they collaborate through the DOM API.
- The DOM API (`document`, `window`) is provided by the **browser/rendering environment**, *not* the JS language. That's why the exact same JS engine (V8) runs in Node with **no** `document` — Node doesn't include a rendering engine.

| Engine | Eats | Produces | Examples |
|---|---|---|---|
| Rendering | HTML + CSS | DOM, layout, pixels | Blink, WebKit, Gecko |
| JavaScript | JS / WASM | program execution | V8, JavaScriptCore, SpiderMonkey |
| Browser (core) | everything | coordination, event loop | Chromium, etc. |

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inside the browser core, a rendering engine and a JS engine cooperate through the DOM">
  <rect x="40" y="30" width="560" height="190" rx="12" fill="none" stroke="#30363d" stroke-dasharray="4 4"/>
  <text x="320" y="50" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Browser engine (core: networking + event loop + coordination)</text>

  <rect x="70" y="80" width="220" height="110" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="180" y="104" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">Rendering engine</text>
  <text x="180" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">HTML + CSS → DOM/CSSOM</text>
  <text x="180" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">→ layout → paint → pixels</text>
  <text x="180" y="162" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Blink / WebKit / Gecko</text>

  <rect x="350" y="80" width="220" height="110" rx="10" fill="#1c2430" stroke="#79c0ff"/>
  <text x="460" y="104" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif">JS engine</text>
  <text x="460" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">parse → compile → run JS</text>
  <text x="460" y="162" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">V8 / JSCore / SpiderMonkey</text>

  <line x1="290" y1="135" x2="350" y2="135" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="350" y1="150" x2="290" y2="150" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="320" y="200" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">DOM API bridges them</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Two engines, one core; JavaScript reaches the page only through the DOM the rendering engine builds.

## 5. Runnable example

Prove that the DOM belongs to the **rendering environment**, not the JS engine, by running the *same* JavaScript in two places.

```js
// save as where.js
// This is pure JS-engine work — runs identically in browser and Node:
const sum = [1, 2, 3].reduce((a, b) => a + b, 0);
console.log("JS engine result:", sum);   // 6 in BOTH

// This touches the DOM — provided by the RENDERING engine, only in a browser:
try {
  console.log("document.title:", document.title);
} catch (e) {
  console.log("No DOM here:", e.message); // ReferenceError: document is not defined
}
```

**How to run, two ways:**
- In **Node**: `node where.js` → prints `JS engine result: 6`, then `No DOM here: document is not defined`.
- In a **browser**: put it in `<script src="where.js">` (or paste into the DevTools console) → prints `JS engine result: 6`, then a real `document.title`.

## 6. Walkthrough

- The `reduce` line is **pure language** — arrays, arrow functions, arithmetic. It's handled entirely by the **JS engine** (V8 in both Chrome and Node), so it prints `6` everywhere. Same engine → same result.
- The `document.title` line reaches for the **DOM**. `document` is not part of JavaScript; it's an object the **rendering engine** injects into the page's global scope.
- In the **browser**, the rendering engine has built a DOM, so `document.title` works and shows the page title.
- In **Node**, there is **no rendering engine** — V8 runs alone — so `document` simply doesn't exist, and we catch `document is not defined`.
- This cleanly separates the two engines: JavaScript execution is one job (JS engine); the DOM and pixels are another (rendering engine). Node took V8 and left the rendering engine behind, which is exactly why server-side JS has no `window`/`document`.

## 7. Gotchas & takeaways

> **"It works in Chrome but not Safari" is usually a rendering-engine gap**, not a JavaScript problem — Blink vs WebKit implement CSS/HTML features at different times. And on **iOS**, all browsers (even "Chrome") are required to use WebKit, so they share Safari's rendering quirks.

> **The DOM is not JavaScript.** `document`/`window` come from the browser's rendering environment. That's why the identical V8 engine in Node has no DOM — and why front-end code that assumes `window` crashes when run on the server (a common SSR pitfall).

- Rendering engine: HTML+CSS → DOM, layout, pixels (Blink/WebKit/Gecko).
- JS engine: parses and runs JavaScript/WASM (V8/JavaScriptCore/SpiderMonkey).
- Browser engine/core: ties them together with networking and the event loop.
- They meet at the **DOM**, which the rendering engine owns and the JS engine manipulates.
