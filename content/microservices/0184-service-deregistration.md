---
card: microservices
gi: 184
slug: service-deregistration
title: "Service deregistration"
---

## 1. What it is

Service deregistration is removing an instance from the [service registry](0182-service-registry-concept.md) once it stops being available — either gracefully, when the instance shuts down cleanly and explicitly tells the registry to remove it, or through timeout, when the registry notices the instance has stopped sending [heartbeats](0189-heartbeats-lease-renewal.md) and removes it automatically after a configured grace period.

## 2. Why & when

An instance that has shut down but remains listed in the registry is worse than one that was never registered at all — callers will keep being routed to it, receiving connection failures or timeouts for every request sent its way, until something removes the stale entry. Graceful deregistration handles the clean-shutdown case (a deliberate scale-down, a planned restart) by having the instance explicitly notify the registry as its very last act before terminating. Timeout-based deregistration handles the unclean case (a crash, a network partition, an unresponsive process) where graceful shutdown code never gets the chance to run at all, relying instead on the registry noticing the absence of expected heartbeats.

Implement graceful deregistration for every planned shutdown path, since it removes the stale entry immediately rather than waiting out a timeout window unnecessarily. Rely on timeout-based deregistration as the necessary safety net for unplanned failures, since graceful deregistration simply cannot run when the process crashes hard or loses network connectivity before it gets the chance.

## 3. Core concept

Graceful deregistration is an explicit registry call made during an instance's shutdown sequence, removing its entry immediately; timeout-based deregistration is the registry's own internal logic, comparing each registered instance's last-known heartbeat timestamp against a configured timeout and purging any instance that has gone silent for too long.

```java
// GRACEFUL: an explicit call, as the LAST thing the instance does before terminating
@PreDestroy
void onShutdown() {
    registryClient.deregister("order-service", myInstanceId); // immediate, deliberate removal
}

// TIMEOUT-BASED: the REGISTRY itself notices missing heartbeats and cleans up
void periodicCleanupSweep() {
    for (ServiceInstance instance : allRegisteredInstances) {
        if (now() - instance.lastHeartbeat() > timeoutDuration) {
            deregister(instance); // the instance never asked for this -- the registry decided, based on silence
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A gracefully shutting down instance explicitly calls deregister and is removed immediately. A crashed instance sends no such call; the registry only removes it after its heartbeats have been missing for longer than the configured timeout window" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Graceful shutdown</text>
  <rect x="30" y="40" width="240" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">explicit deregister() call -- IMMEDIATE</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Crash / timeout</text>
  <rect x="360" y="40" width="240" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="480" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">silence... registry waits out the timeout</text>

  <text x="150" y="110" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">clean removal, no stale window</text>
  <text x="480" y="110" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">callers can hit the dead instance until timeout expires</text>

  <defs>
    <marker id="arr65" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Graceful deregistration is instant and clean; timeout-based deregistration is the necessary but slower fallback for genuine failures.

## 5. Runnable example

Scenario: a scale-down operation that starts with no deregistration at all (showing traffic sent to a dead instance indefinitely), adds graceful deregistration on clean shutdown, and finally adds timeout-based deregistration as a safety net for a crash scenario where the graceful path never runs, demonstrating both mechanisms working together to keep the registry accurate under both planned and unplanned instance loss.

### Level 1 — Basic

```java
// File: NoDeregistration.java -- an instance shuts down but is NEVER removed
// from the registry; callers keep routing to a DEAD address, forever.
import java.util.*;

public class NoDeregistration {
    record ServiceInstance(String id, String host) {}
    static List<ServiceInstance> registeredInstances = new ArrayList<>(List.of(new ServiceInstance("order-a", "10.0.1.5")));

    public static void main(String[] args) {
        System.out.println("Registered instances: " + registeredInstances);

        System.out.println("order-a is now SHUT DOWN...");
        // NOTHING removes it from registeredInstances -- no deregistration logic exists AT ALL

        System.out.println("Registered instances, AFTER shutdown: " + registeredInstances);
        System.out.println("Callers will keep getting routed to order-a's DEAD address INDEFINITELY.");
    }
}
```

**How to run:** `javac NoDeregistration.java && java NoDeregistration` (JDK 17+).

### Level 2 — Intermediate

```java
// File: GracefulDeregistration.java -- the instance EXPLICITLY calls deregister()
// as the LAST step of a CLEAN shutdown -- immediate, correct removal.
import java.util.*;

public class GracefulDeregistration {
    record ServiceInstance(String id, String host) {}

    static class ServiceRegistry {
        List<ServiceInstance> instances = new ArrayList<>();
        void register(ServiceInstance instance) { instances.add(instance); System.out.println("[registry] registered: " + instance.id()); }
        void deregister(String instanceId) {
            instances.removeIf(i -> i.id().equals(instanceId));
            System.out.println("[registry] deregistered: " + instanceId);
        }
    }

    static void gracefulShutdown(ServiceRegistry registry, String instanceId) {
        System.out.println("[" + instanceId + "] beginning graceful shutdown...");
        System.out.println("[" + instanceId + "] draining in-flight requests...");
        registry.deregister(instanceId); // the LAST action before terminating
        System.out.println("[" + instanceId + "] terminated cleanly.");
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        registry.register(new ServiceInstance("order-a", "10.0.1.5"));

        gracefulShutdown(registry, "order-a");

        System.out.println("Registered instances after graceful shutdown: " + registry.instances);
        System.out.println("order-a was removed IMMEDIATELY -- no stale window at all.");
    }
}
```

**How to run:** `javac GracefulDeregistration.java && java GracefulDeregistration` (JDK 17+).

Expected output:
```
[registry] registered: order-a
[order-a] beginning graceful shutdown...
[order-a] draining in-flight requests...
[registry] deregistered: order-a
[order-a] terminated cleanly.
Registered instances after graceful shutdown: []
order-a was removed IMMEDIATELY -- no stale window at all.
```

### Level 3 — Advanced

```java
// File: TimeoutBasedSafetyNet.java -- a CRASH means graceful deregistration
// NEVER RUNS; a TIMEOUT-based sweep is the necessary fallback that eventually
// cleans up the stale entry anyway.
import java.util.*;

public class TimeoutBasedSafetyNet {
    record ServiceInstance(String id, String host, long lastHeartbeatMillis) {}

    static class ServiceRegistry {
        Map<String, ServiceInstance> instances = new LinkedHashMap<>();
        long timeoutMillis;
        ServiceRegistry(long timeoutMillis) { this.timeoutMillis = timeoutMillis; }

        void register(ServiceInstance instance) { instances.put(instance.id(), instance); System.out.println("[registry] registered: " + instance.id()); }
        void heartbeat(String instanceId, long nowMillis) {
            ServiceInstance old = instances.get(instanceId);
            if (old != null) instances.put(instanceId, new ServiceInstance(old.id(), old.host(), nowMillis));
        }
        void gracefulDeregister(String instanceId) {
            instances.remove(instanceId);
            System.out.println("[registry] gracefully deregistered: " + instanceId);
        }

        // the SAFETY NET: sweeps for instances that have gone SILENT past the timeout
        void timeoutSweep(long nowMillis) {
            Iterator<ServiceInstance> it = instances.values().iterator();
            while (it.hasNext()) {
                ServiceInstance instance = it.next();
                if (nowMillis - instance.lastHeartbeatMillis() > timeoutMillis) {
                    System.out.println("[registry, TIMEOUT SWEEP] " + instance.id() + " missed heartbeats past timeout -- removing");
                    it.remove();
                }
            }
        }
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry(1000); // 1 second timeout for the demo
        long t = 0;

        registry.register(new ServiceInstance("order-a", "10.0.1.5", t));
        registry.register(new ServiceInstance("order-b", "10.0.1.6", t));

        // order-a shuts down GRACEFULLY -- immediate, clean removal
        registry.gracefulDeregister("order-a");

        // order-b CRASHES -- no graceful call happens, it just stops sending heartbeats
        System.out.println("order-b CRASHES silently at t=0 -- no deregister() call, EVER.");

        t = 500;
        registry.timeoutSweep(t); // too soon -- order-b's last heartbeat (t=0) is only 500ms old, within the 1000ms timeout
        System.out.println("At t=500ms, sweep found order-b still WITHIN timeout: " + registry.instances.keySet());

        t = 1500;
        registry.timeoutSweep(t); // NOW order-b's silence (1500ms since its last heartbeat) exceeds the 1000ms timeout
        System.out.println("At t=1500ms, sweep result: " + registry.instances.keySet());
    }
}
```

**How to run:** `javac TimeoutBasedSafetyNet.java && java TimeoutBasedSafetyNet` (JDK 17+).

Expected output:
```
[registry] registered: order-a
[registry] registered: order-b
[registry] gracefully deregistered: order-a
order-b CRASHES silently at t=0 -- no deregister() call, EVER.
At t=500ms, sweep found order-b still WITHIN timeout: [order-b]
[registry, TIMEOUT SWEEP] order-b missed heartbeats past timeout -- removing
At t=1500ms, sweep result: []
```

## 6. Walkthrough

1. **Level 1** — `registeredInstances` is printed both before and after a comment stating `order-a` shut down, and the two printed lists are identical, because absolutely nothing in this code ever removes the entry — a directly demonstrated illustration of the stale-registration problem.
2. **Level 2, deregistration as the final shutdown step** — `gracefulShutdown` calls `registry.deregister(instanceId)` after simulated draining logic and immediately before printing that the instance terminated, modeling deregistration as a deliberate, ordered part of a clean shutdown sequence.
3. **Level 2, the immediate, verified removal** — the printed `registry.instances` list after `gracefulShutdown` runs is empty, directly confirming the instance was removed with no delay, unlike Level 1's permanently stale entry.
4. **Level 3, tracking last-heartbeat time explicitly** — `ServiceInstance` now carries a `lastHeartbeatMillis` field, and `ServiceRegistry.heartbeat` updates it whenever called; `timeoutSweep` compares `nowMillis - instance.lastHeartbeatMillis()` against the configured `timeoutMillis` to decide whether an instance should be purged.
5. **Level 3, two different instance fates** — `order-a` is removed via `gracefulDeregister`, immediately and deliberately, exactly as in Level 2; `order-b` is deliberately never deregistered gracefully at all (the printed comment states it "CRASHES silently"), modeling the unplanned-failure case where graceful shutdown code never gets to run.
6. **Level 3, the sweep at two different times** — the first call to `timeoutSweep(500)` checks `order-b`'s last heartbeat (still at `t=0`, since it never sent another one) against the 1000ms timeout; `500 - 0 = 500`, which does *not* exceed 1000, so `order-b` survives this sweep and remains registered.
7. **Level 3, the eventual cleanup** — the second call to `timeoutSweep(1500)` performs the identical check, but now `1500 - 0 = 1500`, which *does* exceed the 1000ms timeout, triggering removal — demonstrating the necessary safety-net behavior: `order-b`'s stale entry is eventually cleaned up automatically, purely from the registry's own periodic observation of missing heartbeats, with zero cooperation required from the crashed instance itself, closing the gap that graceful deregistration alone cannot cover.

## 7. Gotchas & takeaways

> **Gotcha:** the timeout window itself is a real trade-off — too short, and a genuinely healthy instance experiencing a brief network hiccup or a garbage-collection pause gets incorrectly deregistered and loses traffic it could have handled fine; too long, and a genuinely crashed instance stays listed and receives failed requests for an uncomfortably long window before cleanup; tuning this value is a deliberate balance between false-positive deregistrations and slow detection of genuine failures.

- Graceful deregistration is an explicit registry call made during a clean shutdown, removing an instance's entry immediately and avoiding any stale-registration window.
- Timeout-based deregistration is the registry's own fallback mechanism, purging instances that have stopped sending expected heartbeats for longer than a configured timeout — the necessary safety net for crashes and other unplanned failures where graceful shutdown code never runs.
- An instance that shuts down without either mechanism remains listed indefinitely, causing every caller routed to it to fail until something removes the stale entry.
- Both mechanisms are needed together: graceful deregistration handles the common, plannable case quickly and cleanly, while timeout-based deregistration handles the unplannable case that graceful shutdown structurally cannot cover.
- The timeout duration is a genuine trade-off between prematurely deregistering healthy-but-briefly-unresponsive instances and slowly detecting genuinely failed ones — tuning it requires balancing both risks deliberately.
