---
card: data-structures
gi: 31
slug: converting-between-arrays-and-collections
title: Converting between arrays and collections
---

## 1. What it is

Java arrays and the Collections Framework (`List`, `Set`, etc.) are two different worlds — arrays are fixed-size and can hold primitives directly, while collections are resizable and generic-only (they need wrapper types like `Integer`, not `int`). Converting between them means bridging those two worlds: `Arrays.asList(array)` and `List.of(...)` go array-to-list, while `list.toArray(...)` goes list-to-array.

## 2. Why & when

You convert an array to a list when you need list operations (like `contains`, `add`, or passing to an API expecting a `Collection`) on data you received as an array. You convert a list back to an array when an API requires a plain array, or when you want the performance and memory profile of a fixed-size primitive array for a finished, no-longer-changing dataset.

## 3. Core concept

**`Arrays.asList(array)` returns a fixed-size view, not a real resizable list.** It wraps the *original* array directly — no copying happens. This means `set(i, v)` on the returned list writes through to the original array, but `add()`/`remove()` throw `UnsupportedOperationException`, since the list's size cannot change without changing the fixed-size array underneath.

**`Arrays.asList` on a primitive array is a common trap.** `Arrays.asList(intArray)` for `int[] intArray` does not produce `List<Integer>` — because generics require a reference type, it produces a `List<int[]>` containing exactly *one* element: the whole array. You must use a boxed array (`Integer[]`) for this to work as expected.

**`list.toArray(new T[0])` is the standard list-to-array pattern.** Passing a zero-length array as a size hint lets the JVM allocate a correctly-sized array of the right runtime type automatically; the no-argument `toArray()` instead returns `Object[]`, which cannot be cast to `T[]`.

**Converting does not fix the primitive/object gap.** Going from `int[]` to `List<Integer>` (or back) still requires boxing/unboxing every element, one at a time — the conversion methods do not avoid that cost, they just make it convenient.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Arrays.asList wraps the original array as a fixed-size view; toArray copies list elements into a new array">
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="18" fill="#8b949e" text-anchor="middle">Arrays.asList(array) -- wraps, no copy</text>
    <rect x="60" y="30" width="200" height="26" fill="#161b22" stroke="#3fb950"/><text x="160" y="47" fill="#e6edf3" text-anchor="middle" font-size="10">String[] array</text>
    <line x1="160" y1="56" x2="160" y2="80" stroke="#79c0ff" marker-end="url(#a5)"/>
    <defs><marker id="a5" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
    <rect x="60" y="85" width="200" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="160" y="102" fill="#e6edf3" text-anchor="middle" font-size="10">List view (fixed size)</text>

    <text x="480" y="18" fill="#8b949e" text-anchor="middle">list.toArray(new T[0]) -- copies</text>
    <rect x="380" y="30" width="200" height="26" fill="#161b22" stroke="#3fb950"/><text x="480" y="47" fill="#e6edf3" text-anchor="middle" font-size="10">List&lt;String&gt;</text>
    <line x1="480" y1="56" x2="480" y2="80" stroke="#f0883e" marker-end="url(#a6)"/>
    <defs><marker id="a6" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker></defs>
    <rect x="380" y="85" width="200" height="26" fill="#0d1117" stroke="#f0883e"/><text x="480" y="102" fill="#e6edf3" text-anchor="middle" font-size="10">new String[] (separate copy)</text>

    <text x="320" y="150" fill="#79c0ff" text-anchor="middle">asList wraps the same memory; toArray allocates and copies fresh memory</text>
  </g>
</svg>

`Arrays.asList` is a thin, size-fixed wrapper over the original array. `toArray` is a real copy into new, independent memory.

## 5. Runnable example

```java
// ArrayCollectionConversion.java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class ArrayCollectionConversion {

    // Basic: Arrays.asList wraps the array -- writes through, but structural changes are not allowed.
    static void basicLevel() {
        String[] array = {"a", "b", "c"};
        List<String> view = Arrays.asList(array);
        view.set(1, "B"); // writes through to the original array
        System.out.println("basic: original array after set -> " + Arrays.toString(array));

        try {
            view.add("d"); // fixed size -- structural change not allowed
        } catch (UnsupportedOperationException e) {
            System.out.println("basic: caught -> cannot add() to Arrays.asList view");
        }
    }

    // Intermediate: the primitive-array trap -- Arrays.asList(int[]) wraps ONE element, the whole array.
    static void intermediateLevel() {
        int[] primitives = {1, 2, 3};
        List<int[]> wrongList = Arrays.asList(primitives); // NOT List<Integer>!
        System.out.println("intermediate: wrongList.size() -> " + wrongList.size()); // 1, not 3

        Integer[] boxed = {1, 2, 3}; // must box first
        List<Integer> correctList = Arrays.asList(boxed);
        System.out.println("intermediate: correctList -> " + correctList + " size=" + correctList.size());
    }

    // Advanced: a real resizable copy via new ArrayList<>(), and converting back with toArray(new T[0]).
    static void advancedLevel() {
        Integer[] boxed = {1, 2, 3};
        List<Integer> resizable = new ArrayList<>(Arrays.asList(boxed)); // real, independent, growable copy
        resizable.add(4); // works: this is a real ArrayList, not the fixed-size view
        System.out.println("advanced: resizable list after add -> " + resizable);

        Integer[] backToArray = resizable.toArray(new Integer[0]); // correctly-typed array, sized automatically
        System.out.println("advanced: converted back to array -> " + Arrays.toString(backToArray));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ArrayCollectionConversion.java`, then run `java ArrayCollectionConversion.java`.

## 6. Walkthrough

1. `basicLevel()` wraps `array` with `Arrays.asList`. Calling `view.set(1, "B")` writes directly into `array`'s second slot, since `view` is backed by the same memory — the original array prints `[a, B, c]`.
2. Calling `view.add("d")` throws `UnsupportedOperationException`, because the view's size is tied to the fixed-size array underneath — there is no slot to grow into.
3. `intermediateLevel()` calls `Arrays.asList(primitives)` on an `int[]`. Since Java generics cannot use `int` directly, this resolves to `List<int[]>` holding one element (the whole array) — `wrongList.size()` prints `1`, not `3`, a classic and easy-to-miss mistake.
4. Using a boxed `Integer[]` instead produces the expected `List<Integer>` with 3 elements, since `Integer` is a valid generic type argument.
5. `advancedLevel()` wraps the fixed-size view in `new ArrayList<>(...)`, which copies the elements into a genuinely resizable list — `add(4)` now succeeds. `toArray(new Integer[0])` then converts back, using the zero-length array only as a type hint so the JVM allocates a correctly-typed and correctly-sized `Integer[]` result.

## 7. Gotchas & takeaways

> Gotcha: `Arrays.asList(intArray)` for a primitive `int[]` silently compiles and returns a one-element `List<int[]>`, not the `List<Integer>` you likely intended — there is no compiler warning. Always box to `Integer[]` first, or use `Arrays.stream(intArray).boxed().collect(...)`, when you need each primitive as its own list element.

- `Arrays.asList` wraps the original array (no copy, fixed size); `new ArrayList<>(Arrays.asList(...))` makes a real, independent, resizable copy.
- `Arrays.asList` on a primitive array wraps the whole array as one element — box to a wrapper array first.
- `list.toArray(new T[0])` is the standard, correctly-typed way to convert a list back into an array.
- Related concepts: [java.util.ArrayList internals](0027-java-util-arraylist-internals-backing-array-capacity.md), [Autoboxing / unboxing & its cost](0012-autoboxing-unboxing-its-cost.md).
