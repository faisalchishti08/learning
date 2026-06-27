---
card: webdev
gi: 76
slug: void-self-closing-elements
title: Void / self-closing elements
---

## 1. What it is

A **void element** is an HTML element that cannot have children and therefore has no closing tag. The content model for these elements is empty — you can never put text or child elements inside them.

```html
<!-- Void elements — correct -->
<img src="photo.jpg" alt="A photo">
<br>
<hr>
<input type="text">
<link rel="stylesheet" href="style.css">
<meta charset="UTF-8">

<!-- NOT valid — void elements have no content to close -->
<br></br>   ✗  (wrong)
<img ...></img>  ✗  (wrong)
```

In HTML5, writing a trailing slash (`<br />`) is **optional and ignored** — it's valid but meaningless. In XHTML (a stricter XML-based variant), the slash was required. Many developers still write it out of XHTML habit; it doesn't hurt, but it's not necessary in HTML5.

## 2. Why & when

Void elements exist because some HTML elements inherently represent **standalone objects** that have no textual or structural content: a line break has no content; an image is the content itself; an input field is a widget, not a container.

You encounter void elements constantly:
- `<img>` for images.
- `<input>` for form fields (text boxes, checkboxes, radio buttons, buttons).
- `<br>` for a line break within text (sparingly — prefer CSS margin for spacing).
- `<hr>` for a thematic break (a horizontal rule).
- `<link>` for stylesheets and other document relationships.
- `<meta>` for document metadata.

Knowing which elements are void prevents a common mistake: forgetting to close a regular element because you assumed it was self-closing, or adding a closing tag to a void element and confusing the parser.

## 3. Core concept

Think of void elements as **sealed packages**. A `<div>` or `<p>` is an open box you put things into; you need to close the lid (`</div>`, `</p>`). A `<br>` or `<img>` is a sealed factory-made item — it doesn't open, so there's no lid to close.

**The full list of HTML5 void elements:**

| Element | Purpose |
|---------|---------|
| `<area>` | Clickable area inside `<map>` |
| `<base>` | Base URL for relative links |
| `<br>` | Line break |
| `<col>` | Table column (inside `<colgroup>`) |
| `<embed>` | External content plugin |
| `<hr>` | Thematic break / horizontal rule |
| `<img>` | Image |
| `<input>` | Form control |
| `<link>` | Resource link (stylesheets, icons) |
| `<meta>` | Metadata |
| `<param>` | Parameter for `<object>` |
| `<source>` | Media source for `<picture>`, `<audio>`, `<video>` |
| `<track>` | Subtitle/caption track for media |
| `<wbr>` | Word-break opportunity hint |

**Optional trailing slash:** `<img src="..." />` is identical to `<img src="...">` in HTML5. The slash is stripped by the parser. JSX (React) requires the slash because JSX is XML-based — `<img />` — so you often see it in codebases that mix HTML and JSX.

**Invalid content:** putting anything between a void element's "tag" and a closing tag is an error:
```html
<input type="text">Some text</input>  ← parser ignores "Some text" and the </input>
```

## 4. Diagram

<svg viewBox="0 0 580 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of regular elements with open and close tags vs void elements with no closing tag">
  <!-- Regular element -->
  <rect x="20" y="20" width="240" height="190" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="46" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Regular Element</text>

  <rect x="40" y="60" width="200" height="38" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="140" y="84" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace">&lt;p&gt;</text>
  <text x="140" y="108" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">content lives here</text>
  <rect x="40" y="122" width="200" height="38" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="140" y="146" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace">&lt;/p&gt;</text>

  <text x="140" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">open + close tag pair</text>
  <text x="140" y="197" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">contains children/text</text>

  <!-- Void element -->
  <rect x="310" y="20" width="240" height="190" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="430" y="46" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Void Element</text>

  <rect x="330" y="60" width="200" height="38" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="430" y="84" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="monospace">&lt;img src="…" alt="…"&gt;</text>

  <text x="430" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no closing tag</text>
  <text x="430" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no children allowed</text>

  <rect x="330" y="152" width="200" height="30" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="0.8" stroke-dasharray="3,3"/>
  <text x="430" y="172" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">&lt;/img&gt;  ← invalid</text>

  <text x="430" y="197" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">slash optional: &lt;img … /&gt;</text>
</svg>

Regular elements wrap content between open/close tags; void elements are standalone — no closing tag, no children.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Void Elements</title>
  <style>
    body { font-family: sans-serif; padding: 1rem; }
    hr   { border: 1px solid #6db33f; }
  </style>
</head>
<body>

  <!-- img: void element — all info in attributes -->
  <img src="https://httpbin.org/image/png" alt="Sample image" width="200" height="80">

  <hr>  <!-- thematic break, no closing tag -->

  <!-- input: void element — no children, all config via attributes -->
  <label for="name">Name:</label>
  <input type="text" id="name" name="name" aria-label="Enter your name" required>

  <br>  <!-- line break inside text -->

  <label for="check">Subscribe:</label>
  <input type="checkbox" id="check" name="subscribe">

  <!-- source inside picture: void elements stacked -->
  <picture>
    <source srcset="https://httpbin.org/image/png" media="(min-width: 600px)">
    <img src="https://httpbin.org/image/png" alt="Responsive image">
  </picture>

  <script>
    // Void elements have no childNodes that contain text
    const img = document.querySelector("img");
    console.log(img.childNodes.length); // 0
    console.log(img.src);               // absolute URL to the image
    console.log(img.alt);               // "Sample image"

    // innerHTML on a void element is always empty
    const input = document.querySelector("input");
    console.log(input.innerHTML);       // ""
  </script>
</body>
</html>
```

**How to run:** save as `void.html`, open in a browser. The sample images load from a public test endpoint — no server needed.

## 6. Walkthrough

- `<img src="..." alt="...">` — the image IS the element; there's nothing to put inside it. `src` points to the image; `alt` is the text fallback for screen readers and broken images.
- `<hr>` — a semantic thematic break (not just a visual line). Use it to separate distinct topics, not as a decorative spacer.
- `<input type="checkbox">` — all form controls are void elements. Their "value" is set through attributes (`value=""`, `checked`, `disabled`), never through inner content.
- `<source>` inside `<picture>` — another void element. `<picture>` itself is a regular element (it wraps `<source>` elements and an `<img>`); each `<source>` is void.
- `img.childNodes.length === 0` — void elements never have children, even if you try to add them with `innerHTML`. Browsers silently discard any attempt.
- `img.src` returns the absolute URL; `img.getAttribute("src")` would return the raw `src` attribute value.

## 7. Gotchas & takeaways

> **Not closing a regular element "like a void element" is a parse error.** Writing `<div>content` without `</div>` causes the parser to infer where the div ends — which may not be where you expect. Only elements on the void list can safely omit their closing tag.

> **JSX and HTML have different rules.** In React/JSX, ALL elements without children must self-close (`<br />`, `<img />`, `<MyComponent />`). In HTML, self-closing syntax (`<br />`) is optional and ignored. Don't mix up the two sets of rules.

- Void elements: `<img>`, `<input>`, `<br>`, `<hr>`, `<link>`, `<meta>`, `<source>`, and 7 more.
- No closing tag, no children — ever.
- Trailing slash `<img />` is optional in HTML5 (required in XHTML and JSX).
- All information is carried by attributes.
- `element.childNodes.length === 0` always for void elements.
