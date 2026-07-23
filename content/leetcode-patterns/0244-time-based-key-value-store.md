---
card: leetcode-patterns
gi: 244
slug: time-based-key-value-store
title: Time Based Key-Value Store
---

## 1. What it is

Design a class `TimeMap` that stores multiple values for the same key at different timestamps. `set(key, value, timestamp)` stores a value at a given timestamp (timestamps are strictly increasing per key). `get(key, timestamp)` returns the value set for `key` at the LARGEST timestamp that is less than or equal to the given `timestamp`; if none exists, return `""`. Example: `set("foo", "bar", 1)`, `get("foo", 1)` → `"bar"`, `get("foo", 3)` → `"bar"` (most recent value at or before time 3), `get("foo", 0)` → `""` (nothing set yet).

## 2. Why & when

Because `set` calls for the same key always arrive with strictly increasing timestamps, the list of `(timestamp, value)` pairs for any key is automatically sorted by construction, with no extra sorting step needed. Use this shape whenever a design problem stores time-ordered data per key and needs a "most recent value at or before a given time" lookup — a very common building block in versioned or time-travel data stores.

## 3. Core concept

**Key idea:** for each key, keep a list of `(timestamp, value)` pairs in the order they are set (already sorted, since timestamps strictly increase). `get` becomes a binary search for the RIGHTMOST timestamp that is `<= timestamp`, reusing the same "find last occurrence" boundary search used in Find First and Last Position of Element in Sorted Array.

**Steps:**
1. `set(key, value, timestamp)`: append `(timestamp, value)` to the list stored under `key` in a `HashMap<String, List<Pair>>` (create the list if `key` is new).
2. `get(key, timestamp)`: if `key` has no entries, return `""`.
3. Binary search the key's list for the largest index where `list[index].timestamp <= timestamp`.
4. If no such index exists (even the earliest timestamp is later than the query), return `""`.
5. Otherwise, return the value at that index.

**Why it is correct:** because timestamps for a given key are strictly increasing, the stored list is always sorted by timestamp with no gaps to worry about. "Find the last index where `timestamp <= query`" is exactly the same monotonic boundary search as `findLast` in Find First and Last Position, just applied to timestamps instead of array values.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Key foo has entries at timestamps 1 and 4, get at timestamp 3 finds the entry at timestamp 1">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">key "foo": [(t=1, "bar"), (t=4, "bar2")]</text>
    <rect x="10" y="30" width="80" height="24" fill="#161b22" stroke="#30363d"/><text x="50" y="47" text-anchor="middle" font-size="9">t=1, bar</text>
    <rect x="100" y="30" width="90" height="24" fill="#161b22" stroke="#30363d"/><text x="145" y="47" text-anchor="middle" font-size="9">t=4, bar2</text>
    <text x="10" y="80">get("foo", 3): search for largest t &lt;= 3</text>
    <rect x="10" y="90" width="80" height="24" fill="#3fb950"/><text x="50" y="107" fill="#0d1117" text-anchor="middle" font-size="9">t=1 matches</text>
    <text x="10" y="135">returns "bar" (t=4 is too late for query time 3)</text>
  </g>
</svg>

The per-key list is always sorted, so a boundary binary search finds the most recent value at or before the query time.

## 5. Runnable example

```java
// TimeBasedKeyValueStore.java
import java.util.*;

public class TimeBasedKeyValueStore {

    // Level 1 -- Brute force: for get(key, timestamp), scan the whole
    // list for `key` linearly, tracking the best (largest, still <=
    // timestamp) entry seen. Correct, but O(n) per get call.

    // KEY INSIGHT: the list per key is already sorted by timestamp
    // (strictly increasing on every set call), so "largest timestamp
    // <= query" is a boundary binary search, not a linear scan.

    // Level 2 -- Optimal: HashMap of sorted lists + binary search.
    static class Entry {
        int timestamp;
        String value;
        Entry(int timestamp, String value) { this.timestamp = timestamp; this.value = value; }
    }

    private final Map<String, List<Entry>> store = new HashMap<>();

    public void set(String key, String value, int timestamp) {
        store.computeIfAbsent(key, k -> new ArrayList<>()).add(new Entry(timestamp, value));
    }

    public String get(String key, int timestamp) {
        List<Entry> entries = store.get(key);
        if (entries == null || entries.isEmpty()) return "";

        int lo = 0, hi = entries.size() - 1, result = -1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (entries.get(mid).timestamp <= timestamp) {
                result = mid;
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
        return result == -1 ? "" : entries.get(result).value;
    }

    // Level 3 -- Hardened: uses a plain lo<=hi search with a separate
    // `result` tracker (instead of the lo==hi convergence style),
    // which reads clearly when "no valid index" (query earlier than
    // every stored timestamp) must map to a distinct "" return value.

    public static void main(String[] args) {
        TimeBasedKeyValueStore timeMap = new TimeBasedKeyValueStore();
        timeMap.set("foo", "bar", 1);
        System.out.println(timeMap.get("foo", 1));
        // bar
        System.out.println(timeMap.get("foo", 3));
        // bar
        timeMap.set("foo", "bar2", 4);
        System.out.println(timeMap.get("foo", 4));
        // bar2
        System.out.println(timeMap.get("foo", 0));
        // (empty string)
    }
}
```

**How to run:** `java TimeBasedKeyValueStore.java`

## 6. Walkthrough

After `set("foo", "bar", 1)` and `set("foo", "bar2", 4)`, `store["foo"] = [(1,"bar"), (4,"bar2")]`.

Trace `get("foo", 3)`, `lo=0, hi=1`:

| lo | hi | mid | entries[mid].timestamp | <= 3? | action |
|---|---|---|---|---|---|
| 0 | 1 | 0 | 1 | yes | result = 0, lo = 1 |
| 1 | 1 | 1 | 4 | no | hi = 0 |
| 1 | 0 | — | loop ends (lo > hi) | — | return entries[0].value = "bar" |

`get("foo", 0)` finds no entry with `timestamp <= 0`, so `result` stays `-1` and the method returns `""`. Time complexity is O(log n) per `get` call and O(1) amortized per `set` call, where `n` is the number of entries stored for that key. Space is O(total entries stored).

## 7. Gotchas & takeaways

> Gotcha: forgetting to record `result` and keep searching right (`lo = mid + 1`) after finding a valid `timestamp <= query` at `mid` would return the FIRST valid match instead of the LAST (most recent) one — the search must keep looking for an even later valid timestamp before settling.

- This design reuses the exact "last index where a monotonic condition holds" boundary search from Find First and Last Position of Element in Sorted Array, applied to timestamps instead of array values.
- Relying on the problem's guarantee that timestamps strictly increase per key avoids any need to sort the list after each `set` call.
- Related problems: Find First and Last Position of Element in Sorted Array (the same boundary search technique), Search Insert Position (another "closest valid index" binary search).
