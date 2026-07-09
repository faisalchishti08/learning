---
card: java
gi: 584
slug: private-methods-in-interfaces
title: Private methods in interfaces
---

## 1. What it is

Java 9 lets interfaces declare **private instance methods** — helper methods with a method body, callable only from other default (or private) methods within the same interface, never visible to implementing classes or external callers. They exist purely to let default methods share common logic without duplicating code or exposing that shared logic as part of the interface's public contract.

## 2. Why & when

Java 8 introduced default methods (interface methods with a body), which immediately created a familiar problem: once an interface has two or three default methods that share overlapping logic, where does the shared code go? Before Java 9, the only option was either duplicating the logic in each default method, or extracting it into a `static` helper method — but a `static` interface method is necessarily `public` (interfaces had no visibility modifier below public before Java 9), so that "helper" became part of the interface's public API whether you wanted it to be or not. Private interface methods close this gap exactly the way private methods in a class always have: internal helper logic, reusable across the interface's own default methods, without leaking into the public contract implementing classes and callers actually see.

## 3. Core concept

```java
public interface Validator {
    default boolean isValidEmail(String s) {
        return isNotBlank(s) && s.contains("@");
    }

    default boolean isValidUsername(String s) {
        return isNotBlank(s) && s.length() >= 3;
    }

    private boolean isNotBlank(String s) { // shared helper, invisible outside this interface
        return s != null && !s.isBlank();
    }
}
```

`isNotBlank` is callable from `isValidEmail` and `isValidUsername` (both default methods in the same interface), but it is not inherited, not overridable, and not visible on any class that `implements Validator` — exactly like a `private` method in a regular class.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Private interface methods are callable only from the interface's own default methods, invisible to implementing classes">
  <rect x="20" y="15" width="280" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="35" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">interface Validator</text>

  <rect x="35" y="45" width="250" height="30" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="160" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">default isValidEmail(...)</text>
  <rect x="35" y="80" width="250" height="30" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="160" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">default isValidUsername(...)</text>
  <rect x="35" y="115" width="250" height="25" rx="4" fill="#0d1117" stroke="#f0883e"/>
  <text x="160" y="132" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">private isNotBlank(...)</text>

  <text x="320" y="70" fill="#6db33f" font-size="10" font-family="sans-serif">implementing class SEES this</text>
  <text x="320" y="100" fill="#6db33f" font-size="10" font-family="sans-serif">implementing class SEES this</text>
  <text x="320" y="132" fill="#f85149" font-size="10" font-family="sans-serif">implementing class CANNOT see this</text>
</svg>

Only the two default methods are part of the interface's visible contract; the private helper stays entirely internal.

## 5. Runnable example

Scenario: a `Shape` interface computing area-related default behavior, whose default methods share validation logic — starting with two default methods duplicating the same validation check, then extracting that duplication into a private helper method, then adding a second private helper that itself calls the first, demonstrating that private interface methods can call each other.

### Level 1 — Basic

```java
// File: Shape.java
public interface Shape {
    double area();

    default String describe() {
        if (area() < 0) return "Invalid shape (negative area)"; // duplicated check
        return "Shape with area " + area();
    }

    default boolean isLarger(Shape other) {
        if (area() < 0 || other.area() < 0) return false; // same check, duplicated again
        return area() > other.area();
    }
}
```

```java
// File: Circle.java
public class Circle implements Shape {
    private final double radius;
    public Circle(double radius) { this.radius = radius; }
    public double area() { return Math.PI * radius * radius; }

    public static void main(String[] args) {
        Circle small = new Circle(2);
        Circle large = new Circle(5);
        System.out.println(small.describe());
        System.out.println(large.isLarger(small));
    }
}
```

**How to run:** `javac Shape.java Circle.java && java Circle`

Expected output:
```
Shape with area 12.566370614359172
true
```

Both `describe()` and `isLarger(...)` independently check `area() < 0` — a small, duplicated validity check. This works correctly, but the duplication is a maintenance liability: if the "what counts as invalid" logic ever needs to change (say, to also reject `NaN`), it has to be updated in every default method that repeats it.

### Level 2 — Intermediate

```java
// File: Shape.java
public interface Shape {
    double area();

    default String describe() {
        if (!hasValidArea()) return "Invalid shape (negative area)";
        return "Shape with area " + area();
    }

    default boolean isLarger(Shape other) {
        if (!hasValidArea() || !other.hasValidArea()) return false;
        return area() > other.area();
    }

    private boolean hasValidArea() { // shared helper — single source of truth for validity
        return area() >= 0 && !Double.isNaN(area());
    }
}
```

```java
// File: Circle.java
public class Circle implements Shape {
    private final double radius;
    public Circle(double radius) { this.radius = radius; }
    public double area() { return Math.PI * radius * radius; }

    public static void main(String[] args) {
        Circle small = new Circle(2);
        Circle large = new Circle(5);
        System.out.println(small.describe());
        System.out.println(large.isLarger(small));
    }
}
```

**How to run:** `javac Shape.java Circle.java && java Circle`

Expected output:
```
Shape with area 12.566370614359172
true
```

The real-world concern this adds: `hasValidArea()`, a `private` interface method, is now the single, shared implementation of "what counts as a valid area" — both `describe()` and `isLarger(...)` call it instead of duplicating the check. `other.hasValidArea()` inside `isLarger` also works correctly: even though `other` is a *different* `Shape` instance, `hasValidArea()` is still accessible on it because both objects are instances of types implementing the same interface, and the private method's own body (`area() >= 0 && !Double.isNaN(area())`) operates on whichever instance it's called on — `this` inside a default or private interface method, exactly like `this` inside a regular class's private method.

### Level 3 — Advanced

```java
// File: Shape.java
public interface Shape {
    double area();
    double perimeter();

    default String fullReport() {
        StringBuilder report = new StringBuilder();
        report.append(formatMetric("Area", area()));
        report.append(formatMetric("Perimeter", perimeter()));
        return report.toString();
    }

    default boolean isLarger(Shape other) {
        if (!hasValidArea() || !other.hasValidArea()) return false;
        return area() > other.area();
    }

    private boolean hasValidArea() { // helper #1
        return area() >= 0 && !Double.isNaN(area());
    }

    private String formatMetric(String label, double value) { // helper #2 — calls helper #1
        if (label.equals("Area") && !hasValidArea()) {
            return label + ": INVALID\n";
        }
        return String.format("%s: %.2f%n", label, value);
    }
}
```

```java
// File: Rectangle.java
public class Rectangle implements Shape {
    private final double width, height;
    public Rectangle(double width, double height) { this.width = width; this.height = height; }
    public double area() { return width * height; }
    public double perimeter() { return 2 * (width + height); }

    public static void main(String[] args) {
        Rectangle rect = new Rectangle(4, 6);
        System.out.print(rect.fullReport());
    }
}
```

**How to run:** `javac Shape.java Rectangle.java && java Rectangle`

Expected output:
```
Area: 24.00
Perimeter: 20.00
```

This handles the production-flavoured case of **one private interface method calling another**: `formatMetric` (private helper #2) calls `hasValidArea()` (private helper #1) internally, chaining private-method logic entirely within the interface, exactly as private methods in a regular class can call each other freely. `fullReport()` (the only default method actually invoked here) never needs to know that `formatMetric` internally delegates part of its logic to `hasValidArea` — that's an implementation detail fully contained within the interface, invisible to `Rectangle` and to any caller of `fullReport()`.

## 6. Walkthrough

Execution starts in `Rectangle.main` in the Level 3 example. `rect` is constructed with `width=4`, `height=6`. `rect.fullReport()` is called — `fullReport` is a `default` method, inherited from `Shape`, running with `this` bound to `rect`.

Inside `fullReport`, `report` starts as an empty `StringBuilder`. The first call, `formatMetric("Area", area())`, first evaluates `area()` — a call to `rect.area()`, `Shape`'s abstract method, implemented by `Rectangle` as `width * height = 4 * 6 = 24`. This computed value (`24.0`) is passed as `formatMetric`'s second argument, along with the label `"Area"`.

```
formatMetric("Area", 24.0):
  label.equals("Area") -> true
  hasValidArea() called: area() = 24.0 >= 0 && !isNaN -> true -> hasValidArea() returns true
  condition "label.equals(Area) && !hasValidArea()" -> true && !true -> false
  -> falls through to: String.format("%s: %.2f%n", "Area", 24.0) -> "Area: 24.00\n"
```

`formatMetric` calls `hasValidArea()` — this is helper #2 calling helper #1, both private interface methods, resolved entirely within `Shape`'s own default-method machinery, with `this` still bound to `rect` throughout. `hasValidArea()` checks `area() >= 0 && !Double.isNaN(area())`; `24.0 >= 0` is `true` and `Double.isNaN(24.0)` is `false`, so `hasValidArea()` returns `true`. Since the area is valid, `formatMetric`'s special-case branch (`label.equals("Area") && !hasValidArea()`) evaluates to `false`, so control falls through to the normal formatting line, producing `"Area: 24.00\n"`.

`report.append(...)` adds that string. The second call, `formatMetric("Perimeter", perimeter())`, evaluates `perimeter()` as `2 * (4 + 6) = 20.0`; since `label.equals("Area")` is `false` for `"Perimeter"`, the special-case branch is skipped entirely regardless of validity, producing `"Perimeter: 20.00\n"` directly. `report.append(...)` adds that too.

`fullReport()` returns the concatenated string, and `main` prints it via `System.out.print(...)` (not `println`, since each line already ends with `%n` from the format strings) — producing the two lines `"Area: 24.00"` and `"Perimeter: 20.00"`.

## 7. Gotchas & takeaways

> Private interface methods can call other private interface methods, and default methods can call private ones, but the reverse is never needed and doesn't apply the same way — a private method never needs to call an *abstract* interface method's specific implementation by name, it simply calls it the normal way (`area()`), and Java resolves that call dynamically against whatever concrete class `this` actually is at runtime, exactly like any other interface method call.

- A `private` interface method must have a body — interfaces still cannot have private *abstract* methods, since that would be meaningless (nothing outside the interface could ever provide the missing implementation for a method nothing outside the interface can even see).
- Private interface methods come in two forms: private instance methods (covered here, implicitly have access to `this` and can call abstract/default/other private methods) and `private static` methods (covered in the next topic, cannot access `this` at all, used for pure utility logic that doesn't depend on any particular implementing instance).
- Unlike `default` methods, private interface methods are **not inherited** by implementing classes at all — they don't appear in the implementing class's method set, can't be overridden, and can't be called from outside the interface under any circumstances, including via `Shape.super.someMethod()`-style explicit interface-method syntax.
- This feature exists purely for code organization within an interface's own default-method implementations — it changes nothing about what an interface's public contract looks like to implementers or callers, only how that contract's default behavior is internally structured and de-duplicated.
- Before Java 9, the closest approximation was a `static` helper method (necessarily public, polluting the interface's API surface) or, in exceptionally hacky code, delegating to a separate, entirely non-interface utility class — private interface methods make the intended "internal helper, not part of the contract" relationship explicit and enforced by the compiler.
