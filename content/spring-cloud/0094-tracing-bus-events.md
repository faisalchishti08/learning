---
card: spring-cloud
gi: 94
slug: tracing-bus-events
title: "Tracing bus events"
---

## 1. What it is

Every `RemoteApplicationEvent` (built-in or custom) carries an origin service ID and, when Spring Cloud Sleuth/Micrometer Tracing is on the classpath, propagates trace and span identifiers along with it — letting an operator or a log aggregator answer "which instance triggered this broadcast, and which instances actually received and processed it" by following one trace ID across every log line the event touches, fleet-wide.

```properties
spring.application.name=order-service
spring.cloud.bus.id=${spring.application.name}:${server.port}
```

```java
@EventListener
public void onRefresh(RefreshRemoteApplicationEvent event) {
    log.info("bus event id={} origin={} destination={}",
             event.getId(), event.getOriginService(), event.getDestinationService());
}
```

## 2. Why & when

A single `/actuator/busrefresh` call can silently fail on some subset of a fleet — a temporarily disconnected instance, a deserialization error, a listener throwing an exception — and without visibility into which instances actually processed the event, an operator has no way to know the fleet ended up in a consistent state. Every `RemoteApplicationEvent` already carries an `id` (unique per event), an `originService` (who published it), and an optional `destinationService` (for targeted, rather than broadcast, events) — logging these fields on both the publishing and every receiving side turns an otherwise invisible fire-and-forget broadcast into something traceable end to end, especially when correlated with a distributed tracing ID that already threads through the rest of the request path.

Reach for bus event tracing when:

- Operational confidence in fleet-wide broadcasts matters — verifying that a config refresh or cache eviction actually reached every instance it was meant to, not just assuming it did because the originating call returned success.
- Debugging a fleet where some instances appear to be running stale state after a broadcast that should have updated everyone — tracing surfaces exactly which instances received the event and which didn't.
- Correlating a bus event with the broader distributed trace of the request or operation that triggered it (an admin action, a Config Server webhook), so the full causal chain — from the triggering HTTP call through to every instance's local reaction — is visible in one trace.

## 3. Core concept

```
 event.getId()               -- unique per broadcast, same value on every receiving instance
 event.getOriginService()    -- which instance/service published it
 event.getDestinationService() -- "**" for broadcast to everyone, or a specific service ID for a targeted event

 instance A publishes id=abc123, origin=order-service:8080
        |
        v
   [ bus ]
        |            |            |
        v            v            v
   instance B    instance C    instance D
   logs id=abc123   logs id=abc123   logs id=abc123 (FAILS to log -- never arrived)
   (received)        (received)       (never received -- visible as a GAP when comparing logs)
```

Because the event `id` is identical everywhere it's received, searching a centralized log store for that one ID reveals exactly which instances processed it — and, by omission, which didn't.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One event id published from instance A appears in the logs of instances B and C that received it but is absent from instance D's logs revealing it never received the broadcast">
  <rect x="20" y="20" width="150" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="45" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">instance A: publish id=abc123</text>

  <rect x="40" y="110" width="140" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="110" y="131" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">B log: id=abc123 OK</text>
  <rect x="250" y="110" width="140" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="131" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">C log: id=abc123 OK</text>
  <rect x="460" y="110" width="150" height="34" rx="7" fill="#1c2430" stroke="#f85149" stroke-width="1.2"/>
  <text x="535" y="131" fill="#f85149" font-size="7.5" text-anchor="middle" font-family="sans-serif">D log: id=abc123 MISSING</text>

  <defs><marker id="a94" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="95" y1="60" x2="110" y2="110" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a94)"/>
  <line x1="95" y1="60" x2="320" y2="110" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a94)"/>
  <line x1="95" y1="60" x2="535" y2="110" stroke="#f85149" stroke-width="1.2" stroke-dasharray="4,3" marker-end="url(#a94)"/>
</svg>

The dashed line to instance D never actually delivered — a gap that's only visible by correlating the shared event ID across every instance's own logs.

## 5. Runnable example

The scenario: broadcast an event to a small fleet, log its `id`/`origin`/`destination` on every side, then reconcile which instances actually received it. Start with basic logging on publish and receipt, then extend to reconciling expected vs actual receivers, then add a case with a genuinely failed delivery that reconciliation must surface.

### Level 1 — Basic

Log the event's id and origin on both the publishing and receiving side.

```java
import java.util.*;
import java.util.function.Consumer;

public class TracingBusEventsLevel1 {
    record BusEvent(String id, String originService, String type) {}

    static class Bus {
        List<Consumer<BusEvent>> subscribers = new ArrayList<>();
        void subscribe(Consumer<BusEvent> handler) { subscribers.add(handler); }
        void publish(BusEvent e) {
            System.out.println("[PUBLISH] id=" + e.id() + " origin=" + e.originService() + " type=" + e.type());
            for (Consumer<BusEvent> handler : subscribers) handler.accept(e);
        }
    }

    public static void main(String[] args) {
        Bus bus = new Bus();
        bus.subscribe(e -> System.out.println("[RECEIVED by instanceB] id=" + e.id()));

        bus.publish(new BusEvent("evt-001", "instanceA", "RefreshRemoteApplicationEvent"));
    }
}
```

How to run: `java TracingBusEventsLevel1.java`

The `id` field (`"evt-001"`) appears identically in both the publish log line and the receipt log line — the shared identifier is what lets a later log search correlate "this was sent" with "this was received," even across separate log files or centralized log aggregation from separate JVMs.

### Level 2 — Intermediate

Extend to multiple receivers and reconcile the full list of instances that were expected to receive the event against those that logged actually receiving it.

```java
import java.util.*;
import java.util.function.Consumer;

public class TracingBusEventsLevel2 {
    record BusEvent(String id, String originService, String type) {}

    static class Bus {
        Map<String, Consumer<BusEvent>> subscribers = new LinkedHashMap<>();
        List<String> receiptLog = new ArrayList<>(); // models a centralized log store aggregating "received" lines
        void subscribe(String id, Consumer<BusEvent> handler) { subscribers.put(id, handler); }
        void publish(BusEvent e) {
            System.out.println("[PUBLISH] id=" + e.id() + " origin=" + e.originService());
            for (Map.Entry<String, Consumer<BusEvent>> entry : subscribers.entrySet()) {
                entry.getValue().accept(e);
                receiptLog.add(entry.getKey() + ":" + e.id()); // each instance's own "received" log line
            }
        }
    }

    public static void main(String[] args) {
        Bus bus = new Bus();
        List<String> expectedFleet = List.of("instanceB", "instanceC", "instanceD");
        expectedFleet.forEach(id -> bus.subscribe(id, e -> System.out.println("[RECEIVED by " + id + "] id=" + e.id())));

        bus.publish(new BusEvent("evt-002", "instanceA", "RefreshRemoteApplicationEvent"));

        // reconcile: did every expected instance's log actually record this event id?
        for (String instanceId : expectedFleet) {
            boolean received = bus.receiptLog.contains(instanceId + ":evt-002");
            System.out.println("reconcile " + instanceId + ": " + (received ? "CONFIRMED" : "MISSING"));
        }
    }
}
```

How to run: `java TracingBusEventsLevel2.java`

The reconciliation loop checks `receiptLog` — the aggregated stand-in for a centralized logging system — for each expected instance's own `"id:eventId"` entry, printing `CONFIRMED` for every instance that actually processed `evt-002`; since all three subscribers here are connected and healthy, every one reconciles as `CONFIRMED`.

### Level 3 — Advanced

Introduce a genuinely failed delivery (a disconnected instance) and show reconciliation correctly surfacing the gap, plus a listener that throws mid-processing.

```java
import java.util.*;
import java.util.function.Consumer;

public class TracingBusEventsLevel3 {
    record BusEvent(String id, String originService, String type) {}

    static class Bus {
        Map<String, Consumer<BusEvent>> subscribers = new LinkedHashMap<>();
        List<String> receiptLog = new ArrayList<>();
        List<String> errorLog = new ArrayList<>();
        void subscribe(String id, Consumer<BusEvent> handler) { subscribers.put(id, handler); }
        void publish(BusEvent e) {
            System.out.println("[PUBLISH] id=" + e.id() + " origin=" + e.originService());
            for (Map.Entry<String, Consumer<BusEvent>> entry : subscribers.entrySet()) {
                try {
                    entry.getValue().accept(e);
                    receiptLog.add(entry.getKey() + ":" + e.id());
                } catch (RuntimeException ex) {
                    // one listener's failure doesn't stop delivery to the rest of the fleet
                    errorLog.add(entry.getKey() + ":" + e.id() + ":" + ex.getMessage());
                    System.out.println("[ERROR at " + entry.getKey() + "] " + ex.getMessage());
                }
            }
        }
    }

    public static void main(String[] args) {
        Bus bus = new Bus();
        List<String> expectedFleet = List.of("instanceB", "instanceC", "instanceD");

        bus.subscribe("instanceB", e -> System.out.println("[RECEIVED by instanceB] id=" + e.id()));
        // instanceC is intentionally never subscribed -- models a disconnected instance that never gets the event at all
        bus.subscribe("instanceD", e -> { throw new RuntimeException("failed to rebind @RefreshScope bean"); });

        bus.publish(new BusEvent("evt-003", "instanceA", "RefreshRemoteApplicationEvent"));

        System.out.println("-- reconciliation --");
        for (String instanceId : expectedFleet) {
            boolean received = bus.receiptLog.contains(instanceId + ":evt-003");
            boolean errored = bus.errorLog.stream().anyMatch(s -> s.startsWith(instanceId + ":evt-003"));
            String status = received ? "CONFIRMED" : errored ? "ERRORED" : "MISSING (never connected)";
            System.out.println(instanceId + ": " + status);
        }
    }
}
```

How to run: `java TracingBusEventsLevel3.java`

Reconciliation reports `instanceB` as `CONFIRMED`, `instanceD` as `ERRORED` (it received the event but its listener threw, correctly captured in `errorLog` rather than `receiptLog`), and `instanceC` as `MISSING (never connected)` — three distinct, individually diagnosable outcomes from what would otherwise be a single opaque "broadcast complete" result if the code hadn't traced each instance's fate separately.

## 6. Walkthrough

Trace `bus.publish` in Level 3.

1. `bus.publish(new BusEvent("evt-003", "instanceA", ...))` prints the publish log line, then iterates `subscribers`, which contains two entries: `"instanceB"` and `"instanceD"` (`"instanceC"` was deliberately never subscribed).
2. For `"instanceB"`, `entry.getValue().accept(e)` runs its listener successfully (prints the received line), so `receiptLog.add("instanceB:evt-003")` executes with no exception.
3. For `"instanceD"`, `entry.getValue().accept(e)` invokes a listener that immediately throws `RuntimeException("failed to rebind @RefreshScope bean")` — the `catch` block catches it, adds `"instanceD:evt-003:failed to rebind @RefreshScope bean"` to `errorLog`, and prints the error line; critically, this exception does not propagate out of the `for` loop, so processing continues to any remaining subscribers unaffected.
4. The reconciliation loop then checks each of the three *expected* fleet members (`instanceB`, `instanceC`, `instanceD`) — note this list is independent of `subscribers`, modeling an operator's separately-maintained expectation of who should be in the fleet.
5. For `"instanceB"`, `receiptLog.contains("instanceB:evt-003")` is `true`, so it reports `CONFIRMED`.
6. For `"instanceC"`, neither `receiptLog` nor `errorLog` contains any entry for it at all (it was never a subscriber, so `accept` was never called on it), so both checks are `false` and it falls through to `MISSING (never connected)`.
7. For `"instanceD"`, `receiptLog.contains("instanceD:evt-003")` is `false` (its listener threw before reaching the `receiptLog.add` line), but `errorLog.stream().anyMatch(...)` finds its entry, so it reports `ERRORED` — distinct from `instanceC`'s `MISSING`, correctly reflecting that `instanceD` *did* receive the broadcast, it just failed to process it.

```
evt-003 published from instanceA
   instanceB: accept() succeeds        -> receiptLog        -> CONFIRMED
   instanceC: never subscribed         -> no entry anywhere  -> MISSING (never connected)
   instanceD: accept() throws          -> errorLog           -> ERRORED (received, but failed)
```

## 7. Gotchas & takeaways

> **Gotcha:** `MISSING` and `ERRORED` are operationally very different problems requiring different fixes — `MISSING` (instanceC) means the instance never even received the broadcast, typically a connectivity or broker-subscription issue, while `ERRORED` (instanceD) means it received the event fine but failed while acting on it, typically an application bug. Conflating the two into one generic "instance didn't update" status, without tracing each instance's actual fate separately, makes root-causing a fleet-wide broadcast failure far slower than it needs to be.

- Correlating a shared event `id` across every instance's own logs is what turns an inherently distributed, fire-and-forget broadcast into something an operator can audit after the fact.
- Reconciliation requires an independent source of "who should have received this" (an expected fleet membership list, a service registry snapshot) — the bus itself has no concept of who's missing, since a broker fan-out simply delivers to whoever happens to be subscribed at that instant.
- A listener throwing on one instance must never be allowed to block delivery to, or processing by, other instances — isolating each subscriber's failure (as the `try`/`catch` inside the loop does) is what keeps one bad instance from silently degrading the entire broadcast.
- In production, correlate the bus event's `id` with the broader distributed trace ID of whatever triggered it, so a single trace search reveals the entire causal chain: the admin action, the publish, and every instance's individual outcome.
