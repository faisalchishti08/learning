---
card: data-structures
gi: 56
slug: detect-intersection-of-two-lists
title: Detect intersection of two lists
---

## 1. What it is

Two linked lists **intersect** if, at some point, they share the exact same node (by reference, not just by equal value) — meaning after the intersection point, the two lists are literally the same chain of nodes, not just coincidentally equal values. Detecting this means finding whether such a shared node exists, and if so, which one it is.

## 2. Why & when

This appears whenever data structures branch off a shared tail — for example, two separate processing paths that eventually merge back into shared cleanup logic, represented as linked structures. It also tests a specific insight: two lists of different lengths can be aligned so a simple two-pointer walk finds the intersection in O(1) extra space, without needing to count lengths and index-align manually.

## 3. Core concept

**Reference equality, not value equality, defines intersection.** Two nodes "intersect" only if they are the exact same object in memory (`nodeA == nodeB`), not merely nodes that happen to hold equal values. Two completely separate nodes that both happen to store `5` are not an intersection.

**The length-difference approach.** Walk both lists once to find their lengths, `lenA` and `lenB`. Advance the pointer on the longer list by `|lenA - lenB|` steps first, to align both pointers so they have the same number of remaining nodes to the end. Then advance both pointers together, one step at a time — if they ever point at the same node, that is the intersection; if both reach `null` together, there is no intersection.

**The elegant two-pointer swap trick — no length counting needed.** Walk pointer `pA` down list A, then (when it hits the end) redirect it to the *head of list B*. Walk pointer `pB` down list B, then redirect it to the *head of list A*. Both pointers travel the same total distance (`lenA + lenB`) by the time they would meet, which automatically aligns them at the intersection point — or at `null` together, if there is no intersection.

**Why the swap trick works: it equalizes the total distance traveled.** If the lists intersect, the "extra" length difference each pointer walks through the *other* list's unique prefix exactly cancels out — both pointers arrive at the intersection node after traveling the identical total distance `lenA + lenB`, without ever needing to compute `lenA` or `lenB` explicitly.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two lists of different lengths sharing a common tail starting at a node C, with the two-pointer swap technique aligning at that intersection" >
  <g font-family="sans-serif" font-size="11">
    <text x="80" y="16" fill="#8b949e">list A: 1 -&gt; 2 -&gt;</text>
    <text x="80" y="90" fill="#8b949e">list B: 9 -&gt;</text>
    <rect x="220" y="20" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="240" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <rect x="260" y="20" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="280" y="37" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <rect x="260" y="70" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="280" y="87" fill="#e6edf3" text-anchor="middle" font-size="9">9</text>
    <rect x="340" y="45" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="360" y="62" fill="#e6edf3" text-anchor="middle" font-size="9">C</text>
    <rect x="400" y="45" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="420" y="62" fill="#e6edf3" text-anchor="middle" font-size="9">D</text>
    <line x1="300" y1="33" x2="335" y2="55" stroke="#79c0ff"/>
    <line x1="300" y1="83" x2="335" y2="58" stroke="#79c0ff"/>
    <line x1="380" y1="58" x2="395" y2="58" stroke="#79c0ff" marker-end="url(#a23)"/>
    <defs><marker id="a23" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <text x="320" y="140" fill="#79c0ff" text-anchor="middle">both lists share the same C -&gt; D tail -- the intersection point is node C</text>
  </g>
</svg>

Lists A and B are separate up to node `C`, then share the exact same `C -> D` tail — node `C` is the intersection.

## 5. Runnable example

```java
// DetectListIntersection.java
public class DetectListIntersection {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    // Basic: length-difference approach -- count lengths, align, then walk together.
    static Node findIntersectionByLength(Node headA, Node headB) {
        int lenA = length(headA), lenB = length(headB);
        Node pA = headA, pB = headB;
        while (lenA > lenB) { pA = pA.next; lenA--; } // align the longer list forward
        while (lenB > lenA) { pB = pB.next; lenB--; }
        while (pA != pB) { // now walk together; pA==pB (possibly null) is the answer
            pA = pA.next;
            pB = pB.next;
        }
        return pA; // the shared node, or null if no intersection
    }

    static int length(Node head) {
        int count = 0;
        for (Node c = head; c != null; c = c.next) count++;
        return count;
    }

    static void basicLevel() {
        Node intersection = new Node(8);
        intersection.next = new Node(9);

        Node headA = new Node(1);
        headA.next = new Node(2);
        headA.next.next = intersection; // A: 1 -> 2 -> 8 -> 9

        Node headB = new Node(4);
        headB.next = intersection; // B: 4 -> 8 -> 9 (shares the same tail as A)

        Node result = findIntersectionByLength(headA, headB);
        System.out.println("basic: intersection value (by length) -> " + (result != null ? result.value : "none"));
    }

    // Intermediate: the two-pointer swap trick -- no length counting needed.
    static Node findIntersectionBySwap(Node headA, Node headB) {
        if (headA == null || headB == null) return null;
        Node pA = headA, pB = headB;
        while (pA != pB) {
            pA = (pA == null) ? headB : pA.next; // swap to the OTHER list's head once exhausted
            pB = (pB == null) ? headA : pB.next;
        }
        return pA; // both pointers travel lenA + lenB total, aligning at the intersection (or null)
    }

    static void intermediateLevel() {
        Node intersection = new Node(8);
        intersection.next = new Node(9);

        Node headA = new Node(1);
        headA.next = new Node(2);
        headA.next.next = intersection;

        Node headB = new Node(4);
        headB.next = intersection;

        Node result = findIntersectionBySwap(headA, headB);
        System.out.println("intermediate: intersection value (by swap) -> " + (result != null ? result.value : "none"));
    }

    // Advanced: confirm two DIFFERENT lists with EQUAL values at the same position do NOT count as intersecting.
    static void advancedLevel() {
        Node headA = new Node(1);
        headA.next = new Node(2);

        Node headB = new Node(1); // same VALUES as headA, but entirely separate node objects
        headB.next = new Node(2);

        Node result = findIntersectionBySwap(headA, headB);
        System.out.println("advanced: separate lists with equal values, intersection -> " + result); // null
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `DetectListIntersection.java`, then run `java DetectListIntersection.java`.

## 6. Walkthrough

1. `basicLevel()` builds list A (`1 -> 2 -> 8 -> 9`) and list B (`4 -> 8 -> 9`), where the `8` node is the literal same object referenced by both lists' `next` chains. `findIntersectionByLength` computes `lenA=4, lenB=3`, advances `pA` one step to align both pointers with 3 remaining nodes, then walks both together — they meet at the `8` node.
2. `intermediateLevel()`'s `findIntersectionBySwap` walks `pA` down A (`1,2,8,9`, then swaps to `headB`) and `pB` down B (`4,8,9`, then swaps to `headA`) simultaneously. Both pointers end up traveling `lenA + lenB = 7` total steps by the time they land on the same node — the shared `8` node — without ever computing either length explicitly.
3. `advancedLevel()` builds two entirely separate lists that happen to hold equal values (`1`, `2`) at the same positions, but share no actual node objects. `findIntersectionBySwap` correctly returns `null`, since `pA` and `pB` only ever become equal by hitting `null` together at the very end — reference equality, not value equality, is what the algorithm actually checks.

## 7. Gotchas & takeaways

> Gotcha: comparing nodes with `.equals()` (if `Node` ever overrode it to compare values) instead of `==` would incorrectly report an "intersection" for two separate lists that merely contain equal values at the same relative position — intersection is fundamentally about shared object identity, not equal content, so `==` is the correct comparison here.

- Two lists intersect only if they share the exact same node object, not merely equal values.
- The length-difference approach counts both lengths, aligns the longer list's pointer forward, then walks both pointers together.
- The swap-pointers trick avoids counting lengths entirely, by having each pointer traverse both lists in turn, automatically equalizing total distance traveled.
- Related concepts: [Cycle detection (Floyd's tortoise & hare)](0053-cycle-detection-floyd-s-tortoise-hare.md) (a related two-pointer technique), [Merge two sorted linked lists](0055-merge-two-sorted-linked-lists.md).
