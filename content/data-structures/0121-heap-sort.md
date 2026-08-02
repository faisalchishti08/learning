---
card: data-structures
gi: 121
slug: heap-sort
title: Heap sort
---

## 1. What it is

**Heap sort** sorts an array in place using a binary heap: first build a max-heap from the array in `O(n)`, then repeatedly swap the root (the largest remaining value) with the last unsorted element and shrink the heap by one, restoring the heap property each time with sift-down. After `n` such steps, the array is fully sorted, ascending, with no extra array needed.

## 2. Why & when

Heap sort guarantees `O(n log n)` time in every case — best, average, and worst — unlike quicksort, which can degrade to `O(n^2)` on adversarial input. It also sorts **in place**, using `O(1)` extra space, unlike merge sort's `O(n)` auxiliary array. Choose heap sort when you need a guaranteed worst-case bound and cannot afford merge sort's extra memory — though in practice, quicksort's better cache behavior often makes it faster on average.

## 3. Core concept

**How the operation works.**

1. **Build a max-heap** from the whole array using the `O(n)` build-heap method (sift-down from the last non-leaf backward to the root) — see [Build-heap in O(n)](0120-build-heap-in-o-n.md). The array now has its single largest value at index `0`.
2. **Repeat `n - 1` times:** swap `array[0]` (the current maximum) with `array[currentEnd]` (the last element still considered part of the heap), then shrink the heap's logical size by one, and sift-down the new root to restore the heap property over the smaller remaining heap.
3. Each swap places one more value into its final sorted position, at the end of the array, working backward.

**The invariant it must preserve.** At every point, the unsorted prefix `array[0 .. currentEnd]` must remain a valid max-heap, so its root is always the correct next-largest value to place. The sorted suffix, once written, is never touched again.

**Why this gives `O(n log n)`.** Building the initial heap costs `O(n)`. Each of the `n` extraction steps costs `O(log n)` (one sift-down over a shrinking heap). Total: `O(n) + n * O(log n) = O(n log n)`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array being sorted by repeatedly swapping the max heap root with the last unsorted element, shrinking the heap by one, and sifting down, building a sorted suffix from the right">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="20" fill="#8b949e">max-heap: [9,7,8,1,3,2,4]</text>
    <rect x="20" y="35" width="580" height="26" fill="#161b22" stroke="#f0883e"/>
    <text x="45" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">9</text>
    <text x="130" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">7</text>
    <text x="215" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <text x="300" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <text x="385" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <text x="470" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <text x="555" y="53" fill="#e6edf3" text-anchor="middle" font-size="9">4</text>
    <text x="20" y="90" fill="#8b949e">step 1: swap idx0 &lt;-&gt; idx6, shrink, siftDown -&gt;</text>
    <rect x="20" y="100" width="497" height="26" fill="#161b22" stroke="#79c0ff"/>
    <rect x="517" y="100" width="83" height="26" fill="#0d1117" stroke="#6e7681"/>
    <text x="45" y="118" fill="#e6edf3" text-anchor="middle" font-size="9">4</text>
    <text x="130" y="118" fill="#e6edf3" text-anchor="middle" font-size="9">7</text>
    <text x="215" y="118" fill="#e6edf3" text-anchor="middle" font-size="9">8</text>
    <text x="300" y="118" fill="#e6edf3" text-anchor="middle" font-size="9">1</text>
    <text x="385" y="118" fill="#e6edf3" text-anchor="middle" font-size="9">3</text>
    <text x="470" y="118" fill="#e6edf3" text-anchor="middle" font-size="9">2</text>
    <text x="555" y="118" fill="#8b949e" text-anchor="middle" font-size="9">9</text>
    <text x="555" y="135" fill="#8b949e" text-anchor="middle" font-size="7">sorted</text>
    <text x="300" y="170" fill="#79c0ff" text-anchor="middle" font-size="9">heap shrinks left to right; sorted suffix grows right to left</text>
  </g>
</svg>

The root (`9`, the maximum) swaps with the last heap element (`4`); the heap shrinks to exclude that slot, and `4` sifts down into its correct spot within the smaller heap, while `9` is now permanently placed at the end.

## 5. Runnable example

```java
// HeapSort.java
import java.util.Arrays;

public class HeapSort {

    static int leftChild(int i) { return 2 * i + 1; }
    static int rightChild(int i) { return 2 * i + 2; }

    // Max-heap sift-down: swap with the LARGER child, since heap sort's build phase wants the max at the root.
    static void siftDownMax(int[] array, int size, int i) {
        while (true) {
            int left = leftChild(i), right = rightChild(i), largest = i;
            if (left < size && array[left] > array[largest]) largest = left;
            if (right < size && array[right] > array[largest]) largest = right;
            if (largest == i) break;
            int t = array[i]; array[i] = array[largest]; array[largest] = t;
            i = largest;
        }
    }

    // Basic: phase 1 -- build a max-heap in O(n).
    static void basicLevel() {
        int[] array = {9, 4, 7, 1, 3, 8, 2};
        int n = array.length;
        for (int i = n / 2 - 1; i >= 0; i--) siftDownMax(array, n, i);
        System.out.println("basic: array after build-max-heap phase -> " + Arrays.toString(array));
    }

    // Intermediate: phase 2 -- repeatedly extract the max into the array's tail, shrinking the heap each time.
    static void heapSort(int[] array) {
        int n = array.length;
        for (int i = n / 2 - 1; i >= 0; i--) siftDownMax(array, n, i); // phase 1: build max-heap

        for (int end = n - 1; end > 0; end--) { // phase 2: extract max into position `end`, repeatedly
            int t = array[0]; array[0] = array[end]; array[end] = t; // move current max to its final sorted slot
            siftDownMax(array, end, 0); // restore heap property over the SHRUNK heap (size = end, excluding the sorted tail)
        }
    }

    static void intermediateLevel() {
        int[] array = {9, 4, 7, 1, 3, 8, 2};
        heapSort(array);
        System.out.println("intermediate: fully sorted array -> " + Arrays.toString(array));
    }

    // Advanced: confirm O(n log n) behavior holds even on already-sorted and reverse-sorted input (heap sort has no bad case).
    static void advancedLevel() {
        int[] alreadySorted = {1, 2, 3, 4, 5, 6, 7};
        int[] reverseSorted = {7, 6, 5, 4, 3, 2, 1};

        heapSort(alreadySorted);
        heapSort(reverseSorted);

        System.out.println("advanced: sorting already-sorted input -> " + Arrays.toString(alreadySorted));
        System.out.println("advanced: sorting reverse-sorted input -> " + Arrays.toString(reverseSorted));
        System.out.println("advanced: both inputs cost O(n log n) -- heap sort has no adversarial worst case, unlike quicksort");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `HeapSort.java`, then run `java HeapSort.java`.

## 6. Walkthrough

1. `basicLevel()` runs only phase 1 on `{9, 4, 7, 1, 3, 8, 2}`, producing a valid max-heap array where index `0` holds the maximum (`9`).
2. `intermediateLevel()` runs the full `heapSort`. After phase 1, phase 2 begins: swap `array[0] = 9` with `array[6]` (the last element), shrink the effective heap size to `6`, and sift-down the new root over that smaller range. This places `9` permanently at index `6`. The loop repeats with `end = 5`, then `4`, and so on, each time placing the next-largest remaining value at the current `end` and shrinking the heap by one. The final array comes out fully sorted ascending: `{1, 2, 3, 4, 7, 8, 9}`.
3. `advancedLevel()` runs `heapSort` on both an already-sorted array and a reverse-sorted array. Both complete correctly and in the same asymptotic time, since heap sort's cost depends only on the number of elements, not on their initial arrangement — the key advantage over quicksort, whose worst case depends heavily on input order.

## 7. Gotchas & takeaways

> Gotcha: after each swap in phase 2, you must sift-down over the *shrunk* heap size (`end`, not the original array length) — sifting over the full array would let the already-sorted, placed values back into the comparisons and corrupt the sort.

- Heap sort has two phases: build a max-heap in `O(n)`, then extract the max `n` times, each extraction costing `O(log n)` — total `O(n log n)`.
- It sorts in place with `O(1)` extra space, unlike merge sort's `O(n)` auxiliary array.
- Unlike quicksort, heap sort has no adversarial worst case — its `O(n log n)` bound holds for every input, not just on average.
- Heap sort is not stable — equal elements can end up reordered relative to each other, since swaps do not preserve original relative order.
- Related concepts: [Build-heap in O(n)](0120-build-heap-in-o-n.md), [Extract-min/max & sift-down](0119-extract-min-max-sift-down.md).
