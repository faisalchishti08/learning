---
card: microservices
gi: 373
slug: actuator-health-groups-liveness-readiness
title: "Actuator health groups (liveness / readiness)"
---

## 1. What it is

**Actuator health groups** let a single `/actuator/health` endpoint expose multiple, differently-scoped health views — most importantly the built-in `liveness` and `readiness` groups, each aggregating a different subset of health indicators, reachable at `/actuator/health/liveness` and `/actuator/health/readiness`. This directly supports the distinction covered earlier in [liveness & readiness probes via Actuator](0301-liveness-readiness-probes-via-actuator.md): liveness answers "is this process alive and not deadlocked" (should Kubernetes restart it), while readiness answers "is this instance ready to receive traffic right now" (should the load balancer route to it) — two genuinely different questions that shouldn't share the same answer.

## 2. Why & when

A single, undifferentiated `/actuator/health` mixes concerns that need different responses: if the database is temporarily unreachable, the *process itself* is still perfectly alive (restarting it won't fix a database outage, and would just cause unnecessary churn), but the instance genuinely isn't ready to serve requests that need that database. Health groups let these two questions have two different, independently correct answers from the same running instance, rather than forcing one combined health check to somehow serve both Kubernetes' restart decision and the load balancer's routing decision.

Configure the `readiness` group to include health indicators for anything the instance needs to actually serve requests correctly (database connectivity, downstream service dependencies if critical), and keep the `liveness` group narrowly scoped to just "is the JVM/process itself still functioning" (deliberately excluding external dependency checks, since those shouldn't trigger a restart). Wire Kubernetes' `livenessProbe` to `/actuator/health/liveness` and its `readinessProbe` to `/actuator/health/readiness`, exactly matching each group to the corresponding Kubernetes probe.

## 3. Core concept

Each health group is configured with a specific set of health indicators to include; when that group's endpoint is queried, only those indicators are checked and aggregated into the group's own `UP`/`DOWN` status, independent of any other group's result. A database indicator can legitimately report `DOWN` for the readiness group (correctly telling the load balancer to stop routing here) while the liveness group, not including that indicator, still reports `UP` (correctly telling Kubernetes the process itself doesn't need restarting).

```yaml
management:
  endpoint:
    health:
      group:
        readiness:
          include: readinessState, db, downstreamService
        liveness:
          include: livenessState
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Database goes down; the readiness group, which includes the db indicator, reports DOWN, correctly stopping traffic; the liveness group, which does not include db, still reports UP, correctly avoiding an unnecessary restart">
  <rect x="20" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Database DOWN</text>

  <line x1="200" y1="37" x2="270" y2="70" stroke="#f85149" marker-end="url(#a373)"/>
  <rect x="280" y="55" width="180" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="370" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">readiness: DOWN (stop routing)</text>

  <line x1="200" y1="37" x2="270" y2="120" stroke="#3fb950" marker-end="url(#a373b)"/>
  <rect x="280" y="105" width="180" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="370" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">liveness: UP (no restart needed)</text>

  <defs>
    <marker id="a373" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="a373b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The same database outage correctly produces two different answers, because readiness and liveness groups check different indicator sets for different purposes.

## 5. Runnable example

Scenario: a service with a database dependency, first with only one undifferentiated health check causing an unnecessary restart during a database outage, then fixed with separate liveness and readiness groups, and finally extended to show the correct Kubernetes-style behavior driven by each group's independent result.

### Level 1 — Basic

```java
// File: SingleUndifferentiatedHealth.java -- ONE health check covers
// EVERYTHING; a database outage makes the WHOLE health check report
// DOWN, which (if used naively for BOTH liveness and readiness) would
// cause an UNNECESSARY restart that won't even fix the database outage.
import java.util.*;

public class SingleUndifferentiatedHealth {
    static boolean databaseUp = true;
    static boolean processAlive = true; // the JVM/process itself is FINE

    static String getHealth() { // ONE combined check -- mixes process health with external dependency health
        return (databaseUp && processAlive) ? "UP" : "DOWN";
    }

    public static void main(String[] args) {
        databaseUp = false; // simulate a database outage; the PROCESS itself is still perfectly fine

        String health = getHealth();
        System.out.println("/health -> " + health);
        System.out.println("If Kubernetes used THIS single check for BOTH liveness and readiness, it would RESTART "
                + "the process -- but restarting does NOTHING to fix a database outage, and just adds unnecessary churn.");
    }
}
```

How to run: `java SingleUndifferentiatedHealth.java`

`getHealth` reports `DOWN` the moment `databaseUp` is `false`, even though `processAlive` is still `true` — if this single, undifferentiated check were wired to both Kubernetes' liveness and readiness probes, Kubernetes would restart the process based on the liveness probe failing, which is completely useless for fixing an external database outage and just adds unnecessary disruption on top of an already-degraded situation.

### Level 2 — Intermediate

```java
// File: SeparateLivenessReadinessGroups.java -- TWO separate groups,
// each checking a DIFFERENT set of indicators, giving the CORRECT
// independent answer for each purpose.
import java.util.*;

public class SeparateLivenessReadinessGroups {
    static boolean databaseUp = true;
    static boolean processAlive = true;

    // Liveness group: ONLY checks the process itself -- deliberately EXCLUDES external dependencies.
    static String getLivenessHealth() { return processAlive ? "UP" : "DOWN"; }

    // Readiness group: checks EVERYTHING needed to correctly serve traffic, INCLUDING external dependencies.
    static String getReadinessHealth() { return (processAlive && databaseUp) ? "UP" : "DOWN"; }

    public static void main(String[] args) {
        databaseUp = false; // same database outage as Level 1

        System.out.println("/actuator/health/liveness -> " + getLivenessHealth() + " -- process is fine, NO restart needed");
        System.out.println("/actuator/health/readiness -> " + getReadinessHealth() + " -- correctly stop routing traffic here");
    }
}
```

How to run: `java SeparateLivenessReadinessGroups.java`

With the same `databaseUp = false` condition, `getLivenessHealth` correctly reports `UP` (it never checks `databaseUp` at all), while `getReadinessHealth` correctly reports `DOWN` (it does check `databaseUp`). The two groups give genuinely different, independently correct answers for the same underlying situation, exactly matching what each consuming system (Kubernetes for liveness, the load balancer for readiness) actually needs to know.

### Level 3 — Advanced

```java
// File: KubernetesStyleProbeBehavior.java -- simulates how Kubernetes
// (or a load balancer) would ACT on each group's result: liveness DOWN
// triggers a restart, readiness DOWN removes the instance from the load
// balancer's routing pool -- TWO DIFFERENT actions, correctly triggered
// independently.
import java.util.*;

public class KubernetesStyleProbeBehavior {
    static boolean databaseUp = true;
    static boolean processAlive = true;

    static String getLivenessHealth() { return processAlive ? "UP" : "DOWN"; }
    static String getReadinessHealth() { return (processAlive && databaseUp) ? "UP" : "DOWN"; }

    static void simulateKubernetesProbeCycle() {
        String liveness = getLivenessHealth();
        String readiness = getReadinessHealth();

        if (liveness.equals("DOWN")) {
            System.out.println("  Kubernetes liveness probe FAILED -- RESTARTING the container.");
        } else {
            System.out.println("  Kubernetes liveness probe OK -- container left running.");
        }

        if (readiness.equals("DOWN")) {
            System.out.println("  Load balancer readiness probe FAILED -- REMOVING this instance from the routing pool.");
        } else {
            System.out.println("  Load balancer readiness probe OK -- instance remains IN the routing pool.");
        }
    }

    public static void main(String[] args) {
        System.out.println("--- Scenario: database outage, process fine ---");
        databaseUp = false;
        simulateKubernetesProbeCycle();

        System.out.println("--- Scenario: database recovers ---");
        databaseUp = true;
        simulateKubernetesProbeCycle();

        System.out.println("--- Scenario: the PROCESS itself deadlocks (simulated) ---");
        processAlive = false;
        simulateKubernetesProbeCycle();
    }
}
```

How to run: `java KubernetesStyleProbeBehavior.java`

During the database outage, `simulateKubernetesProbeCycle` shows the liveness probe passing (no restart) while the readiness probe fails (removed from routing) — exactly the correct, differentiated response. Once the database recovers, both probes pass and the instance rejoins the routing pool automatically. Finally, when `processAlive` is set to `false` (simulating an actual process-level problem, like a deadlock), the liveness probe now correctly fails too, triggering the restart that's actually warranted in that specific case — demonstrating that each group correctly drives its own distinct, appropriate action.

## 6. Walkthrough

Trace `KubernetesStyleProbeBehavior.main` in order. **First**, `databaseUp` is set to `false`, and `simulateKubernetesProbeCycle()` runs: `getLivenessHealth()` returns `"UP"` (it doesn't check `databaseUp`), so the `if (liveness.equals("DOWN"))` branch is skipped and "container left running" prints. `getReadinessHealth()` returns `"DOWN"` (since `databaseUp` is `false`), so the `if (readiness.equals("DOWN"))` branch fires, printing that the instance is removed from the routing pool.

**Next**, `databaseUp` is set back to `true`, and `simulateKubernetesProbeCycle()` runs again: both `getLivenessHealth()` and `getReadinessHealth()` now return `"UP"`, so both `if` branches are skipped, printing that the container keeps running and the instance stays in the routing pool.

**Finally**, `processAlive` is set to `false`, simulating an actual process-level failure (like a deadlock), and `simulateKubernetesProbeCycle()` runs a third time: `getLivenessHealth()` now returns `"DOWN"` (since it does check `processAlive`), triggering the restart branch; `getReadinessHealth()` also returns `"DOWN"` (since it requires *both* `processAlive` and `databaseUp` to be true, and `processAlive` is now false), triggering the routing-removal branch too — in this specific case, both actions are correctly warranted simultaneously, since the process itself is genuinely broken.

```
Scenario 1 (db down, process fine):     liveness=UP (no restart)     readiness=DOWN (removed from routing)
Scenario 2 (db recovers):               liveness=UP (no restart)     readiness=UP   (back in routing)
Scenario 3 (process itself deadlocked): liveness=DOWN (RESTART)      readiness=DOWN (removed from routing)
```

## 7. Gotchas & takeaways

> Including an external dependency check (like database connectivity) in the *liveness* group is a common and costly misconfiguration — it causes Kubernetes to restart a perfectly healthy process during an external outage that a restart cannot fix, potentially making an already-degraded situation worse by adding restart churn on top of it. Keep liveness narrowly scoped to the process itself.

- Actuator health groups let `/actuator/health/liveness` and `/actuator/health/readiness` report independently, checking different sets of health indicators for different purposes.
- Liveness should check only whether the process itself is functioning (deliberately excluding external dependencies); readiness should check everything actually needed to correctly serve requests.
- The same underlying condition (a database outage) correctly produces different results from each group, driving the appropriately different actions: no restart from liveness, removal from the routing pool from readiness.
- This builds directly on [liveness & readiness probes via Actuator](0301-liveness-readiness-probes-via-actuator.md), giving Kubernetes and load balancers the precisely-scoped signals each one actually needs.
