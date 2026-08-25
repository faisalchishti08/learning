# Java Streams

## Overview

The Stream API (Java 8+) provides a declarative, pipeline-based approach to processing collections of data. Streams are lazy — nothing is computed until a terminal operation is called. They don't store data; they describe transformations on a source.

---

## 1. Stream Concept

### What is it

A stream is a sequence of elements supporting sequential and parallel aggregate operations. It has:
- **A source** (collection, array, generator)
- **Zero or more intermediate operations** (lazy, return Stream)
- **One terminal operation** (eager, triggers processing, returns result)

### Visual Diagram — Pipeline

```
Source → [intermediate ops...] → terminal op → result

List.of(1,2,3,4,5)
    .stream()                    ← source
    .filter(n -> n % 2 == 0)     ← intermediate (lazy, nothing runs yet)
    .map(n -> n * n)             ← intermediate (lazy, nothing runs yet)
    .collect(Collectors.toList()) ← TERMINAL (triggers the whole pipeline)

Data flows element-by-element through the pipeline:
  1 → filter(false) → skip
  2 → filter(true) → map(4) → collect
  3 → filter(false) → skip
  4 → filter(true) → map(16) → collect
  5 → filter(false) → skip
Result: [4, 16]
```

### Example 1 — Basic Stream Pipeline

```java
import java.util.*;
import java.util.stream.*;

public class StreamBasics {
    public static void main(String[] args) {
        List<String> names = List.of("Alice", "Bob", "Charlie", "Dave", "Eve");

        // Pipeline: filter names starting with vowel, uppercase, sort, collect
        List<String> result = names.stream()
            .filter(n -> "AEIOUaeiou".indexOf(n.charAt(0)) >= 0)
            .map(String::toUpperCase)
            .sorted()
            .collect(Collectors.toList());

        System.out.println(result); // [ALICE, EVE]

        // Streams are single-use
        Stream<String> s = names.stream();
        s.forEach(System.out::println);
        // s.count();  // IllegalStateException: stream already consumed!
    }
}
```

**What this does:** Stream is a view over data, not a copy. It processes elements lazily — the filter, map, and sorted operations only execute when `collect` triggers the terminal operation.

---

## 2. Stream Creation

### Example 1 — All Creation Methods

```java
import java.util.*;
import java.util.stream.*;
import java.nio.file.*;

public class StreamCreation {
    public static void main(String[] args) throws Exception {
        // From collection
        Stream<String> fromList = List.of("a", "b", "c").stream();
        Stream<String> parallel = List.of("a", "b", "c").parallelStream();

        // From array
        Stream<String> fromArray = Arrays.stream(new String[]{"x", "y", "z"});
        IntStream fromIntArray = Arrays.stream(new int[]{1, 2, 3});

        // Stream.of
        Stream<Integer> of = Stream.of(1, 2, 3, 4, 5);
        Stream<String> singleElement = Stream.of("only");

        // Stream.iterate — generates infinite sequence
        Stream<Integer> evens = Stream.iterate(0, n -> n + 2);  // 0, 2, 4, 6, ...
        // With predicate [Java 9+]: stops when predicate false
        Stream<Integer> under100 = Stream.iterate(0, n -> n < 100, n -> n + 10);
        System.out.println(under100.collect(Collectors.toList())); // [0,10,20,...,90]

        // Stream.generate — infinite from Supplier
        Stream<Double> randoms = Stream.generate(Math::random);
        randoms.limit(3).forEach(System.out::println);

        // Stream.empty
        Stream<String> empty = Stream.empty();

        // Stream.concat
        Stream<String> combined = Stream.concat(Stream.of("a"), Stream.of("b", "c"));

        // IntStream / LongStream / DoubleStream
        IntStream range = IntStream.range(1, 5);        // 1,2,3,4
        IntStream rangeClosed = IntStream.rangeClosed(1, 5); // 1,2,3,4,5
        LongStream longs = LongStream.range(0, 3);

        // From String [Java 9+]
        IntStream chars = "hello".chars();  // stream of char values

        // From file lines
        // Stream<String> lines = Files.lines(Path.of("file.txt"));
    }
}
```

**What this does:** Multiple ways to create streams. `iterate` and `generate` create infinite streams — always use `limit()` or a predicate to make them finite. `IntStream.range()` is exclusive of the upper bound; `rangeClosed()` is inclusive.

---

## 3. Intermediate Operations

### What is it

Intermediate operations are lazy — they return a new Stream but don't execute until a terminal operation is called. They can be chained.

### Example 1 — filter, map, flatMap

```java
import java.util.*;
import java.util.stream.*;

public class IntermediateOps {
    public static void main(String[] args) {
        List<Integer> nums = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

        // filter — keep elements matching predicate
        List<Integer> evens = nums.stream()
            .filter(n -> n % 2 == 0)
            .collect(Collectors.toList());
        System.out.println(evens); // [2, 4, 6, 8, 10]

        // map — transform each element
        List<String> strings = nums.stream()
            .map(n -> "item_" + n)
            .collect(Collectors.toList());
        System.out.println(strings.subList(0, 3)); // [item_1, item_2, item_3]

        // flatMap — flatten nested structures
        List<List<Integer>> nested = List.of(
            List.of(1, 2, 3),
            List.of(4, 5),
            List.of(6, 7, 8, 9)
        );
        List<Integer> flat = nested.stream()
            .flatMap(Collection::stream)  // each inner List → Stream<Integer>
            .collect(Collectors.toList());
        System.out.println(flat); // [1, 2, 3, 4, 5, 6, 7, 8, 9]

        // flatMap with strings — split and flatten
        List<String> sentences = List.of("hello world", "foo bar baz");
        List<String> words = sentences.stream()
            .flatMap(s -> Arrays.stream(s.split(" ")))
            .distinct()
            .sorted()
            .collect(Collectors.toList());
        System.out.println(words); // [bar, baz, foo, hello, world]
    }
}
```

**What this does:** `filter` is a keep/skip gate. `map` transforms one type to another. `flatMap` is map + flatten — essential for working with nested collections or Optional chains.

### Dry Run — flatMap Pipeline

```
Input: [["a","b"],["c"],["d","e","f"]]
flatMap(Collection::stream):
  ["a","b"] → Stream("a","b")  ─┐
  ["c"]     → Stream("c")      ─┼─► merged Stream: "a","b","c","d","e","f"
  ["d","e","f"] → Stream(...)  ─┘
collect → ["a","b","c","d","e","f"]
```

### Example 2 — distinct, sorted, peek, limit, skip

```java
import java.util.*;
import java.util.stream.*;

public class MoreIntermediateOps {
    public static void main(String[] args) {
        List<Integer> data = Arrays.asList(3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5);

        // distinct — remove duplicates (uses equals/hashCode)
        List<Integer> unique = data.stream()
            .distinct()
            .collect(Collectors.toList());
        System.out.println(unique); // [3, 1, 4, 5, 9, 2, 6]

        // sorted — natural order
        List<Integer> sorted = data.stream()
            .distinct()
            .sorted()
            .collect(Collectors.toList());
        System.out.println(sorted); // [1, 2, 3, 4, 5, 6, 9]

        // limit and skip — pagination
        List<Integer> page2 = data.stream()
            .distinct()
            .sorted()
            .skip(3)   // skip first 3
            .limit(3)  // take next 3
            .collect(Collectors.toList());
        System.out.println(page2); // [4, 5, 6]

        // peek — side effects for debugging (doesn't transform)
        List<Integer> debugged = data.stream()
            .filter(n -> n > 3)
            .peek(n -> System.out.print("after filter: " + n + " "))
            .map(n -> n * 10)
            .peek(n -> System.out.print("after map: " + n + " "))
            .limit(3)
            .collect(Collectors.toList());
        System.out.println("\n" + debugged);

        // takeWhile and dropWhile [Java 9+]
        List<Integer> orderedData = List.of(1, 2, 3, 4, 5, 4, 3, 2, 1);
        List<Integer> taken = orderedData.stream()
            .takeWhile(n -> n < 4)  // takes while condition true, stops at first false
            .collect(Collectors.toList());
        System.out.println(taken); // [1, 2, 3]

        List<Integer> dropped = orderedData.stream()
            .dropWhile(n -> n < 4) // drops while condition true
            .collect(Collectors.toList());
        System.out.println(dropped); // [4, 5, 4, 3, 2, 1]
    }
}
```

**What this does:** `peek` is for debugging pipelines — logs each element without changing the stream. `takeWhile`/`dropWhile` [Java 9+] work on the sequential ordering of elements (different from `filter` which checks all elements).

### Example 3 — mapToInt, mapToLong, mapToDouble

```java
import java.util.*;
import java.util.stream.*;

public class PrimitiveMaps {
    record Employee(String name, double salary) {}

    public static void main(String[] args) {
        List<Employee> employees = List.of(
            new Employee("Alice", 95000),
            new Employee("Bob", 87000),
            new Employee("Charlie", 105000)
        );

        // mapToDouble — avoids boxing
        double avgSalary = employees.stream()
            .mapToDouble(Employee::salary)
            .average()
            .orElse(0);
        System.out.println("Avg: " + avgSalary); // 95666.666...

        double total = employees.stream()
            .mapToDouble(Employee::salary)
            .sum();
        System.out.println("Total: " + total); // 287000.0

        // mapToInt — for counting-style operations
        IntSummaryStatistics stats = employees.stream()
            .mapToInt(e -> (int) e.salary())
            .summaryStatistics();
        System.out.println("Min: " + stats.getMin());   // 87000
        System.out.println("Max: " + stats.getMax());   // 105000
        System.out.println("Sum: " + stats.getSum());   // 287000
        System.out.println("Avg: " + stats.getAverage()); // 95666.666...

        // boxed() — back to Stream<Integer>
        List<Integer> boxed = IntStream.range(1, 6)
            .boxed()
            .collect(Collectors.toList());
        System.out.println(boxed); // [1, 2, 3, 4, 5]
    }
}
```

**What this does:** Primitive streams (`IntStream`, `LongStream`, `DoubleStream`) avoid boxing overhead and provide numeric-specific operations: `sum()`, `average()`, `min()`, `max()`, `summaryStatistics()`.

### mapMulti [Java 16+]

```java
// mapMulti: push-based flatMap — emit 0-n elements per input
List<Integer> nums = List.of(1, 2, 3);
List<Integer> expanded = nums.stream()
    .<Integer>mapMulti((n, consumer) -> {
        for (int i = 0; i < n; i++) consumer.accept(n);
    })
    .collect(Collectors.toList());
System.out.println(expanded); // [1, 2, 2, 3, 3, 3]
```

---

## 4. Terminal Operations

### Example 1 — collect, forEach, count

```java
import java.util.*;
import java.util.stream.*;

public class TerminalOps1 {
    public static void main(String[] args) {
        List<Integer> nums = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

        // collect — most versatile terminal op
        List<Integer> evens = nums.stream()
            .filter(n -> n % 2 == 0)
            .collect(Collectors.toList());

        // toList() [Java 16+] — unmodifiable list, more concise
        List<Integer> evensList = nums.stream()
            .filter(n -> n % 2 == 0)
            .toList();  // unmodifiable

        // forEach — side effects, order not guaranteed in parallel
        nums.stream().limit(3).forEach(n -> System.out.print(n + " ")); // 1 2 3
        System.out.println();

        // count
        long count = nums.stream().filter(n -> n > 5).count();
        System.out.println("Count > 5: " + count); // 5

        // min / max
        Optional<Integer> min = nums.stream().min(Comparator.naturalOrder());
        Optional<Integer> max = nums.stream().max(Comparator.naturalOrder());
        System.out.println(min.get() + " " + max.get()); // 1 10

        // toArray
        Object[] arr = nums.stream().filter(n -> n < 4).toArray();
        Integer[] typedArr = nums.stream().filter(n -> n < 4).toArray(Integer[]::new);
        System.out.println(Arrays.toString(typedArr)); // [1, 2, 3]
    }
}
```

**What this does:** Terminal operations consume the stream. `toList()` [Java 16+] returns an unmodifiable list more concisely than `collect(Collectors.toList())`. `min`/`max` return `Optional` because the stream might be empty.

### Example 2 — reduce, findFirst, findAny, match

```java
import java.util.*;
import java.util.stream.*;

public class TerminalOps2 {
    public static void main(String[] args) {
        List<Integer> nums = List.of(1, 2, 3, 4, 5);

        // reduce — fold operation
        int sum = nums.stream().reduce(0, Integer::sum);       // 15
        int product = nums.stream().reduce(1, (a, b) -> a * b); // 120
        System.out.println("Sum: " + sum + " Product: " + product);

        // reduce without identity returns Optional (may be empty stream)
        Optional<Integer> max = nums.stream().reduce(Integer::max);
        System.out.println("Max: " + max.get()); // 5

        // findFirst — returns first element in encounter order
        Optional<Integer> first = nums.stream()
            .filter(n -> n > 3)
            .findFirst();
        System.out.println("First > 3: " + first.get()); // 4

        // findAny — any element (faster in parallel streams)
        Optional<Integer> any = nums.parallelStream()
            .filter(n -> n > 3)
            .findAny(); // could be 4 or 5
        System.out.println("Any > 3: " + any.isPresent()); // true

        // Match operations (short-circuit)
        System.out.println(nums.stream().anyMatch(n -> n > 4));  // true
        System.out.println(nums.stream().allMatch(n -> n > 0));  // true
        System.out.println(nums.stream().noneMatch(n -> n > 10)); // true
        System.out.println(nums.stream().anyMatch(n -> n > 10)); // false
    }
}
```

**What this does:** `reduce` is the general fold — takes identity + combining function. Match operations short-circuit: `anyMatch` stops at first true, `allMatch` stops at first false.

### Dry Run — reduce(0, Integer::sum)

```
Stream: 1, 2, 3, 4, 5
reduce(0, Integer::sum):
  accumulator = 0 (identity)
  
  Step 1: accumulator = sum(0, 1) = 1
  Step 2: accumulator = sum(1, 2) = 3
  Step 3: accumulator = sum(3, 3) = 6
  Step 4: accumulator = sum(6, 4) = 10
  Step 5: accumulator = sum(10, 5) = 15
  
Result: 15
```

---

## 5. Collectors

### Example 1 — toList, toSet, toMap

```java
import java.util.*;
import java.util.stream.*;
import java.util.function.*;

public class CollectorsBasic {
    record Person(String name, String city, int age) {}

    public static void main(String[] args) {
        List<Person> people = List.of(
            new Person("Alice", "NYC", 30),
            new Person("Bob", "LA", 25),
            new Person("Charlie", "NYC", 35),
            new Person("Dave", "LA", 28)
        );

        // toList
        List<String> names = people.stream()
            .map(Person::name)
            .collect(Collectors.toList());

        // toSet
        Set<String> cities = people.stream()
            .map(Person::city)
            .collect(Collectors.toSet());
        System.out.println(cities); // [NYC, LA]

        // toMap — key must be unique
        Map<String, Integer> nameToAge = people.stream()
            .collect(Collectors.toMap(Person::name, Person::age));
        System.out.println(nameToAge); // {Alice=30, Bob=25, Charlie=35, Dave=28}

        // toMap with merge function — handle duplicate keys
        Map<String, Integer> cityToTotalAge = people.stream()
            .collect(Collectors.toMap(
                Person::city,
                Person::age,
                Integer::sum  // if same city, sum ages
            ));
        System.out.println(cityToTotalAge); // {NYC=65, LA=53}
    }
}
```

**What this does:** `toMap` without merge function throws `IllegalStateException` on duplicate keys. Always provide a merge function when duplicate keys are possible.

### Example 2 — groupingBy and partitioningBy

```java
import java.util.*;
import java.util.stream.*;

public class CollectorsGrouping {
    record Person(String name, String city, int age) {}

    public static void main(String[] args) {
        List<Person> people = List.of(
            new Person("Alice", "NYC", 30),
            new Person("Bob", "LA", 25),
            new Person("Charlie", "NYC", 35),
            new Person("Dave", "LA", 28),
            new Person("Eve", "NYC", 22)
        );

        // groupingBy — group by classifier into Map<K, List<V>>
        Map<String, List<Person>> byCity = people.stream()
            .collect(Collectors.groupingBy(Person::city));
        System.out.println(byCity.get("NYC").stream().map(Person::name).toList());
        // [Alice, Charlie, Eve]

        // groupingBy with downstream collector
        Map<String, Long> countByCity = people.stream()
            .collect(Collectors.groupingBy(Person::city, Collectors.counting()));
        System.out.println(countByCity); // {NYC=3, LA=2}

        Map<String, Double> avgAgeByCity = people.stream()
            .collect(Collectors.groupingBy(
                Person::city,
                Collectors.averagingInt(Person::age)
            ));
        System.out.println(avgAgeByCity); // {NYC=29.0, LA=26.5}

        // partitioningBy — two groups: true and false
        Map<Boolean, List<Person>> partition = people.stream()
            .collect(Collectors.partitioningBy(p -> p.age() >= 30));
        System.out.println("30+: " + partition.get(true).stream().map(Person::name).toList());
        // 30+: [Alice, Charlie]
        System.out.println("<30: " + partition.get(false).stream().map(Person::name).toList());
        // <30: [Bob, Dave, Eve]
    }
}
```

**What this does:** `groupingBy` creates a `Map<K, List<V>>` by default. Use a downstream collector to aggregate the groups further. `partitioningBy` is a special case of groupingBy with exactly two groups: true and false.

### Example 3 — joining, counting, summarizing, teeing

```java
import java.util.*;
import java.util.stream.*;

public class CollectorsAdvanced {
    public static void main(String[] args) {
        List<String> names = List.of("Alice", "Bob", "Charlie", "Dave");

        // joining
        System.out.println(names.stream().collect(Collectors.joining()));
        // AliceBobCharlieDave

        System.out.println(names.stream().collect(Collectors.joining(", ")));
        // Alice, Bob, Charlie, Dave

        System.out.println(names.stream().collect(Collectors.joining(", ", "[", "]")));
        // [Alice, Bob, Charlie, Dave]

        // counting
        long count = names.stream().collect(Collectors.counting());
        System.out.println(count); // 4

        // summingInt
        List<Integer> nums = List.of(1, 2, 3, 4, 5);
        int sum = nums.stream().collect(Collectors.summingInt(n -> n));
        System.out.println(sum); // 15

        // summarizingInt — all stats at once
        IntSummaryStatistics stats = nums.stream()
            .collect(Collectors.summarizingInt(n -> n));
        System.out.println(stats); // IntSummaryStatistics{count=5,sum=15,min=1,avg=3.0,max=5}

        // teeing [Java 12+] — collect into two downstream collectors, then merge
        List<Integer> numbers = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
        Map.Entry<Long, Optional<Integer>> result = numbers.stream()
            .collect(Collectors.teeing(
                Collectors.counting(),           // first: count all
                Collectors.maxBy(Comparator.naturalOrder()), // second: find max
                Map::entry                        // merge: create entry
            ));
        System.out.println("Count: " + result.getKey() + " Max: " + result.getValue().get());
        // Count: 10 Max: 10

        // mapping — transform then collect
        List<String> nameParts = List.of("alice smith", "bob jones", "charlie brown");
        List<String> firstNames = nameParts.stream()
            .collect(Collectors.mapping(
                s -> s.split(" ")[0],
                Collectors.toList()
            ));
        System.out.println(firstNames); // [alice, bob, charlie]

        // collectingAndThen — collect then apply finisher
        List<String> unmodifiable = names.stream()
            .collect(Collectors.collectingAndThen(
                Collectors.toList(),
                Collections::unmodifiableList
            ));
    }
}
```

**What this does:** `joining` is the idiomatic way to build delimited strings from streams. `teeing` [Java 12+] lets you run two collectors in parallel over the same stream. `collectingAndThen` applies a post-processing function after collection.

---

## 6. Parallel Streams

### What is it

Parallel streams split the data across multiple threads using the Fork/Join framework. They can speed up CPU-bound operations on large datasets but have caveats.

### Visual Diagram — Parallel vs Sequential

```
Sequential:
  [1,2,3,4,5,6,7,8] → filter → map → collect

Parallel (4 cores):
  [1,2]             → filter → map ──┐
  [3,4]             → filter → map ──┼─► merge ──► collect
  [5,6]             → filter → map ──┤
  [7,8]             → filter → map ──┘
  
Uses ForkJoinPool.commonPool() by default (cores - 1 threads)
```

### Example 1 — Parallel Stream Usage

```java
import java.util.*;
import java.util.stream.*;

public class ParallelStreams {
    public static void main(String[] args) {
        List<Integer> bigList = IntStream.rangeClosed(1, 1_000_000)
            .boxed()
            .collect(Collectors.toList());

        // Sequential
        long t1 = System.currentTimeMillis();
        long sumSeq = bigList.stream()
            .mapToLong(n -> n * n)
            .sum();
        System.out.println("Sequential: " + (System.currentTimeMillis() - t1) + "ms");

        // Parallel
        long t2 = System.currentTimeMillis();
        long sumPar = bigList.parallelStream()
            .mapToLong(n -> n * n)
            .sum();
        System.out.println("Parallel: " + (System.currentTimeMillis() - t2) + "ms");

        System.out.println("Results match: " + (sumSeq == sumPar)); // true

        // Can switch between sequential and parallel
        Stream<Integer> stream = bigList.stream().parallel(); // parallel
        Stream<Integer> seq = stream.sequential();            // back to sequential

        // Order is NOT guaranteed in parallel:
        bigList.parallelStream()
            .limit(5)
            .forEachOrdered(System.out::print); // forEachOrdered preserves order
        System.out.println();
    }
}
```

**What this does:** `parallelStream()` divides work across available CPU cores. `forEachOrdered` maintains encounter order even in parallel. The speedup depends on dataset size and operation complexity.

### When to Use / When NOT to Use Parallel

```
USE parallel when:
  ✓ Data > ~10,000 elements
  ✓ CPU-bound operations (computation, not IO)
  ✓ No shared mutable state
  ✓ Order doesn't matter (or you use forEachOrdered)
  ✓ Operations are stateless (no side effects)

AVOID parallel when:
  ✗ IO-bound (network calls, DB queries — use async/virtual threads)
  ✗ Small datasets (overhead > benefit)
  ✗ Ordered sources with stateful ops (sorted, distinct affect performance)
  ✗ Collectors with state (groupingBy works, but custom stateful collectors don't)
  ✗ UI thread or environments with restricted thread pools
```

> ⚠️ **Pitfall:** `parallelStream().forEach(list::add)` on a non-thread-safe list causes a race condition. Use `collect(toList())` instead.

---

## 7. Stream Pipeline Internals

### Short-Circuit Operations

```java
import java.util.stream.*;

public class ShortCircuit {
    public static void main(String[] args) {
        // findFirst stops as soon as first match found
        long count = Stream.iterate(1, n -> n + 1)  // infinite stream
            .peek(n -> System.out.print(n + " "))   // shows when elements processed
            .filter(n -> n % 7 == 0)
            .findFirst()  // short-circuit: stops after finding 7
            .get();
        System.out.println("\nFound: " + count); // 1 2 3 4 5 6 7 → Found: 7

        // anyMatch short-circuits on first true
        boolean hasNegative = Stream.of(1, 2, -3, 4, 5)
            .peek(n -> System.out.print(n + " "))
            .anyMatch(n -> n < 0);
        // prints: 1 2 -3 (stops at -3)
        System.out.println("\nHas negative: " + hasNegative);
    }
}
```

**What this does:** Short-circuit terminal operations stop processing as soon as the answer is known. This makes `findFirst()`, `anyMatch()`, and `limit()` efficient even on infinite streams.

### Stream Characteristics

```
ORDERED:    elements have defined encounter order (List-backed streams)
DISTINCT:   all elements are unique (Set.stream() is DISTINCT)
SORTED:     elements are sorted (TreeSet.stream() is SORTED)
SIZED:      known size (collection.stream() is SIZED)
SUBSIZED:   known subsizes after splitting (for parallelism)
NONNULL:    no null elements
IMMUTABLE:  source can't be modified during iteration
CONCURRENT: source can be modified during iteration
```

---

## 8. Optional with Streams [Java 9+]

```java
import java.util.*;
import java.util.stream.*;

public class OptionalStream {
    public static void main(String[] args) {
        // Optional.stream() — 0 or 1 element stream
        Optional<String> present = Optional.of("hello");
        Optional<String> empty = Optional.empty();

        // Use in flatMap to filter out empties
        List<Optional<String>> optionals = List.of(
            Optional.of("Alice"),
            Optional.empty(),
            Optional.of("Bob"),
            Optional.empty(),
            Optional.of("Charlie")
        );

        List<String> names = optionals.stream()
            .flatMap(Optional::stream)  // empties produce no elements
            .collect(Collectors.toList());
        System.out.println(names); // [Alice, Bob, Charlie]
    }
}
```

---

## Quick Reference

```
Creation:
  collection.stream()              from collection
  Arrays.stream(arr)               from array
  Stream.of(a, b, c)               varargs
  Stream.iterate(seed, fn)         infinite sequence
  Stream.generate(supplier)        infinite, stateless
  IntStream.range(0, n)            0..n-1
  IntStream.rangeClosed(1, n)      1..n

Intermediate (lazy):
  filter(Predicate)     keep matching
  map(Function)         transform
  flatMap(Function)     transform + flatten
  distinct()            remove duplicates
  sorted()              natural order
  sorted(Comparator)    custom order
  peek(Consumer)        debug side effects
  limit(n)              first n
  skip(n)               skip first n
  mapToInt/Long/Double  primitive stream (avoid boxing)
  takeWhile(pred)       [9+] while predicate true
  dropWhile(pred)       [9+] drop while predicate true

Terminal (eager):
  collect(Collector)    accumulate
  toList()              [16+] unmodifiable list
  forEach(Consumer)     side effects
  count()               number of elements
  min/max(Cmp)          Optional min/max
  reduce(identity, BinOp) fold
  findFirst/Any()       Optional first/any
  anyMatch/allMatch/noneMatch  boolean, short-circuit
  toArray()             Object[] or typed[]

Key Collectors:
  toList(), toSet(), toUnmodifiableList()
  toMap(kFn, vFn), toMap(kFn, vFn, mergeFn)
  groupingBy(fn), groupingBy(fn, downstream)
  partitioningBy(pred)
  joining(), joining(delim), joining(delim,pre,suf)
  counting(), summingInt/Long/Double(fn)
  averagingInt/Long/Double(fn)
  summarizingInt(fn) → IntSummaryStatistics
  mapping(fn, collector)
  collectingAndThen(collector, finisher)
  teeing(c1, c2, merger) [12+]
```
