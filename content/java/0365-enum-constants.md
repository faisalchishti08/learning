---
card: java
gi: 365
slug: enum-constants
title: Enum constants
---

## 1. What it is

The **enum constants** are the individual named values listed inside an enum's body — `MONDAY`, `TUESDAY`, and so on inside `enum Day`. Each one is not just a label; it is a genuine, unique, `public static final` object of the enum's type, created exactly once when the enum class is first loaded by the JVM. Every reference to `Day.MONDAY` anywhere in your program refers to that same single object — there is never a second copy.

## 2. Why & when

This "exactly one object per constant" guarantee is what makes enums so safe and convenient to work with, and it's stronger than what you get from ordinary objects. A `new Day()` call doesn't exist and isn't allowed — you cannot construct additional enum instances yourself, even with reflection under normal circumstances, so the constants declared in the enum body are truly the *entire* universe of values that type can ever hold.

Because there is only ever one object per constant, comparing enum values with `==` is always correct and safe — unlike comparing `String`s or boxed `Integer`s with `==`, where identity and equality can quietly diverge. You rely on this property constantly: in `switch` statements, in `HashMap` and `HashSet` lookups (which use identity-based hashing internally for enums, extremely fast), and any time you write a simple `if (status == OrderStatus.SHIPPED)` check.

## 3. Core concept

```java
public class ConstantIdentityDemo {
    enum Day { MONDAY, TUESDAY, WEDNESDAY }

    public static void main(String[] args) {
        Day a = Day.MONDAY;
        Day b = Day.MONDAY;
        System.out.println(a == b);              // true -- same singleton object
        System.out.println(a == Day.valueOf("MONDAY")); // still true, same object
        System.out.println(a.equals(b));          // also true, but == is enough for enums
    }
}
```

**How to run:** `java ConstantIdentityDemo.java`

`a` and `b` both refer to `Day.MONDAY` — the *same* object, not two equal-but-distinct ones — so `a == b` is `true`. Even fetching `MONDAY` a different way, via `Day.valueOf("MONDAY")`, returns that identical singleton, so `a == Day.valueOf("MONDAY")` is also `true`. Because of this guarantee, `.equals()` is never strictly necessary for enums, though it works too.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="every reference to an enum constant points to the same single object in memory, created once when the class loads">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="260" y="30" width="120" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="58" fill="#6db33f" font-size="12" text-anchor="middle">Day.MONDAY</text>
  <text x="320" y="70" fill="#8b949e" font-size="9" text-anchor="middle">(one object)</text>

  <line x1="100" y1="110" x2="285" y2="70" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="105" fill="#79c0ff" font-size="10" text-anchor="middle">variable a</text>

  <line x1="320" y1="110" x2="320" y2="80" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="125" fill="#79c0ff" font-size="10" text-anchor="middle">variable b</text>

  <line x1="540" y1="110" x2="360" y2="70" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="105" fill="#79c0ff" font-size="10" text-anchor="middle">valueOf("MONDAY")</text>

  <text x="20" y="145" fill="#8b949e" font-size="10">All three arrows point at the exact same object -- so a == b == valueOf("MONDAY") is always true.</text>
</svg>

## 5. Runnable example

Scenario: tracking a traffic light's current colour, evolved from a version relying on `.equals()` out of habit, to one exploiting `==` for both correctness and speed, to a version storing enum constants as `HashSet`/`HashMap` keys where identity-based hashing pays off.

### Level 1 — Basic

```java
public class LightBasic {
    enum Light { RED, YELLOW, GREEN }

    public static void main(String[] args) {
        Light current = Light.RED;
        if (current.equals(Light.RED)) { // .equals works, but is more than necessary
            System.out.println("Stop");
        }
    }
}
```

**How to run:** `java LightBasic.java`

`.equals()` works correctly here, since enums do implement it sensibly — but it's really doing the same job `==` would, at the cost of a method call instead of a simple reference comparison.

### Level 2 — Intermediate

```java
public class LightIntermediate {
    enum Light { RED, YELLOW, GREEN }

    static String action(Light current) {
        if (current == Light.RED) return "Stop";       // == is safe and idiomatic for enums
        if (current == Light.YELLOW) return "Slow down";
        if (current == Light.GREEN) return "Go";
        throw new IllegalStateException("Unreachable"); // exhaustiveness not enforced here
    }

    public static void main(String[] args) {
        System.out.println(action(Light.RED));
        System.out.println(action(Light.GREEN));
    }
}
```

**How to run:** `java LightIntermediate.java`

Switching to `==` is not just allowed but idiomatic for enums, since every constant is a guaranteed singleton — there is no risk of `==` giving a wrong answer the way it can for boxed numbers or strings. This version is both clearer to a Java reader and marginally faster, since `==` is a raw reference comparison.

### Level 3 — Advanced

```java
import java.util.EnumMap;
import java.util.EnumSet;

public class LightAdvanced {
    enum Light { RED, YELLOW, GREEN }

    public static void main(String[] args) {
        // Enum constant identity underpins both EnumSet and EnumMap's fast internal representation
        EnumSet<Light> stopSignals = EnumSet.of(Light.RED, Light.YELLOW);
        EnumMap<Light, String> actions = new EnumMap<>(Light.class);
        actions.put(Light.RED, "Stop");
        actions.put(Light.YELLOW, "Slow down");
        actions.put(Light.GREEN, "Go");

        for (Light light : Light.values()) {
            boolean mustStop = stopSignals.contains(light); // identity-based lookup, no hashCode() needed
            System.out.println(light + " -> " + actions.get(light) + " (must stop: " + mustStop + ")");
        }
    }
}
```

**How to run:** `java LightAdvanced.java`

`EnumSet` and `EnumMap` are specialised collections that exploit the fact that each enum constant is a fixed, known singleton with a stable **ordinal** (its declared position) — internally they use bitsets and arrays indexed by ordinal rather than general-purpose hashing, making membership checks and lookups extremely fast, entirely because of the guarantee this topic is about.

## 6. Walkthrough

Execution starts in `main`. `EnumSet.of(Light.RED, Light.YELLOW)` builds a set containing exactly those two singleton constants; internally, `EnumSet` represents membership as a small bitmask indexed by each constant's ordinal (`RED` = 0, `YELLOW` = 1, `GREEN` = 2), rather than a general hash table.

`actions` is built as an `EnumMap<Light, String>`, associating each of the three `Light` constants with an action string; `EnumMap` stores its entries in an array ordered by ordinal internally, again relying on the fixed, known set of constants.

The loop `for (Light light : Light.values())` iterates the array returned by `Light.values()`, which contains the constants in declaration order: `RED`, then `YELLOW`, then `GREEN`.

For `RED`: `stopSignals.contains(RED)` checks the bitmask at ordinal 0, finds it set, returns `true`. `actions.get(RED)` looks up the array slot at ordinal 0, returning `"Stop"`. The line prints `RED -> Stop (must stop: true)`.

For `YELLOW`: same process, ordinal 1, `contains` returns `true` (it was added to `stopSignals`), `actions.get` returns `"Slow down"`.

For `GREEN`: ordinal 2, `contains` returns `false` (never added to `stopSignals`), `actions.get` returns `"Go"`.

Expected output:
```
RED -> Stop (must stop: true)
YELLOW -> Slow down (must stop: true)
GREEN -> Go (must stop: false)
```

## 7. Gotchas & takeaways

> Never rely on enum constants staying comparable across a serialization or deserialization boundary that involves a *different* version of the enum class — if constants are reordered, renamed, or removed between versions, previously-serialized data can resolve to the wrong constant, or fail with an exception, even though `==` identity holds perfectly within a single running JVM.

- Every enum constant is a unique, `public static final` singleton object created once when its class loads — there is exactly one `Day.MONDAY` for the lifetime of the program.
- `==` is always safe and idiomatic for comparing enum values; you never need `.equals()`, though it also works correctly.
- `EnumSet` and `EnumMap` exist specifically to exploit this singleton, ordinal-indexed nature — they are dramatically faster and more memory-efficient than a general-purpose `HashSet`/`HashMap` for enum keys.
- You cannot construct new instances of an enum type yourself (`new Day()` doesn't compile) — the constants declared in the enum body are the complete, closed set of values.
- Enum identity (`==`) is a JVM-level guarantee within one running class loader; be cautious about assuming it across serialization, multiple class loaders, or different versions of the enum class.
