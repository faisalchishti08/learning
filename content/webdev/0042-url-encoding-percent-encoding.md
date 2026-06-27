---
card: webdev
gi: 42
slug: url-encoding-percent-encoding
title: URL encoding / percent-encoding
---

## 1. What it is

**Percent-encoding** (also called URL encoding) is a way to represent characters that aren't allowed in URLs by replacing them with a `%` sign followed by two hexadecimal digits matching the character's UTF-8 byte value.

For example:
- Space → `%20` (or `+` in query strings)
- `@` → `%40`
- `/` → `%2F` (when `/` is data, not a path separator)
- `?` → `%3F` (when `?` is data, not a query delimiter)
- Emoji `😀` → `%F0%9F%98%80` (4 UTF-8 bytes)

URLs may only contain a specific set of **unreserved** characters directly: `A-Z a-z 0-9 - _ . ~`. Everything else must be encoded.

## 2. Why & when

URLs were designed when the internet was ASCII-only. Spaces, accented letters, emoji, and special characters would break URL parsing — a raw `&` in a value would look like a new query parameter; a `/` would look like a path separator. Percent-encoding solves this by providing a safe representation for any character. You encounter it when:

- Building query parameters with `encodeURIComponent()` in JavaScript.
- Sending form data — browsers automatically encode form fields before submission.
- Reading server logs — spaces in paths appear as `%20`.
- Working with REST APIs that accept names or text in path segments.
- Debugging encoding bugs where `+` is mistakenly treated as a space (or not).

## 3. Core concept

Analogy: imagine you're sending a telegram in the 1920s where the only punctuation allowed is a period. To send "Hi, how are you?" you'd escape the comma and question mark: `Hi[COMMA] how are you[QMARK]`. Percent-encoding does the same — translates unsafe characters into a safe representation the receiver knows to decode.

**Which characters need encoding:**

```
Safe (unreserved) — use as-is:   A-Z  a-z  0-9  -  _  .  ~
Reserved (structural) — encode when used as data:
  :  /  ?  #  [  ]  @  !  $  &  '  (  )  *  +  ,  ;  =
Everything else — always encode (spaces, emoji, accented letters…)
```

**Two functions in JavaScript, different scope:**

```js
encodeURIComponent("hello world/path?q=1")
// → "hello%20world%2Fpath%3Fq%3D1"
// Encodes everything except: A-Z a-z 0-9 - _ . ! ~ * ' ( )
// Use for VALUES: query param values, path segments

encodeURI("https://example.com/search?q=hello world")
// → "https://example.com/search?q=hello%20world"
// Leaves structural chars intact (: / ? & = # etc.)
// Use for FULL URLs you want to remain structurally valid
```

`+` vs `%20` for spaces: in query strings (`application/x-www-form-urlencoded`), `+` means space. In paths, `+` is a literal `+`; only `%20` means space. Use `%20` everywhere to be safe.

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Percent encoding process: raw string to percent-encoded URL and back">
  <rect width="680" height="280" fill="#0d1117"/>

  <!-- Raw input -->
  <rect x="20" y="28" width="220" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="130" y="48" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Raw value</text>
  <text x="130" y="68" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace">hello world &amp; more</text>

  <!-- Arrow down + encode label -->
  <line x1="130" y1="82" x2="130" y2="122" stroke="#6db33f" stroke-width="2" marker-end="url(#arr1)"/>
  <text x="148" y="108" fill="#6db33f" font-size="11" font-family="monospace">encodeURIComponent()</text>

  <!-- Encoded -->
  <rect x="20" y="126" width="220" height="50" rx="8" fill="#162420" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="146" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Percent-encoded</text>
  <text x="130" y="168" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">hello%20world%20%26%20more</text>

  <!-- Arrow right to URL -->
  <line x1="244" y1="151" x2="316" y2="151" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#arr2)"/>
  <text x="280" y="143" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">in URL</text>

  <!-- Full URL -->
  <rect x="320" y="116" width="340" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="490" y="136" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Full URL</text>
  <text x="490" y="156" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">/search?q=</text>
  <text x="490" y="174" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">hello%20world%20%26%20more</text>

  <!-- Arrow down decode -->
  <line x1="130" y1="180" x2="130" y2="220" stroke="#79c0ff" stroke-width="2" marker-end="url(#arr3)"/>
  <text x="148" y="206" fill="#79c0ff" font-size="11" font-family="monospace">decodeURIComponent()</text>

  <!-- Decoded -->
  <rect x="20" y="224" width="220" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="130" y="249" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="monospace">hello world &amp; more</text>

  <defs>
    <marker id="arr1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e6edf3"/></marker>
    <marker id="arr3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Encode before putting data in a URL; decode when reading it out. Round-trip is lossless.

## 5. Runnable example

```js
// save as url-encoding.js — needs Node.js, no installs
const http = require("http");
const url  = require("url");

const server = http.createServer((req, res) => {
  // url.parse decodes percent-encoding in pathname and query values automatically
  const parsed = url.parse(req.url, true);

  // Show raw (encoded) vs decoded values
  console.log("\n--- Request ---");
  console.log("Raw URL:      ", req.url);         // still encoded
  console.log("Parsed path:  ", parsed.pathname); // decoded
  console.log("Query object: ", parsed.query);    // values decoded

  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({
    rawUrl:   req.url,
    pathname: parsed.pathname,
    query:    parsed.query,
  }));
});

server.listen(3000, () => {
  // Build URLs safely with encodeURIComponent
  const searchTerm = "hello world & more";
  const category   = "café / bistro";

  const encodedSearch   = encodeURIComponent(searchTerm);
  const encodedCategory = encodeURIComponent(category);

  const requestUrl = `/search?q=${encodedSearch}&cat=${encodedCategory}`;
  console.log("Requesting:", requestUrl);

  http.get("http://localhost:3000" + requestUrl, (res) => {
    let body = "";
    res.on("data", (c) => (body += c));
    res.on("end", () => {
      const parsed = JSON.parse(body);
      console.log("\n--- Client sees ---");
      console.log("Raw URL sent:", requestUrl);
      console.log("Server decoded q:  ", parsed.query.q);
      console.log("Server decoded cat:", parsed.query.cat);

      // Demonstrate the + vs %20 pitfall
      const plusEncoded = "hello+world"; // "+" in path = literal plus
      http.get("http://localhost:3000/path/hello+world", (r) => {
        let b2 = "";
        r.on("data", (c) => (b2 += c));
        r.on("end", () => {
          console.log("\n'+' in path pathname:", JSON.parse(b2).pathname);
          // → "/path/hello+world"  (+ is NOT decoded as space in path)
          server.close();
        });
      });
    });
  });
});
```

**How to run:** `node url-encoding.js` — built-in `http` and `url`, no npm.

## 6. Walkthrough

- `encodeURIComponent(searchTerm)` — encodes `"hello world & more"` → `"hello%20world%20%26%20more"`. Encodes spaces as `%20` and `&` as `%26` so they don't break query string parsing.
- `encodeURIComponent(category)` — `"café / bistro"` → `"caf%C3%A9%20%2F%20bistro"`. The `é` becomes two bytes `C3 A9` in UTF-8, each percent-encoded.
- `url.parse(req.url, true)` — `true` makes it parse query values into an object and automatically `decodeURIComponent` each value.
- `parsed.pathname` — the path, decoded. No need to call `decodeURIComponent` manually.
- `parsed.query.q` — `"hello world & more"` — fully decoded, safe to use directly.
- `"/path/hello+world"` — when `+` appears in the path (not a query value), `url.parse` leaves it as `+`. Only `application/x-www-form-urlencoded` (query strings from HTML forms) treats `+` as a space.

## 7. Gotchas & takeaways

> `encodeURIComponent` encodes `+` as `%2B`. This matters when you decode with a form parser that treats `+` as a space — you'd get `" "` instead of `"+"`. Use `%20` for spaces to avoid this ambiguity entirely.

> Double-encoding is a common bug. If a value is already encoded (`hello%20world`) and you call `encodeURIComponent` on it, you get `hello%2520world` (`%` → `%25`). Always start from raw, unencoded values.

- Percent-encoding: unsafe char → `%HH` where `HH` is the UTF-8 byte in hex.
- `encodeURIComponent` — use for values (query params, path segments). Encodes everything except `A-Z a-z 0-9 - _ . ! ~ * ' ( )`.
- `encodeURI` — use for full URLs you want to remain navigable. Leaves structural chars like `/`, `?`, `&` alone.
- `decodeURIComponent` reverses encoding; `url.parse(url, true)` does it automatically for query values.
- `+` = space only in `application/x-www-form-urlencoded` (HTML form data). In paths, `+` is a literal `+`.
