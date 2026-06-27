---
card: webdev
gi: 89
slug: time-mark-abbr-cite-address
title: time, mark, abbr, cite, address
---

## 1. What it is

Five inline semantic elements that annotate specific types of text content:

| Element | Purpose | Renders as |
|---------|---------|-----------|
| `<time>` | Machine-readable date/time | Plain text (no default style) |
| `<mark>` | Highlighted/relevant text | Yellow background |
| `<abbr>` | Abbreviation with expansion | Dotted underline (browser-dependent) |
| `<cite>` | Title of a creative work | Italic |
| `<address>` | Contact information | Italic |

All five are inline elements (except `<address>`, which is block-level) and carry semantic meaning beyond their visual presentation.

## 2. Why & when

Plain text has no machine-readable structure. Writing "Published on January 15, 2025" is legible to humans but opaque to a calendar app or a search engine. `<time datetime="2025-01-15">January 15, 2025</time>` gives both: human-readable display text and machine-readable ISO 8601 in the attribute.

Each element solves a specific communication problem:
- `<time>` — date/time that software should understand.
- `<mark>` — text relevant to the current context (search results, highlighted passages).
- `<abbr>` — first occurrence of an acronym that users might not know.
- `<cite>` — the title of a book, article, film, or other work being referenced.
- `<address>` — contact details for the nearest containing `<article>` or the page overall.

## 3. Core concept

**`<time>`**

```html
<p>Published <time datetime="2025-06-01">June 1, 2025</time></p>
<p>Event at <time datetime="2025-06-01T14:30">2:30 PM on June 1</time></p>
<p>Duration: <time datetime="PT2H30M">2 hours 30 minutes</time></p>
```

The `datetime` attribute uses ISO 8601 format. Display text is for humans; the attribute is for machines. When `datetime` is absent, the element's text content must itself be a valid date/time string.

**`<mark>`**

```html
<!-- In search results — highlighting the query term -->
<p>Results for "web accessibility": <mark>Web accessibility</mark> ensures…</p>

<!-- In documentation — highlighting relevant passage -->
<p>The key rule is: <mark>always validate user input</mark> on the server.</p>
```

Rendered as a yellow highlight by default. Use CSS `::highlight` or `background-color` on `mark` to restyle. Note: `<mark>` denotes *relevance or attention*, not importance (that's `<strong>`).

**`<abbr>`**

```html
<p>The <abbr title="Document Object Model">DOM</abbr> is a tree of nodes.</p>
<p><abbr title="Cascading Style Sheets">CSS</abbr> controls visual presentation.</p>
```

`title` holds the full expansion. On desktop, hovering shows the `title` as a tooltip. Screen readers may read the expansion. Convention: expand the abbreviation on its first use in a document.

**`<cite>`**

```html
<p>As stated in <cite>Clean Code</cite> by Robert C. Martin…</p>
<blockquote>
  <p>The art of programming is the art of organizing complexity.</p>
  <footer>— Edsger Dijkstra, <cite>A Discipline of Programming</cite></footer>
</blockquote>
```

`<cite>` marks titles of works — books, films, articles, albums, paintings, etc. Not for the name of a person or organisation. Renders italic by default.

**`<address>`**

```html
<!-- Page-level contact info (inside <footer>) -->
<footer>
  <address>
    Questions? Email <a href="mailto:hello@example.com">hello@example.com</a>
    or call <a href="tel:+15551234567">+1 (555) 123-4567</a>
  </address>
</footer>

<!-- Article-level author info (inside <article>) -->
<article>
  <address>
    Written by <a href="/author/alice">Alice Smith</a>
  </address>
</article>
```

`<address>` is scoped to its nearest `<article>` ancestor (if inside one) or to the whole page (if not). It is for contact information, not postal addresses generally — use a `<p>` for a plain postal address with no contact relationship.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Five panels each showing an element, its rendered appearance, and its semantic purpose">
  <!-- time -->
  <rect x="10" y="10" width="113" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="66" y="30" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">&lt;time&gt;</text>
  <text x="20" y="50" fill="#e6edf3" font-size="9" font-family="monospace">June 1</text>
  <text x="20" y="67" fill="#8b949e" font-size="8" font-family="sans-serif">datetime=</text>
  <text x="20" y="80" fill="#8b949e" font-size="8" font-family="monospace">"2025-06-01"</text>
  <text x="66" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">machine-readable</text>

  <!-- mark -->
  <rect x="133" y="10" width="113" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="189" y="30" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">&lt;mark&gt;</text>
  <rect x="145" y="42" width="89" height="22" rx="3" fill="#ffeb3b"/>
  <text x="189" y="58" fill="#000" font-size="10" text-anchor="middle" font-family="sans-serif">highlighted</text>
  <text x="189" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">yellow bg</text>
  <text x="189" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">relevance / attention</text>

  <!-- abbr -->
  <rect x="256" y="10" width="113" height="100" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="312" y="30" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">&lt;abbr&gt;</text>
  <text x="265" y="55" fill="#e6edf3" font-size="12" font-family="sans-serif" text-decoration="underline" style="text-decoration-style:dotted">DOM</text>
  <text x="312" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">title="Document</text>
  <text x="312" y="87" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Object Model"</text>
  <text x="312" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">dotted underline</text>

  <!-- cite -->
  <rect x="379" y="10" width="113" height="100" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="435" y="30" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">&lt;cite&gt;</text>
  <text x="390" y="55" fill="#e6edf3" font-size="11" font-family="sans-serif" font-style="italic">Clean Code</text>
  <text x="435" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">italic by default</text>
  <text x="435" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">titles of works only</text>

  <!-- address -->
  <rect x="502" y="10" width="128" height="100" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="566" y="30" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">&lt;address&gt;</text>
  <text x="512" y="52" fill="#e6edf3" font-size="9" font-family="sans-serif" font-style="italic">hello@example</text>
  <text x="512" y="67" fill="#e6edf3" font-size="9" font-family="sans-serif" font-style="italic">+1 555 123</text>
  <text x="566" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">italic · block</text>
  <text x="566" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">contact info only</text>

  <!-- combined usage -->
  <rect x="10" y="125" width="620" height="120" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="30" y="148" fill="#8b949e" font-size="10" font-family="sans-serif" font-weight="bold">Combined in an article footer:</text>
  <text x="30" y="168" fill="#e6edf3" font-size="10" font-family="monospace">&lt;footer&gt;</text>
  <text x="50" y="185" fill="#6db33f" font-size="10" font-family="monospace">&lt;address&gt;By &lt;a href="/alice"&gt;Alice&lt;/a&gt;&lt;/address&gt;</text>
  <text x="50" y="201" fill="#6db33f" font-size="10" font-family="monospace">&lt;time datetime="2025-06-01"&gt;June 1, 2025&lt;/time&gt;</text>
  <text x="50" y="217" fill="#6db33f" font-size="10" font-family="monospace">Reviewed in &lt;cite&gt;Web Dev Weekly&lt;/cite&gt;</text>
  <text x="30" y="233" fill="#e6edf3" font-size="10" font-family="monospace">&lt;/footer&gt;</text>
</svg>

Each element encodes a specific semantic type that plain text cannot express; only `<address>` is block-level — the others are inline.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Inline Semantics Demo</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }
    article { border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; }
    mark { background: #fff3cd; padding: 0 2px; border-radius: 2px; }
    abbr { cursor: help; border-bottom: 1px dotted currentColor; text-decoration: none; }
    address { font-style: normal; }  /* override default italic if desired */
    .meta { color: #666; font-size: 0.875rem; margin: 0.5rem 0 1rem; }
  </style>
</head>
<body>

  <article>
    <h2>Modern <abbr title="Application Programming Interface">API</abbr> Design</h2>

    <p class="meta">
      By <address style="display:inline"><a href="/jane">Jane Doe</a></address>
      · Published <time datetime="2025-03-20">March 20, 2025</time>
      · Updated <time datetime="2025-06-01T10:00:00Z">June 1, 2025</time>
    </p>

    <p>As <cite>RESTful Web APIs</cite> by Leonard Richardson explains,
    a well-designed <abbr title="Application Programming Interface">API</abbr>
    should be <mark>predictable and consistent</mark> across all endpoints.</p>

    <p>The <abbr title="HyperText Transfer Protocol">HTTP</abbr> specification
    defines the semantics of each method. The key insight:
    <mark>GET requests must never have side effects</mark>.</p>

    <blockquote>
      <p>Design APIs for their users, not for your implementation.</p>
      <footer>— From <cite>The Design of Everyday Things</cite></footer>
    </blockquote>
  </article>

  <footer>
    <address>
      Contact the author: <a href="mailto:jane@example.com">jane@example.com</a>
    </address>
  </footer>

  <script>
    // time elements expose datetime attribute directly
    document.querySelectorAll("time").forEach(t => {
      console.log(`Display: "${t.textContent.trim()}"  |  Machine: "${t.dateTime}"`);
    });

    // abbr titles are accessible programmatically
    document.querySelectorAll("abbr").forEach(a => {
      console.log(`Abbr: ${a.textContent} = ${a.title}`);
    });
  </script>
</body>
</html>
```

**How to run:** save as `semantics.html`, open in a browser. Hover over `<abbr>` elements to see expansion tooltips. Check the console for `dateTime` and `title` values.

## 6. Walkthrough

- `<abbr title="Application Programming Interface">API</abbr>` — the first occurrence of "API" in the article is expanded. Subsequent uses can omit the `<abbr>` wrapper since the reader now knows what it means.
- `<time datetime="2025-03-20">March 20, 2025</time>` — `t.dateTime` in JS returns the `datetime` attribute value. Calendar apps and structured data parsers use this, not the display text.
- `<time datetime="2025-06-01T10:00:00Z">` — ISO 8601 with time and timezone (Z = UTC). `dateTime` returns the full string. JavaScript's `new Date(t.dateTime)` would parse this correctly.
- `<mark>predictable and consistent</mark>` — yellow highlight draws the eye to the key concept. Unlike `<strong>` (importance), `<mark>` implies "this is what I searched for" or "this is why this passage is shown."
- `<cite>RESTful Web APIs</cite>` — the book title, not the author. If citing a person, use plain text or `<a>`.
- `<address>` in the article `<p class="meta">` is set to `display:inline` via inline style to flow in the sentence. That's valid — display is a CSS concern, semantics are unchanged.

## 7. Gotchas & takeaways

> **`<cite>` is for titles of works, not people's names.** "As stated by <cite>Tim Berners-Lee</cite>" is wrong — `<cite>` should wrap `<cite>Weaving the Web</cite>`, not the author. For names, use plain text.

> **`<address>` is not a general postal address element.** `<address>123 Main St, Springfield</address>` is incorrect unless that address is contact information for the page or article. Use `<p>` for standalone postal addresses.

> **`<mark>` in search results should match what was searched.** The correct use is server-side rendering of search hit highlighting — wrap matched terms in `<mark>`. Using it for decorative highlighting is a misuse that confuses AT.

- `<time datetime="ISO-8601">human text</time>` — split machine-readable from human-readable.
- `<mark>` = relevance or highlight, not importance (`<strong>` is for importance).
- `<abbr title="expansion">` — use on the first occurrence of each abbreviation.
- `<cite>` = titles of creative works (books, films, articles) — never for person names.
- `<address>` = contact info for the nearest `<article>` or page; block-level by default.
