---
card: webdev
gi: 88
slug: figure-figcaption
title: figure & figcaption
---

## 1. What it is

`<figure>` wraps self-contained content that is referenced from the main text but could be moved without breaking the flow — images, code listings, charts, tables, and quotes. `<figcaption>` provides a caption for that content.

```html
<figure>
  <img src="architecture.png" alt="Microservices diagram showing 5 services">
  <figcaption>Figure 1: A typical microservices architecture with API gateway.</figcaption>
</figure>
```

`<figcaption>` must be the first or last child of `<figure>`. The caption describes the figure content; the `alt` attribute on `<img>` describes the image itself — they serve different audiences and different purposes.

## 2. Why & when

Before HTML5, figures were just `<div>` with a `<p>` caption. The problem: nothing in the markup expressed that the image and caption were one logical unit, or that this unit was self-contained.

`<figure>` + `<figcaption>` solve that:
- **Accessibility** — screen readers associate the caption with the figure. The `<figcaption>` text can serve as the accessible name of the `<figure>`.
- **Semantics** — search engines understand the image-caption relationship.
- **Portability** — the figure unit can be floated, moved to a sidebar, or referenced as "Figure 3" in the text.

Use `<figure>` when:
- An image, diagram, or chart is referenced from the surrounding text.
- A code listing is a standalone example (especially in tutorials).
- A blockquote is a self-contained pull quote.
- A table is a standalone data presentation.

Don't use `<figure>` for purely decorative images, inline icons, or images that aren't referenced from the text.

## 3. Core concept

Think of `<figure>` like a **labelled exhibit case in a museum**. The case (the `<figure>`) holds the exhibit item (image/code/chart) and a label plate (the `<figcaption>`). The label describes what's in the case; together they're one unit that could be physically moved to another wall (floated in layout) without losing its meaning.

**`<figure>` can contain:**
- Images: `<img>`, `<picture>`
- Code: `<pre><code>...</code></pre>`
- Quotes: `<blockquote>`
- Tables: `<table>`
- Video/audio: `<video>`, `<audio>`
- Multiple related images

```html
<!-- Figure with code listing -->
<figure>
  <pre><code>
function greet(name) {
  return `Hello, ${name}!`;
}
  </code></pre>
  <figcaption>Listing 1: A simple greeting function in JavaScript.</figcaption>
</figure>

<!-- Figure with multiple images -->
<figure>
  <img src="before.png" alt="Site layout before redesign">
  <img src="after.png" alt="Site layout after redesign">
  <figcaption>Before and after the 2025 redesign.</figcaption>
</figure>

<!-- Figure with blockquote -->
<figure>
  <blockquote>
    <p>The web is for everyone.</p>
  </blockquote>
  <figcaption>— Tim Berners-Lee, inventor of the World Wide Web</figcaption>
</figure>
```

**`alt` vs `<figcaption>`:**
- `alt` on `<img>` is a text alternative for the image — read when the image fails to load or by AT users who don't see images. It should describe what the image shows.
- `<figcaption>` provides context and meaning — why this image is here, what it illustrates, what Figure 3 is about. It's visible to all users.

They complement each other: `alt="Microservices diagram"` + `<figcaption>Figure 1: Architecture after migrating from monolith to five independent services.</figcaption>`.

## 4. Diagram

<svg viewBox="0 0 560 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Structure of figure element showing image inside with figcaption below as its last child">
  <!-- Outer figure box -->
  <rect x="20" y="20" width="520" height="200" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="40" y="44" fill="#6db33f" font-size="13" font-family="monospace" font-weight="bold">&lt;figure&gt;</text>

  <!-- Image inside -->
  <rect x="40" y="55" width="480" height="100" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="280" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Content: &lt;img&gt; / &lt;pre&gt;&lt;code&gt; / &lt;video&gt; / &lt;blockquote&gt;</text>
  <text x="280" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">alt="describes what image SHOWS" (for AT when image not seen)</text>
  <rect x="100" y="112" width="360" height="30" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="0.8"/>
  <text x="280" y="131" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">alt="Microservices architecture with 5 services"</text>

  <!-- figcaption -->
  <rect x="40" y="162" width="480" height="40" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.2"/>
  <text x="280" y="178" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">&lt;figcaption&gt;</text>
  <text x="280" y="195" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Figure 1: Architecture after migrating to microservices — visible to all users</text>

  <text x="520" y="228" fill="#8b949e" font-size="10" text-anchor="end" font-family="monospace">&lt;/figure&gt;</text>
</svg>

`<figcaption>` is the last (or first) child of `<figure>` and is visible text; `alt` on `<img>` is the invisible text fallback for the image itself.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>figure & figcaption</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }

    figure {
      border: 1px solid #6db33f;
      border-radius: 8px;
      padding: 1rem;
      margin: 1.5rem 0;
      background: #1c2430;
    }
    figcaption {
      margin-top: 0.75rem;
      font-size: 0.875rem;
      color: #8b949e;
      font-style: italic;
      border-top: 1px solid #8b949e33;
      padding-top: 0.5rem;
    }
    figure img   { max-width: 100%; border-radius: 4px; }
    figure pre   { background: #0d1117; color: #e6edf3; padding: 1rem; border-radius: 4px; overflow-x: auto; }
    figure blockquote { border-left: 4px solid #6db33f; margin: 0; padding: 0.5rem 1rem; color: #e6edf3; font-size: 1.1rem; }
  </style>
</head>
<body>
  <p>The system uses a layered architecture, shown in Figure 1.</p>

  <!-- Figure 1: image -->
  <figure id="fig-arch">
    <img src="https://httpbin.org/image/png" alt="Network diagram with three layers: client, server, database" width="400" height="150">
    <figcaption>Figure 1: Three-tier architecture — client, application server, and database.</figcaption>
  </figure>

  <p>The greeting function in Listing 1 demonstrates closures.</p>

  <!-- Figure 2: code listing -->
  <figure id="fig-code">
    <pre><code>function makeGreeter(greeting) {
  return function(name) {
    return `${greeting}, ${name}!`;
  };
}
const hi = makeGreeter("Hello");
console.log(hi("Alice")); // "Hello, Alice!"</code></pre>
    <figcaption>Listing 1: <code>makeGreeter</code> returns a closure over the <code>greeting</code> variable.</figcaption>
  </figure>

  <!-- Figure 3: blockquote -->
  <figure id="fig-quote">
    <blockquote>
      <p>The Web is more a social creation than a technical one.</p>
    </blockquote>
    <figcaption>— Tim Berners-Lee, <cite>Weaving the Web</cite>, 1999</figcaption>
  </figure>

  <script>
    // figure elements are accessible via querySelector
    const figures = document.querySelectorAll("figure");
    figures.forEach((fig, i) => {
      const caption = fig.querySelector("figcaption");
      console.log(`Figure ${i + 1} caption: "${caption?.textContent.trim()}"`);
    });
  </script>
</body>
</html>
```

**How to run:** save as `figure.html`, open in a browser.

## 6. Walkthrough

- `<figure id="fig-arch">` — the `id` lets the surrounding prose reference it: `<a href="#fig-arch">Figure 1</a>`. That link-to-figure pattern is semantically clean and gives screen reader users a navigation path.
- `alt="Network diagram with three layers"` — describes the image content: what's depicted. If the image fails to load, this text appears in its place. It should be specific enough that a sighted and non-sighted user get equivalent information.
- `<figcaption>Figure 1: Three-tier architecture...</figcaption>` — adds interpretive context: what the diagram illustrates and why it's in the document. This is always visible.
- The code listing `<figure>` wraps `<pre><code>...</code></pre>` — a self-contained example with a caption linking it to the prose ("Listing 1").
- `<cite>` inside `<figcaption>` marks the title of a creative work. Browsers italicise `<cite>` by default.
- `figure.querySelector("figcaption")` — each `<figure>` should have at most one `<figcaption>` (first or last child). The `?.textContent.trim()` handles missing captions gracefully.

## 7. Gotchas & takeaways

> **`<figure>` without `<figcaption>` is still valid.** If there's no caption needed, omit `<figcaption>`. Use `<figure>` alone to semantically mark content as a self-contained unit referenced from the text.

> **`<figcaption>` must be first or last child of `<figure>`.** A `<figcaption>` sandwiched between two images is invalid. Put it at the bottom (most common) or top.

> **`alt` and `<figcaption>` are not redundant.** They serve different purposes and different audiences. `alt` is the text alternative when the image isn't available; `<figcaption>` is supplementary context always visible to everyone.

- `<figure>` = any self-contained referenced content (images, code, charts, quotes).
- `<figcaption>` = visible caption; must be first or last child of `<figure>`.
- `alt` on `<img>` ≠ `<figcaption>` — `alt` replaces the image; caption supplements it.
- Link figures from prose with `<a href="#fig-id">Figure N</a>`.
- `<figure>` without `<figcaption>` is valid when no caption is needed.
