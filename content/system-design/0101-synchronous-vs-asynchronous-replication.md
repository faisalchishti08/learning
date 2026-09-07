---
card: system-design
gi: 101
slug: synchronous-vs-asynchronous-replication
title: Synchronous vs asynchronous replication
---

## 1. What it is

**Synchronous replication** makes the leader wait for a follower to confirm it received a write before telling the client the write succeeded. **Asynchronous replication** lets the leader tell the client the write succeeded immediately, without waiting for any follower to confirm. The difference is entirely about *when* the client gets its answer relative to *when* followers actually have the data.

## 2. Why & when

This choice trades durability against latency and availability. Synchronous replication guarantees that once a write is confirmed, at least one follower already has it — so if the leader crashes the instant after confirming, no data is lost. But it makes every write only as fast as the slowest synchronous follower, and if that follower is unreachable, writes can stall entirely. Asynchronous replication is faster and keeps working even if a follower is down, but risks losing the most recent writes if the leader crashes before followers catch up. Use synchronous replication when losing a confirmed write is unacceptable (financial transactions); use asynchronous replication when write latency and availability matter more than the last few writes surviving a leader crash (most read-heavy web applications, with a small risk window).

## 3. Core concept

- **Synchronous:** leader writes locally, sends to the follower, **waits** for the follower's acknowledgment, *then* responds "success" to the client.
- **Asynchronous:** leader writes locally, responds "success" to the client **immediately**, and sends to the follower in the background, without waiting.
- **Semi-synchronous (a common middle ground):** the leader waits for acknowledgment from just one follower (synchronously), while replicating to any other followers asynchronously — giving one durability guarantee without the full latency cost of waiting for every follower.
- **The failure window:** with asynchronous replication, if the leader crashes after confirming a write to the client but before the follower received it, that write is lost when a follower is promoted to leader — the client was told it succeeded, but it did not durably survive.
- **Latency cost:** synchronous replication's write latency is bounded by the round trip to the follower, not just the leader's own local write — this is the direct cost of the durability guarantee.

## 4. Diagram

```
SYNCHRONOUS:                          ASYNCHRONOUS:

Client  Leader  Follower              Client  Leader  Follower
  |write->|                             |write->|
         |--replicate-->|                       |ack to client (immediate)
         |<--ack---------|                       |--replicate-->| (in background)
  |<--ack (success)-----|
  (client waits for follower's ack)     (client never waits for follower)
```
*Caption: synchronous replication delays the client's success response until a follower confirms; asynchronous replication never delays it.*

## 5. Runnable example

**Level 1 — Basic.** Model both replication modes with simulated network delay, and measure how long each takes to confirm a write.

**Level 2 — Crash scenario.** Simulate the leader crashing right after confirming, and check whether the follower actually has the write.

**Level 3 — Semi-synchronous.** Wait for exactly one follower out of two, replicate to the second one asynchronously.

```java
// SyncVsAsyncReplication.java
import java.util.*;

public class SyncVsAsyncReplication {

    static Map<String, String> leaderData = new HashMap<>();
    static Map<String, String> followerData = new HashMap<>();
    static Map<String, String> follower2Data = new HashMap<>();

    // simulates network delay: the follower "receives" the write after some delay, modeled by a counter.
    static Queue<Runnable> pendingReplication = new LinkedList<>();

    static long synchronousWrite(String key, String value) {
        long start = 0; // simulated time units
        leaderData.put(key, value);
        followerData.put(key, value); // waits (in this simulation: applies immediately) before confirming
        long confirmedAt = start + 10; // simulated round-trip cost to the follower
        return confirmedAt;
    }

    static long asynchronousWrite(String key, String value) {
        long start = 0;
        leaderData.put(key, value);
        long confirmedAt = start + 1; // confirms immediately, no round trip to the follower
        pendingReplication.add(() -> followerData.put(key, value)); // replicated later, in the background
        return confirmedAt;
    }

    public static void main(String[] args) {
        // Level 1: measure confirmation latency for each mode.
        long syncLatency = synchronousWrite("balance", "100");
        System.out.println("synchronous write confirmed at t=" + syncLatency + ", follower already has it: " + followerData.get("balance"));

        followerData.clear();
        long asyncLatency = asynchronousWrite("balance", "200");
        System.out.println("asynchronous write confirmed at t=" + asyncLatency + " (faster), follower has it yet? " + followerData.get("balance"));

        // Level 2: leader "crashes" before the pending async replication runs.
        System.out.println("--- leader crashes right after confirming the async write ---");
        System.out.println("follower is promoted to leader, but its data is: " + followerData.get("balance") + " (the write '200' is LOST)");
        System.out.println("(the client was told the write succeeded, but it did not survive the crash)");

        // Level 3: semi-synchronous - wait for follower1, replicate to follower2 asynchronously.
        leaderData.put("balance", "300");
        followerData.put("balance", "300"); // follower1: synchronous, done before confirming
        long semiSyncLatency = 10; // same cost as waiting for one follower
        pendingReplication.add(() -> follower2Data.put("balance", "300")); // follower2: async, in the background
        System.out.println("semi-sync write confirmed at t=" + semiSyncLatency + " once follower1 acked");
        System.out.println("follower1 has it already: " + followerData.get("balance") + ", follower2 not yet: " + follower2Data.get("balance"));

        while (!pendingReplication.isEmpty()) pendingReplication.poll().run(); // background replication catches up
        System.out.println("after background replication runs, follower2 has: " + follower2Data.get("balance"));
    }
}
```

**How to run:** save as `SyncVsAsyncReplication.java`, then run `java SyncVsAsyncReplication.java`.

## 6. Walkthrough

1. `synchronousWrite` writes to `leaderData` and `followerData` before returning a confirmation time of `10` — modeling the leader waiting out the round trip to the follower before telling the client "success".
2. `asynchronousWrite` writes only to `leaderData`, confirms immediately at time `1`, and queues the follower's update in `pendingReplication` to run later — the client is told "success" long before the follower actually has the data.
3. The Level 2 section highlights the risk directly: right after the fast asynchronous confirmation, if the leader crashed, `followerData` would still be empty for that key — the client believed the write succeeded, but it is gone.
4. Level 3 models semi-synchronous replication: `follower1` (`followerData`) is updated synchronously before confirming, while `follower2Data`'s update is queued for later, exactly like the fully asynchronous case.
5. Running the queued `pendingReplication` tasks afterward shows `follower2Data` finally catching up — demonstrating that semi-synchronous gives one durable copy immediately, while still keeping additional followers cheap and asynchronous.

## 7. Gotchas & takeaways

> Gotcha: "the write succeeded" from an asynchronous leader means only the leader has it, not that it survived. Applications that assume a confirmed write is permanently safe on any node have made an assumption that asynchronous replication does not actually guarantee — that gap is exactly what caused the "lost" write in Level 2.

- Synchronous replication trades write latency for a durability guarantee: a confirmed write already exists on at least one follower.
- Asynchronous replication trades that guarantee for lower latency and continued availability if a follower is slow or down.
- Semi-synchronous replication is a common middle ground: wait for one follower, replicate to the rest asynchronously.
- Related concepts: [Leader-follower replication](0098-leader-follower-primary-replica-replication.md) (the scheme this choice applies within), [Replication lag & read-your-writes](0102-replication-lag-read-your-writes.md) (the staleness asynchronous replication introduces even without a crash).
