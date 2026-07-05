---
card: java
gi: 176
slug: java-util-arrays-sort
title: java.util.Arrays.sort()
---

## 1. What it is

`java.util.Arrays.sort()` is a static utility method that sorts an array's elements **in place**, in ascending order, directly modifying the array you pass in rather than returning a new one. It's overloaded to work on every primitive array type (`int[]`, `double[]`, `char[]`, etc.) as well as arrays of objects, and it accepts optional `fromIndex`/`toIndex` arguments to sort only a sub-range.

```java
int[] nums = { 5, 2, 8, 1, 9 };
java.util.Arrays.sort(nums);
System.out.println(java.util.Arrays.toString(nums)); // [1, 2, 5, 8, 9]

int[] partial = { 5, 2, 8, 1, 9 };
java.util.Arrays.sort(partial, 1, 4); // sorts only indices 1..3 (toIndex exclusive)
System.out.println(java.util.Arrays.toString(partial)); // [5, 1, 2, 8, 9]
```

`sort()` returns `void` — it does not return a sorted copy; the original array is reordered directly, so any other variable referencing the same array will also see the new, sorted order.

## 2. Why & when

Sorting is one of the most common operations performed on arrays, and writing a correct, efficient sort algorithm by hand is unnecessary work — the standard library provides a well-tested, optimized implementation:

- **Preparing data for binary search** — `Arrays.binarySearch` (a later topic) requires a sorted array to work correctly, so `sort()` is almost always called first.
- **Presenting data in order** — displaying a leaderboard, alphabetized names, or chronological events.
- **Finding extremes quickly** — after sorting, the minimum and maximum are simply the first and last elements (`sorted[0]` and `sorted[sorted.length - 1]`).

For primitives, `Arrays.sort()` uses a **dual-pivot quicksort** variant (generally very fast, though not "stable" — equal elements might be reordered relative to each other, which doesn't matter for primitives since equal values are indistinguishable). For objects, it uses a stable **merge sort/TimSort** variant, which does preserve the relative order of equal elements — a distinction that matters when sorting objects that are "equal" by one field but differ in others.

## 3. Core concept

```java
public class SortDemo {
    public static void main(String[] args) {
        int[] nums = { 42, 7, 15, 3, 99, 1 };
        java.util.Arrays.sort(nums); // sorts ascending, in place
        System.out.println(java.util.Arrays.toString(nums)); // [1, 3, 7, 15, 42, 99]

        String[] words = { "banana", "apple", "cherry" };
        java.util.Arrays.sort(words); // natural (alphabetical) order for String
        System.out.println(java.util.Arrays.toString(words)); // [apple, banana, cherry]
    }
}
```

For object arrays like `String[]`, `sort()` uses each element's **natural ordering**, defined by its `compareTo` method (`String` compares alphabetically); sorting a custom class this way requires that class to implement `Comparable`, or requires passing a separate `Comparator` as a second argument.

## 4. Diagram

<svg viewBox="0 0 560 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unsorted array 5 2 8 1 9 transformed in place by Arrays dot sort into the sorted array 1 2 5 8 9, same array object, reordered">
  <rect x="8" y="8" width="544" height="114" rx="8" fill="#0d1117"/>
  <text x="280" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Arrays.sort(nums) — modifies nums in place</text>

  <text x="60" y="50" fill="#8b949e" font-size="10" font-family="sans-serif">before:</text>
  <rect x="110" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="130" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">5</text>
  <rect x="150" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="170" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">2</text>
  <rect x="190" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="210" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">8</text>
  <rect x="230" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="250" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">1</text>
  <rect x="270" y="35" width="40" height="28" fill="#1c2430" stroke="#f85149"/><text x="290" y="54" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">9</text>

  <text x="290" y="80" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">↓ sort() reorders the SAME array object ↓</text>

  <text x="60" y="105" fill="#8b949e" font-size="10" font-family="sans-serif">after:</text>
  <rect x="110" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="130" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">1</text>
  <rect x="150" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="170" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">2</text>
  <rect x="190" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="210" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">5</text>
  <rect x="230" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="250" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">8</text>
  <rect x="270" y="90" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="290" y="109" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">9</text>
</svg>

`sort()` reorders the array's own storage — no new array is allocated for the result.

## 5. Runnable example

Scenario: processing a batch of race finish times — starting with a basic ascending sort, then extending to find the median from the sorted data, then hardening into sorting an array of `Runner` objects by their time using a `Comparator`, since objects have no natural numeric order by default.

### Level 1 — Basic

```java
public class RaceTimesBasic {
    public static void main(String[] args) {
        double[] times = { 12.4, 9.8, 15.1, 10.2, 11.0 };

        java.util.Arrays.sort(times);
        System.out.println(java.util.Arrays.toString(times));
    }
}
```

**How to run:** `java RaceTimesBasic.java`

`Arrays.sort(times)` reorders `times` in place into ascending order (`[9.8, 10.2, 11.0, 12.4, 15.1]`) — the fastest time is now first, and the slowest is last.

### Level 2 — Intermediate

Same times, now sorted first so the median (middle value) can be read directly from a fixed position.

```java
public class RaceTimesIntermediate {
    public static void main(String[] args) {
        double[] times = { 12.4, 9.8, 15.1, 10.2, 11.0 };

        java.util.Arrays.sort(times);

        double median = times[times.length / 2]; // odd count: middle element after sorting
        System.out.println("Sorted: " + java.util.Arrays.toString(times));
        System.out.println("Median: " + median);
    }
}
```

**How to run:** `java RaceTimesIntermediate.java`

Because `times` is sorted first, `times[times.length / 2]` (index `2` for 5 elements) is guaranteed to be the middle value (`11.0`) — computing a median without sorting first would require a completely different, more complex algorithm.

### Level 3 — Advanced

Same race, now with full `Runner` objects (name + time), sorted by time using a `Comparator` since `Runner` has no single natural numeric ordering the way `double` does.

```java
import java.util.Arrays;
import java.util.Comparator;

public class RaceTimesAdvanced {
    static class Runner {
        String name;
        double time;
        Runner(String name, double time) { this.name = name; this.time = time; }
        public String toString() { return name + " (" + time + "s)"; }
    }

    public static void main(String[] args) {
        Runner[] runners = {
            new Runner("Chen", 12.4),
            new Runner("Diaz", 9.8),
            new Runner("Osei", 15.1),
            new Runner("Park", 10.2)
        };

        Arrays.sort(runners, Comparator.comparingDouble(r -> r.time)); // sort by the 'time' field

        for (int place = 0; place < runners.length; place++) {
            System.out.println((place + 1) + ". " + runners[place]);
        }
    }
}
```

**How to run:** `java RaceTimesAdvanced.java`

`Comparator.comparingDouble(r -> r.time)` tells `sort()` how to compare two `Runner` objects — by extracting and comparing their `time` field — since `Runner` doesn't implement `Comparable` and has no built-in ordering; without a `Comparator`, `Arrays.sort(runners)` on plain, non-Comparable objects would throw `ClassCastException` at runtime.

## 6. Walkthrough

Trace `Arrays.sort(runners, Comparator.comparingDouble(r -> r.time))` for `runners = [Chen(12.4), Diaz(9.8), Osei(15.1), Park(10.2)]`:

**Comparator construction.** `Comparator.comparingDouble(r -> r.time)` builds a comparator that, given two `Runner`s `a` and `b`, effectively computes `Double.compare(a.time, b.time)` — negative if `a` is faster, positive if `a` is slower, zero if equal.

**Sorting.** `Arrays.sort` uses this comparator (rather than any natural ordering) to determine relative order, applying a stable sort algorithm for objects — repeatedly comparing pairs and rearranging until every element is in non-decreasing order of `.time`.

**Result order.** By ascending `time`: `Diaz (9.8)`, `Park (10.2)`, `Chen (12.4)`, `Osei (15.1)`.

```
before: Chen(12.4)  Diaz(9.8)  Osei(15.1)  Park(10.2)
sort by time ascending ->
after:  Diaz(9.8)  Park(10.2)  Chen(12.4)  Osei(15.1)
```

**Final output.** The loop prints four lines, numbering places `1` through `4`: `"1. Diaz (9.8s)"`, `"2. Park (10.2s)"`, `"3. Chen (12.4s)"`, `"4. Osei (15.1s)"` — the race podium in actual finishing order.

## 7. Gotchas & takeaways

> **`Arrays.sort()` returns `void` and sorts in place — it does not return a new sorted array.** Writing `int[] sorted = Arrays.sort(nums);` is a compile error; the correct pattern is to call `Arrays.sort(nums);` as its own statement, after which `nums` itself is sorted.

> **Sorting an array of objects that don't implement `Comparable` and providing no `Comparator` throws `ClassCastException` at runtime**, not a compile error — the compiler can't verify comparability for plain object arrays, so this mistake only surfaces when the sort actually runs.

- `Arrays.sort(array)` sorts primitives or `Comparable` objects in ascending natural order, modifying the array in place.
- `Arrays.sort(array, comparator)` is required for objects without natural ordering, or to sort by a different rule (descending, by a specific field).
- `Arrays.sort(array, fromIndex, toIndex)` sorts only a sub-range, leaving elements outside `[fromIndex, toIndex)` untouched.
- Sort before calling `Arrays.binarySearch` — binary search assumes its input is already sorted and gives wrong results silently otherwise.
