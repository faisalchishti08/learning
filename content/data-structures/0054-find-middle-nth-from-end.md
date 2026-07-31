---
card: data-structures
gi: 54
slug: find-middle-nth-from-end
title: Find middle & nth-from-end
---

## 1. What it is

Finding the **middle node** and finding the **n-th node from the end** are two classic linked-list problems that both use the same core trick: two pointers moving through the list with a controlled offset between them, so that when one pointer finishes, the other lands exactly where you need it — all in a single pass, without knowing the list's length in advance.

## 2. Why & when

A linked list has no `length` field and no O(1) indexed access, so "find the node at position n/2" or "find the node 3 from the end" cannot be answered by simple index arithmetic the way it could for an array. These two-pointer techniques solve both problems in one O(n) pass, without a separate O(n) pass just to count the list's length first.

## 3. Core concept

**Finding the middle: slow and fast pointers, 1 step vs. 2 steps.** Start both `slow` and `fast` at `head`. Advance `slow` one node per step, `fast` two nodes per step. When `fast` reaches the end (`null`, or has no next), `slow` has covered exactly half the distance — it is sitting at the middle. This is the same two-speed idea as [Cycle detection (Floyd's tortoise & hare)](0053-cycle-detection-floyd-s-tortoise-hare.md), applied to find a position instead of detecting a loop.

**Odd vs. even length changes what "the middle" means.** For an odd-length list, there is one exact middle node. For an even-length list, there are two middle candidates — the exact stopping point (first or second of the pair) depends on the precise loop condition used (`fast != null && fast.next != null`, versus a variant), so the convention must be picked deliberately and applied consistently.

**Finding the n-th from the end: two pointers with a fixed gap.** Advance a `lead` pointer `n` steps ahead of a `trail` pointer first. Then advance both together, one step at a time, until `lead` reaches the end. At that point, `trail` is exactly `n` nodes from the end — because the fixed gap between them, established at the start, is preserved throughout.

**Why both techniques need only one pass.** Neither approach requires first counting the list's length (which would itself be a full pass) and then computing a target index — the pointer offset itself encodes the "n-th from the end" or "half the length" relationship directly, resolved by the time the leading pointer finishes.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Slow and fast pointers finding the middle by moving at 1x and 2x speed, and lead/trail pointers with a fixed gap finding the nth node from the end">
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="16" fill="#8b949e" text-anchor="middle">middle: slow(1x) vs fast(2x)</text>
    <rect x="60" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="80" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <rect x="100" y="30" width="40" height="26" fill="#0d1117" stroke="#3fb950"/><text x="120" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <rect x="140" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="160" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <rect x="180" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="200" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">4</text>
    <rect x="220" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="240" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <text x="120" y="80" fill="#79c0ff" text-anchor="middle" font-size="9">slow stops here when fast hits the end</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">nth-from-end: fixed gap of n=2</text>
    <rect x="420" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="440" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <rect x="460" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="480" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <rect x="500" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="520" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <rect x="540" y="30" width="40" height="26" fill="#0d1117" stroke="#3fb950"/><text x="560" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">4</text>
    <rect x="580" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="600" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">5</text>
    <text x="510" y="80" fill="#79c0ff" text-anchor="middle" font-size="9">trail stops 2 from the end, once lead reaches the end</text>
  </g>
</svg>

Both techniques use two pointers with a controlled relationship (speed ratio, or fixed gap) to land exactly where needed in one pass.

## 5. Runnable example

```java
// FindMiddleNthFromEnd.java
public class FindMiddleNthFromEnd {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    // Basic: find the middle node using slow/fast pointers.
    static Node findMiddle(Node head) {
        Node slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;       // 1 step
            fast = fast.next.next;  // 2 steps
        }
        return slow; // for even length, this lands on the SECOND of the two middle candidates
    }

    static void basicLevel() {
        Node oddList = buildList(1, 2, 3, 4, 5);
        System.out.println("basic: middle of odd-length list -> " + findMiddle(oddList).value); // 3

        Node evenList = buildList(1, 2, 3, 4, 5, 6);
        System.out.println("basic: middle of even-length list -> " + findMiddle(evenList).value); // 4
    }

    // Intermediate: find the nth node from the end using a fixed-gap two-pointer scan.
    static Node findNthFromEnd(Node head, int n) {
        Node lead = head, trail = head;
        for (int i = 0; i < n; i++) {
            if (lead == null) throw new IllegalArgumentException("list shorter than n");
            lead = lead.next; // advance lead n steps first, establishing the gap
        }
        while (lead != null) {
            lead = lead.next;
            trail = trail.next; // now advance both together, preserving the gap
        }
        return trail;
    }

    static void intermediateLevel() {
        Node list = buildList(1, 2, 3, 4, 5);
        System.out.println("intermediate: 2nd from end -> " + findNthFromEnd(list, 2).value); // 4
    }

    // Advanced: remove the nth node from the end in one pass, using the same fixed-gap technique.
    static Node removeNthFromEnd(Node head, int n) {
        Node dummy = new Node(0);
        dummy.next = head;
        Node lead = dummy, trail = dummy;
        for (int i = 0; i < n; i++) lead = lead.next;
        while (lead.next != null) { // stop trail just BEFORE the target, so it can relink
            lead = lead.next;
            trail = trail.next;
        }
        trail.next = trail.next.next; // remove the target node
        return dummy.next;
    }

    static void advancedLevel() {
        Node list = buildList(1, 2, 3, 4, 5);
        Node result = removeNthFromEnd(list, 2); // remove the 2nd-from-end node (value 4)
        printList("advanced (removed 2nd from end)", result);
    }

    static Node buildList(int... values) {
        Node dummy = new Node(0), tail = dummy;
        for (int v : values) { tail.next = new Node(v); tail = tail.next; }
        return dummy.next;
    }

    static void printList(String label, Node head) {
        StringBuilder sb = new StringBuilder();
        for (Node c = head; c != null; c = c.next) sb.append(c.value).append(" -> ");
        System.out.println(label + " -> " + sb + "null");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `FindMiddleNthFromEnd.java`, then run `java FindMiddleNthFromEnd.java`.

## 6. Walkthrough

1. `basicLevel()`'s `findMiddle` on the 5-node list advances `fast` two steps for every one step of `slow`. `fast` reaches the end after covering all 5 nodes (roughly), leaving `slow` at node `3`, the exact middle.
2. On the 6-node list, `fast` runs out of room after `slow` has advanced 3 steps, landing `slow` on node `4` — this loop's specific condition (`fast != null && fast.next != null`) determines that the *second* of the two middle candidates (`3` or `4`) is returned; a different condition would land on the first instead.
3. `intermediateLevel()`'s `findNthFromEnd(list, 2)` first advances `lead` 2 steps (to node `3`), establishing a 2-node gap to `trail` (still at node `1`). Then both advance together until `lead` reaches `null` — `trail` ends up at node `4`, which is indeed 2 nodes from the end (`5` is 1st from the end, `4` is 2nd).
4. `advancedLevel()`'s `removeNthFromEnd` uses a [sentinel dummy node](0048-sentinel-dummy-nodes.md) and the same fixed-gap technique, but stops `trail` one node *before* the target (checking `lead.next != null` instead of `lead != null`), so `trail.next = trail.next.next` can directly unlink the target node (`4`) — the result is `1 -> 2 -> 3 -> 5 -> null`.

## 7. Gotchas & takeaways

> Gotcha: off-by-one errors are the main risk in both techniques — whether `fast` starts one step ahead or even with `slow`, and whether `lead` advances `n` or `n+1` times before the joint walk begins, changes which exact node you land on. Trace through a small example by hand (like a 4- or 5-node list) to confirm your specific loop conditions land where you intend.

- Finding the middle uses a slow (1x) and fast (2x) pointer pair; when the fast pointer finishes, the slow pointer is at the middle.
- Finding the n-th from the end uses two pointers with a fixed gap of `n`, established first, then advanced together.
- Both techniques solve their problem in a single O(n) pass, without a separate length-counting pass.
- Related concepts: [Cycle detection (Floyd's tortoise & hare)](0053-cycle-detection-floyd-s-tortoise-hare.md), [Sentinel / dummy nodes](0048-sentinel-dummy-nodes.md).
