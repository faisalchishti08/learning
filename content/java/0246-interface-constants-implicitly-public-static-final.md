---
card: java
gi: 246
slug: interface-constants-implicitly-public-static-final
title: Interface constants (implicitly public static final)
---

## 1. What it is

Any field declared inside an interface is automatically `public`, `static`, and `final`, whether or not those keywords are written explicitly. This means interface "fields" are never per-instance mutable state — they are shared constants, exactly one value that exists once for the interface itself and can never be reassigned.

```java
interface PhysicsConstants {
    double GRAVITY = 9.8;          // implicitly: public static final double GRAVITY = 9.8;
    double SPEED_OF_LIGHT = 3e8;    // same — implicitly public static final
}

public class ConstantsDemo {
    public static void main(String[] args) {
        System.out.println(PhysicsConstants.GRAVITY);       // accessed via the interface name directly
        // PhysicsConstants.GRAVITY = 9.9; // COMPILE ERROR if uncommented — final, cannot reassign
    }
}
```

`GRAVITY` and `SPEED_OF_LIGHT` are written with no modifiers at all, yet both behave exactly as if declared `public static final` — accessible via `PhysicsConstants.GRAVITY` without ever creating an instance, and permanently fixed once assigned.

## 2. Why & when

Interface constants exist to let a group of related implementing classes (or any unrelated code, since they are `public`) share a single, fixed value defined in one place.

- **Sharing configuration values across implementers** — if several classes implementing the same interface need to agree on a shared limit, rate, or threshold, declaring it as an interface constant means every implementer (and any external caller) references the exact same value, with no risk of duplication or drift.
- **No instance required to access them** — because they are implicitly `static`, interface constants can be read directly through the interface name (`PhysicsConstants.GRAVITY`), without needing any object at all, similar to constants on a utility class.
- **Guaranteed immutability** — because they are implicitly `final`, an interface constant can never be reassigned by any implementing class, giving callers full confidence the value never changes at runtime.

Use interface constants sparingly and deliberately for values that are genuinely fixed and meaningfully tied to the interface's contract (an interface defining a rate-limited API might reasonably declare its `MAX_REQUESTS_PER_SECOND` this way); avoid using an interface purely as a dumping ground for unrelated constants (a well-known anti-pattern called the "constant interface pattern"), which the gotchas below examine.

## 3. Core concept

```java
interface RateLimited {
    int MAX_REQUESTS_PER_MINUTE = 60; // a constant meaningfully tied to this interface's contract
    boolean tryRequest();
}

class ApiClient implements RateLimited {
    int requestCount = 0;

    @Override
    public boolean tryRequest() {
        if (requestCount >= MAX_REQUESTS_PER_MINUTE) return false; // uses the constant directly, unqualified
        requestCount++;
        return true;
    }
}
```

Inside `ApiClient`, `MAX_REQUESTS_PER_MINUTE` is used without any qualifier at all, because implementing `RateLimited` makes the constant directly visible, exactly as if it were inherited — this is one of the few cases where a classic interface contributes something beyond a method signature: a genuinely shared, usable value.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A field declared inside an interface is implicitly public static final, accessible directly through the interface name with no instance required and never reassignable">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="150" y="20" width="300" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="45" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">double GRAVITY = 9.8;</text>

  <line x1="300" y1="60" x2="300" y2="80" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="120" y="85" width="360" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="107" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">is really: public static final double GRAVITY = 9.8;</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">No modifiers needed — the compiler adds public, static, and final automatically.</text>
</svg>

Every interface field is implicitly `public static final`, regardless of what modifiers (if any) are written.

## 5. Runnable example

Scenario: a simple game configuration shared across different game modes via interface constants, evolved from a single constant into several classes relying on shared, immutable values.

### Level 1 — Basic

```java
public class InterfaceConstantsBasic {
    interface GameRules {
        int MAX_PLAYERS = 4; // implicitly public static final
    }

    public static void main(String[] args) {
        System.out.println("Max players allowed: " + GameRules.MAX_PLAYERS);
    }
}
```

**How to run:** `java InterfaceConstantsBasic.java`

`GameRules.MAX_PLAYERS` is accessed directly through the interface name, with no instance of `GameRules` ever created — consistent with the constant being implicitly `static`.

### Level 2 — Intermediate

Same rules, now with a class implementing `GameRules` and using the constant directly (unqualified) inside its own logic, plus a second, unrelated class accessing it through the interface name.

```java
public class InterfaceConstantsIntermediate {
    interface GameRules {
        int MAX_PLAYERS = 4;
    }

    static class Lobby implements GameRules {
        int joinedCount = 0;

        boolean tryJoin() {
            if (joinedCount >= MAX_PLAYERS) return false; // unqualified: inherited via implements
            joinedCount++;
            return true;
        }
    }

    public static void main(String[] args) {
        Lobby lobby = new Lobby();
        for (int i = 1; i <= 5; i++) {
            boolean joined = lobby.tryJoin();
            System.out.println("Player " + i + " join attempt: " + (joined ? "accepted" : "rejected"));
        }
        // Also accessible without implementing the interface at all:
        System.out.println("Rule reference: " + GameRules.MAX_PLAYERS);
    }
}
```

**How to run:** `java InterfaceConstantsIntermediate.java`

`Lobby` uses `MAX_PLAYERS` unqualified inside `tryJoin`, since implementing `GameRules` brings the constant into scope directly; the fifth join attempt fails once `joinedCount` reaches `4`, demonstrating the constant actually gating real logic, not just being printed for display.

### Level 3 — Advanced

Same game system, now demonstrating the well-known "constant interface anti-pattern" pitfall: an unrelated class implementing `GameRules` purely to access its constants without using any actual capability — and the better, corrected approach using a `static` import or direct qualification instead.

```java
public class InterfaceConstantsAdvanced {
    interface GameRules {
        int MAX_PLAYERS = 4;
        int MIN_PLAYERS = 2;
    }

    // ANTI-PATTERN: implementing GameRules purely to avoid typing "GameRules." everywhere.
    // This class has NOTHING to do with game rules as a capability -- it's misusing inheritance
    // just to get unqualified constant access.
    static class ScoreBoardAntiPattern implements GameRules {
        void printLimits() {
            System.out.println("Anti-pattern access -> min: " + MIN_PLAYERS + ", max: " + MAX_PLAYERS);
        }
    }

    // BETTER: reference the constants explicitly through the interface name, no implements needed
    static class ScoreBoardCorrect {
        void printLimits() {
            System.out.println("Correct access -> min: " + GameRules.MIN_PLAYERS + ", max: " + GameRules.MAX_PLAYERS);
        }
    }

    public static void main(String[] args) {
        new ScoreBoardAntiPattern().printLimits(); // works, but ScoreBoardAntiPattern wrongly "is-a" GameRules
        new ScoreBoardCorrect().printLimits();      // works, and correctly has NO false is-a relationship

        System.out.println("ScoreBoardAntiPattern is-a GameRules: "
            + (new ScoreBoardAntiPattern() instanceof GameRules)); // true -- a misleading, unwanted relationship
        System.out.println("ScoreBoardCorrect is-a GameRules: "
            + (new ScoreBoardCorrect() instanceof Object && !(new ScoreBoardCorrect() instanceof GameRules)));
    }
}
```

**How to run:** `java InterfaceConstantsAdvanced.java`

Both classes print identical-looking output, but `ScoreBoardAntiPattern instanceof GameRules` is `true` — meaning code elsewhere could legally (and confusingly) treat a `ScoreBoardAntiPattern` as if it were a genuine `GameRules` implementer, even though it has no real relationship to game rules as a capability, purely because it implemented the interface just to shortcut constant access; `ScoreBoardCorrect` avoids this by referencing the constants explicitly through the interface name, with no misleading inheritance relationship at all.

## 6. Walkthrough

Trace `main` in `InterfaceConstantsAdvanced` line by line.

**`new ScoreBoardAntiPattern().printLimits()`.** `MIN_PLAYERS` and `MAX_PLAYERS` are used unqualified inside `printLimits`, resolving to `GameRules.MIN_PLAYERS` (2) and `GameRules.MAX_PLAYERS` (4) because `ScoreBoardAntiPattern implements GameRules`. Prints `"Anti-pattern access -> min: 2, max: 4"`.

**`new ScoreBoardCorrect().printLimits()`.** `GameRules.MIN_PLAYERS` and `GameRules.MAX_PLAYERS` are referenced explicitly through the interface name — `ScoreBoardCorrect` does not implement `GameRules` at all. Prints `"Correct access -> min: 2, max: 4"` — identical values, obtained without any inheritance relationship.

**`new ScoreBoardAntiPattern() instanceof GameRules`.** Since `ScoreBoardAntiPattern` declares `implements GameRules`, this check is `true` — any code that receives a `ScoreBoardAntiPattern` reference could legally treat it as a `GameRules`, even though nothing about a scoreboard conceptually "is-a" set of game rules; this is the crux of why the pattern is considered a misuse of interface inheritance.

**`new ScoreBoardCorrect() instanceof Object && !(new ScoreBoardCorrect() instanceof GameRules)`.** `instanceof Object` is trivially `true` (every object is-an `Object`). `new ScoreBoardCorrect() instanceof GameRules` is `false`, since `ScoreBoardCorrect` never implements it; negated, this is `true`. The `&&` of two `true` values is `true`.

```
ScoreBoardAntiPattern.printLimits() -> unqualified MIN_PLAYERS/MAX_PLAYERS (inherited via implements) -> 2, 4
ScoreBoardCorrect.printLimits()     -> GameRules.MIN_PLAYERS/MAX_PLAYERS (explicit qualification)     -> 2, 4

instanceof checks:
  ScoreBoardAntiPattern instanceof GameRules -> true  (misleading is-a relationship)
  ScoreBoardCorrect     instanceof GameRules -> false (no false relationship) -> negated -> true
```

**Final output.**
```
Anti-pattern access -> min: 2, max: 4
Correct access -> min: 2, max: 4
ScoreBoardAntiPattern is-a GameRules: true
ScoreBoardCorrect is-a GameRules: true
```

## 7. Gotchas & takeaways

> **Implementing an interface purely to get unqualified access to its constants is a well-known anti-pattern (the "constant interface pattern")** — it creates a false "is-a" relationship (as demonstrated by `ScoreBoardAntiPattern instanceof GameRules` being `true`) between classes that have no real conceptual connection, and pollutes the class's public type with an implementation detail. Reference constants explicitly through the interface name (`GameRules.MAX_PLAYERS`) instead, or place truly general-purpose constants on a plain final class of their own.

> **Interface fields cannot be left uninitialized** — since they are implicitly `final`, every interface field must be assigned a value directly in its declaration; there is no interface equivalent of a constructor to initialize them later, unlike `final` instance fields on a regular class.

- Every field declared in an interface is implicitly `public`, `static`, and `final` — a shared, immutable constant, never per-instance state.
- Interface constants are accessible directly through the interface name, with no instance required, and can never be reassigned.
- A class implementing the interface can reference its constants unqualified, as if inherited, but this convenience should not be the sole reason to implement an interface.
- Avoid the "constant interface" anti-pattern: prefer explicit qualification (`InterfaceName.CONSTANT`) over implementing an interface purely for constant access.
