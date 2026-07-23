---
card: leetcode-patterns
gi: 266
slug: binary-watch
title: Binary Watch
---

## 1. What it is

A binary watch has 4 LEDs for hours (`0-11`) and 6 LEDs for minutes (`0-59`), where each LED represents a power of two, and a lit LED means that bit is set. Given the number of LEDs currently lit (`turnedOn`), return all possible times the watch could be showing, as strings like `"H:MM"`. Example: `turnedOn = 1` → `["0:01","0:02","0:04","0:08","0:16","0:32","1:00","2:00","4:00","8:00"]`.

## 2. Why & when

The number of lit LEDs for a given hour or minute value is exactly its Hamming weight (the count of `1` bits), the same quantity Number of 1 Bits computes. Use this shape whenever a problem's "on/off" or "lit/unlit" description is really just a bit-count constraint on small, bounded numeric ranges — checking every valid combination becomes a bounded brute-force search using bit-counting as the filter.

## 3. Core concept

**Key idea:** the hour and minute ranges are both small and fixed (`0-11` and `0-59`), so instead of any clever bit trick, you can safely check EVERY possible `(hour, minute)` pair directly. For each pair, count the total set bits across both values (using `Integer.bitCount`, or the manual `n & (n - 1)` loop), and keep the pair if that total equals `turnedOn`.

**Steps:**
1. Create an empty results list.
2. Loop `hour` from `0` to `11`.
3. Loop `minute` from `0` to `59`.
4. Compute `totalBits = Integer.bitCount(hour) + Integer.bitCount(minute)`.
5. If `totalBits == turnedOn`, format the pair as `"H:MM"` (minute zero-padded to 2 digits) and add it to the results.
6. Return the results list.

**Why it is correct:** each LED corresponds to exactly one bit position, and a lit LED means that bit is `1` — so the total number of lit LEDs for a given `(hour, minute)` combination is precisely the sum of set bits in `hour` and set bits in `minute`. Checking all `12 * 60 = 720` combinations is a small, fixed amount of work, and directly counting bits for each is the same reliable technique from Number of 1 Bits, applied twice per pair.

## 4. Diagram

<svg viewBox="0 0 460 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hour 8 has 1 set bit (1000), minute 32 has 1 set bit (100000), total 2 lit LEDs">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">turnedOn = 2, checking hour=8, minute=32</text>
    <text x="10" y="45">hour = 8 = 1000 (binary) -&gt; 1 set bit</text>
    <text x="10" y="65">minute = 32 = 100000 (binary) -&gt; 1 set bit</text>
    <rect x="10" y="75" width="30" height="24" fill="#3fb950"/><text x="25" y="92" fill="#0d1117" text-anchor="middle" font-size="9">2</text>
    <text x="50" y="92">total lit LEDs = 1 + 1 = 2, matches turnedOn</text>
    <text x="10" y="130">"8:32" is added to the result list</text>
  </g>
</svg>

Every candidate hour/minute pair is checked by summing its two independent bit counts against the target.

## 5. Runnable example

```java
// BinaryWatch.java
import java.util.*;

public class BinaryWatch {

    // Level 1 -- Brute force: this problem's search space is already
    // tiny (12 hours x 60 minutes = 720 combinations), so directly
    // checking every pair IS the intended approach -- there is no
    // faster asymptotic algorithm needed, only the bit-count check
    // itself needs to be correct and efficient.

    // KEY INSIGHT: the number of lit LEDs for a value is exactly its
    // Hamming weight (set-bit count), the same quantity computed in
    // Number of 1 Bits -- reuse that idea as the filter condition.

    // Level 2 -- Optimal: exhaustive check over the small fixed range.
    static List<String> readBinaryWatch(int turnedOn) {
        List<String> result = new ArrayList<>();
        for (int hour = 0; hour < 12; hour++) {
            for (int minute = 0; minute < 60; minute++) {
                int totalBits = Integer.bitCount(hour) + Integer.bitCount(minute);
                if (totalBits == turnedOn) {
                    result.add(String.format("%d:%02d", hour, minute));
                }
            }
        }
        return result;
    }

    // Level 3 -- Hardened: works unchanged for turnedOn = 0 (only
    // "0:00" qualifies, since both hour and minute must have zero set
    // bits) and for turnedOn values too large to ever be achieved
    // (e.g. 9, more bits than 11's 4 + 59's 6 combined maximum),
    // correctly returning an empty list.

    public static void main(String[] args) {
        System.out.println(readBinaryWatch(1));
        // [0:01, 0:02, 0:04, 0:08, 0:16, 0:32, 1:00, 2:00, 4:00, 8:00]
    }
}
```

**How to run:** `java BinaryWatch.java`

## 6. Walkthrough

Trace a few iterations of `readBinaryWatch(1)`:

| hour | minute | bitCount(hour) | bitCount(minute) | total | == 1? | added? |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | no | no |
| 0 | 1 | 0 | 1 | 1 | yes | "0:01" |
| 0 | 2 | 0 | 1 | 1 | yes | "0:02" |
| 1 | 0 | 1 | 0 | 1 | yes | "1:00" |
| 3 | 0 | 2 | 0 | 2 | no | no |

The full loop over all 720 combinations produces the 10 valid times shown in the expected output. Time complexity is O(12 · 60) = O(1), a fixed number of iterations regardless of `turnedOn`. Space is O(1) beyond the output list itself.

## 7. Gotchas & takeaways

> Gotcha: forgetting to zero-pad the minute value (`String.format("%d:%02d", ...)`, not `"%d:%d"`) produces malformed times like `"1:5"` instead of the required `"1:05"` — always match the exact output format a problem specifies, since minor formatting mismatches fail otherwise-correct solutions.

- This problem shows that not every bit-manipulation problem needs a clever trick — sometimes the search space is small enough that brute-force enumeration, filtered by a bit-count check, is both correct and intended.
- `Integer.bitCount(n)` is Java's built-in equivalent of the manual `n & (n - 1)` loop from Number of 1 Bits — safe to use directly once you've demonstrated you understand the underlying mechanism.
- Related problems: Number of 1 Bits (the bit-counting technique this problem reuses twice per pair), Counting Bits (precomputing bit counts for a range, which could optimize this problem's repeated `bitCount` calls if the range were much larger).
