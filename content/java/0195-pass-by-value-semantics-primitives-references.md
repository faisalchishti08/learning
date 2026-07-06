---
card: java
gi: 195
slug: pass-by-value-semantics-primitives-references
title: Pass-by-value semantics (primitives & references)
---

## 1. What it is

Java is **always pass-by-value** — no exceptions. When you call a method, each parameter receives a **copy** of whatever was passed in. For a primitive (`int`, `double`, `boolean`, etc.), that copy is the actual value itself, so changing the parameter inside the method never affects the caller's original variable. For an object, the "value" being copied is the **reference** (the memory address, conceptually) — so the parameter and the caller's variable both end up pointing at the *same* object, meaning mutations *through* that reference are visible to the caller, even though reassigning the parameter itself is not.

```java
void incrementPrimitive(int x) {
    x = x + 1; // only changes the LOCAL COPY
}

void modifyList(java.util.List<Integer> list) {
    list.add(99); // modifies the SHARED object the reference points to
}

int n = 5;
incrementPrimitive(n);
System.out.println(n); // 5 — unaffected; only the copy inside the method changed

java.util.List<Integer> nums = new java.util.ArrayList<>();
modifyList(nums);
System.out.println(nums); // [99] — the caller sees the mutation, since it's the SAME object
```

Both scenarios are pass-by-value in exactly the same sense — what differs is *what value gets copied*: a primitive's actual data, or an object's reference. Neither case is "pass-by-reference" in the sense some other languages use that term, since reassigning the parameter itself (`list = new ArrayList<>();` inside the method) would never affect the caller's variable.

## 2. Why & when

Understanding this distinction is essential for predicting exactly what a method call can and cannot change about the caller's state:

- **Primitives are always safe from external modification** — passing an `int` to a method can never change the caller's variable, no matter what the method does to its own copy internally.
- **Mutable objects can be changed "through" a reference** — passing a `List`, an array, or a custom mutable object lets the method's code alter the object's *internal* state (adding elements, changing fields), and the caller will see those changes, since both caller and method are looking at the same underlying object.
- **Reassigning a reference parameter never propagates back** — a method can never make a caller's variable point at a *different* object by reassigning its own parameter; it can only mutate the object the reference already points to, if that object is mutable.

This distinction matters constantly when designing method APIs — deciding whether a method should mutate an object it's given (an in-place operation) or should instead return a new object and leave the original untouched (as `Arrays.copyOf` does, contrasted with `Arrays.sort`, which mutates in place).

## 3. Core concept

```java
class Box {
    int value;
}

public class PassByValueDemo {
    static void reassign(Box b) {
        b = new Box(); // makes the LOCAL parameter point at a new object
        b.value = 999;  // only affects that new, local-only object
    }

    static void mutate(Box b) {
        b.value = 999; // changes the SAME object the caller's variable also points to
    }

    public static void main(String[] args) {
        Box original = new Box();
        original.value = 1;

        reassign(original);
        System.out.println(original.value); // 1 — unaffected; reassignment inside the method was local only

        mutate(original);
        System.out.println(original.value); // 999 — mutation through the shared reference IS visible
    }
}
```

`reassign` makes its own local parameter `b` point somewhere else entirely (`new Box()`), which has zero effect on `original`, since `original` still points at the first `Box`; `mutate` never reassigns its parameter at all — it simply changes a field *on* the object both `b` and `original` refer to, and that change is visible through both variables.

## 4. Diagram

<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A parameter b initially pointing at the same object as the caller's original variable, then splitting into two scenarios: reassigning b to point at a brand new object which leaves original untouched, versus mutating a field on the shared object which original does see">
  <rect x="8" y="8" width="584" height="184" rx="8" fill="#0d1117"/>

  <text x="60" y="30" fill="#79c0ff" font-size="11" font-family="monospace">original</text>
  <text x="60" y="48" fill="#79c0ff" font-size="11" font-family="monospace">b (parameter)</text>
  <line x1="130" y1="27" x2="200" y2="60" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="130" y1="45" x2="200" y2="60" stroke="#79c0ff" stroke-width="1.5"/>
  <rect x="200" y="50" width="90" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="245" y="72" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">Box{1}</text>

  <text x="60" y="115" fill="#8b949e" font-size="9" font-family="sans-serif">reassign(b): b = new Box()</text>
  <line x1="200" y1="112" x2="330" y2="112" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#r)"/>
  <rect x="330" y="95" width="90" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="375" y="117" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">Box{999}</text>
  <text x="470" y="117" fill="#8b949e" font-size="9" font-family="sans-serif">local only — original still points at Box{1}</text>

  <text x="60" y="160" fill="#8b949e" font-size="9" font-family="sans-serif">mutate(b): b.value = 999</text>
  <line x1="200" y1="157" x2="245" y2="85" stroke="#3fb950" stroke-width="1.5" marker-end="url(#g)"/>
  <text x="330" y="160" fill="#3fb950" font-size="9" font-family="sans-serif">changes Box{1} itself -&gt; original sees Box{999} too</text>

  <defs>
    <marker id="r" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="g" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Reassigning a reference parameter only redirects the local copy; mutating the object it points to is visible everywhere that object is referenced.

## 5. Runnable example

Scenario: a simple shopping cart tracked as a mutable list — starting with basic demonstration of a primitive being unaffected by a method, then extending to show a method mutating a shared list, then hardening into a method that must carefully choose between mutating in place versus returning a new, independent result, documenting the difference clearly.

### Level 1 — Basic

```java
public class CartBasic {
    static void tryToDouble(int quantity) {
        quantity = quantity * 2; // only the local copy changes
    }

    public static void main(String[] args) {
        int quantity = 3;
        tryToDouble(quantity);
        System.out.println("Quantity: " + quantity); // still 3
    }
}
```

**How to run:** `java CartBasic.java`

`tryToDouble` receives a copy of `quantity`'s value (`3`); doubling that copy inside the method has no way to reach back and change the caller's own `quantity` variable, since primitives are copied by value with no shared storage at all.

### Level 2 — Intermediate

Same idea, now with a mutable `List` representing cart items — demonstrating that adding to the list *inside* a method is visible to the caller, since both refer to the same underlying object.

```java
import java.util.ArrayList;
import java.util.List;

public class CartIntermediate {
    static void addItem(List<String> cart, String item) {
        cart.add(item); // mutates the SAME list object the caller has
    }

    public static void main(String[] args) {
        List<String> cart = new ArrayList<>();
        cart.add("apple");

        addItem(cart, "bread");

        System.out.println(cart); // [apple, bread] — the caller's list reflects the change
    }
}
```

**How to run:** `java CartIntermediate.java`

`addItem(cart, "bread")` passes a copy of the *reference* to `cart`'s list object — inside the method, `cart.add("bread")` mutates that shared object directly, and since `main`'s `cart` variable still points at that exact same object, the addition is immediately visible after the call returns.

### Level 3 — Advanced

Same cart, now with two contrasting methods — one that mutates the given cart in place, and one that deliberately returns a **new**, independent cart with a discount applied, leaving the original untouched — making the pass-by-value distinction an explicit, documented design choice.

```java
import java.util.ArrayList;
import java.util.List;

public class CartAdvanced {

    // Mutates the given cart directly — caller's list changes
    static void clearCart(List<String> cart) {
        cart.clear();
    }

    // Returns a NEW list; the original cart is left completely untouched
    static List<String> withItemAdded(List<String> cart, String item) {
        List<String> copy = new ArrayList<>(cart); // build an independent copy first
        copy.add(item);
        return copy;
    }

    public static void main(String[] args) {
        List<String> original = new ArrayList<>();
        original.add("apple");
        original.add("bread");

        List<String> withMilk = withItemAdded(original, "milk");
        System.out.println("Original: " + original);   // unaffected: [apple, bread]
        System.out.println("With milk: " + withMilk);  // [apple, bread, milk]

        clearCart(original);
        System.out.println("After clear: " + original); // [] — this one DOES mutate
    }
}
```

**How to run:** `java CartAdvanced.java`

`withItemAdded` deliberately builds `copy = new ArrayList<>(cart)` — a genuinely separate list object holding the same initial elements — before adding to it, so `original` is completely unaffected; `clearCart`, by contrast, calls `cart.clear()` directly on the object it was given, which **does** propagate back to `original`, since no copy was ever made there.

## 6. Walkthrough

Trace both method calls in `CartAdvanced.main`:

**`withItemAdded(original, "milk")`.** Parameter `cart` receives a copy of the reference to `original`'s list object (both now point at the same list, containing `["apple", "bread"]`). `copy = new ArrayList<>(cart)` creates a **brand-new**, independent list, initialized with the same elements copied in — `copy` and `cart` are now two separate objects. `copy.add("milk")` only affects this new object. `return copy` hands back this new list, assigned to `withMilk`. `original` (and the object `cart` referred to) was never touched.

**`clearCart(original)`.** Parameter `cart` again receives a copy of the reference to `original`'s list object — the *same* object as before (now `["apple", "bread"]`, unaffected by the previous call). `cart.clear()` removes every element from *that exact object*. Since `original` still refers to this same object, `original` is now also empty.

```
original: [apple, bread]  (list object A)

withItemAdded(original, "milk"):
  cart -> object A
  copy = new list (object B), initialized from A: [apple, bread]
  copy.add("milk") -> B becomes [apple, bread, milk]
  return B  (original still refers to A, unaffected)

clearCart(original):
  cart -> object A (same object as original)
  cart.clear() -> A becomes []
  original now sees [] too, since it's the same object A
```

**Final output.** `"Original: [apple, bread]"`, then `"With milk: [apple, bread, milk]"`, then after `clearCart`, `"After clear: []"` — demonstrating that whether a caller's object appears to change depends entirely on whether the called method mutates the shared object directly or builds and returns an independent copy.

## 7. Gotchas & takeaways

> **Java has no true "pass-by-reference" in the sense some other languages use the term — a method can never make a caller's variable point at a different object by reassigning its own parameter.** Confusing "the object can be mutated through a shared reference" with "the reference itself can be redirected by the callee" is one of the most common sources of confusion around this topic.

> **Whether a method mutates its argument in place or returns a new, independent result is a design decision the method's author makes explicitly** (as seen contrasting `clearCart` with `withItemAdded`) — always check a method's documentation or source when it's unclear which behaviour to expect, since both are common and equally valid patterns in real Java APIs.

- Java parameters always receive a copy: of the primitive's value, or of the object reference.
- Changing a primitive parameter's value inside a method never affects the caller's original variable.
- Mutating an object *through* a reference parameter (calling a method on it, changing one of its fields) is visible to the caller, since both point at the same object.
- Reassigning a reference parameter to point at a different object only affects the method's own local copy of that reference, never the caller's original variable.
