---
card: webdev
gi: 87
slug: paragraphs-lists-ul-ol-dl
title: Paragraphs, lists (ul, ol, dl)
---

## 1. What it is

HTML provides four core elements for text grouping and lists:

- **`<p>`** — a paragraph of text.
- **`<ul>`** — an **unordered list** (bullet list) when item order doesn't matter.
- **`<ol>`** — an **ordered list** (numbered list) when sequence matters.
- **`<dl>`** — a **description list** (term–definition pairs) for glossaries, metadata, and key-value data.

```html
<p>A paragraph of body text.</p>

<ul>
  <li>Apples</li>
  <li>Oranges</li>
</ul>

<ol>
  <li>Preheat oven to 180 °C</li>
  <li>Mix flour and butter</li>
  <li>Bake for 25 minutes</li>
</ol>

<dl>
  <dt>HTTP</dt>
  <dd>HyperText Transfer Protocol</dd>
  <dt>DNS</dt>
  <dd>Domain Name System</dd>
</dl>
```

## 2. Why & when

These are the workhorses of text content. Understanding when to use each:

- `<p>` — any prose text. Every paragraph of content.
- `<ul>` — unordered items: feature lists, navigation items, tags, ingredients.
- `<ol>` — step-by-step instructions, rankings, numbered procedures.
- `<dl>` — glossaries, FAQs (term = question, definition = answer), metadata panels.

Choosing the right element matters for accessibility: screen readers announce "list, 3 items" or "term, HTTP, definition…" — giving context that bare `<div>` blocks don't provide.

## 3. Core concept

**`<p>` — paragraph:**
- Block element. Each `<p>` gets a top+bottom margin by default.
- Cannot contain block-level elements (no `<div>`, `<h2>`, etc. inside `<p>`).
- Use for prose. Don't use for spacing (use CSS margin/padding instead).

**`<ul>` — unordered list:**
- `<ul>` is the container; each item is a `<li>`.
- Renders as bullet points by default (style with `list-style-type`).
- Items have no inherent order — rearranging them doesn't change meaning.
- Nesting: `<ul>` inside `<li>` creates a sub-list.

**`<ol>` — ordered list:**
- Same structure as `<ul>` but renders as 1, 2, 3 by default.
- Useful attributes:
  - `start="5"` — starts numbering from 5.
  - `reversed` — counts down (3, 2, 1).
  - `type="a"` / `type="I"` — letter or Roman numeral numbering.
- Each `<li>` can have a `value` attribute to override its number.

**`<dl>` — description list:**
- `<dt>` (description term) holds the term or name.
- `<dd>` (description details) holds the value or definition.
- One `<dt>` can have multiple `<dd>` elements (term with several definitions).
- Multiple `<dt>` elements can share one `<dd>` (synonyms sharing a definition).

```html
<dl>
  <dt>Author</dt>
  <dd>Jane Doe</dd>

  <dt>Published</dt>
  <dd><time datetime="2025-03-15">March 15, 2025</time></dd>

  <dt>Tags</dt>
  <dd>HTML</dd>
  <dd>CSS</dd>
  <dd>Accessibility</dd>
</dl>
```

**Nesting lists:**

```html
<ul>
  <li>Frontend
    <ul>
      <li>HTML</li>
      <li>CSS</li>
    </ul>
  </li>
  <li>Backend</li>
</ul>
```

The inner `<ul>` goes inside the `<li>`, not directly inside the outer `<ul>`.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four panels showing p, ul, ol, and dl elements with their rendered output">
  <!-- p -->
  <rect x="10" y="10" width="140" height="100" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="30" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">&lt;p&gt;</text>
  <text x="20" y="50" fill="#e6edf3" font-size="9" font-family="sans-serif">A block of prose</text>
  <text x="20" y="64" fill="#e6edf3" font-size="9" font-family="sans-serif">text. Margins</text>
  <text x="20" y="78" fill="#e6edf3" font-size="9" font-family="sans-serif">above and below.</text>
  <text x="80" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">block · prose only</text>

  <!-- ul -->
  <rect x="162" y="10" width="140" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="232" y="30" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">&lt;ul&gt;</text>
  <text x="175" y="50" fill="#e6edf3" font-size="9" font-family="sans-serif">• Apples</text>
  <text x="175" y="66" fill="#e6edf3" font-size="9" font-family="sans-serif">• Oranges</text>
  <text x="175" y="82" fill="#e6edf3" font-size="9" font-family="sans-serif">• Bananas</text>
  <text x="232" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">unordered · order irrelevant</text>

  <!-- ol -->
  <rect x="314" y="10" width="140" height="100" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="384" y="30" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">&lt;ol&gt;</text>
  <text x="327" y="50" fill="#e6edf3" font-size="9" font-family="sans-serif">1. Preheat oven</text>
  <text x="327" y="66" fill="#e6edf3" font-size="9" font-family="sans-serif">2. Mix batter</text>
  <text x="327" y="82" fill="#e6edf3" font-size="9" font-family="sans-serif">3. Bake</text>
  <text x="384" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ordered · sequence matters</text>

  <!-- dl -->
  <rect x="466" y="10" width="165" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="548" y="30" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">&lt;dl&gt;</text>
  <text x="479" y="48" fill="#79c0ff" font-size="9" font-family="monospace">HTTP</text>
  <text x="495" y="62" fill="#e6edf3" font-size="8" font-family="sans-serif">HyperText Transfer…</text>
  <text x="479" y="77" fill="#79c0ff" font-size="9" font-family="monospace">DNS</text>
  <text x="495" y="91" fill="#e6edf3" font-size="8" font-family="sans-serif">Domain Name System</text>
  <text x="548" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">term–definition pairs</text>

  <!-- Nesting diagram -->
  <rect x="10" y="130" width="620" height="138" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="30" y="152" fill="#8b949e" font-size="10" font-family="sans-serif" font-weight="bold">Nested list — inner &lt;ul&gt; goes inside &lt;li&gt;, not &lt;ul&gt;:</text>
  <text x="30" y="172" fill="#e6edf3" font-size="10" font-family="monospace">&lt;ul&gt;</text>
  <text x="48" y="188" fill="#e6edf3" font-size="10" font-family="monospace">&lt;li&gt;Frontend</text>
  <text x="66" y="204" fill="#6db33f" font-size="10" font-family="monospace">&lt;ul&gt;  ← nested list inside &lt;li&gt;</text>
  <text x="84" y="220" fill="#6db33f" font-size="10" font-family="monospace">&lt;li&gt;HTML&lt;/li&gt;</text>
  <text x="66" y="236" fill="#6db33f" font-size="10" font-family="monospace">&lt;/ul&gt;</text>
  <text x="48" y="252" fill="#e6edf3" font-size="10" font-family="monospace">&lt;/li&gt;</text>
  <text x="30" y="260" fill="#e6edf3" font-size="10" font-family="monospace">&lt;/ul&gt;</text>
</svg>

Four list types for four different semantic needs; nesting works by placing the child list inside a `<li>`, not alongside it.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Lists Demo</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }
    h2 { color: #6db33f; border-bottom: 1px solid #6db33f; }
    dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.25rem 1rem; }
    dt { font-weight: bold; color: #79c0ff; }
    dd { margin: 0; }
    /* Custom counter style */
    ol.steps { counter-reset: step; list-style: none; padding-left: 0; }
    ol.steps li { counter-increment: step; padding-left: 2.5rem; position: relative; margin-bottom: 0.5rem; }
    ol.steps li::before { content: counter(step); position: absolute; left: 0; background: #6db33f; color: white; width: 1.8rem; height: 1.8rem; border-radius: 50%; text-align: center; line-height: 1.8rem; font-size: 0.85rem; }
  </style>
</head>
<body>

  <h2>Unordered list</h2>
  <ul>
    <li>HTML — structure</li>
    <li>CSS — presentation</li>
    <li>JavaScript — behaviour
      <ul>
        <li>DOM manipulation</li>
        <li>Events</li>
        <li>Fetch API</li>
      </ul>
    </li>
  </ul>

  <h2>Ordered list (steps)</h2>
  <ol class="steps" start="1">
    <li>Install Node.js from nodejs.org</li>
    <li>Create a new project directory</li>
    <li>Run <code>npm init -y</code></li>
    <li>Write your first script</li>
  </ol>

  <h2>Ordered list attributes</h2>
  <ol type="I" start="3" reversed>
    <li>Third item (but will show as III, II, I counting down)</li>
    <li>Second item</li>
    <li>First item</li>
  </ol>

  <h2>Description list</h2>
  <dl>
    <dt>HTTP method</dt>
    <dd>GET</dd>

    <dt>Status code</dt>
    <dd>200 OK</dd>

    <dt>Content type</dt>
    <dd>application/json</dd>
    <dd>text/html</dd>  <!-- multiple dd per dt -->
  </dl>

  <script>
    // Count list items
    console.log("ul items:", document.querySelectorAll("ul > li").length);  // direct children only
    console.log("ol items:", document.querySelectorAll("ol > li").length);

    // Read dl term-definition pairs
    const terms = document.querySelectorAll("dt");
    terms.forEach(dt => {
      // Collect all dd siblings until the next dt
      let dd = dt.nextElementSibling;
      const values = [];
      while (dd && dd.tagName === "DD") {
        values.push(dd.textContent.trim());
        dd = dd.nextElementSibling;
      }
      console.log(`${dt.textContent}: ${values.join(", ")}`);
    });
  </script>
</body>
</html>
```

**How to run:** save as `lists.html`, open in a browser.

## 6. Walkthrough

- `<ul>` with nested `<ul>` inside the third `<li>` — the inner list indents automatically. Screen readers announce "list, 3 items" for the outer, then "list, 3 items" for the inner.
- `ol.steps` uses CSS `counter-reset`/`counter-increment` to create custom number bubbles. The HTML structure is still `<ol>` — the custom styling doesn't remove the semantic meaning.
- `<ol type="I" start="3" reversed>` — starts at Roman numeral III and counts down to I. The `type` attribute controls display only; the implicit `value` on each `<li>` still tracks the actual number.
- `<dl>` styled as a CSS grid — `grid-template-columns: max-content 1fr` aligns terms in the first column and definitions in the second. This is a common pattern for metadata panels.
- `document.querySelectorAll("ul > li")` — the `>` child combinator selects only direct `<li>` children of `<ul>`, not the nested list's items. Without `>`, all `<li>` descendants would be selected.

## 7. Gotchas & takeaways

> **Only `<li>` is valid directly inside `<ul>` or `<ol>`.** `<ul><p>Not a list item</p></ul>` is invalid. The browser auto-repairs it, but the result is unpredictable. Every list item must be `<li>`.

> **`<dl>` is not just for dictionaries.** It's the right choice for any key-value data displayed in the UI: article metadata (Author, Date, Tags), product specs (SKU, Weight, Dimensions), form labels and values.

> **Don't nest lists just for visual indentation.** Use CSS `margin-left` or `padding-left` for visual indentation without implying hierarchical structure. Nested lists tell AT that there's a sub-list — use that meaning intentionally.

- `<ul>` = order doesn't matter; `<ol>` = order matters.
- Only `<li>` goes directly inside `<ul>`/`<ol>`.
- Nest lists by placing the inner list inside a `<li>`, not alongside it.
- `<ol>` attributes: `start`, `reversed`, `type` (`1`, `a`, `A`, `i`, `I`).
- `<dl>` = term–definition pairs; one `<dt>` can have multiple `<dd>`.
- `<p>` = prose only — no block elements inside it.
