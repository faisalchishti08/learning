---
card: java
gi: 955
slug: compact-canonical-constructor
title: Compact canonical constructor
---

## 1. What it is

The compact canonical constructor is a special, abbreviated syntax for writing a record's [canonical constructor](0954-record-components-canonical-constructor.md) — you write the record's name followed directly by a body, with **no parameter list at all** (`Temperature { ... }`, not `Temperature(double celsius) { ... }`), because the compiler already knows the parameters must exactly match the record's declared components, in the same order. Inside that body, you can validate arguments, throw exceptions, or reassign a parameter to normalize it — but you may **not** write explicit `this.field = value` assignments yourself; the compiler automatically appends the standard field assignments for every component, using whatever value each parameter holds at the end of the compact body, immediately after your written code finishes executing normally.

## 2. Why & when

The compact form exists specifically to keep the common case — adding validation or light normalization to an otherwise-ordinary record — free of the repetition a full, explicit-parameter-list constructor would require (having to write out every component's name and type again in the parameter list, and then write out every single field assignment by hand, even for components you have nothing special to say about). Use it whenever your validation or normalization logic applies uniformly and you don't need to change *which* fields get assigned or in what order — which covers the overwhelming majority of real record-validation needs. You need the full, explicit-parameter-list canonical constructor form instead only in the rare case where you must do something the compact form's fixed "run body, then assign all fields automatically" structure cannot express — for instance, deliberately assigning one component's field based on a computation involving a *different* parameter in a way that doesn't fit the "validate/normalize this same parameter, then let it be auto-assigned" pattern (though even this is unusual, since records are meant to be simple, transparent data carriers, and complex inter-component derivation is often a sign the type should instead expose a static factory method rather than embedding that complexity in the constructor itself).

## 3. Core concept

```
record Range(int low, int high) {

    // COMPACT canonical constructor: no parameter list -- compiler infers (int low, int high)
    Range {
        if (low > high) {
            throw new IllegalArgumentException("low must be <= high");
        }
        // NO "this.low = low; this.high = high;" written here --
        // the compiler appends exactly that, automatically, using
        // whatever 'low' and 'high' currently hold at this point.
    }
}

// The EXPLICIT, full-parameter-list equivalent (verbose, rarely needed):
record RangeVerbose(int low, int high) {
    RangeVerbose(int low, int high) {          // full parameter list -- must repeat exactly
        if (low > high) {
            throw new IllegalArgumentException("low must be <= high");
        }
        this.low = low;                         // MUST write field assignments yourself
        this.high = high;                       // easy to forget, or assign in wrong order
    }
}
```

The compact form trades a small amount of flexibility (you can't skip or reorder field assignments) for guaranteed correctness (you literally cannot forget one) and much less repetition — exactly the tradeoff records as a whole are designed around.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A compact constructor's body executing first for validation or normalization, followed automatically by the compiler-appended field assignments for every component" >
  <rect x="20" y="30" width="260" height="50" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Your compact constructor BODY</text>
  <text x="150" y="66" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">validate / normalize parameters</text>

  <rect x="330" y="30" width="290" height="50" fill="#1c2430" stroke="#6db33f"/>
  <text x="475" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Compiler-appended assignments</text>
  <text x="475" y="66" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">this.x = x; this.y = y; ... (auto)</text>

  <line x1="280" y1="55" x2="330" y2="55" stroke="#8b949e" marker-end="url(#a)"/>

  <text x="320" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Runs ONLY if your body completes normally (no exception thrown) --</text>
  <text x="320" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">uses whatever value each parameter holds AFTER your body finishes</text>
</svg>

*The compact body runs first; the compiler's automatic field assignments only happen afterward, and only if no exception was thrown.*

## 5. Runnable example

Scenario: build a validated numeric range type, evolving through the compact constructor's key behaviors — starting with basic validation, then adding parameter normalization (reassignment before the implicit field assignment), then handling a harder case involving cross-component validation that depends on both parameters together.

### Level 1 — Basic

```java
public class CompactConstructorBasic {
    record Range(int low, int high) {
        Range {
            if (low > high) {
                throw new IllegalArgumentException("low (" + low + ") must be <= high (" + high + ")");
            }
        }
    }

    public static void main(String[] args) {
        Range r = new Range(1, 10);
        System.out.println(r);
        try {
            new Range(10, 1);
        } catch (IllegalArgumentException e) {
            System.out.println("caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CompactConstructorBasic.java` (JDK 17+).

Expected output:
```
CompactConstructorBasic$Range[low=1, high=10]
caught: low (10) must be <= high (1)
```

The compact body's `if` check runs before any field assignment; when it throws, the compiler-appended assignments never execute at all, and no `Range` object is ever fully constructed — exactly the guarantee you want from validation logic: an invalid state simply cannot come into existence.

### Level 2 — Intermediate

```java
public class CompactConstructorNormalization {
    record Range(int low, int high) {
        Range {
            if (low > high) {
                int tmp = low;
                low = high;   // NORMALIZE: swap so low is always <= high, rather than rejecting
                high = tmp;   // reassigning parameters here changes what gets auto-assigned to fields
            }
        }
    }

    public static void main(String[] args) {
        Range r1 = new Range(1, 10);
        Range r2 = new Range(10, 1); // "backwards" arguments -- normalized instead of rejected
        System.out.println("r1: " + r1);
        System.out.println("r2: " + r2);
        System.out.println("r1.equals(r2): " + r1.equals(r2));
    }
}
```

**How to run:** `java CompactConstructorNormalization.java` (JDK 17+).

Expected output:
```
r1: CompactConstructorNormalization$Range[low=1, high=10]
r2: CompactConstructorNormalization$Range[low=1, high=10]
r1.equals(r2): true
```

The real-world concern added: instead of rejecting "backwards" arguments outright, this compact constructor *normalizes* them by swapping the local `low`/`high` parameters when needed — since the compiler's implicit field assignment uses whatever these parameters hold at the end of the body, both `new Range(1, 10)` and `new Range(10, 1)` end up with an internal state of `low=1, high=10`, making them equal via the record's auto-generated `equals()`, despite the constructor arguments being given in opposite order.

### Level 3 — Advanced

```java
public class CompactConstructorCrossValidation {
    record TimeWindow(int startMinute, int endMinute, int minDurationMinutes) {
        TimeWindow {
            if (startMinute < 0 || endMinute > 1440) {
                throw new IllegalArgumentException("times must be within a single day (0-1440 minutes)");
            }
            if (endMinute <= startMinute) {
                throw new IllegalArgumentException("endMinute must be after startMinute");
            }
            int actualDuration = endMinute - startMinute; // computed from TWO parameters together
            if (actualDuration < minDurationMinutes) {
                throw new IllegalArgumentException(
                    "window is only " + actualDuration + " minutes, needs at least " + minDurationMinutes);
            }
        }
    }

    public static void main(String[] args) {
        TimeWindow valid = new TimeWindow(540, 600, 30); // 9:00-10:00, needs >= 30 min -- OK (60 min)
        System.out.println("valid: " + valid);
        try {
            new TimeWindow(540, 550, 30); // only 10 minutes, needs 30
        } catch (IllegalArgumentException e) {
            System.out.println("caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CompactConstructorCrossValidation.java` (JDK 17+).

Expected output:
```
valid: CompactConstructorCrossValidation$TimeWindow[startMinute=540, endMinute=600, minDurationMinutes=30]
caught: window is only 10 minutes, needs at least 30
```

The production-flavored hard case: this validation depends on a computed relationship *across* multiple components together (`endMinute - startMinute` compared against `minDurationMinutes`), not just a check on any single parameter in isolation — the compact constructor form handles this naturally, since its body is ordinary code with full access to every parameter simultaneously, letting you express arbitrarily complex multi-component invariants before the compiler's automatic field assignments run, all without needing to fall back to the verbose, explicit-parameter-list constructor form.

## 6. Walkthrough

Tracing `new TimeWindow(540, 550, 30)` end to end from `CompactConstructorCrossValidation.main`:

1. The constructor call binds the compact constructor's implicit parameters to `startMinute=540`, `endMinute=550`, `minDurationMinutes=30` — matching the record header's three declared components, in order.
2. The first check, `startMinute < 0 || endMinute > 1440`, evaluates `540 < 0` (false) and `550 > 1440` (false), so this check passes without throwing.
3. The second check, `endMinute <= startMinute`, evaluates `550 <= 540`, which is false (550 is indeed after 540), so this check also passes.
4. `actualDuration` is computed as `endMinute - startMinute`, which is `550 - 540 = 10` — this is a genuinely new, derived local value, not one of the record's own components, computed fresh inside the constructor body from two of the parameters together.
5. The final check, `actualDuration < minDurationMinutes`, evaluates `10 < 30`, which is true — so this check throws `IllegalArgumentException`, with a message directly reporting both the actual and required durations, immediately halting construction.
6. Because this exception propagates out of the compact constructor's body before it finishes normally, the compiler's automatically-appended field assignments (`this.startMinute = startMinute`, and so on for the other two components) never execute at all — no `TimeWindow` object is ever produced for these arguments, and the `catch` block in `main` receives and prints the exception's message, confirming that this multi-component, cross-parameter validation rule was enforced correctly and atomically as part of construction itself, exactly as the simpler single-parameter validation in the earlier examples was.

## 7. Gotchas & takeaways

> **Gotcha:** you cannot write `this.low = low;` (or any explicit field assignment) inside a compact constructor's body at all — doing so is a compile error, since the compiler already plans to append exactly those assignments itself; if you find yourself wanting to assign a field to something *other* than the (possibly-reassigned) parameter's final value — for instance, deriving one field's value from a completely different formula than "this same-named parameter, possibly adjusted" — you need the full, explicit-parameter-list canonical constructor form instead, which does require writing every assignment by hand.

- The compact canonical constructor omits the parameter list entirely, relying on the compiler to infer it exactly from the record's declared components — inside its body, you validate, throw, or reassign parameters, but never write explicit field assignments.
- The compiler appends the standard field assignments automatically, immediately after the compact body completes normally — if the body throws, no assignments happen and no object is constructed.
- Reassigning a parameter inside the compact body (for normalization, like swapping or trimming) changes what value ultimately gets assigned to the corresponding field, since the assignment uses whatever the parameter holds at the end of the body.
- The compact body has full, simultaneous access to every parameter, making it straightforward to express validation rules that depend on a relationship across multiple components together, not just a single parameter in isolation.
- Explicit field assignment inside a compact constructor's body is a compile error — if you need a field's value to diverge from "this parameter, possibly adjusted," you need the full, explicit-parameter-list constructor form instead.
- See [record components & canonical constructor](0954-record-components-canonical-constructor.md) for the broader canonical-constructor concept this compact form is a special syntax for, and [records & immutability](0958-records-immutability.md) for how these validation guarantees interact with a record's overall immutability contract.
