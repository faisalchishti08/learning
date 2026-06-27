---
card: webdev
gi: 59
slug: cookies-set-cookie-attributes
title: Cookies (Set-Cookie, attributes)
---

## 1. What it is

A **cookie** is a small piece of data that a server asks the browser to store and send back on every subsequent request to that domain. Cookies are the foundational mechanism for HTTP state — they let a stateless protocol remember things across requests.

The server creates a cookie by sending a `Set-Cookie` response header:

```
Set-Cookie: sessionId=abc123; Max-Age=3600; HttpOnly; Secure; SameSite=Strict
```

The browser stores it and automatically attaches it as a `Cookie` request header on future requests:

```
Cookie: sessionId=abc123
```

Cookies are used for sessions, authentication tokens, user preferences, analytics tracking, and shopping carts.

## 2. Why & when

HTTP is stateless — a server has no memory of who it talked to before. Cookies solve this. Without them, you would need to re-authenticate on every page load.

Key uses:

| Use case | Example cookie |
|----------|---------------|
| Authentication | `sessionId=abc123` — identifies your logged-in session |
| Preferences | `theme=dark` — persists UI settings |
| Analytics | `_ga=GA1.2...` — tracks visits (Google Analytics) |
| Shopping cart | `cartId=xyz` — keeps items between pages |

Set a cookie when the server needs the client to "remember" something across requests, and you want that data sent automatically (unlike `localStorage`, cookies are sent with every request).

## 3. Core concept

Analogy: a **coat check ticket**. You hand your coat (a session) to the attendant (server). They give you a numbered ticket (cookie). Every time you come back, you show the ticket and they retrieve your coat. The ticket itself has no coat — just a reference.

A `Set-Cookie` header has a **name=value** pair and optional **attributes** that control its lifetime and security:

```
Set-Cookie: name=value; Expires=...; Max-Age=...; Domain=...; Path=...; Secure; HttpOnly; SameSite=...
```

Key attributes at a glance (detail in the next tutorial):

| Attribute | Controls |
|-----------|----------|
| `Max-Age` / `Expires` | How long it lives |
| `Domain` | Which domains receive it |
| `Path` | Which URL paths receive it |
| `Secure` | HTTPS-only transmission |
| `HttpOnly` | Hidden from JavaScript |
| `SameSite` | Cross-site request rules |

The browser enforces these — they are hints from the server about how to handle the cookie.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cookie lifecycle: server sets cookie, browser stores and sends it on next request">
  <defs>
    <marker id="arr59a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr59b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Browser -->
  <rect x="30" y="80" width="160" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="108" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser</text>
  <text x="110" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">stores cookie jar</text>
  <text x="110" y="142" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">sessionId=abc123</text>

  <!-- Server -->
  <rect x="450" y="80" width="160" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="108" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>
  <text x="530" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Set-Cookie on login</text>

  <!-- Arrow 1: request (GET /) -->
  <line x1="192" y1="100" x2="448" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr59a)"/>
  <text x="320" y="92" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">1. GET /login (no cookie yet)</text>

  <!-- Arrow 2: response with Set-Cookie -->
  <line x1="448" y1="140" x2="192" y2="140" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr59b)"/>
  <text x="320" y="162" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">2. 200 OK + Set-Cookie: sessionId=abc123</text>

  <!-- Arrow 3: next request with Cookie -->
  <line x1="192" y1="180" x2="448" y2="180" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr59a)"/>
  <text x="320" y="200" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">3. GET /dashboard — Cookie: sessionId=abc123</text>
</svg>

Server sets the cookie once; browser sends it automatically on every matching request thereafter.

## 5. Runnable example

```js
// server.js — Node.js, no installs.
const http = require("http");

const sessions = {}; // in-memory session store

http.createServer((req, res) => {
  if (req.url === "/login") {
    // Issue a session cookie
    const id = Math.random().toString(36).slice(2);
    sessions[id] = { user: "alice", loggedInAt: new Date().toISOString() };

    res.setHeader("Set-Cookie", [
      `sessionId=${id}; Max-Age=3600; HttpOnly; Path=/`
    ]);
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(`Logged in. Session: ${id}`);

  } else if (req.url === "/profile") {
    // Read the cookie to identify the user
    const cookieHeader = req.headers.cookie || "";
    const match = cookieHeader.match(/sessionId=([^;]+)/);
    const session = match && sessions[match[1]];

    if (session) {
      res.writeHead(200, { "Content-Type": "text/plain" });
      res.end(`Hello ${session.user}! Logged in at ${session.loggedInAt}`);
    } else {
      res.writeHead(401, { "Content-Type": "text/plain" });
      res.end("No valid session. Visit /login first.");
    }

  } else {
    res.writeHead(404);
    res.end("try /login or /profile");
  }
}).listen(3000, () => console.log("http://localhost:3000"));
```

**How to run:** `node server.js`. Open `http://localhost:3000/login` then `http://localhost:3000/profile`. The browser automatically sends the cookie on the second request.

## 6. Walkthrough

- `/login` generates a random session ID, stores data server-side in `sessions`, and sends `Set-Cookie` back to the browser.
- `Max-Age=3600` makes the cookie expire in one hour. `HttpOnly` prevents JavaScript access. `Path=/` means it's sent for all paths on this domain.
- On `/profile`, the server reads `req.headers.cookie`, parses the `sessionId` value with a regex, and looks it up in `sessions`.
- The session data (user, time) never travels to the browser — only the opaque `sessionId` does. This is the **reference token** pattern.
- If you visit `/profile` in a fresh browser (no cookie), you get 401 — correct behavior.

## 7. Gotchas & takeaways

> **Never store sensitive data inside the cookie value.** The cookie value travels to the browser. Store it server-side and put only an opaque ID in the cookie.

> **Cookies are sent with every matching request, including images and fonts.** A fat cookie on a site with 50 sub-resources adds up. Keep cookie values small (a few dozen bytes).

- `Set-Cookie` is the server's instruction; `Cookie` is the browser's automatic response.
- Multiple cookies are set with multiple `Set-Cookie` headers (one per cookie).
- Cookies are scoped to a domain and path — they aren't sent to other domains.
- Browser DevTools → Application → Cookies lets you inspect, edit, and delete cookies.
- Cookie attributes (HttpOnly, Secure, SameSite) dramatically affect security — covered in the next tutorial.
