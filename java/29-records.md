# Java Records [Java 16+]

## Overview

Records are a special class form designed to be **transparent data carriers**. Before records, writing a simple DTO required: a class declaration, private fields, a constructor, getters, `equals()`, `hashCode()`, and `toString()` — typically 40–60 lines. A record collapses that to one line. Records are not just syntactic sugar — they carry semantic meaning: "this type's whole purpose is to hold this data."

---

## 1. What Records Are

### What it is

A record declaration `record Point(int x, int y) {}` auto-generates:
- **Canonical constructor** — `Point(int x, int y)` assigning both fields
- **Accessor methods** — `x()` and `y()` (NOT `getX()`/`getY()`)
- **`equals()`** — field-by-field comparison
- **`hashCode()`** — based on all components
- **`toString()`** — `Point[x=3, y=4]`

Records are implicitly `final` — cannot be extended. Fields are implicitly `private final`.

### Visual Diagram

```
Before (JavaBean/DTO — ~50 lines):
  public final class Point {
      private final int x, y;
      public Point(int x, int y) { this.x = x; this.y = y; }
      public int getX() { return x; }
      public int getY() { return y; }
      @Override public boolean equals(Object o) { ... 8 lines ... }
      @Override public int hashCode() { return Objects.hash(x, y); }
      @Override public String toString() { return "Point{x=" + x + ", y=" + y + "}"; }
  }

After (record — 1 line):
  record Point(int x, int y) {}
         ^      ^    ^
         |      |    +-- component 2: generates field + accessor y()
         |      +------- component 1: generates field + accessor x()
         +-------------- class name; implicitly final, extends Record

What you get for free:
  Point p = new Point(3, 4);
  p.x()          → 3         ← NOT getX()
  p.y()          → 4
  p.toString()   → "Point[x=3, y=4]"
  p.equals(new Point(3, 4)) → true
  p.hashCode()   → same as Objects.hash(3, 4)
```

### Code Example 1 — Basic record

```java
record Point(int x, int y) {}

Point p1 = new Point(3, 4);
Point p2 = new Point(3, 4);
Point p3 = new Point(1, 2);

System.out.println(p1.x());           // 3
System.out.println(p1.y());           // 4
System.out.println(p1);               // Point[x=3, y=4]
System.out.println(p1.equals(p2));    // true
System.out.println(p1.equals(p3));    // false
System.out.println(p1.hashCode() == p2.hashCode()); // true
```

**What this does:** Demonstrates all auto-generated members. `equals` compares component values, not identity.

### Code Example 2 — Record as DTO

```java
record UserDTO(String username, String email, int age) {}

UserDTO user = new UserDTO("alice", "alice@example.com", 30);
System.out.println(user);
// UserDTO[username=alice, email=alice@example.com, age=30]

// Perfect for returning from a service layer:
public UserDTO findUser(String username) {
    // ...fetch from DB...
    return new UserDTO(username, "alice@example.com", 30);
}
```

**What this does:** Record replaces a full DTO class. Accessors use component names directly — `user.username()`, not `user.getUsername()`.

### Code Example 3 — Records are final

```java
record Point(int x, int y) {}

// This does NOT compile:
// class Point3D extends Point { ... }
// error: cannot extend a record class

// Records CAN implement interfaces:
interface Printable { void print(); }
record LabeledPoint(String label, int x, int y) implements Printable {
    @Override public void print() {
        System.out.println(label + ": (" + x + ", " + y + ")");
    }
}

new LabeledPoint("Origin", 0, 0).print(); // Origin: (0, 0)
```

**What this does:** Shows finality restriction and the interface workaround. Records implicitly extend `java.lang.Record`, leaving no room for another superclass.

### Dry Run — equals() on records

```
record Point(int x, int y) {}

p1 = new Point(3, 4)
p2 = new Point(3, 4)
p3 = new Point(3, 5)

p1.equals(p2):
  step 1: same reference? p1 == p2 → false (different objects)
  step 2: same type? both Point → true
  step 3: p1.x() == p2.x() → 3 == 3 → true
  step 4: p1.y() == p2.y() → 4 == 4 → true
  result: true

p1.equals(p3):
  step 3: p1.x() == p3.x() → 3 == 3 → true
  step 4: p1.y() == p3.y() → 4 == 5 → false
  result: false
```

> ⚠️ **Pitfall:** Accessor methods are `x()`, NOT `getX()`. Libraries expecting JavaBean conventions (Jackson, JPA, older frameworks) may not find them without configuration. Jackson 2.12+ handles records natively; older versions need `@JsonProperty`.

> ⚠️ **Pitfall:** Record fields are `private final`. You cannot add mutable instance state. If you need one mutable field, records are the wrong tool.

---

## 2. Compact Constructor

### What it is

A compact constructor omits the parameter list. The component parameters are implicitly in scope. Field assignment (`this.x = x`) happens **automatically after** the compact constructor body runs — you don't write it. Use compact constructors for validation and normalization.

### Visual Diagram

```
Canonical constructor (explicit):          Compact constructor:
  Point(int x, int y) {                     Point {
      if (x < 0) throw ...;                     if (x < 0) throw ...;
      this.x = x;   ← you write               // this.x = x ← auto-assigned after body
      this.y = y;   ← you write               // this.y = y ← auto-assigned after body
  }                                          }
                                             ^
                                             No parameter list () — that's what makes it compact
```

### Code Example 1 — Validation with compact constructor

```java
record Point(int x, int y) {
    Point {
        if (x < 0 || y < 0) {
            throw new IllegalArgumentException(
                "Coordinates must be non-negative: x=%d, y=%d".formatted(x, y)
            );
        }
    }
}

Point ok  = new Point(3, 4);  // fine
Point bad = new Point(-1, 4); // throws IllegalArgumentException
```

**What this does:** Validates before fields are assigned. If the exception is thrown, the object is never created — fields are never set.

### Code Example 2 — Null check with compact constructor

```java
import java.util.Objects;

record Person(String firstName, String lastName, int age) {
    Person {
        Objects.requireNonNull(firstName, "firstName must not be null");
        Objects.requireNonNull(lastName,  "lastName must not be null");
        if (age < 0 || age > 150) {
            throw new IllegalArgumentException("Invalid age: " + age);
        }
    }
}

Person p = new Person("Alice", "Smith", 30); // OK
Person n = new Person(null, "Smith", 30);    // NullPointerException
```

**What this does:** Defensive programming at construction time. The record is always valid if it exists — no need to validate at use sites.

### Code Example 3 — Compact constructor with parameter mutation

```java
// In a compact constructor you can reassign the parameters (not the fields directly)
record NormalizedString(String value) {
    NormalizedString {
        // Reassign the parameter 'value' — the field gets the new value
        value = (value == null) ? "" : value.trim().toLowerCase();
    }
}

NormalizedString s1 = new NormalizedString("  HELLO  ");
System.out.println(s1.value()); // hello

NormalizedString s2 = new NormalizedString(null);
System.out.println(s2.value()); // (empty string)
```

**What this does:** Reassigning the parameter in compact constructor changes what gets assigned to the field. This is the canonical way to normalize input.

> ⚠️ **Pitfall:** In a compact constructor you can reassign `value = ...` (the parameter) but NOT `this.value = ...` (the field). `this.value` is assigned automatically after the body — writing `this.value = something` is a compile error.

---

## 3. Canonical Constructor Customization

### What it is

The full explicit canonical constructor — same parameter names and types as the record components. Used when you need to transform values (e.g., swap to maintain invariants), normalize, or do complex validation that can't be expressed compactly.

### Visual Diagram

```
record Range(int lo, int hi) {
    Range(int lo, int hi) {   ← canonical: must assign ALL fields
        this.lo = Math.min(lo, hi);  ← swap if needed
        this.hi = Math.max(lo, hi);
    }
}

Range(3, 1) → lo=1, hi=3  (swapped)
Range(1, 3) → lo=1, hi=3  (unchanged)
Range(5, 5) → lo=5, hi=5  (equal OK)
```

### Code Example 1 — Range with normalization

```java
record Range(int lo, int hi) {
    Range(int lo, int hi) {
        this.lo = Math.min(lo, hi);
        this.hi = Math.max(lo, hi);
    }

    int length() { return hi - lo; }
    boolean contains(int value) { return value >= lo && value <= hi; }
}

Range r1 = new Range(5, 1);
System.out.println(r1);             // Range[lo=1, hi=5]
System.out.println(r1.length());    // 4
System.out.println(r1.contains(3)); // true
System.out.println(r1.contains(9)); // false
```

**What this does:** Caller passes (5, 1) but record normalizes to lo=1, hi=5. Invariant `lo <= hi` is always guaranteed.

### Code Example 2 — Defensive copy for mutable fields

```java
import java.util.List;
import java.util.ArrayList;

record ImmutableTagList(List<String> tags) {
    ImmutableTagList(List<String> tags) {
        // defensive copy to prevent external mutation
        this.tags = List.copyOf(tags);
    }
}

List<String> mutable = new ArrayList<>(List.of("java", "records"));
ImmutableTagList tl = new ImmutableTagList(mutable);
mutable.add("hacked");

System.out.println(tl.tags()); // [java, records] — not affected
```

**What this does:** Record holds an unmodifiable copy. Caller mutating the original list cannot corrupt the record's state. Without canonical constructor, the record would hold a reference to the mutable list.

### Code Example 3 — Canonical vs compact side-by-side

```java
// Compact — simple, can only mutate params
record PositiveInt(int value) {
    PositiveInt {
        if (value <= 0) throw new IllegalArgumentException("Must be positive");
    }
}

// Canonical — needed when you must control exactly what is assigned
record ClampedInt(int value, int min, int max) {
    ClampedInt(int value, int min, int max) {
        if (min > max) throw new IllegalArgumentException("min > max");
        this.min   = min;
        this.max   = max;
        this.value = Math.max(min, Math.min(max, value)); // clamp
    }
}

ClampedInt c = new ClampedInt(150, 0, 100);
System.out.println(c.value()); // 100 (clamped to max)
```

**What this does:** Canonical constructor clamps value to [min, max]. Compact constructor can't do this because it can't pick which fields get which values in the clamping calculation.

> ⚠️ **Pitfall:** Canonical constructor must assign every component field (`this.x = ...`). Omitting any assignment is a compile error — unlike compact constructors where assignment is automatic.

---

## 4. Adding Methods

### What it is

Records can have: instance methods, static methods, static constants (`static final` only). What records **cannot** have: instance fields beyond the declared components, non-final static fields. Records implicitly extend `java.lang.Record` so they cannot extend another class, but they can implement interfaces.

### Visual Diagram

```
record Point(int x, int y) {
    ┌─────────────────────────────────────────┐
    │ Components (auto-generated fields):      │
    │   private final int x                    │
    │   private final int y                    │
    ├─────────────────────────────────────────┤
    │ Can add:                                 │
    │   instance methods     ← YES             │
    │   static methods       ← YES             │
    │   static final fields  ← YES (constants) │
    │   interface impl       ← YES             │
    ├─────────────────────────────────────────┤
    │ Cannot add:                              │
    │   instance fields      ← NO             │
    │   non-final static     ← NO             │
    │   extends SomeClass    ← NO             │
    └─────────────────────────────────────────┘
```

### Code Example 1 — Utility instance methods

```java
record Point(double x, double y) {
    static final Point ORIGIN = new Point(0, 0);

    double distanceTo(Point other) {
        double dx = this.x - other.x;
        double dy = this.y - other.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    Point translate(double dx, double dy) {
        return new Point(x + dx, y + dy); // returns new record — immutable
    }

    double magnitude() {
        return distanceTo(ORIGIN);
    }
}

Point p = new Point(3, 4);
System.out.println(p.magnitude());             // 5.0
System.out.println(p.translate(1, 0));         // Point[x=4.0, y=4.0]
System.out.println(p.distanceTo(Point.ORIGIN)); // 5.0
```

**What this does:** Adds domain logic. `translate` returns a new `Point` — keeps the record immutable. `ORIGIN` is a shared constant.

### Code Example 2 — Static factory methods

```java
record Color(int r, int g, int b) {
    Color {
        if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255) {
            throw new IllegalArgumentException("RGB values must be 0-255");
        }
    }

    static Color fromHex(String hex) {
        int v = Integer.parseInt(hex.replaceFirst("#", ""), 16);
        return new Color((v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF);
    }

    static Color grayscale(int shade) {
        return new Color(shade, shade, shade);
    }

    String toHex() {
        return "#%02X%02X%02X".formatted(r, g, b);
    }
}

Color red  = Color.fromHex("#FF0000");
Color gray = Color.grayscale(128);
System.out.println(red.toHex());   // #FF0000
System.out.println(gray);          // Color[r=128, g=128, b=128]
```

**What this does:** Static factories provide named construction. `toHex()` is a derived view. All transformations return new records.

### Code Example 3 — Override toString and implement interface

```java
interface Serializable { String serialize(); }

record Coordinate(double lat, double lon) implements Serializable {
    @Override
    public String toString() {
        return "(%.4f°, %.4f°)".formatted(lat, lon);
    }

    @Override
    public String serialize() {
        return lat + "," + lon;
    }

    boolean isNorthernHemisphere() { return lat > 0; }
}

Coordinate nyc = new Coordinate(40.7128, -74.0060);
System.out.println(nyc);                        // (40.7128°, -74.0060°)
System.out.println(nyc.serialize());            // 40.7128,-74.006
System.out.println(nyc.isNorthernHemisphere()); // true
```

**What this does:** Overrides auto-generated `toString` for custom format. Implements interface. Instance method encodes domain knowledge.

> ⚠️ **Pitfall:** Adding a non-`static final` field inside a record body is a compile error: `"instance fields are not allowed in records"`. Only the declared components become instance fields.

> ⚠️ **Pitfall:** Overriding `equals()` or `hashCode()` defeats the purpose of a record. If you need custom equality, consider whether a record is the right type.

---

## 5. Records in Pattern Matching [Java 21+]

### What it is

Record patterns extend `instanceof` and `switch` to **deconstruct** a record's components inline. You write `Point(int x, int y)` as a pattern and the compiler extracts `x` and `y` from the record automatically. Nested record patterns deconstruct trees in a single expression.

### Visual Diagram

```
Traditional approach:
  if (obj instanceof Point) {
      Point p = (Point) obj;
      int x = p.x();
      int y = p.y();
      // use x, y
  }

Record pattern (Java 21+):
  if (obj instanceof Point(int x, int y)) {
      // x and y already extracted, typed, in scope
  }

Nested:
  record Line(Point start, Point end) {}
  record Point(int x, int y) {}

  if (shape instanceof Line(Point(int x1, int y1), Point(int x2, int y2))) {
      // All 4 components extracted in one line
  }
                 ^─────────────^  ^─────────────^
                 start deconstruct  end deconstruct
```

### Code Example 1 — instanceof record pattern

```java
record Point(int x, int y) {}

Object obj = new Point(3, 4);

// Old way:
if (obj instanceof Point) {
    Point p = (Point) obj;
    System.out.println("x=" + p.x() + ", y=" + p.y());
}

// New way (Java 16+ for instanceof, 21+ for record patterns):
if (obj instanceof Point(int x, int y)) {
    System.out.println("x=" + x + ", y=" + y); // x=3, y=4
}
```

**What this does:** Combined type-check and deconstruction. `x` and `y` are already `int`, already extracted — no cast, no accessor call.

### Code Example 2 — Switch with record patterns

```java
sealed interface Shape permits Circle, Rectangle, Triangle {}
record Circle(double radius) implements Shape {}
record Rectangle(double width, double height) implements Shape {}
record Triangle(double base, double height) implements Shape {}

double area(Shape shape) {
    return switch (shape) {
        case Circle(double r)             -> Math.PI * r * r;
        case Rectangle(double w, double h) -> w * h;
        case Triangle(double b, double h)  -> 0.5 * b * h;
    };
}

System.out.println(area(new Circle(5)));           // 78.539...
System.out.println(area(new Rectangle(3, 4)));     // 12.0
System.out.println(area(new Triangle(6, 4)));      // 12.0
```

**What this does:** Switch on sealed type with record deconstruction in each case. No explicit casts, no accessor calls. Compiler enforces exhaustiveness over the sealed hierarchy.

### Code Example 3 — Nested record patterns

```java
record Point(int x, int y) {}
record Line(Point start, Point end) {}
record Segment(Line line, String label) {}

Object obj = new Segment(new Line(new Point(0, 0), new Point(3, 4)), "AB");

if (obj instanceof Segment(Line(Point(int x1, int y1), Point(int x2, int y2)), String label)) {
    double length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    System.out.println(label + " length: " + length); // AB length: 5.0
}
```

**What this does:** Three levels of nesting deconstructed in one pattern. Compare to the old way: 6 lines of casts and accessor calls.

### Dry Run — Nested deconstruction

```
obj = Segment(Line(Point(0,0), Point(3,4)), "AB")

Pattern: Segment(Line(Point(int x1, int y1), Point(int x2, int y2)), String label)

Step 1: obj instanceof Segment? YES
Step 2: Deconstruct Segment → line = Line(...), label = "AB"
Step 3: line instanceof Line? YES
Step 4: Deconstruct Line → start = Point(0,0), end = Point(3,4)
Step 5: start instanceof Point? YES
Step 6: Deconstruct Point(0,0) → x1 = 0, y1 = 0
Step 7: end instanceof Point? YES
Step 8: Deconstruct Point(3,4) → x2 = 3, y2 = 4

Variables now in scope: x1=0, y1=0, x2=3, y2=4, label="AB"

length = sqrt((3-0)^2 + (4-0)^2) = sqrt(9+16) = sqrt(25) = 5.0
```

> ⚠️ **Pitfall:** Record patterns require Java 21+ (finalized). Java 16-20 has records but NOT record patterns in switch. Check your target JVM version before using switch deconstruction.

> ⚠️ **Pitfall:** Nested patterns are powerful but hurt readability past 2-3 levels. Extract to local variables if the pattern exceeds one line.

---

## 6. Use Cases

### What it is

Records shine as **value objects and data carriers**. They are wrong when you need inheritance, mutable state, JPA entity lifecycle management, or when frameworks require JavaBean conventions you can't work around.

### Visual Diagram

```
USE records for:                          DON'T use records for:
  ┌─────────────────────────────┐           ┌──────────────────────────────────┐
  │ DTO (API response/request)   │           │ JPA @Entity (needs no-arg ctor,  │
  │ Value object (Money, Range)  │           │   setters, proxy subclassing)    │
  │ Stream groupBy key           │           │ Mutable state (counters, cache)  │
  │ Method return (multi-value)  │           │ Inheritance hierarchy             │
  │ Map key (equals+hashCode ok) │           │ Frameworks needing getX() names  │
  │ Immutable config snapshot    │           │                                  │
  └─────────────────────────────┘           └──────────────────────────────────┘
```

### Code Example 1 — Return multiple values from a method

```java
record MinMax(int min, int max) {}

MinMax findMinMax(int[] arr) {
    int min = arr[0], max = arr[0];
    for (int v : arr) {
        if (v < min) min = v;
        if (v > max) max = v;
    }
    return new MinMax(min, max);
}

MinMax result = findMinMax(new int[]{3, 1, 4, 1, 5, 9, 2, 6});
System.out.println("Min: " + result.min() + ", Max: " + result.max());
// Min: 1, Max: 9
```

**What this does:** Returns two values cleanly. No array packing, no out-parameters, no Pair class. `MinMax` self-documents what the two values mean.

### Code Example 2 — Stream groupBy key (Map.Entry replacement)

```java
record MonthYear(int month, int year) {}

List<LocalDate> dates = List.of(
    LocalDate.of(2024, 1, 5),
    LocalDate.of(2024, 1, 20),
    LocalDate.of(2024, 3, 10),
    LocalDate.of(2025, 1, 7)
);

Map<MonthYear, List<LocalDate>> grouped = dates.stream()
    .collect(Collectors.groupingBy(
        d -> new MonthYear(d.getMonthValue(), d.getYear())
    ));

grouped.forEach((key, vals) ->
    System.out.println(key + " -> " + vals)
);
// MonthYear[month=1, year=2024] -> [2024-01-05, 2024-01-20]
// MonthYear[month=3, year=2024] -> [2024-03-10]
// MonthYear[month=1, year=2025] -> [2025-01-07]
```

**What this does:** Record's auto-generated `equals`/`hashCode` makes it a correct `HashMap` key. `Map.Entry<Integer,Integer>` would be less readable. A plain class would need manual `equals`/`hashCode`.

### Code Example 3 — Immutable value object

```java
record Money(BigDecimal amount, Currency currency) {
    Money {
        Objects.requireNonNull(amount, "amount");
        Objects.requireNonNull(currency, "currency");
        if (amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Amount cannot be negative");
        }
    }

    Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException("Currency mismatch");
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }

    Money multiply(BigDecimal factor) {
        return new Money(this.amount.multiply(factor), this.currency);
    }

    @Override
    public String toString() {
        return amount.toPlainString() + " " + currency.getCurrencyCode();
    }
}

Money price = new Money(new BigDecimal("9.99"), Currency.getInstance("USD"));
Money tax   = price.multiply(new BigDecimal("0.08"));
Money total = price.add(tax);
System.out.println("Total: " + total); // Total: 10.7892 USD
```

**What this does:** Records used as domain value objects. Operations return new records — immutability enforced. Validation in compact constructor guarantees invariants.

### Code Example 4 — When NOT to use: JPA entity

```java
// WRONG — records don't work as JPA entities:
// @Entity
// record Product(Long id, String name, BigDecimal price) {}
// Problems:
//   1. No default no-arg constructor (JPA requires it)
//   2. Final fields (JPA proxies need to subclass and override getters)
//   3. Records are final (JPA proxy can't extend them)
//   4. Accessor names: JPA looks for getName(), not name()

// CORRECT — use a class for JPA entities:
@Entity
class Product {
    @Id Long id;
    String name;
    BigDecimal price;
    protected Product() {}  // JPA needs this
    // getters/setters...
}

// You CAN use a record as a DTO from JPA projections (Spring Data):
record ProductSummary(String name, BigDecimal price) {}
// Spring Data: List<ProductSummary> findAllProjectedBy();  ← works fine
```

**What this does:** Documents the JPA limitation clearly. Shows the hybrid: entity as class, projection as record.

### Dry Run — Stream groupingBy with record key

```
Input dates: [2024-01-05, 2024-01-20, 2024-03-10, 2025-01-07]

groupingBy(d -> new MonthYear(d.getMonthValue(), d.getYear())):

date=2024-01-05 → key=MonthYear[month=1, year=2024] → bucket 1
date=2024-01-20 → key=MonthYear[month=1, year=2024]
  hashCode match? MonthYear(1,2024).hashCode() == MonthYear(1,2024).hashCode() → YES
  equals match?   1==1 && 2024==2024 → YES
  → appended to bucket 1
date=2024-03-10 → key=MonthYear[month=3, year=2024] → new bucket 2
date=2025-01-07 → key=MonthYear[month=1, year=2025] → new bucket 3
  hashCode: MonthYear(1,2025) ≠ MonthYear(1,2024) (year differs)
  → new bucket 3

Result map: {
  MonthYear[month=1, year=2024] → [2024-01-05, 2024-01-20],
  MonthYear[month=3, year=2024] → [2024-03-10],
  MonthYear[month=1, year=2025] → [2025-01-07]
}
```

> ⚠️ **Pitfall:** If a record component is a mutable object (e.g., `List`), `hashCode()` changes when the list changes. Never use a record with mutable components as a Map key without a defensive copy in the canonical constructor.

> ⚠️ **Pitfall:** Records do not support lazy initialization (you can't have a `private final int cachedHash` that's set lazily, because that would be an extra instance field). For heavy computed values, compute eagerly in the constructor or use an external cache.

---

## Summary Cheat-Sheet

```
record Point(int x, int y) {}
  ↳ auto-generates: constructor, x(), y(), equals, hashCode, toString
  ↳ implicitly final, implicitly extends Record
  ↳ accessors: x() NOT getX()

Compact constructor:
  Point { validation here; }
  ↳ no parameter list
  ↳ fields assigned AFTER body automatically
  ↳ reassign params (value = ...) to normalize

Canonical constructor:
  Point(int x, int y) { this.x = ...; this.y = ...; }
  ↳ must assign ALL fields explicitly
  ↳ use when compact can't express the transformation

What you CAN add:
  instance methods    YES
  static methods      YES
  static final fields YES
  interface impls     YES
  override toString   YES

What you CANNOT add:
  instance fields beyond components   NO
  non-final static fields             NO
  extend a class                      NO

Pattern matching [Java 21+]:
  instanceof Point(int x, int y)
  switch { case Point(int x, int y) -> ... }
  nested: Line(Point(int x1,int y1), Point(int x2,int y2))

Use records for:
  DTOs, value objects, multi-return, stream groupBy keys

Avoid records for:
  JPA entities, mutable state, inheritance hierarchies
```
