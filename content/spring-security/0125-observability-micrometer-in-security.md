---
card: spring-security
gi: 125
slug: observability-micrometer-in-security
title: "Observability (Micrometer) in security"
---

## 1. What it is

Spring Security integrates with Micrometer's Observation API to emit structured, vendor-neutral telemetry — metrics and distributed tracing spans — around security-relevant operations: authentication attempts, authorization decisions, and filter chain execution, among others. Rather than each application writing its own logging or metrics code around `AuthenticationManager.authenticate(...)` calls, `ObservationRegistry`-aware components (wired in automatically by Spring Boot when a `Micrometer`/`ObservationRegistry` bean and a tracing implementation are on the classpath) wrap these operations in named `Observation`s that any registered `MeterRegistry` (Prometheus, for instance) or tracer (Zipkin, OpenTelemetry) can pick up without Spring Security needing to know which specific observability backend is in use.

```java
@Bean
public ObservationRegistry observationRegistry() {
    ObservationRegistry registry = ObservationRegistry.create();
    registry.observationConfig()
            .observationHandler(new DefaultMeterObservationHandler(meterRegistry))
            .observationHandler(new PropagatingSenderTracingObservationHandler<>(tracer, propagator));
    return registry;
}
```
```
# example resulting metric (exposed via /actuator/prometheus)
spring_security_authentications_total{result="success"} 1523
spring_security_authentications_total{result="failure"} 47
spring_security_authorizations_total{result="granted"} 8901
spring_security_authorizations_total{result="denied"} 12
```

## 2. Why & when

Nearly every card in this course has covered *what* Spring Security does — which filter runs, which exception fires, which principal gets built — but a running production application needs to know, continuously and in aggregate, *how often* each of these things happens: how many authentication attempts are failing (a spike might mean a credential-stuffing attack, or an outage at an upstream identity provider), how long authorization decisions take (a slow `AuthorizationManager` implementation dragging down every request), and where security-related latency sits within a broader distributed trace spanning multiple services. Micrometer's Observation API is Spring's standard mechanism for exactly this kind of cross-cutting instrumentation — the same abstraction used for HTTP request metrics, database query timing, and message broker instrumentation — and Spring Security's integration means security operations get the same first-class observability treatment without bespoke, hand-rolled instrumentation in every application.

Reach for Spring Security's observability integration when:

- Running any production deployment where visibility into authentication/authorization failure rates matters for security monitoring — a sudden spike in failed authentication attempts against one account is a classic brute-force or credential-stuffing signal worth alerting on.
- Debugging latency in a request that passes through several security checks (authentication, multiple authorization rules, a slow custom `AuthorizationManager`) — distributed tracing spans around each step make it possible to see exactly where time is spent, rather than treating "security" as one opaque block of the request's total latency.
- Building dashboards or alerts around authentication/authorization health as part of a broader application observability strategy already using Micrometer/Prometheus/Grafana or a tracing backend like Zipkin/Jaeger.
- Auditing which specific security operations are instrumented by default versus which require custom `Observation` calls added to bespoke `AuthenticationProvider`/`AuthorizationManager` implementations.

## 3. Core concept

```
Micrometer Observation, conceptually:
    an Observation wraps ONE operation (e.g. "authenticate this request")
    it has a NAME, CONTEXTUAL key-value tags (e.g. result=success/failure), and a DURATION
    ObservationHandlers subscribed to the registry decide WHAT to do with each observation:
        DefaultMeterObservationHandler       -> emits a METRIC (counter, timer)
        PropagatingSenderTracingObservationHandler -> emits/propagates a TRACING SPAN

Spring Security's observed operations (when observability support is enabled):
    authentication  -- wraps AuthenticationManager.authenticate(...)
        tags include: authentication result (success/failure), exception type on failure
    authorization   -- wraps AuthorizationManager.authorize(...)
        tags include: decision (granted/denied)

ONE observation, MULTIPLE outputs:
    the SAME "authenticate this request" event can simultaneously:
        - increment a Prometheus counter (spring_security_authentications_total)
        - create a tracing span visible in Zipkin/Jaeger, nested within the overall request's trace
    -- Spring Security's code only creates the Observation ONCE; how many and which
       backends actually consume it is entirely a matter of what's registered, decoupled
       from the instrumented code itself.
```

This decoupling — instrument once, consume via any number of registered handlers — is the entire value proposition of the Observation API over hand-rolled, backend-specific instrumentation scattered through application code.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing an authentication attempt wrapped in a single Observation which is then consumed by both a meter handler producing a prometheus counter and a tracing handler producing a span in a distributed trace both derived from the same one instrumented event">
  <rect x="20" y="90" width="180" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="110" y="110" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">AuthenticationManager</text>
  <text x="110" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.authenticate(...)</text>

  <line x1="200" y1="115" x2="245" y2="115" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#ob125)"/>

  <rect x="250" y="90" width="160" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.4"/>
  <text x="330" y="110" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">ONE Observation</text>
  <text x="330" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">name + tags + duration</text>

  <line x1="330" y1="90" x2="255" y2="40" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ob125b)"/>
  <line x1="330" y1="140" x2="255" y2="190" stroke="#f0883e" stroke-width="1.5" marker-end="url(#ob125c)"/>

  <rect x="20" y="10" width="230" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="135" y="35" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Prometheus counter/timer</text>

  <rect x="20" y="170" width="230" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.4"/>
  <text x="135" y="195" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Tracing span (Zipkin/OTel)</text>

  <defs>
    <marker id="ob125" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="ob125b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ob125c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

One instrumented event, fanned out to as many observability backends as are registered — the instrumented code never needs to know how many, or which.

## 5. Runnable example

The scenario: a from-scratch Observation-style wrapper around an authentication call, growing from a single metric-emitting handler into multiple simultaneous handlers (metrics and tracing), then into using the recorded tags to demonstrate a real, actionable signal — detecting a spike in failed authentication attempts against one account.

### Level 1 — Basic

Wrap an authentication attempt, emit a simple counter.

```java
import java.util.*;
import java.util.concurrent.atomic.*;

public class ObservabilityLevel1 {
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String message) { super(message); }
    }

    static class Counter {
        private final Map<String, AtomicInteger> countsByTag = new HashMap<>();
        void increment(String tagValue) { countsByTag.computeIfAbsent(tagValue, k -> new AtomicInteger()).incrementAndGet(); }
        int get(String tagValue) { return countsByTag.getOrDefault(tagValue, new AtomicInteger()).get(); }
    }

    // mirrors an "Observation" around AuthenticationManager.authenticate(...)
    static String authenticateObserved(String username, String password, Map<String, String> validCredentials, Counter counter) {
        try {
            if (!password.equals(validCredentials.get(username))) throw new AuthenticationException("Bad credentials");
            counter.increment("success");
            return username;
        } catch (AuthenticationException e) {
            counter.increment("failure");
            throw e;
        }
    }

    public static void main(String[] args) {
        Counter authCounter = new Counter();
        Map<String, String> validCredentials = Map.of("alice", "secret123");

        authenticateObserved("alice", "secret123", validCredentials, authCounter);
        try { authenticateObserved("alice", "WRONG", validCredentials, authCounter); } catch (AuthenticationException ignored) {}
        try { authenticateObserved("alice", "WRONG-AGAIN", validCredentials, authCounter); } catch (AuthenticationException ignored) {}

        System.out.println("spring_security_authentications_total{result=success} " + authCounter.get("success"));
        System.out.println("spring_security_authentications_total{result=failure} " + authCounter.get("failure"));
    }
}
```

**How to run:** save as `ObservabilityLevel1.java`, run `java ObservabilityLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
spring_security_authentications_total{result=success} 1
spring_security_authentications_total{result=failure} 2
```

`authenticateObserved` mirrors the instrumentation Spring Security wraps around a real `AuthenticationManager` call — every attempt, successful or not, increments the appropriate counter, exactly the shape of the Prometheus-style metric a `DefaultMeterObservationHandler` would emit from a real `Observation`.

### Level 2 — Intermediate

Multiple handlers consuming the *same* observed event — a metric handler and a tracing-style handler recording a span — demonstrating the fan-out the Observation API is built around.

```java
import java.util.*;
import java.util.concurrent.atomic.*;
import java.util.function.*;

public class ObservabilityLevel2 {
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String message) { super(message); }
    }
    record Span(String name, String result, long durationMillis) {}

    interface ObservationHandler { void onComplete(String result, long durationMillis); }

    static class MeterHandler implements ObservationHandler {
        private final Map<String, AtomicInteger> counts = new HashMap<>();
        public void onComplete(String result, long durationMillis) {
            counts.computeIfAbsent(result, k -> new AtomicInteger()).incrementAndGet();
        }
        int get(String result) { return counts.getOrDefault(result, new AtomicInteger()).get(); }
    }

    static class TracingHandler implements ObservationHandler {
        final List<Span> recordedSpans = new ArrayList<>();
        public void onComplete(String result, long durationMillis) {
            recordedSpans.add(new Span("authenticate", result, durationMillis));
        }
    }

    // ONE observed operation, fanning out to EVERY registered handler
    static String authenticateObserved(String username, String password, Map<String, String> validCredentials,
                                        List<ObservationHandler> handlers) {
        long start = System.nanoTime();
        String result;
        try {
            if (!password.equals(validCredentials.get(username))) throw new AuthenticationException("Bad credentials");
            result = "success";
            return username;
        } catch (AuthenticationException e) {
            result = "failure";
            throw e;
        } finally {
            long durationMillis = (System.nanoTime() - start) / 1_000_000;
            for (ObservationHandler handler : handlers) handler.onComplete(result, durationMillis); // FAN OUT
        }
    }

    public static void main(String[] args) {
        MeterHandler meterHandler = new MeterHandler();
        TracingHandler tracingHandler = new TracingHandler();
        List<ObservationHandler> handlers = List.of(meterHandler, tracingHandler); // BOTH registered

        Map<String, String> validCredentials = Map.of("alice", "secret123");

        authenticateObserved("alice", "secret123", validCredentials, handlers);
        try { authenticateObserved("alice", "WRONG", validCredentials, handlers); } catch (AuthenticationException ignored) {}

        System.out.println("metric counter -- success: " + meterHandler.get("success") + ", failure: " + meterHandler.get("failure"));
        System.out.println("tracing spans recorded: " + tracingHandler.recordedSpans().size());
        for (Span span : tracingHandler.recordedSpans()) {
            System.out.println("  span: name=" + span.name() + " result=" + span.result());
        }
    }
}
```

**How to run:** save as `ObservabilityLevel2.java`, run `java ObservabilityLevel2.java` (JDK 17+ runs single files directly).

Expected output (durations vary, span count and results are the point):
```
metric counter -- success: 1, failure: 1
tracing spans recorded: 2
  span: name=authenticate result=success
  span: name=authenticate result=failure
```

What changed: `authenticateObserved` now fans out to a *list* of handlers rather than incrementing one hard-coded counter — both `MeterHandler` and `TracingHandler` receive the exact same underlying event, but each does something entirely different with it, exactly mirroring how a real `ObservationRegistry` can have both a `DefaultMeterObservationHandler` and a tracing handler registered simultaneously, with the instrumented `AuthenticationManager` code never needing to know either exists.

### Level 3 — Advanced

Use the recorded, tagged observations to derive a real, actionable security signal — detecting an abnormal spike in failed authentication attempts against one specific username, the kind of pattern a real dashboard or alert built on these metrics would surface.

```java
import java.util.*;
import java.util.concurrent.atomic.*;

public class ObservabilityLevel3 {
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String message) { super(message); }
    }
    record AuthEvent(String username, String result, long timestampMillis) {}

    static class SecurityObservationRecorder {
        private final List<AuthEvent> events = new ArrayList<>();

        void record(String username, String result) {
            events.add(new AuthEvent(username, result, System.currentTimeMillis()));
        }

        // mirrors a dashboard QUERY over the recorded metric/tracing data --
        // "how many failed attempts against THIS username in the recent window?"
        long countRecentFailures(String username, long windowMillis) {
            long now = System.currentTimeMillis();
            return events.stream()
                    .filter(e -> e.username().equals(username))
                    .filter(e -> "failure".equals(e.result()))
                    .filter(e -> now - e.timestampMillis() <= windowMillis)
                    .count();
        }
    }

    static String authenticateObserved(String username, String password, Map<String, String> validCredentials,
                                        SecurityObservationRecorder recorder) {
        try {
            if (!password.equals(validCredentials.get(username))) throw new AuthenticationException("Bad credentials");
            recorder.record(username, "success");
            return username;
        } catch (AuthenticationException e) {
            recorder.record(username, "failure");
            throw e;
        }
    }

    public static void main(String[] args) {
        SecurityObservationRecorder recorder = new SecurityObservationRecorder();
        Map<String, String> validCredentials = Map.of("alice", "secret123", "bob", "hunter2");

        // an attacker repeatedly guessing alice's password
        for (int i = 0; i < 8; i++) {
            try { authenticateObserved("alice", "guess" + i, validCredentials, recorder); }
            catch (AuthenticationException ignored) {}
        }
        // bob logging in normally, one legitimate failed typo, then success
        try { authenticateObserved("bob", "wrong-typo", validCredentials, recorder); } catch (AuthenticationException ignored) {}
        authenticateObserved("bob", "hunter2", validCredentials, recorder);

        long aliceFailures = recorder.countRecentFailures("alice", 60_000);
        long bobFailures = recorder.countRecentFailures("bob", 60_000);

        int alertThreshold = 5;
        System.out.println("alice: " + aliceFailures + " recent failures"
                + (aliceFailures >= alertThreshold ? " -- ALERT: possible credential-stuffing attempt" : ""));
        System.out.println("bob: " + bobFailures + " recent failures"
                + (bobFailures >= alertThreshold ? " -- ALERT" : " -- normal"));
    }
}
```

**How to run:** save as `ObservabilityLevel3.java`, run `java ObservabilityLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
alice: 8 recent failures -- ALERT: possible credential-stuffing attempt
bob: 1 recent failures -- normal
```

What changed: `countRecentFailures` derives a genuinely actionable security signal from the accumulated observation data — alice's eight rapid failed attempts cross the alert threshold, while bob's single, ordinary typo followed by a successful login does not — this is exactly the kind of query a real dashboard or alerting rule (built atop the `spring_security_authentications_total{result="failure"}` metric, filtered or grouped by a username tag if the observation includes one) would run continuously in production to surface credential-stuffing or brute-force attempts.

## 6. Walkthrough

Trace alice's eighth failed attempt through the full observation pipeline, from the raw authentication call to the alerting signal.

**Step 1 — the eighth login attempt with a wrong password:**
```
POST /login HTTP/1.1

username=alice&password=guess7
```

**Step 2 — `AuthenticationManager.authenticate(...)` is invoked, wrapped in an Observation** (in the real integration; corresponding to `authenticateObserved("alice", "guess7", validCredentials, recorder)` in Level 3). The password check fails, `AuthenticationException` is thrown.

**Step 3 — the observation records the outcome before the exception propagates further.** `recorder.record("alice", "failure")` runs in the `catch` block, appending a new `AuthEvent("alice", "failure", <current timestamp>)` to the recorder's list — mirroring how the real `Observation` captures the `result=failure` tag at the point the wrapped operation completes (successfully or not), regardless of what happens to the exception afterward.

**Step 4 — in a real deployment, this same event fans out to every registered handler simultaneously** — a `DefaultMeterObservationHandler` increments `spring_security_authentications_total{result="failure"}` in the application's Prometheus registry, and (if tracing is configured) a span named something like `spring.security.authentications` is recorded, nested within the overall HTTP request's trace, carrying the same `result=failure` tag.

**Step 5 — a monitoring query (Level 3's `countRecentFailures`, standing in for a real Prometheus alerting rule or dashboard panel) aggregates these events over a time window.** Filtering for `username=alice`, `result=failure`, within the last 60 seconds, finds all eight of alice's failed attempts.

**Step 6 — the alert fires.** `aliceFailures (8) >= alertThreshold (5)` is `true`, printing the credential-stuffing warning — in a real production system, this would instead trigger a PagerDuty alert, a Slack notification, or an automated response (temporarily rate-limiting further attempts against that account), all derived from metrics Spring Security emitted automatically, with zero custom instrumentation code required in the application beyond registering the observability handlers themselves.

```
8x failed authenticate("alice", ...) calls
        |
        v (each wrapped in an Observation, tagged result=failure)
metric: spring_security_authentications_total{result="failure"} incremented 8 times
        |
        v (a dashboard/alerting query, run continuously in production)
countRecentFailures("alice", 60s) = 8  >=  threshold (5)  -> ALERT fires
```

## 7. Gotchas & takeaways

> **Gotcha:** observability data (metrics, traces) is only as useful as the granularity of its tags — a metric counting *total* authentication failures across the whole application, without a per-username or per-source-IP dimension, cannot distinguish "one account under sustained attack" from "many accounts each failing once, normally, due to typos." Designing which tags an observation carries (and being mindful of cardinality — a raw username as a metric tag can create an unbounded number of distinct time series in some backends) is a real design decision, not an afterthought.

- Spring Security's Micrometer integration wraps security-relevant operations (authentication, authorization) in `Observation`s that any number of registered handlers can consume independently — the instrumented code itself never needs to know which observability backends are actually in use.
- The same single observed event can simultaneously produce a metric (for dashboards, alerting thresholds) and a tracing span (for understanding where time is spent within a broader distributed request trace) — this fan-out is the core value of the Observation API over backend-specific, hand-rolled instrumentation.
- A spike in authentication failures, especially concentrated against one account or one source, is a classic, actionable security signal that these metrics make straightforward to detect and alert on in production.
- Tag design (what dimensions an observation carries) directly determines what questions the resulting metrics and traces can actually answer — insufficient granularity limits what a monitoring team can distinguish after the fact.
- This observability layer is purely additive — enabling or disabling it changes nothing about actual authentication or authorization *behavior*; it only affects what telemetry is produced about operations that would happen identically either way.
