---
card: spring-cloud
gi: 31
slug: self-preservation-mode
title: "Self-preservation mode"
---

## 1. What it is

Self-preservation mode is a safety switch inside Eureka Server: if the rate of incoming heartbeats drops too far below what's statistically expected (below roughly 85% of the expected renewal rate), the server assumes it's suffering a network partition — not that instances actually died — and stops evicting instances, keeping the entire current registry (even stale entries) rather than risking a mass, incorrect eviction.

```
expected heartbeats per minute  = number_of_instances * (60 / lease_renewal_interval_seconds)
renewal threshold                = expected heartbeats per minute * 0.85

if actual heartbeats per minute < renewal threshold:
    ENTER self-preservation mode: stop evicting anyone
```

## 2. Why & when

Without self-preservation, a network blip that cuts off Eureka Server from a large chunk of its instances would look identical, from the server's point of view, to those instances all crashing simultaneously — and the server would evict every one of them, wiping out a perfectly healthy registry. Self-preservation exists because Eureka is explicitly designed to be AP (favors Availability over strict Consistency, per the CAP theorem): it would rather keep serving a possibly-stale registry than aggressively evict and serve an empty or nearly-empty one during a network problem.

It matters when:

- Running Eureka Server in production, where a transient network partition between the server and a subnet of instances is a real, if uncommon, failure mode — self-preservation prevents that partition from cascading into "every service looks dead."
- Debugging local/dev setups where self-preservation frequently confuses developers: with only 1-2 instances, a single dev restarting their laptop can trip the 85% threshold, and the server appears to stop cleaning up stale entries — this is expected, not a bug.
- Deciding whether to disable it (`eureka.server.enable-self-preservation=false`) for local development or small, low-stakes clusters where you'd rather see immediate, accurate eviction than tolerate a temporarily stale view.

## 3. Core concept

```
 Normal mode:
   heartbeat rate healthy -> evict any instance whose lease expired

 Self-preservation mode (triggered when heartbeat rate < 85% of expected):
   heartbeat rate degraded -> STOP evicting anyone, even expired leases
   assumption: "this looks like a network problem, not mass instance death"
```

Self-preservation trades short-term registry accuracy for protection against a much worse failure: false mass eviction during a network hiccup.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="When the heartbeat rate drops below 85 percent of expected, Eureka Server enters self-preservation mode and stops evicting instances even if their leases have expired">
  <rect x="30" y="30" width="240" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">heartbeat rate &gt;= 85% expected</text>
  <text x="150" y="68" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">normal mode: evict expired leases</text>

  <rect x="370" y="30" width="240" height="50" rx="8" fill="#e6494930" stroke="#e64949" stroke-width="1.5"/>
  <text x="490" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">heartbeat rate &lt; 85% expected</text>
  <text x="490" y="68" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">self-preservation: evict NO ONE</text>

  <line x1="270" y1="55" x2="365" y2="55" stroke="#8b949e" stroke-width="1.4" marker-end="url(#a31)"/>
  <text x="320" y="45" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">drop</text>
  <line x1="365" y1="70" x2="270" y2="70" stroke="#8b949e" stroke-width="1.4" marker-end="url(#a31)"/>
  <text x="320" y="90" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">recover</text>

  <rect x="200" y="140" width="240" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="160" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">assumption: network partition,</text>
  <text x="320" y="174" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">not mass instance death</text>

  <defs><marker id="a31" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The server toggles between two modes based on the observed heartbeat rate, defaulting to caution (no eviction) whenever the rate looks abnormal.

## 5. Runnable example

The scenario: simulate a registry that tracks expected vs. actual heartbeat rate, evolving from naive always-evict behavior, to threshold-based self-preservation, to a full simulation of a network partition triggering and then recovering from self-preservation.

### Level 1 — Basic

Naive eviction: always evict expired leases, no self-preservation.

```java
import java.util.*;

public class SelfPreservationLevel1 {
    static class Lease {
        String id;
        long lastHeartbeat;
        Lease(String id, long lastHeartbeat) { this.id = id; this.lastHeartbeat = lastHeartbeat; }
        boolean expired(long now, long leaseDurationMs) { return now - lastHeartbeat > leaseDurationMs; }
    }

    public static void main(String[] args) {
        long leaseDurationMs = 90_000;
        List<Lease> leases = new ArrayList<>(List.of(
                new Lease("i1", 0), new Lease("i2", 0), new Lease("i3", 0)
        ));

        long now = 200_000; // all three look expired -- but is that a crash or a network blip?
        leases.removeIf(l -> l.expired(now, leaseDurationMs));

        System.out.println("remaining after naive eviction: " + leases.size()); // 0 -- wiped the whole registry
    }
}
```

How to run: `java SelfPreservationLevel1.java`

Naive eviction has no way to distinguish "three instances crashed" from "the network between them and the registry broke" — either way, it wipes the registry down to zero.

### Level 2 — Intermediate

Add a heartbeat-rate check: only evict if the observed heartbeat rate is at or above 85% of what's expected.

```java
import java.util.*;

public class SelfPreservationLevel2 {
    static class Lease {
        String id;
        long lastHeartbeat;
        Lease(String id, long lastHeartbeat) { this.id = id; this.lastHeartbeat = lastHeartbeat; }
        boolean expired(long now, long leaseDurationMs) { return now - lastHeartbeat > leaseDurationMs; }
    }

    static final double RENEWAL_THRESHOLD = 0.85;

    static boolean selfPreservationActive(int expectedHeartbeatsPerMin, int actualHeartbeatsPerMin) {
        return actualHeartbeatsPerMin < expectedHeartbeatsPerMin * RENEWAL_THRESHOLD;
    }

    public static void main(String[] args) {
        long leaseDurationMs = 90_000;
        List<Lease> leases = new ArrayList<>(List.of(
                new Lease("i1", 0), new Lease("i2", 0), new Lease("i3", 0)
        ));

        int expectedPerMin = 3 * 2; // 3 instances, heartbeat every 30s = 2/min each
        int actualPerMin = 0;        // network partition: nothing is getting through

        long now = 200_000;
        if (selfPreservationActive(expectedPerMin, actualPerMin)) {
            System.out.println("SELF-PRESERVATION ACTIVE — skipping eviction, keeping all " + leases.size() + " leases");
        } else {
            leases.removeIf(l -> l.expired(now, leaseDurationMs));
            System.out.println("remaining after eviction: " + leases.size());
        }
    }
}
```

How to run: `java SelfPreservationLevel2.java`

`selfPreservationActive` implements the 85% threshold directly: `actualPerMin` (0) is nowhere near `expectedPerMin * 0.85` (2.55), so the server correctly refuses to evict, leaving the registry intact through what it correctly treats as a suspected network problem rather than a real mass failure.

### Level 3 — Advanced

Simulate the partition happening and then recovering, running eviction checks on a tick, and confirm entries survive the partition window and get correctly evicted only after the rate genuinely recovers and a lease is genuinely still expired.

```java
import java.util.*;

public class SelfPreservationLevel3 {
    static class Lease {
        String id;
        long lastHeartbeat;
        Lease(String id, long lastHeartbeat) { this.id = id; this.lastHeartbeat = lastHeartbeat; }
        boolean expired(long now, long leaseDurationMs) { return now - lastHeartbeat > leaseDurationMs; }
    }

    static final double RENEWAL_THRESHOLD = 0.85;
    static final long LEASE_DURATION_MS = 90_000;

    static boolean selfPreservationActive(int expectedPerMin, int actualPerMin) {
        return actualPerMin < expectedPerMin * RENEWAL_THRESHOLD;
    }

    static void tick(List<Lease> leases, long now, int expectedPerMin, int actualPerMin, String label) {
        if (selfPreservationActive(expectedPerMin, actualPerMin)) {
            System.out.println(label + ": self-preservation ACTIVE, no eviction, size=" + leases.size());
        } else {
            int before = leases.size();
            leases.removeIf(l -> l.expired(now, LEASE_DURATION_MS));
            System.out.println(label + ": normal mode, evicted " + (before - leases.size()) + ", size=" + leases.size());
        }
    }

    public static void main(String[] args) {
        List<Lease> leases = new ArrayList<>(List.of(
                new Lease("i1", 0), new Lease("i2", 0), new Lease("i3", 0)
        ));
        int expectedPerMin = 3 * 2;

        tick(leases, 20_000, expectedPerMin, 6, "t=20s (healthy)");             // full rate, nothing expired yet
        tick(leases, 200_000, expectedPerMin, 0, "t=200s (partition)");         // rate crashes -> self-preservation kicks in
        tick(leases, 260_000, expectedPerMin, 0, "t=260s (still partitioned)"); // still protected
        // network recovers; i1 and i2 resume heartbeating, i3 genuinely crashed and never comes back
        leases.stream().filter(l -> l.id.equals("i1") || l.id.equals("i2")).forEach(l -> l.lastHeartbeat = 350_000);
        tick(leases, 400_000, expectedPerMin, 6, "t=400s (recovered, i3 truly dead)"); // rate back to normal -> evicts i3 only
    }
}
```

How to run: `java SelfPreservationLevel3.java`

Through the partition window (`t=200s`, `t=260s`), self-preservation keeps the registry at 3 entries even though every lease looks expired by lease-duration math alone. Once the heartbeat rate genuinely recovers at `t=400s` (`i1` and `i2` bring the rate back to 6/min, above the 5.1/min threshold), normal eviction resumes — and only `i3`, which truly never resumed heartbeating, gets evicted; `i1` and `i2` survive because their `lastHeartbeat` of `350_000` is only 50 seconds behind `now=400_000`, safely under the 90-second lease duration.

## 6. Walkthrough

Trace the five `tick` calls in Level 3 in order.

1. `t=20s (healthy)`: `actualPerMin=6` equals `expectedPerMin=6`, well above the 85% threshold (5.1). `selfPreservationActive` returns `false`, so normal eviction runs — and at `now=20_000`, every lease's `lastHeartbeat=0` is only 20 seconds old, well under the 90-second `LEASE_DURATION_MS`, so nothing is evicted and the registry stays at 3.
2. `t=200s (partition)`: `actualPerMin` drops to `0` — a real network partition where no heartbeat is reaching the server. `selfPreservationActive` returns `true` (0 < 5.1), so the tick prints "self-preservation ACTIVE" and skips the `removeIf` entirely, regardless of how expired any lease looks by raw lease-duration math.
3. `t=260s (still partitioned)`: rate is still `0`, so self-preservation remains active — the registry holds steady at its prior size through the whole outage window.
4. Between this tick and the next, two of the three instances (`i1`, `i2`) resume heartbeating — modeled directly by setting their `lastHeartbeat` to `350_000` — while `i3` never recovers, modeling a genuine crash that happened to occur during the same window as the network blip.
5. `t=400s (recovered, i3 truly dead)`: `actualPerMin=6` is back at the expected rate, above the 5.1 threshold, so normal mode resumes. `removeIf` evaluates each lease against `now=400_000`: `i1` and `i2` have `lastHeartbeat=350_000`, only 50 seconds old, so they survive; `i3` still has `lastHeartbeat=0`, hundreds of seconds stale, and is evicted.

```
t=20s    healthy        -> normal mode, nothing expired yet
t=200s   partition hits  -> SELF-PRESERVATION: no eviction
t=260s   still down      -> SELF-PRESERVATION: no eviction
  (i1, i2 resume heartbeating; i3 does not)
t=400s   rate recovers   -> normal mode resumes -> only truly-dead i3 evicted
```

## 7. Gotchas & takeaways

> **Gotcha:** in local development, running just one or two Eureka Server/client instances routinely trips the 85% threshold on ordinary restarts (killing and relaunching a service for testing looks, statistically, exactly like a partition to a tiny fleet) — the server logs `EMERGENCY! EUREKA MAY BE INCORRECTLY CLAIMING INSTANCES ARE UP WHEN THEY'RE NOT`. This is expected in dev; consider `eureka.server.enable-self-preservation=false` for local/dev profiles only, never in production.

- Self-preservation is Eureka choosing availability (serve a possibly-stale registry) over consistency (aggressively evict and risk wiping healthy instances) during ambiguous conditions — a direct, deliberate CAP-theorem tradeoff.
- The 85% renewal-rate threshold is a heuristic, not a guarantee — it's tuned to tolerate normal fluctuation while still catching genuine large-scale outages.
- Never disable self-preservation in production without understanding the tradeoff: doing so means a genuine network partition really can cause mass, incorrect instance eviction.
- Self-preservation affects the whole server's eviction behavior, not per-instance — it's an all-or-nothing switch based on aggregate heartbeat health, not a per-lease decision.
