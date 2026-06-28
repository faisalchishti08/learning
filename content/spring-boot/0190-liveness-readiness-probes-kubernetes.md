---
card: spring-boot
gi: 190
slug: liveness-readiness-probes-kubernetes
title: Liveness & readiness probes (Kubernetes)
---

## 1. What it is

When a Spring Boot application runs in **Kubernetes**, the platform polls two HTTP paths to decide what to do with a pod:
- **Liveness probe** (`/actuator/health/liveness`): "Is this process alive?" Failure → pod restarts.
- **Readiness probe** (`/actuator/health/readiness`): "Is this pod ready to receive traffic?" Failure → pod removed from the Service, traffic stops — no restart.

Enable both with one property: `management.endpoint.health.probes.enabled=true`. Spring Boot then registers the `liveness` and `readiness` health groups automatically.

## 2. Why & when

**Without proper probes:** Kubernetes starts routing traffic as soon as the container starts, before Spring context is fully initialized — users get 503s. Or, a deadlocked pod keeps receiving traffic because k8s doesn't know it's broken.

**Liveness** should only test JVM/process liveness — not external dependencies. A DB outage should **not** restart the pod (all pods would restart simultaneously, turning a recoverable outage into a cascading failure).

**Readiness** should test everything needed to serve traffic — DB, caches, downstream APIs. A DOWN readiness removes the pod from the load balancer, stopping traffic without a restart.

## 3. Core concept

Spring Boot 2.3+ tracks two availability states:
- **`LivenessState`**: `CORRECT` (normal) or `BROKEN` (application detected an unrecoverable error).
- **`ReadinessState`**: `ACCEPTING_TRAFFIC` (normal) or `REFUSING_TRAFFIC` (startup/shutdown/maintenance).

`ApplicationAvailability` bean manages these states. Health groups map to them:
- `liveness` group → checks `livenessState` indicator.
- `readiness` group → checks `readinessState` + all other `HealthIndicator`s by default.

Application events automatically update readiness state:
- Context refresh complete → `ACCEPTING_TRAFFIC`.
- `ApplicationContext.close()` called → `REFUSING_TRAFFIC` (before shutdown hooks run).

Kubernetes pod spec:
```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 30
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 10
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kubernetes polls liveness and readiness probes; liveness failure triggers restart, readiness failure removes pod from service">
  <!-- Kubernetes -->
  <rect x="10" y="35" width="130" height="140" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="58" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Kubernetes</text>
  <text x="75" y="76" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">livenessProbe</text>
  <text x="75" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fail → restart pod</text>
  <rect x="20" y="100" width="100" height="1" fill="#8b949e"/>
  <text x="75" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">readinessProbe</text>
  <text x="75" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fail → remove from</text>
  <text x="75" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Service endpoints</text>

  <!-- Arrows to app -->
  <line x1="143" y1="83" x2="240" y2="83" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#kpa)"/>
  <text x="192" y="76" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">GET /health/liveness</text>

  <line x1="143" y1="120" x2="240" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#kpa)"/>
  <text x="192" y="113" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">GET /health/readiness</text>

  <!-- Spring Boot Pod -->
  <rect x="245" y="30" width="240" height="155" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="365" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Boot Pod</text>

  <!-- Liveness -->
  <rect x="260" y="60" width="210" height="44" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="365" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">/actuator/health/liveness</text>
  <text x="365" y="92" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">livenessState: CORRECT → UP → 200</text>

  <!-- Readiness -->
  <rect x="260" y="112" width="210" height="60" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="365" y="129" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">/actuator/health/readiness</text>
  <text x="365" y="144" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">readinessState + db + redis</text>
  <text x="365" y="159" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">any DOWN → 503 → removed from LB</text>

  <!-- Outcomes -->
  <rect x="520" y="55" width="155" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="597" y="73" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">200 → pod alive</text>
  <text x="597" y="86" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">503 → pod restarted</text>

  <rect x="520" y="110" width="155" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="597" y="128" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">200 → serves traffic</text>
  <text x="597" y="141" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">503 → no traffic, no restart</text>

  <line x1="488" y1="83" x2="518" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#kpb)"/>
  <line x1="488" y1="130" x2="518" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#kpb)"/>

  <text x="350" y="198" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">management.endpoint.health.probes.enabled=true creates both groups automatically</text>

  <defs>
    <marker id="kpa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="kpb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Liveness restart on JVM failure; readiness traffic-removal on dependency failure — different responses, one property enables both.

## 5. Runnable example

```java
// LivenessReadinessDemo.java — simulates liveness/readiness lifecycle during startup, operation, failure
// How to run: java LivenessReadinessDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: management.endpoint.health.probes.enabled=true  (auto-wires these probes)

import java.util.*;

public class LivenessReadinessDemo {

    enum LivenessState  { CORRECT, BROKEN }
    enum ReadinessState { ACCEPTING_TRAFFIC, REFUSING_TRAFFIC }

    static LivenessState  liveness  = LivenessState.CORRECT;
    static ReadinessState readiness = ReadinessState.REFUSING_TRAFFIC; // starts refusing during startup
    static boolean        dbUp      = true;

    static Map<String, Object> getLivenessHealth() {
        String status = liveness == LivenessState.CORRECT ? "UP" : "DOWN";
        return Map.of("status", status, "livenessState", liveness);
    }

    static Map<String, Object> getReadinessHealth() {
        String stateStatus = readiness == ReadinessState.ACCEPTING_TRAFFIC ? "UP" : "OUT_OF_SERVICE";
        String dbStatus    = dbUp ? "UP" : "DOWN";
        String overall     = (stateStatus.equals("UP") && dbStatus.equals("UP")) ? "UP" : "DOWN";
        return Map.of("status", overall, "readinessState", readiness, "db", dbStatus);
    }

    static void checkProbes(String phase) {
        var live  = getLivenessHealth();
        var ready = getReadinessHealth();
        System.out.printf("[%s]%n", phase);
        System.out.printf("  /health/liveness  → %s  %s%n", live.get("status"),
                live.get("status").equals("UP") ? "(pod alive)" : "(k8s will RESTART)");
        System.out.printf("  /health/readiness → %s  %s%n", ready.get("status"),
                ready.get("status").equals("UP") ? "(traffic flows)" : "(pod REMOVED from Service)");
        System.out.println();
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Liveness & Readiness Probes (Kubernetes) Demo ===\n");

        // 1. Pod starting: liveness=UP but readiness=OUT_OF_SERVICE (no traffic yet)
        checkProbes("Phase 1: Startup — context loading");

        // 2. Context fully loaded (ApplicationContext refresh event → ACCEPTING_TRAFFIC)
        readiness = ReadinessState.ACCEPTING_TRAFFIC;
        checkProbes("Phase 2: Ready — context fully loaded");

        // 3. Database goes down
        dbUp = false;
        checkProbes("Phase 3: DB outage — readiness DOWN, liveness still UP");
        System.out.println("  ✓ Kubernetes removes pod from load balancer (traffic stops)");
        System.out.println("  ✓ Pod is NOT restarted (liveness is still UP)");
        System.out.println("  ✓ When DB recovers, readiness → UP → pod rejoins Service\n");

        // 4. DB recovers
        dbUp = true;
        checkProbes("Phase 4: DB recovered — back to serving traffic");

        // 5. Application detects unrecoverable state
        liveness = LivenessState.BROKEN;
        checkProbes("Phase 5: Unrecoverable error — liveness BROKEN");
        System.out.println("  ✓ Kubernetes restarts the pod (liveness failed)");
        System.out.println("  ✓ Both probes fail now: pod is removed AND restarted\n");

        // 6. Graceful shutdown
        liveness  = LivenessState.CORRECT;
        readiness = ReadinessState.REFUSING_TRAFFIC; // set before shutdown hooks
        dbUp      = true;
        checkProbes("Phase 6: Graceful shutdown — readiness REFUSING before stop");
        System.out.println("  ✓ Traffic drained before process exits");
        System.out.println("  ✓ Set via: ApplicationAvailability.publishEvent(ReadinessState.REFUSING_TRAFFIC)");
    }
}
```

**How to run:** `java LivenessReadinessDemo.java`

## 6. Walkthrough

- **Phase 1**: readiness starts as `REFUSING_TRAFFIC` — Spring Boot sets this on startup before the context finishes loading. K8s won't send traffic until the pod is ready.
- **Phase 2**: the context refresh event fires → `ACCEPTING_TRAFFIC` → readiness becomes UP → k8s adds pod to Service endpoints.
- **Phase 3**: DB goes down → readiness DOWN → pod removed from Service. But liveness is still UP (JVM is fine) → no restart. When DB recovers (Phase 4), readiness recovers automatically.
- **Phase 5**: application calls `availability.publishEvent(LivenessState.BROKEN)` (or throws an unhandled exception in a background thread) → liveness DOWN → k8s restarts the pod.
- **Phase 6**: before `SIGTERM`, set readiness to `REFUSING_TRAFFIC` → k8s stops routing traffic → shutdown hooks drain in-flight requests → process exits cleanly.

## 7. Gotchas & takeaways

> Never include external dependencies (DB, Redis) in the **liveness** group. Their outage should cause readiness failure (traffic removal), not liveness failure (pod restart) — which would restart all pods simultaneously during an outage.

> `initialDelaySeconds` on the k8s probe must be long enough for Spring Boot to start (typically 20-60 seconds). Under-tuned values cause liveness failures during slow startup, creating a restart loop.

- `management.endpoint.health.probes.enabled=true` — one property enables both groups.
- Spring Boot auto-sets readiness to `REFUSING_TRAFFIC` during context close (graceful shutdown) if `spring.lifecycle.timeout-per-shutdown-phase` is configured.
- Signal BROKEN liveness: inject `ApplicationEventPublisher` and publish `AvailabilityChangeEvent.publish(publisher, this, LivenessState.BROKEN)`.
- Customise readiness group: `management.endpoint.health.group.readiness.include=readinessState,db` to explicitly control which indicators affect readiness.
- Kubernetes deployment example: set `failureThreshold: 3, periodSeconds: 10` — three consecutive failures before restarting. Single transient failure doesn't trigger a restart.
