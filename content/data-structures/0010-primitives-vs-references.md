---
card: data-structures
gi: 10
slug: primitives-vs-references
title: Primitives vs references
---

## 1. What it is

A **primitive** (`int`, `long`, `double`, `boolean`, `char`, etc.) stores its actual value directly, in a fixed, small amount of memory. A **reference** (any object type — `String`, arrays, custom classes, and boxed types like `Integer`) stores the *memory address* of an object that lives elsewhere (typically the heap), not the object's data itself. Assigning, copying, or passing a primitive copies its value; assigning, copying, or passing a reference copies the address, so both variables end up pointing at the *same* underlying object.

## 2. Why & when

Understanding this distinction is essential for predicting whether modifying something through one variable affects another variable that seems unrelated — a extremely common source of confusion (and bugs) for anyone moving between "value" and "reference" semantics. It also directly explains memory layout differences relevant to performance: primitives are compact and fast to copy; references require following a pointer to reach the actual data, and the referenced object itself lives separately in memory.

## 3. Core concept

**The core rule:** copying a primitive variable (via assignment, or passing it as a method argument) creates a completely independent copy of the value — changes to one copy never affect the other. Copying a reference variable creates a second variable pointing at the *same* object — changes made *through* either variable (like mutating a field, or modifying an array element) are visible through both, because there is only ever one underlying object.

**Why "passing an object to a method" can look like pass-by-reference but technically is not, in Java:** Java is always pass-by-value — but for a reference type, the *value* being passed is the reference (the address) itself, not the object. This means a method can mutate the object's internal state (through the passed reference) and the caller will see that change, but if the method reassigns the parameter variable to point at a *different* object entirely, that reassignment is invisible to the caller, since only a copy of the original reference was passed, not the caller's own variable.

**Why this matters for equality checks:** `==` on primitives compares actual values directly. `==` on references compares whether two variables point at the *exact same object* in memory, not whether the objects they point to have "equal" contents — this is why comparing two `String` objects with `==` can surprisingly return `false` even when their text content is identical, and why `.equals()` (which compares content) is the correct choice for reference-type value comparison.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A primitive variable holding its value directly versus two reference variables both pointing at the same object on the heap">
  <g font-family="sans-serif" font-size="12">
    <text x="120" y="20" fill="#8b949e" text-anchor="middle">primitive: int a = 5; int b = a;</text>
    <rect x="40" y="30" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="80" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">a: 5</text>
    <rect x="140" y="30" width="80" height="35" fill="#161b22" stroke="#3fb950"/><text x="180" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">b: 5</text>
    <text x="130" y="90" fill="#79c0ff" text-anchor="middle" font-size="10">independent copies</text>
    <text x="500" y="20" fill="#8b949e" text-anchor="middle">reference: int[] x = {1}; int[] y = x;</text>
    <rect x="430" y="30" width="70" height="35" fill="#161b22" stroke="#f0883e"/><text x="465" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">x: addr</text>
    <rect x="530" y="30" width="70" height="35" fill="#161b22" stroke="#f0883e"/><text x="565" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">y: addr</text>
    <rect x="470" y="90" width="90" height="35" fill="#161b22" stroke="#79c0ff"/><text x="515" y="112" fill="#e6edf3" text-anchor="middle" font-size="11">[1] (heap)</text>
    <line x1="465" y1="65" x2="500" y2="90" stroke="#8b949e"/>
    <line x1="565" y1="65" x2="530" y2="90" stroke="#8b949e"/>
  </g>
</svg>

Primitive copies are fully independent; reference copies share the exact same underlying object — mutating it through either variable is visible through both.

## 5. Runnable example

The artifact below demonstrates both behaviors directly: a primitive copy stays independent, while a reference copy shares mutations, and a method call illustrates that reassigning a reference parameter does not affect the caller's variable.

```java
// PrimitivesVsReferences.java
import java.util.*;

public class PrimitivesVsReferences {

    static void tryToModifyPrimitive(int value) {
        value = 999; // only changes the local copy
    }

    static void mutateArrayContents(int[] arr) {
        arr[0] = 999; // mutates the shared object through the reference
    }

    static void reassignArrayReference(int[] arr) {
        arr = new int[]{999}; // reassigns the LOCAL variable only, caller's reference is untouched
    }

    public static void main(String[] args) {
        int a = 5;
        int b = a;
        b = 10;
        System.out.println("primitive: a=" + a + ", b=" + b + " (independent)");

        int[] x = {1, 2, 3};
        int[] y = x;
        y[0] = 100;
        System.out.println("reference: x=" + Arrays.toString(x) + ", y=" + Arrays.toString(y) + " (shared object)");

        int primitiveArg = 5;
        tryToModifyPrimitive(primitiveArg);
        System.out.println("after tryToModifyPrimitive: " + primitiveArg + " (unchanged)");

        int[] arrayArg = {1};
        mutateArrayContents(arrayArg);
        System.out.println("after mutateArrayContents: " + Arrays.toString(arrayArg) + " (changed via reference)");

        reassignArrayReference(arrayArg);
        System.out.println("after reassignArrayReference: " + Arrays.toString(arrayArg) + " (unchanged - only local reassignment)");
    }
}
```

**How to run:** save as `PrimitivesVsReferences.java`, then run `java PrimitivesVsReferences.java`.

## 6. Walkthrough

1. `int b = a; b = 10;` — `b` starts as an independent copy of `a`'s value (`5`). Changing `b` to `10` has no effect on `a`, which stays `5`.
2. `int[] y = x; y[0] = 100;` — `y` is assigned the same reference as `x` (both point at the *same* array object on the heap). Modifying `y[0]` mutates that shared object directly, so reading `x[0]` afterward also shows `100`.
3. `tryToModifyPrimitive(primitiveArg)` passes a *copy* of `primitiveArg`'s value into the method. Reassigning the local parameter `value` inside the method has no effect on the caller's `primitiveArg`, which remains `5`.
4. `mutateArrayContents(arrayArg)` passes a *copy of the reference* — but that copy still points at the same underlying array object. Mutating `arr[0]` inside the method changes the shared object, so `arrayArg[0]` is `999` after the call returns.
5. `reassignArrayReference(arrayArg)` passes another copy of the reference, but this time the method reassigns its *local* variable `arr` to point at a brand-new array entirely. This reassignment only affects the local copy of the reference inside the method — the caller's `arrayArg` variable still points at the original array, unaffected.

## 7. Gotchas & takeaways

> Gotcha: assuming that passing an object into a method and reassigning it there will change what the caller's variable points to is a common misconception — Java always passes a *copy* of the reference, so reassigning the parameter inside the method never affects the caller's original variable, even though *mutating* the object through that reference does.

- Primitives copy by value (fully independent copies); references copy the address (both variables share the same underlying object).
- `==` compares primitive values directly, but compares reference *identity* (same object in memory), not content — use `.equals()` for content comparison on reference types.
- Related concepts: [Stack vs heap allocation](0011-stack-vs-heap-allocation.md) (where primitives and referenced objects typically live in memory), [Autoboxing / unboxing & its cost](0012-autoboxing-unboxing-its-cost.md) (what happens when a primitive is wrapped into a reference type like `Integer`).
