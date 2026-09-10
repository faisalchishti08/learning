---
card: system-design
gi: 213
slug: grpc-streaming-apis
title: gRPC & streaming APIs
---

## 1. What it is

**gRPC** is a remote procedure call (RPC) framework where a client calls a method on a remote service as if it were a local function call. It uses **Protocol Buffers (protobuf)** — a compact binary format — instead of JSON, and runs over HTTP/2, which natively supports **streaming**: a single call where the client, the server, or both keep sending messages over time instead of one request producing one response.

## 2. Why & when

A REST API modeled around resources works well for CRUD, but is awkward for actions that are naturally procedures ("recalculate this route," "run this batch job") or that need to send or receive a continuous stream of messages ("stream live location updates," "stream log lines as they are produced"). gRPC fits these cases directly: its four call shapes (unary, server streaming, client streaming, bidirectional streaming) map onto exactly these patterns, and protobuf's compact binary encoding and generated strongly-typed client/server code reduce both payload size and boilerplate compared to hand-written JSON REST clients.

Use gRPC for internal service-to-service calls within a system you control end to end — especially where you need streaming, and where you can generate matching client and server code from one `.proto` file. Avoid it for public-facing APIs consumed by arbitrary third parties or browsers, where REST/JSON's universal tooling and human-readability are a better fit — gRPC needs specific client library support that not every environment (particularly browsers, without a proxy layer) provides natively.

## 3. Core concept

- **`.proto` file as the single source of truth.** You define your service's methods and message types once in a `.proto` file; the gRPC toolchain generates client and server code in every target language from that one definition — this makes the contract impossible to accidentally drift out of sync between client and server, unlike a hand-maintained REST client.
- **Unary RPC.** One request, one response — the same shape as a normal REST call, just over gRPC's transport (`rpc GetOrder(OrderId) returns (Order);`).
- **Server streaming.** One request, a stream of responses over time — the client sends one call and keeps receiving messages until the server closes the stream (`rpc WatchOrderStatus(OrderId) returns (stream StatusUpdate);`).
- **Client streaming.** A stream of requests, one final response — the client sends many messages over time, and the server responds once after the stream ends (`rpc UploadLogBatch(stream LogLine) returns (UploadSummary);`).
- **Bidirectional streaming.** Both sides stream simultaneously and independently — useful for a genuinely two-way, ongoing exchange (a chat-like protocol, live collaborative editing).

## 4. Diagram

```
  UNARY                       SERVER STREAMING             CLIENT STREAMING            BIDIRECTIONAL

  Client -- req -->  Server   Client -- req -->  Server    Client -- item1 -->  Server  Client <==> Server
  Client <-- resp -- Server   Client <-- msg1 -- Server     Client -- item2 -->  Server   (both sides send
                               Client <-- msg2 -- Server     Client -- item3 -->  Server    and receive
                               Client <-- msg3 -- Server     Client <-- summary-- Server    independently,
                               (stream closes)                (stream closes,                on one open
                                                                 one final response)          connection)
```
*Caption: all four shapes run over one persistent HTTP/2 connection. Which shape you pick depends only on whether requests, responses, or both need to happen more than once per call.*

## 5. Runnable example

This models the four RPC shapes and what each side sees, in one file — a real implementation uses generated gRPC stubs from a `.proto` file; this shows the pattern each shape follows.

**Level 1 — Basic.** Unary RPC: one request in, one response out.

**Level 2 — Intermediate.** Server streaming: one request, multiple responses delivered over simulated time.

**Level 3 — Advanced.** Client streaming (many requests, one final aggregate response) and bidirectional streaming (both sides sending independently).

```java
// GrpcStreamingDemo.java
import java.util.*;
import java.util.function.*;

public class GrpcStreamingDemo {

    record OrderId(String id) {}
    record Order(String id, double amount) {}
    record StatusUpdate(String status, long timestampMs) {}
    record LogLine(String text) {}
    record UploadSummary(int linesReceived) {}
    record ChatMessage(String from, String text) {}

    // ---------- Level 1: unary RPC ----------
    static Order getOrder(OrderId request) {
        return new Order(request.id(), 42.00); // one request -> one response
    }

    // ---------- Level 2: server streaming RPC ----------
    static void watchOrderStatus(OrderId request, Consumer<StatusUpdate> onEachUpdate) {
        String[] statuses = {"PLACED", "PACKED", "SHIPPED", "DELIVERED"};
        long simulatedTime = 1000L;
        for (String status : statuses) {
            simulatedTime += 500; // simulated elapsed time between updates
            onEachUpdate.accept(new StatusUpdate(status, simulatedTime)); // server pushes each message
        }
    }

    // ---------- Level 3a: client streaming RPC ----------
    static UploadSummary uploadLogBatch(List<LogLine> clientStream) {
        int count = 0;
        for (LogLine line : clientStream) {
            System.out.println("    [server] received: " + line.text());
            count++; // server just accumulates until the client's stream ends
        }
        return new UploadSummary(count); // ONE response, after the whole stream is consumed
    }

    // ---------- Level 3b: bidirectional streaming RPC ----------
    static void chatSession(List<ChatMessage> clientMessages, Consumer<ChatMessage> serverReplies) {
        for (ChatMessage msg : clientMessages) {
            System.out.println("    [client -> server] " + msg.from() + ": " + msg.text());
            // Server can reply independently, interleaved with the client still sending.
            serverReplies.accept(new ChatMessage("server", "ack: " + msg.text()));
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - unary RPC:");
        Order order = getOrder(new OrderId("ORD-1"));
        System.out.println("  request: GetOrder(id=ORD-1) -> response: " + order);

        System.out.println("\nLevel 2 - server streaming RPC:");
        System.out.println("  request: WatchOrderStatus(id=ORD-1)");
        watchOrderStatus(new OrderId("ORD-1"),
            update -> System.out.println("    [client received] " + update.status() + " at t=" + update.timestampMs()));

        System.out.println("\nLevel 3a - client streaming RPC:");
        List<LogLine> logs = List.of(new LogLine("starting up"), new LogLine("processing batch 1"), new LogLine("done"));
        UploadSummary summary = uploadLogBatch(logs);
        System.out.println("  final response after client's stream ended: " + summary);

        System.out.println("\nLevel 3b - bidirectional streaming RPC:");
        List<ChatMessage> outgoing = List.of(
            new ChatMessage("alice", "hello"), new ChatMessage("alice", "are you there?"));
        chatSession(outgoing, reply -> System.out.println("    [client received reply] " + reply.text()));
    }
}
```

**How to run:** `java GrpcStreamingDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `getOrder(new OrderId("ORD-1"))` is called once and returns exactly one `Order` — a plain request-response call, the same shape a REST `GET /orders/ORD-1` would have, just carried over gRPC's transport instead.
2. **Level 2:** `watchOrderStatus(...)` is called once with one `OrderId`, but it invokes `onEachUpdate.accept(...)` four separate times, once per status change, each with an incrementing `simulatedTime`. The single `System.out.println` line in `main` that consumes this callback runs four times — this is what "one request, many responses over time" looks like: the client made one call and kept receiving messages until the server had nothing more to say.
3. **Level 3a:** `uploadLogBatch(logs)` iterates over three `LogLine` entries — standing in for a client sending three separate stream messages over time — printing each as `"[server] received: ..."` as it arrives. Only **after** the loop finishes (the stream has ended) does the method return one `UploadSummary` with the total count, `3`.
4. This ordering matters: in a real client-streaming call, the server does not know how many messages are coming, and cannot respond until the client explicitly closes its stream — the code's structure (accumulate inside the loop, respond after it) mirrors that constraint directly.
5. **Level 3b:** `chatSession(...)` iterates over `outgoing` messages, and for **each** one, both prints the client's message and immediately calls `serverReplies.accept(...)` with a server-generated reply — client and server are both "sending" on the same call, interleaved, rather than one side waiting for the other to fully finish first. This interleaving, not possible in a single request/response HTTP call, is what bidirectional streaming specifically enables.

## 7. Gotchas & takeaways

> **Gotcha:** streaming calls (especially server and bidirectional streaming) hold a connection open for the call's entire duration. Load balancers, connection timeouts, and client resource limits designed around short-lived unary calls can silently break or throttle long-lived streams if they are not configured with streaming in mind.

- Pick the RPC shape that matches the actual data-flow pattern — do not force a naturally streaming interaction (live updates, log ingestion) into a unary call with repeated polling, and do not use streaming where one request/response would do.
- The `.proto` file is the API contract — treat changes to it with the same discipline as [versioning strategies](0208-versioning-strategies.md) for REST: adding a new optional field is safe, removing or renumbering an existing field is a breaking change.
- gRPC is a strong default for internal, polyglot service-to-service calls; keep REST/JSON (or GraphQL) for public or browser-facing APIs where broad client support matters more than raw efficiency.
- Streaming calls need their own error-handling and retry thinking — a mid-stream failure is a different problem from a unary call's failure, since some messages may have already been delivered and acted on before the failure occurred.
