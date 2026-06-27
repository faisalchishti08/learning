---
card: webdev
gi: 10
slug: web-browser-as-a-user-agent
title: Web browser as a user agent
---

## 1. What it is

A **user agent** is any program that acts **on behalf of a user** to make web requests. The web browser is the most common user agent — but `curl`, a mobile app, a search-engine crawler, and a script are user agents too.

The browser introduces itself to every server with a **`User-Agent` header**, a string describing what it is:

```
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36
```

So "user agent" is both a **concept** (software acting for the user) and a concrete **HTTP header** that identifies that software.

## 2. Why & when

The idea matters because the server often **adapts** to who's asking:

- **Content negotiation / responsive delivery** — a server might send a lighter page to a known mobile agent.
- **Analytics** — which browsers/devices visit you (to decide what to support).
- **Bot handling** — search crawlers (`Googlebot`) and scrapers identify via User-Agent; sites may treat them differently (or block them).
- **Feature detection caveats** — historically people sniffed the UA string to branch behaviour (largely discouraged now; feature detection is better).

You meet it when:

- Debugging "works in my browser, not in the app" — different user agents, different behaviour.
- Writing a script/crawler and needing to set a polite, identifying User-Agent.
- Reading server logs full of UA strings.

## 3. Core concept

The browser does far more than send a header — being a *user agent* means it **represents the user faithfully and safely**:

1. **Speaks the protocols** — HTTP(S), and parses HTML/CSS/JS so the user doesn't have to.
2. **Announces itself** — sends `User-Agent`, plus `Accept`, `Accept-Language`, etc., so the server can tailor the response.
3. **Enforces the user's safety** — applies the Same-Origin Policy, manages cookies, blocks mixed content, sandboxes pages. The agent protects *its* user.
4. **Stores user context** — cookies, cache, history, autofill — and decides what to share with which site.

The `User-Agent` string itself is a historical mess: nearly every browser starts with `Mozilla/5.0` for legacy compatibility reasons, then lists rendering engines (`AppleWebKit`, `Gecko`) and browser names. It's **self-reported and trivially spoofable** — never trust it for security.

The web is even **moving away** from the detailed UA string (it leaks fingerprinting data). Newer **Client Hints** (`Sec-CH-UA`) let the browser share only what a server explicitly asks for. But the mental model stays: *the browser is your delegate, identifying itself and acting in your interest.*

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="User delegates to a browser which sends requests with a User-Agent header to servers">
  <circle cx="80" cy="110" r="26" fill="#1c2430" stroke="#6db33f"/>
  <text x="80" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">user</text>
  <rect x="170" y="80" width="170" height="64" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="255" y="106" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="255" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the user agent</text>
  <rect x="460" y="80" width="150" height="64" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="535" y="116" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Server</text>

  <line x1="106" y1="110" x2="168" y2="110" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <text x="137" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">clicks</text>
  <line x1="340" y1="110" x2="458" y2="110" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="400" y="100" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">request +</text>
  <text x="400" y="128" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">User-Agent</text>
  <text x="320" y="190" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">the agent acts for the user and identifies itself to the server</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The user clicks; the browser (agent) turns that into a request and tells the server who it is.

## 5. Runnable example

See the User-Agent two ways: read your browser's, and prove it's just a header by sending a custom one with `curl`.

```bash
# 1) Ask a server to echo back the User-Agent it received:
curl https://httpbin.org/user-agent
# -> {"user-agent": "curl/8.4.0"}

# 2) Pretend to be a browser by overriding the header (shows it is self-reported):
curl -A "Mozilla/5.0 (MyFakeAgent)" https://httpbin.org/user-agent
# -> {"user-agent": "Mozilla/5.0 (MyFakeAgent)"}
```

And in any **browser console** (F12), read the live value:
```js
console.log(navigator.userAgent);
```

**How to run:** paste the `curl` lines in a terminal; paste the `console.log` in your browser's DevTools console. Notice `curl` reports itself as `curl/...`, but you can make it claim anything with `-A`.

## 6. Walkthrough

- The first `curl` sends a normal request; `httpbin.org/user-agent` simply **echoes the `User-Agent` header** it received. With no override, `curl` honestly reports `curl/8.4.0` — `curl` is itself a user agent.
- The second `curl` uses `-A` to **set a fake User-Agent**. The server dutifully echoes `Mozilla/5.0 (MyFakeAgent)`. This demonstrates the crucial fact: the header is **self-declared** and can say anything. A real Chrome, a scraper pretending to be Chrome, and this fake all look the same to the server.
- `navigator.userAgent` in the console reveals your actual browser's string — the same value it sends on every request. You'll see the legacy `Mozilla/5.0` prefix and engine names.
- Together these show both sides: the browser *is* a user agent that identifies itself, and that identification is a convenience signal, **not** a trustworthy credential.

## 7. Gotchas & takeaways

> **Never trust the User-Agent for security or access control.** It's self-reported and spoofable in one flag (`curl -A`). Use it for analytics or best-effort adaptation, never to decide "is this really an admin's browser."

> **Avoid UA sniffing to branch features.** It breaks as browsers change their strings and as new browsers appear. Prefer **feature detection** (`if ('IntersectionObserver' in window)`) over "is this Chrome." The platform is also shifting to **Client Hints**, which share device info only on request.

- A user agent is any software making requests for a user; the browser is the prototypical one.
- It announces itself via the `User-Agent` header and tailors requests with `Accept*` headers.
- The browser-as-agent also enforces the user's safety (Same-Origin Policy, cookies, sandboxing).
- The UA string is legacy-laden, self-reported, and not a security signal.
