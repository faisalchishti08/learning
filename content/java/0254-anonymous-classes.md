---
card: java
gi: 254
slug: anonymous-classes
title: Anonymous classes
---

## 1. What it is

An anonymous class is a class with no name at all, defined and instantiated in a single expression, typically to provide a one-off implementation of an interface or to extend a class on the spot. It combines declaration and instantiation into one step: `new SomeType() { ... }`, where `SomeType` is either an interface being implemented or a class being extended, and the `{ ... }` body supplies the implementation immediately.

```java
interface Greeter {
    void greet();
}

public class AnonymousDemo {
    public static void main(String[] args) {
        Greeter g = new Greeter() { // anonymous class: implements Greeter with no separate named class
            @Override
            public void greet() {
                System.out.println("Hello from an anonymous class!");
            }
        };
        g.greet();
    }
}
```

`new Greeter() { ... }` simultaneously declares an unnamed class implementing `Greeter` and creates exactly one instance of it, assigned to `g` — there is no `class SomethingImplementsGreeter { ... }` declared anywhere else; the entire class exists only inline, at this one point in the code.

## 2. Why & when

Anonymous classes exist for exactly the situation a local class (the previous topic) handles, but taken one step further: when you need only a *single instance* of a one-off implementation, and giving it a name would add no value.

- **One-off implementations used exactly once** — if a class exists purely to be instantiated a single time, right where it's needed, an anonymous class avoids the ceremony of declaring a separate named class (local or otherwise) just for that one use.
- **Historical event-handling and callback style** — before lambda expressions (Java 8), anonymous classes were the standard way to implement single-method interfaces inline, especially for GUI event listeners and simple callback interfaces — you may still see this style in older code and in situations needing more than a lambda can express (see the gotchas).
- **Extending a class, not just implementing an interface** — unlike a lambda (which only works for functional interfaces, one abstract method), an anonymous class can extend a concrete or abstract class, overriding one or more of its methods on the spot, which lambdas cannot do at all.

Prefer an anonymous class when you need a one-off implementation used exactly once and either the target type is not a functional interface (has more than one abstract method, or you're extending a class rather than implementing an interface) or you need capabilities a lambda lacks (like referring to `this` meaning the anonymous class itself, or declaring additional fields); for simple functional interfaces, a lambda expression (covered in dedicated topics) is almost always more concise and preferred in modern code.

## 3. Core concept

```java
abstract class Shape {
    abstract double area();
    void describe() { System.out.println("Area: " + area()); }
}

public class AnonymousCore {
    public static void main(String[] args) {
        Shape circle = new Shape() { // anonymous class EXTENDING an abstract class
            double radius = 3.0; // anonymous classes CAN have their own fields
            @Override
            double area() { return Math.PI * radius * radius; }
        };
        circle.describe(); // "Area: 28.27..."
    }
}
```

The anonymous class here extends the abstract class `Shape` (not an interface), overriding its one abstract method `area()`, and even declares its own field, `radius` — capabilities entirely unavailable to a lambda expression, which can only implement a single-method functional interface and has no way to declare additional state of its own.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An anonymous class declaration and instantiation happen in one single expression, producing exactly one unnamed instance assigned directly to a variable">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="60" y="20" width="480" height="90" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="300" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Greeter g = new Greeter() {</text>
  <rect x="90" y="52" width="420" height="35" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="73" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">public void greet() { ... } // supplied inline</text>
  <text x="300" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">};</text>

  <text x="300" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Declaration and single instantiation combined into one expression — no separate class name exists.</text>
</svg>

An anonymous class declares and instantiates its single instance in one combined expression.

## 5. Runnable example

Scenario: a button-click simulation using an anonymous listener, evolved from a basic one-off handler into one capturing enclosing state, then hardened into a case using anonymous-class-only capabilities (its own field and `this`) that a lambda could not replicate.

### Level 1 — Basic

```java
public class AnonymousBasic {
    interface ClickListener {
        void onClick();
    }

    static void simulateClick(ClickListener listener) {
        System.out.println("Button clicked!");
        listener.onClick();
    }

    public static void main(String[] args) {
        simulateClick(new ClickListener() { // anonymous class passed directly as an argument
            @Override
            public void onClick() {
                System.out.println("Handled by an anonymous class!");
            }
        });
    }
}
```

**How to run:** `java AnonymousBasic.java`

The anonymous `ClickListener` implementation is created and passed directly as an argument to `simulateClick`, with no intermediate variable or named class needed at all — this is one of the most common patterns for anonymous classes: providing a one-off callback right at the call site.

### Level 2 — Intermediate

Same click simulation, now with the anonymous class capturing an effectively-final enclosing variable, demonstrating that anonymous classes (like local classes) can read outer local state directly.

```java
public class AnonymousIntermediate {
    interface ClickListener {
        void onClick();
    }

    static void simulateClick(ClickListener listener) {
        listener.onClick();
    }

    public static void main(String[] args) {
        String buttonName = "Submit"; // effectively final — never reassigned after this point

        simulateClick(new ClickListener() {
            @Override
            public void onClick() {
                System.out.println(buttonName + " button was clicked"); // captures the enclosing variable
            }
        });
    }
}
```

**How to run:** `java AnonymousIntermediate.java`

The anonymous class's `onClick` reads `buttonName` directly from the enclosing `main` method — this is only legal because `buttonName` is effectively final (assigned once, never reassigned), a rule explored fully in the next topic.

### Level 3 — Advanced

Same scenario, now with the anonymous class tracking its own internal state (a click counter, a field the anonymous class declares for itself) and using `this` to refer to itself explicitly — both capabilities entirely unavailable to a plain lambda expression.

```java
public class AnonymousAdvanced {
    interface ClickListener {
        void onClick();
        int getClickCount();
    }

    public static void main(String[] args) {
        ClickListener listener = new ClickListener() {
            int clickCount = 0; // the anonymous class's OWN field — not captured from anywhere

            @Override
            public void onClick() {
                this.clickCount++; // 'this' refers to the anonymous class instance itself
                System.out.println("Click #" + this.clickCount);
            }

            @Override
            public int getClickCount() { return clickCount; }
        };

        listener.onClick();
        listener.onClick();
        listener.onClick();

        System.out.println("Total clicks recorded: " + listener.getClickCount());
    }
}
```

**How to run:** `java AnonymousAdvanced.java`

`clickCount` is a field declared directly inside the anonymous class body, not captured from any enclosing scope — it persists across multiple calls to `onClick` on the same `listener` instance, and `this.clickCount` unambiguously refers to the anonymous class's own field; a lambda expression could not declare this field or use `this` this way, since a lambda has no class body of its own to hold state in.

## 6. Walkthrough

Trace `main` in `AnonymousAdvanced` from the anonymous class's creation through the final print.

**`new ClickListener() { ... }`.** An anonymous class is declared and instantiated in one step, assigned to `listener`. Its field `clickCount` is initialized to `0` as part of construction.

**First `listener.onClick()`.** `this.clickCount++` increments `clickCount` from `0` to `1` (post-increment: the expression's value would be `0`, but here it's used as a statement, so only the side effect matters). Prints `"Click #1"` (using the now-incremented value, `1`, since the print statement runs after the increment completes).

**Second `listener.onClick()`.** `clickCount` increments from `1` to `2`. Prints `"Click #2"`.

**Third `listener.onClick()`.** `clickCount` increments from `2` to `3`. Prints `"Click #3"`.

**`listener.getClickCount()`.** Returns the current value of `clickCount`, which is `3`. The final line prints `"Total clicks recorded: 3"`.

```
new ClickListener() { clickCount = 0 } -> listener created

onClick() #1: clickCount 0 -> 1, prints "Click #1"
onClick() #2: clickCount 1 -> 2, prints "Click #2"
onClick() #3: clickCount 2 -> 3, prints "Click #3"

getClickCount() -> 3
```

**Final output.**
```
Click #1
Click #2
Click #3
Total clicks recorded: 3
```
This demonstrates that the anonymous class instance genuinely holds its own persistent state (`clickCount`) across multiple method calls, exactly like any ordinary object would — the class simply happens to have no name and was declared inline.

## 7. Gotchas & takeaways

> **An anonymous class cannot have a constructor of its own** (since it has no name to give the constructor), though it can use an instance initializer block (`{ ... }` with no method name) for setup logic, or rely on field initializers as shown with `clickCount = 0`. If you need constructor-like parameterization, a local class (which can have a named constructor) is the appropriate alternative.

> **Prefer a lambda expression over an anonymous class whenever the target is a functional interface (exactly one abstract method) and you don't need your own fields, multiple methods, or to extend a concrete class** — the `AnonymousBasic` example, in modern idiomatic code, would typically be written as `simulateClick(() -> System.out.println("Handled by a lambda!"))`, since `ClickListener` (in its single-method form) is a functional interface and no extra state or `this` semantics are needed.

- An anonymous class combines declaration and a single instantiation into one expression: `new Type() { ... }`, where `Type` is an interface or class being implemented or extended on the spot.
- It can declare its own fields and use `this` to refer to itself, capabilities a lambda expression does not have.
- It can extend a concrete or abstract class (not just implement an interface), overriding one or more methods inline — something lambdas cannot do at all.
- Prefer a lambda for simple functional-interface use cases; reach for an anonymous class when you need its own state, `this` semantics, multiple methods, or class extension.
