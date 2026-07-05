---
card: java
gi: 184
slug: defining-a-class
title: Defining a class
---

## 1. What it is

A **class** is a blueprint that describes a category of things: what data each instance holds (its **fields**) and what behaviour each instance can perform (its **methods**). Defining a class means writing that blueprint using the `class` keyword — the class itself creates no objects; it only describes what an object of that type *would* look like, ready to be instantiated later with `new`.

```java
public class Dog {
    String name;   // field: data every Dog has
    int age;       // field

    void bark() {  // method: behaviour every Dog can perform
        System.out.println(name + " says Woof!");
    }
}
```

`class Dog { ... }` alone does not create a dog — it defines what a `Dog` *is*: something with a `name`, an `age`, and the ability to `bark()`. Actual dog objects come from this blueprint via `new Dog()`, covered in the next topic.

## 2. Why & when

Classes are the fundamental unit of organization in Java — nearly everything in a Java program is a class, or lives inside one:

- **Modeling real-world or domain concepts** — a `Customer`, an `Order`, a `BankAccount` — bundling the data and behaviour that concept naturally has into one cohesive unit.
- **Reusability** — define the blueprint once, then create as many independent instances as needed (many `Dog` objects, each with its own `name` and `age`).
- **Encapsulation** — a class can bundle related data and the logic that operates on it together, rather than scattering loose variables and free-floating functions throughout a program.

You define a new class whenever your program needs to represent a distinct "kind of thing" with its own characteristic data and behaviour — as opposed to writing everything as loose, disconnected variables and static utility methods.

## 3. Core concept

```java
public class Book {
    String title;
    String author;
    int pages;

    void describe() {
        System.out.println(title + " by " + author + " (" + pages + " pages)");
    }
}

public class Main {
    public static void main(String[] args) {
        Book b = new Book(); // creating an instance — covered fully in the next topic
        b.title = "1984";
        b.author = "George Orwell";
        b.pages = 328;
        b.describe(); // 1984 by George Orwell (328 pages)
    }
}
```

`Book` bundles three fields (`title`, `author`, `pages`) and one method (`describe`) into a single, named blueprint — every `Book` object created from it automatically has all three fields and can call `describe()`, without needing to redeclare any of that structure each time.

## 4. Diagram

<svg viewBox="0 0 560 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A class named Book acting as a blueprint containing fields title author pages and a method describe, with an arrow showing it is used to stamp out individual Book objects each with their own field values">
  <rect x="8" y="8" width="544" height="164" rx="8" fill="#0d1117"/>

  <rect x="40" y="30" width="180" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">class Book (blueprint)</text>
  <text x="55" y="75" fill="#e6edf3" font-size="10" font-family="monospace">String title;</text>
  <text x="55" y="92" fill="#e6edf3" font-size="10" font-family="monospace">String author;</text>
  <text x="55" y="109" fill="#e6edf3" font-size="10" font-family="monospace">int pages;</text>
  <text x="55" y="130" fill="#79c0ff" font-size="10" font-family="monospace">void describe() {…}</text>

  <line x1="220" y1="90" x2="300" y2="90" stroke="#79c0ff" stroke-width="2" marker-end="url(#a)"/>
  <text x="260" y="80" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">new Book()</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="310" y="35" width="90" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="355" y="55" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">"1984"</text>
  <text x="355" y="70" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">328 pages</text>

  <rect x="410" y="100" width="90" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="455" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">"Dune"</text>
  <text x="455" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">412 pages</text>
</svg>

One class blueprint; many independent objects, each with its own field values.

## 5. Runnable example

Scenario: representing a simple `Product` in a small store system — starting with a minimal class holding just data, then extending with a method that operates on that data, then hardening the class with encapsulation-style validation inside its own method.

### Level 1 — Basic

```java
public class ProductBasic {
    static class Product {
        String name;
        double price;
    }

    public static void main(String[] args) {
        Product p = new Product();
        p.name = "Coffee";
        p.price = 4.50;

        System.out.println(p.name + ": $" + p.price);
    }
}
```

**How to run:** `java ProductBasic.java`

`Product` is defined as a minimal blueprint with just two fields and no methods yet — `main` creates one instance, assigns its fields directly, and reads them back to print.

### Level 2 — Intermediate

Same `Product`, now with a method that computes something (price with tax) directly from the object's own fields, keeping the calculation logic bundled with the data it operates on.

```java
public class ProductIntermediate {
    static class Product {
        String name;
        double price;

        double priceWithTax(double taxRate) {
            return price * (1 + taxRate);
        }
    }

    public static void main(String[] args) {
        Product p = new Product();
        p.name = "Coffee";
        p.price = 4.50;

        System.out.println(p.name + " total: $" + p.priceWithTax(0.08));
    }
}
```

**How to run:** `java ProductIntermediate.java`

`priceWithTax` reads `price` directly — the field it needs is already part of the same object, so no parameter for the base price is required, only the varying `taxRate`; this is the essence of bundling data and the behaviour that uses it into one class.

### Level 3 — Advanced

Same `Product`, now with a method that validates its own state before performing a calculation, guarding against a nonsensical negative price that could otherwise slip in through direct field assignment.

```java
public class ProductAdvanced {
    static class Product {
        String name;
        double price;

        double priceWithTax(double taxRate) {
            if (price < 0) {
                throw new IllegalStateException("Product '" + name + "' has an invalid negative price: " + price);
            }
            if (taxRate < 0) {
                throw new IllegalArgumentException("Tax rate cannot be negative: " + taxRate);
            }
            return price * (1 + taxRate);
        }
    }

    public static void main(String[] args) {
        Product good = new Product();
        good.name = "Coffee";
        good.price = 4.50;
        System.out.println(good.name + " total: $" + good.priceWithTax(0.08));

        Product broken = new Product();
        broken.name = "Mystery Item";
        broken.price = -10.0; // invalid data snuck in via direct field assignment

        try {
            broken.priceWithTax(0.08);
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ProductAdvanced.java`

`priceWithTax` now checks its own object's state (`price < 0`) before doing any calculation — since fields are directly assignable here, nothing prevents `broken.price = -10.0` from happening, so the *method* itself is the last line of defence, catching the invalid state at the point of use rather than trusting it was set correctly beforehand.

## 6. Walkthrough

Trace `ProductAdvanced.main` for the `broken` product:

**Construction.** `new Product()` creates an instance with `name` and `price` both at their defaults (`null` and `0.0`) until assigned.

**Direct assignment.** `broken.name = "Mystery Item"` and `broken.price = -10.0` set the fields directly — nothing in this class prevents an invalid negative price from being assigned this way, since there's no constructor or setter validating it (a gap addressed by constructors, a later topic).

**Calling `priceWithTax(0.08)`.** Inside the method, `price < 0` evaluates `-10.0 < 0`, which is `true`. The guard throws `IllegalStateException("Product 'Mystery Item' has an invalid negative price: -10.0")` immediately — the `taxRate < 0` check and the final calculation are never reached.

**Caught in `main`.** The `try/catch` around `broken.priceWithTax(0.08)` catches the exception and prints `"Rejected: Product 'Mystery Item' has an invalid negative price: -10.0"`.

```
broken.price = -10.0
priceWithTax(0.08) called
  price < 0?  -10.0 < 0 -> true -> throw IllegalStateException
  (taxRate check and multiplication never execute)
caught in main -> print "Rejected: ..."
```

**Contrast with `good`.** `good.priceWithTax(0.08)` passes both guards (`price` is `4.50`, `taxRate` is `0.08`, neither negative) and returns `4.50 * 1.08 = 4.86`, printed as `"Coffee total: $4.86"`.

## 7. Gotchas & takeaways

> **A class definition alone creates zero objects.** `class Book { ... }` only describes the blueprint; nothing exists in memory as an actual `Book` until `new Book()` is called. A common beginner confusion is expecting fields to have real values simply because the class was defined — they don't, until an instance is created and those fields assigned.

> **Fields left as plain, directly-assignable data (as in these examples) offer no protection against invalid values being set from outside the class.** Real-world Java code typically uses `private` fields with constructors and validating methods (covered in upcoming topics) specifically to prevent the kind of invalid state seen in the `broken` product above.

- A class is a blueprint: it defines the fields (data) and methods (behaviour) that every instance created from it will have.
- Defining a class does not create an object — `new` (the next topic) is what actually produces one.
- Bundling related data and the logic that operates on it into one class is the core idea behind encapsulation.
- Methods defined inside a class can freely read and use that same object's own fields, without needing them passed in as parameters.
