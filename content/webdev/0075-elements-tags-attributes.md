---
card: webdev
gi: 75
slug: elements-tags-attributes
title: Elements, tags & attributes
---

## 1. What it is

HTML is built from three interlocking concepts:

- **Element** — the logical unit: a paragraph, a link, an image. What you see in the rendered page.
- **Tag** — the markup syntax that creates an element. Usually comes in pairs: an **opening tag** (`<p>`) and a **closing tag** (`</p>`). The content between them is the element's content.
- **Attribute** — extra information attached to an opening tag as `name="value"` pairs. Attributes modify behaviour, appearance, or provide metadata.

```html
<a href="https://example.com" target="_blank">Visit Example</a>
│  │                          │               │
│  │                          attribute       content
│  └─ opening tag with attributes
└─ element name (anchor)
```

The whole thing — `<a href="...">Visit Example</a>` — is the **element**. `<a>` is the opening **tag**. `href` and `target` are **attributes**. "Visit Example" is the **text content**.

## 2. Why & when

Tags are the syntax; elements are the meaning. Understanding the difference matters when:
- Reading error messages ("unexpected end tag" means a closing tag is wrong or missing).
- Using the DOM API (`document.createElement("p")` creates an element, not a tag).
- Writing attributes correctly — they go only on opening tags, never closing tags.

You use this vocabulary constantly: every single thing in an HTML page is an element, every element is created by tags, and most elements accept attributes.

## 3. Core concept

Think of elements like **labelled boxes**. The box label is the element name (`<div>`, `<h1>`, `<img>`). The opening and closing tags are the top and bottom of the box. Attributes are sticky labels on the outside of the box. The content is whatever's inside.

**Anatomy of a tag:**

```
<tagname attribute1="value1" attribute2="value2">
```

Key rules:
- Element names are case-insensitive (`<P>` = `<p>`) but lowercase is the universal convention.
- Attribute values should be quoted (double quotes are the convention). Some values work without quotes if they contain no spaces, but quoting is always safe.
- Boolean attributes have no value — their presence alone means "true": `<input disabled>` is the same as `<input disabled="disabled">`.
- Attributes with no effect are silently ignored (but unknown attributes stay in the DOM and can be read by JS).

**Common attribute types:**

| Type | Example | Notes |
|------|---------|-------|
| URL | `href="https://..."` | Must be a valid URL |
| Text | `alt="description"` | Plain string |
| Enum | `type="submit"` | One of a fixed set of values |
| Boolean | `required`, `disabled`, `hidden` | Presence = true; absence = false |
| Number | `tabindex="0"` | Integer or float |
| ID reference | `for="email"` | Must match an element's `id` |

**Nesting:** elements can contain other elements. The inner element must close before the outer one:

```html
<!-- Valid: inner closes before outer -->
<p>Hello <strong>world</strong>!</p>

<!-- Invalid: overlapping tags -->
<p>Hello <strong>world</p></strong>
```

## 4. Diagram

<svg viewBox="0 0 600 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Anatomy of an HTML element showing opening tag, attributes, content, and closing tag">
  <defs>
    <marker id="arr75b" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="arr75g" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Main code line -->
  <text x="30" y="100" fill="#e6edf3" font-size="16" font-family="monospace">&lt;a href="https://ex.com" target="_blank"&gt;Visit&lt;/a&gt;</text>

  <!-- Opening tag bracket -->
  <line x1="34" y1="108" x2="34" y2="138" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="34" y1="138" x2="155" y2="138" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr75b)"/>
  <text x="50" y="158" fill="#79c0ff" font-size="11" font-family="sans-serif">opening tag</text>

  <!-- href attribute -->
  <line x1="63" y1="82" x2="63" y2="60" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="63" y1="60" x2="160" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr75g)"/>
  <text x="162" y="64" fill="#6db33f" font-size="11" font-family="sans-serif">attribute name="value"</text>

  <!-- Content -->
  <line x1="315" y1="108" x2="315" y2="138" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="315" y1="138" x2="340" y2="138" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr75b)"/>
  <text x="342" y="158" fill="#8b949e" font-size="11" font-family="sans-serif">content</text>

  <!-- Closing tag -->
  <line x1="365" y1="82" x2="365" y2="60" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="365" y1="60" x2="395" y2="60" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr75b)"/>
  <text x="397" y="64" fill="#8b949e" font-size="11" font-family="sans-serif">closing tag</text>

  <!-- Element bracket -->
  <line x1="30" y1="112" x2="30" y2="185" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="30" y1="185" x2="395" y2="185" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="395" y1="185" x2="395" y2="112" stroke="#6db33f" stroke-width="1.5"/>
  <text x="200" y="200" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">← element (tag + attributes + content + closing tag) →</text>
</svg>

The element is the whole unit; the opening tag carries the attributes; the closing tag mirrors the name with a leading `/`.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Elements, Tags & Attributes</title>
</head>
<body>

  <!-- Tag with text content -->
  <h1>Elements Demo</h1>

  <!-- Tag with multiple attributes -->
  <a href="https://example.com" target="_blank" title="Open Example">Hover me</a>

  <!-- Boolean attribute: "disabled" presence alone = true -->
  <button disabled>Can't click me</button>
  <button>Can click me</button>

  <!-- Attribute with no value vs with value -->
  <input type="text" aria-label="Type something" required>

  <script>
    // The DOM exposes element attributes as properties
    const link = document.querySelector("a");
    console.log(link.href);     // "https://example.com/"
    console.log(link.target);   // "_blank"
    console.log(link.title);    // "Open Example"
    console.log(link.tagName);  // "A" (always uppercase in HTML mode)

    const btn = document.querySelector("button[disabled]");
    console.log(btn.disabled);  // true (boolean attribute read as boolean)

    // getAttribute reads the raw attribute string
    console.log(btn.getAttribute("disabled")); // "" (empty string — just present)
  </script>
</body>
</html>
```

**How to run:** save as `elements.html`, open in a browser, check the console (F12).

## 6. Walkthrough

- `<a href="https://example.com" target="_blank" title="Open Example">` — one element, three attributes. The order of attributes doesn't matter to the browser (but conventions exist: `id`, `class`, then everything else).
- `<button disabled>` — a boolean attribute. The browser treats any of these as identical: `disabled`, `disabled=""`, `disabled="disabled"`. Only the presence/absence matters.
- `link.tagName` returns `"A"` in uppercase — the HTML parser normalises tag names to uppercase in the DOM, even though we write them lowercase in source.
- `link.href` returns the fully resolved URL (`"https://example.com/"`), not the raw attribute value. Use `link.getAttribute("href")` to get the original string (`"https://example.com"`).
- `btn.disabled` is `true` (a JS boolean) because the DOM reflects boolean attributes as boolean properties. But `btn.getAttribute("disabled")` returns `""` (empty string), reflecting what's actually written in HTML.

## 7. Gotchas & takeaways

> **`element.href` ≠ `element.getAttribute("href")`** for URL attributes. DOM properties resolve relative URLs and return absolute ones; `getAttribute` gives you the raw string from the HTML source.

> **Attributes only go on opening tags.** `</p class="foo">` is invalid HTML. The parser ignores attributes on closing tags.

> **Attribute names with no value in JS must use `setAttribute`/`removeAttribute`.** Setting `element.disabled = true` works for known boolean properties; for custom boolean attributes use `element.setAttribute("data-active", "")` and `element.removeAttribute("data-active")`.

- Tag = syntax (the angle-bracket markup). Element = the logical unit in the DOM.
- Attributes live only on opening tags, as `name="value"` pairs.
- Boolean attributes: presence = true, absence = false; no value needed.
- Attribute order doesn't matter; lowercase names are convention.
- DOM property access (`.href`, `.src`) often differs from `getAttribute()` — know which you need.
