---
card: webdev
gi: 30
slug: latency-bandwidth-round-trip-time-rtt
title: Latency, bandwidth & round-trip time (RTT)
---

## 1. What it is

Three numbers dominate network performance conversations:

- **Latency** — the delay between sending a byte and it arriving at the destination. Measured in milliseconds (ms). Caused by the physical distance the signal travels, the number of hops through routers, and queuing inside those routers.
- **Bandwidth** — the maximum amount of data that can flow through a link per unit of time. Measured in bits per second (Mbps, Gbps). Think of it as the width of a pipe.
- **Round-trip time (RTT)** — the time for a message to travel from sender to receiver and for the acknowledgement to return. RTT = two one-way latencies. It's the number you see when you `ping` something.

These are independent: a satellite link has enormous bandwidth (hundreds of Mbps) but terrible latency (~600 ms RTT). A fast home fibre line might have 1 Gbps bandwidth with 5 ms RTT. Slow 3G has both low bandwidth and high latency.

## 2. Why & when

Web performance is dominated by **latency, not bandwidth**, for most pages. An HTML page that requires 10 serial round trips (HTML → discovers CSS → downloads CSS → discovers JS → downloads JS …) burns 10 × RTT before the page is visible. On a 100 ms RTT link (cross-continental), that's 1 second of pure waiting, regardless of how fast the bytes travel once the pipe is open.

Bandwidth matters for large transfers — video streams, big file downloads, image-heavy pages — where the pipe capacity limits throughput. But for typical web interactions (API calls, page loads), halving the file sizes matters far less than eliminating a round trip.

Understanding these numbers helps you:
- Explain why mobile users in rural areas have slow sites even on "fast" connections (high RTT).
- Choose between HTTP/1.1 (serial) vs HTTP/2 (multiplexed, fewer RTTs).
- Justify using a CDN (it cuts RTT by moving the server closer).
- Diagnose whether a slow API is compute-bound or latency-bound.

## 3. Core concept

Bandwidth vs latency: imagine sending a lorry of hard drives across the country versus emailing a text file. The lorry has enormous bandwidth (petabytes of data) but terrible latency (2 days). Email has low bandwidth (kilobytes per second) but near-instant latency. For a 1 KB API response, you want email, not a lorry.

**RTT and protocol costs:**

Every request-response pair costs 1 RTT minimum. But TLS and TCP add overhead:

- TCP three-way handshake: 1 RTT before any data flows.
- TLS 1.3 handshake: 1 more RTT.
- HTTP request: 1 RTT.
- **Total for first HTTPS request over a new connection: 3 RTTs.**

On a 100 ms RTT link, that's 300 ms before you see byte one of the response. HTTP/2 and HTTP/3 reduce this by keeping connections alive and multiplexing many requests over one connection, collapsing subsequent requests to 0 extra RTTs after the connection is established.

**Bandwidth-delay product:** the amount of data "in flight" at any moment = bandwidth × RTT. On a 1 Gbps link with 100 ms RTT, 100 Mb of data is in transit simultaneously. TCP's congestion control uses this to size its window. Long fat networks (high BDP) need tuning.

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Latency vs bandwidth: narrow fast pipe versus wide slow pipe; RTT shown as round-trip arrow">
  <defs>
    <marker id="la" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="lb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <!-- Bandwidth label -->
  <text x="20" y="25" fill="#e6edf3" font-size="12" font-family="sans-serif" font-weight="bold">Bandwidth = pipe width</text>
  <!-- Narrow pipe (low BW) -->
  <rect x="20" y="40" width="260" height="16" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="290" y="53" fill="#8b949e" font-size="10" font-family="sans-serif">narrow (low bandwidth)</text>
  <!-- Wide pipe (high BW) -->
  <rect x="20" y="65" width="260" height="36" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="290" y="88" fill="#6db33f" font-size="10" font-family="sans-serif">wide (high bandwidth)</text>

  <!-- Divider -->
  <line x1="20" y1="120" x2="660" y2="120" stroke="#8b949e" stroke-width="0.5" stroke-dasharray="4,4"/>

  <!-- RTT diagram -->
  <text x="20" y="145" fill="#e6edf3" font-size="12" font-family="sans-serif" font-weight="bold">RTT = request + response time</text>
  <!-- Client -->
  <rect x="30" y="160" width="80" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="183" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>
  <!-- Server -->
  <rect x="560" y="160" width="90" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="605" y="183" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server</text>
  <!-- request arrow -->
  <line x1="110" y1="170" x2="558" y2="170" stroke="#6db33f" stroke-width="1.8" marker-end="url(#la)"/>
  <text x="335" y="163" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">request →   one-way latency</text>
  <!-- response arrow -->
  <line x1="560" y1="188" x2="112" y2="188" stroke="#79c0ff" stroke-width="1.8" marker-end="url(#lb)"/>
  <text x="335" y="207" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">← response   one-way latency</text>
  <!-- RTT brace label -->
  <text x="335" y="228" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">RTT = both arrows combined</text>
</svg>

Bandwidth is the pipe's width; latency is how long each byte takes to travel; RTT is the full round-trip delay.

## 5. Runnable example

Measure RTT and approximate bandwidth to a server using standard tools — no installs on macOS/Linux.

```bash
# 1. Measure RTT via ping (sends ICMP echo, measures round-trip ms)
echo "=== RTT to Google DNS ==="
ping -c 5 8.8.8.8

echo ""
# 2. Measure download bandwidth (fetch 10 MB from a speed-test server)
echo "=== Bandwidth test (10 MB download) ==="
time curl -so /dev/null \
  -w "Downloaded %{size_download} bytes in %{time_total}s  =  %{speed_download} bytes/s\n" \
  "https://speed.cloudflare.com/__down?bytes=10000000"

echo ""
# 3. Count HTTP round trips for a real page load (protocol negotiation)
echo "=== RTTs visible in TLS + HTTP connect ==="
curl -v -o /dev/null https://example.com 2>&1 \
  | grep -E "Connected|TLSv1|HTTP/" | head -10
```

**How to run:** paste into any macOS or Linux terminal with internet access. On some firewalls `ping` is blocked — skip step 1 if it times out.

## 6. Walkthrough

- `ping -c 5 8.8.8.8` sends 5 ICMP packets and measures the round-trip time for each. The `avg` at the end is your RTT to that host. Values under 20 ms = same region; 50–100 ms = cross-country; 150–300 ms = cross-continent; 500+ ms = satellite.
- `curl -w "...%{speed_download}..."` — curl's `-w` flag supports variables. `speed_download` is bytes/second averaged over the transfer. Multiply by 8 to get bits/second (Mbps = result / 125000).
- `size_download` is the total bytes received, confirming we got the full 10 MB.
- `time_total` in the bandwidth test includes TLS handshake + download. On a fast connection this will be sub-second; on a slow connection it saturates the pipe.
- The `-v` curl shows the TCP connect time implicitly via the `Connected to` line, and then TLS version lines show the handshake completing — each exchange is one RTT.
- Compare the RTT you measured in step 1 with the `time_starttransfer` from a curl request to the same server — they should be close (TTFB ≈ RTT + server processing time).

## 7. Gotchas & takeaways

> **High bandwidth does not fix high latency.** A 1 Gbps satellite link with 600 ms RTT will load an HTTP/1.1 page with 10 serial requests in at least 6 seconds — regardless of how fast individual bytes travel. Reducing serial round trips (HTTP/2, resource bundling, preloading) is the fix, not buying more bandwidth.

> **`ping` and HTTP RTT differ.** ICMP packets (ping) get routing priority on some networks; HTTP may be throttled or proxied differently. `ping` gives a lower bound on RTT; actual HTTP RTT is always >= ping RTT.

- RTT ≈ 2× one-way latency (only true if the path is symmetric; satellite and mobile links are often asymmetric).
- Speed tests measure bandwidth to a nearby server — inter-continental bandwidth between your users and your origin may be much lower.
- HTTP/2 multiplexing sends many requests over one connection, collapsing N serial RTTs into 1 connection RTT. Critical for page load performance.
- Server processing time is additive: if your database query takes 200 ms, that's 200 ms on top of RTT. Profile both separately.
- TCP slow start limits throughput at the beginning of large transfers — the first ~14 KB is throttled even on a fast link.
