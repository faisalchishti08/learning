---
card: java
gi: 531
slug: diamond-problem-resolution
title: Diamond problem resolution
---

## 1. What it is

The **diamond problem** occurs when a class implements two interfaces that both provide a `default` method with the *same signature* — the compiler can't automatically decide which default implementation the class should inherit, so it refuses to compile until the ambiguity is resolved explicitly. Java resolves this by requiring the implementing class to **override** the conflicting method itself, optionally calling a specific parent interface's version using the syntax `InterfaceName.super.methodName(...)`.

## 2. Why & when

Before default methods existed, this conflict was impossible — interfaces had no method bodies to conflict over. Once interfaces could carry actual implementations, two unrelated interfaces could each define a method with the same name and signature but different bodies, and a class implementing both would inherit two competing definitions — an ambiguity the compiler cannot silently resolve on your behalf, since guessing wrong could produce silently incorrect behavior. Java's rule is simple and safe: if a class inherits two conflicting default method implementations, the class **must** explicitly override that method, choosing (or combining) the behavior itself.

## 3. Core concept

```java
interface Flyer {
    default String move() { return "flying"; }
}

interface Swimmer {
    default String move() { return "swimming"; }
}

// class Duck implements Flyer, Swimmer {} // WOULD NOT COMPILE -- ambiguous move()

class Duck implements Flyer, Swimmer {
    @Override
    public String move() {
        return Flyer.super.move() + " and " + Swimmer.super.move(); // explicitly choose/combine both
    }
}

System.out.println(new Duck().move()); // "flying and swimming"
```

`Duck` must override `move()` explicitly, and can reach each parent interface's specific default implementation via `InterfaceName.super.methodName(...)` — a syntax that only makes sense in exactly this diamond-resolution context.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a class implementing two interfaces with conflicting default methods must override the method itself">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="80" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="170" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Flyer.move() = "flying"</text>
  <rect x="380" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="470" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Swimmer.move() = "swimming"</text>
  <line x1="170" y1="60" x2="300" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="470" y1="60" x2="340" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <rect x="230" y="105" width="180" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="125" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">class Duck implements both</text>
  <text x="320" y="140" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">MUST override move() explicitly</text>
</svg>

`Duck` sits at the "diamond point" where two conflicting `move()` defaults converge — the compiler forces an explicit resolution rather than guessing.

## 5. Runnable example

Scenario: modeling a class that combines two independent capabilities with overlapping method names — evolved from triggering the diamond-problem compile error conceptually, through resolving it by picking one specific parent's behavior, to a version that combines both parents' behavior using `InterfaceName.super`.

### Level 1 — Basic

```java
public class DiamondCompileError {
    interface Flyer {
        default String move() { return "flying through the air"; }
    }

    interface Swimmer {
        default String move() { return "swimming through water"; }
    }

    // This WOULD NOT COMPILE if left as-is:
    // static class Duck implements Flyer, Swimmer {}
    // Error: "class Duck inherits unrelated defaults for move() from types Flyer and Swimmer"

    // The fix: override move() explicitly, even just to pick one.
    static class Duck implements Flyer, Swimmer {
        @Override
        public String move() {
            return "waddling"; // Duck defines its own behavior entirely, ignoring both parents
        }
    }

    public static void main(String[] args) {
        Duck duck = new Duck();
        System.out.println("Duck moves by: " + duck.move());
    }
}
```

**How to run:** `java DiamondCompileError.java`

Expected output:
```
Duck moves by: waddling
```

Without the `@Override public String move() { return "waddling"; }`, this class would fail to compile, since `Duck` would inherit two conflicting `move()` implementations from `Flyer` and `Swimmer` with no way for the compiler to pick between them. Providing `Duck`'s own override resolves the ambiguity completely — `Duck`'s `move()` simply doesn't call either parent's version at all here.

### Level 2 — Intermediate

```java
public class DiamondPickOne {
    interface Flyer {
        default String move() { return "flying through the air"; }
    }

    interface Swimmer {
        default String move() { return "swimming through water"; }
    }

    static class FlyingFish implements Flyer, Swimmer {
        @Override
        public String move() {
            // Explicitly choose Flyer's specific default implementation.
            return Flyer.super.move();
        }
    }

    public static void main(String[] args) {
        FlyingFish fish = new FlyingFish();
        System.out.println("Flying fish moves by: " + fish.move());
    }
}
```

**How to run:** `java DiamondPickOne.java`

Expected output:
```
Flying fish moves by: flying through the air
```

The real-world concern this adds: `FlyingFish.move()` doesn't write entirely new behavior from scratch — it explicitly delegates to `Flyer`'s specific default implementation via `Flyer.super.move()`, reusing that logic rather than duplicating it. This `InterfaceName.super.methodName(...)` syntax only exists for exactly this scenario: naming which parent interface's default implementation you want to call from within an overriding method.

### Level 3 — Advanced

```java
public class DiamondCombineBoth {
    interface Flyer {
        default String move() { return "flying through the air"; }
    }

    interface Swimmer {
        default String move() { return "swimming through water"; }
    }

    static class Duck implements Flyer, Swimmer {
        @Override
        public String move() {
            // Combine BOTH parents' behavior into one result, rather than picking just one.
            return Flyer.super.move() + ", then " + Swimmer.super.move();
        }
    }

    static class Penguin implements Flyer, Swimmer {
        @Override
        public String move() {
            // Penguins can't actually fly -- override entirely with custom logic, ignoring both parents.
            return "waddling on land, or " + Swimmer.super.move();
        }
    }

    public static void main(String[] args) {
        Duck duck = new Duck();
        Penguin penguin = new Penguin();

        System.out.println("Duck: " + duck.move());
        System.out.println("Penguin: " + penguin.move());
    }
}
```

**How to run:** `java DiamondCombineBoth.java`

Expected output:
```
Duck: flying through the air, then swimming through water
Penguin: waddling on land, or swimming through water
```

This shows two different resolution strategies for the same diamond conflict: `Duck` combines *both* parents' default behavior into one composite result (`Flyer.super.move()` and `Swimmer.super.move()`, joined together), while `Penguin` uses only `Swimmer.super.move()` and supplies entirely custom logic for the rest — since a penguin genuinely can't fly, blindly combining both parents' behavior wouldn't make biological sense, demonstrating that the resolution strategy should reflect the actual semantics of the specific implementing class, not follow one universal pattern.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `duck` and `penguin` are both created, each implementing both `Flyer` and `Swimmer`.

`duck.move()` invokes `Duck`'s overridden `move()` method. Inside it, `Flyer.super.move()` is evaluated first: this syntax specifically calls `Flyer`'s own default implementation of `move()`, bypassing any override — it returns `"flying through the air"`. Next, `Swimmer.super.move()` is evaluated: this calls `Swimmer`'s own default implementation, returning `"swimming through water"`. These two strings are concatenated with `", then "` in between: `"flying through the air" + ", then " + "swimming through water"` = `"flying through the air, then swimming through water"`.

`penguin.move()` invokes `Penguin`'s overridden `move()` method. Here, `Flyer`'s default is never called at all — the method starts with the literal string `"waddling on land, or "`, then calls `Swimmer.super.move()`, which returns `"swimming through water"`, concatenated onto the literal prefix: `"waddling on land, or " + "swimming through water"` = `"waddling on land, or swimming through water"`.

```
Duck.move():
  Flyer.super.move()   -> "flying through the air"    (Flyer's own default, explicitly named)
  Swimmer.super.move() -> "swimming through water"    (Swimmer's own default, explicitly named)
  combined: "flying through the air" + ", then " + "swimming through water"

Penguin.move():
  (Flyer's default is never invoked at all)
  Swimmer.super.move() -> "swimming through water"
  combined: "waddling on land, or " + "swimming through water"
```

`main` prints `"Duck: flying through the air, then swimming through water"` and `"Penguin: waddling on land, or swimming through water"` — both classes resolve the exact same underlying diamond conflict (two default `move()` methods from `Flyer` and `Swimmer`), but each chooses a different, semantically appropriate way to do so.

## 7. Gotchas & takeaways

> `InterfaceName.super.methodName(...)` is a special syntax that only compiles inside a class that directly implements `InterfaceName` and is *overriding* the conflicting method — it cannot be used from arbitrary code, and it specifically bypasses any override to reach that particular parent interface's own default implementation. Confusing this with regular `super.methodName(...)` (used for calling a superclass's method, not an interface's default) is a common early mistake — the two serve related but distinct purposes and use different syntax specifically because interfaces (plural, potentially) are different from a single superclass.

- The diamond problem occurs when a class implements two interfaces with conflicting `default` methods of the same signature — Java refuses to compile until the class explicitly overrides the method.
- The fix is always the same shape: override the conflicting method in the implementing class, choosing what its behavior should be.
- `InterfaceName.super.methodName(...)` lets the overriding method call a *specific* parent interface's own default implementation, rather than writing entirely new logic from scratch.
- The override can pick one parent's behavior, combine both, or ignore both entirely and write custom logic — the "right" resolution depends on the actual semantics of the implementing class, not a fixed rule.
- This conflict only arises between two *default* methods — if only one of the two interfaces provides a default (the other leaves the method abstract), there's no ambiguity, and the implementing class simply inherits the one available default without needing to override anything.
