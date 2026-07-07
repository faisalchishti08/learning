---
card: java
gi: 371
slug: enums-implementing-interfaces
title: Enums implementing interfaces
---

## 1. What it is

An enum can `implements` one or more interfaces, exactly like a regular class — `enum Operator implements Calculable { ... }`. Every constant automatically becomes an instance of that interface, so you can pass an enum constant anywhere the interface type is expected, store different enums that share a common interface in the same collection, or let unrelated enums participate in the same polymorphic contract without any of them knowing about each other's existence.

## 2. Why & when

Constant-specific method bodies (see [[constant-specific-method-bodies]]) give each constant its own behaviour, but that behaviour is only reachable through the concrete enum type itself — code has to know it's dealing with `Operator` specifically. Implementing an interface decouples the *behaviour contract* from the *specific enum*: a method that accepts `Calculable` doesn't need to know or care whether it's being handed an `Operator` constant, a completely different enum, or even a plain class instance that also implements `Calculable`.

This matters whenever you want enum constants to plug into existing polymorphic code — implementing `Comparator` for custom sort orders, `Runnable` for constants that each represent an executable action, or your own domain interface shared between an enum and non-enum implementations. It also enables one particularly useful trick: since an enum cannot extend another class (it already implicitly extends `java.lang.Enum`), interfaces are the *only* way to give enum constants a shared type relationship with other, non-enum classes.

## 3. Core concept

```java
public class ShapeAreaDemo {
    interface HasArea {
        double area();
    }

    enum Shape implements HasArea {
        UNIT_SQUARE {
            @Override public double area() { return 1.0; }
        },
        UNIT_CIRCLE {
            @Override public double area() { return Math.PI; }
        }
    }

    static void printArea(HasArea shape) { // works for ANY HasArea, not just Shape
        System.out.printf("Area: %.4f%n", shape.area());
    }

    public static void main(String[] args) {
        printArea(Shape.UNIT_SQUARE);
        printArea(Shape.UNIT_CIRCLE);
    }
}
```

**How to run:** `java ShapeAreaDemo.java`

`Shape implements HasArea` means every `Shape` constant is also a `HasArea`. `printArea` is written entirely in terms of the interface — it never mentions `Shape` — so it would work unchanged if you later added a non-enum class that also implements `HasArea`, without touching `printArea` at all.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an enum implementing an interface makes every constant usable anywhere that interface type is expected, decoupling callers from the concrete enum type">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="240" y="25" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="47" fill="#79c0ff" font-size="11" text-anchor="middle">interface HasArea</text>

  <line x1="180" y1="90" x2="290" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a1)"/>
  <line x1="460" y1="90" x2="350" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a2)"/>

  <rect x="80" y="95" width="200" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="180" y="122" fill="#6db33f" font-size="10" text-anchor="middle">Shape.UNIT_SQUARE</text>

  <rect x="360" y="95" width="200" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="122" fill="#6db33f" font-size="10" text-anchor="middle">Shape.UNIT_CIRCLE</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <text x="20" y="160" fill="#8b949e" font-size="10">printArea(HasArea shape) accepts either constant -- it never needs to know about Shape specifically.</text>
</svg>

## 5. Runnable example

Scenario: a set of scheduled background actions, evolved from an enum whose constants can only be used as themselves, through implementing `Runnable` so constants plug into ordinary thread/executor APIs, to a version mixed with a genuinely non-enum `Runnable` in the same collection.

### Level 1 — Basic

```java
public class ActionBasic {
    enum Action {
        CLEANUP {
            void run() { System.out.println("Running cleanup"); }
        },
        BACKUP {
            void run() { System.out.println("Running backup"); }
        };

        abstract void run(); // own run() -- but NOT java.lang.Runnable, just a same-named method
    }

    public static void main(String[] args) {
        Action.CLEANUP.run();
        Action.BACKUP.run();
    }
}
```

**How to run:** `java ActionBasic.java`

This works, but `Action`'s `run()` is just a coincidentally-named method — nothing lets `Action` constants be handed to code that expects a real `java.lang.Runnable` (an `ExecutorService`, a `Thread` constructor), since `Action` doesn't actually implement that interface.

### Level 2 — Intermediate

```java
public class ActionRunnable {
    enum Action implements Runnable { // now genuinely a java.lang.Runnable
        CLEANUP {
            @Override public void run() { System.out.println("Running cleanup"); }
        },
        BACKUP {
            @Override public void run() { System.out.println("Running backup"); }
        }
    }

    static void execute(Runnable task) { // accepts ANY Runnable, not just Action
        task.run();
    }

    public static void main(String[] args) {
        execute(Action.CLEANUP);
        execute(Action.BACKUP);
    }
}
```

**How to run:** `java ActionRunnable.java`

`Action implements Runnable` means every constant is a genuine `java.lang.Runnable` — `execute` can be handed any `Runnable`, and `Action` constants qualify without `execute` needing to know `Action` exists at all. This is the same interface a real `Thread` or `ExecutorService.submit(...)` expects.

### Level 3 — Advanced

```java
import java.util.List;

public class ActionMixed {
    enum Action implements Runnable {
        CLEANUP { @Override public void run() { System.out.println("Running cleanup"); } },
        BACKUP { @Override public void run() { System.out.println("Running backup"); } }
    }

    static class LoggingTask implements Runnable { // a plain, non-enum Runnable
        private final String name;
        LoggingTask(String name) { this.name = name; }
        @Override public void run() { System.out.println("Logging task: " + name); }
    }

    public static void main(String[] args) {
        List<Runnable> tasks = List.of( // enum constants and a plain class, side by side
                Action.CLEANUP,
                new LoggingTask("audit"),
                Action.BACKUP
        );
        for (Runnable task : tasks) {
            task.run();
        }
    }
}
```

**How to run:** `java ActionMixed.java`

`List<Runnable>` holds `Action.CLEANUP` (an enum constant), a `LoggingTask` (an ordinary class instance), and `Action.BACKUP` side by side — because both implement the same interface, the list and the loop don't need to distinguish between them at all; this is the specific payoff enums-with-interfaces enables that constant-specific bodies alone cannot, since an enum can never be a superclass of a non-enum class.

## 6. Walkthrough

Execution starts in `main`. `List.of(Action.CLEANUP, new LoggingTask("audit"), Action.BACKUP)` builds an immutable three-element list typed as `List<Runnable>`. The first element is the `Action.CLEANUP` singleton constant; the second is a freshly constructed `LoggingTask` with `name = "audit"`; the third is `Action.BACKUP`.

The `for (Runnable task : tasks)` loop iterates this list in order. On the first iteration, `task` refers to `Action.CLEANUP`. `task.run()` is called — since `task`'s static type is `Runnable`, this is a polymorphic call resolved at runtime to whichever `run()` the actual object provides. The actual object is `Action.CLEANUP`, so its constant-specific `run()` body executes, printing `Running cleanup`.

On the second iteration, `task` refers to the `LoggingTask` instance. `task.run()` dispatches to `LoggingTask.run()`, which prints `Logging task: audit`.

On the third iteration, `task` refers to `Action.BACKUP`. `task.run()` dispatches to `BACKUP`'s own body, printing `Running backup`.

Nothing in the loop ever needed to check "is this an `Action` or a `LoggingTask`?" — the `Runnable` interface is the only thing the loop cares about, and both kinds of objects satisfy it identically.

Expected output:
```
Running cleanup
Logging task: audit
Running backup
```

## 7. Gotchas & takeaways

> An enum can implement any number of interfaces, but it can never `extends` another class — `java.lang.Enum` already occupies the single-superclass slot. If you need enum constants to share a type relationship with plain classes, interfaces are the only mechanism available.

- `enum X implements SomeInterface` makes every constant of `X` a genuine instance of `SomeInterface`, usable anywhere that interface type is expected.
- This decouples calling code from the concrete enum type — a method written against the interface works unchanged whether it's handed an enum constant or an ordinary class instance.
- Interfaces are the only way to give an enum a type relationship with non-enum classes, since enums cannot extend another class.
- Common uses include implementing `Comparator` for enum-based custom sort orders, or implementing `Runnable`/`Callable` for constants that represent discrete executable actions.
- Combine this with constant-specific method bodies (see [[constant-specific-method-bodies]]) when each constant's interface implementation needs genuinely different logic, not just different data.
