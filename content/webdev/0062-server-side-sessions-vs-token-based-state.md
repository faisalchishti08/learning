---
card: webdev
gi: 62
slug: server-side-sessions-vs-token-based-state
title: Server-side sessions vs token-based state
---

## 1. What it is

HTTP is stateless — each request is isolated. To track users across requests (logged-in state, cart contents, permissions), servers use one of two strategies:

- **Server-side sessions** — the server stores state in memory or a database, and gives the client an opaque ID (session ID). The client sends the ID on each request; the server looks up the actual data.
- **Token-based state (JWT / signed tokens)** — all state is encoded inside a token that's given to the client. The server verifies the token's signature on each request and reads the data directly from the token — no database lookup.

Both solve the same problem; they differ in *where state lives*.

## 2. Why & when

| | Server-side sessions | Token-based (JWT) |
|-|---------------------|-------------------|
| State lives in | Server memory / DB | Signed token on client |
| Revocable? | Yes — delete the session | Hard — must use denylist or short TTL |
| Server-to-server? | Shared session DB needed | Token travels across services |
| Horizontal scaling | Needs sticky sessions or shared store | Stateless — any server can verify |
| Data size | Cookie is tiny (opaque ID) | Token grows with payload |
| Invalidation | Instant | Delayed until expiry |

Use **server-side sessions** when:
- You need instant revocation (force-logout, account ban).
- Storing large amounts of user state.
- Traditional monolithic application.

Use **token-based (JWT)** when:
- Microservices or APIs where multiple servers need to verify identity.
- Stateless architecture where no shared session store is desired.
- Third-party API clients (mobile apps, SPAs).

## 3. Core concept

Analogy: **coat check vs name badge**.

Server-side session = **coat check**. You hand your coat to the attendant, get a ticket (session ID). On return, you show the ticket, they retrieve your coat from storage. The storage holds the real data; the ticket is useless without it.

Token-based = **name badge**. Your employer prints your name and role directly on the badge, with a tamper-proof hologram (cryptographic signature). Any security desk can verify it without calling headquarters — the badge *is* the data.

**JWT (JSON Web Token) anatomy:**
```
header.payload.signature

eyJhbGciOiJIUzI1NiJ9      ← header: algorithm
.eyJ1c2VyIjoiYWxpY2UifQ== ← payload: {user:"alice", role:"admin", exp:...}
.SflKxwRJSMeKKF2QT4fwpMeJ  ← signature: HMAC of header+payload with secret
```

The server never looks up a session — it re-computes the signature from the secret key. If the signature matches, the payload is trusted.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Left: server-side session with DB lookup. Right: JWT with signature verification only.">
  <defs>
    <marker id="arr62" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr62b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Left: session -->
  <text x="165" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server-side Session</text>
  <rect x="20" y="35" width="100" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="150" y="35" width="100" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="200" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>
  <text x="200" y="69" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">looks up DB</text>
  <rect x="160" y="100" width="80" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="200" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Session DB</text>
  <text x="200" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">id→{user,role}</text>

  <line x1="122" y1="55" x2="148" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr62)"/>
  <text x="135" y="48" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">sid=abc</text>
  <line x1="200" y1="75" x2="200" y2="98" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr62)"/>

  <!-- Right: JWT -->
  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Token (JWT)</text>
  <rect x="370" y="35" width="100" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="420" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="500" y="35" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>
  <text x="565" y="69" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">verify sig only</text>

  <line x1="472" y1="55" x2="498" y2="55" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr62b)"/>
  <text x="485" y="48" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">JWT token</text>

  <rect x="470" y="100" width="130" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="535" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">No DB needed</text>
  <text x="535" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(data in token)</text>

  <line x1="565" y1="75" x2="535" y2="98" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,2"/>

  <!-- Divider -->
  <line x1="340" y1="10" x2="340" y2="155" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
</svg>

Sessions require a DB round-trip per request; JWTs are self-contained and verified in-memory.

## 5. Runnable example

```js
// server.js — Node.js, no installs.
// Demonstrates both patterns side by side.
const http = require("http");
const crypto = require("crypto");

// ---- SERVER-SIDE SESSION ----
const sessions = {};
function createSession(user) {
  const id = crypto.randomBytes(16).toString("hex");
  sessions[id] = { user, role: "member", createdAt: Date.now() };
  return id;
}
function lookupSession(id) { return sessions[id] || null; }

// ---- JWT-LITE (HMAC-SHA256, no library) ----
const JWT_SECRET = "my-super-secret-key-change-in-prod";
function b64url(s) { return Buffer.from(s).toString("base64url"); }
function createJWT(payload) {
  const header = b64url(JSON.stringify({ alg: "HS256" }));
  const body = b64url(JSON.stringify(payload));
  const sig = crypto.createHmac("sha256", JWT_SECRET)
    .update(`${header}.${body}`).digest("base64url");
  return `${header}.${body}.${sig}`;
}
function verifyJWT(token) {
  const [h, b, sig] = token.split(".");
  const expected = crypto.createHmac("sha256", JWT_SECRET)
    .update(`${h}.${b}`).digest("base64url");
  if (sig !== expected) return null;
  return JSON.parse(Buffer.from(b, "base64url").toString());
}

http.createServer((req, res) => {
  res.setHeader("Content-Type", "text/plain");

  if (req.url === "/session-login") {
    const sid = createSession("alice");
    res.setHeader("Set-Cookie", `sid=${sid}; HttpOnly; Path=/`);
    res.end(`Session created. ID stored server-side.\nCookie: sid=${sid}`);

  } else if (req.url === "/session-whoami") {
    const match = (req.headers.cookie || "").match(/sid=([^;]+)/);
    const sess = match && lookupSession(match[1]);
    res.end(sess ? `Session user: ${sess.user} (role: ${sess.role})` : "No session");

  } else if (req.url === "/jwt-login") {
    const token = createJWT({ user: "alice", role: "member", exp: Date.now() + 3600000 });
    res.end(`JWT created:\n${token}\n\nPaste to /jwt-whoami?token=<jwt>`);

  } else if (req.url.startsWith("/jwt-whoami")) {
    const token = new URL(req.url, "http://x").searchParams.get("token");
    const payload = token && verifyJWT(token);
    res.end(payload ? `JWT user: ${payload.user} (role: ${payload.role})` : "Invalid token");

  } else {
    res.end("try /session-login, /session-whoami, /jwt-login");
  }
}).listen(3000, () => console.log("http://localhost:3000"));
```

**How to run:** `node server.js`. Hit `/session-login` then `/session-whoami`. Also try `/jwt-login`, copy the token, and call `/jwt-whoami?token=<paste>`.

## 6. Walkthrough

- `createSession` stores `{ user, role }` in a server-side `sessions` object and returns only an opaque random hex ID to the client — nothing sensitive ever leaves the server.
- `lookupSession` uses the ID to retrieve the data — one in-memory lookup (real apps use Redis or a DB).
- `createJWT` builds a minimal JWT: base64url-encode header, base64url-encode payload, HMAC-sign both together. The secret never leaves the server.
- `verifyJWT` re-computes the signature and compares with `===`. If equal, the payload is trusted. No DB needed — all state is in the token.
- Notice the JWT approach exposes `{ user, role }` to anyone who base64-decodes the token (it's not encrypted — just signed). Don't put secrets in JWT payloads.

## 7. Gotchas & takeaways

> **JWTs cannot be instantly revoked.** If you issue a JWT valid for 1 hour and a user logs out (or is banned), that token is still valid until expiry unless you maintain a server-side denylist — at which point you've reintroduced server state anyway.

> **JWT is not encryption.** The payload is merely base64-encoded — readable by anyone. Use short expiry and put no sensitive fields (passwords, SSNs) in the payload.

- Server-side sessions: instant revocation, server-side storage required, simple to implement.
- JWT: stateless, scales horizontally, but hard to revoke — use short `exp` (15–60 min) + refresh tokens.
- For most traditional web apps, sessions are simpler and safer. JWT shines in API-driven microservice architectures.
- Store JWTs in `HttpOnly` cookies (not `localStorage`) to prevent XSS theft.
- A "refresh token" (long-lived, stored server-side) issues new short-lived JWTs — combines the best of both patterns.
