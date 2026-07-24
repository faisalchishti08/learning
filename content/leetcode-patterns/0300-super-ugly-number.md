---
card: leetcode-patterns
gi: 300
slug: super-ugly-number
title: Super Ugly Number
---

## 1. What it is

A "super ugly number" is a positive integer whose only prime factors come from a given array `primes`. Given an integer `n` and `primes`, return the `n`-th super ugly number, with `1` counted as the first. Example: `n = 12`, `primes = [2,7,13,19]` → `32`.

## 2. Why & when

This generalizes Ugly Number II from exactly 3 fixed factors (`2, 3, 5`) to an ARBITRARY list of `k` prime factors. With only 3 fixed pointers, three plain `if` checks were simple enough; with `k` arbitrary factors, tracking `k` pointers and finding their minimum candidate each round is exactly the K-way Merge template — a min-heap keeps that minimum-finding step fast as `k` grows. Use this shape whenever a "generate from known values, transform a few ways, merge" problem has a variable or large number of transformation rules.

## 3. Core concept

**Key idea:** keep one pointer per prime in `primes`, each tracking how far along the growing "super ugly numbers so far" list that prime's multiplication has reached. Use a min-heap to always pick the smallest next candidate across all `k` pointers, instead of scanning all `k` candidates by hand each round.

**Steps:**
1. Start `superUgly = [1]`, and `pointers[i] = 0` for each prime index `i`.
2. Create a min-heap seeded with `(primes[i] * superUgly[0], i)` for every prime index `i`.
3. Repeat `n - 1` times: pop the heap's minimum `(value, i)`. If `value` differs from the last appended super ugly number (skip duplicates), append it. Advance `pointers[i]` by one, then push `(primes[i] * superUgly[pointers[i]], i)` back onto the heap.
4. After the loop, the last appended value is the answer.

**Why it is correct:** the same reasoning as Ugly Number II applies — every super ugly number greater than `1` equals some smaller super ugly number times one of the primes. With `k` primes instead of 3, a min-heap replaces the fixed `if` checks, since scanning `k` candidates by hand each round would cost O(k) per step (O(nk) total), while a heap does it in O(log k) per step (O(n log k) total).

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Min-heap tracking one pointer per prime factor, popping the smallest candidate and skipping duplicate values">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">primes = [2,7,13,19], superUgly = [1]</text>
    <text x="10" y="45">seed heap: 1*2=2, 1*7=7, 1*13=13, 1*19=19</text>
    <text x="10" y="65">pop 2 -&gt; append -&gt; superUgly=[1,2] -&gt; push 2*2=4</text>
    <text x="10" y="85">pop 4 -&gt; append -&gt; superUgly=[1,2,4] -&gt; push 4*2=8</text>
    <text x="10" y="105">pop 7 -&gt; append -&gt; superUgly=[1,2,4,7] -&gt; push 2*7=14</text>
    <rect x="10" y="120" width="220" height="24" fill="#3fb950"/><text x="120" y="137" fill="#0d1117" text-anchor="middle" font-size="10">sequence so far: 1,2,4,7,...</text>
  </g>
</svg>

Each prime's pointer advances independently, and the heap always surfaces the globally smallest next candidate.

## 5. Runnable example

```java
// SuperUglyNumber.java
import java.util.PriorityQueue;

public class SuperUglyNumber {

    // KEY INSIGHT: generalizing Ugly Number II's fixed 3 pointers to
    // k arbitrary primes means a heap must find the minimum among k
    // candidates each round, instead of 3 plain comparisons.

    static int nthSuperUglyNumber(int n, int[] primes) {
        int[] superUgly = new int[n];
        superUgly[0] = 1;
        int[] pointers = new int[primes.length];

        // {candidate value, prime index}
        PriorityQueue<long[]> heap = new PriorityQueue<>((a, b) -> Long.compare(a[0], b[0]));
        for (int i = 0; i < primes.length; i++) {
            heap.offer(new long[]{(long) primes[i] * superUgly[0], i});
        }

        int count = 1;
        while (count < n) {
            long[] top = heap.poll();
            long value = top[0];
            int primeIdx = (int) top[1];

            if (value != superUgly[count - 1]) { // skip duplicate candidates
                superUgly[count] = (int) value;
                count++;
            }
            pointers[primeIdx]++;
            heap.offer(new long[]{(long) primes[primeIdx] * superUgly[pointers[primeIdx]], primeIdx});
        }
        return superUgly[n - 1];
    }

    public static void main(String[] args) {
        System.out.println(nthSuperUglyNumber(12, new int[]{2, 7, 13, 19}));
        // 32
    }
}
```

**How to run:** `java SuperUglyNumber.java`

## 6. Walkthrough

Trace the first few rounds of `nthSuperUglyNumber(12, [2,7,13,19])`:

| pop value | primeIdx | duplicate? | superUgly so far | pushed next |
|---|---|---|---|---|
| 2 | 0 (prime 2) | no | [1,2] | 2*2=4 |
| 4 | 0 | no | [1,2,4] | 2*4=8 |
| 7 | 1 (prime 7) | no | [1,2,4,7] | 7*2=14 |
| 8 | 0 | no | [1,2,4,7,8] | 2*8=16 |
| 13 | 2 (prime 13) | no | [1,2,4,7,8,13] | 13*2=26 |

Continuing this process for all 12 rounds ends with `superUgly[11] = 32`. Time complexity is O(n log k), `n` pops, each an O(log k) heap operation for `k` primes. Space is O(n) for the result array, plus O(k) for the heap.

## 7. Gotchas & takeaways

> Gotcha: using `int` for the candidate value in the heap can overflow when `primes` contains large values multiplied against a growing super ugly number — using `long` for the heap entries, as shown, avoids silent overflow bugs for larger test cases.

- This is Ugly Number II generalized: 3 fixed pointers with `if` checks become `k` pointers with a min-heap, once the number of transformation rules is not a small constant.
- The duplicate check (`value != superUgly[count - 1]`) is necessary here because two DIFFERENT primes can produce the identical candidate value (e.g., `2 * 7 = 7 * 2`), which a heap alone does not prevent.
- Related problems: Ugly Number II (the same idea with exactly 3 fixed primes), Merge k Sorted Lists (a heap merging explicit sequences instead of generated candidates).
