---
card: microservices
gi: 455
slug: service-instance-registration-on-deploy
title: "Service instance registration on deploy"
---

## 1. What it is

**Service instance registration** is the moment a running instance becomes visible to whatever mechanism routes traffic to it — a service registry, a load balancer's endpoint list, or a Kubernetes Service's endpoint set. Registration on deploy is specifically about *when* that visibility should happen relative to an instance starting up, and its counterpart, **deregistration**, is about *when* visibility should be withdrawn relative to an instance shutting down. Getting either transition wrong sends traffic to an instance that either isn't ready yet or is already gone.

## 2. Why & when

You need to think carefully about registration timing whenever instances start up and shut down as part of normal deployment — which, under any orchestrator, is constantly:

- **Registering too early routes traffic to an instance that can't serve it yet.** If an instance is added to the routable pool the instant its process starts, but before its database connections are open or its caches are warm, early requests fail against a technically-running-but-not-ready process.
- **Deregistering too late (or not at all) routes traffic to an instance that's already gone**, or about to be — a shutting-down instance still receiving requests either drops them or, worse, if it's already stopped, causes outright connection failures.
- **Deregistration is not instant from the caller's point of view.** Routers, load balancers, and other services often cache the registry's state and only refresh it periodically — deregistering doesn't mean traffic stops arriving immediately, it means traffic *starts to stop* arriving, over some propagation delay.
- **This matters on every single deploy**, not just at initial launch: a [rolling deployment](0450-rolling-deployment.md) constantly creates and retires instances, and each individual creation and retirement needs correct registration timing or the rollout itself becomes a source of dropped requests.

## 3. Core concept

Think of a restaurant host who seats guests only at tables the kitchen has actually confirmed are bussed and ready — not the moment a table is physically empty, and not the moment a server calls out "clearing table 5" before it's actually cleared. Registration is the host adding a table to the "ready to seat" list; deregistration is removing it. Do either at the wrong moment — adding a table before it's really ready, or removing it and immediately seating no one there while other hosts are still working from an outdated list — and guests get sat somewhere that can't actually serve them.

Concretely, the mechanics are:

1. **Registration should be gated on readiness, not on process start.** An instance should only enter the routable pool once it can actually correctly serve a request — exactly the distinction covered in [health checks for orchestrators](0445-health-checks-for-orchestrators.md), where a readiness probe answers "can I serve traffic right now?"
2. **Deregistration should happen before the instance actually stops serving**, not simultaneously with it. Announcing "I'm leaving" and then immediately leaving gives no time for that announcement to reach anyone.
3. **Propagation delay is real and must be planned for.** Whatever routes traffic to an instance — a service registry, a load balancer, DNS, another service's cached endpoint list — takes some nonzero time to notice a deregistration and stop sending new requests. An instance that stops serving *before* that delay has elapsed will drop requests that were sent based on stale information.
4. **A grace period between deregistration and actually stopping** absorbs that propagation delay: deregister first, keep serving for a bit longer, *then* stop — this is the same discipline as graceful shutdown draining in-flight requests, extended to also cover requests still arriving from stale caller state (see [graceful startup & shutdown](0444-graceful-startup-shutdown.md)).

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An instance registers only after passing readiness, and on shutdown deregisters first, then keeps serving through a grace period covering caller propagation delay before actually stopping">
  <text x="320" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">instance lifecycle timeline</text>

  <rect x="20" y="40" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="80" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">starting, not ready</text>

  <rect x="160" y="40" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="220" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ready -&gt; REGISTER</text>

  <rect x="300" y="40" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="370" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">serving traffic</text>

  <rect x="460" y="40" width="150" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="535" y="58" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">DEREGISTER, then</text>
  <text x="535" y="72" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">grace period still serving</text>

  <line x1="140" y1="60" x2="160" y2="60" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="280" y1="60" x2="300" y2="60" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="440" y1="60" x2="460" y2="60" stroke="#f0883e" marker-end="url(#a1)"/>

  <text x="535" y="130" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">only AFTER the grace period elapses does the process actually stop</text>
  <text x="535" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">covering callers whose view of the registry is still stale</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Registration waits for readiness; deregistration happens before the instance stops serving, with a grace period absorbing however long callers take to notice.

## 5. Runnable example

Scenario: an `order-service` instance's full lifecycle from startup to shutdown. We start with the bare register/deregister mechanism, gate registration on a readiness signal so the instance never receives traffic before it can serve it, then handle the hard case: deregistration propagation delay causing dropped requests when an instance stops serving too early, fixed by keeping the instance serving through a grace period after deregistering.

### Level 1 — Basic

```java
// File: RegistrationBasic.java -- models the CORE idea: an instance only
// becomes eligible for traffic AFTER it registers itself with a service
// registry, and it must deregister when shutting down, or traffic keeps
// getting routed to an instance that's no longer there.
import java.util.*;

public class RegistrationBasic {
    static class ServiceRegistry {
        final Set<String> registeredInstances = new LinkedHashSet<>();
        void register(String instanceId) {
            registeredInstances.add(instanceId);
            System.out.println("registry: " + instanceId + " REGISTERED -- now eligible for traffic");
        }
        void deregister(String instanceId) {
            registeredInstances.remove(instanceId);
            System.out.println("registry: " + instanceId + " DEREGISTERED -- no longer eligible for traffic");
        }
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();

        System.out.println("instance starting up...");
        // startup work would happen here (loading config, opening connections)
        registry.register("order-service-i1");
        System.out.println("registered instances: " + registry.registeredInstances);

        System.out.println("instance shutting down...");
        registry.deregister("order-service-i1");
        System.out.println("registered instances: " + registry.registeredInstances);
    }
}
```

How to run: `java RegistrationBasic.java`

`ServiceRegistry` is a minimal stand-in for something like a Kubernetes Service's endpoint list or a Eureka/Consul registry entry: an instance is either in `registeredInstances` (eligible for traffic) or not. Registration and deregistration are the only two operations that change membership — the bare mechanism, with no timing safeguards yet.

### Level 2 — Intermediate

```java
// File: RegistrationGatedByReadiness.java -- the SAME register/deregister
// idea, now GATED by readiness: the instance must NOT register itself the
// moment the process starts -- it must wait until it's actually ready to
// serve (dependencies connected, warm-up complete), or callers will be
// routed to an instance that can't yet handle their request.
import java.util.*;

public class RegistrationGatedByReadiness {
    static class Instance {
        final String id;
        boolean readinessProbePasses = false;
        Instance(String id) { this.id = id; }
    }

    static class ServiceRegistry {
        final Set<String> registeredInstances = new LinkedHashSet<>();
        void register(String instanceId) { registeredInstances.add(instanceId); System.out.println("registry: " + instanceId + " REGISTERED"); }
    }

    static void attemptRegistration(Instance instance, ServiceRegistry registry) {
        if (!instance.readinessProbePasses) {
            System.out.println(instance.id + ": readiness probe NOT yet passing -- registration withheld");
            return;
        }
        registry.register(instance.id);
    }

    public static void main(String[] args) {
        Instance instance = new Instance("order-service-i1");
        ServiceRegistry registry = new ServiceRegistry();

        System.out.println("Process started -- attempting registration immediately (too early):");
        attemptRegistration(instance, registry);
        System.out.println("registered instances: " + registry.registeredInstances);

        System.out.println("Dependencies connect, warm-up completes -- readiness probe now passes:");
        instance.readinessProbePasses = true;
        attemptRegistration(instance, registry);
        System.out.println("registered instances: " + registry.registeredInstances);
    }
}
```

How to run: `java RegistrationGatedByReadiness.java`

`attemptRegistration` checks `readinessProbePasses` before doing anything else — the first call, made right after the process "starts," is correctly withheld, since the instance can't yet serve a request. Only once `readinessProbePasses` flips to `true` (mirroring [health checks for orchestrators](0445-health-checks-for-orchestrators.md)'s readiness probe passing) does registration actually happen — the registry never contains an instance that isn't genuinely ready.

### Level 3 — Advanced

```java
// File: DeregistrationRaceAdvanced.java -- the SAME readiness-gated
// registration, now handling a PRODUCTION-FLAVORED hard case at SHUTDOWN:
// deregistering from the registry does NOT instantly stop traffic --
// callers (load balancers, other services' caches) take a few ticks to
// notice the deregistration and stop sending new requests. An instance
// that stops serving the MOMENT it deregisters drops every request that
// arrives during that propagation window; the correct sequence is
// deregister, then keep serving through a grace period, THEN stop.
import java.util.*;

public class DeregistrationRaceAdvanced {
    static final int PROPAGATION_DELAY_TICKS = 3; // how long callers take to notice deregistration

    static class Instance {
        final String id;
        boolean deregistered = false;
        boolean stillServing = true;
        Instance(String id) { this.id = id; }
    }

    // Simulates a request arriving at tick `t`. Callers may still route here
    // for PROPAGATION_DELAY_TICKS ticks after deregistration, because their
    // view of the registry is slightly stale.
    static boolean requestArrives(Instance instance, int tick, int deregisteredAtTick) {
        boolean callerStillThinksWeAreUp = deregisteredAtTick < 0 || (tick - deregisteredAtTick) < PROPAGATION_DELAY_TICKS;
        return callerStillThinksWeAreUp;
    }

    public static void main(String[] args) {
        System.out.println("--- naive: stop serving THE MOMENT deregistration happens ---");
        runScenario(false);

        System.out.println();
        System.out.println("--- correct: deregister, then keep serving through the propagation grace period ---");
        runScenario(true);
    }

    static void runScenario(boolean useGracePeriod) {
        Instance instance = new Instance("order-service-i1");
        int deregisteredAtTick = -1;
        int dropped = 0, served = 0;

        for (int tick = 0; tick < 6; tick++) {
            if (tick == 2) {
                instance.deregistered = true;
                deregisteredAtTick = tick;
                System.out.println("tick " + tick + ": deregistered from registry");
                if (!useGracePeriod) {
                    instance.stillServing = false;
                    System.out.println("tick " + tick + ": stopped serving immediately (naive)");
                }
            }
            if (useGracePeriod && instance.deregistered && (tick - deregisteredAtTick) >= PROPAGATION_DELAY_TICKS) {
                instance.stillServing = false;
            }

            boolean calledHere = requestArrives(instance, tick, deregisteredAtTick);
            if (calledHere) {
                if (instance.stillServing) {
                    served++;
                    System.out.println("tick " + tick + ": request arrived -- SERVED");
                } else {
                    dropped++;
                    System.out.println("tick " + tick + ": request arrived -- DROPPED (instance already stopped serving)");
                }
            }
        }

        System.out.println("Result: served=" + served + ", dropped=" + dropped);
    }
}
```

How to run: `java DeregistrationRaceAdvanced.java`

`requestArrives` models the propagation delay directly: for `PROPAGATION_DELAY_TICKS` ticks after deregistration, callers still route requests here because their cached view of the registry hasn't caught up yet. The naive scenario sets `stillServing = false` in the very same tick as deregistration, so every request that arrives during the propagation window is dropped. The grace-period scenario keeps `stillServing = true` until the propagation window has fully elapsed, so those same requests are served successfully.

## 6. Walkthrough

Trace the naive scenario in `DeregistrationRaceAdvanced.runScenario(false)` first. **First**, ticks 0 and 1 run with `deregisteredAtTick = -1`, so `requestArrives` returns `true` unconditionally (`deregisteredAtTick < 0` short-circuits the check), and `instance.stillServing` is `true` — both requests are `SERVED`.

**Next**, at tick 2, `instance.deregistered` becomes `true`, `deregisteredAtTick` is set to `2`, and — because `useGracePeriod` is `false` — `instance.stillServing` is immediately set to `false` in the same tick. `requestArrives` is then called for tick 2 itself: `(tick - deregisteredAtTick) = 0`, which is `< PROPAGATION_DELAY_TICKS (3)`, so it still returns `true` — a caller sends a request based on stale information. But `instance.stillServing` is already `false`, so this request is `DROPPED`.

**Then**, ticks 3 and 4 repeat the same pattern: `requestArrives` keeps returning `true` because `(tick - 2)` is `1` and `2`, both still under `3`, but `stillServing` is permanently `false` — two more requests are `DROPPED`. By tick 5, `(5-2)=3` is no longer `< 3`, so `requestArrives` returns `false` and no request even attempts to reach the instance.

**Finally**, in the grace-period run, the same propagation pattern occurs, but `instance.stillServing` only flips to `false` once `(tick - deregisteredAtTick) >= PROPAGATION_DELAY_TICKS` — meaning it stays `true` through ticks 2, 3, and 4, exactly the window during which `requestArrives` still returns `true`. Every request that a stale caller sends during that window is therefore `SERVED`, and the two scenarios' final tallies — `2 served / 3 dropped` versus `5 served / 0 dropped` — make the cost of skipping the grace period concrete.

```
--- naive: stop serving THE MOMENT deregistration happens ---
tick 0: request arrived -- SERVED
tick 1: request arrived -- SERVED
tick 2: deregistered from registry
tick 2: stopped serving immediately (naive)
tick 2: request arrived -- DROPPED (instance already stopped serving)
tick 3: request arrived -- DROPPED (instance already stopped serving)
tick 4: request arrived -- DROPPED (instance already stopped serving)
Result: served=2, dropped=3

--- correct: deregister, then keep serving through the propagation grace period ---
tick 0: request arrived -- SERVED
tick 1: request arrived -- SERVED
tick 2: deregistered from registry
tick 2: request arrived -- SERVED
tick 3: request arrived -- SERVED
tick 4: request arrived -- SERVED
Result: served=5, dropped=0
```

## 7. Gotchas & takeaways

> Deregistering from the registry and terminating the process are two different events, and treating them as one — deregister, then immediately `SIGKILL` — is one of the most common causes of a brief spike in dropped requests during otherwise-routine deploys. The fix costs nothing but a short, deliberate delay between the two.

- Gate registration on actual readiness, never on process start — an instance that's technically running but can't yet serve correctly should be invisible to routing until it can, tying directly into [health checks for orchestrators](0445-health-checks-for-orchestrators.md).
- Deregister first, then keep serving through a grace period sized to your slowest caller's propagation delay, and only then stop accepting new work — this is the shutdown-side analog of the startup discipline in [graceful startup & shutdown](0444-graceful-startup-shutdown.md).
- Every instance created or retired during a [rolling deployment](0450-rolling-deployment.md) goes through this exact registration and deregistration sequence — get it right once, here, and every rollout benefits automatically.
- Orchestrators like Kubernetes handle much of this automatically via readiness probes and a configurable `terminationGracePeriodSeconds`, but the underlying timing discipline is the same regardless of who enforces it — understanding it helps you configure those settings correctly rather than treating them as opaque defaults.
- A [sidecar pattern](0456-sidecar-pattern.md) container is sometimes used specifically to handle registration and deregistration outside the main application process, decoupling that lifecycle concern from the business logic entirely.
