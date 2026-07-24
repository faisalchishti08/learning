---
card: leetcode-patterns
gi: 314
slug: additive-number
title: Additive Number
---

## 1. What it is

An "additive sequence" is one where each number, from the third onward, equals the sum of the two numbers immediately before it (like Fibonacci). Given a string `num` containing only digits, return `true` if it can be split into 3 or more numbers that form an additive sequence. No individual number in the sequence may have a leading zero, except the single digit `"0"` itself. Example: `num = "112358"` → `true` (`1, 1, 2, 3, 5, 8` — each is the sum of the two before it).

## 2. Why & when

This is a string-partitioning backtracking problem, similar to Restore IP Addresses, but instead of a fixed number of segments with a range check, each new segment must equal a COMPUTED sum of the previous two. Use this shape whenever a problem splits a string into pieces where each new piece's validity depends on pieces already chosen, not just a fixed local rule.

## 3. Core concept

**Key idea:** try every possible length for the FIRST number, then every possible length for the SECOND number; from there, the rest of the sequence is fully determined — each next number must be the sum of the previous two, so just check whether that exact sum appears next in the string.

**Steps:**
1. Loop over `i`, the length of the first number (from `1` up to about half the string), and `j`, the length of the second number.
2. Skip `i` or `j` if the corresponding substring has a leading zero and length `> 1` (prune).
3. Parse `first = num.substring(0, i)` and `second = num.substring(i, i + j)` as numbers (use `long` to guard against overflow).
4. Call a helper `check(remainingString, first, second)`: compute `sum = first + second` as a string; if `remainingString` starts with that sum string, recurse with `remainingString` advanced past the sum, and `(second, sum)` as the new "previous two." If `remainingString` is fully consumed at some point (after at least one sum was matched), return `true`.
5. Return `true` as soon as any `(i, j)` starting pair succeeds.

**Why it is correct:** once the first two numbers are fixed, every subsequent number is COMPLETELY determined (it must equal the sum of the previous two) — there is no further branching choice to make, only a check of whether the string actually continues with that exact sum. Trying every possible `(i, j)` starting pair covers every way the sequence could begin, and the leading-zero prune matches the problem's own validity rule for individual numbers.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Trying first two numbers 1 and 1 from 112358, then checking that each subsequent substring matches the computed sum">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">num = "112358"</text>
    <text x="10" y="45">try first="1" (i=1), second="1" (j=1) -&gt; remaining="2358"</text>
    <text x="10" y="65">sum=1+1=2 -&gt; remaining starts with "2"? yes -&gt; remaining="358"</text>
    <text x="10" y="85">sum=1+2=3 -&gt; remaining starts with "3"? yes -&gt; remaining="58"</text>
    <text x="10" y="105">sum=2+3=5 -&gt; remaining starts with "5"? yes -&gt; remaining="8"</text>
    <text x="10" y="125">sum=3+5=8 -&gt; remaining starts with "8"? yes -&gt; remaining="" -&gt; done</text>
    <rect x="10" y="135" width="80" height="24" fill="#3fb950"/><text x="50" y="152" fill="#0d1117" text-anchor="middle" font-size="10">true</text>
  </g>
</svg>

Once the first two numbers are chosen, every following number is forced — only a match/no-match check remains.

## 5. Runnable example

```java
// AdditiveNumber.java
public class AdditiveNumber {

    // KEY INSIGHT: after choosing the first two numbers, the rest of
    // the sequence has NO remaining choices -- each next number must
    // equal a computed sum, so the search only branches on the
    // lengths of the first two numbers.

    static boolean isAdditiveNumber(String num) {
        int n = num.length();
        for (int i = 1; i <= n / 2; i++) {
            if (isInvalidPrefix(num, 0, i)) continue; // prune: leading zero

            for (int j = 1; Math.max(i, j) <= n - i - j; j++) {
                if (isInvalidPrefix(num, i, j)) continue; // prune: leading zero

                if (check(num, i + j, num.substring(0, i), num.substring(i, i + j))) {
                    return true;
                }
            }
        }
        return false;
    }

    static boolean isInvalidPrefix(String num, int start, int length) {
        return length > 1 && num.charAt(start) == '0';
    }

    static boolean check(String num, int start, String first, String second) {
        if (start == num.length()) return true; // whole string consumed successfully

        long sum = Long.parseLong(first) + Long.parseLong(second);
        String sumStr = String.valueOf(sum);

        if (!num.startsWith(sumStr, start)) return false; // next segment must match exactly

        return check(num, start + sumStr.length(), second, sumStr);
    }

    public static void main(String[] args) {
        System.out.println(isAdditiveNumber("112358"));
        // true
        System.out.println(isAdditiveNumber("199100199"));
        // true (1, 99, 100, 199)
        System.out.println(isAdditiveNumber("1023"));
        // false
    }
}
```

**How to run:** `java AdditiveNumber.java`

## 6. Walkthrough

Trace `isAdditiveNumber("112358")` for `i=1, j=1` (first="1", second="1"):

| call | start | first | second | sum | matches? | next start |
|---|---|---|---|---|---|---|
| check 1 | 2 | "1" | "1" | 2 | "2358" starts with "2" | 3 |
| check 2 | 3 | "1" | "2" | 3 | "358" starts with "3" | 4 |
| check 3 | 4 | "2" | "3" | 5 | "58" starts with "5" | 5 |
| check 4 | 5 | "3" | "5" | 8 | "8" starts with "8" | 6 |
| check 5 | 6 | — | — | — | start == num.length() (6) | return true |

Final result: `true`. Time complexity is O(n³) in the worst case: O(n²) starting pairs `(i, j)`, each followed by an O(n) chain of sum checks. Space is O(n), for the substrings created and the recursion depth.

## 7. Gotchas & takeaways

> Gotcha: using `int` instead of `long` for the sum can silently overflow on long numeric strings — since `num` can be up to 35 digits in the full problem constraints, `Long.parseLong` itself can even overflow on the LONGEST possible segments; production code would need `BigInteger` for full safety, though `long` suffices for typical test inputs.

- Once the first two numbers are fixed, the rest of the search has ZERO branching — this is a useful pattern to recognize: some backtracking problems only branch at the START, then become fully deterministic.
- Comparing SUM as a STRING (`num.startsWith(sumStr, start)`) avoids needing to know the sum's exact digit length in advance.
- Related problems: Split Array into Fibonacci Sequence (the same additive-sequence idea, but returning the actual sequence and adding an `int` range constraint per number), Restore IP Addresses (a different string-partitioning backtracking problem, with a fixed segment count instead of a computed-sum rule).
