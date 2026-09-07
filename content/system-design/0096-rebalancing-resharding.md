---
card: system-design
gi: 96
slug: rebalancing-resharding
title: Rebalancing & resharding
---

## 1. What it is

**Rebalancing** is the process of moving data between existing shards so that load is spread more evenly. **Resharding** is the broader process of changing the sharding scheme itself — usually adding or removing shards — and moving the affected data to match the new scheme. Both are operational processes that happen while the system stays live and serving traffic: you cannot simply stop the database to move data around.

## 2. Why & when

A system needs rebalancing or resharding whenever its shards drift out of balance: one shard grows faster than the rest (organic growth), a hot spot develops (see [hot spots & skew](0095-hot-spots-skew.md)), or the total dataset outgrows the current shard count and needs more shards added. The trigger is usually a monitoring alert: one shard's storage, CPU, or request rate is far above the others, or a shard is approaching a hard capacity limit.

## 3. Core concept

- **Live migration:** data must move from its old shard to its new shard while both reads and writes for that data keep working, usually via a copy-then-cutover process: copy existing rows to the new shard, then start dual-writing new changes to both shards, then switch reads to the new shard, then stop writing to the old one.
- **Range splitting:** under [range-based sharding](0090-range-based-sharding.md), rebalancing usually means splitting one large range into two smaller ranges, each becoming its own shard.
- **Consistent hashing minimizes the blast radius:** under [consistent hashing](0094-consistent-hashing-virtual-nodes.md), adding a shard only moves the keys in the ring segment next to it — a small, bounded migration, not a full reshuffle.
- **Directory updates:** under [directory-based sharding](0092-directory-based-sharding.md), rebalancing a single key is just a one-row update in the directory, followed by moving that one key's data.
- **Throttling the migration:** moving data generates extra load on both the source and destination shard, so migrations are usually throttled (moved in small batches) to avoid overwhelming either shard mid-migration.
- **Verification before cutover:** the new shard's copy of the data is checked against the old shard before traffic switches over, to catch any missed or corrupted rows.

## 4. Diagram

```
Rebalancing timeline for moving key range [X, Y) from Shard A to new Shard B:

  1. COPY:        Shard A (source, live) ---copies rows [X,Y)---> Shard B (new)
                  reads/writes still go to Shard A only

  2. DUAL-WRITE:  new writes to [X,Y) go to BOTH Shard A and Shard B
                  reads still go to Shard A only

  3. CUTOVER:     reads for [X,Y) switch to Shard B
                  writes for [X,Y) switch to Shard B only

  4. CLEANUP:     Shard A drops its now-unused copy of [X,Y)
```
*Caption: a live migration moves through copy, dual-write, cutover, and cleanup, so no read or write is ever lost mid-move.*

## 5. Runnable example

**Level 1 — Basic.** Model two shards and copy a key range from one to the other.

**Level 2 — Dual-write phase.** During migration, write to both shards; read from the old shard only.

**Level 3 — Cutover.** Switch reads and writes to the new shard, then clean up the old copy.

```java
// Rebalancing.java
import java.util.*;

public class Rebalancing {

    static Map<String, Integer> shardA = new HashMap<>();
    static Map<String, Integer> shardB = new HashMap<>();
    static boolean dualWriteActive = false;
    static boolean cutoverDone = false;

    static void write(String key, int value) {
        if (!cutoverDone) shardA.put(key, value); // Shard A is still the writer of record
        if (dualWriteActive || cutoverDone) shardB.put(key, value); // mirror to Shard B once dual-write starts
    }

    static Integer read(String key) {
        return cutoverDone ? shardB.get(key) : shardA.get(key); // reads follow whichever shard is authoritative
    }

    public static void main(String[] args) {
        // Level 1: initial state and copy phase - Shard A has existing data, bulk-copy it to Shard B.
        shardA.put("k1", 100);
        shardA.put("k2", 200);
        shardB.putAll(shardA); // one-time bulk copy of existing rows
        System.out.println("after copy phase, shardB has: " + shardB);

        // Level 2: dual-write phase - new writes go to both shards; reads still come from Shard A.
        dualWriteActive = true;
        write("k3", 300);
        System.out.println("after dual-write of k3 -> shardA: " + shardA + ", shardB: " + shardB);
        System.out.println("read during dual-write still comes from shardA: k3 = " + read("k3"));

        // Level 3: cutover - switch reads and writes to Shard B, then clean up Shard A.
        cutoverDone = true;
        write("k4", 400); // this write now only lands on shardB
        System.out.println("read after cutover comes from shardB: k4 = " + read("k4"));
        System.out.println("k1 still readable from shardB after cutover: " + read("k1"));

        shardA.clear(); // cleanup: old shard's copy is no longer needed
        System.out.println("shardA cleaned up: " + shardA + " (shardB is now sole owner)");
    }
}
```

**How to run:** save as `Rebalancing.java`, then run `java Rebalancing.java`.

## 6. Walkthrough

1. The program starts with `shardA` holding two existing rows, then bulk-copies them into `shardB` — modeling the initial COPY phase of the migration.
2. `dualWriteActive` is set to `true`, and `write("k3", 300)` lands in both `shardA` and `shardB` — the DUAL-WRITE phase, where the migration keeps both copies current.
3. `read("k3")` still returns from `shardA`, since `cutoverDone` is still `false` — reads have not moved yet, only writes are being mirrored.
4. `cutoverDone` flips to `true`, and `write("k4", 400)` now lands only in `shardB` (the `if (!cutoverDone)` guard skips `shardA`) — this is the CUTOVER, where Shard B becomes authoritative.
5. `read("k4")` and `read("k1")` both now come from `shardB`, confirming the switch is complete; `shardA.clear()` models the final CLEANUP step, discarding the old shard's now-redundant copy.

## 7. Gotchas & takeaways

> Gotcha: skipping the dual-write phase and cutting over reads and writes in one atomic step looks simpler, but any write that arrives during the brief copy-to-cutover window is silently lost if it only reached the old shard. The dual-write phase exists specifically to close that window — never remove it to "save a step".

- Rebalancing moves data between existing shards; resharding changes the shard count or scheme itself and moves whatever data that implies.
- A live migration typically goes through copy, dual-write, cutover, and cleanup, so no read or write is ever unavailable or lost mid-move.
- The specific mechanics differ by sharding scheme: range splitting for range-based, a bounded ring-segment move for consistent hashing, a one-row update for directory-based.
- Related concepts: [Consistent hashing & virtual nodes](0094-consistent-hashing-virtual-nodes.md) (minimizes how much data a resharding event must move), [Hot spots & skew](0095-hot-spots-skew.md) (the usual trigger for rebalancing).
