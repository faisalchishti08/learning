---
card: leetcode-patterns
gi: 315
slug: split-array-into-fibonacci-sequence
title: Split Array into Fibonacci Sequence
---

## 1. What it is

Given a string `num` of digits, split it into a Fibonacci-like sequence of AT LEAST 3 numbers, where each number fits in a 32-bit signed integer (`0` to `2147483647`), no number has a leading zero (except `"0"` itself), and each number from the third onward equals the sum of the two before it. Return any one valid sequence as a list of integers, or an empty list if none exists. Example: `num = "123456579"` → `[123,456,579]`.

## 2. Why & when

This is Additive Number's twin, but instead of just returning `true`/`false`, it must RETURN the actual sequence, and adds an explicit 32-bit integer range check per number. Use this shape whenever a problem needs not just a yes/no answer about an additive or constrained sequence, but the concrete sequence itself.

## 3. Core concept

**Key idea:** identical to Additive Number — try every length for the first two numbers, then let the rest of the sequence be fully determined by repeated sum-checking — but build up a result list as you go, and add a range check (`value > Integer.MAX_VALUE`) alongside the leading-zero check.

**Steps:**
1. Loop over `i` (length of the first number) and `j` (length of the second number), skipping any prefix with a leading zero.
2. Parse `first` and `second` as `long` (to safely detect overflow past `Integer.MAX_VALUE` before casting down).
3. If either exceeds `Integer.MAX_VALUE`, prune this pair.
4. Call `backtrack(remainingStart, sequence)`: compute `sum = last two numbers in sequence`. If `remainingStart == num.length()` AND `sequence.size() >= 3`, return `true` (success). Otherwise, check the substring at `remainingStart` matches `sum` (as digits, with the same leading-zero and range rules); if so, append `sum` to `sequence` and recurse; if that fails, remove it (un-choose) and return `false`.
5. Return the first successful `sequence` found, or an empty list if no `(i, j)` pair works.

**Why it is correct:** the same determinism argument as Additive Number applies — once the first two numbers are fixed, the rest of the sequence has no further choices, only a sum-and-match check — with the added range check ensuring every number in the returned sequence is a valid 32-bit integer, exactly as the problem requires. Building the `sequence` list alongside the recursion, and popping the last entry on failure (un-choose), keeps the same list object reusable across every explored branch.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Building the fibonacci-like sequence 123, 456, 579 from the digit string, checking each computed sum against the remaining digits">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">num = "123456579"</text>
    <text x="10" y="45">try first="123" (i=3), second="456" (j=3) -&gt; remaining="579"</text>
    <text x="10" y="65">sum=123+456=579 -&gt; remaining starts with "579"? yes, and it is the WHOLE remainder</text>
    <text x="10" y="85">sequence = [123, 456, 579], length &gt;= 3, string fully consumed</text>
    <rect x="10" y="100" width="200" height="24" fill="#3fb950"/><text x="110" y="117" fill="#0d1117" text-anchor="middle" font-size="10">return [123, 456, 579]</text>
  </g>
</svg>

The first successful `(i, j)` starting split, whose forced sum-chain exactly consumes the rest of the string, is returned.

## 5. Runnable example

```java
// SplitIntoFibonacciSequence.java
import java.util.*;

public class SplitIntoFibonacciSequence {

    // KEY INSIGHT: same forced-sum-chain idea as Additive Number, but
    // building the actual result list, with an added 32-bit integer
    // range check per number.

    static List<Integer> splitIntoFibonacci(String num) {
        List<Integer> sequence = new ArrayList<>();
        int n = num.length();

        for (int i = 1; i <= n / 2 + 1; i++) {
            if (isInvalidPrefix(num, 0, i)) continue;
            long first = Long.parseLong(num.substring(0, i));
            if (first > Integer.MAX_VALUE) break;

            for (int j = 1; i + j <= n; j++) {
                if (isInvalidPrefix(num, i, j)) continue;
                long second = Long.parseLong(num.substring(i, i + j));
                if (second > Integer.MAX_VALUE) break;

                sequence.clear();
                sequence.add((int) first);
                sequence.add((int) second);
                if (backtrack(num, i + j, sequence)) {
                    return sequence;
                }
            }
        }
        return new ArrayList<>();
    }

    static boolean backtrack(String num, int start, List<Integer> sequence) {
        if (start == num.length()) {
            return sequence.size() >= 3;
        }

        long sum = (long) sequence.get(sequence.size() - 2) + sequence.get(sequence.size() - 1);
        if (sum > Integer.MAX_VALUE) return false;

        String sumStr = String.valueOf(sum);
        if (!num.startsWith(sumStr, start)) return false;

        sequence.add((int) sum);                              // choose
        if (backtrack(num, start + sumStr.length(), sequence)) return true; // recurse
        sequence.remove(sequence.size() - 1);                 // un-choose

        return false;
    }

    static boolean isInvalidPrefix(String num, int start, int length) {
        return length > 1 && num.charAt(start) == '0';
    }

    public static void main(String[] args) {
        System.out.println(splitIntoFibonacci("123456579"));
        // [123, 456, 579]
        System.out.println(splitIntoFibonacci("11235813"));
        // [1, 1, 2, 3, 5, 8, 13]
        System.out.println(splitIntoFibonacci("1101111"));
        // [11, 0, 11, 11] (one of several valid splits; any correct one is accepted)
    }
}
```

**How to run:** `java SplitIntoFibonacciSequence.java`

## 6. Walkthrough

Trace `splitIntoFibonacci("123456579")` for `i=3, j=3` (`first=123`, `second=456`):

| call | start | sequence | sum | matches? |
|---|---|---|---|---|
| backtrack | 6 | [123, 456] | 123+456=579 | "579" matches remaining "579" |
| after append | 9 | [123, 456, 579] | — | start==num.length()(9), size&gt;=3 -&gt; return true |

Final result: `[123, 456, 579]`. Time complexity is O(n³) in the worst case, matching Additive Number: O(n²) starting pairs, each followed by an O(n) forced-sum chain. Space is O(n), for the sequence list and recursion depth.

## 7. Gotchas & takeaways

> Gotcha: checking `first > Integer.MAX_VALUE` and `second > Integer.MAX_VALUE` using `long` arithmetic BEFORE casting down to `int` is essential — comparing an already-overflowed `int` against `Integer.MAX_VALUE` would never correctly detect the overflow, since the value would have silently wrapped around to a negative number first.

- Clearing and rebuilding `sequence` at the start of each `(i, j)` trial (rather than trying to reuse a stale list) keeps the returned result correct even after a failed earlier trial.
- The `break` (not `continue`) when a prefix exceeds `Integer.MAX_VALUE` is deliberate: growing the prefix LONGER can only make the numeric value bigger, so every longer `i` or `j` from this point on would fail the same check too.
- Related problems: Additive Number (the yes/no version of this exact problem, without the range constraint or the need to return the sequence), Restore IP Addresses (a different string-partitioning backtracking problem, with a fixed segment count).
