---
card: leetcode-patterns
gi: 57
slug: happy-number
title: Happy Number
---

## 1. What it is

A number `n` is "happy" if repeatedly replacing it with the sum of the squares of its digits eventually reaches `1`. If this process loops forever without reaching `1`, the number is not happy. Example: `n = 19` → `1² + 9² = 82` → `8² + 2² = 68` → `6² + 8² = 100` → `1² + 0² + 0² = 1` → happy, answer `true`.

## 2. Why & when

This problem does not look like a linked list, but it hides the same shape: repeatedly applying a function to a value produces a sequence. That sequence either reaches `1` and stays there, or it falls into a repeating cycle that never includes `1`. "Detect whether an iterated process cycles" is exactly the Fast & Slow Pointers signal, just applied to values instead of list nodes.

## 3. Core concept

**Key idea:** treat each number in the sequence as a "node", where the "next node" is the sum of squares of its digits. Run fast & slow pointers over this implicit sequence. If the sequence reaches `1`, it is happy. If `slow` and `fast` ever meet on a value that is not `1`, the sequence is stuck in a cycle and the number is not happy.

**Steps:**
1. Define `next(n)` = sum of squares of the digits of `n`.
2. Set `slow = n`, `fast = next(n)`.
3. While `fast != 1 && slow != fast`:
   - `slow = next(slow)` (one step).
   - `fast = next(next(fast))` (two steps).
4. Return `fast == 1`.

**Why it is correct:** the sequence of digit-square-sums for any starting number is bounded (it cannot grow forever, since squaring digits of a number caps the next value well below the input for numbers with more than 3 digits). A bounded sequence with a deterministic next-step function must eventually repeat a value, forming a cycle. Fast & slow pointers detects that cycle exactly as it does on a linked list.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Happy number sequence treated as a linked list with fast and slow pointers">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">n = 19: 19 -&gt; 82 -&gt; 68 -&gt; 100 -&gt; 1 (reaches 1, happy)</text>
    <circle cx="60" cy="90" r="22" fill="#161b22" stroke="#79c0ff"/>
    <text x="60" y="95" fill="#e6edf3" text-anchor="middle">19</text>
    <circle cx="150" cy="90" r="22" fill="#161b22" stroke="#79c0ff"/>
    <text x="150" y="95" fill="#e6edf3" text-anchor="middle">82</text>
    <circle cx="240" cy="90" r="22" fill="#161b22" stroke="#79c0ff"/>
    <text x="240" y="95" fill="#e6edf3" text-anchor="middle">68</text>
    <circle cx="330" cy="90" r="22" fill="#161b22" stroke="#79c0ff"/>
    <text x="330" y="95" fill="#e6edf3" text-anchor="middle">100</text>
    <circle cx="420" cy="90" r="22" fill="#161b22" stroke="#3fb950"/>
    <text x="420" y="95" fill="#e6edf3" text-anchor="middle">1</text>
    <line x1="82" y1="90" x2="128" y2="90" stroke="#8b949e" marker-end="url(#c)"/>
    <line x1="172" y1="90" x2="218" y2="90" stroke="#8b949e" marker-end="url(#c)"/>
    <line x1="262" y1="90" x2="308" y2="90" stroke="#8b949e" marker-end="url(#c)"/>
    <line x1="352" y1="90" x2="398" y2="90" stroke="#8b949e" marker-end="url(#c)"/>
    <defs><marker id="c" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#8b949e"/></marker></defs>
    <text x="20" y="160" fill="#8b949e">each number is a "node"; next(n) = sum of squares of its digits is the "next pointer"</text>
  </g>
</svg>

The value sequence behaves like a linked list where each number's "next" is computed, not stored — fast & slow pointers still detects whether it loops.

## 5. Runnable example

```java
// HappyNumber.java
import java.util.HashSet;
import java.util.Set;

public class HappyNumber {

    static int next(int n) {
        int sum = 0;
        while (n > 0) {
            int digit = n % 10;
            sum += digit * digit;
            n /= 10;
        }
        return sum;
    }

    // Level 1 -- Brute force: track seen values in a hash set. O(log n)
    // steps to converge, but O(log n) extra space for the set -- wastes
    // memory for a value sequence that only needs O(1).
    static boolean bruteForce(int n) {
        Set<Integer> seen = new HashSet<>();
        while (n != 1 && seen.add(n)) {
            n = next(n);
        }
        return n == 1;
    }

    // KEY INSIGHT: the digit-square-sum sequence is bounded and
    // deterministic, so it must eventually repeat a value -- fast &amp; slow
    // pointers can detect that repeat without storing any history.

    // Level 2 -- Optimal: fast &amp; slow pointers over the implicit
    // sequence. O(log n) time, O(1) space.
    public static boolean isHappy(int n) {
        int slow = n, fast = next(n);
        while (fast != 1 && slow != fast) {
            slow = next(slow);
            fast = next(next(fast));
        }
        return fast == 1;
    }

    // Level 3 -- Hardened: single-digit inputs, including 1 itself
    // (already happy) and 4 (the smallest unhappy number, which cycles
    // 4 -> 16 -> 37 -> 58 -> 89 -> 145 -> 42 -> 20 -> 4).
    static boolean hardened(int n) {
        if (n <= 0) throw new IllegalArgumentException("n must be positive");
        return isHappy(n);
    }

    public static void main(String[] args) {
        System.out.println("19 brute force: " + bruteForce(19));
        System.out.println("19 optimal:     " + isHappy(19));
        System.out.println("2 is happy?     " + hardened(2));
        System.out.println("4 is happy?     " + hardened(4));
    }
}
```

How to run: save as `HappyNumber.java`, then run `java HappyNumber.java`.

## 6. Walkthrough

Dry run of `isHappy(19)`:

| step | slow | fast |
|---|---|---|
| start | 19 | next(19)=82 |
| 1 | next(19)=82 | next(next(82))=next(68)=100 |
| 2 | next(82)=68 | next(next(100))=next(1)=1 |
| — | — | `fast == 1`, loop stops -> return true |

Time complexity: O(log n) per digit-square step multiplied by the number of steps until the sequence stabilizes, effectively bounded and treated as O(log n) for practical inputs. Space complexity: O(1), since only `slow` and `fast` are stored.

## 7. Gotchas & takeaways

> Gotcha: checking `slow == fast` before checking `fast != 1` can loop forever comparing two variables that both start unequal; always check `fast == 1` (or `slow == 1`) as the primary success condition, with the equality check only as the cycle (failure) signal.

- The "sequence" here has no explicit list nodes — recognizing that a repeatedly-applied function forms an implicit linked list is the key transfer from the earlier pattern-meta pages.
- Related problems: Linked List Cycle (the direct list version of this same idea), Find the Duplicate Number (treats array values as next-pointers).
