---
card: java
gi: 637
slug: websocket-support
title: WebSocket support
---

## 1. What it is

Java 11's `HttpClient` includes a built-in **WebSocket client** via `HttpClient.newWebSocketBuilder()`. WebSocket (RFC 6455) is a protocol that upgrades an HTTP connection to a full-duplex, persistent TCP connection where both client and server can send messages at any time — no request/response pairing required. The JDK's `WebSocket` interface provides methods for sending text and binary messages (`sendText`, `sendBinary`), sending ping/pong frames for keep-alive, and registering a `Listener` to receive incoming messages, close notifications, and errors. The API is asynchronous and non-blocking: sends return `CompletableFuture<WebSocket>` and receives come through listener callbacks.

## 2. Why & when

Standard HTTP request/response is half-duplex and client-initiated — the server cannot push data. For real-time applications (chat, live scores, collaborative editing, stock tickers), WebSocket provides a persistent bidirectional channel with low overhead. Before Java 11, JDK developers had to use third-party libraries (Tyrus, Jetty WebSocket, Netty) or the cumbersome `java.net.Socket` directly. The JDK WebSocket client integrates with the same `HttpClient` infrastructure (connection pool, SSL, proxy) and works with any standard WebSocket server. Use it for real-time client applications in Java; for server-side WebSocket, use Jakarta WebSocket (formerly JSR 356) or Spring WebSocket.

## 3. Core concept

```java
HttpClient client = HttpClient.newHttpClient();

// Build a WebSocket connection
WebSocket ws = client.newWebSocketBuilder()
    .buildAsync(URI.create("wss://echo.websocket.org"), listener)
    .join();  // wait for connection

// Send a message (returns CompletableFuture)
ws.sendText("Hello, WebSocket!", true);  // true = isLast

// The listener receives messages asynchronously
// When done:
ws.sendClose(WebSocket.NORMAL_CLOSURE, "done");
```

The `Listener` interface has callbacks: `onText(webSocket, data, last)`, `onBinary(webSocket, data, last)`, `onOpen(webSocket)`, `onClose(webSocket, statusCode, reason)`, `onError(webSocket, error)`. All callbacks are invoked sequentially (never concurrently) for a given `WebSocket` instance.

## 4. Diagram

<svg viewBox="0 0 560 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WebSocket upgrades HTTP to a persistent bidirectional connection">
  <rect x="10" y="10" width="540" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="110" height="50" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="75" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">Client</text>

  <line x1="135" y1="50" x2="415" y2="50" stroke="#3fb950" stroke-width="2"/>
  <line x1="415" y1="60" x2="135" y2="60" stroke="#79c0ff" stroke-width="2"/>

  <text x="275" y="42" fill="#3fb950" font-size="9" text-anchor="middle" font-family="monospace">sendText("Hello")</text>
  <text x="275" y="71" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">onText("Echo: Hello")</text>

  <rect x="420" y="25" width="110" height="50" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="475" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">Server</text>

  <text x="275" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Full-duplex — both sides can send at any time</text>
  <text x="20" y="120" fill="#8b949e" font-size="9" font-family="sans-serif">Upgrade: HTTP Upgrade header → 101 Switching Protocols → persistent WebSocket connection</text>
  <text x="20" y="138" fill="#3fb950" font-size="9" font-family="sans-serif">Builder: newWebSocketBuilder() → .header() → .connectTimeout() → .buildAsync(uri, listener)</text>
</svg>

WebSocket starts as an HTTP upgrade request, then becomes a persistent bidirectional channel. Both sides send messages independently; the `Listener` receives them asynchronously.

## 5. Runnable example

Scenario: connecting to a public WebSocket echo server to demonstrate bidirectional messaging — starting with basic connect/send/receive, extending to a chat-like interaction loop, and finally handling connection lifecycle.

### Level 1 — Basic

```java
// File: WebSocketDemo.java
import java.net.*;
import java.net.http.*;
import java.util.concurrent.*;

public class WebSocketDemo {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();

        // Simple listener that prints received messages
        WebSocket.Listener listener = new WebSocket.Listener() {
            @Override
            public CompletionStage<?> onText(WebSocket webSocket,
                    CharSequence data, boolean last) {
                System.out.println("Received: " + data);
                return null;  // no further action
            }

            @Override
            public void onOpen(WebSocket webSocket) {
                System.out.println("Connected!");
                // Send a message once connected
                webSocket.sendText("Hello, WebSocket!", true);
            }

            @Override
            public CompletionStage<?> onClose(WebSocket webSocket,
                    int statusCode, String reason) {
                System.out.println("Closed: " + statusCode + " " + reason);
                return null;
            }

            @Override
            public void onError(WebSocket webSocket, Throwable error) {
                System.out.println("Error: " + error.getMessage());
            }
        };

        // Connect to a public WebSocket echo server
        System.out.println("Connecting to echo server...");
        WebSocket ws = client.newWebSocketBuilder()
            .buildAsync(URI.create("wss://ws.postman-echo.com/raw"), listener)
            .join();  // wait for connection

        // Keep alive for a few seconds to receive the echo
        Thread.sleep(2000);

        // Close gracefully
        ws.sendClose(WebSocket.NORMAL_CLOSURE, "done")
            .join();
        System.out.println("Done.");
    }
}
```

**How to run:** `java WebSocketDemo.java`

Expected output:
```
Connecting to echo server...
Connected!
Received: Hello, WebSocket!
Closed: 1000 done
Done.
```

The simplest usage: connect to an echo server, send a message, receive the echo back, and close. The `Listener` callbacks handle the asynchronous events. Note that public WebSocket test servers may change — alternatives include `wss://echo.websocket.org` or a local server.

### Level 2 — Intermediate

```java
// File: ChatSimulator.java
import java.net.*;
import java.net.http.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ChatSimulator {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        CountDownLatch latch = new CountDownLatch(3);  // wait for 3 messages
        AtomicInteger msgCount = new AtomicInteger(0);

        WebSocket.Listener listener = new WebSocket.Listener() {
            @Override
            public void onOpen(WebSocket webSocket) {
                System.out.println("[Connected to chat server]");
                // Send a sequence of messages
                sendDelayed(webSocket, "Hello everyone!", 0);
                sendDelayed(webSocket, "How is it going?", 500);
                sendDelayed(webSocket, "Great weather today!", 1000);
            }

            @Override
            public CompletionStage<?> onText(WebSocket webSocket,
                    CharSequence data, boolean last) {
                int n = msgCount.incrementAndGet();
                System.out.println("  ← Server: " + data);
                latch.countDown();
                return null;
            }

            @Override
            public CompletionStage<?> onClose(WebSocket webSocket,
                    int statusCode, String reason) {
                System.out.println("[Disconnected: " + statusCode + " " + reason + "]");
                return null;
            }

            @Override
            public void onError(WebSocket webSocket, Throwable error) {
                System.err.println("[Error: " + error.getMessage() + "]");
                latch.countDown();  // don't hang on error
            }
        };

        WebSocket ws = client.newWebSocketBuilder()
            .buildAsync(URI.create("wss://ws.postman-echo.com/raw"), listener)
            .join();

        // Wait for messages or timeout
        if (!latch.await(10, TimeUnit.SECONDS)) {
            System.out.println("(timeout waiting for messages)");
        }

        ws.sendClose(WebSocket.NORMAL_CLOSURE, "bye").join();
    }

    static void sendDelayed(WebSocket ws, String msg, long delayMs) {
        CompletableFuture.delayedExecutor(delayMs, TimeUnit.MILLISECONDS)
            .execute(() -> {
                System.out.println("  → Client: " + msg);
                ws.sendText(msg, true);
            });
    }
}
```

**How to run:** `java ChatSimulator.java`

Expected output:
```
[Connected to chat server]
  → Client: Hello everyone!
  ← Server: Hello everyone!
  → Client: How is it going?
  ← Server: How is it going?
  → Client: Great weather today!
  ← Server: Great weather today!
[Disconnected: 1000 bye]
```

The real-world concern: bidirectional messaging at independent intervals. Messages are sent with staggered delays; responses arrive asynchronously. The `CountDownLatch` coordinates the main thread with the async listener callbacks — a common pattern for test/simulation code. In production, you'd use a more reactive approach.

### Level 3 — Advanced

```java
// File: WebSocketAdvanced.java
import java.net.*;
import java.net.http.*;
import java.nio.*;
import java.util.concurrent.*;

public class WebSocketAdvanced {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newBuilder()
            .connectTimeout(java.time.Duration.ofSeconds(10))
            .build();

        System.out.println("=== Connection lifecycle ===\n");

        CompletableFuture<WebSocket> future = client.newWebSocketBuilder()
            .header("User-Agent", "Java11-WebSocket-Demo")
            .connectTimeout(java.time.Duration.ofSeconds(5))
            .buildAsync(URI.create("wss://ws.postman-echo.com/raw"),
                new WebSocket.Listener() {
                    @Override
                    public void onOpen(WebSocket webSocket) {
                        System.out.println("1. onOpen — connection established");

                        // Send text message
                        webSocket.sendText("Text message", true);

                        // Send binary message
                        byte[] binaryData = {0x01, 0x02, 0x03, 0x04};
                        webSocket.sendBinary(ByteBuffer.wrap(binaryData), true);

                        // Send ping (keep-alive)
                        webSocket.sendPing(ByteBuffer.wrap("ping".getBytes()));

                        System.out.println("   Sent: text, binary, and ping");
                    }

                    @Override
                    public CompletionStage<?> onText(WebSocket webSocket,
                            CharSequence data, boolean last) {
                        System.out.println("2. onText — received: " + data);

                        // Send a response based on received data
                        webSocket.sendText("ACK: " + data, true);

                        // After first text message, initiate close
                        webSocket.sendClose(WebSocket.NORMAL_CLOSURE, "demo complete");
                        return null;
                    }

                    @Override
                    public CompletionStage<?> onBinary(WebSocket webSocket,
                            ByteBuffer data, boolean last) {
                        byte[] bytes = new byte[data.remaining()];
                        data.get(bytes);
                        System.out.println("3. onBinary — received " + bytes.length + " bytes");
                        return null;
                    }

                    @Override
                    public CompletionStage<?> onPing(WebSocket webSocket,
                            ByteBuffer message) {
                        System.out.println("   onPing — received ping, pong sent automatically");
                        return null;  // JDK sends pong automatically
                    }

                    @Override
                    public CompletionStage<?> onPong(WebSocket webSocket,
                            ByteBuffer message) {
                        System.out.println("   onPong — received pong");
                        return null;
                    }

                    @Override
                    public CompletionStage<?> onClose(WebSocket webSocket,
                            int statusCode, String reason) {
                        System.out.println("4. onClose — status=" + statusCode +
                            " reason=\"" + reason + "\"");
                        return null;
                    }

                    @Override
                    public void onError(WebSocket webSocket, Throwable error) {
                        System.err.println("X. onError — " + error.getMessage());
                    }
                });

        // Wait for connection and then for close
        WebSocket ws = future.join();
        System.out.println("\nWaiting for close...");

        // The listener will initiate close; wait a bit for it to complete
        Thread.sleep(3000);

        if (!ws.isOutputClosed()) {
            ws.sendClose(WebSocket.NORMAL_CLOSURE, "force close").join();
        }

        System.out.println("\n=== WebSocket close codes ===\n");
        System.out.println("NORMAL_CLOSURE (1000)  — graceful close");
        System.out.println("GOING_AWAY (1001)      — endpoint going away");
        System.out.println("PROTOCOL_ERROR (1002)  — protocol error");
        System.out.println("(Use NORMAL_CLOSURE for clean shutdown)");
    }
}
```

**How to run:** `java WebSocketAdvanced.java`

Expected output:
```
=== Connection lifecycle ===

1. onOpen — connection established
   Sent: text, binary, and ping
2. onText — received: Text message
4. onClose — status=1000 reason="demo complete"

Waiting for close...

=== WebSocket close codes ===

NORMAL_CLOSURE (1000)  — graceful close
GOING_AWAY (1001)      — endpoint going away
PROTOCOL_ERROR (1002)  — protocol error
(Use NORMAL_CLOSURE for clean shutdown)
```

The production-flavoured hard cases: (1) **Complete lifecycle** — `onOpen` → `onText`/`onBinary` → `onClose` (or `onError`). The `onClose` callback fires even if the remote side initiates closure. (2) **Ping/Pong** — `sendPing()` for keep-alive; `onPong` receives responses. The JDK automatically responds to incoming pings with pongs. (3) **Binary messages** — `sendBinary(ByteBuffer, last)` sends raw bytes; `onBinary` receives them. (4) **Cumulative messages** — the `last` boolean parameter indicates whether the received frame is the final fragment. For complete messages, `last` is `true`.

## 6. Walkthrough

Tracing a WebSocket connection from open to close:

1. **Build and connect:** `client.newWebSocketBuilder().buildAsync(uri, listener)` sends an HTTP upgrade request:
   ```
   GET /raw HTTP/1.1
   Host: ws.postman-echo.com
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Key: ...
   Sec-WebSocket-Version: 13
   ```
   The server responds with `101 Switching Protocols`. The TCP connection is now a WebSocket. `listener.onOpen(webSocket)` is called.

2. **Send text:** `webSocket.sendText("Hello", true)` serialises the text as a WebSocket text frame (opcode 0x1), masks it with a random 4-byte key, and writes it to the socket. Returns `CompletableFuture<WebSocket>` that completes when the frame is written (not when the server receives it).

3. **Receive text:** The server echoes back a text frame. The JDK client reads the frame, unmaskes it, and calls `listener.onText(webSocket, "Hello", true)`. The `last=true` parameter indicates a complete (non-fragmented) message.

4. **Send close:** `webSocket.sendClose(1000, "done")` sends a close frame with status code 1000 (normal). The server responds with its own close frame. The underlying TCP connection closes. `listener.onClose(webSocket, 1000, "done")` is called.

5. **Data state:** At each stage, the `WebSocket` instance tracks its state (connecting → open → closing → closed). Sending after close initiation queues messages (they may or may not be delivered depending on timing). After `onClose`, no more messages can be sent.

## 7. Gotchas & takeaways

> The `Listener` callbacks are invoked **sequentially** for a given `WebSocket` — never concurrently. This means you don't need synchronisation in your listener. However, callbacks should return quickly; long-running work in `onText` delays subsequent messages.

- `buildAsync()` returns `CompletableFuture<WebSocket>` — the connection is established asynchronously. Calling `.join()` blocks until the connection is open. For non-blocking usage, chain `.thenAccept()`.
- WebSocket messages can be **fragmented**: the `last` parameter in `onText`/`onBinary` is `true` for the final fragment. For most simple use cases, messages arrive complete (`last=true`). For large messages, accumulate fragments until `last` is `true`.
- The JDK WebSocket client supports text (always UTF-8), binary (opaque bytes), ping/pong (keep-alive), and close frames. It does NOT support WebSocket extensions (permessage-deflate, etc.) in Java 11.
- `sendText`/`sendBinary` return `CompletableFuture<WebSocket>`. The future completes when the frame is written to the socket buffer, not when the server acknowledges it. This means "fire and forget" is natural; for request-response patterns, correlate responses in your listener logic.
- WebSocket URIs use `ws://` (unencrypted) or `wss://` (TLS-encrypted). In practice, almost all production WebSocket connections use `wss://`.
