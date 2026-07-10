---
card: java
gi: 957
slug: records-implementing-interfaces
title: Records implementing interfaces
---

## 1. What it is

A record cannot `extend` another class (it implicitly extends the sealed `java.lang.Record`), but it can `implement` any number of interfaces, exactly like an ordinary class — `record Point(int x, int y) implements Comparable<Point> { ... }` is entirely valid. This lets a record participate fully in interface-based polymorphism (being passed around as its interface type, being used wherever that interface is expected) while still gaining all the immutable-data-carrier benefits records provide: auto-generated accessors, `equals`/`hashCode`/`toString`, and a validated canonical constructor. A record implementing an interface must provide implementations for the interface's abstract methods, exactly as any class would — either by writing them explicitly in the record's body, or, for a method the interface declares as a default method, inheriting that default implementation automatically unless the record chooses to override it.

## 2. Why & when

This matters because many real domain types are naturally both "an immutable bundle of these specific values" (what a record gives you for free) *and* "a thing with this particular behavioral contract" (what an interface expresses) — a `Money` record implementing `Comparable<Money>` so amounts can be sorted, a `Point` record implementing a custom `Shape` interface alongside `Circle` and `Square`, or a small value type implementing a marker interface used by a serialization framework to identify eligible types. Because records can implement interfaces just like ordinary classes, you don't have to choose between "get all the record boilerplate-elimination benefits" and "participate in this interface hierarchy" — you get both simultaneously. The one real restriction worth internalizing is that a record's fields are already fixed by its component list — an interface that expects an implementing class to hold *additional* mutable state beyond what a method contract requires (rather than just contributing behavior) is a poor fit for a record, since there's no way to add extra fields beyond the declared components.

## 3. Core concept

```
interface Shape {
    double area();
    default String describe() {                 // default method -- record can inherit as-is
        return "a shape with area " + area();
    }
}

record Circle(double radius) implements Shape {
    public double area() { return Math.PI * radius * radius; }   // MUST implement abstract method
    // describe() inherited from Shape's default -- no need to override unless customizing
}

record Square(double side) implements Shape, Comparable<Square> {  // MULTIPLE interfaces, comma-separated
    public double area() { return side * side; }
    public int compareTo(Square other) { return Double.compare(this.area(), other.area()); }
}
```

A record implementing an interface must supply every abstract method the interface declares, exactly like any class — the record's automatically-generated members (accessors, `equals`, `hashCode`, `toString`) are entirely separate from, and unaffected by, whatever interfaces it additionally implements.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A record implementing an interface, combining its auto-generated data-carrier members with the interface's required behavioral contract" >
  <rect x="20" y="30" width="180" height="90" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">record Circle</text>
  <text x="110" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">auto: accessor, equals,</text>
  <text x="110" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">hashCode, toString</text>

  <rect x="240" y="30" width="180" height="90" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">implements Shape</text>
  <text x="330" y="68" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">must provide: area()</text>
  <text x="330" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">inherits: describe() (default)</text>

  <rect x="460" y="30" width="160" height="90" fill="#1c2430" stroke="#f0883e"/>
  <text x="540" y="55" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">usable as Shape</text>
  <text x="540" y="75" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">polymorphically, alongside</text>
  <text x="540" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">any other Shape implementer</text>

  <line x1="200" y1="75" x2="240" y2="75" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="420" y1="75" x2="460" y2="75" stroke="#8b949e" marker-end="url(#a)"/>
</svg>

*A record gains full interface polymorphism on top of its automatic data-carrier behavior, entirely independently of one another.*

## 5. Runnable example

Scenario: model a small shape hierarchy using records implementing a shared interface, evolving from a basic single-interface implementation, to sorting a mixed collection using an additional `Comparable` interface, to a more advanced case combining multiple interfaces (behavioral and marker) on the same record.

### Level 1 — Basic

```java
public class RecordInterfaceBasic {
    interface Shape {
        double area();
        default String describe() {
            return String.format("area = %.2f", area());
        }
    }

    record Circle(double radius) implements Shape {
        public double area() { return Math.PI * radius * radius; }
    }

    record Square(double side) implements Shape {
        public double area() { return side * side; }
    }

    public static void main(String[] args) {
        Shape c = new Circle(2.0);
        Shape s = new Square(3.0);
        System.out.println("circle: " + c.describe());
        System.out.println("square: " + s.describe());
    }
}
```

**How to run:** `java RecordInterfaceBasic.java` (JDK 17+).

Expected output:
```
circle: area = 12.57
square: area = 9.00
```

Both `Circle` and `Square` implement `Shape`'s single abstract method, `area()`, each in its own record body — and both automatically inherit `describe()`'s default implementation unchanged, since neither record overrides it; both are also usable through the shared `Shape` interface type, exactly as any ordinary class implementing an interface would be.

### Level 2 — Intermediate

```java
import java.util.*;

public class RecordInterfaceComparable {
    interface Shape {
        double area();
    }

    record Circle(double radius) implements Shape, Comparable<Circle> {
        public double area() { return Math.PI * radius * radius; }
        public int compareTo(Circle other) { return Double.compare(this.area(), other.area()); }
    }

    public static void main(String[] args) {
        List<Circle> circles = new ArrayList<>(List.of(
            new Circle(3.0), new Circle(1.0), new Circle(2.0)
        ));
        Collections.sort(circles); // relies on Circle's Comparable<Circle> implementation
        for (Circle c : circles) {
            System.out.printf("radius=%.1f, area=%.2f%n", c.radius(), c.area());
        }
    }
}
```

**How to run:** `java RecordInterfaceComparable.java` (JDK 17+).

Expected output:
```
radius=1.0, area=3.14
radius=2.0, area=12.57
radius=3.0, area=28.27
```

The real-world concern added: `Circle` implements both a domain-specific interface (`Shape`) and the standard `Comparable<Circle>` interface simultaneously — the latter is what lets `Collections.sort` order the list by area with zero additional code beyond the `compareTo` implementation already written directly in the record's body, demonstrating that a record's compatibility with standard library APIs (sorting, in this case) works identically to any ordinary class implementing the same interfaces.

### Level 3 — Advanced

```java
import java.util.*;

public class RecordInterfaceMultiple {
    interface Shape {
        double area();
    }
    interface Serializable3D {
        // A hypothetical marker-like interface expressing "this shape can also be described in 3D
        // by extrusion" -- demonstrates a record implementing an interface with NO methods of its own,
        // purely to participate in a type check elsewhere.
    }

    record Circle(double radius) implements Shape, Comparable<Circle>, Serializable3D {
        public double area() { return Math.PI * radius * radius; }
        public int compareTo(Circle other) { return Double.compare(this.area(), other.area()); }
    }
    record Square(double side) implements Shape, Comparable<Square> {
        public double area() { return side * side; }
        public int compareTo(Square other) { return Double.compare(this.area(), other.area()); }
    }

    static void extrudeIfPossible(Shape shape) {
        if (shape instanceof Serializable3D) {
            System.out.println("shape supports 3D extrusion");
        } else {
            System.out.println("shape does NOT support 3D extrusion");
        }
    }

    public static void main(String[] args) {
        extrudeIfPossible(new Circle(2.0));
        extrudeIfPossible(new Square(3.0));
    }
}
```

**How to run:** `java RecordInterfaceMultiple.java` (JDK 17+).

Expected output:
```
shape supports 3D extrusion
shape does NOT support 3D extrusion
```

The production-flavored hard case: `Circle` implements three interfaces simultaneously — `Shape` (a genuine behavioral contract requiring `area()`), `Comparable<Circle>` (a standard library contract requiring `compareTo`), and `Serializable3D` (a marker interface with no methods at all, used purely so `instanceof Serializable3D` can be checked elsewhere) — while `Square` implements only two of the three; this demonstrates that a record can freely mix multiple, unrelated interface contracts (behavioral, standard-library, and marker) exactly as an ordinary class could, with `instanceof` checks against any of them working identically to checks against any other class hierarchy.

## 6. Walkthrough

Tracing `extrudeIfPossible(new Circle(2.0))` end to end from `RecordInterfaceMultiple.main`:

1. `new Circle(2.0)` constructs a `Circle` record instance — since `Circle` declares `implements Shape, Comparable<Circle>, Serializable3D`, this single object is simultaneously a valid `Shape`, a valid `Comparable<Circle>`, and a valid `Serializable3D`, exactly as any object implementing multiple interfaces would be, regardless of it being a record.
2. This `Circle` instance is passed to `extrudeIfPossible`, whose parameter is declared as `Shape` — this is a legal, ordinary upcast, since `Circle` does implement `Shape` (providing a concrete `area()` implementation, satisfying that interface's sole abstract method).
3. Inside `extrudeIfPossible`, the check `shape instanceof Serializable3D` runs — even though the parameter is statically typed as `Shape`, `instanceof` checks the object's *actual runtime type*, and since the actual object is a `Circle`, which does implement `Serializable3D`, this check evaluates to `true`.
4. The method prints "shape supports 3D extrusion," correctly reflecting that this particular runtime object happens to additionally implement the marker interface, even though the static, declared parameter type (`Shape`) says nothing at all about `Serializable3D`.
5. The second call, `extrudeIfPossible(new Square(3.0))`, follows the identical process, but since `Square` was declared implementing only `Shape` and `Comparable<Square>` — deliberately *not* `Serializable3D` — the `instanceof Serializable3D` check evaluates to `false` for this object.
6. The method prints "shape does NOT support 3D extrusion" for the square — confirming that `instanceof` checks against a record's implemented interfaces behave exactly as they would for any ordinary class, entirely independent of whatever automatic data-carrier behavior (accessors, `equals`, `hashCode`, `toString`) the record additionally provides; interface implementation and record-specific generation are two entirely orthogonal, independently-combinable features of the same declaration.

## 7. Gotchas & takeaways

> **Gotcha:** an interface's default method is inherited by a record unchanged unless explicitly overridden — but if that default method's implementation implicitly assumes mutable state or a particular non-record superclass structure (unusual, but possible in a poorly-designed interface), it may not behave as expected when inherited by a record; always verify a default method's actual logic makes sense for an immutable, record-based implementer before relying on it unmodified.

- A record cannot extend another class (it implicitly extends the sealed `java.lang.Record`), but it can implement any number of interfaces, exactly like an ordinary class.
- A record implementing an interface must provide implementations for all the interface's abstract methods, written directly in the record's body; default methods are inherited automatically unless explicitly overridden.
- Interface implementation and a record's automatic member generation (accessors, `equals`, `hashCode`, `toString`) are entirely independent, freely combinable features — implementing interfaces doesn't affect or replace any of the automatically-generated members.
- Records work seamlessly with standard library APIs built around interfaces (like `Comparable` and `Collections.sort`), exactly as any ordinary class implementing the same interface would.
- A record can implement multiple interfaces simultaneously — behavioral contracts, standard-library interfaces, and even marker interfaces with no methods — and `instanceof` checks against any of them work identically to checks against any other class hierarchy.
- See [record components & canonical constructor](0954-record-components-canonical-constructor.md) for how a record's own declared members interact with whatever interfaces it implements, and [records & immutability](0958-records-immutability.md) for how implementing an interface interacts with — and does not compromise — a record's immutability guarantee.
