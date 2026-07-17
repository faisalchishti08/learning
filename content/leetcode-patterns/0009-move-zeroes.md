---
card: leetcode-patterns
gi: 9
slug: move-zeroes
title: Move Zeroes
---

## 1. What it is

Given an integer array `nums`, move all `0`s to the end while keeping the relative order of the non-zero elements, and do it in place without making a copy of the array. Example: `nums = [0, 1, 0, 3, 12]` → after the operation, `[1, 3, 12, 0, 0]`.

## 2. Why & when

"In place" plus "keep relative order" plus "single array, no extra copy" is the signal for same-direction two pointers: `slow` marks where the next non-zero value should go, `fast` scans ahead to find it. This is the same compacting shape as Remove Duplicates from Sorted Array, but here the array does not need to be sorted — the condition is "is this value non-zero," not "is this a duplicate."

## 3. Core concept

**Key idea:** every non-zero value needs to move to the earliest available non-zero slot, in the order it was found. That is exactly what `slow` (write position) and `fast` (scan position) do together.

**Steps:**
1. Set `slow = 0`.
2. For `fast` from 0 to the end:
   - If `nums[fast] != 0`, swap `nums[slow]` and `nums[fast]`, then increment `slow`.
   - If `nums[fast] == 0`, do nothing except let `fast` continue.
3. By the end, everything before `slow` is non-zero and in original order; everything from `slow` onward is `0`.

**Why it is correct:** using a **swap** (not a plain overwrite) is the key detail here. It guarantees the zero that used to live at `nums[slow]` gets pushed forward to `nums[fast]`'s old position instead of being lost, so no extra pass to "fill in the zeroes at the end" is needed — the swap does both jobs (write the non-zero value, relocate the zero) in one step.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Move zeroes swap based two pointers">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">nums = [0, 1, 0, 3, 12]</text>
    <rect x="20" y="40" width="44" height="34" fill="#161b22" stroke="#79c0ff"/>
    <rect x="64" y="40" width="44" height="34" fill="#161b22" stroke="#f0883e"/>
    <rect x="108" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="152" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="196" y="40" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <text x="42" y="63" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="86" y="63" fill="#e6edf3" text-anchor="middle">1</text>
    <text x="130" y="63" fill="#e6edf3" text-anchor="middle">0</text>
    <text x="174" y="63" fill="#e6edf3" text-anchor="middle">3</text>
    <text x="218" y="63" fill="#e6edf3" text-anchor="middle">12</text>
    <text x="42" y="95" fill="#79c0ff" text-anchor="middle">slow</text>
    <text x="86" y="95" fill="#f0883e" text-anchor="middle">fast</text>
    <text x="20" y="130" fill="#8b949e">nums[fast]=1 != 0 -&gt; swap(slow, fast) -&gt; [1,0,0,3,12], slow++</text>
    <text x="20" y="152" fill="#8b949e">swapping moves the zero forward instead of losing it</text>
  </g>
</svg>

Swapping (not overwriting) means the displaced zero moves to where the non-zero value used to be, staying inside the array.

## 5. Runnable example

```java
// MoveZeroes.java
import java.util.Arrays;

public class MoveZeroes {

    // Level 1 -- Brute force: copy non-zero values into a new array, then
    // pad with zeroes, then copy back. O(n) time, O(n) space -- extra array
    // the in-place constraint says to avoid.
    static void bruteForce(int[] nums) {
        int[] temp = new int[nums.length];
        int idx = 0;
        for (int v : nums) if (v != 0) temp[idx++] = v;
        System.arraycopy(temp, 0, nums, 0, nums.length);
    }

    // KEY INSIGHT: a swap (not a plain write) relocates the zero instead of
    // discarding it, so the zeroes end up correctly placed as a side effect
    // of moving the non-zero values -- no second pass needed.

    // Level 2 -- Optimal: same-direction two pointers with swap. O(n) time,
    // O(1) space.
    public static void moveZeroes(int[] nums) {
        int slow = 0;
        for (int fast = 0; fast < nums.length; fast++) {
            if (nums[fast] != 0) {
                int tmp = nums[slow];
                nums[slow] = nums[fast];
                nums[fast] = tmp;
                slow++;
            }
        }
    }

    // Level 3 -- Hardened: an array that is already all non-zero, or
    // entirely zero, both terminate correctly -- slow either reaches the
    // end (no zeroes moved) or never advances (nothing to swap).
    static void hardened(int[] nums) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        moveZeroes(nums);
    }

    public static void main(String[] args) {
        int[] nums = {0, 1, 0, 3, 12};
        moveZeroes(nums);
        System.out.println("optimal: " + Arrays.toString(nums));

        int[] allZero = {0, 0, 0};
        hardened(allZero);
        System.out.println("all zero: " + Arrays.toString(allZero));
    }
}
```

How to run: save as `MoveZeroes.java`, then run `java MoveZeroes.java`.

## 6. Walkthrough

Dry run of `moveZeroes({0, 1, 0, 3, 12})`:

| fast | nums[fast] before swap | action | array after step | slow after |
|---|---|---|---|---|
| 0 | 0 | zero, skip | [0, 1, 0, 3, 12] | 0 |
| 1 | 1 | swap(0,1) | [1, 0, 0, 3, 12] | 1 |
| 2 | 0 | zero, skip | [1, 0, 0, 3, 12] | 1 |
| 3 | 3 | swap(1,3) | [1, 3, 0, 0, 12] | 2 |
| 4 | 12 | swap(2,4) | [1, 3, 12, 0, 0] | 3 |

Final array: `[1, 3, 12, 0, 0]`. Time complexity: O(n), one pass. Space complexity: O(1), only `slow` and `fast` plus a temp swap variable.

## 7. Gotchas & takeaways

> Gotcha: replacing the swap with `nums[slow] = nums[fast]` (a plain overwrite, like in Remove Duplicates) drops the zero that was sitting at `nums[slow]` — you would then need a second pass to fill the tail with zeroes. The swap avoids that extra pass.

- When `slow == fast`, the swap is a harmless no-op — no special case needed.
- This is the same `slow`/`fast` skeleton as Remove Duplicates, but with a swap instead of an overwrite, because zeroes must still appear somewhere in the array, just at the end.
- Related problems: Remove Duplicates from Sorted Array, Remove Element, Sort Colors (three-way partition, a related but distinct pattern).
