---
card: leetcode-patterns
gi: 58
slug: palindrome-linked-list
title: Palindrome Linked List
---

## 1. What it is

Given the `head` of a singly linked list, determine whether it reads the same forwards and backwards. Example: `head = [1,2,2,1]` → `true`. Example: `head = [1,2]` → `false`.

## 2. Why & when

The obvious approach copies every value into an array, then checks the array reads the same from both ends — O(n) time but O(n) extra space. Fast & slow pointers finds the middle of the list in one pass first, letting you reverse only the second half and compare it against the first half in place, cutting space down to O(1).

## 3. Core concept

**Key idea:** find the middle of the list with fast & slow pointers, reverse the second half in place, then walk two pointers — one from the original head, one from the reversed second half's head — comparing values as they move forward together.

**Steps:**
1. Use fast & slow pointers to find the middle node (as in Middle of the Linked List).
2. Reverse the linked list starting from the middle node, so the second half now points backward.
3. Walk one pointer from the original `head` and another from the head of the reversed second half, comparing values at each step.
4. If every pair of values matches, the list is a palindrome.

**Why it is correct:** a palindrome list's first half and reversed second half are identical value-by-value. Reversing the second half turns "compare forward vs backward" into "compare two forward-moving pointers", which is a simple linear scan.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Palindrome check by reversing the second half">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">head = [1, 2, 2, 1]</text>
    <text x="20" y="50" fill="#8b949e">step 1: find middle -&gt; split into [1,2] and [2,1]</text>
    <text x="20" y="80" fill="#8b949e">step 2: reverse second half -&gt; [2,1] becomes [1,2]</text>
    <rect x="20" y="100" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="40" y="120" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="70" y="100" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="90" y="120" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="130" y="120" fill="#8b949e">vs</text>
    <rect x="160" y="100" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="180" y="120" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="210" y="100" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="230" y="120" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="20" y="165" fill="#8b949e">step 3: compare pointers moving forward through both halves -- 1==1, 2==2 -&gt; palindrome</text>
  </g>
</svg>

Reversing the second half turns a "compare front-to-back against back-to-front" problem into a simple side-by-side forward scan.

## 5. Runnable example

```java
// PalindromeLinkedList.java
public class PalindromeLinkedList {

    static class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    // Level 1 -- Brute force: copy values into an array, check with two
    // index pointers from both ends. O(n) time, O(n) space -- wastes
    // memory holding a full copy of every value.
    static boolean bruteForce(ListNode head) {
        java.util.List<Integer> vals = new java.util.ArrayList<>();
        for (ListNode cur = head; cur != null; cur = cur.next) vals.add(cur.val);
        int i = 0, j = vals.size() - 1;
        while (i < j) {
            if (!vals.get(i).equals(vals.get(j))) return false;
            i++; j--;
        }
        return true;
    }

    // KEY INSIGHT: fast &amp; slow pointers finds the middle in one pass, so
    // the list can be split and its second half reversed IN PLACE --
    // avoiding a full array copy entirely.

    // Level 2 -- Optimal: find middle, reverse second half, compare.
    // O(n) time, O(1) extra space.
    public static boolean isPalindrome(ListNode head) {
        if (head == null || head.next == null) return true;

        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }

        ListNode secondHalf = reverse(slow);
        ListNode p1 = head, p2 = secondHalf;
        boolean result = true;
        while (p2 != null) {
            if (p1.val != p2.val) { result = false; break; }
            p1 = p1.next;
            p2 = p2.next;
        }
        reverse(secondHalf); // restore the list's original shape
        return result;
    }

    static ListNode reverse(ListNode head) {
        ListNode prev = null;
        while (head != null) {
            ListNode next = head.next;
            head.next = prev;
            prev = head;
            head = next;
        }
        return prev;
    }

    // Level 3 -- Hardened: handles empty and single-node lists, both
    // trivially palindromes.
    static boolean hardened(ListNode head) {
        return isPalindrome(head);
    }

    static ListNode build(int... vals) {
        ListNode dummy = new ListNode(0), cur = dummy;
        for (int v : vals) { cur.next = new ListNode(v); cur = cur.next; }
        return dummy.next;
    }

    public static void main(String[] args) {
        System.out.println("[1,2,2,1] brute:   " + bruteForce(build(1, 2, 2, 1)));
        System.out.println("[1,2,2,1] optimal: " + isPalindrome(build(1, 2, 2, 1)));
        System.out.println("[1,2] optimal:     " + isPalindrome(build(1, 2)));
        System.out.println("single node:       " + hardened(build(7)));
        System.out.println("empty list:        " + hardened(null));
    }
}
```

How to run: save as `PalindromeLinkedList.java`, then run `java PalindromeLinkedList.java`.

## 6. Walkthrough

Dry run of `isPalindrome` on `1 -> 2 -> 2 -> 1`:

1. Fast & slow pointers find the middle: `slow` ends on the second `2` (index 2).
2. Reverse from `slow` onward: the second half `2 -> 1` becomes `1 -> 2`.
3. Compare `p1` (from original head: `1, 2, ...`) against `p2` (from reversed half: `1, 2`): `1 == 1`, then `2 == 2`. Both match.
4. `p2` reaches `null` after two comparisons, so the loop ends and the method returns `true`.

Time complexity: O(n) — one pass to find the middle, one pass to reverse, one pass to compare. Space complexity: O(1), since the reversal happens in place.

## 7. Gotchas & takeaways

> Gotcha: reversing the second half mutates the original list's structure. If the list must be left unmodified after the check (common in interview follow-ups), reverse it back before returning, as shown in the example above.

- This problem chains two earlier techniques: find-the-middle (from this pattern) and in-place list reversal.
- Related problems: Middle of the Linked List (step 1 here), Reorder List (also finds the middle, then merges two halves instead of comparing them).
