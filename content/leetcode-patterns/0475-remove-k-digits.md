---
card: leetcode-patterns
gi: 475
slug: remove-k-digits
title: Remove K Digits
---

## 1. What it is

You get a non-negative integer as a string `num` and an integer `k`. Remove exactly `k` digits from `num` so that the remaining digits, kept in their original order, form the smallest possible number. Example: `num = "1432219"`, `k = 3` → `"1219"`.

## 2. Why & when

"Remove digits to make the number as small as possible while keeping order" is the greedy-removal signal from the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family: whenever a bigger digit sits before a smaller one, removing the bigger digit always helps (it lowers a more significant place value). A monotonic (increasing) stack applies that rule greedily, digit by digit. Constraints: `num` can be up to 100,000 digits.

## 3. Core concept

**Key idea:** scan the digits left to right, keeping a stack that stays non-decreasing. Whenever the current digit is smaller than the digit on top of the stack, and you still have removals left (`k > 0`), pop the top — removing a bigger digit that sits before a smaller one always shrinks the number, because it lowers a higher place value.

**Steps:**
1. Use a stack (or a `StringBuilder` used as a stack) of digit characters.
2. For each digit `d` in `num`: while the stack is not empty, its top is greater than `d`, and `k > 0`, pop the top and decrement `k`.
3. Push `d`.
4. If `k > 0` after the scan (the number was already non-decreasing), remove `k` digits from the end of the stack — those are the largest, least significant digits left.
5. Strip any leading zeros from the result, and return `"0"` if everything was removed.

**Why removing from the end when `k` is still positive is safe:** if the whole number never had a "bigger digit before a smaller one" to trigger a pop, it is already sorted non-decreasing — the digits at the end are the largest, so trimming from there removes the least value.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Increasing stack popping bigger digits as smaller ones arrive, with a removal budget k">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">num = "1432219", k = 3</text>
    <text x="20" y="45" fill="#8b949e">'1': push. stack="1"</text>
    <text x="20" y="65" fill="#8b949e">'4': push (1&lt;4). stack="14"</text>
    <text x="20" y="85" fill="#8b949e">'3': pop '4' (4&gt;3, k=3-&gt;2). push. stack="13"</text>
    <text x="20" y="105" fill="#8b949e">'2': pop '3' (3&gt;2, k=2-&gt;1). push. stack="12"</text>
    <text x="20" y="125" fill="#8b949e">'2': push (2 not &gt; 2). stack="122"</text>
    <text x="20" y="145" fill="#8b949e">'1': pop '2' (2&gt;1, k=1-&gt;0). push. stack="121"</text>
    <text x="20" y="165" fill="#3fb950">'9': k=0, no pop. push. stack="1219" -&gt; answer "1219"</text>
  </g>
</svg>

Each smaller digit pops off any larger digits directly before it, as long as the removal budget `k` allows it.

## 5. Runnable example

**Level 1 — Brute force.** Try every combination of `k` removed positions and keep the smallest resulting number. Combinatorial, far too slow for large inputs.

**KEY INSIGHT:** a bigger digit sitting directly before a smaller one should always be removed first, because it occupies a higher place value; greedily enforcing "stack stays non-decreasing" makes each of the `k` removals as impactful as possible.

**Level 2 — Optimal.** Increasing monotonic stack with a removal budget, O(n).

**Level 3 — Hardened.** Handles leftover budget after the scan, leading zeros in the result, and `k` equal to the full length (answer `"0"`).

```java
// RemoveKDigits.java
public class RemoveKDigits {

    // Level 2 & 3: increasing monotonic stack, O(n)
    static String removeKdigits(String num, int k) {
        StringBuilder stack = new StringBuilder();
        for (char d : num.toCharArray()) {
            while (k > 0 && stack.length() > 0 && stack.charAt(stack.length() - 1) > d) {
                stack.deleteCharAt(stack.length() - 1);
                k--;
            }
            stack.append(d);
        }

        // if budget remains, the number was already non-decreasing: trim from the end
        while (k > 0 && stack.length() > 0) {
            stack.deleteCharAt(stack.length() - 1);
            k--;
        }

        int start = 0;
        while (start < stack.length() - 1 && stack.charAt(start) == '0') {
            start++;
        }
        String result = stack.substring(start);
        return result.isEmpty() ? "0" : result;
    }

    public static void main(String[] args) {
        System.out.println(removeKdigits("1432219", 3)); // "1219"
        System.out.println(removeKdigits("10200", 1));   // "200"
        System.out.println(removeKdigits("10", 2));       // "0"
        System.out.println(removeKdigits("112", 1));      // "11" (already non-decreasing, trims end)
    }
}
```

**How to run:** save as `RemoveKDigits.java`, then run `java RemoveKDigits.java`.

## 6. Walkthrough

Trace `removeKdigits("1432219", 3)`:

| digit | stack before | k before | action | stack after | k after |
|---|---|---|---|---|---|
| 1 | "" | 3 | push | "1" | 3 |
| 4 | "1" | 3 | 1 not > 4, push | "14" | 3 |
| 3 | "14" | 3 | pop '4' (4>3) | "1" | 2 |
| — | "1" | 2 | 1 not > 3, push | "13" | 2 |
| 2 | "13" | 2 | pop '3' (3>2) | "1" | 1 |
| — | "1" | 1 | 1 not > 2, push | "12" | 1 |
| 2 | "12" | 1 | 2 not > 2, push | "122" | 1 |
| 1 | "122" | 1 | pop '2' (2>1) | "12" | 0 |
| — | "12" | 0 | push | "121" | 0 |
| 9 | "121" | 0 | k=0, no pop, push | "1219" | 0 |

No leftover budget, no leading zeros. Result: `"1219"`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: forgetting the "trim from the end if `k` still positive after the scan" step fails on already-sorted inputs like `"112"` with `k=1` — the stack never pops during the scan, so the budget must be spent at the end.

- Signal: "remove digits to minimize the number, keep relative order" is a greedy removal problem solved by an increasing monotonic stack.
- Always strip leading zeros afterward, and return `"0"` for an empty or all-zero result.
- Related problems: Remove Duplicate Letters (a similar greedy-stack removal, with a "last occurrence" twist instead of a budget `k`).
