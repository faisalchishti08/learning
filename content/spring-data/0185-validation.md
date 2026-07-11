---
card: spring-data
gi: 185
slug: validation
title: "Validation"
---

## 1. What it is

Spring Data REST integrates Bean Validation (`jakarta.validation` — `@NotNull`, `@Size`, `@Email`, and friends) directly into the create/update lifecycle: validation runs automatically before a save, and constraint violations get translated into an HTTP `400 Bad Request` with a body describing exactly which fields failed and why — no manual validation code required in most cases.

```java
@Entity
class Customer {
    @Id String id;
    @NotBlank String name;
    @Email String email;
}
// POST /customers { "name": "", "email": "not-an-email" }
// -> 400 Bad Request, body describing both violations
```

## 2. Why & when

The previous card's `@HandleBeforeCreate` events are one way to validate, but Bean Validation annotations are usually the better default: they're declarative, colocated with the field they constrain, reusable outside Spring Data REST (the same annotations work with `@Valid` in any Spring MVC controller), and Spring Data REST wires them up automatically with no extra handler class needed.

Reach for Bean Validation annotations when:

- The rule is a straightforward per-field constraint — required, length bounds, format (email, pattern), numeric range — the exact case Bean Validation annotations are built for.
- You want the same validation rules to apply consistently whether the entity is being saved through a generated REST endpoint, a custom controller, or directly via the repository in application code.
- The validation error response should be structured and consistent across the whole API, rather than a custom message format per hand-written check.

Reach for `@HandleBeforeCreate` (previous card) instead when the rule needs to consult other data — a uniqueness check against existing records, a cross-field rule Bean Validation's annotations can't express cleanly.

## 3. Core concept

```
 @Entity
 class Customer {
     @NotBlank String name;
     @Email String email;
     @Size(min = 10, max = 15) String phone;
 }

 POST /customers  { "name": "", "email": "bad", "phone": "123" }

 1. Bean Validation runs automatically, BEFORE the save
 2. Three constraints violated: @NotBlank, @Email, @Size
 3. Save is REJECTED -- entity never persisted
 4. Response: 400 Bad Request, body listing all three violations by field
```

Validation runs as an automatic pre-save gate — every violated constraint is collected and reported together, not just the first one encountered.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An incoming entity is checked against its Bean Validation constraints before the save is allowed to proceed">
  <rect x="20" y="45" width="160" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">incoming entity</text>

  <line x1="180" y1="67" x2="240" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a18)"/>

  <rect x="250" y="45" width="160" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">check @NotBlank,</text>
  <text x="330" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@Email, @Size...</text>

  <line x1="330" y1="90" x2="240" y2="120" stroke="#79c0ff" stroke-width="1.3" marker-end="url(#a18)"/>
  <line x1="330" y1="90" x2="420" y2="120" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a18)"/>

  <rect x="140" y="120" width="200" height="30" rx="6" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="240" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">violations -&gt; 400</text>

  <rect x="380" y="120" width="200" height="30" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">valid -&gt; saved, 201</text>

  <defs><marker id="a18" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Validation is a gate checked before the save is allowed to happen at all.

## 5. Runnable example

The scenario: validating incoming customer data, evolving from hand-written per-field checks, to declarative constraint annotations checked automatically before save, to a validator that collects *all* violations at once (rather than stopping at the first) and shapes them into a structured error response — matching what Spring Data REST actually returns.

### Level 1 — Basic

Show the hand-written baseline: manual field checks, stopping at the first failure.

```java
public class ValidationLevel1 {
    public static void main(String[] args) {
        Customer invalid = new Customer("c1", "", "not-an-email");
        try {
            validate(invalid);
            System.out.println("Valid, saving...");
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage()); // only reports the FIRST failure
        }
    }

    static void validate(Customer c) {
        if (c.name == null || c.name.isBlank()) throw new IllegalArgumentException("name must not be blank");
        if (!c.email.contains("@")) throw new IllegalArgumentException("email must be a valid email address");
    }
}

class Customer {
    String id, name, email;
    Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
}
```

How to run: `java ValidationLevel1.java`

`validate` throws on the *first* failed check — the caller sees only `"name must not be blank"` and has no idea the email is also invalid until they fix the name and resubmit, discovering the second problem only on a second round trip.

### Level 2 — Intermediate

Add declarative-style constraint annotations checked by a small validation engine that collects every violation, not just the first.

```java
import java.util.*;
import java.lang.annotation.*;
import java.lang.reflect.*;

public class ValidationLevel2 {
    public static void main(String[] args) {
        Customer invalid = new Customer("c1", "", "not-an-email");
        List<String> violations = validate(invalid);
        if (violations.isEmpty()) {
            System.out.println("Valid, saving...");
        } else {
            System.out.println("400 Bad Request: " + violations); // ALL violations reported together
        }
    }

    @Retention(RetentionPolicy.RUNTIME) @interface NotBlank { String message() default "must not be blank"; }
    @Retention(RetentionPolicy.RUNTIME) @interface Email { String message() default "must be a valid email address"; }

    static List<String> validate(Customer c) {
        List<String> violations = new ArrayList<>();
        for (Field field : Customer.class.getDeclaredFields()) {
            try {
                field.setAccessible(true);
                Object value = field.get(c);
                if (field.isAnnotationPresent(NotBlank.class) && (value == null || value.toString().isBlank())) {
                    violations.add(field.getName() + ": " + field.getAnnotation(NotBlank.class).message());
                }
                if (field.isAnnotationPresent(Email.class) && value != null && !value.toString().contains("@")) {
                    violations.add(field.getName() + ": " + field.getAnnotation(Email.class).message());
                }
            } catch (IllegalAccessException ignored) {}
        }
        return violations;
    }
}

class Customer {
    String id;
    @ValidationLevel2.NotBlank String name;
    @ValidationLevel2.Email String email;
    Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
}
```

How to run: `java ValidationLevel2.java`

`validate` now checks *every* annotated field and collects *all* violations before returning, instead of stopping at the first — the caller sees both problems (`name`, `email`) in one pass, matching Bean Validation's actual behavior of reporting the complete constraint violation set per request.

### Level 3 — Advanced

Shape the collected violations into a structured error response — the format a real Spring Data REST `400` body actually takes — and add a `Size` constraint to show a third, independent violation type composing with the first two.

```java
import java.util.*;
import java.lang.annotation.*;
import java.lang.reflect.*;

public class ValidationLevel3 {
    public static void main(String[] args) {
        Customer invalid = new Customer("c1", "", "not-an-email", "12");
        ValidationResult result = validate(invalid);

        if (result.isValid()) {
            System.out.println("201 Created");
        } else {
            System.out.println("POST /customers -> 400 Bad Request");
            System.out.println(result.toErrorJson());
        }
    }

    @Retention(RetentionPolicy.RUNTIME) @interface NotBlank { String message() default "must not be blank"; }
    @Retention(RetentionPolicy.RUNTIME) @interface Email { String message() default "must be a valid email address"; }
    @Retention(RetentionPolicy.RUNTIME) @interface Size { int min(); String message() default "too short"; }

    static ValidationResult validate(Customer c) {
        List<Violation> violations = new ArrayList<>();
        for (Field field : Customer.class.getDeclaredFields()) {
            try {
                field.setAccessible(true);
                Object value = field.get(c);
                if (field.isAnnotationPresent(NotBlank.class) && (value == null || value.toString().isBlank())) {
                    violations.add(new Violation(field.getName(), field.getAnnotation(NotBlank.class).message()));
                }
                if (field.isAnnotationPresent(Email.class) && value != null && !value.toString().contains("@")) {
                    violations.add(new Violation(field.getName(), field.getAnnotation(Email.class).message()));
                }
                if (field.isAnnotationPresent(Size.class) && value != null
                        && value.toString().length() < field.getAnnotation(Size.class).min()) {
                    violations.add(new Violation(field.getName(), field.getAnnotation(Size.class).message()));
                }
            } catch (IllegalAccessException ignored) {}
        }
        return new ValidationResult(violations);
    }
}

class Violation {
    String field, message;
    Violation(String field, String message) { this.field = field; this.message = message; }
}

class ValidationResult {
    List<Violation> violations;
    ValidationResult(List<Violation> violations) { this.violations = violations; }
    boolean isValid() { return violations.isEmpty(); }
    String toErrorJson() {
        StringBuilder sb = new StringBuilder("{ \"errors\": [ ");
        for (int i = 0; i < violations.size(); i++) {
            Violation v = violations.get(i);
            sb.append("{ \"field\": \"").append(v.field).append("\", \"message\": \"").append(v.message).append("\" }");
            if (i < violations.size() - 1) sb.append(", ");
        }
        return sb.append(" ] }").toString();
    }
}

class Customer {
    String id;
    @ValidationLevel3.NotBlank String name;
    @ValidationLevel3.Email String email;
    @ValidationLevel3.Size(min = 10) String phone;
    Customer(String id, String name, String email, String phone) { this.id = id; this.name = name; this.email = email; this.phone = phone; }
}
```

How to run: `java ValidationLevel3.java`

`toErrorJson` shapes the collected violations into a structured, per-field error list — the same general shape a real Spring Data REST `400 Bad Request` body takes, letting a client programmatically map each violation back to the specific form field that caused it, rather than parsing a single free-text error message.

## 6. Walkthrough

Execution starts in `main` for Level 3. An invalid `Customer` is built with a blank `name`, a malformed `email`, and a too-short `phone`. `validate(invalid)` reflects over every field, checking each against whichever constraint annotations are present.

Three violations accumulate: `name` fails `@NotBlank`, `email` fails `@Email`, `phone` fails `@Size(min = 10)`. `result.isValid()` returns `false` since the list isn't empty, and `toErrorJson()` builds the structured response:

```
POST /customers -> 400 Bad Request
{ "errors": [ { "field": "name", "message": "must not be blank" }, { "field": "email", "message": "must be a valid email address" }, { "field": "phone", "message": "too short" } ] }
```

In a real Spring Data REST application, this entire validation pass happens automatically before the save is attempted — the incoming JSON request body is deserialized into a `Customer` instance, Bean Validation runs against its annotated fields, and if any constraint fails, a `RepositoryConstraintViolationException` is thrown and translated into exactly this kind of structured `400` response, with the entity never reaching the repository's `save()` call at all.

## 7. Gotchas & takeaways

> Gotcha: Bean Validation only fires automatically on the operations Spring Data REST's validation is wired into (create and update through the generated endpoints) — a custom `@RepositoryRestController` endpoint (the earlier card) that calls `repository.save()` directly does *not* automatically get Bean Validation applied unless the controller explicitly triggers it (e.g. via `@Valid` on its own method parameter).

> Gotcha: constraints that need to check against *other* existing data (uniqueness of an email across all customers, say) can't be expressed with a plain per-field Bean Validation annotation — those need a custom `ConstraintValidator` with injected dependencies, or fall back to the `@HandleBeforeCreate` event-based approach from the previous card.

- Bean Validation annotations (`@NotBlank`, `@Email`, `@Size`, and others) are checked automatically before create/update operations in Spring Data REST, with no extra handler code required for straightforward per-field constraints.
- All violations are collected and reported together in one `400 Bad Request` response, not just the first one encountered — saving the client from a slow, one-violation-at-a-time discovery loop.
- The same annotations work consistently across Spring Data REST, Spring MVC's `@Valid`, and direct application code, unlike ad hoc hand-written validation methods.
- Cross-record or cross-field rules that a simple annotation can't express fall back to a custom `ConstraintValidator` or the `@HandleBeforeCreate` event approach from the previous card.
