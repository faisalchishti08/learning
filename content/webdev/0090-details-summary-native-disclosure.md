---
card: webdev
gi: 90
slug: details-summary-native-disclosure
title: details & summary (native disclosure)
---

## 1. What it is

`<details>` is a native HTML disclosure widget — a collapsible section that users can expand and collapse. `<summary>` provides the visible toggle label. No JavaScript, no CSS tricks, no external library needed.

```html
<details>
  <summary>What is the refund policy?</summary>
  <p>Full refund within 30 days of purchase. No questions asked.</p>
</details>
```

When closed, only the `<summary>` text is visible with a disclosure triangle (▶). Clicking the summary toggles the `<details>` open, revealing all other child content. The `open` attribute controls (and reflects) the open/closed state.

## 2. Why & when

Expanding/collapsing content used to require custom JavaScript with ARIA attributes. `<details>` provides this as a native browser primitive: accessible by default, keyboard-operable, and zero dependencies.

Use `<details>` for:
- FAQ sections (each question = one `<details>`)
- Progressive disclosure in forms (advanced options)
- Code snippet toggles in documentation
- Spoilers in articles
- Debug information in error pages
- Long explanation sections users may not need

Don't use `<details>` for:
- Dropdown navigation menus (use `<nav>` with CSS/JS for full control)
- Accordions where only one panel can be open at a time (native `<details>` doesn't enforce this; needs JS)
- Content so important that users must see it (don't hide critical info behind a toggle)

## 3. Core concept

Think of `<details>` like a **paper folder with a label on the tab**. The label (`<summary>`) is always visible. You can open the folder to see the contents, then close it again. The folder remembers whether it's open or closed via the `open` attribute.

**Structure:**

```html
<details open>       <!-- open attribute: starts expanded -->
  <summary>Label</summary>
  <p>Hidden content revealed when open.</p>
  <ul><li>Also hidden</li></ul>
</details>
```

- `<summary>` must be the first child of `<details>`. If omitted, browsers show a default "Details" label.
- Everything inside `<details>` except `<summary>` is the expandable content.
- The `open` attribute (boolean) toggles the state. Present = open; absent = closed.

**Programmatic control:**

```js
const details = document.querySelector("details");

// Read state
console.log(details.open); // true / false

// Open
details.open = true;

// Close
details.open = false;

// Toggle
details.open = !details.open;

// Event fires when state changes
details.addEventListener("toggle", () => {
  console.log("Now:", details.open ? "open" : "closed");
});
```

**Styling the marker:**

```css
/* Remove default triangle */
details > summary { list-style: none; cursor: pointer; }
details > summary::-webkit-details-marker { display: none; }

/* Custom open/close indicator */
details > summary::before { content: "▶ "; }
details[open] > summary::before { content: "▼ "; }
```

**Accordion pattern (one open at a time):**
Native `<details>` elements in the same `name` group (HTML attribute `name`) can form an exclusive accordion — only one with the same `name` can be open at a time. This is a newer feature (Chrome 120+, Firefox 130+):

```html
<details name="faq">
  <summary>Question 1</summary>
  <p>Answer 1</p>
</details>
<details name="faq">
  <summary>Question 2</summary>
  <p>Answer 2</p>
</details>
```

## 4. Diagram

<svg viewBox="0 0 560 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two states of a details element: closed showing only summary, and open showing summary plus expanded content">
  <!-- Closed state -->
  <rect x="10" y="10" width="255" height="105" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="137" y="32" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Closed (default)</text>

  <rect x="25" y="45" width="225" height="36" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.2"/>
  <text x="42" y="68" fill="#6db33f" font-size="13" font-family="sans-serif">▶</text>
  <text x="62" y="68" fill="#e6edf3" font-size="11" font-family="sans-serif" font-weight="bold">What is the refund policy?</text>

  <text x="137" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">hidden content not in layout</text>

  <!-- Open state -->
  <rect x="295" y="10" width="255" height="220" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="422" y="32" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Open (open attribute set)</text>

  <rect x="310" y="45" width="225" height="36" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.2"/>
  <text x="327" y="68" fill="#6db33f" font-size="13" font-family="sans-serif">▼</text>
  <text x="347" y="68" fill="#e6edf3" font-size="11" font-family="sans-serif" font-weight="bold">What is the refund policy?</text>

  <rect x="310" y="90" width="225" height="128" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="320" y="110" fill="#e6edf3" font-size="9" font-family="sans-serif">Full refund within 30 days</text>
  <text x="320" y="126" fill="#e6edf3" font-size="9" font-family="sans-serif">of purchase. No questions</text>
  <text x="320" y="142" fill="#e6edf3" font-size="9" font-family="sans-serif">asked.</text>
  <text x="320" y="165" fill="#8b949e" font-size="8" font-family="sans-serif">Any HTML here:</text>
  <text x="320" y="180" fill="#8b949e" font-size="8" font-family="sans-serif">• lists  • images  • code</text>
  <text x="320" y="195" fill="#8b949e" font-size="8" font-family="sans-serif">• forms  • tables  • etc.</text>
  <text x="422" y="220" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">&lt;details open&gt;</text>
</svg>

Closed shows only the `<summary>` toggle; open reveals all child content. The ▶/▼ triangle is browser-provided and customisable via CSS.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>details & summary</title>
  <style>
    body { font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; }

    details {
      border: 1px solid #6db33f;
      border-radius: 6px;
      margin-bottom: 0.75rem;
      background: #1c2430;
      color: #e6edf3;
    }

    /* Custom marker via CSS */
    summary {
      padding: 0.75rem 1rem;
      cursor: pointer;
      list-style: none;   /* hide default browser triangle */
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    summary::-webkit-details-marker { display: none; }
    summary::after { content: "＋"; color: #6db33f; font-size: 1.2rem; }
    details[open] summary::after { content: "－"; }

    details .content { padding: 0 1rem 1rem; border-top: 1px solid #8b949e44; }
  </style>
</head>
<body>

  <h2>Frequently Asked Questions</h2>

  <details id="q1">
    <summary>What is the refund policy?</summary>
    <div class="content">
      <p>Full refund within 30 days of purchase. Items must be in original condition.</p>
    </div>
  </details>

  <details>
    <summary>How long does shipping take?</summary>
    <div class="content">
      <ul>
        <li>Standard: 5–7 business days</li>
        <li>Express: 2–3 business days</li>
        <li>Overnight: Next business day</li>
      </ul>
    </div>
  </details>

  <details open>
    <summary>Do you offer international shipping?</summary>
    <div class="content">
      <p>Yes — we ship to 42 countries. Customs fees may apply.</p>
    </div>
  </details>

  <script>
    // Listen to the toggle event on all details elements
    document.querySelectorAll("details").forEach((d, i) => {
      d.addEventListener("toggle", () => {
        console.log(`FAQ ${i + 1}: ${d.open ? "opened" : "closed"}`);
      });
    });

    // Programmatically open the first one after 2 seconds
    setTimeout(() => {
      document.getElementById("q1").open = true;
      console.log("Opened FAQ 1 programmatically");
    }, 2000);
  </script>
</body>
</html>
```

**How to run:** save as `details.html`, open in a browser. Click the summaries to toggle. Watch the console for toggle events.

## 6. Walkthrough

- `summary { list-style: none }` + `summary::-webkit-details-marker { display: none }` — removes the default browser triangle on all browsers. WebKit/Blink uses the `::webkit-details-marker` pseudo-element; Firefox uses `list-style: none`.
- `summary::after { content: "＋" }` + `details[open] summary::after { content: "－" }` — custom open/closed indicators using CSS attribute selectors. The selector `details[open]` matches any `<details>` with the `open` attribute present.
- `<details open>` — the third FAQ starts expanded. The `open` HTML attribute is reflected in `details.open` JavaScript property.
- `d.addEventListener("toggle", ...)` — the `toggle` event fires after the state changes, whether triggered by user click or JS. It's the right hook for saving state (e.g., user preferences for which sections are open).
- `document.getElementById("q1").open = true` — setting the JS property adds/removes the `open` attribute on the element. No CSS classes needed.

## 7. Gotchas & takeaways

> **`<details>` is not an accordion by default.** Multiple `<details>` elements all start closed and can be opened independently. For true exclusive-open accordion behaviour, use the `name` attribute (newer browsers) or add JS that closes other open `<details>` on toggle.

> **`<summary>` must be the first child.** Placing other content before `<summary>` is invalid. If `<summary>` is omitted, browsers use a default label ("Details") which isn't useful to users.

> **Content inside closed `<details>` is in the DOM but not rendered.** JS can still query and read it. But CSS animations on it won't work naturally — the `display:none` that hides the content prevents transitions. Use JS to animate.

- Native, zero-JS collapsible widget: `<details>` + `<summary>`.
- `open` attribute: boolean, present = open, absent = closed.
- `toggle` event fires on every state change.
- `summary` must be the first child; everything else is expandable content.
- Remove default triangle with `list-style: none` + `::-webkit-details-marker { display: none }`.
- `name="group"` attribute on multiple `<details>` creates an exclusive accordion (newer browsers).
