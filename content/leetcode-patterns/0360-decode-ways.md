---
card: leetcode-patterns
gi: 360
slug: decode-ways
title: Decode Ways
---

## 1. What it is

A message of digits can be decoded using the mapping `'A' -> "1"`, `'B' -> "2"`, ..., `'Z' -> "26"`. Given a digit string `s`, return the NUMBER OF WAYS it can be decoded. Example: `s = "12"` → `2` (`"AB"` reading `1,2`, or `"L"` reading `12`).

## 2. Why & when

This is a counting DP where each position's ways depend on the ONE or TWO preceding positions, exactly the Fibonacci/Linear shape — except the transition is CONDITIONAL: a 2-digit look-back is only valid if those two digits form a number between `10` and `26`. Use this shape whenever a problem decodes or parses a sequence where each step consumes 1 or 2 units, with validity rules attached to each option.

## 3. Core concept

**Key idea:** build `dp[i]` = number of ways to decode the PREFIX `s[0..i)` (the first `i` characters), for every `i` from `0` to `s.length()`, by checking whether the last 1 or 2 characters form a valid decode step.

**Steps:**
1. Base cases: `dp[0] = 1` (an empty prefix has exactly one way: decode nothing). `dp[1] = 1` if `s.charAt(0) != '0'`, else `0` (a single `'0'` cannot be decoded alone).
2. For `i` from `2` to `s.length()`: start `dp[i] = 0`. If `s.charAt(i-1) != '0'` (the last single digit is valid, `1`-`9`), add `dp[i-1]`. If `s.substring(i-2, i)` is between `"10"` and `"26"` (the last two digits form a valid letter), add `dp[i-2]`.
3. Return `dp[s.length()]`.

**Why it is correct:** the LAST decoded "chunk" ending at position `i` is either one digit (valid if it is not `'0'`) or two digits (valid if the two-digit number is `10`–`26`). Summing the ways from whichever of these options are valid covers every way to reach position `i`, since any decoding has a well-defined last chunk that falls into exactly one of these two cases.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="dp array for the string 226 showing dp of 3 built from dp of 2 for digit 6 and dp of 1 for two digit 26">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">s="226"; dp[0]=1, dp[1]=1 ('2' valid), dp[2]=2 ('2' valid + "22" valid)</text>
    <text x="10" y="45">dp[3]: last digit '6' valid -&gt; += dp[2] = 2</text>
    <text x="10" y="65">last two "26" valid (10-26) -&gt; += dp[1] = 1</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">dp[3] = 2 + 1 = 3</text>
  </g>
</svg>

Each position sums two conditional contributions: one for a single-digit ending, one for a valid two-digit ending.

## 5. Runnable example

```java
// DecodeWays.java
public class DecodeWays {

    // KEY INSIGHT: same "look back 1 or 2" recurrence as Climbing
    // Stairs, but each look-back option is CONDITIONALLY valid
    // (single digit != '0'; two digits in [10, 26]).

    static int numDecodings(String s) {
        int n = s.length();
        if (n == 0 || s.charAt(0) == '0') return 0;

        int prev2 = 1;
        int prev1 = 1;
        for (int i = 2; i <= n; i++) {
            int curr = 0;
            if (s.charAt(i - 1) != '0') {
                curr += prev1;
            }
            int twoDigit = Integer.parseInt(s.substring(i - 2, i));
            if (twoDigit >= 10 && twoDigit <= 26) {
                curr += prev2;
            }
            prev2 = prev1;
            prev1 = curr;
        }
        return prev1;
    }

    public static void main(String[] args) {
        System.out.println(numDecodings("12"));
        // 2
        System.out.println(numDecodings("226"));
        // 3
        System.out.println(numDecodings("06"));
        // 0
    }
}
```

**How to run:** `java DecodeWays.java`

## 6. Walkthrough

Trace `numDecodings("226")`:

| i | last digit valid? | +prev1 | two-digit valid? | +prev2 | curr |
|---|---|---|---|---|---|
| 2 | '2' != '0', yes | +1 | "22"=22, yes | +1 | 2 |
| 3 | '6' != '0', yes | +2 | "26"=26, yes | +1 | 3 |

Final `prev1 = 3`, matching the expected `3` (`"BBF"`, `"BZ"`, `"VF"`). Time complexity is O(n). Space is O(1) with rolling variables.

## 7. Gotchas & takeaways

> Gotcha: a `'0'` digit can ONLY be part of a valid two-digit chunk (`"10"` or `"20"`) — it can never stand alone or start a two-digit chunk (`"0X"` is not a valid encoding for any letter) — both conditions in the transition must be checked independently, since a position can be reachable via the two-digit path even when the single-digit path is invalid.

- `dp[i] = (valid single digit ? dp[i-1] : 0) + (valid two digits ? dp[i-2] : 0)`: the conditional counting variant of the Fibonacci/Linear template.
- Checking `s.charAt(0) == '0'` upfront handles the case where the ENTIRE string cannot start decoding at all.
- Related problems: Climbing Stairs (the unconditional version of this same "look back 1 or 2" recurrence), Word Break (also builds `dp[i]` from earlier reachable prefixes, but checks against a dictionary instead of a numeric range).
