---
card: webdev
gi: 36
slug: http-status-codes-1xx5xx-their-meaning
title: HTTP status codes (1xx–5xx) & their meaning
---

## 1. What it is

An HTTP **status code** is a three-digit number in the response's status line that tells the client how the request went. The first digit gives the category:

| Range | Class | Meaning |
|-------|-------|---------|
| 1xx | Informational | Request received, keep going |
| 2xx | Success | Request worked |
| 3xx | Redirection | Go somewhere else |
| 4xx | Client error | You sent something wrong |
| 5xx | Server error | Server failed |

The most common codes in practice: `200`, `201`, `204`, `301`, `302`, `304`, `400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`, `502`, `503`.

## 2. Why & when

Status codes let clients, proxies, and infrastructure make decisions without parsing the response body. A `301` tells any HTTP client to follow the new URL, regardless of whether it's a browser, curl, or a microservice. A `5xx` tells load balancers to route to a different instance. A `304` tells the browser it can use its cached copy and skip downloading again. Getting codes right matters because:

- Browsers only retry `429` (rate-limited) or `5xx` automatically.
- Search engine crawlers use `301` to update indexed URLs.
- `401` vs `403` has a specific semantic difference your API clients depend on.
- Incorrect `200` on an error path breaks every consumer that checks the code before the body.

## 3. Core concept

Think of status codes as a door's response to a knock. `200` = "come in, here's what you asked for". `301` = "we moved, try next door". `404` = "no one by that name here". `500` = "the building is on fire, try later".

**Most important codes to know:**

**2xx — Success**
- `200 OK` — standard success with a body.
- `201 Created` — something new was created (include a `Location` header with its URL).
- `204 No Content` — success but no body (common after `DELETE`).

**3xx — Redirection**
- `301 Moved Permanently` — resource moved forever; clients and crawlers update their bookmarks.
- `302 Found` — temporary redirect; clients follow but don't update bookmarks.
- `304 Not Modified` — response to a conditional GET; client can use its cached copy.

**4xx — Client Error**
- `400 Bad Request` — malformed syntax, missing required field.
- `401 Unauthorized` — not authenticated (no or invalid credentials). Despite the name, it means "unauthenticated".
- `403 Forbidden` — authenticated but not allowed to do this.
- `404 Not Found` — resource doesn't exist (or server is hiding its existence).
- `409 Conflict` — state conflict (e.g. creating a duplicate email address).
- `422 Unprocessable Entity` — syntactically valid but semantically wrong (popular in REST APIs).
- `429 Too Many Requests` — rate limited; response often includes `Retry-After` header.

**5xx — Server Error**
- `500 Internal Server Error` — generic catch-all; something crashed.
- `502 Bad Gateway` — upstream service returned an invalid response.
- `503 Service Unavailable` — server down for maintenance or overloaded.

## 4. Diagram

<svg viewBox="0 0 680 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Status code families shown as horizontal bands with example codes">
  <rect width="680" height="320" fill="#0d1117"/>

  <!-- 1xx -->
  <rect x="30" y="20" width="620" height="44" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="50" y="47" fill="#8b949e" font-size="13" font-family="monospace" font-weight="bold">1xx</text>
  <text x="110" y="47" fill="#8b949e" font-size="12" font-family="sans-serif">Informational — </text>
  <text x="280" y="47" fill="#8b949e" font-size="12" font-family="monospace">100 Continue  101 Switching Protocols</text>

  <!-- 2xx -->
  <rect x="30" y="74" width="620" height="44" rx="6" fill="#162420" stroke="#6db33f" stroke-width="1.2"/>
  <text x="50" y="101" fill="#6db33f" font-size="13" font-family="monospace" font-weight="bold">2xx</text>
  <text x="110" y="101" fill="#6db33f" font-size="12" font-family="sans-serif">Success — </text>
  <text x="215" y="101" fill="#6db33f" font-size="12" font-family="monospace">200 OK  201 Created  204 No Content</text>

  <!-- 3xx -->
  <rect x="30" y="128" width="620" height="44" rx="6" fill="#1c2430" stroke="#e3b341" stroke-width="1.2"/>
  <text x="50" y="155" fill="#e3b341" font-size="13" font-family="monospace" font-weight="bold">3xx</text>
  <text x="110" y="155" fill="#e3b341" font-size="12" font-family="sans-serif">Redirection — </text>
  <text x="248" y="155" fill="#e3b341" font-size="12" font-family="monospace">301 Moved  302 Found  304 Not Modified</text>

  <!-- 4xx -->
  <rect x="30" y="182" width="620" height="60" rx="6" fill="#1c1a24" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="50" y="207" fill="#79c0ff" font-size="13" font-family="monospace" font-weight="bold">4xx</text>
  <text x="110" y="207" fill="#79c0ff" font-size="12" font-family="sans-serif">Client Error — </text>
  <text x="256" y="207" fill="#79c0ff" font-size="12" font-family="monospace">400 Bad Request  401 Unauth  403 Forbidden</text>
  <text x="256" y="228" fill="#79c0ff" font-size="12" font-family="monospace">404 Not Found  409 Conflict  429 Rate Limit</text>

  <!-- 5xx -->
  <rect x="30" y="252" width="620" height="44" rx="6" fill="#2d1a1a" stroke="#f85149" stroke-width="1.2"/>
  <text x="50" y="279" fill="#f85149" font-size="13" font-family="monospace" font-weight="bold">5xx</text>
  <text x="110" y="279" fill="#f85149" font-size="12" font-family="sans-serif">Server Error — </text>
  <text x="258" y="279" fill="#f85149" font-size="12" font-family="monospace">500 Server Error  502 Bad Gateway  503 Unavailable</text>
</svg>

First digit = who's at fault. `4xx` = client's problem. `5xx` = server's problem.

## 5. Runnable example

```js
// save as status-codes.js — needs Node.js, no installs
const http = require("http");

const server = http.createServer((req, res) => {
  // Route to different codes based on path
  const routes = {
    "/ok":        () => { res.writeHead(200); res.end("OK"); },
    "/created":   () => { res.writeHead(201, { Location: "/items/99" }); res.end("Created"); },
    "/no-content":() => { res.writeHead(204); res.end(); },
    "/moved":     () => { res.writeHead(301, { Location: "/ok" }); res.end(); },
    "/bad":       () => { res.writeHead(400); res.end("Missing required field: name"); },
    "/unauth":    () => { res.writeHead(401, { "WWW-Authenticate": 'Bearer realm="api"' }); res.end("No token"); },
    "/forbidden": () => { res.writeHead(403); res.end("You lack permission"); },
    "/error":     () => { res.writeHead(500); res.end("Something blew up"); },
  };

  const handler = routes[req.url];
  if (handler) handler();
  else { res.writeHead(404); res.end("Not found"); }
});

server.listen(3000, () => {
  const paths = ["/ok", "/created", "/no-content", "/bad", "/unauth", "/nope", "/error"];
  let pending = paths.length;

  paths.forEach((path) => {
    http.get("http://localhost:3000" + path, (res) => {
      let body = "";
      res.on("data", (c) => (body += c));
      res.on("end", () => {
        console.log(`${path.padEnd(14)} → ${res.statusCode} | ${body || "(no body)"}`);
        if (--pending === 0) server.close();
      });
    });
  });
});
```

**How to run:** `node status-codes.js` — built-in `http`, no npm.

## 6. Walkthrough

- `res.writeHead(201, { Location: "/items/99" })` — `201 Created` always pairs with a `Location` header pointing to the newly created resource.
- `res.writeHead(204); res.end()` — `204` has no body; calling `res.end("")` would be wrong (some clients reject a body on `204`).
- `res.writeHead(301, { Location: "/ok" })` — redirect; the `Location` header is mandatory for `3xx`.
- `res.writeHead(401, { "WWW-Authenticate": ... })` — `401` should include a `WWW-Authenticate` header telling the client what auth scheme the server expects.
- The `routes` object maps paths to handlers; anything unmapped falls to `404`.
- Parallel `http.get` calls at the end test each path; `pending` counts down to zero before closing.

## 7. Gotchas & takeaways

> `401 Unauthorized` actually means **unauthenticated** (no valid identity). `403 Forbidden` means **unauthorized** (identity known, permission denied). The names are historically swapped relative to their meanings — learn the numbers, not the English words.

> Never return `200` with an error in the body (e.g. `{"error": "not found"}`). It breaks every HTTP client that checks the status code before reading the body, including monitoring tools and load balancers.

- First digit is the category: `2xx` works, `4xx` client broke it, `5xx` server broke it.
- `201 Created` needs a `Location` header; `204 No Content` must have no body.
- `301` = permanent redirect (update bookmarks); `302` = temporary (don't update).
- `304 Not Modified` = use your cached copy; it has no body.
- Log and alert on `5xx`; `4xx` usually means a client bug, not a server bug.
