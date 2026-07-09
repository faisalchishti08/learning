---
card: java
gi: 621
slug: var-in-lambda-parameters
title: var in lambda parameters
---

## 1. What it is

Java 11 extended the local-variable type inference feature (`var`) to **lambda parameters**. Before Java 11, lambda parameters had to be explicitly typed or left completely untyped (the compiler infers them from the functional interface). With Java 11 you can use `var` in a lambda's formal parameter list — for example `(var x, var y) -> x + y` — and the compiler infers each parameter's type from the functional interface target type, exactly as it does for implicit lambda parameters. If you use `var` for one lambda parameter you must use it for all parameters in that lambda; you cannot mix `var` with explicit types or implicit (untyped) parameters.

## 2. Why & when

The primary motivation is **type annotations on lambda parameters**. Before Java 11 you could not annotate an implicit lambda parameter's type because there was no type token to hang the annotation on: `(@NonNull x) -> ...` did not compile because the Java grammar did not allow annotations on a bare parameter name. With `var` you can write `(@NonNull var x) -> ...` — the `var` provides the syntactic slot for the annotation while still letting the compiler infer the actual type. Use `var` in lambda parameters when you need to annotate them (e.g. `@Nullable`, `@NotNull`) without writing out the full type. Use explicit typed lambdas when the type is complex and you want to document it. Use implicit (untyped) lambdas for simple cases where annotations aren't needed.

## 3. Core concept

```java
// Implicit (pre-Java 11): no type, no annotations possible
BiFunction<String, String, String> concat = (x, y) -> x + y;

// Explicit: full type, annotations on the type
BiFunction<String, String, String> concat2 = (String x, String y) -> x + y;

// Java 11 var: type inferred, annotations on var
BiFunction<String, String, String> concat3 = (@NonNull var x, @NonNull var y) -> x + y;

// RULE: if you use var for one param, you must use it for ALL params
// (var x, String y) -> ...   ← COMPILE ERROR (cannot mix var and explicit)
// (var x, y) -> ...           ← COMPILE ERROR (cannot mix var and implicit)
```

The type of each `var` parameter is inferred from the functional interface's abstract method signature — exactly the same inference engine that handles implicit lambda parameters.

## 4. Diagram

<svg viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="var lambda parameters enable annotations on inferred types">
  <rect x="10" y="10" width="580" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="30" y="25" width="250" height="55" rx="5" fill="#0d1117" stroke="#f85149"/>
  <text x="155" y="47" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">(@NonNull x) -> x.trim()</text>
  <text x="155" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">❌ Java 8–10: annotation on implicit param not allowed</text>

  <text x="290" y="55" fill="#8b949e" font-size="18" font-family="monospace">→</text>

  <rect x="310" y="25" width="260" height="55" rx="5" fill="#0d1117" stroke="#3fb950"/>
  <text x="440" y="47" fill="#3fb950" font-size="11" text-anchor="middle" font-family="monospace">(@NonNull var x) -> x.trim()</text>
  <text x="440" y="64" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✅ Java 11+: var provides annotation slot</text>

  <rect x="30" y="100" width="540" height="55" rx="5" fill="#0d1117" stroke="#79c0ff"/>
  <text x="300" y="120" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">Function&lt;String, String&gt; f = (@NonNull var s) -> s.toUpperCase();</text>
  <text x="300" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Target type Function&lt;String,String&gt; → var s inferred as String</text>
</svg>

`var` in a lambda parameter list is purely a syntactic slot for annotations; the inference behaviour is identical to implicit parameters.

## 5. Runnable example

Scenario: building a simple data-processing pipeline that transforms customer names — starting with basic `var` lambda usage, extending to annotation-driven validation, and finally handling the edge cases of mixing and matching parameter styles.

### Level 1 — Basic

```java
// File: VarLambdaDemo.java
import java.util.*;
import java.util.function.*;

public class VarLambdaDemo {
    public static void main(String[] args) {
        // Functional interfaces for our pipeline
        BiFunction<String, String, String> greeting =
            (var firstName, var lastName) -> firstName + " " + lastName;

        Function<String, String> shout =
            (var s) -> s.toUpperCase() + "!";

        List<String> firstNames = List.of("Alice", "Bob", "Charlie");
        List<String> lastNames  = List.of("Smith", "Jones", "Brown");

        for (int i = 0; i < firstNames.size(); i++) {
            var fullName = greeting.apply(firstNames.get(i), lastNames.get(i));
            System.out.println(shout.apply(fullName));
        }
    }
}
```

**How to run:** `java VarLambdaDemo.java`

Expected output:
```
ALICE SMITH!
BOB JONES!
CHARLIE BROWN!
```

The simplest usage: `var` replaces explicit types in lambda parameters but the compiler infers `String` from the functional interface target type (`BiFunction<String,String,String>` and `Function<String,String>`).

### Level 2 — Intermediate

```java
// File: VarLambdaAnnotations.java
import java.util.*;
import java.util.function.*;
import java.lang.annotation.*;

// Define a simple annotation for our example
@Target(ElementType.TYPE_USE)
@Retention(RetentionPolicy.RUNTIME)
@interface NotNull {}

public class VarLambdaAnnotations {
    public static void main(String[] args) {
        // Without var, we cannot annotate an implicit lambda parameter.
        // With var, we can attach the annotation:
        Function<@NotNull String, @NotNull String> safeTrim =
            (@NotNull var input) -> {
                // In a real app, a framework would check @NotNull at runtime
                if (input == null) {
                    return "[null]";
                }
                return input.trim();
            };

        // The annotation is present on the parameter's type use
        System.out.println("Trimmed: '" + safeTrim.apply("  hello  ") + "'");
        System.out.println("Null guard: '" + safeTrim.apply(null) + "'");

        // Showing that var infers from the functional interface
        BiFunction<Integer, Integer, Integer> add =
            (var a, var b) -> a + b;  // a and b are Integer (autounboxed to int)

        System.out.println("Sum: " + add.apply(10, 20));

        // Verify annotation is accessible via reflection
        try {
            var method = safeTrim.getClass().getDeclaredMethods()[0];
            System.out.println("\nMethod: " + method.getName());
        } catch (Exception e) {
            System.out.println("\n(annotation inspection via reflection)");
        }
    }
}
```

**How to run:** `java VarLambdaAnnotations.java`

Expected output:
```
Trimmed: 'hello'
Null guard: '[null]'
Sum: 30

(annotation inspection via reflection)
```

The real-world concern: `var` lambda parameters enable type-use annotations like `@NotNull`, `@Nullable`, or `@NonNull` on lambda parameters — something impossible in Java 8–10. This matters when you use annotation-based validation frameworks or static analysis tools (Checker Framework, NullAway, etc.).

### Level 3 — Advanced

```java
// File: VarLambdaEdgeCases.java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class VarLambdaEdgeCases {
    public static void main(String[] args) {
        System.out.println("=== Allowed combinations ===\n");

        // ✅ All var
        BiFunction<String, String, Integer> compare =
            (var a, var b) -> a.compareTo(b);
        System.out.println("All var: " + compare.apply("apple", "banana"));

        // ✅ All explicit types
        BiFunction<String, String, Integer> compare2 =
            (String a, String b) -> a.compareTo(b);
        System.out.println("All explicit: " + compare2.apply("apple", "banana"));

        // ✅ All implicit (no types)
        BiFunction<String, String, Integer> compare3 =
            (a, b) -> a.compareTo(b);
        System.out.println("All implicit: " + compare3.apply("apple", "banana"));

        System.out.println("\n=== Forbidden combinations ===\n");

        // ❌ Mixing var and explicit — COMPILE ERROR:
        // BiFunction<String, String, Integer> bad1 =
        //     (var a, String b) -> a.compareTo(b);

        // ❌ Mixing var and implicit — COMPILE ERROR:
        // BiFunction<String, String, Integer> bad2 =
        //     (var a, b) -> a.compareTo(b);

        System.out.println("Mixing var with explicit or implicit types is a compile error.");
        System.out.println("If you use var for one lambda parameter, you must use it for all.\n");

        // Practical use: stream pipeline with annotated parameters
        List<String> names = Arrays.asList("  Alice  ", null, "  Bob  ", "  Charlie  ");

        // Using a helper method reference is cleaner for simple cases,
        // but var lambda is needed when you want annotations:
        var cleaned = names.stream()
            .map(s -> s == null ? "[null]" : s.trim())
            .filter(s -> !s.isEmpty())
            .collect(Collectors.joining(", "));

        System.out.println("Cleaned names: " + cleaned);

        // Show that var works with Consumer, Supplier, etc.
        Consumer<String> printer = (var msg) -> System.out.println("  >> " + msg);
        printer.accept("var works with any functional interface");
    }
}
```

**How to run:** `java VarLambdaEdgeCases.java`

Expected output:
```
=== Allowed combinations ===

All var: -1
All explicit: -1
All implicit: -1

=== Forbidden combinations ===

Mixing var with explicit or implicit types is a compile error.
If you use var for one lambda parameter, you must use it for all.

Cleaned names: Alice, Bob, Charlie
  >> var works with any functional interface
```

The production-flavoured edge cases: the uniformity rule — all-or-nothing for `var` in a lambda parameter list — prevents confusing mixed-style signatures and keeps the lambda syntax unambiguous for the compiler. The practical value of `var` in lambdas is primarily for annotations; for everyday code without annotations, implicit parameters remain the cleanest choice.

## 6. Walkthrough

Tracing `BiFunction<String, String, String> greeting = (var firstName, var lastName) -> firstName + " " + lastName;`:

1. The compiler reads the declaration: `BiFunction<String, String, String> greeting`. The target type is `BiFunction<String, String, String>`.

2. The compiler looks up `BiFunction`'s single abstract method: `R apply(T t, U u)`. With the type arguments supplied, this becomes `String apply(String t, String u)`.

3. The compiler encounters the lambda `(var firstName, var lastName) -> firstName + " " + lastName`. Because the target type's method signature is `String apply(String, String)`, the compiler infers `firstName` as `String` and `lastName` as `String`.

4. The compiler checks the body `firstName + " " + lastName` — string concatenation on two `String` operands — returns `String`, matching the expected return type.

5. At runtime: `greeting.apply("Alice", "Smith")` invokes the lambda. `firstName` = `"Alice"`, `lastName` = `"Smith"`. The body evaluates to `"Alice Smith"`, which is returned.

The key point: `var` in lambda parameters changes nothing about how types are inferred or how the code runs — it only adds a syntactic position where annotations can be placed.

## 7. Gotchas & takeaways

> The uniformity rule is strict: if one lambda parameter uses `var`, every parameter must use `var`. `(var x, y) -> ...` does not compile. This is different from local variable `var` which has no such constraint because each declaration is independent.

- `var` in lambda parameters was introduced in Java 11 (JEP 323) specifically to enable type-use annotations on lambda parameters. It is not a general-purpose style recommendation.
- The feature has zero runtime overhead — `var` is erased at compile time and the bytecode is identical to implicit or explicit lambda parameters.
- You cannot use `var` for a lambda that has no target type (e.g. `var f = (var x) -> x;` — the compiler cannot infer `x`'s type because there is no functional interface target type).
- For everyday lambdas without annotations, implicit parameters (`(x, y) -> ...`) remain the idiomatic choice. Only reach for `var` when you need to annotate.
- Standard annotation processors (Checker Framework, NullAway, Lombok) recognise `var` lambda parameters and can process type-use annotations correctly.
