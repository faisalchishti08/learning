---
card: java
gi: 223
slug: upcasting-subtype-supertype
title: Upcasting (subtype → supertype)
---

## 1. What it is

**Upcasting** is treating a subclass object as an instance of its superclass (or an implemented interface) — assigning a more specific reference to a more general one. It's always **safe** and often **implicit** (no explicit cast syntax required), since every `Dog` genuinely *is* an `Animal`, so treating it as one loses no correctness. Upcasting doesn't change the object itself at all — only the *reference type* used to access it, which in turn affects which members are visible through that reference (as covered in earlier field-hiding and method-overriding topics).

```java
class Animal {
    void eat() { System.out.println("Eating"); }
}

class Dog extends Animal {
    void bark() { System.out.println("Woof"); }
}

Dog d = new Dog();
Animal a = d; // upcasting — implicit, no cast syntax needed, always safe

a.eat();  // fine — Animal declares eat()
// a.bark(); // COMPILE ERROR — Animal reference doesn't know about bark(), even though the underlying object has it
```

`a` and `d` refer to the exact same `Dog` object in memory — upcasting changes nothing about the object itself, only what the compiler will *let you call* through that particular reference; `bark()` still exists on the actual object, but the `Animal`-typed reference `a` simply doesn't expose it, since `Animal` itself knows nothing about barking.

## 2. Why & when

Upcasting exists to let code work generically with a whole family of related subclasses through their shared superclass or interface, without needing to know which specific subclass it's actually dealing with:

- **Writing general-purpose code** — a method that accepts an `Animal` parameter can be called with a `Dog`, `Cat`, or any other subclass, without needing a separate overload for each specific type.
- **Collections of mixed subclasses** — a `List<Animal>` can hold `Dog`s, `Cat`s, and any other `Animal` subclass together, iterated and processed uniformly through the shared `Animal` interface.
- **The foundation of polymorphism** — upcasting is what makes dynamic method dispatch (a later topic) meaningful in the first place: calling an overridden method through an upcast reference still runs the *actual* object's own override, which is the essence of polymorphic behaviour.

You upcast (usually implicitly, just by assignment or by passing an argument) whenever code is meant to work with the general concept a superclass or interface represents, rather than being tied to one specific subclass — this is a foundational technique for writing flexible, reusable code across a class hierarchy.

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

void printArea(Shape s) { // accepts ANY Shape subclass, via upcasting at the call site
    System.out.println("Area: " + s.area());
}

printArea(new Circle(3)); // Circle upcast to Shape implicitly, as an argument
printArea(new Square(4)); // Square upcast to Shape implicitly
```

`printArea` never mentions `Circle` or `Square` by name — it only knows about `Shape`, yet correctly computes each specific shape's own area, because `s.area()` (even through the general `Shape`-typed parameter) still runs whichever concrete subclass's overridden `area()` actually applies to the object passed in.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Circle object and a Square object both upcast to the shared Shape reference type when passed into printArea, with the same method call dispatching correctly to each object's own actual area implementation despite the shared, more general parameter type">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="30" y="30" width="140" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="52" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">new Circle(3)</text>

  <rect x="430" y="30" width="140" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="52" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">new Square(4)</text>

  <line x1="150" y1="65" x2="270" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#up)"/>
  <line x1="450" y1="65" x2="330" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#up)"/>
  <text x="300" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">upcast (implicit)</text>

  <rect x="220" y="100" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="125" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">printArea(Shape s)</text>

  <defs><marker id="up" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both objects are upcast to the shared `Shape` type, letting one general method handle both.

## 5. Runnable example

Scenario: a small media player supporting different playable item types — starting with basic upcasting through a method parameter, then extending to a collection of mixed subclasses processed uniformly, then hardening into a case demonstrating that upcasting is purely a compile-time reference-type change, verified through runtime type checks.

### Level 1 — Basic

```java
public class UpcastBasic {
    static class MediaItem {
        void play() { System.out.println("Playing generic media"); }
    }

    static class Song extends MediaItem {
        @Override
        void play() { System.out.println("Playing a song"); }
    }

    static void playItem(MediaItem item) { // accepts ANY MediaItem subclass
        item.play();
    }

    public static void main(String[] args) {
        playItem(new Song()); // Song upcast to MediaItem, implicitly, as the argument
    }
}
```

**How to run:** `java UpcastBasic.java`

`playItem(new Song())` implicitly upcasts the `Song` object to `MediaItem` at the point it's passed as an argument — inside `playItem`, `item.play()` still runs `Song`'s overridden `play()`, since the object's actual type doesn't change, only the reference type used to refer to it within `playItem`.

### Level 2 — Intermediate

Same media player, now with a mixed collection of different `MediaItem` subclasses, processed uniformly through the shared supertype.

```java
import java.util.List;

public class UpcastIntermediate {
    static class MediaItem {
        void play() { System.out.println("Playing generic media"); }
    }

    static class Song extends MediaItem {
        @Override
        void play() { System.out.println("Playing a song"); }
    }

    static class Podcast extends MediaItem {
        @Override
        void play() { System.out.println("Playing a podcast episode"); }
    }

    public static void main(String[] args) {
        List<MediaItem> playlist = List.of(new Song(), new Podcast(), new Song());

        for (MediaItem item : playlist) { // every element accessed through the shared MediaItem type
            item.play();
        }
    }
}
```

**How to run:** `java UpcastIntermediate.java`

`List<MediaItem>` holds a mix of `Song` and `Podcast` objects, each implicitly upcast to `MediaItem` when added to the list — the loop calls `.play()` uniformly on every element, and each call correctly runs that specific object's own overridden implementation.

### Level 3 — Advanced

Same media player, now demonstrating that upcasting genuinely doesn't change the object's actual type — using `instanceof` and `getClass()` to confirm the underlying object's real identity survives being referenced through its supertype.

```java
import java.util.List;

public class UpcastAdvanced {
    static class MediaItem {
        void play() { System.out.println("Playing generic media"); }
    }

    static class Song extends MediaItem {
        @Override
        void play() { System.out.println("Playing a song"); }
    }

    static void inspect(MediaItem item) { // item is upcast here; its actual type is unaffected
        System.out.println("Declared type in this method: MediaItem");
        System.out.println("Actual runtime type: " + item.getClass().getSimpleName());
        System.out.println("Is it really a Song? " + (item instanceof Song));
        item.play(); // still dispatches to the actual type's override
    }

    public static void main(String[] args) {
        MediaItem generic = new MediaItem();
        MediaItem song = new Song(); // upcast at the point of declaration itself

        inspect(generic);
        inspect(song);
    }
}
```

**How to run:** `java UpcastAdvanced.java`

Even though `inspect`'s parameter is declared as `MediaItem`, `item.getClass().getSimpleName()` and `item instanceof Song` both correctly report the object's genuine underlying type — `"Song"` and `true` respectively, when a `Song` is passed — proving that upcasting only affects what the compiler permits you to reference directly by name; it never actually changes or erases the object's real, runtime identity.

## 6. Walkthrough

Trace `inspect(song)` from `UpcastAdvanced.main`, where `song` was declared as `MediaItem` but constructed as `new Song()`:

**Entry.** `item` (the parameter) now refers to the same `Song` object that `song` refers to — `item`'s *declared* type is `MediaItem`, matching the parameter's declaration.

**`item.getClass().getSimpleName()`.** `getClass()` is a method every object inherits from `Object`, and it always returns the object's **actual runtime class**, regardless of any reference-type upcasting — it returns the `Class` object representing `Song`, and `.getSimpleName()` on that gives the string `"Song"`.

**`item instanceof Song`.** This checks whether the object `item` refers to is genuinely an instance of `Song` (or a subclass of it) — it is, since it was constructed as `new Song()` — so this evaluates to `true`.

**`item.play()`.** Dispatches based on the object's actual runtime type (dynamic dispatch, covered fully in the next topic) — since the real object is a `Song`, `Song.play()` runs, printing `"Playing a song"`.

```
song (declared MediaItem, actual object: Song)
inspect(song):
  item.getClass().getSimpleName() -> "Song"   (actual type, unaffected by upcasting)
  item instanceof Song            -> true      (actual type, unaffected by upcasting)
  item.play()                     -> "Playing a song"  (dispatches to Song's own override)
```

**Final output for this call.** `"Declared type in this method: MediaItem"`, `"Actual runtime type: Song"`, `"Is it really a Song? true"`, `"Playing a song"` — four lines confirming that upcasting is purely a compile-time, reference-level concept; the object's real identity and behaviour remain completely unaffected underneath.

## 7. Gotchas & takeaways

> **Upcasting never changes what members you can call *through that specific reference* only what the underlying object actually is or can do.** A `Dog` upcast to `Animal` still has all its `Dog`-specific behaviour intact in memory, but code holding only the `Animal`-typed reference simply cannot call `bark()` directly through it — reaching `bark()` again would require downcasting (the next topic) back to `Dog`.

> **Upcasting is always safe and (for classes and interfaces in a genuine "is-a" relationship) is usually implicit — no cast syntax is needed**, unlike downcasting, which is explicit and can fail at runtime. This asymmetry exists because upcasting can never lose information the compiler needs to verify safety, while downcasting assumes information that might turn out to be wrong.

- Upcasting treats a subclass object as its superclass (or interface) type — always safe, usually implicit, and never changes the object itself.
- Only members declared on the reference's declared type are directly callable through that reference, even though the underlying object may have more.
- Upcasting is what allows general-purpose code (a shared parameter type, a mixed collection) to work uniformly across many different subclasses.
- The object's actual runtime type and behaviour are completely unaffected by upcasting — `getClass()`, `instanceof`, and dynamic method dispatch all still reflect the real, underlying object.
