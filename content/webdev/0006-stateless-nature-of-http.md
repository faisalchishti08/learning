---
card: webdev
gi: 6
slug: stateless-nature-of-http
title: Stateless nature of HTTP
---

## 1. What it is

**HTTP is stateless**: the server treats every request as if it had **never seen you before**. Once it sends a response, it forgets the whole exchange. The next request from the same person arrives with **no built-in memory** of the last one.

Imagine a shop assistant with total amnesia between sentences. You say "I'd like a coffee." They make it. You say "and a muffin" — and they have no idea who you are or that you just ordered coffee. Every request must re-introduce itself.

This is by **design**, not a bug. It keeps servers simple and scalable. "State" (who you are, what's in your cart) is added back **on top** of HTTP using cookies, sessions, and tokens.

## 2. Why & when

Statelessness is a deliberate trade that buys huge benefits:

- **Scalability** — because no request depends on server memory of a previous one, any server in a farm can handle any request. You can add 100 servers behind a load balancer and it just works.
- **Simplicity & resilience** — if a server crashes, no in-progress "conversation" is lost; the next request can go anywhere.
- **Caching** — self-contained requests are easy to cache.

But almost every real app **needs** to remember things: that you're logged in, your cart, your preferences. So you constantly work *with* and *around* statelessness:

- Logging in → you must carry proof of identity on **every** later request.
- Shopping carts, multi-step forms, "stay signed in" → all are state layered onto a stateless protocol.

You think about this whenever you handle **authentication or sessions**.

## 3. Core concept

Because the server forgets, the **client must remind it** on every request. The standard mechanisms:

1. **Cookies** — the server sends `Set-Cookie: id=abc` once; the browser **automatically attaches** `Cookie: id=abc` to every future request to that site. Now the server can look you up.
2. **Sessions** — the cookie holds just an ID; the server keeps the real data (who you are) in its own store keyed by that ID. Memory lives server-side, the key travels with each request.
3. **Tokens (e.g. JWT)** — the client stores a signed token and sends it in an `Authorization: Bearer ...` header on each request. The token itself carries identity, so the server may need no per-user storage.

The pattern is always the same: **state is reconstructed each request** from something the client sends along. HTTP stays stateless; identity rides inside the request.

A subtle point: statelessness is about the **protocol**, not your app. Your app obviously has state (databases, sessions). HTTP just refuses to remember *between requests on its own* — you make memory explicit by passing it every time.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two independent requests; the server only knows the user because the client resends a cookie">
  <rect x="30" y="40" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="105" y="62" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="105" y="78" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">stores cookie id=abc</text>
  <rect x="460" y="40" width="150" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="535" y="62" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Server</text>
  <text x="535" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">forgets after</text>
  <text x="535" y="94" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">each response</text>

  <line x1="180" y1="120" x2="458" y2="120" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="320" y="113" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">Request 1  + Cookie: id=abc</text>
  <line x1="180" y1="175" x2="458" y2="175" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="320" y="168" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">Request 2  + Cookie: id=abc (again!)</text>
  <text x="320" y="205" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the cookie must be re-sent every time — server keeps no memory</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The two requests are independent; only the **re-sent cookie** lets the server recognise the same user.

## 5. Runnable example

This server proves it has no memory unless the client carries an ID. It counts visits — but only correctly because the **browser re-sends a cookie** each time.

```js
// save as visits.js — run: node visits.js, open http://localhost:3000, refresh a few times
const http = require("http");
const counts = {};                       // server-side store, keyed by cookie id

http.createServer((req, res) => {
  const cookie = (req.headers.cookie || "");
  let id = (cookie.match(/id=(\w+)/) || [])[1];

  if (!id) {                             // first ever visit: no cookie -> brand new identity
    id = Math.random().toString(36).slice(2, 8);
    res.setHeader("Set-Cookie", `id=${id}`);   // tell the browser to remember this
    counts[id] = 0;
  }
  counts[id] = (counts[id] || 0) + 1;

  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end(`You (id=${id}) have visited ${counts[id]} time(s).`);
}).listen(3000, () => console.log("Open http://localhost:3000 and refresh"));
```

**How to run:** `node visits.js`, open `http://localhost:3000`, and refresh. The count rises because your browser keeps re-sending the cookie. Open a **private/incognito** window (no cookie) and the count restarts at 1 — a "new" user.

## 6. Walkthrough

- `counts` is the **server's memory**, but HTTP gives the server no way to know *which* counter belongs to *you* — unless you tell it.
- On your first request there's **no `Cookie` header**, so `id` is empty. The server mints a random `id`, sends `Set-Cookie: id=...`, and starts a counter. This is the server handing the client a name tag.
- The browser stores that cookie and, on every later request to this site, **automatically** includes `Cookie: id=...`. The server reads it back with the regex and finds *your* counter.
- Because each request re-supplies the id, the server can act "as if" it remembers you — even though, per request, it started from nothing.
- Incognito has a fresh cookie jar, so it sends no id, gets a new one, and counts from 1. That demonstrates the truth: the server never remembered you; the **cookie** did.

## 7. Gotchas & takeaways

> Statelessness is a feature, not a limitation to "fix." It's exactly what lets the web scale to billions of requests across many servers. You **add** state deliberately with cookies/sessions/tokens — you don't remove statelessness.

> If you store session data **in one server's memory** and run multiple servers, a user's second request may hit a different server that has never seen them. Solutions: a shared session store (Redis/DB), sticky sessions, or self-contained tokens (JWT). This is a classic production bug.

- HTTP forgets between requests by design; each request must be self-contained.
- Identity is carried *in* the request — usually a cookie (auto-sent) or an `Authorization` token.
- Sessions keep data server-side keyed by a cookie id; tokens carry identity in the request itself.
- "Stateless protocol" ≠ "stateless app." Your app has state; HTTP just won't remember it for you.
