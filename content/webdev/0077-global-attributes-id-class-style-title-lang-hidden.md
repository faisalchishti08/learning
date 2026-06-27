---
card: webdev
gi: 77
slug: global-attributes-id-class-style-title-lang-hidden
title: Global attributes (id, class, style, title, lang, hidden)
---

## 1. What it is

**Global attributes** are HTML attributes that can be placed on any HTML element — unlike element-specific attributes such as `src` (only `<img>`, `<script>`, `<source>`) or `href` (only `<a>`, `<link>`). HTML5 defines over twenty global attributes; the six most used day-to-day are:

| Attribute | Purpose |
|-----------|---------|
| `id` | Unique identifier for an element on the page |
| `class` | One or more space-separated style/behaviour groups |
| `style` | Inline CSS applied directly to the element |
| `title` | Advisory tooltip text shown on hover |
| `lang` | Language override for the element's content |
| `hidden` | Hides the element (equivalent to `display: none`) |

## 2. Why & when

Global attributes are the main bridge between HTML, CSS, and JavaScript:
- CSS targets elements via `class` (most common) and `id` (for unique elements).
- JS selects elements via `getElementById`, `querySelectorAll(".class")`, `querySelector("[data-*]")`.
- Accessibility tools read `title` and `lang`.
- `hidden` removes an element from view without deleting it from the DOM.

Because they're global, you can add them to any element — `<table id="results">`, `<span lang="fr">`, `<section hidden>` — without breaking HTML validity.

## 3. Core concept

**`id`** — must be unique within a page. If two elements share an `id`, `getElementById` returns the first one and CSS specificity becomes unpredictable. Used for in-page anchor links (`<a href="#section1">`), form label association (`<label for="email">`), and JS targeting.

```html
<section id="about">...</section>
<a href="#about">Go to About</a>  <!-- jumps to that section -->
```

**`class`** — can be shared by many elements and an element can have many classes. Classes are the primary hook for CSS and JS.

```html
<p class="card highlight large">...</p>
<!-- 3 classes: "card", "highlight", "large" -->
```

**`style`** — inline CSS. Highest specificity (overrides external stylesheets). Use sparingly — it mixes presentation into markup and makes maintenance harder. Valid for dynamic JS-generated styles or one-off overrides.

```html
<div style="color: #6db33f; font-weight: bold;">Green bold text</div>
```

**`title`** — shows a tooltip on hover (desktop only; inaccessible on touch devices and not read consistently by screen readers). Don't rely on it for essential information.

```html
<abbr title="Cascading Style Sheets">CSS</abbr>
```

**`lang`** — overrides the document-level language for a specific element. Screen readers switch pronunciation engine; spell checkers use the right dictionary.

```html
<p>The French word for "hello" is <span lang="fr">bonjour</span>.</p>
```

**`hidden`** — a boolean attribute. Adds `display: none` equivalent to the element, removing it from layout and accessibility tree. Can be toggled with JS.

```html
<div id="modal" hidden>I'm invisible</div>
<script>
  document.getElementById("modal").hidden = false; // shows it
</script>
```

`hidden` differs from `visibility: hidden` (invisible but occupies space) and `opacity: 0` (invisible but occupies space and still interactive). `hidden` = not there at all.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Single HTML element showing all six global attributes annotated">
  <defs>
    <marker id="arr77g" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr77b" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Code -->
  <rect x="20" y="90" width="600" height="50" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="30" y="120" fill="#e6edf3" font-size="12" font-family="monospace">&lt;div id="box" class="card" style="color:green" title="tip" lang="en" hidden&gt;</text>

  <!-- id annotation -->
  <line x1="82" y1="90" x2="82" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr77g)"/>
  <text x="82" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">id — unique</text>

  <!-- class annotation -->
  <line x1="150" y1="90" x2="150" y2="40" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr77g)"/>
  <text x="155" y="30" fill="#6db33f" font-size="9" font-family="sans-serif">class — CSS/JS hook</text>

  <!-- style annotation -->
  <line x1="228" y1="90" x2="228" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr77b)"/>
  <text x="228" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">inline CSS</text>

  <!-- title annotation (below) -->
  <line x1="336" y1="140" x2="336" y2="170" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr77b)"/>
  <text x="336" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">title — tooltip</text>

  <!-- lang annotation -->
  <line x1="404" y1="140" x2="404" y2="175" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr77b)"/>
  <text x="404" y="190" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">lang — language</text>

  <!-- hidden annotation -->
  <line x1="468" y1="140" x2="468" y2="215" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr77b)"/>
  <text x="468" y="228" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">hidden — not rendered</text>
</svg>

All six attributes live on the same opening tag; all work on any HTML element.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Global Attributes</title>
  <style>
    .card { border: 1px solid #6db33f; padding: 1rem; border-radius: 6px; margin: 0.5rem; }
    .highlight { background: #1c2430; color: #e6edf3; }
    .large { font-size: 1.2rem; }
  </style>
</head>
<body>

  <!-- id: unique page anchor -->
  <h2 id="greeting">Hello</h2>

  <!-- class: multiple classes on one element -->
  <div class="card highlight large">
    Styled with three classes.
  </div>

  <!-- style: inline override -->
  <p style="color: #6db33f; text-decoration: underline;">Inline green underline.</p>

  <!-- title: hover tooltip -->
  <abbr title="HyperText Markup Language">HTML</abbr> — hover to see the tooltip.

  <!-- lang override -->
  <p>The word <span lang="es" title="Spanish word">hola</span> means hello.</p>

  <!-- hidden: invisible but in DOM -->
  <p id="secret" hidden>You can't see me yet.</p>
  <button onclick="document.getElementById('secret').hidden = false">Reveal</button>

  <script>
    // id lookup — O(1)
    console.log(document.getElementById("greeting").textContent); // "Hello"

    // class query
    const cards = document.querySelectorAll(".card");
    console.log(cards.length); // 1

    // classList API is cleaner than class attribute manipulation
    cards[0].classList.add("active");
    cards[0].classList.remove("large");
    console.log(cards[0].className); // "card highlight active"
  </script>
</body>
</html>
```

**How to run:** save as `global-attrs.html`, open in a browser. Click "Reveal" to toggle `hidden`.

## 6. Walkthrough

- `id="greeting"` — enables `getElementById("greeting")` in JS and the CSS selector `#greeting`. The value must not contain spaces.
- `class="card highlight large"` — three separate class names in one `class` attribute, space-separated. CSS rules for `.card`, `.highlight`, and `.large` all apply simultaneously.
- `style="color: #6db33f"` — inline styles override any external or internal CSS for the same property (they have the highest specificity, short of `!important`).
- `<abbr title="...">` — the canonical use of `title`. When a screen reader announces an `<abbr>`, it reads the expanded form from `title`. For other elements, `title` tooltips are desktop-only — invisible on mobile.
- `lang="es"` on `<span>` overrides the document's `lang="en"`. A Spanish-language screen reader voice kicks in for just that word.
- `hidden` on `<p id="secret">` — the paragraph is in the DOM but not rendered and not announced by assistive technology. Toggling `element.hidden = false` is equivalent to removing the `hidden` attribute.

## 7. Gotchas & takeaways

> **Duplicate `id` values are a bug.** `getElementById` silently returns the first match; CSS specificity becomes unreliable; accessibility is broken. Keep IDs unique. Use `class` for shared styling.

> **`title` is not accessible on mobile.** Hover tooltips don't work on touch screens. Never use `title` as the sole source of important information; use visible text or `aria-label` instead.

> **CSS `display: none` overrides `hidden`, but not the other way.** If you set `hidden` and also `.my-class { display: block }`, the CSS wins and the element appears. Use `hidden` for JS-driven show/hide rather than mixing with CSS that might override it.

- `id` = unique per page; `class` = reusable across many elements.
- Multiple classes: space-separated in one attribute (`class="a b c"`).
- Inline `style` has highest CSS specificity; use it sparingly.
- `title` tooltips are desktop-hover only — not mobile, not reliable for screen readers.
- `lang` on a subtree switches pronunciation for screen readers.
- `hidden` = not rendered + not in accessibility tree; togglable via `element.hidden`.
