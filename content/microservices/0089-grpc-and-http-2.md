---
card: microservices
gi: 89
slug: grpc-and-http-2
title: "gRPC and HTTP/2"
---

## 1. What it is

gRPC is Google's open-source [RPC](0088-remote-procedure-call-rpc-model.md) framework, built on top of HTTP/2 and using [Protocol Buffers](0090-protocol-buffers-protobuf-idl.md) as its default serialization format. Its reliance on HTTP/2 specifically (rather than HTTP/1.1, which most REST APIs use) is what unlocks several of its defining capabilities: true request **multiplexing** (many concurrent requests over a single TCP connection, with no head-of-line blocking between them) and native support for **streaming** (a call that sends or receives a sequence of messages over time, not just one request and one response).

## 2. Why & when

HTTP/1.1 opens a new connection (or reuses one from a limited pool) per concurrent request, and older HTTP/1.1 pipelining suffers from head-of-line blocking — one slow response can hold up others queued behind it on the same connection. HTTP/2 solves this at the protocol level with multiplexed streams: many logically independent requests and responses share a single TCP connection, interleaved at the frame level, so one slow call never blocks the others. This matters enormously for service-to-service calls in a microservices mesh, where a single service might need to make many concurrent calls to the same downstream dependency — gRPC's HTTP/2 foundation lets all of them share one connection efficiently instead of needing many separate ones.

Choose gRPC when internal service-to-service performance matters (lower latency, higher throughput than typical REST/JSON), when streaming is genuinely needed (a service pushing a continuous sequence of updates), or when strongly-typed, code-generated contracts across languages are valuable. REST over HTTP/1.1 remains the better choice for public APIs (broader client and tooling support, human-readable payloads) and cases where gRPC's added infrastructure complexity (proxies, load balancers, and browsers historically needing gRPC-Web translation) isn't worth the performance gain.

## 3. Core concept

HTTP/1.1 effectively serializes concurrent requests across a small pool of connections; HTTP/2 multiplexes many concurrent request/response streams over one connection, so no single slow call blocks the others sharing it.

```
HTTP/1.1 (connection pool of 2):        HTTP/2 (ONE connection, multiplexed):
conn A: req1 ---[waits]---> req3        conn: req1  afafaf req2 afaf req3   <- interleaved on ONE connection
conn B: req2 ---[waits]---> req4                     ...all concurrent, no head-of-line blocking
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTTP 1.1 uses a small pool of separate connections where requests can queue behind each other, while HTTP/2 multiplexes many concurrent request and response streams over a single shared connection">
  <text x="160" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">HTTP/1.1 (connection pool)</text>
  <rect x="40" y="30" width="240" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">conn A: req1, then req3 (queued)</text>
  <rect x="40" y="70" width="240" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">conn B: req2, then req4 (queued)</text>

  <text x="480" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">HTTP/2 (multiplexed)</text>
  <rect x="360" y="30" width="240" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="52" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ONE connection</text>
  <text x="480" y="70" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">req1, req2, req3, req4</text>
  <text x="480" y="87" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">all interleaved, concurrent</text>
</svg>

HTTP/2 collapses many logically independent request/response streams onto one shared, multiplexed connection.

## 5. Runnable example

Scenario: simulate the practical effect of head-of-line blocking versus multiplexing — first modeling HTTP/1.1-style behavior where a slow request on a connection delays everything queued behind it, then modeling HTTP/2-style multiplexing where a slow request never blocks unrelated concurrent requests, then extended to add a streaming call, a capability HTTP/1.1's one-request-one-response model doesn't support natively at all.

### Level 1 — Basic

```java
// File: Http11HeadOfLineBlocking.java -- a SLOW request on a connection
// delays every OTHER request queued behind it on that SAME connection.
import java.util.*;
import java.util.concurrent.*;

public class Http11HeadOfLineBlocking {
    static String handleRequest(String name, int delayMs) throws InterruptedException {
        Thread.sleep(delayMs);
        return name + " done";
    }

    public static void main(String[] args) throws Exception {
        // ONE connection handles req1 (slow) THEN req2 (fast) -- req2 waits behind req1
        long start = System.currentTimeMillis();
        String r1 = handleRequest("req1 (slow, 200ms)", 200);
        String r2 = handleRequest("req2 (fast, 20ms)", 20); // must wait for req1 to finish first
        long elapsed = System.currentTimeMillis() - start;
        System.out.println(r1);
        System.out.println(r2 + " (had to wait behind req1)");
        System.out.println("Total time: ~" + elapsed + "ms (sum of both -- req2 blocked behind req1)");
    }
}
```

**How to run:** `javac Http11HeadOfLineBlocking.java && java Http11HeadOfLineBlocking` (JDK 17+).

Expected output (elapsed time will vary slightly, always at least 220):
```
req1 (slow, 200ms) done
req2 (fast, 20ms) done (had to wait behind req1)
Total time: ~220ms (sum of both -- req2 blocked behind req1)
```

### Level 2 — Intermediate

```java
// File: Http2Multiplexing.java -- the SAME two requests, now MULTIPLEXED
// (run concurrently, as HTTP/2 streams sharing one connection would) --
// the slow request no longer blocks the fast one.
import java.util.concurrent.*;

public class Http2Multiplexing {
    static ExecutorService connection = Executors.newFixedThreadPool(2); // ONE "connection," multiple concurrent streams

    static String handleRequest(String name, int delayMs) throws InterruptedException {
        Thread.sleep(delayMs);
        return name + " done";
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        Future<String> f1 = connection.submit(() -> handleRequest("req1 (slow, 200ms)", 200));
        Future<String> f2 = connection.submit(() -> handleRequest("req2 (fast, 20ms)", 20)); // does NOT wait for req1

        String r2 = f2.get(); // req2's result is available quickly, independent of req1's progress
        long r2Elapsed = System.currentTimeMillis() - start;
        System.out.println(r2 + " (available after ~" + r2Elapsed + "ms -- did NOT wait behind req1)");

        String r1 = f1.get();
        System.out.println(r1);
        connection.shutdown();
    }
}
```

**How to run:** `javac Http2Multiplexing.java && java Http2Multiplexing` (JDK 17+).

Expected output (timing will vary slightly, but req2 always completes well before req1):
```
req2 (fast, 20ms) done (available after ~25ms -- did NOT wait behind req1)
req1 (slow, 200ms) done
```

### Level 3 — Advanced

```java
// File: StreamingCall.java -- model a gRPC-style SERVER STREAMING call:
// the server sends a SEQUENCE of messages over time on one call, rather
// than a single request producing a single response -- something
// HTTP/1.1's request/response model doesn't support natively.
import java.util.*;
import java.util.function.Consumer;

public class StreamingCall {
    interface StreamObserver<T> { // models gRPC's StreamObserver
        void onNext(T value);
        void onCompleted();
    }

    static void streamOrderUpdates(String orderId, StreamObserver<String> observer) {
        // simulates the SERVER pushing a SEQUENCE of updates over ONE call
        observer.onNext("PLACED");
        observer.onNext("PACKED");
        observer.onNext("SHIPPED");
        observer.onNext("DELIVERED");
        observer.onCompleted();
    }

    public static void main(String[] args) {
        List<String> received = new ArrayList<>();
        streamOrderUpdates("ORD-1", new StreamObserver<String>() {
            public void onNext(String status) {
                received.add(status);
                System.out.println("Received update: " + status);
            }
            public void onCompleted() {
                System.out.println("Stream completed. Total updates received: " + received.size());
            }
        });
    }
}
```

**How to run:** `javac StreamingCall.java && java StreamingCall` (JDK 17+).

Expected output:
```
Received update: PLACED
Received update: PACKED
Received update: SHIPPED
Received update: DELIVERED
Stream completed. Total updates received: 4
```

## 6. Walkthrough

1. **Level 1** — `handleRequest("req1 (slow, 200ms)", 200)` and then `handleRequest("req2 (fast, 20ms)", 20)` are called strictly sequentially on `main`'s single thread, modeling HTTP/1.1's per-connection request handling: req2 cannot even *begin* until req1 finishes, regardless of how fast req2 itself would otherwise be. The total elapsed time (~220ms) is the sum of both — req2's own short 20ms delay is dwarfed by having to wait behind req1's 200ms first.
2. **Level 2 — multiplexing removes that ordering constraint** — `connection`, a 2-thread pool, stands in for one HTTP/2 connection capable of handling multiple concurrent streams. Both `f1` (req1) and `f2` (req2) are submitted essentially back-to-back, and because the pool has 2 threads, both begin running *concurrently* rather than one waiting for the other.
3. **Tracing the timing** — `f2.get()` is called first and returns after roughly 20-25ms — req2's own delay, essentially unaffected by req1 running concurrently in the pool's other thread. Only afterward does `main` call `f1.get()`, which returns once req1's full 200ms completes. The printed timing (`~25ms`) directly demonstrates that req2's completion time was determined by its *own* delay, not by having to wait behind req1's — precisely the head-of-line blocking elimination that HTTP/2 multiplexing provides in a real connection.
4. **Level 3 — a capability HTTP/1.1 can't express at all** — `streamOrderUpdates` takes a `StreamObserver`, an interface with `onNext` (called once per message in the sequence) and `onCompleted` (called once the sequence ends) — this exactly mirrors gRPC's real `StreamObserver` API for server-streaming calls. `main` calls `streamOrderUpdates`, providing an anonymous `StreamObserver` implementation that appends each received status to a `received` list and prints it as it arrives.
5. **Tracing the streamed sequence** — `streamOrderUpdates` calls `observer.onNext("PLACED")`, `onNext("PACKED")`, `onNext("SHIPPED")`, `onNext("DELIVERED")` in order, each triggering the corresponding print statement immediately as it's called — so the printed lines appear one at a time, in the exact order the server "pushed" them, followed finally by `onCompleted()`, which prints the summary line reporting all 4 updates were received. In genuine HTTP/1.1's one-request-one-response model, achieving this same "push a sequence of updates over time" behavior would require either repeated polling (the client asking "any update yet?" over and over) or a separate mechanism like WebSockets — gRPC's HTTP/2 foundation supports it as a first-class call type.

## 7. Gotchas & takeaways

> **Gotcha:** HTTP/2 multiplexing happens *within* one TCP connection, but that connection still ultimately traverses one network path — a severe enough network-level problem (packet loss causing TCP-level retransmission) can still affect every multiplexed stream sharing that connection, an effect sometimes called TCP-level head-of-line blocking (which HTTP/3, built on QUIC, addresses further). Multiplexing solves *application-level* head-of-line blocking, not every possible network-layer bottleneck.

- gRPC builds RPC (see [RPC model](0088-remote-procedure-call-rpc-model.md)) on top of HTTP/2, gaining true multiplexing and native streaming support as a direct consequence of that protocol choice.
- HTTP/2 multiplexing means a slow concurrent call no longer blocks other calls sharing the same connection — a real, measurable improvement over HTTP/1.1's connection-pool-based concurrency.
- Streaming calls (server, client, or bidirectional) let a single call exchange a sequence of messages over time, a capability that doesn't fit naturally into HTTP/1.1's strict one-request-one-response model.
- Choose gRPC for internal, performance-sensitive service-to-service calls or genuine streaming needs; choose REST/HTTP-1.1-style APIs for public-facing, broadly-compatible, human-debuggable interfaces.
- See [gRPC streaming](0091-grpc-streaming-server-client-bidirectional.md) for the full set of streaming call shapes gRPC supports, and [gRPC vs REST trade-offs](0092-grpc-vs-rest-trade-offs.md) for a direct comparison to guide the choice between them.
