---
card: leetcode-patterns
gi: 470
slug: final-prices-with-a-special-discount-in-a-shop
title: Final Prices With a Special Discount in a Shop
---

## 1. What it is

You get an array `prices`, where `prices[i]` is the price of the `i`-th item. For each item, if there is a later item with a price less than or equal to it, the item gets a discount equal to that later price (only the first such later item counts). Return the array of final prices. Example: `prices = [8, 4, 6, 2, 3]` → `[4, 2, 4, 2, 3]`.

## 2. Why & when

This is "next smaller-or-equal element," a direct variant of the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md): "the first later item with price less than or equal" is exactly a next-smaller-or-equal query for every index. Constraints: up to 500 items.

## 3. Core concept

**Key idea:** use an **increasing** monotonic stack of indices. As you scan left to right, the current price is compared against the price at the top of the stack. If the current price is less than or equal to that top price, the top index's discount is resolved — pop it, subtract the current price from its original price.

**Steps:**
1. Copy `prices` into a `result` array (default: no discount, so `result[i] = prices[i]`).
2. Maintain a stack of indices, kept increasing in price (bottom to top).
3. For each index `i`: while the stack is not empty and `prices[i] <= prices[stack.peek()]`, pop an index `j` and set `result[j] = prices[j] - prices[i]`.
4. Push `i` onto the stack.
5. Indices left on the stack at the end get no discount, so their `result` value stays equal to their original price.

**Why "less than or equal" (not strictly less) matters:** the problem statement defines the discount using "less than or equal to," which changes the pop condition from a strict next-greater comparison. Missing this detail is the most common bug on this problem.

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Increasing stack resolving discounts as smaller-or-equal prices arrive">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">prices = [8, 4, 6, 2, 3]</text>
    <rect x="20" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="70" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="120" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="170" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="220" y="40" width="50" height="34" fill="#161b22" stroke="#30363d"/>
    <text x="45" y="63" fill="#e6edf3" text-anchor="middle">8</text>
    <text x="95" y="63" fill="#e6edf3" text-anchor="middle">4</text>
    <text x="145" y="63" fill="#e6edf3" text-anchor="middle">6</text>
    <text x="195" y="63" fill="#e6edf3" text-anchor="middle">2</text>
    <text x="245" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="20" y="100" fill="#8b949e">i=1 (4): pops i=0 (8&gt;=4) -&gt; result[0]=8-4=4</text>
    <text x="20" y="120" fill="#8b949e">i=3 (2): pops i=2 (6&gt;=2), pops i=1 (4&gt;=2) -&gt; result[2]=4, result[1]=2</text>
    <text x="20" y="140" fill="#8b949e">i=4 (3): 2&lt;3, no pop -&gt; push 4</text>
    <text x="20" y="160" fill="#3fb950">final: [4, 2, 4, 2, 3]</text>
  </g>
</svg>

Each price pops every stacked price that is greater than or equal to it, applying that discount immediately.

## 5. Runnable example

**Level 1 — Brute force.** For each item, scan forward for the first price less than or equal to it. O(n²).

**KEY INSIGHT:** "first later item that is smaller or equal" is the next-smaller-or-equal query, solvable in one pass with an increasing monotonic stack of indices.

**Level 2 — Optimal.** Single-pass stack solution, O(n).

**Level 3 — Hardened.** Handles no-discount items (price never matched) and a single-item array.

```java
// FinalPrices.java
import java.util.*;

public class FinalPrices {

    // Level 1: brute force, O(n^2)
    static int[] bruteForce(int[] prices) {
        int[] result = prices.clone();
        for (int i = 0; i < prices.length; i++) {
            for (int j = i + 1; j < prices.length; j++) {
                if (prices[j] <= prices[i]) {
                    result[i] = prices[i] - prices[j];
                    break;
                }
            }
        }
        return result;
    }

    // Level 2 & 3: increasing monotonic stack of indices, O(n)
    static int[] finalPrices(int[] prices) {
        int[] result = prices.clone();
        Deque<Integer> stack = new ArrayDeque<>(); // increasing prices, holds indices

        for (int i = 0; i < prices.length; i++) {
            while (!stack.isEmpty() && prices[stack.peek()] >= prices[i]) {
                int j = stack.pop();
                result[j] = prices[j] - prices[i];
            }
            stack.push(i);
        }
        return result;
    }

    public static void main(String[] args) {
        int[] prices = {8, 4, 6, 2, 3};
        System.out.println("brute force: " + Arrays.toString(bruteForce(prices)));
        System.out.println("optimal:     " + Arrays.toString(finalPrices(prices)));

        System.out.println("no discounts: " + Arrays.toString(finalPrices(new int[]{1, 2, 3, 4})));
        System.out.println("single item:  " + Arrays.toString(finalPrices(new int[]{10})));
    }
}
```

**How to run:** save as `FinalPrices.java`, then run `java FinalPrices.java`.

## 6. Walkthrough

Trace `finalPrices({8, 4, 6, 2, 3})`:

| i | price | stack before | action | stack after |
|---|---|---|---|---|
| 0 | 8 | [] | push 0 | [0] |
| 1 | 4 | [0] | `prices[0]=8 >= 4`: pop 0, `result[0]=8-4=4`; push 1 | [1] |
| 2 | 6 | [1] | `prices[1]=4 >= 6`? no; push 2 | [1, 2] |
| 3 | 2 | [1, 2] | `prices[2]=6 >= 2`: pop 2, `result[2]=6-2=4`. `prices[1]=4 >= 2`: pop 1, `result[1]=4-2=2`; push 3 | [3] |
| 4 | 3 | [3] | `prices[3]=2 >= 3`? no; push 4 | [3, 4] |

Indices `3` and `4` are never popped, so `result[3]=prices[3]=2` and `result[4]=prices[4]=3` (no discount). Final: `[4, 2, 4, 2, 3]`, matching the expected output.

## 7. Gotchas & takeaways

> Gotcha: using a strict `>` instead of `>=` in the pop condition misses the "or equal to" case from the problem statement, giving no discount when the later price exactly matches — always re-read whether the problem means strictly smaller or smaller-or-equal.

- Signal: "first later item with a smaller-or-equal value" is a next-smaller-or-equal query.
- The stack must stay increasing (by price) and hold indices, so the discount can be written to the right slot in `result`.
- Time: O(n) — every index is pushed once and popped at most once.
