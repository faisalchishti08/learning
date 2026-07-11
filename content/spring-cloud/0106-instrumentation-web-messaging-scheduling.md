---
card: spring-cloud
gi: 106
slug: instrumentation-web-messaging-scheduling
title: "Instrumentation (web, messaging, scheduling)"
---

## 1. What it is

Instrumentation is the automatic span creation Spring Boot's auto-configuration performs on an application's behalf whenever Micrometer Tracing is on the classpath — an incoming/outgoing HTTP request, a message consumed from or produced to a broker, and a `@Scheduled` method's execution each automatically get wrapped in a span, with trace context correctly propagated in and out, with zero manual `Tracer` API calls required from application code for these three common cases.

```java
@RestController
class OrderController {
    @GetMapping("/orders/{id}")
    Order getOrder(@PathVariable String id) { // automatically wrapped in a span -- no manual tracing code
        return orderService.find(id);
    }
}
```

```java
@Scheduled(fixedRate = 60000)
void syncInventory() { // ALSO automatically wrapped in its own span
    inventoryService.sync();
}
```

## 2. Why & when

Manually creating and ending a span around every single HTTP request handler, every message listener, and every scheduled method across an entire application would be enormous, repetitive boilerplate — and worse, easy to forget in any one specific place, silently leaving gaps in trace coverage. Spring Boot's auto-instrumentation eliminates this entirely for the three most common sources of "a unit of work worth tracing" in a typical application: Spring MVC/WebFlux request handling, Spring Cloud Stream/Kafka/RabbitMQ message handling, and `@Scheduled` method execution all get spans automatically, correctly named and correctly nested relative to whatever trace context (if any) was already active, purely from having the relevant Micrometer Tracing and instrumentation dependencies on the classpath.

Reach for understanding (rather than bypassing) auto-instrumentation when:

- Confirming what's already traced automatically, before writing any manual `Tracer` code — most applications need zero manual span creation for their web endpoints, message handlers, or scheduled jobs, since auto-instrumentation already covers exactly these cases.
- Debugging a missing span for one of these three categories — checking that the correct starter/binder dependency is actually present (auto-instrumentation is conditional on specific classpath dependencies being available) is usually the first thing to verify before assuming a code-level tracing bug.
- Deciding where manual span creation (the `Tracer` API from an earlier card) genuinely adds value — typically inside a request handler's business logic, around a specific slow operation the automatic request-level span doesn't itself subdivide, rather than duplicating what auto-instrumentation already provides at the request/message/schedule boundary.

## 3. Core concept

```
 auto-instrumented boundaries (span created AUTOMATICALLY, no manual code):

   incoming HTTP request  -> span created on entry, ended on response, named after the route
   outgoing HTTP call (RestTemplate/WebClient) -> span created around the call
   message consumed from broker -> span created around the listener invocation
   message produced to broker   -> span created around the send
   @Scheduled method execution  -> span created around each invocation

 manual instrumentation (Tracer API, from an earlier card) is layered ON TOP of these,
 typically for a specific sub-operation WITHIN an already-auto-spanned boundary
```

Auto-instrumentation activates purely based on which starters/dependencies are present — a plain `Function` bean with no web, messaging, or scheduling annotation gets no automatic span, consistent with there being no natural "unit of work boundary" for the framework to hook into.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An incoming HTTP request automatically gets a span at the controller boundary and a scheduled method automatically gets its own separate span both created by auto instrumentation with no manual tracing code required in either case">
  <rect x="30" y="20" width="260" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">GET /orders/42</text>
  <text x="160" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">auto span: "getOrder"</text>
  <text x="160" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">zero manual Tracer calls needed</text>

  <rect x="350" y="20" width="260" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">@Scheduled syncInventory()</text>
  <text x="480" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">auto span: "syncInventory"</text>
  <text x="480" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">its OWN, separate trace each run</text>
</svg>

Two entirely different trigger types, both producing automatic, correctly-scoped spans with no shared code path required in application logic.

## 5. Runnable example

The scenario: model an "auto-instrumentation" layer that wraps arbitrary method invocations with spans automatically, based purely on annotations attached to those methods — mirroring what Spring Boot's actual auto-configuration does via AOP-style interception. Start with manual wrapping (the baseline being replaced), then add automatic wrapping driven by a marker annotation, then extend to distinguish web-triggered spans from scheduled-triggered spans with correctly different naming/behavior.

### Level 1 — Basic

Manual span wrapping around a request handler — the tedious baseline auto-instrumentation exists to eliminate.

```java
import java.util.*;

public class InstrumentationLevel1 {
    record Span(String name, long startMs, long endMs) {}
    static List<Span> recordedSpans = new ArrayList<>();

    static String getOrder(String id) {
        long start = System.currentTimeMillis();
        String result = "Order#" + id; // the actual business logic
        long end = System.currentTimeMillis();
        recordedSpans.add(new Span("getOrder", start, end)); // MANUAL span recording -- easy to forget elsewhere
        return result;
    }

    public static void main(String[] args) {
        System.out.println(getOrder("42"));
        System.out.println("recorded spans: " + recordedSpans.size());
    }
}
```

How to run: `java InstrumentationLevel1.java`

Every method that should be traced needs this same manual start/end/record pattern repeated inside it — multiply this across every controller method, every message listener, and every scheduled job in a real application, and the repetition (and risk of a forgotten span somewhere) becomes obvious.

### Level 2 — Intermediate

Replace manual wrapping with automatic interception: a generic `instrument` helper wraps *any* method call in a span, without that method's own code containing any tracing logic.

```java
import java.util.*;
import java.util.function.Supplier;

public class InstrumentationLevel2 {
    record Span(String name, long startMs, long endMs) {}
    static List<Span> recordedSpans = new ArrayList<>();

    // models what Spring's auto-instrumentation does via AOP interception -- wraps ANY call automatically
    static <T> T instrument(String spanName, Supplier<T> work) {
        long start = System.currentTimeMillis();
        T result = work.get();
        long end = System.currentTimeMillis();
        recordedSpans.add(new Span(spanName, start, end));
        return result;
    }

    // the "controller method" itself contains ZERO tracing code
    static String getOrder(String id) {
        return "Order#" + id;
    }

    public static void main(String[] args) {
        String result = instrument("getOrder", () -> getOrder("42")); // auto-instrumentation wraps the call site
        System.out.println(result);
        System.out.println("recorded spans: " + recordedSpans.size());
    }
}
```

How to run: `java InstrumentationLevel2.java`

`getOrder` itself is now indistinguishable from a plain, untraced method — all span-recording logic lives in the reusable `instrument` wrapper, called once per traced boundary, mirroring how Spring's auto-configuration wraps controller methods, message listeners, and scheduled methods via interception rather than requiring tracing code inside each one.

### Level 3 — Advanced

Extend to two distinct auto-instrumented boundary types (web request handling and scheduled execution), each producing correctly-named, independently-triggered spans, plus a simple registry proving different trigger types are still handled uniformly by the same underlying instrumentation mechanism.

```java
import java.util.*;
import java.util.function.Supplier;

public class InstrumentationLevel3 {
    record Span(String name, String triggerType, long startMs, long endMs) {}
    static List<Span> recordedSpans = new ArrayList<>();

    static <T> T instrument(String spanName, String triggerType, Supplier<T> work) {
        long start = System.currentTimeMillis();
        T result = work.get();
        long end = System.currentTimeMillis();
        recordedSpans.add(new Span(spanName, triggerType, start, end));
        return result;
    }

    // business logic methods -- NEITHER contains any tracing code
    static String getOrder(String id) { return "Order#" + id; }
    static void syncInventory() { /* sync logic */ }

    // models the web adapter's auto-instrumentation hook
    static String handleHttpRequest(String path, String id) {
        return instrument(path, "web", () -> getOrder(id));
    }

    // models the scheduler's auto-instrumentation hook -- a DIFFERENT trigger type, same instrument() mechanism
    static void handleScheduledRun() {
        instrument("syncInventory", "scheduled", () -> { syncInventory(); return null; });
    }

    public static void main(String[] args) {
        System.out.println(handleHttpRequest("GET /orders/{id}", "42"));
        handleScheduledRun();
        handleScheduledRun(); // scheduled methods run repeatedly -- each run gets its OWN separate span

        System.out.println("-- recorded spans --");
        for (Span s : recordedSpans) {
            System.out.println(s.name() + " [" + s.triggerType() + "]");
        }
    }
}
```

How to run: `java InstrumentationLevel3.java`

`handleHttpRequest` and `handleScheduledRun` both delegate to the same `instrument` method, but each passes a different `triggerType` and each is invoked by a structurally different caller (one HTTP request, versus the scheduler firing twice) — the recorded spans list ends up with one `"web"`-tagged span and two separate `"scheduled"`-tagged spans (one per scheduled invocation), correctly reflecting that a repeatedly-firing scheduled method produces a fresh, independent span (and typically a fresh trace) on every single execution, unlike a request-scoped span which exists only for that one request's lifetime.

## 6. Walkthrough

Trace the two `handleScheduledRun()` calls in Level 3.

1. The first `handleScheduledRun()` call runs `instrument("syncInventory", "scheduled", () -> {...})` — inside `instrument`, `start` captures the current time, `work.get()` executes the lambda (which calls `syncInventory()` and returns `null`), `end` captures the time after, and a new `Span("syncInventory", "scheduled", start, end)` is appended to `recordedSpans`.
2. The second `handleScheduledRun()` call repeats the identical process — a *new* `start`/`end` pair is captured, and a *second*, independent `Span` object (also named `"syncInventory"`, also tagged `"scheduled"`) is appended to `recordedSpans`.
3. Critically, nothing links these two spans together as part of the same trace — each scheduled invocation is its own independent unit of work with its own trace, unlike, say, a parent HTTP request span with multiple child spans nested inside one single trace; two consecutive `@Scheduled` firings are two entirely separate traces in the real framework too.
4. The final `for` loop over `recordedSpans` prints three lines total: one `"getOrder [web]"` entry from the single HTTP request, and two separate `"syncInventory [scheduled]"` entries from the two scheduled firings — confirming both trigger types were captured, correctly labeled, by the exact same underlying `instrument` mechanism, with the scheduled boundary correctly producing one independent span per execution rather than accumulating into some shared, ongoing span.

```
handleHttpRequest(...) -> instrument("GET /orders/{id}", "web", ...)      -> 1 span recorded
handleScheduledRun()   -> instrument("syncInventory", "scheduled", ...)   -> 1 span recorded (run #1)
handleScheduledRun()   -> instrument("syncInventory", "scheduled", ...)   -> 1 span recorded (run #2, INDEPENDENT of run #1)

recordedSpans: [getOrder(web), syncInventory(scheduled)#1, syncInventory(scheduled)#2]
```

## 7. Gotchas & takeaways

> **Gotcha:** a plain, unannotated method call — one `Function` bean invoked directly in code, a private helper method, a call between two beans with no web/messaging/scheduling boundary between them — gets no automatic span, and a common misconception is expecting Micrometer Tracing to "just trace everything" once it's on the classpath. Auto-instrumentation activates specifically at recognized framework boundaries (a controller method, a message listener, a `@Scheduled` method); genuinely custom internal logic that isn't one of those boundaries needs manual `Tracer` calls (an earlier card) if fine-grained visibility into it is wanted.

- Auto-instrumentation covers the three most common natural "unit of work" boundaries in a typical Spring application — an incoming/outgoing web request, a message consumed or produced, and a scheduled method's execution — with zero manual tracing code required for any of them.
- Because auto-instrumentation is dependency- and configuration-driven rather than code-driven, confirming it's active for a given boundary is mostly a matter of confirming the relevant starter (`spring-boot-starter-web`/`webflux`, a stream binder, `spring-boot-starter` for `@Scheduled` support) plus the tracing bridge dependency are both present.
- A scheduled method's automatic span exists only for the duration of one single invocation — repeated firings produce repeated, independent spans (and independent traces), never one continuously-growing span across multiple executions.
- Manual span creation via the `Tracer` API is complementary to, not a replacement for, auto-instrumentation — it's reached for specifically to add finer-grained visibility *within* an already auto-instrumented boundary (a slow sub-step inside a request handler, say), not to replicate what auto-instrumentation already provides at the boundary itself.
