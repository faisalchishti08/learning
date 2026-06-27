---
card: webdev
gi: 5
slug: requestresponse-cycle
title: Request–response cycle
---

## 1. What it is

The **request–response cycle** is the single round-trip at the heart of the web: a client **sends a request**, a server **sends back exactly one response**, and the exchange is over. Every web page load, every API call, every image fetch is one of these cycles.

It's a strict back-and-forth, like a question and an answer:

- **Request** — "Please give me `/about`."
- **Response** — "Here it is: 200 OK, plus this HTML."

One request → one response. Always. Loading a typical web page is actually **many** such cycles (one for the HTML, then more for CSS, images, fonts, scripts).

## 2. Why & when

Understanding this cycle is foundational because it frames **everything** in web development:

- Debugging ("why is my page blank?") usually means inspecting a request and its response.
- Performance ("why is it slow?") is often "too many cycles" or "one slow response."
- APIs are literally designed as request/response contracts.

You think about it whenever you:

- Open the browser's **Network tab** and watch the waterfall of requests.
- Design an endpoint (what request shape comes in, what response goes out).
- Hit a `404` or `500` and need to reason about which side failed.

It's not a "sometimes" concept — it's the lens through which all web traffic is read.

## 3. Core concept

A full cycle has predictable stages:

1. **Resolve** — turn the hostname into an IP via **DNS**.
2. **Connect** — open a TCP connection (and a TLS handshake for HTTPS).
3. **Send request** — the client sends a **request line** (`GET /about HTTP/1.1`), **headers** (host, accept, cookies…), and an optional **body** (for `POST`/`PUT`).
4. **Server processes** — routing, logic, maybe a database call.
5. **Send response** — a **status line** (`HTTP/1.1 200 OK`), **headers** (content-type, length, caching…), and usually a **body** (HTML/JSON/bytes).
6. **Render / use** — the browser parses the response and, for a web page, discovers sub-resources (CSS, JS, images) and fires **more cycles** for each.

Two properties to internalise:

- **One-to-one and ordered:** every request gets exactly one response; the client must ask first.
- **Self-contained:** each cycle carries everything the server needs (the server doesn't remember the previous one — that statelessness is a separate topic). Cookies/tokens ride along *inside* the request to simulate memory.

The anatomy of the messages is consistent: **start line → headers → blank line → optional body**, for both requests and responses.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Numbered steps of a request travelling to the server and a response returning">
  <rect x="30" y="100" width="150" height="60" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="105" y="135" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif">Client</text>
  <rect x="460" y="100" width="150" height="60" rx="10" fill="#1c2430" stroke="#6db33f"/>
  <text x="535" y="135" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif">Server</text>

  <line x1="180" y1="118" x2="458" y2="118" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <text x="320" y="110" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">GET /about  (line + headers + body?)</text>

  <line x1="458" y1="146" x2="180" y2="146" stroke="#79c0ff" stroke-width="2" marker-end="url(#b)"/>
  <text x="320" y="166" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">200 OK  (status + headers + body)</text>

  <text x="320" y="210" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">a web page = many such cycles (HTML, then CSS, JS, images…)</text>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

One arrow out, one arrow back — repeated for every resource a page needs.

## 5. Runnable example

Make a raw request and print the raw response so you can see the actual message parts. This uses `curl`, which ships on macOS, Linux, and modern Windows.

```bash
# -v shows the request lines (>) and response lines (<), headers and all
curl -v https://example.com/
```

Expected (trimmed):
```
> GET / HTTP/2
> Host: example.com
> user-agent: curl/8.4.0
> accept: */*
>
< HTTP/2 200
< content-type: text/html; charset=UTF-8
< content-length: 1256
<
<!doctype html> ... (the HTML body) ...
```

**How to run:** paste `curl -v https://example.com/` into a terminal. Lines starting with `>` are **your request**, lines with `<` are the **server's response**.

## 6. Walkthrough

- `curl` is acting as the **client**. `-v` (verbose) makes it print both halves of the cycle.
- The `>` block is the **request**: a request line (`GET / HTTP/2`), then headers (`Host`, `user-agent`, `accept`), then a blank line marking the end of the request head. A `GET` has no body.
- `curl` resolves `example.com` to an IP (DNS), opens a TLS connection (because `https`), and sends that request — stages 1–3 from part 3.
- The `<` block is the **response**: a status line (`HTTP/2 200`), response headers (`content-type` tells the browser it's HTML, `content-length` is the body size), a blank line, then the **body** (the HTML document).
- That's exactly one cycle. In a real browser, parsing that HTML would reveal `<link>` and `<img>` tags, each triggering its **own** `curl`-like request — which is why one page produces a waterfall of cycles in the Network tab.

## 7. Gotchas & takeaways

> **One page is not one request.** A single visit commonly fires dozens of cycles (stylesheets, scripts, fonts, images, API calls). Slowness is frequently "too many round-trips," not one slow file — which is why bundling, caching, and HTTP/2 multiplexing matter.

> The server **cannot** respond without a request, and it sends **exactly one** response per request. If you need the server to send data later (notifications), you need WebSockets or Server-Sent Events, not the plain cycle.

- Structure of both messages: start line → headers → blank line → optional body.
- Exactly one response per request; the client always initiates.
- DNS → connect → request → process → response → render is the standard pipeline.
- The browser Network tab is the place you actually watch these cycles happen.
