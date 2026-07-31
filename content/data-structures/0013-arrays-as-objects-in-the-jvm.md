---
card: data-structures
gi: 13
slug: arrays-as-objects-in-the-jvm
title: Arrays as objects in the JVM
---

## 1. What it is

In Java, an array is not a primitive value — it is a full **object** that lives on the heap, even when it holds primitives like `int`. Writing `int[] arr = new int[5];` allocates a heap object with an object header, a stored `length` field, and five contiguous `int` slots. The variable `arr` itself is just a **reference** to that object, the same way an object reference works for any other class.

## 2. Why & when

Understanding this matters whenever you reason about memory layout, aliasing, or method parameters. Because arrays are objects, passing an array to a method passes a *copy of the reference*, not a copy of the data — the method can mutate the caller's array in place. This is different from how many beginners assume arrays behave (like a value type), and it explains bugs where a "local" change inside a method unexpectedly shows up outside it.

## 3. Core concept

**Every array has a hidden object header.** The Java Virtual Machine (JVM) stores type information and a synchronization/GC-tracking word before the actual data, the same header every object gets. For arrays there is one more field: `length`. That is why `arr.length` reads instantly — it is a stored field, not something recomputed by scanning the array.

**Arrays are contiguous, but the array *object* is one heap block.** The five `int` slots in `new int[5]` sit next to each other in memory, right after the header and length field. This contiguity is what makes indexed access (`arr[i]`) O(1): the JVM computes the exact byte offset from the base address, with no traversal needed.

**Reference semantics follow from "arrays are objects".** `int[] b = a;` copies the reference, so `a` and `b` point at the same heap object — mutating through `b` is visible through `a`. This is identical to how `Object b = a;` works for any class, because an array genuinely *is* an object, with a synthetic class like `int[].class` that extends `Object`.

**Arrays of objects store references, not the objects themselves.** `String[] names = new String[3];` allocates one array object holding three reference slots, each initialized to `null`. The actual `String` objects (if any) live elsewhere on the heap; the array only stores pointers to them.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An int array as one heap object with header, length field, and contiguous int slots; a reference variable pointing at it">
  <g font-family="sans-serif" font-size="12">
    <text x="120" y="20" fill="#8b949e" text-anchor="middle">stack</text>
    <rect x="40" y="30" width="160" height="35" fill="#161b22" stroke="#79c0ff"/>
    <text x="120" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">arr (reference)</text>
    <text x="480" y="20" fill="#8b949e" text-anchor="middle">heap: the array object</text>
    <rect x="260" y="30" width="440" height="80" fill="none" stroke="#f0883e"/>
    <rect x="270" y="40" width="110" height="25" fill="#161b22" stroke="#3fb950"/>
    <text x="325" y="57" fill="#e6edf3" text-anchor="middle" font-size="10">object header</text>
    <rect x="390" y="40" width="90" height="25" fill="#161b22" stroke="#3fb950"/>
    <text x="435" y="57" fill="#e6edf3" text-anchor="middle" font-size="10">length = 5</text>
    <rect x="270" y="75" width="42" height="25" fill="#0d1117" stroke="#79c0ff"/><text x="291" y="92" fill="#e6edf3" text-anchor="middle" font-size="10">0</text>
    <rect x="312" y="75" width="42" height="25" fill="#0d1117" stroke="#79c0ff"/><text x="333" y="92" fill="#e6edf3" text-anchor="middle" font-size="10">1</text>
    <rect x="354" y="75" width="42" height="25" fill="#0d1117" stroke="#79c0ff"/><text x="375" y="92" fill="#e6edf3" text-anchor="middle" font-size="10">2</text>
    <rect x="396" y="75" width="42" height="25" fill="#0d1117" stroke="#79c0ff"/><text x="417" y="92" fill="#e6edf3" text-anchor="middle" font-size="10">3</text>
    <rect x="438" y="75" width="42" height="25" fill="#0d1117" stroke="#79c0ff"/><text x="459" y="92" fill="#e6edf3" text-anchor="middle" font-size="10">4</text>
    <text x="500" y="92" fill="#8b949e" font-size="10">contiguous int slots</text>
    <line x1="120" y1="65" x2="290" y2="80" stroke="#79c0ff" marker-end="url(#arrow)"/>
    <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#79c0ff"/></marker></defs>
    <text x="350" y="150" fill="#79c0ff" text-anchor="middle">arr holds only a reference; the header, length, and data live together on the heap</text>
  </g>
</svg>

The reference variable `arr` points at one heap object. That object bundles the header, the `length` field, and the contiguous data slots together.

## 5. Runnable example

The artifact below shows array reference semantics, aliasing through a method call, and the difference between a primitive array and an object-reference array.

```java
// ArraysAsObjects.java
import java.util.Arrays;

public class ArraysAsObjects {

    // Basic: arrays are objects, so length is a field, and == compares references.
    static void basicLevel() {
        int[] a = new int[5];
        int[] b = a; // copies the reference, not the data
        b[0] = 99;
        System.out.println("basic: a[0] = " + a[0]); // 99, same underlying object
        System.out.println("basic: a == b -> " + (a == b)); // true: same heap object
        System.out.println("basic: a.length -> " + a.length); // stored field, O(1)
    }

    // Intermediate: passing an array to a method passes the reference, so mutation is visible.
    static void mutateFirstElement(int[] arr) {
        arr[0] = -1; // mutates the caller's array in place
    }

    static void intermediateLevel() {
        int[] nums = {10, 20, 30};
        mutateFirstElement(nums);
        System.out.println("intermediate: nums after call -> " + Arrays.toString(nums));
    }

    // Advanced: an array of objects stores references, not the objects themselves.
    static void advancedLevel() {
        String[] names = new String[3]; // all slots start as null references
        System.out.println("advanced: fresh String[] -> " + Arrays.toString(names));

        names[0] = "Ada";
        String[] alias = names;
        alias[1] = "Grace"; // mutates through the alias, visible via names too
        System.out.println("advanced: names after alias write -> " + Arrays.toString(names));

        // A shallow copy makes a new array object, but the *element references* are shared.
        String[] copy = names.clone();
        copy[2] = "Linus"; // only affects copy's own slot 2, since clone() is a new array object
        System.out.println("advanced: names unaffected by copy[2] -> " + Arrays.toString(names));
        System.out.println("advanced: copy has its own slot 2 -> " + Arrays.toString(copy));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ArraysAsObjects.java`, then run `java ArraysAsObjects.java`.

## 6. Walkthrough

1. `basicLevel()` creates one array object and assigns two references, `a` and `b`, to it. Writing through `b` shows up when reading through `a`, because both variables point at the same heap object.
2. `a == b` prints `true` because `==` on array references compares identity (same object), not contents — this is the same rule as for any Java object reference.
3. `intermediateLevel()` passes `nums` into `mutateFirstElement`. The parameter `arr` receives a copy of the *reference*, not a copy of the array. The method's write to `arr[0]` mutates the one array object both `nums` and `arr` point at.
4. `advancedLevel()` allocates `String[] names`, whose three slots start as `null` references — no `String` objects exist yet, only empty pointer slots.
5. `alias = names` creates a second reference to the same array object; writing `alias[1]` is visible through `names`, exactly like the `int[]` case.
6. `names.clone()` allocates a brand-new array object, so writes to `copy` do not affect `names` — but note `clone()` is a shallow copy: if the array held mutable objects, the *same* objects would be shared between `names` and `copy`, only the array container itself is new.

## 7. Gotchas & takeaways

> Gotcha: `==` on arrays checks whether two references point at the same array object, never whether the contents are equal. `new int[]{1,2} == new int[]{1,2}` is always `false`. Use `Arrays.equals(a, b)` (or `Arrays.deepEquals` for nested arrays) to compare contents.

- An array is a heap object with a header, a `length` field, and contiguous data slots — never a primitive value, even for `int[]`.
- Passing an array to a method passes the reference; the method can mutate the caller's data through it.
- `clone()` makes a new array object (shallow copy) — element references inside are still shared for arrays of objects.
- Related concepts: [Primitives vs references](0010-primitives-vs-references.md) (why array-of-primitive and array-of-object slots differ), [Stack vs heap allocation](0011-stack-vs-heap-allocation.md) (where the array object itself lives).
