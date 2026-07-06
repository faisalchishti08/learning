---
card: java
gi: 225
slug: dynamic-method-dispatch-virtual-methods
title: Dynamic method dispatch (virtual methods)
---

## 1. What it is

**Dynamic method dispatch** is the mechanism by which Java decides, **at runtime**, which actual method implementation to run when an overridden method is called — the decision is based on the object's real, runtime type, never the reference variable's declared (compile-time) type. Every non-`static`, non-`private`, non-`final` method in Java is "virtual" by default, meaning it automatically participates in this dynamic dispatch; this is precisely why calling an overridden method through a supertype-typed reference still correctly runs the subclass's own version.

```java
class Animal {
    String makeSound() { return "..."; }
}

class Dog extends Animal {
    @Override
    String makeSound() { return "Woof"; }
}

class Cat extends Animal {
    @Override
    String makeSound() { return "Meow"; }
}

Animal a = getRandomAnimal(); // returns either a Dog or a Cat, decided at RUNTIME
System.out.println(a.makeSound()); // "Woof" or "Meow" — decided by the ACTUAL object, not by 'a's declared type
```

`a`'s declared type is `Animal`, fixed at compile time — but which `makeSound()` implementation actually runs is decided fresh, every single time the call executes, based purely on what `a` genuinely refers to at that moment; the compiler cannot know this in advance if the actual object is only determined at runtime (as with `getRandomAnimal()` here).

## 2. Why & when

Dynamic dispatch is the mechanism that makes polymorphism actually work — it's what allows code written against a general supertype to automatically produce the *correct*, type-specific behaviour for whatever concrete object it's actually handed:

- **Polymorphic collections and parameters** — a `List<Animal>` holding a mix of `Dog`s and `Cat`s, iterated with a call to `.makeSound()` on each, automatically runs each element's own correct override — this is only possible because the method call is resolved dynamically, per-object, at runtime.
- **Extensibility without modifying existing code** — adding a new `Animal` subclass (say, `Bird`) with its own `makeSound()` override doesn't require changing any code that already calls `.makeSound()` on `Animal` references — the dispatch mechanism automatically picks up the new override wherever a `Bird` object happens to be used.
- **Contrast with field access and static methods** — as covered in earlier topics, field access and `static` method calls do *not* use dynamic dispatch; they're resolved at compile time based on the reference's declared type, which is precisely why field hiding behaves so differently (and more confusingly) than method overriding.

You rely on dynamic dispatch every time you call a non-`static`, overridden method through a supertype reference — it happens automatically, without any special syntax, and is the fundamental mechanism underlying essentially all practical uses of inheritance and polymorphism in Java.

## 3. Core concept

```java
class Shape {
    double area() { return 0.0; }
}

class Circle extends Shape {
    double radius;
    Circle(double radius) { this.radius = radius; }
    @Override
    double area() { return Math.PI * radius * radius; }
}

class Square extends Shape {
    double side;
    Square(double side) { this.side = side; }
    @Override
    double area() { return side * side; }
}

Shape[] shapes = { new Circle(2), new Square(3) };
for (Shape s : shapes) {
    System.out.println(s.area()); // dispatch decided per-element, based on each object's ACTUAL type
}
```

Both array elements are accessed through the exact same `Shape`-typed loop variable `s`, yet `s.area()` produces a different, correct result for each iteration — `12.566...` for the `Circle`, `9.0` for the `Square` — because each call to `.area()` is dispatched fresh, based on whichever specific object `s` actually refers to during that particular iteration.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single loop variable typed as Shape calling area on each iteration, with the JVM inspecting each object's actual runtime type at the moment of the call and dispatching to Circle's area implementation for one element and Square's for the other">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">for (Shape s : shapes) { s.area(); }</text>

  <rect x="60" y="45" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="67" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">s -&gt; Circle(radius=2)</text>

  <line x1="150" y1="80" x2="150" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#dd)"/>
  <text x="150" y="115" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">runs Circle.area() -&gt; 12.57</text>

  <rect x="360" y="45" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="67" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">s -&gt; Square(side=3)</text>

  <line x1="450" y1="80" x2="450" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#dd)"/>
  <text x="450" y="115" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">runs Square.area() -&gt; 9.0</text>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same call site, same declared type — dispatch decided fresh per object, at runtime.</text>

  <defs><marker id="dd" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The exact same call site dispatches to different implementations, decided by each object's actual runtime type.

## 5. Runnable example

Scenario: a small game with different enemy types sharing a common attack behaviour — starting with basic dynamic dispatch across two subclasses, then extending to a mixed collection processed uniformly, then hardening into a case demonstrating dispatch continuing to work correctly even when an object is passed through several layers of generic code.

### Level 1 — Basic

```java
public class DispatchBasic {
    static class Enemy {
        String attack() { return "Generic attack"; }
    }

    static class Goblin extends Enemy {
        @Override
        String attack() { return "Goblin slashes with a dagger"; }
    }

    static class Dragon extends Enemy {
        @Override
        String attack() { return "Dragon breathes fire"; }
    }

    public static void main(String[] args) {
        Enemy e1 = new Goblin();
        Enemy e2 = new Dragon();

        System.out.println(e1.attack()); // dispatches to Goblin's version
        System.out.println(e2.attack()); // dispatches to Dragon's version
    }
}
```

**How to run:** `java DispatchBasic.java`

Both `e1` and `e2` are declared as `Enemy`, yet `.attack()` correctly produces each subclass's own distinct message — dynamic dispatch resolves the call based on each variable's actual referenced object, not its shared declared type.

### Level 2 — Intermediate

Same game, now with a mixed array of enemy types processed uniformly in a single loop.

```java
public class DispatchIntermediate {
    static class Enemy {
        String attack() { return "Generic attack"; }
    }

    static class Goblin extends Enemy {
        @Override
        String attack() { return "Goblin slashes with a dagger"; }
    }

    static class Dragon extends Enemy {
        @Override
        String attack() { return "Dragon breathes fire"; }
    }

    static class Skeleton extends Enemy {
        @Override
        String attack() { return "Skeleton rattles and swings a bone club"; }
    }

    public static void main(String[] args) {
        Enemy[] enemies = { new Goblin(), new Dragon(), new Skeleton(), new Goblin() };

        for (Enemy e : enemies) {
            System.out.println(e.attack());
        }
    }
}
```

**How to run:** `java DispatchIntermediate.java`

One loop, one call site (`e.attack()`), yet four different results — each correctly determined by that specific iteration's actual object, demonstrating dynamic dispatch scaling naturally to any number and mix of subclasses without the loop code needing any special handling per type.

### Level 3 — Advanced

Same game, now passing enemies through a generic "battle" method that itself has no idea which specific subclasses exist, demonstrating that dynamic dispatch continues working correctly even several layers of indirection away from where the objects were originally created.

```java
import java.util.List;

public class DispatchAdvanced {
    static class Enemy {
        String name;
        Enemy(String name) { this.name = name; }
        String attack() { return name + " performs a generic attack"; }
    }

    static class Goblin extends Enemy {
        Goblin() { super("Goblin"); }
        @Override
        String attack() { return name + " slashes with a dagger"; }
    }

    static class Dragon extends Enemy {
        Dragon() { super("Dragon"); }
        @Override
        String attack() { return name + " breathes fire"; }
    }

    static void runBattleRound(List<Enemy> combatants) { // has NO idea which specific subclasses exist
        for (Enemy e : combatants) {
            System.out.println(e.attack()); // still dispatches correctly, however deep this call is
        }
    }

    public static void main(String[] args) {
        List<Enemy> combatants = List.of(new Goblin(), new Dragon(), new Goblin());
        runBattleRound(combatants);
    }
}
```

**How to run:** `java DispatchAdvanced.java`

`runBattleRound` is written entirely in terms of the general `Enemy` type — it was written *before* (conceptually) any specific subclass even existed, and would continue working correctly even if a brand-new `Enemy` subclass were added later, since dynamic dispatch resolves `e.attack()` based on each object's actual type at the moment the loop runs, completely independent of what `runBattleRound`'s own code knows about.

## 6. Walkthrough

Trace `runBattleRound(combatants)` from `DispatchAdvanced.main`, where `combatants = [Goblin, Dragon, Goblin]`:

**First iteration.** `e` refers to the first `Goblin` object. `e.attack()` — the JVM looks at `e`'s *actual* runtime type (`Goblin`), finds its most specific `attack()` override, and runs it: `name + " slashes with a dagger"` where `name = "Goblin"` (set via `super("Goblin")` in the constructor), producing `"Goblin slashes with a dagger"`.

**Second iteration.** `e` refers to the `Dragon` object. `e.attack()` dispatches to `Dragon`'s override: `"Dragon breathes fire"`.

**Third iteration.** `e` refers to the second `Goblin` object. `e.attack()` dispatches to `Goblin`'s override again: `"Goblin slashes with a dagger"`.

```
combatants = [Goblin, Dragon, Goblin]

for each e in combatants:
  e.attack() -> JVM checks e's ACTUAL type at this exact moment -> runs that type's own attack() override
  Goblin  -> "Goblin slashes with a dagger"
  Dragon  -> "Dragon breathes fire"
  Goblin  -> "Goblin slashes with a dagger"
```

**Final output.** Three lines, in order: `"Goblin slashes with a dagger"`, `"Dragon breathes fire"`, `"Goblin slashes with a dagger"` — `runBattleRound`'s own code never once referenced `Goblin` or `Dragon` by name; the correct, type-specific behaviour emerged entirely from dynamic dispatch resolving each call based on the actual objects passed in.

## 7. Gotchas & takeaways

> **Dynamic dispatch applies only to non-`static`, non-`private`, non-`final` methods — `static` methods are resolved at compile time based on the reference's *declared* type, exactly like fields, not dynamically.** Calling a `static` method through a subclass reference that "hides" a same-named `static` superclass method behaves like field hiding (an earlier topic), not like overriding — a common and important distinction.

> **Constructors are never dynamically dispatched — calling `new Dog()` always runs exactly `Dog`'s own constructor (and, transitively, its ancestors' via `super(...)`), never some hypothetical "overridden" constructor**, since constructors aren't inherited or overridden the way ordinary instance methods are.

- Dynamic method dispatch resolves an overridden method call based on the object's actual runtime type, decided fresh at the moment each call executes.
- This is what makes polymorphism work: code written against a general supertype automatically gets each specific subclass's correct behaviour.
- Only non-`static`, non-`private`, non-`final` methods participate in dynamic dispatch — fields and `static` methods are resolved by declared (compile-time) type instead.
- Dynamic dispatch continues working correctly through any number of layers of generic code, since the resolution always happens fresh at the actual point of the method call, based on the real object involved.
