---
card: leetcode-patterns
gi: 601
slug: plus-one
title: Plus One
---

## 1. What it is

Given an array of digits representing a non-negative integer (most significant digit first, no leading zeros except the number `0` itself), return the array of digits representing that integer plus one. Example: `digits=[1,2,3]` → `[1,2,4]`; `digits=[9,9,9]` → `[1,0,0,0]` (the array grows by one digit, since `999 + 1 = 1000`).

## 2. Why & when

This is elementary-school addition, applied to a digit array instead of a number: add `1` to the last digit, and if that causes a carry (the digit becomes `10`), propagate the carry leftward, exactly like adding `1` to `...99`. The one twist beyond simple digit arithmetic is handling the case where the carry propagates all the way past the first digit, requiring the result array to grow by one position.

## 3. Core concept

**Key idea:** walk the digits array from the **last** digit to the first. Add `1` (as a carry) to the current digit. If the result is `10`, set that position to `0` and continue the carry into the next digit to the left. If the result is less than `10`, no further carry is needed — set that digit and return immediately, since every digit to its left is unaffected.

**Steps:**
1. Walk `i` from `digits.length - 1` down to `0`.
2. If `digits[i] < 9`, increment it by one and return the array immediately — the addition is complete, no carry propagates further left.
3. If `digits[i] == 9`, set it to `0` (the carry continues) and move to `i - 1`.
4. If the loop finishes without an early return, every original digit was `9` (like `999`), meaning the carry propagated past the first digit. Return a new array one element longer than the original, with a leading `1` followed by all zeros (matching `999 + 1 = 1000`).

**Why the early return the moment a non-9 digit is found is correct:** once a digit that is not `9` absorbs the carry (becomes one larger, with no overflow past `9`), there is nothing left to propagate — every digit to its left in a valid addition like this remains completely unchanged, so returning immediately avoids unnecessary work on the rest of the array.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Adding one to [9,9,9]: the carry propagates through all three 9s, growing the array by one digit">
  <g font-family="sans-serif" font-size="12">
    <rect x="60" y="30" width="50" height="35" fill="#161b22" stroke="#f0883e"/><text x="85" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">9-&gt;0</text>
    <rect x="120" y="30" width="50" height="35" fill="#161b22" stroke="#f0883e"/><text x="145" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">9-&gt;0</text>
    <rect x="180" y="30" width="50" height="35" fill="#161b22" stroke="#f0883e"/><text x="205" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">9-&gt;0</text>
    <text x="145" y="90" fill="#79c0ff" text-anchor="middle">carry propagates past the leftmost digit</text>
    <rect x="330" y="30" width="50" height="35" fill="#161b22" stroke="#3fb950"/><text x="355" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">1</text>
    <rect x="390" y="30" width="50" height="35" fill="#161b22" stroke="#30363d"/><text x="415" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">0</text>
    <rect x="450" y="30" width="50" height="35" fill="#161b22" stroke="#30363d"/><text x="475" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">0</text>
    <rect x="510" y="30" width="50" height="35" fill="#161b22" stroke="#30363d"/><text x="535" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">0</text>
    <text x="440" y="90" fill="#79c0ff" text-anchor="middle">new array, one digit longer: [1,0,0,0]</text>
  </g>
</svg>

Every digit turns from `9` to `0`, and since the carry never finds a non-9 digit to stop at, a new leading `1` is prepended — the array grows by exactly one position.

## 5. Runnable example

**Level 1 — Brute force.** Convert the digit array to a `long` (or `BigInteger` for very long arrays), add `1`, then convert back to a digit array. Works for reasonably small arrays, but risks overflow for very long digit sequences, and does unnecessary numeric conversion work.

**KEY INSIGHT:** addition only needs to touch digits up to and including the first one that is *not* `9` — every digit array operation can be done in place, comparing each digit against `9` to decide whether the carry continues, without ever forming the full number.

**Level 2 — Optimal.** Right-to-left in-place walk with early return, O(n) worst case (all `9`s), O(1) extra space except for the rare array-growth case.

**Level 3 — Hardened.** Correctly handles the all-`9`s case by allocating a new, longer array with a leading `1`, and correctly returns immediately (not continuing the loop) once a digit absorbs the carry without overflowing.

```java
// PlusOne.java
import java.util.*;

public class PlusOne {

    public static int[] plusOne(int[] digits) {
        for (int i = digits.length - 1; i >= 0; i--) {
            if (digits[i] < 9) {
                digits[i]++;
                return digits;
            }
            digits[i] = 0;
        }
        // every digit was 9: the carry propagated past the first digit.
        int[] result = new int[digits.length + 1];
        result[0] = 1;
        return result;
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(plusOne(new int[]{1, 2, 3}))); // [1, 2, 4]
        System.out.println(Arrays.toString(plusOne(new int[]{9, 9, 9}))); // [1, 0, 0, 0]
        System.out.println(Arrays.toString(plusOne(new int[]{1, 9})));   // [2, 0]
    }
}
```

**How to run:** save as `PlusOne.java`, then run `java PlusOne.java`.

## 6. Walkthrough

Dry-run `plusOne([1,9])`:

| i | digits[i] | < 9? | action |
|---|---|---|---|
| 1 | 9 | no | set digits[1]=0, continue carry |
| 0 | 1 | yes | digits[0]++ = 2, return immediately |

Result: `[2, 0]`. The carry from the last digit (`9 -> 0`) propagates into the first digit (`1 -> 2`), which is not `9`, so the loop returns right there — matching `19 + 1 = 20`.

## 7. Gotchas & takeaways

> Gotcha: forgetting the special case for an all-`9`s input (like `[9,9,9]`) and letting the loop simply exit without returning anything produces a `null` or an unmodified array — the loop must explicitly handle "carry propagated past every digit" by allocating a new, longer array.

- Signal: "digit array plus one, propagate a carry" is the right-to-left in-place carry-propagation signal, identical in spirit to manual addition.
- The loop can return the moment it finds a digit that does not overflow — no need to touch digits further left.
- Related problems: Add Binary (the same carry-propagation idea, base 2 instead of base 10, on two digit strings instead of one array plus a constant).
