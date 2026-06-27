---
card: webdev
gi: 83
slug: nesting-rules-valid-content-models
title: Nesting rules & valid content models
---

## 1. What it is

**Content models** define what types of content are allowed inside each HTML element. Not every element can contain every other element — the HTML spec assigns each element a content model that constrains valid nesting.

For example:
- `<p>` can contain text and inline elements but **not** block elements.
- `<ul>` can contain only `<li>` elements (plus script and template elements).
- `<a>` can contain most content but **not** another `<a>`.

Violating these rules produces **invalid HTML**. Browsers try to recover gracefully (they auto-repair the DOM), but the repaired tree may not be what you intended. Layout breaks, JavaScript DOM operations return wrong results, and validators flag errors.

## 2. Why & when

Nesting rules seem pedantic until the browser "helpfully" auto-repairs your HTML and your JS reads a different structure than what you wrote. Common breakage:

- Wrapping a `<div>` inside a `<p>` — the browser closes the `<p>` early, putting the `<div>` after it.
- Putting a `<button>` inside a `<label>` directly without understanding the implications.
- Nesting `<a>` inside `<a>` — the browser ends the outer `<a>` immediately, breaking both links.

You need to know these rules when: writing templates, debugging layout issues that don't match your HTML structure, or failing HTML validation.

## 3. Core concept

HTML5 defines elements by **content categories**. An element's content model says which categories of content it accepts. The main categories:

| Category | Meaning |
|----------|---------|
| **Flow content** | Almost everything — block and inline elements, text |
| **Phrasing content** | Inline-level: text, `<span>`, `<strong>`, `<a>`, `<img>`, etc. |
| **Heading content** | `<h1>`–`<h6>` |
| **Sectioning content** | `<article>`, `<aside>`, `<nav>`, `<section>` |
| **Embedded content** | `<img>`, `<video>`, `<audio>`, `<iframe>`, etc. |
| **Interactive content** | Elements users can interact with: `<a>`, `<button>`, `<input>`, etc. |
| **Transparent content** | Inherits model from parent (e.g., `<a>`, `<ins>`) |

**Key nesting rules to memorise:**

```html
<!-- ✓ Valid: div contains p -->
<div><p>Text</p></div>

<!-- ✗ Invalid: p contains div (div is flow, not phrasing) -->
<p><div>Text</div></p>
<!-- Browser repairs to: <p></p><div>Text</div><p></p> — NOT what you wrote -->

<!-- ✓ Valid: ul contains li -->
<ul><li>Item</li></ul>

<!-- ✗ Invalid: ul directly contains p -->
<ul><p>Not a list item</p></ul>

<!-- ✓ Valid: a wrapping block content (transparent model allows it) -->
<a href="/"><div class="card">Click this card</div></a>

<!-- ✗ Invalid: a inside a -->
<a href="/outer"><a href="/inner">nested</a></a>

<!-- ✓ Valid: button with text or inline content -->
<button><span>Click</span></button>

<!-- ✗ Invalid: interactive inside interactive -->
<button><a href="/">link inside button</a></button>

<!-- ✗ Invalid: p > h2 (heading is not phrasing content) -->
<p>Text <h2>Heading</h2> more text</p>
```

**`<a>` has a transparent content model:** it accepts whatever its parent allows. If `<a>` is inside a `<div>` (flow content), the `<a>` can contain flow content including `<div>`, `<p>`, etc. This is how clickable card patterns work. But `<a>` inside a `<p>` (phrasing content) can only contain phrasing content.

**Table content model** is especially strict:
- `<table>` → `<thead>`, `<tbody>`, `<tfoot>`, `<tr>`, `<caption>`, `<colgroup>`
- `<tr>` → `<td>`, `<th>` only
- Text or `<div>` directly inside `<table>` is invalid

## 4. Diagram

<svg viewBox="0 0 640 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Valid and invalid nesting examples side by side showing correct p inside div and incorrect div inside p">
  <defs>
    <marker id="arr83g" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr83r" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- Valid -->
  <rect x="10" y="10" width="290" height="245" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="32" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">✓ Valid nesting</text>

  <text x="25" y="56" fill="#e6edf3" font-size="10" font-family="monospace">&lt;div&gt;</text>
  <rect x="30" y="62" width="255" height="36" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="40" y="85" fill="#6db33f" font-size="10" font-family="monospace">&lt;p&gt;Text&lt;/p&gt;</text>
  <text x="25" y="108" fill="#e6edf3" font-size="10" font-family="monospace">&lt;/div&gt;</text>
  <text x="155" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">div (flow) → p (phrasing) ✓</text>

  <text x="25" y="150" fill="#e6edf3" font-size="10" font-family="monospace">&lt;ul&gt;</text>
  <rect x="30" y="156" width="255" height="36" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="40" y="179" fill="#6db33f" font-size="10" font-family="monospace">&lt;li&gt;Item&lt;/li&gt;</text>
  <text x="25" y="202" fill="#e6edf3" font-size="10" font-family="monospace">&lt;/ul&gt;</text>
  <text x="155" y="219" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ul → li (only) ✓</text>
  <text x="155" y="247" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DOM matches source</text>

  <!-- Invalid -->
  <rect x="340" y="10" width="290" height="245" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="485" y="32" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">✗ Invalid nesting</text>

  <text x="355" y="56" fill="#e6edf3" font-size="10" font-family="monospace">&lt;p&gt;</text>
  <rect x="360" y="62" width="255" height="36" rx="3" fill="#0d1117" stroke="#f85149" stroke-width="0.8"/>
  <text x="370" y="85" fill="#f85149" font-size="10" font-family="monospace">&lt;div&gt;block&lt;/div&gt;</text>
  <text x="355" y="108" fill="#e6edf3" font-size="10" font-family="monospace">&lt;/p&gt;</text>
  <text x="485" y="125" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">p (phrasing) → div (flow) ✗</text>

  <text x="355" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Browser auto-repairs to:</text>
  <text x="355" y="165" fill="#8b949e" font-size="9" font-family="monospace">  &lt;p&gt;&lt;/p&gt;</text>
  <text x="355" y="180" fill="#8b949e" font-size="9" font-family="monospace">  &lt;div&gt;block&lt;/div&gt;</text>
  <text x="355" y="195" fill="#8b949e" font-size="9" font-family="monospace">  &lt;p&gt;&lt;/p&gt;</text>
  <text x="485" y="220" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">DOM ≠ source — layout breaks</text>
  <text x="485" y="247" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">JS traversal returns unexpected tree</text>
</svg>

Invalid nesting causes browsers to auto-repair the DOM, producing a structure that doesn't match the source — silent bugs.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Nesting Rules</title>
  <style>
    .demo { font-family: monospace; background: #1c2430; color: #e6edf3; padding: 1rem; margin: 0.5rem 0; border-radius: 4px; }
    .valid   { border-left: 4px solid #6db33f; }
    .invalid { border-left: 4px solid #f85149; }
  </style>
</head>
<body>

  <!-- VALID: p inside div -->
  <div class="demo valid" id="valid-nest">
    <p>Paragraph correctly inside a div.</p>
    <p>Second paragraph.</p>
  </div>

  <!-- INVALID: div inside p — browser will repair this -->
  <p id="bad-p">Before <div style="color:#f85149">Block inside p — invalid!</div> After</p>

  <!-- VALID: card link wrapping block content (transparent model) -->
  <a href="#" id="card-link" style="text-decoration:none;display:block;margin:0.5rem 0">
    <div class="demo valid">Entire card is clickable — valid because a has transparent content model</div>
  </a>

  <!-- INVALID: interactive inside interactive -->
  <!-- <button><a href="/">link in button</a></button> ← don't do this -->

  <script>
    // Show how the browser repaired the invalid p>div nesting
    const p = document.getElementById("bad-p");
    console.log("bad-p children:", p.childNodes.length);
    // Expect: 1 text node "Before " — the <div> got moved OUT of the <p>
    console.log("bad-p childNodes:");
    p.childNodes.forEach((n, i) => {
      console.log(`  [${i}] type=${n.nodeType} value="${(n.textContent || "").trim().slice(0, 40)}"`);
    });

    // Valid nesting is exactly what you wrote
    const valid = document.getElementById("valid-nest");
    console.log("\nvalid-nest children:", valid.children.length); // 2 <p> elements
  </script>
</body>
</html>
```

**How to run:** save as `nesting.html`, open in a browser, check the console. The `bad-p` children demonstrate how the browser repaired invalid HTML.

## 6. Walkthrough

- `<div class="demo valid">` containing `<p>` elements — valid: `<div>` accepts flow content, `<p>` is flow content.
- `<p id="bad-p">Before <div ...>Block...</div> After</p>` — when the parser encounters `<div>` inside `<p>`, it auto-closes the `<p>` (because `<div>` is not valid phrasing content), creates the `<div>`, then creates a new empty `<p>`. The "After" text ends up in a second `<p>`.
- The console output shows `p.childNodes.length` is 1 — only the text "Before " remains inside `<p>`. The `<div>` was moved out. This is silent; no error is thrown.
- `<a href="#"><div ...>card</div></a>` — valid because `<a>` has a transparent content model. The `<a>` is inside `<body>`, which accepts flow content, so the `<a>` can also contain flow content (including `<div>`).
- `valid.children.length === 2` confirms the DOM matches the source — two `<p>` elements as expected.

## 7. Gotchas & takeaways

> **The browser silently repairs invalid nesting.** No error message, no warning in the console — just a DOM tree that doesn't match your source. Use an HTML validator (`validator.w3.org`) or your editor's HTML linter to catch these.

> **`<p>` is particularly strict.** It is a "phrasing content" container — it cannot contain any block-level element. The browser auto-closes it the moment it encounters a block element. This trips up beginners who try to put lists, headings, or divs inside paragraphs.

> **`<a>` wrapping blocks is valid in HTML5 (not HTML4).** Clickable card patterns (`<a><div>...</div></a>`) are valid HTML5 thanks to the transparent content model. But nested `<a>` inside `<a>` is still invalid — the first `<a>` is auto-closed.

- `<p>` accepts only phrasing content (inline elements, text) — never block elements.
- `<ul>` / `<ol>` accepts only `<li>`, `<script>`, `<template>`.
- `<a>` is transparent — inherits parent's content model, enabling clickable card blocks.
- Interactive elements (`<button>`, `<a>`) cannot be nested inside each other.
- Table elements have strict required children: `<tr>` → `<td>`/`<th>` only.
- Validate at `validator.w3.org` or use an HTML linter — broken nesting is silent at runtime.
