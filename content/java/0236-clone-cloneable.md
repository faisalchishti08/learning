---
card: java
gi: 236
slug: clone-cloneable
title: clone() & Cloneable
---

## 1. What it is

`clone()` is a `protected` method inherited from `Object` intended to create and return a new object that is a copy of the one it's called on. By default, calling `clone()` on a class that does not implement the marker interface `Cloneable` throws `CloneNotSupportedException` — `Object.clone()` refuses to copy a class unless that class explicitly opts in by implementing `Cloneable`, which itself declares no methods at all; it exists purely as a flag.

```java
class Point implements Cloneable {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }

    @Override
    public Point clone() {
        try {
            return (Point) super.clone(); // calls Object's native field-by-field copy
        } catch (CloneNotSupportedException e) {
            throw new AssertionError(e); // can't happen: we implement Cloneable
        }
    }
}

public class CloneDemo {
    public static void main(String[] args) {
        Point original = new Point(3, 4);
        Point copy = original.clone();
        System.out.println(copy.x + ", " + copy.y); // 3, 4
        System.out.println(original == copy);         // false — genuinely a different object
    }
}
```

`Point implements Cloneable` and overrides `clone()` (widening its visibility to `public` and its return type to `Point`, both allowed refinements), calling `super.clone()` to get `Object`'s field-by-field copy — the result is a distinct object with matching field values.

## 2. Why & when

`clone()` exists to let an object produce a duplicate of itself without the caller needing to know its internal fields, but it comes with enough sharp edges that most modern code avoids it in favor of alternatives.

- **Copying without exposing internals** — a well-implemented `clone()` lets calling code duplicate an object through a uniform interface, without needing a full copy constructor or knowing every field to copy manually.
- **Historical prevalence in the JDK** — arrays and several early collection classes implement `Cloneable`, so understanding `clone()` matters for reading and working with existing, older Java code that relies on it.
- **The shallow-copy pitfall (next topic)** — `super.clone()` performs only a *shallow* copy: reference fields are copied as references, not duplicated recursively, meaning the original and the clone can end up sharing the same mutable nested object unless the class's `clone()` override explicitly fixes this.

Because `Cloneable`'s design is widely considered awkward (a marker interface with no methods, a `protected` method that must be overridden and widened, and checked exceptions that "can't happen" but must still be handled), most modern Java code prefers copy constructors (`new Point(other.x, other.y)`) or static factory methods (`Point.copyOf(other)`) instead — but `clone()` still appears often enough in existing code and interviews that understanding it is essential.

## 3. Core concept

```java
class Box implements Cloneable {
    int[] items; // a reference field — this is where shallow copy risk appears
    Box(int[] items) { this.items = items; }

    @Override
    public Box clone() {
        try {
            return (Box) super.clone(); // copies the ARRAY REFERENCE, not the array's contents
        } catch (CloneNotSupportedException e) {
            throw new AssertionError(e);
        }
    }
}
```

`super.clone()` copies `Box`'s `items` field as a reference — the clone's `items` and the original's `items` point to the *same* underlying array in memory, so mutating the array through one reference is visible through the other, which is exactly the shallow-copy behaviour the next topic examines and fixes.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="clone requires Cloneable, calls super.clone for a field by field copy, primitive fields are duplicated but reference fields still point to the same shared object">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="30" y="20" width="220" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">implements Cloneable (flag)</text>

  <line x1="140" y1="50" x2="140" y2="70" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="30" y="75" width="220" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="95" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">super.clone() field-by-field copy</text>

  <rect x="330" y="30" width="110" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="385" y="52" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">original.items</text>

  <rect x="330" y="100" width="110" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="385" y="122" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">clone.items</text>

  <line x1="440" y1="47" x2="500" y2="80" stroke="#f85149" stroke-width="1.5"/>
  <line x1="440" y1="117" x2="500" y2="80" stroke="#f85149" stroke-width="1.5"/>
  <rect x="490" y="65" width="90" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="535" y="85" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">same array!</text>

  <text x="300" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Both objects' array fields point to the identical shared array — a shallow copy.</text>
</svg>

`clone()` duplicates the object itself, but reference fields (like arrays) still point to the same shared data underneath.

## 5. Runnable example

Scenario: an inventory `Cart` class cloned to make a "quote" before checkout, evolved from a basic clone into a working duplicate, then examined for exactly where the shallow-copy risk bites.

### Level 1 — Basic

```java
public class CloneBasic {
    static class Cart implements Cloneable {
        String customerName;
        Cart(String customerName) { this.customerName = customerName; }

        @Override
        public Cart clone() {
            try {
                return (Cart) super.clone();
            } catch (CloneNotSupportedException e) {
                throw new AssertionError(e);
            }
        }
    }

    public static void main(String[] args) {
        Cart original = new Cart("Alex");
        Cart copy = original.clone();
        System.out.println(copy.customerName); // Alex
        System.out.println(original == copy);   // false — distinct objects
    }
}
```

**How to run:** `java CloneBasic.java`

`Cart` has only a `String` field, and since `String` is immutable, this simple case has no shallow-copy risk at all — `clone()` produces a fully independent copy in every meaningful sense.

### Level 2 — Intermediate

Same `Cart`, now with an `int[] itemIds` array field — demonstrating that `super.clone()` copies the array *reference*, not its contents, so mutating one cart's items unexpectedly affects the other.

```java
import java.util.Arrays;

public class CloneIntermediate {
    static class Cart implements Cloneable {
        String customerName;
        int[] itemIds;

        Cart(String customerName, int[] itemIds) {
            this.customerName = customerName;
            this.itemIds = itemIds;
        }

        @Override
        public Cart clone() {
            try {
                return (Cart) super.clone(); // SHALLOW: itemIds reference is copied, not the array
            } catch (CloneNotSupportedException e) {
                throw new AssertionError(e);
            }
        }
    }

    public static void main(String[] args) {
        Cart original = new Cart("Alex", new int[]{101, 102});
        Cart quote = original.clone();

        quote.itemIds[0] = 999; // mutate through the CLONE...

        System.out.println(Arrays.toString(original.itemIds)); // [999, 102] — original changed too!
        System.out.println(Arrays.toString(quote.itemIds));    // [999, 102]
    }
}
```

**How to run:** `java CloneIntermediate.java`

Mutating `quote.itemIds[0]` unexpectedly changes `original.itemIds` as well, because `super.clone()` only copied the array *reference* into the clone — both `original.itemIds` and `quote.itemIds` still point to the exact same underlying array in memory.

### Level 3 — Advanced

Same `Cart`, now fixed with a proper deep-copy override that duplicates the array explicitly, restoring true independence between the original and the clone — the correct fix for the shallow-copy problem demonstrated above.

```java
import java.util.Arrays;

public class CloneAdvanced {
    static class Cart implements Cloneable {
        String customerName;
        int[] itemIds;

        Cart(String customerName, int[] itemIds) {
            this.customerName = customerName;
            this.itemIds = itemIds;
        }

        @Override
        public Cart clone() {
            try {
                Cart copy = (Cart) super.clone();       // shallow copy first (customerName, itemIds reference)
                copy.itemIds = itemIds.clone();          // then explicitly deep-copy the array field
                return copy;
            } catch (CloneNotSupportedException e) {
                throw new AssertionError(e);
            }
        }
    }

    public static void main(String[] args) {
        Cart original = new Cart("Alex", new int[]{101, 102});
        Cart quote = original.clone();

        quote.itemIds[0] = 999; // mutate through the clone

        System.out.println(Arrays.toString(original.itemIds)); // [101, 102] — unaffected now
        System.out.println(Arrays.toString(quote.itemIds));    // [999, 102]
    }
}
```

**How to run:** `java CloneAdvanced.java`

After `super.clone()` runs, `copy.itemIds = itemIds.clone()` explicitly replaces the copy's array reference with a brand-new array containing the same values — arrays have their own built-in `clone()` that always performs a real element-by-element copy — so `original.itemIds` and `quote.itemIds` now point to two entirely separate arrays, and mutating one no longer affects the other.

## 6. Walkthrough

Trace `main` in `CloneAdvanced` step by step.

**`new Cart("Alex", new int[]{101, 102})`.** A `Cart` is constructed with `customerName = "Alex"` and `itemIds` pointing to a freshly created two-element array, call it array `A1`, containing `[101, 102]`.

**`original.clone()`.** Inside the override, `super.clone()` runs `Object`'s native copy: a new `Cart` object is allocated, and every field is copied field-by-field — `customerName` (a `String` reference) is copied as-is, and `itemIds` is copied as a reference, meaning at this point the new object's `itemIds` also points to `A1` (the *same* array as `original`). Then `copy.itemIds = itemIds.clone()` runs: `itemIds.clone()` (called on the array, using array's own built-in clone, not `Cart`'s) creates a brand-new array, `A2`, with the same contents `[101, 102]`, and reassigns `copy.itemIds` to point to `A2` instead of `A1`. The method returns `copy`, now bound to the variable `quote`.

**`quote.itemIds[0] = 999`.** This mutates index `0` of array `A2` (the one `quote.itemIds` now references), changing it from `101` to `999`. Array `A1` (still referenced only by `original.itemIds`) is completely untouched by this assignment.

**Printing `original.itemIds`.** `original.itemIds` still points to `A1`, unchanged: `[101, 102]`.

**Printing `quote.itemIds`.** `quote.itemIds` points to `A2`, which was just mutated: `[999, 102]`.

```
new Cart("Alex", A1=[101,102])

original.clone():
  super.clone() -> new Cart, itemIds still points to A1 (shallow copy so far)
  copy.itemIds = itemIds.clone() -> A2 = new array [101,102], copy.itemIds now -> A2

quote.itemIds[0] = 999 -> mutates A2 only -> A2 = [999,102]

original.itemIds -> still A1 -> [101,102]  (untouched)
quote.itemIds    -> A2       -> [999,102]
```

**Final output.** `"[101, 102]"` followed by `"[999, 102]"` — confirming that the explicit `itemIds.clone()` step successfully decoupled the two arrays, unlike the intermediate version where both arrays remained one and the same, shared object.

## 7. Gotchas & takeaways

> **`super.clone()` alone only ever performs a shallow copy** — primitive fields are duplicated correctly, but every reference field (arrays, other objects, collections) is copied as a shared reference, not a recursive duplicate. Any mutable reference field needs its own explicit deep-copy step inside `clone()`, exactly as `itemIds.clone()` does here — this is common enough to be its own topic (Shallow vs deep clone) immediately following this one.

> **`Cloneable` is a marker interface with no methods** — implementing it does not give you a working `clone()` for free; it merely changes `Object.clone()`'s behaviour from "throw `CloneNotSupportedException`" to "perform the field copy." You must still override `clone()` yourself (typically just to widen its visibility to `public` and its return type, and to handle the checked exception) for callers to be able to invoke it conveniently.

- `clone()` on `Object` throws `CloneNotSupportedException` unless the class implements the empty marker interface `Cloneable`.
- `super.clone()` performs a field-by-field shallow copy: primitives are duplicated, reference fields are shared between the original and the clone.
- Any reference field holding mutable data (arrays, mutable objects, collections) needs an explicit deep-copy step inside `clone()` to avoid the original and the clone unintentionally sharing state.
- Many modern codebases avoid `clone()`/`Cloneable` entirely in favor of copy constructors or static factory copy methods, due to `Cloneable`'s awkward, checked-exception-laden design.
