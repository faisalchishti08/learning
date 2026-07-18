---
card: leetcode-patterns
gi: 93
slug: couples-holding-hands
title: Couples Holding Hands
---

## 1. What it is

`n` couples sit in a row of `2n` seats. Couple `i` is represented by people `2i` and `2i+1`. Given `row`, the current seating arrangement, find the minimum number of swaps needed so that every couple sits next to each other. Example: `row = [0,2,1,3]` → `1` swap (swap positions `1` and `2` so `0` and `1` end up adjacent, and `2` and `3` end up adjacent).

## 2. Why & when

This problem uses the same "place each element where it belongs by swapping" mechanics as cyclic sort, but the target position is defined by *pairing*, not by value-equals-index. Instead of a single array of values wanting specific indices, pairs of seats "want" to hold a specific *partner*, and each swap that fixes one couple is guaranteed to make progress, just like a cyclic sort swap.

## 3. Core concept

**Key idea:** walk through the row two seats at a time (positions `0-1`, `2-3`, `4-5`, ...). For each pair of seats, check whether the person sitting in the first seat's partner is already in the second seat. If not, find that partner elsewhere in the row and swap them into the second seat.

**Steps:**
1. For each even position `i` (`0, 2, 4, ...`):
   - The expected partner of `row[i]` is `row[i] XOR 1` (since partners are `2k` and `2k+1`, XOR with `1` flips between them).
   - If `row[i+1]` already equals that expected partner, this couple is already seated together — move on.
   - Otherwise, find the index `j` (elsewhere in the row) holding the expected partner, swap `row[i+1]` and `row[j]`, and count one swap.
2. Return the total swap count.

**Why it is correct:** each swap places at least one couple correctly and permanently — once a couple sits together at positions `i, i+1`, no future swap in the algorithm ever touches those two seats again (the loop only examines each even position once). Since there are `n` couples, at most `n` swaps can ever be needed, giving a clear upper bound on the work.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Swapping seats so each couple sits together">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">row = [0, 2, 1, 3] (couples: {0,1} and {2,3})</text>
    <rect x="20" y="45" width="40" height="26" fill="#161b22" stroke="#79c0ff"/><text x="40" y="63" fill="#e6edf3" text-anchor="middle">0</text>
    <rect x="60" y="45" width="40" height="26" fill="#161b22" stroke="#f0883e"/><text x="80" y="63" fill="#e6edf3" text-anchor="middle">2</text>
    <rect x="100" y="45" width="40" height="26" fill="#161b22" stroke="#f0883e"/><text x="120" y="63" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="140" y="45" width="40" height="26" fill="#161b22" stroke="#79c0ff"/><text x="160" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="20" y="100" fill="#8b949e">position 0 holds 0, wants partner 1 (0 XOR 1); position 1 holds 2, not 1 -&gt; find 1 at index 2, swap</text>
    <text x="20" y="125" fill="#8b949e">result: [0, 1, 2, 3] -- 1 swap total, both couples now adjacent</text>
  </g>
</svg>

Seat `0` holds person `0`, whose partner is `1` (via `0 XOR 1`); since seat `1` holds `2` instead, the algorithm locates `1` elsewhere and swaps it into place — fixing both couples in a single move.

## 5. Runnable example

```java
// CouplesHoldingHands.java
public class CouplesHoldingHands {

    // Level 1 -- Brute force: repeatedly scan the whole row looking for
    // any mismatched couple, fix it, and restart the scan from the
    // beginning. O(n^2) time -- wastes repeated full re-scans after
    // every single swap.
    static int bruteForce(int[] row) {
        int swaps = 0;
        boolean fixedSomething = true;
        while (fixedSomething) {
            fixedSomething = false;
            for (int i = 0; i < row.length; i += 2) {
                int expectedPartner = row[i] ^ 1;
                if (row[i + 1] != expectedPartner) {
                    for (int j = i + 2; j < row.length; j++) {
                        if (row[j] == expectedPartner) {
                            int temp = row[i + 1];
                            row[i + 1] = row[j];
                            row[j] = temp;
                            swaps++;
                            fixedSomething = true;
                            break;
                        }
                    }
                }
            }
        }
        return swaps;
    }

    // KEY INSIGHT: fixing a couple at positions i, i+1 never needs to be
    // revisited -- a single forward pass, one swap per mismatched pair,
    // is enough (no need to restart scanning from the beginning).

    // Level 2 -- Optimal: single forward pass with a position index for
    // O(1) lookups. O(n) time, O(n) space for the position map.
    public static int minSwapsCouples(int[] row) {
        int n = row.length;
        int[] position = new int[n]; // person -> current index
        for (int i = 0; i < n; i++) position[row[i]] = i;

        int swaps = 0;
        for (int i = 0; i < n; i += 2) {
            int person = row[i];
            int expectedPartner = person ^ 1;
            if (row[i + 1] != expectedPartner) {
                int partnerPos = position[expectedPartner];
                // swap row[i+1] and row[partnerPos], keep position[] in sync
                int displaced = row[i + 1];
                row[i + 1] = row[partnerPos];
                row[partnerPos] = displaced;
                position[expectedPartner] = i + 1;
                position[displaced] = partnerPos;
                swaps++;
            }
        }
        return swaps;
    }

    // Level 3 -- Hardened: a row where every couple is already correctly
    // seated -- must return 0 swaps without doing any unnecessary work.
    static int hardened(int[] row) {
        return minSwapsCouples(row);
    }

    public static void main(String[] args) {
        int[] a = {0, 2, 1, 3};
        System.out.println("brute force: " + bruteForce(a.clone()));
        System.out.println("optimal:     " + minSwapsCouples(a));

        int[] alreadyDone = {0, 1, 2, 3};
        System.out.println("already seated (expect 0): " + hardened(alreadyDone));
    }
}
```

How to run: save as `CouplesHoldingHands.java`, then run `java CouplesHoldingHands.java`.

## 6. Walkthrough

Dry run of `minSwapsCouples({0, 2, 1, 3})`:

1. `position = {0:0, 2:1, 1:2, 3:3}` initially.
2. `i = 0`: `person = row[0] = 0`, `expectedPartner = 0 ^ 1 = 1`. `row[1] = 2 != 1` — mismatch. `partnerPos = position[1] = 2`. Swap `row[1]` (`2`) and `row[2]` (`1`): row becomes `[0, 1, 2, 3]`. Update `position[1] = 1`, `position[2] = 2`. `swaps = 1`.
3. `i = 2`: `person = row[2] = 2`, `expectedPartner = 2 ^ 1 = 3`. `row[3] = 3 == 3` — already matched, no swap.
4. Loop ends. Return `swaps = 1`.

Time complexity: O(n), one forward pass with O(1) position lookups. Space complexity: O(n) for the position-tracking array.

## 7. Gotchas & takeaways

> Gotcha: forgetting to update the `position` array after a swap causes future lookups (`position[expectedPartner]`) to point at stale, now-incorrect indices, silently producing wrong swap counts on later iterations.

- The `person ^ 1` trick (XOR with `1`) is the compact way to compute a partner from person IDs `2k` and `2k+1` — worth memorizing for any "paired IDs" problem.
- Related problems: Cyclic sort's core template (place-by-swap mechanics), Sort Array By Parity (a simpler two-pointer, place-by-swap partition).
