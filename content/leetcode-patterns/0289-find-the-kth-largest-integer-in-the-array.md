---
card: leetcode-patterns
gi: 289
slug: find-the-kth-largest-integer-in-the-array
title: Find the Kth Largest Integer in the Array
---

## 1. What it is

Given an array of strings `nums`, where each string represents a non-negative integer (possibly larger than fits in a normal integer type), and an integer `k`, return the `k`-th largest integer, as a string. Example: `nums = ["3","6","7","10"]`, `k = 4` → `"3"`.

## 2. Why & when

This is Kth Largest Element in an Array, but with a twist: the numbers arrive as STRINGS, specifically so that some of them can be too large for a normal `int` or `long`. It still belongs to the size-k-heap signal, but the comparator must compare the underlying numeric value correctly without ever parsing the string into a fixed-size numeric type. Use this shape whenever a problem represents numbers as strings to hint that they may exceed standard integer limits.

## 3. Core concept

**Key idea:** compare two numeric strings without parsing them into `int`/`long` — first by LENGTH (a longer digit string is always a larger number, since these are non-negative integers with no leading zeros), then LEXICOGRAPHICALLY if the lengths match.

**Steps:**
1. Create a min-heap of strings, with a custom comparator: compare `a.length()` to `b.length()` first; if equal, compare `a` to `b` lexicographically (`String.compareTo`).
2. Offer each string in `nums` to the heap.
3. If the heap size exceeds `k`, poll (remove) the head — the current smallest of the kept elements, under this custom comparator.
4. After the scan, the heap's head is the `k`-th largest integer, as a string.

**Why it is correct:** for non-negative integers written without leading zeros, a string with more digits always represents a larger number (`"100" > "99"` even though `'1' < '9'` character by character), so comparing lengths first is both correct and avoids overflow entirely. When lengths tie, ordinary lexicographic string comparison agrees exactly with numeric comparison, since every digit position carries equal weight. The size-k heap mechanics are otherwise identical to the plain integer version.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparing numeric strings by length first then lexicographically, showing 10 as larger than 7 despite starting with a smaller digit">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">nums = ["3","6","7","10"], k = 4</text>
    <text x="10" y="45">compare "7" vs "10": length 1 &lt; length 2 -&gt; "10" is larger</text>
    <text x="10" y="65">compare "3" vs "6": same length, "3" &lt; "6" lexicographically</text>
    <text x="10" y="90">sorted ascending by custom comparator: [3, 6, 7, 10]</text>
    <rect x="10" y="100" width="150" height="24" fill="#3fb950"/><text x="85" y="117" fill="#0d1117" text-anchor="middle" font-size="10">4th largest = "3"</text>
  </g>
</svg>

Comparing by digit-string length first avoids ever parsing an oversized number into a fixed-width type.

## 5. Runnable example

```java
// KthLargestIntegerInArray.java
import java.util.PriorityQueue;
import java.util.Comparator;

public class KthLargestIntegerInArray {

    // KEY INSIGHT: for non-negative integers with no leading zeros,
    // compare digit strings by LENGTH first, then lexicographically --
    // this matches numeric comparison exactly, with no risk of
    // overflow for arbitrarily large numbers.

    static String kthLargestNumber(String[] nums, int k) {
        Comparator<String> byNumericValue = (a, b) -> {
            if (a.length() != b.length()) return a.length() - b.length();
            return a.compareTo(b);
        };

        PriorityQueue<String> heap = new PriorityQueue<>(byNumericValue);
        for (String num : nums) {
            heap.offer(num);
            if (heap.size() > k) {
                heap.poll();
            }
        }
        return heap.peek();
    }

    public static void main(String[] args) {
        System.out.println(kthLargestNumber(new String[]{"3", "6", "7", "10"}, 4));
        // 3
        System.out.println(kthLargestNumber(new String[]{"2", "21", "12", "1"}, 3));
        // 2
    }
}
```

**How to run:** `java KthLargestIntegerInArray.java`

## 6. Walkthrough

Trace `kthLargestNumber(["3","6","7","10"], 4)`:

| num | heap before | action | heap after |
|---|---|---|---|
| "3" | [] | offer | ["3"] |
| "6" | ["3"] | offer | ["3","6"] |
| "7" | ["3","6"] | offer | ["3","6","7"] |
| "10" | ["3","6","7"] | offer, size 4 &gt; 4? no, size==k | ["3","6","7","10"] |

Since `k = 4` equals the array length, the whole heap survives, and its head under the custom comparator is `"3"` (shortest length, smallest lexicographically among length-1 strings). Time complexity is O(n log k): one O(log k) heap operation per element, each comparison costing O(digits) in the worst case. Space is O(k), for the heap.

## 7. Gotchas & takeaways

> Gotcha: parsing each string into a `long` works for small inputs but silently overflows or throws `NumberFormatException` if `nums` contains numbers with more digits than `Long` can hold — the length-then-lexicographic comparator sidesteps this entirely, since it never converts the string to a numeric type.

- This problem teaches you to write a CUSTOM comparator that encodes a domain-specific ordering rule (numeric value of a digit string), while keeping the same size-k-heap mechanics as the plain-integer version.
- The "compare by length first" trick only holds because the problem guarantees non-negative integers with no leading zeros — a leading-zero string like `"007"` would break the length-based comparison.
- Related problems: Kth Largest Element in an Array (the same heap mechanics with plain integers), Sort the People (a different custom-comparator ranking problem).
