# Java 19 Features (2022)

Java 19 previewed virtual threads and structured concurrency — major concurrency features that finalized in Java 21.

---

## 1. Virtual Threads (Preview) [Java 19]

Lightweight JVM-managed threads. Finalized Java 21. See `22-virtual-threads.md` for full coverage.

```java
// Preview in Java 19 — requires --enable-preview
// API identical to Java 21 final version

// Create virtual thread
Thread vt = Thread.ofVirtual().start(() -> System.out.println("virtual!"));
vt.join();

// Virtual thread executor
try (var exec = java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 100_000; i++) {
        exec.submit(() -> Thread.sleep(1000));
    }
}
// ~1000ms — 100K threads, each sleeping 1s
```

---

## 2. Structured Concurrency (Incubating) [Java 19]

`StructuredTaskScope` for scoped virtual thread lifetimes. Preview in Java 21, final Java 23+.

```java
import java.util.concurrent.*;

// Incubating in Java 19
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    var user  = scope.fork(() -> fetchUser(1));
    var order = scope.fork(() -> fetchOrder(1));
    scope.join().throwIfFailed();
    System.out.println(user.get() + " | " + order.get());
}
```

---

## 3. Pattern Matching for switch (3rd Preview) [Java 19]

Refinements — when guards, null handling. Finalized Java 21.

```java
// 3rd preview — stable API, closer to final
static double area(Object shape) {
    record Circle(double r) {}
    record Rect(double w, double h) {}

    return switch (shape) {
        case Circle c when c.r() > 0 -> Math.PI * c.r() * c.r();
        case Circle c -> 0;
        case Rect r   -> r.w() * r.h();
        case null     -> 0;
        default       -> -1;
    };
}
```

---

## 4. Record Patterns (Preview) [Java 19]

Destructure records in switch/instanceof. Finalized Java 21.

```java
// Preview Java 19 — record destructuring
record Point(int x, int y) {}

Object obj = new Point(3, 4);
if (obj instanceof Point(int x, int y)) {  // destructure
    System.out.println("x=" + x + " y=" + y); // x=3 y=4
}
```

---

## 5. Vector API (4th Incubator) [Java 19]

---

## Quick Reference

```
Java 19 key features:
  Virtual threads (preview)          Thread.ofVirtual(), newVirtualThreadPerTaskExecutor()
  Structured concurrency (incubat.)  StructuredTaskScope
  Pattern switch (3rd preview)       when guards, null handling
  Record patterns (preview)          case Point(int x, int y) ->
  Vector API (4th incubat.)          SIMD
  Foreign Function + Memory (preview) stable enough to preview
  
Notable: Java 19 is the first preview of virtual threads —
  the biggest Java concurrency feature since java.util.concurrent in Java 5.
```
