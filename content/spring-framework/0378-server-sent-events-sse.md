---
card: spring-framework
gi: 378
slug: server-sent-events-sse
title: "Server-Sent Events (SSE)"
---

## 1. What it is

Server-Sent Events in Spring WebFlux is a handler method (annotated or functional) that returns `Flux<ServerSentEvent<T>>` (or a plain `Flux<T>` with `text/event-stream` as the produces type) — the natural, reactive-native counterpart to Spring MVC's `SseEmitter` (an earlier card), letting a server push a continuous stream of named events to a browser's `EventSource`, expressed entirely through ordinary `Flux` operators rather than an imperative emitter object.

```java
@GetMapping(value = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> stream() {
    return Flux.interval(Duration.ofSeconds(1))
        .map(tick -> ServerSentEvent.builder("tick " + tick).build());
}
```

## 2. Why & when

Because WebFlux's entire programming model is already built around `Flux` (a stream of values over time), SSE support is almost a direct, natural fit — there's no separate "emitter" abstraction to learn, unlike Spring MVC's `SseEmitter`, which exists specifically because MVC's normal handler methods aren't inherently stream-oriented. Use reactive SSE when:

- You're building a WebFlux application and need to push a live stream of updates to a browser — notifications, live prices, progress updates, log tailing.
- You want the event stream itself to be composed from other reactive sources (a message broker's reactive client, a database change stream) using ordinary `Flux` operators, rather than manually bridging an external event source into an imperative emitter.
- You want automatic backpressure handling for the event stream "for free," since `Flux` already implements the Reactive Streams contract end to end.

## 3. Core concept

```
Flux<ServerSentEvent<T>> — each emitted element becomes ONE SSE event:

  ServerSentEvent.builder(data)
      .id("42")            <- optional: lets EventSource resume from here on reconnect
      .event("tick")        <- optional: named event type, JS listens via addEventListener("tick", ...)
      .retry(Duration...)    <- optional: reconnection delay hint for the browser
      .build()

Wire format written to the client (text/event-stream):

  id: 42
  event: tick
  data: tick 5

  (blank line terminates each event)

Backpressure: because Flux<ServerSentEvent<T>> IS a genuine Reactive
Streams Publisher, a slow client (or slow network) naturally applies
backpressure back through the SAME mechanism covered in the earlier
backpressure card — no separate mechanism needed for SSE specifically.

Comparison to Spring MVC's SseEmitter (earlier card):
  SseEmitter: imperative object, emitter.send(...) called manually
  WebFlux Flux<ServerSentEvent<T>>: declarative, composed from
    Flux operators — the STREAM ITSELF is the abstraction
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Flux&lt;ServerSentEvent&lt;T&gt;&gt; -&gt; text/event-stream wire format</text>

  <rect x="20" y="50" width="280" height="90" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="72" text-anchor="middle" fill="#6db33f" font-size="10">Flux.interval(1s).map(...)</text>
  <text x="35" y="95" fill="#8b949e" font-size="9">emits tick 0, tick 1, tick 2...</text>
  <text x="35" y="113" fill="#8b949e" font-size="9">each wrapped as ServerSentEvent</text>

  <line x1="300" y1="95" x2="360" y2="95" stroke="#8b949e" marker-end="url(#a54)"/>

  <rect x="360" y="50" width="340" height="90" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="72" text-anchor="middle" fill="#79c0ff" font-size="10">text/event-stream wire</text>
  <text x="375" y="95" fill="#e6edf3" font-size="9">event: tick</text>
  <text x="375" y="113" fill="#e6edf3" font-size="9">data: tick 0</text>
  <text x="375" y="128" fill="#8b949e" font-size="8">(blank line, repeats per element)</text>

  <defs>
    <marker id="a54" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Each `Flux` element becomes one SSE event on the wire — the reactive stream and the SSE protocol align naturally.*

## 5. Runnable example

### Level 1 — Basic

A simple ticking event stream, declared entirely with `Flux` operators:

```java
// StreamController.java
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

import java.time.Duration;

@RestController
public class StreamController {

    @GetMapping(value = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> stream() {
        return Flux.interval(Duration.ofSeconds(1))
            .take(5)
            .map(tick -> ServerSentEvent.<String>builder()
                .event("tick")
                .data("tick " + tick)
                .build());
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
# ... (one per second, 5 total, then the connection closes)
```

`Flux.interval(Duration.ofSeconds(1))` alone provides both the timing and the stream — no manual thread management, no emitter object to construct and send to explicitly. `.take(5)` limits it to five ticks, after which the `Flux` completes and WebFlux closes the SSE connection cleanly.

### Level 2 — Intermediate

Composing an SSE stream from a genuinely external, application-driven event source (a `Sinks.Many`, Reactor's programmatic bridge for pushing values into a `Flux` from outside code) — modeling a real notification feed:

```java
// NotificationController.java
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Sinks;

@RestController
public class NotificationController {

    // Sinks.Many: a programmatic bridge — application code calls tryEmitNext(...)
    // from OUTSIDE any reactive pipeline, and every current subscriber's Flux
    // receives it. This is the reactive equivalent of the SseEmitter-based
    // subscriber list pattern from the Spring MVC streaming card.
    private final Sinks.Many<String> notifications = Sinks.many().multicast().onBackpressureBuffer();

    @GetMapping(value = "/notifications/subscribe", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> subscribe() {
        return notifications.asFlux()
            .map(message -> ServerSentEvent.<String>builder()
                .event("notification")
                .data(message)
                .build());
    }

    @PostMapping("/notifications/publish")
    public String publish(@RequestParam String message) {
        Sinks.EmitResult result = notifications.tryEmitNext(message);
        return "Emit result: " + result;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Terminal 1: subscribe
curl -N http://localhost:8080/notifications/subscribe &

# Terminal 2: publish
curl -X POST "http://localhost:8080/notifications/publish?message=Order+shipped"
# Emit result: OK

# Terminal 1 immediately shows:
# event:notification
# data:Order shipped
```

**What changed:** `Sinks.Many` bridges imperative, "outside" code (the `POST /notifications/publish` handler, triggered by a completely separate HTTP request) into the reactive world — `tryEmitNext(message)` pushes a value that every current subscriber's `Flux` (from `notifications.asFlux()`) receives. `multicast().onBackpressureBuffer()` means multiple concurrent subscribers each get every published message, with a buffer absorbing bursts a slow subscriber temporarily can't keep up with — directly analogous to the shared-subscriber-list pattern from the Spring MVC `SseEmitter` streaming card, but expressed through Reactor's own multicast primitive instead of a manually managed list.

### Level 3 — Advanced

Production concern: heartbeats to prevent proxy timeouts (mirroring the MVC SSE card's equivalent concern), merged with the actual notification stream via `Flux.merge`, plus per-client connection cleanup logic:

```java
// NotificationController.java (production version)
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Sinks;

import java.time.Duration;

@RestController
public class NotificationController {

    private static final Logger log = LoggerFactory.getLogger(NotificationController.class);
    private final Sinks.Many<String> notifications = Sinks.many().multicast().onBackpressureBuffer();

    @GetMapping(value = "/notifications/subscribe", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> subscribe() {
        Flux<ServerSentEvent<String>> realNotifications = notifications.asFlux()
            .map(message -> ServerSentEvent.<String>builder()
                .event("notification")
                .data(message)
                .build());

        // Heartbeat comments — sent regardless of real notifications, keeping
        // intermediate proxies from treating the connection as idle and closing it.
        Flux<ServerSentEvent<String>> heartbeat = Flux.interval(Duration.ofSeconds(15))
            .map(tick -> ServerSentEvent.<String>builder().comment("heartbeat").build());

        return Flux.merge(realNotifications, heartbeat)
            .doOnSubscribe(sub -> log.info("Client subscribed, current subscriber count: {}",
                notifications.currentSubscriberCount()))
            .doFinally(signal -> log.info("Client disconnected ({}), remaining subscribers: {}",
                signal, notifications.currentSubscriberCount()));
    }

    @PostMapping("/notifications/publish")
    public String publish(@RequestParam String message) {
        Sinks.EmitResult result = notifications.tryEmitNext(message);
        if (result.isFailure()) {
            log.warn("Failed to emit notification: {}", result);
        }
        return "published to " + notifications.currentSubscriberCount() + " subscriber(s)";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -N http://localhost:8080/notifications/subscribe
# (immediately connected; server log shows "Client subscribed, current subscriber count: 1")
# :heartbeat            (every 15s, keeps proxies from timing out the connection)
# event:notification
# data:Order shipped    (whenever /publish is called)

# Ctrl+C the curl connection:
# server log: "Client disconnected (onComplete), remaining subscribers: 0"
```

**What changed and why:**
- `Flux.merge(realNotifications, heartbeat)` combines two independent, ongoing streams into one — real notifications arrive whenever `publish` is called, heartbeat comments arrive on a fixed 15-second interval, and both interleave naturally onto the same SSE connection because `merge` subscribes to both sources concurrently and emits from whichever produces a value first.
- `.doOnSubscribe`/`.doFinally` provide the connection lifecycle visibility needed in production — logging when a client connects and disconnects (and via `notifications.currentSubscriberCount()`, exactly how many clients are currently listening) without needing to manually track a subscriber list, since `Sinks.Many` already tracks this internally.
- This mirrors, almost operator-for-operator, the equivalent concerns addressed in the Spring MVC `SseEmitter` production example (heartbeats, connection lifecycle logging) — but expressed as composed `Flux` operators rather than imperative callback registration (`onCompletion`/`onTimeout`/`onError` on an `SseEmitter` instance), reinforcing how WebFlux's reactive-native approach reshapes even a feature (SSE) that both frameworks support.

## 6. Walkthrough

**Request: `GET /notifications/subscribe`, followed by `POST /notifications/publish?message=Order+shipped` from a separate client (Level 3 code).**

1. `DispatcherHandler` dispatches the `GET` to `subscribe()`. The method constructs `realNotifications` (a mapped view of `notifications.asFlux()`) and `heartbeat` (a fifteen-second interval), then combines them via `Flux.merge(...)`, attaching `.doOnSubscribe`/`.doFinally` logging — this entire composed `Flux<ServerSentEvent<String>>` is returned as the method's result.
2. Because the return type is `Flux<ServerSentEvent<T>>` with `produces = TEXT_EVENT_STREAM_VALUE`, WebFlux recognizes this as a genuine SSE streaming response and subscribes to it, keeping the underlying HTTP connection open rather than buffering-then-closing.
3. Subscription triggers `.doOnSubscribe(...)` immediately, logging the new subscriber count — this fires because `notifications.asFlux()` (feeding into the merged stream) increments its internal subscriber tracking the moment something subscribes to it.
4. The `heartbeat` branch of the merge begins independently ticking on its own 15-second interval, producing comment-only `ServerSentEvent`s that WebFlux writes to the connection as bare `:heartbeat` lines — these don't trigger a browser's `onmessage`/named-event listeners, existing purely to keep the connection's byte flow alive for intermediate proxies.
5. Later, a completely separate client issues `POST /notifications/publish?message=Order+shipped`, hitting `publish(...)` on a different request/response cycle entirely. Inside: `notifications.tryEmitNext("Order shipped")` pushes this value into the `Sinks.Many` — since the earlier `subscribe()` call is still an active subscriber to `notifications.asFlux()`, this triggers that subscription's `onNext` with the new message.
6. This flows through the `.map(...)` transformation into a `ServerSentEvent` with `event="notification"`, `data="Order shipped"`, then through `Flux.merge`'s combined output (since `realNotifications` is one of the two merged sources), and finally gets written to the still-open SSE connection from step 2.
7. The originally-connected client sees this event appear on its stream:
   ```
   event: notification
   data: Order shipped
   ```
8. If the subscribing client eventually disconnects (closes its connection, or `curl` is interrupted), WebFlux's underlying connection-handling detects this and cancels the subscription to the merged `Flux` — this cancellation signal propagates through `.doFinally(signal -> {...})`, firing the disconnect-logging callback and, critically, also decrementing `notifications`'s internal subscriber count, since the `notifications.asFlux()` subscription this client held is now properly cleaned up.

## 7. Gotchas & takeaways

> **`Sinks.Many.tryEmitNext` can fail (returning a non-success `EmitResult`) under certain conditions** — such as no subscribers currently present with certain sink configurations, or a backpressure buffer genuinely overflowing. Always check the result (as the Level 3 example does, logging a warning on failure) rather than assuming emission always succeeds silently.

> **`Flux.interval` (used for both `.take(5)` demos and heartbeats) runs on Reactor's default parallel scheduler by default** — this is appropriate for lightweight, timer-driven work like heartbeats, but be mindful that many concurrent SSE connections each running their own `Flux.interval` heartbeat can add up; consider sharing a single heartbeat-ticking source across all subscribers for very high connection counts, rather than each subscription creating its own independent timer.

> **`Sinks.many().multicast()` (used in these examples) only delivers events to subscribers connected *at the time of emission* — a client connecting after a message was published never sees that earlier message.** For use cases needing "replay the last N messages to newly connecting clients," Reactor's `Sinks.many().replay(...)` variant exists specifically for that purpose, trading some memory for that replay capability.

- WebFlux's SSE support (`Flux<ServerSentEvent<T>>`) is a natural extension of the existing reactive programming model, rather than a separate emitter-based API like Spring MVC's `SseEmitter`.
- `Sinks.Many` bridges imperative, "outside" code into a reactive stream that multiple SSE subscribers can share — the reactive counterpart to manually managing a list of `SseEmitter` instances.
- `Flux.merge` naturally combines multiple independent streams (real events, heartbeats) onto one SSE connection, expressed as ordinary operator composition.
- `.doOnSubscribe`/`.doFinally` provide connection lifecycle visibility (connect/disconnect logging, subscriber counts) without manual bookkeeping, since Reactor's own subscription mechanism already tracks this internally.
