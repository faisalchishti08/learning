---
card: java
gi: 203
slug: instance-initializer-blocks
title: Instance initializer blocks
---

## 1. What it is

An **instance initializer block** is a plain `{ ... }` block (no `static` keyword) written directly inside a class body, used to run setup logic for instance fields. Unlike a static block (which runs once for the class), an instance initializer block runs **every time** a new object is created — specifically, after field initializers and any instance blocks run in source order, but *before* the constructor's own body executes, for every single `new` call.

```java
class Widget {
    int id;
    java.util.List<String> tags;

    { // instance initializer block — runs on EVERY new Widget(), before the constructor body
        tags = new java.util.ArrayList<>();
        tags.add("default");
        System.out.println("Instance block ran");
    }

    Widget(int id) {
        this.id = id;
        System.out.println("Constructor ran");
    }
}

new Widget(1); // prints: "Instance block ran" then "Constructor ran"
new Widget(2); // prints the SAME two lines again — this runs fresh for every instance
```

Every single `new Widget(...)` call runs the instance block again, fresh, before that specific constructor's body — this is the key difference from a static block, which runs only once no matter how many instances are created afterward.

## 2. Why & when

Instance initializer blocks exist for setup logic shared across **all** constructors of a class, when that logic is too involved for a simple field-initializer expression:

- **Shared setup across multiple constructor overloads** — if every constructor overload needs the same non-trivial setup step (initializing a collection with several starting entries, computing something from multiple fields together), an instance block runs that logic exactly once per object, regardless of which constructor overload was actually called.
- **Anonymous class initialization** — instance blocks are also the *only* way to run multi-statement setup logic when creating an anonymous class (a class with no name and therefore no ability to define a named constructor), a more advanced topic covered elsewhere.
- **In practice, instance blocks are relatively rare** — most of the time, putting shared setup logic directly into a designated constructor (with other overloads delegating to it via `this(...)`, as covered earlier) achieves the same result more clearly; instance blocks are most useful specifically when no single "most complete" constructor naturally exists to hold that shared logic.

You reach for an instance block specifically when you have multiple constructors that all need to share some setup step, and constructor chaining with `this(...)` doesn't cleanly express it — otherwise, putting the logic in a designated constructor is usually the clearer, more idiomatic choice.

## 3. Core concept

```java
class Report {
    java.util.List<String> sections = new java.util.ArrayList<>();
    String title;

    { // runs before EITHER constructor's own body, for every instance
        sections.add("Header");
        sections.add("Summary");
    }

    Report() {
        this.title = "Untitled Report";
    }

    Report(String title) {
        this.title = title;
    }
}

Report r1 = new Report();
Report r2 = new Report("Q4 Results");
System.out.println(r1.sections); // [Header, Summary] — added by the instance block
System.out.println(r2.sections); // [Header, Summary] — same, regardless of which constructor ran
```

Both `Report()` and `Report(String title)` benefit from the exact same instance block, which runs before either constructor's own body — this avoids duplicating `sections.add("Header"); sections.add("Summary");` inside both constructors separately.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two different constructor overloads both routing through the same instance initializer block first, before each constructor's own distinct body runs, for every single new object created">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="30" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="105" y="52" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">new Report()</text>

  <rect x="30" y="90" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="105" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">new Report("Q4")</text>

  <rect x="230" y="55" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="82" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">instance block (shared)</text>

  <line x1="180" y1="47" x2="230" y2="70" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ib)"/>
  <line x1="180" y1="107" x2="230" y2="85" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ib)"/>

  <rect x="450" y="30" width="130" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="515" y="52" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Report() body</text>

  <rect x="450" y="90" width="130" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="515" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Report(title) body</text>

  <line x1="410" y1="70" x2="450" y2="47" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ib)"/>
  <line x1="410" y1="85" x2="450" y2="107" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ib)"/>

  <defs><marker id="ib" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Every constructor overload runs through the same instance block first, avoiding duplicated setup logic.

## 5. Runnable example

Scenario: a simple game character with starting inventory shared across multiple ways of creating a character — starting with basic shared setup via an instance block, then extending with additional shared logic, then hardening into a comparison showing when a designated constructor is actually the clearer alternative.

### Level 1 — Basic

```java
public class CharacterBasic {
    static class Character {
        java.util.List<String> inventory = new java.util.ArrayList<>();
        String name;

        { // shared starting inventory, for every character no matter which constructor is used
            inventory.add("Basic Sword");
            inventory.add("Health Potion");
        }

        Character() {
            this.name = "Unnamed Hero";
        }

        Character(String name) {
            this.name = name;
        }
    }

    public static void main(String[] args) {
        Character c1 = new Character();
        Character c2 = new Character("Aria");

        System.out.println(c1.name + ": " + c1.inventory);
        System.out.println(c2.name + ": " + c2.inventory);
    }
}
```

**How to run:** `java CharacterBasic.java`

Both `c1` and `c2` end up with the same starting inventory (`["Basic Sword", "Health Potion"]`), regardless of which constructor created them — the instance block runs identically before either constructor's own body, ensuring this shared setup can never be accidentally skipped or duplicated inconsistently between the overloads.

### Level 2 — Intermediate

Same character system, now with the instance block also computing a derived starting value (total inventory weight) shared identically across every constructor.

```java
public class CharacterIntermediate {
    static class Character {
        java.util.List<String> inventory = new java.util.ArrayList<>();
        int startingWeight;
        String name;

        {
            inventory.add("Basic Sword");
            inventory.add("Health Potion");
            startingWeight = inventory.size() * 5; // shared derived computation
            System.out.println("Instance block ran; starting weight computed as " + startingWeight);
        }

        Character() {
            this.name = "Unnamed Hero";
        }

        Character(String name) {
            this.name = name;
        }
    }

    public static void main(String[] args) {
        Character c1 = new Character();
        Character c2 = new Character("Aria");

        System.out.println(c1.name + ", weight=" + c1.startingWeight);
        System.out.println(c2.name + ", weight=" + c2.startingWeight);
    }
}
```

**How to run:** `java CharacterIntermediate.java`

The `"Instance block ran..."` message prints **twice** — once for each `new Character(...)` call — since (unlike a static block) an instance block runs fresh, every single time, for every object created, regardless of which constructor overload is actually invoked.

### Level 3 — Advanced

Same character system, now contrasted directly against the alternative, more common pattern of putting shared logic in a designated constructor with `this(...)` chaining — demonstrating that both achieve the same *result*, but instance blocks are specifically useful when there's genuinely no single natural "most complete" constructor to designate.

```java
public class CharacterAdvanced {

    // Approach A: instance block — useful when constructors don't naturally chain to one "most complete" version
    static class CharacterWithBlock {
        java.util.List<String> inventory = new java.util.ArrayList<>();
        String name;

        {
            inventory.add("Basic Sword");
            inventory.add("Health Potion");
        }

        CharacterWithBlock() { this.name = "Unnamed Hero"; }
        CharacterWithBlock(String name) { this.name = name; }
    }

    // Approach B: designated constructor with this(...) chaining — often clearer when it fits naturally
    static class CharacterWithChaining {
        java.util.List<String> inventory;
        String name;

        CharacterWithChaining(String name) { // designated constructor: holds the real setup logic
            this.name = name;
            this.inventory = new java.util.ArrayList<>();
            inventory.add("Basic Sword");
            inventory.add("Health Potion");
        }

        CharacterWithChaining() {
            this("Unnamed Hero"); // delegates instead of duplicating setup
        }
    }

    public static void main(String[] args) {
        CharacterWithBlock a = new CharacterWithBlock("Aria");
        CharacterWithChaining b = new CharacterWithChaining("Aria");

        System.out.println(a.name + ": " + a.inventory);
        System.out.println(b.name + ": " + b.inventory);
    }
}
```

**How to run:** `java CharacterAdvanced.java`

Both `CharacterWithBlock` and `CharacterWithChaining` end up producing objects with identical `inventory` contents — the instance block approach and the `this(...)`-chaining approach both correctly share setup logic across constructors, and the choice between them in real code usually comes down to readability: chaining is generally preferred when a natural "most complete" constructor exists, while an instance block is reserved for cases where it doesn't.

## 6. Walkthrough

Trace `new CharacterWithBlock("Aria")` from `CharacterAdvanced.main`:

**Field initializer.** `inventory = new java.util.ArrayList<>()` runs first, creating an empty list.

**Instance block.** Runs next, before the constructor body: `inventory.add("Basic Sword")`, then `inventory.add("Health Potion")` — `inventory` now holds `["Basic Sword", "Health Potion"]`.

**Constructor body.** `CharacterWithBlock(String name)`'s body finally runs: `this.name = "Aria"`.

**Object complete.** `a.name` is `"Aria"`, `a.inventory` is `["Basic Sword", "Health Potion"]`.

```
new CharacterWithBlock("Aria"):
  1. field initializer: inventory = new ArrayList() -> []
  2. instance block: inventory.add("Basic Sword"), inventory.add("Health Potion") -> [Basic Sword, Health Potion]
  3. constructor body: this.name = "Aria"
  result: name="Aria", inventory=[Basic Sword, Health Potion]
```

**Contrast: `new CharacterWithChaining("Aria")`.** No instance block exists here; instead, the designated constructor itself does everything in one place: `this.name = "Aria"`, then builds and populates `inventory` directly in its own body. The *result* is identical to the instance-block approach, just organized differently — one designated constructor holding all the logic, rather than an instance block plus separate, simpler constructors.

**Final output.** Both `"Aria: [Basic Sword, Health Potion]"` lines print identically for `a` and `b`, confirming both approaches produce the same observable result through different, equally valid mechanisms.

## 7. Gotchas & takeaways

> **An instance initializer block runs fresh for every single `new` call — never confuse it with a static block, which runs only once for the entire class.** A block without the `static` keyword is an instance block; forgetting or misreading this keyword is an easy way to misunderstand a piece of unfamiliar code's actual behaviour.

> **Instance blocks execute in the order they're written relative to field initializers, and always before any constructor's own body** — if a class has multiple instance blocks and field initializers interleaved, they all run top-to-bottom in source order first, and only then does whichever constructor was actually invoked run its own body.

- An instance initializer block (`{ ... }`, no `static`) runs on every `new` call, after field initializers, before the constructor body.
- It's most useful for setup logic shared identically across multiple constructor overloads that don't naturally chain into one designated constructor.
- In most real code, putting shared logic in a designated constructor (with other overloads delegating via `this(...)`) is more common and often clearer.
- Never confuse an instance block with a static block — one runs per-object, every time; the other runs once, ever, for the whole class.
