---
card: webdev
gi: 9
slug: origin-scheme-host-port
title: Origin (scheme + host + port)
---

## 1. What it is

An **origin** is the combination of exactly three parts of a URL:

```
scheme  +  host  +  port
https   +  example.com  +  443
```

Two URLs have the **same origin** only if **all three** match. The path, query, and fragment are **not** part of the origin.

Origin is the web's fundamental **security boundary**. The browser uses it to decide what one page is allowed to do to another. "Same origin" means "same trust zone"; "cross-origin" means "be careful."

## 2. Why & when

Origin underpins the rules that keep the web safe:

- The **Same-Origin Policy (SOP)** stops a script on `evil.com` from reading your `bank.com` data. Without it, any site could rifle through your logged-in sessions on other sites.
- **CORS** (Cross-Origin Resource Sharing) is how a server *opts in* to letting other origins call it.
- **Cookies**, `localStorage`, and many APIs are **scoped to an origin**.

You bump into origins whenever:

- Your frontend on `http://localhost:3000` calls an API on `http://localhost:5000` and the browser blocks it → **different port = different origin**.
- You move from `http://` to `https://` and something breaks → **different scheme = different origin**.
- You see a console error: *"blocked by CORS policy: No 'Access-Control-Allow-Origin' header."*

## 3. Core concept

The rule is unforgiving: **change any one of scheme, host, or port and it's a new origin.**

Compare against `https://example.com` (port 443 implied):

| URL | Same origin? | Why |
|---|---|---|
| `https://example.com/page` | ✅ | path doesn't matter |
| `https://example.com?q=1` | ✅ | query doesn't matter |
| `http://example.com` | ❌ | scheme differs (http vs https) |
| `https://api.example.com` | ❌ | host differs (subdomain counts!) |
| `https://example.com:8443` | ❌ | port differs |

Key subtleties:

- **Subdomains are different origins.** `app.example.com` ≠ `example.com`. (Cookies have their own, looser domain rules, but *origin* is strict.)
- **Default ports count even when hidden.** `https://example.com` is really port 443; `https://example.com:443` is the same origin, but `:8443` is not.
- The **Same-Origin Policy** lets a page freely load cross-origin *resources* (images, scripts, CSS) but blocks it from **reading** cross-origin *data* (the response of a `fetch`) unless the other server allows it via **CORS**.

So origin is "who am I, security-wise," and crossing it triggers the browser's protective machinery.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Origin equals scheme plus host plus port; changing any one creates a new origin">
  <rect x="160" y="20" width="320" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="45" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace">origin = https + example.com + 443</text>

  <rect x="40" y="100" width="170" height="90" rx="8" fill="#102a17" stroke="#3fb950"/>
  <text x="125" y="122" fill="#3fb950" font-size="12" text-anchor="middle" font-family="sans-serif">SAME origin</text>
  <text x="125" y="144" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">/page</text>
  <text x="125" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">?q=1</text>
  <text x="125" y="178" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(path/query ignored)</text>

  <rect x="240" y="100" width="360" height="90" rx="8" fill="#2a1414" stroke="#ff7b72"/>
  <text x="420" y="122" fill="#ff7b72" font-size="12" text-anchor="middle" font-family="sans-serif">DIFFERENT origin</text>
  <text x="420" y="144" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">http://example.com  (scheme)</text>
  <text x="420" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">https://api.example.com  (host)</text>
  <text x="420" y="176" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">https://example.com:8443  (port)</text>
</svg>

Match all three → same trust zone. Differ in any one → the browser treats it as foreign.

## 5. Runnable example

The browser exposes the current origin and lets you compare. This page reports its own origin and tests a few URLs against it.

```html
<!doctype html>
<html lang="en">
  <body>
    <h1>Origin checker</h1>
    <pre id="out"></pre>
    <script>
      const me = location.origin;             // scheme + host + port of THIS page
      const urls = [
        location.href + "some/path?q=1",      // same origin (path/query differ)
        "https://example.com/",
        "http://" + location.hostname + "/",  // different scheme
        "https://api." + location.hostname + "/" // different host (subdomain)
      ];
      const lines = ["This page's origin: " + me, ""];
      for (const u of urls) {
        const o = new URL(u, me).origin;
        lines.push((o === me ? "SAME      " : "DIFFERENT ") + " -> " + o);
      }
      document.getElementById("out").textContent = lines.join("\n");
    </script>
  </body>
</html>
```

**How to run:** save as `origin.html` and open it in a browser. (Open it via a local server like `python3 -m http.server` to see a real `http://localhost:PORT` origin rather than a `file://` one.)

## 6. Walkthrough

- `location.origin` gives the **current page's origin** — just scheme+host+port, no path. That's the browser's own definition, authoritative.
- We build a list of candidate URLs and, for each, construct `new URL(u, me).origin` to extract *its* origin, then compare with `===`.
- The first URL only differs in **path and query**, so its origin equals `me` → printed `SAME`. This proves path/query are irrelevant to origin.
- Swapping the **scheme** to `http://` yields a different origin → `DIFFERENT`, even though the host is identical. Scheme is part of the identity.
- Prefixing the host with `api.` (a **subdomain**) also yields `DIFFERENT`. This is the gotcha people trip on: subdomains are separate origins.
- Run it from `localhost:8000` vs `localhost:8001` and you'd see the **port** flip the result too.

## 7. Gotchas & takeaways

> The classic dev frustration: frontend on `localhost:3000`, API on `localhost:5000`. Same machine, same scheme, same host — but **different port = different origin**, so the browser enforces CORS. Fix it by enabling CORS on the API or proxying through the same origin, not by "turning off security."

> **Subdomains are not the same origin.** `app.example.com` calling `example.com` is cross-origin. (Cookies can be shared across subdomains via the `Domain` attribute, but that's a cookie rule, not an origin rule — don't conflate them.)

- Origin = scheme + host + port; all three must match.
- Path, query, and fragment are **not** part of the origin.
- Default ports count even when omitted (https ⇒ 443).
- Origin is the browser's security boundary; crossing it triggers Same-Origin Policy and CORS.
