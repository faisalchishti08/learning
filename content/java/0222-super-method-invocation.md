---
card: java
gi: 222
slug: super-method-invocation
title: super.method() invocation
---

## 1. What it is

`super.method()` explicitly calls the superclass's version of a method from within a subclass, even when the subclass has overridden that same method — it's the mechanism for a subclass to say "run the *original* behaviour, in addition to (or instead of, in some path) my own." This is distinct from `super.field` (accessing a hidden field) and `super(...)` (calling a superclass constructor) — `super.method()` specifically bypasses the subclass's own override to reach the superclass's implementation directly.

```java
class Animal {
    String makeSound() {
        return "...generic sound...";
    }
}

class Dog extends Animal {
    @Override
    String makeSound() {
        String base = super.makeSound(); // explicitly calls Animal's ORIGINAL version
        return base + " but specifically: Woof!";
    }
}

new Dog().makeSound(); // "...generic sound... but specifically: Woof!"
```

`super.makeSound()` inside `Dog`'s override calls `Animal`'s original implementation directly — without `super.`, writing plain `makeSound()` here would call `Dog`'s *own* overriding method again, causing infinite recursion, since a method call with no explicit target defaults to the current object's most-derived version.

## 2. Why & when

`super.method()` exists for the common pattern of **extending** rather than completely **replacing** inherited behaviour:

- **Augmenting instead of replacing** — an override often wants to do everything the superclass version does, *plus* something extra, rather than discarding the original behaviour entirely; `super.method()` lets the override call the original and build on top of its result.
- **Avoiding code duplication** — if the superclass's method already does most of what's needed, calling it via `super.method()` and adding just the delta avoids copy-pasting the superclass's logic into the override.
- **A common, idiomatic pattern in constructors and lifecycle-style methods** — many real-world overrides (like a `toString()` override that wants to include a superclass's fields alongside its own) naturally want "everything the superclass version produces, plus a bit more," which is exactly the shape `super.method()` supports.

You use `super.method()` specifically when an override's new behaviour is meant to build on top of the inherited behaviour, rather than completely discard it — if the override genuinely needs entirely different logic with nothing shared, it simply wouldn't call `super.method()` at all.

## 3. Core concept

```java
class Employee {
    String name;
    Employee(String name) { this.name = name; }

    String describe() {
        return "Employee: " + name;
    }
}

class Manager extends Employee {
    int teamSize;
    Manager(String name, int teamSize) {
        super(name);
        this.teamSize = teamSize;
    }

    @Override
    String describe() {
        return super.describe() + ", managing " + teamSize + " people"; // builds on the original
    }
}

Manager m = new Manager("Ann", 5);
System.out.println(m.describe()); // "Employee: Ann, managing 5 people"
```

`Manager.describe()` calls `super.describe()` to get `"Employee: Ann"` first, then appends its own additional detail — the final result combines both the superclass's original formatting logic and the subclass's own addition, without `Manager` needing to know or duplicate exactly how `Employee.describe()` formats the name.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Manager's overridden describe method calling super dot describe to retrieve Employee's original result first, then appending its own additional team size detail to build the final combined string">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="200" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Employee.describe() -&gt; "Employee: Ann"</text>

  <line x1="320" y1="55" x2="320" y2="75" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sm)"/>
  <text x="380" y="70" fill="#79c0ff" font-size="9" font-family="sans-serif">super.describe()</text>

  <rect x="150" y="80" width="340" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Manager.describe() combines:</text>
  <text x="320" y="118" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">"Employee: Ann" + ", managing 5 people"</text>

  <defs><marker id="sm" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

`super.method()` retrieves the superclass's original result, which the override then builds on top of.

## 5. Runnable example

Scenario: a small logging system where a specialized logger wants to keep the base formatting and add extra detail — starting with a basic `super.method()` call extending inherited behaviour, then extending with a case appending to a collection using the superclass's version, then hardening into a three-level hierarchy where each level augments the one below it.

### Level 1 — Basic

```java
public class SuperMethodBasic {
    static class Logger {
        String format(String message) {
            return "[LOG] " + message;
        }
    }

    static class DebugLogger extends Logger {
        @Override
        String format(String message) {
            return super.format(message) + " [DEBUG MODE]"; // extends, doesn't replace
        }
    }

    public static void main(String[] args) {
        Logger log = new DebugLogger();
        System.out.println(log.format("Something happened"));
    }
}
```

**How to run:** `java SuperMethodBasic.java`

`DebugLogger.format` calls `super.format(message)` to get `"[LOG] Something happened"`, then appends `" [DEBUG MODE]"` — the final printed result includes both the original formatting and the subclass's addition, without `DebugLogger` needing to duplicate the `"[LOG] "` prefix logic itself.

### Level 2 — Intermediate

Same idea, now with an override that calls `super.method()` as part of a larger operation involving other work before and after the call.

```java
import java.util.ArrayList;
import java.util.List;

public class SuperMethodIntermediate {
    static class Logger {
        List<String> history = new ArrayList<>();

        String format(String message) {
            String formatted = "[LOG] " + message;
            history.add(formatted);
            return formatted;
        }
    }

    static class DebugLogger extends Logger {
        @Override
        String format(String message) {
            System.out.println("About to format a debug message...");
            String result = super.format(message) + " [DEBUG MODE]"; // reuses history-tracking behaviour too
            System.out.println("Formatting complete.");
            return result;
        }
    }

    public static void main(String[] args) {
        DebugLogger log = new DebugLogger();
        System.out.println(log.format("Startup"));
        System.out.println("History size: " + log.history.size());
    }
}
```

**How to run:** `java SuperMethodIntermediate.java`

`super.format(message)` still runs `Logger`'s original logic, including adding the plain `"[LOG] Startup"` entry to `history` — `DebugLogger` gets this history-tracking behaviour "for free" by delegating to `super.format`, rather than needing to reimplement the `history.add(...)` call itself.

### Level 3 — Advanced

Same logging system, now with a three-level hierarchy — `Logger`, `DebugLogger`, `VerboseDebugLogger` — where each level's override calls `super.method()`, building up the final formatted string through successive layers of augmentation.

```java
public class SuperMethodAdvanced {
    static class Logger {
        String format(String message) {
            return "[LOG] " + message;
        }
    }

    static class DebugLogger extends Logger {
        @Override
        String format(String message) {
            return super.format(message) + " [DEBUG]";
        }
    }

    static class VerboseDebugLogger extends DebugLogger {
        @Override
        String format(String message) {
            return super.format(message) + " [VERBOSE]"; // calls DebugLogger's format, which itself calls Logger's
        }
    }

    public static void main(String[] args) {
        Logger log = new VerboseDebugLogger();
        System.out.println(log.format("System check"));
    }
}
```

**How to run:** `java SuperMethodAdvanced.java`

`VerboseDebugLogger.format` calls `super.format(message)`, which resolves to `DebugLogger.format` (the nearest ancestor's override), which itself calls `super.format(message)`, resolving further up to `Logger.format` — three layers of formatting compose together in sequence, each one appending its own suffix to whatever the layer below it produced.

## 6. Walkthrough

Trace `log.format("System check")` from `SuperMethodAdvanced.main`, where `log` is declared `Logger` but actually holds a `VerboseDebugLogger`:

**Dispatch to the most-derived override.** Since `log`'s actual runtime type is `VerboseDebugLogger`, calling `.format(...)` runs `VerboseDebugLogger.format` first (dynamic dispatch, covered fully in the next topic).

**`VerboseDebugLogger.format` runs.** Its first action is `super.format(message)` — this explicitly calls `DebugLogger.format` (the next class up the chain from `VerboseDebugLogger`), not `Logger.format` directly, and *not* `VerboseDebugLogger.format` itself again (which would cause infinite recursion).

**`DebugLogger.format` runs.** Its first action is `super.format(message)` — this calls `Logger.format` (the next class up from `DebugLogger`). `Logger.format` returns `"[LOG] System check"` directly, with no further `super` calls, since `Logger` is the top of this hierarchy.

**Back in `DebugLogger.format`.** It receives `"[LOG] System check"` from its `super.format(message)` call, and appends `" [DEBUG]"`, producing `"[LOG] System check [DEBUG]"`. This is returned back up to `VerboseDebugLogger.format`.

**Back in `VerboseDebugLogger.format`.** It receives `"[LOG] System check [DEBUG]"` from its `super.format(message)` call, and appends `" [VERBOSE]"`, producing the final result: `"[LOG] System check [DEBUG] [VERBOSE]"`.

```
VerboseDebugLogger.format("System check")
  -> super.format(...) calls DebugLogger.format("System check")
       -> super.format(...) calls Logger.format("System check")
            returns "[LOG] System check"
       DebugLogger appends " [DEBUG]"  -> "[LOG] System check [DEBUG]"
  VerboseDebugLogger appends " [VERBOSE]" -> "[LOG] System check [DEBUG] [VERBOSE]"
```

**Final output.** `"[LOG] System check [DEBUG] [VERBOSE]"` — a single string built up through three successive layers, each contributing its own piece via `super.method()`, without any layer needing to know or duplicate what the layers below it actually do.

## 7. Gotchas & takeaways

> **`super.method()` always calls the method exactly one level up from the class whose code is currently executing — never all the way to the top of the hierarchy directly, and never back down to a more-derived override.** Inside `VerboseDebugLogger.format`, `super.format(...)` reaches `DebugLogger.format`, not `Logger.format` directly — the multi-level effect only happens because `DebugLogger.format` *itself* also calls `super.format(...)`, chaining one level further up in turn.

> **Calling a method without `super.` inside an override always calls the current object's own most-derived version — never the superclass's, even from within a method that's itself an override.** Confusing this is what leads to infinite recursion if `super.` is accidentally omitted where it was needed (writing plain `format(message)` inside `DebugLogger.format` would call `DebugLogger.format` again, infinitely, rather than reaching `Logger`'s version).

- `super.method()` explicitly calls the immediately-next-higher class's version of a method, bypassing the current class's own override.
- It's the standard pattern for extending inherited behaviour — running the original logic and adding something on top — rather than fully replacing it.
- In a multi-level hierarchy, each `super.method()` call reaches exactly one level up; chaining through several ancestors requires each level to also call `super.method()` in turn.
- Omitting `super.` inside an override and calling the method plainly always invokes the current object's own most-derived version, which can cause infinite recursion if that happens to be the very method currently executing.
