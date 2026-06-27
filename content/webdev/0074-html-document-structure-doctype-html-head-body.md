---
card: webdev
gi: 74
slug: html-document-structure-doctype-html-head-body
title: HTML document structure (<!DOCTYPE>, html, head, body)
---

## 1. What it is

Every HTML page is built on the same four-part skeleton:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <!-- metadata: title, styles, scripts, character encoding -->
  </head>
  <body>
    <!-- visible content -->
  </body>
</html>
```

- `<!DOCTYPE html>` — a declaration (not a tag) that tells the browser to parse the page in **standards mode**.
- `<html>` — the root element that wraps the entire document.
- `<head>` — invisible metadata: page title, character set, CSS links, script tags, and SEO information.
- `<body>` — everything the user sees and interacts with.

## 2. Why & when

This structure exists because browsers need to know two things before rendering a single pixel: *what dialect of HTML this is* (the doctype), and *what's visible vs what's metadata* (head vs body).

Without `<!DOCTYPE html>`, Internet Explorer and older browsers entered **quirks mode** — a compatibility mode that mimicked bugs in early 1990s browsers. In quirks mode, box sizing, font size inheritance, and layout algorithms all behave differently. The `<!DOCTYPE html>` declaration (simplified in HTML5 from longer SGML declarations) forces **no-quirks (standards) mode** in every modern browser.

The head/body split keeps concerns separate: browsers can parse `<head>` first to discover stylesheets and set character encoding before painting anything on screen.

## 3. Core concept

Think of an HTML file like a letter. `<!DOCTYPE html>` is the envelope marking telling the post office what format to expect. `<html>` is the letter itself. `<head>` is the letterhead — your name, address, date — metadata that identifies and describes the letter but isn't the main message. `<body>` is the actual content of the letter.

**`<!DOCTYPE html>`**
- Must be the very first line, before any whitespace or comments.
- Case-insensitive (`<!doctype html>` is valid), but `<!DOCTYPE html>` is the convention.
- Not closed (it's a declaration, not an element).
- This is the entire HTML5 doctype — the old HTML4 doctype was 97 characters long.

**`<html lang="en">`**
- `lang` attribute tells browsers, screen readers, and search engines what language the page is in. Use an [IETF language tag](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry): `"en"`, `"en-US"`, `"fr"`, `"zh-Hant"`.
- Omitting `lang` causes accessibility failures (screen readers default to the OS language, which may mispronounce content).

**`<head>`**
At minimum contains:
```html
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page Title</title>
```
Also common: `<link rel="stylesheet">`, `<script>`, `<meta name="description">`, Open Graph tags, favicons.

**`<body>`**
Contains all rendered content: headings, paragraphs, images, forms, interactive elements. Nothing in `<body>` is hidden from the user by default (use CSS for that).

## 4. Diagram

<svg viewBox="0 0 500 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTML document structure showing DOCTYPE declaration followed by html root with head and body children">
  <!-- DOCTYPE -->
  <rect x="40" y="10" width="420" height="38" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="250" y="34" fill="#8b949e" font-size="13" text-anchor="middle" font-family="monospace">&lt;!DOCTYPE html&gt;</text>
  <text x="420" y="22" fill="#8b949e" font-size="9" text-anchor="end" font-family="sans-serif">standards mode declaration</text>

  <!-- html -->
  <rect x="40" y="58" width="420" height="268" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="60" y="82" fill="#6db33f" font-size="13" font-family="monospace">&lt;html lang="en"&gt;</text>
  <text x="380" y="316" fill="#6db33f" font-size="13" font-family="monospace">&lt;/html&gt;</text>

  <!-- head -->
  <rect x="70" y="92" width="380" height="100" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90" y="115" fill="#79c0ff" font-size="12" font-family="monospace">&lt;head&gt;</text>
  <text x="105" y="135" fill="#8b949e" font-size="10" font-family="monospace">&lt;meta charset="UTF-8"&gt;</text>
  <text x="105" y="152" fill="#8b949e" font-size="10" font-family="monospace">&lt;title&gt;My Page&lt;/title&gt;</text>
  <text x="105" y="169" fill="#8b949e" font-size="10" font-family="monospace">&lt;link rel="stylesheet" href="style.css"&gt;</text>
  <text x="90" y="183" fill="#79c0ff" font-size="12" font-family="monospace">&lt;/head&gt;  ← invisible metadata</text>

  <!-- body -->
  <rect x="70" y="202" width="380" height="100" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="90" y="225" fill="#6db33f" font-size="12" font-family="monospace">&lt;body&gt;</text>
  <text x="105" y="245" fill="#8b949e" font-size="10" font-family="monospace">&lt;h1&gt;Hello, world!&lt;/h1&gt;</text>
  <text x="105" y="262" fill="#8b949e" font-size="10" font-family="monospace">&lt;p&gt;All visible content goes here.&lt;/p&gt;</text>
  <text x="90" y="293" fill="#6db33f" font-size="12" font-family="monospace">&lt;/body&gt;  ← visible content</text>
</svg>

`<head>` holds metadata; `<body>` holds rendered content; both live inside `<html>`; all preceded by the `<!DOCTYPE html>` declaration.

## 5. Runnable example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>My First Page</title>
  <style>
    body { font-family: sans-serif; max-width: 600px; margin: 2rem auto; }
    h1   { color: #6db33f; }
  </style>
</head>
<body>
  <h1>Hello from the body!</h1>
  <p>This paragraph is visible content. The title and style above live in <code>&lt;head&gt;</code> — you can see the page title in your browser tab.</p>

  <script>
    // document.title is set in <head> but readable/writable from JS
    console.log("Page title:", document.title);
    console.log("Lang:", document.documentElement.lang);
  </script>
</body>
</html>
```

**How to run:** save as `index.html` and open it in any browser (double-click or drag to browser window). No server needed for a static HTML file.

## 6. Walkthrough

- `<!DOCTYPE html>` is the first thing in the file — even before comments. Moving it below any content would trigger quirks mode in some browsers.
- `<meta charset="UTF-8">` must appear in the first 1 024 bytes of the file. If it's missing, the browser guesses the encoding, which can corrupt characters like `é`, `中`, `€`.
- `<meta name="viewport" ...>` controls how mobile browsers scale the page. Without it, a phone browser renders the page at desktop width (980 px) and scales it down — text becomes unreadably small.
- `<title>My First Page</title>` sets the browser tab label, the bookmark name, and the headline shown in search engine results. It's mandatory (pages without it fail accessibility audits).
- `<style>` in `<head>` applies CSS before the browser paints content, avoiding a flash of unstyled content.
- `document.documentElement.lang` accesses the `lang` attribute on `<html>`. Screen readers use this to choose a speech synthesis voice.

## 7. Gotchas & takeaways

> **Forgetting `<!DOCTYPE html>` is silent but breaking.** The page renders, but in quirks mode. CSS `box-sizing`, `vertical-align`, and `font-size` calculations all behave differently. Always include the doctype as line 1.

> **`<meta charset>` must be within the first 1 024 bytes.** If you put it after a long comment block, the browser may interpret the file as a different encoding before it finds the charset declaration — corrupting accented characters and emojis.

> **`<body>` can be omitted, but shouldn't.** HTML5 parsers auto-insert a `<body>` if it's missing, but omitting it confuses code editors, linters, and developers.

- `<!DOCTYPE html>` = line 1, always, triggers standards mode.
- `<html lang="en">` = accessibility and SEO, set the right IETF language tag.
- `<head>` = metadata only; `<body>` = all rendered content.
- `<meta charset="UTF-8">` and `<meta name="viewport">` belong in every `<head>`.
- Missing `<title>` fails accessibility audits and hurts SEO.
