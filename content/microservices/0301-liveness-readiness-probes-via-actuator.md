---
card: microservices
gi: 301
slug: liveness-readiness-probes-via-actuator
title: "Liveness & readiness probes via Actuator"
---

## 1. What it is

Spring Boot Actuator exposes Kubernetes-compatible liveness and readiness endpoints out of the box — `/actuator/health/liveness` and `/actuator/health/readiness` — once `management.endpoint.health.probes.enabled=true` is set (automatically enabled when Spring Boot detects it's running inside a Kubernetes environment). These map directly onto the [liveness vs readiness](0290-health-checks-for-self-healing.md) distinction: the liveness group reflects the application's `LivenessState` (`CORRECT` or `BROKEN`), and the readiness group reflects its `ReadinessState` (`ACCEPTING_TRAFFIC` or `REFUSING_TRAFFIC`), each independently composed from any registered `HealthIndicator` beans assigned to that group.

## 2. Why & when

Wiring up separate liveness and readiness signals from scratch for every service would be repetitive and error-prone — Actuator standardizes this so that any Spring Boot application gets working, Kubernetes-shaped probe endpoints with minimal configuration, and lets custom health indicators plug into whichever group (or both) is appropriate for what they check. It also automatically publishes `AvailabilityChangeEvent`s that application code can listen for or trigger explicitly — for instance, code that detects an unrecoverable internal problem can publish an event switching `LivenessState` to `BROKEN`, causing Kubernetes to restart the pod, without that code needing to know anything about HTTP endpoints or Kubernetes APIs directly.

Use this whenever deploying a Spring Boot application to Kubernetes (or any orchestrator understanding the liveness/readiness split) — it is the standard, expected integration point, and configuring the orchestrator's `livenessProbe` and `readinessProbe` to point at these two distinct paths is a near-universal deployment requirement for production Spring Boot services.

## 3. Core concept

Health indicators are grouped by contributing to `liveness` or `readiness`; application code can also directly publish availability state changes.

```java
import org.springframework.boot.availability.AvailabilityChangeEvent;
import org.springframework.boot.availability.LivenessState;
import org.springframework.boot.availability.ReadinessState;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Component;

@Component
class SelfHealthMonitor {
    private final ApplicationEventPublisher publisher;
    SelfHealthMonitor(ApplicationEventPublisher publisher) { this.publisher = publisher; }

    void onUnrecoverableError() {
        // Directly flips the LIVENESS state -- Kubernetes' livenessProbe will
        // observe /actuator/health/liveness go DOWN and restart this pod.
        AvailabilityChangeEvent.publish(publisher, this, LivenessState.BROKEN);
    }

    void onStartupWarmupComplete() {
        // Flips READINESS -- this instance can now receive traffic.
        AvailabilityChangeEvent.publish(publisher, this, ReadinessState.ACCEPTING_TRAFFIC);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Registered health indicators contribute to either the liveness group or the readiness group; Actuator aggregates each group into its own endpoint, which Kubernetes polls separately as livenessProbe and readinessProbe, restarting the pod on a liveness failure or removing it from service endpoints on a readiness failure">
  <rect x="20" y="20" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="40" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">HealthIndicator A</text>
  <rect x="20" y="60" width="140" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">HealthIndicator B</text>

  <line x1="160" y1="35" x2="230" y2="55" stroke="#8b949e" marker-end="url(#arr301)"/>
  <line x1="160" y1="75" x2="230" y2="115" stroke="#8b949e" marker-end="url(#arr301)"/>

  <rect x="240" y="35" width="150" height="35" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="315" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">/actuator/health/liveness</text>
  <rect x="240" y="100" width="150" height="35" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="315" y="122" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">/actuator/health/readiness</text>

  <line x1="390" y1="52" x2="470" y2="52" stroke="#8b949e" marker-end="url(#arr301)"/>
  <text x="530" y="47" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">livenessProbe</text>
  <text x="530" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; restart pod</text>

  <line x1="390" y1="117" x2="470" y2="117" stroke="#8b949e" marker-end="url(#arr301)"/>
  <text x="530" y="112" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">readinessProbe</text>
  <text x="530" y="123" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; remove from Service</text>

  <defs><marker id="arr301" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Indicators feed two separate endpoints; Kubernetes polls each independently and reacts with a different, appropriate remedy.

## 5. Runnable example

Scenario: a bare application with no probe endpoints, leaving Kubernetes with no way to know its health, extended to a hand-rolled stand-in for Actuator's grouped health aggregation exposing both endpoints, and finally application code that explicitly publishes availability state changes in response to detected conditions, mirroring `AvailabilityChangeEvent` usage, along with a simulated Kubernetes poller reacting to each endpoint appropriately.

### Level 1 — Basic

```java
// File: NoProbeEndpoints.java -- the application has no health
// endpoints at all; a simulated Kubernetes poller has nothing to check
// and can never detect a real problem inside the process.
public class NoProbeEndpoints {
    static boolean applicationHealthy = true;

    public static void main(String[] args) {
        applicationHealthy = false; // something goes wrong internally
        System.out.println("Application is internally unhealthy: " + !applicationHealthy);
        System.out.println("But there is NO probe endpoint exposing this -- Kubernetes has no way to know, ever.");
    }
}
```

How to run: `java NoProbeEndpoints.java`

The application's internal state genuinely changes to unhealthy, but nothing exposes this to the outside world. A real Kubernetes deployment with no configured probes (or an application with no Actuator health endpoints) would simply never detect this — the broken instance keeps receiving traffic and is never restarted, indefinitely.

### Level 2 — Intermediate

```java
// File: ActuatorStyleHealthGroups.java -- a hand-rolled stand-in for
// Spring Boot Actuator's grouped health aggregation: HealthIndicator
// beans are registered against either the "liveness" or "readiness"
// group, and each group's endpoint aggregates its members' statuses.
import java.util.*;
import java.util.function.Supplier;

public class ActuatorStyleHealthGroups {
    enum Status { UP, DOWN }
    record HealthIndicator(String name, String group, Supplier<Status> check) {}

    static final List<HealthIndicator> indicators = new ArrayList<>();
    static boolean deadlocked = false;
    static boolean databaseConnected = true;

    static {
        // "liveness" group: reflects the PROCESS's own internal health.
        indicators.add(new HealthIndicator("deadlockDetector", "liveness",
                () -> deadlocked ? Status.DOWN : Status.UP));
        // "readiness" group: reflects ability to serve traffic RIGHT NOW.
        indicators.add(new HealthIndicator("database", "readiness",
                () -> databaseConnected ? Status.UP : Status.DOWN));
    }

    static Status aggregateGroup(String group) {
        return indicators.stream()
                .filter(ind -> ind.group().equals(group))
                .anyMatch(ind -> ind.check().get() == Status.DOWN) ? Status.DOWN : Status.UP;
    }

    static String probeLiveness() { return "/actuator/health/liveness -> " + aggregateGroup("liveness"); }
    static String probeReadiness() { return "/actuator/health/readiness -> " + aggregateGroup("readiness"); }

    public static void main(String[] args) {
        System.out.println(probeLiveness());
        System.out.println(probeReadiness());

        databaseConnected = false; // DB connection lost
        System.out.println("-- after DB connection lost --");
        System.out.println(probeLiveness());   // still UP -- process itself is fine
        System.out.println(probeReadiness());  // now DOWN -- can't serve correctly
    }
}
```

How to run: `java ActuatorStyleHealthGroups.java`

Initially both probes report `UP`. Once `databaseConnected` flips to `false`, the readiness group's aggregation correctly reports `DOWN` (since its member indicator, `database`, now returns `DOWN`), while the liveness group is entirely unaffected and stays `UP`, since `deadlockDetector` (the only liveness-group indicator) never changed. This mirrors exactly how Actuator's real `/actuator/health/liveness` and `/actuator/health/readiness` endpoints aggregate only the indicators assigned to their respective groups — a database connectivity problem correctly shows up only in readiness.

### Level 3 — Advanced

```java
// File: ExplicitAvailabilityEventsWithKubernetesPoller.java -- application
// code EXPLICITLY publishes availability state changes (mirroring
// AvailabilityChangeEvent.publish(...)) rather than relying only on
// passive HealthIndicator polling, combined with a simulated Kubernetes
// poller that reacts differently to each probe's outcome.
public class ExplicitAvailabilityEventsWithKubernetesPoller {
    enum LivenessState { CORRECT, BROKEN }
    enum ReadinessState { ACCEPTING_TRAFFIC, REFUSING_TRAFFIC }

    static LivenessState livenessState = LivenessState.CORRECT;
    static ReadinessState readinessState = ReadinessState.REFUSING_TRAFFIC; // starts REFUSING during startup

    // Mirrors AvailabilityChangeEvent.publish(publisher, source, state)
    static void publishLiveness(LivenessState newState) {
        livenessState = newState;
        System.out.println("  [event] LivenessState -> " + newState);
    }
    static void publishReadiness(ReadinessState newState) {
        readinessState = newState;
        System.out.println("  [event] ReadinessState -> " + newState);
    }

    static class KubernetesPoller {
        boolean restarted = false;
        boolean inServiceEndpoints = false;

        void poll() {
            if (livenessState == LivenessState.BROKEN) {
                System.out.println("  [k8s] livenessProbe FAILED -- restarting pod");
                restarted = true;
                return; // pod is being replaced; readiness is moot until the new pod starts
            }
            inServiceEndpoints = (readinessState == ReadinessState.ACCEPTING_TRAFFIC);
            System.out.println("  [k8s] readinessProbe " + (inServiceEndpoints ? "PASSED -- in Service endpoints" : "FAILED -- removed from Service endpoints"));
        }
    }

    public static void main(String[] args) {
        KubernetesPoller k8s = new KubernetesPoller();

        System.out.println("-- application starting up --");
        k8s.poll(); // still warming up, readiness = REFUSING_TRAFFIC

        System.out.println("-- warmup complete --");
        publishReadiness(ReadinessState.ACCEPTING_TRAFFIC);
        k8s.poll();

        System.out.println("-- unrecoverable internal error detected --");
        publishLiveness(LivenessState.BROKEN);
        k8s.poll();
    }
}
```

How to run: `java ExplicitAvailabilityEventsWithKubernetesPoller.java`

The application starts with `readinessState=REFUSING_TRAFFIC` (a realistic default during startup/warmup), so the first poll correctly keeps it out of Service endpoints even though liveness is fine. Once warmup logic explicitly calls `publishReadiness(ACCEPTING_TRAFFIC)` — mirroring real code calling `AvailabilityChangeEvent.publish(...)` once initialization completes — the next poll shows the instance entering the Service's traffic rotation. Finally, simulated code detects an unrecoverable internal error and explicitly publishes `LivenessState.BROKEN`; the poller's next check short-circuits on the liveness failure first and triggers a pod restart, without even evaluating readiness — matching the real precedence where a broken process needs replacing, not just traffic-draining.

## 6. Walkthrough

Trace `ExplicitAvailabilityEventsWithKubernetesPoller.main` in order. **First**, `livenessState` starts `CORRECT` and `readinessState` starts `REFUSING_TRAFFIC` — the realistic default for an application still starting up.

**The first `k8s.poll()` call**: `livenessState == LivenessState.BROKEN` is `false`, so the method proceeds to the readiness check. `inServiceEndpoints = (readinessState == ReadinessState.ACCEPTING_TRAFFIC)` evaluates to `false`, since `readinessState` is still `REFUSING_TRAFFIC`. The poller prints "readinessProbe FAILED -- removed from Service endpoints" — correctly keeping this still-warming-up instance out of traffic.

**`publishReadiness(ReadinessState.ACCEPTING_TRAFFIC)` is called**, simulating application startup code finishing its warmup (e.g., pre-loading a cache, establishing connection pools) and explicitly signaling readiness — this directly sets `readinessState`.

**The second `k8s.poll()` call**: liveness check still passes (`CORRECT`), so it proceeds to readiness — now `readinessState == ACCEPTING_TRAFFIC` is `true`, so `inServiceEndpoints` becomes `true`, and the poller prints "readinessProbe PASSED -- in Service endpoints." The instance now begins receiving real traffic.

**`publishLiveness(LivenessState.BROKEN)` is called**, simulating application code detecting a genuinely unrecoverable problem (e.g., a deadlock detector firing) and explicitly signaling that the process itself is broken.

**The third `k8s.poll()` call**: this time `livenessState == LivenessState.BROKEN` is `true` at the very first check — the method prints "livenessProbe FAILED -- restarting pod," sets `restarted = true`, and `return`s immediately, *without* ever evaluating the readiness branch at all, since a liveness failure supersedes any readiness consideration — the pod is being torn down and replaced regardless of what its readiness state currently says.

```
poll 1: readiness=REFUSING -> "removed from Service endpoints" (still warming up)
publishReadiness(ACCEPTING_TRAFFIC)
poll 2: readiness=ACCEPTING -> "in Service endpoints" (now serving traffic)
publishLiveness(BROKEN)
poll 3: liveness=BROKEN -> "restarting pod" (readiness check never even reached)
```

## 7. Gotchas & takeaways

> Spring Boot's readiness state defaults to `REFUSING_TRAFFIC` until the application context has fully started (an `ApplicationReadyEvent`-adjacent point) — if a custom health indicator or the `readinessProbe`'s `initialDelaySeconds` is misconfigured to check too early, a perfectly healthy, still-starting application can appear to fail its readiness probe, delaying rollout unnecessarily rather than indicating a real problem.

- `management.endpoint.health.probes.enabled=true` (auto-enabled under detected Kubernetes environments) is required to expose the dedicated `/actuator/health/liveness` and `/actuator/health/readiness` paths as separate, Kubernetes-shaped endpoints.
- Custom `HealthIndicator` beans can be assigned to the `liveness` or `readiness` group via `management.endpoint.health.group.<name>.include`, letting application-specific checks (a deadlock detector, a critical cache warm-up flag) plug into the right signal.
- `AvailabilityChangeEvent.publish(...)` lets application code directly and explicitly declare a state change (e.g., after detecting an unrecoverable condition), rather than relying solely on a `HealthIndicator` being polled reactively — useful for conditions the application itself detects proactively.
- Configure the corresponding Kubernetes `livenessProbe` and `readinessProbe` in the deployment manifest to point at these two distinct paths, with `initialDelaySeconds` tuned to the application's real startup time to avoid premature liveness restarts during normal startup.
