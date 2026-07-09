---
card: java
gi: 631
slug: predicate-not
title: Predicate.not()
---

## 1. What it is

`Predicate.not(Predicate<T>)` is a Java 11 static method that returns a **negated predicate** — a predicate that returns `true` when the original predicate would return `false`, and vice versa. It is equivalent to `predicate.negate()` but works as a **method reference target**, which `negate()` does not. The killer feature is that you can write `stream.filter(Predicate.not(String::isBlank))` to filter out blank strings — a fluent, readable negation of a method reference that was impossible before Java 11. Previously you had to write `stream.filter(s -> !s.isBlank())` or `stream.filter(((Predicate<String>) String::isBlank).negate())` — both verbose and clunky.

## 2. Why & when

The classic frustration: you have a method reference like `String::isBlank` and you want the opposite — "everything that is NOT blank." Before Java 11, you couldn't negate a method reference directly. You had to fall back to a lambda (`s -> !s.isBlank()`) or an ugly cast-and-negate (`((Predicate<String>) String::isBlank).negate()`). `Predicate.not()` solves this elegantly. Use it whenever you need the negation of a predicate in a stream pipeline, `Optional.filter()`, or any `Predicate`-accepting API — especially where a method reference would be the cleanest expression but you need the opposite condition.

## 3. Core concept

```java
// Before Java 11: cannot negate a method reference
strings.stream()
    .filter(s -> !s.isBlank())                          // lambda — works but verbose
    // .filter(String::isBlank.negate())                // does NOT compile
    // .filter(((Predicate<String>) String::isBlank).negate())  // works but hideous

// Java 11+: clean negation of any predicate, including method references
strings.stream()
    .filter(Predicate.not(String::isBlank))             // reads as "not isBlank"

// Works with any Predicate:
Predicate<String> isLong = s -> s.length() > 10;
Predicate<String> isShort = Predicate.not(isLong);

// Works with Optional.filter:
Optional<String> opt = Optional.of("hello");
opt.filter(Predicate.not(String::isBlank));             // present if not blank
```

`Predicate.not()` wraps the given predicate and returns its logical negation. It is essentially `predicate.negate()` in static-method form, enabling method-reference usage.

## 4. Diagram

<svg viewBox="0 0 560 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Predicate.not() negates a predicate, enabling method-reference negation">
  <rect x="10" y="10" width="540" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="170" height="45" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="105" y="44" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">s -> !s.isBlank()</text>
  <text x="105" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Pre-Java 11 (verbose lambda)</text>

  <text x="205" y="50" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="225" y="20" width="220" height="55" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="335" y="40" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">Predicate.not(String::isBlank)</text>
  <text x="335" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Java 11+ (method reference, reads as "not blank")</text>

  <text x="20" y="95" fill="#8b949e" font-size="9" font-family="sans-serif">Predicate.not(p) ≡ p.negate() — same behaviour, static form enables method-reference usage</text>
  <text x="20" y="113" fill="#3fb950" font-size="9" font-family="sans-serif">Common uses: filter(Predicate.not(String::isBlank)), filter(Predicate.not(List::isEmpty))</text>
</svg>

`Predicate.not()` transforms `String::isBlank` (a method reference) into its negation — cleanly, without casting or wrapping in a lambda.

## 5. Runnable example

Scenario: processing a list of user-submitted strings — filtering out blanks, validating inputs, and composing complex conditions — starting with basic negation, extending to chained predicates, and finally handling edge cases with `null` and stream operations.

### Level 1 — Basic

```java
// File: PredicateNotDemo.java
import java.util.*;
import java.util.function.*;

public class PredicateNotDemo {
    public static void main(String[] args) {
        // Mixed user input: some valid, some blank, some whitespace
        List<String> inputs = List.of("Alice", "", "  ", "Bob", "\t\n", "Charlie");

        // Before Java 11: lambda
        List<String> valid1 = inputs.stream()
            .filter(s -> !s.isBlank())
            .toList();
        System.out.println("Old way (lambda):     " + valid1);

        // Java 11+: Predicate.not with method reference
        List<String> valid2 = inputs.stream()
            .filter(Predicate.not(String::isBlank))
            .toList();
        System.out.println("New way (not blank):  " + valid2);

        // Also works with any method reference
        List<String> nonEmpty = inputs.stream()
            .filter(Predicate.not(String::isEmpty))
            .toList();
        System.out.println("Not empty:            " + nonEmpty);
    }
}
```

**How to run:** `java PredicateNotDemo.java`

Expected output:
```
Old way (lambda):     [Alice, Bob, Charlie]
New way (not blank):  [Alice, Bob, Charlie]
Not empty:            [Alice,   , Bob, 	
, Charlie]
```

The simplest usage: `Predicate.not(String::isBlank)` replaces the lambda `s -> !s.isBlank()` and reads as natural English: "filter not blank." The difference from `isEmpty()` is visible in the output — whitespace-only strings like `"  "` are not empty but are blank.

### Level 2 — Intermediate

```java
// File: InputValidator.java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class InputValidator {
    public static void main(String[] args) {
        List<String> submissions = List.of(
            "alice@example.com",
            "",
            "  ",
            "bob@example",
            "charlie@example.com",
            "not-an-email",
            null  // careful!
        );

        System.out.println("=== Email Validation Pipeline ===\n");

        // Step 1: Remove nulls
        // Step 2: Remove blanks
        // Step 3: Validate email format

        Predicate<String> notNull = Objects::nonNull;
        Predicate<String> nonBlank = Predicate.not(String::isBlank);
        Predicate<String> validEmail = s -> s.contains("@") && s.contains(".");

        // Combine: not null AND not blank AND valid email
        Predicate<String> isValid = notNull
            .and(nonBlank)
            .and(validEmail);

        List<String> valid = submissions.stream()
            .filter(isValid)
            .toList();

        System.out.println("Valid emails: " + valid);

        // Show rejected
        List<String> rejected = submissions.stream()
            .filter(Predicate.not(isValid))
            .toList();
        System.out.println("Rejected:     " + rejected);

        System.out.println("\n=== Negated combined predicates ===\n");

        // What was rejected because it was blank (including null as blank-like)?
        Predicate<String> isBlankOrNull = s -> s == null || s.isBlank();
        List<String> blankOnes = submissions.stream()
            .filter(Objects::nonNull)
            .filter(Predicate.not(nonBlank))  // exactly: was blank
            .toList();
        System.out.println("Blank ones: " + blankOnes);
    }
}
```

**How to run:** `java InputValidator.java`

Expected output:
```
=== Email Validation Pipeline ===

Valid emails: [alice@example.com, charlie@example.com]
Rejected:     [,   , bob@example, not-an-email, null]

=== Negated combined predicates ===

Blank ones: [,   ]
```

The real-world concern: validation pipelines. `Predicate.not()` can negate complex composed predicates — `Predicate.not(isValid)` gives you "everything that didn't pass validation." Combined with `and()` and `or()`, you can build sophisticated filtering logic without nested `if` statements.

### Level 3 — Advanced

```java
// File: PredicateNotAdvanced.java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class PredicateNotAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Predicate.not vs negate() ===\n");

        Predicate<String> isBlank = String::isBlank;

        // negate() — cannot be used as a method reference
        Predicate<String> notBlank1 = isBlank.negate();

        // Predicate.not() — works everywhere, including as method reference
        Predicate<String> notBlank2 = Predicate.not(String::isBlank);

        // Both produce the same results
        System.out.println("notBlank1.test(\"\"):   " + notBlank1.test(""));
        System.out.println("notBlank2.test(\"\"):   " + notBlank2.test(""));
        System.out.println("notBlank1.test(\"hi\"): " + notBlank1.test("hi"));
        System.out.println("notBlank2.test(\"hi\"): " + notBlank2.test("hi"));

        System.out.println("\n=== Real-world: removing empty collections ===\n");

        // List of lists — keep only non-empty ones
        List<List<String>> data = List.of(
            List.of("a", "b"),
            List.of(),               // empty
            List.of("c"),
            Collections.emptyList(), // empty
            List.of("d", "e", "f")
        );

        // Clean: filter out empty lists
        List<List<String>> nonEmpty = data.stream()
            .filter(Predicate.not(List::isEmpty))
            .toList();

        System.out.println("Non-empty lists: " + nonEmpty.size());
        nonEmpty.forEach(list -> System.out.println("  " + list));

        System.out.println("\n=== Predicate.not with Map filtering ===\n");

        Map<String, Integer> scores = new LinkedHashMap<>();
        scores.put("Alice", 95);
        scores.put("Bob", 0);
        scores.put("Charlie", 87);
        scores.put("Diana", 0);
        scores.put("Eve", 73);

        // Remove entries with zero scores
        scores.entrySet().removeIf(e -> e.getValue() == 0);
        System.out.println("After removing zeros: " + scores);

        // Same with Predicate.not
        Map<String, Integer> scores2 = new LinkedHashMap<>();
        scores2.put("Alice", 95);
        scores2.put("Bob", 0);
        scores2.put("Charlie", 87);
        scores2.put("Diana", 0);

        scores2.entrySet().removeIf(
            entry -> Predicate.not((Predicate<Map.Entry<String, Integer>>) e -> e.getValue() > 0).test(entry)
        );
        // ^ more verbose than lambda in this case — use judgment!

        System.out.println("\n=== Static import for readability ===\n");

        // With static import: import static java.util.function.Predicate.not;
        // Then: filter(not(String::isBlank))
        System.out.println("Static import makes it even cleaner:");
        System.out.println("  import static java.util.function.Predicate.not;");
        System.out.println("  list.stream().filter(not(String::isBlank))");
    }
}
```

**How to run:** `java PredicateNotAdvanced.java`

Expected output:
```
=== Predicate.not vs negate() ===

notBlank1.test(""):   false
notBlank2.test(""):   false
notBlank1.test("hi"): true
notBlank2.test("hi"): true

=== Real-world: removing empty collections ===

Non-empty lists: 3
  [a, b]
  [c]
  [d, e, f]

=== Predicate.not with Map filtering ===

After removing zeros: {Alice=95, Charlie=87, Eve=73}

=== Static import for readability ===

Static import makes it even cleaner:
  import static java.util.function.Predicate.not;
  list.stream().filter(not(String::isBlank))
```

The production-flavoured hard cases: (1) `Predicate.not()` vs `negate()` — `negate()` is an instance method (can't be method-referenced), while `not()` is a static method that takes the predicate as an argument. They produce identical results. (2) `Predicate.not(List::isEmpty)` works for any method reference on any type, not just `String`. (3) With static import (`import static java.util.function.Predicate.not`), the call site becomes even more concise: `filter(not(String::isBlank))`. (4) For simple cases like `e.getValue() == 0`, a lambda is still clearer — `Predicate.not()` is most valuable when negating a method reference.

## 6. Walkthrough

Tracing `inputs.stream().filter(Predicate.not(String::isBlank)).toList()`:

1. `inputs` is a `List<String>` containing `["Alice", "", "  ", "Bob"]`.

2. `.stream()` creates a sequential `Stream<String>` over the list.

3. `.filter(Predicate.not(String::isBlank))`:
   - `String::isBlank` is a method reference bound to `Predicate<String>` (the `String::isBlank` signature `() -> boolean` matches `Predicate.test(String)` — the string is the receiver, not the argument). This creates a predicate `p` where `p.test(s)` calls `s.isBlank()`.
   - `Predicate.not(p)` wraps `p` and returns a new predicate `notP` where `notP.test(s)` calls `!p.test(s)` — effectively `!s.isBlank()`.
   - The filter passes only elements where `notP.test(element)` returns `true` — i.e., strings that are NOT blank.

4. The stream processes each element:
   - `"Alice"` → `isBlank()` returns `false`, `not` returns `true` → KEPT.
   - `""` → `isBlank()` returns `true`, `not` returns `false` → DISCARDED.
   - `"  "` → `isBlank()` returns `true`, `not` returns `false` → DISCARDED.
   - `"Bob"` → `isBlank()` returns `false`, `not` returns `true` → KEPT.

5. `.toList()` collects the surviving elements into a new `List`: `["Alice", "Bob"]`.

## 7. Gotchas & takeaways

> `Predicate.not()` with a method reference like `String::isBlank` works because the method reference is adapted to a `Predicate<String>`. But `Predicate.not(String::isEmpty)` with a `List<String>` stream will NOT compile — `String::isEmpty` tests the string, not the list. The method reference must match the stream element type. For `List<String>`, use `Predicate.not(List::isEmpty)`.

- `Predicate.not(p)` is semantically identical to `p.negate()` — the only difference is that `not()` is a static method, enabling method-reference usage that `negate()` cannot support.
- Use `Predicate.not()` when you want to negate a method reference. Use `p.negate()` when you already have a `Predicate` variable and want to negate it. Use a plain lambda (`s -> !condition`) when the condition is simple and `Predicate.not()` would add ceremony.
- With static import (`import static java.util.function.Predicate.not;`), the call reads as `filter(not(String::isBlank))` — very close to natural English.
- `Predicate.not()` can wrap any `Predicate`, including composed ones (`Predicate.not(p.and(q))`), but at that point readability may suffer — consider extracting a named predicate variable.
- `Predicate.not()` does NOT handle `null` specially. If the underlying predicate throws on `null` input (many method references do), `Predicate.not()` does too. Always filter out `null` first if your data may contain it.
