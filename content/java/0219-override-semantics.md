---
card: java
gi: 219
slug: override-semantics
title: '@Override semantics'
---

## 1. What it is

`@Override` is an **annotation** — a compile-time marker with no runtime effect on its own — that you place directly above a method to declare "I intend this to override an inherited method." The compiler then verifies that a matching method actually exists in some superclass or implemented interface; if it doesn't (due to a typo, wrong parameter types, or any signature mismatch), the compiler reports an error immediately, rather than silently letting the method become an unrelated new overload.

```java
class Animal {
    String makeSound() {
        return "...";
    }
}

class Dog extends Animal {
    @Override
    String makeSound() { // compiler checks: does Animal (or an ancestor) really have a matching makeSound()? Yes.
        return "Woof";
    }

    @Override
    // String makeSund() { return "Meow"; } // COMPILE ERROR if uncommented: no such method to override (typo!)
}
```

Without `@Override`, a typo like `makeSund()` (missing an `o`) would compile just fine as a brand-new, unrelated method on `Dog` — it simply wouldn't override anything, and any code expecting polymorphic behaviour would silently keep calling `Animal`'s original `makeSound()` instead; `@Override` turns this entire category of silent mistake into a loud compile-time error.

## 2. Why & when

`@Override` exists purely to catch a specific, easy-to-make mistake: writing what you *believe* is an override, but which the compiler actually treats as something else entirely because the signature doesn't quite match:

- **Typos in method names** — `getname()` instead of `getName()`, or `equal()` instead of `equals()`, both compile silently without `@Override`, quietly creating a useless new method instead of the intended override.
- **Parameter type mismatches** — overriding `void process(int x)` when the superclass actually declares `void process(long x)` creates an overload, not an override, since the parameter types don't match exactly.
- **Refactoring safety** — if a superclass method is later renamed or its signature changes, every subclass override marked `@Override` immediately fails to compile, loudly surfacing every place that needs updating, rather than silently leaving stale, now-disconnected methods behind.

You should annotate **every** intended override with `@Override`, as a matter of habit — there's no downside to it, and it converts an entire class of quiet, hard-to-debug mistakes into immediate, clear compiler errors.

## 3. Core concept

```java
class Shape {
    double area() {
        return 0.0;
    }
}

class Circle extends Shape {
    double radius;
    Circle(double radius) { this.radius = radius; }

    @Override
    double area() { // matches Shape's area() exactly — compiles fine
        return Math.PI * radius * radius;
    }
}

// class BrokenCircle extends Shape {
//     double radius;
//     @Override
//     double area(int precision) { // COMPILE ERROR — Shape has no area(int); this doesn't override anything
//         return Math.PI * radius * radius;
//     }
// }
```

`BrokenCircle`'s `area(int precision)` has a different parameter list than `Shape`'s `area()` — without `@Override`, this would silently compile as an unrelated new method that happens to share a name; with `@Override` present, the compiler immediately flags the mismatch, since no method matching this exact signature exists anywhere in `Shape`.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two scenarios compared: a correctly annotated override that compiles successfully because the compiler finds a matching signature in the superclass, and a mistyped or mismatched method also annotated with Override that fails to compile because no matching method exists to override">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="30" y="30" width="250" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Override area()</text>
  <text x="155" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">compiler finds matching</text>
  <text x="155" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Shape.area() -&gt; compiles OK</text>

  <rect x="320" y="30" width="250" height="90" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="445" y="50" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">@Override area(int)</text>
  <text x="445" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no matching method in Shape</text>
  <text x="445" y="85" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">-&gt; COMPILE ERROR, caught immediately</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Override converts a silent, hard-to-find bug into a loud, immediate compiler error.</text>
</svg>

`@Override` forces the compiler to verify a matching method genuinely exists to override.

## 5. Runnable example

Scenario: a small logging framework with a customizable formatting method — starting with a basic correctly-annotated override, then extending to demonstrate a caught mistake using `@Override`, then hardening into a case showing `@Override` working correctly across a multi-level hierarchy.

### Level 1 — Basic

```java
public class OverrideAnnotationBasic {
    static class Logger {
        String format(String message) {
            return "[LOG] " + message;
        }
    }

    static class TimestampLogger extends Logger {
        @Override
        String format(String message) { // exact match: compiles cleanly
            return "[2024-01-01] " + message;
        }
    }

    public static void main(String[] args) {
        Logger log = new TimestampLogger();
        System.out.println(log.format("Server started"));
    }
}
```

**How to run:** `java OverrideAnnotationBasic.java`

`TimestampLogger.format(String)` matches `Logger.format(String)` exactly — the `@Override` annotation confirms this to the compiler, and the program runs printing the customized, timestamped format.

### Level 2 — Intermediate

The same scenario, now showing what would happen (as a comment, since it wouldn't compile if left active) if a mistake were made — demonstrating exactly the kind of error `@Override` is designed to catch.

```java
public class OverrideAnnotationIntermediate {
    static class Logger {
        String format(String message) {
            return "[LOG] " + message;
        }
    }

    static class TimestampLogger extends Logger {
        @Override
        String format(String message) { // correct: matches exactly
            return "[2024-01-01] " + message;
        }

        // The following, if uncommented, would NOT compile:
        // @Override
        // String Format(String message) { // capital F — a typo! Does not override anything.
        //     return "[BROKEN] " + message;
        // }
    }

    public static void main(String[] args) {
        Logger log = new TimestampLogger();
        System.out.println(log.format("Order placed"));
    }
}
```

**How to run:** `java OverrideAnnotationIntermediate.java`

The commented-out `Format` (capitalized, a typo for `format`) would, if actually written and left uncommented, fail to compile specifically *because* of the `@Override` annotation — the compiler would report that no method named `Format(String)` exists to override in `Logger`, catching the typo immediately rather than allowing a silent, unused extra method to exist alongside the real, correctly-spelled `format`.

### Level 3 — Advanced

Same logging system, now with a three-level hierarchy where a middle class overrides once, and a further subclass overrides again — demonstrating `@Override` working correctly across multiple levels, always checking against whatever the *nearest* ancestor with a matching method actually declares.

```java
public class OverrideAnnotationAdvanced {
    static class Logger {
        String format(String message) {
            return "[LOG] " + message;
        }
    }

    static class TimestampLogger extends Logger {
        @Override
        String format(String message) { // overrides Logger's version
            return "[2024-01-01] " + message;
        }
    }

    static class JsonTimestampLogger extends TimestampLogger {
        @Override
        String format(String message) { // overrides TimestampLogger's version (which itself overrode Logger's)
            return "{\"time\":\"2024-01-01\",\"msg\":\"" + message + "\"}";
        }
    }

    public static void main(String[] args) {
        Logger plain = new Logger();
        Logger timestamped = new TimestampLogger();
        Logger json = new JsonTimestampLogger();

        System.out.println(plain.format("Event"));
        System.out.println(timestamped.format("Event"));
        System.out.println(json.format("Event"));
    }
}
```

**How to run:** `java OverrideAnnotationAdvanced.java`

`JsonTimestampLogger.format` is annotated `@Override` and matches `TimestampLogger.format`'s signature — the compiler verifies against the nearest ancestor that declares a matching method, which happens to be `TimestampLogger` here, not directly `Logger`; each call in `main` correctly dispatches to the actual runtime type's own `format` implementation, regardless of the reference's declared type (`Logger` in every case here).

## 6. Walkthrough

Trace all three calls in `OverrideAnnotationAdvanced.main`:

**`plain.format("Event")`.** `plain` is declared `Logger` and actually *is* a plain `Logger` object — its own `format` runs, returning `"[LOG] Event"`.

**`timestamped.format("Event")`.** `timestamped` is declared `Logger` but is actually a `TimestampLogger` object — dynamic dispatch runs `TimestampLogger`'s overriding `format`, returning `"[2024-01-01] Event"`.

**`json.format("Event")`.** `json` is declared `Logger` but is actually a `JsonTimestampLogger` object — dynamic dispatch runs `JsonTimestampLogger`'s overriding `format` (which itself overrides `TimestampLogger`'s, which overrides `Logger`'s), returning `"{\"time\":\"2024-01-01\",\"msg\":\"Event\"}"`.

```
plain (actual type Logger)              -> Logger.format()              -> "[LOG] Event"
timestamped (actual type TimestampLogger) -> TimestampLogger.format()    -> "[2024-01-01] Event"
json (actual type JsonTimestampLogger)    -> JsonTimestampLogger.format() -> "{\"time\":\"2024-01-01\",\"msg\":\"Event\"}"
```

**Final output.** Three lines, one per call, each dispatching correctly to that specific object's own most-derived `format` override — `@Override` on each subclass's method confirmed at compile time that each one genuinely does override something real, further up its own particular chain of ancestors.

## 7. Gotchas & takeaways

> **`@Override` has zero effect on runtime behaviour — it is purely a compile-time check.** Removing it from a correctly-matching override changes nothing about how the program runs; its entire value is catching mistakes *before* the program ever runs, at compile time, when a mismatch exists.

> **`@Override` also correctly applies when implementing a method declared in an interface** (a topic covered separately) — not just for overriding a superclass's method; the same "does a matching method genuinely exist above this one" check applies in both cases.

- `@Override` tells the compiler to verify that a matching method genuinely exists to be overridden, catching typos and signature mismatches immediately.
- Without `@Override`, a mismatched method silently becomes an unrelated new method or overload, with no compiler warning by default.
- Always annotate every intended override with `@Override` — there is no downside, and it converts a whole class of silent bugs into loud compile errors.
- `@Override` has no runtime effect of its own; its value is entirely in the compile-time verification it triggers.
