---
card: webdev
gi: 61
slug: session-vs-persistent-cookies
title: Session vs persistent cookies
---

## 1. What it is

Cookies come in two lifetime flavors:

- **Session cookies** — no `Max-Age` or `Expires` attribute. The browser deletes them when it closes (end of the "session"). They live only in memory.
- **Persistent cookies** — have a `Max-Age` (seconds from now) or `Expires` (absolute date). The browser writes them to disk and they survive browser restarts until their expiry time.

```
Set-Cookie: sessionId=abc; HttpOnly; Path=/           ← session cookie
Set-Cookie: rememberMe=tok; Max-Age=2592000; Path=/   ← persistent (30 days)
```

The distinction controls how long a user stays logged in or has their preferences remembered.

## 2. Why & when

Choosing between session and persistent is a **security vs convenience** trade-off:

| | Session cookie | Persistent cookie |
|-|---------------|------------------|
| Lives until | Browser closes | `Max-Age` / `Expires` expires |
| Survives restart | No | Yes |
| Risk if device stolen | Lower (auto-cleared) | Higher (token on disk) |
| User experience | Must re-login every session | "Remember me" works |

Use session cookies when:
- High-security contexts (banking, admin panels).
- You never want credentials to outlive the browser session.

Use persistent cookies when:
- Users expect to stay logged in across browser restarts ("Remember me").
- Storing non-sensitive preferences (theme, language) long-term.

## 3. Core concept

Analogy: a temporary visitor badge vs an annual employee ID. The visitor badge is collected at the end of the day (session cookie). The employee ID is kept until it expires (persistent cookie).

The difference is entirely about the `Max-Age` or `Expires` attribute:

```
# Session cookie (no expiry attribute)
Set-Cookie: sid=abc123; HttpOnly; Secure; SameSite=Lax

# Persistent cookie (Max-Age = 30 days)
Set-Cookie: rememberToken=xyz; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax

# Persistent cookie (Expires = specific date)
Set-Cookie: pref=dark; Expires=Fri, 31 Dec 2026 23:59:59 GMT
```

**Browser behaviour nuance:** "session" depends on the browser. Some browsers (Chrome with session restore, Firefox) restore the previous session on restart, which can re-activate session cookies — they persist as long as the browser "session" concept persists, which varies. Treat session cookies as "probably cleared on browser close," not "guaranteed."

Setting `Max-Age=0` or `Expires` to a past date is the server's way to delete a cookie:
```
Set-Cookie: sid=; Max-Age=0; Path=/
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Timeline showing session cookie dying on browser close vs persistent cookie surviving restarts">
  <defs>
    <marker id="arr61" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>

  <!-- Timeline axis -->
  <line x1="40" y1="100" x2="620" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr61)"/>
  <text x="330" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">time →</text>

  <!-- Login point -->
  <line x1="80" y1="90" x2="80" y2="110" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="80" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Login</text>

  <!-- Browser close -->
  <line x1="300" y1="90" x2="300" y2="110" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="80" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Browser close</text>

  <!-- Reopen -->
  <line x1="360" y1="90" x2="360" y2="110" stroke="#79c0ff" stroke-width="2"/>
  <text x="360" y="80" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Reopen</text>

  <!-- Persistent cookie bar -->
  <rect x="80" y="108" width="440" height="16" rx="4" fill="#6db33f" opacity="0.7"/>
  <text x="300" y="121" fill="#0d1117" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">persistent cookie (survives close → reopen)</text>

  <!-- Session cookie bar -->
  <rect x="80" y="130" width="218" height="16" rx="4" fill="#79c0ff" opacity="0.7"/>
  <text x="190" y="143" fill="#0d1117" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">session cookie (deleted on close)</text>

  <!-- Max-Age end marker -->
  <line x1="520" y1="90" x2="520" y2="125" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="520" y="80" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Max-Age expires</text>
</svg>

Session cookie dies when the browser closes; persistent cookie survives until its `Max-Age` runs out.

## 5. Runnable example

```js
// server.js — Node.js, no installs.
const http = require("http");

http.createServer((req, res) => {
  if (req.url === "/login-session") {
    // No Max-Age / Expires → session cookie
    res.setHeader("Set-Cookie", "authSid=sessToken123; HttpOnly; Path=/; SameSite=Lax");
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Session cookie set. Close the browser tab and re-open — gone.");

  } else if (req.url === "/login-persistent") {
    // Max-Age = 30 days → persistent cookie
    res.setHeader("Set-Cookie",
      "authPersist=permToken456; Max-Age=2592000; HttpOnly; Path=/; SameSite=Lax");
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Persistent cookie set (30 days). Survives browser restart.");

  } else if (req.url === "/logout") {
    // Delete both by setting Max-Age=0
    res.setHeader("Set-Cookie", [
      "authSid=; Max-Age=0; Path=/",
      "authPersist=; Max-Age=0; Path=/"
    ]);
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Logged out — both cookies deleted.");

  } else if (req.url === "/whoami") {
    const cookies = req.headers.cookie || "(none)";
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Cookies the server sees:\n" + cookies);

  } else {
    res.writeHead(404);
    res.end("try /login-session, /login-persistent, /whoami, or /logout");
  }
}).listen(3000, () => console.log("http://localhost:3000"));
```

**How to run:** `node server.js`. Visit `/login-session`, then `/login-persistent`, then `/whoami` to see both. Restart the browser and hit `/whoami` again — only the persistent one remains.

## 6. Walkthrough

- `/login-session` sends `Set-Cookie` without `Max-Age` or `Expires`. Browser stores it in memory; it's gone when the browser (not tab) closes.
- `/login-persistent` adds `Max-Age=2592000` (2,592,000 seconds = 30 days). Browser writes to disk; survives restarts.
- `/logout` sends `Max-Age=0` for both cookies, which instructs the browser to delete them immediately — even if they're persistent. This is the standard logout mechanism.
- `/whoami` shows the `Cookie` header the server receives. After clearing, it shows `(none)`.
- Notice both cookies use `HttpOnly` and `SameSite=Lax` regardless of lifetime — security attributes are orthogonal to lifetime.

## 7. Gotchas & takeaways

> **`Max-Age` takes precedence over `Expires` when both are set.** `Max-Age` is relative to the current time (seconds); `Expires` is an absolute UTC datetime. Prefer `Max-Age` for simplicity and to avoid timezone bugs.

> **Session cookie ≠ session data.** A "session cookie" (no expiry) is just a naming convention for lifetime. The cookie might still contain a token that references server-side session data — the concepts are independent.

- Deleting a cookie: set `Max-Age=0` (or `Expires` in the past) with the same `Path` and `Domain` as the original.
- "Remember me" = persistent cookie with a long `Max-Age` + secure random token stored in the database.
- Never store session tokens in `localStorage` as a substitute for session cookies — localStorage survives indefinitely and is readable by any JavaScript on the page.
- Check cookie lifetimes in DevTools → Application → Cookies; the "Expires / Max-Age" column shows the exact expiry.
