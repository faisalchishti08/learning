---
card: java
gi: 968
slug: record-deconstruction-patterns
title: Record deconstruction patterns
---

## 1. What it is

Beyond the basic `Point(int x, int y)` form introduced in [record patterns / deconstruction](0960-record-patterns-deconstruction.md), record deconstruction has several additional mechanical details worth understanding on their own: you can use `var` in place of an explicit type for any component (`Point(var x, var y)`), letting the compiler infer each component's type exactly as it would for a `var` local variable declaration; deconstruction works not just in `instanceof` and `switch`, but also directly in an enhanced `for` loop's header, when iterating over a collection of a record type (`for (Point(int x, int y) : points)`); and a record pattern's component sub-patterns can themselves be nested type patterns, guarded patterns, or further record patterns, all composed together in a single deconstruction expression.

## 2. Why & when

Using `var` in a deconstruction pattern is most useful when a component's type is verbose or already obvious from context (a `BigDecimal`, a long generic type, or simply when you want the destructuring to keep working unchanged if the record's component type is later refined) — it trades a small amount of explicitness for reduced repetition, exactly the same tradeoff `var` makes for ordinary local variables. Deconstructing directly in a `for` loop header matters whenever you're iterating over a collection of records and want immediate access to their components without an extra line inside the loop body calling accessors — this is a small but genuinely common convenience once records are used pervasively for domain data. Understanding that component sub-patterns can nest and combine (a component itself matched with a guard, or against a further record pattern) is what lets deconstruction handle realistically complex domain shapes — a list of orders, each containing a nested address record, each of which you want to both destructure and validate in one expression — without falling back to verbose, manual accessor-chaining code.

## 3. Core concept

```
record Point(int x, int y) {}

// var in a component position -- inferred, not explicitly typed
if (obj instanceof Point(var x, var y)) {
    System.out.println(x + y);   // x, y both inferred as int
}

// Deconstruction directly in an enhanced for-loop header:
List<Point> points = List.of(new Point(1, 2), new Point(3, 4));
for (Point(int x, int y) : points) {
    System.out.println("(" + x + ", " + y + ")");
}

// Nested + guarded sub-patterns, composed together:
record Order(String id, Point deliveryLocation) {}
if (order instanceof Order(String id, Point(int x, int y)) when x >= 0 && y >= 0) {
    System.out.println("Order " + id + " delivers to non-negative quadrant (" + x + ", " + y + ")");
}
```

Every one of these forms is still fundamentally the same mechanism from [record patterns / deconstruction](0960-record-patterns-deconstruction.md) — a type check plus simultaneous component extraction — just applied in more contexts (`for` loops) and with more flexible component sub-patterns (`var`, nested patterns, guards).

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A record deconstruction pattern used directly in an enhanced for-loop header, binding each element's components fresh on every iteration" >
  <rect x="20" y="30" width="280" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">for (Point(int x, int y) : points)</text>
  <text x="160" y="63" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">destructure EACH element, every iteration</text>

  <rect x="340" y="30" width="260" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="470" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">x, y freshly bound per loop body</text>
  <text x="470" y="63" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no manual .x() / .y() calls needed</text>

  <line x1="300" y1="50" x2="340" y2="50" stroke="#8b949e" marker-end="url(#a)"/>

  <text x="320" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same deconstruction mechanism as instanceof/switch, applied to loop iteration directly</text>
</svg>

*A record pattern in a for-loop header deconstructs each iterated element automatically, without a separate accessor-call step inside the loop body.*

## 5. Runnable example

Scenario: process a list of delivery orders, evolving from a basic `var`-based deconstruction, to a realistic loop-header deconstruction over a list of nested records, to a more advanced case combining nested patterns and guards to validate and route orders in one expression.

### Level 1 — Basic

```java
public class RecordDeconstructionVar {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        Object obj = new Point(3, 4);
        if (obj instanceof Point(var x, var y)) { // var infers int for both components here
            System.out.println("sum: " + (x + y));
        }
    }
}
```

**How to run:** `java RecordDeconstructionVar.java` (JDK 21+; record patterns require Java 21+).

Expected output:
```
sum: 7
```

`var x` and `var y` let the compiler infer each component's declared type (`int`, in both cases) from `Point`'s own component declarations, rather than requiring `Point(int x, int y)` explicitly — functionally identical here, but useful when a component's type is more verbose or you'd rather not repeat it.

### Level 2 — Intermediate

```java
import java.util.*;

public class RecordDeconstructionForLoop {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        List<Point> points = List.of(new Point(1, 1), new Point(3, 4), new Point(0, 5));

        double totalDistance = 0;
        for (Point(int x, int y) : points) { // deconstruct DIRECTLY in the loop header
            totalDistance += Math.sqrt(x * x + y * y);
        }
        System.out.printf("total distance from origin: %.2f%n", totalDistance);
    }
}
```

**How to run:** `java RecordDeconstructionForLoop.java` (JDK 21+).

Expected output:
```
total distance from origin: 8.83
```

The real-world concern added: iterating over `points` with `for (Point(int x, int y) : points)` gives immediate access to `x` and `y` inside the loop body, with no separate call to `.x()`/`.y()` needed at all — for a loop processing many records' components, this keeps the body focused purely on the actual computation (`Math.sqrt(x * x + y * y)`), rather than a preliminary line of accessor calls before the real logic begins.

### Level 3 — Advanced

```java
import java.util.*;

public class RecordDeconstructionNestedGuarded {
    record Point(int x, int y) {}
    record Order(String id, Point deliveryLocation, double weightKg) {}

    static String route(Order order) {
        return switch (order) {
            case Order(String id, Point(int x, int y), double w) when x == 0 && y == 0 ->
                id + ": local pickup, no delivery needed";
            case Order(String id, Point(int x, int y), double w) when w > 50.0 ->
                id + ": heavy freight route to (" + x + ", " + y + "), weight " + w + "kg";
            case Order(String id, Point(int x, int y), double w) ->
                id + ": standard delivery to (" + x + ", " + y + ")";
        };
    }

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("A100", new Point(0, 0), 2.5),
            new Order("A101", new Point(10, 20), 75.0),
            new Order("A102", new Point(5, 5), 3.0)
        );
        for (Order order : orders) {
            System.out.println(route(order));
        }
    }
}
```

**How to run:** `java RecordDeconstructionNestedGuarded.java` (JDK 21+).

Expected output:
```
A100: local pickup, no delivery needed
A101: heavy freight route to (10, 20), weight 75.0kg
A102: standard delivery to (5, 5)
```

The production-flavored hard case: each `switch` case deconstructs `Order` down through its nested `Point` component (`Order(String id, Point(int x, int y), double w)`) *and* applies a guard condition referencing both the outer record's `weightKg` and the inner record's coordinates simultaneously — expressing a realistic, multi-level routing decision (special-case local pickups, special-case heavy freight, then a general fallback) entirely through pattern structure and guards, with no manual accessor chaining (`order.deliveryLocation().x()`) anywhere in the code.

## 6. Walkthrough

Tracing `route(new Order("A101", new Point(10, 20), 75.0))` end to end from `RecordDeconstructionNestedGuarded.main`:

1. The `switch`'s first case, `case Order(String id, Point(int x, int y), double w) when x == 0 && y == 0`, first matches the outer shape: is the value an `Order`? Yes — it destructures into `id = "A101"`, and then attempts to further destructure the second component (which must itself be a `Point`) into `x` and `y`, and binds the third component to `w`.
2. With all of `id`, `x`, `y`, and `w` now bound (`"A101"`, `10`, `20`, `75.0`), the guard `x == 0 && y == 0` is evaluated: since `x` is `10` (not `0`), this guard is `false`, so this case does not match, and the `switch` proceeds to the next case, even though the underlying `Order`/`Point` shape did successfully destructure.
3. The second case, `case Order(String id, Point(int x, int y), double w) when w > 50.0`, re-attempts the identical destructuring (binding fresh copies of `id`, `x`, `y`, `w` for this case's own scope) — the shape matches again (it's the same `Order`), and this time the guard `w > 50.0` is evaluated: since `w` is `75.0`, this is `true`, so this case is selected.
4. The matched case's body constructs and returns the string `"A101: heavy freight route to (10, 20), weight 75.0kg"`, using the `id`, `x`, `y`, and `w` bound specifically within *this* case's own pattern match.
5. Back in `main`, this returned string is printed directly via the enhanced `for` loop iterating over `orders` — the loop itself doesn't use record deconstruction here (it binds each element to the plain variable `order`), but `route`'s internal `switch` performs the full nested-and-guarded deconstruction described above for every order passed to it.
6. The same process repeats independently for `"A100"` (matching the first, origin-check case, since its `Point` is `(0, 0)`) and `"A102"` (matching neither special case, since its weight is only `3.0` and its location isn't the origin, falling through to the final, unguarded case) — demonstrating that each `switch` invocation re-evaluates its cases fresh, in order, against whatever specific `Order` it's given, with nested destructuring and guard conditions composing together naturally to express a genuinely multi-factor routing decision in a compact, declarative form.

## 7. Gotchas & takeaways

> **Gotcha:** using `var` in a record pattern's component position infers the component's *declared* type from the record itself, not some broader or narrower type based on context — `Point(var x, var y)` against a record declared as `record Point(int x, int y)` always infers `x` and `y` as `int`, regardless of how they're subsequently used; `var` here is purely a syntactic shorthand for "whatever type this component is actually declared as," not an independent type-inference mechanism the way `var` can sometimes feel more open-ended for a local variable initialized from a complex expression.

- A record pattern's component can use `var` instead of an explicit type, inferring the component's actual declared type directly from the record — useful for reducing repetition when a component's type is verbose or already clear from context.
- Record deconstruction works directly in an enhanced `for` loop header when iterating over a collection of a record type, giving immediate access to each element's components without separate accessor calls inside the loop body.
- Component sub-patterns can themselves be further record patterns (nesting), type patterns, or combined with guard conditions — letting a single pattern express a genuinely multi-level, multi-factor match against complex, nested domain data.
- Guards attached to a case with nested destructuring can reference any of the bound variables from any level of the nesting, letting routing or validation logic reference both outer and inner record components together.
- See [record patterns / deconstruction](0960-record-patterns-deconstruction.md) for the foundational mechanics this topic builds additional detail onto, and [nested patterns](0969-nested-patterns.md) for a more focused look specifically at multi-level pattern composition.
