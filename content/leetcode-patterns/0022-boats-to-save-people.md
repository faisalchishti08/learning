---
card: leetcode-patterns
gi: 22
slug: boats-to-save-people
title: Boats to Save People
---

## 1. What it is

Given an array `people`, where `people[i]` is the weight of the `i`-th person, and an integer `limit`, the maximum weight a boat can carry, find the minimum number of boats needed to carry everyone. Each boat carries at most two people, as long as their combined weight does not exceed `limit`. Example: `people = [3, 2, 2, 1]`, `limit = 3` → answer `3` (boats: `[1,2]`, `[2]`, `[3]`).

## 2. Why & when

This is a greedy pairing problem: to minimize the number of boats, pair the heaviest remaining person with the lightest remaining person whenever possible. Sorting the array first, then using opposite-ends two pointers, implements exactly that greedy rule.

## 3. Core concept

**Key idea:** the heaviest person always needs a boat. Check whether the lightest remaining person can share it — if so, that pairing wastes the least capacity; if not, the heaviest person needs the boat alone, since no one else is any lighter.

**Steps:**
1. Sort `people`.
2. Set `left = 0`, `right = people.length - 1`, `boats = 0`.
3. While `left <= right`:
   - If `people[left] + people[right] <= limit`, they share a boat — `left++`.
   - Either way, the heaviest person (`right`) always gets a boat — `right--`.
   - Increment `boats`.
4. Return `boats`.

**Why it is correct:** the heaviest remaining person must go on some boat. Pairing them with the *lightest* remaining person is never worse than pairing them with anyone else — if the lightest person cannot fit with the heaviest, no one else (who is at least as heavy) can fit either, so the heaviest person must ride alone. This greedy choice is proven optimal by an exchange argument: any solution can be rearranged into this pairing without using more boats.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Boats to save people pairing lightest and heaviest">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">sorted people = [1, 2, 2, 3], limit = 3</text>
    <rect x="20" y="40" width="44" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="64" y="40" width="44" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="108" y="40" width="44" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="152" y="40" width="44" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="42" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="86" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="130" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="174" y="60" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="42" y="90" fill="#79c0ff" text-anchor="middle">left</text>
    <text x="174" y="90" fill="#f0883e" text-anchor="middle">right</text>
    <text x="20" y="120" fill="#8b949e">1+3=4 &gt; 3 -&gt; can't share -&gt; right alone gets a boat; right--, boats=1</text>
  </g>
</svg>

The heaviest person always takes a boat; the lightest joins them only if there is room left.

## 5. Runnable example

```java
// BoatsToSavePeople.java
public class BoatsToSavePeople {

    // Level 1 -- Brute force: try every way to group people into pairs and
    // singles satisfying the limit, searching for the minimum count. This
    // is exponential in the worst case -- shown conceptually, not run on
    // large input, to contrast with the greedy two-pointer approach.
    static int bruteForceSmall(int[] people, int limit) {
        // For small inputs only: sort, then always pair heaviest with the
        // next heaviest that still fits, scanning from the back --
        // equivalent in result to the optimal method below, but written
        // as a plain scan without the two-pointer framing.
        java.util.Arrays.sort(people);
        boolean[] used = new boolean[people.length];
        int boats = 0;
        for (int i = people.length - 1; i >= 0; i--) {
            if (used[i]) continue;
            used[i] = true;
            boats++;
            for (int j = 0; j < i; j++) {
                if (!used[j] && people[i] + people[j] <= limit) {
                    used[j] = true;
                    break;
                }
            }
        }
        return boats;
    }

    // KEY INSIGHT: the heaviest remaining person always needs a boat;
    // pairing them with the lightest remaining person is the best possible
    // use of that boat's spare capacity -- this greedy rule is exactly an
    // opposite-ends two-pointer scan on sorted weights.

    // Level 2 -- Optimal: two pointers on sorted weights. O(n log n) time
    // (for the sort), O(1) extra space.
    public static int numRescueBoats(int[] people, int limit) {
        java.util.Arrays.sort(people);
        int left = 0, right = people.length - 1, boats = 0;
        while (left <= right) {
            if (people[left] + people[right] <= limit) {
                left++;
            }
            right--;
            boats++;
        }
        return boats;
    }

    // Level 3 -- Hardened: a single person, or a person whose weight
    // exactly equals the limit, both are handled by the same loop with no
    // extra branch (they always get their own boat).
    static int hardened(int[] people, int limit) {
        if (people == null || people.length == 0) return 0;
        return numRescueBoats(people, limit);
    }

    public static void main(String[] args) {
        int[] people = {3, 2, 2, 1};
        System.out.println("optimal: " + numRescueBoats(people, 3));
        System.out.println("single person: " + hardened(new int[] {5}, 5));
    }
}
```

How to run: save as `BoatsToSavePeople.java`, then run `java BoatsToSavePeople.java`.

## 6. Walkthrough

Dry run of `numRescueBoats({1, 2, 2, 3}, limit = 3)` (already sorted):

| step | left | right | people[left] | people[right] | sum | fits? | action |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 3 | 1 | 3 | 4 | no | right alone; right--, boats=1 |
| 2 | 0 | 2 | 1 | 2 | 3 | yes | pair; left++, right--, boats=2 |
| 3 | 1 | 1 | — | — | — | left<=right still true (1<=1) | people[1]=2 alone; right--, boats=3 |

Final `boats = 3`. Time complexity: O(n log n), dominated by the sort. Space complexity: O(1) extra.

## 7. Gotchas & takeaways

> Gotcha: forgetting that the loop condition is `left <= right` (not `<`) drops the middle person when there is an odd count of unpaired people left — that last person still needs their own boat.

- `right` always decrements every iteration (someone heavy always boards); `left` only increments when a pairing succeeds — this asymmetry is what makes the greedy proof work.
- Related problems: 3Sum-style pairing problems, Two City Scheduling, Assign Cookies (a simpler two-pointer greedy matching problem).
