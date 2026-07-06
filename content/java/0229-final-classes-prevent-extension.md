---
card: java
gi: 229
slug: final-classes-prevent-extension
title: Final classes (prevent extension)
---

## 1. What it is

A `final` class is one that no other class may extend, at all. Where a `final` method (the previous topic) only locks one method against overriding, a `final` class locks the *entire class* against subclassing — attempting `class X extends SomeFinalClass { ... }` is a compile error, full stop, regardless of what `X` intends to add or change.

```java
final class Currency {
    private final String code;

    Currency(String code) { this.code = code; }

    String getCode() { return code; }
}

// class SpecialCurrency extends Currency { ... } // COMPILE ERROR if uncommented — Currency is final
```

`Currency` is declared `final`, so it can never have subclasses — every `Currency` object in the entire program is guaranteed to behave exactly as `Currency` defines, with no possibility of a subclass altering, extending, or overriding any of its behaviour.

## 2. Why & when

Making a class `final` is a strong design statement: this class is complete as written, and no variation of it should exist.

- **Immutability guarantees** — an immutable class (like `String` or `Currency` above) often needs to be `final`; if it weren't, a subclass could add mutable state or override methods in ways that break the immutability callers rely on, even though the base class itself never changes.
- **Security and correctness** — value types, cryptographic key wrappers, and other classes where identity and behaviour must be exactly as documented benefit from `final`, since it closes off an entire class of "what if a subclass changes this" bugs and attacks.
- **API stability** — library authors often mark utility or configuration classes `final` so that future changes to the class's internals can never break a subclass that was depending on overriding some part of it — there simply are no subclasses to break.

Reach for `final` on a class when you can say with confidence "this class should never be specialized," which is common for small, self-contained value types, utility classes, and security-sensitive types — it is a much broader guarantee than a `final` method, which only locks down one piece of behaviour while leaving the rest of the class open.

## 3. Core concept

```java
final class Point {
    final int x;
    final int y;

    Point(int x, int y) { this.x = x; this.y = y; }

    Point translate(int dx, int dy) {
        return new Point(x + dx, y + dy); // always returns a plain Point, never a subclass
    }
}
```

Because `Point` is `final`, `translate` can safely assume every `Point` it ever creates or receives behaves exactly as written here — there is no subclass that could override `translate` to return something with unexpected behaviour, which makes reasoning about `Point` mechanically simple: read the class, and you have read everything that can ever happen with it.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A final class blocks any subclass from being written at all, compared to an ordinary class which can be freely extended by any number of subclasses">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="40" y="25" width="180" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="130" y="47" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">final class Currency</text>
  <text x="130" y="80" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">X — no subclass allowed</text>

  <rect x="380" y="25" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="47" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">class Shape</text>
  <line x1="470" y1="60" x2="470" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <rect x="380" y="85" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="104" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">class Circle extends Shape</text>

  <text x="300" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">final closes off extension entirely; a non-final class stays open to any number of subclasses.</text>
</svg>

A `final` class permits zero subclasses; an ordinary class permits any number of them.

## 5. Runnable example

Scenario: a small immutable `Money` value type, evolved from a plain final class into one that defends its immutability guarantee against exactly the kind of subclassing trick `final` is meant to prevent.

### Level 1 — Basic

```java
public final class MoneyBasic {
    private final long cents;

    MoneyBasic(long cents) { this.cents = cents; }

    long getCents() { return cents; }

    public static void main(String[] args) {
        MoneyBasic price = new MoneyBasic(1999);
        System.out.println("Price in cents: " + price.getCents());
    }
}
```

**How to run:** `java MoneyBasic.java`

`MoneyBasic` is declared `final`, so `class DiscountedMoney extends MoneyBasic { ... }` would fail to compile if anyone tried it — every `MoneyBasic` object is guaranteed to be exactly what this one class defines.

### Level 2 — Intermediate

Same `Money` idea, now with an actual immutable operation (`plus`) that returns a new instance — a pattern that depends on the class being closed to subclassing to stay trustworthy.

```java
public final class MoneyIntermediate {
    private final long cents;

    MoneyIntermediate(long cents) {
        if (cents < 0) throw new IllegalArgumentException("Money cannot be negative");
        this.cents = cents;
    }

    long getCents() { return cents; }

    MoneyIntermediate plus(MoneyIntermediate other) {
        return new MoneyIntermediate(this.cents + other.cents); // always a genuine MoneyIntermediate
    }

    public static void main(String[] args) {
        MoneyIntermediate a = new MoneyIntermediate(500);
        MoneyIntermediate b = new MoneyIntermediate(250);
        MoneyIntermediate total = a.plus(b);
        System.out.println("Total cents: " + total.getCents()); // 750
    }
}
```

**How to run:** `java MoneyIntermediate.java`

Because `MoneyIntermediate` is `final`, `plus` can trust that `other` is a real, unmodified `MoneyIntermediate` whose `cents` field was validated by the constructor — there is no subclass that could have skipped that validation or overridden `getCents` to lie about its value.

### Level 3 — Advanced

Same scenario, now contrasted with a non-final version to show concretely what `final` prevents: a subclass that overrides a getter to break the invariant every caller relies on.

```java
public class MoneyAdvanced {
    // Demonstrates the RISK if the class is NOT final
    static class UnsafeMoney {
        private final long cents;
        UnsafeMoney(long cents) {
            if (cents < 0) throw new IllegalArgumentException("Money cannot be negative");
            this.cents = cents;
        }
        long getCents() { return cents; } // NOT final class, so this could be overridden by a subclass
    }

    static class LyingMoney extends UnsafeMoney {
        LyingMoney(long cents) { super(cents); }
        @Override
        long getCents() { return -999; } // breaks the "money is never negative" invariant entirely
    }

    // The SAFE version: final class, so no subclass like LyingMoney can ever exist
    static final class SafeMoney {
        private final long cents;
        SafeMoney(long cents) {
            if (cents < 0) throw new IllegalArgumentException("Money cannot be negative");
            this.cents = cents;
        }
        long getCents() { return cents; }
    }

    public static void main(String[] args) {
        UnsafeMoney sneaky = new LyingMoney(100);
        System.out.println("Unsafe money reports: " + sneaky.getCents()); // -999, invariant broken

        SafeMoney safe = new SafeMoney(100);
        System.out.println("Safe money reports: " + safe.getCents()); // 100 — always correct
    }
}
```

**How to run:** `java MoneyAdvanced.java`

`LyingMoney` overrides `getCents` to return a nonsensical negative value, something only possible because `UnsafeMoney` is not `final`; `SafeMoney` being `final` makes writing an equivalent `LyingMoney` subclass of it a compile error, so every `SafeMoney` instance is guaranteed to report a value that actually passed the constructor's validation.

## 6. Walkthrough

Trace `main` in `MoneyAdvanced` from top to bottom.

**`new LyingMoney(100)`.** The constructor calls `super(100)`, which runs `UnsafeMoney`'s constructor: `100 < 0` is false, so no exception, and `cents` is set to `100` inside the `UnsafeMoney` part of the object. The reference `sneaky` is declared as `UnsafeMoney` but its actual runtime type is `LyingMoney`.

**`sneaky.getCents()`.** Dynamic dispatch looks at the *actual* type, `LyingMoney`, which overrides `getCents` to unconditionally `return -999;` — the real `cents` field (`100`) is never even read. Output: `"Unsafe money reports: -999"`.

**`new SafeMoney(100)`.** Constructor validates `100 < 0` is false, stores `cents = 100`. There is no subclass of `SafeMoney` in existence (and none could ever be written, since `SafeMoney` is `final`), so `safe.getCents()` can only ever run `SafeMoney`'s own implementation.

**`safe.getCents()`.** Returns the real, validated `cents` field: `100`. Output: `"Safe money reports: 100"`.

```
LyingMoney extends UnsafeMoney (allowed, class not final):
  getCents() overridden -> always -999, invariant broken

SafeMoney (final class):
  no subclass possible -> getCents() always returns the real validated cents
```

**Final output.** `"Unsafe money reports: -999"` followed by `"Safe money reports: 100"` — demonstrating that only the `final` class structurally guarantees its invariant (money is never negative) can never be undermined by an override.

## 7. Gotchas & takeaways

> **A `final` class can still have `final` fields, `final` methods, or ordinary mutable state — `final` on the class itself says nothing about immutability directly.** Many immutable classes happen to be `final` (to protect that immutability), but marking a class `final` alone does not make it immutable; you must also make its fields `final` and avoid exposing mutable internals.

> **You cannot mark a class both `abstract` and `final`** — an abstract class exists specifically to be subclassed (and completed) by others, while `final` forbids subclassing entirely; the two are direct opposites, and the compiler rejects any class declared as both.

- A `final` class cannot be extended by any other class, anywhere, ever — this is a compile-time guarantee, not just a convention.
- Use `final` on classes that must remain exactly as written: immutable value types, security-sensitive wrappers, and stable utility classes are the most common candidates.
- Unlike a `final` method (which locks one piece of behaviour), a `final` class locks the entire class against any kind of specialization.
- `final` and `abstract` are mutually exclusive on the same class declaration.
