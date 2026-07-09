---
card: java
gi: 785
slug: flexible-constructor-bodies-standardized
title: Flexible constructor bodies — standardized
---

## 1. What it is

**Java 24** (JEP 492) makes flexible constructor bodies a **permanent, standard feature** — no `--enable-preview` flag required — after two preview rounds ([Java 22](0761-statements-before-super-preview.md), [Java 23](0773-flexible-constructor-bodies-2nd-preview.md)). A constructor may now permanently contain statements before its explicit `super(...)`/`this(...)` call, as long as those statements don't reference the instance under construction — including the second preview's refinement allowing an inner class's prologue to reference its already-existing **enclosing instance**. The decades-old rule that `super(...)`/`this(...)` had to be a constructor's literal first statement is gone for good.

## 2. Why & when

Both preview rounds targeted a genuinely common pain point — argument validation and derived-value computation that logically belongs *before* initialization but couldn't be expressed as ordinary statements — and neither round found a reason to walk back the core relaxation; the second round only extended it slightly further, for inner classes referencing their enclosing instance. With two rounds of real-world use confirming the safety model holds (the instance under construction genuinely never becomes observable early, whatever else is relaxed around it), standardization removes the last reason to hesitate: any constructor that used to cram validation into a `super(...)` call's argument expression, or introduce an extra private constructor purely to sequence checks before initialization, can now be written as plain, readable, top-to-bottom code, with no preview flag and no workaround.

## 3. Core concept

```java
class PositiveNumber {
    private final int value;

    PositiveNumber(int value) {
        // No --enable-preview needed anymore — standard Java 24 syntax.
        if (value <= 0) {
            throw new IllegalArgumentException("value must be positive: " + value);
        }
        this.value = value; // implicit super() runs automatically before this line
    }
}
```

The validation runs before any implicit or explicit `super(...)` call — permanently legal syntax as of Java 24, with no flag required.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Flexible constructor bodies standardize after two preview rounds, permanently allowing validation and precomputation statements before super or this calls">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 22 preview -&gt; Java 23 2nd preview -&gt; Java 24 standard</text>

  <rect x="60" y="90" width="220" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="170" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">validate arguments</text>
  <text x="170" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">before super()/this() — legal</text>

  <rect x="360" y="90" width="220" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="470" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">this.field access</text>
  <text x="470" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">before super()/this() — still illegal</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The safety boundary is permanent, not just previewed</text>
</svg>

*The line between "safe to run early" and "requires the instance to exist" is now a fixed, standard rule.*

## 5. Runnable example

Scenario: a range-checked temperature type with a subclass that precomputes a converted value, growing from validation into the full nested-class enclosing-instance pattern from the second preview — all as standard Java 24 code.

### Level 1 — Basic

```java
public class TemperatureStandardBasic {
    static class Temperature {
        private final double celsius;

        Temperature(double celsius) {
            if (celsius < -273.15) {
                throw new IllegalArgumentException("below absolute zero: " + celsius);
            }
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

**How to run:** `java TemperatureStandardBasic.java` (JDK 24+, no `--enable-preview` needed).

Validation runs before the implicit `super()` call, exactly as in the preview rounds, now with no flag required.

### Level 2 — Intermediate

```java
public class TemperatureStandardDerived {
    static class Measurement {
        protected final double value;
        protected final String unit;

        Measurement(double value, String unit) {
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
        }
    }

    public static void main(String[] args) {
        Temperature t = new Temperature(68.0);
        System.out.println(t.value + " " + t.unit);
    }
}
```

**How to run:** `java TemperatureStandardDerived.java`.

The real-world concern added: a subclass constructor validating its argument, then computing a derived value **before** calling `super(...)` with it — the exact pattern that used to require awkward inlining into the `super(...)` call's arguments, now ordinary, readable code.

### Level 3 — Advanced

```java
public class TemperatureStandardEnclosing {
    static class Roster {
        private final String[] names;

        Roster(String[] names) { this.names = names; }

        class Slot {
            private final int index;
            private final String label;

            Slot(int index) {
                if (index < 0 || index >= Roster.this.names.length) {
                    throw new IndexOutOfBoundsException("bad index: " + index);
                }
                String computedLabel = Roster.this.names[index] + "#" + index;
                super();
                this.index = index;
                this.label = computedLabel;
            }
        }
    }

    public static void main(String[] args) {
        Roster roster = new Roster(new String[]{"Ada", "Grace", "Linus"});
        Roster.Slot slot = roster.new Slot(1);
        System.out.println(slot.label);

        try {
            roster.new Slot(9);
        } catch (IndexOutOfBoundsException e) {
            System.out.println("rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java TemperatureStandardEnclosing.java`.

This adds the production-flavored hard case: an inner class prologue reading its **enclosing instance** (`Roster.this.names`) before `super()` — the second preview's refinement — now standard, permanent behavior with no flag needed.

## 6. Walkthrough

Tracing `TemperatureStandardEnclosing.main`'s failing call, `roster.new Slot(9)`:

1. `Slot`'s constructor begins with `index = 9`, its captured reference to the enclosing `roster` already set as part of inner-class instance creation.
2. The prologue check reads `Roster.this.names.length` (which is `3`); since `9 >= 3`, `IndexOutOfBoundsException` is thrown immediately, before `super()` and before any `Slot` field is touched.
3. `main`'s `catch` block prints the rejection message.

For the successful call, `roster.new Slot(1)`:
1. The bounds check passes.
2. `computedLabel = Roster.this.names[1] + "#" + 1` reads the enclosing `Roster`'s array to compute `"Grace#1"` — a prologue statement touching only the already-existing enclosing instance, legal under the now-permanent rule.
3. `super()` runs, after which `this.index` and `this.label` are set on the `Slot` instance.

Expected output:
```
Grace#1
rejected: bad index: 9
```

## 7. Gotchas & takeaways

> **Gotcha:** the rule remains exactly as strict as the preview rounds established — a prologue statement still cannot reference `this` in any form, only static members, constructor parameters, locals, and (for inner classes) the already-existing enclosing instance. Standardization changed the flag requirement, not the safety boundary.

- Standardized in Java 24 (JEP 492) — no `--enable-preview` flag needed; production-ready.
- Statements before `super(...)`/`this(...)` may validate arguments, compute derived values, or (for inner classes) read the enclosing instance — but never the instance under construction itself.
- This removes the last preview-era caveat around the feature; code from either preview round runs unchanged as standard Java 24, only the compiler/runtime flags need removing.
- The old workarounds — inlining validation into a `super(...)`/`this(...)` call's arguments, or adding an extra constructor purely to sequence checks — are now unnecessary for any codebase targeting Java 24+.
- Especially valuable in subclass constructors validating or transforming an argument before passing a derived value to `super(...)`, and in inner classes validating against their enclosing instance's state.
