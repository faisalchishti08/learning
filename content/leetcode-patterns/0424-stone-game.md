---
card: leetcode-patterns
gi: 424
slug: stone-game
title: Stone Game
---

## 1. What it is

Alice and Bob take turns picking a pile of stones from either END of a row of piles, adding that pile's stone count to their own total. Alice goes first, and both players play OPTIMALLY. Return `true` if Alice wins (strictly more stones than Bob). Example: `piles = [5, 3, 4, 5]` → `true`.

## 2. Why & when

Use this shape whenever a problem is phrased as a named two-player game (Alice vs. Bob) picking from either end of a row, and it guarantees an EVEN number of piles with an ODD total of stones (no ties possible). This is the exact same DP as Predict the Winner; the constraints here simply let you ALSO reason about it without writing any code at all.

## 3. Core concept

**Key idea:** reuse the identical `dp[i][j]` = maximum score difference the current player can guarantee, over the range of remaining piles `[i, j]`.

**Steps:**
1. Base case: `dp[i][i] = piles[i]`.
2. `dp[i][j] = max(piles[i] - dp[i+1][j], piles[j] - dp[i][j-1])`, filled by increasing range length, exactly as in Predict the Winner.
3. Alice wins if and only if `dp[0][n-1] > 0` (this problem asks for a STRICT win, not a tie — but a tie is impossible here anyway, since piles always sum to an odd total).

**The mathematical shortcut this problem's constraints unlock:** because there is always an EVEN number of piles, Alice (moving first) can always choose to take only the piles at EVEN INDICES, or always take only the piles at ODD INDICES — she gets to pick which parity she commits to on her very first move, and Bob is then forced to take whichever piles are left. Comparing the sum of even-indexed piles to the sum of odd-indexed piles tells Alice which parity is bigger; picking that parity guarantees her at least that much, so Alice can ALWAYS win under these specific constraints. This means the DP, while fully general and always correct, is not strictly necessary for this problem's specific constraints — but it is worth solving with DP anyway, since it is the general technique that also handles Predict the Winner's harder, unconstrained version.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="alice choosing to commit to either all even indexed piles or all odd indexed piles on her first move">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">piles = [5, 3, 4, 5] -- even-index sum = 5+4 = 9; odd-index sum = 3+5 = 8</text>
    <rect x="10" y="40" width="300" height="24" fill="#3fb950"/><text x="160" y="57" fill="#0d1117" text-anchor="middle" font-size="10">Alice commits to even indices (9 &gt; 8) and always wins</text>
    <text x="10" y="85">the general dp[i][j] transition still applies, and agrees with this shortcut</text>
  </g>
</svg>

Alice's first move locks in a whole parity class of piles that Bob can never take from her.

## 5. Runnable example

```java
// StoneGame.java
public class StoneGame {

    // KEY INSIGHT: identical DP to Predict the Winner -- track the
    // score DIFFERENCE the current player can guarantee, not each
    // player's raw total.

    static boolean stoneGame(int[] piles) {
        int n = piles.length;
        int[][] dp = new int[n][n];
        for (int i = 0; i < n; i++) dp[i][i] = piles[i];

        for (int len = 2; len <= n; len++) {
            for (int i = 0; i + len - 1 < n; i++) {
                int j = i + len - 1;
                dp[i][j] = Math.max(piles[i] - dp[i + 1][j], piles[j] - dp[i][j - 1]);
            }
        }
        return dp[0][n - 1] > 0;
    }

    public static void main(String[] args) {
        System.out.println(stoneGame(new int[]{5, 3, 4, 5}));
        // true
        System.out.println(stoneGame(new int[]{3, 7, 2, 3}));
        // true
    }
}
```

**How to run:** `java StoneGame.java`

## 6. Walkthrough

Trace `dp` for `piles = [5, 3, 4, 5]`:

| range | dp value |
|---|---|
| [0,0],[1,1],[2,2],[3,3] | 5, 3, 4, 5 |
| [0,1] | max(5-3, 3-5) = 2 |
| [1,2] | max(3-4, 4-3) = 1 |
| [2,3] | max(4-5, 5-4) = 1 |
| [0,2] | max(5-1, 4-2) = 4 |
| [1,3] | max(3-1, 5-1) = 4 |
| [0,3] | max(5-4, 5-4) = 1 |

`dp[0][3] = 1 > 0`, so Alice wins, matching the expected answer. Time complexity is O(n^2). Space is O(n^2) (reducible to O(n)).

## 7. Gotchas & takeaways

> Gotcha: this problem asks for a STRICT win (`dp[0][n-1] > 0`), unlike Predict the Winner's tie-inclusive `>= 0` — always re-check the exact comparison a problem's wording demands, even when reusing an otherwise identical DP.

- Identical `dp[i][j]` transition to Predict the Winner: this problem is really "Predict the Winner, under constraints that also admit a clever O(1) mathematical shortcut."
- The parity-based shortcut (even-index sum vs. odd-index sum) only works because of THIS problem's guarantees (even pile count); it does not generalize to arbitrary two-player range games.
- Related problems: Predict the Winner (the fully general version, without the even-count/odd-total guarantees), Guess Number Higher or Lower II (a different adversarial game, with a full scan over guesses instead of two end choices).
