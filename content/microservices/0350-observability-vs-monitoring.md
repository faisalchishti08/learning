---
card: microservices
gi: 350
slug: observability-vs-monitoring
title: "Observability vs monitoring"
---

## 1. What it is

**Monitoring** means watching for a predefined set of known failure conditions — dashboards and alerts built in advance for problems you already anticipated ("CPU above 90%," "error rate above 1%"). **Observability** means having enough rich, correlated data (the [three pillars](0349-three-pillars-logs-metrics-traces.md): logs, metrics, traces) that you can answer *new, previously unanticipated* questions about the system's behavior after the fact, without having predicted that specific question in advance. Monitoring tells you *that* a known problem is happening; observability lets you *investigate* an unknown one.

## 2. Why & when

A monolith fails in a comparatively small number of predictable ways, so monitoring — a fixed set of dashboards and alerts for known failure modes — often suffices. Microservices fail in combinatorially many ways: a specific customer's specific request pattern interacting with a specific service's specific code path under a specific load condition, which nobody predicted or built a dashboard for. Observability is the response to this reality: instead of trying to predict every possible failure mode in advance, you instrument the system richly enough (structured logs with context, detailed metrics, distributed traces) that when something unanticipated goes wrong, you can drill in and ask new questions of the data you already have, without needing to ship new instrumentation first and wait for the problem to recur.

Build monitoring for the failure modes you already know about and want proactive alerts for (this remains valuable and necessary). Invest in observability as the necessary complement for the failure modes you haven't thought of yet — which, in a system with enough services and enough scale, will eventually be most of your genuinely hard incidents. Neither replaces the other; monitoring answers "is something wrong right now," observability answers "why, exactly, for this specific unexpected case."

## 3. Core concept

Monitoring is defined by its dashboards and alert rules being written *before* an incident, against known metrics ("alert if error rate > 1%"). Observability is defined by the ability to construct a *new* query against already-collected, richly-contextualized data *after* an incident starts, to answer a question nobody thought to ask in advance ("show me every request from this one customer's account that touched this one code path in the last hour").

```java
// Monitoring: a PRE-DEFINED alert rule, written in advance.
if (errorRate() > 0.01) alert("error rate exceeded 1%");

// Observability: an AD-HOC query, constructed AFTER the fact, against rich existing data.
traces.stream().filter(t -> t.customerId().equals("cust-42") && t.tags().contains("checkout-v2")).toList();
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Monitoring: predefined dashboards and alerts built before an incident, for known failure modes. Observability: rich correlated data queried after an incident, to answer a new, previously unanticipated question">
  <rect x="30" y="20" width="270" height="130" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="165" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Monitoring</text>
  <text x="165" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">predefined dashboards/alerts</text>
  <text x="165" y="86" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">built BEFORE the incident</text>
  <text x="165" y="104" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">"is something wrong RIGHT NOW"</text>

  <rect x="340" y="20" width="270" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="475" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Observability</text>
  <text x="475" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ad-hoc queries on rich data</text>
  <text x="475" y="86" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">constructed AFTER the incident</text>
  <text x="475" y="104" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">"WHY, for this NEW/unexpected case"</text>
</svg>

Monitoring watches for what you already anticipated; observability lets you investigate what you didn't.

## 5. Runnable example

Scenario: an incident that a predefined monitoring alert catches only partially, then investigated with an ad-hoc observability query the team never predefined, and finally extended to show building a *new* dashboard from that discovery — turning a one-off observability finding into permanent monitoring for next time.

### Level 1 — Basic

```java
// File: PredefinedMonitoringAlert.java -- a fixed, predefined alert rule
// fires on a known condition; it can tell THAT something is wrong, but not WHY.
import java.util.*;

public class PredefinedMonitoringAlert {
    record RequestOutcome(String customerId, String endpoint, boolean failed) {}
    static List<RequestOutcome> requests = new ArrayList<>();

    static double errorRate() {
        long failures = requests.stream().filter(RequestOutcome::failed).count();
        return requests.isEmpty() ? 0 : (double) failures / requests.size();
    }

    static void checkPredefinedAlert() { // written BEFORE any incident, for a KNOWN condition
        if (errorRate() > 0.05) System.out.println("ALERT: error rate " + (errorRate() * 100) + "% exceeds 5% threshold!");
        else System.out.println("no alert -- error rate " + (errorRate() * 100) + "% is within normal range");
    }

    public static void main(String[] args) {
        for (int i = 0; i < 90; i++) requests.add(new RequestOutcome("cust-" + (i % 20), "/checkout", false));
        for (int i = 0; i < 10; i++) requests.add(new RequestOutcome("cust-42", "/checkout-v2", true)); // all failures from ONE customer, ONE endpoint

        checkPredefinedAlert();
        System.out.println("The alert fired -- but it does NOT tell us WHICH customer or endpoint is actually affected.");
    }
}
```

How to run: `java PredefinedMonitoringAlert.java`

`checkPredefinedAlert` is a fixed rule written in advance: if the overall error rate crosses `5%`, alert. It correctly fires here (`10%` overall), but it only tells the team *that* something is wrong — nothing in this predefined check surfaces *which* customer or endpoint is actually responsible, because nobody predicted this specific combination when writing the rule.

### Level 2 — Intermediate

```java
// File: AdHocObservabilityQuery.java -- the SAME data, but now queried
// with an AD-HOC question constructed AFTER the alert fired, to find the
// actual root cause -- a query nobody wrote in advance.
import java.util.*;
import java.util.stream.*;

public class AdHocObservabilityQuery {
    record RequestOutcome(String customerId, String endpoint, boolean failed) {}
    static List<RequestOutcome> requests = new ArrayList<>();

    public static void main(String[] args) {
        for (int i = 0; i < 90; i++) requests.add(new RequestOutcome("cust-" + (i % 20), "/checkout", false));
        for (int i = 0; i < 10; i++) requests.add(new RequestOutcome("cust-42", "/checkout-v2", true));

        System.out.println("Investigating the alert: which customer/endpoint combinations have failures?");
        Map<String, Long> failuresByEndpoint = requests.stream()
                .filter(RequestOutcome::failed)
                .collect(Collectors.groupingBy(RequestOutcome::endpoint, Collectors.counting())); // AD-HOC grouping, invented on the spot
        System.out.println("Failures by endpoint: " + failuresByEndpoint);

        Set<String> affectedCustomers = requests.stream()
                .filter(RequestOutcome::failed)
                .map(RequestOutcome::customerId)
                .collect(Collectors.toSet()); // ANOTHER ad-hoc question, also invented on the spot
        System.out.println("Affected customers: " + affectedCustomers + " -- ALL failures trace to ONE customer on ONE new endpoint!");
    }
}
```

How to run: `java AdHocObservabilityQuery.java`

Neither `groupingBy(RequestOutcome::endpoint, ...)` nor the `affectedCustomers` computation was predefined anywhere — they're queries the investigator constructs on the spot, against the same underlying request data, specifically to answer the new question "who and what is actually causing this alert." The result immediately reveals that every failure comes from one customer (`cust-42`) hitting one specific new endpoint (`/checkout-v2`) — a root cause the predefined alert alone could never surface, because the alert only tracked an aggregate number.

### Level 3 — Advanced

```java
// File: PromoteFindingToNewMonitoring.java -- having discovered the root
// cause via observability, the team adds a NEW, specific monitoring rule
// for it -- turning a one-off discovery into permanent, predefined coverage.
import java.util.*;
import java.util.stream.*;

public class PromoteFindingToNewMonitoring {
    record RequestOutcome(String customerId, String endpoint, boolean failed) {}
    static List<RequestOutcome> requests = new ArrayList<>();

    // The NEW monitoring rule, added AFTER this incident, based on what observability revealed.
    static void checkPerEndpointErrorRate() {
        Map<String, List<RequestOutcome>> byEndpoint = requests.stream().collect(Collectors.groupingBy(RequestOutcome::endpoint));
        for (Map.Entry<String, List<RequestOutcome>> entry : byEndpoint.entrySet()) {
            long failures = entry.getValue().stream().filter(RequestOutcome::failed).count();
            double rate = (double) failures / entry.getValue().size();
            if (rate > 0.5) System.out.println("NEW ALERT: endpoint '" + entry.getKey() + "' has error rate " + (rate * 100) + "% -- would have caught THIS incident immediately, per-endpoint, next time.");
        }
    }

    public static void main(String[] args) {
        for (int i = 0; i < 90; i++) requests.add(new RequestOutcome("cust-" + (i % 20), "/checkout", false));
        for (int i = 0; i < 10; i++) requests.add(new RequestOutcome("cust-42", "/checkout-v2", true));

        System.out.println("Running the NEW per-endpoint monitoring rule, added based on last incident's observability finding:");
        checkPerEndpointErrorRate();
        System.out.println("What started as an ad-hoc OBSERVABILITY query is now PERMANENT, predefined MONITORING.");
    }
}
```

How to run: `java PromoteFindingToNewMonitoring.java`

`checkPerEndpointErrorRate` is a new, specific, predefined rule — added *because* the previous incident's ad-hoc observability investigation revealed that per-endpoint error rates matter more than the aggregate. Running it against the same data immediately flags `/checkout-v2` at a `100%` error rate. This demonstrates the natural relationship between the two: observability investigates the unknown, and its findings often get promoted into new, permanent monitoring so the *next* occurrence of the *same* pattern is caught immediately, without needing another investigation.

## 6. Walkthrough

Trace `PromoteFindingToNewMonitoring.main` in order. **First**, the same 100 requests are populated: 90 successful requests spread across 20 customers hitting `/checkout`, and 10 failing requests all from `cust-42` hitting `/checkout-v2`.

**Next**, `checkPerEndpointErrorRate()` runs. It groups all requests by `endpoint` using `Collectors.groupingBy`, producing a map with two keys: `/checkout` (90 requests) and `/checkout-v2` (10 requests).

**For the `/checkout` entry**, the loop counts `failures` among its 90 requests, which is `0`, so `rate` is `0.0` — this is not greater than `0.5`, so no alert prints for this endpoint.

**For the `/checkout-v2` entry**, the loop counts `failures` among its 10 requests, which is `10` (all of them), so `rate` is `1.0` — this *is* greater than `0.5`, so the alert branch fires, printing that this specific endpoint has a `100%` error rate.

**Finally**, `main` prints a closing message noting that this specific, targeted rule exists only because a prior incident's ad-hoc observability investigation (as shown in Level 2) revealed that per-endpoint granularity was the missing piece — turning a one-time discovery into standing, predefined monitoring coverage for the future.

```
Prior incident: predefined AGGREGATE alert fired -> ad-hoc query REVEALED root cause (one endpoint, one customer)
This run: NEW per-endpoint rule (built FROM that discovery) -> /checkout-v2 flagged at 100% error rate, IMMEDIATELY
```

## 7. Gotchas & takeaways

> Treating "we have dashboards" as equivalent to "we have observability" is a common and costly mistake — dashboards built for known conditions will miss any failure mode nobody predicted, no matter how many of them you have. Observability specifically requires the *underlying data* (rich, structured, correlated logs/metrics/traces) to support genuinely new questions, not just more dashboards on the same predefined metrics.

- Monitoring answers "is a known problem happening right now," using dashboards and alerts built in advance; observability answers "why is this new, unanticipated thing happening," using rich data queried after the fact.
- Microservices fail in combinatorially many ways that can't all be predicted in advance, making observability's after-the-fact investigative capability essential, not optional.
- A common healthy cycle: an incident is investigated via ad-hoc observability queries, and the resulting insight is promoted into new, permanent, predefined monitoring for next time.
- Rich [structured logging](0360-structured-logging.md), [distributed tracing](0352-distributed-tracing-concepts-trace-span-context-propagation.md), and carefully chosen metric [cardinality](0355-cardinality-of-metrics-labels.md) are the concrete building blocks that make genuine observability (not just monitoring) possible.
