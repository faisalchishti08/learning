---
card: java
gi: 612
slug: var-rules-where-it-is-allowed
title: var rules & where it is allowed
---

## 1. What it is

`var` in Java 10 has specific syntactic and semantic rules about where it can and cannot be used. It is allowed for local variables with initialisers (including for-loop variables, enhanced for-loop variables, and try-with-resources variables), but prohibited for fields, method parameters, method return types, catch formal parameters, and uninitialised variables. These rules are enforced at compile time and are designed to ensure that the inferred type is always locally and unambiguously determinable from the immediate context.

## 2. Why & when

The restrictions exist because type inference for fields, parameters, and return types would cross method or compilation-unit boundaries. A field's type must be stable across all methods; a method parameter's type is part of the method's public API signature; a return type is part of the API contract. Allowing `var` in these positions would mean the type is determined by the compiler from the initialiser or method body, making it invisible to human readers and tooling without source-level analysis — defeating Java's explicit-API philosophy. The rules deliberately scope `var` to the smallest possible context: a single method body, where the reader can see both the declaration and the initialiser in one glance.

## 3. Core concept

```java
// ✅ ALLOWED:
var name = "Alice";                              // local variable
for (var i = 0; i < 10; i++) { ... }            // for-loop index
for (var item : list) { ... }                    // enhanced for-loop
try (var in = Files.newBufferedReader(path)) {}  // try-with-resources

// ❌ NOT ALLOWED:
// class Foo { var x = 5; }              // fields
// void method(var param) { ... }        // method parameters
// var method() { return 5; }            // return types
// try { } catch (var e) { }             // catch formal (until Java 22 preview)
// var x;                                 // no initialiser
// var x = null;                          // null initialiser
```

The rule is straightforward: `var` is allowed wherever the compiler can see an initialiser expression and the variable's scope is limited to a single method, constructor, or initialiser block.

## 4. Diagram

<svg viewBox="0 0 520 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="var is allowed for local variables with initialisers, not for fields, params, or return types">
  <rect x="20" y="10" width="480" height="200" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#6db33f" font-size="12" font-family="sans-serif">✅ ALLOWED:</text>
  <text x="40" y="55" fill="#6db33f" font-size="10" font-family="monospace">  var x = 42;</text>
  <text x="40" y="72" fill="#6db33f" font-size="10" font-family="monospace">  for (var item : list)</text>
  <text x="40" y="89" fill="#6db33f" font-size="10" font-family="monospace">  for (var i = 0; i < n; i++)</text>
  <text x="40" y="106" fill="#6db33f" font-size="10" font-family="monospace">  try (var reader = ...)</text>

  <line x1="30" y1="115" x2="490" y2="115" stroke="#8b949e" stroke-width="0.5"/>

  <text x="30" y="135" fill="#f85149" font-size="12" font-family="sans-serif">❌ NOT ALLOWED:</text>
  <text x="40" y="155" fill="#f85149" font-size="10" font-family="monospace">  var field;               (instance/static fields)</text>
  <text x="40" y="172" fill="#f85149" font-size="10" font-family="monospace">  void m(var param)        (method parameters)</text>
  <text x="40" y="189" fill="#f85149" font-size="10" font-family="monospace">  var method()             (method return types)</text>
  <text x="40" y="206" fill="#f85149" font-size="10" font-family="monospace">  catch (var e)            (catch formal)</text>
  <text x="40" y="223" fill="#f85149" font-size="10" font-family="monospace">  var x;  var x = null;     (no/null initialiser)</text>

  <text x="300" y="50" fill="#8b949e" font-size="8" font-family="sans-serif">Rule: scope = single method/block</text>
  <text x="300" y="155" fill="#8b949e" font-size="8" font-family="sans-serif">Reason: type would cross API boundaries</text>
</svg>

The dividing line: local scope with initialiser = allowed; API-level or no initialiser = not allowed.

## 5. Runnable example

Scenario: a comprehensive checklist of `var` legality — starting with basic allowed usage, extending to a method that exercises every legal position, and finally a lint-like pass over a code sample detecting all illegal uses.

### Level 1 — Basic

```java
// File: VarRulesDemo.java
import java.util.*;

public class VarRulesDemo {

    // ❌ Not allowed here
    // var instanceField = 42;

    // ✅ Allowed: method-local
    public static void showAllowed() {
        var name = "Java 10";                      // simple type
        var list = List.of(1, 2, 3);               // generic type from factory
        var map = new HashMap<String, Integer>();   // generic type from constructor

        for (var item : list) {                    // enhanced for
            System.out.print(item + " ");
        }
        System.out.println();

        for (var i = 0; i < 3; i++) {              // traditional for
            System.out.print(".");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        System.out.println("=== var: where it's allowed ===\n");
        showAllowed();
    }
}
```

**How to run:** `java VarRulesDemo.java`

Expected output:
```
=== var: where it's allowed ===

1 2 3 
...
```

The simplest demonstration: `var` works in local variable declarations, enhanced for loops, and traditional for loops. The instance field declaration is commented out because it would not compile.

### Level 2 — Intermediate

```java
// File: VarEverywhere.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class VarEverywhere {

    // ❌ Fields — would not compile:
    // private var config = new Properties();

    // ❌ Method params — would not compile:
    // public static void process(var input) {}

    // ❌ Return type — would not compile:
    // public static var compute() { return 42; }

    // ✅ All local uses combined
    public static void main(String[] args) throws Exception {
        System.out.println("=== Every Legal Location for var ===\n");

        // 1. Simple assignment
        var message = "Hello from var";
        System.out.println("1. Simple: " + message);

        // 2. Complex generic type
        var nested = new HashMap<String, List<Map.Entry<Integer, String>>>();
        nested.put("key", List.of(Map.entry(1, "one")));
        System.out.println("2. Complex generic: " + nested);

        // 3. For-loop index
        System.out.print("3. For-loop: ");
        for (var i = 0; i < 3; i++) System.out.print(i + " ");
        System.out.println();

        // 4. Enhanced for-loop
        System.out.print("4. Enhanced for: ");
        for (var num : new int[]{10, 20, 30}) System.out.print(num + " ");
        System.out.println();

        // 5. Try-with-resources (write and delete a temp file)
        Path tmp = Files.createTempFile("var-demo", ".txt");
        try (var writer = Files.newBufferedWriter(tmp)) {
            writer.write("var works in try-with-resources too!");
        }
        System.out.println("5. Try-with-resources: wrote to " + tmp.getFileName());
        Files.delete(tmp);

        // 6. var in ternary
        var result = args.length > 0 ? args[0] : "default";
        System.out.println("6. Ternary: " + result);

        System.out.println("\n✅ All locations above compile and run.");
    }
}
```

**How to run:** `java VarEverywhere.java`

Expected output:
```
=== Every Legal Location for var ===

1. Simple: Hello from var
2. Complex generic: {key=[1=one]}
3. For-loop: 0 1 2 
4. Enhanced for: 10 20 30 
5. Try-with-resources: wrote to var-demo...txt
6. Ternary: default

✅ All locations above compile and run.
```

The real-world demonstration: every legal use of `var` in a single method. Simple assignment, complex generics (where `var` shines), for-loop index, enhanced for, try-with-resources, and ternary expressions — all compile and work correctly because the compiler can unambiguously infer the type from the right-hand side.

### Level 3 — Advanced

```java
// File: VarLinter.java
import java.util.*;
import java.util.stream.*;

public class VarLinter {

    record LintResult(String location, boolean allowed, String reason) {}

    static List<LintResult> lintVarUsage() {
        return List.of(
            new LintResult("Local variable:      var x = 42;", true, "has initialiser"),
            new LintResult("Enhanced for:        for (var item : list)", true, "type from iterable"),
            new LintResult("For loop index:      for (var i = 0; ...)", true, "initialiser = int"),
            new LintResult("Try-with-resources:  try (var r = ...)", true, "has initialiser"),
            new LintResult("\nInstance field:      var x = 5;", false, "field scope > method"),
            new LintResult("Static field:        static var x;", false, "field scope > method"),
            new LintResult("Method param:        void m(var p)", false, "API boundary"),
            new LintResult("Method return:       var method()", false, "API boundary"),
            new LintResult("Catch formal:        catch (var e)", false, "type from exception hierarchy"),
            new LintResult("\nNo initialiser:      var x;", false, "cannot infer type"),
            new LintResult("Null initialiser:    var x = null;", false, "null has no type"),
            new LintResult("Array initialiser:   var arr = {1,2};", false, "ambiguous array type")
        );
    }

    public static void main(String[] args) {
        System.out.println("=== var Legality Linter ===\n");

        var results = lintVarUsage();
        long allowed = results.stream().filter(r -> r.allowed()).count();
        long blocked = results.stream().filter(r -> !r.allowed()).count();

        for (var r : results) {
            if (r.location().startsWith("\n")) {
                System.out.println(r.location().trim());
                continue;
            }
            var icon = r.allowed() ? "✅" : "❌";
            System.out.printf("  %s %s%n    → %s%n", icon, r.location(), r.reason());
        }

        System.out.printf("\nSummary: %d allowed, %d blocked%n", allowed, blocked);
        System.out.println("\nRule: var requires (a) local scope + (b) unambiguous initialiser");
    }
}
```

**How to run:** `java VarLinter.java`

Expected output:
```
=== var Legality Linter ===

  ✅ Local variable:      var x = 42;
    → has initialiser
  ✅ Enhanced for:        for (var item : list)
    → type from iterable
  ✅ For loop index:      for (var i = 0; ...)
    → initialiser = int
  ✅ Try-with-resources:  try (var r = ...)
    → has initialiser

Instance field:      var x = 5;
  ❌ Instance field:      var x = 5;
    → field scope > method
  ❌ Static field:        static var x;
    → field scope > method
  ❌ Method param:        void m(var p)
    → API boundary
  ❌ Method return:       var method()
    → API boundary
  ❌ Catch formal:        catch (var e)
    → type from exception hierarchy

No initialiser:      var x;
  ❌ No initialiser:      var x;
    → cannot infer type
  ❌ Null initialiser:    var x = null;
    → null has no type
  ❌ Array initialiser:   var arr = {1,2};
    → ambiguous array type

Summary: 4 allowed, 8 blocked

Rule: var requires (a) local scope + (b) unambiguous initialiser
```

The production-flavoured analysis: a linter that enumerates every legal and illegal use of `var` with explanations. The pattern is clear — if the type is determinable from the right-hand side and the declaration doesn't cross a method/API boundary, `var` is allowed. Otherwise, it isn't.

## 6. Walkthrough

For each legal use, the compiler's inference is straightforward:

- `var x = 42;` → RHS is an `int` literal → `x` is `int`.
- `for (var item : list)` → `list` is `Iterable<T>`, compiler infers `item` as `T` → `item` is `T`.
- `for (var i = 0; ...)` → RHS `0` is an `int` literal → `i` is `int`.
- `try (var reader = Files.newBufferedReader(path))` → method return type is `BufferedReader` → `reader` is `BufferedReader`.
- `var result = args.length > 0 ? args[0] : "default"` → ternary: `String` & `String` → result is `String`.

For illegal uses:

- `var x = null;` → `null` has no type. The compiler cannot determine whether `x` should be `String`, `Integer`, `Object`, etc. Error: "cannot infer type for local variable x".
- `var arr = {1, 2, 3};` → array initialisers like `{1, 2, 3}` are only allowed in declarations with an explicit array type or as part of `new int[]{1, 2, 3}`. `var` doesn't provide array type context.
- Fields, parameters, return types: the compiler rejects these because the JLS restricts `var` to local variables with initialisers (JLS §14.4).

## 7. Gotchas & takeaways

> `var` with anonymous classes: `var obj = new Object() { void hello() { System.out.println("hi"); } };` — this works, and `obj` is a non-denotable type (the anonymous subclass). You can call `obj.hello()` but you cannot pass `obj` to a method expecting `Object` without casting because the anonymous type has additional methods. This is an advanced use case; avoid it unless you specifically need the anonymous type's extra methods.

- `var` is a reserved type name, not a keyword. `var var = "var";` compiles because the first `var` is the type name and the second is an identifier. This backward compatibility is important for codebases that used `var` as a variable name before Java 10.
- The compiler infers the most specific type possible. `var list = new ArrayList<String>()` → `ArrayList<String>` (not `List<String>`). To get a more general type, use the interface on the RHS: `var list = (List<String>) new ArrayList<String>()` or use the explicit type.
- `var` in lambda parameter position (`(var x, var y) -> x + y`) is allowed from Java 11 onward, not Java 10. In Java 10, lambda parameters must have explicit types or be implicitly typed (no `var`).
- IDE support for `var` is excellent — IntelliJ and Eclipse can show the inferred type inline as a hint, inline the explicit type back, or toggle between `var` and explicit type with a single action. 