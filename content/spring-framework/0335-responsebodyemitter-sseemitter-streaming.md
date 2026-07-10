---
card: spring-framework
gi: 335
slug: responsebodyemitter-sseemitter-streaming
title: "ResponseBodyEmitter / SseEmitter (streaming)"
---

## 1. What it is

`ResponseBodyEmitter` is a return type for Spring MVC handler methods that lets you push chunks of data to the client asynchronously over time, instead of computing a complete response and returning it all at once. `SseEmitter` is a subclass specialized for **Server-Sent Events** — a standard, one-way, HTTP-based protocol for a server to push a stream of named events to a browser, which the browser's `EventSource` API consumes natively.

```java
@GetMapping("/events")
public SseEmitter stream() {
    SseEmitter emitter = new SseEmitter();
    executor.execute(() -> {
        try {
            for (int i = 0; i < 5; i++) {
                emitter.send(SseEmitter.event().name("tick").data("tick " + i));
                Thread.sleep(1000);
            }
            emitter.complete();
        } catch (Exception e) {
            emitter.completeWithError(e);
        }
    });
    return emitter;
}
```

## 2. Why & when

A normal `@GetMapping` handler returns a value once the method finishes, and the entire response is written as one unit. That model breaks down when:

- Data becomes available incrementally (progress updates, live search results, a slow report generating row by row) and you want the client to see it as it arrives, not after everything is ready.
- You need to push server-originated updates to a browser without polling — stock tickers, notification feeds, live dashboards, chat message streams.
- The alternative (client polling every N seconds) wastes requests and adds latency between an event happening and the client learning about it.

`SseEmitter` specifically targets browser consumption because it speaks the SSE wire format the native `EventSource` JavaScript API understands, with automatic reconnection built into the browser. Use plain `ResponseBodyEmitter` for non-SSE streaming (e.g. a raw chunked JSON-lines stream to a non-browser client) where you don't need the SSE framing or browser auto-reconnect.

## 3. Core concept

```
Normal handler:                      SseEmitter handler:
  method computes full result          method returns an EMITTER immediately,
  return result                        the HTTP connection stays OPEN,
       |                                a background thread pushes events
       v                               over time via emitter.send(...)
  ONE write, response closes
                                       Client (EventSource):
                                         onmessage fires for EACH event,
                                         connection stays open until
                                         emitter.complete() or timeout

Wire format (text/event-stream):
  event: tick
  data: tick 0

  event: tick
  data: tick 1

  (blank line terminates each event; browser's EventSource parses this natively)
```

The handler method returns almost instantly (just the emitter object); the actual data transmission happens later, off the request thread, via calls to `emitter.send(...)` from another thread (an executor, a message listener, etc.).

## 4. Diagram

<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="240" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">SseEmitter: one open connection, many pushed events</text>

  <rect x="20" y="50" width="160" height="150" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="72" text-anchor="middle" fill="#79c0ff">Browser</text>
  <text x="100" y="90" text-anchor="middle" fill="#8b949e" font-size="9">EventSource</text>
  <text x="100" y="115" text-anchor="middle" fill="#8b949e" font-size="9">onmessage: tick 0</text>
  <text x="100" y="135" text-anchor="middle" fill="#8b949e" font-size="9">onmessage: tick 1</text>
  <text x="100" y="155" text-anchor="middle" fill="#8b949e" font-size="9">onmessage: tick 2</text>
  <text x="100" y="180" text-anchor="middle" fill="#8b949e" font-size="9">connection stays open</text>

  <rect x="280" y="50" width="180" height="150" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="370" y="72" text-anchor="middle" fill="#6db33f">SseEmitter</text>
  <text x="370" y="90" text-anchor="middle" fill="#8b949e" font-size="9">held open on server</text>
  <text x="370" y="115" text-anchor="middle" fill="#8b949e" font-size="9">send("tick 0")</text>
  <text x="370" y="135" text-anchor="middle" fill="#8b949e" font-size="9">send("tick 1")</text>
  <text x="370" y="155" text-anchor="middle" fill="#8b949e" font-size="9">send("tick 2")</text>
  <text x="370" y="180" text-anchor="middle" fill="#8b949e" font-size="9">complete()</text>

  <rect x="520" y="80" width="180" height="60" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="610" y="102" text-anchor="middle" fill="#8b949e" font-size="10">background thread</text>
  <text x="610" y="120" text-anchor="middle" fill="#8b949e" font-size="10">produces events over time</text>

  <line x1="180" y1="120" x2="280" y2="120" stroke="#6db33f" marker-end="url(#a11)"/>
  <line x1="520" y1="110" x2="460" y2="110" stroke="#8b949e" marker-end="url(#a11)"/>

  <defs>
    <marker id="a11" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*A background thread feeds events into the emitter; the browser's `EventSource` receives them one at a time over the single, long-lived connection.*

## 5. Runnable example

### Level 1 — Basic

A simple ticking event stream:

```java
// StreamController.java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.concurrent.Executors;

@RestController
public class StreamController {

    private final java.util.concurrent.ExecutorService executor = Executors.newCachedThreadPool();

    @GetMapping("/events")
    public SseEmitter stream() {
        SseEmitter emitter = new SseEmitter();
        executor.execute(() -> {
            try {
                for (int i = 0; i < 5; i++) {
                    emitter.send(SseEmitter.event().name("tick").data("tick " + i));
                    Thread.sleep(1000);
                }
                emitter.complete();
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });
        return emitter;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl -N http://localhost:8080/events
# event:tick
# data:tick 0
#
# event:tick
# data:tick 1
# ... (one line pair per second, connection closes after 5)
```

The handler returns the `SseEmitter` object almost instantly — the HTTP connection stays open while a background thread sends five events one second apart. `curl -N` disables buffering so you see each event as it arrives, mimicking what a browser's `EventSource` would see.

### Level 2 — Intermediate

Multiple concurrent subscribers, each receiving broadcast events from a shared source (simulating a live notification feed):

```java
// NotificationController.java
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@RestController
public class NotificationController {

    private final List<SseEmitter> subscribers = new CopyOnWriteArrayList<>();

    @GetMapping("/notifications/subscribe")
    public SseEmitter subscribe() {
        SseEmitter emitter = new SseEmitter(0L);   // 0 = no timeout
        subscribers.add(emitter);
        emitter.onCompletion(() -> subscribers.remove(emitter));
        emitter.onTimeout(() -> subscribers.remove(emitter));
        emitter.onError((ex) -> subscribers.remove(emitter));
        return emitter;
    }

    @PostMapping("/notifications/publish")
    public String publish(@RequestParam String message) {
        List<SseEmitter> dead = new java.util.ArrayList<>();
        for (SseEmitter emitter : subscribers) {
            try {
                emitter.send(SseEmitter.event().name("notification").data(message));
            } catch (Exception e) {
                dead.add(emitter);   // client disconnected; will be cleaned up
            }
        }
        subscribers.removeAll(dead);
        return "published to " + subscribers.size() + " subscriber(s)";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Terminal 1 and 2, each subscribes:
curl -N http://localhost:8080/notifications/subscribe &
curl -N http://localhost:8080/notifications/subscribe &

# Terminal 3, publishes:
curl -X POST "http://localhost:8080/notifications/publish?message=Order+shipped"
# published to 2 subscriber(s)

# Both terminal 1 and 2 immediately print:
# event:notification
# data:Order shipped
```

**What changed:** Instead of one emitter per stream self-generating its own events, subscribers now register into a shared list and receive events pushed by a *separate* endpoint (`/publish`). `onCompletion`/`onTimeout`/`onError` callbacks clean up disconnected clients from the list — critical to avoid a slow memory leak of dead emitter references. This is the shape of a real pub/sub notification feed.

### Level 3 — Advanced

Production concerns: timeout handling, heartbeats to keep proxies/load balancers from closing idle connections, backpressure-aware error handling, and moving from an in-memory subscriber list (which breaks across multiple server instances) to acknowledging that limitation explicitly:

```java
// NotificationController.java (production version)
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

@RestController
public class NotificationController {

    private static final Logger log = LoggerFactory.getLogger(NotificationController.class);
    private static final long TIMEOUT_MS = 60_000L;

    private final List<SseEmitter> subscribers = new CopyOnWriteArrayList<>();

    @GetMapping("/notifications/subscribe")
    public SseEmitter subscribe() {
        SseEmitter emitter = new SseEmitter(TIMEOUT_MS);
        subscribers.add(emitter);

        emitter.onCompletion(() -> {
            subscribers.remove(emitter);
            log.info("subscriber disconnected normally, {} remain", subscribers.size());
        });
        emitter.onTimeout(() -> {
            emitter.complete();   // must explicitly complete on timeout, or the connection lingers
            log.info("subscriber timed out after {}ms", TIMEOUT_MS);
        });
        emitter.onError((ex) -> {
            subscribers.remove(emitter);
            log.warn("subscriber error: {}", ex.getMessage());
        });

        try {
            // Send an immediate event so the client (and any intermediate proxy) knows
            // the connection is alive right away, rather than waiting for the first real event.
            emitter.send(SseEmitter.event().name("connected").data("ok"));
        } catch (IOException e) {
            subscribers.remove(emitter);
        }
        return emitter;
    }

    // Heartbeat: proxies/load balancers often kill connections idle for >30-60s with no bytes.
    @Scheduled(fixedRate = 15_000)
    public void heartbeat() {
        List<SseEmitter> dead = new java.util.ArrayList<>();
        for (SseEmitter emitter : subscribers) {
            try {
                emitter.send(SseEmitter.event().comment("heartbeat"));   // comment lines are ignored by EventSource
            } catch (IOException e) {
                dead.add(emitter);
            }
        }
        subscribers.removeAll(dead);
    }

    @PostMapping("/notifications/publish")
    public String publish(@RequestParam String message) {
        List<SseEmitter> dead = new java.util.ArrayList<>();
        for (SseEmitter emitter : subscribers) {
            try {
                emitter.send(SseEmitter.event().name("notification").data(message));
            } catch (IOException e) {
                dead.add(emitter);
            }
        }
        subscribers.removeAll(dead);
        return "published to " + subscribers.size() + " subscriber(s)";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
# (requires @EnableScheduling on the main application class for heartbeat() to run)

curl -N http://localhost:8080/notifications/subscribe
# event:connected
# data:ok
#
# :heartbeat            (every 15s, keeps intermediate proxies from timing out the connection)
#
# event:notification
# data:Order shipped    (whenever /publish is called)
```

**What changed and why:**
- Explicit `onTimeout`/`onError`/`onCompletion` callbacks are mandatory in production — without them, disconnected clients silently accumulate as dead `SseEmitter` references, a slow memory leak that's easy to miss in testing but shows up under real traffic churn.
- The heartbeat comment line (`emitter.event().comment(...)`) sends bytes over the wire without triggering the browser's `onmessage` handler — its only purpose is keeping intermediate infrastructure (load balancers, reverse proxies) from treating the connection as idle and closing it.
- This in-memory `subscribers` list only works correctly on a single server instance — with multiple instances behind a load balancer, a client subscribed to instance A never receives events published via instance B. Production systems typically back this with a message broker (Redis pub/sub, Kafka) so any instance can publish and any instance's local subscribers receive it; that's the natural next evolution beyond this example.

## 6. Walkthrough

**Request: `GET /notifications/subscribe`, followed later by `POST /notifications/publish?message=Order+shipped` from a different client (Level 3 code).**

1. `DispatcherServlet` dispatches the `GET` to `subscribe()`. A new `SseEmitter(60000L)` is created and immediately added to the shared `subscribers` list.
2. Lifecycle callbacks are registered (`onCompletion`, `onTimeout`, `onError`) — these will fire later, asynchronously, whenever the connection state changes.
3. `emitter.send(...)` writes an initial `connected` event to the still-open HTTP response, then `subscribe()` returns the emitter object. Crucially, Spring MVC does **not** close the connection just because the method returned — that's the entire point of an async return type like `SseEmitter`: the underlying request-processing thread is released back to the server's thread pool, but the client's HTTP connection remains open, tracked separately by the emitter.
4. The client (a browser's `EventSource`, or `curl -N` in the example) receives the `connected` event and stays waiting for more.
5. Every 15 seconds, the `@Scheduled` `heartbeat()` method runs on a completely separate thread from any request thread. It iterates all live subscribers (including the one from step 1) and sends a comment-only SSE line — the browser's `EventSource` ignores comment lines for `onmessage` purposes, but the bytes on the wire reset any idle-connection timers in intermediate proxies.
6. Later, a second, unrelated `POST /notifications/publish?message=Order+shipped` request arrives on a different thread. `publish()` iterates the same `subscribers` list and calls `emitter.send(...)` on each — including the one from step 1.
7. That `send()` call writes directly onto the *original*, still-open HTTP connection from step 1 (even though the original request thread has long since been released) — the subscribing client receives:
   ```
   event: notification
   data: Order shipped
   ```
8. The browser's `EventSource.onmessage` (or a named listener for `"notification"`) fires with this data — no polling, no new request needed.
9. If the client's connection eventually drops (browser tab closed, network failure), the next `send()` attempt on that emitter throws `IOException`; `publish()` and `heartbeat()` both catch this, collect the dead emitter, and remove it from `subscribers` — preventing the list from growing unbounded with disconnected clients.

## 7. Gotchas & takeaways

> **A request thread handling an `SseEmitter` is released back to the pool once the handler method returns the emitter — but the HTTP connection itself stays open.** This is what makes streaming scalable (you're not blocking one thread per open connection for the connection's whole lifetime), but it also means all further `emitter.send()` calls happen from *other* threads (schedulers, listeners, other request threads) — you must design for that concurrency from the start, as the examples do with `CopyOnWriteArrayList`.

> **Forgetting to call `emitter.complete()` in `onTimeout` leaves the connection in a lingering state** even after the configured timeout fires — always explicitly complete the emitter in the timeout callback, as shown in Level 3.

> **`SseEmitter` state (subscriber lists) is per-JVM-instance.** Behind a load balancer with multiple app instances, events published on one instance never reach subscribers connected to another — you need a shared broadcast mechanism (Redis pub/sub, a message queue) to fan out events across instances in a horizontally scaled deployment.

- `ResponseBodyEmitter` is the general streaming return type; `SseEmitter` specializes it for the SSE wire format that browsers' `EventSource` consumes natively.
- Always register `onCompletion`/`onTimeout`/`onError` callbacks to clean up subscriber references — otherwise disconnected clients leak memory over time.
- Send periodic heartbeats (SSE comment lines) to prevent intermediate proxies/load balancers from closing idle-looking connections.
- In-memory emitter lists don't scale across multiple server instances — back real production fan-out with a shared message broker.
