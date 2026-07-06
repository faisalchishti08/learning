---
card: java
gi: 196
slug: object-lifecycle-creation-order
title: Object lifecycle & creation order
---

## 1. What it is

An object's **lifecycle** is the sequence of steps the JVM performs when `new` creates an instance, in a fixed, well-defined order: (1) memory is allocated and every field is set to its default value (`0`, `false`, `null`); (2) field initializers and instance initializer blocks run, top to bottom, in the order they appear in the source; (3) the constructor's body runs, though if the class has a superclass, the superclass's own construction (steps 1–3 for it) completes *first*, before this class's field initializers or constructor body run at all.

```java
class Base {
    Base() { System.out.println("Base constructor"); }
}

class Derived extends Base {
    int x = printAndReturn(); // field initializer

    static int printAndReturn() {
        System.out.println("Derived field initializer");
        return 5;
    }

    Derived() {
        System.out.println("Derived constructor");
    }
}

new Derived();
// prints, in order:
// Base constructor
// Derived field initializer
// Derived constructor
```

The superclass's constructor runs to completion *before* `Derived`'s own field initializers execute — this ordering guarantees that anything the superclass sets up is fully in place before the subclass begins initializing its own state.

## 2. Why & when

Understanding this precise order matters whenever a class's fields depend on values that might be affected by inheritance, or when field initializers themselves call methods that could theoretically be overridden:

- **Predictable state before use** — knowing exactly when each field gets its real (non-default) value is essential for reasoning about what a constructor, or any initializer, can safely rely on being already set up.
- **Superclass-first construction** — since `Base` always finishes constructing before `Derived` begins its own field initialization, a subclass can trust that any state the superclass establishes is already valid by the time its own fields start initializing.
- **This becomes especially important with inheritance** (a later topic) — calling an overridable method from a superclass constructor is a well-known hazard, precisely because the subclass's own field initializers haven't run yet at that point, so an overridden method might read fields that are still at their Java defaults.

You need this mental model any time initialization order could plausibly matter — most commonly, when one field's initializer depends on another field, or when a class hierarchy is involved and you need to reason about exactly what's already set up at each stage.

## 3. Core concept

```java
class Widget {
    int a = 1;
    int b = a + 1; // relies on 'a' already being initialized — fields initialize top-to-bottom, in source order

    Widget() {
        System.out.println("a=" + a + ", b=" + b); // both already set by the time the constructor body runs
    }
}

new Widget(); // prints: a=1, b=2
```

Field initializers run strictly in the **order they appear in the source file**, from top to bottom — `b`'s initializer (`a + 1`) works correctly here specifically because `a`'s initializer runs first; if the declarations were reversed (`b` declared before `a`), this would either use `a`'s still-default value of `0` or fail to compile, depending on the exact expression.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline of object construction showing four ordered stages: allocate and default all fields, run superclass construction fully, run this class's field initializers top to bottom in source order, then run this class's constructor body">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Object construction order, always in this sequence</text>

  <rect x="20" y="45" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">1. allocate, default all fields</text>

  <rect x="170" y="45" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="235" y="70" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">2. superclass construction (full)</text>

  <rect x="320" y="45" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="385" y="70" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">3. this class's field initializers</text>

  <rect x="470" y="45" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">4. constructor body</text>

  <line x1="150" y1="65" x2="170" y2="65" stroke="#8b949e" marker-end="url(#s)"/>
  <line x1="300" y1="65" x2="320" y2="65" stroke="#8b949e" marker-end="url(#s)"/>
  <line x1="450" y1="65" x2="470" y2="65" stroke="#8b949e" marker-end="url(#s)"/>
  <defs><marker id="s" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>

  <text x="300" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Field initializers within one class run top-to-bottom, in the exact order they're declared.</text>
  <text x="300" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The superclass's ENTIRE construction (stages 1-4 for it) completes before stage 3 of the subclass begins.</text>
</svg>

Superclass construction always finishes completely before a subclass's own field initializers run.

## 5. Runnable example

Scenario: tracing initialization order in a small `Vehicle`/`Car` hierarchy — starting with a basic single-class trace, then extending to two classes with inheritance, then hardening into a case demonstrating exactly why calling an overridable method from a superclass constructor is dangerous.

### Level 1 — Basic

```java
public class LifecycleBasic {
    static class Vehicle {
        int wheels = 4;
        String label = "wheels=" + wheels; // depends on 'wheels', declared above it

        Vehicle() {
            System.out.println(label);
        }
    }

    public static void main(String[] args) {
        new Vehicle();
    }
}
```

**How to run:** `java LifecycleBasic.java`

`label`'s initializer runs *after* `wheels`'s, since it's declared second in the source — by the time `label = "wheels=" + wheels` executes, `wheels` already holds `4`, so `label` correctly becomes `"wheels=4"`, printed by the constructor.

### Level 2 — Intermediate

Same idea, now with a `Car` subclass, demonstrating that `Vehicle`'s entire construction finishes before `Car`'s own field initializers or constructor body begin.

```java
public class LifecycleIntermediate {
    static class Vehicle {
        Vehicle() {
            System.out.println("1. Vehicle constructor runs");
        }
    }

    static class Car extends Vehicle {
        int doors = printAndReturn();

        static int printAndReturn() {
            System.out.println("2. Car field initializer runs");
            return 4;
        }

        Car() {
            System.out.println("3. Car constructor runs");
        }
    }

    public static void main(String[] args) {
        new Car();
    }
}
```

**How to run:** `java LifecycleIntermediate.java`

The output prints in the exact numbered order shown in the code comments — `Vehicle`'s constructor (implicitly called first, before any of `Car`'s own initialization) always completes before `Car`'s field initializer runs, which in turn always completes before `Car`'s own constructor body executes.

### Level 3 — Advanced

Same hierarchy, now demonstrating the classic hazard: a superclass constructor that calls an overridable method, which a subclass overrides and relies on a field that hasn't been initialized yet at that point in the sequence.

```java
public class LifecycleAdvanced {
    static class Vehicle {
        Vehicle() {
            System.out.println("Vehicle constructor calling describe()...");
            describe(); // calling an overridable method from the superclass constructor — risky!
        }

        void describe() {
            System.out.println("Generic vehicle");
        }
    }

    static class Car extends Vehicle {
        String model = "Sedan"; // NOT YET initialized when Vehicle's constructor calls describe()

        @Override
        void describe() {
            System.out.println("Car model: " + model); // reads model BEFORE Car's field initializer has run
        }
    }

    public static void main(String[] args) {
        new Car();
    }
}
```

**How to run:** `java LifecycleAdvanced.java`

Because `Vehicle`'s constructor runs completely *before* `Car`'s field initializers, the call to `describe()` — even though it's overridden by `Car` — executes while `model` is still at its default value, `null`, not yet `"Sedan"`; the output demonstrates this surprising gap directly, printing `"Car model: null"` even though the field's declared initial value is `"Sedan"`.

## 6. Walkthrough

Trace `new Car()` from `LifecycleAdvanced.main` step by step:

**Step 1 — allocation.** Memory for the `Car` object is allocated; all fields (including the inherited absence of any `Vehicle` fields here, and `Car`'s own `model`) default to `null`/`0`/`false`. `model` is `null` at this point.

**Step 2 — superclass construction.** Since `Car extends Vehicle`, `Vehicle`'s constructor runs *first*, in full, before anything belonging to `Car` initializes. Inside `Vehicle()`, `"Vehicle constructor calling describe()..."` prints, then `describe()` is called.

**Step 3 — dynamic dispatch to the override.** Even though this call originates inside `Vehicle`'s constructor, Java's dynamic method dispatch (covered in later inheritance topics) means the *actual* object is a `Car`, so `Car`'s overridden `describe()` runs, not `Vehicle`'s. Inside `Car.describe()`, `System.out.println("Car model: " + model)` reads `model` — but `Car`'s field initializers haven't run yet, since we're still inside step 2 (`Vehicle`'s construction). `model` is still `null`. Prints `"Car model: null"`.

**Step 4 — `Vehicle`'s constructor finishes.** Control returns from `describe()` back into `Vehicle()`'s constructor body, which has nothing left to do, so it completes.

**Step 5 — `Car`'s field initializers, finally.** *Now*, `Car`'s own field initializer runs: `model = "Sedan"`.

**Step 6 — `Car`'s constructor body.** `Car` has no explicit constructor written, so the compiler-generated implicit one (with no body of its own) runs, doing nothing further.

```
new Car()
  1. allocate; model = null (default)
  2. Vehicle() runs:
       print "Vehicle constructor calling describe()..."
       describe() dispatches to Car.describe() (dynamic dispatch)
         prints "Car model: " + model   -> model is still null here!
       Vehicle() finishes
  3. Car's field initializer runs: model = "Sedan"   (too late for the describe() call above)
  4. Car's (implicit) constructor body runs: nothing further
```

**Final output.** Two lines: `"Vehicle constructor calling describe()..."` then `"Car model: null"` — the surprising `null` is the direct, demonstrable consequence of the fixed construction order: superclass construction (including any methods it calls) always completes before a subclass's own fields are initialized.

## 7. Gotchas & takeaways

> **Calling an overridable (non-`private`, non-`final`, non-`static`) method from a constructor is a well-known hazard specifically because of this ordering** — if a subclass overrides that method and the override relies on the subclass's own fields, those fields are guaranteed not to be initialized yet at the time the superclass constructor makes the call. The safe fix is to avoid calling overridable methods from constructors, or to make the called method `final` (preventing override) if it must be called during construction.

> **Field initializers run in the exact order they're written in the source, top to bottom, within one class** — reordering field declarations can silently change behaviour if one initializer depends on another's value being already set, since Java does not analyze dependencies between initializers; it purely follows declaration order.

- Object construction always follows a fixed order: allocate and default every field, complete the superclass's own full construction, run this class's field initializers top-to-bottom, then run this class's constructor body.
- A subclass's fields are still at their Java default values throughout the entire time the superclass's constructor is running.
- Calling an overridable method from a constructor risks that method (if overridden) reading not-yet-initialized subclass fields.
- Field initializer order within a single class always matches source declaration order — a later initializer can safely depend on an earlier one, never the reverse.
