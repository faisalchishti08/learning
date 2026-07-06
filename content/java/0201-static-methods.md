---
card: java
gi: 201
slug: static-methods
title: static methods
---

## 1. What it is

A **static method** is declared with the `static` keyword and belongs to the class itself, callable without ever creating an instance. Because it's not tied to any particular object, a static method has no access to `this` and cannot directly read or write instance (non-static) fields — it can only work with its own parameters, local variables, and other static members of the class.

```java
class MathHelper {
    static int square(int n) { // no object needed to call this
        return n * n;
    }
}

int result = MathHelper.square(5); // called through the CLASS name, no 'new' anywhere
System.out.println(result); // 25
```

`MathHelper.square(5)` never requires a `MathHelper` object to exist at all — the method is called directly on the class itself, which is exactly the point of marking it `static`: it represents a self-contained operation that doesn't need any particular instance's data to do its job.

## 2. Why & when

Static methods exist for behaviour that is a property of the class or concept as a whole, rather than behaviour that depends on one specific object's individual state:

- **Utility and helper functions** — pure computations that only depend on their parameters, like `Math.sqrt(x)`, `Arrays.sort(array)`, or a custom validation/conversion function that has no need for any instance-specific data.
- **Factory methods** — a static method that constructs and returns instances of the class, sometimes used instead of (or alongside) constructors when extra logic or a more descriptive name is useful (e.g., `LocalDate.of(2024, 1, 15)`).
- **The `main` method itself is static** — this is precisely why `public static void main(String[] args)` can be the JVM's entry point without needing any object to exist first; the JVM simply calls it directly on the class.

Choose `static` for a method specifically when its logic doesn't need to read or modify any particular object's instance fields — if it only needs its parameters (and perhaps other static state), it's a good candidate; the moment it needs `this.someField`, it must be an instance method instead.

## 3. Core concept

```java
class Converter {
    static double celsiusToFahrenheit(double celsius) { // no instance data needed at all
        return celsius * 9.0 / 5.0 + 32.0;
    }

    // static int broken() {
    //     return someInstanceField; // COMPILE ERROR — static methods cannot access instance fields directly
    // }
}

public class StaticMethodDemo {
    public static void main(String[] args) {
        double f = Converter.celsiusToFahrenheit(100.0); // called with no Converter object anywhere
        System.out.println(f); // 212.0
    }
}
```

`celsiusToFahrenheit` never needs `this` — it computes its result purely from its parameter `celsius` — which is exactly why it can, and should, be `static`; a hypothetical attempt to read a non-static (instance) field from inside a static method would fail to compile, since there is no specific object for that field reference to belong to.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A static method called directly on the class itself with no object required, contrasted with an instance method which can only be called on an actual object and has access to that object's own fields via this">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="30" y="30" width="240" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ClassName.staticMethod(args)</text>
  <text x="150" y="66" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no object needed, no "this" available</text>

  <rect x="330" y="30" width="240" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">objectRef.instanceMethod(args)</text>
  <text x="450" y="66" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">needs an object; "this" refers to it</text>

  <text x="300" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Static methods work only with their parameters and other static members — never with instance fields.</text>
</svg>

Static methods are called on the class; instance methods are called on a specific object and can access that object's own state.

## 5. Runnable example

Scenario: a small validation and formatting utility for phone numbers — starting with a basic static utility method, then extending with a static factory method that validates before constructing, then hardening into a class that clearly separates static utility logic from instance-specific behaviour.

### Level 1 — Basic

```java
public class PhoneBasic {

    static boolean isValidLength(String digits) {
        return digits.length() == 10;
    }

    public static void main(String[] args) {
        System.out.println(isValidLength("5551234567")); // true
        System.out.println(isValidLength("123"));          // false
    }
}
```

**How to run:** `java PhoneBasic.java`

`isValidLength` only needs its parameter `digits` to do its job — no object's individual state is required, so it's naturally a `static` method, called directly without any instance of anything existing.

### Level 2 — Intermediate

Same idea, now with a static **factory method** that validates input before constructing a `PhoneNumber` object, only returning an object once the input has been confirmed valid.

```java
public class PhoneIntermediate {
    static class PhoneNumber {
        String digits;

        private PhoneNumber(String digits) { // private constructor: force creation through the factory
            this.digits = digits;
        }

        static PhoneNumber parse(String raw) { // static factory method
            String digits = raw.replaceAll("[^0-9]", ""); // strip anything that isn't a digit
            if (digits.length() != 10) {
                throw new IllegalArgumentException("Invalid phone number: " + raw);
            }
            return new PhoneNumber(digits);
        }

        String formatted() {
            return "(" + digits.substring(0, 3) + ") " + digits.substring(3, 6) + "-" + digits.substring(6);
        }
    }

    public static void main(String[] args) {
        PhoneNumber p = PhoneNumber.parse("555-123-4567");
        System.out.println(p.formatted());
    }
}
```

**How to run:** `java PhoneIntermediate.java`

`PhoneNumber.parse(...)` is a static factory method — it performs cleanup and validation logic that doesn't belong to any particular instance yet (there isn't one until parsing succeeds), then calls the `private` constructor itself and returns the resulting object; making the constructor `private` forces every caller to go through this validating factory method instead of bypassing it.

### Level 3 — Advanced

Same phone number handling, now with a static method that batch-validates a whole array of raw phone number strings, clearly separating this stateless, static batch-processing logic from the instance method (`formatted()`) that genuinely depends on one specific object's own data.

```java
import java.util.ArrayList;
import java.util.List;

public class PhoneAdvanced {
    static class PhoneNumber {
        String digits;

        private PhoneNumber(String digits) {
            this.digits = digits;
        }

        static PhoneNumber parse(String raw) {
            String digits = raw.replaceAll("[^0-9]", "");
            if (digits.length() != 10) {
                throw new IllegalArgumentException("Invalid phone number: " + raw);
            }
            return new PhoneNumber(digits);
        }

        String formatted() { // instance method: genuinely depends on THIS object's own digits
            return "(" + digits.substring(0, 3) + ") " + digits.substring(3, 6) + "-" + digits.substring(6);
        }

        static List<PhoneNumber> parseAll(String[] rawNumbers) { // static: batch operation, no single instance involved
            List<PhoneNumber> results = new ArrayList<>();
            for (String raw : rawNumbers) {
                try {
                    results.add(parse(raw));
                } catch (IllegalArgumentException e) {
                    System.out.println("Skipping invalid entry: " + e.getMessage());
                }
            }
            return results;
        }
    }

    public static void main(String[] args) {
        String[] rawNumbers = { "555-123-4567", "bad-number", "800-555-0199" };

        List<PhoneNumber> valid = PhoneNumber.parseAll(rawNumbers);
        for (PhoneNumber p : valid) {
            System.out.println(p.formatted()); // instance method, called on each specific object
        }
    }
}
```

**How to run:** `java PhoneAdvanced.java`

`parseAll` is `static` because it operates on a whole array, producing a list of results — it has no single "current object" to be an instance method of; `formatted()`, called once per resulting `PhoneNumber` object inside the loop, is correctly an instance method, since it genuinely needs each specific object's own `digits` field to produce its result.

## 6. Walkthrough

Trace `PhoneAdvanced.main`:

**`PhoneNumber.parseAll(rawNumbers)`.** This static method iterates over all three raw strings.

**First entry, `"555-123-4567"`.** `parse("555-123-4567")` strips non-digits, yielding `"5551234567"` (10 digits) — passes validation, returns a new `PhoneNumber` object, added to `results`.

**Second entry, `"bad-number"`.** `parse("bad-number")` strips non-digits (letters aren't digits either), yielding an empty or very short string, definitely not length 10 — throws `IllegalArgumentException`. Back in `parseAll`, the `catch` block catches this and prints `"Skipping invalid entry: Invalid phone number: bad-number"`; this entry is never added to `results`.

**Third entry, `"800-555-0199"`.** Strips to `"8005550199"` (10 digits) — passes, added to `results`.

**Return.** `parseAll` returns `results`, now containing exactly 2 `PhoneNumber` objects (skipping the invalid one entirely).

```
parseAll(["555-123-4567", "bad-number", "800-555-0199"]):
  parse("555-123-4567") -> "5551234567" (10 digits) -> OK, added
  parse("bad-number")   -> too few digits -> throws -> caught, skipped, printed
  parse("800-555-0199") -> "8005550199" (10 digits) -> OK, added
  returns [PhoneNumber(5551234567), PhoneNumber(8005550199)]
```

**Formatting loop.** `main` then calls `.formatted()` on each of the 2 valid `PhoneNumber` objects in the returned list: `"(555) 123-4567"` and `"(800) 555-0199"`.

**Final output.** `"Skipping invalid entry: Invalid phone number: bad-number"`, followed by `"(555) 123-4567"` and `"(800) 555-0199"` — the exact order depends on when the skip message prints relative to the loop, but since `parseAll` runs to completion (including the skip message) before `main`'s formatting loop begins, the skip message appears first.

## 7. Gotchas & takeaways

> **A static method cannot directly access instance (non-static) fields or call instance methods, because it has no `this` — there is no specific object for that data to belong to.** Attempting to reference an instance field from inside a static method is a compile error, not a runtime one; the compiler catches this mismatch immediately.

> **A common misuse is making a method `static` purely out of habit or convenience, even when it genuinely needs per-object state** — if a method needs to read or modify a specific instance's fields, it must be an instance method; forcing it to be `static` (by, say, passing the object in as an extra parameter instead of calling the method on it) usually signals the method was designed incorrectly.

- A static method belongs to the class and can be called with no object needing to exist first.
- Static methods cannot access instance fields or call instance methods directly, since there's no `this` for them to refer to.
- Static factory methods are a common, idiomatic pattern for validating input before constructing an object, especially when paired with a `private` constructor.
- Choose `static` when a method's logic depends only on its parameters (and other static state), and an instance method when it genuinely needs a specific object's own field values.
