---
card: microservices
gi: 473
slug: spring-boot-actuator-liveness-readiness-probes-for-kubernete
title: "Spring Boot Actuator liveness/readiness probes for Kubernetes"
---

## 1. What it is

Spring Boot **Actuator** exposes two distinct health endpoints — `/actuator/health/liveness` and `/actuator/health/readiness` — designed to answer two different questions Kubernetes asks about a running Pod. **Liveness** answers "is this process alive and functioning, or should it be restarted?" **Readiness** answers "can this instance currently handle traffic, or should it be temporarily removed from the routable pool?" Kubernetes polls each endpoint separately and takes different action depending on which one fails.

## 2. Why & when

You configure both probes, and keep their logic genuinely distinct, because conflating "alive" and "ready" causes two very different, very real failure modes:

- **A deadlocked or wedged process needs restarting, not just removal from traffic.** If liveness fails, Kubernetes kills and restarts the container — the right response to a process that's technically running but permanently stuck.
- **A temporarily-overloaded or dependency-starved instance needs traffic paused, not a restart.** If a database connection pool is briefly exhausted, restarting the process doesn't fix that and just adds startup churn — readiness failing simply removes the Pod from the load balancer's routable set until it recovers on its own.
- **Using the same check for both endpoints causes cascading, unnecessary restarts.** If a temporary database outage makes an instance fail its *liveness* check (because it was really only meant to signal "not ready right now"), Kubernetes restarts every affected Pod — which does nothing to bring the database back and just adds thrashing on top of an already-degraded situation.
- **You configure both, correctly separated, on every Spring Boot service deployed to Kubernetes** — this is standard, expected configuration for any production Kubernetes deployment, not an advanced or optional feature.

## 3. Core concept

Think of a restaurant kitchen: "is the kitchen on fire" (liveness — if true, evacuate and rebuild) is a completely different question from "is the kitchen currently able to take a new order" (readiness — if no, the host simply stops seating new customers at that kitchen's tables until it catches up, no rebuilding required). Confusing the two means either burning down a kitchen that was just temporarily backed up, or leaving customers being seated at a kitchen that's genuinely on fire.

Concretely:

1. **Liveness checks internal application health that only a restart can fix** — deadlocks, unrecoverable internal state, a genuinely crashed application thread. Spring Boot's liveness state is typically simple: the application context started successfully and hasn't entered a broken state.
2. **Readiness checks whether the instance can currently serve requests successfully** — often including whether its downstream dependencies (a database, a required upstream service) are currently reachable.
3. **Kubernetes polls each endpoint on its own schedule**, defined in the Pod spec's `livenessProbe` and `readinessProbe` configuration (path, interval, failure threshold).
4. **A failing liveness probe triggers a container restart.** A failing readiness probe removes the Pod from a Service's routable endpoints, without touching the container's running process at all — it stays running, just temporarily out of rotation.
5. **Readiness recovering automatically re-adds the Pod to the routable set** the next time the probe succeeds — no restart needed, no manual intervention, the instance simply rejoins traffic once it's actually able to handle it again.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kubernetes polls liveness and readiness separately: a failing liveness probe restarts the container, a failing readiness probe only removes it from traffic">
  <rect x="20" y="20" width="280" height="90" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="160" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">liveness probe fails</text>
  <text x="160" y="65" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">"process is stuck, unrecoverable"</text>
  <text x="160" y="85" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">-&gt; Kubernetes RESTARTS the container</text>

  <rect x="360" y="20" width="280" height="90" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="500" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">readiness probe fails</text>
  <text x="500" y="65" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">"temporarily can't serve traffic"</text>
  <text x="500" y="85" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">-&gt; Kubernetes REMOVES Pod from traffic only</text>

  <text x="330" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the SAME running Pod behaves completely differently depending on WHICH probe failed</text>

</svg>

Liveness and readiness answer different questions and drive different Kubernetes actions on the same Pod.

## 5. Runnable example

Scenario: a health-monitoring loop simulating Kubernetes polling both probes for a service. We start with a basic distinct-probe check, extend it to show a readiness failure that only affects traffic routing, then handle the hard case: a temporary database outage that must fail readiness (pausing traffic) without ever failing liveness (avoiding an unnecessary, unhelpful restart).

### Level 1 — Basic

```java
// File: ProbesBasic.java -- models TWO distinct probes for one service,
// checked independently, each answering a DIFFERENT question.
public class ProbesBasic {
    static boolean checkLiveness() {
        System.out.println("[probe] liveness: application context started, no deadlock detected");
        return true;
    }

    static boolean checkReadiness() {
        System.out.println("[probe] readiness: dependencies reachable, ready for traffic");
        return true;
    }

    public static void main(String[] args) {
        boolean alive = checkLiveness();
        boolean ready = checkReadiness();
        System.out.println("[kubernetes] liveness=" + alive + " (restart if false), readiness=" + ready + " (route traffic if true)");
    }
}
```

How to run: `java ProbesBasic.java`

`checkLiveness` and `checkReadiness` are two entirely separate methods, called independently and never sharing logic — mirroring the two genuinely different endpoints Kubernetes polls, `/actuator/health/liveness` and `/actuator/health/readiness`.

### Level 2 — Intermediate

```java
// File: ProbesReadinessOnly.java -- the SAME two probes, now showing a
// READINESS-only failure: the application is alive and healthy, but
// temporarily can't serve traffic (e.g. still warming up a cache) --
// liveness stays TRUE throughout, so no restart happens.
public class ProbesReadinessOnly {
    static boolean applicationStarted = true; // never becomes false in this scenario
    static boolean cacheWarmedUp = false; // starts false, becomes true after warm-up completes

    static boolean checkLiveness() {
        boolean alive = applicationStarted;
        System.out.println("[probe] liveness: " + (alive ? "OK -- process running normally" : "FAILED"));
        return alive;
    }

    static boolean checkReadiness() {
        boolean ready = applicationStarted && cacheWarmedUp;
        System.out.println("[probe] readiness: " + (ready ? "OK -- ready for traffic" : "NOT READY -- cache still warming up"));
        return ready;
    }

    public static void main(String[] args) {
        System.out.println("--- poll 1: just started, cache not warm yet ---");
        checkLiveness();
        checkReadiness();

        System.out.println();
        System.out.println("--- cache finishes warming up ---");
        cacheWarmedUp = true;

        System.out.println();
        System.out.println("--- poll 2: cache is now warm ---");
        checkLiveness();
        checkReadiness();
    }
}
```

How to run: `java ProbesReadinessOnly.java`

`applicationStarted` never changes across this whole run, so `checkLiveness` returns `true` on both polls — no restart would ever be triggered. `checkReadiness`, by contrast, depends on `cacheWarmedUp`, which starts `false` and only becomes `true` between poll 1 and poll 2 — so readiness genuinely transitions from `false` to `true` while liveness stays constant throughout, demonstrating the two signals evolving completely independently.

### Level 3 — Advanced

```java
// File: ProbesDbOutageIsolated.java -- the SAME two independent probes,
// now handling the PRODUCTION-FLAVORED hard case: a TEMPORARY DATABASE
// OUTAGE. Readiness MUST fail (the app genuinely can't serve DB-backed
// requests), but liveness MUST stay healthy throughout -- restarting the
// application process does nothing to fix a database that's down, and
// would just add restart churn on top of an already-degraded system.
public class ProbesDbOutageIsolated {
    static boolean applicationProcessHealthy = true; // the JVM itself is fine the whole time
    static boolean databaseReachable = true;

    static boolean checkLiveness() {
        // Liveness deliberately does NOT depend on the database --
        // a down database is not a reason to restart a perfectly healthy process.
        boolean alive = applicationProcessHealthy;
        System.out.println("[probe] liveness: " + (alive ? "OK" : "FAILED (would trigger restart)"));
        return alive;
    }

    static boolean checkReadiness() {
        // Readiness DOES depend on the database -- traffic shouldn't be routed
        // to an instance that can't actually serve DB-backed requests.
        boolean ready = applicationProcessHealthy && databaseReachable;
        System.out.println("[probe] readiness: " + (ready ? "OK" : "NOT READY (removed from traffic, no restart)"));
        return ready;
    }

    static void simulatePoll(int pollNumber) {
        System.out.println("--- poll " + pollNumber + " ---");
        boolean alive = checkLiveness();
        boolean ready = checkReadiness();
        if (!alive) {
            System.out.println("[kubernetes] RESTARTING container");
        } else if (!ready) {
            System.out.println("[kubernetes] Pod removed from Service endpoints, container left running untouched");
        } else {
            System.out.println("[kubernetes] Pod healthy and receiving traffic normally");
        }
    }

    public static void main(String[] args) {
        simulatePoll(1); // everything healthy

        System.out.println();
        System.out.println("[incident] database goes down");
        databaseReachable = false;
        simulatePoll(2); // db down: readiness fails, liveness stays fine

        System.out.println();
        System.out.println("[incident] database comes back up");
        databaseReachable = true;
        simulatePoll(3); // recovered: readiness passes again, with NO restart ever having happened
    }
}
```

How to run: `java ProbesDbOutageIsolated.java`

`checkLiveness`'s condition, `applicationProcessHealthy`, never references `databaseReachable` at all — by design, a database outage can never fail liveness in this code, no matter what happens to `databaseReachable`. `checkReadiness`'s condition explicitly includes `databaseReachable`, so it fails the moment the simulated outage sets that flag to `false`, and `simulatePoll`'s `if (!alive) ... else if (!ready) ...` branch correctly routes to the "removed from traffic, no restart" outcome rather than the restart outcome, because `alive` stayed `true` throughout the entire incident.

## 6. Walkthrough

Trace `ProbesDbOutageIsolated.main` in order. **First**, `simulatePoll(1)` runs with both flags `true`: `checkLiveness` returns `true`, `checkReadiness` returns `true`, and `simulatePoll`'s branching lands on the final `else`, printing that the Pod is healthy and receiving traffic normally.

**Next**, the simulated incident sets `databaseReachable = false`, with `applicationProcessHealthy` left completely untouched.

**Then**, `simulatePoll(2)` runs: `checkLiveness` reads only `applicationProcessHealthy`, which is still `true`, so it prints "OK" and returns `true`. `checkReadiness` reads `applicationProcessHealthy && databaseReachable`, which is `true && false`, evaluating to `false` — it prints "NOT READY" and returns `false`. Back in `simulatePoll`, `alive` is `true` so the `if (!alive)` branch is skipped entirely; `ready` is `false` so the `else if (!ready)` branch runs, printing that the Pod is removed from Service endpoints with the container left running untouched — no restart happens anywhere in this path.

**After that**, the incident resolves: `databaseReachable = true` is set back.

**Finally**, `simulatePoll(3)` runs with both flags `true` again: both checks pass, and `simulatePoll` lands back on the healthy-traffic branch — the Pod automatically rejoins traffic the moment readiness recovers, with no restart having occurred at any point across the entire three-poll sequence, despite a real, full database outage happening in the middle of it.

```
--- poll 1 ---
[probe] liveness: OK
[probe] readiness: OK
[kubernetes] Pod healthy and receiving traffic normally

[incident] database goes down
--- poll 2 ---
[probe] liveness: OK
[probe] readiness: NOT READY (removed from traffic, no restart)
[kubernetes] Pod removed from Service endpoints, container left running untouched

[incident] database comes back up
--- poll 3 ---
[probe] liveness: OK
[probe] readiness: OK
[kubernetes] Pod healthy and receiving traffic normally
```

## 7. Gotchas & takeaways

> Wiring a downstream dependency check (database, external API) into the *liveness* endpoint instead of readiness is one of the most common and damaging Kubernetes misconfigurations — it turns a temporary, external outage into a cluster-wide restart storm of every affected Pod, adding restart churn on top of an outage that a restart can't fix and that would have resolved on its own.
- Spring Boot Actuator's health groups make this separation explicit and configurable — `management.endpoint.health.probes.enabled=true` exposes the dedicated liveness and readiness groups, and you control exactly which health indicators feed into each.
- Liveness should generally check very little — mostly "is the application context up and not deadlocked" — precisely because a liveness failure is a blunt, disruptive instrument (a full restart).
- Readiness is the right place for anything that reflects "can I currently serve requests correctly" — dependency reachability, a warm-up flag, a circuit breaker's open/closed state.
- Watch for restart loops as a diagnostic signal: if a service keeps restarting during a downstream outage rather than just dropping out of traffic and recovering cleanly, that's a strong sign a dependency check has been wired into liveness by mistake.
