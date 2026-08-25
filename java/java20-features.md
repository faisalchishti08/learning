# Java 20 Features (2023)

Java 20 was a refining release — virtual threads and pattern matching moved to 2nd preview, scoped values previewed.

---

## 1. Virtual Threads (2nd Preview) [Java 20]

API stable, closer to Java 21 final. See `22-virtual-threads.md` for full coverage.

```java
// Same API as Java 21 final
Thread.startVirtualThread(() -> System.out.println("virtual"));

try (var exec = java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
    exec.submit(() -> System.out.println("task"));
}
```

---

## 2. Structured Concurrency (2nd Incubator) [Java 20]

Further refinements to StructuredTaskScope.

```java
// Same conceptual API as Java 21 preview
try (var scope = new java.util.concurrent.StructuredTaskScope.ShutdownOnFailure()) {
    var t1 = scope.fork(() -> callService1());
    var t2 = scope.fork(() -> callService2());
    scope.join().throwIfFailed();
    process(t1.get(), t2.get());
}
```

---

## 3. Scoped Values (Incubating) [Java 20]

Immutable per-thread data — safer, more efficient replacement for `ThreadLocal` with virtual threads.

```java
import jdk.incubator.concurrent.*;

public class ScopedValueDemo {
    // ScopedValue — immutable, no setter, thread-local-like
    static final ScopedValue<String> USER = ScopedValue.newInstance();

    static void processRequest(String userId) {
        // Bind value for the duration of the lambda
        ScopedValue.where(USER, userId).run(() -> {
            handleRequest();
        });
        // After .run() exits, USER binding is gone
    }

    static void handleRequest() {
        // Access current value — always present if set in scope
        System.out.println("Handling for: " + USER.get()); // userId
        // No mutation — no .set() method — safe for virtual threads
    }
}
```

**Why better than ThreadLocal for virtual threads:**
- ThreadLocal persists until explicitly removed — memory leak risk with millions of virtual threads
- ScopedValue is automatically removed when scope exits
- Immutable — no accidental mutation

---

## 4. Record Patterns (2nd Preview) [Java 20]

Refinements — nested patterns, generic records.

```java
// 2nd preview
record Pair<A, B>(A first, B second) {}

Object obj = new Pair<>("hello", 42);
if (obj instanceof Pair(String s, Integer n)) {
    System.out.println(s + " " + n); // hello 42
}
```

---

## 5. Pattern Matching for switch (4th Preview) [Java 20]

```java
// 4th preview — finalized in Java 21
// when keyword instead of && for guards
static String classify(Object o) {
    return switch (o) {
        case Integer i when i < 0 -> "negative";
        case Integer i            -> "non-negative";
        case String s             -> "string";
        default                   -> "other";
    };
}
```

---

## Quick Reference

```
Java 20 key features:
  Virtual threads (2nd preview)      API stable, ready for Java 21
  Structured concurrency (2nd incub.) StructuredTaskScope refinements
  Scoped values (incubating)          immutable ThreadLocal replacement for VTs
  Record patterns (2nd preview)       nested, generic record destructuring
  Pattern switch (4th preview)        when keyword, null handling
  Vector API (5th incubating)         SIMD maturation
  Foreign Function + Memory (2nd preview) native interop maturing

Java 20 = setup release for Java 21 LTS.
All major features landed in 21 as final/preview.
```
