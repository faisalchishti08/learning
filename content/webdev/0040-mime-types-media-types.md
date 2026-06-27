---
card: webdev
gi: 40
slug: mime-types-media-types
title: MIME types / media types
---

## 1. What it is

A **MIME type** (also called a *media type*) is a standardised string that identifies the format of data. It appears in the `Content-Type` header and the `Accept` header. The format is:

```
type/subtype[;parameter=value]
```

Examples: `text/html`, `application/json`, `image/png`, `multipart/form-data; boundary=----XYZ`.

MIME originally stood for *Multipurpose Internet Mail Extensions* — it was invented for email attachments and later adopted by HTTP.

## 2. Why & when

Without MIME types, browsers would have to sniff the content to decide how to display it (and they do, dangerously, if `Content-Type` is missing). MIME types matter whenever:

- A browser decides to render HTML vs. download a file vs. display an image.
- A server parses a request body — it reads `Content-Type` to know whether to parse JSON, form data, or a multipart upload.
- An API returns a `415 Unsupported Media Type` — the client sent a body with a MIME type the server doesn't understand.
- Static file servers need to serve `.woff2` fonts or `.webp` images with the right type so browsers handle them correctly.

## 3. Core concept

Think of a MIME type as a food label. `image/png` is like "food / canned-peas" — the broad category (`image`) and the specific kind (`png`). A browser reading this knows exactly how to open the file, just like a kitchen knows exactly what to do with canned peas.

**Structure:**

```
text / html ; charset = utf-8
│      │        │
type   subtype  parameter
```

**Top-level types:**

| Type | Meaning |
|------|---------|
| `text` | Human-readable text |
| `image` | Image data |
| `audio` | Audio |
| `video` | Video |
| `application` | Binary/structured data |
| `multipart` | Multiple parts (file uploads) |
| `font` | Web fonts |

**Common MIME types in web development:**

| MIME type | Used for |
|-----------|---------|
| `text/html` | HTML pages |
| `text/css` | CSS stylesheets |
| `text/javascript` | JavaScript (official since 2019) |
| `application/json` | JSON API payloads |
| `application/xml` | XML data |
| `application/x-www-form-urlencoded` | HTML form submissions |
| `multipart/form-data` | File uploads |
| `image/png` / `image/jpeg` / `image/webp` | Images |
| `font/woff2` | Web fonts |
| `application/octet-stream` | Unknown binary / force-download |

The `application/x-` prefix historically indicated experimental types; some like `x-www-form-urlencoded` became permanent with the `x-` baked in.

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MIME type anatomy showing type, slash, subtype and optional parameters, with a tree of common top-level types">
  <!-- Anatomy -->
  <rect x="20" y="20" width="640" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="340" y="40" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">MIME type anatomy</text>

  <text x="90"  y="68" fill="#6db33f"  font-size="18" text-anchor="middle" font-family="monospace" font-weight="bold">application</text>
  <text x="240" y="68" fill="#e6edf3"  font-size="18" text-anchor="middle" font-family="monospace">/</text>
  <text x="340" y="68" fill="#79c0ff"  font-size="18" text-anchor="middle" font-family="monospace" font-weight="bold">json</text>
  <text x="455" y="68" fill="#e6edf3"  font-size="18" text-anchor="middle" font-family="monospace">;</text>
  <text x="570" y="68" fill="#e3b341"  font-size="15" text-anchor="middle" font-family="monospace">charset=utf-8</text>

  <text x="90"  y="84" fill="#6db33f"  font-size="10" text-anchor="middle" font-family="sans-serif">type</text>
  <text x="340" y="84" fill="#79c0ff"  font-size="10" text-anchor="middle" font-family="sans-serif">subtype</text>
  <text x="570" y="84" fill="#e3b341"  font-size="10" text-anchor="middle" font-family="sans-serif">parameter (optional)</text>

  <!-- Tree of types -->
  <text x="40" y="118" fill="#8b949e" font-size="11" font-family="sans-serif">Common types:</text>
  <!-- text -->
  <rect x="20"  y="128" width="90" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="65"  y="146" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">text</text>
  <text x="20"  y="172" fill="#8b949e" font-size="9" font-family="monospace">html css js</text>

  <!-- image -->
  <rect x="124" y="128" width="90" height="28" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="169" y="146" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">image</text>
  <text x="124" y="172" fill="#8b949e" font-size="9" font-family="monospace">png jpeg webp</text>

  <!-- application -->
  <rect x="228" y="128" width="110" height="28" rx="4" fill="#1c2430" stroke="#e3b341" stroke-width="1"/>
  <text x="283" y="146" fill="#e3b341" font-size="11" text-anchor="middle" font-family="monospace">application</text>
  <text x="228" y="172" fill="#8b949e" font-size="9" font-family="monospace">json xml pdf wasm</text>

  <!-- multipart -->
  <rect x="352" y="128" width="90" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="397" y="146" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">multipart</text>
  <text x="352" y="172" fill="#8b949e" font-size="9" font-family="monospace">form-data</text>

  <!-- font -->
  <rect x="456" y="128" width="90" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="501" y="146" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">font</text>
  <text x="456" y="172" fill="#8b949e" font-size="9" font-family="monospace">woff2 ttf</text>

  <!-- Special case note -->
  <rect x="20" y="192" width="640" height="60" rx="6" fill="#161d27" stroke="#8b949e" stroke-width="0.8" stroke-dasharray="5,3"/>
  <text x="40" y="213" fill="#8b949e" font-size="11" font-family="sans-serif">Special cases:</text>
  <text x="40" y="232" fill="#e6edf3" font-size="11" font-family="monospace">application/octet-stream</text>
  <text x="260" y="232" fill="#8b949e" font-size="11" font-family="sans-serif">— unknown binary; browser offers "Save As"</text>
  <text x="40" y="248" fill="#e6edf3" font-size="11" font-family="monospace">application/x-www-form-urlencoded</text>
  <text x="360" y="248" fill="#8b949e" font-size="11" font-family="sans-serif">— default HTML form POST</text>
</svg>

`type/subtype` plus optional parameters. `application/octet-stream` is the generic "unknown binary" fallback.

## 5. Runnable example

```js
// save as mime-types.js — needs Node.js, no installs
const http = require("http");
const path = require("path");

// Map file extensions to MIME types
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css":  "text/css",
  ".js":   "text/javascript",
  ".json": "application/json",
  ".png":  "image/png",
  ".jpg":  "image/jpeg",
  ".svg":  "image/svg+xml",
  ".woff2":"font/woff2",
};

const server = http.createServer((req, res) => {
  const ext = path.extname(req.url); // ".json", ".html", etc.
  const contentType = MIME[ext] || "application/octet-stream";

  if (req.url === "/data.json") {
    const body = JSON.stringify({ name: "Alice" });
    res.writeHead(200, { "Content-Type": contentType, "Content-Length": Buffer.byteLength(body) });
    return res.end(body);
  }

  if (req.url === "/page.html") {
    const body = "<html><body><h1>Hello</h1></body></html>";
    res.writeHead(200, { "Content-Type": contentType });
    return res.end(body);
  }

  // Unknown extension → octet-stream (browser will offer to download)
  res.writeHead(200, { "Content-Type": "application/octet-stream" });
  res.end(Buffer.from([0x50, 0x4B, 0x03, 0x04])); // fake ZIP header bytes
});

server.listen(3000, () => {
  const paths = ["/data.json", "/page.html", "/archive.bin"];

  let pending = paths.length;
  paths.forEach((p) => {
    http.get("http://localhost:3000" + p, (res) => {
      let b = "";
      res.on("data", (c) => (b += c));
      res.on("end", () => {
        console.log(`${p.padEnd(14)} → Content-Type: ${res.headers["content-type"]}`);
        if (--pending === 0) server.close();
      });
    });
  });
});
```

**How to run:** `node mime-types.js` — built-in modules only, no npm.

## 6. Walkthrough

- `path.extname(req.url)` — extracts the file extension from the URL path. `.json` from `/data.json`.
- `MIME[ext]` — table lookup; `undefined` falls through to `"application/octet-stream"`.
- `"text/html; charset=utf-8"` — the `charset` parameter is critical for HTML; without it, some browsers assume a legacy encoding and mangle characters above ASCII.
- `"application/json"` — no charset needed; JSON is always UTF-8 by spec.
- `"application/octet-stream"` — the generic fallback for unknown binary. Browsers see this and prompt "Save As" instead of trying to render it.
- `Buffer.from([0x50, 0x4B, ...])` — raw bytes simulating a file, showing that the content type controls browser behaviour regardless of what the bytes actually are.

## 7. Gotchas & takeaways

> Browsers do **MIME type sniffing** — they peek at the first bytes and override the declared type if they think they know better. This is a security hole: an attacker can upload an HTML file disguised as an image and it gets executed. Send `X-Content-Type-Options: nosniff` to disable sniffing for scripts and styles.

> The "official" MIME type for JavaScript is `text/javascript` (RFC 9239, 2022). `application/javascript` still works everywhere but is technically obsolete. `application/x-javascript` is even older — avoid it.

- MIME type = `type/subtype[;param=value]`. Identifies the data format.
- Sent in `Content-Type` (what you're sending) and `Accept` (what you'll accept).
- `application/octet-stream` = unknown binary; browsers offer to download it.
- `multipart/form-data` is required for file uploads; `application/x-www-form-urlencoded` is for plain form fields.
- Send `X-Content-Type-Options: nosniff` to prevent browser MIME sniffing on responses.
