---
card: spring-data
gi: 131
slug: redis-sentinel-support
title: "Redis Sentinel support"
---

## 1. What it is

**Redis Sentinel** provides automatic failover for a standalone-style Redis deployment: one primary node handles writes, one or more replicas mirror it, and a set of Sentinel processes continuously monitor all of them — if the primary goes down, Sentinels agree on a replacement and promote a replica automatically. Spring Data Redis supports this through `RedisSentinelConfiguration`, which points the client at the Sentinels rather than a fixed primary address.

```java
@Bean
RedisConnectionFactory redisConnectionFactory() {
    RedisSentinelConfiguration sentinelConfig = new RedisSentinelConfiguration()
        .master("mymaster")
        .sentinel("sentinel-1", 26379)
        .sentinel("sentinel-2", 26379)
        .sentinel("sentinel-3", 26379);
    return new LettuceConnectionFactory(sentinelConfig);
}
```

## 2. Why & when

A standalone Redis instance is a single point of failure — if it crashes, every application depending on it loses connectivity until someone manually starts a new one and reconfigures every client to point at it. Sentinel automates that: it monitors the primary and its replicas, detects a failure via a majority vote among Sentinel processes (avoiding a single Sentinel's flaky network view triggering an unnecessary failover), and promotes a replica to primary, while the client library asks the Sentinels for the *current* primary's address rather than hardcoding one.

Reach for Sentinel when:

- You need automatic failover for a Redis deployment that's still conceptually "one primary, some replicas" — not sharded across many nodes, which is what Redis Cluster (the earlier card) is for instead.
- Your dataset comfortably fits on a single node, so you don't need Cluster's horizontal sharding — you need availability, not more capacity.
- You want the client to always talk to whichever node is *currently* the primary, without the application needing to know or care which physical node that is at any given moment.

## 3. Core concept

```
                 Sentinel-1  Sentinel-2  Sentinel-3    (monitor everything, vote on failures)
                      \           |           /
                       \          |          /
                    Primary --- replica --- replica

 Client asks: "who is the current primary for 'mymaster'?"
      -> Sentinels answer with the CURRENT primary's address (not a fixed one)

 Primary crashes:
   1. Sentinels detect it (via their own health checks)
   2. A MAJORITY of Sentinels must agree it's actually down (avoids a false alarm from one Sentinel's bad network view)
   3. Sentinels elect one replica and promote it to primary
   4. Clients asking "who is primary?" now get the NEW primary's address
```

The client never hardcodes the primary's address — it always asks the Sentinels, which always know the current truth.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sentinels monitor a primary and its replicas; when the primary fails, they promote a replica and clients learn the new primary address">
  <rect x="240" y="20" width="160" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="44" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Sentinel-1/2/3</text>

  <rect x="120" y="100" width="150" height="40" rx="8" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="195" y="124" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Primary (DOWN)</text>

  <rect x="370" y="100" width="150" height="40" rx="8" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="445" y="120" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">Replica</text>
  <text x="445" y="133" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">promoted to primary</text>

  <line x1="280" y1="60" x2="200" y2="95" stroke="#8b949e" stroke-width="1.3"/>
  <line x1="360" y1="60" x2="440" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>

  <text x="320" y="170" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">clients asking Sentinels "who is primary?" now get the replica's address</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Once a replica is promoted, Sentinel updates what it tells clients — no manual reconfiguration required anywhere.

## 5. Runnable example

The scenario: a client resolving the current Redis primary through Sentinels, evolving from a basic lookup, to detecting a failure and triggering failover, to requiring a **quorum** of Sentinels before acting — avoiding a single Sentinel's false alarm from causing an unwanted failover.

### Level 1 — Basic

Model asking Sentinels for the current primary's address.

```java
import java.util.*;

public class SentinelLevel1 {
    public static void main(String[] args) {
        SentinelGroup sentinels = new SentinelGroup("mymaster", "primary-node-1");

        String currentPrimary = sentinels.getCurrentPrimary(); // ASK the Sentinels, don't hardcode
        System.out.println("Client resolves current primary: " + currentPrimary);
    }
}

// Stands in for RedisSentinelConfiguration.master(name).sentinel(host, port)...
class SentinelGroup {
    private final String masterName;
    private String currentPrimaryAddress;

    SentinelGroup(String masterName, String initialPrimary) {
        this.masterName = masterName;
        this.currentPrimaryAddress = initialPrimary;
    }

    String getCurrentPrimary() { return currentPrimaryAddress; } // SENTINEL get-master-addr-by-name mymaster
}
```

How to run: `java SentinelLevel1.java`

`getCurrentPrimary()` mirrors the real command a Sentinel-aware client issues, `SENTINEL get-master-addr-by-name mymaster` — the client asks Sentinel for the address rather than being configured with a fixed primary hostname, which is exactly what makes automatic failover transparent to application code.

### Level 2 — Intermediate

Simulate a primary failure and the resulting promotion — the client re-asks Sentinel and gets a different, correct answer without any reconfiguration.

```java
import java.util.*;

public class SentinelLevel2 {
    public static void main(String[] args) {
        SentinelGroup sentinels = new SentinelGroup("mymaster", "primary-node-1", List.of("replica-node-1", "replica-node-2"));

        System.out.println("Before failure, primary: " + sentinels.getCurrentPrimary());

        sentinels.reportPrimaryDown(); // simulates Sentinel's own health checks detecting the primary is unreachable

        System.out.println("After failover,  primary: " + sentinels.getCurrentPrimary());
    }
}

class SentinelGroup {
    private final String masterName;
    private String currentPrimaryAddress;
    private final List<String> replicas;

    SentinelGroup(String masterName, String initialPrimary, List<String> replicas) {
        this.masterName = masterName;
        this.currentPrimaryAddress = initialPrimary;
        this.replicas = new ArrayList<>(replicas);
    }

    String getCurrentPrimary() { return currentPrimaryAddress; }

    void reportPrimaryDown() {
        System.out.println("  Sentinels detected " + currentPrimaryAddress + " is unreachable -- promoting a replica");
        String promoted = replicas.remove(0); // Sentinel elects one replica (simplified selection here)
        currentPrimaryAddress = promoted;
        System.out.println("  " + promoted + " promoted to new primary");
    }
}
```

How to run: `java SentinelLevel2.java`

`reportPrimaryDown` mirrors the internal Sentinel failover process: it removes the old primary from consideration and promotes the first available replica, updating `currentPrimaryAddress`. `getCurrentPrimary()` called again after the failure returns the *new* primary's address automatically — a client re-resolving through Sentinel after a connection failure gets routed to the correct node with no manual intervention.

### Level 3 — Advanced

Require a **quorum**: only trigger failover once a majority of Sentinel processes independently agree the primary is down, avoiding a false alarm from a single Sentinel with a flaky network view.

```java
import java.util.*;

public class SentinelLevel3 {
    public static void main(String[] args) {
        SentinelGroup sentinels = new SentinelGroup("mymaster", "primary-node-1", List.of("replica-node-1", "replica-node-2"), 3, 2); // quorum=2 of 3

        System.out.println("--- Sentinel-1 alone reports primary down (not enough for quorum) ---");
        sentinels.sentinelReportsDown("sentinel-1");
        System.out.println("Primary still: " + sentinels.getCurrentPrimary() + " (no failover triggered)");

        System.out.println("--- Sentinel-2 ALSO reports primary down (quorum reached) ---");
        sentinels.sentinelReportsDown("sentinel-2");
        System.out.println("Primary now: " + sentinels.getCurrentPrimary());
    }
}

class SentinelGroup {
    private final String masterName;
    private String currentPrimaryAddress;
    private final List<String> replicas;
    private final int totalSentinels;
    private final int quorum;
    private final Set<String> sentinelsReportingDown = new LinkedHashSet<>();

    SentinelGroup(String masterName, String initialPrimary, List<String> replicas, int totalSentinels, int quorum) {
        this.masterName = masterName;
        this.currentPrimaryAddress = initialPrimary;
        this.replicas = new ArrayList<>(replicas);
        this.totalSentinels = totalSentinels;
        this.quorum = quorum;
    }

    String getCurrentPrimary() { return currentPrimaryAddress; }

    // Mirrors the "Subjectively Down" (SDOWN) -> "Objectively Down" (ODOWN) transition Sentinel performs internally.
    void sentinelReportsDown(String sentinelId) {
        sentinelsReportingDown.add(sentinelId);
        System.out.println("  " + sentinelId + " marks primary as SDOWN (subjectively down, its own view)");
        if (sentinelsReportingDown.size() >= quorum) {
            System.out.println("  quorum reached (" + sentinelsReportingDown.size() + "/" + quorum
                + ") -- primary is ODOWN (objectively down) -- triggering failover");
            failover();
        } else {
            System.out.println("  quorum NOT yet reached (" + sentinelsReportingDown.size() + "/" + quorum
                + ") -- no failover, could be one Sentinel's network issue");
        }
    }

    private void failover() {
        String promoted = replicas.remove(0);
        currentPrimaryAddress = promoted;
        sentinelsReportingDown.clear();
    }
}
```

How to run: `java SentinelLevel3.java`

With `quorum=2` out of `3` total Sentinels, a single Sentinel reporting the primary down (`SDOWN`, "subjectively down" — that Sentinel's own view) is *not* enough to trigger failover, since it could be a network partition affecting only that one Sentinel rather than a real primary failure. Only once a second, independent Sentinel also reports the primary down does the group reach quorum, transition to `ODOWN` ("objectively down"), and actually promote a replica — protecting against unnecessary failovers caused by one Sentinel's flaky connectivity.

## 6. Walkthrough

Execution starts in `main` for Level 3. `sentinels` is constructed with `totalSentinels=3` and `quorum=2`, and the primary starts as `"primary-node-1"`.

`sentinels.sentinelReportsDown("sentinel-1")` adds `"sentinel-1"` to `sentinelsReportingDown`, bringing its size to `1`. Since `1 >= 2` (quorum) is `false`, the `else` branch runs: no failover happens, and `getCurrentPrimary()` still returns `"primary-node-1"`.

`sentinels.sentinelReportsDown("sentinel-2")` adds `"sentinel-2"`, bringing `sentinelsReportingDown`'s size to `2`. Now `2 >= 2` is `true`, so the `if` branch runs: it prints that quorum was reached and calls `failover()`, which removes `"replica-node-1"` from `replicas`, sets it as the new `currentPrimaryAddress`, and clears `sentinelsReportingDown` for the next monitoring cycle. `getCurrentPrimary()` now returns `"replica-node-1"`.

```
--- Sentinel-1 alone reports primary down (not enough for quorum) ---
  sentinel-1 marks primary as SDOWN (subjectively down, its own view)
  quorum NOT yet reached (1/2) -- no failover, could be one Sentinel's network issue
Primary still: primary-node-1 (no failover triggered)
--- Sentinel-2 ALSO reports primary down (quorum reached) ---
  sentinel-2 marks primary as SDOWN (subjectively down, its own view)
  quorum reached (2/2) -- primary is ODOWN (objectively down) -- triggering failover
Primary now: replica-node-1
```

In a real Sentinel deployment, this exact two-stage process — `SDOWN` (one Sentinel's individual suspicion) escalating to `ODOWN` (a quorum of Sentinels agreeing) before a failover is triggered — is what makes Sentinel-based failover resilient to a single Sentinel's own network problems, and it's precisely why `quorum` is a required, deliberately-chosen configuration value rather than an implicit "any one Sentinel can decide," which would make failover far too trigger-happy.

## 7. Gotchas & takeaways

> Gotcha: `quorum` should always be set so that a majority of your total Sentinels is required — with an even number of Sentinels split by a network partition, it's possible for both halves to independently think they have "enough" votes unless the quorum value and Sentinel count are chosen carefully (an odd total, like 3 or 5, is the standard recommendation).

> Gotcha: Sentinel failover changes which node is primary, but the client must **always** resolve the primary through Sentinel (as `RedisSentinelConfiguration` does) rather than caching a resolved address indefinitely — a client that connects once and holds onto a stale address forever won't notice a failover has happened.

- Redis Sentinel provides automatic failover for a single-primary, replica-backed Redis deployment, distinct from Redis Cluster's horizontal sharding.
- Clients configured with `RedisSentinelConfiguration` ask Sentinel for the current primary's address rather than hardcoding one, so failover is transparent to application code.
- Failover only triggers once a **quorum** of Sentinels independently agree the primary is down (`SDOWN` escalating to `ODOWN`), protecting against a single Sentinel's flaky network view causing an unnecessary promotion.
- Choose Sentinel when you need availability for a dataset that fits on one node; choose Cluster (the earlier card) when you need to shard data or throughput across multiple nodes.
