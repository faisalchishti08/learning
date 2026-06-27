---
card: webdev
gi: 71
slug: credentialed-requests-withcredentials
title: Credentialed requests & withCredentials
---

## 1. What it is

A **credentialed request** is a cross-origin HTTP request that includes **cookies, HTTP authentication (Basic/Digest), or TLS client certificates**. By default, cross-origin requests are credential-free — `fetch` won't attach cookies or auth headers to them even if they exist in the browser for that domain.

To opt in, the client must set `credentials: "include"` in `fetch` (or `withCredentials = true` on `XMLHttpRequest`). The server must respond with `Access-Control-Allow-Credentials: true` **and** a specific (non-wildcard) `Access-Control-Allow-Origin`. If either side doesn't cooperate, the browser silently drops the response.

## 2. Why & when

Without this protection, any page on the internet could silently make authenticated requests to your bank, your company's intranet, or any site the user is logged into — and read the responses. The double opt-in (client + server) prevents that: the client controls whether to send credentials, and the server controls whether to accept credentialed cross-origin requests.

You need credentialed requests when:
- A SPA (e.g. `app.example.com`) calls an API (`api.example.com`) and the user's session cookie must travel with the request.
- A dashboard at one subdomain calls a data API at another and both subdomains share a cookie domain.
- Any cross-origin call that relies on the browser's cookie jar for authentication.

If the API uses `Authorization: Bearer <token>` set explicitly in JS, you don't need `withCredentials` — you're setting the header manually, not relying on the browser's cookie jar.

## 3. Core concept

Think of a hotel building with two wings (origins). Normally, a key card from Wing A only opens Wing A's rooms. A **credentialed request** is you walking into Wing B with your Wing A key card hoping it works. The building (browser) will only let you try if:
1. You (the JS code) explicitly say "use my key card" (`credentials: "include"`).
2. Wing B's management (the server) has registered your card as acceptable (`Access-Control-Allow-Credentials: true` + specific origin).

Both conditions must be true. Either party can veto.

**Client side:**

```js
// fetch API
fetch("https://api.example.com/profile", {
  credentials: "include",   // ← attach cookies, TLS certs, HTTP auth
});

// XMLHttpRequest equivalent
const xhr = new XMLHttpRequest();
xhr.open("GET", "https://api.example.com/profile");
xhr.withCredentials = true;  // ← same effect
xhr.send();
```

The `credentials` option has three values:
- `"omit"` — never send credentials (useful to override browser defaults in same-origin context).
- `"same-origin"` — send credentials only to the same origin. Default for `fetch`.
- `"include"` — always send credentials, even cross-origin.

**Server side (required response headers):**

```http
Access-Control-Allow-Origin: https://app.example.com  ← must be specific, not *
Access-Control-Allow-Credentials: true
```

If `Allow-Origin` is `*`, the browser ignores `Allow-Credentials: true` and blocks the response anyway.

**Cookie constraints:** Even with both headers correct, cookies must satisfy `SameSite` attribute rules. `SameSite=Strict` cookies never travel cross-site. `SameSite=None` is required for cross-site cookies — and `SameSite=None` requires `Secure` (HTTPS). So for credentialed cross-origin cookies:
- Cookie must be `SameSite=None; Secure`.
- Request must be over HTTPS.
- Server must echo `Allow-Credentials: true` and a specific origin.

## 4. Diagram

<svg viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Credentialed CORS flow showing both client and server must opt in">
  <defs>
    <marker id="arr71g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr71b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="arr71r" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- Browser -->
  <rect x="10" y="110" width="150" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="138" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Browser</text>
  <text x="85" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JS: fetch(url, {</text>
  <text x="85" y="169" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">  credentials: "include"</text>
  <text x="85" y="183" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">})</text>

  <!-- Server -->
  <rect x="520" y="110" width="150" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="138" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>
  <text x="595" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">api.example.com</text>

  <!-- Request arrow with cookie label -->
  <line x1="162" y1="143" x2="518" y2="143" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr71b)"/>
  <text x="340" y="134" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">GET /profile  Cookie: session=abc  Origin: app.example.com</text>

  <!-- Success response -->
  <line x1="518" y1="165" x2="162" y2="165" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr71g)"/>
  <text x="340" y="182" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">200 OK  Allow-Origin: app.example.com  Allow-Credentials: true</text>
  <text x="340" y="196" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">✓ JS can read response</text>

  <!-- Fail path -->
  <line x1="518" y1="225" x2="162" y2="225" stroke="#f85149" stroke-width="1.5" marker-end="url(#arr71r)" stroke-dasharray="4,3"/>
  <text x="340" y="244" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">200 OK  Allow-Origin: *  ← wildcard + credentials = BLOCKED</text>
  <text x="340" y="260" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">✗ Browser discards response, JS gets TypeError</text>

  <!-- Separator -->
  <line x1="100" y1="210" x2="580" y2="210" stroke="#8b949e" stroke-width="0.5" stroke-dasharray="3,3"/>
  <text x="640" y="200" fill="#8b949e" font-size="8" font-family="sans-serif">success</text>
  <text x="640" y="232" fill="#f85149" font-size="8" font-family="sans-serif">failure</text>
</svg>

`credentials: "include"` alone isn't enough — the server must echo the specific origin and set `Allow-Credentials: true`; a wildcard origin silently blocks the response.

## 5. Runnable example

```js
// cred-server.js — Node.js, no installs.
// A login endpoint that sets a session cookie, then a protected endpoint
// that reads it — shows the full credentialed CORS flow.
const http = require("http");
const sessions = new Map(); // simple in-memory session store

const ALLOWED_ORIGIN = "http://localhost:5500";

function corsHeaders(res, origin) {
  // Must be specific origin when Allow-Credentials is true
  if (origin === ALLOWED_ORIGIN) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  }
}

http.createServer((req, res) => {
  const origin = req.headers.origin || "";
  corsHeaders(res, origin);

  if (req.method === "OPTIONS") {
    res.writeHead(204); res.end(); return;
  }

  if (req.url === "/login" && req.method === "POST") {
    const sessionId = Math.random().toString(36).slice(2);
    sessions.set(sessionId, { user: "alice" });
    res.writeHead(200, {
      "Content-Type": "application/json",
      // SameSite=None;Secure required for cross-site (needs HTTPS in production)
      "Set-Cookie": `session=${sessionId}; HttpOnly; SameSite=None; Secure; Path=/`,
    });
    res.end(JSON.stringify({ ok: true, sessionId }));
    return;
  }

  if (req.url === "/profile" && req.method === "GET") {
    const cookie = req.headers.cookie || "";
    const match = cookie.match(/session=([^;]+)/);
    const session = match ? sessions.get(match[1]) : null;

    if (!session) {
      res.writeHead(401, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "Not authenticated" }));
      return;
    }
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ user: session.user }));
    return;
  }

  res.writeHead(404); res.end("Not found");
}).listen(8000, () => {
  console.log("API at http://localhost:8000");
  console.log("From http://localhost:5500 run:");
  console.log("  // 1. Login (sets cookie cross-origin)");
  console.log('  await fetch("http://localhost:8000/login", {');
  console.log('    method: "POST", credentials: "include"');
  console.log('  });');
  console.log("  // 2. Fetch profile — cookie travels automatically");
  console.log('  const r = await fetch("http://localhost:8000/profile", {');
  console.log('    credentials: "include"');
  console.log('  });');
  console.log('  console.log(await r.json()); // { user: "alice" }');
});
```

**How to run:** `node cred-server.js`. Serve a static HTML file from `http://localhost:5500` (e.g. VS Code Live Server), then paste the `fetch` calls into the browser console.

## 6. Walkthrough

- `corsHeaders` always echoes `origin` (the specific value) not `*`. This is required when `Allow-Credentials: true` — using `*` would cause the browser to block the response after receiving it.
- `"Set-Cookie": "... SameSite=None; Secure"` — for a cookie to travel cross-site with credentials, it must be `SameSite=None`. But `SameSite=None` requires `Secure` (HTTPS). In this localhost demo the `Secure` flag is technically incorrect (no TLS), but modern browsers may still accept it on `localhost` for testing purposes.
- `credentials: "include"` in the `fetch` call makes the browser attach all cookies for `localhost:8000` to the request, even though the page is on `localhost:5500`.
- The `/profile` handler reads `req.headers.cookie` — this is the cookie the browser attached because of `credentials: "include"`. Without that option, `req.headers.cookie` would be empty.
- `res.setHeader("Access-Control-Allow-Credentials", "true")` on the `/profile` response is what lets JS actually read the `200 OK` response body. Without it, the browser receives the data but discards it before handing it to JS.

## 7. Gotchas & takeaways

> **`credentials: "include"` without `Allow-Credentials: true` on the server silently discards the response.** JS gets a `TypeError: Failed to fetch` with no details — the same error as a network failure. The mismatch is invisible unless you check the Network tab in DevTools and look at the response headers.

> **`SameSite=None; Secure` is required for cross-site cookies.** Cookies without `SameSite=None` are blocked by modern browsers in cross-site requests even when `credentials: "include"` is set. HTTPS is mandatory in production for `SameSite=None`.

> **`withCredentials = true` on XHR is the older equivalent.** Same semantics, different API: `xhr.withCredentials = true` before `xhr.send()`. Same server-side requirements apply.

- Client opts in with `credentials: "include"` (or `xhr.withCredentials = true`).
- Server opts in with `Access-Control-Allow-Credentials: true` + a specific (non-`*`) origin.
- Both opt-ins required — one alone causes silent blocking.
- Session cookies must be `SameSite=None; Secure` to travel cross-site.
- `Authorization: Bearer` tokens set manually in JS headers don't need `withCredentials` — they're just headers, handled by `Allow-Headers`.
- Test credentialed flows with browser DevTools, not `curl` — `curl` doesn't enforce CORS.
