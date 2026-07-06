---
card: java
gi: 211
slug: final-modifier-fields-methods-classes
title: final modifier (fields/methods/classes)
---

## 1. What it is

The `final` modifier means "cannot be changed further," applied to three different things with three related but distinct meanings: a `final` **field** cannot be reassigned once initialized; a `final` **method** cannot be overridden by any subclass; a `final` **class** cannot be extended (subclassed) at all.

```java
final int MAX = 100;
// MAX = 200; // COMPILE ERROR — final field, cannot reassign

class Base {
    final void lockedMethod() { // subclasses CANNOT override this
        System.out.println("Fixed behaviour");
    }
}

final class Sealed { // no class can extend Sealed at all
    // ...
}

// class SubSealed extends Sealed {} // COMPILE ERROR — Sealed is final, cannot be subclassed
```

All three uses share the same underlying idea — locking something against further change — but apply it at different levels: a value (field), a specific behaviour (method), or an entire type's extensibility (class).

## 2. Why & when

`final` exists to let a class's author declare, and have the compiler enforce, that certain things are meant to stay fixed:

- **`final` fields** guarantee a value, once set, can never be reassigned — used for constants (`static final`, covered earlier) and for fields that should be set once at construction and never again, expressing an object's immutable properties.
- **`final` methods** prevent subclasses from changing critical behaviour that the class's correctness depends on — useful when a method's exact behaviour is essential to the class working correctly, and allowing an override could silently break that guarantee.
- **`final` classes** prevent any subclassing entirely — appropriate for classes not designed to be extended, especially security-sensitive or heavily-optimized classes (like `String`, which is itself `final` in Java, specifically to guarantee its immutability can never be violated by a subclass).

You reach for `final` whenever allowing further change (reassignment, overriding, or subclassing) would risk breaking an invariant the class relies on, or simply whenever a value or design is deliberately meant to be fixed and unchangeable going forward.

## 3. Core concept

```java
class ImmutablePoint {
    final int x; // set once, in the constructor, never again
    final int y;

    ImmutablePoint(int x, int y) {
        this.x = x;
        this.y = y;
    }

    final int distanceSquaredFromOrigin() { // subclasses cannot override this calculation
        return x * x + y * y;
    }
}

final class LockedUtility { // cannot be extended by anyone
    static int square(int n) { return n * n; }
}
```

`ImmutablePoint`'s `x` and `y` must be assigned exactly once, inside the constructor — any attempt to assign them again anywhere else in the class (or, of course, from outside it, since they're not shown as `private` here but would typically also be) is a compile error, guaranteeing every `ImmutablePoint` object's coordinates never change after construction.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three separate applications of final: a final field locked against reassignment after its first value is set, a final method locked against being overridden by any subclass, and a final class locked against being extended by any subclass at all">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="20" y="25" width="170" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">final field</text>
  <text x="105" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">set once, never reassigned</text>

  <rect x="215" y="25" width="170" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">final method</text>
  <text x="300" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">cannot be overridden</text>

  <rect x="410" y="25" width="170" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="495" y="45" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">final class</text>
  <text x="495" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">cannot be subclassed at all</text>

  <text x="300" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">All three share the same idea: "locked against further change" — applied at different levels.</text>
</svg>

`final` locks a field's value, a method's behaviour, or a class's extensibility, depending on where it's applied.

## 5. Runnable example

Scenario: a small `Money` value type meant to be genuinely immutable — starting with basic final fields, then extending with a final method guaranteeing consistent behaviour across any potential subclass, then hardening into a fully final class, preventing subclassing entirely to lock in the immutability guarantee completely.

### Level 1 — Basic

```java
public class MoneyBasic {
    static class Money {
        final long cents; // set once, at construction, never reassigned

        Money(long cents) {
            this.cents = cents;
        }
    }

    public static void main(String[] args) {
        Money price = new Money(1999);
        System.out.println("Cents: " + price.cents);
        // price.cents = 500; // would NOT compile — cents is final
    }
}
```

**How to run:** `java MoneyBasic.java`

`cents` is assigned exactly once, in the constructor — any code attempting to reassign it afterward, from anywhere, would fail to compile, guaranteeing every `Money` object's value is fixed for its entire lifetime.

### Level 2 — Intermediate

Same `Money`, now with a `final` method computing a formatted display, guaranteeing this exact formatting logic can never be silently altered by a subclass.

```java
public class MoneyIntermediate {
    static class Money {
        final long cents;

        Money(long cents) {
            this.cents = cents;
        }

        final String display() { // subclasses cannot override this — formatting stays consistent everywhere
            return "$" + (cents / 100) + "." + String.format("%02d", cents % 100);
        }
    }

    public static void main(String[] args) {
        Money price = new Money(1999);
        System.out.println(price.display()); // $19.99
    }
}
```

**How to run:** `java MoneyIntermediate.java`

Marking `display()` as `final` guarantees that no future subclass of `Money` could override it to produce a different, inconsistent display format — anywhere in the codebase that calls `.display()` on any `Money` (or subclass of `Money`) object can trust it always behaves identically.

### Level 3 — Advanced

Same `Money`, now made entirely `final` as a class, preventing subclassing altogether — the strongest possible guarantee that this specific immutable value type's behaviour can never be altered or extended by anyone.

```java
public class MoneyAdvanced {
    static final class Money { // final class: cannot be extended by anyone, anywhere
        final long cents;

        Money(long cents) {
            if (cents < 0) {
                throw new IllegalArgumentException("Money cannot be negative: " + cents);
            }
            this.cents = cents;
        }

        Money plus(Money other) { // returns a NEW Money — never mutates 'this' or 'other'
            return new Money(this.cents + other.cents);
        }

        String display() {
            return "$" + (cents / 100) + "." + String.format("%02d", cents % 100);
        }
    }

    public static void main(String[] args) {
        Money price1 = new Money(1999);
        Money price2 = new Money(500);

        Money total = price1.plus(price2);

        System.out.println(price1.display()); // $19.99 — unchanged
        System.out.println(price2.display()); // $5.00 — unchanged
        System.out.println(total.display());  // $24.99 — a brand new object
    }
}
```

**How to run:** `java MoneyAdvanced.java`

`Money` being `final` as a class means no code anywhere could ever subclass it to change its behaviour or add mutable state that would undermine its immutability guarantee; combined with `final` fields and returning new objects from `plus` rather than mutating existing ones, `Money` here achieves genuine, fully-locked-down immutability — the same overall design pattern Java's own `String` and boxed number classes (`Integer`, `Double`, etc.) use internally.

## 6. Walkthrough

Trace `price1.plus(price2)` from `MoneyAdvanced.main`, where `price1 = Money(1999)` and `price2 = Money(500)`:

**Method entry.** `plus` is called on `price1` (so `this` refers to `price1`), with `other = price2`.

**Validation via constructor.** `new Money(this.cents + other.cents)` computes `1999 + 500 = 2499`, then calls `Money`'s constructor with `cents = 2499`. Inside, `cents < 0` is `2499 < 0`, false — no exception. `this.cents = 2499` (for this brand-new object).

**Return.** The newly-constructed `Money` object (with `cents = 2499`) is returned and assigned to `total` in `main`. `price1` and `price2` are completely untouched — `plus` never modified either of them, only read their `cents` values to compute a new one.

```
price1.cents = 1999 (unchanged throughout)
price2.cents = 500  (unchanged throughout)
price1.plus(price2):
  computes 1999 + 500 = 2499
  returns new Money(2499)  (a THIRD, separate object)
total.cents = 2499
```

**Display calls.** `price1.display()` computes `1999/100 = 19` and `1999%100 = 99`, formatted as `"$19.99"`. `price2.display()` gives `"$5.00"`. `total.display()` computes `2499/100 = 24` and `2499%100 = 99`, giving `"$24.99"`.

**Final output.** `"$19.99"`, `"$5.00"`, `"$24.99"` — three separate, immutable `Money` objects, none of which were ever mutated after construction, precisely the guarantee `final` fields and a `final` class together provide.

## 7. Gotchas & takeaways

> **A `final` field holding a reference to a mutable object still allows that object's own contents to change — `final` only locks the field's own reference, not the referenced object's internals.** `final List<String> items = new ArrayList<>();` prevents reassigning `items` to a different list, but `items.add(...)` remains completely legal, since the list object itself isn't made immutable by this.

> **`final` on a method only prevents *overriding* it in a subclass — it says nothing about whether the method can be called, or how many times.** A common point of confusion is expecting `final` to mean something about calling restrictions, when it specifically and only concerns whether subclasses may redefine the method's behaviour.

- `final` on a field means it can be assigned exactly once and never reassigned afterward.
- `final` on a method means no subclass can override it, guaranteeing that exact behaviour everywhere it's called.
- `final` on a class means it cannot be subclassed at all, the strongest guarantee against any of its behaviour being altered through inheritance.
- A `final` field referencing a mutable object still allows that object's own internal state to change — `final` locks only the reference itself, not what it points to.
