---
card: data-structures
gi: 58
slug: copy-a-list-with-random-pointers
title: Copy a list with random pointers
---

## 1. What it is

A **list with random pointers** is a linked list where each node has two links: `next`, the normal forward link, and `random`, which can point to *any* node in the list (or to `null`). Copying it means building a completely new, independent list where every `next` and every `random` link mirrors the original — but points to nodes in the *copy*, not the original.

## 2. Why & when

This is a named LeetCode problem ("Copy List with Random Pointer") and it tests whether you can build a second graph-like structure while an unpredictable second reference is still being resolved — the `random` target might not exist yet in the new list when you copy a given node. The same shape appears when cloning object graphs with arbitrary cross-references, such as a scene graph or a document with internal links.

## 3. Core concept

**Key idea in one sentence.** Interleave a cloned node right after each original node, so that `original.next.random` gives you the clone of `original.random`, for free.

**Level 1 — Brute force: a hash map from original node to clone.** Walk the list once, creating a clone for every node and storing the mapping `original -> clone` in a `HashMap`. Walk the list again, and for each original node, set `clone.next = map.get(original.next)` and `clone.random = map.get(original.random)`. This is correct and O(n) time, but uses O(n) extra space for the map.

**KEY INSIGHT.** You do not need a separate map if you weave the clones directly into the original list. Placing `clone_A` right after `original_A` means `original_A.next` *is* `clone_A` — so to find the clone of any node reachable via `random`, you just take `original.random.next`.

**Level 2 — Optimal: interleaving, no extra map.** Three passes over the *interleaved* list: (1) insert each clone right after its original, so the list becomes `A -> A' -> B -> B' -> ...`; (2) set every clone's `random` using `original.random.next` (the clone of the random target); (3) unweave the list back into two separate lists — original and copy — by fixing up `next` pointers on each pass.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Original nodes A and B interleaved with their clones A prime and B prime, showing how a clone random pointer is found via original.random.next">
  <g font-family="sans-serif" font-size="11">
    <rect x="20" y="20" width="46" height="26" fill="#161b22" stroke="#8b949e"/><text x="43" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">A</text>
    <rect x="86" y="20" width="46" height="26" fill="#0d1117" stroke="#f0883e"/><text x="109" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">A'</text>
    <rect x="152" y="20" width="46" height="26" fill="#161b22" stroke="#8b949e"/><text x="175" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">B</text>
    <rect x="218" y="20" width="46" height="26" fill="#0d1117" stroke="#f0883e"/><text x="241" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">B'</text>
    <line x1="66" y1="33" x2="82" y2="33" stroke="#79c0ff" marker-end="url(#ar)"/>
    <line x1="132" y1="33" x2="148" y2="33" stroke="#79c0ff" marker-end="url(#ar)"/>
    <line x1="198" y1="33" x2="214" y2="33" stroke="#79c0ff" marker-end="url(#ar)"/>
    <defs><marker id="ar" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <path d="M43,46 C43,120 175,120 175,46" fill="none" stroke="#f0883e"/>
    <text x="109" y="135" fill="#f0883e" text-anchor="middle" font-size="9">A.random -&gt; B</text>
    <text x="20" y="170" fill="#79c0ff">so A'.random = A.random.next = B.next = B'  (the clone of B)</text>
  </g>
</svg>

`A.random` points to `B`. Because `B'` sits right after `B`, `A.random.next` gives the clone of `B` directly.

## 5. Runnable example

```java
// CopyRandomList.java
import java.util.HashMap;
import java.util.Map;

public class CopyRandomList {

    static class Node {
        int value;
        Node next;
        Node random;
        Node(int value) { this.value = value; }
    }

    // Level 1: brute force with a HashMap from original node to its clone.
    static Node copyWithMap(Node head) {
        if (head == null) return null;
        Map<Node, Node> map = new HashMap<>();
        for (Node c = head; c != null; c = c.next) map.put(c, new Node(c.value));
        for (Node c = head; c != null; c = c.next) {
            map.get(c).next = map.get(c.next);
            map.get(c).random = map.get(c.random);
        }
        return map.get(head);
    }

    // Level 2: optimal -- interleave clones, wire randoms, then unweave. O(1) extra space.
    static Node copyByInterleaving(Node head) {
        if (head == null) return null;

        // Pass 1: A -> A' -> B -> B' -> ...
        for (Node c = head; c != null; c = c.next.next) {
            Node clone = new Node(c.value);
            clone.next = c.next;
            c.next = clone;
        }

        // Pass 2: wire each clone's random using original.random.next.
        for (Node c = head; c != null; c = c.next.next) {
            if (c.random != null) c.next.random = c.random.next;
        }

        // Pass 3: unweave into the original list and the cloned list.
        Node cloneHead = head.next;
        for (Node c = head; c != null; c = c.next) {
            Node clone = c.next;
            c.next = clone.next;
            clone.next = (clone.next != null) ? clone.next.next : null;
        }
        return cloneHead;
    }

    static void basicLevel() {
        Node a = new Node(1), b = new Node(2), c = new Node(3);
        a.next = b; b.next = c;
        a.random = c; b.random = b; c.random = a;

        Node copy = copyWithMap(a);
        System.out.println("basic: copy head value -> " + copy.value
            + ", copy is different object -> " + (copy != a)
            + ", copy.random.value -> " + copy.random.value);
    }

    static void intermediateLevel() {
        Node a = new Node(1), b = new Node(2), c = new Node(3);
        a.next = b; b.next = c;
        a.random = c; b.random = b; c.random = a;

        Node copy = copyByInterleaving(a);
        System.out.println("intermediate: copy chain -> " + copy.value + "," + copy.next.value + "," + copy.next.next.value);
        System.out.println("intermediate: copy.random.value (should be 3) -> " + copy.random.value);
        System.out.println("intermediate: original list untouched, a.next.value -> " + a.next.value);
    }

    // Advanced: a node whose random points to null, and a single-node list.
    static void advancedLevel() {
        Node single = new Node(42);
        single.random = null;
        Node copySingle = copyByInterleaving(single);
        System.out.println("advanced: single node copy value -> " + copySingle.value + ", random -> " + copySingle.random);

        Node a = new Node(1);
        a.random = null;
        Node copyA = copyByInterleaving(a);
        System.out.println("advanced: node with null random, copy.random -> " + copyA.random);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `CopyRandomList.java`, then run `java CopyRandomList.java`.

## 6. Walkthrough

Trace `copyByInterleaving` on `A -> B -> C` where `A.random = C`, `B.random = B`, `C.random = A`.

| Step | Action | State after |
|---|---|---|
| 1 | Pass 1 clones `A`, splices `A'` after `A` | `A -> A' -> B` |
| 2 | Pass 1 clones `B`, splices `B'` after `B` | `A -> A' -> B -> B' -> C` |
| 3 | Pass 1 clones `C`, splices `C'` after `C` | `A -> A' -> B -> B' -> C -> C'` |
| 4 | Pass 2: `A'.random = A.random.next = C.next = C'` | `A'.random` set |
| 5 | Pass 2: `B'.random = B.random.next = B.next = B'` | `B'.random` points to itself |
| 6 | Pass 2: `C'.random = C.random.next = A.next = A'` | `C'.random` set |
| 7 | Pass 3 unweaves: restores `A -> B -> C`, builds `A' -> B' -> C'` separately | two clean lists |

Every `random` on the clone side ends up pointing to a clone, never to an original node, because it was always read through `.next` off an original node's `random`.

## 7. Gotchas & takeaways

> Gotcha: if you unweave before wiring the `random` pointers, `original.random.next` no longer gives you the clone — the interleaving must stay intact until pass 2 finishes. Also handle `random == null` explicitly; `null.next` throws a `NullPointerException`.

- The brute-force hash-map approach is easiest to get right first: map every original node to its clone, then rewire both `next` and `random`.
- The interleaving trick removes the map by exploiting `original.next == clone`, so `original.random.next == clone.random`.
- Always unweave last, and only after every clone's `random` has been set.
- Related concepts: [Singly linked list](0045-singly-linked-list.md); the same interleaving trick generalizes to any deep copy of a graph with cross-references, not just linked lists.
