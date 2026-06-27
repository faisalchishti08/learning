---
card: webdev
gi: 4
slug: static-vs-dynamic-web-pages
title: Static vs dynamic web pages
---

## 1. What it is

This is about **how a page's HTML is produced**:

- A **static page** is a file that already exists on disk. The server finds it and sends it **as-is** — the same bytes to everyone. Think of a printed flyer: identical for every reader.
- A **dynamic page** is **built on demand**. The server runs code (or the browser runs JavaScript) to assemble the HTML *for this particular request*, often using a database. Think of a custom letter with your name and order details filled in.

"Static" doesn't mean boring or non-interactive — a static page can have animations and JavaScript. It means **the HTML the server delivers was not generated per-request.**

## 2. Why & when

The trade-off is **speed/simplicity vs personalisation/freshness**:

- **Static** is extremely fast (just serve a file), cheap, cacheable, and hard to hack (no server code per request). But every visitor sees the same thing.
- **Dynamic** can tailor content to the user, show live data, and react to input. But it needs server logic and/or a database, costs more, and is slower per request.

Use **static** when content is the same for everyone and changes rarely: marketing pages, blogs, documentation, this checklist.

Use **dynamic** when content depends on **who** is asking or **when**: a logged-in dashboard, search results, a price that changes, a social feed.

Modern reality: many sites are **both** — static shells with dynamic data fetched by JavaScript, or pre-rendered pages that hydrate into apps (see rendering strategies like SSG/SSR).

## 3. Core concept

There are two *different* axes people lump under "dynamic," and it helps to separate them:

1. **Server-dynamic** — the *server* generates HTML per request (PHP, a Spring controller with a template, Express + EJS). The browser receives finished, personalised HTML.
2. **Client-dynamic** — the server sends a fixed page, and *JavaScript in the browser* changes it afterward (fetching data, updating the DOM). The delivered file is static; the *experience* is dynamic.

So a page can be:

| | HTML built per request? | Example |
|---|---|---|
| **Static** | No — file on disk | A `.html` landing page |
| **Server-dynamic** | Yes, on the server | Profile page rendered with your data |
| **Client-dynamic** | No, but JS mutates it | Static shell that fetches a live feed |

The classic "static vs dynamic" distinction is about that middle question: **did the server build this HTML specifically for this request?** If yes → dynamic. If it just handed over a pre-made file → static.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Static returns a file as-is; dynamic runs code and a database to build HTML per request">
  <text x="160" y="30" fill="#3fb950" font-size="13" text-anchor="middle" font-family="sans-serif">STATIC</text>
  <rect x="60" y="50" width="90" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="105" y="75" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Request</text>
  <rect x="190" y="50" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="245" y="68" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server finds</text>
  <text x="245" y="82" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">page.html</text>
  <line x1="150" y1="70" x2="188" y2="70" stroke="#8b949e" stroke-width="2"/>
  <text x="245" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">same file for everyone</text>

  <text x="420" y="30" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif">DYNAMIC</text>
  <rect x="330" y="50" width="80" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="370" y="75" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Request</text>
  <rect x="430" y="50" width="90" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="475" y="68" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Run code</text>
  <text x="475" y="82" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">+ DB</text>
  <rect x="540" y="50" width="80" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="580" y="68" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Build</text>
  <text x="580" y="82" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">HTML</text>
  <line x1="410" y1="70" x2="428" y2="70" stroke="#8b949e" stroke-width="2"/>
  <line x1="520" y1="70" x2="538" y2="70" stroke="#8b949e" stroke-width="2"/>
  <text x="475" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">tailored per request</text>
</svg>

Static skips the code-and-database step entirely; dynamic pays for it to personalise.

## 5. Runnable example

One server, two routes: `/static` returns the same HTML every time, `/dynamic` builds HTML using the current time and a query parameter — different for every request.

```js
// save as pages.js — run: node pages.js
const http = require("http");

http.createServer((req, res) => {
  const url = new URL(req.url, "http://localhost:3000");
  res.writeHead(200, { "Content-Type": "text/html" });

  if (url.pathname === "/static") {
    // STATIC: identical bytes for everyone
    res.end("<h1>Welcome</h1><p>This text never changes.</p>");
  } else {
    // DYNAMIC: built right now, using inputs from THIS request
    const name = url.searchParams.get("name") || "stranger";
    res.end(`<h1>Hello, ${name}</h1><p>Generated at ${new Date().toISOString()}</p>`);
  }
}).listen(3000, () => console.log("Try http://localhost:3000/static and /dynamic?name=Sam"));
```

**How to run:** `node pages.js`, then visit `http://localhost:3000/static` (same every time) and `http://localhost:3000/dynamic?name=Sam` (refresh — the timestamp changes).

## 6. Walkthrough

- Both routes live in one server so you can compare them side by side.
- `/static` calls `res.end("<h1>Welcome</h1>...")` with a **fixed string**. No inputs, no database — every visitor gets identical HTML. That's static behaviour (here built in code, but conceptually a pre-made file).
- `/dynamic` reads `url.searchParams.get("name")` — input **from this specific request** — and `new Date()` — the moment of the request. It interpolates them into the HTML with a template literal.
- Refresh `/dynamic`: the timestamp changes each time, and `?name=Sam` vs `?name=Lee` produces different pages. The HTML is **manufactured per request**. That's the essence of dynamic.
- Real dynamic pages swap `new Date()` for a database query ("get this user's orders"), but the principle is identical: run code, build HTML for *this* caller.

## 7. Gotchas & takeaways

> "Static" is not the opposite of "interactive." A static `.html` file can have rich JavaScript animations. Static refers to **how the HTML was produced** (pre-made file), not to whether the page moves.

> Dynamic pages cost more on every request (CPU, database). That's why caching and static-site generation exist — to get personalised-looking results without paying the dynamic price each time.

- Static = serve a pre-made file, same for all; fast, cheap, cacheable.
- Dynamic = build HTML per request using code/DB/inputs; personalised, fresh, costlier.
- "Client-dynamic" pages are delivered static but mutated by browser JavaScript afterward.
- The defining question: *was this HTML generated specifically for this request?*
