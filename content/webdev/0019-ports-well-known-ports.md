---
card: webdev
gi: 19
slug: ports-well-known-ports
title: Ports & well-known ports
---

## 1. What it is

An **IP address** gets traffic to the right machine. A **port** gets it to the right program on that machine. A port is a 16-bit integer (0–65 535) that acts as a numbered door — many programs can run on one machine simultaneously, each listening on a different port.

A full network connection endpoint (called a **socket**) is the combination of: IP address + port + protocol. Two sockets — one on the client, one on the server — form a connection: `(93.184.216.34, 443, TCP)` paired with `(192.168.1.5, 54321, TCP)`.

## 2. Why & when

Without ports, your machine couldn't distinguish whether an incoming packet is meant for the web server, the mail server, or SSH — they'd all arrive at the same IP. Ports solve this by giving each service its own numbered "slot."

You work with ports when:
- Starting a development server (`node server.js` defaults to port `3000`; the URL is `http://localhost:3000`).
- Configuring firewalls (open port 443 for HTTPS; block everything else).
- Debugging connection failures (`ECONNREFUSED` means nothing is listening on that port).
- Setting up Docker port mappings (`-p 8080:80` maps host port 8080 to container port 80).
- Reading server logs that include the source port of each connection.

## 3. Core concept

Think of an IP address as a large apartment building's street address, and a port as the individual apartment number. Many residents (services) share one address (IP), but mail (packets) is delivered to the right door (port).

**Port ranges:**

| Range | Name | Who assigns |
|-------|------|------------|
| 0–1 023 | Well-known / system ports | IANA-assigned; root/admin to bind |
| 1 024–49 151 | Registered ports | IANA-registered for specific services |
| 49 152–65 535 | Dynamic / ephemeral ports | OS assigns automatically to clients |

**Well-known ports every developer should know:**

| Port | Protocol | Service |
|------|---------|---------|
| 20, 21 | TCP | FTP (data, control) |
| 22 | TCP | SSH |
| 25 | TCP | SMTP (email sending) |
| 53 | TCP+UDP | DNS |
| 80 | TCP | HTTP |
| 110 | TCP | POP3 (email retrieval) |
| 143 | TCP | IMAP (email) |
| 443 | TCP | HTTPS |
| 465/587 | TCP | SMTP with TLS / submission |
| 3306 | TCP | MySQL |
| 5432 | TCP | PostgreSQL |
| 6379 | TCP | Redis |
| 27017 | TCP | MongoDB |

**How a client picks a port:** when you open `https://example.com`, your browser doesn't use a fixed source port — the OS picks a random **ephemeral port** (e.g. 54 321) from the dynamic range. The server sees connections coming from `your_ip:54321` → `93.184.216.34:443`. When you open a second tab to the same server, the OS picks a different ephemeral port (e.g. 54 322) so the two connections are distinguishable.

## 4. Diagram

<svg viewBox="0 0 640 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a client connecting with an ephemeral port to server port 443, alongside other server services on ports 80 and 22">
  <defs>
    <marker id="pa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Client machine -->
  <rect x="10" y="30" width="180" height="200" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="54" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Client (browser)</text>
  <text x="100" y="72" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">IP: 192.168.1.5</text>

  <rect x="30"  y="88"  width="140" height="32" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="100" y="109" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">:54321 (tab 1)</text>

  <rect x="30"  y="128" width="140" height="32" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="100" y="149" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">:54322 (tab 2)</text>

  <text x="100" y="196" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Ephemeral ports</text>
  <text x="100" y="212" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">49152–65535</text>

  <!-- Server machine -->
  <rect x="450" y="30" width="180" height="200" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="54" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Server</text>
  <text x="540" y="72" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">IP: 93.184.216.34</text>

  <rect x="470" y="88"  width="140" height="32" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="109" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">:443  HTTPS</text>

  <rect x="470" y="128" width="140" height="32" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="540" y="149" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">:80   HTTP</text>

  <rect x="470" y="168" width="140" height="32" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="540" y="189" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">:22   SSH</text>

  <!-- Connection arrows -->
  <line x1="192" y1="104" x2="448" y2="104" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pa)"/>
  <text x="320" y="97" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">:54321 → :443</text>

  <line x1="192" y1="144" x2="448" y2="144" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pa)"/>
  <text x="320" y="157" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">:54322 → :443</text>

  <!-- Legend -->
  <text x="320" y="250" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Each browser tab gets a unique ephemeral port — same destination, distinct connections</text>
</svg>

The server listens on fixed well-known ports (443, 80, 22). Each client connection arrives from a unique ephemeral source port.

## 5. Runnable example

```js
// save as ports.js — Node.js, no installs
// Starts two servers on different ports and shows how clients get ephemeral ports

const net = require("net");

// Server 1 on port 4001
const server1 = net.createServer((socket) => {
  console.log(`Server:4001  ← client port ${socket.remotePort}`);
  socket.end("hello from 4001\n");
});

// Server 2 on port 4002
const server2 = net.createServer((socket) => {
  console.log(`Server:4002  ← client port ${socket.remotePort}`);
  socket.end("hello from 4002\n");
});

server1.listen(4001, () => {
  server2.listen(4002, () => {
    // Client connects to both servers; OS assigns a different ephemeral port each time
    const c1 = net.createConnection({ port: 4001 }, () => {
      console.log(`Client connected to :4001 from local port ${c1.localPort}`);
    });
    const c2 = net.createConnection({ port: 4002 }, () => {
      console.log(`Client connected to :4002 from local port ${c2.localPort}`);
    });

    c1.on("close", () => c2.destroy());
    c2.on("close", () => { server1.close(); server2.close(); });
  });
});
```

**How to run:** `node ports.js` — no `npm install` needed; `net` is built into Node.

Expected output (port numbers will differ):
```
Server:4001  ← client port 54891
Client connected to :4001 from local port 54891
Server:4002  ← client port 54892
Client connected to :4002 from local port 54892
```

## 6. Walkthrough

- `net.createServer((socket) => {...})` — creates a TCP server. `socket.remotePort` is the ephemeral port the client's OS chose automatically.
- `server1.listen(4001, ...)` — binds the process to port 4001. If something is already on that port you'll get `EADDRINUSE`.
- `net.createConnection({ port: 4001 }, ...)` — the client connects; `c1.localPort` shows the ephemeral source port the OS assigned for this specific connection.
- Two separate calls to `net.createConnection` get two different ephemeral ports (54891 vs. 54892) even though both come from the same machine — this is how the OS and the remote server tell the connections apart.
- `server1.close(); server2.close()` — releases the bound ports so the OS can reuse them. Without this, the ports remain in `TIME_WAIT` state briefly.

## 7. Gotchas & takeaways

> **Ports below 1024 require root/admin on Linux/macOS.** Running a web server on port 80 directly needs `sudo`. In production, the common approach is to run your app on port 3000 and use a reverse proxy (nginx, Caddy) that listens on 80/443 as root and forwards traffic.

> **`EADDRINUSE` means the port is already taken.** Kill the process using it (`lsof -i :3000 | grep LISTEN`, then `kill <pid>`) or pick a different port.

- Firewalls filter by port: a cloud server default security group typically blocks everything except port 22 (SSH) and 80/443 (web).
- `localhost:3000` = `127.0.0.1:3000` = "my machine, port 3000" — no network packet ever leaves the machine.
- `0.0.0.0` as the bind address means "all interfaces" — required if you want the server reachable from outside the machine, not just localhost.
- Docker `-p 8080:80` maps host port 8080 to the container's internal port 80 — you hit `localhost:8080` outside, which routes to `:80` inside.
- `netstat -an | grep LISTEN` or `ss -tlnp` shows all listening ports on your machine.
