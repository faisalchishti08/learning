---
card: webdev
gi: 60
slug: cookie-attributes-httponly-secure-samesite-domain-path-max-a
title: Cookie attributes (HttpOnly, Secure, SameSite, Domain, Path, Max-Age)
---

## 1. What it is

Cookie **attributes** are optional directives appended to `Set-Cookie` that control three things:
1. **Where** the cookie is sent (Domain, Path).
2. **When** it expires (Max-Age, Expires).
3. **How safely** it travels and who can read it (Secure, HttpOnly, SameSite).

```
Set-Cookie: token=xyz; Max-Age=3600; Domain=example.com; Path=/; Secure; HttpOnly; SameSite=Strict
```

Each attribute is a separate guard. Understanding all of them is required to set cookies that don't leak user data or enable attacks.

## 2. Why & when

Default cookies (no attributes) are insecure by design:
- Sent over HTTP — eavesdropping risk.
- Readable by `document.cookie` — XSS risk.
- Sent on cross-site requests — CSRF risk.
- Sent to all subdomains — oversharing risk.

The attributes exist to tighten each of these. For any authentication or session cookie, all three security attributes (`Secure`, `HttpOnly`, `SameSite=Strict` or `Lax`) should be set.

## 3. Core concept

Think of a cookie like a hotel keycard:
- **Domain/Path** — which doors it opens (only floors 3–5, only the gym).
- **Max-Age** — when it expires (check-out time).
- **Secure** — keycard only works on the secure (RFID) locks, not old mechanical ones.
- **HttpOnly** — only the lock reader can use it; guests can't clone it.
- **SameSite** — keycard only works when you physically walk from your room, not when a stranger slides it under the door.

| Attribute | Type | Effect |
|-----------|------|--------|
| `Max-Age=N` | Lifetime | Expire after N seconds from now |
| `Expires=date` | Lifetime | Expire at absolute date/time |
| `Domain=example.com` | Scope | Sent to this domain and all subdomains |
| `Path=/admin` | Scope | Sent only when URL starts with `/admin` |
| `Secure` | Security | HTTPS only |
| `HttpOnly` | Security | Hidden from `document.cookie` |
| `SameSite=Strict/Lax/None` | Security | Cross-site sending rules |

**SameSite** values explained:
- `Strict` — cookie only sent when navigating within the same site. Safest; breaks some OAuth flows.
- `Lax` — cookie sent on top-level navigations (clicking a link) but not on embedded cross-site requests (image loads, iframes). Default in modern browsers.
- `None` — cookie sent on all cross-site requests. Must also set `Secure`. Required for third-party cookies (embeds, ad tech).

## 4. Diagram

<svg viewBox="0 0 680 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cookie attribute decision tree showing Secure blocks HTTP, HttpOnly blocks JS, SameSite blocks cross-site">
  <defs>
    <marker id="arr60y" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr60n" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>

  <!-- Cookie box -->
  <rect x="260" y="10" width="160" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="35" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Cookie set</text>

  <!-- Secure check -->
  <rect x="250" y="70" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="95" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Secure attr?</text>
  <line x1="340" y1="50" x2="340" y2="68" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr60y)"/>

  <text x="200" y="100" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">No → HTTP sends it</text>
  <text x="460" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Yes → HTTPS only</text>

  <!-- HttpOnly check -->
  <rect x="250" y="140" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="165" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">HttpOnly attr?</text>
  <line x1="340" y1="110" x2="340" y2="138" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr60y)"/>

  <text x="200" y="168" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">No → JS can read</text>
  <text x="460" y="168" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Yes → JS blocked</text>

  <!-- SameSite check -->
  <rect x="230" y="210" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="235" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">SameSite=?</text>
  <line x1="340" y1="180" x2="340" y2="208" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr60y)"/>

  <text x="100" y="258" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Strict: same-site only</text>
  <text x="340" y="258" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Lax: top-level nav ok</text>
  <text x="560" y="258" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">None: all cross-site</text>
</svg>

Each attribute adds one layer of protection. Stack all three security attributes for auth cookies.

## 5. Runnable example

```js
// server.js — Node.js, no installs.
const http = require("http");

http.createServer((req, res) => {
  if (req.url === "/set-cookies") {
    res.setHeader("Set-Cookie", [
      // Auth session: maximum security
      "sessionId=abc123; Max-Age=3600; Path=/; Secure; HttpOnly; SameSite=Lax",
      // User preference: accessible to JS, lasts a year, whole site
      "theme=dark; Max-Age=31536000; Path=/; SameSite=Lax",
      // Admin-only path: only sent to /admin URLs
      "adminToken=xyz; Max-Age=900; Path=/admin; Secure; HttpOnly; SameSite=Strict",
    ]);
    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(`
      <p>Cookies set! Check DevTools → Application → Cookies.</p>
      <script>
        // Can read "theme" (no HttpOnly), cannot read "sessionId" or "adminToken"
        document.write("<p>JS sees: " + document.cookie + "</p>");
      </script>
    `);
  } else {
    res.writeHead(404);
    res.end("try /set-cookies");
  }
}).listen(3000, () => console.log("http://localhost:3000/set-cookies"));
```

**How to run:** `node server.js`, open `http://localhost:3000/set-cookies`. Note that JS can only read `theme=dark`, not the HttpOnly cookies.

## 6. Walkthrough

- `sessionId` has `Secure; HttpOnly; SameSite=Lax` — strongest setting for auth: HTTPS-only, invisible to JavaScript (can't be stolen by XSS), not sent on embedded cross-site sub-requests (reduces CSRF exposure).
- `theme` has no `HttpOnly` because the JavaScript needs to read it to apply the dark mode class. No security risk for a theme value.
- `adminToken` has `Path=/admin` — the browser only includes it in requests to URLs starting with `/admin`. Requests to `/dashboard` don't carry it, limiting exposure.
- `Max-Age=31536000` on `theme` (one year) makes it a persistent cookie. `Max-Age=900` on `adminToken` (15 min) means admin actions require re-auth more frequently.
- In the browser console, `document.cookie` only shows `theme=dark` — proof that `HttpOnly` hides the sensitive cookies from JavaScript.

## 7. Gotchas & takeaways

> **`Secure` is not optional for auth cookies.** Without it, the cookie travels in plaintext over HTTP — any network observer can steal the session. Always pair auth cookies with HTTPS + `Secure`.

> **`SameSite=None` requires `Secure`.** Modern browsers reject `SameSite=None` cookies sent without `Secure`. If you build a third-party embed, you must use HTTPS.

> **Domain scoping is broader than you might expect.** `Domain=example.com` includes `api.example.com`, `admin.example.com`, etc. Omitting `Domain` restricts the cookie to the exact origin server.

- `HttpOnly` is the primary XSS mitigation for cookies — attackers' injected scripts can't steal what they can't read.
- `SameSite=Strict` is the strongest CSRF protection but breaks login flows that arrive from external links (e.g., email links). `Lax` is the common balance.
- Omit `Max-Age` and `Expires` for a session cookie — the browser deletes it when the browser closes.
- `Path=/` is the safe default; narrow it (`Path=/admin`) for sensitive tokens.
- Inspect all cookies in DevTools → Application → Cookies before shipping — check that auth cookies have all three security flags.
