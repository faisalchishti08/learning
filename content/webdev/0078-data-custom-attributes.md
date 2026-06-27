---
card: webdev
gi: 78
slug: data-custom-attributes
title: data-* custom attributes
---

## 1. What it is

**`data-*` attributes** (pronounced "data dash") are custom HTML attributes you define yourself. Any attribute whose name starts with `data-` followed by at least one character is a valid HTML5 data attribute:

```html
<button data-user-id="42" data-action="delete" data-confirm="true">
  Delete User
</button>
```

The browser ignores the values but stores them in the DOM. JavaScript reads and writes them through the `dataset` property:

```js
const btn = document.querySelector("button");
console.log(btn.dataset.userId);  // "42"    (data-user-id → userId)
console.log(btn.dataset.action);  // "delete"
```

`data-*` attributes are the standard way to embed custom data in HTML without inventing fake attributes like `userid="42"` (which is invalid HTML) or bloating `class` with non-styling information.

## 2. Why & when

Before `data-*` (HTML4 era), developers stored extra data in `class` names (`class="user-42"`) or in invalid custom attributes (`userid="42"`). Both are hacks. HTML5 introduced `data-*` as the sanctioned extension mechanism.

Use `data-*` when:
- You need to pass data from server-rendered HTML to JavaScript without extra API calls.
- A JS event handler needs context about the element it's acting on (which item to delete, which tab is active, which slide to go to).
- You want to drive behaviour with HTML configuration instead of JS constants.

Don't use `data-*` for:
- Data that should be visible to users (use element content or standard attributes).
- Accessibility information (use `aria-*` attributes instead).
- Replacing a real API — if data is large or changes often, fetch it dynamically.

## 3. Core concept

Think of `data-*` attributes as **sticky notes on an element**. The browser doesn't read the notes; it just keeps them attached. Your JavaScript reads the notes to decide what to do when the element is interacted with.

**Name conversion rules** — attribute names use kebab-case in HTML; the `dataset` property converts them to camelCase automatically:

| HTML attribute | `dataset` key |
|----------------|--------------|
| `data-user-id` | `dataset.userId` |
| `data-max-retries` | `dataset.maxRetries` |
| `data-x` | `dataset.x` |
| `data-my-long-name` | `dataset.myLongName` |

The conversion: strip `data-`, then convert each `-X` to uppercase `X`.

**Reading and writing:**

```js
const el = document.querySelector("[data-user-id]");

// Read
el.dataset.userId          // "42" (always a string)

// Write
el.dataset.userId = "99";  // sets data-user-id="99" on the element

// Delete
delete el.dataset.userId;  // removes the data-user-id attribute

// Check existence
"userId" in el.dataset     // true / false
```

Values are always strings. Parse numbers and booleans explicitly:

```js
const count = parseInt(el.dataset.count, 10);
const active = el.dataset.active === "true";
```

**CSS can read `data-*` too:**

```css
[data-theme="dark"] { background: #1c2430; color: #e6edf3; }
[data-active="true"] { font-weight: bold; }
```

This is a clean way to drive CSS from JS-toggled HTML state without adding/removing classes.

## 4. Diagram

<svg viewBox="0 0 620 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="data-* attributes stored on an HTML element read by JavaScript via dataset property with kebab-to-camelCase conversion">
  <defs>
    <marker id="arr78g" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr78b" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- HTML element -->
  <rect x="20" y="20" width="280" height="120" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="44" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">HTML</text>
  <text x="35" y="65" fill="#e6edf3" font-size="11" font-family="monospace">&lt;button</text>
  <text x="55" y="83" fill="#79c0ff" font-size="10" font-family="monospace">data-user-id="42"</text>
  <text x="55" y="99" fill="#79c0ff" font-size="10" font-family="monospace">data-action="delete"</text>
  <text x="55" y="115" fill="#79c0ff" font-size="10" font-family="monospace">data-confirm="true"</text>
  <text x="35" y="131" fill="#e6edf3" font-size="11" font-family="monospace">&gt;Delete&lt;/button&gt;</text>

  <!-- Arrow -->
  <line x1="302" y1="80" x2="338" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr78g)"/>
  <text x="320" y="73" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">dataset</text>

  <!-- JS dataset -->
  <rect x="340" y="20" width="260" height="120" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="44" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">JS  btn.dataset</text>
  <text x="360" y="65" fill="#8b949e" font-size="10" font-family="monospace">.userId   →  "42"</text>
  <text x="360" y="83" fill="#8b949e" font-size="10" font-family="monospace">.action   →  "delete"</text>
  <text x="360" y="101" fill="#8b949e" font-size="10" font-family="monospace">.confirm  →  "true"</text>
  <text x="360" y="125" fill="#6db33f" font-size="9" font-family="sans-serif">kebab-case → camelCase auto</text>

  <!-- CSS note -->
  <rect x="20" y="165" width="580" height="48" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="35" y="185" fill="#8b949e" font-size="10" font-family="monospace">/* CSS can select by data-* value */</text>
  <text x="35" y="203" fill="#6db33f" font-size="10" font-family="monospace">[data-action="delete"] { background: #f85149; color: white; }</text>
</svg>

`data-user-id` in HTML becomes `dataset.userId` in JS — kebab-case stripped and camelCased automatically.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>data-* Attributes</title>
  <style>
    button { padding: 0.5rem 1rem; margin: 0.25rem; cursor: pointer; }
    [data-variant="danger"]  { background: #f85149; color: white; border: none; border-radius: 4px; }
    [data-variant="primary"] { background: #6db33f; color: white; border: none; border-radius: 4px; }
    #log { margin-top: 1rem; font-family: monospace; background: #1c2430; color: #e6edf3; padding: 1rem; border-radius: 4px; }
  </style>
</head>
<body>

  <button data-user-id="1" data-action="edit"   data-variant="primary">Edit Alice</button>
  <button data-user-id="2" data-action="delete" data-variant="danger">Delete Bob</button>
  <button data-user-id="3" data-action="edit"   data-variant="primary">Edit Charlie</button>

  <div id="log">Click a button…</div>

  <script>
    // Single handler reads data from whichever button was clicked
    document.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const { userId, action, variant } = btn.dataset;
        document.getElementById("log").textContent =
          `Action: ${action}  |  User ID: ${userId}  |  Variant: ${variant}`;
      });
    });

    // Writing a data attribute from JS
    const firstBtn = document.querySelector("button");
    firstBtn.dataset.lastClicked = new Date().toISOString();
    console.log(firstBtn.getAttribute("data-last-clicked")); // ISO timestamp string

    // Iterating all data attributes
    for (const [key, value] of Object.entries(firstBtn.dataset)) {
      console.log(`${key}: ${value}`);
    }
  </script>
</body>
</html>
```

**How to run:** save as `data-attrs.html`, open in a browser. Click the buttons and watch the log update.

## 6. Walkthrough

- `data-user-id="1"` on each button stores the user's ID in HTML. The JS event handler doesn't need a lookup table — it reads the ID off the element that was clicked.
- `{ userId, action, variant } = btn.dataset` — destructuring `dataset` works because `dataset` is a `DOMStringMap` object. All values are strings.
- `[data-variant="danger"]` in CSS — attribute selectors on `data-*` values let you drive styling from the same HTML data that JS uses. One source of truth, two consumers (CSS + JS).
- `firstBtn.dataset.lastClicked = new Date().toISOString()` — writing to `dataset` creates or updates the corresponding `data-last-clicked` attribute on the element. Check it in DevTools Elements panel to verify.
- `getAttribute("data-last-clicked")` — the attribute name uses kebab-case (what's in the HTML); `dataset.lastClicked` uses camelCase (the JS API).
- `Object.entries(btn.dataset)` — iterates all `data-*` attributes as `[camelCaseKey, value]` pairs.

## 7. Gotchas & takeaways

> **All values are strings.** `data-count="0"` gives `dataset.count === "0"` (string), not `0` (number). Always parse: `parseInt(el.dataset.count, 10)` or `el.dataset.flag === "true"`.

> **Don't use `data-*` for sensitive data.** Values are visible in DevTools and the page source. Never store passwords, tokens, or PII in `data-*` attributes.

> **`data-*` doesn't help accessibility.** Screen readers ignore `data-*` entirely. For semantic roles and states, use `aria-*` attributes (`aria-expanded`, `aria-label`, etc.).

- `data-user-id` in HTML → `dataset.userId` in JS (kebab → camelCase).
- Read: `el.dataset.key`. Write: `el.dataset.key = value`. Delete: `delete el.dataset.key`.
- Values are always strings — parse numbers and booleans explicitly.
- CSS can select on `data-*` values with attribute selectors `[data-key="value"]`.
- Not for sensitive data (visible in source) or accessibility (use `aria-*` for that).
