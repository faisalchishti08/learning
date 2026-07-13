---
card: microservices
gi: 445
slug: health-checks-for-orchestrators
title: "Health checks for orchestrators"
---

## 1. What it is

**Health checks for orchestrators** are HTTP (or TCP/exec) endpoints an orchestrator like Kubernetes probes periodically to decide two separate questions about a running instance: is it *alive* (should the orchestrator restart it because it's stuck or crashed), and is it *ready* (should the load balancer send it traffic right now)? These correspond to Kubernetes's **liveness probe** and **readiness probe** — two conceptually different checks that are easy to conflate but answer different questions and drive different orchestrator actions. Spring Boot Actuator exposes both out of the box via its health groups: `/actuator/health/liveness` and `/actuator/health/readiness`.

## 2. Why & when

Getting this distinction right matters because using the wrong probe for the wrong purpose causes exactly the failure modes health checks exist to prevent:

- **Liveness answers "should this instance be restarted?"** If a service's internals get into an unrecoverable state — a deadlock, a corrupted internal cache, a thread pool exhausted beyond recovery — no amount of retrying from outside will fix it; only killing and restarting the process will. A failing liveness probe tells the orchestrator to do exactly that.
- **Readiness answers "should traffic be sent here right now?"** A service can be perfectly alive (not deadlocked, not crashed) while genuinely unable to serve requests correctly at this moment — its database connection pool temporarily exhausted, a downstream dependency it needs is unreachable, or it's still warming up (see [graceful startup & shutdown](0444-graceful-startup-shutdown.md)). A failing readiness probe pulls the instance out of load-balancer rotation *without* restarting it — exactly the right response, since restarting wouldn't fix a downstream outage and would only add unnecessary churn.
- **Conflating the two causes real outages.** If a temporary downstream dependency failure is (incorrectly) wired only into the liveness probe, the orchestrator restarts every instance in the fleet simultaneously the moment that dependency has a blip — turning a transient, recoverable issue into a full-fleet restart storm, often making the original problem worse.
- **Startup probes handle a third, related case**: a service whose normal startup is slow enough that it would otherwise fail its liveness probe before it's even finished starting — a startup probe gives it a longer initial grace period before liveness checks begin being enforced.

You configure both liveness and readiness probes on every service deployed under an orchestrator — an instance with no health checks configured is, from the orchestrator's perspective, always assumed healthy and ready, which means it keeps receiving traffic and never gets automatically restarted even while it's silently broken.

## 3. Core concept

Think of the difference between a person's pulse and their readiness to work a shift. A pulse check (liveness) answers "is this person alive at all?" — if there's no pulse, nothing short of drastic intervention (a restart) helps. Whether they're ready to work a shift (readiness) is a completely different, more situational question — someone can have a perfectly strong pulse while being unable to work right now because they're still getting dressed, waiting on a ride that hasn't arrived, or momentarily stepped away — none of which calls for drastic intervention, just "don't schedule this person for a task right now," which is exactly what pulling an instance out of load-balancer rotation does.

Concretely, the mechanics are:

1. **Liveness probe** — checked periodically; on repeated failure, the orchestrator kills and restarts the container. Should only check things a *restart* would actually fix: the process's own internal health, not external dependency availability.
2. **Readiness probe** — checked periodically; on failure, the orchestrator removes the instance from service endpoints (stops routing traffic to it) without restarting it, and adds it back once the probe passes again. Should check things that determine "can I correctly serve a request right now": database connectivity, critical downstream dependency availability, whether startup warm-up has completed.
3. **Startup probe** (where supported) — checked only during the initial startup window; while it's failing, liveness checks are suppressed, giving a slow-starting service room to finish initializing without being killed mid-startup for not yet being "alive" by the liveness definition.
4. **Probe failure thresholds and intervals matter.** A probe that fails once shouldn't necessarily trigger action immediately — orchestrators typically require a configurable number of consecutive failures before acting, to avoid overreacting to a single transient blip.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A liveness probe failure causes the orchestrator to restart the container; a readiness probe failure causes the orchestrator to remove the instance from load balancer routing without restarting it, and re-add it once the probe passes again" >
  <rect x="30" y="30" width="230" height="180" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="145" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Liveness probe fails</text>
  <text x="145" y="55" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"is the process alive/unstuck?"</text>
  <rect x="55" y="75" width="180" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="145" y="99" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">deadlocked / stuck instance</text>
  <line x1="145" y1="115" x2="145" y2="140" stroke="#f85149"/>
  <rect x="55" y="140" width="180" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="145" y="164" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">orchestrator KILLS &amp; RESTARTS</text>

  <rect x="380" y="30" width="230" height="180" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="495" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Readiness probe fails</text>
  <text x="495" y="55" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"can it serve traffic right now?"</text>
  <rect x="405" y="75" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="495" y="93" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DB pool exhausted / warming up</text>
  <line x1="495" y1="115" x2="495" y2="140" stroke="#f0883e"/>
  <rect x="405" y="140" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="495" y="158" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">REMOVED from routing only</text>
  <text x="495" y="172" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">re-added once healthy again</text>

  <text x="320" y="235" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">wiring a downstream dependency into liveness turns a transient blip into a fleet-wide restart storm</text>
</svg>

Liveness failures trigger a restart because the process itself is broken; readiness failures only pause traffic because the process is fine but temporarily can't serve requests.

## 5. Runnable example

Scenario: an `order-service` instance exposing both probe types. We model liveness and readiness as independent booleans first, then wire realistic conditions (a stuck internal loop for liveness, a downstream dependency check for readiness) into each, then handle a production-flavored case: correctly distinguishing a transient downstream outage (readiness-only impact) from a genuinely stuck instance (liveness impact), so a fleet doesn't restart-storm over a recoverable blip.

### Level 1 — Basic

```java
// File: ProbesBasic.java -- models the CORE distinction: liveness and
// readiness are SEPARATE signals, checked and acted on differently.
public class ProbesBasic {
    static class OrderServiceInstance {
        boolean alive = true;   // liveness: is the process itself healthy?
        boolean ready = false;  // readiness: can it serve a request right now?

        String livenessProbe() { return alive ? "200 OK" : "500 FAIL -- orchestrator will RESTART this instance"; }
        String readinessProbe() { return ready ? "200 OK" : "503 FAIL -- orchestrator will STOP ROUTING traffic here, no restart"; }
    }

    public static void main(String[] args) {
        OrderServiceInstance instance = new OrderServiceInstance();

        System.out.println("During startup (alive, not yet ready):");
        System.out.println("  liveness:  " + instance.livenessProbe());
        System.out.println("  readiness: " + instance.readinessProbe());

        instance.ready = true;
        System.out.println("After startup completes:");
        System.out.println("  liveness:  " + instance.livenessProbe());
        System.out.println("  readiness: " + instance.readinessProbe());
    }
}
```

How to run: `java ProbesBasic.java`

`alive` and `ready` are tracked as two entirely independent flags, and `livenessProbe`/`readinessProbe` react to only their own flag. During startup, the instance is genuinely `alive` (the process is running fine) but not yet `ready` — liveness correctly reports healthy while readiness correctly reports not-yet-serving, exactly matching the real state of a service that's still warming up.

### Level 2 — Intermediate

```java
// File: ProbesWithRealConditionsIntermediate.java -- the SAME two probes,
// now driven by REALISTIC conditions: liveness checks an internal
// stuck-thread signal; readiness checks a downstream dependency.
public class ProbesWithRealConditionsIntermediate {
    static class OrderServiceInstance {
        boolean internalWatchdogHealthy = true; // flips false if internal processing loop is stuck
        boolean databaseReachable = true;
        boolean startupComplete = true;

        String livenessProbe() {
            // Liveness should ONLY reflect things a restart would actually fix.
            return internalWatchdogHealthy ? "200 OK" : "500 FAIL -- process is stuck, restart needed";
        }

        String readinessProbe() {
            // Readiness reflects whether THIS request, right now, could succeed.
            if (!startupComplete) return "503 FAIL -- still starting up";
            if (!databaseReachable) return "503 FAIL -- database unreachable, but process itself is fine";
            return "200 OK";
        }
    }

    public static void main(String[] args) {
        OrderServiceInstance instance = new OrderServiceInstance();
        System.out.println("Steady state:  liveness=" + instance.livenessProbe() + " readiness=" + instance.readinessProbe());

        // A downstream database has a temporary outage. The PROCESS is fine.
        instance.databaseReachable = false;
        System.out.println("DB outage:     liveness=" + instance.livenessProbe() + " readiness=" + instance.readinessProbe());
        System.out.println("  -- correct outcome: instance pulled from routing, NOT restarted (a restart wouldn't fix the DB anyway).");

        instance.databaseReachable = true;
        // Now the internal processing loop genuinely deadlocks.
        instance.internalWatchdogHealthy = false;
        System.out.println("Deadlock:      liveness=" + instance.livenessProbe() + " readiness=" + instance.readinessProbe());
        System.out.println("  -- correct outcome: orchestrator restarts this instance; only a fresh process recovers from a deadlock.");
    }
}
```

How to run: `java ProbesWithRealConditionsIntermediate.java`

`livenessProbe` deliberately checks only `internalWatchdogHealthy` — a signal that only a restart could fix. `readinessProbe` checks `startupComplete` and `databaseReachable` — conditions where pulling traffic, not restarting, is the correct response. A database outage flips only readiness to failing, leaving liveness healthy — the instance stops receiving traffic but isn't killed. A genuine internal deadlock flips only liveness to failing — correctly triggering a restart, since the database being reachable again wouldn't matter if the process itself can no longer make progress.

### Level 3 — Advanced

```java
// File: FleetRestartStormAdvanced.java -- the SAME probe model, now handling
// a PRODUCTION-FLAVORED hard case: proving that wiring a downstream
// dependency into LIVENESS (a common misconfiguration) turns one transient
// outage into a fleet-wide restart storm, versus the correct wiring (into
// readiness only) which absorbs the same outage with zero restarts.
import java.util.*;

public class FleetRestartStormAdvanced {
    static class OrderServiceInstance {
        final String id;
        boolean internalWatchdogHealthy = true;
        boolean databaseReachable = true;
        boolean misconfiguredLivenessChecksDatabase; // simulates the common misconfiguration

        OrderServiceInstance(String id, boolean misconfigured) { this.id = id; this.misconfiguredLivenessChecksDatabase = misconfigured; }

        boolean livenessPasses() {
            if (misconfiguredLivenessChecksDatabase) {
                return internalWatchdogHealthy && databaseReachable; // WRONG: couples liveness to an external dependency
            }
            return internalWatchdogHealthy; // CORRECT: liveness reflects only the process's own health
        }

        boolean readinessPasses() {
            return internalWatchdogHealthy && databaseReachable;
        }
    }

    public static void main(String[] args) {
        List<OrderServiceInstance> misconfiguredFleet = new ArrayList<>();
        List<OrderServiceInstance> correctFleet = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            misconfiguredFleet.add(new OrderServiceInstance("m-" + i, true));
            correctFleet.add(new OrderServiceInstance("c-" + i, false));
        }

        System.out.println("--- database has a transient outage across the WHOLE fleet ---");
        for (OrderServiceInstance inst : misconfiguredFleet) inst.databaseReachable = false;
        for (OrderServiceInstance inst : correctFleet) inst.databaseReachable = false;

        long misconfiguredRestarts = misconfiguredFleet.stream().filter(inst -> !inst.livenessPasses()).count();
        long correctRestarts = correctFleet.stream().filter(inst -> !inst.livenessPasses()).count();
        long misconfiguredOutOfRotation = misconfiguredFleet.stream().filter(inst -> !inst.readinessPasses()).count();
        long correctOutOfRotation = correctFleet.stream().filter(inst -> !inst.readinessPasses()).count();

        System.out.println("Misconfigured fleet (liveness checks DB): " + misconfiguredRestarts + "/5 instances RESTARTED, "
                + misconfiguredOutOfRotation + "/5 pulled from routing.");
        System.out.println("Correct fleet (liveness checks process only): " + correctRestarts + "/5 instances RESTARTED, "
                + correctOutOfRotation + "/5 pulled from routing.");
        System.out.println();
        System.out.println("Both fleets correctly stop serving traffic during the outage. "
                + "Only the misconfigured fleet ALSO restarts every instance simultaneously -- "
                + "a self-inflicted restart storm on top of an outage that a restart can't even fix.");
    }
}
```

How to run: `java FleetRestartStormAdvanced.java`

The hard case is the exact misconfiguration warned about in section 2: `misconfiguredLivenessChecksDatabase` models wiring an external dependency check into the liveness probe. When the shared database has a transient outage, both fleets correctly drop to zero readiness (`5/5` pulled from routing) — the right response, since neither fleet can serve requests correctly right now. But the misconfigured fleet's liveness probe *also* fails for all five instances, triggering `5/5` simultaneous restarts — pure wasted churn, since restarting a process does nothing to fix an unreachable database, and the correctly configured fleet demonstrates the same outage handled with zero unnecessary restarts.

## 6. Walkthrough

Trace `FleetRestartStormAdvanced.main` in order. **First**, `misconfiguredFleet` and `correctFleet` are each populated with five instances; the misconfigured ones are constructed with `misconfigured = true`, meaning their `livenessPasses()` will incorrectly also check `databaseReachable`.

**Next**, the simulated outage sets `databaseReachable = false` on every instance in both fleets — modeling a shared database dependency having a transient, fleet-wide blip that affects all ten instances identically.

**Then**, `misconfiguredRestarts` filters `misconfiguredFleet` for instances where `livenessPasses()` returns `false`. For each misconfigured instance, `livenessPasses()` evaluates `internalWatchdogHealthy && databaseReachable`, which is `true && false = false` — so all five fail liveness and would be restarted. `correctRestarts` performs the same filter on `correctFleet`, but `livenessPasses()` there evaluates only `internalWatchdogHealthy`, which remains `true` for all five instances — zero fail liveness, zero would be restarted.

**Finally**, `misconfiguredOutOfRotation` and `correctOutOfRotation` both filter on `readinessPasses()`, which checks `internalWatchdogHealthy && databaseReachable` in *both* fleets identically — correctly, all ten instances across both fleets fail readiness and get pulled from routing, since neither fleet can actually serve requests while the database is down. The final printed comparison makes the actual difference concrete: identical, correct readiness behavior in both fleets, but only the misconfigured fleet adds five unnecessary, simultaneous restarts on top of an outage that no restart could have fixed.

```
--- database has a transient outage across the WHOLE fleet ---
Misconfigured fleet (liveness checks DB): 5/5 instances RESTARTED, 5/5 pulled from routing.
Correct fleet (liveness checks process only): 0/5 instances RESTARTED, 5/5 pulled from routing.

Both fleets correctly stop serving traffic during the outage. Only the misconfigured fleet ALSO restarts every instance simultaneously -- a self-inflicted restart storm on top of an outage that a restart can't even fix.
```

## 7. Gotchas & takeaways

> A liveness probe that transitively depends on a shared external resource (a database, a downstream service) is one of the most common and most damaging health-check misconfigurations in production Kubernetes deployments — it converts any outage of that shared resource into a synchronized restart of every instance depending on it, adding restart churn and cold-start latency exactly when the system is already degraded and least able to absorb it.

- Liveness should check only what a restart could plausibly fix — internal deadlocks, unrecoverable internal state — never the availability of an external dependency.
- Readiness should check everything relevant to "can I correctly serve a request right now," including external dependency availability and startup completion — failing readiness pulls traffic without restarting, which is exactly the right response to a transient or external problem.
- Startup probes (where the orchestrator supports them) give a slow-starting service a longer initial grace period before liveness checks begin being enforced, avoiding a false restart during legitimately slow initialization — see [graceful startup & shutdown](0444-graceful-startup-shutdown.md) for the startup-side discipline these probes gate.
- Spring Boot Actuator's `/actuator/health/liveness` and `/actuator/health/readiness` health groups implement this separation directly and are the standard way to wire Kubernetes probes for a Spring Boot service — prefer them over hand-rolled probe endpoints.
- Tune probe failure thresholds and check intervals deliberately: too sensitive (few consecutive failures required) overreacts to transient blips; too lax (many failures required, or long intervals) delays detecting a genuinely broken instance.
