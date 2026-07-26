---
card: leetcode-patterns
gi: 447
slug: lemonade-change
title: Lemonade Change
---

## 1. What it is

Lemonade costs `$5`. Customers pay with a `$5`, `$10`, or `$20` bill, one at a time, in the given order, and must receive EXACT change. Starting with no money, return whether you can give correct change to every customer. Example: `bills = [5,5,5,10,20]` → `true`.

## 2. Why & when

Use this shape whenever a problem requires making CHANGE (or a similar resource-allocation decision) using a SMALL set of denominations, processed in a FIXED order, where a specific greedy tie-breaking rule (prefer using larger bills for change first) is what keeps future options open.

## 3. Core concept

**Key idea:** track only how many `$5` and `$10` bills you are currently holding (you never need to give a `$20` back as change, so its count does not matter for future decisions).

**Steps:**
1. For a `$5` bill: no change needed. Increment your `$5` count.
2. For a `$10` bill: give one `$5` as change (fail if you have none). Increment your `$10` count.
3. For a `$20` bill: give `$15` in change, preferring a `$10` + a `$5` FIRST (if both are available); only fall back to three `$5`s if you have no `$10` to use. If neither option is available, return `false`.
4. If every customer is served, return `true`.

**Why preferring a `$10` + `$5` over three `$5`s is the correct greedy tie-break:** a `$5` bill is more FLEXIBLE than a `$10` bill, since a `$5` can be used to make change for EITHER a `$10` or a `$20` customer, while a `$10` can only ever be used for a `$20` customer. Spending the LESS flexible `$10` first (when both options work) preserves more `$5`s for future customers who might specifically need them — this is the exchange argument that makes the tie-break safe.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a twenty dollar customer choosing between ten plus five or three fives with the ten plus five option preferred to save flexible fives">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">$20 customer needs $15 change -- two ways to pay it</text>
    <rect x="20" y="40" width="140" height="26" fill="#3fb950"/><text x="90" y="58" text-anchor="middle" font-size="10" fill="#0d1117">preferred: $10 + $5</text>
    <rect x="180" y="40" width="140" height="26" fill="#30363d" stroke="#8b949e"/><text x="250" y="58" text-anchor="middle" font-size="10">fallback: $5+$5+$5</text>
    <rect x="10" y="80" width="330" height="24" fill="#3fb950"/><text x="175" y="97" fill="#0d1117" text-anchor="middle" font-size="10">$5 bills are more flexible -- spend the less flexible $10 first</text>
  </g>
</svg>

Preferring to spend the less flexible bill first preserves the more flexible one for future customers.

## 5. Runnable example

```java
// LemonadeChange.java
public class LemonadeChange {

    // KEY INSIGHT: a $5 bill is more flexible than a $10 (it can make
    // change for either a $10 or a $20 customer) -- always spend the
    // less flexible $10 first, when both options are available.

    static boolean lemonadeChange(int[] bills) {
        int fives = 0, tens = 0;
        for (int bill : bills) {
            if (bill == 5) {
                fives++;
            } else if (bill == 10) {
                if (fives == 0) return false;
                fives--;
                tens++;
            } else {
                if (tens > 0 && fives > 0) {
                    tens--;
                    fives--;
                } else if (fives >= 3) {
                    fives -= 3;
                } else {
                    return false;
                }
            }
        }
        return true;
    }

    public static void main(String[] args) {
        System.out.println(lemonadeChange(new int[]{5, 5, 5, 10, 20}));
        // true
        System.out.println(lemonadeChange(new int[]{5, 5, 10, 10, 20}));
        // false
    }
}
```

**How to run:** `java LemonadeChange.java`

## 6. Walkthrough

Trace `lemonadeChange([5,5,10,10,20])`:

| bill | fives before | tens before | action | fives after | tens after |
|---|---|---|---|---|---|
| 5 | 0 | 0 | fives++ | 1 | 0 |
| 5 | 1 | 0 | fives++ | 2 | 0 |
| 10 | 2 | 0 | use one $5 | 1 | 1 |
| 10 | 1 | 1 | use one $5 | 0 | 2 |
| 20 | 0 | 2 | need $10+$5, but fives=0, and fives&lt;3 -- FAIL | — | — |

The function returns `false` at the last customer, matching the expected answer: two `$10` customers used up both `$5` bills, leaving nothing to give the final `$20` customer. Time complexity is O(n). Space is O(1).

## 7. Gotchas & takeaways

> Gotcha: giving three `$5`s for a `$20` customer when a `$10` + `$5` was ALSO available (instead of preferring the `$10`+`$5` combination) is not INCORRECT for that single customer, but it wastes flexible `$5`s that a LATER customer might strictly need — always apply the preference, even when the fallback would also technically work for the current step.

- Only `$5` and `$10` counts matter — `$20` bills are never given as change, so tracking how many you've collected is unnecessary.
- The tie-break rule (prefer spending less-flexible bills first) is the entire greedy insight in this problem — without it, a naive "any valid combination works" approach can fail on later customers.
- Related problems: Assign Cookies (a different matching-based greedy, without the "preserve flexibility" tie-break), Gas Station (a running-balance greedy, tracking one cumulative value instead of discrete bill counts).
