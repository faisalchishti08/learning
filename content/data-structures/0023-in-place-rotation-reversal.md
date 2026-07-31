---
card: data-structures
gi: 23
slug: in-place-rotation-reversal
title: In-place rotation & reversal
---

## 1. What it is

**Reversal** flips an array's order end to end. **Rotation** shifts every element over by `k` positions, wrapping the elements that fall off one end back onto the other. Doing either **in-place** means transforming the array using only O(1) extra memory — no second array — by swapping elements directly within the original array.

## 2. Why & when

The naive approach to rotation copies elements into a new array and copies back — O(n) extra space. The in-place versions matter whenever memory is constrained, or when a problem explicitly requires O(1) extra space (common in interview constraints). The "reverse three times" trick turns rotation into pure reversal, which is easy to do in-place with two pointers.

## 3. Core concept

**In-place reversal with two pointers.** Point `left` at the start and `right` at the end. Swap `arr[left]` and `arr[right]`, then move `left` forward and `right` backward, repeating until they meet or cross. This touches each element once, using no extra array.

**The reverse-three-times trick for rotation.** To rotate an array right by `k`, reverse the whole array, then reverse the first `k` elements, then reverse the remaining `n-k` elements. This works because reversing the whole array puts every element in exactly the reverse order needed, but with each of the two logical halves *also* internally reversed — reversing each half back undoes only that inner flip, leaving the correct rotated order.

**Why this is O(1) extra space.** Every step is a swap-based reversal on a sub-range of the *same* array — no second array is ever allocated. Total work is still O(n) (each element is touched a constant number of times across the three reversals), but the auxiliary space drops from O(n) to O(1).

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Rotating an array right by 2 via three reversals: reverse all, reverse first k, reverse the rest">
  <g font-family="sans-serif" font-size="11">
    <text x="320" y="16" fill="#8b949e" text-anchor="middle">original: 1 2 3 4 5 | rotate right by 2</text>
    <text x="320" y="45" fill="#e6edf3" text-anchor="middle">step 1 — reverse all: 5 4 3 2 1</text>
    <text x="320" y="75" fill="#e6edf3" text-anchor="middle">step 2 — reverse first k=2: 4 5 3 2 1</text>
    <text x="320" y="105" fill="#e6edf3" text-anchor="middle">step 3 — reverse remaining n-k=3: 4 5 1 2 3</text>
    <text x="320" y="140" fill="#79c0ff" text-anchor="middle">result: 4 5 1 2 3 -- matches rotating {1,2,3,4,5} right by 2</text>
    <text x="320" y="180" fill="#8b949e" text-anchor="middle" font-size="10">every reversal is done with two in-place pointers, no second array</text>
  </g>
</svg>

Three in-place reversals, each on a sub-range of the same array, produce the same result as a full rotation.

## 5. Runnable example

```java
// InPlaceRotationReversal.java
import java.util.Arrays;

public class InPlaceRotationReversal {

    // Basic: in-place reversal of a full array using two pointers.
    static void reverse(int[] arr, int from, int to) {
        while (from < to) {
            int temp = arr[from];
            arr[from] = arr[to];
            arr[to] = temp;
            from++;
            to--;
        }
    }

    static void basicLevel() {
        int[] arr = {1, 2, 3, 4, 5};
        reverse(arr, 0, arr.length - 1);
        System.out.println("basic: fully reversed -> " + Arrays.toString(arr));
    }

    // Intermediate: reverse just a sub-range in place.
    static void intermediateLevel() {
        int[] arr = {1, 2, 3, 4, 5};
        reverse(arr, 1, 3); // reverse only indexes 1..3
        System.out.println("intermediate: partial reverse [1..3] -> " + Arrays.toString(arr));
    }

    // Advanced: in-place rotation via the reverse-three-times trick, O(1) extra space.
    static void rotateRight(int[] arr, int k) {
        int n = arr.length;
        k = k % n; // handle k larger than the array length
        reverse(arr, 0, n - 1);      // step 1: reverse the whole array
        reverse(arr, 0, k - 1);      // step 2: reverse the first k elements back
        reverse(arr, k, n - 1);      // step 3: reverse the remaining n-k elements back
    }

    static void advancedLevel() {
        int[] arr = {1, 2, 3, 4, 5};
        rotateRight(arr, 2);
        System.out.println("advanced: rotated right by 2 -> " + Arrays.toString(arr)); // expect [4,5,1,2,3]

        int[] arr2 = {1, 2, 3};
        rotateRight(arr2, 5); // k larger than length -- 5 % 3 = 2
        System.out.println("advanced: rotated right by 5 (mod 3) -> " + Arrays.toString(arr2));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `InPlaceRotationReversal.java`, then run `java InPlaceRotationReversal.java`.

## 6. Walkthrough

1. `basicLevel()` calls `reverse(arr, 0, 4)` on `{1,2,3,4,5}`. `left=0,right=4` swap to give `{5,2,3,4,1}`; `left=1,right=3` swap to give `{5,4,3,2,1}`; `left=2,right=2` meet, loop stops.
2. `intermediateLevel()` calls `reverse(arr, 1, 3)`, only swapping indexes 1 and 3 (`2` and `4`), leaving indexes 0 and 4 untouched — the result is `{1,4,3,2,5}`.
3. `advancedLevel()`'s `rotateRight(arr, 2)` on `{1,2,3,4,5}` first reverses the whole array to `{5,4,3,2,1}`, then reverses the first `k=2` elements (`{5,4}` becomes `{4,5}`), giving `{4,5,3,2,1}`, then reverses the remaining `n-k=3` elements (`{3,2,1}` becomes `{1,2,3}`), giving the final `{4,5,1,2,3}`.
4. The second call uses `k=5` on a 3-element array; `k % n = 5 % 3 = 2`, so it correctly behaves as rotating by 2, avoiding an out-of-bounds reversal range.
5. Every reversal call reuses the same `reverse` helper and swaps elements within the original array — no second array is ever allocated, so the whole rotation runs in O(1) extra space.

## 7. Gotchas & takeaways

> Gotcha: forgetting `k = k % n` before rotating causes an out-of-bounds error (or silently wrong results) whenever `k >= n` — rotating an array of length `n` by exactly `n` positions should return the array unchanged, and rotating by `n + 2` should behave the same as rotating by `2`.

- In-place reversal with two pointers touches each element once and uses O(1) extra space.
- The reverse-three-times trick converts rotation into three reversals, giving O(1) extra space instead of the O(n) a copy-based rotation needs.
- Always normalize `k` with `k % n` first, since rotating by more than the array's length should wrap around.
- Related concepts: [Prefix-sum & difference arrays](0022-prefix-sum-difference-arrays.md), [Two-pointer & sliding-window on arrays](0021-two-pointer-sliding-window-on-arrays.md).
