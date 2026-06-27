---
card: webdev
gi: 73
slug: jsonp-legacy-workaround
title: JSONP (legacy workaround)
---

## 1. What it is

**JSONP (JSON with Padding)** is a pre-CORS technique for loading cross-origin data using `<script>` tags. It exploits the fact that `<script src="...">` can fetch resources from any origin — no Same-Origin Policy restriction applies to script loads.

Instead of returning plain JSON, a JSONP-capable server wraps the data in a function call:

```json
// Normal JSON (blocked cross-origin by SOP)
{ "user": "alice", "score": 42 }
```

```js
// JSONP (loads fine as a <script>)
myCallback({ "user": "alice", "score": 42 })
```

The page defines `myCallback` before requesting the script; when the script executes, the function fires with the data. JSONP predates CORS (which was standardised in 2014) and is now considered a **legacy workaround**. Modern code should use `fetch` with proper CORS headers instead.

## 2. Why & when

JSONP was invented around 2005 to let web pages pull data from third-party APIs before browsers implemented CORS. The only cross-origin mechanism available then was script tags (and `<img>`, `<iframe>` — all more limited). Developers found that `<script>` was the cleanest way to smuggle JSON across origins.

You encounter JSONP today when:
- Maintaining legacy code that talks to an old API that only offers JSONP.
- Reading older tutorials or libraries (jQuery's `$.ajax({ dataType: "jsonp" })` was widely used).
- Understanding why old mashup sites from the 2000s worked.

**Do not use JSONP for new code.** It is slower (requires a `<script>` tag), harder to error-handle, and carries serious security risks. CORS is the correct solution for every cross-origin fetch in modern browsers.

## 3. Core concept

Think of JSONP as **calling a radio station to request a song**. You phone the station (your page defines a callback), request a track by name (the `?callback=myCallback` query param), and the DJ (the server) plays your song addressed to you personally ("myCallback({...})"). The broadcast (the `<script>` tag executing) causes your function to fire with the data.

**How it works step by step:**

1. Page defines a callback function globally:
   ```js
   window.handleData = function(data) {
     console.log(data.user); // "alice"
   };
   ```

2. Page dynamically injects a `<script>` tag pointing to the JSONP endpoint:
   ```js
   const script = document.createElement("script");
   script.src = "https://api.example.com/user?callback=handleData";
   document.head.appendChild(script);
   ```

3. Server receives the request and wraps the JSON:
   ```js
   // Server response body (Content-Type: application/javascript)
   handleData({ "user": "alice", "score": 42 });
   ```

4. Browser parses and executes the script. `handleData(...)` runs, calling the function defined in step 1.

**Why it's dangerous:**
- The server can return **any JavaScript**, not just the function call. A malicious or compromised JSONP endpoint could execute arbitrary code in your page's context.
- No HTTPS requirement — downgrade attacks are trivial.
- No error handling — `<script>` tag silently fails on network errors; no `catch` possible.
- No request headers — you can't send `Authorization` or `Content-Type`.
- GET only — no POST, no request body.
- Vulnerable to **CSRF** — any page on the internet can include your JSONP endpoint as a script tag and see the authenticated user's data (no SameSite cookie protection equivalent).

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JSONP flow: page creates script tag, server returns a function-call wrapping JSON data, browser executes it">
  <defs>
    <marker id="arr73g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr73b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Page -->
  <rect x="10" y="80" width="175" height="100" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="97" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Page (page.com)</text>
  <text x="97" y="123" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. define handleData()</text>
  <text x="97" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. create &lt;script src=...&gt;</text>
  <text x="97" y="155" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">4. handleData({user:"alice"})</text>
  <text x="97" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">   ← executes in page context</text>

  <!-- Server -->
  <rect x="495" y="80" width="175" height="100" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="582" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server (api.com)</text>
  <text x="582" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">GET /user?callback=handleData</text>
  <text x="582" y="145" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">returns:</text>
  <text x="582" y="160" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">handleData({user:"alice"})</text>

  <!-- Step 2: script tag request -->
  <line x1="187" y1="110" x2="493" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr73b)"/>
  <text x="340" y="102" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">GET /user?callback=handleData  (via &lt;script&gt; tag)</text>

  <!-- Step 3: JSONP response -->
  <line x1="493" y1="155" x2="187" y2="155" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr73g)"/>
  <text x="340" y="172" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">handleData({user:"alice", score:42});  (JavaScript response)</text>

  <!-- Warning box -->
  <rect x="140" y="210" width="400" height="36" rx="5" fill="#2d1117" stroke="#f85149" stroke-width="1.2"/>
  <text x="340" y="225" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">⚠ Executes arbitrary JS in page context — never use JSONP with untrusted servers</text>
  <text x="340" y="240" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Modern alternative: CORS + fetch()  |  JSONP is for legacy compatibility only</text>
</svg>

The server's response is literally JavaScript that the browser executes — elegant in 2005, dangerous in 2025.

## 5. Runnable example

```js
// jsonp-server.js — Node.js, no installs.
// A minimal JSONP server. Shows the old pattern, then a CORS comparison.
const http = require("http");

http.createServer((req, res) => {
  const url = new URL(req.url, "http://localhost:3000");

  if (url.pathname === "/user-jsonp") {
    // ── JSONP ENDPOINT (legacy) ──
    const callback = url.searchParams.get("callback");

    // Validate callback name: only allow safe identifiers
    // Without this check, an attacker could inject ?callback=alert(1)//
    if (!/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(callback || "")) {
      res.writeHead(400, { "Content-Type": "text/plain" });
      res.end("Invalid callback name");
      return;
    }

    const data = { user: "alice", score: 42 };
    res.writeHead(200, { "Content-Type": "application/javascript; charset=utf-8" });
    // Wrap JSON in the callback function call
    res.end(`${callback}(${JSON.stringify(data)});`);
    return;
  }

  if (url.pathname === "/user-cors") {
    // ── CORS ENDPOINT (modern equivalent) ──
    res.writeHead(200, {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    });
    res.end(JSON.stringify({ user: "alice", score: 42 }));
    return;
  }

  res.writeHead(404); res.end("Not found");
}).listen(3000, () => {
  console.log("Server on http://localhost:3000");
  console.log("\nJSONP (old):");
  console.log("  curl 'http://localhost:3000/user-jsonp?callback=myFn'");
  console.log("\nCORS (modern):");
  console.log("  curl http://localhost:3000/user-cors");
});
```

**How to run:** `node jsonp-server.js`

```bash
# JSONP response — the server wraps the data in a function call
curl 'http://localhost:3000/user-jsonp?callback=myFn'
# → myFn({"user":"alice","score":42});

# CORS response — plain JSON, no wrapping
curl http://localhost:3000/user-cors
# → {"user":"alice","score":42}
```

Browser JSONP usage (HTML, for historical illustration only):
```html
<script>
function myFn(data) {
  console.log("Got:", data.user, data.score);
}
</script>
<!-- This script tag fetches the JSONP endpoint: -->
<script src="http://localhost:3000/user-jsonp?callback=myFn"></script>
```

## 6. Walkthrough

- `url.searchParams.get("callback")` — the client names its callback function in the query string. This value ends up in the response body as JS code, so it **must be validated**.
- `/^[a-zA-Z_$][a-zA-Z0-9_$]*$/` — the safelist regex only allows valid JS identifiers. Without this, `?callback=alert(document.cookie)//` would cause the server to return `alert(document.cookie)//({"user":...})` — executing arbitrary JS in every browser that loads it.
- `Content-Type: application/javascript` — the response must be JavaScript, not JSON. Browsers execute script responses, not parse them as data.
- `${callback}(${JSON.stringify(data)});` — `JSON.stringify` escapes the data safely. Never use string concatenation to build the JSON yourself.
- The CORS endpoint (`/user-cors`) shows the modern equivalent: the same data, as plain JSON, with a proper `Access-Control-Allow-Origin` header. `fetch()` can read it; no global callback, no `<script>` injection, proper error handling.

## 7. Gotchas & takeaways

> **JSONP is a remote code execution vector.** The server's response is executed as JavaScript in your page's full security context — it has access to cookies, DOM, localStorage, and can exfiltrate data. Only use JSONP with servers you fully trust and control.

> **Always validate the `callback` parameter server-side.** An unvalidated callback turns a JSONP endpoint into a reflected XSS vulnerability. The regex `^[a-zA-Z_$][a-zA-Z0-9_$]*$` is the minimum safe check.

> **JSONP has no error handling.** A failed `<script>` load just... does nothing. No `catch`, no HTTP status visible to JS, no timeout unless you build one manually.

- JSONP is a historical workaround; **use CORS + `fetch()` for all new code**.
- Works only for `GET` requests — no POST, no custom request headers.
- The callback name from the query string must be validated to prevent XSS.
- Cookies are sent with JSONP requests (no `SameSite` equivalent protection), making JSONP endpoints CSRF-vulnerable.
- jQuery's `$.ajax({ dataType: "jsonp" })` auto-generates a random callback name and cleans up after itself — it's safer than manual JSONP but still carries the fundamental risks.
- If a legacy API offers both JSONP and CORS, always prefer CORS.
