---
card: microservices
gi: 361
slug: centralized-log-aggregation
title: "Centralized log aggregation"
---

## 1. What it is

**Centralized log aggregation** means every service ships its logs to one shared system (Elasticsearch/Logstash/Kibana, Loki/Grafana, a cloud provider's logging service) instead of each service's logs staying only on the local disk of whatever container or VM produced them. From that central system, a single search across `correlationId` or any [structured log](0360-structured-logging.md) field returns matching entries from every service at once, regardless of which machine actually ran which service.

## 2. Why & when

In a microservices system, a single request's logs are scattered across however many services (and however many container instances of each) it touched — and those containers are frequently short-lived, restarted, rescheduled onto different machines, or scaled up and down entirely. Logs that only live on local disk vanish the moment their container is destroyed, and even while it's running, manually SSHing into dozens of different machines to grep for a correlation ID is completely impractical at any real scale. Centralized aggregation solves both problems: logs are shipped off the ephemeral container the instant they're produced, durably retained centrally, and searchable from one place regardless of which service or instance generated them.

Adopt centralized log aggregation as a baseline requirement for any microservices deployment beyond a handful of services on one machine — this is what makes [structured logging](0360-structured-logging.md) and [correlation IDs](0351-correlation-ids-request-ids.md) actually useful in practice: structuring your logs is only valuable if there's a central place to search across all of them together.

## 3. Core concept

Each service writes structured log lines to standard output (or a local file); a log shipping agent (Fluentd, Filebeat, Promtail, or a platform-provided sidecar) running alongside the service tails that output and forwards each entry to the central aggregation system, which indexes it for search. The service itself typically doesn't need to know or care about the aggregation system directly — it just logs normally, and the shipping agent handles getting the data centralized.

```java
// The service just logs normally -- structured, to stdout.
System.out.println(toJson(Map.of("level", "ERROR", "correlationId", correlationId, "message", "payment failed")));
// A separate shipping agent (not this code) tails stdout and forwards it to the central log store.
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three services each write logs to their own local stdout; a shipping agent alongside each forwards them to one centralized log store; a single search there returns matching entries from all three services at once">
  <rect x="20" y="20" width="130" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-service</text>
  <rect x="20" y="70" width="130" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">payment-service</text>
  <rect x="20" y="120" width="130" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="142" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">inventory-service</text>

  <line x1="150" y1="37" x2="260" y2="90" stroke="#79c0ff" marker-end="url(#a361)"/>
  <line x1="150" y1="87" x2="260" y2="90" stroke="#79c0ff" marker-end="url(#a361)"/>
  <line x1="150" y1="137" x2="260" y2="90" stroke="#79c0ff" marker-end="url(#a361)"/>

  <rect x="270" y="70" width="180" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="360" y="95" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Centralized log store</text>

  <text x="360" y="150" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">One search here returns matching entries from ALL THREE services at once.</text>

  <defs><marker id="a361" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Every service's logs are shipped to one central store, making a cross-service search possible from a single place.

## 5. Runnable example

Scenario: an incident investigation across three services, first attempted with only local per-service log storage (impractical to search across), then rebuilt with a simulated centralized log store, and finally extended to show searching that central store by correlation ID across all services at once.

### Level 1 — Basic

```java
// File: LocalPerServiceLogsOnly.java -- each service's logs live ONLY in
// its own local store; investigating a cross-service issue means manually
// checking EACH ONE separately.
import java.util.*;

public class LocalPerServiceLogsOnly {
    static List<String> orderServiceLocalLogs = new ArrayList<>();
    static List<String> paymentServiceLocalLogs = new ArrayList<>();
    static List<String> inventoryServiceLocalLogs = new ArrayList<>();

    public static void main(String[] args) {
        orderServiceLocalLogs.add("[corr-42] order-service: checkout received");
        paymentServiceLocalLogs.add("[corr-42] payment-service: card declined");
        inventoryServiceLocalLogs.add("[corr-42] inventory-service: stock check skipped (payment failed first)");

        System.out.println("To investigate corr-42, an engineer must manually check THREE separate local log stores:");
        System.out.println("order-service local logs: " + orderServiceLocalLogs);
        System.out.println("payment-service local logs: " + paymentServiceLocalLogs);
        System.out.println("inventory-service local logs: " + inventoryServiceLocalLogs);
        System.out.println("With MANY services and MANY instances, this manual per-service checking doesn't scale AT ALL.");
    }
}
```

How to run: `java LocalPerServiceLogsOnly.java`

Each service's logs exist only in its own isolated list, standing in for local disk on separate machines. Investigating `corr-42`'s full story means an engineer manually inspecting three separate stores — and in a real system with dozens of services and many replicated instances each, this manual approach becomes completely impractical.

### Level 2 — Intermediate

```java
// File: CentralizedLogStore.java -- ALL services ship to ONE central
// store; investigating no longer means checking multiple separate places.
import java.util.*;

public class CentralizedLogStore {
    record LogEntry(String service, String correlationId, String message) {}
    static List<LogEntry> centralLogStore = new ArrayList<>(); // ONE shared destination for EVERY service

    static void shipLog(String service, String correlationId, String message) { // simulates the shipping agent's job
        centralLogStore.add(new LogEntry(service, correlationId, message));
    }

    public static void main(String[] args) {
        shipLog("order-service", "corr-42", "checkout received");
        shipLog("payment-service", "corr-42", "card declined");
        shipLog("inventory-service", "corr-42", "stock check skipped (payment failed first)");

        System.out.println("ALL services' logs now live in ONE place:");
        centralLogStore.forEach(e -> System.out.println("  [" + e.service() + "] " + e.message()));
        System.out.println("No more hopping between separate per-service stores.");
    }
}
```

How to run: `java CentralizedLogStore.java`

`shipLog` writes every service's log entries into the same `centralLogStore` list, standing in for each service's log-shipping agent forwarding data to one shared aggregation system. All three services' entries now live together in one place, ready to be searched as a unit rather than requiring separate lookups per service.

### Level 3 — Advanced

```java
// File: SearchCentralStoreAcrossServices.java -- a SINGLE search against
// the centralized store finds every relevant entry across ALL services
// for a given correlation ID, reconstructing the FULL cross-service story
// of one request in one query.
import java.util.*;
import java.util.stream.*;

public class SearchCentralStoreAcrossServices {
    record LogEntry(String service, String correlationId, String message, long timestampMs) {}
    static List<LogEntry> centralLogStore = new ArrayList<>();

    static void shipLog(String service, String correlationId, String message, long timestampMs) {
        centralLogStore.add(new LogEntry(service, correlationId, message, timestampMs));
    }

    static List<LogEntry> searchByCorrelationId(String correlationId) { // the ONE query that matters
        return centralLogStore.stream()
                .filter(e -> e.correlationId().equals(correlationId))
                .sorted(Comparator.comparingLong(LogEntry::timestampMs))
                .toList();
    }

    public static void main(String[] args) {
        shipLog("order-service", "corr-42", "checkout received", 1000);
        shipLog("order-service", "corr-99", "checkout received", 1050); // UNRELATED request
        shipLog("payment-service", "corr-42", "card declined", 1100);
        shipLog("inventory-service", "corr-42", "stock check skipped", 1150);
        shipLog("inventory-service", "corr-99", "reserved 2 units", 1200); // UNRELATED request

        List<LogEntry> fullStory = searchByCorrelationId("corr-42");
        System.out.println("Full cross-service story for corr-42, in chronological order:");
        fullStory.forEach(e -> System.out.println("  t=" + e.timestampMs() + " [" + e.service() + "] " + e.message()));
        System.out.println("Found in ONE query, across THREE services, correctly EXCLUDING corr-99's unrelated entries.");
    }
}
```

How to run: `java SearchCentralStoreAcrossServices.java`

`searchByCorrelationId` filters the entire `centralLogStore` down to only entries matching `"corr-42"`, then sorts them chronologically by timestamp — reconstructing the full, correctly-ordered, cross-service story of that one request (checkout, then decline, then skipped stock check) in a single query, while correctly excluding the two unrelated `"corr-99"` entries that happen to share the same store but belong to a different request entirely.

## 6. Walkthrough

Trace `SearchCentralStoreAcrossServices.main` in order. **First**, five `shipLog` calls populate `centralLogStore`: three tagged `"corr-42"` (from `order-service` at `t=1000`, `payment-service` at `t=1100`, and `inventory-service` at `t=1150`) and two tagged `"corr-99"` (from `order-service` at `t=1050` and `inventory-service` at `t=1200`), all mixed together in insertion order within the same list.

**Next**, `searchByCorrelationId("corr-42")` runs: the stream filter checks `e.correlationId().equals("corr-42")` for each of the five entries, keeping the three that match and discarding the two `"corr-99"` entries regardless of their position in the underlying list.

**The three matching entries are then sorted** by `timestampMs` — since they were already inserted in increasing timestamp order in this example, the sort doesn't change their relative order here, but it guarantees correctness even if entries had arrived out of order (for instance, if a slower service's log line was shipped to the central store later than a faster service's later-occurring event).

**Finally**, `main` prints the three sorted entries — `order-service`'s checkout at `t=1000`, `payment-service`'s decline at `t=1100`, and `inventory-service`'s skipped check at `t=1150` — reconstructing the complete, correctly-ordered, cross-service timeline of this one request from a single query against the centralized store, with the two unrelated `"corr-99"` entries never appearing in the result at all.

```
centralLogStore: [order/corr-42@1000, order/corr-99@1050, payment/corr-42@1100, inventory/corr-42@1150, inventory/corr-99@1200]
searchByCorrelationId("corr-42") -> filter matches 3 -> sort by timestamp -> [order@1000, payment@1100, inventory@1150]
```

## 7. Gotchas & takeaways

> Shipping logs centrally without also retaining them locally (even briefly) for a short buffer window can lose data if the shipping agent itself is down or backed up during an incident — the worst possible time for logs to go missing. Most production setups buffer locally for a short period and retry shipping, rather than assuming the network path to the central store is always immediately available.

- Centralized log aggregation ships every service's logs to one shared, searchable store, instead of leaving them scattered across ephemeral, per-container local disks.
- This is what actually makes [structured logging](0360-structured-logging.md) and [correlation IDs](0351-correlation-ids-request-ids.md) practically useful — structuring logs only pays off once there's a central place to search across all of them together.
- A log-shipping agent typically runs alongside each service (as a sidecar or host-level daemon), tailing its output and forwarding it centrally, with the service itself needing no direct awareness of the aggregation system.
- Once centralized, a single query by correlation ID or trace ID can reconstruct a request's full cross-service story in one step, exactly the capability an incident investigation needs.
