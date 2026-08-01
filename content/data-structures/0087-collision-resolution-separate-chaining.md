---
card: data-structures
gi: 87
slug: collision-resolution-separate-chaining
title: 'Collision resolution: separate chaining'
---

## 1. What it is

A **collision** happens when two different keys hash to the same bucket. **Separate chaining** resolves this by letting each bucket hold a small collection — usually a linked list, or in Java's `HashMap`, a linked list that upgrades to a balanced tree once it grows large enough — of every entry that landed there. Instead of one value per bucket, each bucket can hold many.

## 2. Why & when

Collisions are unavoidable in any real hash table: even with a great hash function, the pigeonhole principle guarantees collisions once you have more possible keys than buckets. Separate chaining is one of the two standard strategies for handling them (the other is open addressing, covered separately) — it is the strategy Java's own `HashMap` uses, so understanding it explains what actually happens inside `HashMap` under the hood.

## 3. Core concept

**How the operation transforms the structure.** Each bucket starts empty, or holds a reference to a small linked list. Inserting a key: compute its hash, find its bucket, then walk that bucket's list checking `equals()` against each existing entry — if found, overwrite the value; if not, append a new node. Looking up a key: same bucket computation, then walk the list checking `equals()` until found or the list ends.

**Why this works.** As long as the hash function distributes keys well, each bucket's list stays short — close to `size / bucketCount` entries on average (the load factor). Searching a short list is fast in practice, even though it is technically O(k) for a list of length `k`, not O(1) — the O(1) *average* case comes from `k` staying small as long as load factor stays low.

**Worst case, and why Java treeifies.** If many keys collide into the same bucket (a bad hash function, or a hostile adversary crafting colliding keys), that one bucket's list can grow to hold most or all of the table's entries, degrading lookups in that bucket to O(n). Java's `HashMap` mitigates this: once a single bucket's chain grows past 8 entries (and the table is large enough), it converts that bucket from a linked list to a red-black tree, bounding worst-case lookup in that bucket to O(log n) instead of O(n).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bucket array where bucket 2 holds a chain of three colliding entries linked together, while other buckets hold zero or one entry">
  <g font-family="sans-serif" font-size="11">
    <rect x="20" y="20" width="46" height="26" fill="#161b22" stroke="#8b949e"/><text x="43" y="37" fill="#8b949e" text-anchor="middle" font-size="8">bucket 0</text>
    <rect x="76" y="20" width="46" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="99" y="37" fill="#e6edf3" text-anchor="middle" font-size="8">"x"</text>
    <rect x="132" y="20" width="46" height="26" fill="#0d1117" stroke="#f0883e"/><text x="155" y="37" fill="#e6edf3" text-anchor="middle" font-size="8">"a"</text>
    <rect x="132" y="60" width="46" height="26" fill="#0d1117" stroke="#f0883e"/><text x="155" y="77" fill="#e6edf3" text-anchor="middle" font-size="8">"b"</text>
    <rect x="132" y="100" width="46" height="26" fill="#0d1117" stroke="#f0883e"/><text x="155" y="117" fill="#e6edf3" text-anchor="middle" font-size="8">"c"</text>
    <line x1="155" y1="46" x2="155" y2="60" stroke="#f0883e" marker-end="url(#ch)"/>
    <line x1="155" y1="86" x2="155" y2="100" stroke="#f0883e" marker-end="url(#ch)"/>
    <defs><marker id="ch" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker></defs>
    <text x="155" y="145" fill="#f0883e" text-anchor="middle" font-size="9">bucket 2: "a", "b", "c" all collided here -- chained together</text>
    <text x="43" y="60" fill="#8b949e" text-anchor="middle" font-size="9">empty</text>
  </g>
</svg>

Bucket `2` holds three colliding entries as a linked chain; a lookup for `"c"` walks past `"a"` and `"b"` first, checking `equals()` at each step.

## 5. Runnable example

```java
// SeparateChainingHashTable.java
import java.util.LinkedList;

public class SeparateChainingHashTable<K, V> {
    private static class Entry<K, V> {
        K key; V value;
        Entry(K key, V value) { this.key = key; this.value = value; }
    }

    private LinkedList<Entry<K, V>>[] buckets;
    private int size = 0;

    @SuppressWarnings("unchecked")
    SeparateChainingHashTable(int capacity) {
        buckets = new LinkedList[capacity];
        for (int i = 0; i < capacity; i++) buckets[i] = new LinkedList<>();
    }

    private int bucketIndex(K key) {
        return Math.floorMod(key.hashCode(), buckets.length); // floorMod handles negative hash codes correctly
    }

    void put(K key, V value) {
        LinkedList<Entry<K, V>> chain = buckets[bucketIndex(key)];
        for (Entry<K, V> e : chain) {
            if (e.key.equals(key)) { e.value = value; return; } // overwrite existing key
        }
        chain.add(new Entry<>(key, value)); // new key: append to the chain
        size++;
    }

    V get(K key) {
        LinkedList<Entry<K, V>> chain = buckets[bucketIndex(key)];
        for (Entry<K, V> e : chain) {
            if (e.key.equals(key)) return e.value; // walk the chain checking equals()
        }
        return null;
    }

    // Basic: put and get with no collisions expected.
    static void basicLevel() {
        SeparateChainingHashTable<String, Integer> table = new SeparateChainingHashTable<>(8);
        table.put("apple", 1);
        table.put("banana", 2);
        System.out.println("basic: get(\"apple\") -> " + table.get("apple"));
        System.out.println("basic: get(\"banana\") -> " + table.get("banana"));
        System.out.println("basic: get(\"missing\") -> " + table.get("missing"));
    }

    // Intermediate: force a collision with a tiny capacity, and confirm both keys are still found correctly.
    static void intermediateLevel() {
        SeparateChainingHashTable<Integer, String> table = new SeparateChainingHashTable<>(1); // 1 bucket -- every key collides
        table.put(1, "one");
        table.put(2, "two");
        table.put(3, "three");
        System.out.println("intermediate: all keys forced into bucket 0, still correct -> "
            + table.get(1) + ", " + table.get(2) + ", " + table.get(3));
    }

    // Advanced: overwrite an existing key, and confirm size only counts distinct keys.
    static void advancedLevel() {
        SeparateChainingHashTable<String, Integer> table = new SeparateChainingHashTable<>(4);
        table.put("count", 1);
        table.put("count", 2); // overwrite, not a new chain entry
        table.put("other", 3);
        System.out.println("advanced: get(\"count\") after overwrite -> " + table.get("count"));
        System.out.println("advanced: size (distinct keys only) -> " + table.size);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SeparateChainingHashTable.java`, then run `java SeparateChainingHashTable.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `"apple"` and `"banana"` into distinct (or at least non-colliding, at this capacity) buckets. `get` computes each key's bucket, walks that bucket's short chain, and finds the match via `equals()`.
2. `intermediateLevel()` uses a table with only `1` bucket, forcing every key into the same chain. `put(1, ...)`, `put(2, ...)`, `put(3, ...)` all append to bucket `0`'s list. `get(2)` walks the chain — checks entry `1` (no match), then entry `2` (match) — and returns `"two"` correctly, just slower than it would be with more buckets, since it is now a full linear scan.
3. `advancedLevel()` calls `put("count", 1)` then `put("count", 2)` — the second call finds `"count"` already in the chain via `equals()`, and overwrites its value in place rather than appending a duplicate node. `size` correctly stays at `2` (`"count"` and `"other"`), confirming overwrites do not inflate the count.

## 7. Gotchas & takeaways

> Gotcha: separate chaining's worst case (all keys colliding into one bucket) degrades to O(n) per operation, exactly like a single linked list — this is why hash function quality (see [Hash functions & desirable properties](0085-hash-functions-desirable-properties.md)) and Java's treeify-at-8 mitigation both exist: to keep that worst case from actually happening in practice.

- Separate chaining resolves collisions by letting each bucket hold a small collection (usually a linked list) of every entry that hashed there.
- Lookup cost within a bucket is proportional to that bucket's chain length — short chains (low load factor, good hash function) keep this close to O(1).
- Java's `HashMap` converts a bucket's chain to a balanced tree once it exceeds 8 entries, bounding worst-case lookup to O(log n) in that bucket.
- Related concepts: [Collision resolution: open addressing (linear/quadratic/double)](0088-collision-resolution-open-addressing-linear-quadratic-double.md), [HashMap internals (buckets, treeify at 8)](0091-hashmap-internals-buckets-treeify-at-8.md).
