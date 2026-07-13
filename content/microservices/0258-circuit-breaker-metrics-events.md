---
card: microservices
gi: 258
slug: circuit-breaker-metrics-events
title: "Circuit breaker metrics & events"
---

## 1. What it is

Circuit breaker metrics and events are the observable signals a circuit breaker emits about its own internal state and decisions — state transitions (closed to open, open to half-open), individual call outcomes, and aggregate statistics (current failure rate, current slow-call rate) — exposed so that monitoring, alerting, and dashboards can track the breaker's behavior, rather than the breaker's protective logic operating as an invisible black box.

## 2. Why & when

A circuit breaker that silently trips and silently recovers, with nothing observing or recording that either event happened, turns a genuinely important signal — "a dependency just failed badly enough to warrant protection" — into something no one notices until a downstream symptom (missing data on a page, a support ticket) eventually surfaces it, likely much later and with much less context than the breaker itself had in the moment. Emitting metrics and events for every state transition and, more granularly, every individual call decision, lets operators build alerts ("page someone the moment any breaker trips"), dashboards (breaker state across every protected dependency, at a glance), and post-incident timelines (exactly when a dependency started failing, when the breaker reacted, and when it recovered) directly from the breaker's own authoritative record of what happened.

Wire circuit breaker events into monitoring and alerting for any breaker protecting a meaningfully important dependency — a tripped breaker is exactly the kind of event that should be visible immediately, not discovered indirectly through its downstream effects. This is standard practice with production libraries like Resilience4j, which expose a rich event stream specifically for this purpose.

## 3. Core concept

The breaker publishes an event (or updates a metric) at each meaningful moment in its lifecycle — a state transition, a recorded success, a recorded failure, a rejected call — and external listeners (a metrics registry, a logging statement, an alerting rule) subscribe to these events without needing to poll the breaker's state directly.

```java
CircuitBreaker breaker = CircuitBreaker.of("inventory-service", config);

breaker.getEventPublisher()
    .onStateTransition(event -> log.warn("Breaker {} transitioned {} -> {}",
        event.getCircuitBreakerName(), event.getStateTransition().getFromState(), event.getStateTransition().getToState()))
    .onFailureRateExceeded(event -> alertingService.page("Circuit breaker " + event.getCircuitBreakerName() + " exceeded failure rate threshold"))
    .onCallNotPermitted(event -> metrics.increment("circuit_breaker.rejected", "name", event.getCircuitBreakerName()));
// EVERY transition and decision is now OBSERVABLE, not a silent internal detail
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circuit breaker's internal state transitions and call decisions each publish an event to subscribed listeners -- a logging system, a metrics registry, and an alerting service -- turning what would otherwise be invisible internal behavior into observable, actionable signals" >
  <rect x="20" y="65" width="150" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Circuit breaker</text>

  <rect x="260" y="20" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="325" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Logging</text>

  <rect x="260" y="80" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="325" y="102" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Metrics registry</text>

  <rect x="260" y="130" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="325" y="152" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Alerting service</text>

  <line x1="170" y1="80" x2="258" y2="38" stroke="#8b949e" marker-end="url(#arr258)"/>
  <line x1="170" y1="88" x2="258" y2="97" stroke="#8b949e" marker-end="url(#arr258)"/>
  <line x1="170" y1="95" x2="258" y2="147" stroke="#8b949e" marker-end="url(#arr258)"/>

  <defs>
    <marker id="arr258" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

One internal event fans out to multiple independent observers, each using it for a different purpose.

## 5. Runnable example

Scenario: a circuit breaker whose state transitions happen with no observability at all (invisible from the outside), refactored to publish events on every transition to registered listeners, and finally demonstrating multiple independent listeners (a log, a counter, an alert trigger) all reacting to the same underlying events without needing to modify the breaker's core logic to add each one.

### Level 1 — Basic

```java
// File: SilentBreaker.java -- the breaker trips and recovers with
// ABSOLUTELY NO observable signal -- invisible from the outside.
public class SilentBreaker {
    enum State { CLOSED, OPEN }
    static State state = State.CLOSED;
    static int consecutiveFailures = 0;

    static void recordFailure() {
        if (++consecutiveFailures >= 3) state = State.OPEN; // trips SILENTLY -- nothing observes this
    }

    public static void main(String[] args) {
        for (int i = 0; i < 3; i++) recordFailure();
        System.out.println("Breaker state: " + state);
        System.out.println("This transition happened with ZERO observable signal -- no log, no metric, no alert.");
        System.out.println("An operator would have NO WAY to know this happened without manually checking `state`.");
    }
}
```

**How to run:** `javac SilentBreaker.java && java SilentBreaker` (JDK 17+).

### Level 2 — Intermediate

```java
// File: EventPublishingBreaker.java -- publishes an EVENT on every state
// transition; a REGISTERED listener reacts to it -- now OBSERVABLE.
import java.util.*;
import java.util.function.*;

public class EventPublishingBreaker {
    enum State { CLOSED, OPEN }
    record StateTransitionEvent(String breakerName, State from, State to) {}

    static State state = State.CLOSED;
    static int consecutiveFailures = 0;
    static List<Consumer<StateTransitionEvent>> listeners = new ArrayList<>();

    static void onStateTransition(Consumer<StateTransitionEvent> listener) { listeners.add(listener); }

    static void transitionTo(State newState) {
        State oldState = state;
        state = newState;
        StateTransitionEvent event = new StateTransitionEvent("inventory-service", oldState, newState);
        for (Consumer<StateTransitionEvent> listener : listeners) listener.accept(event); // PUBLISH to all listeners
    }

    static void recordFailure() {
        if (++consecutiveFailures >= 3) transitionTo(State.OPEN); // now goes through the PUBLISHING path
    }

    public static void main(String[] args) {
        onStateTransition(event -> System.out.println("  [LOG] " + event.breakerName() + " transitioned " + event.from() + " -> " + event.to()));

        for (int i = 0; i < 3; i++) recordFailure();
        System.out.println("Final state: " + state + " -- and the transition was OBSERVED via the registered listener.");
    }
}
```

**How to run:** `javac EventPublishingBreaker.java && java EventPublishingBreaker` (JDK 17+).

Expected output:
```
  [LOG] inventory-service transitioned CLOSED -> OPEN
Final state: OPEN -- and the transition was OBSERVED via the registered listener.
```

### Level 3 — Advanced

```java
// File: MultipleIndependentListeners.java -- THREE independent listeners
// (log, metrics counter, alert trigger) all react to the SAME events,
// with NO changes needed to the breaker's core logic to add each one.
import java.util.*;
import java.util.function.*;

public class MultipleIndependentListeners {
    enum State { CLOSED, OPEN, HALF_OPEN }
    record StateTransitionEvent(String breakerName, State from, State to) {}

    static State state = State.CLOSED;
    static int consecutiveFailures = 0;
    static List<Consumer<StateTransitionEvent>> listeners = new ArrayList<>();
    static Map<String, Integer> metricsCounters = new HashMap<>(); // simulates a METRICS REGISTRY
    static List<String> alertsFired = new ArrayList<>(); // simulates an ALERTING SERVICE

    static void onStateTransition(Consumer<StateTransitionEvent> listener) { listeners.add(listener); }

    static void transitionTo(State newState) {
        State oldState = state;
        state = newState;
        StateTransitionEvent event = new StateTransitionEvent("inventory-service", oldState, newState);
        for (Consumer<StateTransitionEvent> listener : listeners) listener.accept(event);
    }

    static void recordFailure() { if (++consecutiveFailures >= 3) transitionTo(State.OPEN); }

    public static void main(String[] args) {
        // THREE SEPARATE listeners, each added INDEPENDENTLY, each serving a DIFFERENT purpose
        onStateTransition(event -> System.out.println("  [LOG] " + event.from() + " -> " + event.to())); // logging
        onStateTransition(event -> metricsCounters.merge("breaker.transitions." + event.to(), 1, Integer::sum)); // metrics
        onStateTransition(event -> { if (event.to() == State.OPEN) alertsFired.add("PAGE: " + event.breakerName() + " tripped open!"); }); // alerting

        for (int i = 0; i < 3; i++) recordFailure();

        System.out.println("\nMetrics recorded: " + metricsCounters);
        System.out.println("Alerts fired: " + alertsFired);
        System.out.println("\nALL THREE listeners reacted to the SAME single event -- none needed to modify the breaker's core trip logic.");
    }
}
```

**How to run:** `javac MultipleIndependentListeners.java && java MultipleIndependentListeners` (JDK 17+).

Expected output:
```
  [LOG] CLOSED -> OPEN

Metrics recorded: {breaker.transitions.OPEN=1}
Alerts fired: [PAGE: inventory-service tripped open!]

ALL THREE listeners reacted to the SAME single event -- none needed to modify the breaker's core trip logic.
```

## 6. Walkthrough

1. **Level 1, complete invisibility** — `recordFailure` mutates `state` directly with no external notification of any kind; the only way to observe the transition happened is to directly inspect the `state` field afterward, which is exactly what `main` does here for demonstration purposes — a real operator monitoring a running system has no equivalent direct access to inspect internal state on demand.
2. **Level 2, introducing a publish-subscribe mechanism** — `listeners` holds a list of callback functions, `onStateTransition` registers new ones, and `transitionTo` (now the single place that actually changes `state`) constructs a `StateTransitionEvent` and passes it to every registered listener immediately after the change.
3. **Level 2, the observable outcome** — the single registered listener prints a log line the moment the transition occurs, meaning an external observer (a real logging system, in production) now has a direct, immediate record of exactly when and how the state changed, without needing to poll or directly inspect the breaker's internals.
4. **Level 3, three genuinely independent purposes** — the logging listener, the metrics-counting listener, and the alerting listener are each registered via separate, independent `onStateTransition` calls; none of them know about or depend on the others, and none of them required any modification to `transitionTo` or `recordFailure` to be added.
5. **Level 3, each listener extracting different information from the identical event** — the metrics listener increments a counter keyed by the *destination* state (`breaker.transitions.OPEN`), useful for tracking transition frequency over time, while the alerting listener specifically checks `event.to() == State.OPEN` to decide whether this particular transition warrants paging someone — two very different consumers deriving two very different actions from the same underlying `StateTransitionEvent`.
6. **Level 3, why this extensibility matters** — adding a fourth, fifth, or tenth listener (a dashboard update, a distributed trace annotation, a Slack notification) would follow the exact same pattern: one more call to `onStateTransition`, with zero changes required to `transitionTo` or `recordFailure` themselves — this is precisely the value of an event-based observability model over ad-hoc, hard-coded notification logic scattered directly inside the breaker's core state-management code.

## 7. Gotchas & takeaways

> **Gotcha:** listeners that perform slow or blocking work (a synchronous network call to an alerting service, for instance) directly inside an event callback can slow down or even block the circuit breaker's own call-handling path, since the event is typically published synchronously as part of processing the triggering call; production event handlers for anything non-trivial (like actually paging someone) should generally hand off to an asynchronous queue or a separate thread rather than performing the slow work inline within the listener callback itself.

- Circuit breaker metrics and events expose state transitions, call outcomes, and aggregate statistics as observable signals, rather than leaving the breaker's protective logic as an invisible internal detail.
- A tripped breaker with no observability wired to it means the protection is working, but no one knows it triggered until a downstream symptom eventually surfaces the underlying problem, likely much later.
- An event-publishing design lets multiple independent consumers (logging, metrics, alerting) react to the same underlying events without any of them needing to modify the breaker's core state-management logic.
- Each listener can extract different, purpose-specific information from the same event — a metrics listener counting by destination state, an alerting listener filtering specifically for transitions to open.
- Slow or blocking work inside an event listener can affect the breaker's own call-handling performance, since events are typically published synchronously; genuinely slow listener work should be handed off asynchronously rather than performed inline.
