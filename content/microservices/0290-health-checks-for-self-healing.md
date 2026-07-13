---
card: microservices
gi: 290
slug: health-checks-for-self-healing
title: "Health checks for self-healing"
---

## 1. What it is

A health check is an endpoint or probe that reports whether a service instance is currently able to do its job — commonly split into *liveness* ("is this process alive and not deadlocked?") and *readiness* ("is this instance currently able to serve traffic correctly?"). Self-healing is what an orchestrator (Kubernetes, a load balancer, a service mesh) does in response: automatically restarting an instance that fails its liveness check, or automatically removing an instance that fails its readiness check from receiving traffic, without any human intervening.

## 2. Why & when

A service instance can be in a broken state in ways that are invisible from the outside unless something actively asks: a deadlocked thread pool, a lost database connection that hasn't yet triggered a visible error, a memory leak degrading performance, a dependency the instance needs but currently cannot reach. Without health checks, an orchestrator has no way to know an instance is unhealthy — it keeps routing traffic to it (readiness) or assumes it's fine and never restarts it (liveness), and the only signal anyone gets is a stream of failed user requests.

Liveness and readiness answer different questions and should trigger different remedies. A failed liveness check means "this process is fundamentally broken and needs to be replaced" — the orchestrator restarts it. A failed readiness check means "this process is fine but temporarily cannot serve traffic correctly" (e.g., still warming up, or its database connection pool briefly exhausted) — the orchestrator stops sending it traffic but does *not* restart it, since restarting wouldn't help and would just add more churn. Use both together: readiness protects users from being routed to an instance that can't currently serve them; liveness ensures a genuinely stuck instance gets automatically replaced.

## 3. Core concept

A Spring Boot application typically exposes both via the Actuator's `/actuator/health/liveness` and `/actuator/health/readiness` endpoints, each backed by custom health indicators reflecting the actual state that matters.

```java
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

@Component("database")
class DatabaseHealthIndicator implements HealthIndicator {
    private final DataSource dataSource;
    DatabaseHealthIndicator(DataSource dataSource) { this.dataSource = dataSource; }

    @Override
    public Health health() {
        try (Connection conn = dataSource.getConnection()) {
            if (conn.isValid(1)) return Health.up().build();     // READINESS-relevant: can currently serve
            return Health.down().withDetail("reason", "connection invalid").build();
        } catch (SQLException e) {
            return Health.down(e).build(); // instance is UP (liveness fine) but NOT READY
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A liveness probe failing causes the orchestrator to restart the instance because it is fundamentally broken; a readiness probe failing causes the orchestrator to remove the instance from the load balancer's traffic rotation without restarting it, since the instance may recover on its own">
  <rect x="30" y="20" width="200" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">liveness probe FAILS</text>
  <line x1="130" y1="60" x2="130" y2="90" stroke="#8b949e" marker-end="url(#arr290)"/>
  <rect x="30" y="95" width="200" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="119" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">orchestrator RESTARTS instance</text>

  <rect x="400" y="20" width="200" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="500" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">readiness probe FAILS</text>
  <line x1="500" y1="60" x2="500" y2="90" stroke="#8b949e" marker-end="url(#arr290)"/>
  <rect x="400" y="95" width="200" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="500" y="115" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">removed from traffic rotation</text>
  <text x="500" y="128" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">(NOT restarted -- may self-recover)</text>

  <text x="315" y="170" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">two different questions, two different remedies</text>

  <defs><marker id="arr290" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Liveness failures get the instance restarted; readiness failures just pull it from traffic — different problems, different fixes.

## 5. Runnable example

Scenario: a service with no health checks that keeps receiving traffic even while its database connection is down, extended to add a readiness check that lets an orchestrator stop routing to it, and finally adding a separate liveness check with different logic, simulating an orchestrator's polling loop reacting differently to each kind of failure.

### Level 1 — Basic

```java
// File: NoHealthChecksSilentlyFails.java -- a service instance loses its
// database connection but has NO health check exposing this; a simulated
// load balancer keeps routing traffic to it regardless, and every
// request fails.
public class NoHealthChecksSilentlyFails {
    static boolean databaseConnected = true;

    static String handleRequest() {
        if (!databaseConnected) throw new RuntimeException("500: database unavailable");
        return "200 OK";
    }

    public static void main(String[] args) {
        System.out.println("Request 1: " + handleRequest());
        databaseConnected = false; // simulate losing the DB connection
        for (int i = 2; i <= 4; i++) {
            try {
                System.out.println("Request " + i + ": " + handleRequest());
            } catch (Exception e) {
                System.out.println("Request " + i + ": FAILED -- " + e.getMessage()
                        + " (load balancer had NO way to know, kept routing here anyway)");
            }
        }
    }
}
```

How to run: `java NoHealthChecksSilentlyFails.java`

The first request succeeds. Once `databaseConnected` flips to false (simulating a lost DB connection), every subsequent request fails with a 500 — but nothing in this program tells any external load balancer or orchestrator that this instance has a problem. With no health check to consult, a real load balancer would keep sending every user's request to this broken instance indefinitely, producing a stream of failed requests until a human notices.

### Level 2 — Intermediate

```java
// File: ReadinessRemovesFromRotation.java -- adds a readiness check the
// "load balancer" polls; once it fails, the simulated load balancer
// stops routing traffic to this instance, protecting users from hitting
// the broken instance at all.
public class ReadinessRemovesFromRotation {
    static boolean databaseConnected = true;

    static boolean isReady() { return databaseConnected; } // READINESS: can this instance serve correctly RIGHT NOW?

    static String handleRequest() {
        if (!databaseConnected) throw new RuntimeException("500: database unavailable");
        return "200 OK";
    }

    static class SimulatedLoadBalancer {
        boolean instanceInRotation = true;
        void pollReadiness() {
            instanceInRotation = isReady();
            if (!instanceInRotation) System.out.println("  [load balancer] readiness check FAILED -- removing instance from rotation");
        }
        String routeRequest(int requestNum) {
            if (!instanceInRotation) return "Request " + requestNum + ": NOT ROUTED HERE (instance out of rotation)";
            try { return "Request " + requestNum + ": " + handleRequest(); }
            catch (Exception e) { return "Request " + requestNum + ": FAILED -- " + e.getMessage(); }
        }
    }

    public static void main(String[] args) {
        SimulatedLoadBalancer lb = new SimulatedLoadBalancer();
        System.out.println(lb.routeRequest(1));
        databaseConnected = false;
        lb.pollReadiness(); // orchestrator/load balancer periodically checks readiness
        System.out.println(lb.routeRequest(2));
        System.out.println(lb.routeRequest(3));
    }
}
```

How to run: `java ReadinessRemovesFromRotation.java`

Request 1 succeeds normally. Once the database connection drops, the simulated load balancer's `pollReadiness()` call (standing in for Kubernetes' periodic readiness probe) detects `isReady()` returning false and removes the instance from `instanceInRotation`. Requests 2 and 3 are never even routed to this instance's `handleRequest()` — they're intercepted at the load balancer layer and reported as "NOT ROUTED HERE," meaning real user traffic would instead go to a different, healthy instance rather than hitting this broken one and failing.

### Level 3 — Advanced

```java
// File: LivenessVsReadinessDifferentiated.java -- separate liveness and
// readiness checks with DIFFERENT triggers and DIFFERENT orchestrator
// responses: a lost DB connection only fails readiness (removed from
// traffic, might self-recover), while a detected deadlock fails
// liveness (orchestrator RESTARTS the whole instance).
public class LivenessVsReadinessDifferentiated {
    static boolean databaseConnected = true;
    static boolean deadlocked = false;

    static boolean isReady() { return databaseConnected && !deadlocked; }
    static boolean isAlive() { return !deadlocked; } // deadlock = fundamentally broken process

    static class SimulatedOrchestrator {
        boolean inRotation = true;
        boolean restarted = false;

        void poll() {
            if (!isAlive()) {
                System.out.println("  [orchestrator] LIVENESS FAILED -- process is fundamentally broken, RESTARTING instance");
                restarted = true;
                deadlocked = false;      // restart clears the deadlock -- fresh process
                databaseConnected = true; // fresh process reconnects to the DB on startup
                inRotation = true;
                return;
            }
            inRotation = isReady();
            if (!inRotation) System.out.println("  [orchestrator] READINESS FAILED -- removing from traffic, NOT restarting (may self-recover)");
            else if (restarted) { System.out.println("  [orchestrator] instance back to normal after restart"); restarted = false; }
        }
    }

    public static void main(String[] args) {
        SimulatedOrchestrator orch = new SimulatedOrchestrator();

        System.out.println("-- scenario 1: DB connection lost (readiness issue only) --");
        databaseConnected = false;
        orch.poll();
        System.out.println("inRotation=" + orch.inRotation + " (removed from traffic, but process itself is fine, no restart)");

        databaseConnected = true; // DB comes back on its own
        orch.poll();
        System.out.println("inRotation=" + orch.inRotation + " (self-recovered, back in rotation, still never restarted)");

        System.out.println("-- scenario 2: thread pool deadlock detected (liveness issue) --");
        deadlocked = true;
        orch.poll();
        System.out.println("restarted=" + orch.restarted + " inRotation=" + orch.inRotation + " (fresh process, back in rotation immediately)");
    }
}
```

How to run: `java LivenessVsReadinessDifferentiated.java`

Scenario 1 simulates a lost database connection: `isReady()` returns false but `isAlive()` still returns true (the process itself isn't broken, just temporarily unable to serve). The orchestrator's `poll()` sees a failed readiness check, removes the instance from rotation, and does *not* restart it. When the database reconnects on its own, the next poll finds `isReady()` true again and puts the instance back in rotation — no restart was ever needed, because the process itself was never broken. Scenario 2 simulates a detected deadlock: `isAlive()` now returns false, which the orchestrator treats as a fundamentally broken process — it restarts the instance (clearing the deadlock and reconnecting the database as a side effect of a fresh start) rather than merely pulling it from rotation, since a deadlocked process would never recover on its own no matter how long it stayed out of traffic.

## 6. Walkthrough

Trace `LivenessVsReadinessDifferentiated.main` through scenario 2. **First**, scenario 1 has already run and left the system in a healthy state (`databaseConnected=true`, `deadlocked=false`, `orch.inRotation=true`).

**`deadlocked` is set to `true`**, simulating a health indicator detecting a genuinely stuck thread pool inside the instance.

**`orch.poll()` is called.** Inside, the first check is `if (!isAlive())`. `isAlive()` returns `!deadlocked`, which is now `!true = false`, so `!isAlive()` evaluates to `true` — the liveness check has failed, and this branch executes *before* the readiness check is even consulted, reflecting the real precedence: a liveness failure is the more severe condition and takes priority.

**Inside the liveness-failure branch**, the orchestrator prints its restart message, sets `restarted = true`, and then — modeling exactly what a real process restart accomplishes — resets `deadlocked = false` and `databaseConnected = true` (a fresh process starts with a clean thread pool and re-establishes its database connection from scratch) and sets `inRotation = true` (the newly restarted, healthy instance rejoins traffic). The method then `return`s immediately, skipping the readiness-check logic entirely for this poll cycle, since the restart already resolved everything.

**Back in `main`**, the printed state shows `restarted=true inRotation=true` — the instance was actively restarted by the orchestrator and immediately came back healthy, in contrast to scenario 1's DB-only failure, where `restarted` never became `true` at all and the instance simply waited out of rotation until it recovered on its own.

```
poll() called
   |
   v
isAlive()? --false--> RESTART instance (clears deadlock, reconnects DB, back in rotation) -> return, skip readiness check
   |true
   v
isReady()? --false--> remove from rotation, do NOT restart
   |true
   v
stays in rotation, serving traffic normally
```

## 7. Gotchas & takeaways

> Making a liveness check depend on an external dependency (like the database) is a common, serious mistake: if the database goes down, every instance's liveness check would fail simultaneously, and the orchestrator would restart the entire fleet at once — which does nothing to fix the actual problem (the database is still down) and adds a thundering herd of restart churn on top of an already-degraded system. Liveness should only reflect the process's own internal health; readiness should reflect its ability to serve given current external dependencies.

- Liveness answers "should this process be replaced?" and should be restart-fixable — deadlocks, unrecoverable internal corruption, truly hung state.
- Readiness answers "can this instance serve traffic right now?" and should reflect external dependency health — database connectivity, downstream service availability, whether startup/warm-up has completed.
- Never make a liveness probe depend on a shared external resource, or a single outage of that resource can trigger a synchronized, useless restart of an entire fleet.
- Spring Boot Actuator exposes both out of the box (`/actuator/health/liveness` and `/actuator/health/readiness`) and lets custom `HealthIndicator` beans contribute to either group — Kubernetes deployments should point their `livenessProbe` and `readinessProbe` at the corresponding distinct endpoints, never the same one for both.
