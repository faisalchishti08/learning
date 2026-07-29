---
card: leetcode-patterns
gi: 585
slug: snapshot-array
title: Snapshot Array
---

## 1. What it is

Design a `SnapshotArray` of a fixed length, initialized so every index starts at `0`. `set(index, val)` updates a value. `snap()` takes a snapshot of the entire array's current state and returns the snapshot's ID (starting at `0`, incrementing by `1` each call). `get(index, snapId)` returns the value at `index` **as it was at the time of that snapshot**. Example: `SnapshotArray(3)`, `set(0,5)`, `snap()` → `0`, `set(0,6)`, `get(0,0)` → `5` (the value at index 0 when snapshot 0 was taken).

## 2. Why & when

The brute-force idea — copy the entire array on every `snap()` call — is O(length) per snapshot, which is too slow if `snap()` is called many times on a large array while only a few indices ever actually change. The key realization is that most indices never change between snapshots, so storing a full copy wastes almost all of that work; instead, record a **history of changes per index**, and look up the right historical value only when asked.

## 3. Core concept

**Key idea:** for each index, keep a list of `(snapId, value)` pairs, recorded only when that index is actually modified with `set`. `get(index, snapId)` then needs the most recent recorded value at or before `snapId` — found with binary search, since each index's history list is naturally sorted by `snapId` (values are appended in increasing snapshot order).

**Steps:**
1. Maintain `snapId` as a counter, starting at `0`.
2. `set(index, val)`: append `(snapId, val)` to `history[index]`. (If the current `snapId` already has an entry for this index — multiple `set` calls before the next `snap` — overwrite it instead of appending a duplicate, since only the latest value before the next snapshot matters.)
3. `snap()`: return the current `snapId`, then increment it.
4. `get(index, snapId)`: binary search `history[index]` for the entry with the largest recorded `snapId` that is `<=` the requested `snapId`. Return its value, or `0` if no entry exists at or before that point (the index was never set before that snapshot).

**Why binary search, not a linear scan:** each index's history can grow up to the total number of `set` calls on that index across the array's lifetime. A linear scan for every `get` would be O(history length); since the history is sorted by `snapId`, binary search finds the answer in O(log(history length)) instead.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Per-index history list of (snapId, value) pairs, binary searched to answer a get at an earlier snapshot">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#8b949e" font-size="11">history[0]:</text>
    <rect x="20" y="30" width="90" height="35" fill="#161b22" stroke="#3fb950"/><text x="65" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">(snap0, 5)</text>
    <rect x="120" y="30" width="90" height="35" fill="#161b22" stroke="#30363d"/><text x="165" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">(snap2, 9)</text>
    <rect x="220" y="30" width="90" height="35" fill="#161b22" stroke="#30363d"/><text x="265" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">(snap5, 1)</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">get(0, 3): binary search finds the entry with the largest snapId &lt;= 3 -&gt; (snap2, 9)</text>
    <text x="350" y="140" fill="#8b949e" text-anchor="middle" font-size="11">only indices actually set() are recorded - no full-array copy per snapshot</text>
  </g>
</svg>

Each index keeps its own sparse, sorted history — `get` finds the last change at or before the requested snapshot with a binary search, never scanning the whole array.

## 5. Runnable example

**Level 1 — Brute force.** On every `snap()`, copy the entire array into a saved list of arrays; `get(index, snapId)` is then O(1), but `snap()` is O(length), wasteful when only a few indices ever change between snapshots.

**KEY INSIGHT:** record changes only where they happen (per index, per `set` call) instead of copying everything on every snapshot — `snap()` becomes O(1), and `get` pays a small O(log(history length)) cost only for indices that were actually modified.

**Level 2 — Optimal.** `List<int[]>[] history`, one sorted list per index, binary search on `get`.

**Level 3 — Hardened.** Handles multiple `set` calls on the same index within the same snapshot (overwrite, not duplicate) and indices never touched by `set` (default to `0`).

```java
// SnapshotArray.java
import java.util.*;

public class SnapshotArray {

    private final List<int[]>[] history; // each entry: [snapId, value]
    private int snapId;

    @SuppressWarnings("unchecked")
    public SnapshotArray(int length) {
        history = new List[length];
        for (int i = 0; i < length; i++) history[i] = new ArrayList<>();
        snapId = 0;
    }

    public void set(int index, int val) {
        List<int[]> h = history[index];
        if (!h.isEmpty() && h.get(h.size() - 1)[0] == snapId) {
            h.get(h.size() - 1)[1] = val; // overwrite within the same pending snapshot
        } else {
            h.add(new int[]{snapId, val});
        }
    }

    public int snap() {
        return snapId++;
    }

    public int get(int index, int snapIdQuery) {
        List<int[]> h = history[index];
        int lo = 0, hi = h.size() - 1, result = 0;
        while (lo <= hi) {
            int mid = (lo + hi) / 2;
            if (h.get(mid)[0] <= snapIdQuery) {
                result = h.get(mid)[1];
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        return result;
    }

    public static void main(String[] args) {
        SnapshotArray arr = new SnapshotArray(3);
        arr.set(0, 5);
        System.out.println(arr.snap()); // 0
        arr.set(0, 6);
        System.out.println(arr.get(0, 0)); // 5, value at index 0 when snapshot 0 was taken
    }
}
```

**How to run:** save as `SnapshotArray.java`, then run `java SnapshotArray.java`.

## 6. Walkthrough

Trace `set(0,5)`, `snap()`, `set(0,6)`, `get(0,0)`:

1. `set(0,5)`: `history[0]` is empty, so append `[0,5]` (current `snapId=0`). `history[0] = [[0,5]]`.
2. `snap()`: return `0`, then `snapId` becomes `1`.
3. `set(0,6)`: `history[0]`'s last entry has `snapId=0`, which is not equal to the current `snapId=1`, so append `[1,6]`. `history[0] = [[0,5],[1,6]]`.
4. `get(0,0)`: binary search `history[0]` for the largest entry with `snapId <= 0`. Entry `[0,5]` qualifies (`0 <= 0`); entry `[1,6]` does not (`1 > 0`). Return `5`.

The value `6` (set after snapshot `0` was taken) correctly does not affect what snapshot `0` reports.

## 7. Gotchas & takeaways

> Gotcha: appending a new `(snapId, value)` entry on every `set` call, even when several `set` calls happen on the same index before the next `snap()`, wastes memory and complicates the binary search with duplicate `snapId`s — overwrite the last entry instead when its `snapId` matches the current pending `snapId`.

- Signal: "take a snapshot of a large structure, then query its historical state" with far more reads/writes than snapshots is a per-element sparse-history-plus-binary-search signal, not a full-copy signal.
- Binary search on each index's history works because entries are appended in strictly increasing `snapId` order.
- Related problems: Time Based Key-Value Store (an almost identical binary-search-over-timestamped-history idea, keyed by string instead of array index).
