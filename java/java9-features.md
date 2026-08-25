# Java 9 Features (2017)

Java 9 introduced the Module System (JPMS), collection factory methods, and important API improvements.

---

## 1. Module System (JPMS)

See `28-modules.md` for full coverage.

```java
// module-info.java
module com.myapp {
    requires java.sql;
    exports com.myapp.api;
    opens com.myapp.model to com.framework;
}
```

---

## 2. Collection Factory Methods

Create immutable collections concisely.

```java
// Before Java 9
List<String> list = Collections.unmodifiableList(new ArrayList<>(Arrays.asList("a", "b")));

// Java 9+ — concise, null-hostile, immutable
List<String> list2 = List.of("Alice", "Bob", "Charlie");
Set<Integer> set   = Set.of(1, 2, 3);
Map<String, Integer> map = Map.of("a", 1, "b", 2, "c", 3);
Map<String, Integer> map2 = Map.ofEntries(
    Map.entry("longKey1", 1),
    Map.entry("longKey2", 2)
);

// Attempt to modify → UnsupportedOperationException
// list2.add("Dave"); // throws!
// set.remove(1);     // throws!

// List.copyOf, Set.copyOf, Map.copyOf [Java 10]
List<String> copy = List.copyOf(existingList);
```

---

## 3. Stream Improvements

New stream methods: `takeWhile`, `dropWhile`, `ofNullable`, `iterate` with predicate.

```java
import java.util.stream.*;
import java.util.*;

// takeWhile — take while predicate true (stop at first false)
List<Integer> nums = List.of(1, 2, 3, 4, 5, 1, 2);
List<Integer> taken = nums.stream()
    .takeWhile(n -> n < 4)
    .collect(Collectors.toList());
System.out.println(taken); // [1, 2, 3]  ← stops at 4

// dropWhile — drop while predicate true, then take rest
List<Integer> dropped = nums.stream()
    .dropWhile(n -> n < 4)
    .collect(Collectors.toList());
System.out.println(dropped); // [4, 5, 1, 2]

// Stream.ofNullable — empty stream for null
Stream.ofNullable(null).count();   // 0 (no NPE)
Stream.ofNullable("hi").count();   // 1

// iterate with predicate (like a for loop)
Stream.iterate(0, n -> n < 10, n -> n + 2)
    .forEach(System.out::print); // 02468
```

---

## 4. Optional Improvements

`ifPresentOrElse`, `or`, `stream`.

```java
import java.util.*;

Optional<String> opt = Optional.of("hello");
Optional<String> empty = Optional.empty();

// ifPresentOrElse — handle both cases
opt.ifPresentOrElse(
    s -> System.out.println("Got: " + s), // Got: hello
    () -> System.out.println("Empty")
);

// or — provide alternative Optional (lazy)
Optional<String> result = empty.or(() -> Optional.of("fallback"));
System.out.println(result.get()); // fallback

// stream — convert Optional to Stream (0 or 1 element)
long count = opt.stream().count(); // 1
long emptyCount = empty.stream().count(); // 0

// Useful for flatMap in streams
List<Optional<String>> opts = List.of(Optional.of("a"), Optional.empty(), Optional.of("b"));
List<String> values = opts.stream()
    .flatMap(Optional::stream) // unwrap non-empty optionals
    .collect(Collectors.toList());
System.out.println(values); // [a, b]
```

---

## 5. Private Interface Methods

```java
interface Validator<T> {
    boolean validate(T value);

    default boolean validateAll(java.util.List<T> items) {
        return items.stream().allMatch(this::validateNonNull);
    }

    default boolean validateAny(java.util.List<T> items) {
        return items.stream().anyMatch(this::validateNonNull);
    }

    // Private helper — shared by default methods, not exposed to implementors
    private boolean validateNonNull(T item) {
        return item != null && validate(item);
    }
}

Validator<String> notEmpty = s -> !s.isEmpty();
System.out.println(notEmpty.validateAll(List.of("a", "b", "c"))); // true
```

---

## 6. Process API Improvements

```java
// ProcessHandle — inspect and manage OS processes
ProcessHandle self = ProcessHandle.current();
System.out.println("PID: " + self.pid());
System.out.println("Info: " + self.info().command());

// List all processes
ProcessHandle.allProcesses()
    .filter(p -> p.info().command().isPresent())
    .limit(5)
    .forEach(p -> System.out.println(p.pid() + " " + p.info().command().get()));
```

---

## 7. CompletableFuture Improvements

`orTimeout`, `completeOnTimeout`, `failedFuture`, `completedStage`.

```java
import java.util.concurrent.*;

// orTimeout [Java 9] — fail with TimeoutException if too slow
CompletableFuture.supplyAsync(() -> {
    try { Thread.sleep(5000); } catch (InterruptedException e) {}
    return "slow";
}).orTimeout(200, TimeUnit.MILLISECONDS); // throws TimeoutException

// completeOnTimeout [Java 9] — return default if too slow
CompletableFuture<String> cf = CompletableFuture
    .supplyAsync(() -> { try { Thread.sleep(5000); } catch (InterruptedException e) {} return "slow"; })
    .completeOnTimeout("default", 200, TimeUnit.MILLISECONDS);
System.out.println(cf.get()); // "default"

// failedFuture [Java 9]
CompletableFuture<String> failed = CompletableFuture.failedFuture(new RuntimeException("fail"));
```

---

## 8. Reactive Streams — Flow API

`java.util.concurrent.Flow` provides the standard interfaces for reactive programming (Publisher, Subscriber, Subscription, Processor). Foundation for reactive frameworks (Reactor, RxJava).

```java
import java.util.concurrent.*;

// Interfaces only — no implementation in JDK
// Flow.Publisher<T>    — produces items
// Flow.Subscriber<T>   — consumes items
// Flow.Subscription    — link between publisher and subscriber
// Flow.Processor<T,R>  — both Publisher and Subscriber

// Use with Reactor or RxJava for implementations
```

---

## Quick Reference

```
Java 9 key features:
  JPMS (modules)         module-info.java, exports/requires
  List/Set/Map.of()      immutable factory methods
  takeWhile/dropWhile    ordered stream early termination
  Stream.ofNullable      null-safe stream creation
  Stream.iterate(seed,pred,fn) bounded iterate
  Optional.or            lazy alternative Optional
  Optional.ifPresentOrElse  handle both cases
  Optional.stream        convert to 0-or-1 element stream
  Private interface methods  private helper methods in interfaces
  ProcessHandle          OS process inspection
  orTimeout              CompletableFuture timeout [CF]
  completeOnTimeout      CF default on timeout
  failedFuture           pre-failed CF
  Flow API               reactive streams interfaces
  jshell                 REPL (Read-Eval-Print Loop) for Java
  HTTP/2 Client          incubating (finalized Java 11)
```
