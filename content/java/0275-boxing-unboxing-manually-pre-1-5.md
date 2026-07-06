---
card: java
gi: 275
slug: boxing-unboxing-manually-pre-1-5
title: Boxing/unboxing manually (pre-1.5)
---

## 1. What it is

Before Java 5 introduced automatic autoboxing and auto-unboxing, converting between a primitive and its wrapper class required writing the conversion explicitly, by hand, every single time: `new Integer(42)` (or the equivalent factory method) to box a primitive into a wrapper object, and `.intValue()` (or the equivalent method for each type) to unbox a wrapper back into a primitive. Modern Java still supports writing this manual form, even though it's rarely necessary anymore.

```java
public class ManualBoxingDemo {
    public static void main(String[] args) {
        // Manual boxing (the pre-1.5 way — still legal, just no longer necessary)
        int primitiveValue = 42;
        Integer boxed = Integer.valueOf(primitiveValue); // manual boxing

        // Manual unboxing
        Integer wrapperValue = boxed;
        int unboxed = wrapperValue.intValue(); // manual unboxing

        System.out.println("Boxed: " + boxed);
        System.out.println("Unboxed: " + unboxed);

        // Modern equivalent, using autoboxing/auto-unboxing (Java 5+):
        Integer autoBoxed = primitiveValue; // compiler inserts Integer.valueOf(...) automatically
        int autoUnboxed = autoBoxed;          // compiler inserts .intValue() automatically
    }
}
```

`Integer.valueOf(primitiveValue)` and `wrapperValue.intValue()` are the explicit, manual forms of exactly what the compiler does invisibly for you with `Integer autoBoxed = primitiveValue;` and `int autoUnboxed = autoBoxed;` — since Java 5, both directions of conversion happen automatically wherever the compiler can infer they're needed, but understanding the manual form clarifies exactly what's happening underneath that convenient syntax.

## 2. Why & when

Understanding manual boxing and unboxing matters for reading pre-Java-5 code, for understanding exactly what autoboxing/auto-unboxing are doing behind the scenes, and for a handful of situations where being explicit remains clearer or more correct than relying on the compiler's automatic conversion.

- **Reading legacy code** — Java code written before 2004 (Java 5's release) had no autoboxing at all; understanding the manual `new Integer(...)` / `.intValue()` pattern is necessary for reading and maintaining genuinely old codebases, or code written in a deliberately explicit style.
- **Understanding what autoboxing actually does** — knowing that `Integer i = 5;` really compiles down to `Integer i = Integer.valueOf(5);` explains real behaviours like the `Integer` caching discussed in the previous topic (`Integer.valueOf` is exactly the method responsible for that caching), which would otherwise seem like unexplained "magic."
- **Being deliberately explicit in performance-sensitive or type-ambiguous code** — in rare cases (particularly involving overloaded methods where autoboxing could resolve ambiguously, or extremely performance-sensitive code where you want the boxing operation to be visually obvious in the source), writing the conversion manually can be a deliberate stylistic choice, though this is uncommon in modern code.

Prefer autoboxing and auto-unboxing for everyday code (it's what virtually all modern Java style guides recommend), but recognize the manual `valueOf`/`xxxValue()` pattern when reading older code, and understand that it is exactly, precisely what the compiler is doing for you automatically underneath the convenient modern syntax — this equivalence is the core insight of this whole topic.

## 3. Core concept

```java
public class ManualBoxingCore {
    public static void main(String[] args) {
        // Manual boxing for EVERY primitive type follows the same pattern:
        Integer i = Integer.valueOf(10);
        Long l = Long.valueOf(100L);
        Double d = Double.valueOf(3.14);
        Boolean b = Boolean.valueOf(true);
        Character c = Character.valueOf('A');

        // Manual unboxing similarly follows one consistent pattern per type:
        int primInt = i.intValue();
        long primLong = l.longValue();
        double primDouble = d.doubleValue();
        boolean primBoolean = b.booleanValue();
        char primChar = c.charValue();

        System.out.println(primInt + " " + primLong + " " + primDouble + " " + primBoolean + " " + primChar);
    }
}
```

Every wrapper class follows the exact same naming convention: a static `valueOf(primitive)` factory method for boxing, and an instance method named `xxxValue()` (`intValue()`, `longValue()`, `doubleValue()`, and so on) for unboxing — once you recognize this consistent pattern, manual boxing and unboxing for any primitive type becomes entirely predictable.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Manual boxing uses the static valueOf factory method, manual unboxing uses an instance method named after the primitive type, modern autoboxing and auto unboxing insert these exact same calls automatically">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="220" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Integer.valueOf(42) — box</text>

  <rect x="330" y="20" width="220" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="440" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">wrapper.intValue() — unbox</text>

  <line x1="150" y1="55" x2="150" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="440" y1="55" x2="440" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="40" y="95" width="220" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="117" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">Integer i = 42; (autoboxed)</text>

  <rect x="330" y="95" width="220" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="117" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">int n = wrapper; (auto-unboxed)</text>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Modern autoboxing inserts exactly these calls, invisibly, at compile time.</text>
</svg>

Modern autoboxing and auto-unboxing insert exactly the manual `valueOf`/`xxxValue()` calls automatically, at compile time.

## 5. Runnable example

Scenario: a small numeric utility class demonstrating boxing and unboxing across a mix of styles, evolved from fully manual conversions into fully modern autoboxed code, then hardened to show one real, practical case where being explicit about boxing still matters: resolving overload ambiguity.

### Level 1 — Basic

```java
public class ManualBoxingBasic {
    static int sumManual(Integer a, Integer b) {
        return a.intValue() + b.intValue(); // fully manual unboxing, the pre-1.5 style
    }

    public static void main(String[] args) {
        Integer x = Integer.valueOf(3); // fully manual boxing
        Integer y = Integer.valueOf(4);
        System.out.println("Sum: " + sumManual(x, y));
    }
}
```

**How to run:** `java ManualBoxingBasic.java`

Every conversion is written out explicitly here: `Integer.valueOf(3)` to box, `.intValue()` to unbox — this is exactly how this code would have needed to be written before Java 5 introduced automatic conversion.

### Level 2 — Intermediate

Same summing utility, now rewritten using modern autoboxing and auto-unboxing, demonstrating that the compiler produces functionally identical behaviour with far less visual noise.

```java
public class ManualBoxingIntermediate {
    static int sumAuto(Integer a, Integer b) {
        return a + b; // compiler auto-unboxes both 'a' and 'b' here, then adds the resulting primitives
    }

    public static void main(String[] args) {
        Integer x = 3; // compiler auto-boxes: Integer.valueOf(3)
        Integer y = 4; // compiler auto-boxes: Integer.valueOf(4)
        System.out.println("Sum: " + sumAuto(x, y));

        // Mixing manual and automatic styles is legal and behaves identically either way:
        Integer manuallyBoxed = Integer.valueOf(10);
        int autoUnboxedResult = manuallyBoxed + 5; // '+5' triggers auto-unboxing of manuallyBoxed
        System.out.println("Mixed style result: " + autoUnboxedResult);
    }
}
```

**How to run:** `java ManualBoxingIntermediate.java`

`sumAuto(a, b)` looks like plain primitive addition, but the compiler silently inserts `a.intValue() + b.intValue()` underneath — the manual and automatic styles are functionally interchangeable and can even be freely mixed within the same expression, since autoboxing/auto-unboxing is purely a compile-time convenience layered over the exact same underlying method calls.

### Level 3 — Advanced

Same utility, now demonstrating a genuine, practical reason to be explicit about boxing: resolving ambiguity between overloaded methods, where relying on autoboxing could silently call the "wrong" overload compared to what the manual, explicit call makes clear.

```java
public class ManualBoxingAdvanced {
    static void process(int value) {
        System.out.println("Processing PRIMITIVE int: " + value);
    }

    static void process(Integer value) {
        System.out.println("Processing WRAPPER Integer: " + value);
    }

    static void process(Object value) {
        System.out.println("Processing generic Object: " + value);
    }

    public static void main(String[] args) {
        int primitive = 42;
        Integer wrapper = Integer.valueOf(42);

        process(primitive); // resolves to process(int) -- EXACT match, no boxing needed at all
        process(wrapper);   // resolves to process(Integer) -- EXACT match, no unboxing needed at all

        // Being EXPLICIT about which overload you intend removes any doubt:
        process((Integer) null); // forces the Integer overload -- process(int) would NPE trying to unbox null!
    }
}
```

**How to run:** `java ManualBoxingAdvanced.java`

Java's overload resolution always prefers an exact type match before considering boxing or unboxing conversions at all, so `process(primitive)` calls `process(int)` directly and `process(wrapper)` calls `process(Integer)` directly, with neither needing any box/unbox conversion; the explicit cast `(Integer) null` is necessary specifically to force the `process(Integer)` overload to be selected for a literal `null` — without the cast, `process(null)` alone would actually be ambiguous between `process(Integer)` and `process(Object)` (both accept `null` directly, with neither requiring boxing), and the compiler would reject it as an ambiguous method call.

## 6. Walkthrough

Trace `main` in `ManualBoxingAdvanced` line by line, focusing on exactly how overload resolution picks each `process` method.

**`process(primitive)`.** `primitive` is declared as `int`. Java's overload resolution first looks for an exact, unconverted match: `process(int value)` matches `int` directly, with zero boxing needed. This exact match is chosen immediately, without even considering the `Integer` or `Object` overloads. Prints `"Processing PRIMITIVE int: 42"`.

**`process(wrapper)`.** `wrapper` is declared as `Integer`. An exact match exists: `process(Integer value)` matches `Integer` directly, again with zero conversion needed. This is selected. Prints `"Processing WRAPPER Integer: 42"`.

**`process((Integer) null)`.** The expression `(Integer) null` has the compile-time type `Integer` (a cast forces the compiler to treat the literal `null` as specifically an `Integer` reference, rather than leaving its type ambiguous). With this explicit type information, overload resolution finds an exact match: `process(Integer value)`. It runs with `value` bound to `null`. Prints `"Processing WRAPPER Integer: null"` (since string concatenation with a `null` reference produces the literal text `"null"`, not an exception — string concatenation is one of the few contexts where `null` is handled gracefully rather than triggering a `NullPointerException`).

```
process(primitive):       int exact match     -> process(int)     -> "Processing PRIMITIVE int: 42"
process(wrapper):         Integer exact match -> process(Integer) -> "Processing WRAPPER Integer: 42"
process((Integer) null):  cast forces Integer type -> process(Integer), value=null -> "Processing WRAPPER Integer: null"
```

**Final output.**
```
Processing PRIMITIVE int: 42
Processing WRAPPER Integer: 42
Processing WRAPPER Integer: null
```

## 7. Gotchas & takeaways

> **Calling `process(null)` without the explicit `(Integer)` cast would be a compile error due to ambiguity** — both `process(Integer value)` and `process(Object value)` can accept a literal `null` directly, with neither requiring any boxing conversion, so the compiler cannot determine which one you meant and rejects the call outright as "reference to process is ambiguous." The explicit cast is the standard way to resolve this: it tells the compiler exactly which overload's parameter type `null` should be treated as.

> **Overload resolution always prefers an exact type match over one requiring boxing or unboxing** — if both `process(int)` and `process(Integer)` exist, passing a plain `int` variable always calls `process(int)`, never `process(Integer)` via autoboxing, even though the latter would technically also be a valid, compiling call; boxing/unboxing conversions are only ever considered by the compiler as a fallback, after all exact matches have been ruled out.

- Manual boxing uses each wrapper class's static `valueOf(primitive)` factory method; manual unboxing uses an instance method named after the primitive type (`intValue()`, `doubleValue()`, `booleanValue()`, and so on).
- Modern autoboxing and auto-unboxing (Java 5+) insert exactly these same calls automatically wherever the compiler can infer the conversion is needed, with no functional difference from writing them manually.
- Recognizing this manual pattern explains the "magic" behind autoboxing, including why small `Integer` values are cached (`Integer.valueOf` is precisely the method responsible).
- Being explicit about a value's wrapper type (via an explicit cast, like `(Integer) null`) remains genuinely useful for resolving ambiguity between overloaded methods, since overload resolution always prefers an exact type match before considering any boxing conversion.
