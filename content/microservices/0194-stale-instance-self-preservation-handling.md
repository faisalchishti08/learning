---
card: microservices
gi: 194
slug: stale-instance-self-preservation-handling
title: "Stale instance / self-preservation handling"
---

## 1. What it is

Self-preservation is a defensive mode some registries (Eureka being the canonical example) enter when the rate of instance expirations crosses an unusually high threshold — instead of trusting that many instances genuinely failed at once, the registry assumes it's more likely experiencing a network partition or connectivity problem of its own, and stops expiring instances entirely for a while, deliberately keeping possibly-stale entries around rather than aggressively deregistering what might actually be healthy instances the registry has simply lost contact with.

## 2. Why & when

A registry's normal timeout-based deregistration assumes that "an instance stopped sending heartbeats" reliably means "that instance is actually down" — but this assumption breaks during a network partition, where the registry itself loses connectivity to a large swath of otherwise-perfectly-healthy instances simultaneously. Without self-preservation, a network blip affecting the registry's own connectivity could cause it to mass-deregister a huge fraction of genuinely healthy instances all at once, which is actively worse than the alternative of temporarily keeping stale entries: routing some traffic to instances that might be down is a partial, recoverable problem, while suddenly having no registered instances at all for a service is a total, cascading one.

Self-preservation mode activates automatically based on a threshold (Eureka's default: expiring more than roughly 15% of registered instances within a renewal window), trading correctness (some genuinely-dead instances might stay registered longer than they should) for stability (avoiding a catastrophic mass-deregistration event). Understand this behavior specifically so that a sudden, unexplained spike in "stale-looking" registered instances during a network event isn't mistaken for a registry bug — it's a deliberate, protective trade-off.

## 3. Core concept

The registry tracks the rate of heartbeat renewals relative to the total number of registered instances; if that renewal rate drops below an expected threshold (suggesting many instances have simultaneously stopped renewing, which is far more consistent with a registry-side connectivity issue than a genuine simultaneous mass-failure), the registry suspends its normal expiration logic until renewals recover.

```java
double expectedRenewalsPerMinute = totalRegisteredInstances * expectedRenewsPerInstancePerMinute;
double actualRenewalsPerMinute = countRecentRenewals();

if (actualRenewalsPerMinute < expectedRenewalsPerMinute * selfPreservationThreshold) {
    selfPreservationModeActive = true; // STOP expiring instances -- likely a registry-side network issue, not mass failure
}
// while self-preservation is active: normal timeout-based expiration is SUSPENDED
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Normal operation: renewal rate tracks expected levels, and instances that stop renewing are expired promptly. During a network partition: renewal rate drops sharply below the self-preservation threshold, and the registry suspends expiration entirely rather than mass-deregistering instances" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Normal operation</text>
  <rect x="30" y="40" width="240" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">renewal rate near 100% -- expire normally</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Network partition</text>
  <rect x="360" y="40" width="240" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="480" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">renewal rate crashes -- SELF-PRESERVATION</text>

  <text x="150" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">stale instances expired promptly</text>
  <text x="480" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">expiration SUSPENDED, entries kept</text>

  <defs>
    <marker id="arr75" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

A sharp drop in renewal rate signals a likely registry-side problem, not mass instance failure — expiration pauses accordingly.

## 5. Runnable example

Scenario: an order-service registry that starts with naive timeout-based expiration mass-deregistering during a simulated network partition (showing the catastrophic outcome), adds self-preservation detection so the registry recognizes the anomalous renewal-rate drop and suspends expiration, and finally demonstrates the registry automatically resuming normal expiration once the renewal rate recovers, confirming the partition has genuinely ended.

### Level 1 — Basic

```java
// File: NaiveTimeoutExpiration.java -- a NETWORK PARTITION drops MOST renewals;
// naive timeout logic mass-deregisters nearly EVERYTHING, even though the
// instances are almost certainly still healthy.
import java.util.*;

public class NaiveTimeoutExpiration {
    public static void main(String[] args) {
        int totalInstances = 20;
        Set<Integer> registered = new HashSet<>();
        for (int i = 0; i < totalInstances; i++) registered.add(i);

        // NETWORK PARTITION: only 2 of 20 instances' heartbeats reach the registry this cycle
        Set<Integer> renewalsReceived = Set.of(0, 1);

        // NAIVE logic: expire anything that DIDN'T renew, no matter how many that is
        registered.removeIf(id -> !renewalsReceived.contains(id));

        System.out.println("Instances remaining after naive expiration: " + registered.size() + " / " + totalInstances);
        System.out.println("18 of 20 PERFECTLY HEALTHY instances were just mass-deregistered because of a REGISTRY-SIDE network issue, not because they actually failed.");
    }
}
```

**How to run:** `javac NaiveTimeoutExpiration.java && java NaiveTimeoutExpiration` (JDK 17+).

### Level 2 — Intermediate

```java
// File: SelfPreservationDetection.java -- the registry NOTICES the anomalous
// renewal-rate DROP and SUSPENDS expiration rather than trusting it blindly.
import java.util.*;

public class SelfPreservationDetection {
    static class Registry {
        Set<Integer> registered = new HashSet<>();
        double selfPreservationThreshold = 0.85; // expect at LEAST 85% of expected renewals

        boolean expirationCycle(Set<Integer> renewalsReceived) {
            double expectedRenewals = registered.size();
            double actualRenewals = renewalsReceived.size();
            double renewalRate = actualRenewals / expectedRenewals;

            if (renewalRate < selfPreservationThreshold) {
                System.out.println("  renewal rate " + String.format("%.0f%%", renewalRate * 100) + " is BELOW threshold -- SELF-PRESERVATION activated, expiration SUSPENDED");
                return true; // self-preservation active -- do NOT expire anything
            }
            registered.removeIf(id -> !renewalsReceived.contains(id)); // safe to expire -- renewal rate looks normal
            System.out.println("  renewal rate " + String.format("%.0f%%", renewalRate * 100) + " is normal -- expiring non-renewing instances as usual");
            return false;
        }
    }

    public static void main(String[] args) {
        Registry registry = new Registry();
        for (int i = 0; i < 20; i++) registry.registered.add(i);

        System.out.println("Network partition -- only 2 of 20 instances' heartbeats reach the registry:");
        registry.expirationCycle(Set.of(0, 1));

        System.out.println("Instances remaining: " + registry.registered.size() + " / 20");
        System.out.println("ALL 20 instances are STILL registered -- the registry correctly recognized this as ITS OWN connectivity issue, not mass failure.");
    }
}
```

**How to run:** `javac SelfPreservationDetection.java && java SelfPreservationDetection` (JDK 17+).

Expected output:
```
Network partition -- only 2 of 20 instances' heartbeats reach the registry:
  renewal rate 10% is BELOW threshold -- SELF-PRESERVATION activated, expiration SUSPENDED
Instances remaining: 20 / 20
ALL 20 instances are STILL registered -- the registry correctly recognized this as ITS OWN connectivity issue, not mass failure.
```

### Level 3 — Advanced

```java
// File: AutomaticRecoveryFromSelfPreservation.java -- ONCE the renewal rate
// RECOVERS (the partition heals), the registry AUTOMATICALLY resumes normal
// expiration -- confirming the anomaly has genuinely passed.
import java.util.*;

public class AutomaticRecoveryFromSelfPreservation {
    static class Registry {
        Set<Integer> registered = new HashSet<>();
        double selfPreservationThreshold = 0.85;
        boolean selfPreservationActive = false;

        void expirationCycle(int cycleNumber, Set<Integer> renewalsReceived) {
            double renewalRate = (double) renewalsReceived.size() / registered.size();
            boolean shouldSelfPreserve = renewalRate < selfPreservationThreshold;

            if (shouldSelfPreserve) {
                selfPreservationActive = true;
                System.out.println("Cycle " + cycleNumber + ": renewal rate " + String.format("%.0f%%", renewalRate * 100) + " -- SELF-PRESERVATION active, no expiration");
            } else {
                if (selfPreservationActive) {
                    System.out.println("Cycle " + cycleNumber + ": renewal rate " + String.format("%.0f%%", renewalRate * 100) + " -- RECOVERED, self-preservation DEACTIVATED, resuming normal expiration");
                    selfPreservationActive = false;
                } else {
                    System.out.println("Cycle " + cycleNumber + ": renewal rate " + String.format("%.0f%%", renewalRate * 100) + " -- normal operation");
                }
                registered.removeIf(id -> !renewalsReceived.contains(id)); // NOW safe to expire non-renewing instances
            }
        }
    }

    public static void main(String[] args) {
        Registry registry = new Registry();
        for (int i = 0; i < 20; i++) registry.registered.add(i);

        // cycle 1: everything normal
        registry.expirationCycle(1, new HashSet<>(registry.registered));

        // cycle 2: NETWORK PARTITION begins -- renewal rate crashes
        registry.expirationCycle(2, Set.of(0, 1));
        System.out.println("  Instances remaining: " + registry.registered.size());

        // cycle 3: partition CONTINUES -- self-preservation stays active
        registry.expirationCycle(3, Set.of(0, 1, 2));
        System.out.println("  Instances remaining: " + registry.registered.size());

        // cycle 4: partition HEALS -- renewal rate recovers, self-preservation deactivates AUTOMATICALLY
        Set<Integer> fullRecovery = new HashSet<>(registry.registered);
        registry.expirationCycle(4, fullRecovery);
        System.out.println("  Instances remaining: " + registry.registered.size());
    }
}
```

**How to run:** `javac AutomaticRecoveryFromSelfPreservation.java && java AutomaticRecoveryFromSelfPreservation` (JDK 17+).

Expected output:
```
Cycle 1: renewal rate 100% -- normal operation
Cycle 2: renewal rate 10% -- SELF-PRESERVATION active, no expiration
  Instances remaining: 20
Cycle 3: renewal rate 15% -- SELF-PRESERVATION active, no expiration
  Instances remaining: 20
Cycle 4: renewal rate 100% -- RECOVERED, self-preservation DEACTIVATED, resuming normal expiration
  Instances remaining: 20
```

## 6. Walkthrough

1. **Level 1** — `renewalsReceived` contains only 2 of the 20 registered instance IDs, and `registered.removeIf(id -> !renewalsReceived.contains(id))` blindly removes every instance not in that set, regardless of how implausible it is that 18 of 20 instances genuinely failed simultaneously; the printed result confirms only 2 instances survive this naive logic.
2. **Level 2, computing the renewal rate** — `Registry.expirationCycle` computes `actualRenewals / expectedRenewals`, comparing how many instances actually renewed against how many were expected to (based on the total registered count).
3. **Level 2, the threshold check** — when `renewalRate` (0.10, or 10%) falls below `selfPreservationThreshold` (0.85), the method prints a self-preservation activation message and returns `true` *without* calling `registered.removeIf(...)` at all — the expiration logic never runs.
4. **Level 2, the preserved outcome** — after the identical partition scenario from Level 1 (only 2 of 20 instances renewing), `registry.registered.size()` remains at 20, directly contrasting with Level 1's catastrophic drop to 2, because self-preservation correctly suspended expiration entirely.
5. **Level 3, tracking state across multiple cycles** — `selfPreservationActive` is now a persistent field on `Registry`, tracked across successive calls to `expirationCycle`, modeling how a real registry's self-preservation mode is an ongoing state, not a one-time decision made independently each cycle.
6. **Level 3, the partition persisting across cycles 2 and 3** — both cycles show a renewal rate well below the threshold (10% and 15% respectively), and both correctly keep `selfPreservationActive` set to `true`, with `registered.size()` remaining at 20 throughout — the registry doesn't need the partition to resolve in exactly one cycle; it continues protecting the registration data for as long as the anomalous condition persists.
7. **Level 3, the automatic recovery** — cycle 4 passes `fullRecovery`, a copy of the *entire* current `registered` set as renewals, simulating every instance's heartbeat successfully reaching the registry again (the partition has healed); `renewalRate` computes to 100%, crossing back above the threshold, and because `selfPreservationActive` was `true` entering this check, the code takes the "RECOVERED" branch, printing the deactivation message and setting `selfPreservationActive = false` — critically, normal expiration logic (`registered.removeIf(...)`) resumes immediately in this same cycle, demonstrating that the registry requires no separate manual intervention to exit self-preservation mode; a genuinely recovered renewal rate is itself sufficient evidence that normal operation, including normal expiration, can safely resume.

## 7. Gotchas & takeaways

> **Gotcha:** self-preservation mode is specifically designed for development and testing environments to be a source of confusion — a small, low-traffic test Eureka instance with only a handful of registered services can trip the self-preservation threshold far more easily than a large production cluster (since a single instance's restart represents a much larger percentage of a small total), leading developers to see stale entries lingering in a test registry and mistakenly assume something is broken, when it's actually the self-preservation mechanism working exactly as intended for the (misleadingly small) scale it's observing.

- Self-preservation mode suspends a registry's normal timeout-based expiration when the renewal rate drops anomalously, on the assumption that a mass, simultaneous renewal failure is more likely a registry-side connectivity issue than genuine mass instance failure.
- This trades correctness (stale, possibly-dead instances staying registered longer than ideal) for stability (avoiding a catastrophic mass-deregistration event during a network partition affecting the registry itself).
- The threshold-based detection compares actual renewal rate against expected renewal rate, activating protection automatically when the gap becomes too large to be plausible as genuine instance failure.
- Recovery is automatic: once the renewal rate returns to normal levels, self-preservation deactivates and normal expiration resumes, with no manual intervention required.
- Self-preservation can be misleadingly easy to trigger in small-scale development and testing environments, where a single instance's restart represents a disproportionately large percentage of the total registered count — worth understanding explicitly to avoid mistaking it for a bug.
