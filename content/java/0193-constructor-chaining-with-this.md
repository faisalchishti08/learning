---
card: java
gi: 193
slug: constructor-chaining-with-this
title: Constructor chaining with this()
---

## 1. What it is

**Constructor chaining** is the pattern, introduced briefly in the previous topic, of one constructor calling another constructor in the same class via `this(...)`. This topic looks at the mechanics in more depth: `this(...)` must be the constructor's first statement, the compiler resolves which overload it targets using the same overload-resolution rules as any method call, and a chain can run through several constructors before reaching the one that actually assigns every field.

```java
class Coordinate {
    int x, y, z;

    Coordinate(int x, int y, int z) {
        this.x = x; this.y = y; this.z = z;
    }

    Coordinate(int x, int y) {
        this(x, y, 0); // chains to the three-arg constructor
    }

    Coordinate() {
        this(0, 0); // chains to the two-arg constructor, which itself chains further
    }
}
```

`new Coordinate()` triggers a chain: the no-arg constructor calls `this(0, 0)`, which matches the two-arg constructor, which itself calls `this(x, y, 0)`, matching the three-arg constructor — three constructors run in sequence for a single `new Coordinate()` call, each one just adding a default before delegating further.

## 2. Why & when

Chaining constructors avoids scattering the same initialization or validation logic across every overload, keeping a single source of truth for how an object actually gets built:

- **One place for the real logic** — only the "most complete" constructor needs to contain the actual validation and assignment code; every other constructor's job is simply to supply sensible defaults for whatever wasn't given, then hand off.
- **Reduces the chance of overloads drifting apart** — without chaining, each constructor might duplicate similar assignment logic by hand, and a future bug fix or new validation rule could easily be applied to some overloads but forgotten in others.
- **Readable, layered defaults** — each link in the chain reads clearly as "given less information, assume this specific default, and delegate the rest," which documents the class's defaults directly in code, at the point they're chosen.

Use `this(...)` chaining any time you have several constructor overloads that share the same fundamental setup logic — as opposed to a rare situation where two constructors are so different in what they do that forcing one to delegate to the other would produce confusing, unnatural code, in which case both should stand alone with their own explicit logic instead.

## 3. Core concept

```java
class Color {
    int red, green, blue;

    Color(int red, int green, int blue) {
        if (red < 0 || red > 255 || green < 0 || green > 255 || blue < 0 || blue > 255) {
            throw new IllegalArgumentException("RGB values must be 0-255");
        }
        this.red = red; this.green = green; this.blue = blue;
    }

    Color(int gray) { // grayscale shortcut: same value for all three channels
        this(gray, gray, gray);
    }

    Color() { // pure black
        this(0);
    }
}
```

`Color()` chains to `Color(int gray)` with no arguments needed since it hard-codes `this(0)`; `Color(int gray)` in turn chains to the three-argument constructor, meaning even the simplest `new Color()` call still passes through the full RGB-range validation, just with `0, 0, 0`, which always passes.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three Color constructors chained together, no argument calling the one argument grayscale constructor which calls the three argument fully validated constructor, forming a chain that runs sequentially for a single new call">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="30" y="30" width="140" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="52" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">Color()</text>

  <line x1="170" y1="47" x2="230" y2="47" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#e)"/>
  <text x="200" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">this(0)</text>

  <rect x="230" y="30" width="160" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="310" y="52" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">Color(int gray)</text>

  <line x1="390" y1="47" x2="440" y2="47" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#e)"/>
  <text x="415" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">this(g,g,g)</text>

  <rect x="30" y="90" width="530" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="295" y="112" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Color(int red, int green, int blue) — validation + assignment</text>

  <line x1="310" y1="65" x2="295" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#e)"/>

  <defs><marker id="e" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <text x="300" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new Color() runs all three constructor bodies in sequence, in this order.</text>
</svg>

A chain of `this(...)` calls runs each linked constructor's body in sequence before the object is complete.

## 5. Runnable example

Scenario: a simple `Recipe` representing a dish with a name, servings, and prep time — starting with a two-link chain, then extending to a three-link chain with layered defaults, then hardening into a chain where the designated constructor's validation genuinely protects every overload equally.

### Level 1 — Basic

```java
public class RecipeBasic {
    static class Recipe {
        String name;
        int servings;

        Recipe(String name, int servings) {
            this.name = name;
            this.servings = servings;
        }

        Recipe(String name) {
            this(name, 4); // default to 4 servings
        }
    }

    public static void main(String[] args) {
        Recipe r = new Recipe("Pasta");
        System.out.println(r.name + " serves " + r.servings);
    }
}
```

**How to run:** `java RecipeBasic.java`

`new Recipe("Pasta")` matches the one-argument constructor, which chains via `this(name, 4)` to the two-argument constructor — a simple, single link in the chain providing one sensible default (4 servings).

### Level 2 — Intermediate

Same `Recipe`, now extended with prep time and a third constructor overload, chaining two levels deep.

```java
public class RecipeIntermediate {
    static class Recipe {
        String name;
        int servings;
        int prepMinutes;

        Recipe(String name, int servings, int prepMinutes) {
            this.name = name;
            this.servings = servings;
            this.prepMinutes = prepMinutes;
        }

        Recipe(String name, int servings) {
            this(name, servings, 30); // default to 30 minutes prep
        }

        Recipe(String name) {
            this(name, 4); // default to 4 servings, which itself defaults prep time
        }
    }

    public static void main(String[] args) {
        Recipe r = new Recipe("Pasta");
        System.out.println(r.name + ": " + r.servings + " servings, " + r.prepMinutes + " min prep");
    }
}
```

**How to run:** `java RecipeIntermediate.java`

`new Recipe("Pasta")` chains through **two** links: first to `Recipe(name, 4)`, which itself chains to `Recipe(name, 4, 30)` — each link adds exactly one more default value before delegating further, until the fully-specified constructor finally runs the actual field assignment.

### Level 3 — Advanced

Same `Recipe`, now with the fully-specified constructor validating its inputs, guaranteeing that **every** overload — no matter how many links deep it starts from — is protected by the same checks.

```java
public class RecipeAdvanced {
    static class Recipe {
        String name;
        int servings;
        int prepMinutes;

        Recipe(String name, int servings, int prepMinutes) {
            if (name == null || name.isEmpty()) {
                throw new IllegalArgumentException("Recipe name is required");
            }
            if (servings <= 0) {
                throw new IllegalArgumentException("Servings must be positive: " + servings);
            }
            if (prepMinutes < 0) {
                throw new IllegalArgumentException("Prep time cannot be negative: " + prepMinutes);
            }
            this.name = name;
            this.servings = servings;
            this.prepMinutes = prepMinutes;
        }

        Recipe(String name, int servings) {
            this(name, servings, 30);
        }

        Recipe(String name) {
            this(name, 4);
        }
    }

    public static void main(String[] args) {
        Recipe r = new Recipe("Pasta");
        System.out.println(r.name + ": " + r.servings + " servings, " + r.prepMinutes + " min prep");

        try {
            new Recipe(""); // invalid name, caught even though it enters through the shortest overload
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java RecipeAdvanced.java`

`new Recipe("")` enters through the *simplest* one-argument constructor, yet is still rejected — the empty name is only actually checked once it reaches the fully-specified constructor at the end of the chain, proving that validation placed there protects every overload equally, regardless of which one a caller happens to use.

## 6. Walkthrough

Trace `new Recipe("")` from `RecipeAdvanced.main`:

**Entry.** One `String` argument, `""` — matches `Recipe(String name)`.

**First link.** `this(name, 4)` is the sole statement; it delegates to `Recipe(String name, int servings)` with `name = ""`, `servings = 4`.

**Second link.** `this(name, servings, 30)` delegates further, to `Recipe(String name, int servings, int prepMinutes)` with `name = ""`, `servings = 4`, `prepMinutes = 30`.

**Validation, finally.** `name == null || name.isEmpty()` — `""` isn't `null`, but `"".isEmpty()` is `true` — the overall condition is `true`. The guard throws `IllegalArgumentException("Recipe name is required")` immediately; `servings` and `prepMinutes` are never even checked, since this guard is the first one in the method.

**Propagation.** The exception unwinds back through both delegating constructor calls (`this(name, 4)` and `this(name, 4, 30)`) and out of `new Recipe("")` entirely — no `Recipe` object of any kind is ever produced.

```
new Recipe("")
  matches Recipe(String name)
  -> this(name, 4) -> Recipe(String name, int servings)
     -> this(name, servings, 30) -> Recipe(String name, int servings, int prepMinutes)
        name.isEmpty()? true -> throw IllegalArgumentException("Recipe name is required")
  exception propagates all the way out
```

**Caught in `main`.** Prints `"Rejected: Recipe name is required"` — demonstrating the entire two-link chain still ultimately depends on, and is protected by, the single validation point at its end.

## 7. Gotchas & takeaways

> **`this(...)` must be the absolute first statement in a constructor — you cannot run any code (not even a simple `System.out.println`, let alone a validation check) before it.** If you need per-overload logic to run *before* delegating, that logic generally has to be restructured to happen inside the constructor being delegated *to*, or via a `private static` helper method called as part of the `this(...)` arguments themselves.

> **A chain of `this(...)` calls must eventually terminate at a constructor that does NOT call `this(...)`** — Java detects circular constructor chains (`this(...)` calls that eventually loop back on themselves) at compile time and rejects them, since such a chain could never actually finish.

- `this(...)` chains one constructor's call to another in the same class, and must be that constructor's very first statement.
- Chaining keeps the real validation and assignment logic in one designated constructor, with simpler overloads only supplying defaults before delegating.
- A single `new` call can run several constructor bodies in sequence if the chain is several links deep.
- Validation placed in the constructor at the end of a chain protects every overload that eventually delegates to it, regardless of how many links deep the call started.
