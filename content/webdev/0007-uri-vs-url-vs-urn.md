---
card: webdev
gi: 7
slug: uri-vs-url-vs-urn
title: URI vs URL vs URN
---

## 1. What it is

These three acronyms name **identifiers for resources**, and they nest:

- **URI** (Uniform Resource **Identifier**) — the umbrella term. Any string that **identifies** a resource. Every URL and every URN is a URI.
- **URL** (Uniform Resource **Locator**) — a URI that also tells you **where** the resource is and **how** to get it (the protocol). `https://example.com/cat.png` — it locates *and* gives directions.
- **URN** (Uniform Resource **Name**) — a URI that **names** a resource permanently without saying where it lives. `urn:isbn:9780131103627` names a specific book; it doesn't tell you which shelf or shop.

In short: **URI = identifier**; **URL = identifier + location**; **URN = identifier as a stable name**. URLs are the kind you use every day.

## 2. Why & when

The distinction matters mostly for **precision and correctness**:

- In casual speech, "URL" is fine for the web addresses you type.
- In **specs, standards, and APIs**, the correct umbrella word is **URI** — e.g. XML namespaces and some HTTP headers are "URIs," and they need not be fetchable.
- **URNs** appear where you need a **permanent name** that survives even if the thing moves: ISBNs for books, UUIDs (`urn:uuid:...`), namespace identifiers.

When you'll care:

- Reading RFCs or framework docs that say "URI" and wondering if a plain URL counts (it does).
- Designing identifiers that must stay valid forever, independent of hosting → think URN-style names.
- Day-to-day linking, fetching, `<a href>` → you're using **URLs**.

## 3. Core concept

A URI's job is to **identify** a resource. *How* it identifies splits into two styles:

- **By location (URL):** include a **scheme** (`https`, `ftp`, `mailto`) that says *how to access it*, plus where it is. Because it encodes location, a URL can **break** if the resource moves (a `404`).
- **By name (URN):** use the `urn:` scheme with a namespace and a name. It's a **stable label**, not directions. It never 404s because it never promised a location — but you need a separate system to *resolve* a URN to something fetchable.

The relationship as a set:

```
        URI  (any identifier)
        /  \
      URL    URN
 (locates)  (names)
```

Most URIs you meet are URLs. Pure URNs are comparatively rare. And yes, some URIs are *both-ish* or neither in the strict sense — the categories are about **intent**: are you giving an address (URL) or a permanent name (URN)?

A handy test: **Can you paste it into a browser and fetch it?** If the scheme implies retrieval (`http`, `https`, `ftp`), it's acting as a URL. If it's just an identifying name (`urn:isbn:...`), it's a URN.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="URI is the umbrella term containing URL which locates and URN which names">
  <rect x="170" y="20" width="300" height="44" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="40" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif">URI — identifies a resource</text>
  <text x="320" y="56" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(umbrella term)</text>

  <line x1="260" y1="64" x2="180" y2="110" stroke="#8b949e"/>
  <line x1="380" y1="64" x2="460" y2="110" stroke="#8b949e"/>

  <rect x="60" y="110" width="240" height="70" rx="10" fill="#1c2430" stroke="#3fb950"/>
  <text x="180" y="134" fill="#3fb950" font-size="13" text-anchor="middle" font-family="sans-serif">URL — locates</text>
  <text x="180" y="152" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">https://example.com/cat.png</text>
  <text x="180" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">scheme says how to fetch</text>

  <rect x="340" y="110" width="240" height="70" rx="10" fill="#1c2430" stroke="#79c0ff"/>
  <text x="460" y="134" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif">URN — names</text>
  <text x="460" y="152" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">urn:isbn:9780131103627</text>
  <text x="460" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">stable, no location</text>
</svg>

URL and URN are two ways of being a URI: one gives an address, the other a permanent name.

## 5. Runnable example

Browsers and Node ship a `URL` parser. Let's parse a URL and contrast it with a URN string (which the locator-parser deliberately treats differently).

```js
// save as ids.js — run: node ids.js   (URL is a built-in global in modern Node)
const url = new URL("https://shop.example.com:8443/books?q=js#reviews");
console.log("scheme/protocol:", url.protocol); // how to fetch -> makes it a URL
console.log("host:", url.host);
console.log("path:", url.pathname);
console.log("query:", url.search);

const urn = new URL("urn:isbn:9780131103627");
console.log("\nURN protocol:", urn.protocol);   // "urn:"
console.log("URN pathname:", urn.pathname);     // "isbn:9780131103627" — a NAME, no host
console.log("URN has host?", urn.host === "");   // true -> it locates nothing
```

**How to run:** `node ids.js`. Note how the URL exposes a host/path/query (a location), while the URN has **no host** — it's purely a name.

## 6. Walkthrough

- `new URL("https://...")` parses a real **URL**. The `protocol` (`https:`) is the scheme that tells a client *how to retrieve* the resource — that locating ability is what makes it a URL.
- `host`, `pathname`, and `search` together describe **where** the resource is and which variant you want. A client can act on all of this to fetch bytes.
- `new URL("urn:isbn:...")` still parses (a URN is a valid URI), but `protocol` is `urn:` and crucially `host` is empty. There's **no location** — only `pathname` holds the name `isbn:9780131103627`.
- So the same parser shows the difference: the `https` value carries a fetchable address; the `urn` value carries only an identifying name. Both are URIs; their *intent* differs.
- This is exactly why a URL can 404 (the location changed) while a URN can't (it never claimed a location).

## 7. Gotchas & takeaways

> In everyday talk, say "URL" and you'll be understood. But when a **specification** says "URI," don't assume it must be fetchable — XML namespaces and some identifiers are URIs that you should never try to download.

> A URN needs a separate **resolver** to become useful (ISBN → a library catalogue, for instance). It guarantees a stable name, not retrievability. Don't expect to paste `urn:isbn:...` into a browser and get a book.

- URI is the umbrella; URL and URN are kinds of URI.
- URL = identifier **plus** location/protocol (how to fetch). It can break if the resource moves.
- URN = a permanent **name**, no location, needs resolving to fetch anything.
- Quick test: does the scheme imply retrieval? Then it's behaving as a URL.
