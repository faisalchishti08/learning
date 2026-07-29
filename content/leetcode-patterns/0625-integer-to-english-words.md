---
card: leetcode-patterns
gi: 625
slug: integer-to-english-words
title: Integer to English Words
---

## 1. What it is

Given a non-negative integer `num` (up to `2^31 - 1`), convert it to its English words representation. Example: `num=123` → `"One Hundred Twenty Three"`; `num=1234567` → `"One Million Two Hundred Thirty Four Thousand Five Hundred Sixty Seven"`.

## 2. Why & when

This is a compound conversion problem: English number names are structured in repeating **groups of three digits** (ones, thousands, millions, billions), where each group of three digits (`0-999`) is converted using the *same* sub-routine, then suffixed with a scale word (`"Thousand"`, `"Million"`, `"Billion"`). Recognizing this repeating three-digit-group structure is what turns a seemingly ad hoc string-building problem into a clean, reusable helper applied at each scale.

## 3. Core concept

**Key idea:** split `num` into groups of three digits from the right (ones group, thousands group, millions group, billions group). Convert each non-zero group independently using a helper that handles any number from `1` to `999` (itself broken into hundreds, tens, and ones, with special handling for the irregular `11-19` teen names). Join the groups together, largest scale first, each followed by its scale word.

**Steps:**
1. If `num == 0`, return `"Zero"` immediately (a special case, since the general algorithm below only processes non-zero groups).
2. Define word lists: `ones` for `0-19` (including the irregular teens), `tens` for the tens digit (`20, 30, ..., 90`), and scale words `["", "Thousand", "Million", "Billion"]`.
3. A helper `convertBelow1000(n)`: if `n >= 100`, emit `ones[n/100] + " Hundred"`, then recurse (or continue) on `n % 100`. If the remainder is `>= 20`, emit `tens[remainder/10]`, then if `remainder % 10 != 0`, emit `ones[remainder % 10]`. If the remainder is `1-19`, emit `ones[remainder]` directly (handles the irregular teens in one lookup).
4. Split `num` into groups of 3 digits, from the least significant group upward, pairing each with its scale word (index `0` = no suffix, index `1` = "Thousand", etc.).
5. For each group (processing from the *most* significant non-zero group down to the least, to build the string in correct reading order), if the group is non-zero, convert it with `convertBelow1000` and append its scale word.

**Why the `ones` array must directly include indices `11` through `19` (not derive them from `10 + 1..9`):** English number names are irregular in this range — `"Eleven"`, `"Twelve"`, `"Thirteen"` do not follow the regular "tens-word plus ones-word" pattern that `"Twenty One"` or `"Forty Five"` do. Storing them as direct, individual entries in the lookup array sidesteps needing separate irregular-case logic.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="1234567 split into groups of three digits, each converted independently and suffixed with its scale word">
  <g font-family="sans-serif" font-size="12">
    <rect x="30" y="30" width="140" height="35" fill="#161b22" stroke="#3fb950"/><text x="100" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">1 -&gt; "One" "Million"</text>
    <rect x="200" y="30" width="180" height="35" fill="#161b22" stroke="#f0883e"/><text x="290" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">234 -&gt; "Two Hundred Thirty Four" "Thousand"</text>
    <rect x="410" y="30" width="180" height="35" fill="#161b22" stroke="#79c0ff"/><text x="500" y="52" fill="#e6edf3" text-anchor="middle" font-size="10">567 -&gt; "Five Hundred Sixty Seven"</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">each group of 3 digits uses the identical convertBelow1000 helper</text>
  </g>
</svg>

Every group of three digits, regardless of its scale, is converted by the exact same reusable helper — only the trailing scale word differs between groups.

## 5. Runnable example

**Level 1 — Brute force.** Write separate, largely duplicated conversion logic for the ones group, thousands group, and millions group individually, instead of a shared helper. Works, but triples (or more) the amount of nearly-identical code.

**KEY INSIGHT:** every group of three digits, regardless of its scale (ones, thousands, millions, billions), is converted by the exact same `1-999` sub-routine — factoring this into one reusable helper, called once per non-zero group, avoids duplicating the hundreds/tens/ones logic at every scale.

**Level 2 — Optimal.** Split into groups of 3 digits, shared `convertBelow1000` helper per group, join with scale words, O(digits) time and space.

**Level 3 — Hardened.** Correctly handles `num == 0` as a special case, correctly uses direct lookup for the irregular `11-19` teen names, and correctly skips scale words entirely for any group that is zero (avoiding output like `"Zero Thousand"`).

```java
// IntegerToEnglishWords.java
public class IntegerToEnglishWords {

    private static final String[] ONES = {
        "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"
    };
    private static final String[] TENS = {
        "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
    };
    private static final String[] SCALES = {"", "Thousand", "Million", "Billion"};

    private static String convertBelow1000(int n) {
        StringBuilder sb = new StringBuilder();
        if (n >= 100) {
            sb.append(ONES[n / 100]).append(" Hundred ");
            n %= 100;
        }
        if (n >= 20) {
            sb.append(TENS[n / 10]).append(" ");
            n %= 10;
            if (n > 0) sb.append(ONES[n]).append(" ");
        } else if (n > 0) {
            sb.append(ONES[n]).append(" ");
        }
        return sb.toString();
    }

    public static String numberToWords(int num) {
        if (num == 0) return "Zero";

        StringBuilder result = new StringBuilder();
        int scaleIndex = 0;
        java.util.List<Integer> groups = new java.util.ArrayList<>();
        while (num > 0) {
            groups.add(num % 1000);
            num /= 1000;
        }

        for (int i = groups.size() - 1; i >= 0; i--) {
            int group = groups.get(i);
            if (group != 0) {
                result.append(convertBelow1000(group));
                if (!SCALES[i].isEmpty()) {
                    result.append(SCALES[i]).append(" ");
                }
            }
        }

        return result.toString().trim();
    }

    public static void main(String[] args) {
        System.out.println(numberToWords(123));     // One Hundred Twenty Three
        System.out.println(numberToWords(1234567));  // One Million Two Hundred Thirty Four Thousand Five Hundred Sixty Seven
    }
}
```

**How to run:** save as `IntegerToEnglishWords.java`, then run `java IntegerToEnglishWords.java`.

## 6. Walkthrough

Trace `numberToWords(1234567)`:

1. Split into groups of 3 (least significant first): `groups = [567, 234, 1]` (`1234567 % 1000 = 567`, then `1234 % 1000 = 234`, then `1`).
2. Process from most significant (`i=2`) to least (`i=0`):
3. `i=2`, `group=1`: non-zero. `convertBelow1000(1) = "One "`. Scale `SCALES[2]="Million"`. Append `"One Million "`.
4. `i=1`, `group=234`: non-zero. `convertBelow1000(234)`: `234 >= 100`, append `"Two Hundred "`, `n=34`; `34 >= 20`, append `"Thirty "`, `n=4`; `n>0`, append `"Four "`. Result: `"Two Hundred Thirty Four "`. Scale `"Thousand"`. Append `"Two Hundred Thirty Four Thousand "`.
5. `i=0`, `group=567`: non-zero. `convertBelow1000(567) = "Five Hundred Sixty Seven "`. Scale `SCALES[0]=""`, no scale word appended.
6. Final (trimmed): `"One Million Two Hundred Thirty Four Thousand Five Hundred Sixty Seven"`.

## 7. Gotchas & takeaways

> Gotcha: appending a scale word even when its group is zero (like producing `"Zero Thousand"` for a number like `1000000` where the thousands group is `000`) produces invalid output — always check `group != 0` before both converting the group *and* appending its scale word.

- Signal: number-to-words conversion is a repeating-groups-of-three-digits signal — one shared sub-routine handles every group, only the trailing scale word changes.
- The irregular teen names (`11-19`) are best handled by direct array lookup, not derived arithmetically from tens and ones.
- Related problems: none directly in this section, but the "process fixed-size groups with a shared helper, differing only by an outer label" pattern generalizes to other structured string-building problems.
