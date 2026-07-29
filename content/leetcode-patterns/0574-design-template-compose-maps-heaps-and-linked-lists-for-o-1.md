---
card: leetcode-patterns
gi: 574
slug: design-template-compose-maps-heaps-and-linked-lists-for-o-1
title: Design — template: compose maps, heaps, and linked lists for O(1)/O(log n) ops
---

## 1. What it is

A reusable recipe for building Design-problem classes: pick a `HashMap` for O(1) lookup by key, a doubly linked list for O(1) insert/remove given a node, and a heap (`PriorityQueue`) for O(log n) access to a minimum or maximum. Most Design problems are solved by picking one or two of these three and wiring them together, rather than inventing a new structure.

## 2. Why & when

Use this template whenever [the Design signal](0573-design-signal-implement-a-data-structure-to-a-required-inter.md) applies: a class with a fixed interface and a per-method complexity bound. Instead of designing a bespoke structure from scratch each time, check whether the required operations map onto this fixed toolkit — most do.

## 3. Core concept

**The three building blocks and what each is for:**

- **`HashMap<K, V>`** — O(1) average lookup, insert, and delete by key. Use it whenever a method must find something by an arbitrary key, not by position.
- **Doubly linked list (with sentinel head/tail nodes)** — O(1) insert or remove of a node **once you already have a reference to it**. Use it whenever a method must reorder or evict elements in O(1), and combine it with a hash map so "find the node" is also O(1).
- **`PriorityQueue<T>` (a binary heap)** — O(log n) insert, and O(log n) removal of the current minimum or maximum; O(1) peek at the minimum or maximum. Use it whenever a method must repeatedly report or remove "the smallest/largest so far."

**The general template steps:**
1. Declare the fields: usually a `HashMap` plus one of {doubly linked list, heap, plain array}.
2. On each mutating method, update every field so they stay consistent with each other — a stale reference in one structure while another has moved on is the most common bug class in Design problems.
3. On each query method, use whichever field answers it fastest; usually the `HashMap` for point lookups, the list's head/tail for "most/least recent," or the heap's root for "min/max so far."

**Sentinel nodes:** a doubly linked list used for eviction (like an LRU cache) almost always uses two dummy nodes, `head` and `tail`, that never hold real data. This removes every null check for "is this the first/last real node," since `head.next` and `tail.prev` are always valid references, even when the list is empty.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Doubly linked list with sentinel head and tail nodes wrapping real data nodes">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="70" width="80" height="40" rx="4" fill="#161b22" stroke="#8b949e" stroke-dasharray="4,2"/>
    <text x="60" y="94" fill="#8b949e" text-anchor="middle" font-size="11">head (sentinel)</text>
    <rect x="160" y="70" width="80" height="40" rx="4" fill="#161b22" stroke="#3fb950"/>
    <text x="200" y="94" fill="#e6edf3" text-anchor="middle" font-size="11">node A</text>
    <rect x="300" y="70" width="80" height="40" rx="4" fill="#161b22" stroke="#3fb950"/>
    <text x="340" y="94" fill="#e6edf3" text-anchor="middle" font-size="11">node B</text>
    <rect x="440" y="70" width="80" height="40" rx="4" fill="#161b22" stroke="#8b949e" stroke-dasharray="4,2"/>
    <text x="480" y="94" fill="#8b949e" text-anchor="middle" font-size="11">tail (sentinel)</text>
    <line x1="100" y1="85" x2="160" y2="85" stroke="#79c0ff" marker-end="url(#a2)"/>
    <line x1="240" y1="90" x2="300" y2="90" stroke="#79c0ff" marker-end="url(#a2)"/>
    <line x1="380" y1="85" x2="440" y2="85" stroke="#79c0ff" marker-end="url(#a2)"/>
    <line x1="300" y1="95" x2="240" y2="95" stroke="#f0883e" marker-end="url(#a2)"/>
    <line x1="440" y1="100" x2="380" y2="100" stroke="#f0883e" marker-end="url(#a2)"/>
    <defs>
      <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/>
      </marker>
    </defs>
    <text x="350" y="160" fill="#e6edf3" text-anchor="middle">head.next / tail.prev are always valid, even on an empty list</text>
  </g>
</svg>

Sentinel nodes remove edge-case checks — inserting or removing the "first" or "last" real node is handled by the same code path as any middle node.

## 5. Runnable example

The reusable template below wires a `HashMap` to a sentinel-based doubly linked list, giving O(1) `moveToFront` and O(1) lookup — the core machinery behind most eviction-style Design problems.

```java
// DesignTemplate.java
import java.util.*;

public class DesignTemplate {

    static class Node {
        int key, value;
        Node prev, next;
        Node(int key, int value) { this.key = key; this.value = value; }
    }

    static class MapPlusList {
        Map<Integer, Node> map = new HashMap<>();
        Node head = new Node(-1, -1); // sentinel: most-recently-used side
        Node tail = new Node(-1, -1); // sentinel: least-recently-used side

        MapPlusList() {
            head.next = tail;
            tail.prev = head;
        }

        void remove(Node node) {
            node.prev.next = node.next;
            node.next.prev = node.prev;
        }

        void insertAtFront(Node node) {
            node.next = head.next;
            node.prev = head;
            head.next.prev = node;
            head.next = node;
        }

        void put(int key, int value) {
            if (map.containsKey(key)) {
                remove(map.get(key));
            }
            Node node = new Node(key, value);
            map.put(key, node);
            insertAtFront(node);
        }

        int get(int key) {
            if (!map.containsKey(key)) return -1;
            Node node = map.get(key);
            remove(node);
            insertAtFront(node); // mark as most recently used
            return node.value;
        }
    }

    public static void main(String[] args) {
        MapPlusList store = new MapPlusList();
        store.put(1, 100);
        store.put(2, 200);
        System.out.println("get(1): " + store.get(1)); // 100, and 1 moves to the front
        store.put(3, 300);
        System.out.println("get(2): " + store.get(2)); // 200, still present
    }
}
```

**How to run:** save as `DesignTemplate.java`, then run `java DesignTemplate.java`.

## 6. Walkthrough

Trace `put(1,100)`, `put(2,200)`, `get(1)`:

1. `put(1,100)`: no existing node for key `1`. Create `Node(1,100)`, store it in `map`, insert it right after `head`. List: `head <-> [1,100] <-> tail`.
2. `put(2,200)`: same process. List: `head <-> [2,200] <-> [1,100] <-> tail`.
3. `get(1)`: `map` finds the node for key `1` in O(1). `remove(node)` unlinks it from its current position. `insertAtFront(node)` relinks it right after `head`. List becomes: `head <-> [1,100] <-> [2,200] <-> tail`. Return `100`.

Every step — find, unlink, relink — touches a fixed, small number of pointers, so each is O(1) regardless of how many entries the map and list hold.

## 7. Gotchas & takeaways

> Gotcha: forgetting to update **both** the map and the list on every mutation leaves them out of sync — for example, removing a node from the list but forgetting to `map.remove(key)` leaves a dangling reference that later lookups will incorrectly still find.

- The three-tool toolkit: `HashMap` for O(1) key lookup, doubly linked list (with sentinels) for O(1) reordering, `PriorityQueue` for O(log n) min/max.
- Sentinel head/tail nodes remove null checks for the list's boundary cases.
- Whenever you touch one structure in a composed design, check whether the other structures also need updating in the same method — this is the most common source of bugs.
