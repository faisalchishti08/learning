---
card: leetcode-patterns
gi: 605
slug: fizz-buzz
title: Fizz Buzz
---

## 1. What it is

Given an integer `n`, return a string array `answer` of length `n` where, for each `i` from `1` to `n`: `answer[i-1] = "FizzBuzz"` if `i` is divisible by both `3` and `5`; `"Fizz"` if divisible by `3` only; `"Buzz"` if divisible by `5` only; otherwise the string form of `i` itself. Example: `n=5` → `["1","2","Fizz","4","Buzz"]`; `n=15` produces `"FizzBuzz"` at position `15` (divisible by both `3` and `5`).

## 2. Why & when

This is a straightforward single-pass problem testing careful conditional ordering rather than any real algorithmic insight — its main pitfall is check order, not complexity. It appears here as the canonical example of the simplest tier of the Math & Geometry family: pure modular-arithmetic checks (`% 3`, `% 5`), applied once per number, no data structure involved.

## 3. Core concept

**Key idea:** for each number `i` from `1` to `n`, check divisibility by `3` and `5` **together first**, before checking either individually — checking `i % 3 == 0` alone first, and appending `"Fizz"` immediately, would incorrectly miss numbers that are *also* divisible by `5` (like `15`), since the function would have already produced `"Fizz"` and moved on before ever checking `%5`.

**Steps:**
1. For `i` from `1` to `n`:
2. If `i % 15 == 0` (equivalently, `i % 3 == 0 && i % 5 == 0`), append `"FizzBuzz"`.
3. Else if `i % 3 == 0`, append `"Fizz"`.
4. Else if `i % 5 == 0`, append `"Buzz"`.
5. Else, append `String.valueOf(i)`.

**Why `i % 15 == 0` is equivalent to checking both `%3` and `%5`:** `15` is the least common multiple of `3` and `5`. A number divisible by both `3` and `5` is, by definition, divisible by their least common multiple — so checking `% 15` in a single operation is a shorthand for the combined condition, though checking both conditions with `&&` is equally correct and arguably clearer.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A decision order: check divisible-by-15 first, then by-3, then by-5, then default to the number itself">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="140" height="35" rx="4" fill="#161b22" stroke="#3fb950"/><text x="90" y="42" fill="#e6edf3" text-anchor="middle" font-size="11">i%15==0? FizzBuzz</text>
    <rect x="190" y="20" width="140" height="35" rx="4" fill="#161b22" stroke="#f0883e"/><text x="260" y="42" fill="#e6edf3" text-anchor="middle" font-size="11">i%3==0? Fizz</text>
    <rect x="360" y="20" width="140" height="35" rx="4" fill="#161b22" stroke="#79c0ff"/><text x="430" y="42" fill="#e6edf3" text-anchor="middle" font-size="11">i%5==0? Buzz</text>
    <rect x="530" y="20" width="140" height="35" rx="4" fill="#161b22" stroke="#8b949e"/><text x="600" y="42" fill="#e6edf3" text-anchor="middle" font-size="11">else: str(i)</text>
    <line x1="160" y1="37" x2="190" y2="37" stroke="#8b949e" marker-end="url(#a13)"/>
    <line x1="330" y1="37" x2="360" y2="37" stroke="#8b949e" marker-end="url(#a13)"/>
    <line x1="500" y1="37" x2="530" y2="37" stroke="#8b949e" marker-end="url(#a13)"/>
    <defs><marker id="a13" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">order matters: the combined check must come before either individual check</text>
  </g>
</svg>

The most specific condition (divisible by both) is checked first — checking a narrower condition before a broader one that would also match is the general rule for ordering `if`/`else if` chains.

## 5. Runnable example

**Level 1 — Brute force / natural.** Exactly the check-order approach described above — there is no meaningfully "worse" brute force here, since the problem is already O(n) minimum (you must produce n output strings), so this level and the optimal level coincide.

**KEY INSIGHT:** checking the combined condition (`%15`, or `%3 && %5`) before either individual condition is the one detail that makes the whole solution correct — reversing this order silently produces wrong output only on multiples of 15, which is easy to miss in casual testing if `n` is small.

**Level 2 — Optimal.** Single pass, `if`/`else if` chain with the combined check first, O(n) time (unavoidable, since output has `n` elements), O(1) extra space beyond the output array.

**Level 3 — Hardened.** Uses `StringBuilder`-free direct string concatenation (or `String.valueOf`) correctly for the non-Fizz/Buzz case, and confirms the combined check truly precedes both individual checks.

```java
// FizzBuzz.java
import java.util.*;

public class FizzBuzz {

    public static List<String> fizzBuzz(int n) {
        List<String> answer = new ArrayList<>();
        for (int i = 1; i <= n; i++) {
            if (i % 15 == 0) {
                answer.add("FizzBuzz");
            } else if (i % 3 == 0) {
                answer.add("Fizz");
            } else if (i % 5 == 0) {
                answer.add("Buzz");
            } else {
                answer.add(String.valueOf(i));
            }
        }
        return answer;
    }

    public static void main(String[] args) {
        System.out.println(fizzBuzz(15));
        // [1, 2, Fizz, 4, Buzz, Fizz, 7, 8, Fizz, Buzz, 11, Fizz, 13, 14, FizzBuzz]
    }
}
```

**How to run:** save as `FizzBuzz.java`, then run `java FizzBuzz.java`.

## 6. Walkthrough

Trace `i=13,14,15` from `fizzBuzz(15)`:

| i | i%15==0? | i%3==0? | i%5==0? | output |
|---|---|---|---|---|
| 13 | no | no | no | "13" |
| 14 | no | no | no | "14" |
| 15 | yes | — | — | "FizzBuzz" |

At `i=15`, the first check (`i % 15 == 0`) is `true`, so `"FizzBuzz"` is appended and the `else if` branches for `%3` and `%5` alone are never evaluated — this is exactly why the combined check must be first in the chain.

## 7. Gotchas & takeaways

> Gotcha: checking `i % 3 == 0` before `i % 15 == 0` (or the combined `&&`) makes every multiple of 15 incorrectly output `"Fizz"` instead of `"FizzBuzz"`, since the `%3` branch matches first and the chain never reaches the `%5`/combined check for that number.

- Signal: multiple overlapping modular conditions on the same loop variable require ordering the most specific (most restrictive) condition first in an `if`/`else if` chain.
- This problem is O(n) at minimum, since it must produce n strings — there is no faster asymptotic approach to beat.
- Related problems: none directly in this section, but the "check the combined/more-specific condition first" lesson generalizes to any multi-condition classification problem.
