---
card: java
gi: 742
slug: pattern-matching-for-switch-standardized
title: Pattern matching for switch — standardized
---

## 1. What it is

**Java 21** (JEP 441) standardizes **pattern matching for `switch`** after four preview rounds spanning Java 17 through 20. A `switch` statement or expression can now use `case` labels that are **type patterns** (`case Circle c ->`) or [record patterns](0740-record-patterns-standardized.md) (`case Rectangle(Point tl, Point br) ->`), not just constants. Combined with a sealed type hierarchy, the compiler can also verify the switch handles every possible case — see [exhaustiveness checking](0745-exhaustiveness-checking-in-switch.md) — turning `switch` into a general-purpose, compiler-checked "what kind of thing is this, and what are its parts" dispatch mechanism.

## 2. Why & when

Classic Java `switch` only worked on a narrow set of types — `int`, `String`, `enum` — and only ever tested for exact equality against a constant. Any code that needed to branch on an object's *type* had to use a chain of `if (x instanceof A) ... else if (x instanceof B) ...`, which is verbose, easy to get wrong (missing a case silently falls to a catch-all `else`), and gives the compiler no way to check completeness. Pattern matching for switch turns type-based dispatch into a first-class language construct: each `case` names a type (optionally destructuring it via a record pattern), the compiler picks the first matching case in order, and — critically — when the switch operates over a `sealed` type, the compiler proves at compile time that every subtype is handled, so adding a new subtype later produces compile errors at every switch that needs updating, instead of a runtime bug from a forgotten `else if`. This is the natural implementation vehicle for algebraic-style data modeling in Java: a sealed interface plus record implementations plus a pattern-matching switch is Java's version of what other languages call "sum types with pattern matching."

## 3. Core concept

```java
sealed interface Shape permits Circle, Square {}
record Circle(double radius) implements Shape {}
record Square(double side) implements Shape {}

static double area(Shape shape) {
    return switch (shape) {
        case Circle c -> Math.PI * c.radius() * c.radius();
        case Square s -> s.side() * s.side();
        // no default needed — Circle and Square are the only permitted subtypes
    };
}
```

The compiler knows `Shape` permits exactly `Circle` and `Square`; since both are handled, this `switch` expression is exhaustive without a `default` arm.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A switch on a sealed type dispatches to the case matching the value's runtime type, with the compiler verifying every permitted subtype is covered">
  <rect x="20" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">shape: Shape</text>

  <line x1="180" y1="45" x2="240" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow742)"/>
  <defs><marker id="arrow742" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="250" y="20" width="150" height="50" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="325" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">switch (shape) {...}</text>

  <line x1="325" y1="70" x2="200" y2="110" stroke="#8b949e"/>
  <line x1="325" y1="70" x2="450" y2="110" stroke="#8b949e"/>

  <rect x="120" y="110" width="160" height="40" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="200" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">case Circle c -&gt; ...</text>
  <rect x="370" y="110" width="160" height="40" rx="6" fill="#0f1620" stroke="#8b949e"/>
  <text x="450" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">case Square s -&gt; ...</text>

  <text x="325" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Compiler proves: every Shape subtype has a matching arm</text>
</svg>

*Sealed hierarchy + pattern-matching switch = compiler-checked exhaustive dispatch by type.*

## 5. Runnable example

Scenario: a small event-processing dispatcher that grows from a two-branch `if/else` chain into a full pattern-matching switch over a sealed hierarchy.

### Level 1 — Basic

```java
public class DispatchIfElse {
    sealed interface Event permits Login, Logout {}
    record Login(String user) implements Event {}
    record Logout(String user) implements Event {}

    static String describe(Event event) {
        if (event instanceof Login l) {
            return l.user() + " logged in";
        } else if (event instanceof Logout l) {
            return l.user() + " logged out";
        }
        return "unknown event";
    }

    public static void main(String[] args) {
        System.out.println(describe(new Login("ada")));
        System.out.println(describe(new Logout("ada")));
    }
}
```

**How to run:** `java DispatchIfElse.java` (JDK 21+).

This is the pre-pattern-matching style: an `if/else` chain of `instanceof` checks, plus a redundant final `return "unknown event"` that the compiler can't verify is actually unreachable.

### Level 2 — Intermediate

```java
public class DispatchSwitch {
    sealed interface Event permits Login, Logout {}
    record Login(String user) implements Event {}
    record Logout(String user) implements Event {}

    static String describe(Event event) {
        return switch (event) {
            case Login(String user) -> user + " logged in";
            case Logout(String user) -> user + " logged out";
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(new Login("ada")));
        System.out.println(describe(new Logout("ada")));
    }
}
```

**How to run:** `java DispatchSwitch.java`.

The real-world concern added: the `if/else` chain becomes a `switch` **expression** with record patterns destructuring each event directly in the `case` label, and — because `Event` is sealed with exactly `Login` and `Logout` permitted — the compiler proves the switch is exhaustive, so no `default` or fallback `return` is needed (or accepted).

### Level 3 — Advanced

```java
public class DispatchAdvanced {
    sealed interface Event permits Login, Logout, Purchase {}
    record Login(String user) implements Event {}
    record Logout(String user) implements Event {}
    record Purchase(String user, double amount) implements Event {}

    static String describe(Event event) {
        return switch (event) {
            case Login(String user) -> user + " logged in";
            case Logout(String user) -> user + " logged out";
            case Purchase(String user, double amount) when amount >= 100.0 ->
                user + " made a large purchase of $" + amount;
            case Purchase(String user, double amount) ->
                user + " made a purchase of $" + amount;
        };
    }

    public static void main(String[] args) {
        Event[] events = {
            new Login("ada"),
            new Purchase("ada", 42.50),
            new Purchase("ada", 250.00),
            new Logout("ada"),
        };
        for (Event e : events) {
            System.out.println(describe(e));
        }
    }
}
```

**How to run:** `java DispatchAdvanced.java`.

This adds the production-flavored hard case: a **third event type** (`Purchase`) plus a **guarded pattern** (`when amount >= 100.0`, covered in depth in [guarded patterns](0743-guarded-patterns-when-clauses.md)) that splits `Purchase` handling into two arms based on a runtime condition, not just type. The compiler still proves exhaustiveness across all three `Event` subtypes, even though `Purchase` now has two case labels between them.

## 6. Walkthrough

Tracing `DispatchAdvanced.main`:

1. `main` builds an array of four events: a login, a small purchase, a large purchase, and a logout.
2. The loop calls `describe(e)` for each, and inside `describe`, the `switch (event)` expression tests `event`'s runtime type against each `case` **in textual order**.
3. For `new Login("ada")`: the first case, `Login(String user)`, matches — `event` is a `Login`, and its single component is destructured into `user = "ada"`. The arm evaluates to `"ada logged in"`, immediately returned as the switch expression's value.
4. For `new Purchase("ada", 42.50)`: the `Login` and `Logout` cases don't match (wrong type). The third case, `Purchase(String user, double amount) when amount >= 100.0`, matches the *type* but the **guard** `amount >= 100.0` evaluates to `false` (42.50 < 100.0), so this case is skipped even though the pattern matched. The switch falls through to the fourth case, the unguarded `Purchase(String user, double amount)`, which always matches once the type and destructure succeed — producing `"ada made a purchase of $42.5"`.
5. For `new Purchase("ada", 250.00)`: the guarded case's pattern matches **and** its guard `250.00 >= 100.0` is `true`, so this arm wins, producing `"ada made a large purchase of $250.0"`. The unguarded `Purchase` case below it is never reached for this value.
6. For `new Logout("ada")`: `Logout(String user)` matches, producing `"ada logged out"`.

Expected output:
```
ada logged in
ada made a purchase of $42.5
ada made a large purchase of $250.0
ada logged out
```

## 7. Gotchas & takeaways

> **Gotcha:** case order matters when patterns overlap, exactly like a guarded `Purchase` case followed by an unguarded one. If the unguarded `Purchase(String user, double amount)` case were listed **before** the guarded one, it would match every `Purchase` first and the guarded case would become unreachable dead code — the compiler does flag genuinely unreachable cases like this as an error, so this particular mistake gets caught, but it's worth understanding *why* order matters rather than relying only on the compiler to save you.

- Standardized in Java 21 — production-ready, no preview flag.
- Works together with `sealed` hierarchies for compiler-verified exhaustive dispatch — see [exhaustiveness checking](0745-exhaustiveness-checking-in-switch.md).
- Combine with record patterns to destructure and dispatch in one expression.
- Guarded patterns (`when` clauses) let you refine a type-based case with a runtime condition without leaving the switch — see [guarded patterns](0743-guarded-patterns-when-clauses.md).
- `case` order is significant: put more specific or guarded patterns before more general ones that would otherwise shadow them.
