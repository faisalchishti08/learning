---
card: leetcode-patterns
gi: 103
slug: split-linked-list-in-parts
title: Split Linked List in Parts
---

## 1. What it is

Given the `head` of a linked list and an integer `k`, split the list into `k` consecutive parts with sizes as equal as possible. Parts must be constructed left to right, and any earlier part must never be smaller than a later part by more than one node. Return an array of the `k` part heads (some parts may be `null` if there are fewer nodes than `k`). Example: `head = [1,2,3]`, `k = 5` → `[[1],[2],[3],[],[]]`.

## 2. Why & when

This problem needs precise length-based boundary computation, similar to Rotate List, combined with cutting the list into pieces by breaking `next` pointers at computed positions — the same relinking skill used throughout this section, applied to produce multiple sub-lists instead of one reordered list.

## 3. Core concept

**Key idea:** first measure the list's total length `n`. Compute the base size `n / k` and the remainder `n % k` — the first `remainder` parts get one extra node each, so sizes stay as equal as possible. Walk through the list once, cutting off each part at its computed size.

**Steps:**
1. Measure `n`, the total number of nodes.
2. Compute `baseSize = n / k` and `extra = n % k`.
3. For each of the `k` parts (index `i` from `0` to `k - 1`):
   - This part's size is `baseSize + (i < extra ? 1 : 0)`.
   - If the size is `0`, this part is `null`.
   - Otherwise, record the current node as this part's head, walk `size - 1` more steps to reach this part's tail, save `next = tail.next`, cut `tail.next = null`, and move the walking pointer to `next` for the next part.

**Why it is correct:** distributing the remainder `extra` nodes one at a time to the first `extra` parts guarantees no part is ever more than one node larger than any later part, exactly matching the problem's balance requirement. Cutting each part's tail via `tail.next = null` correctly separates it from the rest of the list without needing to copy any nodes.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Splitting a linked list into balanced parts">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1,2,3,4,5,6,7], k = 3 (n=7, baseSize=2, extra=1)</text>
    <rect x="20" y="45" width="90" height="24" fill="#161b22" stroke="#79c0ff"/><text x="65" y="61" fill="#e6edf3" text-anchor="middle" font-size="10">part 0: [1,2,3]</text>
    <rect x="120" y="45" width="60" height="24" fill="#161b22" stroke="#f0883e"/><text x="150" y="61" fill="#e6edf3" text-anchor="middle" font-size="10">part 1: [4,5]</text>
    <rect x="190" y="45" width="60" height="24" fill="#161b22" stroke="#f0883e"/><text x="220" y="61" fill="#e6edf3" text-anchor="middle" font-size="10">part 2: [6,7]</text>
    <text x="20" y="110" fill="#8b949e">7 nodes / 3 parts = base size 2, remainder 1 -&gt; first part gets the extra node (size 3)</text>
  </g>
</svg>

The first part absorbs the single extra node (size `3`), while the remaining parts each get the base size (`2`), keeping every part within one node of every other.

## 5. Runnable example

```java
// SplitLinkedListInParts.java
public class SplitLinkedListInParts {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy all values into an array, compute
    // part boundaries, rebuild each part as a brand-new list. O(n) time,
    // O(n) space -- wastes memory an in-place cut does not need.
    static ListNode[] bruteForce(ListNode head, int k) {
        java.util.List<Integer> vals = new java.util.ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) vals.add(cur.val);
        int n = vals.size(), baseSize = n / k, extra = n % k;
        ListNode[] result = new ListNode[k];
        int idx = 0;
        for (int i = 0; i < k; i++) {
            int size = baseSize + (i < extra ? 1 : 0);
            ListNode dummy = new ListNode(0), cur = dummy;
            for (int j = 0; j < size; j++) { cur.next = new ListNode(vals.get(idx++)); cur = cur.next; }
            result[i] = dummy.next;
        }
        return result;
    }

    // KEY INSIGHT: distributing the remainder one extra node at a time to
    // the FIRST `extra` parts keeps every part within one node of every
    // other -- an in-place cut (tail.next = null) then separates each
    // part without copying any node.

    // Level 2 -- Optimal: measure length, compute sizes, cut in place.
    // O(n) time, O(1) extra space (excluding the output array).
    public static ListNode[] splitListToParts(ListNode head, int k) {
        int n = 0;
        for (ListNode cur = head; cur != null; cur = cur.next) n++;

        int baseSize = n / k, extra = n % k;
        ListNode[] result = new ListNode[k];
        ListNode curr = head;

        for (int i = 0; i < k; i++) {
            int size = baseSize + (i < extra ? 1 : 0);
            if (size == 0) { result[i] = null; continue; }

            result[i] = curr;
            for (int j = 0; j < size - 1; j++) curr = curr.next;
            ListNode next = curr.next;
            curr.next = null;
            curr = next;
        }
        return result;
    }

    // Level 3 -- Hardened: k larger than the number of nodes (some parts
    // must be null), and k == 1 (the whole list is one part).
    static ListNode[] hardened(ListNode head, int k) {
        return splitListToParts(head, k);
    }

    static ListNode build(int... vals) {
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    static void printParts(ListNode[] parts) {
        for (ListNode part : parts) {
            StringBuilder sb = new StringBuilder("[");
            for (ListNode cur = part; cur != null; cur = cur.next) sb.append(cur.val).append(cur.next != null ? "," : "");
            sb.append("]");
            System.out.print(sb + " ");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        printParts(bruteForce(build(1, 2, 3, 4, 5, 6, 7), 3));
        printParts(splitListToParts(build(1, 2, 3, 4, 5, 6, 7), 3));

        System.out.print("k > n: "); printParts(hardened(build(1, 2, 3), 5));
    }
}
```

How to run: save as `SplitLinkedListInParts.java`, then run `java SplitLinkedListInParts.java`.

## 6. Walkthrough

Dry run of `splitListToParts({1,2,3,4,5,6,7}, 3)`, `n = 7`, `baseSize = 2`, `extra = 1`:

| part i | size | head | tail found after (size-1) steps | next (saved) |
|---|---|---|---|---|
| 0 | 2+1=3 | 1 | walk 2 steps -> 3 | 4 |
| 1 | 2+0=2 | 4 | walk 1 step -> 5 | 6 |
| 2 | 2+0=2 | 6 | walk 1 step -> 7 | null |

Result: `[[1,2,3], [4,5], [6,7]]`. Time complexity: O(n) — one pass to measure length, one pass to cut. Space complexity: O(1) extra space, not counting the output array.

## 7. Gotchas & takeaways

> Gotcha: computing `extra` nodes distribution wrong (e.g. giving the extra node to the *last* parts instead of the *first*) still produces `k` parts of correct total size, but violates the problem's explicit rule that earlier parts must never be smaller than later ones.

- The "base size plus remainder distributed to the front" formula is a reusable pattern for any "split into k balanced groups" problem, not just linked lists.
- Related problems: Rotate List (also needs precise length-based boundary computation), Reorder List (splits at a computed boundary, though only into two parts).
