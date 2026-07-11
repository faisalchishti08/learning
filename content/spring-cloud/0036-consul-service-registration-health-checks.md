---
card: spring-cloud
gi: 36
slug: consul-service-registration-health-checks
title: "Consul service registration & health checks"
---

## 1. What it is

Zooming into the registration piece from the previous card: a Spring Boot application configures how it registers with its local Consul agent — its service ID, tags, and, critically, which kind of health check the agent should run against it (HTTP, TCP, TTL, or script) and on what interval.

```properties
spring.cloud.consul.discovery.instance-id=${spring.application.name}:${random.value}
spring.cloud.consul.discovery.health-check-path=/actuator/health
spring.cloud.consul.discovery.health-check-interval=10s
spring.cloud.consul.discovery.tags=version=1.2.0,team=payments
```

## 2. Why & when

The previous card showed the *shape* of Consul's agent-driven health checking; this card is about actually configuring it correctly for a real Spring Boot service. The default HTTP check works well when the app already exposes Actuator's `/actuator/health`, but different workloads need different check types — a check interval that's too slow leaves a dead instance discoverable for longer than necessary, and one that's too fast adds needless load.

Configure this deliberately when:

- You want Consul's health check to reuse Spring Boot Actuator's aggregate health status (database, disk space, custom indicators) rather than a bare TCP port check that only proves the process is listening.
- The service isn't HTTP-based (a message consumer with no web port, say) and needs a TTL check instead — where the *application itself* periodically calls Consul to say "I'm still alive," rather than Consul polling it.
- Multiple versions or variants of a service run side by side, and tags are needed so callers (or Consul's routing/mesh layer) can filter by version, region, or team ownership.

## 3. Core concept

```
 HTTP check:   agent GETs health-check-path every interval -> 2xx = healthy
 TCP check:    agent opens a TCP connection every interval -> connects = healthy
 TTL check:    application itself PUTs a "still alive" signal before the TTL expires
                -> agent marks critical if the TTL passes with no signal
 script check: agent runs a local command/script every interval -> exit 0 = healthy
```

Every check type answers the same question — "is this instance healthy right now?" — through a different mechanism suited to a different kind of workload.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Consul agent runs an HTTP check against an application's health endpoint on an interval, while a background worker instead pushes a TTL heartbeat before its own deadline expires">
  <rect x="30" y="20" width="250" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">orders-service (HTTP)</text>
  <text x="155" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">agent GETs /actuator/health</text>
  <text x="155" y="72" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">every 10s -&gt; 200 OK = healthy</text>

  <rect x="360" y="20" width="250" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">billing-worker (TTL)</text>
  <text x="485" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">worker PUTs /v1/agent/check/pass</text>
  <text x="485" y="72" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">before its 30s TTL expires</text>

  <rect x="200" y="130" width="240" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="154" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Consul Agent (local, per host)</text>

  <line x1="155" y1="90" x2="280" y2="128" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="485" y1="90" x2="360" y2="128" stroke="#8b949e" stroke-width="1.2"/>

  <defs><marker id="a36" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The agent either actively polls (HTTP/TCP/script) or passively waits to be told (TTL) — the right choice depends on whether the workload speaks HTTP at all.

## 5. Runnable example

The scenario: simulate Consul's agent-side health checking for two kinds of services — an HTTP-checkable web service and a TTL-checkable background worker — starting from a basic HTTP check, then adding failure detection, then adding the TTL variant side by side.

### Level 1 — Basic

An HTTP check: the agent polls a health endpoint on an interval.

```java
import java.util.*;

public class ConsulHealthLevel1 {
    static class HttpCheckedService {
        String name;
        boolean healthEndpointReturnsOk = true;

        boolean pollCheck() {
            return healthEndpointReturnsOk; // agent's HTTP GET, simplified to a boolean
        }
    }

    public static void main(String[] args) {
        HttpCheckedService orders = new HttpCheckedService();
        orders.name = "orders-service";

        System.out.println(orders.name + " check result: " + (orders.pollCheck() ? "passing" : "critical"));
    }
}
```

How to run: `java ConsulHealthLevel1.java`

`pollCheck()` stands in for the agent's periodic `GET /actuator/health` — a simple pass/fail signal driven entirely by what the application currently reports.

### Level 2 — Intermediate

Add a check interval and simulate polling over time, including a transition to unhealthy.

```java
import java.util.*;

public class ConsulHealthLevel2 {
    static class HttpCheckedService {
        String name;
        boolean healthEndpointReturnsOk = true;
        int checkIntervalSeconds = 10;
        List<Boolean> checkHistory = new ArrayList<>();

        void agentPolls() {
            checkHistory.add(healthEndpointReturnsOk); // agent records the result of each poll
        }

        String currentStatus() {
            // Consul marks critical only after a check fails -- not proactively, just reactively per-poll
            return checkHistory.isEmpty() ? "unknown"
                    : (checkHistory.get(checkHistory.size() - 1) ? "passing" : "critical");
        }
    }

    public static void main(String[] args) {
        HttpCheckedService orders = new HttpCheckedService();
        orders.name = "orders-service";

        orders.agentPolls(); // t=0s: healthy
        System.out.println("t=0s status: " + orders.currentStatus());

        orders.healthEndpointReturnsOk = false; // database connection drops
        orders.agentPolls(); // t=10s: unhealthy, agent notices on its next poll
        System.out.println("t=10s status: " + orders.currentStatus());
    }
}
```

How to run: `java ConsulHealthLevel2.java`

`agentPolls()` records a snapshot every `checkIntervalSeconds`, and `currentStatus()` reflects the most recent poll — the moment the application's underlying health flips to unhealthy, the *next* scheduled poll (at most `checkIntervalSeconds` later) catches it, showing the real latency between "app breaks" and "Consul notices," bounded by the check interval.

### Level 3 — Advanced

Add the TTL check variant for a non-HTTP background worker, running side by side with the HTTP-checked service, and show what happens when the worker stops sending its heartbeat.

```java
import java.util.*;

public class ConsulHealthLevel3 {
    interface HealthChecked {
        String name();
        String status(long now);
    }

    static class HttpCheckedService implements HealthChecked {
        String name;
        boolean healthy = true;
        public String name() { return name; }
        public String status(long now) { return healthy ? "passing" : "critical"; }
    }

    static class TtlCheckedWorker implements HealthChecked {
        String name;
        long ttlSeconds;
        long lastPing;

        public String name() { return name; }

        void ping(long now) {
            lastPing = now; // worker calls PUT /v1/agent/check/pass/{checkId}
        }

        public String status(long now) {
            // TTL check: critical if the worker hasn't pinged within its own declared TTL window
            return (now - lastPing <= ttlSeconds) ? "passing" : "critical";
        }
    }

    public static void main(String[] args) {
        HttpCheckedService orders = new HttpCheckedService();
        orders.name = "orders-service";

        TtlCheckedWorker billingWorker = new TtlCheckedWorker();
        billingWorker.name = "billing-worker";
        billingWorker.ttlSeconds = 30;
        billingWorker.ping(0);

        List<HealthChecked> services = List.of(orders, billingWorker);

        printAll(services, 20); // both still within bounds
        billingWorker.ping(20);  // worker pings again, resetting its TTL clock
        printAll(services, 45); // 45 - 20 = 25s since last ping, still under 30s TTL
        printAll(services, 60); // 60 - 20 = 40s since last ping, worker missed its window -- critical
    }

    static void printAll(List<HealthChecked> services, long now) {
        StringBuilder sb = new StringBuilder("t=" + now + "s: ");
        for (HealthChecked s : services) sb.append(s.name()).append("=").append(s.status(now)).append("  ");
        System.out.println(sb.toString().trim());
    }
}
```

How to run: `java ConsulHealthLevel3.java`

`TtlCheckedWorker.status()` inverts the polling direction from `HttpCheckedService`: instead of the agent reaching out, the worker itself calls `ping()` (modeling `PUT /v1/agent/check/pass/{checkId}`) before its TTL window closes, and `status()` computes whether that window has been honored. At `t=60s`, the worker's last ping was at `t=20s`, 40 seconds ago — past its 30-second TTL — so it correctly shows `critical` even though nothing actively told Consul it failed; the absence of a timely ping *is* the failure signal.

## 6. Walkthrough

Trace Level 3's three `printAll` calls in order.

1. `printAll(services, 20)` runs first — `orders` (HTTP-checked) reports `passing` because its `healthy` flag is still `true`; `billingWorker` (TTL-checked) computes `20 - 0 = 20`, which is `<= 30`, so it also reports `passing`. This models both an HTTP poll succeeding and a TTL check still within its window.
2. `billingWorker.ping(20)` runs — this models the background worker's own internal loop calling Consul's TTL-pass endpoint again, resetting `lastPing` to `20` and buying itself another 30-second window before the next check is due.
3. `printAll(services, 45)` runs — `billingWorker` computes `45 - 20 = 25`, still `<= 30`, so it remains `passing`. This is the TTL mechanism working as intended: a live worker keeps renewing its own window before it lapses.
4. `printAll(services, 60)` runs — the worker never pinged again after `t=20`, so `60 - 20 = 40`, which exceeds the 30-second TTL. `status()` returns `critical`. This models Consul correctly detecting a stalled or crashed worker purely from the *absence* of an expected signal, exactly the way a TTL check is meant to work for processes that can't be polled over HTTP.

```
HTTP check:  agent -> GET /health -> pass/fail per poll, interval-bounded detection latency
TTL check:   worker -> PUT check/pass -> resets its own clock
             agent marks critical only if that PUT doesn't arrive before the TTL deadline
```

## 7. Gotchas & takeaways

> **Gotcha:** a TTL check requires the application to actively call the pass endpoint — if that logic has a bug (an exception swallowed silently, a thread that dies without crashing the process), the worker can be completely stuck while Consul still shows it healthy right up until the TTL genuinely lapses. TTL checks are only as reliable as the code that calls them.

- Choose HTTP checks for anything that already serves HTTP and exposes Actuator health; choose TTL checks for background workers, batch jobs, or anything without a listening port to poll.
- The check interval directly bounds detection latency for HTTP/TCP/script checks — a 10-second interval means up to 10 seconds between a real failure and Consul noticing it.
- TTL checks invert the responsibility: the application must remember to ping before its own declared deadline, rather than passively waiting to be polled — this is a real implementation obligation, not just configuration.
- Tags (`version=1.2.0`, `team=payments`) don't affect health checking directly, but let discovery queries and Consul's UI filter and group instances meaningfully at scale.
