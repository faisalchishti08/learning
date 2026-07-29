---
card: leetcode-patterns
gi: 592
slug: all-o-one-data-structure
title: All O`one Data Structure
---

## 1. What it is

Design an `AllOne` class tracking string keys and integer counts, all starting implicitly at `0`. `inc(key)` increases `key`'s count by one (inserting it at count `1` if new). `dec(key)` decreases `key`'s count by one (removing `key` entirely if its count reaches `0`). `getMaxKey()` returns any key currently holding the maximum count (or `""` if empty). `getMinKey()` returns any key currently holding the minimum count (or `""` if empty). Every method must run in O(1). Example: `inc("a")`, `inc("b")`, `inc("b")`, `getMaxKey()` → `"b"` (count 2), `getMinKey()` → `"a"` (count 1).

## 2. Why & when

This is [LFU Cache](0591-lfu-cache.md)'s `freqToKeys`-grouping idea, pushed further: instead of only needing the *minimum* frequency group, you need O(1) access to **both** the minimum and maximum count groups, and those groups must themselves support O(1) insert/remove of a key as counts change. A doubly linked list of count-buckets, each holding a `LinkedHashSet` of keys at that exact count, with head and tail sentinels pointing at the true min and max buckets, achieves this.

## 3. Core concept

**Key idea:** maintain a doubly linked list of "buckets," each bucket holding a distinct count value and the `LinkedHashSet` of keys currently at that count. The list stays sorted by count from a sentinel `head` (count would decrease going further, i.e. the bucket right after `head` holds the current minimum count) to a sentinel `tail` (the bucket right before `tail` holds the current maximum count). A `HashMap<key, bucket>` gives O(1) lookup of which bucket a key is currently in.

**Steps:**
1. `inc(key)`: if `key` is new, it belongs in a bucket of count `1`. If `key` exists, find its current bucket (count `c`), remove `key` from it, and move it into a bucket of count `c+1`. In both cases, if the target bucket (count `1` or `c+1`) does not exist yet, create it and insert it right after the source bucket in the list (keeping counts sorted); if the source bucket becomes empty after removing `key`, delete it from the list.
2. `dec(key)`: find `key`'s bucket (count `c`). If `c == 1`, remove `key` entirely (its count would become `0`). Otherwise, move it into a bucket of count `c-1`, creating that bucket right before the source bucket if it does not exist. Delete the source bucket if it becomes empty.
3. `getMaxKey()`: if the list is empty (only sentinels), return `""`. Otherwise, return any key from `tail.prev`'s set (any key from the bucket with the highest count).
4. `getMinKey()`: symmetric, using `head.next`'s set.

**Why a linked list of buckets, not a sorted map by count:** a `TreeMap<count, Set<key>>` would give the same logical behavior but its insert/remove is O(log n) due to tree rebalancing. A linked list, ordered by construction (each new bucket is only ever inserted immediately adjacent to a known neighbor bucket), achieves the same ordering guarantee in true O(1), since no search or rebalancing is needed to find where to splice in a new bucket.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A doubly linked list of count buckets between head and tail sentinels, sorted by count">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="60" width="60" height="30" fill="#161b22" stroke="#8b949e" stroke-dasharray="3,2"/><text x="50" y="80" fill="#8b949e" text-anchor="middle" font-size="10">head</text>
    <rect x="110" y="60" width="120" height="40" rx="4" fill="#161b22" stroke="#3fb950"/><text x="170" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">count=1</text><text x="170" y="94" fill="#8b949e" text-anchor="middle" font-size="10">{a}</text>
    <rect x="260" y="60" width="120" height="40" rx="4" fill="#161b22" stroke="#f0883e"/><text x="320" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">count=2</text><text x="320" y="94" fill="#8b949e" text-anchor="middle" font-size="10">{b}</text>
    <rect x="420" y="60" width="60" height="30" fill="#161b22" stroke="#8b949e" stroke-dasharray="3,2"/><text x="450" y="80" fill="#8b949e" text-anchor="middle" font-size="10">tail</text>
    <line x1="80" y1="75" x2="110" y2="75" stroke="#79c0ff" marker-end="url(#a10)"/>
    <line x1="230" y1="75" x2="260" y2="75" stroke="#79c0ff" marker-end="url(#a10)"/>
    <line x1="380" y1="75" x2="420" y2="75" stroke="#79c0ff" marker-end="url(#a10)"/>
    <defs><marker id="a10" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
    <text x="350" y="140" fill="#79c0ff" text-anchor="middle">getMinKey() reads head.next's set; getMaxKey() reads tail.prev's set - both O(1)</text>
  </g>
</svg>

Buckets stay ordered by count purely through where they are spliced into the list — the sentinels make both ends O(1) to read without any search.

## 5. Runnable example

**Level 1 — Brute force.** A single `HashMap<key, count>`; `getMaxKey`/`getMinKey` scan every entry to find the extreme. O(n) per call.

**KEY INSIGHT:** group keys into buckets by their exact count, and keep those buckets in a sorted doubly linked list — since each `inc`/`dec` only ever moves a key to an *adjacent* count, the new bucket's position in the sort order is always known in advance (immediately next to the source bucket), so no search is ever needed to maintain the order.

**Level 2 — Optimal.** Doubly linked list of count-buckets (sentinel `head`/`tail`), each bucket a `LinkedHashSet<String>`, plus `HashMap<key, bucket>` for O(1) key-to-bucket lookup.

**Level 3 — Hardened.** Correctly removes a key entirely when `dec` would bring its count to `0`, and correctly deletes any bucket that becomes empty after a key moves out of it, so `getMinKey`/`getMaxKey` never read a stale empty bucket.

```java
// AllOne.java
import java.util.*;

public class AllOne {

    static class Bucket {
        int count;
        Set<String> keys = new LinkedHashSet<>();
        Bucket prev, next;
        Bucket(int count) { this.count = count; }
    }

    private final Bucket head = new Bucket(Integer.MIN_VALUE);
    private final Bucket tail = new Bucket(Integer.MAX_VALUE);
    private final Map<String, Bucket> keyToBucket = new HashMap<>();

    public AllOne() {
        head.next = tail;
        tail.prev = head;
    }

    private Bucket insertAfter(Bucket node, int count) {
        Bucket bucket = new Bucket(count);
        bucket.prev = node;
        bucket.next = node.next;
        node.next.prev = bucket;
        node.next = bucket;
        return bucket;
    }

    private void removeIfEmpty(Bucket bucket) {
        if (bucket.keys.isEmpty()) {
            bucket.prev.next = bucket.next;
            bucket.next.prev = bucket.prev;
        }
    }

    public void inc(String key) {
        Bucket cur = keyToBucket.get(key);
        if (cur == null) {
            if (head.next.count != 1) {
                insertAfter(head, 1);
            }
            head.next.keys.add(key);
            keyToBucket.put(key, head.next);
            return;
        }
        Bucket next = cur.next;
        if (next.count != cur.count + 1) {
            next = insertAfter(cur, cur.count + 1);
        }
        next.keys.add(key);
        keyToBucket.put(key, next);
        cur.keys.remove(key);
        removeIfEmpty(cur);
    }

    public void dec(String key) {
        Bucket cur = keyToBucket.get(key);
        if (cur.count == 1) {
            keyToBucket.remove(key);
            cur.keys.remove(key);
            removeIfEmpty(cur);
            return;
        }
        Bucket prev = cur.prev;
        if (prev.count != cur.count - 1) {
            prev = insertAfter(cur.prev, cur.count - 1);
        }
        prev.keys.add(key);
        keyToBucket.put(key, prev);
        cur.keys.remove(key);
        removeIfEmpty(cur);
    }

    public String getMaxKey() {
        return tail.prev == head ? "" : tail.prev.keys.iterator().next();
    }

    public String getMinKey() {
        return head.next == tail ? "" : head.next.keys.iterator().next();
    }

    public static void main(String[] args) {
        AllOne allOne = new AllOne();
        allOne.inc("a");
        allOne.inc("b");
        allOne.inc("b");
        System.out.println(allOne.getMaxKey()); // "b", count 2
        System.out.println(allOne.getMinKey()); // "a", count 1
        allOne.dec("b");
        allOne.dec("b");
        System.out.println(allOne.getMaxKey()); // "a", count 1 (b was removed)
    }
}
```

**How to run:** save as `AllOne.java`, then run `java AllOne.java`.

## 6. Walkthrough

Trace `inc("a")`, `inc("b")`, `inc("b")`, `getMaxKey()`:

1. `inc("a")`: `keyToBucket` has no entry for `"a"`. `head.next` is `tail` (count `MAX_VALUE`, not `1`), so insert a new bucket of count `1` right after `head`. Add `"a"` to it. List: `head -> [1:{a}] -> tail`.
2. `inc("b")`: same as above — `head.next` is now the count-`1` bucket, which already has count `1`, so reuse it. Add `"b"`. List: `head -> [1:{a,b}] -> tail`.
3. `inc("b")`: `"b"`'s current bucket has count `1`. Its `next` is `tail` (not count `2`), so insert a new bucket of count `2` right after it. Add `"b"` there; remove `"b"` from the count-`1` bucket (now `{a}`, not empty, kept). List: `head -> [1:{a}] -> [2:{b}] -> tail`.
4. `getMaxKey()`: `tail.prev` is the count-`2` bucket; its set is `{b}`. Return `"b"`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to call `removeIfEmpty` after moving a key out of its old bucket leaves an empty bucket sitting in the list — `getMinKey`/`getMaxKey` would then read from that empty bucket's `keys.iterator().next()`, throwing `NoSuchElementException` instead of returning the correct adjacent bucket's key.

- Signal: "O(1) access to both the current min and max of a dynamically changing frequency count" is the doubly-linked-list-of-buckets signal — one step beyond a single min-or-max-only structure.
- New buckets are always inserted adjacent to a known bucket (never requiring a search), which is what keeps insertion O(1) instead of O(log n).
- Related problems: LFU Cache (the same bucket-by-count idea, but only needing the minimum, not both extremes).
