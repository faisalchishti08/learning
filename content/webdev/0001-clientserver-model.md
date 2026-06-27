---
card: webdev
gi: 1
slug: clientserver-model
title: Client–server model
---

## 1. What it is

The **client–server model** is the basic way almost everything on the web is organised. Two kinds of programs talk to each other:

- A **client** asks for something. On the web the client is usually your **browser** (Chrome, Safari, Firefox), but it can also be a mobile app, a `curl` command, or another server.
- A **server** is a program that waits for requests, does some work, and sends back a **response**. It "serves" things: web pages, images, JSON data, etc.

The client always starts the conversation. The server never randomly pushes a page to you out of nowhere — it answers when asked. One server can handle thousands of clients at the same time, and one client can talk to many servers (the page you're reading might pull from a dozen).

In one sentence: **the client requests, the server responds.**

## 2. Why & when

Before this model, the alternative was everyone's computer being equal and talking directly to everyone else (peer-to-peer). That's hard to secure, hard to keep consistent, and hard to scale. The client–server split exists because it cleanly separates concerns:

- **Centralised data & logic** — the server is the single source of truth (your bank balance lives on the bank's server, not on your laptop).
- **Thin, replaceable clients** — any browser on any device can use the same server.
- **Security** — sensitive work (checking passwords, charging cards) happens on the server where users can't tamper with it.
- **Scalability** — you can add more servers behind one address to serve more clients.

You use it essentially **always** in web development:

- Loading a website (browser → web server).
- A single-page app fetching data (JavaScript → API server).
- A microservice calling another microservice (server → server: here the caller is the "client").

The alternative model worth knowing is **peer-to-peer (P2P)** — used by BitTorrent or some video-call tech — where every node is both client and server. The web itself, though, is overwhelmingly client–server.

## 3. Core concept

Think of a restaurant. **You (client)** read the menu and tell the **waiter (the network)** what you want. The **kitchen (server)** cooks it and sends the dish back. You never walk into the kitchen; you only send requests and receive responses through a well-defined interface (the menu = the API).

The full loop has a few moving parts:

1. **Identify the server.** The client has an address — a URL like `https://example.com`. The hostname (`example.com`) is turned into an IP address by **DNS** (the web's phone book).
2. **Open a connection.** The client opens a network connection to that IP on a specific **port** (80 for HTTP, 443 for HTTPS).
3. **Send a request.** The client sends an **HTTP request**: a method (`GET`, `POST`…), a path (`/users/42`), headers, and optionally a body.
4. **Server processes.** The server reads the request, maybe queries a database, runs business logic, and builds a response.
5. **Send a response.** The server returns an **HTTP response**: a status code (`200 OK`, `404 Not Found`), headers, and a body (HTML, JSON, an image…).
6. **Connection handling.** The connection may stay open for more requests or close.

Key properties that fall out of this:

- **The client drives.** No request → no response.
- **Stateless by default.** Each request stands alone; the server doesn't automatically remember the last one (cookies/sessions are added on top to fake memory).
- **The roles are relative.** "Client" and "server" describe *behaviour in one exchange*, not fixed machines. A web server calling a database is acting as a *client* of that database.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client sends a request to a server and the server sends a response back">
  <rect x="30" y="80" width="170" height="64" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="108" fill="#e6edf3" font-size="15" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="115" y="128" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">(browser)</text>

  <rect x="440" y="80" width="170" height="64" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="108" fill="#e6edf3" font-size="15" text-anchor="middle" font-family="sans-serif">Server</text>
  <text x="525" y="128" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">(web / API)</text>

  <line x1="205" y1="100" x2="435" y2="100" stroke="#3fb950" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="320" y="92" fill="#3fb950" font-size="12" text-anchor="middle" font-family="sans-serif">1. HTTP request (GET /)</text>

  <line x1="435" y1="126" x2="205" y2="126" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow2)"/>
  <text x="320" y="146" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">2. HTTP response (200 OK + HTML)</text>

  <defs>
    <marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="arrow2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The client always sends arrow 1 first; the server replies with arrow 2. The server cannot start the conversation on its own.

## 5. Runnable example

Let's actually *be* both sides. This tiny Node.js program starts a **server**, then acts as a **client** that sends it a request — so you can watch one full request/response cycle on your own machine.

```js
// save as server.js — needs Node.js (no extra installs)
const http = require("http");

// ---- THE SERVER: waits for requests, sends responses ----
const server = http.createServer((request, response) => {
  console.log(`Server got: ${request.method} ${request.url}`);
  response.writeHead(200, { "Content-Type": "text/plain" });
  response.end("Hello from the server!");
});

server.listen(3000, () => {
  console.log("Server listening on http://localhost:3000");

  // ---- THE CLIENT: sends a request, reads the response ----
  http.get("http://localhost:3000/hello", (res) => {
    let body = "";
    res.on("data", (chunk) => (body += chunk));
    res.on("end", () => {
      console.log(`Client received status ${res.statusCode}: "${body}"`);
      server.close(); // done — shut the server down so the program exits
    });
  });
});
```

**How to run:** save as `server.js`, then run `node server.js` in a terminal. (No `npm install` needed — `http` is built into Node.)

Expected output:
```
Server listening on http://localhost:3000
Server got: GET /hello
Client received status 200: "Hello from the server!"
```

## 6. Walkthrough

- `const http = require("http")` loads Node's built-in HTTP library — it can play both client and server.
- `http.createServer((request, response) => { ... })` defines the **server**. The callback runs **once per incoming request**. `request` describes what was asked; `response` is what we write back.
- `response.writeHead(200, {...})` sets the **status code** (`200` = success) and a header saying the body is plain text. This is the server choosing how to answer.
- `response.end("Hello from the server!")` sends the **body** and finishes the response. That string is what the client will receive.
- `server.listen(3000, ...)` starts the server on **port 3000** and only *then* runs the client code — we wait until the server is ready before asking it anything.
- `http.get("http://localhost:3000/hello", (res) => {...})` is the **client** making a `GET` request. `localhost` means "this same machine," so the request travels right back to our own server.
- The server logs `Server got: GET /hello` — proof the request arrived. Then the client's `res` events fire: we accumulate the body in chunks (`data`) and, when complete (`end`), print the status and body.
- `server.close()` stops the server so the Node process can exit cleanly.

The whole thing demonstrates the rule from part 3: the client spoke first (`http.get`), the server only answered after being asked.

## 7. Gotchas & takeaways

> "Client" and "server" are **roles in one exchange, not machine types.** Your backend web server becomes a *client* the moment it calls a database or another API. Don't think "client = laptop, server = big computer."

> The server can't initiate. If you need the server to push data to the client (chat messages, live scores), plain request/response isn't enough — that's exactly why **WebSockets** and **Server-Sent Events** were invented.

- The client always sends the first message; the server only responds.
- One request gets one response — and by default the server remembers nothing between them (HTTP is stateless).
- `localhost` / `127.0.0.1` means "this same machine," handy for running client and server together while learning.
- Ports matter: a server listens on a port (e.g. 3000, 80, 443); the client must aim at that exact port.
- This single pattern underlies web pages, REST APIs, and microservice-to-microservice calls alike.
