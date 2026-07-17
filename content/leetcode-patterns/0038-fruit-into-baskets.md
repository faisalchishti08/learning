---
card: leetcode-patterns
gi: 38
slug: fruit-into-baskets
title: Fruit Into Baskets
---

## 1. What it is

You are given an array `fruits` where `fruits[i]` is the type of fruit on the `i`-th tree. You have exactly 2 baskets, and each basket can hold only one type of fruit (unlimited quantity of that type). Starting from any tree, pick fruit from trees moving only to the right, stopping as soon as you'd need a third basket. Return the maximum number of fruits you can collect. Example: `fruits = [1, 2, 1]` → answer `3` (both baskets, one per type, collect everything).

## 2. Why & when

This is "Longest Substring with At Most 2 Distinct Characters" wearing a fruit costume: the window is valid exactly when it contains at most 2 distinct fruit types, which is an incrementally checkable condition using a frequency map's size.

## 3. Core concept

**Key idea:** the window's validity depends only on how many *distinct* fruit types it contains — track a frequency map, and the map's key count is the distinct-type count directly.

**Steps:**
1. Create an empty map `count` from fruit type to its count in the current window. Set `left = 0`, `best = 0`.
2. For each index `right` from 0 to `fruits.length - 1`:
   - Increment `count[fruits[right]]`.
   - While `count.size() > 2`: decrement `count[fruits[left]]`; if that count reaches 0, remove the key entirely; then `left++`.
   - Update `best = max(best, right - left + 1)`.
3. Return `best`.

**Why it is correct:** `count.size()` is exactly the number of distinct fruit types currently in the window, since every type present has a positive count and every type absent has been removed from the map. Shrinking whenever that size exceeds 2 keeps the window representing a plan that fits in exactly 2 baskets, and the maximum length across all valid states is the answer.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fruit into baskets window with at most 2 distinct types">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">fruits = [1, 2, 3, 2, 2]</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="20" y="95" fill="#8b949e">window {1,2}: count={1:1,2:1}, size 2, valid, length 2</text>
    <text x="20" y="118" fill="#8b949e">right adds type 3: count.size()=3 &gt; 2 -&gt; shrink until only 2 types remain</text>
  </g>
</svg>

The map's key count directly tells you how many distinct fruit types (baskets needed) the window currently requires.

## 5. Runnable example

```java
// FruitIntoBaskets.java
import java.util.HashMap;
import java.util.Map;

public class FruitIntoBaskets {

    // Level 1 -- Brute force: for every window start, expand right,
    // tracking distinct types with a HashSet, until a third type appears.
    // O(n^2) time, O(1) space.
    static int bruteForce(int[] fruits) {
        int best = 0;
        for (int i = 0; i < fruits.length; i++) {
            java.util.Set<Integer> types = new java.util.HashSet<>();
            int j = i;
            while (j < fruits.length) {
                types.add(fruits[j]);
                if (types.size() > 2) break;
                j++;
            }
            best = Math.max(best, j - i);
        }
        return best;
    }

    // KEY INSIGHT: this is "at most 2 distinct values in a window" --
    // exactly the same shape as Longest Substring with At Most K Distinct
    // Characters, with k fixed at 2 and characters replaced by fruit types.

    // Level 2 -- Optimal: sliding window with a type-count map. O(n) time,
    // O(1) space (at most 3 keys in the map at any time).
    public static int totalFruit(int[] fruits) {
        Map<Integer, Integer> count = new HashMap<>();
        int left = 0, best = 0;
        for (int right = 0; right < fruits.length; right++) {
            count.merge(fruits[right], 1, Integer::sum);
            while (count.size() > 2) {
                int type = fruits[left];
                count.merge(type, -1, Integer::sum);
                if (count.get(type) == 0) count.remove(type);
                left++;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    // Level 3 -- Hardened: an orchard with only 1 fruit type overall never
    // triggers the shrink condition, so the whole array is one valid window.
    static int hardened(int[] fruits) {
        if (fruits == null || fruits.length == 0) return 0;
        return totalFruit(fruits);
    }

    public static void main(String[] args) {
        int[] fruits = {1, 2, 3, 2, 2};
        System.out.println("brute force: " + bruteForce(fruits));
        System.out.println("optimal:     " + totalFruit(fruits));
        System.out.println("one type:    " + hardened(new int[] {5, 5, 5}));
    }
}
```

How to run: save as `FruitIntoBaskets.java`, then run `java FruitIntoBaskets.java`.

## 6. Walkthrough

Dry run of `totalFruit({1, 2, 3, 2, 2})`:

| right | fruit | count map after add | size | shrink? | window | best |
|---|---|---|---|---|---|---|
| 0 | 1 | {1:1} | 1 | no | [0,0] | 1 |
| 1 | 2 | {1:1,2:1} | 2 | no | [0,1] | 2 |
| 2 | 3 | {1:1,2:1,3:1} | 3 | yes: remove fruits[0]=1 -> {2:1,3:1}, left=1 | [1,2] | 2 |
| 3 | 2 | {2:2,3:1} | 2 | no | [1,3] | 3 |
| 4 | 2 | {2:3,3:1} | 2 | no | [1,4] | 4 |

Final answer: `4`, from the window `[2, 3, 2, 2]` (trees at indices 1 through 4). Time complexity: O(n). Space complexity: O(1), since the map never holds more than 3 keys.

## 7. Gotchas & takeaways

> Gotcha: forgetting to remove a key from the map once its count reaches `0` leaves a stale zero-count entry, which inflates `count.size()` and makes the algorithm shrink windows that should still be considered valid.

- "2 baskets" is a disguised "at most 2 distinct values" sliding window — recognizing the disguise is the whole difficulty of this problem.
- Related problems: Longest Substring with At Most K Distinct Characters, Longest Substring with At Most Two Distinct Characters (the direct, undisguised version of this exact problem).
