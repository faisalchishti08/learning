---
card: leetcode-patterns
gi: 43
slug: get-equal-substrings-within-budget
title: Get Equal Substrings Within Budget
---

## 1. What it is

Given two strings `s` and `t` of the same length, and an integer `maxCost`, you may change any character of `s` to the corresponding character of `t`, at a cost of `abs(s[i] - t[i])` (using ASCII values). Return the length of the longest substring of `s` that can be changed to the corresponding substring of `t` without the total cost exceeding `maxCost`. Example: `s = "abcd"`, `t = "bcdf"`, `maxCost = 3` → answer `3`.

## 2. Why & when

Precompute the per-position cost array (`cost[i] = abs(s[i] - t[i])`), and the problem becomes exactly Minimum Size Subarray Sum's sibling: "longest subarray with sum at most `maxCost`" — the same shrink-while-invalid sliding window, just with the goal flipped from shortest-at-least to longest-at-most.

## 3. Core concept

**Key idea:** once you reduce the problem to a `cost` array, "longest contiguous substring within budget" is a direct application of the "longest valid window" sliding-window template — the same shape as Longest Repeating Character Replacement or Max Consecutive Ones III, but with a running sum instead of a frequency-based condition.

**Steps:**
1. Build `cost[i] = abs(s.charAt(i) - t.charAt(i))` for each index.
2. Set `left = 0`, `sum = 0`, `best = 0`.
3. For each index `right` from 0 to `length - 1`:
   - Add `cost[right]` to `sum`.
   - While `sum > maxCost`: subtract `cost[left]` from `sum`; `left++`.
   - Update `best = max(best, right - left + 1)`.
4. Return `best`.

**Why it is correct:** every character's contribution to the total change cost is independent and additive, so the total cost of changing a substring is exactly the sum of `cost` over that range — turning the problem into "find the longest window whose sum is at most `maxCost`," the standard longest-valid-window template.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Get equal substrings within budget cost array sliding window">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "abcd", t = "bcdf" -&gt; cost = [1, 1, 1, 2]</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="20" y="95" fill="#8b949e">window [0,2] sum=3 &lt;= maxCost(3) -&gt; valid, length 3</text>
    <text x="20" y="118" fill="#8b949e">adding index 3 (cost 2) makes sum=5 &gt; 3 -&gt; must shrink</text>
  </g>
</svg>

Precomputing per-position costs reduces the string problem directly to a numeric sliding-window-sum problem.

## 5. Runnable example

```java
// EqualSubstringsWithinBudget.java
public class EqualSubstringsWithinBudget {

    // Level 1 -- Brute force: check every substring's total cost directly.
    // O(n^2) time, O(1) space.
    static int bruteForce(String s, String t, int maxCost) {
        int best = 0;
        for (int i = 0; i < s.length(); i++) {
            int sum = 0;
            for (int j = i; j < s.length(); j++) {
                sum += Math.abs(s.charAt(j) - t.charAt(j));
                if (sum <= maxCost) best = Math.max(best, j - i + 1);
                else break;
            }
        }
        return best;
    }

    // KEY INSIGHT: precomputing a per-position cost array reduces this to
    // the standard "longest window with sum at most X" sliding-window
    // template -- no string-specific logic needed once the array exists.

    // Level 2 -- Optimal: sliding window over the cost array. O(n) time,
    // O(n) space for the cost array (O(1) if computed on the fly).
    public static int equalSubstring(String s, String t, int maxCost) {
        int left = 0, sum = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            sum += Math.abs(s.charAt(right) - t.charAt(right));
            while (sum > maxCost) {
                sum -= Math.abs(s.charAt(left) - t.charAt(left));
                left++;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    // Level 3 -- Hardened: maxCost of 0 only allows windows where s and t
    // already match exactly at every position, since any cost > 0
    // immediately triggers a shrink.
    static int hardened(String s, String t, int maxCost) {
        if (s == null || t == null || s.length() != t.length()) {
            throw new IllegalArgumentException("s and t must have equal length");
        }
        return equalSubstring(s, t, maxCost);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("abcd", "bcdf", 3));
        System.out.println("optimal:     " + equalSubstring("abcd", "bcdf", 3));
        System.out.println("maxCost=0:   " + hardened("aa", "ab", 0));
    }
}
```

How to run: save as `EqualSubstringsWithinBudget.java`, then run `java EqualSubstringsWithinBudget.java`.

## 6. Walkthrough

Dry run of `equalSubstring("abcd", "bcdf", maxCost = 3)`, using `cost = [1, 1, 1, 2]`:

| right | cost[right] | sum | shrink? | window | best |
|---|---|---|---|---|---|
| 0 | 1 | 1 | no | [0,0] | 1 |
| 1 | 1 | 2 | no | [0,1] | 2 |
| 2 | 1 | 3 | no | [0,2] | 3 |
| 3 | 2 | 5 | yes: remove cost[0]=1, sum=4, left=1; remove cost[1]=1, sum=3, left=2 | [2,3] | 3 |

Final answer: `3`. Time complexity: O(n). Space complexity: O(1) beyond the input strings.

## 7. Gotchas & takeaways

> Gotcha: computing the cost with `s.charAt(i) - t.charAt(i)` without `Math.abs` produces a signed value, which breaks the "total cost" sum whenever `s`'s character has a lower ASCII value than `t`'s at some position — always take the absolute value.

- Reducing a string-comparison problem to a numeric array first, then applying a standard numeric sliding window, is a common two-step pattern worth recognizing on its own.
- Related problems: Minimum Size Subarray Sum, Max Consecutive Ones III, Longest Repeating Character Replacement.
