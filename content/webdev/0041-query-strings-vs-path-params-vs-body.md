---
card: webdev
gi: 41
slug: query-strings-vs-path-params-vs-body
title: Query strings vs path params vs body
---

## 1. What it is

HTTP requests carry data from client to server in three different places:

- **Path parameters** — values embedded in the URL path: `/users/42` (the `42` is a path param).
- **Query strings** — key/value pairs after the `?` in the URL: `/search?q=cats&page=2`.
- **Request body** — data sent alongside `POST`/`PUT`/`PATCH` requests, usually as JSON or form data.

Choosing the right place for each piece of data shapes your API's design, cacheability, and security.

## 2. Why & when

The three locations exist for different purposes. Misplacing data causes real problems:

- Putting a password in the URL query string leaks it in server logs, browser history, and `Referer` headers.
- Putting a filter in the body of a `GET` request breaks caching and isn't cacheable by CDNs.
- Using the body for an ID (`{"userId": 42}`) instead of the path (`/users/42`) makes your API non-RESTful and harder to link to.

The right location depends on what the data *means*, not just where it's convenient to put it.

## 3. Core concept

**Path parameters** — identify *which* resource. They're part of the resource's identity, like a street address. `/users/42` and `/users/99` are two different resources.

```
/articles/{articleId}/comments/{commentId}
/orders/{orderId}/items/{itemId}
```

Use path params for: resource IDs, nested resource relationships.

**Query strings** — *filter, sort, or paginate* within a collection. They modify how you see the resource without changing its identity. `/products?category=shoes&sort=price&page=3`.

```
/search?q=java+programming&lang=en&limit=10
/events?from=2026-01-01&to=2026-12-31&status=active
```

Use query strings for: search terms, filters, pagination, optional flags. They're visible, shareable, and bookmarkable.

**Request body** — *data to create or modify*. Used with `POST`, `PUT`, `PATCH`. The body is opaque to URLs, so it doesn't appear in logs or bookmarks.

```json
POST /users
{"name": "Alice", "email": "a@a.com", "password": "s3cret"}
```

Use the body for: the payload of mutations (new/updated records), sensitive data (passwords, tokens), large amounts of data, file uploads.

| | Path params | Query string | Body |
|---|---|---|---|
| Visible in logs/history | ✅ | ✅ | ❌ |
| Cacheable by CDN | ✅ | ✅ | ❌ |
| Used with GET | ✅ | ✅ | ❌ (avoid) |
| Best for | Resource ID | Filters/search | Mutations/secrets |

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="URL broken into scheme, host, path with path params highlighted, question mark, query string, and a separate body payload below">
  <rect width="680" height="260" fill="#0d1117"/>

  <!-- URL bar -->
  <rect x="20" y="30" width="640" height="44" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>

  <!-- scheme+host -->
  <text x="36" y="58" fill="#8b949e" font-size="13" font-family="monospace">https://api.example.com</text>

  <!-- path with param -->
  <text x="260" y="58" fill="#6db33f" font-size="13" font-family="monospace">/users/</text>
  <rect x="320" y="38" width="32" height="26" rx="3" fill="#22331a"/>
  <text x="336" y="58" fill="#6db33f" font-size="13" font-family="monospace" font-weight="bold">42</text>

  <!-- /comments/ -->
  <text x="358" y="58" fill="#6db33f" font-size="13" font-family="monospace">/comments</text>

  <!-- ? -->
  <text x="455" y="58" fill="#e6edf3" font-size="13" font-family="monospace">?</text>

  <!-- query string -->
  <rect x="467" y="38" width="176" height="26" rx="3" fill="#1a2233"/>
  <text x="475" y="58" fill="#79c0ff" font-size="13" font-family="monospace">sort=date&page=2</text>

  <!-- Labels below URL -->
  <text x="336" y="92" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">↑ path param (resource ID)</text>
  <text x="555" y="92" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">↑ query string (filter)</text>

  <!-- Body box -->
  <rect x="20" y="118" width="640" height="110" rx="6" fill="#1c2430" stroke="#e3b341" stroke-width="1.2"/>
  <text x="40" y="140" fill="#e3b341" font-size="11" font-family="sans-serif">Request Body  (POST/PUT/PATCH only)</text>
  <text x="40" y="162" fill="#e6edf3" font-size="12" font-family="monospace">{</text>
  <text x="60" y="180" fill="#e6edf3" font-size="12" font-family="monospace">"name": "Alice",</text>
  <text x="60" y="198" fill="#e6edf3" font-size="12" font-family="monospace">"email": "alice@example.com",</text>
  <text x="60" y="216" fill="#e3b341" font-size="12" font-family="monospace">"password": "s3cret"   ← sensitive: invisible in URL/logs</text>
  <text x="40" y="224" fill="#e6edf3" font-size="12" font-family="monospace">}</text>
</svg>

Path = identity; query = filters; body = mutation payload (and secrets).

## 5. Runnable example

```js
// save as param-demo.js — needs Node.js, no installs
const http = require("http");
const url  = require("url");

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true); // true = parse query string
  const path   = parsed.pathname;         // "/users/42"
  const query  = parsed.query;            // { sort: "date", page: "2" }

  // Extract path param with a simple regex
  const pathMatch = path.match(/^\/users\/(\d+)(?:\/comments)?$/);
  const userId    = pathMatch ? pathMatch[1] : null;

  res.setHeader("Content-Type", "application/json");

  // GET /users/:id — path param
  if (req.method === "GET" && userId) {
    return res.end(JSON.stringify({
      location: "path param",
      userId,
      filters: query, // sort, page, etc.
    }));
  }

  // POST /users — body
  if (req.method === "POST" && path === "/users") {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      const data = JSON.parse(body);
      console.log("Received body:", data);
      res.writeHead(201);
      res.end(JSON.stringify({ created: data.name, via: "request body" }));
    });
    return;
  }

  res.writeHead(404);
  res.end(JSON.stringify({ error: "not found" }));
});

server.listen(3000, () => {
  // 1. GET with path param + query string
  http.get("http://localhost:3000/users/42?sort=date&page=2", (res) => {
    let b = "";
    res.on("data", (c) => (b += c));
    res.on("end", () => {
      console.log("GET response:", b);

      // 2. POST with body
      const body = JSON.stringify({ name: "Alice", password: "s3cret" });
      const opts = {
        hostname: "localhost", port: 3000, path: "/users", method: "POST",
        headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) },
      };
      const r = http.request(opts, (res2) => {
        let b2 = "";
        res2.on("data", (c) => (b2 += c));
        res2.on("end", () => { console.log("POST response:", b2); server.close(); });
      });
      r.write(body);
      r.end();
    });
  });
});
```

**How to run:** `node param-demo.js` — built-in `http` and `url`, no npm.

## 6. Walkthrough

- `url.parse(req.url, true)` — parses the full URL; `parsed.query` is already an object (`{ sort: "date", page: "2" }`).
- `path.match(/^\/users\/(\d+)/)` — regex captures the numeric segment after `/users/`; this is the path parameter.
- `GET /users/42?sort=date&page=2` hits the first handler: the `42` comes from the path, the sort/page come from `query`.
- `POST /users` body — JSON string sent via `req.write()`. Server assembles chunks into `body`, parses it, and uses `data.name` to build the response.
- `data.password` — notice it's in the body, not the URL. It's printed to the server's console (in a real app you'd hash it immediately), but it never appears in any URL or log line.
- `201 Created` confirms a new resource was created.

## 7. Gotchas & takeaways

> **Never put secrets (passwords, tokens, credit card numbers) in the URL.** URLs appear in browser history, access logs, CDN logs, and the `Referer` header when the user clicks a link. They're effectively public. Put secrets in the request body, over HTTPS.

> Query strings are case-sensitive and order matters for caching. `/products?a=1&b=2` and `/products?b=2&a=1` are technically different cache keys even if your server treats them identically. Normalise query parameter order in your cache keys.

- **Path params** identify *which* resource: `/users/42`.
- **Query strings** modify or filter the response: `?sort=date&page=2`. Visible, cacheable.
- **Body** carries the mutation payload or sensitive data. Not in URLs, not cached.
- Sensitive data belongs in the body (encrypted by HTTPS), never in the URL.
- `url.parse(req.url, true)` splits path and query; regex or path-matching libraries extract path params.
