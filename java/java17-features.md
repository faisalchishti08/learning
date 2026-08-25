# Java 17 Features (2021 LTS)

Java 17 is a Long-Term Support release. Key: sealed classes finalized, strong encapsulation enforced, pattern matching for switch (preview).

---

## 1. Sealed Classes (Final) [Java 17]

Restricts which classes can extend/implement. See `30-sealed-classes.md` for full coverage.

```java
// Standard in Java 17+
sealed interface Shape permits Circle, Rectangle, Triangle {}

record Circle(double radius)          implements Shape {}
record Rectangle(double w, double h)  implements Shape {}
final class Triangle implements Shape {
    final double a, b, c;
    Triangle(double a, double b, double c) { this.a = a; this.b = b; this.c = c; }
}

// Pattern matching switch (preview in 17, final in 21)
static double area(Shape s) {
    return switch (s) {
        case Circle c    -> Math.PI * c.radius() * c.radius();
        case Rectangle r -> r.w() * r.h();
        case Triangle t  -> {
            double sp = (t.a + t.b + t.c) / 2;
            yield Math.sqrt(sp * (sp-t.a) * (sp-t.b) * (sp-t.c));
        }
    }; // exhaustive — no default needed
}
```

---

## 2. Strong Encapsulation of JDK Internals

`--illegal-access` flag removed. Accessing internal JDK packages (`sun.*`, `com.sun.*`) requires explicit `--add-opens`.

```bash
# Old way (Java 9-16): --illegal-access=permit  (deprecated, now removed)
# Java 17: illegal access throws InaccessibleObjectException

# If a framework needs access (e.g., Spring, Hibernate):
java --add-opens java.base/java.lang=ALL-UNNAMED \
     --add-opens java.base/java.util=ALL-UNNAMED \
     -jar myapp.jar

# Or in module-info.java:
opens com.myapp.model to org.hibernate.orm.core;
```

---

## 3. Pattern Matching for switch (Preview) [Java 17]

Type patterns in switch. Finalized Java 21.

```java
// Preview — requires --enable-preview in Java 17
static String format(Object obj) {
    return switch (obj) {
        case Integer i -> "int: " + i;
        case Long l    -> "long: " + l;
        case String s  -> "str: " + s;
        case null      -> "null";
        default        -> "other: " + obj.getClass().getSimpleName();
    };
}
```

---

## 4. Restore Always-Strict Floating-Point Semantics

`strictfp` modifier is now the default everywhere. Floating-point operations are always IEEE 754 strict. `strictfp` keyword still valid but redundant.

---

## 5. Enhanced Pseudo-Random Number Generators [Java 17]

New `java.util.random` package with `RandomGenerator` interface.

```java
import java.util.random.*;

// New interface — switchable algorithm
RandomGenerator rng = RandomGeneratorFactory.of("Xoshiro256PlusPlus").create();
System.out.println(rng.nextInt(100)); // 0-99

// LegacyAlgorithm for old Random/ThreadLocalRandom
RandomGenerator legacy = RandomGeneratorFactory.of("Random").create();

// Splittable random (for parallel streams)
SplittableRandom sr = new SplittableRandom();
int[] randoms = sr.ints(10, 0, 100).toArray();

// List of algorithms
RandomGeneratorFactory.all()
    .map(RandomGeneratorFactory::name)
    .forEach(System.out::println);
```

---

## Quick Reference

```
Java 17 key features (LTS):
  Sealed classes (final)          sealed/permits/non-sealed
  Strong encapsulation (final)    --illegal-access removed
  Pattern matching switch (prev)  type patterns in switch
  Enhanced PRNG                   RandomGenerator interface, pluggable algorithms
  Strict floating-point default   strictfp is now always-on
  Foreign Function API (incubat.) access native code (→ finalized Java 22)
  Vector API 2nd incubator        SIMD
  macOS AArch64 support           Apple Silicon native support
  Deprecate Security Manager      removed in Java 17 (was no-op since Java 15)
  Removed: Applet API (deprecated since Java 9)
  Removed: RMI Activation

LTS: yes — Java 17 is widely adopted as replacement for Java 11 LTS
```
