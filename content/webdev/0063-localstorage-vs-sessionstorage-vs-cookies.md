---
card: webdev
gi: 63
slug: localstorage-vs-sessionstorage-vs-cookies
title: localStorage vs sessionStorage vs cookies
---

## 1. What it is

Browsers provide three main places to persist data client-side:

- **`localStorage`** — key-value string storage, tied to the origin, persists indefinitely until cleared by code or the user.
- **`sessionStorage`** — same API as `localStorage`, but scoped to the browser tab and cleared when that tab closes.
- **Cookies** — key-value pairs sent to the server automatically on every request, with server-controlled expiry and security attributes.

All three live in the browser, but they differ in scope, lifetime, and who can read them.

## 2. Why & when

| | localStorage | sessionStorage | Cookies |
|-|-------------|---------------|---------|
| Capacity | ~5–10 MB | ~5–10 MB | ~4 KB |
| Lifetime | Until cleared | Until tab closes | Server-set (Max-Age) |
| Sent to server? | Never | Never | Always (automatically) |
| JS accessible? | Yes | Yes | Yes (unless HttpOnly) |
| Tab isolation? | No (shared across tabs) | Yes (per tab) | No (shared across tabs) |
| Server control? | No | No | Yes (attributes, expiry) |

Use **cookies** for authentication tokens and anything the server needs to see.

Use **localStorage** for client-only data that should persist across tabs and sessions (e.g. user preferences, cached API data, draft form content).

Use **sessionStorage** for per-tab state that should be isolated and temporary (e.g. multi-step wizard data, tab-specific UI state).

## 3. Core concept

Analogy: three types of storage in a physical store.
- **Cookies** = till receipt in your pocket. The cashier printed it; every register you visit will see it.
- **localStorage** = a personal locker with your name on it. Anyone in that shop (any tab from the same origin) can open it; it's there next week.
- **sessionStorage** = a tray on the counter for your current visit. You leave (close the tab), the tray is cleared.

Web Storage API (`localStorage` and `sessionStorage`) stores only strings:
```js
localStorage.setItem("theme", "dark");
const theme = localStorage.getItem("theme"); // "dark"
localStorage.removeItem("theme");
localStorage.clear(); // clear everything
```

For objects, serialize to JSON:
```js
localStorage.setItem("user", JSON.stringify({ name: "Alice", role: "admin" }));
const user = JSON.parse(localStorage.getItem("user"));
```

Cookies are set by the server via `Set-Cookie` or by JavaScript via `document.cookie` (unless `HttpOnly`):
```js
document.cookie = "theme=dark; SameSite=Lax";
```

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of localStorage, sessionStorage, and cookies: capacity, lifetime, and server visibility">

  <!-- Headers -->
  <text x="115" y="25" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">localStorage</text>
  <text x="340" y="25" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">sessionStorage</text>
  <text x="565" y="25" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Cookies</text>

  <!-- localStorage box -->
  <rect x="30" y="35" width="170" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="60" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">~5–10 MB</text>
  <text x="115" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Until cleared</text>
  <text x="115" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">All tabs (same origin)</text>
  <text x="115" y="120" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Never sent to server</text>
  <text x="115" y="140" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JS readable</text>
  <text x="115" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Use: prefs, cache</text>
  <text x="115" y="178" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">client-only data</text>

  <!-- sessionStorage box -->
  <rect x="255" y="35" width="170" height="160" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="60" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">~5–10 MB</text>
  <text x="340" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Until tab closes</text>
  <text x="340" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">This tab only</text>
  <text x="340" y="120" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Never sent to server</text>
  <text x="340" y="140" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JS readable</text>
  <text x="340" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Use: wizard steps,</text>
  <text x="340" y="178" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">tab-specific UI</text>

  <!-- Cookies box -->
  <rect x="480" y="35" width="170" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="565" y="60" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">~4 KB</text>
  <text x="565" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Max-Age / Expires</text>
  <text x="565" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">All tabs (same origin)</text>
  <text x="565" y="120" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Sent automatically</text>
  <text x="565" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">HttpOnly blocks JS</text>
  <text x="565" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Use: auth tokens,</text>
  <text x="565" y="178" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">server-read data</text>
</svg>

Cookies go to the server; Web Storage stays client-side. Capacity and lifetime diverge significantly.

## 5. Runnable example

```html
<!-- storage-demo.html — open directly in any browser, no server needed -->
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Storage demo</title></head>
<body>
<h2>Client Storage Comparison</h2>
<button onclick="writeAll()">Write to all three</button>
<button onclick="readAll()">Read all three</button>
<button onclick="clearAll()">Clear Web Storage</button>
<pre id="out" style="background:#1c2430;color:#e6edf3;padding:1em;margin-top:1em"></pre>

<script>
function log(msg) { document.getElementById("out").textContent += msg + "\n"; }
function clearLog() { document.getElementById("out").textContent = ""; }

function writeAll() {
  clearLog();
  localStorage.setItem("lsKey", "I persist across tabs & sessions");
  sessionStorage.setItem("ssKey", "I die when this tab closes");
  document.cookie = "cKey=I travel to the server; SameSite=Lax; Path=/";
  log("Written:");
  log("  localStorage.lsKey = " + localStorage.getItem("lsKey"));
  log("  sessionStorage.ssKey = " + sessionStorage.getItem("ssKey"));
  log("  document.cookie = " + document.cookie);
}

function readAll() {
  clearLog();
  log("Read:");
  log("  localStorage.lsKey = " + (localStorage.getItem("lsKey") || "(not set)"));
  log("  sessionStorage.ssKey = " + (sessionStorage.getItem("ssKey") || "(not set or tab was closed)"));
  log("  document.cookie = " + (document.cookie || "(none)"));
  log("");
  log("Open a NEW tab and read again:");
  log("  localStorage.lsKey will be there (shared).");
  log("  sessionStorage.ssKey will be EMPTY (tab-isolated).");
}

function clearAll() {
  localStorage.clear();
  sessionStorage.clear();
  document.cookie = "cKey=; Max-Age=0; Path=/";
  clearLog();
  log("Web Storage cleared. Cookie deleted.");
}
</script>
</body>
</html>
```

**How to run:** save as `storage-demo.html`, open in a browser. Click "Write to all three" then open a new tab to the same file and click "Read" — notice the difference.

## 6. Walkthrough

- `localStorage.setItem("lsKey", ...)` persists the value to disk. Opening a second tab to the same origin and calling `getItem` returns the same value — shared storage.
- `sessionStorage.setItem("ssKey", ...)` writes only to this tab's isolated storage. The new tab sees nothing for `ssKey`.
- `document.cookie = "cKey=..."` sets a cookie readable by JS (no `HttpOnly`). In a real app, auth cookies set by the server would not appear here.
- `Max-Age=0` on the cookie delete line is the standard way to remove a cookie from JavaScript.
- Notice: neither `localStorage` nor `sessionStorage` is ever sent to the server automatically — unlike cookies. That's why they can hold megabytes without network overhead.

## 7. Gotchas & takeaways

> **Never store auth tokens in `localStorage`.** It's accessible to any JavaScript on the page — including injected XSS payloads. Use `HttpOnly` cookies for authentication tokens.

> **`sessionStorage` is not shared between tabs.** A user opening your checkout in two tabs will have two separate `sessionStorage` states. Design flows accordingly.

> **Storage limits vary by browser** (5 MB is common but not universal). For structured data or large blobs, use IndexedDB instead (next tutorial).

- Cookies: small, server-visible, server-controlled — right for auth/session.
- localStorage: large, client-only, cross-tab shared, permanent until cleared — right for non-sensitive persistent prefs.
- sessionStorage: large, client-only, tab-isolated, auto-cleared on close — right for temporary in-progress state.
- Web Storage (`localStorage`/`sessionStorage`) stores only strings — serialize objects with `JSON.stringify` / `JSON.parse`.
- Check DevTools → Application → Storage to inspect and manually clear all three storage types.
