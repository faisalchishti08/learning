---
card: java
gi: 636
slug: http-2-support
title: HTTP/2 support
---

## 1. What it is

Java 11's `HttpClient` natively supports **HTTP/2** (RFC 7540), the binary-framed successor to HTTP/1.1. By default, the client negotiates the protocol version automatically: it attempts HTTP/2 first via TLS-ALPN (Application-Layer Protocol Negotiation), falling back to HTTP/1.1 if the server doesn't support it. HTTP/2 brings multiplexing (multiple concurrent streams over one TCP connection), header compression (HPACK), server push, and stream prioritisation — all handled transparently by the JDK. You can also force a specific version via `HttpClient.newBuilder().version(HttpClient.Version.HTTP_2)` or `.HTTP_1_1`.

## 2. Why & when

HTTP/1.1's head-of-line blocking means a slow request can delay all subsequent requests on the same connection. HTTP/2 solves this with multiplexed streams: multiple requests and responses interleave over a single TCP connection without blocking each other. This is especially valuable in microservice architectures where a service makes many outbound HTTP calls. Use HTTP/2 when your infrastructure supports it (most modern servers, CDNs, and load balancers do). The JDK client handles the complexity — you write the same `HttpRequest`/`HttpResponse` code regardless of protocol version. The performance benefit is most noticeable with many concurrent requests to the same host.

## 3. Core concept

```java
// Default: auto-negotiate (HTTP/2 preferred, fallback to HTTP/1.1)
HttpClient client = HttpClient.newHttpClient();
// The client will use HTTP/2 if the server supports it

// Force HTTP/2 (throws if server doesn't support it)
HttpClient h2Client = HttpClient.newBuilder()
    .version(HttpClient.Version.HTTP_2)
    .build();

// Force HTTP/1.1
HttpClient h1Client = HttpClient.newBuilder()
    .version(HttpClient.Version.HTTP_1_1)
    .build();

// Check what version was used for a response
HttpResponse<String> resp = client.send(request, BodyHandlers.ofString());
System.out.println(resp.version());  // HTTP_1_1 or HTTP_2
```

HTTP/2 is transparent to your code — the same API works for both protocols. The version is negotiated at connection time and available on the `HttpResponse`.

## 4. Diagram

<svg viewBox="0 0 560 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTTP/2 multiplexes multiple streams over a single TCP connection">
  <rect x="10" y="10" width="540" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="100" height="50" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="70" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Client</text>

  <text x="135" y="55" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">←→</text>

  <rect x="160" y="15" width="220" height="70" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="270" y="32" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">Single TCP Connection</text>
  <rect x="175" y="40" width="60" height="15" rx="2" fill="#3fb950"/>
  <text x="205" y="51" fill="#0d1117" font-size="7" text-anchor="middle" font-family="monospace">Stream 1</text>
  <rect x="240" y="40" width="60" height="15" rx="2" fill="#79c0ff"/>
  <text x="270" y="51" fill="#0d1117" font-size="7" text-anchor="middle" font-family="monospace">Stream 2</text>
  <rect x="305" y="40" width="60" height="15" rx="2" fill="#f0883e"/>
  <text x="335" y="51" fill="#0d1117" font-size="7" text-anchor="middle" font-family="monospace">Stream 3</text>
  <text x="270" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Multiplexed — no head-of-line blocking</text>

  <text x="395" y="55" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">←→</text>

  <rect x="410" y="25" width="100" height="50" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="460" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Server</text>

  <text x="20" y="115" fill="#8b949e" font-size="9" font-family="sans-serif">HTTP/1.1: 1 request per connection (or pipelined, often blocked)  |  HTTP/2: many concurrent streams per connection</text>
  <text x="20" y="133" fill="#3fb950" font-size="9" font-family="sans-serif">JDK client handles TLS-ALPN negotiation, HPACK compression, and stream multiplexing automatically</text>
</svg>

HTTP/2 multiplexes multiple concurrent requests and responses over a single TCP connection, eliminating head-of-line blocking and reducing connection overhead.

## 5. Runnable example

Scenario: demonstrating the difference between HTTP/1.1 and HTTP/2 by sending multiple concurrent requests and inspecting protocol versions — starting with basic version detection, extending to concurrent request comparison, and finally handling version-specific behaviour.

### Level 1 — Basic

```java
// File: Http2Demo.java
import java.net.*;
import java.net.http.*;

public class Http2Demo {
    public static void main(String[] args) throws Exception {
        // Client with auto-negotiation
        HttpClient client = HttpClient.newHttpClient();

        // Test different servers for HTTP/2 support
        String[] urls = {
            "https://httpbin.org/get",        // httpbin uses HTTP/1.1
            "https://www.google.com/",        // Google supports HTTP/2
            "https://http2.golang.org/reqinfo" // Known HTTP/2 test server
        };

        System.out.println("=== Protocol version detection ===\n");

        for (String urlStr : urls) {
            try {
                HttpRequest req = HttpRequest.newBuilder()
                    .uri(URI.create(urlStr))
                    .GET().build();
                HttpResponse<String> resp = client.send(req,
                    HttpResponse.BodyHandlers.ofString());
                System.out.printf("%-40s → %s (%d)%n",
                    urlStr, resp.version(), resp.statusCode());
            } catch (Exception e) {
                System.out.printf("%-40s → ERROR: %s%n",
                    urlStr, e.getMessage());
            }
        }
    }
}
```

**How to run:** `java Http2Demo.java`

Expected output:
```
=== Protocol version detection ===

https://httpbin.org/get                  → HTTP_1_1 (200)
https://www.google.com/                  → HTTP_2 (200)
https://http2.golang.org/reqinfo         → HTTP_2 (200)
```

The simplest demonstration: different servers support different protocol versions. The JDK client handles the negotiation transparently — your code doesn't change.

### Level 2 — Intermediate

```java
// File: Http2Concurrent.java
import java.net.*;
import java.net.http.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class Http2Concurrent {
    public static void main(String[] args) throws Exception {
        // Force HTTP/2 (will work only with HTTP/2 servers)
        HttpClient h2Client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_2)
            .build();

        // Force HTTP/1.1
        HttpClient h1Client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();

        // Make 10 concurrent requests to an HTTP/2-capable server
        int numRequests = 10;
        String testUrl = "https://www.google.com/";

        System.out.println("=== HTTP/2: " + numRequests + " concurrent requests ===");
        long start = System.currentTimeMillis();

        List<CompletableFuture<HttpResponse<Void>>> futures = IntStream.range(0, numRequests)
            .mapToObj(i -> HttpRequest.newBuilder()
                .uri(URI.create(testUrl))
                .GET().build())
            .map(req -> h2Client.sendAsync(req, HttpResponse.BodyHandlers.discarding()))
            .toList();

        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        long h2Time = System.currentTimeMillis() - start;

        long h2Streams = futures.stream()
            .map(CompletableFuture::join)
            .filter(r -> r.version() == HttpClient.Version.HTTP_2)
            .count();

        System.out.println("Time: " + h2Time + " ms");
        System.out.println("HTTP/2 streams confirmed: " + h2Streams + "/" + numRequests);
        System.out.println("(HTTP/2 multiplexes streams over 1 connection — faster)");

        // Clean comparison with HTTP/1.1
        System.out.println("\n=== HTTP/1.1: " + numRequests + " concurrent requests ===");
        start = System.currentTimeMillis();

        futures = IntStream.range(0, numRequests)
            .mapToObj(i -> HttpRequest.newBuilder()
                .uri(URI.create(testUrl))
                .GET().build())
            .map(req -> h1Client.sendAsync(req, HttpResponse.BodyHandlers.discarding()))
            .toList();

        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        long h1Time = System.currentTimeMillis() - start;

        System.out.println("Time: " + h1Time + " ms");
    }
}
```

**How to run:** `java Http2Concurrent.java`

Expected output:
```
=== HTTP/2: 10 concurrent requests ===
Time: ~500 ms
HTTP/2 streams confirmed: 10/10
(HTTP/2 multiplexes streams over 1 connection — faster)

=== HTTP/1.1: 10 concurrent requests ===
Time: ~1500 ms
```

The real-world concern: concurrent request throughput. HTTP/2 multiplexes all 10 streams over one TCP connection, significantly reducing total time compared to HTTP/1.1 which requires multiple connections (or suffers head-of-line blocking). The benefit grows with request count.

### Level 3 — Advanced

```java
// File: Http2Advanced.java
import java.net.*;
import java.net.http.*;
import java.util.*;

public class Http2Advanced {
    public static void main(String[] args) throws Exception {
        System.out.println("=== HTTP/2 features ===\n");

        // SSL context — HTTP/2 requires TLS in practice
        // (The JDK client supports h2c — HTTP/2 over cleartext — but most servers don't)

        HttpClient client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_2)
            .build();

        System.out.println("Client preferred version: " + client.version());
        System.out.println("(HTTP_2 — will negotiate down if server doesn't support it)\n");

        // 1. Check if a server supports HTTP/2
        System.out.println("--- Testing HTTP/2 support ---");
        testHttp2("https://www.google.com/");
        testHttp2("https://httpbin.org/get");

        // 2. HTTP/2 with custom settings
        System.out.println("\n--- HTTP/2 specific behaviour ---");

        // HTTP/2 push (server can push resources before client requests)
        // Note: JDK client receives pushes but discards them by default in Java 11.
        // You need a custom PushPromiseHandler to handle them.

        System.out.println("HTTP/2 server push: supported by protocol but requires");
        System.out.println("custom PushPromiseHandler in JDK client (advanced topic).");

        // 3. HTTP/2 connection reuse
        System.out.println("\n--- Connection management ---");
        System.out.println("HTTP/2 client automatically:");
        System.out.println("  - Multiplexes streams over 1 connection per origin");
        System.out.println("  - Handles HPACK header compression");
        System.out.println("  - Manages stream flow control (WINDOW_UPDATE)");
        System.out.println("  - Gracefully handles GOAWAY frames for connection shutdown");
        System.out.println("(All handled transparently — no code changes needed)");

        // 4. Fallback behaviour
        System.out.println("\n--- Forced HTTP/2 fallback ---");
        try {
            HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create("https://httpbin.org/get"))  // HTTP/1.1 only
                .GET().build();

            // Client with HTTP_2 preferred will auto-fallback
            HttpResponse<String> resp = client.send(req,
                HttpResponse.BodyHandlers.ofString());
            System.out.println("Result: " + resp.version() +
                " (auto-negotiated down to HTTP/1.1)");
        } catch (Exception e) {
            System.out.println("Error: " + e.getMessage());
        }
    }

    static void testHttp2(String urlStr) {
        try {
            HttpClient client = HttpClient.newHttpClient();
            HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(urlStr)).GET().build();
            HttpResponse<Void> resp = client.send(req,
                HttpResponse.BodyHandlers.discarding());
            System.out.printf("  %-30s → %-8s (%d)%n",
                urlStr, resp.version(), resp.statusCode());
        } catch (Exception e) {
            System.out.printf("  %-30s → ERROR%n", urlStr);
        }
    }
}
```

**How to run:** `java Http2Advanced.java`

Expected output:
```
=== HTTP/2 features ===

Client preferred version: HTTP_2
(HTTP_2 — will negotiate down if server doesn't support it)

--- Testing HTTP/2 support ---
  https://www.google.com/        → HTTP_2   (200)
  https://httpbin.org/get        → HTTP_1_1 (200)

--- HTTP/2 specific behaviour ---
HTTP/2 server push: supported by protocol but requires
custom PushPromiseHandler in JDK client (advanced topic).

--- Connection management ---
HTTP/2 client automatically:
  - Multiplexes streams over 1 connection per origin
  - Handles HPACK header compression
  - Manages stream flow control (WINDOW_UPDATE)
  - Gracefully handles GOAWAY frames for connection shutdown
(All handled transparently — no code changes needed)

--- Forced HTTP/2 fallback ---
Result: HTTP_1_1 (auto-negotiated down to HTTP/1.1)
```

The production-flavoured hard cases: (1) **Auto-negotiation** — the default client prefers HTTP/2 but silently falls back to HTTP/1.1. Check `response.version()` to confirm what was negotiated. (2) **Server push** — HTTP/2 push is supported at the protocol level but requires a custom `PushPromiseHandler` in the JDK client (the default handler discards pushes). (3) **Connection reuse** — HTTP/2 automatically reuses connections and multiplexes streams. You don't manage connections manually. (4) **TLS requirement** — in practice, HTTP/2 requires TLS. The JDK client supports cleartext HTTP/2 (h2c) but almost no public server does.

## 6. Walkthrough

Tracing HTTP/2 negotiation in a default `HttpClient`:

1. `HttpClient.newHttpClient()` creates a client with `version = HTTP_2` (preferred, not required).

2. A request is sent to `https://www.google.com/`:
   - The client opens a TCP connection to Google's IP on port 443.
   - The TLS handshake begins. In the `ClientHello` message, the TLS-ALPN extension advertises `h2` (HTTP/2) as the preferred protocol.
   - Google's server responds with `ServerHello` containing ALPN selection `h2` — the server supports HTTP/2.

3. Now HTTP/2 frames flow over the TLS connection:
   - The client sends a `SETTINGS` frame to configure stream concurrency and flow control.
   - The request is sent as `HEADERS` + `DATA` frames on stream ID 1.
   - The server responds with `HEADERS` + `DATA` frames on the same stream.
   - HPACK compresses headers (e.g. `:method: GET`, `:path: /`, `user-agent: ...`).

4. `HttpResponse.version()` returns `HTTP_2`.

5. Additional concurrent requests to the same origin reuse the existing connection on new stream IDs (3, 5, 7, ...).

If the server had NOT supported HTTP/2, the ALPN negotiation would select `http/1.1`, and the client would silently fall back to HTTP/1.1 wire format. The `HttpResponse.version()` would show `HTTP_1_1`.

## 7. Gotchas & takeaways

> Forcing `HTTP_2` via `.version(HttpClient.Version.HTTP_2)` means the client **will fail** if the server doesn't support HTTP/2. The default (auto-negotiate) is safer for general-purpose clients. Only force a version when you control both ends or have verified server support.

- HTTP/2 is transparent to your `HttpRequest`/`HttpResponse` code — you write the same API calls regardless of protocol. The version is available for introspection via `response.version()`.
- HTTP/2 requires TLS in practice. While the specification defines cleartext HTTP/2 (h2c), no major public server enables it. All HTTP/2 connections go over HTTPS.
- The client handles HPACK header compression, stream multiplexing, flow control, and connection management automatically. You don't set window sizes or prioritise streams — the JDK provides sensible defaults.
- HTTP/2 server push is supported at the protocol level but requires opt-in via `PushPromiseHandler`. Pushes received without a handler are discarded (no error). This is intentional — most applications don't need server push.
- Connection pooling works across HTTP/2: the client maintains one multiplexed connection per origin (host:port). All concurrent requests to the same origin share this connection.
