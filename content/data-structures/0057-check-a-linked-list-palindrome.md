---
card: data-structures
gi: 57
slug: check-a-linked-list-palindrome
title: Check a linked-list palindrome
---

## 1. What it is

A **palindrome** is a sequence that reads the same forwards and backwards, like `1 -> 2 -> 3 -> 2 -> 1`. Checking a linked list for this property means comparing its values from both ends inward, but a singly linked list has no `previous` pointer — you cannot walk backwards the way you can index an array from the end.

## 2. Why & when

This tests whether you can solve a "compare from both ends" problem on a structure that only supports forward movement. It comes up whenever you need to verify symmetry in a stream of values you can only read once, in order — for example, validating that a sequence of logged events mirrors itself. The naive fix is to copy every value into an array first; the sharper solution reverses only half the list in place, using O(1) extra space.

## 3. Core concept

**Copy to an array, then compare with two indices.** Walk the list once, storing every value in an `ArrayList` or array. Then compare index `i` from the front with index `n-1-i` from the back, moving inward. This costs O(n) extra space but is simple and correct.

**Find the middle, then reverse the second half.** Use the slow/fast pointer technique to find the middle node in one pass. Reverse the second half of the list in place, so it now points backwards from the middle to the tail. Walk the first half and the reversed second half together, comparing values at each step — if every pair matches, the list is a palindrome.

**Why reversing half the list is enough.** A palindrome is symmetric around its center. Once the second half points backwards, its values run in reverse order — exactly the order needed to compare against the first half moving forwards. You never need a full reversed copy, only the back half.

**Restoring the list (optional but polite).** Reversing the second half mutates the original list's structure. If the caller still needs the original list afterward, reverse the second half back before returning.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A five node list split at the middle, with the second half reversed so it can be compared against the first half node by node">
  <g font-family="sans-serif" font-size="11">
    <text x="10" y="20" fill="#8b949e">original: 1 -&gt; 2 -&gt; 3 -&gt; 2 -&gt; 1</text>
    <rect x="20" y="50" width="36" height="26" fill="#161b22" stroke="#8b949e"/><text x="38" y="67" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <rect x="70" y="50" width="36" height="26" fill="#161b22" stroke="#8b949e"/><text x="88" y="67" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <rect x="120" y="50" width="36" height="26" fill="#0d1117" stroke="#f0883e"/><text x="138" y="67" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <text x="138" y="100" fill="#f0883e" text-anchor="middle">middle</text>
    <text x="10" y="140" fill="#8b949e">first half:  1 -&gt; 2  (forward)</text>
    <text x="10" y="160" fill="#79c0ff">second half: 1 -&gt; 2  (reversed from 2 -&gt; 1)</text>
    <line x1="30" y1="170" x2="140" y2="170" stroke="#79c0ff"/>
    <text x="330" y="170" fill="#79c0ff" text-anchor="middle">compare pairwise: 1==1, 2==2 -&gt; palindrome</text>
  </g>
</svg>

The second half `2 -> 1` is reversed to `1 -> 2`, so it lines up value-by-value with the first half.

## 5. Runnable example

```java
// LinkedListPalindrome.java
import java.util.ArrayList;
import java.util.List;

public class LinkedListPalindrome {

    static class Node {
        int value;
        Node next;
        Node(int value) { this.value = value; }
    }

    // Basic: copy values into a list, compare with two indices.
    static boolean isPalindromeByCopy(Node head) {
        List<Integer> values = new ArrayList<>();
        for (Node c = head; c != null; c = c.next) values.add(c.value);
        int left = 0, right = values.size() - 1;
        while (left < right) {
            if (!values.get(left).equals(values.get(right))) return false;
            left++;
            right--;
        }
        return true;
    }

    static void basicLevel() {
        Node head = build(1, 2, 3, 2, 1);
        System.out.println("basic: 1,2,3,2,1 is palindrome -> " + isPalindromeByCopy(head));
    }

    // Intermediate: find the middle with slow/fast pointers, reverse the second half, compare in place.
    static boolean isPalindromeInPlace(Node head) {
        if (head == null || head.next == null) return true;

        Node slow = head, fast = head;
        while (fast.next != null && fast.next.next != null) { // slow lands on the last node of the first half
            slow = slow.next;
            fast = fast.next.next;
        }

        Node secondHalfHead = reverse(slow.next);
        Node p1 = head, p2 = secondHalfHead;
        boolean result = true;
        while (p2 != null) { // second half is shorter or equal, so it drives the comparison
            if (p1.value != p2.value) { result = false; break; }
            p1 = p1.next;
            p2 = p2.next;
        }

        slow.next = reverse(secondHalfHead); // restore the original list shape
        return result;
    }

    static Node reverse(Node head) {
        Node prev = null;
        while (head != null) {
            Node next = head.next;
            head.next = prev;
            prev = head;
            head = next;
        }
        return prev;
    }

    static void intermediateLevel() {
        Node head = build(1, 2, 3, 2, 1);
        System.out.println("intermediate: 1,2,3,2,1 is palindrome (in place) -> " + isPalindromeInPlace(head));
        System.out.println("intermediate: list restored -> " + toString(head));
    }

    // Advanced: even-length list and a non-palindrome, to confirm both branches work.
    static void advancedLevel() {
        Node even = build(1, 2, 2, 1);
        System.out.println("advanced: 1,2,2,1 is palindrome -> " + isPalindromeInPlace(even));

        Node notPalindrome = build(1, 2, 3);
        System.out.println("advanced: 1,2,3 is palindrome -> " + isPalindromeInPlace(notPalindrome));
    }

    static Node build(int... vals) {
        Node dummy = new Node(0);
        Node tail = dummy;
        for (int v : vals) { tail.next = new Node(v); tail = tail.next; }
        return dummy.next;
    }

    static String toString(Node head) {
        StringBuilder sb = new StringBuilder();
        for (Node c = head; c != null; c = c.next) sb.append(c.value).append(c.next != null ? "," : "");
        return sb.toString();
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `LinkedListPalindrome.java`, then run `java LinkedListPalindrome.java`.

## 6. Walkthrough

1. `basicLevel()` copies `1,2,3,2,1` into an `ArrayList`, then compares index `0` with `4`, then `1` with `3` — both pairs match, so the list is a palindrome.
2. `intermediateLevel()` moves `slow` and `fast` from the head. `fast` reaches the end after `slow` reaches node `3` (the middle), because `fast` moves two steps for every one of `slow`'s. `reverse(slow.next)` turns `2 -> 1` into `1 -> 2` and returns its new head.
3. The walkthrough then compares `p1` (`1 -> 2 -> 3`) against `p2` (`1 -> 2`) two steps: `1==1`, then `2==2`. Since `p2` runs out first, the loop stops — the odd middle node `3` is never compared, which is correct, since a middle element in an odd-length palindrome has no partner.
4. Finally, `slow.next = reverse(secondHalfHead)` reverses `1 -> 2` back to `2 -> 1` and reattaches it, restoring the list to its original shape before returning.

## 7. Gotchas & takeaways

> Gotcha: forgetting to restore the list after reversing the second half leaves the caller with a corrupted structure — if anything else holds a reference to the original tail node, it now points into the middle of a broken chain. Always reverse back unless you are certain the list will be discarded.

- Copying values into an array is the simplest correct solution, at O(n) extra space.
- The in-place approach finds the middle with slow/fast pointers, reverses only the second half, and compares in O(1) extra space.
- For an odd-length list, the middle node is naturally skipped in the comparison, since the second half is always the shorter or equal-length side.
- Related concepts: [Reverse a linked list](0052-reverse-a-linked-list-iterative-recursive.md), [Find the middle / nth from end](0054-find-middle-nth-from-end.md).
