---
card: leetcode-patterns
gi: 500
slug: corporate-flight-bookings
title: Corporate Flight Bookings
---

## 1. What it is

You get `n` flights, numbered `1` to `n`, and a list of bookings `[first, last, seats]`, each meaning `seats` seats were reserved on every flight from `first` to `last`, inclusive. Return an array of length `n` where each entry is the total seats booked on that flight. Example: `bookings = [[1,2,10],[2,3,20],[2,5,25]]`, `n = 5` → `[10, 55, 45, 25, 25]`.

## 2. Why & when

Each booking adds a constant value to an entire *range*, and you need the final value at every position after all bookings are applied. Rather than looping over the full range for every booking (which is what the range-sum problem is trying to avoid, from the [prefix-sum signal](0487-prefix-sum-signal-range-sums-or-subarray-sum-conditions.md) family), record only the *start* and *end+1* of each range's effect, then recover the final array with a single prefix-sum pass. This technique is often called the "difference array." Constraints: up to 20,000 bookings, up to 20,000 flights.

## 3. Core concept

**Key idea:** build a `diff` array of size `n + 1` (one extra slot as a buffer past the end). For each booking `[first, last, seats]` (1-indexed), add `seats` at `diff[first - 1]` and subtract `seats` at `diff[last]` (the position right after the range ends). After processing every booking, compute the prefix sum of `diff` — the running total at each index is exactly the number of active bookings' seats affecting that flight.

**Steps:**
1. Allocate `diff` of size `n + 1`, all zero.
2. For each booking `[first, last, seats]`: `diff[first - 1] += seats`; `diff[last] -= seats`.
3. Compute the prefix sum of `diff` in place: `diff[i] += diff[i-1]` for each `i` from `1` to `n-1`.
4. The first `n` entries of `diff` are the answer.

**Why adding at the start and subtracting just past the end works:** the prefix sum of the `diff` array accumulates every `+seats` that has "started" by index `i` and cancels out every `-seats` from ranges that have already "ended" before `i`. This is exactly a range-update turned into two point-updates, resolved by the same prefix-sum accumulation used for range-sum queries, just run in reverse (updates instead of queries).

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A difference array recording range starts and ends, then prefix-summed into final totals">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">bookings = [[1,2,10],[2,3,20],[2,5,25]], n = 5</text>
    <text x="20" y="45" fill="#8b949e">[1,2,10]: diff[0]+=10, diff[2]-=10</text>
    <text x="20" y="65" fill="#8b949e">[2,3,20]: diff[1]+=20, diff[3]-=20</text>
    <text x="20" y="85" fill="#8b949e">[2,5,25]: diff[1]+=25, diff[5]-=25</text>
    <text x="20" y="110" fill="#79c0ff">diff (indices 0-5) = [10, 45, -10, -20, 0, -25]</text>
    <text x="20" y="135" fill="#3fb950">prefix sum: [10, 55, 45, 25, 25] -&gt; the final answer</text>
  </g>
</svg>

Each booking becomes two point-updates; a single prefix-sum pass reconstructs every flight's total.

## 5. Runnable example

**Level 1 — Brute force.** For each booking, add `seats` to every flight in its range directly. O(bookings · range width).

**KEY INSIGHT:** a range update (add `seats` to every index in `[first, last]`) can be represented by two point-updates (`+seats` at the start, `-seats` just past the end) — a final prefix-sum pass turns those point-updates into the correct per-index totals.

**Level 2 — Optimal.** Difference array + one prefix-sum pass, O(bookings + n).

**Level 3 — Hardened.** Handles overlapping ranges (the running sum naturally combines them) and a booking covering the entire flight range.

```java
// CorporateFlightBookings.java
import java.util.Arrays;

public class CorporateFlightBookings {

    // Level 1: brute force, O(bookings * range width)
    static int[] bruteForce(int[][] bookings, int n) {
        int[] result = new int[n];
        for (int[] booking : bookings) {
            int first = booking[0], last = booking[1], seats = booking[2];
            for (int i = first - 1; i <= last - 1; i++) {
                result[i] += seats;
            }
        }
        return result;
    }

    // Level 2 & 3: difference array + prefix sum, O(bookings + n)
    static int[] corpFlightBookings(int[][] bookings, int n) {
        int[] diff = new int[n + 1];
        for (int[] booking : bookings) {
            int first = booking[0], last = booking[1], seats = booking[2];
            diff[first - 1] += seats;
            diff[last] -= seats;
        }

        int[] result = new int[n];
        result[0] = diff[0];
        for (int i = 1; i < n; i++) {
            result[i] = result[i - 1] + diff[i];
        }
        return result;
    }

    public static void main(String[] args) {
        int[][] bookings = {{1, 2, 10}, {2, 3, 20}, {2, 5, 25}};
        System.out.println("brute force: " + Arrays.toString(bruteForce(bookings, 5)));
        System.out.println("optimal:     " + Arrays.toString(corpFlightBookings(bookings, 5)));

        int[][] wholeRange = {{1, 5, 100}};
        System.out.println("whole range: " + Arrays.toString(corpFlightBookings(wholeRange, 5)));
    }
}
```

**How to run:** save as `CorporateFlightBookings.java`, then run `java CorporateFlightBookings.java`.

## 6. Walkthrough

Building `diff` (size 6) for `bookings = [[1,2,10],[2,3,20],[2,5,25]]`, `n = 5`:

| booking | diff update | diff after |
|---|---|---|
| [1,2,10] | diff[0]+=10, diff[2]-=10 | [10,0,-10,0,0,0] |
| [2,3,20] | diff[1]+=20, diff[3]-=20 | [10,20,-10,-20,0,0] |
| [2,5,25] | diff[1]+=25, diff[5]-=25 | [10,45,-10,-20,0,-25] |

Prefix sum of the first 5 entries: `result[0]=10`, `result[1]=10+45=55`, `result[2]=55+(-10)=45`, `result[3]=45+(-20)=25`, `result[4]=25+0=25`. Final: `[10, 55, 45, 25, 25]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: subtracting `seats` at index `last - 1` instead of `last` (using the 1-indexed range's last flight directly instead of one past it) removes the seats one flight too early — always subtract at `last`, since flight indices are 1-indexed but the difference array is 0-indexed, and the range is inclusive of `last`.

- Turning range updates into two point updates, resolved by a final prefix sum, is the mirror image of turning range *queries* into a subtraction of two prefix sums — same underlying idea, applied to writes instead of reads.
- Overlapping bookings are handled automatically: the difference array simply sums every applicable `+seats` and `-seats` at each position.
- Time: O(bookings + n) — one O(1) update per booking, one O(n) prefix-sum pass at the end.
