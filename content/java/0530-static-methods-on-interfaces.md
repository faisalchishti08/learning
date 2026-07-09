---
card: java
gi: 530
slug: static-methods-on-interfaces
title: Static methods on interfaces
---

## 1. What it is

A **static method on an interface** is a method defined with the `static` keyword directly inside an interface, callable on the interface itself (`InterfaceName.methodName(...)`) rather than on an instance. Unlike default methods, static interface methods are **not** inherited by implementing classes — they belong to the interface as a namespace, exactly like static methods on a regular class belong to that class.

## 2. Why & when

Before Java 8, factory methods and helper utilities related to an interface had to live in a separate companion class — `Collections` for `Collection`, `Arrays` for array-related helpers — since interfaces couldn't hold any method with a body at all. Static interface methods let related utility and factory logic live directly on the interface itself, keeping the API discoverable in one place: `Comparator.comparing(...)`, `Comparator.naturalOrder()`, `List.of(...)`, `Stream.of(...)` are all static interface methods, not methods on some separate helper class.

## 3. Core concept

```java
interface Discount {
    double apply(double price);

    static Discount percentage(double percent) { // static factory method on the interface
        return price -> price * (1 - percent / 100);
    }

    static Discount none() {
        return price -> price;
    }
}

Discount tenPercentOff = Discount.percentage(10); // called on the interface, not an instance
System.out.println(tenPercentOff.apply(100.0)); // 90.0
```

`Discount.percentage(10)` is called directly on the interface — there's no `Discount` instance yet, since the static method's job is to *produce* one.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a static interface method is called on the interface itself, not inherited by implementing classes">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="220" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">interface Discount</text>
  <text x="140" y="58" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">static percentage(...) -- factory</text>
  <text x="140" y="72" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">apply(price) -- abstract</text>
  <text x="380" y="45" fill="#6db33f" font-size="11" font-family="sans-serif">Discount.percentage(10)</text>
  <line x1="250" y1="45" x2="370" y2="45" stroke="#6db33f" stroke-width="2" marker-end="url(#arrowSM)"/>
  <text x="380" y="65" fill="#8b949e" font-size="10" font-family="sans-serif">called on the interface itself</text>
  <defs><marker id="arrowSM" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

`percentage(...)` lives on `Discount` as a namespace, called directly without any implementing instance — its job is to construct one.

## 5. Runnable example

Scenario: building a small library of reusable text-validation rules — evolved from a basic static factory method, through combining multiple static factories to build composite rules, to a version demonstrating that static methods are not inherited (a common point of confusion for those coming from class-based static methods).

### Level 1 — Basic

```java
public class StaticInterfaceBasic {
    interface Validator {
        boolean check(String input);

        static Validator minLength(int min) {
            return input -> input != null && input.length() >= min;
        }
    }

    public static void main(String[] args) {
        Validator atLeast5 = Validator.minLength(5); // called on the interface

        System.out.println("'hello' valid: " + atLeast5.check("hello"));
        System.out.println("'hi' valid: " + atLeast5.check("hi"));
    }
}
```

**How to run:** `java StaticInterfaceBasic.java`

Expected output:
```
'hello' valid: true
'hi' valid: false
```

`Validator.minLength(5)` is a static factory method called directly on the `Validator` interface, returning a lambda-backed `Validator` instance (using `Validator` as a functional interface, since it has exactly one abstract method, `check`). `"hello"` (`5` characters) passes; `"hi"` (`2` characters) doesn't.

### Level 2 — Intermediate

```java
public class StaticInterfaceComposed {
    interface Validator {
        boolean check(String input);

        static Validator minLength(int min) {
            return input -> input != null && input.length() >= min;
        }

        static Validator maxLength(int max) {
            return input -> input != null && input.length() <= max;
        }

        // Another static method that COMBINES two Validator instances into one.
        static Validator and(Validator first, Validator second) {
            return input -> first.check(input) && second.check(input);
        }
    }

    public static void main(String[] args) {
        Validator usernameRule = Validator.and(Validator.minLength(3), Validator.maxLength(12));

        System.out.println("'ab' valid: " + usernameRule.check("ab"));
        System.out.println("'alice' valid: " + usernameRule.check("alice"));
        System.out.println("'a_very_long_username' valid: " + usernameRule.check("a_very_long_username"));
    }
}
```

**How to run:** `java StaticInterfaceComposed.java`

Expected output:
```
'ab' valid: false
'alice' valid: true
'a_very_long_username' valid: false
```

The real-world concern this adds: `Validator.and(...)` is itself a static factory method, but it takes *other* `Validator` instances as arguments and combines them into a new one — building a small composable rules library entirely through static interface methods, without needing any separate builder or utility class. `"ab"` fails the minimum length; `"a_very_long_username"` fails the maximum length; only `"alice"` satisfies both.

### Level 3 — Advanced

```java
public class StaticNotInherited {
    interface Validator {
        boolean check(String input);

        static Validator minLength(int min) {
            return input -> input != null && input.length() >= min;
        }
    }

    // A class implementing Validator -- but static methods are NOT part of what it inherits.
    static class StrictValidator implements Validator {
        @Override public boolean check(String input) {
            return input != null && !input.isBlank();
        }
    }

    public static void main(String[] args) {
        // This works: calling the static method on the INTERFACE.
        Validator viaInterface = Validator.minLength(5);
        System.out.println("Via interface: " + viaInterface.check("hello"));

        // This does NOT compile if uncommented -- static methods aren't inherited by implementers:
        // Validator viaClass = StrictValidator.minLength(5); // COMPILE ERROR

        // StrictValidator only has its own instance method, check(), fully independent of minLength(...).
        StrictValidator strict = new StrictValidator();
        System.out.println("StrictValidator's own check(): " + strict.check("  "));
    }
}
```

**How to run:** `java StaticNotInherited.java`

Expected output:
```
Via interface: true
StrictValidator's own check(): false
```

This demonstrates the key distinction from default methods: `Validator.minLength(5)` must be called on `Validator` itself — attempting `StrictValidator.minLength(5)` would not compile, since static interface methods are **not** inherited by implementing classes, unlike default methods (see [[default-methods]]), which *are* inherited. `StrictValidator` has its own, entirely separate `check(...)` instance method, with no relationship to `minLength(...)` at all beyond both existing somewhere in the same interface hierarchy.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. First, `Validator viaInterface = Validator.minLength(5)` calls the static method directly on the `Validator` interface — the JVM resolves `minLength` as belonging to `Validator`'s own namespace, no instance involved, and it returns a lambda `input -> input != null && input.length() >= 5`, stored as `viaInterface`.

`viaInterface.check("hello")` invokes that lambda: `"hello" != null` is `true`, `"hello".length() >= 5` is `5 >= 5`, `true` — both conditions hold, so `check` returns `true`, printed as `"Via interface: true"`.

The commented-out line, `StrictValidator.minLength(5)`, is included specifically to illustrate what would happen if attempted: the Java compiler does not consider `minLength` to be a member of `StrictValidator` at all, even though `StrictValidator implements Validator`, because static interface methods are excluded from inheritance by the Java Language Specification — only instance methods (abstract and default) are inherited by implementing classes.

`StrictValidator strict = new StrictValidator()` creates an instance, and `strict.check("  ")` calls `StrictValidator`'s own `check` implementation (an entirely separate override of the `check` abstract method, unrelated to `minLength`): `"  " != null` is `true`, but `!"  ".isBlank()` — since `"  "` is all whitespace, `.isBlank()` returns `true`, so `!true` is `false`. The overall `&&` expression is `false`, so `check` returns `false`, printed as `"StrictValidator's own check(): false"`.

```
Validator.minLength(5)         -- static call ON THE INTERFACE, produces a lambda-backed Validator
viaInterface.check("hello")    -- instance call on that lambda: length 5 >= 5 -> true

StrictValidator.minLength(5)   -- WOULD NOT COMPILE: static methods aren't inherited by implementers

strict.check("  ")             -- instance call on StrictValidator's OWN check(): isBlank() true -> false
```

The two `check` behaviors (`viaInterface`'s length check versus `StrictValidator`'s own blank check) are entirely independent implementations, connected only by both fulfilling the same `Validator` interface's abstract `check` method — `minLength(...)` never enters `StrictValidator`'s picture at all.

## 7. Gotchas & takeaways

> A common point of confusion for developers used to static methods on classes (where subclasses *can* reference an inherited static method, e.g. `Subclass.staticMethod()` if `staticMethod` is defined on `Superclass`) is that this does **not** carry over to interfaces and their implementers — static interface methods belong strictly to the interface itself and are never inherited by implementing classes, only by extending interfaces (an interface can inherit another interface's static methods only through explicit re-declaration, which is uncommon).

- A static interface method (`static` keyword + body, inside an interface) is called on the interface directly, like `InterfaceName.method(...)`, never on an instance.
- Static interface methods are commonly used as factory methods, producing instances of the interface — `Comparator.comparing(...)`, `List.of(...)`, `Stream.of(...)` are all examples from the JDK itself.
- Unlike default methods, static interface methods are **not** inherited by implementing classes — a class implementing the interface cannot call the static method through itself.
- Static interface methods let related factory and utility logic live directly on the interface, rather than requiring a separate companion utility class (as was necessary before Java 8, e.g. `Collections` alongside `Collection`).
- Static interface methods can call and combine other static methods (as `and(...)` combines two `Validator` instances), enabling a fluent, composable API built entirely within the interface itself.
