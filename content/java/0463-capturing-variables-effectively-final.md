---
card: java
gi: 463
slug: capturing-variables-effectively-final
title: Capturing variables (effectively final)
---

## 1. What it is

A lambda can read local variables and parameters from its enclosing scope — this is called **capturing**. Java only allows capturing a local variable if it is **effectively final**: assigned exactly once, with its value never reassigned anywhere after that first assignment, even if it isn't explicitly marked `final`. You don't have to write the `final` keyword yourself, but the compiler enforces the same restriction as if you had.

## 2. Why & when

Java's lambdas capture local variables **by value**, not by reference — the lambda gets a private, permanent snapshot of the variable's value at the moment the lambda is created, not a live link back to the variable itself. If Java allowed a captured variable to be reassigned after the lambda was created, the lambda's snapshot and the enclosing method's live variable would silently diverge, and worse, a lambda might run on a different thread *after* its enclosing method has already returned — at which point the original local variable no longer even exists on the stack. Effectively-final enforcement makes that whole class of confusion impossible: if the compiler can prove a variable is never reassigned, capturing its one, unchanging value by copy is always safe.

You run into this rule any time a lambda references a variable from outside itself — a loop variable, a method parameter, a local computed earlier in the method. It matters most in exactly the situations where you're tempted to break it: accumulating a running total inside a lambda passed to `forEach`, or trying to reuse and mutate one variable across multiple lambda invocations. Both require rethinking the approach — usually with a proper reduction operation, or an object whose *field* (not a local variable) holds the mutable state, since fields aren't subject to this restriction at all.

## 3. Core concept

```java
import java.util.function.*;

int base = 10; // effectively final -- assigned once, never reassigned
Function<Integer, Integer> addBase = x -> x + base; // captures 'base' by value

// int total = 0;
// list.forEach(x -> total += x); // DOES NOT COMPILE: total is reassigned, so it's not effectively final
```

`addBase` captures a private copy of `base`'s value (`10`) at the moment it's created — later reassigning `base` (if the compiler even allowed it) would have no effect on the lambda, which is exactly why the compiler refuses to allow reassignment in the first place.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A lambda captures a snapshot copy of an effectively final local variable, not a live reference to it">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="200" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="55" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">int base = 10;</text>
  <text x="130" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">local variable, never reassigned</text>

  <line x1="130" y1="80" x2="130" y2="105" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <text x="200" y="98" fill="#8b949e" font-size="10" font-family="sans-serif">copied by value</text>

  <rect x="30" y="105" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="130" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">lambda's own private copy: 10</text>

  <text x="340" y="60" fill="#f85149" font-size="10" font-family="sans-serif">int total = 0; total += x;</text>
  <text x="340" y="78" fill="#f85149" font-size="10" font-family="sans-serif">-- reassigned, so NOT effectively</text>
  <text x="340" y="94" fill="#f85149" font-size="10" font-family="sans-serif">final -- compile error to capture it</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#8b949e"/></marker></defs>
</svg>

Once a value is copied into the lambda, there is no live connection back to the original variable to keep in sync — which is exactly why the original must never change.

## 5. Runnable example

Scenario: building per-item discount calculators — evolved from a single lambda capturing one effectively-final variable, through several lambdas each capturing a *different* value of a loop variable safely, to a workaround for accumulating a running total using a mutable holder object instead of a reassigned local.

### Level 1 — Basic

```java
import java.util.function.*;

public class CaptureBasic {
    public static void main(String[] args) {
        double discountRate = 0.15; // effectively final -- assigned once, never reassigned

        Function<Double, Double> applyDiscount = price -> price - (price * discountRate);

        System.out.println(applyDiscount.apply(100.0));
        System.out.println(applyDiscount.apply(50.0));
    }
}
```

**How to run:** `java CaptureBasic.java`

Expected output:
```
85.0
42.5
```

`discountRate` is captured by the lambda: it's assigned exactly once and never reassigned, so it qualifies as effectively final, and the lambda is allowed to read it. Every call to `applyDiscount.apply(...)` uses the same captured value, `0.15`.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.function.*;

public class CaptureLoopVariable {
    public static void main(String[] args) {
        List<Supplier<String>> greeters = new ArrayList<>();

        for (String name : List.of("Alice", "Bob", "Carol")) {
            // 'name' is a NEW effectively-final variable on every loop iteration --
            // each lambda captures its OWN iteration's value, not a shared, mutated one.
            greeters.add(() -> "Hello, " + name + "!");
        }

        for (Supplier<String> greeter : greeters) {
            System.out.println(greeter.get());
        }
    }
}
```

**How to run:** `java CaptureLoopVariable.java`

Expected output:
```
Hello, Alice!
Hello, Bob!
Hello, Carol!
```

The real-world concern this shows: a for-each loop variable is a **fresh** effectively-final variable on every iteration (unlike a classic `for (int i = 0; ...; i++)` counter, which is reassigned and therefore cannot be captured at all) — so each of the three lambdas correctly captures its own iteration's `name`, and none of them see a shared, later-overwritten value.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;

public class CaptureMutableHolder {
    // A tiny mutable holder -- its FIELD can be reassigned freely, because effectively-final
    // rules apply only to local variables, never to an object's fields.
    static class Total {
        double value = 0.0;
    }

    public static void main(String[] args) {
        List<Double> prices = List.of(19.99, 5.50, 42.00, 3.25);
        Total total = new Total(); // 'total' itself is effectively final -- never reassigned

        Consumer<Double> accumulate = price -> total.value += price; // mutates the FIELD, not the local

        prices.forEach(accumulate);

        System.out.println("Total: " + total.value);
    }
}
```

**How to run:** `java CaptureMutableHolder.java`

Expected output:
```
Total: 70.74
```

`total` (the local variable) is captured and never reassigned — it always points to the same `Total` object — so it satisfies effectively-final rules. The lambda mutates `total.value`, a **field** on that object, which is not subject to the effectively-final restriction at all. This is the standard workaround for "I need to accumulate state across lambda calls": wrap the mutable state in an object's field and capture a reference to the object, rather than trying to capture and reassign a bare local.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `prices` holds four values. `total` is created once, pointing to a fresh `Total` object whose `value` field starts at `0.0`.

`accumulate` is defined as `price -> total.value += price`. At the moment this lambda is created, it captures the local variable `total` — a reference to the `Total` object — by value. Since references are themselves values, what's captured is "which object `total` points to," and that never changes (`total` is never reassigned to point elsewhere), so this capture is legal.

`prices.forEach(accumulate)` calls the lambda once per element, in list order: first with `price = 19.99`, then `5.50`, then `42.00`, then `3.25`.

On each call, `total.value += price` does **not** touch the captured local variable `total` at all — it dereferences the captured reference to reach the `Total` object, and mutates that object's `value` field in place. Since all four invocations captured the *same* reference (there's only one `total`, created once outside the loop-like `forEach` call), all four mutations accumulate onto the same object's field.

```
call 1: total.value = 0.0 + 19.99 = 19.99
call 2: total.value = 19.99 + 5.50 = 25.49
call 3: total.value = 25.49 + 42.00 = 67.49
call 4: total.value = 67.49 + 3.25 = 70.74
```

After `forEach` finishes, `total.value` holds `70.74`, which `System.out.println` prints. The key distinction from the Level 2 example is that here the *same* object's field is deliberately mutated across every call (an intentional running total), whereas in Level 2, each lambda deliberately captured a *distinct*, unchanging value per iteration (three separate greetings, not one running computation).

## 7. Gotchas & takeaways

> Capturing `this` inside a lambda is different from capturing a local variable: a lambda's `this` refers to the *enclosing instance*, not the lambda itself (lambdas have no `this` of their own) — see the dedicated topic on `this` in lambdas for the full detail. That's unrelated to effectively-final rules, but it's easy to conflate the two since both concern "what a lambda can see from outside itself."

- A captured local variable must be effectively final: assigned exactly once, never reassigned afterward — the compiler enforces this even without an explicit `final` keyword.
- Capturing happens **by value**: the lambda gets a private, permanent copy of the variable's value (or, for a reference type, a copy of the reference) at creation time, not a live link back to the original.
- A classic counting `for` loop's index variable (`i` in `for (int i = 0; ...; i++)`) is reassigned every iteration, so it can never be captured directly — a for-each loop's variable, by contrast, is fresh and effectively final on each iteration, and can be captured safely.
- To accumulate mutable state across multiple lambda invocations, capture a reference to an object and mutate its **field**, since fields are not subject to the effectively-final restriction — this is the standard workaround, not a special exception.
- This restriction exists to guarantee a captured value can never silently diverge between the enclosing method and the lambda, especially important since a lambda may still run long after the method that created it has returned (for example, on another thread).
