---
card: java
gi: 390
slug: enhanced-for-each-loop
title: Enhanced for-each loop
---

## 1. What it is

The **enhanced for loop** (commonly called for-each), introduced in Java 5, iterates over every element of an array or anything implementing `Iterable` (which includes every standard collection: `List`, `Set`, etc.) without needing an explicit index or iterator. Its syntax, `for (ElementType element : collection) { ... }`, reads almost like English: "for each element in this collection." Under the hood, for a `Collection`, the compiler translates it into ordinary `Iterator` calls (`hasNext()`, `next()`); for an array, into an ordinary indexed loop.

## 2. Why & when

Before Java 5, iterating a `List` meant either an indexed loop (`for (int i = 0; i < list.size(); i++) { list.get(i); }`) or manually working with an `Iterator` (`Iterator it = list.iterator(); while (it.hasNext()) { ... }`) — both correct, but both carry boilerplate and small opportunities for mistakes: an off-by-one error in the index bound, or forgetting to call `hasNext()` correctly. For-each removes both entirely: there's no index to get wrong, and no iterator boilerplate to manage, for the extremely common case of simply visiting every element in order.

Reach for for-each whenever you need to process every element of a collection or array and don't need the index itself, and don't need to modify the collection's structure (add or remove elements) while iterating. When you genuinely need the index (to also print "item #3"), or need to remove elements during iteration, an indexed loop or an explicit `Iterator` (whose own `remove()` method is safe) is still the right tool.

## 3. Core concept

```java
import java.util.List;

public class ForEachDemo {
    public static void main(String[] args) {
        List<String> fruits = List.of("Apple", "Banana", "Cherry");

        for (String fruit : fruits) { // "for each fruit in fruits"
            System.out.println(fruit);
        }

        int[] numbers = { 10, 20, 30 };
        int total = 0;
        for (int n : numbers) { // works identically for arrays
            total += n;
        }
        System.out.println("Total: " + total);
    }
}
```

**How to run:** `java ForEachDemo.java`

`for (String fruit : fruits)` visits each element of `fruits` in order, binding it to `fruit` — no index variable, no `.get(i)` calls. The second loop shows the identical syntax working over a plain array (`int[]`), not just a `List` — for-each supports both arrays and anything implementing `Iterable` with the same clean syntax.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="for-each visits each element of a collection in order, binding it to the loop variable, without an explicit index or iterator visible in the source">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">for (String fruit : fruits) { println(fruit); }</text>

  <rect x="30" y="50" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="75" fill="#6db33f" font-size="10" text-anchor="middle">"Apple"</text>
  <rect x="170" y="50" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="230" y="75" fill="#6db33f" font-size="10" text-anchor="middle">"Banana"</text>
  <rect x="310" y="50" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="370" y="75" fill="#6db33f" font-size="10" text-anchor="middle">"Cherry"</text>

  <text x="20" y="120" fill="#8b949e" font-size="10">Each box is visited once, in order -- no index variable ever appears in the source at all.</text>
</svg>

## 5. Runnable example

Scenario: printing a numbered shopping list, evolved from an old-style indexed loop, through the cleaner for-each version, to a version showing for-each's real limitation — it cannot safely remove elements, requiring a fallback to an explicit `Iterator` for that specific need.

### Level 1 — Basic

```java
import java.util.ArrayList;
import java.util.List;

public class ShoppingListIndexed {
    public static void main(String[] args) {
        List<String> items = new ArrayList<>(List.of("Milk", "Eggs", "Bread"));

        for (int i = 0; i < items.size(); i++) { // classic indexed loop -- more to get wrong
            System.out.println((i + 1) + ". " + items.get(i));
        }
    }
}
```

**How to run:** `java ShoppingListIndexed.java`

This works, but requires managing an index variable (`i`), a bound check (`i < items.size()`), and an explicit `.get(i)` call on every iteration — three separate places a mistake (like `<=` instead of `<`) could introduce an off-by-one bug.

### Level 2 — Intermediate

```java
import java.util.ArrayList;
import java.util.List;

public class ShoppingListForEach {
    public static void main(String[] args) {
        List<String> items = new ArrayList<>(List.of("Milk", "Eggs", "Bread"));

        int number = 1;
        for (String item : items) { // no index management needed for the iteration itself
            System.out.println(number + ". " + item);
            number++; // still need a separate counter if the number itself is required
        }
    }
}
```

**How to run:** `java ShoppingListForEach.java`

For-each removes the index-based iteration risk entirely (no `i < items.size()` to get wrong), though a separate `number` counter is still needed here since the numbering itself is part of the desired output — for-each doesn't expose an index, only the elements.

### Level 3 — Advanced

```java
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class ShoppingListRemovalNeedsIterator {
    public static void main(String[] args) {
        List<String> items = new ArrayList<>(List.of("Milk", "Eggs", "Bread", "Expired Yogurt"));

        // for (String item : items) {
        //     if (item.startsWith("Expired")) {
        //         items.remove(item); // ConcurrentModificationException at runtime -- for-each can't do this safely
        //     }
        // }

        Iterator<String> it = items.iterator(); // explicit iterator needed for safe removal
        while (it.hasNext()) {
            String item = it.next();
            if (item.startsWith("Expired")) {
                it.remove(); // safe -- the iterator itself tracks the removal correctly
            }
        }

        int number = 1;
        for (String item : items) { // safe to use for-each again now that removal is done
            System.out.println(number++ + ". " + item);
        }
    }
}
```

**How to run:** `java ShoppingListRemovalNeedsIterator.java`

The commented-out for-each loop shows the trap: removing from a `List` while iterating it with for-each throws `ConcurrentModificationException` at runtime, because for-each's underlying iterator detects the list was structurally modified out from under it. The fix uses an explicit `Iterator` and calls `it.remove()` — the one safe way to remove elements during iteration — after which a plain for-each loop is used again for the final, simple task of printing the cleaned-up list.

## 6. Walkthrough

Execution starts in `main`. `items` is built containing four strings, including `"Expired Yogurt"`. `Iterator<String> it = items.iterator()` obtains an iterator directly tied to `items`'s current internal state.

The `while (it.hasNext())` loop runs: `it.next()` returns `"Milk"` first. `"Milk".startsWith("Expired")` is `false`, so nothing happens. `it.hasNext()` is checked again, `it.next()` returns `"Eggs"`, same non-match. Then `"Bread"`, also no match.

On the fourth iteration, `it.next()` returns `"Expired Yogurt"`. `"Expired Yogurt".startsWith("Expired")` is `true`, so `it.remove()` runs — this removes the element the iterator most recently returned (`"Expired Yogurt"`) directly from `items`, and crucially, updates the iterator's own internal bookkeeping to stay consistent with the now-shorter list. `it.hasNext()` is checked once more, now `false` (all four original elements have been visited), so the `while` loop ends.

At this point, `items` contains exactly `["Milk", "Eggs", "Bread"]` — the expired item was removed safely, with no exception, because the removal went through the iterator's own `remove()` method rather than calling `items.remove(...)` directly during a for-each (which is exactly what the commented-out block above would have done, and exactly why it would have thrown `ConcurrentModificationException`).

The final `for (String item : items)` loop then runs safely over the now-stable list — no further modifications happen during this loop, so plain for-each is perfectly safe here. It prints each item prefixed with an incrementing number.

Expected output:
```
1. Milk
2. Eggs
3. Bread
```

## 7. Gotchas & takeaways

> Never call a collection's own `remove()`, `add()`, or similar structural-modification methods directly inside a for-each loop over that same collection — doing so throws `ConcurrentModificationException` at runtime, because the for-each loop's underlying iterator detects the collection changed size or structure out from under it. Use an explicit `Iterator` and its own `remove()` method instead.

- For-each (`for (Type element : collection)`) works over arrays and anything implementing `Iterable`, iterating every element in order without an explicit index or iterator visible in the source.
- It is the right default choice whenever you need to visit every element and don't need the index itself or need to structurally modify the collection during iteration.
- Reach for a classic indexed loop when you genuinely need the index value (for numbering, or comparing adjacent elements by position).
- Reach for an explicit `Iterator` (using its own `remove()` method) when you need to remove elements from a `List` or `Set` while iterating it — for-each alone cannot do this safely.
- Under the hood, for-each over a `Collection` compiles to ordinary `Iterator` calls (`hasNext()`/`next()`) — it is syntactic sugar over the same mechanism, not a fundamentally different iteration strategy.
