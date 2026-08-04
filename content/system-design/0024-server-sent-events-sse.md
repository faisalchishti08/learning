---
card: system-design
gi: 24
slug: server-sent-events-sse
title: "Server-Sent Events (SSE)"
---

## 1. What it is

**Server-Sent Events (SSE)** is a protocol that lets a server push a stream of updates to a client over a single, long-lived HTTP connection, using a simple text-based format. Unlike WebSocket, SSE is **one-directional**: the server can push many messages to the client over time, but the client cannot send messages back over that same connection — it is a one-way broadcast channel, not a two-way conversation.

## 2. Why & when

SSE is the right fit when your use case is genuinely one-directional: the server has a stream of updates (stock prices, a live notification feed, progress updates for a long-running job) and the client only needs to receive them, never send data back over the same channel. It is simpler to implement and operate than WebSocket, works over plain HTTP (so it passes through existing infrastructure like proxies and load balancers more easily), and browsers reconnect automatically if the connection drops — all without you writing that reconnection logic yourself.

## 3. Core concept

**How SSE works:** the client opens a normal HTTP request to an endpoint, but the server responds with the header `Content-Type: text/event-stream` and keeps the connection open, sending new lines of text as events happen, rather than closing the response after one reply. Each event is a simple text block:

```
data: {"price": 101.5}

data: {"price": 102.0}

```

Each event is separated by a blank line. The browser's built-in `EventSource` API automatically parses this stream and delivers each `data:` block as an event to your JavaScript code — no manual message-framing logic needed, unlike raw WebSocket.

**SSE vs WebSocket — when to pick which:**

| | SSE | WebSocket |
|---|---|---|
| Direction | Server → client only | Both directions |
| Protocol | Plain HTTP | Upgraded, separate protocol |
| Browser reconnect | Automatic (built into `EventSource`) | Must implement yourself |
| Best fit | Live feeds, notifications, progress updates | Chat, collaborative editing, gaming |

**Why SSE is simpler operationally:** because it is plain HTTP, existing tools that understand HTTP — proxies, load balancers, firewalls — work with it without special handling. WebSocket, being a protocol upgrade, sometimes needs explicit support configured in intermediate infrastructure.

## 4. Diagram

```
 Client                                       Server
   |--GET /events, Accept: text/event-stream-->|
   |<--200 OK, Content-Type: text/event-stream--|
   |<-- data: {"price": 101.5}\n\n---------------|   (pushed, no new request)
   |<-- data: {"price": 102.0}\n\n---------------|   (pushed again)
   |<-- data: {"price": 101.8}\n\n---------------|   (pushed again)
   (client never sends data back over this connection)
```
*Caption: one HTTP response stays open; the server appends new text-formatted events to it over time.*

## 5. Runnable example

### Artifact: a Java simulation of an SSE-style event stream, formatting events the way a real server would

```java
import java.util.*;

public class SseSim {

    static String formatEvent(String jsonData) {
        return "data: " + jsonData + "\n\n";
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Client: GET /events  Accept: text/event-stream");
        System.out.println("Server: 200 OK  Content-Type: text/event-stream");
        System.out.println("=== connection stays open; server streams events below ===");

        List<String> priceUpdates = List.of(
            "{\"price\": 101.5}",
            "{\"price\": 102.0}",
            "{\"price\": 101.8}"
        );

        StringBuilder streamedResponse = new StringBuilder();
        for (String update : priceUpdates) {
            String event = formatEvent(update);
            streamedResponse.append(event);
            System.out.print(event); // simulates the server writing to the still-open response
        }

        System.out.println("Total events streamed on this single connection: " + priceUpdates.size());
    }
}
```

**How to run:** save as `SseSim.java`, run `java SseSim.java` (JDK 17+).

## 6. Walkthrough

1. `formatEvent` wraps a piece of JSON data in the exact `data: ...\n\n` format the SSE protocol requires — a `data:` prefix, followed by two newlines to mark the end of one event.
2. `main` first prints the initial HTTP request and response headers, matching how the connection is established as plain HTTP that simply never closes its response body.
3. `priceUpdates` simulates three price changes happening over time; the loop formats and "streams" each one by printing it, standing in for the server writing new bytes to an already-open HTTP response.
4. Output:
```
Client: GET /events  Accept: text/event-stream
Server: 200 OK  Content-Type: text/event-stream
=== connection stays open; server streams events below ===
data: {"price": 101.5}

data: {"price": 102.0}

data: {"price": 101.8}

Total events streamed on this single connection: 3
```
5. Notice all three events arrive over the exact same single connection that was opened once at the start — the client never made a second request to get the second or third update. This is the core efficiency win SSE offers over polling: one connection, many pushed updates.

## 7. Gotchas & takeaways

> **Gotcha:** reaching for SSE when the client also needs to send frequent messages back to the server. Because SSE has no channel for client-to-server messages, you would need a *separate* regular HTTP request for every client message, adding complexity that a single WebSocket connection avoids entirely.

- SSE is one-directional (server to client only), built on plain HTTP, with automatic browser reconnection.
- Choose SSE for pure push feeds (notifications, live prices, progress updates); choose WebSocket when the client must also send frequent messages back.
- Its plain-HTTP nature makes it easier to deploy through existing infrastructure than a protocol-upgraded WebSocket connection.
