---
card: java
gi: 954
slug: record-components-canonical-constructor
title: Record components & canonical constructor
---

## 1. What it is

A record is a special kind of class, standardized in Java 16, designed specifically to model an immutable aggregate of data with minimal boilerplate. Its header declares its **components** — `record Point(int x, int y) {}` declares two components, `x` and `y` — and from just that one line, the compiler automatically generates: a **private final field** for each component, a public accessor method matching each component's name (`x()`, `y()` — not `getX()`, deliberately breaking from JavaBeans convention to signal these are plain data accessors, not arbitrary computed getters), and a **canonical constructor**, which takes exactly the components in declared order and assigns each directly to its matching field. The canonical constructor is the one the compiler always guarantees exists in some form — you can write it explicitly to add validation or normalization logic, but even if you never write it yourself, the compiler synthesizes an implicit one that does exactly the straightforward field-assignment version.

## 2. Why & when

Records exist to eliminate the enormous amount of near-identical, error-prone boilerplate that plain immutable data classes required before Java 16 — a private final field, a constructor, an accessor, and correct `equals`/`hashCode`/`toString` implementations for every single simple data-carrying class, each one an opportunity for a copy-paste mistake (a `hashCode` that doesn't match `equals`, a `toString` someone forgot to update after adding a field). Reach for a record whenever you're modeling a simple, transparent, immutable data aggregate — a coordinate pair, a money amount, a request/response DTO, a key in a map — where the entire point of the type is "this exact combination of these exact values," not encapsulated internal state or behavior beyond the data itself. Records are the wrong choice when a class needs mutable state, needs to hide its internal representation behind a genuinely different public API (records' components are inherently part of the public contract), or needs to participate in a class hierarchy via `extends` (records cannot extend any other class, since they implicitly extend the sealed `java.lang.Record`, though they can implement interfaces — see [records implementing interfaces](0957-records-implementing-interfaces.md)).

## 3. Core concept

```
record Point(int x, int y) {}

// The line above is EQUIVALENT to hand-writing all of this:
final class Point extends Record {
    private final int x;
    private final int y;
    Point(int x, int y) {         // the CANONICAL constructor -- auto-generated if not written explicitly
        this.x = x;
        this.y = y;
    }
    public int x() { return x; }  // accessor -- note: x(), NOT getX()
    public int y() { return y; }
    // equals(), hashCode(), toString() also auto-generated, based on ALL components
}
```

Every record component becomes exactly three things automatically: a private final field, a same-named accessor method, and a parameter position in the canonical constructor — writing the constructor explicitly only lets you intercept and modify what happens during construction, not change which fields exist or how they're accessed.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single record declaration line expanding into a private final field, an accessor method, and a canonical constructor parameter for each component" >
  <rect x="20" y="30" width="180" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="49" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">record Point(int x, int y)</text>

  <line x1="110" y1="60" x2="110" y2="90" stroke="#8b949e"/>

  <rect x="20" y="95" width="180" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="114" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">private final int x, y;</text>

  <rect x="230" y="95" width="180" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="114" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">int x() {...} int y() {...}</text>

  <rect x="440" y="95" width="180" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="530" y="114" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Point(int x, int y) {...}</text>

  <text x="320" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">One declaration, three auto-generated members, per component</text>
</svg>

*Each record component becomes a field, an accessor, and a canonical-constructor parameter, all from one declaration.*

## 5. Runnable example

Scenario: model a temperature reading as a record, evolving from the basic auto-generated form, to adding validation via an explicit canonical constructor, to a more advanced case with normalization logic that must still preserve the canonical constructor's essential contract.

### Level 1 — Basic

```java
public class RecordCanonicalBasic {
    record Temperature(double celsius) {}

    public static void main(String[] args) {
        Temperature t = new Temperature(21.5);
        System.out.println("celsius: " + t.celsius());
        System.out.println("toString: " + t);
        System.out.println("equals check: " + t.equals(new Temperature(21.5)));
    }
}
```

**How to run:** `java RecordCanonicalBasic.java` (JDK 17+).

Expected output:
```
celsius: 21.5
toString: RecordCanonicalBasic$Temperature[celsius=21.5]
equals check: true
```

With just the one-line `record Temperature(double celsius) {}` declaration, the accessor `celsius()`, a working `toString()` (listing every component by name), and a correct `equals()` (comparing all components) are all present with zero additional code — this is the implicit canonical constructor and auto-generated members at work, entirely without an explicit constructor being written.

### Level 2 — Intermediate

```java
public class RecordCanonicalValidation {
    record Temperature(double celsius) {
        // An EXPLICIT canonical constructor -- same parameter list, same order, as the header.
        // This is the standard way to add validation to a record.
        Temperature {
            if (celsius < -273.15) {
                throw new IllegalArgumentException("temperature below absolute zero: " + celsius);
            }
            // note: no explicit "this.celsius = celsius;" needed here -- see compact form details
            // in "Compact canonical constructor"; the assignment still happens automatically.
        }
    }

    public static void main(String[] args) {
        Temperature valid = new Temperature(21.5);
        System.out.println("valid: " + valid);
        try {
            Temperature invalid = new Temperature(-300);
        } catch (IllegalArgumentException e) {
            System.out.println("caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java RecordCanonicalValidation.java` (JDK 17+).

Expected output:
```
valid: RecordCanonicalValidation$Temperature[celsius=21.5]
caught: temperature below absolute zero: -300.0
```

The real-world concern added: this is the compact canonical constructor form (parameter list omitted, since it must exactly match the header) — it lets you insert validation logic that runs before the automatic field assignment, rejecting invalid states (a temperature below absolute zero) at construction time, which is exactly the point of allowing an explicit canonical constructor at all: records are otherwise pure, unchecked data carriers, and this is the sanctioned place to enforce invariants.

### Level 3 — Advanced

```java
import java.util.Objects;

public class RecordCanonicalNormalization {
    record EmailAddress(String value) {
        EmailAddress {
            Objects.requireNonNull(value, "email cannot be null");
            value = value.trim().toLowerCase(); // NORMALIZE before assignment -- reassigning the parameter
            if (!value.contains("@")) {
                throw new IllegalArgumentException("invalid email: " + value);
            }
        }
    }

    public static void main(String[] args) {
        EmailAddress e1 = new EmailAddress("  Ada@Example.COM  ");
        EmailAddress e2 = new EmailAddress("ada@example.com");
        System.out.println("e1: " + e1);
        System.out.println("e1.equals(e2): " + e1.equals(e2)); // normalization makes these equal
        try {
            new EmailAddress("not-an-email");
        } catch (IllegalArgumentException ex) {
            System.out.println("caught: " + ex.getMessage());
        }
    }
}
```

**How to run:** `java RecordCanonicalNormalization.java` (JDK 17+).

Expected output:
```
e1: RecordCanonicalNormalization$EmailAddress[value=ada@example.com]
e1.equals(e2): true
caught: invalid email: not-an-email
```

The production-flavored hard case: the compact constructor's parameter, `value`, is reassigned (`value = value.trim().toLowerCase()`) before the implicit field assignment occurs — this is a deliberate, sanctioned technique for *normalizing* input, not just validating it, so that `new EmailAddress("  Ada@Example.COM  ")` and `new EmailAddress("ada@example.com")` end up with genuinely identical internal state, which is exactly why they compare equal via the record's auto-generated `equals()` afterward, despite differing wildly in their original constructor arguments.

## 6. Walkthrough

Tracing `new EmailAddress("  Ada@Example.COM  ")` end to end from `RecordCanonicalNormalization.main`:

1. The constructor call `new EmailAddress("  Ada@Example.COM  ")` invokes the record's canonical constructor — because it was written in compact form (`EmailAddress { ... }`, with no explicit parameter list), the compiler has already inserted the implicit parameter `String value` matching the header's single component, so this compact block executes with `value` bound to the raw argument, `"  Ada@Example.COM  "`.
2. `Objects.requireNonNull(value, "email cannot be null")` runs first, checking `value` isn't null (it isn't here) — this check runs *before* any assignment to the record's actual internal field, since compact constructors execute their body first and only perform the implicit field assignment afterward, automatically, once the body completes normally.
3. `value = value.trim().toLowerCase()` reassigns the local parameter `value` — trimming leading/trailing whitespace and lowercasing the result — producing `"ada@example.com"`; this reassignment only affects the *parameter*, and it's precisely because compact constructors assign the (possibly-reassigned) parameter to the field only *after* the body runs that this normalization technique works at all.
4. The `if (!value.contains("@"))` check runs against the now-normalized value, `"ada@example.com"`, which does contain `@`, so no exception is thrown.
5. With the compact constructor's body having completed normally, the compiler's implicit field assignment now runs: the record's actual internal field, `value`, is set to the *current* value of the local parameter — `"ada@example.com"`, the normalized form, not the original raw argument.
6. `new EmailAddress("ada@example.com")` (constructing `e2`) runs through the identical process: `requireNonNull` passes, the normalization step leaves the value unchanged (it's already trimmed and lowercase), and the `@` check passes, so `e2`'s internal field is also set to `"ada@example.com"` — since the record's auto-generated `equals()` compares all components' field values directly, and both `e1` and `e2`'s `value` fields now hold the identical string `"ada@example.com"`, `e1.equals(e2)` correctly evaluates to `true`, despite the two constructor calls having received visibly different raw string arguments.

## 7. Gotchas & takeaways

> **Gotcha:** a compact canonical constructor's parameter reassignment (`value = value.trim()...`) only works because it happens *before* the implicit field assignment — this is a specific, deliberate language rule unique to compact constructors; writing an *explicit-parameter-list* canonical constructor instead (`EmailAddress(String value) { this.value = value.trim()...; }`) requires you to write the field assignment yourself explicitly, and forgetting to include it (or getting a component's assignment wrong or out of order) is a real, if less common, source of bugs in that form.

- A record's header declares its components, and the compiler automatically generates a private final field, a same-named accessor (`x()`, not `getX()`), and a canonical constructor for each — even if you never write the constructor explicitly.
- An explicit canonical constructor written in *compact* form (no parameter list, just the record name and a body) is the idiomatic way to add validation or normalization logic that runs before the automatic field assignment.
- Reassigning a compact constructor's parameter (as in a normalization step) changes what value ultimately gets assigned to the field, since the implicit field assignment happens *after* the compact body runs.
- Records automatically get correct `equals()`, `hashCode()`, and `toString()` based on all components' field values — two instances are equal if and only if all their components' values are equal after any constructor-time normalization.
- Records are ideal for simple, transparent, immutable data aggregates, but cannot extend another class (they implicitly extend `java.lang.Record`) and are a poor fit when internal representation needs to be hidden from the public API.
- See [compact canonical constructor](0955-compact-canonical-constructor.md) for a deeper look at this specific constructor form's rules, and [records & immutability](0958-records-immutability.md) for what "immutable" precisely does and doesn't guarantee for a record's components.
