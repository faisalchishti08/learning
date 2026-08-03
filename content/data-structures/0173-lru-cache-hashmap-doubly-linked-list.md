---
card: data-structures
gi: 173
slug: lru-cache-hashmap-doubly-linked-list
title: LRU cache (HashMap + doubly linked list)
---

## 1. What it is

An **LRU (Least Recently Used) cache** holds a fixed number of items, and when it is full, evicts the item that has gone the longest without being accessed. Combining a hash map with a [doubly linked list](0046-doubly-linked-list.md) gives `O(1)` for every operation: get, put, and eviction.

## 2. Why & when

Use an LRU cache when memory is limited and you want to keep the "most useful" items — the ones accessed recently are statistically likely to be accessed again soon (temporal locality). A plain `HashMap` alone gives `O(1)` lookup but has no notion of access order, so it cannot decide what to evict without an `O(n)` scan. A plain linked list alone gives ordering but `O(n)` lookup. Combining them gets the best of both.

## 3. Core concept

**The shape.** A `HashMap<Key, Node>` for `O(1)` lookup, where each `Node` also lives in a doubly linked list ordered by recency: the **head** end holds the most recently used item, the **tail** end holds the least recently used item.

**The invariant.** Every access (`get` or `put`) on an existing key must move that key's node to the head of the list — "just used" always means "move to the front." When the cache exceeds capacity, the node at the **tail** is evicted, since it is, by the invariant, the least recently used.

**Why both pieces are necessary.** The hash map gives `O(1)` access to any node by key, skipping any linked-list traversal. The doubly linked list lets you unlink and reinsert a node in `O(1)`, because with both `prev` and `next` pointers, removing a node from the middle of the list needs no traversal to find its neighbors — you already have direct references to them.

**Why doubly linked, not singly linked.** Moving an arbitrary node to the head requires detaching it from its current position first: `node.prev.next = node.next` and `node.next.prev = node.prev`. A singly linked list would need to walk from the head to find the node *before* the one being removed, costing `O(n)` — defeating the whole point.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An LRU cache with a hash map pointing into a doubly linked list ordered from most recently used at the head to least recently used at the tail">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">HashMap: {A -&gt; node_A, B -&gt; node_B, C -&gt; node_C}</text>

    <text x="60" y="60" fill="#8b949e">HEAD (most recent)</text>
    <rect x="60" y="70" width="60" height="36" fill="#161b22" stroke="#3fb950"/><text x="90" y="92" text-anchor="middle">C</text>
    <rect x="160" y="70" width="60" height="36" fill="#161b22" stroke="#79c0ff"/><text x="190" y="92" text-anchor="middle">A</text>
    <rect x="260" y="70" width="60" height="36" fill="#161b22" stroke="#79c0ff"/><text x="290" y="92" text-anchor="middle">B</text>
    <text x="290" y="60" fill="#8b949e">TAIL (evict next)</text>

    <line x1="120" y1="88" x2="160" y2="88" stroke="#79c0ff" marker-end="url(#arrow)"/>
    <line x1="160" y1="98" x2="120" y2="98" stroke="#79c0ff"/>
    <line x1="220" y1="88" x2="260" y2="88" stroke="#79c0ff"/>
    <line x1="260" y1="98" x2="220" y2="98" stroke="#79c0ff"/>

    <text x="190" y="150" font-size="9" fill="#8b949e">get("C") just happened -&gt; C moved to head</text>
    <text x="290" y="170" font-size="9" fill="#f0883e">if a new key arrives and capacity is full -&gt; evict B (tail)</text>
  </g>
</svg>

The map gives instant node lookup; the list order (head to tail) gives instant eviction choice.

## 5. Runnable example

```java
// LRUCache.java
import java.util.*;

public class LRUCache {

    // Basic: build an LRU cache from scratch with a HashMap and a hand-rolled doubly linked list.
    static class Node {
        int key, value;
        Node prev, next;
        Node(int key, int value) { this.key = key; this.value = value; }
    }

    static class Cache {
        int capacity;
        Map<Integer, Node> map = new HashMap<>();
        Node head = new Node(-1, -1); // dummy head (most recent side)
        Node tail = new Node(-1, -1); // dummy tail (least recent side)

        Cache(int capacity) {
            this.capacity = capacity;
            head.next = tail;
            tail.prev = head;
        }

        void remove(Node node) {
            node.prev.next = node.next;
            node.next.prev = node.prev;
        }

        void insertAtHead(Node node) {
            node.next = head.next;
            node.prev = head;
            head.next.prev = node;
            head.next = node;
        }

        int get(int key) {
            if (!map.containsKey(key)) return -1;
            Node node = map.get(key);
            remove(node);
            insertAtHead(node);
            return node.value;
        }

        void put(int key, int value) {
            if (map.containsKey(key)) {
                Node existing = map.get(key);
                existing.value = value;
                remove(existing);
                insertAtHead(existing);
                return;
            }
            if (map.size() == capacity) {
                Node lru = tail.prev;
                remove(lru);
                map.remove(lru.key);
            }
            Node fresh = new Node(key, value);
            map.put(key, fresh);
            insertAtHead(fresh);
        }
    }

    static void basicLevel() {
        Cache cache = new Cache(2);
        cache.put(1, 100);
        cache.put(2, 200);
        System.out.println("basic: get(1) -> " + cache.get(1)); // moves 1 to head
        cache.put(3, 300); // evicts 2, since 1 was just used
        System.out.println("basic: get(2) after eviction -> " + cache.get(2));
        System.out.println("basic: get(3) -> " + cache.get(3));
    }

    // Intermediate: trace which key gets evicted under a longer access sequence.
    static void intermediateLevel() {
        Cache cache = new Cache(3);
        cache.put(1, 1);
        cache.put(2, 2);
        cache.put(3, 3);
        cache.get(1);       // 1 becomes most recent
        cache.put(4, 4);    // capacity full -> evict least recent, which is 2

        System.out.println("intermediate: get(2) after eviction (expect -1) -> " + cache.get(2));
        System.out.println("intermediate: get(1) (expect 1, survived) -> " + cache.get(1));
        System.out.println("intermediate: get(4) (expect 4, just added) -> " + cache.get(4));
    }

    // Advanced: use LinkedHashMap's built-in access-order mode to get the same behavior with less code.
    static class LinkedHashMapCache<K, V> extends LinkedHashMap<K, V> {
        int capacity;

        LinkedHashMapCache(int capacity) {
            super(capacity, 0.75f, true); // accessOrder=true: reorders entries on get()
            this.capacity = capacity;
        }

        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > capacity;
        }
    }

    static void advancedLevel() {
        LinkedHashMapCache<Integer, String> cache = new LinkedHashMapCache<>(2);
        cache.put(1, "one");
        cache.put(2, "two");
        cache.get(1); // marks 1 as recently used
        cache.put(3, "three"); // evicts 2 automatically

        System.out.println("advanced: contains key 2 (expect false) -> " + cache.containsKey(2));
        System.out.println("advanced: contains key 1 (expect true) -> " + cache.containsKey(1));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java LRUCache.java`

## 6. Walkthrough

Create a cache with `capacity = 2`. `put(1, 100)`: map is empty, so insert a new node for key `1` at the head. `put(2, 200)`: same, insert at head; the list is now `2 -> 1` (head to tail).

Call `get(1)`. The map finds `node_1` in `O(1)`. Since it exists, `remove(node_1)` unlinks it from its current position, and `insertAtHead(node_1)` puts it back at the front. The list is now `1 -> 2` — `1` is most recent, `2` is least recent.

Call `put(3, 300)`. The map does not contain key `3`, and the cache is at capacity (`2` items). Evict the **tail**'s neighbor (`tail.prev`), which is `node_2` — correctly the least recently used, since `1` was just accessed. Remove it from both the map and the list, then insert the new node for key `3` at the head. The list is now `3 -> 1`.

Checking `get(2)` now returns `-1` (not found), confirming `2` was correctly evicted, while `get(3)` and a later `get(1)` both succeed.

**Complexity.** `get`: `O(1)` — one map lookup, one list detach, one list re-insert, all constant time. `put`: `O(1)` — same operations, plus a possible eviction, which is also `O(1)` since it only touches the tail's neighbor. Space: `O(capacity)`.

## 7. Gotchas & takeaways

> Forgetting to use **dummy head and tail sentinel nodes** (as shown above) forces extra null checks for "is this the first/last real node?" on every insert and remove — the sentinel trick keeps the linked-list code branch-free and less error-prone.

- Both `get` and `put` on an **existing** key must move that node to the head — a common bug is only doing this in `put` and forgetting it in `get`, which breaks the recency invariant for read-only accesses.
- Java's own [LinkedHashMap in access-order mode](0175-linkedhashmap-access-order-for-lru.md) implements exactly this pattern internally, and overriding `removeEldestEntry` gives you a working LRU cache in a few lines — know both the from-scratch version (for interviews) and the built-in version (for production code).
- For a cache that evicts by **frequency** instead of recency, see the [LFU cache](0174-lfu-cache-overview.md) — a related but more complex structure.
