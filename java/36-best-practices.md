# Java Best Practices

## Overview

Collected best practices covering code quality, API design, performance, testing, and common pitfalls. Distilled from Effective Java (Bloch), Java Concurrency in Practice, and production experience.

---

## 1. Object Design

### Immutability First

```java
// PREFER: immutable classes — thread-safe, cacheable, simpler
public final class Money {          // final: no subclassing
    private final long cents;       // final fields
    private final String currency;  // no setters

    public Money(long cents, String currency) {
        if (cents < 0) throw new IllegalArgumentException("cents must be >= 0");
        this.cents = cents;
        this.currency = java.util.Objects.requireNonNull(currency);
    }

    // Return new instance instead of mutating
    public Money add(Money other) {
        if (!this.currency.equals(other.currency))
            throw new IllegalArgumentException("Currency mismatch");
        return new Money(this.cents + other.cents, this.currency);
    }

    @Override public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Money m)) return false;
        return cents == m.cents && currency.equals(m.currency);
    }
    @Override public int hashCode() { return java.util.Objects.hash(cents, currency); }
    @Override public String toString() { return cents / 100 + "." + cents % 100 + " " + currency; }
}
```

**Why:** Immutable objects are inherently thread-safe, can be freely shared/cached, and simplify reasoning. Modern Java: use `record` for pure data holders.

---

### equals/hashCode Contract

```java
// RULES for equals():
// 1. Reflexive:  x.equals(x) == true
// 2. Symmetric:  x.equals(y) == y.equals(x)
// 3. Transitive: x.equals(y) && y.equals(z) → x.equals(z)
// 4. Consistent: multiple calls → same result (if no mutation)
// 5. Null-safe:  x.equals(null) == false (never throw NPE)
//
// hashCode() contract:
// - If x.equals(y), then x.hashCode() == y.hashCode()
// - If !x.equals(y), hashCodes SHOULD differ (not required, but performance)

public class Point {
    private final int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;           // reflexive optimization
        if (!(o instanceof Point p)) return false; // null-safe + type check
        return x == p.x && y == p.y;
    }

    @Override
    public int hashCode() {
        return java.util.Objects.hash(x, y);  // consistent with equals
    }
}
// Or just: record Point(int x, int y) {}  — gets all this for free
```

> ⚠️ **Pitfall:** Override `hashCode` whenever you override `equals`. Objects used as HashMap keys or in HashSet need consistent hashCode. Breaking the contract causes "lost" entries.

---

## 2. API Design

### Minimize Mutability — Return Defensive Copies

```java
import java.util.*;

public class ApiDesign {
    private final List<String> items;

    public ApiDesign(List<String> items) {
        this.items = new ArrayList<>(items); // defensive copy on input
    }

    // Return unmodifiable view — caller can't mutate internal list
    public List<String> getItems() {
        return Collections.unmodifiableList(items); // [Java 9+]: List.copyOf(items)
    }

    // Prefer returning Optional over null [Java 8+]
    public Optional<String> findFirst(String prefix) {
        return items.stream()
            .filter(s -> s.startsWith(prefix))
            .findFirst();
    }

    // Fail fast with Objects.requireNonNull
    public void add(String item) {
        Objects.requireNonNull(item, "item must not be null");
        items.add(item);
    }
}
```

### Prefer Interfaces Over Concrete Types in API

```java
// BAD: exposes implementation detail
ArrayList<String> getNames(); // caller tied to ArrayList

// GOOD: return interface
List<String> getNames();      // can swap to LinkedList, etc.

// GOOD: even better — return view or copy
List<String> getNames() { return List.copyOf(this.names); } // [Java 10+] immutable copy

// In parameters: accept the broadest type
void process(Collection<String> items); // accepts List, Set, any Collection
// not: void process(ArrayList<String> items);
```

---

## 3. Null Handling

```java
import java.util.*;

public class NullHandling {
    // Rule 1: never return null for collections — return empty
    List<String> getItems() {
        return Collections.emptyList(); // NOT null
    }

    // Rule 2: never return null for strings — return ""
    String getName() {
        return ""; // NOT null
    }

    // Rule 3: use Optional for values that may be absent [Java 8+]
    Optional<String> findUser(int id) {
        if (id <= 0) return Optional.empty();
        return Optional.of("User-" + id);
    }

    // Rule 4: Objects.requireNonNull for constructor/method validation
    void setConfig(String host, int port) {
        this.host = Objects.requireNonNull(host, "host must not be null");
        this.port = port;
    }
    private String host; private int port;

    // Rule 5: Objects.requireNonNullElse [Java 9+] for default values
    String display(String name) {
        return Objects.requireNonNullElse(name, "Anonymous");
    }

    // Rule 6: null checks in equals() — always use Objects.equals
    boolean same(String a, String b) {
        return Objects.equals(a, b); // null-safe: (a==null ? b==null : a.equals(b))
    }
}
```

---

## 4. Exception Handling

```java
public class ExceptionBestPractices {
    // Rule 1: use checked exceptions for recoverable conditions
    // use unchecked for programming errors

    // BAD: swallowing exceptions
    static void bad() {
        try { riskyOp(); }
        catch (Exception e) {} // swallowed — caller has no idea what happened
    }

    // BAD: catching Exception/Throwable too broadly
    static void alsoBAd() {
        try { riskyOp(); }
        catch (Exception e) { e.printStackTrace(); } // hides root cause in log noise
    }

    // GOOD: catch specific, rethrow with context
    static void good() throws ProcessingException {
        try { riskyOp(); }
        catch (IOException e) {
            throw new ProcessingException("Failed to process file", e); // wraps cause
        }
    }

    // Rule 2: clean up in finally / try-with-resources
    static void withCleanup() throws Exception {
        try (var resource = openResource()) {
            process(resource);
        } // auto-closes even if exception
    }

    // Rule 3: log at the boundary (once), not at every layer
    static void boundary() {
        try { processAll(); }
        catch (ProcessingException e) {
            // LOG HERE — once, with full context
            System.err.println("Processing failed: " + e.getMessage());
            throw new RuntimeException("Application error", e);
        }
    }

    static class ProcessingException extends Exception {
        ProcessingException(String msg, Throwable cause) { super(msg, cause); }
    }
    static void riskyOp() throws java.io.IOException {}
    static AutoCloseable openResource() { return () -> {}; }
    static void process(AutoCloseable r) {}
    static void processAll() throws ProcessingException {}
}
```

> ⚠️ **Pitfall:** Catching `Exception` or `Throwable` hides bugs. Catch the most specific exception possible. Only catch `Throwable` at top-level application boundaries.

---

## 5. Collections

```java
import java.util.*;

public class CollectionBestPractices {
    // Prefer List.of/Set.of/Map.of [Java 9+] for immutable
    List<String> names = List.of("Alice", "Bob"); // null-hostile, unmodifiable
    Set<Integer> ids   = Set.of(1, 2, 3);
    Map<String, Integer> scores = Map.of("a", 1, "b", 2);

    // Pre-size collections when size is known
    void presize() {
        int n = 1000;
        // HashMap default load factor 0.75 → need capacity = n/0.75+1 to avoid resize
        Map<String, Integer> map = new HashMap<>(n * 4 / 3 + 1);
        List<String> list = new ArrayList<>(n); // avoids resizing
    }

    // Use entrySet() for map iteration — not keySet() + get()
    void iterateMap(Map<String, Integer> map) {
        // BAD: two lookups per entry
        for (String key : map.keySet()) {
            int val = map.get(key); // O(1) but redundant
        }

        // GOOD: one lookup per entry
        for (Map.Entry<String, Integer> e : map.entrySet()) {
            String key = e.getKey();
            int val = e.getValue();
        }
    }

    // Use ArrayDeque instead of Stack
    Deque<String> stack = new ArrayDeque<>(); // NOT new Stack()
    // Stack extends Vector (synchronized) — bad for non-concurrent use
}
```

---

## 6. String Handling

```java
public class StringPractices {
    // Use StringBuilder for string construction in loops
    String buildReport(java.util.List<String> lines) {
        StringBuilder sb = new StringBuilder();
        for (String line : lines) {
            sb.append(line).append('\n');
        }
        return sb.toString();
    }

    // Use String.join or collectors for delimited lists
    String joinNames(java.util.List<String> names) {
        return String.join(", ", names); // "Alice, Bob, Charlie"
    }

    // Use formatted() [Java 15+] or String.format()
    String format(String name, int age) {
        return "Name: %s, Age: %d".formatted(name, age); // [Java 15+]
    }

    // String comparison
    void compare(String a, String b) {
        // NEVER: a == b  (compares references, not content)
        // ALWAYS: a.equals(b)
        // Null-safe: Objects.equals(a, b)

        // case-insensitive
        boolean same = a.equalsIgnoreCase(b);
    }

    // Check blank vs empty [Java 11+]
    void checkString(String s) {
        boolean empty  = s.isEmpty();  // length == 0
        boolean blank  = s.isBlank();  // all whitespace [Java 11+]
        String stripped = s.strip();   // Unicode-aware trim [Java 11+]
    }
}
```

---

## 7. Concurrency

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ConcurrencyBestPractices {
    // Rule 1: prefer high-level concurrency over low-level synchronized
    // BAD:
    private int counter = 0;
    synchronized void badIncrement() { counter++; }

    // GOOD:
    private AtomicInteger atomicCounter = new AtomicInteger(0);
    void goodIncrement() { atomicCounter.incrementAndGet(); }

    // Rule 2: use ExecutorService, not raw Thread
    static void usePools() {
        // BAD: raw thread (no pool, no lifecycle management)
        new Thread(() -> System.out.println("task")).start();

        // GOOD: thread pool
        ExecutorService exec = Executors.newFixedThreadPool(4);
        exec.submit(() -> System.out.println("task"));
        exec.shutdown(); // lifecycle managed
    }

    // Rule 3: always shut down executors
    static void shutdownProperly(ExecutorService exec) throws InterruptedException {
        exec.shutdown(); // stop accepting new tasks
        if (!exec.awaitTermination(30, TimeUnit.SECONDS)) {
            exec.shutdownNow(); // force if needed
        }
    }

    // Rule 4: use ConcurrentHashMap over synchronizedMap
    ConcurrentHashMap<String, Integer> concurrentMap = new ConcurrentHashMap<>();
    // NOT: Collections.synchronizedMap(new HashMap<>())

    // Rule 5: document thread-safety
    // @ThreadSafe, @NotThreadSafe, @GuardedBy
}
```

---

## 8. Performance

```java
public class PerformancePractices {
    // Rule 1: avoid premature optimization — measure first
    // Rule 2: use streams for readability; parallel streams only when proven beneficial

    // Rule 3: avoid boxing in tight loops
    static long sumBoxed(java.util.List<Integer> nums) {
        long sum = 0;
        for (Integer n : nums) sum += n; // auto-unbox per element — OK for small lists
        return sum;
    }

    static long sumPrimitive(int[] nums) {
        long sum = 0;
        for (int n : nums) sum += n; // no boxing
        return sum;
    }

    // Rule 4: reuse StringBuilder
    static String[] buildStrings(int n) {
        StringBuilder sb = new StringBuilder();
        String[] results = new String[n];
        for (int i = 0; i < n; i++) {
            sb.setLength(0); // reset instead of new StringBuilder
            sb.append("item-").append(i);
            results[i] = sb.toString();
        }
        return results;
    }

    // Rule 5: use int[] instead of Integer[] for primitive arrays
    // Rule 6: cache expensive computations (compute-once)
    private static final double LOG2 = Math.log(2); // computed once at class load

    static double log2(double x) { return Math.log(x) / LOG2; }
}
```

---

## 9. Modern Java (Java 8-21) Quick Wins

```java
import java.util.*;
import java.util.stream.*;

public class ModernJava {
    record Person(String name, int age) {}

    public static void main(String[] args) {
        var people = List.of(
            new Person("Alice", 30),
            new Person("Bob", 25),
            new Person("Charlie", 35)
        );

        // Grouping with streams
        Map<Boolean, List<Person>> byAge = people.stream()
            .collect(Collectors.partitioningBy(p -> p.age() >= 30));
        System.out.println(byAge);

        // var for local type inference [Java 10+]
        var names = people.stream()
            .map(Person::name)
            .sorted()
            .toList(); // [Java 16+] — immutable List directly
        System.out.println(names);

        // Text blocks [Java 15+]
        String json = """
                {
                    "name": "Alice",
                    "age": 30
                }
                """;

        // Pattern matching instanceof [Java 16+]
        Object obj = "hello";
        if (obj instanceof String s && s.length() > 3) {
            System.out.println(s.toUpperCase()); // HELLO
        }

        // Switch expressions [Java 14+]
        int day = 3;
        String type = switch (day) {
            case 1, 7 -> "weekend";
            case 2, 3, 4, 5, 6 -> "weekday";
            default -> "unknown";
        };
        System.out.println(type); // weekday
    }
}
```

---

## Quick Reference — Rules

```
Object design:
  Make classes immutable when possible (final class, final fields, no setters)
  Always override hashCode when overriding equals
  Use records for pure data (Java 16+)
  Defensive copy on mutable input/output

API design:
  Return interfaces, not implementations
  Return Optional for absent values, not null
  Return empty collections, not null
  Objects.requireNonNull for validation

Exceptions:
  Catch specific exceptions, not Exception
  Never swallow exceptions
  Wrap with context when rethrowing
  Log at boundary (once), not every layer

Collections:
  List.of/Set.of/Map.of for immutable [Java 9+]
  Pre-size HashMap: new HashMap<>(n * 4/3 + 1)
  entrySet() for map iteration
  ArrayDeque over Stack

Concurrency:
  AtomicXxx over synchronized for single-variable
  ExecutorService over raw threads
  ConcurrentHashMap over synchronizedMap
  Always shut down executors

Strings:
  StringBuilder in loops
  String.join for delimited lists
  .equals() not == for content comparison
  .isBlank() [Java 11+] for whitespace check

Modern Java:
  var for local inference [Java 10+]
  Records for data [Java 16+]
  Text blocks [Java 15+]
  Stream.toList() [Java 16+]
  Pattern matching instanceof [Java 16+]
  Switch expressions [Java 14+]
```
