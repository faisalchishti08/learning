---
card: system-design
gi: 23
slug: websocket-full-duplex
title: "WebSocket (full-duplex)"
---

## 1. What it is

**WebSocket** is a communication protocol that opens a single, long-lived connection between client and server, over which both sides can send messages to each other at any time, in either direction, without waiting for a request first. This is called **full-duplex**: unlike normal HTTP, where the client always asks and the server always answers, a WebSocket connection lets the server push a message to the client whenever it wants, and the client can send to the server whenever it wants, independently.

## 2. Why & when

Regular HTTP is request-response: the server can only send data in reply to a client's request. This is a poor fit for anything requiring instant, server-initiated updates — a chat app, live collaborative editing, a live sports score, or real-time trading data. WebSocket is the right choice when you need frequent, low-latency, bidirectional messages after an initial connection, and both client and server need to send messages independently of each other.

## 3. Core concept

**How a WebSocket connection starts:** the client sends a normal HTTP request with an `Upgrade: websocket` header. If the server agrees, it responds with `101 Switching Protocols`, and from that point on, the same underlying TCP connection is reused as a WebSocket connection instead of HTTP — no new connection is opened, but the protocol running over it changes.

**Why full-duplex matters:** once upgraded, either side can send a message frame at any time. The server does not need to wait for the client to ask "anything new?" — it can push new data the instant it exists. This removes the delay and wasted requests that come from a client repeatedly asking a server for updates (see the "long polling vs short polling" tutorial for that pattern's cost).

**The connection stays open, which changes your design:** unlike stateless HTTP requests, a WebSocket connection is a stateful, long-lived resource. Your server must track which clients are connected, and hold state (like which user or session each connection belongs to) for as long as the connection lasts. This has real implications for scaling: if you run many server instances behind a load balancer, a message destined for a specific user must be routed to whichever specific server instance is holding that user's open connection — often solved with a message broker (like Redis pub/sub) that fans a message out to all server instances, so whichever one holds the right connection can deliver it.

## 4. Diagram

```
 Client                                        Server
   |--HTTP GET, Upgrade: websocket------------>|
   |<--101 Switching Protocols-------------------|
   |========= connection now WebSocket ==========|
   |--- message: "hello" ----------------------->|
   |<-- message: "chat update" ------------------|   (server pushes, unprompted)
   |<-- message: "chat update" ------------------|   (server pushes again, unprompted)
   |--- message: "typing..." -------------------->|
```
*Caption: after the HTTP upgrade, both sides send messages independently, at any time, over the same open connection.*

## 5. Runnable example

### Artifact: a Java simulation of a WebSocket-style bidirectional message exchange using an in-memory queue

```java
import java.util.*;
import java.util.concurrent.*;

public class WebSocketSim {

    // Simulates one open, full-duplex connection: two independent message queues.
    static class Connection {
        BlockingQueue<String> toClient = new LinkedBlockingQueue<>();
        BlockingQueue<String> toServer = new LinkedBlockingQueue<>();
    }

    public static void main(String[] args) throws InterruptedException {
        Connection conn = new Connection();

        System.out.println("Client sends HTTP GET with Upgrade: websocket header");
        System.out.println("Server responds 101 Switching Protocols");
        System.out.println("=== connection is now full-duplex ===");

        // Client sends a message to the server.
        conn.toServer.put("hello from client");

        // Server can push messages WITHOUT waiting for a client request first.
        conn.toClient.put("chat update #1");
        conn.toClient.put("chat update #2");

        // Client sends another message, independently of the server's pushes above.
        conn.toServer.put("typing...");

        System.out.println("Messages the server received: " + drain(conn.toServer));
        System.out.println("Messages the client received: " + drain(conn.toClient));
    }

    static List<String> drain(BlockingQueue<String> queue) {
        List<String> all = new ArrayList<>();
        queue.drainTo(all);
        return all;
    }
}
```

**How to run:** save as `WebSocketSim.java`, run `java WebSocketSim.java` (JDK 17+).

## 6. Walkthrough

1. `Connection` models one open WebSocket connection as two independent queues: `toClient` (messages the server pushes to the client) and `toServer` (messages the client sends to the server) — modeling that either side can write at any time, independently of the other.
2. The program first prints the HTTP upgrade handshake steps, matching the diagram above.
3. It then simulates the client sending one message, followed by the server pushing *two* messages in a row — something a plain request-response HTTP call could never do, since the server has no request to reply to for those pushes.
4. The client then sends another message, entirely independent of the server's earlier pushes.
5. `drain` empties each queue into a list so the final contents can be printed. Output:
```
Client sends HTTP GET with Upgrade: websocket header
Server responds 101 Switching Protocols
=== connection is now full-duplex ===
Messages the server received: [hello from client, typing...]
Messages the client received: [chat update #1, chat update #2]
```
6. The key detail is that the server received two client messages and independently pushed two of its own, with no message from one side waiting on a message from the other — that independence is exactly what "full-duplex" means.

## 7. Gotchas & takeaways

> **Gotcha:** treating an open WebSocket connection as free to keep around indefinitely. Each open connection holds server resources (memory, a file descriptor) for as long as it lasts; at large scale, this changes your capacity planning from "requests per second" to "concurrent open connections", a very different number to size for.

- WebSocket starts as an HTTP request, then upgrades the same connection to a full-duplex protocol.
- Use it when the server needs to push data to the client without the client asking first, and both sides need low-latency, independent messaging.
- At scale across multiple server instances, route messages to the specific instance holding the target connection — typically via a pub/sub broker like Redis.
