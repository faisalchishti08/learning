---
card: java
gi: 761
slug: statements-before-super-preview
title: Statements before super(...) (preview)
---

## 1. What it is

**Java 22** (JEP 447) previews relaxed constructor bodies: a constructor can now contain statements **before** an explicit `super(...)` or `this(...)` call, as long as those statements don't reference the instance being constructed (no `this` field access, no calling instance methods, nothing that needs the object to already exist). Previously, `super(...)`/`this(...)` had to be the **very first statement** in a constructor, full stop — even a simple argument-validation check had to be awkwardly inlined into the `super(...)` call's arguments themselves, or moved into a `static` helper method, rather than living as ordinary prior statements. Being a preview feature, it requires `--enable-preview` to compile and run.

## 2. Why & when

The old "super() must be first" rule existed for a good reason — the superclass has to finish initializing before any subclass code that might depend on it runs — but it was stricter than it needed to be, because it blocked even code that has **nothing to do with the instance itself**: validating constructor arguments, computing a derived value to pass to `super(...)`, or logging that construction started. Developers worked around this with ugly patterns: cramming validation logic into a ternary expression inside the `super(...)` call itself, or introducing a `private static` helper method purely so a check could run "before" the constructor body technically began. This preview relaxes the rule to match what was actually required all along: statements before `super(...)`/`this(...)` are fine, provided they only touch static state, constructor parameters, or locals — anything that doesn't require the not-yet-constructed instance to exist. This makes argument validation, precomputation, and early failure read as ordinary, readable code at the top of a constructor, rather than contorted expressions squeezed into a single call.

## 3. Core concept

```java
class PositiveNumber {
    private final int value;

    PositiveNumber(int value) {
        // Previously illegal: no statement before super()/this() call.
        if (value <= 0) {
            throw new IllegalArgumentException("value must be positive: " + value);
        }
        super(); // implicit super() made explicit here for clarity
        this.value = value;
    }
}
```

The validation check runs, and can throw, **before** `super()` — but it never touches `this`, so it's legal under the relaxed rule.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A relaxed constructor body allows statements that do not reference the instance to run before the super or this call, followed by the super call, followed by statements that may reference the instance">
  <rect x="20" y="20" width="200" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="120" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">pre-super statements</text>
  <text x="120" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no `this` access allowed</text>

  <line x1="220" y1="45" x2="270" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow761)"/>
  <defs><marker id="arrow761" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="280" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">super(...)</text>

  <line x1="420" y1="45" x2="470" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow761)"/>

  <rect x="480" y="20" width="140" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="550" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">rest of constructor</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The safety rule is preserved: nothing can touch the instance before super() completes</text>
</svg>

*Validation and precomputation can now precede `super(...)`, as long as they never touch the not-yet-constructed instance.*

## 5. Runnable example

Scenario: a range-checked measurement type, growing from an awkward validate-in-the-call-expression workaround into clean, readable pre-super validation.

### Level 1 — Basic

```java
public class TemperatureWorkaround {
    static class Temperature {
        private final double celsius;

        Temperature(double celsius) {
            // Old workaround: cram validation into the argument expression itself,
            // since no statement was allowed before this().
            this(validate(celsius));
        }

        private Temperature(double validated) {
            this.celsius = validated;
        }

        static double validate(double celsius) {
            if (celsius < -273.15) {
                throw new IllegalArgumentException("below absolute zero: " + celsius);
            }
            return celsius;
        }
    }

    public static void main(String[] args) {
        Temperature t = new Temperature(20.0);
        System.out.println("ok: " + t.celsius);
    }
}
```

**How to run:** `java TemperatureWorkaround.java` (JDK 22+; this specific workaround pattern works on any JDK).

This is the pre-JEP-447 workaround: a second, private constructor exists purely so validation logic can run inside a static helper method called *as an argument* to `this(...)`, since no statement could precede it directly.

### Level 2 — Intermediate

```java
public class TemperaturePreview {
    static class Temperature {
        private final double celsius;

        Temperature(double celsius) {
            if (celsius < -273.15) {
                throw new IllegalArgumentException("below absolute zero: " + celsius);
            }
            super(); // explicit, though implicit is equally legal
            this.celsius = celsius;
        }
    }

    public static void main(String[] args) {
        Temperature t = new Temperature(20.0);
        System.out.println("ok: " + t.celsius);

        try {
            new Temperature(-300.0);
        } catch (IllegalArgumentException e) {
            System.out.println("rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java --enable-preview --source 22 TemperaturePreview.java`.

The real-world concern added: the validation check moves directly into the constructor body, **before** `super()`, with no second constructor or static helper needed — the single constructor now reads top to bottom as "validate, then initialize," exactly matching the logical order a reader expects.

### Level 3 — Advanced

```java
public class TemperatureAdvanced {
    static class Measurement {
        protected final double value;
        protected final String unit;

        Measurement(double value, String unit) {
            System.out.println("Measurement super constructor running");
            this.value = value;
            this.unit = unit;
        }
    }

    static class Temperature extends Measurement {
        private final double celsius;

        Temperature(double fahrenheit) {
            if (fahrenheit < -459.67) {
                throw new IllegalArgumentException("below absolute zero (F): " + fahrenheit);
            }
            double computedCelsius = (fahrenheit - 32) * 5.0 / 9.0; // precompute before super
            super(computedCelsius, "celsius");
            this.celsius = computedCelsius;
            System.out.println("Temperature constructor finished: " + this.celsius + "C");
        }
    }

    public static void main(String[] args) {
        Temperature t = new Temperature(68.0);
        System.out.println("stored: " + t.value + " " + t.unit);

        try {
            new Temperature(-500.0);
        } catch (IllegalArgumentException e) {
            System.out.println("rejected before any construction happened: " + e.getMessage());
        }
    }
}
```

**How to run:** `java --enable-preview --source 22 TemperatureAdvanced.java`.

This adds the production-flavored hard case: a **subclass constructor** that validates its argument, then **computes a derived value** (`computedCelsius`, converting Fahrenheit to Celsius) before calling `super(...)` with that computed value — something the old rule made awkward, since the conversion math would otherwise have to be inlined directly into the `super(...)` call's argument expression.

## 6. Walkthrough

Tracing `TemperatureAdvanced.main`'s failing call, `new Temperature(-500.0)`:

1. The `Temperature(double fahrenheit)` constructor begins executing with `fahrenheit = -500.0`.
2. The validation check `if (fahrenheit < -459.67)` evaluates `true` (−500 is below absolute zero in Fahrenheit), so `IllegalArgumentException` is thrown **immediately** — critically, this happens before `super(...)` has been called at all, meaning no `Measurement` instance state has been initialized, and the `Measurement` super constructor's `println` never runs.
3. The exception propagates out of the constructor entirely; `main`'s `catch` block catches it and prints the rejection message.

For the successful call, `new Temperature(68.0)`:
1. The validation check passes (68°F is well above absolute zero).
2. `computedCelsius = (68 - 32) * 5.0 / 9.0 = 20.0` is computed as an ordinary local variable — this is a statement running before `super(...)`, but it only touches the constructor parameter `fahrenheit` and a new local, never `this`, so it's legal.
3. `super(computedCelsius, "celsius")` calls `Measurement`'s constructor with the precomputed value, which prints `"Measurement super constructor running"` and sets `this.value = 20.0` and `this.unit = "celsius"`.
4. Control returns to `Temperature`'s constructor, which sets `this.celsius = computedCelsius` (also `20.0`) and prints its own completion message.
5. Back in `main`, `t.value` and `t.unit` (inherited fields from `Measurement`) are printed.

Expected output:
```
Measurement super constructor running
Temperature constructor finished: 20.0C
stored: 20.0 celsius
rejected before any construction happened: below absolute zero (F): -500.0
```

## 7. Gotchas & takeaways

> **Gotcha:** statements before `super(...)`/`this(...)` still cannot reference `this` in any form — not `this.someField`, not calling an instance method, not passing `this` as an argument to something else. The compiler enforces this strictly; a pre-super statement can only use static members, constructor parameters, and local variables it creates itself.

- Preview feature in Java 22 — requires `--enable-preview` at compile and run time.
- Statements before `super(...)`/`this(...)` may validate arguments, compute derived values, or perform logging — but must not touch the instance under construction (`this`) in any way.
- This removes the old workarounds of inlining validation into a `super(...)`/`this(...)` call's arguments, or introducing an extra static helper method or overloaded constructor purely to sequence validation before initialization.
- The safety guarantee is unchanged: nothing can observe or use a partially-constructed instance — the relaxation only affects code that never needed the instance in the first place.
- Especially useful in subclass constructors that need to validate or transform a constructor argument before passing a derived value up to `super(...)`.
