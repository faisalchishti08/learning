---
card: microservices
gi: 189
slug: heartbeats-lease-renewal
title: "Heartbeats & lease renewal"
---

## 1. What it is

A heartbeat is a periodic signal a registered instance sends to the [service registry](0182-service-registry-concept.md) to confirm it's still alive and should remain registered. Lease renewal is the specific mechanism many registries build on top of heartbeats: registration is granted as a time-bounded lease (not a permanent entry), and each heartbeat renews that lease for another period — if renewal stops, the lease naturally expires and the registry [deregisters](0184-service-deregistration.md) the instance automatically, without needing a separate, explicit timeout-sweep mechanism layered on top.

## 2. Why & when

A registry needs some way to distinguish "this instance is still alive and healthy" from "this instance crashed or lost network connectivity and never got the chance to explicitly deregister" — and heartbeats are the simplest, most direct signal for this: silence past an expected interval is itself the failure signal, with no separate health-check polling required if heartbeats alone are the chosen mechanism. Framing registration as a leased, expiring grant (rather than a permanent entry requiring an explicit removal action) makes the failure-handling case the *default*, safe behavior — an instance that stops heartbeating is automatically and eventually removed, rather than requiring some other component to notice and explicitly clean it up.

Use heartbeat-based lease renewal as the standard mechanism for keeping registry entries accurate over an instance's lifetime, tuning the heartbeat interval and lease duration to balance detection speed (shorter intervals detect failures faster) against overhead and false-positive risk (too-short a lease duration relative to normal network jitter causes healthy instances to be prematurely expired).

## 3. Core concept

Each registration is stored with an expiration timestamp; a heartbeat received before that timestamp extends it forward by the configured lease duration, and a registry sweep (or lazy check on access) treats any lease whose expiration timestamp has already passed as expired, deregistering that instance.

```java
// registration grants a LEASE, not a permanent entry
registry.register(instanceId, leaseDurationSeconds = 30); // expires in 30s UNLESS renewed

// each heartbeat RENEWS the lease, pushing the expiration forward
void onHeartbeat(String instanceId) {
    registry.renewLease(instanceId, now() + leaseDurationSeconds); // "still alive, extend my lease"
}

// if NO heartbeat arrives before expiration, the lease naturally LAPSES
if (now() > registry.getLeaseExpiration(instanceId)) registry.expire(instanceId); // automatic, no special-case logic needed
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An instance sends heartbeats at regular intervals, each one renewing its lease and pushing the expiration deadline forward; when heartbeats stop arriving, the lease's expiration deadline is eventually reached and the instance is automatically deregistered" >
  <line x1="20" y1="100" x2="600" y2="100" stroke="#8b949e"/>
  <circle cx="100" cy="100" r="4" fill="#6db33f"/><text x="100" y="85" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">heartbeat</text>
  <circle cx="220" cy="100" r="4" fill="#6db33f"/><text x="220" y="85" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">heartbeat</text>
  <circle cx="340" cy="100" r="4" fill="#6db33f"/><text x="340" y="85" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">heartbeat</text>
  <text x="460" y="85" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">silence...</text>
  <circle cx="530" cy="100" r="5" fill="#8b949e"/><text x="530" y="120" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">lease expires -&gt; deregistered</text>

  <defs>
    <marker id="arr70" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each heartbeat pushes the expiration deadline forward; silence lets it arrive, triggering automatic deregistration.

## 5. Runnable example

Scenario: an order-service instance that starts with permanent, un-leased registration (showing the crash-detection gap), adds heartbeat-driven lease renewal so silence naturally leads to expiration, and finally demonstrates tuning the heartbeat interval and lease duration together, comparing fast-detection versus jitter-tolerant configurations.

### Level 1 — Basic

```java
// File: PermanentRegistrationNoLease.java -- registration is PERMANENT; a
// crashed instance stays registered FOREVER, with NO mechanism to detect its absence.
import java.util.*;

public class PermanentRegistrationNoLease {
    static Set<String> registeredInstances = new HashSet<>(Set.of("order-a"));

    public static void main(String[] args) {
        System.out.println("Registered: " + registeredInstances);
        System.out.println("order-a CRASHES silently...");
        // NOTHING checks for this -- registeredInstances is NEVER updated, EVER, without an explicit action
        System.out.println("Registered (unchanged, forever): " + registeredInstances);
        System.out.println("No lease, no heartbeat, no expiration mechanism -- a crash is INVISIBLE to this registry design.");
    }
}
```

**How to run:** `javac PermanentRegistrationNoLease.java && java PermanentRegistrationNoLease` (JDK 17+).

### Level 2 — Intermediate

```java
// File: HeartbeatDrivenLeaseRenewal.java -- registration grants a TIME-BOUNDED
// lease; heartbeats RENEW it; silence lets it EXPIRE automatically.
import java.util.*;

public class HeartbeatDrivenLeaseRenewal {
    static class LeaseRegistry {
        Map<String, Long> leaseExpirations = new HashMap<>(); // instanceId -> expiration timestamp
        long leaseDurationMillis;
        LeaseRegistry(long leaseDurationMillis) { this.leaseDurationMillis = leaseDurationMillis; }

        void register(String instanceId, long nowMillis) {
            leaseExpirations.put(instanceId, nowMillis + leaseDurationMillis);
            System.out.println("[t=" + nowMillis + "] " + instanceId + " registered, lease expires at t=" + leaseExpirations.get(instanceId));
        }
        void heartbeat(String instanceId, long nowMillis) {
            if (leaseExpirations.containsKey(instanceId)) {
                leaseExpirations.put(instanceId, nowMillis + leaseDurationMillis); // RENEW -- push expiration forward
                System.out.println("[t=" + nowMillis + "] " + instanceId + " heartbeat -- lease renewed to t=" + leaseExpirations.get(instanceId));
            }
        }
        void sweepExpired(long nowMillis) {
            leaseExpirations.entrySet().removeIf(entry -> {
                boolean expired = nowMillis > entry.getValue();
                if (expired) System.out.println("[t=" + nowMillis + "] " + entry.getKey() + " LEASE EXPIRED -- auto-deregistered");
                return expired;
            });
        }
    }

    public static void main(String[] args) {
        LeaseRegistry registry = new LeaseRegistry(1000); // 1-second lease duration

        registry.register("order-a", 0);
        registry.heartbeat("order-a", 800);   // renewed BEFORE expiration
        registry.sweepExpired(1500);           // NOT expired -- last renewal (t=800) + 1000ms = t=1800, still future

        System.out.println("order-a CRASHES at t=1600 -- no more heartbeats, EVER.");
        registry.sweepExpired(2900);           // last renewal was t=800, expiration was t=1800 -- NOW t=2900 is PAST it
        System.out.println("Registered after sweep: " + registry.leaseExpirations.keySet());
    }
}
```

**How to run:** `javac HeartbeatDrivenLeaseRenewal.java && java HeartbeatDrivenLeaseRenewal` (JDK 17+).

Expected output:
```
[t=0] order-a registered, lease expires at t=1000
[t=800] order-a heartbeat -- lease renewed to t=1800
order-a CRASHES at t=1600 -- no more heartbeats, EVER.
[t=2900] order-a LEASE EXPIRED -- auto-deregistered
Registered after sweep: []
```

### Level 3 — Advanced

```java
// File: TuningIntervalVsJitterTolerance.java -- compares an AGGRESSIVE
// (fast-detection) configuration against a JITTER-TOLERANT one, showing the
// real trade-off: fast detection risks false-positive expiration under normal network jitter.
import java.util.*;

public class TuningIntervalVsJitterTolerance {
    static class LeaseRegistry {
        Map<String, Long> leaseExpirations = new HashMap<>();
        long leaseDurationMillis;
        LeaseRegistry(long leaseDurationMillis) { this.leaseDurationMillis = leaseDurationMillis; }
        void register(String instanceId, long nowMillis) { leaseExpirations.put(instanceId, nowMillis + leaseDurationMillis); }
        void heartbeat(String instanceId, long nowMillis) {
            if (leaseExpirations.containsKey(instanceId)) leaseExpirations.put(instanceId, nowMillis + leaseDurationMillis);
        }
        boolean sweepAndCheck(String instanceId, long nowMillis) {
            Long expiration = leaseExpirations.get(instanceId);
            if (expiration != null && nowMillis > expiration) { leaseExpirations.remove(instanceId); return false; }
            return expiration != null;
        }
    }

    public static void main(String[] args) {
        // scenario: heartbeats normally arrive every 500ms, but ONE heartbeat is DELAYED
        // by 900ms due to a transient network hiccup -- a REALISTIC, harmless jitter event
        long[] heartbeatTimes = {0, 500, 1400, 1900, 2400}; // the THIRD heartbeat is late (900ms gap instead of 500ms)

        System.out.println("=== AGGRESSIVE config: 700ms lease (barely more than the normal 500ms interval) ===");
        LeaseRegistry aggressive = new LeaseRegistry(700);
        aggressive.register("order-a", 0);
        boolean aggressiveSurvived = true;
        for (int i = 1; i < heartbeatTimes.length; i++) {
            if (!aggressive.sweepAndCheck("order-a", heartbeatTimes[i])) { aggressiveSurvived = false; break; }
            aggressive.heartbeat("order-a", heartbeatTimes[i]);
        }
        System.out.println("order-a survived the jitter with AGGRESSIVE config: " + aggressiveSurvived + " (700ms lease < 900ms gap -- FALSE-POSITIVE expiration)");

        System.out.println("\n=== JITTER-TOLERANT config: 1500ms lease (generous margin over the normal interval) ===");
        LeaseRegistry tolerant = new LeaseRegistry(1500);
        tolerant.register("order-a", 0);
        boolean tolerantSurvived = true;
        for (int i = 1; i < heartbeatTimes.length; i++) {
            if (!tolerant.sweepAndCheck("order-a", heartbeatTimes[i])) { tolerantSurvived = false; break; }
            tolerant.heartbeat("order-a", heartbeatTimes[i]);
        }
        System.out.println("order-a survived the jitter with JITTER-TOLERANT config: " + tolerantSurvived + " (1500ms lease > 900ms gap -- correctly tolerated)");
    }
}
```

**How to run:** `javac TuningIntervalVsJitterTolerance.java && java TuningIntervalVsJitterTolerance` (JDK 17+).

Expected output:
```
=== AGGRESSIVE config: 700ms lease (barely more than the normal 500ms interval) ===
order-a survived the jitter with AGGRESSIVE config: false (700ms lease < 900ms gap -- FALSE-POSITIVE expiration)

=== JITTER-TOLERANT config: 1500ms lease (generous margin over the normal interval) ===
order-a survived the jitter with JITTER-TOLERANT config: true (1500ms lease > 900ms gap -- correctly tolerated)
```

## 6. Walkthrough

1. **Level 1** — `registeredInstances` is a plain `Set<String>` with no notion of expiration at all; the printed comment confirms a crash produces literally no change to this set, since nothing observes or reacts to the absence of any ongoing signal.
2. **Level 2, registration as a leased grant** — `LeaseRegistry.register` stores `nowMillis + leaseDurationMillis` as the instance's expiration timestamp, rather than simply adding it to a permanent set — this is the fundamental shift from "registered forever" to "registered until this specific moment, unless renewed."
3. **Level 2, heartbeat as renewal** — `heartbeat` recalculates and overwrites the stored expiration to `nowMillis + leaseDurationMillis` again, pushing the deadline forward each time it's called — `order-a`'s heartbeat at `t=800` moves its expiration from `t=1000` to `t=1800`.
4. **Level 2, the crash and eventual detection** — after the simulated crash at `t=1600` (with the last successful heartbeat having been at `t=800`, giving an expiration of `t=1800`), the sweep at `t=2900` finds `nowMillis > entry.getValue()` (2900 > 1800) true, removes the entry, and prints the expiration message — the crash was detected automatically, purely from the absence of a heartbeat that should have arrived and renewed the lease before `t=1800`.
5. **Level 3, a realistic jitter scenario** — `heartbeatTimes` models heartbeats normally spaced 500ms apart, but with one gap stretched to 900ms (`1400` following `500`, rather than the expected `1000`), representing a genuine, harmless, transient network delay rather than an actual instance failure.
6. **Level 3, the aggressive configuration's false positive** — with a 700ms lease duration, the gap between the heartbeat at `t=500` (renewing the lease to expire at `t=1200`) and the delayed heartbeat at `t=1400` means the lease expires at `t=1200`, before the delayed heartbeat arrives at `t=1400` — the `sweepAndCheck` call at `t=1400` finds the lease already expired and reports the instance as no longer surviving, a false-positive expiration of a perfectly healthy instance that merely experienced normal network jitter.
7. **Level 3, the jitter-tolerant configuration's correct behavior** — with a 1500ms lease duration, the same 900ms gap between heartbeats is comfortably within the lease's margin (the heartbeat at `t=500` renews the lease to expire at `t=2000`, well after the delayed heartbeat arrives at `t=1400`), so the instance correctly survives the same jitter event that caused a false positive under the aggressive configuration — this side-by-side comparison makes the real, practical trade-off concrete: a shorter lease duration detects genuine failures faster but risks prematurely expiring healthy instances during normal network variability, while a longer lease duration tolerates that variability at the cost of slower genuine-failure detection.

## 7. Gotchas & takeaways

> **Gotcha:** the lease duration needs to be set with real margin above the *expected worst-case* heartbeat interval, not just the *typical* interval — tuning it against average-case timing (as the aggressive configuration effectively did) leaves no room for the normal jitter that real networks and busy systems routinely produce, turning occasional healthy delays into false-positive deregistrations that unnecessarily remove working instances from rotation.

- Heartbeats are the periodic signal an instance sends to confirm it's still alive; lease renewal frames registration as a time-bounded grant that heartbeats extend, rather than a permanent entry requiring explicit removal.
- This makes automatic deregistration the default, safe outcome of a crash or lost connectivity — an instance that stops heartbeating naturally falls out of the registry once its lease expires, with no separate failure-detection mechanism needed.
- The lease duration and heartbeat interval need to be tuned together, with the lease duration providing real margin above the expected worst-case (not just typical) heartbeat interval.
- Too short a lease duration relative to normal timing variability causes healthy instances to be falsely expired; too long a lease duration delays detecting genuine failures.
- This mechanism is the concrete implementation behind the general concept of [timeout-based service deregistration](0184-service-deregistration.md), providing the specific expiration-and-renewal logic that makes it work.
