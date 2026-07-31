---
card: data-structures
gi: 53
slug: cycle-detection-floyd-s-tortoise-hare
title: Cycle detection (Floyd's tortoise & hare)
---

## 1. What it is

**Floyd's cycle detection algorithm** (the "tortoise and hare") finds whether a linked list contains a **cycle** — a node whose `next` chain loops back to an earlier node instead of eventually reaching `null` — using only two pointers moving at different speeds, and O(1) extra memory. One pointer (the tortoise) moves one node at a time; the other (the hare) moves two nodes at a time. If they ever meet, a cycle exists.

## 2. Why & when

A cycle is usually a bug — accidental corruption from a linked-list operation gone wrong — and this algorithm is the standard way to detect it without extra memory. Use it whenever you cannot guarantee a list is well-formed (ends in `null`) and need to check safely before a traversal that would otherwise loop forever.

## 3. Core concept

**Why a faster pointer must eventually catch a slower one, if there is a cycle.** Once both pointers enter the cycle, the hare gains on the tortoise by one extra step every iteration (it moves 2 steps to the tortoise's 1). Since the cycle has a finite length, the gap between them (measured within the cycle) shrinks by 1 each iteration and must eventually reach 0 — they meet. If there is no cycle, the hare simply reaches `null` first, proving there was nothing to detect.

**Detection alone is O(1) space, O(n) time.** No extra data structure (like a `HashSet` of visited nodes) is needed — just two pointer variables. This is the main advantage over the alternative of tracking visited nodes in a `HashSet`, which would use O(n) extra space.

**Finding the cycle's *starting* node: a second phase.** After the tortoise and hare meet somewhere inside the cycle, reset one pointer to `head` and leave the other at the meeting point, then advance both one step at a time. They are mathematically guaranteed to meet again exactly at the cycle's starting node — this follows from the relationship between the distance from `head` to the cycle start and the distance around the cycle back to the meeting point.

**Alternative: a `HashSet` of visited nodes.** Walk the list, adding each node reference to a `HashSet`; if you ever encounter a node already in the set, that is the cycle's start. This is easier to reason about but costs O(n) extra space — Floyd's algorithm trades that away for pure pointer arithmetic.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tortoise pointer moving one step and a hare pointer moving two steps around a linked list with a cycle, eventually meeting inside the loop">
  <g font-family="sans-serif" font-size="11">
    <rect x="40" y="80" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="70" y="100" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <rect x="130" y="80" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="160" y="100" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <rect x="220" y="30" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="250" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <rect x="320" y="30" width="60" height="30" fill="#0d1117" stroke="#f0883e"/><text x="350" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">4 (meet)</text>
    <rect x="220" y="130" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="250" y="150" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>

    <line x1="100" y1="95" x2="125" y2="95" stroke="#79c0ff" marker-end="url(#a22)"/>
    <line x1="190" y1="90" x2="215" y2="50" stroke="#79c0ff" marker-end="url(#a22)"/>
    <line x1="280" y1="45" x2="315" y2="45" stroke="#79c0ff" marker-end="url(#a22)"/>
    <line x1="380" y1="55" x2="285" y2="135" stroke="#79c0ff" marker-end="url(#a22)"/>
    <line x1="220" y1="140" x2="195" y2="100" stroke="#79c0ff" marker-end="url(#a22)"/>
    <defs><marker id="a22" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <text x="320" y="185" fill="#79c0ff" text-anchor="middle">node 5's next points back to node 3 -- a cycle; tortoise and hare meet at node 4</text>
  </g>
</svg>

Node `5` loops back to node `3` instead of `null`. The faster hare eventually laps the slower tortoise inside the loop, and they meet.

## 5. Runnable example

```java
// FloydCycleDetection.java
public class FloydCycleDetection {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    // Basic: detect whether a cycle exists at all.
    static boolean hasCycle(Node head) {
        Node tortoise = head, hare = head;
        while (hare != null && hare.next != null) {
            tortoise = tortoise.next;      // moves 1 step
            hare = hare.next.next;         // moves 2 steps
            if (tortoise == hare) return true; // they met -- a cycle exists
        }
        return false; // hare reached null -- no cycle
    }

    static void basicLevel() {
        Node a = new Node(1), b = new Node(2), c = new Node(3);
        a.next = b; b.next = c; c.next = null; // no cycle
        System.out.println("basic: acyclic list has cycle -> " + hasCycle(a));

        c.next = a; // introduce a cycle: 3 -> 1 (loops back)
        System.out.println("basic: cyclic list has cycle -> " + hasCycle(a));
    }

    // Intermediate: find the exact node where the cycle begins.
    static Node findCycleStart(Node head) {
        Node tortoise = head, hare = head;
        while (hare != null && hare.next != null) {
            tortoise = tortoise.next;
            hare = hare.next.next;
            if (tortoise == hare) { // met -- now find the start
                Node pointer = head;
                while (pointer != tortoise) { // both now move 1 step at a time
                    pointer = pointer.next;
                    tortoise = tortoise.next;
                }
                return pointer; // guaranteed to be the cycle's start node
            }
        }
        return null; // no cycle
    }

    static void intermediateLevel() {
        Node a = new Node(1), b = new Node(2), c = new Node(3), d = new Node(4);
        a.next = b; b.next = c; c.next = d; d.next = b; // cycle starts at 'b' (value 2)
        Node cycleStart = findCycleStart(a);
        System.out.println("intermediate: cycle starts at value -> " + (cycleStart != null ? cycleStart.value : "none"));
    }

    // Advanced: alternative HashSet-based detection, trading O(1) space for simpler reasoning.
    static boolean hasCycleWithHashSet(Node head) {
        java.util.Set<Node> visited = new java.util.HashSet<>();
        Node current = head;
        while (current != null) {
            if (!visited.add(current)) return true; // add() returns false if already present
            current = current.next;
        }
        return false;
    }

    static void advancedLevel() {
        Node a = new Node(1), b = new Node(2), c = new Node(3);
        a.next = b; b.next = c; c.next = a; // cycle: 3 -> 1
        System.out.println("advanced: HashSet-based detection -> " + hasCycleWithHashSet(a));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `FloydCycleDetection.java`, then run `java FloydCycleDetection.java`.

## 6. Walkthrough

1. `basicLevel()` first builds an acyclic list `1 -> 2 -> 3 -> null`. `hasCycle` advances `hare` two steps at a time; it reaches `null` before ever equaling `tortoise`, so the function returns `false`.
2. After setting `c.next = a`, the list becomes cyclic (`3` loops back to `1`). Now `hare` never reaches `null` — it keeps circling, gaining on `tortoise` by one extra step per iteration, until they land on the same node, and `hasCycle` returns `true`.
3. `intermediateLevel()`'s `findCycleStart` first runs the same tortoise/hare loop until they meet, then resets a `pointer` to `head` and advances both `pointer` and `tortoise` one step at a time — they are guaranteed to meet exactly at the cycle's start node, `b` (value 2).
4. `advancedLevel()`'s `hasCycleWithHashSet` walks the list adding each node to a `HashSet`; `visited.add(current)` returns `false` the moment it tries to add a node already present, immediately signaling a cycle — simpler to follow than the two-pointer approach, at the cost of O(n) extra memory for the set.

## 7. Gotchas & takeaways

> Gotcha: the loop condition must check `hare != null && hare.next != null` before advancing `hare` two steps — checking only `hare != null` risks a `NullPointerException` when `hare.next` is `null` and the code tries to read `hare.next.next`.

- Floyd's tortoise-and-hare algorithm detects a cycle in O(n) time and O(1) space, using two pointers moving at different speeds.
- If a cycle exists, the faster pointer is guaranteed to eventually meet the slower one inside the loop; if not, it reaches `null` first.
- After detecting a meeting point, resetting one pointer to `head` and advancing both one step at a time finds the cycle's exact starting node.
- Related concepts: [Circular linked list](0047-circular-linked-list.md) (an intentional structural cycle, versus this algorithm's target — an unintended one), [Find middle & nth-from-end](0054-find-middle-nth-from-end.md) (the same two-speed-pointer idea, applied differently).
