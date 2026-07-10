---
card: java
gi: 995
slug: composition-over-inheritance
title: Composition over inheritance
---

## 1. What it is

**Composition over inheritance** is the guideline that, when you want a class to reuse another class's behavior, prefer **holding a reference to it** (composition — "has-a") over **extending it** (inheritance — "is-a"). A `Car` that needs an engine's behavior should *have an* `Engine` field, not *be an* `Engine` subclass. Inheritance is a powerful tool, but it's also the tightest coupling two classes can have — a subclass depends on its parent's internal implementation details, not just its public contract, and that coupling is hard to undo later.

## 2. Why & when

Deep inheritance hierarchies tend to calcify: a change to a base class ripples through every subclass, and subclasses can't easily mix and match behaviors from unrelated hierarchies (Java classes only extend one class). Composition sidesteps both problems — a class can hold as many collaborator objects as it needs, each collaborator can be swapped independently at runtime, and there's no hidden coupling to a base class's internals.

Reach for inheritance only when there's a genuine, stable "is-a" relationship *and* the subclass will faithfully honor the full behavioral contract of the parent (see [SOLID — Liskov Substitution](0991-solid-liskov-substitution.md)). Reach for composition whenever you catch yourself wanting to reuse behavior from two unrelated sources, when the "is-a" relationship feels forced (a `Duck extends Bird` that can't fly, forcing an override), or when you want to swap a behavior at runtime rather than committing to it at compile time via a fixed class hierarchy.

## 3. Core concept

```
// Inheritance-heavy: forces every Duck subtype into the same fly() implementation,
// or forces an awkward override when a duck genuinely can't fly.
class Duck {
    void fly() { System.out.println("flying"); }
    void quack() { System.out.println("quack"); }
}
class RubberDuck extends Duck {
    @Override void fly() { /* can't fly -- awkward override */ }
}

// Composition: flying behavior is a separate, swappable collaborator
interface FlyBehavior { void fly(); }
class FlyWithWings implements FlyBehavior { public void fly() { System.out.println("flying"); } }
class CannotFly implements FlyBehavior { public void fly() { System.out.println("can't fly"); } }

class Duck {
    private final FlyBehavior flyBehavior; // Duck HAS-A FlyBehavior, isn't locked into one
    Duck(FlyBehavior flyBehavior) { this.flyBehavior = flyBehavior; }
    void fly() { flyBehavior.fly(); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Duck inheriting fly behavior it must override versus a Duck holding a swappable FlyBehavior collaborator">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Inheritance (is-a)</text>
  <rect x="40" y="40" width="200" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="140" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Duck { fly() }</text>
  <rect x="40" y="110" width="200" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="140" y="135" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">RubberDuck overrides fly()</text>
  <line x1="140" y1="80" x2="140" y2="110" stroke="#8b949e" marker-end="url(#a)"/>

  <text x="490" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Composition (has-a)</text>
  <rect x="400" y="70" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="460" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Duck</text>
  <rect x="540" y="40" width="90" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="585" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">FlyWithWings</text>
  <rect x="540" y="100" width="90" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="585" y="121" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">CannotFly</text>
  <line x1="520" y1="85" x2="540" y2="60" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="520" y1="95" x2="540" y2="115" stroke="#79c0ff" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`Duck` holds a `FlyBehavior` reference that can point at either implementation — no override, no forced inheritance of a behavior that doesn't fit.

## 5. Runnable example

Scenario: a duck simulation where different duck types fly and quack differently, evolving from a rigid inheritance hierarchy into composed, swappable behaviors — the classic example composition-over-inheritance is taught with.

### Level 1 — Basic

```java
// File: CompositionBasic.java
class Duck {
    void fly() { System.out.println("flying"); }
    void quack() { System.out.println("quack"); }
}

// Forced into an awkward override -- rubber ducks can't fly, but they still
// inherit fly() from Duck and must override it to avoid lying about behavior.
class RubberDuck extends Duck {
    @Override void fly() { System.out.println("can't fly, I'm rubber"); }
    @Override void quack() { System.out.println("squeak"); }
}

public class CompositionBasic {
    public static void main(String[] args) {
        Duck mallard = new Duck();
        Duck rubber = new RubberDuck();
        mallard.fly();
        rubber.fly();
    }
}
```

**How to run:** save as `CompositionBasic.java`, then `javac CompositionBasic.java && java CompositionBasic` (JDK 17+).

Expected output:
```
flying
can't fly, I'm rubber
```

Every new duck variant needs its own subclass overriding `fly()` and `quack()` — and there's no way to reuse, say, `RubberDuck`'s "can't fly" behavior for an unrelated `Penguin` class without duplicating it, since Java classes can only extend one parent.

### Level 2 — Intermediate

```java
// File: CompositionIntermediate.java
interface FlyBehavior { void fly(); }
class FlyWithWings implements FlyBehavior {
    public void fly() { System.out.println("flying"); }
}
class CannotFly implements FlyBehavior {
    public void fly() { System.out.println("can't fly"); }
}

class Duck {
    private final FlyBehavior flyBehavior;
    Duck(FlyBehavior flyBehavior) { this.flyBehavior = flyBehavior; }
    void fly() { flyBehavior.fly(); }
}

public class CompositionIntermediate {
    public static void main(String[] args) {
        Duck mallard = new Duck(new FlyWithWings());
        Duck rubber = new Duck(new CannotFly());
        mallard.fly();
        rubber.fly();
    }
}
```

**How to run:** save as `CompositionIntermediate.java`, then `javac CompositionIntermediate.java && java CompositionIntermediate` (JDK 17+).

Expected output:
```
flying
can't fly
```

The real-world concern added: there's only one `Duck` class now — behavior differences are captured by which `FlyBehavior` is composed in, not by a new subclass. `FlyWithWings` and `CannotFly` can also be reused by any other class that needs the same behavior, unrelated to ducks entirely.

### Level 3 — Advanced

```java
// File: CompositionAdvanced.java
interface FlyBehavior { void fly(); }
interface QuackBehavior { void quack(); }

class FlyWithWings implements FlyBehavior {
    public void fly() { System.out.println("flying"); }
}
class CannotFly implements FlyBehavior {
    public void fly() { System.out.println("can't fly"); }
}
class NormalQuack implements QuackBehavior {
    public void quack() { System.out.println("quack"); }
}
class Squeak implements QuackBehavior {
    public void quack() { System.out.println("squeak"); }
}

class Duck {
    private FlyBehavior flyBehavior;
    private QuackBehavior quackBehavior;

    Duck(FlyBehavior flyBehavior, QuackBehavior quackBehavior) {
        this.flyBehavior = flyBehavior;
        this.quackBehavior = quackBehavior;
    }

    void fly() { flyBehavior.fly(); }
    void quack() { quackBehavior.quack(); }

    // The real payoff of composition: behavior can be swapped at RUNTIME,
    // something an inheritance-based design (fixed at compile time) cannot do.
    void setFlyBehavior(FlyBehavior newBehavior) { this.flyBehavior = newBehavior; }
}

public class CompositionAdvanced {
    public static void main(String[] args) {
        Duck decoyDuck = new Duck(new CannotFly(), new Squeak());
        decoyDuck.fly();
        decoyDuck.quack();

        // A decoy duck gets "upgraded" with a wing-flapping mechanism at runtime --
        // no new subclass, no recompilation of Duck, just a swapped collaborator.
        decoyDuck.setFlyBehavior(new FlyWithWings());
        decoyDuck.fly();
    }
}
```

**How to run:** save as `CompositionAdvanced.java`, then `javac CompositionAdvanced.java && java CompositionAdvanced` (JDK 17+).

Expected output:
```
can't fly
squeak
flying
```

The production-flavored hard case: `setFlyBehavior` swaps the duck's flying behavior at runtime — something no inheritance hierarchy can do, since a subclass's behavior is fixed the moment the object is constructed. `Duck` itself never changed; only which `FlyBehavior` object it holds changed.

## 6. Walkthrough

Tracing `CompositionAdvanced.main` end to end:

1. `new Duck(new CannotFly(), new Squeak())` constructs a `Duck` holding references to a `CannotFly` and a `Squeak` instance — `Duck` itself has no flying or quacking logic of its own; it delegates both.
2. `decoyDuck.fly()` calls `flyBehavior.fly()`, which dispatches to `CannotFly.fly()`, printing `"can't fly"`.
3. `decoyDuck.quack()` calls `quackBehavior.quack()`, dispatching to `Squeak.quack()`, printing `"squeak"`.
4. `decoyDuck.setFlyBehavior(new FlyWithWings())` replaces the `flyBehavior` field's value with a new `FlyWithWings` instance — the `Duck` object itself is the same object throughout; only what it *holds* changed.
5. `decoyDuck.fly()` is called again, but this time `flyBehavior.fly()` dispatches to the newly-assigned `FlyWithWings.fly()`, printing `"flying"` — the exact same line of calling code (`flyBehavior.fly()`) produced a different result purely because of which object was composed in at that moment.
6. This demonstrates the core advantage over inheritance: reconfiguring behavior didn't require a new class, a recompilation, or even re-constructing the `Duck` — just swapping one collaborator reference.

## 7. Gotchas & takeaways

> **Gotcha:** composition isn't automatically superior in every case — a real, stable "is-a" relationship where the subtype genuinely satisfies the supertype's full contract (see [SOLID — Liskov Substitution](0991-solid-liskov-substitution.md)) is exactly what inheritance is for. The guideline is "prefer composition when in doubt," not "never use inheritance."

- Composition ("has-a", holding a reference) is looser coupling than inheritance ("is-a", sharing a base class's implementation details).
- The classic sign you need composition instead of inheritance: an override that exists purely to say "not for me" or "differently for me" — that's behavior that should have been a separate, swappable object all along.
- Composition allows mixing behaviors from multiple unrelated sources (a `Duck` composed of a `FlyBehavior` and a `QuackBehavior`), something single-inheritance Java classes can't do directly.
- The biggest practical advantage: composed behavior can be swapped at runtime; inherited behavior is fixed at compile time.
- Reserve inheritance for genuinely stable, narrow "is-a" hierarchies where every subtype can honestly satisfy the full parent contract.
- This is the same idea behind [dependency inversion](0993-solid-dependency-inversion.md): both favor depending on a swappable interface reference over a hard-wired concrete relationship.
