---
card: java
gi: 204
slug: field-initialization-order
title: Field initialization order
---

## 1. What it is

**Field initialization order** is the complete, precise sequence in which every piece of setup code for a class runs, bringing together everything covered in this series' recent topics: (1) fields default to `0`/`false`/`null`; (2) the superclass's *entire* construction (its own steps 1–4) completes first; (3) this class's field initializers and instance initializer blocks run together, strictly in the order they're written in the source, top to bottom; (4) this class's constructor body runs last. Static initialization (static fields and static blocks) is separate from all of this — it happens once, earlier, when the class is first loaded, before any instance-related steps happen at all.

```java
class Parent {
    static { System.out.println("A: Parent static block"); }      // once, class loading, earliest of all
    { System.out.println("C: Parent instance block"); }            // per-instance, before Parent's constructor
    Parent() { System.out.println("D: Parent constructor"); }
}

class Child extends Parent {
    static { System.out.println("B: Child static block"); }        // once, class loading
    { System.out.println("E: Child instance block"); }             // per-instance, before Child's constructor
    Child() { System.out.println("F: Child constructor"); }
}

new Child();
// prints, in this exact order: A, B, C, D, E, F
```

Both static blocks (`A` and `B`) run once, during class loading, *before* any instance is created at all — and even between the two, `Parent`'s static block runs before `Child`'s, since a subclass's class-loading also triggers its superclass's class-loading first, mirroring the same superclass-first rule that governs instance construction.

## 2. Why & when

Understanding the complete, combined order matters because real classes commonly mix several of these mechanisms together, and predicting the exact sequence of events is essential for reasoning correctly about a program's behaviour:

- **Debugging unexpected values** — if a field appears to be `null` or `0` somewhere it "shouldn't" be, tracing the exact initialization order pinpoints exactly which stage of construction hadn't happened yet at that point.
- **Static vs. instance separation** — static initialization happens once, ever, completely separately from (and before) any particular object's construction; conflating the two is a common source of confusion, especially when static fields reference instance-related concepts inappropriately.
- **Superclass-first, always** — no matter how deep an inheritance hierarchy goes, every ancestor's full construction (both static class-loading and instance construction) completes before the next class down the hierarchy begins its own, which is essential for reasoning about multi-level class hierarchies correctly.

You need this full mental model any time a bug's root cause might be about *when* something got its value — which, in any codebase using inheritance, static fields, and instance blocks together, is a genuinely common category of subtle bug.

## 3. Core concept

```java
class Base {
    static int staticCounter = incrementStatic(); // static field initializer
    int instanceCounter = incrementInstance();     // instance field initializer

    static int incrementStatic() {
        System.out.println("Base static field initializer");
        return 1;
    }

    int incrementInstance() {
        System.out.println("Base instance field initializer");
        return 1;
    }

    Base() {
        System.out.println("Base constructor");
    }
}

new Base();
new Base();
// FIRST new Base(): "Base static field initializer" THEN "Base instance field initializer" THEN "Base constructor"
// SECOND new Base(): only "Base instance field initializer" THEN "Base constructor" — static already ran
```

The static field initializer (`incrementStatic`) only prints on the *first* `new Base()` call, since static initialization happens once for the class; the instance field initializer (`incrementInstance`) prints on *every* call, since it's part of each individual object's own construction.

## 4. Diagram

<svg viewBox="0 0 600 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A complete ordered timeline: static initialization for the whole class hierarchy happens once at class loading, then for each new instance the superclass constructs fully first, then this class's field initializers and instance blocks run in source order, then this class's own constructor body runs last">
  <rect x="8" y="8" width="584" height="204" rx="8" fill="#0d1117"/>

  <rect x="20" y="25" width="560" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="47" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">STATIC init (once, whole hierarchy, class loading — superclass's static first)</text>

  <text x="300" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">↓ then, for EACH "new" call ↓</text>

  <rect x="20" y="95" width="170" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="117" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">superclass full construct</text>

  <rect x="210" y="95" width="170" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="295" y="117" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">field inits + instance blocks</text>

  <rect x="400" y="95" width="170" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="117" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">this class's constructor</text>

  <line x1="190" y1="112" x2="210" y2="112" stroke="#8b949e" marker-end="url(#fo)"/>
  <line x1="380" y1="112" x2="400" y2="112" stroke="#8b949e" marker-end="url(#fo)"/>
  <defs><marker id="fo" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>

  <text x="300" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Static init happens ONCE, ever. Everything else repeats for EVERY "new" call.</text>
  <text x="300" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Field initializers and instance blocks interleave in exact source order, top to bottom.</text>
</svg>

Static initialization happens once for the whole class hierarchy; everything else repeats for every new instance, superclass-first.

## 5. Runnable example

Scenario: tracing the complete initialization sequence of a small `Vehicle`/`ElectricCar` hierarchy, combining static fields, instance fields, instance blocks, and constructors — starting with a basic single-class trace, then extending to two classes, then hardening into a full trace exercising every mechanism together across two instances.

### Level 1 — Basic

```java
public class OrderBasic {
    static class Vehicle {
        int wheels = 4;                       // 1. field initializer
        { System.out.println("Vehicle instance block, wheels=" + wheels); } // 2. instance block
        Vehicle() { System.out.println("Vehicle constructor"); }            // 3. constructor body
    }

    public static void main(String[] args) {
        new Vehicle();
    }
}
```

**How to run:** `java OrderBasic.java`

The output prints `"Vehicle instance block, wheels=4"` then `"Vehicle constructor"` — the instance block runs after the field initializer just above it (`wheels` is already `4` by the time the block reads it) and before the constructor body, exactly matching the fixed order this topic describes.

### Level 2 — Intermediate

Same idea, now with a `Vehicle`/`ElectricCar` hierarchy, demonstrating the superclass-first rule combined with each class's own field-initializer-then-block-then-constructor sequence.

```java
public class OrderIntermediate {
    static class Vehicle {
        int wheels = 4;
        { System.out.println("Vehicle instance block"); }
        Vehicle() { System.out.println("Vehicle constructor"); }
    }

    static class ElectricCar extends Vehicle {
        int batteryKwh = 75;
        { System.out.println("ElectricCar instance block, batteryKwh=" + batteryKwh); }
        ElectricCar() { System.out.println("ElectricCar constructor"); }
    }

    public static void main(String[] args) {
        new ElectricCar();
    }
}
```

**How to run:** `java OrderIntermediate.java`

The four lines print in this order: `"Vehicle instance block"`, `"Vehicle constructor"`, `"ElectricCar instance block, batteryKwh=75"`, `"ElectricCar constructor"` — `Vehicle`'s entire construction (its own field initializer, instance block, and constructor) completes fully before `ElectricCar`'s own field initializer even begins.

### Level 3 — Advanced

Same hierarchy, now with static fields and static blocks added at both levels, and two separate instances created, demonstrating the complete combined order: static initialization once for the whole hierarchy, then full per-instance construction (superclass-first) for each of the two `new` calls.

```java
public class OrderAdvanced {
    static class Vehicle {
        static int vehicleCount = announceStatic();
        static int announceStatic() {
            System.out.println("STATIC: Vehicle static field initializer");
            return 0;
        }

        int wheels = 4;
        { System.out.println("Vehicle instance block"); }
        Vehicle() {
            vehicleCount++;
            System.out.println("Vehicle constructor, vehicleCount=" + vehicleCount);
        }
    }

    static class ElectricCar extends Vehicle {
        static int carModelYear = announceCarStatic();
        static int announceCarStatic() {
            System.out.println("STATIC: ElectricCar static field initializer");
            return 2024;
        }

        int batteryKwh = 75;
        { System.out.println("ElectricCar instance block"); }
        ElectricCar() {
            System.out.println("ElectricCar constructor, modelYear=" + carModelYear);
        }
    }

    public static void main(String[] args) {
        System.out.println("--- creating first ElectricCar ---");
        new ElectricCar();
        System.out.println("--- creating second ElectricCar ---");
        new ElectricCar();
    }
}
```

**How to run:** `java OrderAdvanced.java`

Both `"STATIC: ..."` lines print exactly once, entirely before either `"--- creating ... ElectricCar ---"` message — because referencing `ElectricCar` (even just to call `new` on it) triggers class loading for both `ElectricCar` and its superclass `Vehicle` immediately, and static initialization for the whole hierarchy completes before the very first instance is constructed; everything else (`Vehicle instance block`, `Vehicle constructor`, `ElectricCar instance block`, `ElectricCar constructor`) then repeats in full for each of the two separate `new ElectricCar()` calls.

## 6. Walkthrough

Trace `OrderAdvanced.main` completely, from the very first line:

**Class loading (once, before `main`'s first real statement about `ElectricCar` executes any construction).** Referencing `ElectricCar` for the first time (`new ElectricCar()`) triggers loading of `ElectricCar`, which first requires loading its superclass, `Vehicle`. `Vehicle`'s static field initializer runs: `"STATIC: Vehicle static field initializer"` prints; `vehicleCount = 0`. Then `ElectricCar`'s own static field initializer runs: `"STATIC: ElectricCar static field initializer"` prints; `carModelYear = 2024`. This entire static phase happens exactly once, regardless of the two `new ElectricCar()` calls to come.

**First `new ElectricCar()`.** `Vehicle`'s instance construction runs first: field initializer `wheels = 4`, then the instance block prints `"Vehicle instance block"`, then the `Vehicle()` constructor body runs — `vehicleCount++` makes it `1`, prints `"Vehicle constructor, vehicleCount=1"`. Only now does `ElectricCar`'s own instance construction begin: field initializer `batteryKwh = 75`, then its instance block prints `"ElectricCar instance block"`, then `ElectricCar()`'s constructor body prints `"ElectricCar constructor, modelYear=2024"`.

**Second `new ElectricCar()`.** The static phase does **not** repeat. Instance construction runs fresh again: `Vehicle`'s field initializer, instance block (`"Vehicle instance block"` again), constructor (`vehicleCount++` makes it `2`, prints `"...vehicleCount=2"`), then `ElectricCar`'s field initializer, instance block, and constructor (`"...modelYear=2024"` again, since `carModelYear` is a static field, unchanged since it was set once).

```
class loading (once):
  STATIC: Vehicle static field initializer     -> vehicleCount = 0
  STATIC: ElectricCar static field initializer -> carModelYear = 2024

--- creating first ElectricCar ---
  Vehicle instance block
  Vehicle constructor, vehicleCount=1
  ElectricCar instance block
  ElectricCar constructor, modelYear=2024

--- creating second ElectricCar ---
  Vehicle instance block
  Vehicle constructor, vehicleCount=2
  ElectricCar instance block
  ElectricCar constructor, modelYear=2024
```

**Final output.** Exactly matches the trace above, ten lines total in that precise order — the two `"STATIC: ..."` lines appearing only once, right at the top, before either `"--- creating ..."` message, with `vehicleCount` correctly incrementing across both instances while `carModelYear` stays fixed at its one-time-initialized value.

## 7. Gotchas & takeaways

> **Static initialization for an entire class hierarchy happens once, triggered by the very first meaningful reference to the most-derived class — and it always completes fully before the first instance's construction begins.** This means a superclass's static block can run as a side effect of merely loading a subclass, even if the superclass is never used directly anywhere else in the program.

> **Mixing static and instance concerns in the same class, without clearly separating them, is a common source of confusing bugs** — a static field incremented inside an instance constructor (like `vehicleCount++` above) is a legitimate, common pattern (counting total instances), but it's easy to lose track of which fields are "once, ever" versus "fresh, every time" without carefully tracing the actual initialization order.

- Static initialization (static fields, static blocks) happens once per class hierarchy, at class loading, before any instance construction.
- Instance construction always proceeds superclass-first: the entire superclass construction finishes before the subclass's own field initializers begin.
- Within one class, field initializers and instance blocks run together in exact source order, followed by that class's constructor body.
- Static state persists and accumulates across every instance (like a shared counter); instance state (fields, blocks) is rebuilt fresh for every single `new` call.
