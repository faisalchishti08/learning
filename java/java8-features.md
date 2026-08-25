# Java 8 Features (2014)

Java 8 was transformational — lambdas and streams brought functional programming to Java. Still the most widely-used Java version as of 2024.

---

## 1. Lambdas

Anonymous functions implementing functional interfaces.

```java
import java.util.*;
import java.util.function.*;

// Old: anonymous inner class
Runnable r1 = new Runnable() { public void run() { System.out.println("hi"); } };

// Java 8: lambda
Runnable r2 = () -> System.out.println("hi");

// With parameters
Comparator<String> byLen = (a, b) -> a.length() - b.length();

List<String> names = new ArrayList<>(List.of("Charlie", "Alice", "Bob"));
names.sort(byLen);
System.out.println(names); // [Bob, Alice, Charlie]

// Functional interfaces
Predicate<Integer> isEven    = n -> n % 2 == 0;
Function<String, Integer> len = String::length;
Consumer<String> print       = System.out::println;
Supplier<List<String>> empty = ArrayList::new;

System.out.println(isEven.test(4));     // true
System.out.println(len.apply("hello")); // 5
print.accept("hello");                  // hello
```

See `13-lambdas.md` for full coverage.

---

## 2. Streams API

Declarative processing of collections — filter, map, reduce.

```java
import java.util.*;
import java.util.stream.*;

List<String> names = List.of("Alice", "Bob", "Charlie", "Ann", "David");

// Pipeline: source → intermediate ops → terminal
List<String> result = names.stream()
    .filter(n -> n.startsWith("A"))    // intermediate
    .map(String::toUpperCase)           // intermediate
    .sorted()                           // intermediate
    .collect(Collectors.toList());      // terminal

System.out.println(result); // [ALICE, ANN]

// Reduce
int total = IntStream.rangeClosed(1, 100).sum(); // 5050

// Collect to map
Map<Integer, List<String>> byLength = names.stream()
    .collect(Collectors.groupingBy(String::length));
System.out.println(byLength);
// {3=[Bob, Ann], 5=[Alice, David], 7=[Charlie]}
```

See `14-streams.md` for full coverage.

---

## 3. Optional

Explicit null-absence representation.

```java
import java.util.*;

Optional<String> opt = Optional.of("hello");
Optional<String> empty = Optional.empty();

System.out.println(opt.isPresent());           // true
System.out.println(opt.map(String::toUpperCase).orElse("none")); // HELLO
System.out.println(empty.orElse("default"));   // default
System.out.println(empty.orElseGet(() -> computeDefault())); // lazy
```

See `15-optional.md` for full coverage.

---

## 4. Default and Static Interface Methods

```java
interface Greeter {
    String greet(String name); // abstract — must implement

    // Default method — has implementation, can be overridden
    default String greetFormal(String name) {
        return "Dear " + greet(name);
    }

    // Static factory method on interface
    static Greeter english() { return name -> "Hello, " + name; }
    static Greeter spanish() { return name -> "Hola, " + name; }
}

Greeter g = Greeter.english();
System.out.println(g.greet("Alice"));        // Hello, Alice
System.out.println(g.greetFormal("Alice"));  // Dear Hello, Alice
```

---

## 5. Method References

Shorthand for lambdas that just call a method.

```java
import java.util.*;
import java.util.stream.*;

// Four types:
// 1. Static:     ClassName::staticMethod
// 2. Bound:      instance::method
// 3. Unbound:    ClassName::instanceMethod
// 4. Constructor: ClassName::new

List<String> names = List.of("Charlie", "Alice", "Bob");
names.stream()
    .map(String::toUpperCase)     // type 3: unbound instance method
    .forEach(System.out::println); // type 2: bound instance (System.out)

// Constructor reference
java.util.function.Supplier<ArrayList<String>> maker = ArrayList::new;
ArrayList<String> list = maker.get();
```

---

## 6. Date-Time API (java.time)

Replaced the broken `java.util.Date` / `Calendar`.

```java
import java.time.*;
import java.time.format.*;

LocalDate today = LocalDate.now();
LocalDate birthday = LocalDate.of(1990, Month.JUNE, 15);
System.out.println(Period.between(birthday, today).getYears()); // age

LocalDateTime now = LocalDateTime.now();
ZonedDateTime nyTime = ZonedDateTime.now(ZoneId.of("America/New_York"));

DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
System.out.println(now.format(fmt));

Instant start = Instant.now();
// ... work ...
Duration elapsed = Duration.between(start, Instant.now());
System.out.println(elapsed.toMillis() + "ms");
```

See `16-date-time.md` for full coverage.

---

## 7. CompletableFuture

Async programming with non-blocking chaining.

```java
import java.util.concurrent.*;

CompletableFuture.supplyAsync(() -> "Hello")
    .thenApply(s -> s + " World")
    .thenAccept(System.out::println)  // Hello World
    .join();

// Combine two async calls
CompletableFuture<Integer> price = CompletableFuture.supplyAsync(() -> 100);
CompletableFuture<Integer> tax   = CompletableFuture.supplyAsync(() -> 15);
price.thenCombine(tax, Integer::sum).thenAccept(System.out::println); // 115
```

See `19-completable-future.md` for full coverage.

---

## 8. Nashorn JavaScript Engine

Embedded JavaScript engine (deprecated Java 11, removed Java 15).

```java
// javax.script.ScriptEngine was the API
// Replaced by GraalVM polyglot in modern Java
```

---

## 9. Parallel Arrays

```java
int[] arr = {5, 3, 1, 4, 2};
java.util.Arrays.parallelSort(arr); // parallel merge sort
System.out.println(java.util.Arrays.toString(arr)); // [1, 2, 3, 4, 5]

// parallelPrefix — compute running totals
int[] nums = {1, 2, 3, 4, 5};
java.util.Arrays.parallelPrefix(nums, Integer::sum);
System.out.println(java.util.Arrays.toString(nums)); // [1, 3, 6, 10, 15]
```

---

## Quick Reference

```
Java 8 key features:
  Lambdas              (a, b) -> a + b  anonymous functions
  Streams              filter/map/reduce/collect on collections
  Optional<T>          explicit absent value (no null returns)
  Default methods      interface default void method() { }
  Static interface     interface static T factory() { }
  Method references    String::length, System.out::println
  java.time            LocalDate, ZonedDateTime, Duration, Period
  CompletableFuture    async non-blocking chaining
  Collectors           groupingBy, joining, partitioningBy
  Functional interfaces Predicate, Function, Consumer, Supplier, etc.
  forEach on Iterable  list.forEach(System.out::println)
  Map.forEach          map.forEach((k, v) -> ...)
  Map.getOrDefault     map.getOrDefault(key, defaultValue)
  Map.computeIfAbsent  map.computeIfAbsent(key, k -> ...)
  StringJoiner         new StringJoiner(", ", "[", "]")
  parallelSort         Arrays.parallelSort(arr)
```
