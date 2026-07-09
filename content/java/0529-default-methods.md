---
card: java
gi: 529
slug: default-methods
title: Default methods
---

## 1. What it is

A **default method** is a method defined inside an interface with a `default` keyword and a method body, instead of just a signature. Before Java 8, every method in an interface had to be abstract (no body), meaning any class implementing that interface had to provide its own implementation for every single method. Default methods let an interface provide a working implementation directly, which implementing classes automatically inherit and can optionally override.

## 2. Why & when

Default methods were introduced specifically to solve a real problem: how do you add a new method to an interface that's already widely implemented (like `Collection` or `List`) without breaking every existing class that implements it? Before Java 8, adding a method to an interface would force every implementer to add that method too, or fail to compile. Default methods let the JDK add new capabilities — `List.sort(...)`, `Collection.stream()`, `Map.getOrDefault(...)`, and many others — to existing interfaces, with a sensible default implementation that existing classes get for free, without any changes needed on their part.

## 3. Core concept

```java
interface Greeter {
    String name(); // abstract -- implementers must provide this

    default String greet() { // default -- implementers get this for free
        return "Hello, " + name() + "!";
    }
}

class Person implements Greeter {
    private final String name;
    Person(String name) { this.name = name; }
    @Override public String name() { return name; } // only the abstract method needs implementing
}

Person p = new Person("Alice");
System.out.println(p.greet()); // "Hello, Alice!" -- inherited from the interface, no override needed
```

`Person` only implements `name()`; `greet()` comes free from the interface's default implementation, which itself calls `name()` to produce its result.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a default method provides a working implementation in the interface itself, inherited by implementing classes">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="220" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="40" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">interface Greeter</text>
  <text x="140" y="58" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">name() -- abstract</text>
  <text x="140" y="72" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">greet() -- default, has body</text>
  <line x1="140" y1="80" x2="140" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowDM)"/>
  <rect x="30" y="105" width="220" height="0" fill="none"/>
  <text x="140" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">class Person implements Greeter -- inherits greet() for free</text>
  <defs><marker id="arrowDM" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`Person` inherits `greet()` automatically, needing to implement only the abstract `name()` method.

## 5. Runnable example

Scenario: building a small validation framework where multiple rule types share common reporting behavior — evolved from a basic default method, through overriding a default method in a specific implementation, to a version where multiple default methods interact, including one default method calling another.

### Level 1 — Basic

```java
public class DefaultMethodBasic {
    interface ValidationRule {
        boolean isValid(String input);

        default String describe(String input) {
            return isValid(input) ? "VALID: " + input : "INVALID: " + input;
        }
    }

    static class NonEmptyRule implements ValidationRule {
        @Override public boolean isValid(String input) {
            return input != null && !input.isBlank();
        }
    }

    public static void main(String[] args) {
        ValidationRule rule = new NonEmptyRule();
        System.out.println(rule.describe("hello"));
        System.out.println(rule.describe(""));
    }
}
```

**How to run:** `java DefaultMethodBasic.java`

Expected output:
```
VALID: hello
INVALID: 
```

`NonEmptyRule` implements only the abstract `isValid(...)` method; `describe(...)` comes entirely from `ValidationRule`'s default implementation, which internally calls `isValid(...)` — since `NonEmptyRule` provides that, `describe(...)` works correctly without `NonEmptyRule` ever writing its own version of it.

### Level 2 — Intermediate

```java
public class DefaultMethodOverride {
    interface ValidationRule {
        boolean isValid(String input);

        default String describe(String input) {
            return isValid(input) ? "VALID: " + input : "INVALID: " + input;
        }
    }

    static class NonEmptyRule implements ValidationRule {
        @Override public boolean isValid(String input) {
            return input != null && !input.isBlank();
        }
    }

    static class LengthRule implements ValidationRule {
        private final int minLength;
        LengthRule(int minLength) { this.minLength = minLength; }

        @Override public boolean isValid(String input) {
            return input != null && input.length() >= minLength;
        }

        // Overriding the default -- this rule wants a more specific message, not the generic one.
        @Override public String describe(String input) {
            return isValid(input)
                    ? "VALID: '" + input + "' meets minimum length " + minLength
                    : "INVALID: '" + input + "' is shorter than " + minLength + " characters";
        }
    }

    public static void main(String[] args) {
        ValidationRule nonEmpty = new NonEmptyRule();
        ValidationRule minLength5 = new LengthRule(5);

        System.out.println(nonEmpty.describe("hi"));      // uses the DEFAULT describe
        System.out.println(minLength5.describe("hi"));    // uses LengthRule's OVERRIDDEN describe
    }
}
```

**How to run:** `java DefaultMethodOverride.java`

Expected output:
```
VALID: hi
INVALID: 'hi' is shorter than 5 characters
```

The real-world concern this adds: a default method is just that — a *default*, not a mandate. `LengthRule` overrides `describe(...)` with its own, more specific implementation (an ordinary `@Override`, exactly like overriding any inherited method), while `NonEmptyRule` doesn't bother, and simply keeps using the interface's default version. Both are entirely valid — a default method gives implementers a *choice*, not a requirement.

### Level 3 — Advanced

```java
public class DefaultMethodChaining {
    interface ValidationRule {
        boolean isValid(String input);

        default String describe(String input) {
            return isValid(input) ? "VALID: " + input : "INVALID: " + input;
        }

        // A default method that calls ANOTHER default method -- building on top of describe().
        default String describeWithSeverity(String input, boolean critical) {
            String base = describe(input); // calls the (possibly overridden) describe()
            return critical ? "[CRITICAL] " + base : "[info] " + base;
        }
    }

    static class LengthRule implements ValidationRule {
        private final int minLength;
        LengthRule(int minLength) { this.minLength = minLength; }

        @Override public boolean isValid(String input) {
            return input != null && input.length() >= minLength;
        }

        @Override public String describe(String input) {
            return isValid(input)
                    ? "'" + input + "' meets minimum length " + minLength
                    : "'" + input + "' is too short (needs " + minLength + "+ chars)";
        }
    }

    public static void main(String[] args) {
        ValidationRule rule = new LengthRule(8);

        System.out.println(rule.describeWithSeverity("password123", true));
        System.out.println(rule.describeWithSeverity("hi", false));
    }
}
```

**How to run:** `java DefaultMethodChaining.java`

Expected output:
```
[CRITICAL] 'password123' meets minimum length 8
[info] 'hi' is too short (needs 8+ chars)
```

This shows one default method (`describeWithSeverity`) calling *another* default method (`describe`) from within the same interface — and because `LengthRule` overrides `describe(...)`, `describeWithSeverity(...)` (which `LengthRule` does **not** override) automatically picks up `LengthRule`'s custom `describe(...)` when it calls `describe(input)` internally, exactly the same way any regular method dispatch works through inheritance.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `rule` is a `LengthRule` instance with `minLength = 8`.

`rule.describeWithSeverity("password123", true)` is called. `LengthRule` doesn't override `describeWithSeverity`, so the interface's default implementation runs: `String base = describe(input)`. This call to `describe(input)` is resolved via normal virtual dispatch — since `rule`'s actual runtime type is `LengthRule`, and `LengthRule` *does* override `describe(...)`, `LengthRule`'s version runs, not `ValidationRule`'s original default.

Inside `LengthRule.describe("password123")`: `isValid("password123")` checks `"password123".length() >= 8`, i.e. `11 >= 8`, `true`. Since valid, it returns `"'password123' meets minimum length 8"`.

Back in `describeWithSeverity`, `base` is now `"'password123' meets minimum length 8"`. Since `critical` is `true`, the method returns `"[CRITICAL] " + base`, i.e. `"[CRITICAL] 'password123' meets minimum length 8"`.

```
rule.describeWithSeverity("password123", true)
  -> default describeWithSeverity runs (not overridden)
     -> calls describe("password123") -- dispatches to LengthRule's OVERRIDE, not the interface default
        -> isValid: 11 >= 8 true -> "'password123' meets minimum length 8"
     -> base = "'password123' meets minimum length 8"
     -> critical=true -> "[CRITICAL] " + base
```

`main` prints `"[CRITICAL] 'password123' meets minimum length 8"`. The second call, `rule.describeWithSeverity("hi", false)`, follows the same path: `describe("hi")` calls `LengthRule`'s override, `isValid("hi")` checks `2 >= 8`, `false`, so it returns `"'hi' is too short (needs 8+ chars)"`; with `critical=false`, the final result is prefixed `"[info] "` instead, printed as `"[info] 'hi' is too short (needs 8+ chars)"`.

## 7. Gotchas & takeaways

> When a default method calls another method on the same interface (like `describeWithSeverity` calling `describe`), that call always goes through **normal virtual dispatch** — if the implementing class overrides the called method, the override runs, even from inside a default method the class did *not* override. This is exactly how ordinary method inheritance works in Java, but it's worth being explicit about, since it means a default method's *behavior* can change based on what the implementing class overrides elsewhere, even if the default method's own code is untouched.

- A default method (`default` keyword + method body, inside an interface) provides a working implementation that implementing classes inherit automatically.
- Default methods were introduced specifically to let existing interfaces (like `Collection`, `List`, `Map`) gain new methods without breaking every class that already implements them.
- An implementing class can override a default method with `@Override`, exactly like overriding a regular inherited method — the default is a starting point, not a mandate.
- A default method can call other methods on the same interface, including other default methods or abstract methods — those calls resolve via normal virtual dispatch, respecting whatever the concrete implementing class overrides.
- Default methods make interfaces closer to abstract classes in capability (shared implementation code), but interfaces still cannot hold instance state (fields) the way abstract classes can — default methods can only compute from arguments and other interface methods, not from stored fields of their own.
