---
card: data-structures
gi: 91
slug: hashmap-internals-buckets-treeify-at-8
title: 'HashMap internals (buckets, treeify at 8)'
---

## 1. What it is

`java.util.HashMap` is Java's standard hash table implementation. Internally, it is an array of buckets, where each bucket is either empty, a linked list of entries (separate chaining), or — once that list grows past a threshold — a red-black tree. Understanding this internal structure explains behavior that would otherwise look mysterious: why iteration order is unpredictable, why a bad `hashCode()` still "works" but is slow, and why performance stays stable even under heavy collisions.

## 2. Why & when

Knowing `HashMap`'s internals matters whenever performance under load is a concern, when writing custom key types, or when explaining *why* `HashMap` behaves the way it does in an interview. It also directly explains topics covered elsewhere in this section — [Load factor & rehashing](0086-load-factor-rehashing.md) and [Collision resolution: separate chaining](0087-collision-resolution-separate-chaining.md) — as concrete implementation choices, not abstract theory.

## 3. Core concept

**What backs it.** An array of `Node<K,V>` bucket heads (`table` internally). Each `Node` holds a key, a value, a cached hash code, and a `next` reference — a plain singly linked list node. `hash(key)` combines `key.hashCode()` with a bit-spreading step (XOR-ing the hash with its own upper bits) before taking it modulo the table size, which improves distribution for hash codes that vary mostly in their high bits.

**Bucket index computation.** `HashMap` uses `(capacity - 1) & hash` instead of `hash % capacity` — capacity is always a power of two, so a bitwise AND with `capacity - 1` is equivalent to modulo, but faster.

**Treeify at 8.** If a single bucket's chain grows to 8 or more nodes, *and* the table's total capacity is at least 64, that bucket converts from a linked list to a red-black tree (`TreeNode`, a subclass of `Node`), bounding worst-case lookup within that bucket to O(log n). If the table is smaller than 64 buckets, `HashMap` instead resizes the whole table first, since a small table with only 8 buckets is more likely the real cause of the crowding, not bad luck.

**Untreeify at 6.** If entries are removed and a treeified bucket's size drops back to 6 or fewer, it converts back to a plain linked list — the tree's bookkeeping overhead is not worth it for a small bucket.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A HashMap bucket array where most buckets hold a short chain or are empty, and one heavily collided bucket has become a red black tree after exceeding 8 entries">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">table[] -- capacity 16 (power of two)</text>
    <rect x="20" y="30" width="34" height="24" fill="#161b22" stroke="#8b949e"/>
    <rect x="58" y="30" width="34" height="24" fill="#0d1117" stroke="#79c0ff"/><text x="75" y="46" fill="#e6edf3" text-anchor="middle" font-size="8">1 node</text>
    <rect x="96" y="30" width="34" height="24" fill="#161b22" stroke="#8b949e"/>
    <text x="180" y="46" fill="#8b949e" font-size="9">... mostly empty or short chains ...</text>
    <rect x="360" y="30" width="60" height="24" fill="#0d1117" stroke="#f0883e"/><text x="390" y="46" fill="#e6edf3" text-anchor="middle" font-size="8">bucket 9</text>
    <circle cx="390" cy="90" r="14" fill="#0d1117" stroke="#f0883e"/>
    <circle cx="360" cy="130" r="14" fill="#161b22" stroke="#8b949e"/>
    <circle cx="420" cy="130" r="14" fill="#161b22" stroke="#8b949e"/>
    <line x1="384" y1="100" x2="368" y2="118" stroke="#8b949e"/>
    <line x1="396" y1="100" x2="412" y2="118" stroke="#8b949e"/>
    <text x="390" y="165" fill="#f0883e" text-anchor="middle" font-size="9">bucket 9: 9+ entries -&gt; treeified into a red-black tree</text>
  </g>
</svg>

Most buckets stay short linked chains; a bucket that grows past 8 entries (with a large-enough table) converts to a balanced tree instead.

## 5. Runnable example

```java
// HashMapInternalsDemo.java
import java.util.HashMap;
import java.util.Map;

public class HashMapInternalsDemo {

    // Basic: iteration order is NOT insertion order -- it follows internal bucket order, which looks arbitrary.
    static void basicLevel() {
        Map<String, Integer> map = new HashMap<>();
        map.put("zebra", 1);
        map.put("apple", 2);
        map.put("mango", 3);
        System.out.println("basic: HashMap iteration order (not insertion order) -> " + map.keySet());
    }

    // Deliberately collide many keys into ONE bucket, to observe the map still working correctly at scale.
    static class SameBucketKey {
        int value;
        SameBucketKey(int value) { this.value = value; }
        @Override public int hashCode() { return 7; } // fixed hash -- forces every instance into the same bucket
        @Override public boolean equals(Object o) { return o instanceof SameBucketKey k && k.value == value; }
        @Override public String toString() { return "K" + value; }
    }

    // Intermediate: push a bucket past the treeify threshold (8), and confirm correctness is unaffected.
    static void intermediateLevel() {
        Map<SameBucketKey, Integer> map = new HashMap<>();
        for (int i = 0; i < 20; i++) map.put(new SameBucketKey(i), i); // far more than 8 -- forces treeification (capacity permitting)

        System.out.println("intermediate: get(K15) after forcing 20 keys into one bucket -> " + map.get(new SameBucketKey(15)));
        System.out.println("intermediate: size (all 20 distinct keys correctly stored) -> " + map.size());
    }

    // Advanced: untreeify -- remove entries back down below 6, confirming the map still behaves correctly either way.
    static void advancedLevel() {
        Map<SameBucketKey, Integer> map = new HashMap<>();
        for (int i = 0; i < 20; i++) map.put(new SameBucketKey(i), i);

        for (int i = 0; i < 15; i++) map.remove(new SameBucketKey(i)); // drop back to 5 remaining entries in that bucket

        System.out.println("advanced: after removing most entries, remaining size -> " + map.size());
        System.out.println("advanced: get(K19) still correct after untreeify -> " + map.get(new SameBucketKey(19)));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `HashMapInternalsDemo.java`, then run `java HashMapInternalsDemo.java`.

## 6. Walkthrough

1. `basicLevel()` inserts three keys and prints the iteration order, which reflects internal bucket order (`hash(key) & (capacity - 1)`), not insertion order — this is the direct, visible consequence of `HashMap`'s bucket-array structure, and why `HashMap` never promises a predictable iteration order.
2. `intermediateLevel()` forces 20 keys into the same bucket via a constant `hashCode()`. Once that bucket's chain exceeds 8 nodes (and the table is at least 64 buckets, which `HashMap` grows into automatically as needed), Java internally converts it to a red-black tree. `get(K15)` still returns the correct value — correctness is unaffected — but internally the lookup now does a tree search instead of a linear scan.
3. `advancedLevel()` removes most of those 20 entries, dropping the crowded bucket's size to `5`, below the untreeify threshold of `6`. `HashMap` converts the bucket back to a plain linked list, since a tree's bookkeeping overhead is no longer justified for so few entries. The map continues to return correct results throughout, regardless of which internal representation the bucket currently uses.

## 7. Gotchas & takeaways

> Gotcha: treeification only happens if the *whole table* has at least 64 buckets — a small table with one badly crowded bucket resizes the entire table first instead, since Java assumes an undersized table (not a bad hash function) is the more likely cause when this happens early. This means the same colliding-key scenario can behave differently depending on how many total entries the map has accumulated so far.

- `HashMap` buckets start as linked lists (separate chaining) and convert to red-black trees once a bucket exceeds 8 entries, in a table of at least 64 buckets.
- Bucket index uses `(capacity - 1) & hash`, relying on capacity always being a power of two, instead of the slower `%` operator.
- Iteration order reflects internal bucket layout, not insertion order — never rely on it.
- A bucket untreeifies back to a linked list if it shrinks to 6 or fewer entries after removals.
- Related concepts: [Collision resolution: separate chaining](0087-collision-resolution-separate-chaining.md), [Worst-case degradation & mitigation](0090-worst-case-degradation-mitigation.md), [HashSet & LinkedHashMap ordering](0092-hashset-linkedhashmap-ordering.md).
