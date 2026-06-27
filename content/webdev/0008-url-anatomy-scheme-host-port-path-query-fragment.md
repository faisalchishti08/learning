---
card: webdev
gi: 8
slug: url-anatomy-scheme-host-port-path-query-fragment
title: URL anatomy (scheme, host, port, path, query, fragment)
---

## 1. What it is

A URL is not one blob — it's a **structured address** with named parts, each doing a specific job. Take:

```
https://shop.example.com:8443/products/shoes?color=red&size=9#reviews
```

- **scheme** — `https` — *how* to talk (the protocol).
- **host** — `shop.example.com` — *which machine* (resolved by DNS).
- **port** — `8443` — *which door* on that machine.
- **path** — `/products/shoes` — *which resource* on the server.
- **query** — `?color=red&size=9` — *parameters* refining the request.
- **fragment** — `#reviews` — *which part of the page* to scroll to (browser-only).

Knowing the parts lets you read, build, and debug URLs precisely.

## 2. Why & when

You manipulate URL parts constantly:

- **Routing**: backends switch on the **path** to decide what to return.
- **Filtering/search/pagination**: encoded in the **query** (`?page=2&sort=price`).
- **Linking to a section**: the **fragment** (`#install`) jumps within a page.
- **Local vs prod**: the **host** and **port** change between `localhost:3000` and `example.com:443`.

When it bites you:

- Forgetting to **URL-encode** a query value with spaces or `&` → broken parameters.
- Sending secrets in the **query string** (they end up in logs and browser history) — a security mistake.
- Expecting the server to see the **fragment** — it never does; fragments stay in the browser.

## 3. Core concept

Read a URL left to right; each part hands off to the next stage:

1. **scheme** (`https:`) decides the protocol and the **default port** (http→80, https→443). If the scheme's default matches, the port is omitted.
2. **authority** = `host` (+ optional `:port`). The host is resolved by **DNS** to an IP; the port selects the listening service. `//` introduces the authority.
3. **path** (`/products/shoes`) identifies the resource within that server. Modern apps map paths to routes/handlers.
4. **query** (`?key=value&key2=value2`) is a `&`-separated list of key/value pairs. It refines *what* you want (filters, search terms). Values must be **percent-encoded** if they contain special characters (space → `%20`).
5. **fragment** (`#reviews`) is handled **entirely by the browser** — it scrolls to an element with that id or drives client-side routing. It is **not sent to the server**.

Who sees what:

| Part | Sent to server? | Resolved by |
|---|---|---|
| scheme | (determines connection) | client |
| host | yes (as `Host` header) | DNS |
| port | (used to connect) | client/OS |
| path | yes | server routing |
| query | yes | server logic |
| fragment | **no** | browser only |

That last row is the most commonly forgotten fact in the whole topic.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A URL split into labelled coloured segments">
  <text x="20" y="70" font-family="monospace" font-size="15">
    <tspan fill="#3fb950">https</tspan><tspan fill="#8b949e">://</tspan><tspan fill="#79c0ff">shop.example.com</tspan><tspan fill="#d2a8ff">:8443</tspan><tspan fill="#ffa657">/products/shoes</tspan><tspan fill="#f0883e">?color=red&amp;size=9</tspan><tspan fill="#ff7b72">#reviews</tspan>
  </text>
  <text x="20" y="110" font-family="sans-serif" font-size="11"><tspan fill="#3fb950">scheme</tspan></text>
  <text x="120" y="110" font-family="sans-serif" font-size="11"><tspan fill="#79c0ff">host</tspan></text>
  <text x="280" y="110" font-family="sans-serif" font-size="11"><tspan fill="#d2a8ff">port</tspan></text>
  <text x="340" y="130" font-family="sans-serif" font-size="11"><tspan fill="#ffa657">path</tspan></text>
  <text x="450" y="150" font-family="sans-serif" font-size="11"><tspan fill="#f0883e">query</tspan></text>
  <text x="560" y="170" font-family="sans-serif" font-size="11"><tspan fill="#ff7b72">fragment (browser only)</tspan></text>
</svg>

Each colour is a separate component with its own role; only the fragment stays out of the request.

## 5. Runnable example

The built-in `URL` object pulls every component apart for you.

```js
// save as anatomy.js — run: node anatomy.js   (URL is a global in modern Node and all browsers)
const u = new URL("https://shop.example.com:8443/products/shoes?color=red&size=9#reviews");

console.log("scheme  :", u.protocol);     // "https:"
console.log("host    :", u.hostname);     // "shop.example.com"
console.log("port    :", u.port);         // "8443"
console.log("path    :", u.pathname);     // "/products/shoes"
console.log("query   :", u.search);       // "?color=red&size=9"
console.log("fragment:", u.hash);         // "#reviews"

// queries are best read as key/value pairs:
console.log("color   :", u.searchParams.get("color")); // "red"
console.log("size    :", u.searchParams.get("size"));   // "9"

// building one safely (auto-encodes!):
const made = new URL("https://api.example.com/search");
made.searchParams.set("q", "red shoes & socks");
console.log("built   :", made.href);      // ...?q=red+shoes+%26+socks
```

**How to run:** `node anatomy.js`. The same code runs in a browser console too.

## 6. Walkthrough

- `new URL(...)` parses the string once; each property then exposes a part — no manual string-splitting (which is error-prone).
- `protocol` includes the trailing colon (`https:`); `hostname` is the bare host; `port` is `8443` because it's non-default (for plain `https` it would be empty).
- `pathname` is what the server routes on; `search` is the raw query string starting with `?`.
- `hash` is the fragment (`#reviews`). Remember: although the parser shows it, this value is **never transmitted** to `shop.example.com` — only the browser uses it.
- `searchParams.get("color")` reads a single query value cleanly, instead of hand-parsing `?color=red&size=9`.
- The build step shows why you should use `URL`/`searchParams`: `set("q", "red shoes & socks")` **percent-encodes** the space and `&` automatically (`%26`), preventing a broken or injected query. Concatenating strings by hand would corrupt the URL.

## 7. Gotchas & takeaways

> **The fragment (`#...`) never reaches the server.** If your server-side analytics or routing depends on it, it won't work. Fragments are purely client-side (anchor scrolling, hash routing).

> **Never put secrets in the query string.** Query strings are saved in browser history, server logs, and `Referer` headers. Put sensitive data in the request body or headers, over HTTPS.

> Always **encode** query values you build from user input. Use `URL`/`URLSearchParams` (or `encodeURIComponent`) — never glue strings together, or special characters like `&`, `=`, `#`, and spaces will break or hijack your URL.

- A URL = scheme + host (+port) + path + query + fragment, each with a distinct job.
- Default ports (80/443) are implied by the scheme and usually omitted.
- Server sees scheme-connection, host, port, path, query — **not** the fragment.
- Parse and build with the `URL` API to get correct encoding for free.
