---
card: webdev
gi: 35
slug: safe-vs-idempotent-methods
title: Safe vs idempotent methods
---

## 1. What it is

HTTP methods carry two formal properties that describe their side-effect behaviour:

- **Safe** — the request has no observable effect on server state. It only reads.
- **Idempotent** — sending the same request multiple times produces the same end state as sending it once. Repeating it is harmless.

Every safe method is also idempotent, but not every idempotent method is safe.

| Method | Safe? | Idempotent? |
|--------|-------|-------------|
| GET | ✅ | ✅ |
| HEAD | ✅ | ✅ |
| OPTIONS | ✅ | ✅ |
| PUT | ❌ | ✅ |
| DELETE | ❌ | ✅ |
| POST | ❌ | ❌ |
| PATCH | ❌ | ❌ (usually) |

## 2. Why & when

These properties let HTTP infrastructure make smart, automatic decisions:

- **Caches** may store and replay `GET`/`HEAD` responses because safe methods read-only.
- **Browsers** warn before resubmitting a `POST` form because `POST` is not idempotent — doing it twice creates two records.
- **Retry logic** in HTTP clients (load balancers, SDKs) safely retries idempotent requests on network failure; they never auto-retry `POST` because that could double-charge a payment or create duplicate orders.
- **Link prefetching** works only on `GET` — browsers wouldn't prefetch a `DELETE` URL.

## 3. Core concept

Think of a vending machine. **Safe**: peeking through the glass at the snacks (no coins, no change). **Idempotent**: pressing the "cancel" button repeatedly — pressing it ten times after cancelling produces the same result as pressing it once (the transaction is still cancelled). **Neither**: inserting a coin and selecting a snack — each time you do it, you get one more snack and lose one more coin.

**Safe** means the server state is unchanged. Reading a document is safe; updating a counter is not (even if you call it "just a `GET`").

**Idempotent** means the *end state* is the same, not that the response is identical. `DELETE /users/42` the first time returns `200` (deleted); the second time might return `404` (already gone). Different responses, but the end state — user 42 does not exist — is the same both times. That's still idempotent.

**Non-idempotent** means each request may produce new state. `POST /orders` creates one order per call.

`PATCH` is technically defined as non-idempotent because a `PATCH` like `{"increment_views": true}` adds 1 each time. A `PATCH` that sets an absolute value (`{"status": "active"}`) is effectively idempotent in practice, but the spec doesn't assume it.

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Venn diagram showing safe subset inside idempotent set and POST outside both">
  <!-- Background -->
  <rect width="660" height="280" fill="#0d1117"/>

  <!-- Idempotent outer ellipse -->
  <ellipse cx="310" cy="150" rx="260" ry="110" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="72" y="152" fill="#79c0ff" font-size="12" font-family="sans-serif">Idempotent</text>

  <!-- Safe inner ellipse -->
  <ellipse cx="370" cy="150" rx="140" ry="78" fill="#162420" stroke="#6db33f" stroke-width="1.5"/>
  <text x="322" y="90" fill="#6db33f" font-size="12" font-family="sans-serif">Safe</text>

  <!-- Methods in safe zone -->
  <text x="350" y="130" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace">GET</text>
  <text x="350" y="152" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace">HEAD</text>
  <text x="350" y="174" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace">OPTIONS</text>

  <!-- Methods in idempotent-only zone -->
  <text x="152" y="142" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="monospace">PUT</text>
  <text x="152" y="164" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="monospace">DELETE</text>

  <!-- POST outside both -->
  <rect x="530" y="100" width="100" height="60" rx="8" fill="#2d1a1a" stroke="#f85149" stroke-width="1.5"/>
  <text x="580" y="126" fill="#f85149" font-size="13" text-anchor="middle" font-family="monospace">POST</text>
  <text x="580" y="148" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">PATCH*</text>

  <!-- Legend -->
  <text x="40" y="262" fill="#8b949e" font-size="11" font-family="sans-serif">* PATCH is technically non-idempotent; safe to treat as idempotent only when it sets absolute values</text>
</svg>

Safe ⊂ idempotent. POST and PATCH live outside both circles.

## 5. Runnable example

```js
// save as idempotent-demo.js — needs Node.js, no installs
const http = require("http");

let counter = 0;
let resource = { name: "Alice" };

const server = http.createServer((req, res) => {
  res.setHeader("Content-Type", "application/json");

  // GET — safe + idempotent: reading never changes state
  if (req.method === "GET" && req.url === "/resource") {
    return res.end(JSON.stringify({ ...resource, counter }));
  }

  // PUT — idempotent: calling twice leaves same state
  if (req.method === "PUT" && req.url === "/resource") {
    resource = { name: "Bob" }; // always ends up as Bob
    res.writeHead(200);
    return res.end(JSON.stringify(resource));
  }

  // POST — NOT idempotent: each call increments counter
  if (req.method === "POST" && req.url === "/increment") {
    counter++;
    res.writeHead(200);
    return res.end(JSON.stringify({ counter }));
  }
});

server.listen(3000, async () => {
  const get = (path) =>
    new Promise((resolve) => {
      http.get("http://localhost:3000" + path, (res) => {
        let b = "";
        res.on("data", (c) => (b += c));
        res.on("end", () => resolve(JSON.parse(b)));
      });
    });

  const request = (method, path) =>
    new Promise((resolve) => {
      const r = http.request({ hostname: "localhost", port: 3000, path, method }, (res) => {
        let b = "";
        res.on("data", (c) => (b += c));
        res.on("end", () => resolve(JSON.parse(b)));
      });
      r.end();
    });

  // PUT is idempotent — run 3x, state same as 1x
  await request("PUT", "/resource");
  await request("PUT", "/resource");
  await request("PUT", "/resource");
  const afterPut = await get("/resource");
  console.log("After 3x PUT:", afterPut); // name always "Bob", counter still 0

  // POST is NOT idempotent — each call adds 1
  await request("POST", "/increment");
  await request("POST", "/increment");
  await request("POST", "/increment");
  const afterPost = await get("/resource");
  console.log("After 3x POST:", afterPost); // counter is 3

  server.close();
});
```

**How to run:** `node idempotent-demo.js` — built-in `http`, no npm.

## 6. Walkthrough

- `PUT /resource` always sets `resource = { name: "Bob" }`. Call it once or a hundred times — the result is identical. Idempotent.
- `POST /increment` adds 1 to `counter` each call. Three calls → counter is 3. Not idempotent.
- `GET /resource` only reads; `counter` and `resource` are untouched. Safe.
- `afterPut` shows `counter: 0` — three `PUT`s left counter unchanged because `PUT` didn't touch it, proving safe `GET` + idempotent `PUT` left the same final state.
- `afterPost` shows `counter: 3` — each `POST` created new state, demonstrating non-idempotency.

## 7. Gotchas & takeaways

> Idempotent means the **end state** is the same, not the **HTTP response**. `DELETE /users/42` returns `200` first time and `404` second time — different responses, same end state. That's still idempotent.

> Never trigger side effects (sending emails, charging cards, creating records) inside a `GET` handler. Bots, prefetchers, and link checkers call `GET` freely, assuming it's safe.

- **Safe** = read-only, no server state change. `GET`, `HEAD`, `OPTIONS`.
- **Idempotent** = repeat-safe, same end state. All safe methods plus `PUT` and `DELETE`.
- `POST` is neither — each call may produce a new side effect.
- Retry logic in HTTP clients uses idempotency: safe to retry `GET`, unsafe to retry `POST`.
- `PATCH` is formally non-idempotent; design your patches to be idempotent (set values, don't increment them) when retry safety matters.
