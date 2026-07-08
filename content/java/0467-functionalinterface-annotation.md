---
card: java
gi: 467
slug: functionalinterface-annotation
title: '@FunctionalInterface annotation'
---

## 1. What it is

`@FunctionalInterface` is a marker annotation, added in Java 8, that you put on an interface declaration to assert "this interface has exactly one abstract method, and is intended to be implemented by a lambda." It doesn't change how the interface behaves — an interface with exactly one abstract method is a valid lambda target with or without this annotation — but it makes the compiler **enforce** that single-abstract-method property, turning an accidental second abstract method into a compile error instead of a silent design mistake.

## 2. Why & when

Without `@FunctionalInterface`, nothing stops someone from adding a second abstract method to an interface you designed to be used with lambdas — the change compiles fine right up until every place that assigned a lambda to that interface suddenly breaks, potentially far away from the interface itself and with a confusing error message. `@FunctionalInterface` moves that check to the interface's own declaration: the moment a second abstract method is added, the compiler flags it immediately, at the point of the mistake, with a clear message — not later, scattered across every call site.

You add `@FunctionalInterface` to any interface **you design** with the intention that it be implemented via a lambda — it documents your intent to future maintainers and gets the compiler's help enforcing it. You don't need to add it to interfaces you merely *use* as lambda targets (like `Comparator`, `Runnable`, or anything in `java.util.function`) — those are already annotated in the JDK itself. Leaving it off your own interface doesn't break anything either; it's a safety net and a documentation tool, not a requirement for an interface to work with lambdas.

## 3. Core concept

```java
@FunctionalInterface
interface Validator<T> {
    boolean isValid(T value); // exactly one abstract method -- required for a lambda target

    // default and static methods are fine -- they don't count as "abstract"
    default Validator<T> negate() {
        return value -> !isValid(value);
    }
}

// interface BrokenValidator {
//     boolean isValid(String value);
//     boolean isReady(); // a SECOND abstract method
// }
// @FunctionalInterface on BrokenValidator above would be a COMPILE ERROR:
// "BrokenValidator is not a functional interface -- multiple non-overriding abstract methods found"
```

`Validator<T>` compiles cleanly because it has exactly one abstract method; a hypothetical second abstract method on an `@FunctionalInterface`-annotated interface would fail to compile immediately, at the interface declaration itself.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FunctionalInterface enforces exactly one abstract method at the interface declaration, catching a mistake immediately instead of at every distant call site">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="260" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">@FunctionalInterface Validator</text>
  <text x="160" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">exactly one abstract method: OK</text>

  <rect x="350" y="30" width="260" height="50" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="480" y="50" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">+ second abstract method added</text>
  <text x="480" y="68" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">compile error, right here</text>

  <text x="30" y="115" fill="#8b949e" font-size="10" font-family="sans-serif">Without the annotation: same mistake compiles fine, breaks every distant lambda call site instead.</text>
</svg>

The annotation moves the failure from "many confusing errors, far away" to "one clear error, right at the source."

## 5. Runnable example

Scenario: a small validation framework — evolved from a correctly annotated single-method interface used with a lambda, through combining validators with a `default` method (which doesn't affect the single-abstract-method count), to demonstrating what the compiler catches if a second abstract method is mistakenly added.

### Level 1 — Basic

```java
public class FunctionalInterfaceBasic {
    @FunctionalInterface
    interface Validator<T> {
        boolean isValid(T value);
    }

    public static void main(String[] args) {
        Validator<String> notBlank = value -> !value.trim().isEmpty();

        System.out.println(notBlank.isValid("hello"));
        System.out.println(notBlank.isValid("   "));
    }
}
```

**How to run:** `java FunctionalInterfaceBasic.java`

Expected output:
```
true
false
```

`Validator<T>` has exactly one abstract method, `isValid`, so `@FunctionalInterface` compiles without complaint, and the interface can be implemented directly by the lambda `value -> !value.trim().isEmpty()`.

### Level 2 — Intermediate

```java
public class FunctionalInterfaceDefaultMethods {
    @FunctionalInterface
    interface Validator<T> {
        boolean isValid(T value); // the ONE abstract method

        // default methods have a body -- they don't count toward the abstract-method total,
        // so a functional interface can have as many of these as it wants.
        default Validator<T> negate() {
            return value -> !isValid(value);
        }

        default Validator<T> and(Validator<T> other) {
            return value -> isValid(value) && other.isValid(value);
        }
    }

    public static void main(String[] args) {
        Validator<String> notBlank = value -> !value.trim().isEmpty();
        Validator<String> shortEnough = value -> value.length() <= 10;

        Validator<String> combined = notBlank.and(shortEnough);

        System.out.println(combined.isValid("hello"));
        System.out.println(combined.isValid("this is way too long"));
        System.out.println(notBlank.negate().isValid("   "));
    }
}
```

**How to run:** `java FunctionalInterfaceDefaultMethods.java`

Expected output:
```
true
false
true
```

The real-world concern this shows: `default` methods (`negate`, `and`) have bodies, so the compiler doesn't count them as "abstract" at all — a functional interface can have any number of `default` (and `static`) methods, as long as exactly one method remains genuinely abstract. `and` and `negate` both *return* new `Validator<T>` lambdas built by combining existing ones, a common and powerful pattern once an interface is confirmed single-abstract-method.

### Level 3 — Advanced

```java
public class FunctionalInterfaceViolation {
    // Deliberately BROKEN: two abstract methods on an interface annotated @FunctionalInterface.
    // This is what a compile error for this looks like -- shown here as a comment, since
    // including it uncommented would make the whole file fail to compile.
    //
    // @FunctionalInterface
    // interface BrokenValidator<T> {
    //     boolean isValid(T value);
    //     boolean isReady(); // second abstract method -- COMPILE ERROR:
    //     // "BrokenValidator is not a functional interface
    //     //  multiple non-overriding abstract methods found in interface BrokenValidator"
    // }

    // The FIX: move the second method's logic into a default method that delegates,
    // or split it into a genuinely separate interface -- restoring exactly one abstract method.
    @FunctionalInterface
    interface FixedValidator<T> {
        boolean isValid(T value);

        default boolean isReady() {
            return true; // now a default method: no longer counted as abstract
        }
    }

    public static void main(String[] args) {
        FixedValidator<String> notBlank = value -> !value.trim().isEmpty();

        System.out.println(notBlank.isValid("hello"));
        System.out.println(notBlank.isReady());
    }
}
```

**How to run:** `java FunctionalInterfaceViolation.java`

Expected output:
```
true
true
```

This demonstrates the fix for the exact mistake `@FunctionalInterface` is designed to catch: `isReady()` started as a second abstract method (which would fail to compile), and was corrected into a `default` method with a body — restoring the single-abstract-method property the annotation requires, while still exposing `isReady()` as a usable method on the interface, just with a built-in default implementation rather than one every lambda would need to supply.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `notBlank` is assigned a lambda, `value -> !value.trim().isEmpty()`, targeted against `FixedValidator<String>`.

Because `FixedValidator<T>` has exactly one abstract method (`isValid`), the compiler accepts this lambda as a valid implementation: the lambda's shape (one `String` parameter, `boolean` result) matches `isValid(T value)` exactly, and it becomes the implementation of that single abstract method.

`notBlank.isValid("hello")` calls the lambda with `value = "hello"`. `value.trim()` produces `"hello"` unchanged (no surrounding whitespace to remove), `.isEmpty()` on that is `false`, and the leading `!` negates it to `true` — printed as the first line.

`notBlank.isReady()` calls `isReady`, but `notBlank` (the lambda) never provided an implementation for it — nor could it, since a lambda only ever implements the interface's one abstract method. Instead, this call resolves to `FixedValidator`'s `default` implementation, which simply returns `true` unconditionally, printed as the second line.

```
notBlank = lambda implementing isValid(String) only
notBlank.isValid("hello")  --> lambda body runs   --> true
notBlank.isReady()          --> default method runs --> true (lambda has no say here)
```

This is the concrete payoff of the annotation: because `FixedValidator` genuinely has only one abstract method, a lambda can implement it fully, while `default` methods like `isReady` remain available on every instance — including lambda-created ones — without the lambda ever needing to know they exist.

## 7. Gotchas & takeaways

> `@FunctionalInterface` is **optional** — an interface with exactly one abstract method is already usable as a lambda target without it. The annotation adds a compile-time *check*, not a capability. Omitting it on your own single-abstract-method interfaces doesn't break anything today, but it removes the safety net that catches a future, accidental second abstract method before it silently breaks every lambda that implements the interface.

- `@FunctionalInterface` asserts, and the compiler enforces, that an interface has exactly one abstract method — the requirement for being a valid lambda target.
- `default` and `static` methods have bodies and never count toward the abstract-method total — a functional interface can have any number of them alongside its one abstract method.
- Adding a second abstract method to an `@FunctionalInterface`-annotated interface is a compile error at the interface declaration itself, catching the mistake immediately rather than at every distant lambda call site.
- Applying the annotation is best practice on interfaces **you design** for lambda use, even though it's not required — it documents intent and adds a safety net for future changes.
- Every relevant interface in `java.util.function` (`Function`, `Predicate`, `Consumer`, `Supplier`, and the rest) is already annotated `@FunctionalInterface` in the JDK, so you get this same protection automatically when using them.
