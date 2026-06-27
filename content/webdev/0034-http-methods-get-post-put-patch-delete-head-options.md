---
card: webdev
gi: 34
slug: http-methods-get-post-put-patch-delete-head-options
title: HTTP methods (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
---

## 1. What it is

An HTTP **method** (also called a *verb*) is the first word of a request line. It declares the client's **intent** — what it wants to do with the resource at the given path:

| Method | Intent |
|--------|--------|
| `GET` | Read a resource |
| `POST` | Create / submit |
| `PUT` | Replace entirely |
| `PATCH` | Partial update |
| `DELETE` | Remove |
| `HEAD` | Same as GET, but return only headers (no body) |
| `OPTIONS` | Ask what methods this endpoint allows |

## 2. Why & when

Methods give APIs a consistent vocabulary. Without them, every API would invent URLs like `/getUserById` and `/deleteUser`, producing sprawl. REST APIs map the *same* URL to different methods: `GET /users/42` reads, `DELETE /users/42` removes — same resource, different action. Knowing the method also lets HTTP infrastructure (caches, load balancers, proxies) make smart decisions: a cache may store a `GET` response but must never cache a `DELETE`.

## 3. Core concept

Think of the URL as a *noun* (the thing) and the method as a *verb* (the action). `GET /users/42` = "give me user 42". `DELETE /users/42` = "delete user 42".

**GET** — safest method. Retrieves a resource without side effects. Browser pre-fetching, bookmarking, and caching all rely on `GET` being safe to repeat.

**POST** — creates a new resource or submits data. Posting a form twice *should* create two records. Browsers warn you before resubmitting a POST ("Confirm Form Resubmission").

**PUT** — replaces the entire resource at a URL. You send the full new state; anything not in the body is wiped. `PUT /users/42` with `{"name":"Bob"}` removes every field that isn't `name`.

**PATCH** — partial update. You send only the fields you want changed. `PATCH /users/42` with `{"email":"b@b.com"}` only touches `email`.

**DELETE** — removes the resource. Usually returns `200`, `204`, or `404`.

**HEAD** — identical to `GET` but the server sends headers only, no body. Used to check if a resource exists or to get its size/content-type without downloading it (useful for large files).

**OPTIONS** — asks the server which methods and headers it accepts on a URL. Browsers send a preflight `OPTIONS` request before cross-origin `POST`/`PUT`/`DELETE` calls (CORS preflight).

## 4. Diagram

<svg viewBox="0 0 680 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTTP methods mapped to CRUD operations on a users resource">
  <!-- Title -->
  <text x="340" y="22" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">HTTP Methods → CRUD on /users</text>

  <!-- Column headers -->
  <text x="90"  y="48" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Method</text>
  <text x="260" y="48" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">URL example</text>
  <text x="460" y="48" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Meaning</text>

  <!-- Rows -->
  <!-- GET -->
  <rect x="20"  y="56" width="140" height="32" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="90"  y="76" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace">GET</text>
  <text x="260" y="76" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">GET /users/42</text>
  <text x="460" y="76" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Read user 42</text>

  <!-- POST -->
  <rect x="20"  y="98" width="140" height="32" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90"  y="118" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="monospace">POST</text>
  <text x="260" y="118" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">POST /users</text>
  <text x="460" y="118" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Create new user</text>

  <!-- PUT -->
  <rect x="20"  y="140" width="140" height="32" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90"  y="160" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="monospace">PUT</text>
  <text x="260" y="160" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">PUT /users/42</text>
  <text x="460" y="160" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Replace user 42 entirely</text>

  <!-- PATCH -->
  <rect x="20"  y="182" width="140" height="32" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90"  y="202" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="monospace">PATCH</text>
  <text x="260" y="202" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">PATCH /users/42</text>
  <text x="460" y="202" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Update one field of user 42</text>

  <!-- DELETE -->
  <rect x="20"  y="224" width="140" height="32" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1.2"/>
  <text x="90"  y="244" fill="#f85149" font-size="13" text-anchor="middle" font-family="monospace">DELETE</text>
  <text x="260" y="244" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">DELETE /users/42</text>
  <text x="460" y="244" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Remove user 42</text>

  <!-- HEAD -->
  <rect x="20"  y="266" width="140" height="32" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90"  y="286" fill="#8b949e" font-size="13" text-anchor="middle" font-family="monospace">HEAD</text>
  <text x="260" y="286" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">HEAD /users/42</text>
  <text x="460" y="286" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Headers only, no body</text>

  <!-- OPTIONS -->
  <rect x="20"  y="308" width="140" height="26" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90"  y="325" fill="#8b949e" font-size="13" text-anchor="middle" font-family="monospace">OPTIONS</text>
  <text x="260" y="325" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">OPTIONS /users</text>
  <text x="460" y="325" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">What methods are allowed here?</text>
</svg>

Same resource, different method → different action. The URL is the noun; the method is the verb.

## 5. Runnable example

```js
// save as methods-demo.js — needs Node.js, no installs
const http = require("http");

// Tiny in-memory "database"
let users = { 1: { id: 1, name: "Alice", email: "a@a.com" } };

const server = http.createServer((req, res) => {
  const id = req.url.match(/\/users\/(\d+)/)?.[1];

  let body = "";
  req.on("data", (c) => (body += c));
  req.on("end", () => {
    const data = body ? JSON.parse(body) : null;

    if (req.method === "GET" && id) {
      const user = users[id];
      if (!user) { res.writeHead(404); return res.end("Not found"); }
      res.writeHead(200, { "Content-Type": "application/json" });
      return res.end(JSON.stringify(user));
    }

    if (req.method === "POST" && req.url === "/users") {
      const newId = Date.now();
      users[newId] = { id: newId, ...data };
      res.writeHead(201, { "Content-Type": "application/json" });
      return res.end(JSON.stringify(users[newId]));
    }

    if (req.method === "PUT" && id) {
      users[id] = { id: Number(id), ...data }; // full replace
      res.writeHead(200, { "Content-Type": "application/json" });
      return res.end(JSON.stringify(users[id]));
    }

    if (req.method === "PATCH" && id) {
      users[id] = { ...users[id], ...data }; // merge
      res.writeHead(200, { "Content-Type": "application/json" });
      return res.end(JSON.stringify(users[id]));
    }

    if (req.method === "DELETE" && id) {
      delete users[id];
      res.writeHead(204);
      return res.end();
    }

    res.writeHead(405);
    res.end("Method Not Allowed");
  });
});

server.listen(3000, () => {
  console.log("Server ready. Run in a second terminal:");
  console.log("  curl http://localhost:3000/users/1");
  console.log("  curl -X DELETE http://localhost:3000/users/1");
});
```

**How to run:** `node methods-demo.js`, then in another terminal:
```bash
curl http://localhost:3000/users/1
curl -s -X PATCH -H "Content-Type: application/json" \
  -d '{"email":"new@a.com"}' http://localhost:3000/users/1
```

## 6. Walkthrough

- `req.method` — the HTTP verb as a string (`"GET"`, `"POST"`, etc.).
- `req.url.match(...)` — extracts `id` from paths like `/users/42`.
- `GET` branch — looks up `users[id]`, returns `404` if missing.
- `POST /users` — creates a new record; replies `201 Created` (not `200`).
- `PUT` branch — **replaces** the whole object: `{ id: Number(id), ...data }` discards anything not in `data`.
- `PATCH` branch — **merges** into existing: `{ ...users[id], ...data }` preserves fields not in `data`.
- `DELETE` branch — removes the key, returns `204 No Content` (success, nothing to send back).
- `405 Method Not Allowed` — polite rejection for verbs we didn't handle.

## 7. Gotchas & takeaways

> `PUT` is destructive. If you `PUT /users/42` with only `{"name":"Bob"}`, the server should erase every field that isn't `name`. Many developers accidentally implement `PUT` with merge semantics — that's `PATCH` behaviour.

> HTML forms only support `GET` and `POST`. To use `PUT`, `PATCH`, or `DELETE` from a browser form you need JavaScript (`fetch`) or a framework workaround.

- `GET` reads, `POST` creates, `PUT` replaces, `PATCH` merges, `DELETE` removes.
- `HEAD` = `GET` without the body — useful for size checks or existence checks.
- `OPTIONS` is sent automatically by browsers before cross-origin requests (CORS preflight).
- Respond `201 Created` to `POST` that creates something; `204 No Content` to `DELETE`.
- Use the method correctly — caches and proxies rely on `GET` being read-only.
