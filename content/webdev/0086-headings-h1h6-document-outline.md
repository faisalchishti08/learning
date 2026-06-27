---
card: webdev
gi: 86
slug: headings-h1h6-document-outline
title: Headings (h1–h6) & document outline
---

## 1. What it is

HTML provides six heading elements — `<h1>` through `<h6>` — that create a hierarchical document outline. `<h1>` is the most important heading (there should be one per page); `<h6>` is the least important. The numbers express rank, not size — size is controlled by CSS.

```html
<h1>Document Title</h1>
  <h2>Chapter One</h2>
    <h3>Section 1.1</h3>
    <h3>Section 1.2</h3>
  <h2>Chapter Two</h2>
    <h3>Section 2.1</h3>
      <h4>Subsection 2.1.1</h4>
```

This hierarchy creates a navigable outline — screen reader users can jump between headings to scan content, just like a sighted user scans visually by reading headings.

## 2. Why & when

Headings are the most important structural element after the page itself. They serve three audiences:

1. **Screen reader users** — most AT users navigate pages by heading (pressing `H` key in most readers to jump heading-to-heading). Without a good heading structure, the page is inaccessible to this group.
2. **Search engines** — `<h1>` signals the primary topic; lower-level headings outline subtopics. Keyword placement in headings carries more weight than body text.
3. **All users** — people skim headings before committing to reading. A clear heading hierarchy lets users find what they need fast.

Use headings to structure content — not to make text large or bold (use CSS for that). Never skip levels for visual effect (`<h1>` then `<h3>`). The hierarchy must be logical.

## 3. Core concept

Think of headings like a book's **table of contents**. `<h1>` is the book title. `<h2>` elements are chapters. `<h3>` elements are sections within chapters. You'd never have Chapter 3 start without Chapter 1 and 2 existing — likewise, never use `<h3>` without a preceding `<h2>` in the same context.

**Rules:**
- One `<h1>` per page (the page's main topic, usually the same as `<title>`).
- Never skip heading levels: `<h1>` → `<h2>` → `<h3>` is correct; `<h1>` → `<h3>` is not.
- You can go back up levels: `<h3>` followed by `<h2>` is fine (new chapter).
- Heading rank = structural importance, not visual size. Always style with CSS.

**Default browser styles (vary by browser):**

| Element | Approximate default size |
|---------|-------------------------|
| `<h1>` | 2em |
| `<h2>` | 1.5em |
| `<h3>` | 1.17em |
| `<h4>` | 1em (same as body) |
| `<h5>` | 0.83em |
| `<h6>` | 0.67em |

All headings are bold by default. Use CSS `font-size` and `font-weight` to style them as your design requires.

**The heading outline** can be inspected in DevTools (Elements panel → Accessibility tab → headings) or with screen reader software. A well-structured page looks like an indented list:

```
h1: "Understanding Web Accessibility"
  h2: "Why Accessibility Matters"
    h3: "Legal Requirements"
    h3: "Business Case"
  h2: "Implementing Accessible HTML"
    h3: "Semantic Elements"
    h3: "ARIA Attributes"
```

## 4. Diagram

<svg viewBox="0 0 560 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Document outline showing h1 at the top, two h2 sections below it, and h3 headings inside each h2 section">
  <!-- h1 -->
  <rect x="20" y="20" width="520" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="40" y="44" fill="#6db33f" font-size="16" font-family="monospace" font-weight="bold">&lt;h1&gt; Document Title</text>
  <text x="510" y="44" fill="#8b949e" font-size="10" text-anchor="end" font-family="sans-serif">rank 1</text>

  <!-- h2 first -->
  <rect x="55" y="68" width="445" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="88" fill="#79c0ff" font-size="13" font-family="monospace">&lt;h2&gt; Chapter One</text>

  <!-- h3s under first h2 -->
  <rect x="90" y="108" width="360" height="24" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="125" fill="#8b949e" font-size="11" font-family="monospace">&lt;h3&gt; Section 1.1</text>
  <rect x="90" y="140" width="360" height="24" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="157" fill="#8b949e" font-size="11" font-family="monospace">&lt;h3&gt; Section 1.2</text>

  <!-- h2 second -->
  <rect x="55" y="178" width="445" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="198" fill="#79c0ff" font-size="13" font-family="monospace">&lt;h2&gt; Chapter Two</text>

  <!-- h3 under second h2 -->
  <rect x="90" y="218" width="360" height="24" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="235" fill="#8b949e" font-size="11" font-family="monospace">&lt;h3&gt; Section 2.1</text>

  <!-- h4 under h3 -->
  <rect x="125" y="250" width="290" height="22" rx="2" fill="#0d1117" stroke="#8b949e" stroke-width="0.8" stroke-dasharray="3,2"/>
  <text x="142" y="265" fill="#8b949e" font-size="10" font-family="monospace">&lt;h4&gt; Subsection 2.1.a</text>
</svg>

Headings indent with rank to create a scannable visual and semantic hierarchy — like a book's table of contents.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Understanding Web Accessibility</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }
    h1 { font-size: 2rem; color: #1a1a1a; border-bottom: 3px solid #6db33f; padding-bottom: 0.5rem; }
    h2 { font-size: 1.4rem; color: #2a2a2a; margin-top: 2rem; }
    h3 { font-size: 1.1rem; color: #3a3a3a; margin-top: 1rem; }
    /* All headings bold by default — override for h4+ if needed */
    h4 { font-size: 1rem; color: #6db33f; }
  </style>
</head>
<body>

  <h1>Understanding Web Accessibility</h1>

  <h2>Why Accessibility Matters</h2>
  <p>Accessibility ensures everyone can use the web, regardless of ability.</p>

  <h3>Legal Requirements</h3>
  <p>WCAG 2.1 AA is required by law in many jurisdictions.</p>

  <h3>Business Case</h3>
  <p>Accessible sites reach a wider audience and rank better in search.</p>

  <h2>Implementing Accessible HTML</h2>
  <p>Semantic markup is the foundation of accessible web pages.</p>

  <h3>Semantic Elements</h3>
  <p>Use <code>&lt;nav&gt;</code>, <code>&lt;main&gt;</code>, <code>&lt;article&gt;</code>.</p>

  <h4>Landmark Roles</h4>
  <p>Screen readers expose landmarks as jump points for quick navigation.</p>

  <h3>ARIA Attributes</h3>
  <p>Use ARIA to supplement semantics where HTML falls short.</p>

  <script>
    // Extract the heading outline programmatically
    const headings = document.querySelectorAll("h1, h2, h3, h4, h5, h6");
    console.log("Document outline:");
    headings.forEach(h => {
      const level = parseInt(h.tagName[1]);
      const indent = "  ".repeat(level - 1);
      console.log(`${indent}${h.tagName}: ${h.textContent}`);
    });
  </script>
</body>
</html>
```

**How to run:** save as `headings.html`, open in a browser. The console logs the full heading outline. On macOS VoiceOver (Cmd+F5) or Windows Narrator, press `H` to jump between headings.

## 6. Walkthrough

- `<h1>Understanding Web Accessibility</h1>` — the sole `<h1>`. Its text matches the `<title>` — a best practice for clarity.
- `<h2>Why Accessibility Matters</h2>` — starts a new chapter-level section. `<h2>` elements are siblings (same level), marking two distinct top-level topics.
- `<h3>Legal Requirements</h3>` and `<h3>Business Case</h3>` — subsections within the first `<h2>`. They're siblings with each other and children of the `<h2>` in the outline sense (not DOM sense — headings are flat in the DOM).
- `<h4>Landmark Roles</h4>` — goes one level deeper inside `<h3>Semantic Elements</h3>`. The level jumped from h3 to h4, not h3 to h5 — no level skipped.
- The JS `querySelectorAll("h1, h2, h3, h4, h5, h6")` collects all headings in document order. `parseInt(h.tagName[1])` extracts the level number. The indent (`"  ".repeat(level - 1)`) makes the hierarchy visible in the console.

## 7. Gotchas & takeaways

> **Don't skip heading levels.** `<h1>` followed directly by `<h3>` is a common error (often because `<h3>` looks the right visual size). Use CSS to control size; use the correct heading level for structure.

> **Don't use headings just for bold/large text.** If you need large text in a list item, caption, or table cell, use CSS. Headings imply outline structure. Misuse confuses AT users who navigate by heading.

> **One `<h1>` per page, not per section.** In HTML5, the outline algorithm was supposed to allow multiple `<h1>` elements inside sectioning elements, but browsers never implemented the outline algorithm and screen readers ignore it. Use one `<h1>` per page.

- One `<h1>` per page — the page's primary topic.
- Never skip levels (h1 → h3 is wrong; h1 → h2 → h3 is right).
- Heading rank = semantic importance, not visual size — style with CSS.
- Screen reader users navigate pages by heading level — structure matters.
- Extract the outline in DevTools: Accessibility tab → "Headings" section.
