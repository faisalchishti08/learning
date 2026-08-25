# Java Pattern Matching

## Overview

Pattern matching allows extracting data from objects in a concise, safe way. Java 21 includes: `instanceof` type patterns, switch expression patterns (with guards), record patterns, and primitive patterns.

---

## 1. instanceof Pattern Matching [Java 16+]

### What is it

The old `instanceof` required a manual cast. Pattern matching combines the check and binding in one step.

### Visual Diagram

```
Old way (Java 15 and earlier):
  if (obj instanceof String) {
      String s = (String) obj;  // redundant cast
      doSomething(s.length());
  }

New way (Java 16+):
  if (obj instanceof String s) {  // check + bind in one step
      doSomething(s.length());    // s is in scope here
  }

Scope rules:
  if (obj instanceof String s) {
      // s in scope — obj IS a String here
      System.out.println(s.length());
  } else {
      // s NOT in scope — obj is NOT a String here
  }

  // Also works in conditional expressions:
  if (obj instanceof String s && s.length() > 5) { ... }
  // s is available in the && right-hand side because left must be true first
```

### Example 1 — Pattern Matching instanceof

```java
public class InstanceofPattern {
    sealed interface Shape permits Circle, Rectangle, Triangle {}
    record Circle(double radius) implements Shape {}
    record Rectangle(double w, double h) implements Shape {}
    record Triangle(double base, double height) implements Shape {}

    static String describe(Object obj) {
        // Old: if (obj instanceof Shape) { Shape s = (Shape) obj; ... }
        if (obj instanceof Circle c) {
            return "Circle with radius " + c.radius();
        } else if (obj instanceof Rectangle r && r.w() == r.h()) {
            return "Square with side " + r.w(); // guard condition with && 
        } else if (obj instanceof Rectangle r) {
            return "Rectangle " + r.w() + "×" + r.h();
        } else if (obj instanceof String s) {
            return "String: " + s.toUpperCase();
        }
        return "Unknown: " + obj;
    }

    public static void main(String[] args) {
        System.out.println(describe(new Circle(3.0)));        // Circle with radius 3.0
        System.out.println(describe(new Rectangle(4.0, 4.0)));// Square with side 4.0
        System.out.println(describe(new Rectangle(3.0, 5.0)));// Rectangle 3.0×5.0
        System.out.println(describe("hello"));                 // String: HELLO
        System.out.println(describe(42));                      // Unknown: 42
    }
}
```

**What this does:** `obj instanceof Circle c` declares binding variable `c` — only in scope when the check passes. The `&&` pattern uses the bound variable in the same condition.

### Dry Run — Scope Flow

```
describe(new Rectangle(4.0, 4.0)):

  obj instanceof Circle c?  → false  → c not in scope
  obj instanceof Rectangle r && r.w() == r.h()?
    → obj instanceof Rectangle r → true, r bound to Rectangle[4.0, 4.0]
    → r.w() == r.h() → 4.0 == 4.0 → true
  → return "Square with side 4.0"

describe(new Rectangle(3.0, 5.0)):
  obj instanceof Rectangle r && r.w() == r.h()?
    → true, r bound
    → 3.0 == 5.0 → false
    → whole condition false
  obj instanceof Rectangle r?  ← next check, new r binding
    → true, return "Rectangle 3.0×5.0"
```

---

## 2. Switch Expression Patterns [Java 21]

### What is it

Pattern matching in `switch` expressions and statements. Handles type patterns, guard clauses (`when`), null cases, and sealed type exhaustiveness.

### Example 1 — Type Patterns in Switch

```java
public class SwitchPatterns {
    sealed interface Notification permits Email, SMS, Push {}
    record Email(String to, String subject, String body) implements Notification {}
    record SMS(String phone, String message) implements Notification {}
    record Push(String deviceId, String title) implements Notification {}

    static String format(Notification n) {
        return switch (n) {
            case Email e  -> "EMAIL to " + e.to() + ": " + e.subject();
            case SMS s    -> "SMS to " + s.phone() + ": " + s.message();
            case Push p   -> "PUSH to device " + p.deviceId() + ": " + p.title();
        }; // exhaustive — no default needed (sealed interface)
    }

    // Guard clauses with 'when' [Java 21]
    static String priority(Notification n) {
        return switch (n) {
            case SMS s when s.message().startsWith("URGENT") -> "HIGH PRIORITY SMS";
            case SMS s                                        -> "Normal SMS";
            case Email e when e.subject().contains("URGENT") -> "HIGH PRIORITY Email";
            case Email e                                      -> "Normal Email";
            case Push p                                       -> "Push notification";
        };
    }

    public static void main(String[] args) {
        System.out.println(format(new Email("alice@ex.com", "Hi", "Hello")));
        // EMAIL to alice@ex.com: Hi

        System.out.println(priority(new SMS("555-0100", "URGENT: server down")));
        // HIGH PRIORITY SMS

        System.out.println(priority(new SMS("555-0101", "weekly digest")));
        // Normal SMS
    }
}
```

**What this does:** `when` guards refine case matching — check the type first, then the additional condition. Cases are evaluated top-to-bottom; the first matching case wins.

### Example 2 — null Handling in Switch

```java
public class NullInSwitch {
    static String describe(Object obj) {
        return switch (obj) {
            case null          -> "null value";           // [Java 21] explicit null case
            case Integer i
                when i < 0     -> "negative: " + i;
            case Integer i     -> "positive: " + i;
            case String s
                when s.isEmpty() -> "empty string";
            case String s      -> "string: " + s;
            default            -> "other: " + obj.getClass().getSimpleName();
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(null));    // null value
        System.out.println(describe(-5));      // negative: -5
        System.out.println(describe(42));      // positive: 42
        System.out.println(describe(""));      // empty string
        System.out.println(describe("hi"));    // string: hi
        System.out.println(describe(3.14));    // other: Double
    }
}
```

**What this does:** Before Java 21, `switch` threw `NullPointerException` on null. Now a `case null` branch handles it explicitly. Without `case null`, null still throws NPE — this is a backward-compatible default.

### Dry Run — Guard Evaluation

```
describe(-5):
  case null?         → obj is -5, not null → skip
  case Integer i when i < 0?
    → -5 instanceof Integer? YES, i = -5
    → i < 0? -5 < 0? YES
    → match! return "negative: -5"

describe(42):
  case null?         → skip
  case Integer i when i < 0?
    → 42 instanceof Integer? YES, i = 42
    → i < 0? 42 < 0? NO → guard fails, try next
  case Integer i?
    → 42 instanceof Integer? YES, i = 42
    → no guard → match! return "positive: 42"
```

---

## 3. Record Patterns [Java 21]

### What is it

Record patterns destructure records — extract components inline during pattern match. Nests naturally for complex record graphs.

### Example 1 — Destructuring Records

```java
public class RecordPatterns {
    record Point(int x, int y) {}
    record Circle(Point center, double radius) {}
    record Rectangle(Point topLeft, Point bottomRight) {}

    sealed interface Shape permits Circle, Rectangle {}
    record CircleShape(Circle circle) implements Shape {}
    record RectShape(Rectangle rect) implements Shape {}

    static String describe(Object obj) {
        return switch (obj) {
            // Record pattern — destructure directly
            case Point(int x, int y)
                when x == 0 && y == 0 -> "Origin";
            case Point(int x, int y)  -> "Point(" + x + ", " + y + ")";

            // Nested record pattern
            case Circle(Point(int cx, int cy), double r) ->
                "Circle at (" + cx + "," + cy + ") radius " + r;

            default -> "unknown";
        };
    }

    static double area(Shape shape) {
        return switch (shape) {
            case CircleShape(Circle(Point _, double r)) ->  // _ ignores center
                Math.PI * r * r;
            case RectShape(Rectangle(Point(int x1, int y1), Point(int x2, int y2))) ->
                (double) Math.abs(x2 - x1) * Math.abs(y2 - y1);
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(new Point(0, 0)));          // Origin
        System.out.println(describe(new Point(3, 4)));          // Point(3, 4)
        System.out.println(describe(new Circle(new Point(1, 2), 5.0)));
        // Circle at (1,2) radius 5.0

        System.out.println(area(new CircleShape(new Circle(new Point(0, 0), 3.0))));
        // 28.27...
        System.out.println(area(new RectShape(new Rectangle(new Point(0, 0), new Point(4, 3)))));
        // 12.0
    }
}
```

**What this does:** `case Circle(Point(int cx, int cy), double r)` destructures two levels deep — extracts center coordinates and radius in one pattern. `_` ignores components you don't need.

### Dry Run — Nested Record Pattern Matching

```
area(new CircleShape(new Circle(new Point(0,0), 3.0))):

switch(shape):
  case CircleShape(Circle(Point _, double r)):
    → shape instanceof CircleShape? YES
    → extract: circle = Circle(Point(0,0), 3.0)
    → circle instanceof Circle(Point _, double r)?
    → YES: _ matches Point(0,0) (ignored), r = 3.0
    → yield Math.PI * 3.0 * 3.0 = 28.27...
```

---

## 4. Primitive Patterns [Java 23+]

### What is it

[Java 23 preview, Java 24+ final] allows primitive types in type patterns. Useful when `Object` might hold a boxed primitive.

```java
// Java 23+ preview
Object obj = 42;
switch (obj) {
    case int i when i > 0  -> System.out.println("positive int: " + i);
    case int i             -> System.out.println("non-positive int: " + i);
    case long l            -> System.out.println("long: " + l);
    default                -> System.out.println("other");
}
```

---

## 5. Pattern Matching with Generics

### Example 1

```java
import java.util.*;

public class GenericPatterns {
    sealed interface Container<T> permits Box, Empty {}
    record Box<T>(T value) implements Container<T> {}
    record Empty<T>() implements Container<T> {}

    static <T> String inspect(Container<T> c) {
        return switch (c) {
            case Box<T> b when b.value() instanceof String s -> "Box of String: " + s;
            case Box<T> b when b.value() instanceof Integer i -> "Box of Integer: " + i;
            case Box<T> b -> "Box of other: " + b.value();
            case Empty<T> e -> "Empty container";
        };
    }

    public static void main(String[] args) {
        System.out.println(inspect(new Box<>("hello")));  // Box of String: hello
        System.out.println(inspect(new Box<>(42)));        // Box of Integer: 42
        System.out.println(inspect(new Empty<>()));        // Empty container
    }
}
```

---

## Quick Reference

```
instanceof pattern [Java 16+]:
  if (obj instanceof String s) { ... }
  if (obj instanceof String s && s.length() > 5) { ... }

switch patterns [Java 21]:
  switch (expr) {
    case TypeName varName -> ...              // type pattern
    case TypeName varName when condition -> ... // guarded type pattern
    case null -> ...                          // null case
    default -> ...                           // fallback
  }
  
Record patterns [Java 21]:
  case Point(int x, int y) -> ...             // destructure
  case Circle(Point(int cx, int cy), double r) -> ... // nested
  case Circle(Point _, double r) -> ...       // _ ignores component

Sealed + switch = exhaustiveness:
  sealed interface I permits A, B {}
  switch (i) {
    case A a -> ...
    case B b -> ...
  }  // no default needed — compiler verifies completeness

Guard keyword: when (Java 21)
  case Integer i when i > 0 -> "positive"

History:
  Java 14: switch expressions (final, no patterns yet)
  Java 16: instanceof patterns (final)
  Java 17: sealed classes (final)
  Java 19: switch patterns (preview)
  Java 21: switch patterns + record patterns + null case (final)
```
