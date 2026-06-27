---
card: webdev
gi: 82
slug: block-vs-inline-vs-inline-block-elements
title: Block vs inline vs inline-block elements
---

## 1. What it is

Every HTML element has a default **display type** that controls how it flows relative to surrounding content:

- **Block** — takes up the full available width, starts on a new line, pushes content below it. Width, height, margin, and padding all apply normally.
- **Inline** — flows within text, only as wide as its content. Width and height are ignored; vertical margin/padding has limited effect.
- **Inline-block** — flows like inline (sits in a line of text) but respects width, height, and all margin/padding like a block.

These are the three fundamental layout modes that existed before Flexbox and Grid. Understanding them is still essential because they describe the default behaviour of every HTML element.

## 2. Why & when

Most layout bugs for beginners come from not knowing which box model a given element uses. `<span>` with a fixed width "does nothing" — it's inline. `<div>` sits on its own line even if you only need a small badge — it's block. Setting `display: inline-block` on navigation links lets them stack horizontally while still accepting padding.

Block vs inline is baked into HTML defaults:

**Default block elements:** `<div>`, `<p>`, `<h1>`–`<h6>`, `<ul>`, `<ol>`, `<li>`, `<blockquote>`, `<article>`, `<section>`, `<header>`, `<footer>`, `<nav>`, `<main>`, `<form>`, `<table>`.

**Default inline elements:** `<span>`, `<a>`, `<strong>`, `<em>`, `<img>`, `<input>`, `<label>`, `<button>`, `<code>`, `<abbr>`.

Any element's display type can be overridden with CSS: `display: block`, `display: inline`, `display: inline-block`.

## 3. Core concept

Think of a document page:
- **Block elements** are like paragraphs and headings — each one starts on a fresh line and stretches edge-to-edge.
- **Inline elements** are like words in a sentence — they flow left to right inside a paragraph, wrapping to the next line when they run out of space.
- **Inline-block elements** are like photo thumbnails in a sentence — they sit in the flow like words but are treated as rigid boxes with defined dimensions.

**Block:**
```css
/* defaults: */
width: 100%;          /* fills parent width */
height: auto;         /* shrinks to content */
display: block;       /* starts on new line */
/* width, height, all margins & padding work */
```

**Inline:**
```css
/* defaults: */
width: auto;          /* only as wide as content (cannot set) */
height: auto;         /* only as tall as line-height (cannot set) */
display: inline;
/* horizontal margin/padding work; vertical margin ignored; 
   width/height properties have NO effect */
```

**Inline-block:**
```css
display: inline-block;
/* flows like inline but accepts width, height, 
   vertical margin and padding */
```

**The box model difference visualised:**

| Property | block | inline | inline-block |
|----------|-------|--------|--------------|
| Starts new line | yes | no | no |
| width/height settable | yes | no | yes |
| margin (all sides) | yes | horizontal only | yes |
| padding (all sides) | yes | horizontal only* | yes |
| Can contain blocks | yes | no | yes |

*Inline elements can have top/bottom padding that renders visually but does not push surrounding lines apart.

## 4. Diagram

<svg viewBox="0 0 620 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three columns showing block stacking vertically, inline flowing in text, and inline-block sitting in text flow with fixed dimensions">
  <!-- Block column -->
  <text x="100" y="22" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Block</text>
  <rect x="20" y="32" width="160" height="40" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="57" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">&lt;div&gt; full width</text>
  <rect x="20" y="80" width="160" height="40" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">&lt;p&gt; next block</text>
  <rect x="20" y="128" width="160" height="40" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="153" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">&lt;h2&gt; next block</text>
  <text x="100" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">each on its own line</text>
  <text x="100" y="206" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">full width of parent</text>

  <!-- Inline column -->
  <text x="310" y="22" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Inline</text>
  <rect x="220" y="32" width="180" height="80" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <rect x="228" y="44" width="32" height="16" rx="2" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="244" y="56" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">Hi</text>
  <rect x="262" y="44" width="56" height="16" rx="2" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="290" y="56" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">&lt;a&gt;link</text>
  <rect x="320" y="44" width="70" height="16" rx="2" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="355" y="56" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">&lt;strong&gt;</text>
  <rect x="228" y="64" width="42" height="16" rx="2" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="249" y="76" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">wraps</text>
  <text x="310" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">flows in text, width = content</text>
  <text x="310" y="149" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">width/height ignored</text>

  <!-- Inline-block column -->
  <text x="525" y="22" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Inline-block</text>
  <rect x="430" y="32" width="185" height="80" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <rect x="438" y="44" width="50" height="60" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="463" y="74" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">60px</text>
  <text x="463" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">tall</text>
  <rect x="494" y="44" width="50" height="60" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="519" y="74" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">60px</text>
  <text x="519" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">tall</text>
  <rect x="550" y="44" width="50" height="60" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="575" y="74" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">60px</text>
  <text x="575" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">tall</text>
  <text x="525" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">flows in text</text>
  <text x="525" y="149" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">width/height respected</text>
</svg>

Block elements stack vertically; inline elements flow in text; inline-block combines both — flows with text but accepts box-model dimensions.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Display Types</title>
  <style>
    body { font-family: sans-serif; padding: 1rem; }

    /* Block */
    .block-demo div {
      background: #1c2430;
      border: 2px solid #6db33f;
      color: #e6edf3;
      padding: 0.5rem;
      margin-bottom: 0.25rem;
    }

    /* Inline — width/height have no effect */
    .inline-demo span {
      background: #1c2430;
      border: 1px solid #79c0ff;
      color: #79c0ff;
      padding: 0.25rem 0.5rem;
      /* width: 200px;  ← this would be ignored on inline */
    }

    /* Inline-block — width/height DO take effect */
    .ib-demo span {
      display: inline-block;
      background: #1c2430;
      border: 1px solid #6db33f;
      color: #e6edf3;
      width: 80px;
      height: 60px;
      text-align: center;
      line-height: 60px; /* vertically centre text */
      margin: 4px;
    }
  </style>
</head>
<body>

  <h3>Block (each on own line, full width)</h3>
  <div class="block-demo">
    <div>Block one</div>
    <div>Block two</div>
    <div>Block three</div>
  </div>

  <h3>Inline (flows in text, ignores width/height)</h3>
  <p class="inline-demo">
    Sentence with <span>inline A</span> and <span>inline B</span> and <span>inline C</span> flowing together.
  </p>

  <h3>Inline-block (flows in text, respects dimensions)</h3>
  <div class="ib-demo">
    <span>Box 1</span>
    <span>Box 2</span>
    <span>Box 3</span>
    <span>Box 4</span>
  </div>

  <script>
    // Check computed display type of any element
    const div = document.querySelector(".block-demo div");
    console.log(window.getComputedStyle(div).display); // "block"

    const span = document.querySelector(".inline-demo span");
    console.log(window.getComputedStyle(span).display); // "inline"

    const ibSpan = document.querySelector(".ib-demo span");
    console.log(window.getComputedStyle(ibSpan).display); // "inline-block"
  </script>
</body>
</html>
```

**How to run:** save as `display.html`, open in a browser. Resize the window to see inline-block boxes wrap to the next line like words.

## 6. Walkthrough

- `.block-demo div` — each `<div>` starts on a new line and stretches to the container width, even though there's no explicit width set. That's the default block behaviour.
- `.inline-demo span` — `<span>` elements sit side by side in the text flow. If you add `width: 200px` to the CSS here, nothing happens — inline elements ignore width declarations.
- `.ib-demo span` has `display: inline-block` plus `width: 80px; height: 60px`. These take effect: the boxes are fixed-dimension squares that flow horizontally like words and wrap when they run out of horizontal space.
- `line-height: 60px` on a 60px-tall inline-block centres single-line text vertically — a classic trick before Flexbox made centering easy.
- `getComputedStyle(el).display` returns the actual computed display value, even after CSS overrides. Use this in DevTools console to debug "why isn't this element sitting where I expected."

## 7. Gotchas & takeaways

> **`<img>` is inline by default but behaves strangely.** Images sit in a line of text and have a mysterious gap below them — the descender space reserved for letters like `g`, `p`, `y`. Fix: `img { display: block; }` or `vertical-align: bottom`. Most CSS resets do this.

> **Inline-block elements have a whitespace gap.** Adjacent `inline-block` elements have a small gap between them from the whitespace (newlines, spaces) between tags in HTML. Fixes: `font-size: 0` on the parent, or use Flexbox instead.

> **Vertical margin doesn't work on inline elements.** `margin-top: 20px` on a `<span>` does nothing. If you need spacing, change to `inline-block` or `block`.

- Block: new line, full width, all box-model properties work.
- Inline: flows in text, width/height ignored, vertical margin ineffective.
- Inline-block: flows in text, full box-model support.
- Change any element's display with `display: block|inline|inline-block`.
- For modern layouts, prefer Flexbox (`display: flex`) or Grid (`display: grid`) over inline-block.
- `img` is inline by default — set `display: block` to remove the descender gap.
