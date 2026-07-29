---
card: leetcode-patterns
gi: 576
slug: lru-cache
title: LRU Cache
---

## 1. What it is

Design a `LRUCache` class with a fixed `capacity`. It supports `get(key)`, which returns the value for `key` or `-1` if absent, and `put(key, value)`, which inserts or updates a key's value. When `put` would exceed `capacity`, the **least recently used** (LRU) entry — the one that has gone longest without being read or written — is evicted first. Both methods must run in O(1) average time. Example: `capacity=2`; `put(1,1)`, `put(2,2)`, `get(1)` → `1` (and `1` becomes most recent); `put(3,3)` evicts key `2` (now the least recent); `get(2)` → `-1`.

## 2. Why & when

This is the canonical example of the [Design template](0574-design-template-compose-maps-heaps-and-linked-lists-for-o-1.md): no single built-in structure gives O(1) lookup by key **and** O(1) tracking of recency order, so you compose a `HashMap` (for lookup) with a doubly linked list (for recency order). Constraints: up to 3,000 capacity, up to 200,000 calls to `get` and `put` combined — ruling out any O(n) per-call approach.

## 3. Core concept

**Key idea:** keep a `HashMap<key, Node>` for O(1) lookup, where each `Node` also lives in a doubly linked list ordered by recency, most-recently-used at the front and least-recently-used at the back. Every `get` or `put` on an existing key moves that key's node to the front. Every `put` that exceeds capacity removes the node at the back.

**Steps:**
1. `get(key)`: if `key` is not in the map, return `-1`. Otherwise, unlink the node from its current list position, relink it at the front, and return its value.
2. `put(key, value)`: if `key` already exists, update its value and move its node to the front (same as `get`'s reordering). Otherwise, create a new node, add it to the map and the front of the list; if this pushes the size over `capacity`, remove the node at the back of the list and delete its key from the map.
3. Use sentinel `head` and `tail` nodes so "insert at front" and "remove at back" never need a null check for an empty list.

**Why the linked list, not just an array of recent keys:** an array would need O(n) work to move an arbitrary key to the front (shifting every element in between). A doubly linked list moves any node to the front in O(1), as long as you already have a direct reference to that node — which the `HashMap` supplies.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LRU cache: HashMap points to nodes in a doubly linked list ordered by recency">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="25" fill="#8b949e">HashMap</text>
    <rect x="20" y="35" width="120" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="80" y="55" fill="#e6edf3" text-anchor="middle" font-size="11">1 -&gt; node</text>
    <rect x="20" y="70" width="120" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="80" y="90" fill="#e6edf3" text-anchor="middle" font-size="11">3 -&gt; node</text>
    <rect x="220" y="50" width="90" height="40" rx="4" fill="#161b22" stroke="#79c0ff"/>
    <text x="265" y="74" fill="#e6edf3" text-anchor="middle" font-size="11">[3,3] MRU</text>
    <rect x="360" y="50" width="90" height="40" rx="4" fill="#161b22" stroke="#79c0ff"/>
    <text x="405" y="74" fill="#e6edf3" text-anchor="middle" font-size="11">[1,1]</text>
    <rect x="500" y="50" width="90" height="40" rx="4" fill="#161b22" stroke="#f0883e"/>
    <text x="545" y="74" fill="#e6edf3" text-anchor="middle" font-size="11">[2,2] LRU</text>
    <line x1="310" y1="70" x2="360" y2="70" stroke="#8b949e" marker-end="url(#a3)"/>
    <line x1="450" y1="70" x2="500" y2="70" stroke="#8b949e" marker-end="url(#a3)"/>
    <defs><marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="405" y="140" fill="#79c0ff" text-anchor="middle">a put() that exceeds capacity evicts the node at the LRU end</text>
  </g>
</svg>

The map gives O(1) access to any node by key; the list's ordering, from most- to least-recently-used, tells eviction exactly which node to drop.

## 5. Runnable example

**Level 1 — Brute force.** Store entries in an `ArrayList`, and on every access, linear-scan to find the key, then move that entry to the end (or front) by shifting elements. O(n) per call.

**KEY INSIGHT:** the only reason a plain array is slow is moving an arbitrary element to the front requires shifting everything in between; a doubly linked list moves any node to the front in O(1) once you already have a reference to it — and a `HashMap` supplies that reference in O(1).

**Level 2 — Optimal.** `HashMap<Integer, Node>` plus a sentinel-based doubly linked list, O(1) per call.

**Level 3 — Hardened.** Handles updating an existing key's value (move-to-front without changing capacity used), and evicting exactly one entry when a new key would exceed capacity.

```java
// LRUCache.java
import java.util.*;

public class LRUCache {

    static class Node {
        int key, value;
        Node prev, next;
        Node(int key, int value) { this.key = key; this.value = value; }
    }

    private final int capacity;
    private final Map<Integer, Node> map = new HashMap<>();
    private final Node head = new Node(-1, -1); // sentinel, most-recent side
    private final Node tail = new Node(-1, -1); // sentinel, least-recent side

    public LRUCache(int capacity) {
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    private void remove(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    private void insertAtFront(Node node) {
        node.next = head.next;
        node.prev = head;
        head.next.prev = node;
        head.next = node;
    }

    public int get(int key) {
        if (!map.containsKey(key)) return -1;
        Node node = map.get(key);
        remove(node);
        insertAtFront(node);
        return node.value;
    }

    public void put(int key, int value) {
        if (map.containsKey(key)) {
            Node node = map.get(key);
            node.value = value;
            remove(node);
            insertAtFront(node);
            return;
        }
        if (map.size() == capacity) {
            Node lru = tail.prev;
            remove(lru);
            map.remove(lru.key);
        }
        Node node = new Node(key, value);
        map.put(key, node);
        insertAtFront(node);
    }

    public static void main(String[] args) {
        LRUCache cache = new LRUCache(2);
        cache.put(1, 1);
        cache.put(2, 2);
        System.out.println(cache.get(1)); // 1, and key 1 becomes most recent
        cache.put(3, 3);                  // evicts key 2 (least recent)
        System.out.println(cache.get(2)); // -1
        cache.put(4, 4);                  // evicts key 1 (least recent)
        System.out.println(cache.get(1)); // -1
        System.out.println(cache.get(3)); // 3
        System.out.println(cache.get(4)); // 4
    }
}
```

**How to run:** save as `LRUCache.java`, then run `java LRUCache.java`.

## 6. Walkthrough

Trace `capacity=2`; `put(1,1)`, `put(2,2)`, `get(1)`, `put(3,3)`, `get(2)`:

| call | map keys | list order (MRU -> LRU) | return |
|---|---|---|---|
| put(1,1) | {1} | [1] | — |
| put(2,2) | {1,2} | [2,1] | — |
| get(1) | {1,2} | [1,2] | 1 |
| put(3,3) | size==2, evict LRU (2); {1,3} | [3,1] | — |
| get(2) | {1,3} | [3,1] | -1 |

`get(1)` moves key `1` to the front, making key `2` the new least-recently-used. `put(3,3)` then evicts key `2`, matching the observed `-1` for `get(2)`.

## 7. Gotchas & takeaways

> Gotcha: updating an existing key's value with `put` must also move it to the front — treating an update as if it were a fresh insert without reordering leaves stale recency information and evicts the wrong key later.

- Signal: an interface needing O(1) lookup by key *and* O(1) recency-based eviction is the direct HashMap-plus-doubly-linked-list signal.
- Sentinel `head`/`tail` nodes remove null checks for inserting into or removing from an empty list.
- Related problems: LFU Cache (adds frequency tracking on top of recency), Design Browser History (a similar linked-structure-plus-pointer idea for a different access pattern).
