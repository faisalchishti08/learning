---
card: java
gi: 1018
slug: static-factory-methods
title: Static factory methods
---

## 1. What it is

A **static factory method** is a plain `static` method on a class that returns an instance of that class (or a related type), used *instead of* a public constructor — `LocalDate.of(2024, 1, 15)` instead of `new LocalDate(2024, 1, 15)`, or `List.of(1, 2, 3)` instead of a constructor call. Unlike the Factory Method *design pattern* (which centralizes the decision of which concrete subclass to instantiate across an inheritance hierarchy), a static factory method here is a narrower idiom: a named, static entry point for creating instances of one specific class, with more freedom and clearer intent than a bare constructor.

## 2. Why & when

A constructor's name is always the class name — it can't describe *what kind* of instance is being created, and Java doesn't allow two constructors with the same parameter types even if their meanings are completely different (you can't have both `new Color(int rgb)` and `new Color(String name)`). A static factory method has none of these limits: it has its own descriptive name (`Color.fromRgb(int)` and `Color.fromName(String)` can coexist), it isn't required to create a new object every time (it can return a cached instance, enabling patterns like [Singleton](0997-singleton.md)), and it can return an instance of any subtype of its declared return type, including one chosen dynamically based on the arguments.

Reach for a static factory method when a descriptive name would clarify what's being constructed (`BigInteger.probablePrime(...)` reads far better than an equivalent constructor could), when you want to control instance creation (caching, returning a singleton, choosing between implementations), or when the natural constructor signature would collide with another overload. Skip it for a simple class with one obvious, unambiguous way to construct it — a public constructor is simpler and just as clear there.

## 3. Core concept

```
class Color {
    private final int red, green, blue;
    private Color(int red, int green, int blue) { this.red = red; this.green = green; this.blue = blue; } // private!

    // Descriptive names a constructor could never have -- and no signature collision risk.
    static Color fromRgb(int red, int green, int blue) {
        return new Color(red, green, blue);
    }
    static Color fromHex(String hex) {
        int rgb = Integer.parseInt(hex, 16);
        return new Color((rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF);
    }

    // Caching: doesn't have to create a new instance every call.
    private static final Color BLACK = new Color(0, 0, 0);
    static Color black() { return BLACK; }
}

Color a = Color.fromRgb(255, 0, 0);
Color b = Color.fromHex("00FF00");
Color c = Color.black(); // no `new` at the call site at all
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two differently-named static factory methods, fromRgb and fromHex, both calling the same private constructor, plus a third factory method returning a cached instance instead of constructing a new one">
  <rect x="30" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Color.fromRgb(...)</text>
  <rect x="30" y="70" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="91" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Color.fromHex(...)</text>
  <rect x="30" y="120" width="140" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="100" y="141" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Color.black()</text>

  <rect x="280" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">private Color(...)</text>
  <rect x="280" y="120" width="140" height="34" rx="6" fill="#1c2430" stroke="#f0883e" stroke-dasharray="4"/>
  <text x="350" y="141" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">cached BLACK instance</text>

  <line x1="170" y1="37" x2="280" y2="37" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="170" y1="87" x2="280" y2="45" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="170" y1="137" x2="280" y2="137" stroke="#f0883e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two factory methods share and hide the same private constructor; a third skips construction entirely and returns a pre-built cached instance.

## 5. Runnable example

Scenario: a `Color` class constructed from different input formats, evolving from ambiguous, colliding constructors into descriptive static factory methods that also enable caching.

### Level 1 — Basic

```java
// File: StaticFactoryBasic.java
class Color {
    final int red, green, blue;
    Color(int red, int green, int blue) {
        this.red = red; this.green = green; this.blue = blue;
    }
    @Override public String toString() { return "rgb(" + red + "," + green + "," + blue + ")"; }
}

public class StaticFactoryBasic {
    public static void main(String[] args) {
        Color red = new Color(255, 0, 0);
        System.out.println(red);
        // No way to also construct from a hex string like "00FF00" -- a second
        // constructor taking a String would work, but "new Color(String)" doesn't
        // say WHAT format that string is in, and can't coexist with another
        // String-based constructor meaning something different.
    }
}
```

**How to run:** save as `StaticFactoryBasic.java`, then `javac StaticFactoryBasic.java && java StaticFactoryBasic` (JDK 17+).

Expected output:
```
rgb(255,0,0)
```

There's exactly one way to construct a `Color`, and its name (`Color(...)`) can't describe what format the arguments represent — a caller reading `new Color(255, 0, 0)` has to check the parameter types to know it means RGB values.

### Level 2 — Intermediate

```java
// File: StaticFactoryIntermediate.java
class Color {
    final int red, green, blue;
    private Color(int red, int green, int blue) {
        this.red = red; this.green = green; this.blue = blue;
    }

    static Color fromRgb(int red, int green, int blue) {
        return new Color(red, green, blue);
    }

    static Color fromHex(String hex) {
        int rgb = Integer.parseInt(hex, 16);
        return new Color((rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF);
    }

    @Override public String toString() { return "rgb(" + red + "," + green + "," + blue + ")"; }
}

public class StaticFactoryIntermediate {
    public static void main(String[] args) {
        Color a = Color.fromRgb(255, 0, 0);
        Color b = Color.fromHex("00FF00");
        System.out.println(a);
        System.out.println(b);
    }
}
```

**How to run:** save as `StaticFactoryIntermediate.java`, then `javac StaticFactoryIntermediate.java && java StaticFactoryIntermediate` (JDK 17+).

Expected output:
```
rgb(255,0,0)
rgb(0,255,0)
```

The real-world concern added: `fromRgb` and `fromHex` both construct `Color` instances, but their names describe exactly what input format each expects — something no constructor name could do, since a constructor is always just named after the class.

### Level 3 — Advanced

```java
// File: StaticFactoryAdvanced.java
import java.util.HashMap;
import java.util.Map;

class Color {
    final int red, green, blue;
    private Color(int red, int green, int blue) {
        this.red = red; this.green = green; this.blue = blue;
    }

    static Color fromRgb(int red, int green, int blue) {
        return new Color(red, green, blue);
    }

    static Color fromHex(String hex) {
        int rgb = Integer.parseInt(hex, 16);
        return new Color((rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF);
    }

    // A cache of commonly-requested colors -- fromRgb() below can return an
    // EXISTING instance instead of always allocating a new one.
    private static final Map<Integer, Color> CACHE = new HashMap<>();
    static {
        CACHE.put(0x000000, new Color(0, 0, 0));
        CACHE.put(0xFFFFFF, new Color(255, 255, 255));
    }

    static Color fromRgbCached(int red, int green, int blue) {
        int key = (red << 16) | (green << 8) | blue;
        return CACHE.computeIfAbsent(key, k -> new Color(red, green, blue));
    }

    @Override public String toString() { return "rgb(" + red + "," + green + "," + blue + ")"; }
}

public class StaticFactoryAdvanced {
    public static void main(String[] args) {
        Color black1 = Color.fromRgbCached(0, 0, 0);
        Color black2 = Color.fromRgbCached(0, 0, 0);
        System.out.println("same instance: " + (black1 == black2));

        Color custom1 = Color.fromRgbCached(10, 20, 30);
        Color custom2 = Color.fromRgbCached(10, 20, 30);
        System.out.println("custom same instance (now cached too): " + (custom1 == custom2));
    }
}
```

**How to run:** save as `StaticFactoryAdvanced.java`, then `javac StaticFactoryAdvanced.java && java StaticFactoryAdvanced` (JDK 17+).

Expected output:
```
same instance: true
custom same instance (now cached too): true
```

The production-flavored hard case: `fromRgbCached` uses `computeIfAbsent` to return an existing cached `Color` instance when one already exists for the given key, and to cache-and-return a newly-created one otherwise — the calling code never knows or cares whether a fresh object was allocated or an existing one was reused, since a static factory method isn't bound to always constructing something new.

## 6. Walkthrough

Tracing the two `fromRgbCached` calls with `(10, 20, 30)` in `StaticFactoryAdvanced.main`:

1. `Color.fromRgbCached(10, 20, 30)` (first call) computes `key = (10 << 16) | (20 << 8) | 30`, a single packed integer uniquely representing this RGB combination.
2. `CACHE.computeIfAbsent(key, k -> new Color(10, 20, 30))` checks whether `key` already exists in the map — it doesn't yet (only black and white were pre-populated), so the lambda `k -> new Color(10, 20, 30)` runs, constructing a genuinely new `Color` instance, which is stored in the map under `key` and returned as `custom1`.
3. `Color.fromRgbCached(10, 20, 30)` (second call) computes the exact same `key` value again.
4. `CACHE.computeIfAbsent(key, ...)` checks the map again — this time `key` **is** present (from step 2), so the lambda is never invoked at all, and the map simply returns the existing `Color` instance stored there, assigned to `custom2`.
5. `custom1 == custom2` compares object references (not `.equals()`), and since both variables point to the exact same object created in step 2, this is `true` — printed as `"custom same instance (now cached too): true"`.
6. This mirrors what happened with `black1` and `black2` at the top: both calls resolved to the exact same pre-populated `Color(0, 0, 0)` instance from the static initializer block, since `0x000000` was already a key in `CACHE` before either call ran.

## 7. Gotchas & takeaways

> **Gotcha:** unlike a constructor, a static factory method is easy to overlook when scanning a class's public API for "how do I create one of these?" — following the Java standard library's naming conventions (`of`, `from`, `valueOf`, `getInstance`, `newInstance`) helps readers recognize a static factory method as a construction entry point rather than an ordinary utility method.

- A static factory method is a named, `static` entry point for creating instances, used instead of (or alongside) a public constructor — it's a narrower idiom than the [Factory Method](0998-factory-method.md) design pattern, which centralizes subclass selection across a hierarchy.
- Descriptive names let multiple "ways of constructing" coexist clearly, something overloaded constructors with colliding parameter types can't always do.
- A static factory method isn't obligated to create a new instance on every call — it can return a cached or otherwise reused instance, enabling patterns like object pooling or [Singleton](0997-singleton.md).
- Common naming conventions in the Java standard library: `of` (`List.of(...)`), `from` (`Instant.from(...)`), `valueOf` (`Integer.valueOf(...)`), `getInstance`/`newInstance` (for singleton-like or explicitly-fresh instances).
- A class exposing only static factory methods (with a `private` constructor) can't be subclassed via the standard constructor-chaining mechanism, which is sometimes a deliberate constraint and sometimes an unwanted limitation — worth considering explicitly.
- Don't add a static factory method purely out of habit for a class with one obvious, unambiguous constructor — a plain public constructor remains the clearer choice there.
