---
card: microservices
gi: 297
slug: resilience4j-metrics-via-micrometer
title: "Resilience4j metrics via Micrometer"
---

## 1. What it is

Resilience4j publishes detailed metrics about every module's runtime behavior — a circuit breaker's current state, its failure rate, call counts by outcome (successful, failed, not permitted); a retry's attempt counts and success/failure-after-retry counts; a bulkhead's available and max concurrent call counts — through Micrometer, Spring's standard metrics facade. Once registered, these become ordinary Micrometer meters, exportable to Prometheus, Datadog, CloudWatch, or any other backend Micrometer supports, and visible in Spring Boot Actuator's `/actuator/metrics` and `/actuator/prometheus` endpoints alongside every other application metric.

## 2. Why & when

Without metrics, a circuit breaker's behavior is invisible until someone notices its effects indirectly — a spike in fallback responses, a service that seems to be failing more than expected. Metrics make the resilience layer's own internal state directly observable: an operator can build a dashboard showing exactly which circuit breakers are open right now, how close each one's failure rate is to its threshold, and how often retries are actually needed versus how often the first attempt succeeds — turning "is our resilience configuration actually appropriate?" from a guess into a measurable, answerable question.

Use these metrics wherever Resilience4j is used in a Spring Boot application with Actuator and Micrometer already present (the common case) — the registration is largely automatic via `spring-boot-starter-actuator` plus the relevant `resilience4j-micrometer` dependency, requiring no manual instrumentation code for the standard metrics. They are especially valuable for alerting: a circuit breaker sitting open for an extended period, or a failure rate consistently near its threshold, are exactly the kind of conditions worth paging someone about before they become a full outage.

## 3. Core concept

Micrometer's `Tags`-based model attaches labels (like the circuit breaker's name and its state) to each metric, letting a single metric name be filtered and grouped per instance in a dashboard or query.

```java
import io.micrometer.core.instrument.MeterRegistry;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.micrometer.tagged.TaggedCircuitBreakerMetrics;

// This wiring is normally done automatically by Spring Boot's
// auto-configuration once resilience4j-micrometer is on the classpath;
// shown explicitly here to illustrate what's actually happening.
TaggedCircuitBreakerMetrics.ofCircuitBreakerRegistry(circuitBreakerRegistry)
        .bindTo(meterRegistry);

// resulting metrics, queryable by name + tag, e.g.:
//   resilience4j_circuitbreaker_state{name="inventory", state="open"}    -> 0 or 1
//   resilience4j_circuitbreaker_calls{name="inventory", kind="failed"}   -> counter
//   resilience4j_circuitbreaker_failure_rate{name="inventory"}           -> gauge, current %
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Resilience4j's internal event stream for each module feeds into Micrometer meters tagged by instance name; Micrometer exports those meters to whatever monitoring backend is configured, such as Prometheus, making the resilience layer's internal state visible on dashboards and available for alerting">
  <rect x="20" y="55" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="79" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Resilience4j events</text>

  <line x1="160" y1="75" x2="240" y2="75" stroke="#8b949e" marker-end="url(#arr297)"/>
  <rect x="250" y="55" width="140" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="79" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Micrometer meters</text>

  <line x1="390" y1="75" x2="470" y2="75" stroke="#8b949e" marker-end="url(#arr297)"/>
  <rect x="480" y="55" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="79" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Prometheus/dashboard</text>

  <text x="320" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">tagged by instance name -- filterable per dependency</text>
</svg>

Resilience4j's internal events flow through Micrometer into any configured metrics backend, tagged per instance.

## 5. Runnable example

Scenario: a circuit breaker whose state changes are invisible to any monitoring, extended to a hand-rolled stand-in for Micrometer meters that record state and call outcomes as the breaker operates, and finally a small in-memory metrics snapshot/alerting check that flags a circuit breaker sitting open too long or a failure rate near its threshold — the same kind of check a real Prometheus alerting rule would perform against exported Resilience4j metrics.

### Level 1 — Basic

```java
// File: InvisibleCircuitBreakerState.java -- a circuit breaker changes
// state internally, but nothing outside the object can observe that
// change without directly inspecting its Java field.
public class InvisibleCircuitBreakerState {
    enum State { CLOSED, OPEN }
    static class CircuitBreaker {
        State state = State.CLOSED;
        int consecutiveFailures = 0;
        final int threshold = 2;

        <T> T call(java.util.function.Supplier<T> supplier) {
            if (state == State.OPEN) throw new RuntimeException("circuit OPEN");
            try { T r = supplier.get(); consecutiveFailures = 0; return r; }
            catch (Exception e) { consecutiveFailures++; if (consecutiveFailures >= threshold) state = State.OPEN; throw e; }
        }
    }

    public static void main(String[] args) {
        CircuitBreaker cb = new CircuitBreaker();
        for (int i = 1; i <= 3; i++) {
            try { cb.call(() -> { throw new RuntimeException("fail"); }); }
            catch (Exception ignored) {}
        }
        System.out.println("Breaker state is now " + cb.state + ", but NO metric anywhere reflects this -- an operator has no visibility.");
    }
}
```

How to run: `java InvisibleCircuitBreakerState.java`

The circuit breaker trips open after two failures, but this state change exists only as a private Java field — no dashboard, no alert, no metrics endpoint reflects it. An operator watching a monitoring system would see nothing unusual until the *downstream effects* (rising fallback responses, degraded feature) become visible some other way.

### Level 2 — Intermediate

```java
// File: MicrometerStandInMetrics.java -- a hand-rolled stand-in for
// Micrometer's Counter and Gauge types (the real classes are
// io.micrometer.core.instrument.Counter/Gauge, auto-bound by
// resilience4j-micrometer's TaggedCircuitBreakerMetrics in a real Spring
// Boot app) that records state and call outcomes as the breaker runs.
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

public class MicrometerStandInMetrics {
    enum State { CLOSED, OPEN }

    // Stands in for a MeterRegistry: a simple tagged metrics store.
    static class SimpleMeterRegistry {
        final Map<String, AtomicLong> counters = new ConcurrentHashMap<>();
        void increment(String metricName, String tag) {
            counters.computeIfAbsent(metricName + "{" + tag + "}", k -> new AtomicLong()).incrementAndGet();
        }
        long get(String metricName, String tag) {
            return counters.getOrDefault(metricName + "{" + tag + "}", new AtomicLong()).get();
        }
    }

    static class CircuitBreaker {
        State state = State.CLOSED;
        int consecutiveFailures = 0;
        final int threshold = 2;
        final String name; final SimpleMeterRegistry registry;

        CircuitBreaker(String name, SimpleMeterRegistry registry) { this.name = name; this.registry = registry; }

        <T> T call(java.util.function.Supplier<T> supplier) {
            if (state == State.OPEN) {
                registry.increment("resilience4j_circuitbreaker_calls", "name=" + name + ",kind=not_permitted");
                throw new RuntimeException("circuit OPEN");
            }
            try {
                T r = supplier.get();
                consecutiveFailures = 0;
                registry.increment("resilience4j_circuitbreaker_calls", "name=" + name + ",kind=successful");
                return r;
            } catch (Exception e) {
                consecutiveFailures++;
                registry.increment("resilience4j_circuitbreaker_calls", "name=" + name + ",kind=failed");
                if (consecutiveFailures >= threshold) {
                    state = State.OPEN;
                    registry.increment("resilience4j_circuitbreaker_state_transitions", "name=" + name + ",to=open");
                }
                throw e;
            }
        }
    }

    public static void main(String[] args) {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        CircuitBreaker cb = new CircuitBreaker("inventory", registry);
        for (int i = 1; i <= 4; i++) {
            try { cb.call(() -> { throw new RuntimeException("fail"); }); } catch (Exception ignored) {}
        }
        System.out.println("failed calls: " + registry.get("resilience4j_circuitbreaker_calls", "name=inventory,kind=failed"));
        System.out.println("not_permitted calls: " + registry.get("resilience4j_circuitbreaker_calls", "name=inventory,kind=not_permitted"));
        System.out.println("state transitions to OPEN: " + registry.get("resilience4j_circuitbreaker_state_transitions", "name=inventory,to=open"));
    }
}
```

How to run: `java MicrometerStandInMetrics.java`

Every call outcome now increments a correspondingly tagged counter in the `SimpleMeterRegistry` stand-in, mirroring the real metric names Resilience4j's `TaggedCircuitBreakerMetrics` registers via Micrometer. The printed counts show 2 failed calls (which tripped the breaker) and 2 not-permitted calls (short-circuited after it opened), plus exactly 1 state transition to open — this is precisely the shape of data a real Prometheus query against `resilience4j_circuitbreaker_calls_total{name="inventory"}` would return, now visible and queryable instead of trapped inside a private field.

### Level 3 — Advanced

```java
// File: AlertingOnMetrics.java -- takes a snapshot of the recorded
// metrics and runs simple alerting-style checks against them, mirroring
// what a real Prometheus alerting rule evaluating exported Resilience4j
// metrics would do: flag a circuit breaker that has been open too long,
// and flag one whose failure rate is dangerously close to its threshold.
import java.util.*;

public class AlertingOnMetrics {
    record CircuitBreakerSnapshot(String name, String state, long openedAtEpochSeconds,
                                    long totalCalls, long failedCalls, int failureRateThreshold) {
        double currentFailureRatePercent() { return totalCalls == 0 ? 0 : 100.0 * failedCalls / totalCalls; }
    }

    static List<String> evaluateAlerts(CircuitBreakerSnapshot snapshot, long nowEpochSeconds) {
        List<String> alerts = new ArrayList<>();
        if ("OPEN".equals(snapshot.state())) {
            long openDurationSeconds = nowEpochSeconds - snapshot.openedAtEpochSeconds();
            if (openDurationSeconds > 300) {
                alerts.add("ALERT: circuit '" + snapshot.name() + "' has been OPEN for " + openDurationSeconds
                        + "s (> 5min) -- dependency may need manual intervention");
            }
        }
        double rate = snapshot.currentFailureRatePercent();
        if (rate >= snapshot.failureRateThreshold() * 0.8 && rate < snapshot.failureRateThreshold()) {
            alerts.add("WARNING: circuit '" + snapshot.name() + "' failure rate " + String.format("%.1f", rate)
                    + "% is approaching its " + snapshot.failureRateThreshold() + "% threshold -- may trip soon");
        }
        return alerts;
    }

    public static void main(String[] args) {
        long now = 1_700_000_000L;
        List<CircuitBreakerSnapshot> snapshots = List.of(
                new CircuitBreakerSnapshot("inventory", "OPEN", now - 400, 50, 30, 50),   // open 400s, past 5min
                new CircuitBreakerSnapshot("reporting", "CLOSED", 0, 100, 42, 50),         // 42% approaching 50% threshold
                new CircuitBreakerSnapshot("payments", "CLOSED", 0, 100, 5, 50)            // healthy, well below threshold
        );

        for (CircuitBreakerSnapshot snapshot : snapshots) {
            List<String> alerts = evaluateAlerts(snapshot, now);
            if (alerts.isEmpty()) {
                System.out.println(snapshot.name() + ": OK (rate=" + String.format("%.1f", snapshot.currentFailureRatePercent()) + "%)");
            } else {
                alerts.forEach(System.out::println);
            }
        }
    }
}
```

How to run: `java AlertingOnMetrics.java`

Three circuit breaker snapshots are evaluated against simple alerting logic. `inventory` has been open for 400 seconds, past the 5-minute threshold, triggering a hard alert suggesting manual intervention may be needed. `reporting` is still closed but its failure rate (42%) has crossed 80% of its 50% trip threshold, triggering an early warning before it actually opens. `payments` is healthy and produces no alerts at all. This is the practical payoff of exporting Resilience4j state via Micrometer: real alerting rules (in Prometheus Alertmanager, Grafana, or similar) can be written directly against these metrics, catching problems — a stuck-open circuit, a dependency trending toward failure — before or as they happen, rather than relying on someone noticing degraded behavior after the fact.

## 6. Walkthrough

Trace `AlertingOnMetrics.main` for the `"inventory"` snapshot. **First**, the snapshot is constructed with `state="OPEN"`, `openedAtEpochSeconds = now - 400` (opened 400 seconds before the current evaluation time), `totalCalls=50`, `failedCalls=30`, `failureRateThreshold=50`.

**`evaluateAlerts(snapshot, now)` is called.** Inside, the first check is `if ("OPEN".equals(snapshot.state()))` — true. This computes `openDurationSeconds = now - snapshot.openedAtEpochSeconds() = now - (now - 400) = 400`. The check `openDurationSeconds > 300` (5 minutes) is true, so a hard `"ALERT:"` string is appended to the `alerts` list, naming the circuit and how long it's been open.

**Next**, regardless of the open-state check's outcome, the failure-rate check runs: `rate = snapshot.currentFailureRatePercent()`, computed as `100.0 * 30 / 50 = 60.0`. The condition `rate >= threshold * 0.8 && rate < threshold` evaluates `60.0 >= 40.0 && 60.0 < 50.0` — the second half is `false` (60 is not less than 50, since the breaker is already open and past its threshold), so no additional warning is appended for this snapshot; only the hard "stuck open" alert applies.

**Back in `main`**, `alerts` for `"inventory"` is non-empty, so the `alerts.forEach(System.out::println)` branch prints the single ALERT line.

**For `"reporting"`**, `state` is `"CLOSED"`, so the first `if` block is skipped entirely — no "stuck open" check applies to a closed breaker. The failure-rate check computes `rate = 100.0 * 42 / 100 = 42.0`; the condition `42.0 >= 40.0 && 42.0 < 50.0` is `true` on both sides, so a `"WARNING:"` string is appended, flagging that this circuit is trending toward its threshold even though it hasn't tripped yet.

**For `"payments"`**, `rate = 100.0 * 5 / 100 = 5.0`, which fails both parts of the warning condition (`5.0 >= 40.0` is false), so `alerts` stays empty and `main` prints the plain "OK" line instead.

```
inventory: OPEN, 400s elapsed > 300s threshold -> hard ALERT
reporting: CLOSED, rate=42% within [40%, 50%) band -> early WARNING
payments:  CLOSED, rate=5%, well below the warning band -> OK, no alert
```

## 7. Gotchas & takeaways

> A circuit breaker's `failure_rate` metric is only meaningful once `minimumNumberOfCalls` has been reached within the current sliding window — querying or alerting on it before enough calls have occurred can show a misleadingly extreme percentage (e.g., 100% after just one failed call out of one total call), producing false alerts if this nuance isn't accounted for.

- Resilience4j's Micrometer integration is largely automatic in a Spring Boot app once `spring-boot-starter-actuator` and the relevant Resilience4j starter are present — no manual instrumentation code is typically needed for the standard metrics.
- Build dashboards and alerts specifically around circuit breaker state transitions and sustained "stuck open" duration — these are strong, specific, actionable signals, unlike raw request-level error rates which conflate many possible causes.
- An "approaching threshold" early-warning alert (as in Level 3) gives operators a chance to investigate before a circuit actually trips, rather than only being notified after user-facing degradation has already begun.
- Because metrics are tagged by instance name, the same dashboard/alerting rule template can apply uniformly across every named circuit breaker, retry, and bulkhead instance in the application, rather than needing bespoke monitoring per dependency.
