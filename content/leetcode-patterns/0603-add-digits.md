---
card: leetcode-patterns
gi: 603
slug: add-digits
title: Add Digits
---

## 1. What it is

Given a non-negative integer `num`, repeatedly add all its digits together until only a single digit remains, and return that digit. This single-digit result is called the **digital root**. Example: `num=38` → `3+8=11`, then `1+1=2`; return `2`. A follow-up asks: can you solve this in O(1), without any loop?

## 2. Why & when

The naive repeated-summing approach directly simulates the problem statement, and it works. But the digital root has a well-known closed-form formula based on **modular arithmetic**: it equals `num mod 9`, with two adjustments — `0` stays `0`, and any positive multiple of `9` maps to `9` (not `0`). Recognizing "repeated digit-sum until one digit remains" as the digital-root operation is the signal to reach for the mod-9 formula instead of looping.

## 3. Core concept

**Key idea:** the digital root formula is `1 + (num - 1) % 9` for `num > 0`, and `0` for `num == 0`. This single expression avoids ever summing digits or looping.

**Why `mod 9` specifically:** in base 10, `10 ≡ 1 (mod 9)`, so any power of 10 is also `≡ 1 (mod 9)`. This means a number's value modulo 9 is always congruent to the sum of its digits modulo 9 (since each digit's place-value contribution reduces to just the digit itself, mod 9). Repeatedly summing digits preserves this same "mod 9" residue at every step, all the way down to a single digit — so the final single-digit answer must equal `num mod 9`, adjusted only for the boundary cases where a direct `%` would give `0` for a nonzero multiple of 9 (since the digital root of, say, `18` is `9`, not `0`).

**Why the `1 + (num - 1) % 9` formula handles the boundary correctly:** plain `num % 9` gives `0` both for `num == 0` and for any positive multiple of `9` (like `9`, `18`, `27`) — but the digital root of a positive multiple of 9 is `9`, not `0`. Shifting to `1 + (num-1) % 9` maps `num=9` to `1 + 8%9 = 1+8 = 9` correctly, while `num=0` is handled as a separate special case (`(0-1)%9` in most languages would not give a clean answer, and `0`'s digital root is trivially `0` anyway).

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Repeated digit summing of 38 converges to the same result as the mod-9 formula">
  <g font-family="sans-serif" font-size="12">
    <rect x="30" y="30" width="80" height="35" fill="#161b22" stroke="#30363d"/><text x="70" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">38</text>
    <rect x="150" y="30" width="80" height="35" fill="#161b22" stroke="#30363d"/><text x="190" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">3+8=11</text>
    <rect x="270" y="30" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="310" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">1+1=2</text>
    <line x1="110" y1="47" x2="150" y2="47" stroke="#8b949e" marker-end="url(#a11)"/>
    <line x1="230" y1="47" x2="270" y2="47" stroke="#8b949e" marker-end="url(#a11)"/>
    <defs><marker id="a11" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="450" y="52" fill="#79c0ff" text-anchor="middle">formula: 1+(38-1)%9 = 1+37%9 = 1+1 = 2</text>
    <text x="350" y="110" fill="#8b949e" text-anchor="middle">both paths reach the same digital root, since digit-summing preserves value mod 9</text>
  </g>
</svg>

Repeated digit summing and the mod-9 formula always agree, because summing digits never changes a number's residue modulo 9.

## 5. Runnable example

**Level 1 — Brute force / loop.** Repeatedly sum the digits of `num` (using `% 10` and `/ 10` to extract them) until the result is a single digit. O(log(num)) per summing pass, and possibly several passes.

**KEY INSIGHT:** since `10 ≡ 1 (mod 9)`, any number's value modulo 9 already equals its digit sum modulo 9 — repeated summing is just repeatedly computing "mod 9" in a roundabout way, so a single closed-form formula replaces the entire loop.

**Level 2 — Optimal.** `1 + (num - 1) % 9` for `num > 0`, else `0`. O(1) time, O(1) space.

**Level 3 — Hardened.** Both the loop version and the formula version are provided, so the formula's correctness can be checked against simulation across many inputs, including the `num == 0` edge case.

```java
// AddDigits.java
public class AddDigits {

    // Level 1: repeated digit summing (the loop the problem describes directly).
    static int addDigitsLoop(int num) {
        while (num >= 10) {
            int sum = 0;
            while (num > 0) {
                sum += num % 10;
                num /= 10;
            }
            num = sum;
        }
        return num;
    }

    // Level 2/3: O(1) digital root formula.
    static int addDigitsFormula(int num) {
        if (num == 0) return 0;
        return 1 + (num - 1) % 9;
    }

    public static void main(String[] args) {
        for (int n : new int[]{0, 9, 18, 38, 132}) {
            System.out.println(n + " -> loop=" + addDigitsLoop(n) + ", formula=" + addDigitsFormula(n));
        }
    }
}
```

**How to run:** save as `AddDigits.java`, then run `java AddDigits.java`.

## 6. Walkthrough

Trace `addDigitsFormula(18)` and confirm against `addDigitsLoop(18)`:

1. `addDigitsLoop(18)`: `num=18 >= 10`, sum digits: `1+8=9`. `num=9`, now `< 10`, loop ends. Return `9`.
2. `addDigitsFormula(18)`: `num != 0`, so compute `1 + (18-1) % 9 = 1 + 17 % 9 = 1 + 8 = 9`.
3. Both return `9`, confirming the formula matches simulation — `18`'s digits sum to `9` directly in one pass, and the formula reaches the same answer with no loop at all.

## 7. Gotchas & takeaways

> Gotcha: using plain `num % 9` instead of `1 + (num - 1) % 9` gives `0` for any positive multiple of `9` (like `9`, `18`, `27`), but their correct digital root is `9`, not `0` — only `num == 0` itself should produce a `0` result.

- Signal: "repeat an operation on a number's digits until one digit remains" is the digital-root signal, solvable in O(1) via `mod 9`, because `10 ≡ 1 (mod 9)`.
- The loop version is still correct and easy to reason about; the formula version is the O(1) follow-up the problem explicitly invites.
- Related problems: Happy Number (a different repeated-digit-operation problem — sum of squared digits — that needs cycle detection instead of a closed-form formula, since it does not converge to a single fixed value the same way).
