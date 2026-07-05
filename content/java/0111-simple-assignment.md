---
card: java
gi: 111
slug: simple-assignment
title: Simple assignment =
---

## 1. What it is

`=` stores the value of its right-hand expression into the variable named on its left. For primitive types, assignment copies the *value* itself — after `int b = a;`, `a` and `b` are independent copies, and changing one never affects the other. For reference types (objects, arrays), assignment copies the *reference* (the "address" the variable points to), not the object's contents — after `Point p2 = p1;`, both `p1` and `p2` point to the *same* object, so a mutation through either variable is visible through both.

```java
int a = 5;
int b = a;   // b gets a COPY of a's value: 5
a = 10;
System.out.println(b);   // still 5 — primitives are copied by value

int[] arr1 = { 1, 2, 3 };
int[] arr2 = arr1;        // arr2 gets a COPY of the REFERENCE, not a new array
arr2[0] = 99;
System.out.println(arr1[0]);  // 99! both variables point to the same array object
```

`=` is also right-associative and itself an expression that evaluates to the assigned value, which is why chained assignment works: `a = b = c = 5;` assigns `5` to `c`, then that expression's value (`5`) is assigned to `b`, then to `a`.

## 2. Why & when

Understanding the value-vs-reference distinction in `=` is fundamental to avoiding one of the most common categories of Java bugs — accidental aliasing:

- Passing an array or object to a method and expecting the method's internal changes not to affect the caller's copy — but since only the reference is passed, mutations *are* visible to the caller.
- Assigning one collection variable to another (`List<String> copy = original;`) expecting an independent copy, but getting a second name for the same list instead.
- Deliberately wanting shared state (e.g., a shared configuration object multiple components should all see updates to) — here, reference-copy semantics are exactly what you want.

You need an explicit copy (via a copy constructor, `clone()`, `Arrays.copyOf`, or a copying constructor like `new ArrayList<>(original)`) whenever you need the new variable to be truly independent of the original.

## 3. Core concept

```java
import java.util.*;

public class AssignmentDemo {
    public static void main(String[] args) {
        // Primitive assignment: independent copies
        int a = 5;
        int b = a;
        a = 999;
        System.out.println("a=" + a + ", b=" + b);   // a=999, b=5 (unaffected)

        // Reference assignment: shared object
        int[] arr1 = { 1, 2, 3 };
        int[] arr2 = arr1;             // same array, two names
        arr2[0] = 99;
        System.out.println("arr1[0]=" + arr1[0]);   // 99 — arr1 sees arr2's change too

        // Chained assignment: right-associative, evaluates right to left
        int x, y, z;
        x = y = z = 10;
        System.out.println("x=" + x + ", y=" + y + ", z=" + z);   // 10, 10, 10

        // Reassigning a reference variable does NOT affect what it used to point to
        List<String> listA = new ArrayList<>(List.of("one", "two"));
        List<String> listB = listA;    // same list, two names
        listB = new ArrayList<>(List.of("three"));  // listB now points somewhere new
        System.out.println("listA=" + listA + ", listB=" + listB);  // listA unaffected, still [one, two]
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Assignment diagram: primitive assignment copies the value into a separate box, so later changes to one do not affect the other. Reference assignment copies the pointer, so both variables point to the same object box, and mutating through either name is visible through both.">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">int b = a;  vs.  int[] arr2 = arr1;</text>

  <text x="170" y="46" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Primitive: independent copies</text>
  <rect x="80" y="56" width="70" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">a: 5</text>
  <rect x="190" y="56" width="70" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="225" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">b: 5</text>
  <text x="170" y="112" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">two separate boxes — changing a never touches b</text>

  <text x="530" y="46" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Reference: shared object</text>
  <rect x="450" y="56" width="60" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="76" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">arr1</text>
  <rect x="590" y="56" width="60" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="620" y="76" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">arr2</text>
  <rect x="500" y="110" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="565" y="134" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">[1, 2, 3]</text>
  <line x1="480" y1="86" x2="540" y2="110" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="620" y1="86" x2="590" y2="110" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="168" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">one shared box — mutating via either name is visible through both</text>
</svg>

Primitive `=` copies the value into a new box; reference `=` copies the pointer, so both names lead to the same box.

## 5. Runnable example

Scenario: a shopping cart where a "checkout snapshot" of the cart's items must be taken — showing the aliasing bug that arises from a naive `=` "copy," then fixing it with a real copy.

### Level 1 — Basic

```java
import java.util.*;

public class AssignmentBasic {
    public static void main(String[] args) {
        List<String> cart = new ArrayList<>();
        cart.add("Book");
        cart.add("Pen");

        // Intending to "snapshot" the cart before checkout for a receipt
        List<String> receiptItems = cart;   // NOT a copy — same list, two names

        cart.add("Eraser");  // customer adds one more item after "checkout" started
        System.out.println("Receipt items: " + receiptItems);  // shows Eraser too! bug
    }
}
```

**How to run:** `java AssignmentBasic.java`

`List<String> receiptItems = cart;` does not create a new list — it copies the *reference*, so `receiptItems` and `cart` are two names for the exact same `ArrayList` object. When `cart.add("Eraser")` runs afterward, that mutation is visible through `receiptItems` too, because there was never a second list to begin with — the "receipt snapshot" was never actually frozen in time.

### Level 2 — Intermediate

Same cart, now taking a genuine, independent snapshot using a copying constructor, so later mutations to the live cart do not leak into the receipt.

```java
import java.util.*;

public class AssignmentIntermediate {
    public static void main(String[] args) {
        List<String> cart = new ArrayList<>();
        cart.add("Book");
        cart.add("Pen");

        // A real copy: new ArrayList<>(cart) creates a NEW list containing the same elements
        List<String> receiptItems = new ArrayList<>(cart);

        cart.add("Eraser");  // mutating the live cart after the snapshot was taken
        System.out.println("Live cart:     " + cart);          // [Book, Pen, Eraser]
        System.out.println("Receipt items: " + receiptItems);   // [Book, Pen] — unaffected, correct
    }
}
```

**How to run:** `java AssignmentIntermediate.java`

`new ArrayList<>(cart)` constructs a brand-new `ArrayList` object and copies each element reference from `cart` into it — `receiptItems` now points to a genuinely different object from `cart`. Adding `"Eraser"` to `cart` afterward only affects `cart`'s own internal array; `receiptItems` has its own separate internal array that was populated once, at copy time, and is untouched by later changes to `cart`.

### Level 3 — Advanced

Same cart system, now handling a subtler case: the copy above is a **shallow copy** — if the cart held mutable objects (not immutable `String`s), mutating one of *those* shared objects would still leak through both lists. Demonstrated and fixed with a deep copy.

```java
import java.util.*;

public class AssignmentAdvanced {

    static class CartItem {
        String name;
        int quantity;
        CartItem(String name, int quantity) { this.name = name; this.quantity = quantity; }
        CartItem(CartItem other) { this.name = other.name; this.quantity = other.quantity; } // copy constructor
        public String toString() { return name + " x" + quantity; }
    }

    public static void main(String[] args) {
        List<CartItem> cart = new ArrayList<>();
        cart.add(new CartItem("Book", 1));
        cart.add(new CartItem("Pen", 3));

        // Shallow copy: new list, but the SAME CartItem objects inside it
        List<CartItem> shallowReceipt = new ArrayList<>(cart);

        // Mutating an item's field (not the list itself) through the live cart...
        cart.get(1).quantity = 5;   // customer changed pen quantity after "checkout" began

        System.out.println("Live cart:      " + cart);
        System.out.println("Shallow receipt: " + shallowReceipt);  // ALSO shows quantity 5! shared objects leak

        // Deep copy: build brand-new CartItem objects for the snapshot
        List<CartItem> deepReceipt = new ArrayList<>();
        for (CartItem item : cart) {
            deepReceipt.add(new CartItem(item));  // uses the copy constructor to clone each item
        }

        cart.get(0).quantity = 100;  // another late mutation to the live cart
        System.out.println("Live cart:    " + cart);
        System.out.println("Deep receipt: " + deepReceipt);  // unaffected — true independent snapshot
    }
}
```

**How to run:** `java AssignmentAdvanced.java`

`new ArrayList<>(cart)` for `shallowReceipt` copies the list structure (a new array of references) but each slot still holds a reference to the *same* `CartItem` objects as `cart` — this is a shallow copy. When `cart.get(1).quantity = 5` mutates the `CartItem` object itself (not the list), that mutation is visible through *both* `cart` and `shallowReceipt`, because both lists' slot at index `1` point to the identical object. The deep copy loop instead constructs a brand-new `CartItem` for each entry via the copy constructor `new CartItem(item)`, which copies each field individually — `deepReceipt` now holds entirely separate `CartItem` objects, so later mutations to the live cart's items (like `cart.get(0).quantity = 100`) have no effect on `deepReceipt` at all.

## 6. Walkthrough

Trace the shallow-copy leak in the advanced example:

**Building the cart.** `cart.add(new CartItem("Book", 1))` creates a `CartItem` object (call its identity `#101`) and adds a reference to it at index `0`. `cart.add(new CartItem("Pen", 3))` creates a second object (`#102`) at index `1`.

**Shallow copy.** `new ArrayList<>(cart)` creates a new `ArrayList` object, then copies the *references* stored in `cart` into it: index `0` of `shallowReceipt` points to `#101` (the same `Book` object), index `1` points to `#102` (the same `Pen` object). No new `CartItem` objects were created — only a new list "container" was.

**The mutation.** `cart.get(1)` retrieves the reference at index `1`, which is `#102`. `.quantity = 5` mutates the `quantity` field *inside* object `#102` directly. This is a change to the object itself, not to either list's structure.

**Observing the leak.** `shallowReceipt.get(1)` also holds a reference to `#102` — the same object that was just mutated. Printing `shallowReceipt` therefore shows `"Pen x5"`, reflecting the mutation, even though nothing was ever explicitly done to `shallowReceipt`.

```
cart:            [ ref→#101(Book,1), ref→#102(Pen,3) ]
shallowReceipt:  [ ref→#101(Book,1), ref→#102(Pen,3) ]   <- same object references, different list container

cart.get(1).quantity = 5   mutates object #102 directly

cart:            [ ref→#101(Book,1), ref→#102(Pen,5) ]
shallowReceipt:  [ ref→#101(Book,1), ref→#102(Pen,5) ]   <- sees the mutation, because it's the SAME #102 object
```

**The deep-copy fix.** The loop `for (CartItem item : cart) deepReceipt.add(new CartItem(item));` explicitly constructs a *new* `CartItem` object for every entry (say `#201` copying from `#101`, `#202` copying from `#102`), so `deepReceipt` holds entirely distinct objects from `cart`. Subsequent mutations to `cart`'s objects (`#101`, `#102`) have no path to reach `#201`/`#202`, since nothing in `deepReceipt` references the originals anymore.

## 7. Gotchas & takeaways

> **`=` on a reference type copies the pointer, not the object.** `List<X> b = a;` makes `b` and `a` two names for the identical object — mutating the object through either name is visible through both. If you need an independent copy, you must create one explicitly (a copy constructor, `clone()`, `Arrays.copyOf`, etc.).

> **A "copy" of a collection (e.g., `new ArrayList<>(original)`) is shallow by default.** The list container is new, but the elements inside it are the same shared objects. If those elements are mutable, you need a deep copy (copying each element individually) to achieve true independence.

- Primitive `=` copies the value: the two variables become fully independent afterward.
- Reference `=` copies the reference: the two variables become aliases for the same underlying object.
- `=` is right-associative and is itself an expression, enabling chained assignment (`a = b = c = 5;`), which assigns right to left.
- Distinguish shallow copies (new container, shared elements) from deep copies (new container, new elements too) based on whether the elements themselves are mutable and need independence.
