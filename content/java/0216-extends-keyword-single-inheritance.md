---
card: java
gi: 216
slug: extends-keyword-single-inheritance
title: extends keyword & single inheritance
---

## 1. What it is

The `extends` keyword establishes **inheritance**: a subclass (also called a child class) automatically gains all the accessible fields and methods of its superclass (parent class), and can add new fields and methods, or override inherited ones, on top of what it inherited. Java enforces **single inheritance** for classes — a class can `extends` at most **one** other class (though, as covered in later topics, it can `implements` multiple interfaces), which keeps a class's inheritance hierarchy a simple, unambiguous straight line rather than a tangled web.

```java
class Animal {
    String name;
    Animal(String name) { this.name = name; }

    void eat() {
        System.out.println(name + " is eating");
    }
}

class Dog extends Animal { // Dog IS-A Animal — inherits name and eat()
    void bark() { // Dog adds its own new behaviour
        System.out.println(name + " says Woof!"); // 'name' is inherited, usable directly
    }
}

Dog d = new Dog("Rex");
d.eat();  // inherited from Animal
d.bark(); // Dog's own method
```

`Dog` never redeclares `name` or `eat()` — it automatically has both, simply by virtue of `extends Animal`; `Dog` then adds `bark()`, a method that only `Dog` (and any further subclasses of `Dog`) would have, since `Animal` itself knows nothing about barking.

## 2. Why & when

Inheritance exists to model genuine "is-a" relationships between concepts, letting shared behaviour and data be defined once in a common superclass rather than duplicated across every related subclass:

- **Code reuse** — common fields and methods shared by several related concepts (all animals eat, all vehicles have a speed) are written once, in the superclass, and automatically available to every subclass.
- **A natural "is-a" hierarchy** — `Dog extends Animal` expresses that every `Dog` genuinely *is* a kind of `Animal`, which is the litmus test for when inheritance is the right tool: if the relationship can't honestly be phrased as "is-a," inheritance is probably the wrong choice, and composition (an object holding a reference to another, rather than extending it) is likely more appropriate instead.
- **Single inheritance keeps hierarchies simple** — by limiting a class to exactly one direct superclass, Java avoids the "diamond problem" ambiguity that multiple class inheritance can create in other languages (where two parent classes might define conflicting versions of the same inherited method) — this is one reason Java allows multiple interface implementation (a separate topic) but only single class inheritance.

You reach for `extends` when a new class is genuinely a more specific version of an existing class, sharing its fundamental data and behaviour while adding or customizing something on top — not merely because two classes happen to share a few unrelated method names.

## 3. Core concept

```java
class Vehicle {
    int speed;
    void accelerate(int amount) {
        speed += amount;
        System.out.println("Speed is now " + speed);
    }
}

class Car extends Vehicle { // Car IS-A Vehicle
    int numberOfDoors;
    Car(int numberOfDoors) {
        this.numberOfDoors = numberOfDoors;
    }
}

class SportsCar extends Car { // SportsCar IS-A Car, which IS-A Vehicle — multi-level, still single-parent at each step
    SportsCar() {
        super(2); // sports cars have 2 doors
    }
}

SportsCar sc = new SportsCar();
sc.accelerate(50); // inherited all the way from Vehicle, two levels up
System.out.println(sc.numberOfDoors); // inherited from Car, one level up
```

`SportsCar` inherits from `Car`, which itself inherits from `Vehicle` — this is a **multi-level** hierarchy, but at every single step, each class still `extends` exactly one direct superclass; `SportsCar` transitively has access to everything `Vehicle` and `Car` define, even though it doesn't extend `Vehicle` directly.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A three level single inheritance chain: Vehicle at the top, Car extending Vehicle in the middle, and SportsCar extending Car at the bottom, with each class inheriting everything from every ancestor above it in the chain">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">class Vehicle</text>

  <line x1="300" y1="60" x2="300" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ex)"/>
  <text x="330" y="75" fill="#79c0ff" font-size="9" font-family="sans-serif">extends</text>

  <rect x="220" y="85" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="300" y="110" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">class Car</text>

  <line x1="300" y1="125" x2="300" y2="145" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ex)"/>
  <text x="330" y="140" fill="#79c0ff" font-size="9" font-family="sans-serif">extends</text>

  <rect x="220" y="150" width="160" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="300" y="170" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">class SportsCar</text>

  <text x="490" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Each class has exactly ONE</text>
  <text x="490" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">direct superclass (single</text>
  <text x="490" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">inheritance) — a straight chain.</text>

  <defs><marker id="ex" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

A single-inheritance chain: each class has exactly one direct superclass, forming a simple, unambiguous line.

## 5. Runnable example

Scenario: a small library system modeling different kinds of media — starting with basic inheritance sharing common fields and behaviour, then extending with a subclass adding genuinely new state and behaviour, then hardening into a multi-level hierarchy demonstrating that inherited members are usable at every level down the chain.

### Level 1 — Basic

```java
public class MediaBasic {
    static class LibraryItem {
        String title;
        boolean checkedOut = false;

        LibraryItem(String title) {
            this.title = title;
        }

        void checkOut() {
            checkedOut = true;
            System.out.println(title + " checked out");
        }
    }

    static class Book extends LibraryItem { // Book IS-A LibraryItem
        Book(String title) {
            super(title); // calls LibraryItem's constructor
        }
    }

    public static void main(String[] args) {
        Book b = new Book("Java Basics");
        b.checkOut(); // inherited from LibraryItem
        System.out.println(b.title + " checked out: " + b.checkedOut);
    }
}
```

**How to run:** `java MediaBasic.java`

`Book` inherits `title`, `checkedOut`, and `checkOut()` entirely from `LibraryItem`, adding nothing new of its own yet — `super(title)` is required in `Book`'s constructor since `LibraryItem` has no no-argument constructor (it only defines one requiring a `title`), so `Book` must explicitly pass one along.

### Level 2 — Intermediate

Same hierarchy, now with `Book` adding genuinely new state (`author`) and behaviour of its own, on top of what it inherits.

```java
public class MediaIntermediate {
    static class LibraryItem {
        String title;
        boolean checkedOut = false;

        LibraryItem(String title) { this.title = title; }

        void checkOut() {
            checkedOut = true;
            System.out.println(title + " checked out");
        }
    }

    static class Book extends LibraryItem {
        String author; // NEW field, not present in LibraryItem

        Book(String title, String author) {
            super(title);
            this.author = author;
        }

        void printInfo() { // NEW method, not present in LibraryItem
            System.out.println(title + " by " + author);
        }
    }

    public static void main(String[] args) {
        Book b = new Book("Java Basics", "Jane Doe");
        b.printInfo();  // Book's own method
        b.checkOut();   // inherited from LibraryItem
    }
}
```

**How to run:** `java MediaIntermediate.java`

`Book` now genuinely extends `LibraryItem` with real, new capability (`author`, `printInfo()`) that plain `LibraryItem` objects don't have, while still inheriting and freely using `checkOut()` — this combination of "keep everything shared" plus "add something specific" is exactly what inheritance is for.

### Level 3 — Advanced

Same library system, now with a two-level hierarchy — `AudioBook extends Book extends LibraryItem` — demonstrating that inherited members from *both* ancestor levels remain fully usable at the bottom of the chain.

```java
public class MediaAdvanced {
    static class LibraryItem {
        String title;
        boolean checkedOut = false;

        LibraryItem(String title) { this.title = title; }

        void checkOut() {
            checkedOut = true;
            System.out.println(title + " checked out");
        }
    }

    static class Book extends LibraryItem {
        String author;

        Book(String title, String author) {
            super(title);
            this.author = author;
        }

        void printInfo() {
            System.out.println(title + " by " + author);
        }
    }

    static class AudioBook extends Book { // AudioBook IS-A Book, which IS-A LibraryItem
        int durationMinutes;

        AudioBook(String title, String author, int durationMinutes) {
            super(title, author); // calls Book's constructor, which calls LibraryItem's
            this.durationMinutes = durationMinutes;
        }

        void printFullInfo() {
            printInfo(); // inherited from Book (one level up)
            System.out.println("Duration: " + durationMinutes + " minutes");
            System.out.println("Checked out: " + checkedOut); // inherited from LibraryItem (two levels up)
        }
    }

    public static void main(String[] args) {
        AudioBook ab = new AudioBook("Java Basics", "Jane Doe", 480);
        ab.printFullInfo();
        ab.checkOut(); // inherited from LibraryItem, two levels up
        System.out.println("Now checked out: " + ab.checkedOut);
    }
}
```

**How to run:** `java MediaAdvanced.java`

`AudioBook` never redeclares `title`, `author`, `checkedOut`, `printInfo()`, or `checkOut()` — all five are inherited, two of them (`title`, `checkedOut`, `checkOut()`) from two levels up (`LibraryItem`), and two (`author`, `printInfo()`) from one level up (`Book`) — `AudioBook` adds only what's genuinely new to it: `durationMinutes` and `printFullInfo()`.

## 6. Walkthrough

Trace `new AudioBook("Java Basics", "Jane Doe", 480)` followed by `ab.printFullInfo()` and `ab.checkOut()`:

**Construction chain.** `AudioBook`'s constructor calls `super(title, author)`, invoking `Book`'s constructor, which itself calls `super(title)`, invoking `LibraryItem`'s constructor — `this.title = "Java Basics"` is set there first. Control returns to `Book`'s constructor: `this.author = "Jane Doe"`. Control returns to `AudioBook`'s constructor: `this.durationMinutes = 480`. (This is the same superclass-first construction order covered in earlier topics, now spanning three levels.)

**`ab.printFullInfo()`.** Calls `printInfo()` — since `AudioBook` doesn't override it, the inherited `Book.printInfo()` runs, printing `"Java Basics by Jane Doe"`. Then prints `"Duration: 480 minutes"` directly. Then reads `checkedOut` (inherited from `LibraryItem`, currently `false`), printing `"Checked out: false"`.

**`ab.checkOut()`.** `AudioBook` has no `checkOut()` of its own, nor does `Book` — the call resolves all the way up to `LibraryItem.checkOut()`, which sets `checkedOut = true` and prints `"Java Basics checked out"`.

**Final check.** `ab.checkedOut` now reads `true`.

```
construction: LibraryItem sets title -> Book sets author -> AudioBook sets durationMinutes
printFullInfo():
  printInfo() [from Book]        -> "Java Basics by Jane Doe"
  "Duration: 480 minutes"         (AudioBook's own)
  checkedOut [from LibraryItem]  -> "Checked out: false"
checkOut() [from LibraryItem]:   checkedOut = true -> "Java Basics checked out"
```

**Final output.** `"Java Basics by Jane Doe"`, `"Duration: 480 minutes"`, `"Checked out: false"`, `"Java Basics checked out"`, `"Now checked out: true"` — five lines total, demonstrating members inherited from two different ancestor levels all working together seamlessly in one final subclass.

## 7. Gotchas & takeaways

> **Java classes support single inheritance only — `class X extends A, B { }` is a compile error.** If a class genuinely needs to share behaviour from multiple unrelated sources, the idiomatic solutions are implementing multiple interfaces (a later topic) or using composition (holding references to other objects rather than extending them) instead of attempting multiple class inheritance, which Java deliberately disallows.

> **A subclass constructor must, directly or indirectly (via `this(...)`), invoke a superclass constructor as its effective first action** — if you don't write an explicit `super(...)` call, Java automatically inserts a call to the superclass's no-argument constructor; if the superclass has no no-argument constructor (as `LibraryItem` doesn't, in these examples), you must write an explicit `super(...)` call yourself, or the subclass fails to compile.

- `extends` establishes inheritance: a subclass automatically gains its superclass's accessible fields and methods.
- Java classes support single inheritance only — exactly one direct superclass per class, though hierarchies can be many levels deep.
- Use inheritance specifically to model genuine "is-a" relationships; reach for composition instead when the relationship doesn't honestly fit that description.
- Inherited members remain fully accessible at every level of a multi-level hierarchy, however many ancestors deep they were originally defined.
