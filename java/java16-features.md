# Java 16 Features (2021)

Java 16 finalized records and pattern matching instanceof, and added Stream.toList().

---

## 1. Records (Final) [Java 16]

Concise immutable data classes. See `29-records.md` for full coverage.

```java
// Standard (no preview) in Java 16+
record Point(int x, int y) {}

// Auto-generated: constructor, getters x(), y(), equals, hashCode, toString
Point p = new Point(3, 4);
System.out.println(p.x());  // 3
System.out.println(p.y());  // 4
System.out.println(p);      // Point[x=3, y=4]

// Custom compact constructor
record Range(int min, int max) {
    Range { // compact constructor
        if (min > max) throw new IllegalArgumentException("min > max");
    }
}

// Records implement interfaces
record NamedPoint(String name, int x, int y) implements Comparable<NamedPoint> {
    @Override public int compareTo(NamedPoint o) { return this.name.compareTo(o.name); }
}
```

---

## 2. Pattern Matching for instanceof (Final) [Java 16]

```java
// Standard in Java 16+
Object obj = "hello world";

if (obj instanceof String s && s.length() > 5) {
    System.out.println(s.toUpperCase()); // HELLO WORLD
}

// Use in expressions
static String describe(Object o) {
    if (o instanceof Integer i)        return "int: " + i;
    if (o instanceof String s)         return "str: " + s;
    if (o instanceof double[] doubles) return "double[]: len=" + doubles.length;
    return "other: " + o.getClass().getSimpleName();
}

System.out.println(describe(42));              // int: 42
System.out.println(describe("hi"));           // str: hi
System.out.println(describe(new double[]{1.0})); // double[]: len=1
```

---

## 3. Stream.toList() [Java 16]

```java
import java.util.*;
import java.util.stream.*;

List<String> names = List.of("Charlie", "Alice", "Bob");

// Before Java 16
List<String> sorted1 = names.stream().sorted().collect(Collectors.toList());

// Java 16+ — shorter, returns unmodifiable list
List<String> sorted2 = names.stream().sorted().toList();

// sorted2.add("Dave"); // throws UnsupportedOperationException

System.out.println(sorted2); // [Alice, Bob, Charlie]

// Note: Collectors.toList() returns mutable List
// Stream.toList() returns unmodifiable List
```

---

## 4. Vector API (Incubating) [Java 16]

SIMD (single instruction, multiple data) operations via `java.incubator.vector`. Not stable yet.

```java
// Incubating — API will change
// import jdk.incubator.vector.*;
// VectorSpecies<Float> SPECIES = FloatVector.SPECIES_256; // 256-bit = 8 floats
// FloatVector v1 = FloatVector.fromArray(SPECIES, arr1, 0);
// FloatVector v2 = FloatVector.fromArray(SPECIES, arr2, 0);
// v1.mul(v2).intoArray(result, 0); // 8 multiplications in one instruction
```

---

## 5. Unix-Domain Socket Channels [Java 16]

```java
import java.net.*;
import java.nio.channels.*;
import java.nio.file.*;

// Unix domain sockets — faster for same-host IPC than TCP loopback
Path socketFile = Path.of("/tmp/myapp.sock");

// Server
ServerSocketChannel server = ServerSocketChannel.open(StandardProtocolFamily.UNIX);
server.bind(UnixDomainSocketAddress.of(socketFile));

// Client
SocketChannel client = SocketChannel.open(StandardProtocolFamily.UNIX);
client.connect(UnixDomainSocketAddress.of(socketFile));
```

---

## Quick Reference

```
Java 16 key features:
  Records (final)                 record Point(int x, int y) {}
  Pattern instanceof (final)      obj instanceof String s
  Stream.toList()                 short for .collect(toUnmodifiableList())
  Unix-domain sockets             same-host IPC faster than TCP loopback
  Vector API (incubating)         SIMD operations
  jpackage tool (final)           create native installers
  Foreign Linker API (incubating) access native libraries (→ Panama)
  Warnings for strong encapsulation  --illegal-access removed in Java 17
```
