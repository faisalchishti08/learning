---
card: webdev
gi: 12
slug: internet-vs-world-wide-web
title: Internet vs World Wide Web
---

## 1. What it is

People use "the internet" and "the web" as synonyms, but they're different layers:

- The **Internet** is the **global network of networks** — the physical and logical plumbing (cables, routers, Wi-Fi, IP addresses) that lets any two computers exchange data. It's the **infrastructure**.
- The **World Wide Web** is **one service that runs on top of** the Internet: a system of interlinked documents and apps accessed over **HTTP** using **URLs**, viewed in browsers. It's an **application** of the Internet.

Analogy: the **Internet is the road network**; the **Web is one kind of traffic** on it (cars). Email, video calls, online games, and app sync are *other* traffic on the same roads — they use the Internet but are **not** the Web.

## 2. Why & when

The distinction sharpens how you think about systems:

- Not everything online is "the Web." **Email (SMTP), file transfer (FTP), DNS, SSH, video (RTP), and many app protocols** run directly on the Internet without HTTP or browsers.
- When you build a "web app," you're using **one** Internet service (HTTP/Web). When you add a real-time chat over **WebSockets** or push notifications, you're still on the Internet but stretching beyond classic request/response Web.
- Outages and debugging: "the internet is down" (no connectivity at all) is different from "the website is down" (the Web service/server failed while the Internet works fine).

It clarifies history too: the Internet existed for **~20 years before** the Web (invented by Tim Berners-Lee in 1989). The Web made the Internet usable for ordinary people.

## 3. Core concept

Think in **layers**, bottom to top:

1. **Internet (transport):** computers get **IP addresses** and exchange packets using **TCP/IP**. This layer just moves bytes between machines; it doesn't care what the bytes mean.
2. **Services on top:** many protocols use that transport for different purposes — **HTTP** (Web), **SMTP/IMAP** (email), **FTP** (files), **DNS** (name lookup), **SSH** (remote shell), etc.
3. **The Web specifically** is the trio invented together:
   - **HTTP** — the protocol for requesting/serving resources.
   - **URLs** — addresses for those resources.
   - **HTML** — the linked document format.
   Plus browsers to render it. Hyperlinks weaving documents together are what make it a "web."

So the Web is a **subset** of what the Internet carries. Every Web request is Internet traffic; not every bit of Internet traffic is the Web.

A quick test: if you can do it **without HTTP/URLs/a browser**, it's an Internet service that isn't the Web. Sending email via SMTP? Internet, not Web. Loading a page via `https://`? That's the Web (on the Internet).

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Internet is the base network; the Web is one of several services running on it">
  <rect x="40" y="170" width="560" height="56" rx="10" fill="#102a17" stroke="#3fb950"/>
  <text x="320" y="195" fill="#3fb950" font-size="14" text-anchor="middle" font-family="sans-serif">INTERNET — global TCP/IP network (the infrastructure)</text>
  <text x="320" y="214" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">IP addresses · routers · cables · Wi-Fi</text>

  <rect x="60" y="80" width="120" height="60" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="106" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif">WEB</text>
  <text x="120" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">HTTP+URL+HTML</text>
  <rect x="200" y="80" width="110" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="255" y="106" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Email</text>
  <text x="255" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">SMTP/IMAP</text>
  <rect x="330" y="80" width="110" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="385" y="106" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Files</text>
  <text x="385" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">FTP</text>
  <rect x="460" y="80" width="120" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="106" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Video/Games</text>
  <text x="520" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">other protocols</text>

  <line x1="120" y1="140" x2="120" y2="170" stroke="#8b949e"/>
  <line x1="255" y1="140" x2="255" y2="170" stroke="#8b949e"/>
  <line x1="385" y1="140" x2="385" y2="170" stroke="#8b949e"/>
  <line x1="520" y1="140" x2="520" y2="170" stroke="#8b949e"/>
</svg>

The Web is just one box sitting on the Internet; email, files, and video are siblings, not children of the Web.

## 5. Runnable example

Show the two layers directly: first prove raw **Internet** connectivity (IP packets, no Web), then make a **Web** request on the same network.

```bash
# 1) INTERNET layer — ping moves IP packets; no HTTP, no URL, no browser involved:
ping -c 2 1.1.1.1

# 2) Name lookup — DNS is an Internet service, also not the Web:
nslookup example.com         # (or: host example.com)

# 3) WEB layer — now an actual HTTP request for a resource by URL:
curl -I https://example.com/
```

Expected shape:
```
# ping -> replies from 1.1.1.1 (Internet works, pure IP)
# nslookup -> example.com resolves to an IP (DNS, an Internet service)
# curl -I -> HTTP/2 200 ... content-type: text/html   (THIS is the Web)
```

**How to run:** paste each command into a terminal. Steps 1–2 use the Internet **without** the Web; step 3 is the Web riding on that same Internet.

## 6. Walkthrough

- `ping 1.1.1.1` sends **ICMP packets** to an IP address. There's no HTTP, no URL, no HTML — just the raw **Internet** moving bytes between machines. Getting replies proves connectivity at the network layer.
- `nslookup example.com` uses **DNS**, an Internet service that maps names to IPs. It's essential plumbing the Web *relies on*, but DNS itself is not the Web — it's another protocol on the Internet.
- `curl -I https://example.com/` finally does a **Web** thing: an **HTTP** request for a **URL**, getting back a status line and headers (`HTTP/2 200`, `content-type: text/html`). This is the World Wide Web — and notice it could only happen because steps 1–2 (Internet + DNS) already worked.
- The progression makes the layering concrete: the Internet (and DNS) are underneath; the Web is the HTTP/URL/HTML service layered on top. Turn off Wi-Fi and *all three* fail — because the Web can't exist without the Internet beneath it.

## 7. Gotchas & takeaways

> **"The internet" ≠ "the web."** Email, app sync, video calls, online games, and SSH are Internet services that are **not** the Web. When someone says "it's on the internet," they often mean the Web specifically — but as a developer, keep the layers distinct.

> The Web **depends on** the Internet, never the reverse. The Internet ran for two decades before the Web existed (1989). If the Internet is down, the Web is down; but plenty of Internet traffic keeps flowing with no Web involved.

- Internet = the global TCP/IP network (infrastructure that moves bytes).
- Web = one service on it: HTTP + URLs + HTML, viewed in browsers.
- Other Internet services (email, FTP, DNS, video, SSH) are siblings of the Web, not part of it.
- Every Web request is Internet traffic; not all Internet traffic is the Web.
