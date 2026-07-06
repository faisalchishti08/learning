---
card: java
gi: 243
slug: interface-declaration
title: Interface declaration
---

## 1. What it is

An interface is declared with the `interface` keyword instead of `class`, and defines a set of method signatures that any implementing class must provide. In its classic form (Java's original design), every method in an interface is implicitly abstract — no body — and every field is implicitly a constant; it describes purely *what* a type can do, never *how*.

```java
interface Drawable {
    void draw(); // no body — implicitly public and abstract
}

class Circle implements Drawable {
    @Override
    public void draw() { // must be public — cannot reduce visibility below the interface's
        System.out.println("Drawing a circle");
    }
}
```

`interface Drawable` declares just one method signature, `draw()`, with no implementation at all; `Circle` uses `implements` (not `extends`, reserved for classes) to promise it will supply a `draw()` method, and does so — the interface itself never says how drawing happens, only that anything calling itself `Drawable` must be able to do it.

## 2. Why & when

Declaring an interface is how you express a pure capability or contract, independent of any particular class hierarchy or implementation detail.

- **Decoupling "what" from "how"** — code that only depends on the `Drawable` interface can work with a `Circle`, a `Square`, or any future shape, without ever needing to know or care how each one actually draws itself.
- **Defining a contract multiple unrelated classes can share** — as the previous topic discussed, any number of otherwise unrelated classes can implement the same interface, which is essential for capabilities that cut across class hierarchies (like `Comparable`, implemented by `String`, `Integer`, and countless unrelated user classes).
- **Enabling test doubles and swappable implementations** — code written against an interface type can be tested with a fake or mock implementation, or have its real implementation swapped out entirely, without changing any of the code that depends on the interface.

Declare an interface whenever you want to describe a capability that should be implementable by many different, potentially unrelated classes, or whenever you want calling code to depend only on "what" a type can do rather than a specific concrete class.

## 3. Core concept

```java
interface Playable {
    void play();          // implicitly public abstract
    void pause();          // implicitly public abstract
    int MAX_VOLUME = 100;  // implicitly public static final — a constant, not a regular field
}

class MusicTrack implements Playable {
    @Override
    public void play() { System.out.println("Playing track"); }
    @Override
    public void pause() { System.out.println("Paused"); }
}
```

`MAX_VOLUME` inside the interface is automatically `public static final`, even though none of those keywords appear explicitly — this means it behaves as a shared constant accessible via `Playable.MAX_VOLUME`, and cannot be reassigned by any implementing class, which is exactly why interface "fields" are really constants, not mutable instance state (a distinction explored fully in an upcoming topic).

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An interface declares method signatures with no bodies, implementing classes use the implements keyword and must supply public bodies for every method">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="60" y="20" width="220" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="170" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">interface Drawable</text>
  <text x="170" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">void draw(); — no body</text>

  <line x1="170" y1="70" x2="170" y2="95" stroke="#8b949e" stroke-width="1.5"/>
  <text x="220" y="88" fill="#8b949e" font-size="8" font-family="sans-serif">implements</text>

  <rect x="60" y="100" width="220" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="118" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">class Circle implements Drawable</text>
  <text x="170" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">public void draw() { ... } — full body required</text>

  <text x="450" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The interface</text>
  <text x="450" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">declares the "what."</text>
  <text x="450" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The class supplies</text>
  <text x="450" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the "how."</text>
</svg>

An interface declares method signatures with no bodies; implementing classes must supply a `public` body for each one.

## 5. Runnable example

Scenario: a simple media-playback capability declared as an interface, evolved from one implementing class into several unrelated classes sharing the same contract, then used generically through the interface type.

### Level 1 — Basic

```java
public class InterfaceDeclarationBasic {
    interface Playable {
        void play();
    }

    static class Song implements Playable {
        String title;
        Song(String title) { this.title = title; }
        @Override
        public void play() { System.out.println("Playing song: " + title); }
    }

    public static void main(String[] args) {
        Playable p = new Song("Interstellar Theme");
        p.play();
    }
}
```

**How to run:** `java InterfaceDeclarationBasic.java`

`Song` implements the single-method `Playable` interface, and a variable of the *interface type* `Playable` can hold a `Song` reference — calling `p.play()` runs `Song`'s implementation, even though the variable's declared type mentions only the interface.

### Level 2 — Intermediate

Same interface, now implemented by two completely unrelated classes — a `Song` and a `Podcast` — demonstrating that an interface's implementers need not share any common superclass at all.

```java
import java.util.List;

public class InterfaceDeclarationIntermediate {
    interface Playable {
        void play();
    }

    static class Song implements Playable {
        String title;
        Song(String title) { this.title = title; }
        @Override
        public void play() { System.out.println("Playing song: " + title); }
    }

    static class Podcast implements Playable {
        String episodeName;
        int durationMinutes;
        Podcast(String episodeName, int durationMinutes) {
            this.episodeName = episodeName;
            this.durationMinutes = durationMinutes;
        }
        @Override
        public void play() {
            System.out.println("Playing podcast: " + episodeName + " (" + durationMinutes + " min)");
        }
    }

    public static void main(String[] args) {
        List<Playable> queue = List.of(
            new Song("Interstellar Theme"),
            new Podcast("Deep Space Explained", 42)
        );
        for (Playable p : queue) {
            p.play(); // resolves to each object's own implementation, regardless of unrelated class hierarchies
        }
    }
}
```

**How to run:** `java InterfaceDeclarationIntermediate.java`

`Song` and `Podcast` share no superclass beyond `Object`, and have entirely different fields, yet both satisfy `Playable` and can be stored together in a single `List<Playable>` — the interface is what makes this uniform treatment possible.

### Level 3 — Advanced

Same media system, now with an interface constant and a third implementer that validates against it, plus a queue-processing routine that reports a summary — showing an interface constant used meaningfully across multiple implementations.

```java
import java.util.List;

public class InterfaceDeclarationAdvanced {
    interface Playable {
        int MAX_TITLE_LENGTH = 50; // implicitly public static final
        void play();
        default boolean isTitleValid(String title) { // default method — has a body, covered fully in a later topic
            return title != null && title.length() <= MAX_TITLE_LENGTH;
        }
    }

    static class Song implements Playable {
        String title;
        Song(String title) {
            if (!isTitleValid(title)) throw new IllegalArgumentException("Title too long or null");
            this.title = title;
        }
        @Override
        public void play() { System.out.println("Playing song: " + title); }
    }

    static class Podcast implements Playable {
        String episodeName;
        Podcast(String episodeName) {
            if (!isTitleValid(episodeName)) throw new IllegalArgumentException("Episode name too long or null");
            this.episodeName = episodeName;
        }
        @Override
        public void play() { System.out.println("Playing podcast: " + episodeName); }
    }

    public static void main(String[] args) {
        List<Playable> queue = List.of(
            new Song("Interstellar Theme"),
            new Podcast("Deep Space Explained")
        );

        System.out.println("Max title length allowed: " + Playable.MAX_TITLE_LENGTH);
        for (Playable p : queue) p.play();

        try {
            new Song("x".repeat(60)); // exceeds MAX_TITLE_LENGTH
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java InterfaceDeclarationAdvanced.java`

`Playable.MAX_TITLE_LENGTH` is accessed directly through the interface name (a hallmark of `static final` constants), and `isTitleValid`, a `default` method with a real body, is inherited by both `Song` and `Podcast` without either needing to redefine the validation logic — both constructors reuse the exact same rule from the interface.

## 6. Walkthrough

Trace `main` in `InterfaceDeclarationAdvanced` from the first line to the final `catch` block.

**Constructing `new Song("Interstellar Theme")`.** Inside `Song`'s constructor, `isTitleValid("Interstellar Theme")` is called — this resolves to `Playable`'s `default` method, since `Song` does not override it. `title != null` is `true`; `title.length()` (19) `<= MAX_TITLE_LENGTH` (50) is `true`; the method returns `true`. The constructor proceeds, setting `this.title`.

**Constructing `new Podcast("Deep Space Explained")`.** Same validation path: `isTitleValid` returns `true` (length 21, within the limit), so the constructor proceeds normally.

**`System.out.println("Max title length allowed: " + Playable.MAX_TITLE_LENGTH)`.** Accesses the constant directly via the interface name, printing `"Max title length allowed: 50"`.

**The loop over `queue`.** First iteration: `p` is the `Song`; `p.play()` dispatches to `Song.play()`, printing `"Playing song: Interstellar Theme"`. Second iteration: `p` is the `Podcast`; `p.play()` dispatches to `Podcast.play()`, printing `"Playing podcast: Deep Space Explained"`.

**`new Song("x".repeat(60))`.** `"x".repeat(60)` builds a 60-character string. Inside `Song`'s constructor, `isTitleValid` is called: `title.length()` (60) `<= 50` is `false`, so the method returns `false`. `!isTitleValid(title)` is `true`, so the constructor throws `IllegalArgumentException("Title too long or null")` before `this.title` is ever assigned — the `Song` object is never fully constructed.

**The `catch` block.** Catches the exception and prints `"Rejected: Title too long or null"`.

```
new Song("Interstellar Theme")  -> isTitleValid: len 19 <= 50 -> true  -> constructed OK
new Podcast("Deep Space Explained") -> isTitleValid: len 21 <= 50 -> true -> constructed OK

Playable.MAX_TITLE_LENGTH -> 50 (accessed via interface name)

queue loop: Song.play() -> "Playing song: Interstellar Theme"
            Podcast.play() -> "Playing podcast: Deep Space Explained"

new Song("x"*60) -> isTitleValid: len 60 <= 50 -> false -> throws IllegalArgumentException
  -> caught -> "Rejected: Title too long or null"
```

**Final output.**
```
Max title length allowed: 50
Playing song: Interstellar Theme
Playing podcast: Deep Space Explained
Rejected: Title too long or null
```

## 7. Gotchas & takeaways

> **Every method you override from an interface must be declared `public`, even though the interface itself never writes the word `public` on its abstract method signatures.** Interface methods are implicitly `public abstract`, and Java does not allow an overriding method to reduce visibility below what it inherits — writing `void draw()` (package-private) instead of `public void draw()` in the implementing class is a compile error.

> **Fields declared inside an interface are always `public static final` constants, never per-instance mutable state** — `MAX_TITLE_LENGTH` behaves exactly like a `static final int` declared on a regular class; every implementing class and every caller shares the exact same single value, and it can never be reassigned.

- Interfaces are declared with `interface` and describe a capability's contract; classes use `implements` (not `extends`) to fulfill that contract.
- Classic interface methods have no body (implicitly `public abstract`); implementing classes must supply a `public` implementation for each one.
- Fields declared in an interface are implicitly `public static final` constants, accessible directly via the interface name.
- Any number of otherwise unrelated classes can implement the same interface, enabling uniform treatment of very different concrete types through one shared type.
