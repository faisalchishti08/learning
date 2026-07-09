---
card: java
gi: 611
slug: local-variable-type-inference-var
title: Local-variable type inference: var
---

## 1. What it is

`var` is a Java 10 feature that lets you declare local variables without explicitly writing the type — the compiler infers the type from the initialiser on the right-hand side. `var` is not a keyword (it's a reserved type name), so existing code that uses `var` as a variable or method name continues to compile. The variable is still statically typed at compile time — `var name = "Alice"` produces a `String` variable, not a dynamically-typed one. The type is fixed at the point of declaration and cannot change.

## 2. Why & when

Java's explicit type declarations are valuable for public APIs, but for local variables — especially those initialised with a constructor or factory method that already states the type — the repetition is noise: `Map<String, List<Order>> ordersByCustomer = new HashMap<>();` states the type twice. `var` eliminates the redundancy when the right-hand side makes the type obvious, while keeping Java's static type safety intact. The feature was heavily influenced by similar constructs in C# (`var`), Scala (`val`/`var`), and Kotlin (`val`/`var`), and is designed to reduce boilerplate without sacrificing readability — the type is still visible to the reader in the initialiser.

## 3. Core concept

```java
var name = "Alice";                    // String
var age = 30;                          // int
var prices = List.of(10, 20, 30);      // List<Integer>
var map = new HashMap<String, List<String>>(); // HashMap<String, List<String>>

// The type is fixed at compile time:
// name = 42;  ← COMPILE ERROR: String cannot hold int

// Works with diamond:
var orders = new ArrayList<Order>();   // ArrayList<Order>
```

The compiler infers the type from the initialiser expression. There is no runtime overhead — `var` is purely a compile-time feature; the bytecode is identical to an explicit type declaration.

## 4. Diagram

<svg viewBox="0 0 560 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="var infers type at compile time from the right-hand side initialiser">
  <rect x="20" y="10" width="520" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="40" y="30" width="200" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="140" y="55" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">var name = "Alice"</text>

  <text x="250" y="55" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="265" y="30" width="130" height="40" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="330" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">String name</text>

  <text x="405" y="55" fill="#8b949e" font-size="10" font-family="monospace">──►</text>

  <rect x="420" y="30" width="110" height="40" rx="4" fill="#0d1117" stroke="#6db33f"/>
  <text x="475" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">bytecode identical</text>

  <text x="40" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">var list = new ArrayList&lt;String&gt;() → ArrayList&lt;String&gt;</text>
  <text x="40" y="118" fill="#8b949e" font-size="10" font-family="sans-serif">var map = new HashMap&lt;String, Integer&gt;() → HashMap&lt;String, Integer&gt;</text>
  <text x="40" y="136" fill="#8b949e" font-size="10" font-family="sans-serif">var x = 42 → int  |  var y = 3.14 → double  |  var flag = true → boolean</text>

  <text x="40" y="160" fill="#f85149" font-size="9" font-family="sans-serif">Does NOT work: fields, method parameters, return types, catch formal, uninitialised</text>
</svg>

The compiler replaces `var` with the inferred type during compilation; the bytecode shows the actual type.

## 5. Runnable example

Scenario: refactoring verbose local variable declarations in a data-processing method — starting with basic type inference, extending to complex generic types and streams, and finally exploring the limits of `var` with lambdas and ambiguous types.

### Level 1 — Basic

```java
// File: VarDemo.java
import java.util.*;

public class VarDemo {
    public static void main(String[] args) {
        // Explicit types (old way)
        String explicitName = "Alice";
        int explicitAge = 30;
        List<String> explicitList = List.of("a", "b", "c");

        // var (new way — same types inferred)
        var name = "Alice";
        var age = 30;
        var list = List.of("a", "b", "c");

        System.out.println("Explicit: " + explicitName + ", " + explicitAge + ", " + explicitList);
        System.out.println("var:      " + name + ", " + age + ", " + list);

        // The inferred types are exactly the same
        System.out.println("\nTypes:");
        System.out.println("  name: " + name.getClass().getSimpleName());
        System.out.println("  list: " + list.getClass().getSimpleName());
    }
}
```

**How to run:** `java VarDemo.java`

Expected output:
```
Explicit: Alice, 30, [a, b, c]
var:      Alice, 30, [a, b, c]

Types:
  name: String
  list: ImmutableCollections$ListN
```

The simplest usage: replace explicit local type declarations with `var` when the right-hand side makes the type obvious. `name.getClass()` confirms it's a `String`, `list.getClass()` confirms it's the `List` implementation from `List.of()`.

### Level 2 — Intermediate

```java
// File: VarWithGenerics.java
import java.util.*;
import java.util.stream.*;

public class VarWithGenerics {
    public static void main(String[] args) {
        // Complex generic types benefit most from var
        var ordersByCustomer = new HashMap<String, List<String>>();
        var stats = new TreeMap<String, Double>();

        ordersByCustomer.put("Alice", List.of("ORD-1", "ORD-2"));
        ordersByCustomer.put("Bob",   List.of("ORD-3"));

        // Stream pipelines: var reduces noise
        var customers = List.of("Alice", "Bob", "Charlie", "Diana");
        var result = customers.stream()
            .filter(c -> c.length() > 3)
            .map(String::toUpperCase)
            .collect(Collectors.joining(", "));

        System.out.println("Long-name customers: " + result);

        // var with for-each (since Java 10, the loop variable can also use var)
        System.out.println("\nCustomer orders:");
        for (var entry : ordersByCustomer.entrySet()) {
            var customer = entry.getKey();
            var orders = entry.getValue();
            System.out.printf("  %s → %s%n", customer, orders);
        }

        // Type is still static — this would not compile:
        // var x = "hello";
        // x = 42;  // COMPILE ERROR
    }
}
```

**How to run:** `java VarWithGenerics.java`

Expected output:
```
Long-name customers: ALICE, CHARLIE, DIANA

Customer orders:
  Alice → [ORD-1, ORD-2]
  Bob → [ORD-3]
```

The real-world concern: complex generic types (`HashMap<String, List<String>>`) are where `var` provides the most value — the type is stated once in the constructor, not repeated in the declaration. Enhanced for-loops also support `var` for the loop variable, making the code cleaner when iterating complex maps.

### Level 3 — Advanced

```java
// File: VarLimitations.java
import java.util.*;
import java.util.function.*;

public class VarLimitations {

    // var CANNOT be used here:
    // var instanceField = "nope";          // ❌ fields
    // static var staticField = "nope";      // ❌ static fields
    // public var method(var param) { ... }   // ❌ method params & return types

    public static void main(String[] args) {
        System.out.println("=== Where var works and where it doesn't ===\n");

        // ✅ Local variables with initializer
        var name = "Alice";
        var numbers = new int[]{1, 2, 3};

        // ✅ Enhanced for-loop variables
        for (var n : numbers) {
            // n is int
        }

        // ✅ Local variable in for-loop
        for (var i = 0; i < 3; i++) {
            // i is int
        }

        // ✅ Try-with-resources
        // try (var reader = new BufferedReader(...)) { ... }

        // ✅ Lambda parameters (with explicit target type, Java 11+)
        // But in Java 10, var is NOT allowed on lambda params

        // ❌ No initializer — type cannot be inferred
        // var x;  // COMPILE ERROR

        // ❌ Null initializer — no type info
        // var x = null;  // COMPILE ERROR

        // ❌ Array initializer without explicit type
        // var arr = {1, 2, 3};  // COMPILE ERROR (use new int[]{1,2,3})

        // ❌ Lambda target type ambiguous
        // var func = s -> s.length();  // COMPILE ERROR — Function or UnaryOperator?

        System.out.println("var is allowed in:");
        System.out.println("  ✅ Local variable declarations (with initializer)");
        System.out.println("  ✅ Enhanced for-loop variable");
        System.out.println("  ✅ For-loop index variable");
        System.out.println("  ✅ Try-with-resources variable\n");

        System.out.println("var is NOT allowed in:");
        System.out.println("  ❌ Fields (instance or static)");
        System.out.println("  ❌ Method parameters");
        System.out.println("  ❌ Method return types");
        System.out.println("  ❌ Catch formal parameters");
        System.out.println("  ❌ Lambda parameters (until Java 11)");
        System.out.println("  ❌ Without initializer (var x;)");
        System.out.println("  ❌ With null initializer (var x = null;)");

        // Demonstrate a legitimate use
        var complexMap = new LinkedHashMap<Integer, List<Map.Entry<String, Double>>>();
        System.out.println("\n\nExample of where var truly helps:");
        System.out.println("  Without var: LinkedHashMap<Integer, List<Map.Entry<String, Double>>> map");
        System.out.println("  With var:    var map = new LinkedHashMap<Integer, List<Map.Entry<String, Double>>>()");
    }
}
```

**How to run:** `java VarLimitations.java`

Expected output:
```
=== Where var works and where it doesn't ===

var is allowed in:
  ✅ Local variable declarations (with initializer)
  ✅ Enhanced for-loop variable
  ✅ For-loop index variable
  ✅ Try-with-resources variable

var is NOT allowed in:
  ❌ Fields (instance or static)
  ❌ Method parameters
  ❌ Method return types
  ❌ Catch formal parameters
  ❌ Lambda parameters (until Java 11)
  ❌ Without initializer (var x;)
  ❌ With null initializer (var x = null;)


Example of where var truly helps:
  Without var: LinkedHashMap<Integer, List<Map.Entry<String, Double>>> map
  With var:    var map = new LinkedHashMap<Integer, List<Map.Entry<String, Double>>>()
```

The production-flavoured edge cases: where `var` is and isn't allowed. The constraint is simple — `var` works only where the compiler can unambiguously determine the type from the immediate context (the initialiser). No initialiser = no type to infer. Null = no type information. Lambda = target type depends on the functional interface, which `var` alone can't determine.

## 6. Walkthrough

Tracing `var result = customers.stream().filter(...).map(...).collect(...)`:

1. The compiler encounters the declaration `var result`. It looks at the initialiser expression: `customers.stream().filter(c -> c.length() > 3).map(String::toUpperCase).collect(Collectors.joining(", "))`.

2. The compiler evaluates the expression type bottom-up:
   - `customers` is `List<String>` → `.stream()` returns `Stream<String>`.
   - `.filter(pred)` returns `Stream<String>` (same element type).
   - `.map(String::toUpperCase)` returns `Stream<String>` (same element type).
   - `.collect(Collectors.joining(", "))` — the `joining` collector returns `String`.
   - The full expression type is `String`.

3. The compiler infers `var result` → `String result`. The bytecode writes `String result` as if the developer had typed it explicitly.

4. At runtime: `result` is a plain `String` variable. No boxing, no dynamic dispatch, no overhead. `System.out.println(result)` calls `println(String)` directly.

## 7. Gotchas & takeaways

> `var` with diamond (`var list = new ArrayList<>()`) infers `ArrayList<Object>`, not the type you probably wanted. This is because the compiler needs type information from the right-hand side, and `<>` (diamond) with no constructor arguments provides none. Always specify type arguments on the right when using `var`: `var list = new ArrayList<String>()`.

- `var` is not a keyword — it's a "reserved type name." You can still have variables named `var`, methods named `var()`, and packages named `var`. The compiler distinguishes `var` as a type name from `var` as an identifier based on context.
- `var` in compound declarations is not allowed: `var x = 1, y = 2;` does not compile. Each `var` declaration must be on its own line.
- The type is fixed after inference — `var x = "hello"; x = 42;` is a compile error because `x` is a `String`. This is fundamentally different from JavaScript's `var` or Python's untyped variables.
- Use `var` when the type is obvious from the right-hand side (constructors, factory methods, `List.of()`, `Map.of()`). Avoid `var` when the type is not obvious (e.g. `var result = calculate()` — what does `calculate()` return?).
- `var` was introduced in Java 10 as a preview of local-variable type inference. Lambda parameter `var` was added in Java 11. The feature has been stable and widely adopted since. 