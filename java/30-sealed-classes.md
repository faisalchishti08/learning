# Java Sealed Classes [Java 17+]

## Overview

Sealed classes (finalized Java 17, JEP 409) restrict which classes can extend or implement them. The set of subtypes is closed and enumerated in the declaration. Together with records and pattern matching, they enable algebraic data types.

---

## 1. Sealed Class Basics

### Visual Diagram

```
Before sealed:
  abstract class Shape {}
  // Anyone anywhere can extend Shape — open hierarchy
  class Circle extends Shape {}  // in any package, any module
  class Triangle extends Shape {} // unknown extensions

After sealed:
  sealed class Shape permits Circle, Rectangle, Triangle {}
  // ONLY Circle, Rectangle, Triangle may extend Shape
  // Any other extension is a compile error

Subtypes must be:
  final         → no further extension
  sealed        → extends but also restricts its own subtypes
  non-sealed    → opens the hierarchy back up

Permitted classes must:
  - Be in the same package (or same compilation unit) as the sealed class
  - Directly extend/implement the sealed class
  - Not be anonymous or local
```

### Example 1 — Sealed Class with final Subtypes

```java
public class SealedDemo {
    sealed interface Shape permits Circle, Rectangle, Triangle {}

    record Circle(double radius) implements Shape {}
    record Rectangle(double width, double height) implements Shape {}
    final class Triangle implements Shape {
        final double a, b, c;
        Triangle(double a, double b, double c) { this.a = a; this.b = b; this.c = c; }
    }

    // Pattern matching switch — compiler knows ALL cases (exhaustive) [Java 21]
    static double area(Shape shape) {
        return switch (shape) {
            case Circle c    -> Math.PI * c.radius() * c.radius();
            case Rectangle r -> r.width() * r.height();
            case Triangle t  -> {
                double s = (t.a + t.b + t.c) / 2;
                yield Math.sqrt(s * (s-t.a) * (s-t.b) * (s-t.c)); // Heron's formula
            }
        }; // NO default needed — compiler verifies exhaustiveness!
    }

    public static void main(String[] args) {
        System.out.println(area(new Circle(5)));        // 78.54
        System.out.println(area(new Rectangle(4, 6)));  // 24.0
        System.out.println(area(new Triangle(3, 4, 5))); // 6.0
    }
}
```

**What this does:** The sealed hierarchy lets the compiler verify the `switch` is exhaustive — no `default` needed. Add a new permitted subtype? The compiler immediately flags all switches that don't handle it.

### Dry Run — Compiler Exhaustiveness Check

```
sealed interface Shape permits Circle, Rectangle, Triangle

switch(shape) {
  case Circle c    → ...
  case Rectangle r → ...
  // Triangle missing!
}
→ COMPILE ERROR: switch expression does not cover all possible input values

This is the key advantage: the compiler tells you exactly what you missed.
With a plain abstract class, a switch without default gives no warning.
```

---

## 2. sealed, final, non-sealed

### Example 1 — Extending the Hierarchy

```java
public class HierarchyDemo {
    // sealed interface — closed at this level
    sealed interface Expr permits Num, Add, Mul, Neg {}

    // final — no further subclassing
    record Num(int value) implements Expr {}

    // non-sealed — opens the hierarchy again
    non-sealed interface Add extends Expr {
        Expr left();
        Expr right();
    }

    // sealed subtype — further restricts Add
    sealed interface Mul extends Expr permits IntMul, FloatMul {}

    record Neg(Expr expr) implements Expr {}

    // Concrete Add implementations (not restricted since Add is non-sealed)
    record SimpleAdd(Expr left, Expr right) implements Add {}

    record IntMul(int a, int b) implements Mul {}
    record FloatMul(double a, double b) implements Mul {}

    // Evaluate the expression tree
    static double eval(Expr expr) {
        return switch (expr) {
            case Num n        -> n.value();
            case Add a        -> eval(a.left()) + eval(a.right()); // catches all Add subtypes
            case IntMul m     -> m.a() * m.b();
            case FloatMul m   -> m.a() * m.b();
            case Neg n        -> -eval(n.expr());
        };
    }

    public static void main(String[] args) {
        // (2 + 3) * -4
        Expr expr = new IntMul(
            (int) eval(new SimpleAdd(new Num(2), new Num(3))),
            (int) eval(new Neg(new Num(4)))
        );
        System.out.println(eval(expr)); // -20.0
    }
}
```

**What this does:** Three permission levels — `final` (stop here), `sealed` (restrict further), `non-sealed` (re-open). `non-sealed` is useful when a library wants to seal its own types but allow users to extend a specific branch.

---

## 3. Sealed Interfaces

### Example 1 — Result Type (Railway-Oriented Programming)

```java
public class ResultType {
    // Sealed interface for success/failure — like Rust's Result<T, E>
    sealed interface Result<T> permits Result.Success, Result.Failure {
        record Success<T>(T value) implements Result<T> {}
        record Failure<T>(String error, Exception cause) implements Result<T> {
            Failure(String error) { this(error, null); }
        }
    }

    static Result<Integer> divide(int a, int b) {
        if (b == 0) return new Result.Failure<>("Division by zero");
        return new Result.Success<>(a / b);
    }

    static Result<String> toString(Result<Integer> result) {
        return switch (result) {
            case Result.Success<Integer> s -> new Result.Success<>("Result: " + s.value());
            case Result.Failure<Integer> f -> new Result.Failure<>(f.error());
        };
    }

    public static void main(String[] args) {
        var r1 = divide(10, 2);
        var r2 = divide(10, 0);

        switch (r1) {
            case Result.Success<Integer> s -> System.out.println("Got: " + s.value()); // Got: 5
            case Result.Failure<Integer> f -> System.out.println("Error: " + f.error());
        }

        switch (r2) {
            case Result.Success<Integer> s -> System.out.println("Got: " + s.value());
            case Result.Failure<Integer> f -> System.out.println("Error: " + f.error()); // Error: Division by zero
        }
    }
}
```

**What this does:** Sealed `Result<T>` with `Success`/`Failure` variants — a type-safe alternative to exceptions for expected errors. The switch is exhaustive: you're forced to handle both cases.

---

## 4. Sealed Classes and Pattern Matching Together

### Example 1 — JSON AST

```java
public class JsonAST {
    sealed interface JsonNode permits JsonNull, JsonBool, JsonNumber, JsonString, JsonArray, JsonObject {}

    record JsonNull()                          implements JsonNode {}
    record JsonBool(boolean value)             implements JsonNode {}
    record JsonNumber(double value)            implements JsonNode {}
    record JsonString(String value)            implements JsonNode {}
    record JsonArray(java.util.List<JsonNode> elements) implements JsonNode {}
    record JsonObject(java.util.Map<String, JsonNode> fields) implements JsonNode {}

    static String prettyPrint(JsonNode node) {
        return switch (node) {
            case JsonNull n           -> "null";
            case JsonBool b           -> String.valueOf(b.value());
            case JsonNumber n         -> String.valueOf(n.value());
            case JsonString s         -> "\"" + s.value() + "\"";
            case JsonArray a          -> "[" + a.elements().stream()
                                           .map(JsonAST::prettyPrint)
                                           .reduce((l, r) -> l + ", " + r)
                                           .orElse("") + "]";
            case JsonObject o         -> "{" + o.fields().entrySet().stream()
                                           .map(e -> "\"" + e.getKey() + "\": " + prettyPrint(e.getValue()))
                                           .reduce((l, r) -> l + ", " + r)
                                           .orElse("") + "}";
        };
    }

    public static void main(String[] args) {
        var person = new JsonObject(java.util.Map.of(
            "name", new JsonString("Alice"),
            "age", new JsonNumber(30),
            "active", new JsonBool(true)
        ));

        System.out.println(prettyPrint(person));
        // {"name": "Alice", "age": 30.0, "active": true}
    }
}
```

**What this does:** Sealed `JsonNode` hierarchy models all JSON value types. The `prettyPrint` switch is exhaustive — if you add a new JSON type (e.g., `JsonDate`), every switch site is immediately flagged by the compiler.

---

## Quick Reference

```
Sealed class/interface declaration:
  sealed class Foo permits A, B, C {}
  sealed interface I permits X, Y {}

Subtypes must be one of:
  final class A extends Foo {}          → no further subclassing
  sealed class B extends Foo permits D {} → further restricted
  non-sealed class C extends Foo {}     → opened back up

Constraints:
  - Permitted classes must be in same package (or compilation unit)
  - Must directly extend the sealed parent
  - Cannot be anonymous or local classes

Pattern matching with sealed:
  switch (expr) {
    case A a -> ...   // covers A and all its sealed subtypes
    case B b -> ...   // NO default needed if all cases covered
  }
  // Compiler verifies exhaustiveness — compile error if any case missing

Use cases:
  - Domain modeling (Shape, Result<T>, Expr, JsonNode)
  - Error types with explicit handling
  - State machines with explicit states
  - Command/event patterns

Java version:
  Java 15: preview
  Java 16: second preview
  Java 17: final (JEP 409)
```
