---
card: leetcode-patterns
gi: 65
slug: add-two-numbers
title: Add Two Numbers
---

## 1. What it is

You are given two non-empty linked lists representing two non-negative integers, with digits stored in reverse order (the ones digit first). Add the two numbers and return the sum as a linked list, also in reverse-digit order. Example: `l1 = [2,4,3]` (represents `342`) and `l2 = [5,6,4]` (represents `465`) → return `[7,0,8]` (represents `807`).

## 2. Why & when

This problem sits in the Fast & Slow Pointers section because it needs two pointers walking two different linked lists in lockstep, one per list, advancing together the same way `slow` and `fast` advance together in the base pattern — just at equal (not different) speeds, since each list must be consumed digit by digit. It is the standard example for "simulate manual addition, one node at a time, carrying overflow forward."

## 3. Core concept

**Key idea:** walk both lists at the same time, one node at a time, adding corresponding digits plus any carry from the previous position, and building a new list with the resulting digit while carrying the overflow to the next position — exactly like adding two numbers by hand, right to left.

**Steps:**
1. Set `p1 = l1`, `p2 = l2`, `carry = 0`, and build a result list starting from a dummy head.
2. While `p1 != null` or `p2 != null` or `carry != 0`:
   - `sum = (p1 != null ? p1.val : 0) + (p2 != null ? p2.val : 0) + carry`.
   - New digit is `sum % 10`; new `carry` is `sum / 10`.
   - Append the new digit as a node to the result list.
   - Advance `p1` and `p2` if they are not null.
3. Return the result list (after the dummy head).

**Why it is correct:** each step processes exactly one place value (ones, tens, hundreds, ...) from both numbers simultaneously, matching how addition works by hand. Carrying the overflow forward handles digit sums of `10` or more, and continuing the loop while `carry != 0` correctly handles a final carry that extends the result beyond the longer input list (e.g. `5 + 5 = 10`, one extra digit).

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Adding two numbers represented as reverse-digit linked lists">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">l1 = [2,4,3] (342)   l2 = [5,6,4] (465)</text>
    <rect x="20" y="40" width="34" height="26" fill="#161b22" stroke="#79c0ff"/><text x="37" y="58" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="60" y="40" width="34" height="26" fill="#161b22" stroke="#79c0ff"/><text x="77" y="58" fill="#e6edf3" text-anchor="middle">4</text>
    <rect x="100" y="40" width="34" height="26" fill="#161b22" stroke="#79c0ff"/><text x="117" y="58" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="20" y="80" width="34" height="26" fill="#161b22" stroke="#f0883e"/><text x="37" y="98" fill="#e6edf3" text-anchor="middle">5</text>
    <rect x="60" y="80" width="34" height="26" fill="#161b22" stroke="#f0883e"/><text x="77" y="98" fill="#e6edf3" text-anchor="middle">6</text>
    <rect x="100" y="80" width="34" height="26" fill="#161b22" stroke="#f0883e"/><text x="117" y="98" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="150" y="72" fill="#8b949e">2+5=7 (no carry), 4+6=10-&gt;0 carry 1, 3+4+1=8</text>
    <rect x="20" y="130" width="34" height="26" fill="#161b22" stroke="#3fb950"/><text x="37" y="148" fill="#e6edf3" text-anchor="middle">7</text>
    <rect x="60" y="130" width="34" height="26" fill="#161b22" stroke="#3fb950"/><text x="77" y="148" fill="#e6edf3" text-anchor="middle">0</text>
    <rect x="100" y="130" width="34" height="26" fill="#161b22" stroke="#3fb950"/><text x="117" y="148" fill="#e6edf3" text-anchor="middle">8</text>
    <text x="20" y="180" fill="#8b949e">result = [7,0,8] = 807, matching 342 + 465</text>
  </g>
</svg>

Two pointers advance through both lists together, adding digits and carrying overflow, exactly like adding numbers by hand from the ones place upward.

## 5. Runnable example

```java
// AddTwoNumbers.java
public class AddTwoNumbers {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: convert both lists to actual numbers (as
    // BigInteger to avoid overflow), add them, convert back to a list.
    // Works, but wastes effort building large intermediate numbers when
    // the list-walk approach can compute digit-by-digit directly.
    static ListNode bruteForce(ListNode l1, ListNode l2) {
        java.math.BigInteger n1 = toNumber(l1);
        java.math.BigInteger n2 = toNumber(l2);
        String sum = n1.add(n2).toString();
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int i = sum.length() - 1; i >= 0; i--) {
            cur.next = new ListNode(sum.charAt(i) - '0');
            cur = cur.next;
        }
        return dummy.next;
    }

    static java.math.BigInteger toNumber(ListNode head) {
        StringBuilder sb = new StringBuilder();
        for (ListNode cur = head; cur != null; cur = cur.next) sb.insert(0, cur.val);
        return new java.math.BigInteger(sb.toString());
    }

    // KEY INSIGHT: two pointers walking both lists in lockstep, carrying
    // overflow forward one digit at a time, reproduces manual addition
    // without ever materializing the full numbers.

    // Level 2 -- Optimal: walk both lists together with a carry.
    // O(max(n, m)) time, O(max(n, m)) space for the result list.
    public static ListNode addTwoNumbers(ListNode l1, ListNode l2) {
        ListNode dummy = new ListNode(0), cur = dummy;
        int carry = 0;
        while (l1 != null || l2 != null || carry != 0) {
            int sum = carry;
            if (l1 != null) { sum += l1.val; l1 = l1.next; }
            if (l2 != null) { sum += l2.val; l2 = l2.next; }
            carry = sum / 10;
            cur.next = new ListNode(sum % 10);
            cur = cur.next;
        }
        return dummy.next;
    }

    // Level 3 -- Hardened: lists of unequal length, and a final carry
    // that extends the result past both input lists (e.g. 5 + 5 = 10).
    static ListNode hardened(ListNode l1, ListNode l2) {
        return addTwoNumbers(l1, l2);
    }

    static ListNode build(int... vals) {
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    static void print(ListNode head) {
        StringBuilder sb = new StringBuilder();
        for (ListNode cur = head; cur != null; cur = cur.next) sb.append(cur.val).append(" ");
        System.out.println(sb.toString().trim());
    }

    public static void main(String[] args) {
        System.out.print("brute force 342+465: "); print(bruteForce(build(2, 4, 3), build(5, 6, 4)));
        System.out.print("optimal 342+465:     "); print(addTwoNumbers(build(2, 4, 3), build(5, 6, 4)));
        System.out.print("5+5 (extra carry):   "); print(hardened(build(5), build(5)));
        System.out.print("unequal lengths:     "); print(hardened(build(9, 9), build(1)));
    }
}
```

How to run: save as `AddTwoNumbers.java`, then run `java AddTwoNumbers.java`.

## 6. Walkthrough

Dry run of `addTwoNumbers` on `l1 = [2,4,3]`, `l2 = [5,6,4]`:

| step | l1 val | l2 val | carry in | sum | new digit | carry out |
|---|---|---|---|---|---|---|
| 1 | 2 | 5 | 0 | 7 | 7 | 0 |
| 2 | 4 | 6 | 0 | 10 | 0 | 1 |
| 3 | 3 | 4 | 1 | 8 | 8 | 0 |
| — | null | null | 0 | loop ends (both lists exhausted, no carry) | | |

Result list: `[7, 0, 8]`, representing `807`, matching `342 + 465 = 807`. Time complexity: O(max(n, m)), where `n` and `m` are the two list lengths. Space complexity: O(max(n, m)) for the result list (plus possibly one extra node for a final carry).

## 7. Gotchas & takeaways

> Gotcha: stopping the loop as soon as either `l1` or `l2` becomes null drops the remaining digits of the longer list, and stopping without checking `carry != 0` drops a final carry digit (e.g. `5 + 5` would wrongly produce `[0]` instead of `[0, 1]`).

- The dummy-head technique (`dummy.next` as the real answer) avoids special-casing the first node when building the result list — a pattern worth reusing in any "build a new list" problem.
- Related problems: Multiply Strings (same digit-by-digit-with-carry idea, but for multiplication), Merge Two Sorted Lists (similar two-pointer walk over two lists, without arithmetic).
