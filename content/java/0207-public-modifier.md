---
card: java
gi: 207
slug: public-modifier
title: public modifier
---

## 1. What it is

The `public` modifier is the most permissive of Java's access levels: a `public` class, field, method, or constructor is accessible from **any other code**, anywhere — any other class, in any package, in any part of the program (or in a separate library depending on it). It represents the deliberate, intended external interface of whatever it's applied to.

```java
package com.example.orders;

public class Order { // public: any code, in any package, can use this class
    public String id;               // public: any code can read/write this field directly
    public double calculateTotal() { // public: any code can call this method
        return 0.0;
    }
}
```

`public class Order` means code in a completely different package (`com.example.billing`, say) can write `import com.example.orders.Order;` and use it freely — without `public`, a class is only visible within its own package (the "default" access level, covered in a later topic).

## 2. Why & when

`public` marks the parts of a class deliberately designed to be the class's external, supported interface — what other code is meant to depend on:

- **Public API surface** — methods and constructors meant to be called by other classes, especially from other packages, form the intentional, documented way to use a class.
- **Public classes as the entry point to a package's functionality** — a package typically exposes a small number of `public` classes representing its main abstractions, while keeping internal helper classes package-private (default access) or hiding their details behind `private` fields.
- **Once something is `public`, changing or removing it can break other code that depends on it** — this is why thoughtful API design typically starts with the *most restrictive* access level that works, only widening to `public` when external access is genuinely intended and stable.

You mark something `public` specifically when it's meant to be part of the stable, external contract other code relies on — everything else should default to a more restrictive level, to keep implementation details free to change without breaking other code.

## 3. Core concept

```java
public class Calculator { // the class itself is public — usable from anywhere
    public int add(int a, int b) { // public method: part of the intended external interface
        return a + b;
    }

    private int helper(int x) { // NOT public — an internal implementation detail (covered fully in the private topic)
        return x * 2;
    }
}
```

`add` is `public` because it's meant to be called by any other code that uses a `Calculator`; `helper` is deliberately *not* `public`, since it's an internal detail that other code should never need to call directly — this distinction, choosing which members are part of the public interface versus which are private implementation, is the foundation of good API design.

## 4. Diagram

<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A public class and its public method are accessible from any other package, shown with arrows reaching in from outside code, while its non public helper method remains hidden and unreachable from outside">
  <rect x="8" y="8" width="584" height="124" rx="8" fill="#0d1117"/>

  <rect x="220" y="25" width="180" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">public class Calculator</text>
  <text x="310" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">public add(a, b)</text>
  <text x="310" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">(not public) helper(x)</text>

  <line x1="60" y1="70" x2="220" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#pu)"/>
  <text x="60" y="55" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">any other package</text>

  <line x1="500" y1="70" x2="400" y2="83" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="500" y="60" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">cannot reach helper()</text>

  <defs><marker id="pu" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

`public` members are reachable from anywhere; more restricted members stay hidden from outside code.

## 5. Runnable example

Scenario: a small library-style `Rectangle` class meant for use by other code — starting with a basic public class and method, then extending with a public constructor enforcing valid construction, then hardening into a class exposing a clear public interface while keeping internal details separate.

### Level 1 — Basic

```java
public class RectangleBasic {
    public static class Rectangle {
        public double width;
        public double height;

        public double area() {
            return width * height;
        }
    }

    public static void main(String[] args) {
        Rectangle r = new Rectangle();
        r.width = 4;
        r.height = 5;
        System.out.println("Area: " + r.area());
    }
}
```

**How to run:** `java RectangleBasic.java`

Every member here is `public` — the fields, the method, and the class itself — meaning any other code anywhere could use this exact same `Rectangle` freely, directly setting its fields and calling `area()`.

### Level 2 — Intermediate

Same `Rectangle`, now with a `public` constructor requiring valid dimensions upfront, making the public interface both usable and safe.

```java
public class RectangleIntermediate {
    public static class Rectangle {
        public double width;
        public double height;

        public Rectangle(double width, double height) {
            if (width <= 0 || height <= 0) {
                throw new IllegalArgumentException("Dimensions must be positive");
            }
            this.width = width;
            this.height = height;
        }

        public double area() {
            return width * height;
        }
    }

    public static void main(String[] args) {
        Rectangle r = new Rectangle(4, 5);
        System.out.println("Area: " + r.area());

        try {
            new Rectangle(-1, 5);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java RectangleIntermediate.java`

The `public` constructor is the intended, documented way for any outside code to create a valid `Rectangle` — it validates its inputs immediately, so any code anywhere that uses this public interface correctly can trust that a successfully-constructed `Rectangle` always has positive dimensions.

### Level 3 — Advanced

Same `Rectangle`, now with fields made non-public (a preview of encapsulation, covered fully in a later topic) while keeping the constructor and essential methods `public`, demonstrating a class whose public interface is deliberately narrower than its full internal structure.

```java
public class RectangleAdvanced {
    public static class Rectangle {
        private double width;  // implementation detail, not directly public
        private double height; // implementation detail, not directly public

        public Rectangle(double width, double height) { // public: the supported way to create one
            if (width <= 0 || height <= 0) {
                throw new IllegalArgumentException("Dimensions must be positive");
            }
            this.width = width;
            this.height = height;
        }

        public double area() { // public: part of the supported interface
            return width * height;
        }

        public double perimeter() { // public: part of the supported interface
            return 2 * (width + height);
        }
    }

    public static void main(String[] args) {
        Rectangle r = new Rectangle(4, 5);
        System.out.println("Area: " + r.area());
        System.out.println("Perimeter: " + r.perimeter());
        // r.width; // would NOT compile from outside the Rectangle class — width is private now
    }
}
```

**How to run:** `java RectangleAdvanced.java`

Outside code can only interact with a `Rectangle` through its `public` constructor and `public` methods (`area()`, `perimeter()`) — the actual `width` and `height` fields are hidden implementation details, which means their internal representation could later change (say, storing area directly instead of separate width/height) without breaking any code that only ever used the public interface.

## 6. Walkthrough

Trace `new Rectangle(4, 5)` followed by `r.area()` and `r.perimeter()` from `RectangleAdvanced.main`:

**Construction.** `new Rectangle(4, 5)` calls the `public` constructor with `width = 4`, `height = 5`. Validation passes (`4 > 0`, `5 > 0`). `this.width = 4`, `this.height = 5` — but these are now `private` fields, invisible to `main` directly.

**`r.area()`.** This `public` method reads `width * height` — from *inside* the `Rectangle` class, `private` fields are fully accessible, since access restrictions apply to code *outside* the class, not to the class's own methods. Returns `4 * 5 = 20.0`.

**`r.perimeter()`.** Similarly reads `2 * (width + height) = 2 * (4 + 5) = 18.0`.

```
new Rectangle(4, 5): width=4, height=5 (private, hidden from main)
r.area()      -> width * height = 20.0        (computed via public method)
r.perimeter() -> 2*(width+height) = 18.0       (computed via public method)
```

**Final output.** `"Area: 20.0"` then `"Perimeter: 18.0"` — `main` never directly touches `width` or `height`; it only ever goes through the `public` constructor and `public` methods, exactly as the class's author intended.

## 7. Gotchas & takeaways

> **Making everything `public` by default (fields included) removes the ability to change a class's internal representation later without breaking every piece of code that directly used those fields.** Once a field is `public`, any external code might already be reading or writing it directly, so narrowing it to `private` later is a breaking change — this is why starting with the most restrictive access level and only widening deliberately is the safer default habit.

> **`public` on a top-level class requires the file name to exactly match the class name** (`Rectangle.java` for `public class Rectangle`), and a single `.java` file may contain at most one `public` top-level class — a rule the compiler enforces strictly.

- `public` is the least restrictive access level: accessible from any class, in any package.
- Mark a class, method, constructor, or field `public` specifically when it's part of the intended, external interface other code should depend on.
- Keeping fields non-public while exposing behaviour through public methods (as in the advanced example) allows internal representation to change safely later.
- A single source file can contain at most one `public` top-level class, and that file's name must match the class's name exactly.
