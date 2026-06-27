---
card: webdev
gi: 31
slug: reverse-proxy-load-balancer-basics
title: Reverse proxy & load balancer basics
---

## 1. What it is

A **reverse proxy** is a server that sits in front of one or more backend servers and forwards client requests to them. From the client's perspective, it is talking to one address — it never knows about the backends. The reverse proxy:

- Receives every request.
- Decides which backend handles it.
- Forwards the request, gets the response, and sends it back to the client.

A **load balancer** is a reverse proxy whose primary job is distributing traffic across multiple identical backend instances to avoid overloading any single one. The terms overlap: most load balancers are reverse proxies, and most reverse proxies can do basic load balancing.

Common software: **Nginx** and **HAProxy** are the classic open-source options. Cloud-managed equivalents: AWS ALB/NLB, GCP Cloud Load Balancing, Azure Load Balancer.

## 2. Why & when

A single server has a ceiling: a fixed amount of CPU, RAM, and network bandwidth. When traffic exceeds that ceiling, requests queue and latency spikes. Solutions:

- **Scale up** — get a bigger single server. Has limits; eventually impossible.
- **Scale out** — run many identical servers and distribute load. The load balancer makes this possible by hiding the fact that many servers exist behind one address.

Other reasons to add a reverse proxy even with one backend:

- **TLS termination** — the proxy handles HTTPS; backends speak plain HTTP on a private network.
- **Caching** — Nginx can cache upstream responses.
- **Compression** — gzip responses before sending to clients.
- **Security** — hide backend IPs, rate-limit clients, strip sensitive headers.
- **Routing** — send `/api/*` to the API servers and `/*` to the static file servers.

You need a load balancer as soon as you run more than one instance of a service, or when a single instance can no longer handle peak traffic.

## 3. Core concept

Think of a receptionist at a large company. Every visitor (client request) arrives at the front desk (reverse proxy). The receptionist decides which employee (backend server) is free to handle them and sends the visitor to that desk. Visitors never know how many employees there are or which one helped them.

**Load-balancing algorithms** determine how the receptionist picks:

- **Round-robin** — rotate through the backends in order: request 1 → server A, request 2 → server B, request 3 → server C, request 4 → server A …
- **Least connections** — send the next request to whichever backend has the fewest active connections. Better for variable-length requests.
- **IP hash** — hash the client IP and always route that IP to the same backend. Useful when you need sticky sessions without a shared session store.
- **Weighted** — give powerful servers a higher share of traffic.

**Health checks** are essential: the load balancer periodically sends a probe (e.g. `GET /health`) to each backend. If a backend fails to respond, it is removed from rotation until it recovers. This makes deployments safer — you can take one backend offline for an upgrade while others continue serving.

**Session stickiness** (also called affinity) means all requests from one client always go to the same backend. Needed if backends store session state locally. The better solution is to store sessions in a shared store (Redis) and allow any backend to serve any request.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reverse proxy / load balancer distributing client requests across three backend servers">
  <defs>
    <marker id="ra" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <!-- Clients -->
  <rect x="20" y="110" width="90" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="135" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Clients</text>
  <!-- Load balancer -->
  <rect x="250" y="100" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="325" y="126" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Load Balancer</text>
  <text x="325" y="146" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">/ Reverse Proxy</text>
  <!-- Backends -->
  <rect x="520" y="40" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Backend A</text>

  <rect x="520" y="110" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="135" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Backend B</text>

  <rect x="520" y="180" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="205" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Backend C</text>

  <!-- client → LB -->
  <line x1="110" y1="130" x2="248" y2="130" stroke="#6db33f" stroke-width="1.8" marker-end="url(#ra)"/>

  <!-- LB → backends -->
  <line x1="400" y1="118" x2="518" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rb)"/>
  <line x1="400" y1="130" x2="518" y2="130" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rb)"/>
  <line x1="400" y1="142" x2="518" y2="200" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rb)"/>

  <!-- health check label -->
  <text x="585" y="235" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">health-checked every N seconds</text>

  <!-- algorithm label -->
  <text x="325" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">round-robin / least-conn / IP-hash</text>
</svg>

All clients talk to one address; the load balancer distributes requests across backends and removes unhealthy ones automatically.

## 5. Runnable example

This Node.js script starts **three mini backend servers** on ports 3001–3003 and a **round-robin load balancer** on port 3000, all in one file. No extra installs — only Node's built-in `http` module.

```js
// save as lb_demo.js — needs Node.js
const http = require("http");

// ─── Three backends ───────────────────────────────────────
const backends = [3001, 3002, 3003];
backends.forEach((port) => {
  http.createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(`Hello from backend on port ${port}\n`);
  }).listen(port);
});

// ─── Round-robin load balancer ────────────────────────────
let current = 0;

const lb = http.createServer((clientReq, clientRes) => {
  const targetPort = backends[current % backends.length];
  current++;

  // Forward the request to the chosen backend
  const proxy = http.request(
    { hostname: "localhost", port: targetPort, path: clientReq.url, method: clientReq.method },
    (backendRes) => {
      clientRes.writeHead(backendRes.statusCode, backendRes.headers);
      backendRes.pipe(clientRes);
    }
  );
  proxy.on("error", (e) => {
    clientRes.writeHead(502);
    clientRes.end(`Backend error: ${e.message}`);
  });
  clientReq.pipe(proxy);
});

lb.listen(3000, () => {
  console.log("Load balancer on http://localhost:3000");
  console.log("Send 6 requests to see round-robin:");

  // Send 6 requests sequentially and print each response
  let done = 0;
  for (let i = 0; i < 6; i++) {
    http.get(`http://localhost:3000/`, (res) => {
      let body = "";
      res.on("data", (c) => (body += c));
      res.on("end", () => {
        console.log(`Request ${i + 1}: ${body.trim()}`);
        if (++done === 6) {
          lb.close();
          process.exit(0);
        }
      });
    });
  }
});
```

**How to run:** save as `lb_demo.js`, then run `node lb_demo.js`.

Expected output:
```
Load balancer on http://localhost:3000
Send 6 requests to see round-robin:
Request 1: Hello from backend on port 3001
Request 2: Hello from backend on port 3002
Request 3: Hello from backend on port 3003
Request 4: Hello from backend on port 3001
Request 5: Hello from backend on port 3002
Request 6: Hello from backend on port 3003
```

## 6. Walkthrough

- `backends.forEach((port) => { http.createServer(...).listen(port) })` — spins up three HTTP servers, each identifying itself by port number in the response body.
- `let current = 0` — the round-robin counter. Every incoming request increments it; `current % backends.length` maps it to 0, 1, or 2.
- `const targetPort = backends[current % backends.length]` — picks the next backend in rotation. After `current` reaches 3 it wraps back to 0 via modulo.
- `http.request({ hostname: "localhost", port: targetPort, ... })` — the load balancer opens a new HTTP connection to the chosen backend, forwards the client's method and path.
- `backendRes.pipe(clientRes)` — streams the backend's response body directly to the client. The client sees a normal HTTP response; it has no idea a proxy was involved.
- `proxy.on("error", ...)` — if a backend is down, respond with `502 Bad Gateway` (the standard "upstream server failed" status). A production LB would also remove that backend from rotation.
- `clientReq.pipe(proxy)` — forward any request body (e.g. POST data) to the backend.

## 7. Gotchas & takeaways

> **A load balancer is a single point of failure — unless it is itself redundant.** Running one Nginx as your LB means one process crashing takes down everything. Production setups use active-active LB pairs (both serving) or cloud-managed LBs that are inherently redundant.

> **Sticky sessions and horizontal scaling fight each other.** If backend A holds session state locally and the LB sends the next request to backend B, the session is gone. Fix: use a shared session store (Redis, a database) so any backend can serve any user.

- `502 Bad Gateway` = load balancer could not reach a backend. `503 Service Unavailable` = no healthy backends. `504 Gateway Timeout` = backend took too long.
- Layer 4 LBs (TCP) are faster but can only route by IP/port. Layer 7 LBs (HTTP) are slower but can route by URL path, headers, or cookies — far more flexible for web apps.
- Zero-downtime deploys work by taking one backend out of the LB's rotation, upgrading it, verifying it passes health checks, then rotating back in — repeat for each backend.
- Nginx can act as both reverse proxy and static file server in one config, which is why it is so common in front of Node or Python/Gunicorn backends.
