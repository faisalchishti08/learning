# Java 15 Features (2020)

Java 15 finalized text blocks and sealed classes (preview), and continued records/patterns previews.

---

## 1. Text Blocks (Final) [Java 15]

Multi-line strings are now standard. See `java13-features.md` for full details.

```java
// Standard (no preview flag needed in Java 15+)
String json = """
        {
            "name": "Alice",
            "age": 30
        }
        """;

// New methods added in Java 15
String html = """
        <html>
            <body>%s</body>
        </html>
        """.formatted("<h1>Hello</h1>"); // .formatted() = String.format() on the text block

// stripIndent() — remove common leading whitespace
String code = "    line1\n    line2\n    line3";
System.out.println(code.stripIndent());
// line1
// line2
// line3

// translateEscapes() — process escape sequences in a string
String raw = "first\\nsecond";         // raw: "first\nsecond" (backslash-n literal)
System.out.println(raw.translateEscapes()); // first
                                            // second
```

---

## 2. Sealed Classes (Preview) [Java 15]

Finalized in Java 17. See `30-sealed-classes.md` for full coverage.

```java
// Preview Java 15 — finalized Java 17
sealed interface Shape permits Circle, Rectangle {}
record Circle(double radius) implements Shape {}
record Rectangle(double w, double h) implements Shape {}
```

---

## 3. Hidden Classes [Java 15]

Classes that cannot be used directly by other code — for frameworks that generate classes dynamically (lambda implementation, reflection proxies).

```java
// Used internally by JVM for lambda implementation
// Not directly visible in application code
// Enables: faster class unloading, no namespace pollution
// Key for: Lambdas, MethodHandles.Lookup.defineHiddenClass()
```

---

## 4. ZGC Production-Ready [Java 15]

ZGC (Z Garbage Collector) — low-latency GC with sub-millisecond pauses — graduates from experimental to production.

```bash
# Now production-ready (was experimental in Java 11)
java -XX:+UseZGC -Xmx16g MyApp

# ZGC features in Java 15:
# - Returns uncommitted memory to OS (since Java 13)
# - NUMA-aware allocation
# - Class unloading (since Java 16)
```

---

## 5. Shenandoah GC Production-Ready [Java 15]

```bash
java -XX:+UseShenandoahGC -Xmx8g MyApp
# Concurrent evacuation, sub-10ms pauses
```

---

## 6. Removed: Nashorn JavaScript Engine

Nashorn (introduced Java 8) is removed. Use GraalVM Polyglot or a third-party library.

---

## Quick Reference

```
Java 15 key features:
  Text blocks (final)        """ standard — no preview needed
  String.formatted()         "text %s".formatted(arg)
  String.stripIndent()       remove common leading whitespace
  String.translateEscapes()  process \n, \t etc. in raw strings
  Sealed classes (preview)   sealed/permits
  Hidden classes             dynamic class generation for frameworks
  ZGC (production)           sub-ms GC pauses
  Shenandoah (production)    concurrent GC
  Removed: Nashorn JS engine use GraalVM polyglot instead
  Removed: Legacy DatagramSocket implementation
```
