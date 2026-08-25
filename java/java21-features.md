# Java 21 Features (2023 LTS)

Java 21 is the current Long-Term Support release. Virtual threads, pattern matching, and record patterns all graduate to final. This is the production target for modern Java.

---

## 1. Virtual Threads (Final) [Java 21]

See `22-virtual-threads.md` for full coverage.

```java
import java.util.concurrent.*;

// Create virtual thread
Thread vt = Thread.ofVirtual().name("my-vt").start(() ->
    System.out.println("Running: " + Thread.currentThread().isVirtual()) // true
);
vt.join();

// Quick one-liner
Thread.startVirtualThread(() -> System.out.println("quick virtual")).join();

// Executor (recommended for services)
try (var exec = Executors.newVirtualThreadPerTaskExecutor()) {
    // one virtual thread per task — scales to millions
    for (int i = 0; i < 1_000_000; i++) {
        exec.submit(() -> Thread.sleep(1000));
    }
} // ~1000ms total
```

---

## 2. Pattern Matching for switch (Final) [Java 21]

See `31-pattern-matching.md` for full coverage.

```java
sealed interface Shape permits Circle, Rectangle {}
record Circle(double r) implements Shape {}
record Rectangle(double w, double h) implements Shape {}

// Type patterns, guards, null handling — all standard
static double area(Shape s) {
    return switch (s) {
        case Circle c when c.r() > 0  -> Math.PI * c.r() * c.r();
        case Circle c                  -> 0;
        case Rectangle r               -> r.w() * r.h();
    }; // exhaustive — sealed interface
}

// Object switch with null
static String describe(Object obj) {
    return switch (obj) {
        case null          -> "null";
        case Integer i     -> "int: " + i;
        case String s      -> "str: " + s;
        default            -> "other";
    };
}
```

---

## 3. Record Patterns (Final) [Java 21]

Destructure records in patterns. See `31-pattern-matching.md`.

```java
record Point(int x, int y) {}
record Circle(Point center, double radius) {}

// Nested destructuring
Object obj = new Circle(new Point(1, 2), 5.0);
if (obj instanceof Circle(Point(int cx, int cy), double r)) {
    System.out.println("Center: (" + cx + "," + cy + ") r=" + r);
    // Center: (1,2) r=5.0
}

// In switch
static String format(Object o) {
    return switch (o) {
        case Point(int x, int y) when x == 0 && y == 0 -> "origin";
        case Point(int x, int y)                        -> "(" + x + "," + y + ")";
        case Circle(Point(int cx, int cy), double r)    -> "circle@(" + cx + "," + cy + ")";
        default                                          -> "unknown";
    };
}
```

---

## 4. Sequenced Collections [Java 21]

New interfaces for collections with defined encounter order: `SequencedCollection`, `SequencedSet`, `SequencedMap`.

```java
import java.util.*;

// SequencedCollection — Collection with defined first/last
SequencedCollection<String> list = new ArrayList<>(List.of("A", "B", "C", "D"));

System.out.println(list.getFirst()); // A  [Java 21]
System.out.println(list.getLast());  // D  [Java 21]
list.addFirst("Z");                  // [Z, A, B, C, D]
list.addLast("X");                   // [Z, A, B, C, D, X]
list.removeFirst();                  // removes Z
list.removeLast();                   // removes X
System.out.println(list.reversed()); // [D, C, B, A] — reversed view

// SequencedMap
SequencedMap<String, Integer> map = new LinkedHashMap<>(Map.of("a", 1, "b", 2, "c", 3));
System.out.println(map.firstEntry()); // a=1
System.out.println(map.lastEntry());  // c=3
map.putFirst("z", 0);                 // {z=0, a=1, b=2, c=3}
SequencedMap<String, Integer> rev = map.reversed();

// Hierarchy:
// SequencedCollection ← List, Deque, LinkedHashSet
// SequencedSet        ← SortedSet, LinkedHashSet
// SequencedMap        ← SortedMap, LinkedHashMap
```

---

## 5. Structured Concurrency (Preview) [Java 21]

```java
import java.util.concurrent.*;
import java.util.concurrent.StructuredTaskScope.*;

try (var scope = new ShutdownOnFailure()) {
    Subtask<String> user  = scope.fork(() -> fetchUser());
    Subtask<String> order = scope.fork(() -> fetchOrder());
    scope.join().throwIfFailed();
    System.out.println(user.get() + " | " + order.get());
}

// Racing — first success wins
try (var scope = new ShutdownOnSuccess<String>()) {
    scope.fork(() -> fetchFromPrimary());
    scope.fork(() -> fetchFromBackup());
    scope.join();
    System.out.println(scope.result()); // fastest wins
}
```

---

## 6. Scoped Values (Preview) [Java 21]

Immutable ThreadLocal replacement for virtual threads.

```java
import java.lang.ScopedValue;

static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

void handleRequest(String reqId) {
    ScopedValue.where(REQUEST_ID, reqId).run(() -> {
        processStep1(); // can call REQUEST_ID.get()
        processStep2(); // REQUEST_ID.get() returns reqId
    });
    // binding automatically removed
}

void processStep1() {
    System.out.println("ReqId: " + REQUEST_ID.get());
}
```

---

## 7. String Templates (Preview) [Java 21]

String interpolation with processors (removed in Java 23 — redesign underway).

```java
// NOTE: String templates were previewed in Java 21 but removed in Java 23
// for API redesign. Do not rely on this in production.

// Conceptual syntax (Java 21 preview only):
// String name = "Alice";
// String msg = STR."Hello, \{name}!"; // "Hello, Alice!"
// Use String.formatted() or String.format() instead for now
String name = "Alice";
String msg = "Hello, %s!".formatted(name); // stable alternative
```

---

## 8. Unnamed Patterns and Variables (Preview) [Java 21]

`_` ignores components in patterns and unused variables.

```java
// Unnamed pattern variable _ — ignore what you don't need
record Point(int x, int y) {}
record Circle(Point center, double radius) {}

Object obj = new Circle(new Point(0, 0), 5.0);

// _ ignores center
if (obj instanceof Circle(Point _, double r)) {
    System.out.println("radius: " + r);
}

// In switch
switch (obj) {
    case Circle(Point _, double r) -> System.out.println("r=" + r);
    default -> {}
}

// Unnamed variable in catch (ignore exception object)
try {
    Integer.parseInt("abc");
} catch (NumberFormatException _) {  // _ — we don't need the exception
    System.out.println("Not a number");
}
```

---

## 9. Unnamed Classes and Instance Main Methods (Preview) [Java 21]

Simpler programs without boilerplate class/main declaration.

```java
// Traditional (still works):
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}

// Java 21 preview — unnamed class, simplified main
void main() {              // no class, no public, no static, no String[]
    System.out.println("Hello, World!");
}
// Run: java --enable-preview HelloWorld.java
```

---

## Quick Reference

```
Java 21 final features:
  Virtual threads                Thread.ofVirtual(), newVirtualThreadPerTaskExecutor()
  Pattern matching switch        type patterns, when guards, null case
  Record patterns                case Point(int x, int y) ->
  Sequenced collections          getFirst/getLast/addFirst/reversed on List/Map

Java 21 preview features:
  Structured concurrency         StructuredTaskScope.ShutdownOnFailure/Success
  Scoped values                  ScopedValue.where(SV, val).run(...)
  Unnamed patterns               _ in pattern positions
  Unnamed instance main          void main() {} without class wrapper

Java 21 removed/deprecated:
  String templates removed in Java 23 — use String.formatted()
  
LTS: yes — Java 21 is the current LTS (after Java 17)
     Production recommendation: Java 21 for new projects
```
