---
card: system-design
gi: 52
slug: hot-keys-key-distribution
title: Hot keys & key distribution
---

## 1. What it is

A **hot key** is a single cache key that receives a disproportionate share of traffic compared to every other key — a celebrity's profile, a viral post, a flash-sale product. **Key distribution** is how evenly (or unevenly) requests spread across all the keys in a cache; a hot key is an extreme case of uneven distribution, where one shard or node absorbs far more load than the others.

## 2. Why & when

Caches are usually scaled by sharding keys across many nodes, on the assumption that traffic spreads roughly evenly, so each node gets a fair share. A hot key breaks that assumption: whichever single node owns that key gets overwhelmed, even while every other node sits idle, and adding more nodes does not help because the same one node still owns that same one key. Recognize this whenever a cache metric shows one node's CPU or network far above the others while total load looks reasonable on average.

## 3. Core concept

**Why sharding alone does not fix a hot key:** sharding (via consistent hashing or similar) spreads *different* keys to *different* nodes, but every request for the *same* key always maps to the *same* node, no matter how many nodes you add. A hot key is a single-key problem, and adding capacity elsewhere does not add capacity for that one key.

**Mitigation: local (in-process) caching.** Put a very short-lived copy of the hot key's value directly in the application server's own memory, so a large fraction of requests never even reach the shared cache tier for that key.

**Mitigation: key replication.** Store the hot key's value on multiple cache nodes under variant keys (`product:99#0`, `product:99#1`, `product:99#2`), and have the application pick a variant at random (or round-robin) on each read, spreading the load for that one logical key across several physical nodes.

**Mitigation: request coalescing.** When many concurrent requests miss the same key at once, let only the first one trigger a database load; the rest wait on that same in-flight result instead of each independently hitting the database. This overlaps with the thundering-herd problem covered later in this section.

## 4. Diagram

```
Without replication (one node owns the key):
  1000 req/s for "product:99" ---> all routed to Node B (owner) ---> Node B overloaded
  Node A: idle          Node C: idle

With key replication (3 variants spread across nodes):
  requests randomly pick a variant:
  "product:99#0" -> Node A     "product:99#1" -> Node B     "product:99#2" -> Node C
  1000 req/s split ~333/333/334 across three nodes, none overloaded
```
*Caption: replicating one hot key under several variant keys spreads its load across nodes that consistent hashing alone would never touch for that key.*

## 5. Runnable example

**Level 1 — Basic.** Show that a single key always maps to the same shard, concentrating all its traffic on one node.

**Level 2 — Key replication.** Spread one logical key across several variant keys and route requests to them round-robin.

**Level 3 — Load measurement.** Count requests per underlying node to show replication balances the previously concentrated load.

```java
// HotKeys.java
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

public class HotKeys {

    static final int NODE_COUNT = 3;

    static int shardFor(String key) {
        return Math.floorMod(key.hashCode(), NODE_COUNT); // plain sharding
    }

    public static void main(String[] args) {
        Map<Integer, AtomicInteger> loadWithoutReplication = new HashMap<>();
        for (int i = 0; i < NODE_COUNT; i++) loadWithoutReplication.put(i, new AtomicInteger());

        // Level 1: every request for the same key always hits the same node.
        for (int i = 0; i < 900; i++) {
            int node = shardFor("product:99");
            loadWithoutReplication.get(node).incrementAndGet();
        }
        System.out.println("without replication, load per node: " + loadWithoutReplication);

        // Level 2 & 3: replicate the hot key under 3 variants, round-robin across them.
        Map<Integer, AtomicInteger> loadWithReplication = new HashMap<>();
        for (int i = 0; i < NODE_COUNT; i++) loadWithReplication.put(i, new AtomicInteger());

        int variantCount = 3;
        for (int i = 0; i < 900; i++) {
            int variant = i % variantCount; // round-robin across variants
            String variantKey = "product:99#" + variant;
            int node = shardFor(variantKey);
            loadWithReplication.get(node).incrementAndGet();
        }
        System.out.println("with replication, load per node: " + loadWithReplication);
    }
}
```

**How to run:** save as `HotKeys.java`, then run `java HotKeys.java`.

## 6. Walkthrough

1. `shardFor("product:99")` always returns the same node number, because it is a pure function of the same fixed string — this models how consistent hashing always routes one key to one owner.
2. The loop of 900 requests for the plain key therefore adds every single count to one entry in `loadWithoutReplication`, leaving the others at zero — one node absorbs all 900 requests.
3. In the replicated version, each request first picks a variant (`0`, `1`, or `2`) round-robin, then hashes the variant string, which — because the variant suffix changes the string — can land on a different node than the plain key would.
4. Requests are now split roughly evenly across `loadWithReplication`'s three entries (300 each, since the round-robin assignment guarantees an even split across variants, and each variant is a fixed string that hashes to one node).
5. The same 900 logical requests for `"product:99"` now spread across multiple physical nodes, instead of concentrating on one.

## 7. Gotchas & takeaways

> Gotcha: replicating a key means every write to it must update all variants, or reads can return different variants with different values; replication trades write complexity and eventual-consistency risk for read scalability, so only apply it to keys that are read far more than they are written.

- A hot key is invisible to per-node load averages but very visible in per-node maximums — always look for outlier nodes, not just totals.
- Sharding balances load across *different* keys; it does nothing for one key that is disproportionately hot.
- Related concepts: [Thundering herd / cache stampede & mitigation](0053-thundering-herd-cache-stampede-mitigation.md) (a related but distinct problem — many keys expiring together, versus one key being permanently hot), [IP-hash & consistent-hash routing](0039-ip-hash-consistent-hash-routing.md) (the sharding mechanism hot keys break).
