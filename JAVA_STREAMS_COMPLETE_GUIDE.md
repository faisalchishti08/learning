# Java Streams: The Complete Java SE 26 Guide

> **Target:** Java SE 26  
> **Scope:** Standard JDK `java.util.stream` API and JDK stream sources  
> **Levels:** Basic → Average → Intermediate → Advanced → Expert  
> **Last API reconciliation:** 2026-08-26

This is a standalone learning path, cookbook, and API audit for Java Streams. It covers every public Java SE 26 `java.util.stream` type and method family, the practical JDK APIs that produce streams, meaningful operation combinations, correctness rules, performance boundaries, and extension through collectors, gatherers, and spliterators.

“Complete” means complete API, behavioral-contract, and practical-pattern coverage. It does not mean listing arbitrary permutations such as every possible ordering of `filter`, `map`, and `sorted`; those combinations are unlimited and many are equivalent or invalid. The guide instead teaches the laws that let you derive any valid pipeline.

## How to use this guide

- New to Streams: read Parts I–IV in order, then the Basic and Average recipes.
- Comfortable with pipelines: focus on Parts V, VIII, and X.
- Preparing for advanced interviews or library work: master Parts VI, VII, and IX.
- Looking up an operation: use the [API coverage matrix](#api-coverage-matrix).
- Solving a problem: use the [operation-selection guide](#operation-selection-guide) and [use-case matrix](#use-case-coverage-matrix).

## Contents

1. [Part I — Orientation and mental model](#part-i-orientation-and-mental-model)
2. [Part II — Creating streams](#part-ii-creating-streams)
3. [Part III — Intermediate operations](#part-iii-intermediate-operations)
4. [Part IV — Terminal operations and reductions](#part-iv-terminal-operations-and-reductions)
5. [Part V — Collectors](#part-v-collectors)
6. [Part VI — Gatherers](#part-vi-gatherers)
7. [Part VII — Spliterators and execution mechanics](#part-vii-spliterators-and-execution-mechanics)
8. [Part VIII — Meaningful combinations and recipes](#part-viii-meaningful-combinations-and-recipes)
9. [Part IX — Parallelism, performance, and production safety](#part-ix-parallelism-performance-and-production-safety)
10. [Part X — Failures, testing, debugging, and maintainability](#part-x-failures-testing-debugging-and-maintainability)
11. [Part XI — Practice and quick reference](#part-xi-practice-and-quick-reference)

## Conventions used in examples

- **Level** states the expected reader depth.
- **Result** is exact for deterministic sequential examples. Parallel or unordered examples state only guaranteed invariants.
- **Semantics** calls out laziness, state, ordering, short-circuiting, closing, or parallel constraints that can change correctness.
- **Cost** gives useful asymptotic or allocation guidance, not a promise about a particular JDK implementation.
- Imports normally come from `java.util.*`, `java.util.function.*`, `java.util.stream.*`, `java.math.*`, `java.nio.file.*`, and `java.time.*`.

---

<a id="part-i-orientation-and-mental-model"></a>

# Part I — Orientation and mental model

## Shared example model

The longer examples reuse this compact domain. The records are immutable; the fixture collections are unmodifiable; time and money values are deterministic.

```java
import java.io.*;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.function.*;
import java.util.jar.JarFile;
import java.util.random.RandomGenerator;
import java.util.regex.*;
import java.util.stream.*;

enum Department { ENGINEERING, FINANCE, SALES }
enum TransactionType { CREDIT, DEBIT }

record Address(String city, String country) {}

record Employee(
        int id,
        String name,
        Department department,
        BigDecimal salary,
        Set<String> skills,
        Address address,       // deliberately nullable for null-policy examples
        boolean active) {}

record LineItem(String sku, int quantity, BigDecimal unitPrice) {
    BigDecimal total() {
        return unitPrice.multiply(BigDecimal.valueOf(quantity));
    }
}

record Order(String id, int customerId, List<LineItem> items, Instant createdAt) {}

record Transaction(
        String id,
        String account,
        TransactionType type,
        long minorUnits,
        Instant occurredAt) {}

record Event(String id, String key, String status, Instant occurredAt) {}

record TreeNode<T>(T value, List<TreeNode<T>> children) {
    TreeNode(T value, TreeNode<T>... children) {
        this(value, List.of(children));
    }
}

final class Fixtures {
    static final List<Employee> EMPLOYEES = List.of(
        new Employee(1, "Asha", Department.ENGINEERING,
            new BigDecimal("90000"), Set.of("Java", "SQL"),
            new Address("Pune", "IN"), true),
        new Employee(2, "Ben", Department.FINANCE,
            new BigDecimal("78000"), Set.of("Excel", "SQL"),
            null, true),
        new Employee(3, "Chen", Department.ENGINEERING,
            new BigDecimal("105000"), Set.of("Java", "AWS"),
            new Address("Singapore", "SG"), false),
        new Employee(4, "Diya", Department.SALES,
            new BigDecimal("72000"), Set.of("CRM", "Negotiation"),
            new Address("Mumbai", "IN"), true)
    );

    static final List<Order> ORDERS = List.of(
        new Order("O-1", 10, List.of(
            new LineItem("BOOK", 2, new BigDecimal("12.50")),
            new LineItem("PEN", 3, new BigDecimal("1.20"))),
            Instant.parse("2026-08-20T10:00:00Z")),
        new Order("O-2", 11, List.of(
            new LineItem("BOOK", 1, new BigDecimal("12.50"))),
            Instant.parse("2026-08-21T10:00:00Z"))
    );

    static final List<Transaction> TRANSACTIONS = List.of(
        new Transaction("T-1", "A", TransactionType.CREDIT, 10_000,
            Instant.parse("2026-08-20T09:00:00Z")),
        new Transaction("T-2", "A", TransactionType.DEBIT, 2_500,
            Instant.parse("2026-08-20T10:00:00Z")),
        new Transaction("T-3", "B", TransactionType.CREDIT, 7_000,
            Instant.parse("2026-08-20T11:00:00Z"))
    );

    private Fixtures() {}
}
```

**Explanation:** records supply value-based equality, which matters to `distinct`, sets, grouping keys, and map keys. `BigDecimal` avoids binary floating-point error for money. The one nullable address is intentional: examples must decide whether null means “unknown,” “invalid,” or “discard,” rather than silently guessing.

## Stream, collection, and iterator

A collection owns stored elements. A stream does not store data: it describes a one-time aggregate computation over a source. An iterator exposes external iteration—your code asks for each next element. A stream uses internal iteration—the library drives traversal and may fuse stages, stop early, split work, or omit provably irrelevant stages.

| Property | Collection | Iterator | Stream |
|---|---|---|---|
| Stores elements | Yes | No | No |
| Reusable | Yes | One traversal | One pipeline traversal |
| Access style | Indexed/key/iteration | Pull one value | Declarative aggregate |
| Lazy transformations | Not inherently | Manual | Intermediate operations |
| Parallel decomposition | Not inherently | Usually no | Possible through spliterator |

Streams do not mutate their source merely because `map`, `filter`, or `sorted` is used. Side effects inside lambdas can mutate other state, but doing so usually violates the model and becomes unsafe under optimization or parallel execution.

## Pipeline anatomy and laziness

A pipeline contains:

1. one **source** such as a list, array, generator, file, or spliterator;
2. zero or more **intermediate operations**, which return another stream and are lazy; and
3. one **terminal operation**, which starts traversal and returns a non-stream result or performs a terminal side effect.

### Basic example — laziness and short-circuiting

**Goal:** find the first active employee whose name has at least four characters.

```java
Optional<String> first = Fixtures.EMPLOYEES.stream()       // source
    .filter(Employee::active)                              // lazy intermediate
    .map(Employee::name)                                   // lazy intermediate
    .filter(name -> name.length() >= 4)                    // lazy intermediate
    .findFirst();                                          // terminal, short-circuiting

System.out.println(first.orElse("none"));
```

**Result:** `Asha`.

**Explanation:** calling `filter` and `map` builds stages but visits nothing. `findFirst` pulls elements through the complete fused pipeline. Traversal stops as soon as `Asha` satisfies every stage, so later employees need not be examined.

**Cost:** worst-case `O(n)` time and `O(1)` pipeline state; short-circuiting may inspect fewer than `n` values.

### Why intermediate side effects may disappear

```java
long count = List.of("a", "b", "c").stream()
    .peek(System.out::println)
    .count();
```

Do not require this code to print three values. A JDK may obtain the count directly from a sized source and elide traversal because `peek` cannot affect `count`'s result. `forEach` and `forEachOrdered` explicitly define terminal actions; arbitrary intermediate side effects are not a correctness mechanism.

### Operation classifications

- A **stateless** operation such as `map` handles one element without remembering earlier elements.
- A **stateful** operation such as `sorted` or `distinct` needs information about other elements and may buffer data.
- A **short-circuiting intermediate** such as `limit` can turn an unbounded stream into a finite one.
- A **short-circuiting terminal** such as `anyMatch` may finish without consuming the whole input.

Short-circuiting is necessary but not always sufficient for an infinite pipeline to finish. `Stream.generate(...).sorted().limit(10)` never reaches `limit`, because `sorted` first needs the end of an infinite source.

## Behavioral contracts

Most functions passed into Stream operations must be:

- **non-interfering:** they do not modify the stream source while it is being traversed;
- **stateless:** their result does not depend on mutable state that can change during the pipeline; and
- **non-null:** unless an individual method explicitly permits otherwise.

### Incorrect — source interference

```java
List<String> names = new ArrayList<>(List.of("Asha", "Ben"));
names.stream().forEach(names::add); // unsafe: modifies the source
```

This can throw `ConcurrentModificationException`, loop unexpectedly for a specially designed source, or otherwise behave unpredictably.

### Correct — produce a separate result

```java
List<String> duplicated = names.stream()
    .flatMap(name -> Stream.of(name, name))
    .toList();
```

**Result:** `[Asha, Asha, Ben, Ben]`.

**Explanation:** the source remains unchanged; the pipeline represents the intended one-to-many transformation. `toList()` returns an unmodifiable result.

State captured by a lambda can be just as dangerous:

```java
// Incorrect: order-dependent and data-racing in parallel.
Set<String> seen = new HashSet<>();
List<String> unique = names.parallelStream()
    .filter(seen::add)
    .toList();

// Correct: use the stateful operation whose contract defines uniqueness.
List<String> safe = names.parallelStream().distinct().toList();
```

Use external state only when the terminal operation's purpose is an explicit side effect and the execution/order/thread-safety consequences are accepted.

## Encounter order and characteristics

**Encounter order** is the order in which a stream conceptually presents elements. A `List` and arrays are ordered; a `TreeSet` is sorted and ordered; a `HashSet` generally has no specified encounter order. `sorted()` imposes an order; `unordered()` declares that order is not required but does not shuffle values.

For ordered streams:

- `findFirst`, `limit`, `skip`, `takeWhile`, and `dropWhile` respect the encounter order;
- `forEachOrdered` preserves it even in parallel;
- `distinct` is stable: it retains the first equal element; and
- `sorted` is stable for equal object elements.

For unordered streams, operations have more freedom. That may improve parallel performance, but the program must not rely on which qualifying element or subset is chosen.

A `Spliterator` advertises characteristics such as `ORDERED`, `DISTINCT`, `SORTED`, `SIZED`, `NONNULL`, `IMMUTABLE`, `CONCURRENT`, and `SUBSIZED`. These facts allow optimization and define what a custom source promises. Lying about them can produce wrong answers.

## Single use, closing, and unbounded streams

### Streams are consumable once

```java
Stream<Employee> stream = Fixtures.EMPLOYEES.stream();
long active = stream.filter(Employee::active).count();
// stream.count(); // IllegalStateException: stream already operated upon or closed
```

When repeated traversal is required, keep the reusable source or a stream supplier:

```java
Supplier<Stream<Employee>> employees = Fixtures.EMPLOYEES::stream;
long activeCount = employees.get().filter(Employee::active).count();
long engineerCount = employees.get()
    .filter(e -> e.department() == Department.ENGINEERING)
    .count();
```

**Explanation:** each `get()` creates a fresh pipeline. Do not cache a `Stream` in a field as if it were a collection.

### Closing and `onClose`

Collection-, array-, and generator-backed streams normally hold no external resource. I/O-backed streams can hold file descriptors and must be closed, normally with try-with-resources. `onClose` registers handlers; handlers run in registration order. If several throw, the first exception is thrown and later exceptions are suppressed.

```java
try (Stream<String> lines = Files.lines(Path.of("orders.csv"))
        .onClose(() -> System.out.println("lines closed"))) {
    long nonBlank = lines.filter(line -> !line.isBlank()).count();
}
```

**Result:** the file is closed promptly and the handler prints `lines closed`, including when traversal fails.

### Unbounded sources

```java
List<Integer> powersOfTwo = Stream.iterate(1, n -> n * 2)
    .limit(5)
    .toList();
```

**Result:** `[1, 2, 4, 8, 16]`.

**Explanation:** `iterate(seed, next)` is unbounded. `limit(5)` is a short-circuiting intermediate operation, so `toList` completes. Move a full-barrier operation such as `sorted` before the limit and completion may become impossible.

---

<a id="part-ii-creating-streams"></a>

# Part II — Creating streams

## Core object-stream factories

All factory streams are sequential unless explicitly converted with `parallel()`.

### `empty`, `of`, and `ofNullable`

```java
Stream<String> none = Stream.empty();
Stream<String> one = Stream.of("Asha");
Stream<String> many = Stream.of("Asha", "Ben", "Chen");
Stream<String> maybe = Stream.ofNullable(System.getenv("REGION")); // Java 9
```

`Stream.of((String) null)` contains one null; `Stream.ofNullable(null)` is empty. The latter is useful when absence should mean zero elements:

```java
List<String> cities = Fixtures.EMPLOYEES.stream()
    .flatMap(e -> Stream.ofNullable(e.address()))
    .map(Address::city)
    .toList();
```

**Result:** `[Pune, Singapore, Mumbai]`.

**Explanation:** each employee maps to zero or one address stream, and `flatMap` merges them. This deliberately treats missing address as absence; validation code should instead report it if null is invalid.

### `iterate` — unbounded and predicate-bounded

```java
List<Integer> unboundedThenLimited = Stream.iterate(1, n -> n + 1)
    .limit(5)
    .toList();

List<Integer> bounded = Stream.iterate(1, n -> n <= 5, n -> n + 1)
    .toList(); // Java 9
```

Both results are `[1, 2, 3, 4, 5]`. The three-argument form behaves like an ordered `for` loop: seed, test, emit, advance. If the initial seed fails the predicate, it emits nothing.

### `generate`

```java
Iterator<String> source = List.of("A", "B", "C").iterator();
List<String> generated = Stream.generate(source::next)
    .limit(3)
    .toList();
```

**Result:** `[A, B, C]`.

`generate` creates an unbounded, unordered stream from a supplier. The supplier above is stateful and only safe sequentially. A typical safe use is constant or independently generated values, always with a terminating operation.

### `concat`

```java
List<String> all = Stream.concat(
        Stream.of("A", "B"),
        Stream.of("C", "D"))
    .toList();
```

**Result:** `[A, B, C, D]`.

The result is ordered if both inputs are ordered. Closing it closes both inputs. Deeply nested concatenation can create deep call chains; prefer `Stream.of(streams...).flatMap(Function.identity())` or a builder for many sources.

## Primitive-stream factories

`IntStream`, `LongStream`, and `DoubleStream` avoid boxing each numeric element. They share `empty`, `of`, `builder`, `iterate`, `generate`, and `concat`. `IntStream` and `LongStream` additionally provide `range(startInclusive, endExclusive)` and `rangeClosed(startInclusive, endInclusive)`.

```java
int sum = IntStream.range(1, 5).sum();           // 1 + 2 + 3 + 4 = 10
long closed = LongStream.rangeClosed(1, 5).sum(); // 15
double average = DoubleStream.of(1.5, 2.5, 3.5)
    .average()
    .orElseThrow();                              // 2.5
```

**Explanation:** ranges are ordered, sequential, sized, and efficient for indexes and numeric domains. A descending range is empty; Java ranges do not infer a negative step.

### Conversion and boxing

```java
LongStream widened = IntStream.of(1, 2, 3).asLongStream();
DoubleStream doubles = IntStream.of(1, 2, 3).asDoubleStream();
List<Integer> boxed = IntStream.rangeClosed(1, 3).boxed().toList();
```

`int → long → double` widening has dedicated operations. `LongStream.asDoubleStream()` can lose integer precision for values larger than `2^53`. `boxed()` enables object-only collectors but allocates wrapper objects; remain primitive while doing numeric work.

## Collections, arrays, and builders

```java
Stream<Employee> sequential = Fixtures.EMPLOYEES.stream();
Stream<Employee> parallel = Fixtures.EMPLOYEES.parallelStream();

String[] names = {"Asha", "Ben", "Chen"};
Stream<String> allNames = Arrays.stream(names);
Stream<String> slice = Arrays.stream(names, 1, 3); // Ben, Chen
IntStream ints = Arrays.stream(new int[] {3, 1, 4});
```

Array range bounds follow the normal half-open rule and are validated. Collection encounter order comes from the collection. Calling `stream()` does not copy the source; non-concurrent source changes during traversal may interfere.

### Builders

```java
Stream.Builder<String> builder = Stream.builder();
builder.add("required");
boolean includeOptional = true;
if (includeOptional) builder.accept("optional");

List<String> values = builder.build().toList();
```

**Result:** `[required, optional]`.

Object and primitive builders have `accept`, fluent `add`, and `build`. After `build`, further additions or another build throw `IllegalStateException`. Builders suit imperative conditional assembly; `ofNullable`, concatenation, or `mapMulti` is often clearer inside an existing pipeline.

## Iterators, spliterators, and StreamSupport

`StreamSupport` creates object or primitive streams from spliterators. Prefer a collection's own `stream()` when available; use this bridge for custom sources.

```java
Iterator<String> iterator = List.of("A", "B", "C").iterator();
Spliterator<String> spliterator =
    Spliterators.spliteratorUnknownSize(iterator, Spliterator.ORDERED);

List<String> values = StreamSupport.stream(spliterator, false).toList();
```

**Result:** `[A, B, C]`.

**Explanation:** the spliterator is ordered but has unknown size and weak splitting, so parallel execution is unlikely to help. The boolean selects parallel mode; it does not magically make a source efficiently splittable.

The supplier overload delays spliterator creation until terminal traversal begins:

```java
Stream<String> lateBound = StreamSupport.stream(
    () -> List.of("latest", "snapshot").spliterator(),
    Spliterator.ORDERED | Spliterator.SIZED | Spliterator.SUBSIZED,
    false);
```

The supplier must create a fresh spliterator and must be invoked at most once. Primitive counterparts are `intStream`, `longStream`, and `doubleStream`, each with direct and supplier forms.

## Files, readers, directories, and archives

These sources are finite but commonly hold resources. Keep the terminal operation inside try-with-resources; returning the raw stream transfers a close obligation that callers often miss.

### File lines

```java
Path path = Path.of("orders.csv");
try (Stream<String> lines = Files.lines(path, StandardCharsets.UTF_8)) {
    long dataRows = lines.skip(1).filter(line -> !line.isBlank()).count();
}
```

`Files.lines` lazily reads lines and must be closed. `BufferedReader.lines()` is similar, but closing the stream does not replace clear ownership of the reader; place both in try-with-resources when the method opened the reader.

```java
try (BufferedReader reader = Files.newBufferedReader(path);
     Stream<String> lines = reader.lines()) {
    Optional<String> first = lines.findFirst();
}
```

### Directory streams

```java
Path root = Path.of("data");
try (Stream<Path> children = Files.list(root)) {
    List<Path> csv = children
        .filter(p -> p.getFileName().toString().endsWith(".csv"))
        .sorted()
        .toList();
}

try (Stream<Path> tree = Files.walk(root, 3)) {
    long regularFiles = tree.filter(Files::isRegularFile).count();
}

try (Stream<Path> found = Files.find(root, 3,
        (p, attrs) -> attrs.isRegularFile() && p.toString().endsWith(".csv"))) {
    List<Path> paths = found.toList();
}
```

`Files.list`, `walk`, and `find` all require closing. File-system traversal can fail lazily during the terminal operation, wrapping an `IOException` in `UncheckedIOException`. Symbolic-link options can introduce cycles; use the API's cycle detection and an appropriate maximum depth.

### JAR entries

```java
try (JarFile jar = new JarFile("application.jar")) {
    long classes = jar.stream()
        .filter(entry -> !entry.isDirectory())
        .filter(entry -> entry.getName().endsWith(".class"))
        .count();
}
```

The `JarFile` owns the resource. `versionedStream()` exposes the effective entries for a multi-release JAR; `stream()` exposes physical entries. Keep traversal within the `JarFile` lifetime.

## Regex, scanners, characters, random values, bits, and services

### Regex token and match streams

```java
List<String> words = Pattern.compile("\\s+")
    .splitAsStream("streams are lazy")
    .toList();

List<String> numbers = Pattern.compile("\\d+")
    .matcher("A12 B7")
    .results()
    .map(MatchResult::group)
    .toList();
```

**Results:** `[streams, are, lazy]` and `[12, 7]`.

`splitAsStream` produces tokens; `Matcher.results()` produces immutable match snapshots in encounter order. A matcher is stateful and should not be concurrently modified.

### Scanner streams

```java
try (Scanner scanner = new Scanner("red 12 blue 7")) {
    List<String> tokens = scanner.tokens().toList();
}

try (Scanner scanner = new Scanner("red 12 blue 7")) {
    List<Integer> values = scanner.findAll("\\d+")
        .map(MatchResult::group)
        .map(Integer::parseInt)
        .toList();
}
```

Closing a `Scanner` closes its underlying closeable source. Its token/match streams are ordered and stateful; they are poor parallel sources.

### UTF-16 code units versus Unicode code points

```java
String text = "A😀";
long codeUnits = text.chars().count();      // 3
long codePoints = text.codePoints().count(); // 2
```

`chars()` exposes unsigned UTF-16 code units as ints; a supplementary character uses two. `codePoints()` combines valid surrogate pairs and is the normal choice for Unicode characters.

### Random values

```java
RandomGenerator rng = RandomGenerator.of("L64X128MixRandom");
int[] dice = rng.ints(5, 1, 7).toArray();
```

The invariant is five values in `[1, 7)`. Seed a seedable generator in tests if exact reproducibility is required. Random streams have bounded and unbounded overloads; always bound the unbounded form before materializing it.

### Set bits

```java
BitSet flags = new BitSet();
flags.set(1);
flags.set(4);
flags.set(9);
List<Integer> setIndexes = flags.stream().boxed().toList();
```

**Result:** `[1, 4, 9]`. `BitSet.stream()` yields set-bit indexes in increasing order, not boolean values for every position.

### Service providers

```java
List<Class<?>> providerTypes = ServiceLoader.load(java.nio.file.spi.FileSystemProvider.class)
    .stream()
    .map(ServiceLoader.Provider::type)
    .toList();
```

`ServiceLoader.stream()` exposes provider descriptors and permits inspecting types before calling `Provider.get()`. Discovery and instantiation can execute provider/module logic, so do not treat this as a pure cheap source.

## Source-selection table

| Need | Preferred source | Reason / caveat |
|---|---|---|
| Existing collection | `collection.stream()` | Preserves its encounter-order and splitting model |
| Existing array or slice | `Arrays.stream` | Sized, ordered, efficiently splittable |
| Integer/long index range | `range` / `rangeClosed` | Avoids boxed index lists |
| Zero or one nullable value | `Stream.ofNullable` | Expresses absence without a temporary list |
| Repeated recurrence | `iterate` | Use predicate or effective short-circuiting |
| Independent generated values | `generate` | Unbounded unless limited |
| Conditional imperative assembly | builder | Build once; cannot add afterward |
| Custom traversal | `Spliterator` + `StreamSupport` | Characteristics and splitting must be correct |
| File lines/directory entries | `Files.*` stream | Must close with try-with-resources |
| Tokens or matches | `Pattern`, `Matcher`, or `Scanner` | Usually ordered and sequential in nature |
| Unicode characters | `codePoints()` | `chars()` exposes UTF-16 code units |
| Numeric computation | primitive stream | Avoids boxing; use object stream for object collectors |

**Decision rule:** start from the source that already owns the data and preserves the facts you need. Do not copy into a list merely to obtain a stream. Do materialize deliberately when you need repeatable traversal, random access, a snapshot, sorting reuse, or a boundary that closes a resource.

---

<a id="part-iii-intermediate-operations"></a>

# Part III — Intermediate operations

## Filtering and mapping

These operations are lazy, stateless, and order-preserving unless the source is unordered.

### `filter(Predicate)` — keep matching elements

```java
List<String> activeNames = Fixtures.EMPLOYEES.stream()
    .filter(Employee::active)
    .map(Employee::name)
    .toList();
```

**Result:** `[Asha, Ben, Diya]`.

**Explanation:** `filter` emits the original employee only when the predicate returns true; `map` then replaces each retained employee with one name. Filter does not remove anything from `EMPLOYEES`.

**Cost:** `O(n)` predicate calls, `O(1)` intermediate state, plus the result. Put cheap/selective filters before expensive mappings when semantics permit.

### `map(Function)` — one input to one output

```java
List<String> labels = Fixtures.EMPLOYEES.stream()
    .map(e -> e.id() + ":" + e.name().toUpperCase(Locale.ROOT))
    .toList();
```

`map` may return null, but later operations such as `findFirst`, natural sorting, unmodifiable collectors, or method references may reject it. Prefer an explicit domain representation for absence or use the zero-or-one patterns below.

### Object-to-primitive mappings

```java
int totalNameCharacters = Fixtures.EMPLOYEES.stream()
    .mapToInt(e -> e.name().length())
    .sum(); // 15

long totalSalaryMinorUnits = Fixtures.EMPLOYEES.stream()
    .mapToLong(e -> e.salary().movePointRight(2).longValueExact())
    .sum();

double averageNameLength = Fixtures.EMPLOYEES.stream()
    .mapToDouble(e -> e.name().length())
    .average()
    .orElse(0.0); // 3.75
```

`mapToInt`, `mapToLong`, and `mapToDouble` avoid wrapper allocation and unlock specialized numeric terminals. The salary example uses exact decimal conversion before entering `LongStream`; do not turn money into `double`.

### Primitive mappings and conversions

```java
IntStream squares = IntStream.rangeClosed(1, 4).map(n -> n * n);
Stream<String> labels = IntStream.rangeClosed(1, 3)
    .mapToObj(n -> "item-" + n);
LongStream longs = IntStream.of(1, 2, 3).mapToLong(n -> n * 1_000L);
DoubleStream ratios = LongStream.of(1, 2, 3).mapToDouble(n -> n / 2.0);
IntStream truncated = DoubleStream.of(1.2, 2.9).mapToInt(d -> (int) d);
```

All three primitive types offer `map`, `mapToObj`, and the meaningful cross-primitive conversions. Narrowing (`long → int`, `double → int/long`) requires an explicit function and can overflow, truncate, or mishandle `NaN`; the Stream API does not validate that conversion for you.

## Flattening and zero-or-more mapping

### `flatMap` — map to streams, then flatten

```java
List<String> skus = Fixtures.ORDERS.stream()
    .flatMap(order -> order.items().stream())
    .map(LineItem::sku)
    .toList();
```

**Result:** `[BOOK, PEN, BOOK]`.

**Explanation:** each order becomes a stream of its line items; `flatMap` drains each mapped stream into one output stream and closes each mapped stream afterward. If a mapper returns null, `flatMap` treats it as an empty stream, but returning `Stream.empty()` is clearer.

Primitive variants avoid boxing nested numeric data:

```java
int units = Fixtures.ORDERS.stream()
    .flatMapToInt(order -> order.items().stream().mapToInt(LineItem::quantity))
    .sum(); // 6

LongStream charsPerName = Fixtures.EMPLOYEES.stream()
    .flatMapToLong(e -> LongStream.of(e.name().length()));

DoubleStream lineTotals = Fixtures.ORDERS.stream()
    .flatMapToDouble(order -> order.items().stream()
        .mapToDouble(item -> item.total().doubleValue()));
```

The last example is suitable for demonstration, not money accounting; converting `BigDecimal` to double loses exactness.

Primitive streams themselves have `flatMap`:

```java
int[] repeated = IntStream.of(2, 3)
    .flatMap(n -> IntStream.generate(() -> n).limit(n))
    .toArray();
// [2, 2, 3, 3, 3]
```

### `mapMulti` — emit zero, one, or many without a temporary stream

`mapMulti` (Java 16) passes a downstream consumer to the mapper. It is useful when each input emits a small, imperative number of outputs.

```java
List<String> javaOrSql = Fixtures.EMPLOYEES.stream()
    .<String>mapMulti((employee, emit) -> {
        for (String skill : employee.skills()) {
            if (skill.equals("Java") || skill.equals("SQL")) {
                emit.accept(employee.name() + ":" + skill);
            }
        }
    })
    .toList();
```

**Result (inner set order may vary):** it contains `Asha:Java`, `Asha:SQL`, `Ben:SQL`, and `Chen:Java`.

**Explanation:** an employee can emit zero, one, or two labels. The explicit `<String>` type witness helps inference when the downstream type is not obvious. The consumer is valid only during the mapper call; never retain or call it later.

Primitive targets are available from object streams:

```java
int totalUnits = Fixtures.ORDERS.stream()
    .mapMultiToInt((order, emit) ->
        order.items().forEach(item -> emit.accept(item.quantity())))
    .sum(); // 6
```

The sibling methods are `mapMultiToLong` and `mapMultiToDouble`:

```java
long totalCharacters = Stream.of("A", "BC")
    .mapMultiToLong((text, emit) -> emit.accept(text.length()))
    .sum(); // 3

double averageLength = Stream.of("A", "BC")
    .mapMultiToDouble((text, emit) -> emit.accept(text.length()))
    .average().orElseThrow(); // 1.5
```

All three object-to-primitive variants emit zero or more primitive values without boxing. Use the specific target type required by later numeric work.

And each primitive stream has its specialized `mapMulti`:

```java
int[] positiveAndNegative = IntStream.of(1, 2)
    .mapMulti((value, emit) -> {
        emit.accept(value);
        emit.accept(-value);
    })
    .toArray(); // [1, -1, 2, -2]
```

The mapper types are the public nested functional interfaces `IntStream.IntMapMultiConsumer`, `LongStream.LongMapMultiConsumer`, and `DoubleStream.DoubleMapMultiConsumer`. Each defines `accept(value, downstreamPrimitiveConsumer)`. As with object `mapMulti`, the downstream consumer is callback-scoped and must not be retained.

Choose:

- `map` for exactly one result;
- `filter` + `map` or `ofNullable` for zero or one;
- `flatMap` when a natural stream/collection already exists or emission may be large;
- `mapMulti` for small imperative zero-to-many expansion without temporary streams; and
- `gather` for state across multiple upstream elements, windows, scans, or controlled concurrency.

## Observation, uniqueness, and sorting

### `peek` — observe elements as they are consumed

```java
List<String> result = Fixtures.EMPLOYEES.stream()
    .filter(Employee::active)
    .peek(e -> System.out.println("after filter: " + e.name()))
    .map(Employee::name)
    .toList();
```

`peek` is mainly a diagnostic probe. It is lazy, can run on arbitrary worker threads in parallel, and can be elided if traversal is unnecessary. Do not use it to save records, update counters, or make a business action happen. Use `forEach` for an intentional terminal action or a collector for a result.

### `distinct` — equality-based uniqueness

```java
List<String> stable = Stream.of("B", "A", "B", "C", "A")
    .distinct()
    .toList();
```

**Result:** `[B, A, C]`.

For object streams, equality uses `equals`; correct `hashCode` implementations matter to performance and behavior. On ordered streams, the first equal element survives. `distinct` is stateful and needs memory proportional to unique values in the general case. On an unbounded stream with endlessly new values, memory can grow without bound.

Primitive `distinct` follows boxed equality semantics. For `DoubleStream`, all NaNs compare as one distinct value while `0.0` and `-0.0` are distinct.

### `sorted` — natural or comparator order

```java
List<String> ranked = Fixtures.EMPLOYEES.stream()
    .sorted(Comparator.comparing(Employee::salary).reversed()
        .thenComparing(Employee::name))
    .map(Employee::name)
    .toList();
```

**Result:** `[Chen, Asha, Ben, Diya]`.

`sorted()` requires mutually comparable, non-null values; otherwise terminal traversal can throw. `sorted(comparator)` defines the order and can handle nulls explicitly with `nullsFirst`/`nullsLast`. Object sorting is stable for an ordered stream. Sorting is a stateful full barrier: general cost is `O(n log n)` time and `O(n)` buffering. It cannot complete on an unbounded source.

Primitive streams provide natural `sorted()` only. Floating-point order follows `Double.compare`: negative zero precedes positive zero and NaN values sort after other numbers.

## Slicing and prefix operations

### `limit` and `skip`

```java
List<String> page2 = Fixtures.EMPLOYEES.stream()
    .sorted(Comparator.comparingInt(Employee::id))
    .skip(2)
    .limit(2)
    .map(Employee::name)
    .toList();
```

**Result:** `[Chen, Diya]`.

`limit(n)` keeps at most `n`; `skip(n)` discards the first `n`. Negative arguments throw `IllegalArgumentException`. Both are stateful; `limit` is short-circuiting. Ordered parallel pipelines may pay a high coordination cost to find the correct prefix. If any subset is acceptable, removing order with `unordered()` can unlock faster execution.

Pagination with `skip(page * size)` still traverses/skips earlier elements and can overflow the multiplication. For large datasets, use a source-level cursor/keyset query instead of loading and skipping in memory.

### `takeWhile` and `dropWhile` (Java 9)

```java
List<Integer> prefix = Stream.of(2, 4, 6, 7, 8, 10)
    .takeWhile(n -> n % 2 == 0)
    .toList();                    // [2, 4, 6]

List<Integer> remainder = Stream.of(2, 4, 6, 7, 8, 10)
    .dropWhile(n -> n % 2 == 0)
    .toList();                    // [7, 8, 10]
```

These are prefix operations, not general filter/reject operations. On an ordered stream, `takeWhile` stops at the first failure; it does not resume at 8. `dropWhile` discards the longest matching prefix, then keeps everything including later matches.

On an unordered stream, when some but not all elements match, the chosen matching subset is nondeterministic. `takeWhile` is short-circuiting; `dropWhile` is not. Ordered parallel prefix operations can be expensive.

All four slicing/prefix families exist on object and primitive streams with the corresponding predicate type.

## BaseStream mode, order, close, and traversal controls

```java
Stream<Employee> pipeline = Fixtures.EMPLOYEES.stream()
    .parallel()
    .filter(Employee::active)
    .sequential();

System.out.println(pipeline.isParallel()); // false
```

The final mode chosen before the terminal operation applies to the entire pipeline; individual stages do not run in different modes because a switch appeared between them.

- `parallel()` requests parallel execution.
- `sequential()` requests sequential execution.
- `isParallel()` reports the current mode.
- `unordered()` removes the ordering constraint; it does not randomize data.
- `onClose()` and `close()` manage close handlers and resources.
- `iterator()` and `spliterator()` are escape-hatch terminal operations for controlled traversal. Once obtained, traversal is external and the original stream must not be reused.

Primitive interfaces override mode and traversal methods covariantly, returning their own stream, primitive iterator, and primitive spliterator types.

Use `iterator` when a consumer API requires pull traversal. Use `spliterator` when characteristics, partitioning, bulk traversal, or a new custom stream source is required. A loop is usually clearer if escaping internal iteration immediately.

## Intermediate-operation classification

| Family | Lazy | Stateful | Short-circuiting intermediate | Preserves encounter order | General buffering |
|---|---|---|---|---|---|
| `filter`, `map`, primitive mappings | Yes | No | No | Yes | `O(1)` |
| `flatMap`, primitive flat maps | Yes | No per outer element | No | Yes | Current mapped stream |
| `mapMulti`, primitive variants | Yes | No unless mapper cheats | No | Yes | `O(1)` from framework |
| `peek` | Yes | No | No | Yes, but action timing/thread unspecified | `O(1)` |
| `distinct` | Yes | Yes | No | Yes when ordered | Up to unique count |
| `sorted` | Yes | Yes/full barrier | No | Produces sorted order | `O(n)` |
| `limit` | Yes | Yes | Yes | Yes when ordered | Implementation-dependent |
| `skip` | Yes | Yes | No | Yes when ordered | Implementation-dependent |
| `takeWhile` | Yes | Yes | Yes | Prefix if ordered | Implementation-dependent |
| `dropWhile` | Yes | Yes | No | Remaining suffix if ordered | Implementation-dependent |
| `unordered`, mode changes, `onClose` | Yes/configuration | No | No | `unordered` removes constraint | `O(1)` |

**Optimization rule:** operation order is semantic. `filter(...).map(...)` is only interchangeable with `map(...).filter(...)` if the predicate can be expressed on the mapped value and mapping does not change failures, cost, or side effects. Prefer pipelines that minimize expensive work while keeping the business meaning obvious.

---

<a id="part-iv-terminal-operations-and-reductions"></a>

# Part IV — Terminal operations and reductions

## Traversal and materialization

Terminal operations consume the pipeline. Calling another operation on the same stream afterward is invalid.

### `forEach` and `forEachOrdered`

```java
Fixtures.EMPLOYEES.stream()
    .map(Employee::name)
    .forEach(System.out::println);
```

Sequential `forEach` normally follows encounter order, but its contract explicitly permits arbitrary order in parallel. Use it for an intentional terminal side effect whose correctness does not depend on ordering.

```java
Fixtures.EMPLOYEES.parallelStream()
    .map(Employee::name)
    .forEachOrdered(System.out::println);
```

**Result order:** `Asha`, `Ben`, `Chen`, `Diya`.

`forEachOrdered` preserves encounter order. In parallel it may reduce throughput by coordinating actions; the action for one element happens-before the action for the next, though actions need not all use one thread. Neither method transforms values into a reusable result.

### `toArray`

```java
Object[] generic = Fixtures.EMPLOYEES.stream()
    .map(Employee::name)
    .toArray();

String[] typed = Fixtures.EMPLOYEES.stream()
    .map(Employee::name)
    .toArray(String[]::new);

int[] primitive = IntStream.rangeClosed(1, 3).toArray();
```

**Results:** the first two contain the four names; the last is `[1, 2, 3]`.

The generator form preserves the requested runtime array type and may be invoked multiple times for partitioned execution or resizing. An incompatible runtime component type can produce `ArrayStoreException`. Primitive streams return their primitive array directly.

### `Stream.toList()` (Java 16)

```java
List<String> names = Fixtures.EMPLOYEES.stream()
    .map(Employee::name)
    .toList();

// names.add("Eva"); // UnsupportedOperationException
```

The result is unmodifiable, preserves encounter order, and may contain null. Do not depend on its concrete class, serializability, identity, or value-based-instance identity. This differs from `Collectors.toList()`, whose mutability and concrete type are intentionally unspecified, and from `toUnmodifiableList()`, which rejects null.

## Scalar queries, matching, and finding

### `count`, `min`, and `max`

```java
long activeCount = Fixtures.EMPLOYEES.stream()
    .filter(Employee::active)
    .count(); // 3

Optional<Employee> highestPaid = Fixtures.EMPLOYEES.stream()
    .max(Comparator.comparing(Employee::salary)); // Chen
```

`count` returns a `long` and may be optimized from a known source size without traversing elements. `min` and `max` return `Optional.empty()` on empty input and use the supplied comparator for object streams. If the selected result is null, object `min`/`max` throw `NullPointerException`; normalize or reject nulls first.

Primitive streams supply comparator-free `min` and `max`, returning `OptionalInt`, `OptionalLong`, or `OptionalDouble`.

### Match operations and vacuous truth

```java
boolean anyInactive = Fixtures.EMPLOYEES.stream()
    .anyMatch(e -> !e.active());                  // true
boolean allPaid = Fixtures.EMPLOYEES.stream()
    .allMatch(e -> e.salary().signum() > 0);      // true
boolean noneBlank = Fixtures.EMPLOYEES.stream()
    .noneMatch(e -> e.name().isBlank());          // true
```

All three are short-circuiting. On an empty stream, `anyMatch` is false, while `allMatch` and `noneMatch` are true. This is **vacuous truth**: no element disproves the universal/no-match claim.

Primitive streams expose the same families with primitive predicates.

### `findFirst` and `findAny`

```java
Optional<String> deterministic = Fixtures.EMPLOYEES.stream()
    .map(Employee::name)
    .findFirst(); // Asha

Optional<Employee> parallelChoice = Fixtures.EMPLOYEES.parallelStream()
    .filter(Employee::active)
    .findAny(); // any active employee
```

`findFirst` honors encounter order and can constrain parallel execution. `findAny` may choose any element and is often a better parallel expression when identity does not matter. Both are short-circuiting and return empty for an empty stream. If the chosen object-stream element is null, they throw `NullPointerException`; a Stream's `Optional` result cannot represent “present null.”

## Immutable reduction

Reduction combines input values into one value. A parallel-safe reduction requires an **associative** operation: regrouping must not change the mathematical result.

### `reduce(BinaryOperator)` — no identity

```java
Optional<BigDecimal> total = Fixtures.ORDERS.stream()
    .flatMap(order -> order.items().stream())
    .map(LineItem::total)
    .reduce(BigDecimal::add);
```

**Result:** `41.10` in the fixture (`25.00 + 3.60 + 12.50`). Empty input produces `Optional.empty()`.

### `reduce(identity, BinaryOperator)`

```java
BigDecimal total = Fixtures.ORDERS.stream()
    .flatMap(order -> order.items().stream())
    .map(LineItem::total)
    .reduce(BigDecimal.ZERO, BigDecimal::add);
```

The identity must be neutral on both sides: `op(identity, x) == x` and, for the intended domain, `op(x, identity) == x`. Addition uses zero; multiplication uses one; concatenation uses the empty string.

### Incorrect — subtraction is not associative

```java
int sequential = Stream.of(10, 2, 1).reduce(0, (a, b) -> a - b);          // -13
int parallel = Stream.of(10, 2, 1).parallel().reduce(0, (a, b) -> a - b); // may differ

int negativeSum = -Stream.of(10, 2, 1)
    .mapToInt(Integer::intValue)
    .sum(); // -13, associative addition followed by one negation
```

Subtraction is neither associative nor compatible with zero as a two-sided identity for this accumulation. Use a sum of negated values or keep the explicitly ordered calculation sequential in a loop.

### `reduce(identity, accumulator, combiner)` — change result type

```java
int totalCharacters = Fixtures.EMPLOYEES.parallelStream().reduce(
    0,
    (subtotal, employee) -> subtotal + employee.name().length(),
    Integer::sum);
```

**Result:** `15`.

The accumulator folds one `Employee` into an `Integer` partial result; the combiner merges two partial integers. Required compatibility is conceptually:

```text
combiner(u, accumulator(identity, t)) == accumulator(u, t)
```

The identity must be an identity for the combiner, and the combiner must be associative. The reduction value should be immutable. Accumulating into the same mutable list and returning it from `reduce` lets parallel partitions share and combine aliases—use `collect` instead.

### Primitive reductions

Each primitive stream provides `reduce(identity, primitiveOperator)` and `reduce(primitiveOperator)` returning its optional specialization.

```java
int product = IntStream.rangeClosed(1, 5).reduce(1, (a, b) -> a * b); // 120
OptionalLong maximum = LongStream.of(5, 9, 2).reduce(Long::max);       // 9
```

Integer arithmetic still overflows silently; use exact methods, a wider type, or `BigInteger` when overflow is invalid.

## Mutable reduction

Mutable reduction accumulates into containers without creating a new immutable accumulator on every step.

### `collect(Collector)`

```java
Map<Department, List<Employee>> byDepartment = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(Employee::department));
```

A collector defines how to create partial containers, add values, merge partial containers, and optionally finish the result. Part V covers every built-in and custom collector.

### Three-argument `collect`

```java
ArrayList<String> names = Fixtures.EMPLOYEES.parallelStream().collect(
    ArrayList::new,
    (list, employee) -> list.add(employee.name()),
    ArrayList::addAll);
```

**Result:** `[Asha, Ben, Chen, Diya]` for this ordered stream.

**Explanation:** each parallel partition receives a distinct list from the supplier; the accumulator mutates only its local list; the combiner merges lists. The framework handles partition isolation.

### Incorrect — shared accumulator

```java
List<String> shared = new ArrayList<>();
// Incorrect: every partition mutates the same non-thread-safe object.
List<String> broken = Fixtures.EMPLOYEES.parallelStream().collect(
    () -> shared,
    (list, e) -> list.add(e.name()),
    List::addAll);
```

The supplier must return a new independent container, not the same captured object. Even a synchronized shared list violates the collector model and can duplicate data when combined.

Primitive streams expose the same pattern with `ObjIntConsumer`, `ObjLongConsumer`, or `ObjDoubleConsumer`:

```java
IntSummaryStatistics stats = IntStream.of(3, 1, 4).collect(
    IntSummaryStatistics::new,
    IntSummaryStatistics::accept,
    IntSummaryStatistics::combine);
```

Use the built-in `summaryStatistics()` for this exact task; the example reveals how primitive mutable collection works.

## Primitive numeric terminals

| Terminal | Empty result | Important caveat |
|---|---|---|
| `sum()` | zero | `int`/`long` overflow silently; floating sum is order-sensitive |
| `min()` / `max()` | empty optional | `DoubleStream`: NaN and signed-zero rules apply |
| `average()` | empty `OptionalDouble` | floating representation and count affect accuracy |
| `summaryStatistics()` | count 0; sum 0; extreme sentinel min/max | Read `count()` before treating min/max as data |
| `count()` | `0L` | traversal may be elided for sized pipelines |

```java
IntSummaryStatistics stats = Fixtures.EMPLOYEES.stream()
    .mapToInt(e -> e.name().length())
    .summaryStatistics();

System.out.printf("count=%d min=%d max=%d sum=%d average=%.2f%n",
    stats.getCount(), stats.getMin(), stats.getMax(),
    stats.getSum(), stats.getAverage());
```

**Result:** `count=4 min=3 max=4 sum=15 average=3.75`.

### Overflow and exactness

```java
int overflowed = IntStream.of(Integer.MAX_VALUE, 1).sum(); // MIN_VALUE

long exact = Fixtures.TRANSACTIONS.stream()
    .mapToLong(Transaction::minorUnits)
    .reduce(0L, Math::addExact); // throws if long range is exceeded
```

`IntStream.sum` and `LongStream.sum` use Java primitive arithmetic. They do not signal overflow. For exact decimal values, reduce `BigDecimal` in an object stream.

### Floating-point edge cases

- A `DoubleStream` sum/average can change slightly with evaluation order; parallel regrouping is allowed.
- If any input is NaN, sum and average are NaN.
- `min` treats negative zero as smaller than positive zero; `max` treats positive zero as larger.
- A NaN is selected by `min`/`max` when present according to their specified numerical comparison behavior.
- `DoubleSummaryStatistics` improves summation accuracy internally but cannot make binary floating point exact or fully order-independent.

Use an error tolerance for approximate scientific values. Use decimal/integer domain types for money, identifiers, counters that must not overflow, and exact audit results.

## Terminal-operation decision table

| Need | Operation | Empty input | Short-circuit | Order notes | Result mutability |
|---|---|---|---|---|---|
| Intentional action per value | `forEach` | no actions | No | Arbitrary in parallel | N/A |
| Ordered actions | `forEachOrdered` | no actions | No | Preserves encounter order | N/A |
| Array | `toArray` | empty array | No | Preserves encounter order | Mutable array |
| General snapshot | `toList` | empty list | No | Preserves encounter order | Unmodifiable |
| Count | `count` | `0` | No | May elide traversal | Scalar |
| Extreme object | `min` / `max` | empty `Optional` | No | Comparator defines result | Scalar |
| Existence/universal checks | match family | false/true/true | Yes | Choice not exposed | Scalar |
| One value | `findFirst` / `findAny` | empty optional | Yes | First vs any | Scalar |
| Immutable fold | `reduce` | identity or empty optional | No | Operation must be associative | Result type decides |
| Mutable aggregate | `collect` | fresh empty container/result | No | Collector defines it | Collector decides |
| Primitive total/summary | numeric terminals | zero/empty/empty stats | No | Floating order matters | Scalar/statistics object |

**Selection rule:** use the most specific terminal operation. `count()` communicates counting better than `map(x -> 1).reduce(0, Integer::sum)`; `sum()` communicates numeric addition better than a custom reduction; a collector communicates mutable aggregation better than mutable `reduce`.

---

<a id="part-v-collectors"></a>

# Part V — Collectors

## Collector lifecycle and laws

A `Collector<T,A,R>` describes a mutable reduction:

- `T`: input element type;
- `A`: mutable accumulation type, often hidden with `?`; and
- `R`: published result type.

```text
supplier()    -> fresh A for each partition
accumulator() -> add one T into that partition's A
combiner()    -> merge two independent A values
finisher()    -> transform final A into R
characteristics() -> facts the framework may rely on
```

### Lifecycle trace

For a parallel list collection, the framework can do:

```text
A1 = supplier(); accumulate(A1, e1); accumulate(A1, e2)
A2 = supplier(); accumulate(A2, e3); accumulate(A2, e4)
A3 = combine(A1, A2)
R  = finish(A3)
```

It may partition differently. Therefore:

1. each supplier result must be an independent container;
2. combining must be associative;
3. accumulating then combining must be equivalent to sequential accumulation;
4. a non-concurrent collector must not expose one partial container to multiple threads; and
5. the result equivalence rule respects encounter order unless the collector is `UNORDERED`.

### Characteristics

- `IDENTITY_FINISH`: `A` is safely cast to `R`; the finisher is effectively identity. Claiming this when a real transformation is needed may cause the finisher to be skipped.
- `UNORDERED`: result equivalence does not depend on encounter order. It does not mean the result will be shuffled.
- `CONCURRENT`: the accumulator may be called concurrently on the same result container. The container and accumulator must truly support that. Concurrent reduction normally applies when the stream is unordered or the collector is also unordered.

### `Collector.of`

```java
Collector<String, StringJoiner, String> bracketed = Collector.of(
    () -> new StringJoiner(", ", "[", "]"),
    StringJoiner::add,
    StringJoiner::merge,
    StringJoiner::toString);

String result = Stream.of("A", "B", "C").collect(bracketed);
```

**Result:** `[A, B, C]`.

The four-functional-argument overload uses a finisher; the shorter overload returns the mutable accumulation object itself and therefore has identity finish. Optional characteristics follow as varargs. Do not add `CONCURRENT` to an ordinary `StringJoiner` collector.

## Collection and map collectors

### Lists, sets, and chosen collection types

```java
List<String> list = Fixtures.EMPLOYEES.stream()
    .map(Employee::name)
    .collect(Collectors.toList());

Set<String> skills = Fixtures.EMPLOYEES.stream()
    .flatMap(e -> e.skills().stream())
    .collect(Collectors.toSet());

TreeSet<String> sortedSkills = Fixtures.EMPLOYEES.stream()
    .flatMap(e -> e.skills().stream())
    .collect(Collectors.toCollection(TreeSet::new));

ArrayDeque<String> queue = Fixtures.EMPLOYEES.stream()
    .map(Employee::name)
    .collect(Collectors.toCollection(ArrayDeque::new));
```

`toList()` and `toSet()` make no guarantee about concrete type, mutability, serializability, or thread safety. `toSet` is unordered. Use `toCollection(factory)` when those properties matter.

Java 10 added `toUnmodifiableList()` and `toUnmodifiableSet()`:

```java
List<String> immutableNames = Fixtures.EMPLOYEES.stream()
    .map(Employee::name)
    .collect(Collectors.toUnmodifiableList());
```

These reject null and return unmodifiable results. For an unmodifiable set, if equal duplicate values are different objects, which instance survives is unspecified.

### Maps and duplicate-key policies

```java
Map<Integer, Employee> byId = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.toMap(Employee::id, Function.identity()));
```

The two-function `toMap` throws `IllegalStateException` on duplicate keys. Never rely on “duplicates cannot happen” without an invariant; select an explicit policy:

```java
Map<Department, Employee> highestPaidByDepartment = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.toMap(
        Employee::department,
        Function.identity(),
        BinaryOperator.maxBy(Comparator.comparing(Employee::salary))));
```

**Explanation:** values sharing a department are merged by retaining the higher salary. If ties need deterministic resolution, add a tie-breaker to the comparator.

The four-argument form selects the map implementation:

```java
LinkedHashMap<Integer, String> namesById = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.toMap(
        Employee::id,
        Employee::name,
        (left, right) -> left,
        LinkedHashMap::new));
```

This preserves encounter insertion order in the chosen map. The merge function must be associative for parallel collection and must not return null unless removal semantics are intentionally understood.

`toUnmodifiableMap` has two- and three-function forms. It rejects null keys/values and duplicate keys unless the merge overload resolves them. `toConcurrentMap` has two-, three-, and four-argument forms and returns a `ConcurrentMap`; use the map-supplier overload to choose a concurrent implementation.

```java
ConcurrentMap<String, Long> skillCounts = Fixtures.EMPLOYEES.parallelStream()
    .flatMap(e -> e.skills().stream())
    .collect(Collectors.toConcurrentMap(
        Function.identity(),
        skill -> 1L,
        Long::sum));
```

The concurrent result does not promise encounter order. A concurrent map collector is useful only when concurrent accumulation fits the result semantics and outperforms merging ordinary partial maps.

## Grouping and partitioning

### `groupingBy` — one key per input, many values per key

```java
Map<Department, List<Employee>> byDepartment = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(Employee::department));
```

The one-argument form groups into lists. The two-argument form applies a downstream collector:

```java
Map<Department, Long> headcount = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.counting()));
```

The three-argument form selects the map:

```java
EnumMap<Department, List<String>> names = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        () -> new EnumMap<>(Department.class),
        Collectors.mapping(Employee::name, Collectors.toList())));
```

Classifier results must be non-null. Default map type/order/mutability are unspecified. Grouping can be nested:

```java
Map<Department, Map<Boolean, List<String>>> activeNames =
    Fixtures.EMPLOYEES.stream().collect(Collectors.groupingBy(
        Employee::department,
        Collectors.partitioningBy(
            Employee::active,
            Collectors.mapping(Employee::name, Collectors.toList()))));
```

### `groupingByConcurrent`

Its three overloads mirror `groupingBy`: classifier only, classifier + downstream, and classifier + concurrent-map supplier + downstream. The collector is concurrent and unordered; the default returns `ConcurrentMap<K,List<T>>`. The lists themselves are not promised to be thread-safe after publication, and their element order is not the purpose of concurrent grouping.

### `partitioningBy`

```java
Map<Boolean, List<Employee>> partition = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.partitioningBy(Employee::active));
```

The result always contains both `true` and `false` keys, even when one partition is empty. The downstream overload can count, map, summarize, or otherwise reduce both partitions:

```java
Map<Boolean, Long> counts = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.partitioningBy(
        Employee::active,
        Collectors.counting()));
```

Use partitioning for exactly two groups defined by a predicate. Use grouping for multi-valued classifiers. An upstream filter removes categories entirely; downstream filtering preserves a group with an empty downstream result.

## Downstream adapters

Adapters change what a downstream collector sees.

### `mapping`

```java
Map<Department, Set<String>> namesByDepartment = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.mapping(Employee::name, Collectors.toSet())));
```

It is equivalent to applying a map within each group, not to mapping the whole stream before the classifier has seen each employee.

### `flatMapping` (Java 9)

```java
Map<Department, Set<String>> skillsByDepartment = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.flatMapping(
            employee -> employee.skills().stream(),
            Collectors.toSet())));
```

Each mapped stream is drained and closed. A null mapped stream is treated as empty.

### `filtering` (Java 9)

```java
Map<Department, List<Employee>> activeByDepartment = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.filtering(Employee::active, Collectors.toList())));
```

If a department has employees but none active, it remains as a key with an empty list. An upstream `.filter(Employee::active)` would remove that key completely.

### `collectingAndThen`

```java
Map<Department, List<String>> immutableNames = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.collectingAndThen(
            Collectors.mapping(Employee::name, Collectors.toList()),
            List::copyOf)));
```

The finisher transforms the downstream result. It is ideal for immutable snapshots, domain wrappers, or extracting a final scalar. Because a real finisher runs, the resulting collector is not identity-finish.

## Text, scalar, numeric, reducing, and teeing collectors

### `joining`

```java
String plain = Stream.of("A", "B", "C").collect(Collectors.joining());
String csv = Stream.of("A", "B", "C").collect(Collectors.joining(","));
String wrapped = Stream.of("A", "B", "C")
    .collect(Collectors.joining(", ", "[", "]"));
```

**Results:** `ABC`, `A,B,C`, and `[A, B, C]`. Empty input returns `""` for the first two forms and `prefix + suffix` for the third. Inputs are `CharSequence`; map other types to text first.

### Counting and extrema downstream

`counting()`, `minBy(comparator)`, and `maxBy(comparator)` are useful under grouping/partitioning. `minBy` and `maxBy` return `Optional<T>`.

```java
Map<Department, Optional<Employee>> highest = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.maxBy(Comparator.comparing(Employee::salary))));
```

### Summing, averaging, and summarizing

Each family has `Int`, `Long`, and `Double` forms:

- `summingInt`, `summingLong`, and `summingDouble` produce totals;
- `averagingInt`, `averagingLong`, and `averagingDouble` produce `Double`; and
- `summarizingInt`, `summarizingLong`, and `summarizingDouble` produce the matching summary-statistics type.

```java
Map<Department, Integer> nameCharacters = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.summingInt(e -> e.name().length())));

Map<Department, DoubleSummaryStatistics> salaryStats = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.summarizingDouble(e -> e.salary().doubleValue())));
```

`summingInt/Long/Double` return boxed scalar totals; `averaging*` return `0.0` on empty input; `summarizing*` return mutable statistics objects. Primitive overflow and floating-point caveats remain. The salary conversion above is for descriptive illustration, not exact accounting.

### Three `reducing` forms

```java
Map<Department, BigDecimal> payroll = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        Collectors.reducing(
            BigDecimal.ZERO,
            Employee::salary,
            BigDecimal::add)));
```

The forms correspond to: identity + operator; operator returning optional; and identity + mapper + operator. Prefer specialized collectors (`counting`, `summing*`, `maxBy`) when they express the job. `reducing` is especially useful downstream where a direct primitive stream is unavailable.

### `teeing` (Java 12)

```java
record SalaryRange(BigDecimal min, BigDecimal max) {}

SalaryRange range = Fixtures.EMPLOYEES.stream().collect(Collectors.teeing(
    Collectors.mapping(Employee::salary,
        Collectors.minBy(Comparator.naturalOrder())),
    Collectors.mapping(Employee::salary,
        Collectors.maxBy(Comparator.naturalOrder())),
    (min, max) -> new SalaryRange(min.orElseThrow(), max.orElseThrow())));
```

**Result:** `SalaryRange[min=72000, max=105000]`.

`teeing` feeds every input to both downstream collectors, then merges their final results. It is not a general N-way collector and does not avoid downstream memory use. Its characteristics are the compatible intersection of downstream characteristics, with a real merge finisher.

## Custom collectors

Build a custom collector only when composition of standard collectors is less clear or materially less efficient.

### Advanced — top N greatest values

```java
static <T> Collector<T, PriorityQueue<T>, List<T>> topN(
        int n, Comparator<? super T> ascendingOrder) {
    if (n < 0) throw new IllegalArgumentException("n must be non-negative");

    BiConsumer<PriorityQueue<T>, T> add = (heap, value) -> {
        heap.add(value);
        if (heap.size() > n) heap.poll(); // discard current smallest
    };

    return Collector.of(
        () -> new PriorityQueue<T>(ascendingOrder),
        add,
        (left, right) -> {
            right.forEach(value -> add.accept(left, value));
            return left;
        },
        heap -> heap.stream().sorted(ascendingOrder.reversed()).toList());
}

List<Integer> greatest = Stream.of(8, 1, 6, 3, 9, 2)
    .collect(topN(3, Comparator.naturalOrder()));
```

**Result:** `[9, 8, 6]`.

**Explanation:** each partial min-heap retains only its greatest `n` values. Combining feeds one heap through the same bounded rule, preserving equivalence. The finisher sorts descending and publishes an unmodifiable list. It claims no characteristics.

**Cost:** `O(m log n)` time and `O(n)` retained values per live partition for `m` inputs. For tiny data, `sorted(...).limit(n)` is simpler.

### Multi-field aggregation with an explicit accumulator

```java
record EmployeeSummary(long count, BigDecimal payroll) {}

final class EmployeeAccumulator {
    long count;
    BigDecimal payroll = BigDecimal.ZERO;

    void add(Employee employee) {
        count++;
        payroll = payroll.add(employee.salary());
    }

    EmployeeAccumulator merge(EmployeeAccumulator other) {
        count += other.count;
        payroll = payroll.add(other.payroll);
        return this;
    }

    EmployeeSummary finish() {
        return new EmployeeSummary(count, payroll);
    }
}

Collector<Employee, EmployeeAccumulator, EmployeeSummary> summaryCollector =
    Collector.of(
        EmployeeAccumulator::new,
        EmployeeAccumulator::add,
        EmployeeAccumulator::merge,
        EmployeeAccumulator::finish);
```

The accumulator is never exposed. Each partition owns one; merging is associative; finishing creates an immutable record. Test empty input, one value, duplicates, and equality of sequential versus parallel results.

### Collector law checklist

- Supplier returns a new empty container every time.
- Accumulation into an empty container represents that one element correctly.
- Combining does not lose, duplicate, reorder (when order matters), or alias data incorrectly.
- Combining in different groupings gives equivalent results.
- Finisher does not mutate shared state or leak a mutable object unintentionally.
- Characteristics describe facts, not wishes.
- Sequential and parallel collection are equivalent for representative and property-generated inputs.

## Collector-selection table

| Need | Collector | Key caveat |
|---|---|---|
| General list/set | `toList` / `toSet` | Concrete type and mutability unspecified |
| Guaranteed unmodifiable list/set | `toUnmodifiableList/Set` | Reject null |
| Specific collection | `toCollection` | Supplier must return a fresh collection |
| Unique-key map | two-arg `toMap` | Duplicate key throws |
| Duplicate policy | three-arg `toMap` | Merge must be associative |
| Ordered/special map | four-arg `toMap` | Choose supplier explicitly |
| Concurrent map | `toConcurrentMap` | No encounter-order guarantee |
| One-to-many classifier | `groupingBy` | Classifier must not return null |
| Concurrent grouping | `groupingByConcurrent` | Collector is unordered |
| Exactly two groups | `partitioningBy` | Both Boolean keys always present |
| Transform inside each group | `mapping` / `flatMapping` | Flat-mapped streams are closed |
| Filter while preserving groups | `filtering` | Unlike upstream filter |
| Finish/wrap downstream result | `collectingAndThen` | Not identity-finish |
| Text | `joining` | Inputs must be `CharSequence` |
| Scalar per group | `counting`, `minBy`, `maxBy` | Extrema return optional |
| Numeric per group | `summing*`, `averaging*`, `summarizing*` | Overflow/precision still apply |
| General downstream fold | `reducing` | Prefer specialized collector when possible |
| Two aggregates in one pass | `teeing` | Every value feeds both downstreams |
| Specialized bounded/stateful result | custom collector | Prove collector laws first |

---

<a id="part-vi-gatherers"></a>

# Part VI — Gatherers

## Gatherer lifecycle and laws

`Stream.gather` and the Gatherer API were finalized in Java 24. A `Gatherer<T,A,R>` is a programmable intermediate operation:

- `T`: upstream input type;
- `A`: private, possibly mutable state; and
- `R`: zero or more downstream output values.

Its four functions are:

```text
initializer: () -> A
integrator:  (A, T, Downstream<R>) -> boolean
combiner:    (A, A) -> A
finisher:    (A, Downstream<R>) -> void
```

The integrator may update state, call `downstream.push(result)` zero or more times, and return whether upstream should continue. `push` returns false when downstream rejects more values, for example after a downstream `limit`. A well-behaved integrator propagates that false result.

### Default sentinel functions

The static `defaultInitializer`, `defaultCombiner`, and `defaultFinisher` return recognized sentinel functions:

- default initializer means stateless; initialization can be skipped;
- default combiner means sequential-only; it is not an ordinary callable merge strategy; and
- default finisher means no end-of-stream action; finishing can be skipped.

Each invocation of the four accessors must return semantically identical functions. Never retain or expose state or a downstream reference beyond the callback receiving it. Once state is passed to a combiner or finisher, it must not return to integration.

### Stateless map gatherer

```java
static <T, R> Gatherer<T, ?, R> mappingGatherer(
        Function<? super T, ? extends R> mapper) {
    return Gatherer.of((unused, element, downstream) ->
        downstream.push(mapper.apply(element)));
}

List<String> names = Fixtures.EMPLOYEES.stream()
    .gather(mappingGatherer(Employee::name))
    .toList();
```

**Result:** `[Asha, Ben, Chen, Diya]`.

This is educational; use `map` for ordinary mapping. The one-integrator `of` factory supplies stateless/default initialization and finishing and a real parallelizable stateless combiner strategy.

### Integrator contracts

`Gatherer.Integrator.of(integrator)` returns the integrator with its normal potentially short-circuiting contract. `ofGreedy(greedyIntegrator)` marks an integrator that never short-circuits; an implementation may ignore its boolean return.

```java
Gatherer<Integer, ?, Integer> doubled = Gatherer.of(
    Gatherer.Integrator.ofGreedy((unused, n, downstream) ->
        downstream.push(n * 2)));
```

Only use `ofGreedy` when the integrator truly never decides to stop. Downstream rejection still means `push` should not be used as an invitation to perform more unnecessary emissions.

### Factory families

| Factory | State | Parallelizable | End-of-stream hook |
|---|---|---|---|
| `ofSequential(integrator)` | Stateless | No | No |
| `ofSequential(integrator, finisher)` | Stateless | No | Yes |
| `ofSequential(initializer, integrator)` | Stateful | No | No |
| `ofSequential(initializer, integrator, finisher)` | Stateful | No | Yes |
| `of(integrator)` | Stateless | Yes | No |
| `of(integrator, finisher)` | Stateless | Yes | Yes |
| `of(initializer, integrator, combiner, finisher)` | Stateful | Yes if laws hold | Yes |

Supplying a combiner is a correctness claim: isolated partition states can be associatively merged into a state equivalent to encounter-order processing. If that cannot be proved, use `ofSequential`; the upstream may still be a parallel stream, but the gathering operation itself must evaluate sequentially.

## Built-in Gatherers

All five Java SE 26 factories are in `java.util.stream.Gatherers`.

### `windowFixed(size)` — non-overlapping batches

```java
List<List<Integer>> windows = Stream.of(1, 2, 3, 4, 5, 6, 7, 8)
    .gather(Gatherers.windowFixed(3))
    .toList();
```

**Result:** `[[1, 2, 3], [4, 5, 6], [7, 8]]`.

Windows preserve encounter order, are unmodifiable, and have no promised concrete type. Empty input emits no window; the last window may be partial. Size below one throws `IllegalArgumentException`. A very large size may allocate eagerly and waste memory even for a small source.

### `windowSliding(size)` — overlapping windows

```java
List<List<Integer>> moving = Stream.of(1, 2, 3, 4)
    .gather(Gatherers.windowSliding(3))
    .toList();
```

**Result:** `[[1, 2, 3], [2, 3, 4]]`.

If non-empty input is shorter than the requested size, exactly one partial window is emitted. Empty input emits none. Windows are unmodifiable; size below one fails. Cost is at least proportional to the produced output—`O(n × windowSize)` values across all copied windows in the general case.

### `fold(initial, folder)` — one final ordered result

```java
Optional<String> joined = Stream.of(1, 2, 3, 4)
    .gather(Gatherers.fold(() -> "", (text, n) -> text + n))
    .findFirst();
```

**Result:** `Optional[1234]`. Empty input emits the supplied initial value. Fold is ordered and intended for intrinsically order-dependent reduction when no correct combiner exists. It emits only one element if processing succeeds. Use `reduce` or `collect` for an associative reduction that can parallelize naturally.

### `scan(initial, scanner)` — every running result

```java
List<Long> balances = Fixtures.TRANSACTIONS.stream()
    .filter(t -> t.account().equals("A"))
    .gather(Gatherers.scan(
        () -> 0L,
        (balance, tx) -> balance +
            (tx.type() == TransactionType.CREDIT
                ? tx.minorUnits() : -tx.minorUnits())))
    .toList();
```

**Result:** `[10000, 7500]`.

Scan emits after each input; it does not emit the initial value by itself. Empty input emits nothing. It is an ordered prefix operation and generally sequential because later values depend on the exact preceding state.

### `mapConcurrent(maxConcurrency, mapper)` — ordered bounded concurrency

```java
List<String> normalized = Stream.of(" a ", " b ", " c ")
    .gather(Gatherers.mapConcurrent(4, value ->
        value.strip().toUpperCase(Locale.ROOT)))
    .toList();
```

**Result:** `[A, B, C]`.

The mapper runs concurrently on virtual threads up to the positive limit, while outputs preserve encounter order. This is valuable for independently blocking transformations; it does not make database transactions, remote side effects, rate limits, or non-thread-safe clients safe. If a mapper fails when its ordered result is due, the operation rethrows a runtime exception and attempts best-effort cancellation of remaining tasks. Cancellation does not guarantee that external side effects stop.

## Custom stateless and stateful gatherers

### Stateless filtering

```java
static <T> Gatherer<T, ?, T> filteringGatherer(
        Predicate<? super T> predicate) {
    return Gatherer.of((unused, element, downstream) ->
        !predicate.test(element) || downstream.push(element));
}
```

If the predicate fails, the gatherer emits nothing and continues. If it passes, the downstream's acceptance becomes the continuation result. Prefer ordinary `filter`; this shows zero-output integration.

### Stateful zip-with-index

```java
record Indexed<T>(long index, T value) {}

static <T> Gatherer<T, ?, Indexed<T>> withIndex() {
    return Gatherer.<T, long[], Indexed<T>>ofSequential(
        () -> new long[] {0L},
        Gatherer.Integrator.ofGreedy((state, element, downstream) ->
            downstream.push(new Indexed<>(state[0]++, element))));
}

List<Indexed<String>> indexed = Stream.of("A", "B", "C")
    .gather(withIndex())
    .toList();
```

**Result:** `[Indexed[index=0, value=A], Indexed[index=1, value=B], Indexed[index=2, value=C]]`.

This gatherer is deliberately sequential: global encounter indexes cannot be assigned to arbitrary partitions without knowing preceding partition sizes and correcting outputs. The state is created per evaluation, not captured externally.

### Distinct until changed

```java
static <T> Gatherer<T, ?, T> distinctUntilChanged() {
    class State {
        T previous;
        boolean seen;
    }
    return Gatherer.<T, State, T>ofSequential(
        State::new,
        (state, element, downstream) -> {
            if (!state.seen || !Objects.equals(state.previous, element)) {
                state.previous = element;
                state.seen = true;
                return downstream.push(element);
            }
            return true;
        });
}

List<String> changes = Stream.of("A", "A", "B", "B", "A")
    .gather(distinctUntilChanged())
    .toList();
```

**Result:** `[A, B, A]`. Unlike `distinct`, this remembers only the previous value and permits a value to reappear after a change. Space is `O(1)`.

### Adjacent pairs

```java
record Pair<T>(T left, T right) {}

static <T> Gatherer<T, ?, Pair<T>> adjacentPairs() {
    class State { T previous; boolean seen; }
    return Gatherer.<T, State, Pair<T>>ofSequential(
        State::new,
        (state, current, downstream) -> {
            if (!state.seen) {
                state.previous = current;
                state.seen = true;
                return true;
            }
            Pair<T> pair = new Pair<>(state.previous, current);
            state.previous = current;
            return downstream.push(pair);
        });
}
```

Input `[1,2,4,7]` emits `(1,2)`, `(2,4)`, `(4,7)`. Empty/single input emits none. Use `windowSliding(2)` when list windows are sufficient; a pair record gives a clearer domain type.

### Custom batching with finisher

```java
static <T> Gatherer<T, ?, List<T>> batches(int size) {
    if (size < 1) throw new IllegalArgumentException("size must be positive");
    return Gatherer.<T, ArrayList<T>, List<T>>ofSequential(
        ArrayList::new,
        (buffer, element, downstream) -> {
            buffer.add(element);
            if (buffer.size() < size) return true;
            List<T> batch = List.copyOf(buffer);
            buffer.clear();
            return downstream.push(batch);
        },
        (buffer, downstream) -> {
            if (!buffer.isEmpty() && !downstream.isRejecting()) {
                downstream.push(List.copyOf(buffer));
            }
        });
}
```

This reproduces fixed windows to demonstrate end-of-input finishing. `List.copyOf` prevents later buffer mutation from changing emitted windows. Prefer `Gatherers.windowFixed` in real code.

## Early termination and parallel-capable gatherers

### Take through a boundary, inclusively

```java
static <T> Gatherer<T, ?, T> takeUntilInclusive(
        Predicate<? super T> stop) {
    return Gatherer.ofSequential((unused, element, downstream) -> {
        boolean accepted = downstream.push(element);
        return accepted && !stop.test(element);
    });
}

List<Integer> throughFive = Stream.of(1, 2, 5, 6, 7)
    .gather(takeUntilInclusive(n -> n == 5))
    .toList();
```

**Result:** `[1, 2, 5]`.

Returning false tells the framework to stop passing upstream values. The boundary value is pushed before the stop decision. If downstream already rejects it, the gatherer also stops. This behavior cannot be expressed by `takeWhile`, which excludes the first predicate failure.

### A truly parallel-capable stateful gatherer

```java
static <T> Gatherer<T, ?, Long> countingGatherer() {
    return Gatherer.of(
        () -> new long[] {0L},
        Gatherer.Integrator.ofGreedy((state, element, downstream) -> {
            state[0]++;
            return true;
        }),
        (left, right) -> {
            left[0] = Math.addExact(left[0], right[0]);
            return left;
        },
        (state, downstream) -> downstream.push(state[0]));
}
```

Each partition counts independently; addition is associative; the finisher emits one combined count. This is lawful in parallel. It is still the wrong production tool—use `count()`—but it demonstrates the requirements. Parallelizing a stateful gatherer is not achieved by adding a combiner that discards one state or merely mutates shared state.

### Early termination in parallel

When an earlier ordered partition short-circuits, state and outputs from later partitions must be discarded. That can waste speculative work. A short-circuiting custom gatherer should therefore be sequential unless its combiner and cancellation semantics are rigorously designed. Finishers must check `downstream.isRejecting()` before emitting optional tail data.

## Gatherer composition and selection

`andThen` connects one gatherer's outputs directly to another's inputs:

```java
Gatherer<Integer, ?, Integer> doubleValues = mappingGatherer(n -> n * 2);
Gatherer<Integer, ?, List<Integer>> windows = Gatherers.windowFixed(2);

List<List<Integer>> result = Stream.of(1, 2, 3, 4)
    .gather(doubleValues.andThen(windows))
    .toList();
```

**Result:** `[[2, 4], [6, 8]]`.

Composition is semantically equivalent to consecutive gathering stages and can enable implementation fusion. It should still tell one clear story; named gatherers help. Null composition arguments throw `NullPointerException`.

Gatherers remain intermediate, so a normal collector can finish them:

```java
Map<Integer, Long> windowSizes = Stream.of(1, 2, 3, 4, 5)
    .gather(Gatherers.windowFixed(2))
    .collect(Collectors.groupingBy(List::size, Collectors.counting()));
// {1=1, 2=2}
```

| Need | Best default |
|---|---|
| One output per input | `map` |
| Keep/discard each independently | `filter` |
| Existing nested stream/collection | `flatMap` |
| Small imperative zero-to-many output | `mapMulti` |
| State across inputs / windows / scans | built-in or custom `gather` |
| One final mutable aggregate | `collect` |
| New traversal/source | `Spliterator` + `StreamSupport` |
| Index-heavy mutation or complex control flow | loop |

**Design rule:** use the narrowest standard operation first. A gatherer is powerful because it centralizes state and short-circuiting contracts, not because it makes a familiar `map` look more advanced.

---

<a id="part-vii-spliterators-and-execution-mechanics"></a>

# Part VII — Spliterators and execution mechanics

## Iterator versus Spliterator

An `Iterator` advances sequentially with `hasNext`/`next`. A `Spliterator` (“splitable iterator”) can traverse, describe, and optionally partition a source. Streams use spliterators to understand order, size, sortedness, distinctness, immutability/concurrency, and parallel decomposition.

| Capability | Iterator | Spliterator |
|---|---|---|
| Advance one | `next()` | `tryAdvance(action)` |
| Traverse remainder | loop / `forEachRemaining` | `forEachRemaining(action)` |
| Partition | No standard support | `trySplit()` |
| Estimate remaining size | No | `estimateSize()` |
| Declare characteristics | No | `characteristics()` |
| Primitive specializations | `PrimitiveIterator` | `Spliterator.OfInt/OfLong/OfDouble` |

Spliterators are not reusable. After handing one to `StreamSupport`, do not also traverse it manually.

## Traversal, splitting, sizing, and characteristics

- `tryAdvance(action)` performs the action on the next element and returns true, or returns false at exhaustion.
- `forEachRemaining(action)` consumes the rest, usually more efficiently than repeated external calls.
- `trySplit()` partitions remaining elements, returning a prefix/partition while the original retains the rest, or null when splitting is unsuitable.
- `estimateSize()` returns an estimate or `Long.MAX_VALUE` when effectively unknown.
- `getExactSizeIfKnown()` returns the size when `SIZED`, otherwise `-1`.
- `characteristics()` is a bit set of promises.
- `hasCharacteristics(bits)` tests promises.
- `getComparator()` returns the comparator for a `SORTED` spliterator, null for natural order, and otherwise throws `IllegalStateException`.

### The eight standard characteristics

| Flag | Promise |
|---|---|
| `ORDERED` | Defined encounter order exists |
| `DISTINCT` | No equal pair exists |
| `SORTED` | Encounter order follows a comparator or natural order; also implies `ORDERED` |
| `SIZED` | Exact remaining size is known before traversal |
| `NONNULL` | No element is null |
| `IMMUTABLE` | Source cannot be structurally modified during traversal |
| `CONCURRENT` | Source can be safely structurally modified under its documented policy |
| `SUBSIZED` | This spliterator and all splits are `SIZED` |

Characteristics are correctness commitments. Marking an unsorted source `SORTED`, returning a changing “exact” size under `SIZED`, or claiming `DISTINCT` for duplicates can allow the pipeline to omit needed work and return a wrong result.

Good splitting is balanced, cheap relative to element work, and preserves characteristics. A split should reduce both sides meaningfully; producing one-element splits for a huge source creates overhead, while refusing to split eliminates parallelism.

## StreamSupport

Java SE 26 exposes eight factories: direct and supplier forms for object, int, long, and double streams.

```java
Stream<T> stream(Spliterator<T> source, boolean parallel)
Stream<T> stream(Supplier<? extends Spliterator<T>> source,
                 int characteristics, boolean parallel)

IntStream intStream(Spliterator.OfInt source, boolean parallel)
IntStream intStream(Supplier<? extends Spliterator.OfInt> source,
                    int characteristics, boolean parallel)
// Equivalent pairs exist for longStream and doubleStream.
```

The direct form binds the spliterator immediately. The supplier form defers binding until the terminal operation begins, which narrows the interference window. The supplier is called at most once and must produce a spliterator compatible with the declared characteristics.

```java
Supplier<Spliterator<String>> latestSnapshot =
    () -> List.of("A", "B", "C").spliterator();

List<String> values = StreamSupport.stream(
        latestSnapshot,
        Spliterator.ORDERED | Spliterator.SIZED | Spliterator.SUBSIZED,
        false)
    .toList();
```

**Result:** `[A, B, C]`.

The boolean sets the initial execution mode; it does not make a poor source split well. If the source owns a closeable resource, add an `onClose` handler and still use try-with-resources on the resulting stream.

## Custom source examples

### Expert — balanced integer range

This educational spliterator behaves like a half-open integer range. Prefer `IntStream.range` in real code.

```java
final class RangeSpliterator implements Spliterator.OfInt {
    private int current;
    private final int fence;

    RangeSpliterator(int current, int fence) {
        this.current = current;
        this.fence = fence;
    }

    @Override
    public boolean tryAdvance(IntConsumer action) {
        Objects.requireNonNull(action);
        if (current >= fence) return false;
        action.accept(current++);
        return true;
    }

    @Override
    public OfInt trySplit() {
        int lo = current;
        int mid = lo + ((fence - lo) >>> 1);
        if (mid <= lo) return null;
        current = mid;
        return new RangeSpliterator(lo, mid);
    }

    @Override public long estimateSize() { return (long) fence - current; }

    @Override public int characteristics() {
        return ORDERED | DISTINCT | SORTED | SIZED |
               NONNULL | IMMUTABLE | SUBSIZED;
    }

    @Override public Comparator<? super Integer> getComparator() {
        return null; // natural order
    }
}

int sum = StreamSupport.intStream(new RangeSpliterator(1, 5), true).sum();
```

**Result:** `10`. Splits are balanced, sized, naturally sorted, distinct, and immutable. Arithmetic uses `long` in `estimateSize` to avoid subtraction overflow.

### Depth-first tree traversal with cycle protection

```java
static <T> Stream<TreeNode<T>> depthFirst(TreeNode<T> root) {
    Spliterator<TreeNode<T>> source =
        new Spliterators.AbstractSpliterator<>(
            Long.MAX_VALUE, Spliterator.ORDERED | Spliterator.NONNULL) {

            final Deque<TreeNode<T>> stack = new ArrayDeque<>(List.of(root));
            final Set<TreeNode<T>> seen =
                Collections.newSetFromMap(new IdentityHashMap<>());

            @Override
            public boolean tryAdvance(Consumer<? super TreeNode<T>> action) {
                while (!stack.isEmpty()) {
                    TreeNode<T> node = stack.pop();
                    if (!seen.add(node)) continue;
                    List<TreeNode<T>> children = node.children();
                    for (int i = children.size() - 1; i >= 0; i--) {
                        stack.push(children.get(i));
                    }
                    action.accept(node);
                    return true;
                }
                return false;
            }
        };
    return StreamSupport.stream(source, false);
}
```

**Explanation:** the stack preserves left-to-right depth-first encounter order. Identity-based cycle protection handles graph-shaped input without treating equal-but-distinct nodes as the same object. Size is unknown and splitting is not meaningfully implemented, so the stream is sequential. A simple explicit loop may be easier when traversal also mutates or prunes the tree.

### Batches from an arbitrary spliterator

```java
static <T> Spliterator<List<T>> batching(
        Spliterator<T> source, int batchSize) {
    if (batchSize < 1) throw new IllegalArgumentException();
    long remaining = source.estimateSize();
    long estimatedBatches = remaining == Long.MAX_VALUE
        ? Long.MAX_VALUE
        : remaining / batchSize + (remaining % batchSize == 0 ? 0 : 1);

    return new Spliterators.AbstractSpliterator<>(
            estimatedBatches,
            source.characteristics() &
                (Spliterator.ORDERED | Spliterator.IMMUTABLE)) {
        @Override
        public boolean tryAdvance(Consumer<? super List<T>> action) {
            ArrayList<T> batch = new ArrayList<>(batchSize);
            while (batch.size() < batchSize && source.tryAdvance(batch::add)) {}
            if (batch.isEmpty()) return false;
            action.accept(List.copyOf(batch));
            return true;
        }
    };
}
```

This illustrates a source adapter, but its size formula is only exact when the input is genuinely sized, and the default abstract splitting policy may not match desired batch boundaries. `Gatherers.windowFixed` is the preferred Java 24+ pipeline operation. Use a custom spliterator when batching is intrinsic to the source abstraction itself.

---

<a id="part-viii-meaningful-combinations-and-recipes"></a>

# Part VIII — Meaningful combinations and recipes

## Transformation, null, and Optional recipes

### Basic — select, normalize, project, and sort

**Problem:** produce normalized names of active engineers.

```java
List<String> names = Fixtures.EMPLOYEES.stream()
    .filter(Employee::active)
    .filter(e -> e.department() == Department.ENGINEERING)
    .map(Employee::name)
    .map(name -> name.strip().toUpperCase(Locale.ROOT))
    .sorted()
    .toList();
```

**Result:** `[ASHA]`.

**Explanation:** the pipeline narrows the domain before transforming strings, then imposes deterministic output order. It is `O(n + r log r)` for `r` retained employees and does not mutate the source. A loop is equally valid when several conditions need shared diagnostics or early domain-specific error handling.

### Zero, one, and many outputs

| Cardinality per input | Idiom |
|---|---|
| Exactly one | `map` |
| Zero or one by predicate | `filter` then `map` |
| Nullable zero or one | `flatMap(x -> Stream.ofNullable(...))` |
| Optional zero or one | `flatMap(x -> optional(...).stream())` |
| Existing collection/stream many | `flatMap` |
| Small imperative zero-to-many | `mapMulti` |
| Cross-input state | `gather` |

```java
List<String> countries = Fixtures.EMPLOYEES.stream()
    .flatMap(e -> Optional.ofNullable(e.address()).stream())
    .map(Address::country)
    .distinct()
    .sorted()
    .toList();
```

**Result:** `[IN, SG]`. `Optional.stream()` (Java 9) turns empty into zero values and present into one. It is useful at a Stream boundary; do not wrap every non-null field in `Optional` solely to make a pipeline look functional.

### Flatten nested collections and compute exact totals

```java
Map<String, BigDecimal> revenueBySku = Fixtures.ORDERS.stream()
    .flatMap(order -> order.items().stream())
    .collect(Collectors.groupingBy(
        LineItem::sku,
        Collectors.reducing(
            BigDecimal.ZERO,
            LineItem::total,
            BigDecimal::add)));
```

**Result:** `{BOOK=37.50, PEN=3.60}` (map display order is unspecified).

`flatMap` removes the order boundary; grouping then aggregates exact decimal values. Complexity is `O(total line items)` expected plus result-map storage.

### Null policy, not merely null filtering

Choose explicitly:

```java
// Absence is allowed: discard missing address.
List<Address> known = Fixtures.EMPLOYEES.stream()
    .map(Employee::address)
    .flatMap(Stream::ofNullable)
    .toList();

// Absence is invalid: collect affected employee IDs.
List<Integer> missingAddressIds = Fixtures.EMPLOYEES.stream()
    .filter(e -> e.address() == null)
    .map(Employee::id)
    .toList();

// Absence needs a display value: map it.
List<String> cities = Fixtures.EMPLOYEES.stream()
    .map(e -> e.address() == null ? "UNKNOWN" : e.address().city())
    .toList();
```

Silently applying `Objects::nonNull` is only correct for the first policy.

### Stable deduplication by a key

`distinct` uses whole-object equality. To retain the first employee for each name while preserving encounter order:

```java
List<Employee> firstByName = new ArrayList<>(
    Fixtures.EMPLOYEES.stream().collect(Collectors.toMap(
        Employee::name,
        Function.identity(),
        (first, ignored) -> first,
        LinkedHashMap::new)).values());
```

**Explanation:** a linked map defines stable first-wins semantics. A captured `HashSet` inside `filter` is an unsafe stateful predicate, especially in parallel. Complexity is expected `O(n)` time and `O(unique keys)` space.

## Aggregation and map recipes

### Frequency map / histogram

```java
Map<String, Long> skillFrequency = Fixtures.EMPLOYEES.stream()
    .flatMap(e -> e.skills().stream())
    .collect(Collectors.groupingBy(
        Function.identity(),
        Collectors.counting()));
```

This is the canonical histogram. If deterministic display order is required, use the three-argument `groupingBy` with `TreeMap::new` or sort entries at the presentation boundary.

### Nested aggregate with multiple metrics

```java
record DepartmentMetrics(long count, BigDecimal payroll) {}

Map<Department, DepartmentMetrics> metrics = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(
        Employee::department,
        () -> new EnumMap<>(Department.class),
        Collectors.teeing(
            Collectors.counting(),
            Collectors.reducing(
                BigDecimal.ZERO, Employee::salary, BigDecimal::add),
            DepartmentMetrics::new)));
```

`groupingBy` establishes one partition per department; `teeing` computes headcount and exact payroll over each partition. Each employee is supplied to both downstream collectors. Complexity is `O(n)` time and `O(number of departments)` result state.

### Invert a map when values are not unique

```java
Map<Department, List<Integer>> employeeIdsByDepartment =
    Fixtures.EMPLOYEES.stream().collect(Collectors.groupingBy(
        Employee::department,
        Collectors.mapping(Employee::id, Collectors.toList())));
```

Inversion from employee ID → department is one-to-many in reverse, so `Map<Department,List<Integer>>` is correct. `toMap(Employee::department, Employee::id)` would throw on duplicates or lose data under an arbitrary merge rule.

### Deterministic immutable map

```java
Map<Integer, String> immutable = Collections.unmodifiableMap(
    Fixtures.EMPLOYEES.stream().collect(Collectors.toMap(
        Employee::id,
        Employee::name,
        (left, right) -> { throw new IllegalStateException("duplicate ID"); },
        LinkedHashMap::new)));
```

The supplied map preserves order; the wrapper prevents mutation but remains a view over the map created inside the pipeline (which is no longer otherwise referenced). `toUnmodifiableMap` is simpler when map iteration order is irrelevant.

## Relational and positional recipes

### Inner and left lookup joins

```java
record Customer(int id, String name) {}
record OrderCustomer(Order order, Customer customer) {}
record OrderMaybeCustomer(Order order, Optional<Customer> customer) {}

List<Customer> customers = List.of(
    new Customer(10, "Ravi"),
    new Customer(11, "Mina"));

Map<Integer, Customer> customerById = customers.stream()
    .collect(Collectors.toMap(Customer::id, Function.identity()));

List<OrderCustomer> inner = Fixtures.ORDERS.stream()
    .filter(order -> customerById.containsKey(order.customerId()))
    .map(order -> new OrderCustomer(
        order, customerById.get(order.customerId())))
    .toList();

List<OrderMaybeCustomer> left = Fixtures.ORDERS.stream()
    .map(order -> new OrderMaybeCustomer(
        order, Optional.ofNullable(customerById.get(order.customerId()))))
    .toList();
```

**Explanation:** indexing the smaller/right relation gives expected `O(customers + orders)` work. Nesting `customers.stream().filter(...)` inside each order would be `O(customers × orders)`. A database join is preferable when data already lives in a database.

A full outer join can concatenate the left result with customers whose IDs are absent from an `orderCustomerIds` set. Use a sealed/domain result type that can represent “missing order” and “missing customer” instead of null-filled pairs.

### Cartesian product

```java
record Combination(String color, String size) {}

List<Combination> combinations = Stream.of("red", "blue")
    .flatMap(color -> Stream.of("S", "M", "L")
        .map(size -> new Combination(color, size)))
    .toList();
```

**Result:** six combinations in color-major order. Output size is `O(n × m)` by definition; add filters early but do not pretend the product is cheap for large inputs.

### Zip two random-access lists

```java
List<String> names = List.of("Asha", "Ben", "Chen");
List<Integer> scores = List.of(90, 82, 95, 77);

record Scored(String name, int score) {}

List<Scored> zipped = IntStream.range(0, Math.min(names.size(), scores.size()))
    .mapToObj(i -> new Scored(names.get(i), scores.get(i)))
    .toList();
```

**Result:** `[Scored[name=Asha, score=90], Scored[name=Ben, score=82], Scored[name=Chen, score=95]]`.

This truncates to the shorter list. Validate equal sizes instead if mismatch is invalid. This is efficient only for random-access lists; linked-list `get(i)` makes it quadratic. Use paired iterators/custom spliterator or a loop for general sequences. `withIndex()` and `adjacentPairs()` in Part VI cover indexing and neighbors for arbitrary streams.

### Ranking, top-N, and stable ties

```java
List<Employee> topTwo = Fixtures.EMPLOYEES.stream()
    .sorted(Comparator.comparing(Employee::salary).reversed()
        .thenComparingInt(Employee::id))
    .limit(2)
    .toList();
```

**Result:** Chen then Asha. The ID tie-breaker makes results reproducible. Full sorting costs `O(n log n)`; the custom top-N collector retains `O(k)` per partition and is better for large `n`, small `k` after measurement.

For page `p` and size `s`, use `skip(Math.multiplyExact(p, s)).limit(s)` only for already materialized, modest data. Source-level keyset/cursor pagination is the production choice for large datasets.

## Temporal and stateful recipes

### Fixed batches and sliding averages

```java
List<List<Transaction>> batches = Fixtures.TRANSACTIONS.stream()
    .gather(Gatherers.windowFixed(2))
    .toList();

List<Double> movingAverage = Stream.of(10L, 20L, 30L, 40L)
    .gather(Gatherers.windowSliding(3))
    .map(window -> window.stream().mapToLong(Long::longValue).average().orElseThrow())
    .toList();
```

**Results:** transaction batches of sizes two and one; moving averages `[20.0, 30.0]`. Sliding windows copy/output multiple values, so space/time scale with window size.

### Running balance and fold

Use `scan` to emit every intermediate balance and `fold` to emit one final ordered result. Use `reduce` instead of fold when the operation is associative and a combiner exists. The account-balance scan in Part VI is the canonical example.

### Session segmentation

Events can be grouped into sessions by a gap threshold with a sequential gatherer. Its state holds the current session; on a gap it pushes an immutable copy and starts another; the finisher pushes the final session. This is the same lifecycle as the custom batch gatherer, but the flush predicate compares adjacent timestamps rather than a count.

```java
// Core integrator decision inside Gatherer.ofSequential(...):
if (!session.isEmpty() &&
    Duration.between(session.getLast().occurredAt(), event.occurredAt())
        .compareTo(Duration.ofMinutes(30)) > 0) {
    if (!downstream.push(List.copyOf(session))) return false;
    session.clear();
}
session.add(event);
return true;
```

**Caveat:** input must first be encounter-ordered by timestamp. Sorting an unbounded event stream is impossible; sessionize bounded ordered input or use a streaming system designed for watermarks and late events.

Consecutive-status deduplication uses `distinctUntilChanged`; global duplicate removal uses `distinct`. They solve different problems.

## Traversal, text, and I/O recipes

### Resource-safe word frequency

```java
Path file = Path.of("notes.txt");
Map<String, Long> frequency;

try (Stream<String> lines = Files.lines(file, StandardCharsets.UTF_8)) {
    frequency = lines
        .flatMap(line -> Pattern.compile("[^\\p{L}\\p{N}]+").splitAsStream(line))
        .map(token -> token.toLowerCase(Locale.ROOT))
        .filter(token -> !token.isBlank())
        .collect(Collectors.groupingBy(
            Function.identity(),
            Collectors.counting()));
}
```

**Explanation:** traversal, tokenization, normalization, empty-token removal, and aggregation remain inside the resource scope. The regex accepts Unicode letters/numbers. Compiling the `Pattern` once outside the line lambda avoids repeated compilation in hot code.

### Directory inventory

```java
record FileInfo(Path path, long bytes) {}

try (Stream<Path> paths = Files.find(
        Path.of("data"), 5, (path, attrs) -> attrs.isRegularFile())) {
    List<FileInfo> largest = paths
        .map(path -> {
            try { return new FileInfo(path, Files.size(path)); }
            catch (IOException ex) { throw new UncheckedIOException(ex); }
        })
        .sorted(Comparator.comparingLong(FileInfo::bytes).reversed())
        .limit(10)
        .toList();
}
```

This intentionally translates a checked `IOException` at a narrow boundary. If partial success is required, map each path to a success/error result instead of aborting the pipeline.

Tree traversal, JAR entries, scanner tokens, regex matches, Unicode code points, random samples, bit positions, and service providers are covered in Parts II and VII. The recurring rules are close owned resources, distinguish ordered from unordered sources, and avoid parallelizing inherently sequential I/O traversal.

## Validation, errors, statistics, and reconciliation

### Collect every validation error

```java
record Violation(int employeeId, String message) {}

List<Violation> violations = Fixtures.EMPLOYEES.stream()
    .<Violation>mapMulti((employee, emit) -> {
        if (employee.name().isBlank())
            emit.accept(new Violation(employee.id(), "blank name"));
        if (employee.salary().signum() <= 0)
            emit.accept(new Violation(employee.id(), "non-positive salary"));
        if (employee.address() == null)
            emit.accept(new Violation(employee.id(), "missing address"));
    })
    .toList();
```

**Result:** one violation for Ben's missing address.

`mapMulti` expresses zero-to-many errors without exceptions as control flow. For fail-fast validation, use `findFirst` after mapping invalid values. For validation that depends on several evolving fields or requires rich branching, a named imperative validator is clearer.

### Partition successes and failures

Model the result explicitly:

```java
sealed interface ParseResult<T> permits Parsed, ParseFailure {}
record Parsed<T>(T value) implements ParseResult<T> {}
record ParseFailure<T>(String input, String message) implements ParseResult<T> {}

List<ParseResult<Integer>> parsed = Stream.of("10", "oops", "20")
    .<ParseResult<Integer>>map(text -> {
        try { return new Parsed<Integer>(Integer.parseInt(text)); }
        catch (NumberFormatException ex) {
            return new ParseFailure<Integer>(text, ex.getMessage());
        }
    })
    .toList();
```

This preserves every outcome. A later partition/group can separate result variants. Do not catch `Exception` broadly and replace errors with null.

### Exact money and percentiles

```java
BigDecimal orderTotal = Fixtures.ORDERS.stream()
    .flatMap(order -> order.items().stream())
    .map(LineItem::total)
    .reduce(BigDecimal.ZERO, BigDecimal::add); // 41.10

double median = IntStream.of(9, 1, 5, 2, 7)
    .sorted()
    .skip(2)
    .findFirst()
    .orElseThrow(); // 5
```

Exact money stays decimal. True percentiles generally require ordering/materialization or an approximate data structure not supplied by `java.util.stream`; document the chosen percentile definition, interpolation, and empty-input policy.

### Diff and reconciliation

```java
Set<String> expected = Set.of("T-1", "T-2", "T-4");
Set<String> actual = Fixtures.TRANSACTIONS.stream()
    .map(Transaction::id)
    .collect(Collectors.toSet());

Set<String> missing = expected.stream()
    .filter(id -> !actual.contains(id))
    .collect(Collectors.toUnmodifiableSet());

Set<String> unexpected = actual.stream()
    .filter(id -> !expected.contains(id))
    .collect(Collectors.toUnmodifiableSet());
```

**Results:** `missing={T-4}` and `unexpected={T-3}` (set display order unspecified).

Prebuilding sets gives expected `O(n + m)` membership work. For duplicate-sensitive reconciliation, compare frequency maps instead of sets. For keyed value mismatches, build maps with an explicit duplicate policy and compare common keys field by field.

---

<a id="part-ix-parallelism-performance-and-production-safety"></a>

# Part IX — Parallelism, performance, and production safety

## Parallel execution model

A parallel pipeline recursively splits the source, processes leaf partitions, and combines or coordinates results. `parallelStream()` and `parallel()` request this mode; `sequential()` reverses it. The API does not let a pipeline choose an executor. Standard JDK execution normally uses fork/join infrastructure associated with the common pool, but code should not depend on undocumented pool-selection details.

Parallel does **not** mean one thread per stage. Stages are fused per partition: a worker pulls an element through `filter`, `map`, and later stateless stages before taking another. Stateful barriers may require completing and coordinating one stage before the next can proceed.

Operations that constrain parallelism include:

- ordered `distinct`, `limit`, `skip`, `takeWhile`, and `dropWhile`;
- `sorted`, which buffers all input;
- `findFirst` and `forEachOrdered`, which preserve encounter order;
- sequential-only gatherers; and
- sources that split poorly, such as iterators, readers, and I/O channels.

Short-circuit cancellation is cooperative and may leave already-started partition work. Never assume `anyMatch` prevents all later side effects.

## Correctness laws and shared state

Parallel correctness follows the same laws already introduced:

- behavioral functions are stateless and non-interfering;
- reduction operators are associative and have valid identities;
- collectors provide isolated containers or truly concurrent accumulation;
- gatherer combiners reconstruct a result equivalent to ordered semantics;
- encounter order is preserved only when required by the source/operations; and
- custom spliterators advertise only true characteristics.

### Incorrect — shared mutable result

```java
List<Integer> shared = new ArrayList<>();
IntStream.range(0, 10_000).parallel().forEach(shared::add); // data race
```

The result can lose values, corrupt internal array state, or fail. A synchronized list prevents structural corruption but still couples correctness/performance to side effects and gives arbitrary encounter order.

### Correct — isolated mutable reduction

```java
List<Integer> values = IntStream.range(0, 10_000)
    .parallel()
    .boxed()
    .toList();
```

The framework creates/combines internal result storage and preserves encounter order. For an unordered set-like result, collect to an appropriate set and compare by set equality.

### Side effects and happens-before

Except where an operation explicitly states ordering (notably `forEachOrdered`), there is no guarantee about the thread or timing of action execution. Thread-local context may not be present. Locks around a side effect can serialize the workload and remove any benefit. External calls can outlive cancellation and cannot generally be rolled back.

Test a supposedly parallel-capable reduction, collector, or gatherer with:

```java
R sequential = input.stream().collect(candidate);
R parallel = input.parallelStream().collect(candidate);
assert equivalent(sequential, parallel);
```

Run this over empty, one-element, duplicate-heavy, ordered, randomized, and large inputs. One passing example is evidence, not a proof of associativity.

## Performance decision framework

Parallel Streams help only when saved compute exceeds splitting, scheduling, coordination, allocation, memory traffic, and merging costs.

Ask in this order:

1. **Is the result lawful in parallel?** If not, stop.
2. **Is the source large, in memory, and cheaply balanced?** Arrays and array-backed lists are strong; iterators/I/O are weak.
3. **Is per-element work substantial and independent?** Tiny arithmetic rarely amortizes overhead.
4. **Are there full barriers or strict ordering constraints?** They reduce scalability.
5. **Is the environment free to use shared parallel resources?** Server workloads may contend with unrelated work.
6. **Has a representative benchmark shown an improvement?** Intuition is insufficient.

### Allocation and boxing

Prefer `mapToInt(...).sum()` to `map(...).reduce(...)` for primitive numeric work. Avoid creating temporary lists, streams, or optionals per element when a direct operation expresses the result. But do not sacrifice domain correctness—for exact money, `BigDecimal` is more important than primitive speed.

### Complexity traps

- `distinct`: expected hash-based `O(n)` time and `O(u)` unique storage, but equality/hash quality matters.
- `sorted`: `O(n log n)` time and `O(n)` storage.
- nested stream lookup without an index: often `O(n × m)`; pre-index to make lookups near `O(1)` expected.
- repeated `skip` pagination: increasingly large prefixes are traversed.
- sliding windows: output volume itself is `O(n × windowSize)` in copied elements.

### Benchmarking correctly

Use JMH rather than `System.nanoTime` around one pipeline. A useful benchmark:

- warms up until JIT compilation stabilizes;
- consumes results so work cannot be eliminated;
- parameterizes realistic sizes and data distributions;
- compares loop, sequential Stream, and parallel Stream;
- separates setup from measured work;
- uses multiple forks and reports variance; and
- runs under representative CPU/container limits.

There is no universal element-count threshold for parallel Streams. It changes with source, operation cost, core count, memory bandwidth, JVM, and surrounding load.

## Production boundaries

Prefer another construct when:

- an indexed loop expresses in-place mutation or neighbor access more clearly;
- a `break`, labeled control flow, or several evolving variables dominate the algorithm;
- a database can filter/group/join before transferring rows;
- blocking tasks need explicit executor ownership, deadlines, rate limits, retries, or bulkheads;
- asynchronous backpressure and long-lived event streams are required;
- work participates in thread-bound transactions/security/request context;
- the pipeline would hide error recovery or resource ownership; or
- profiling shows boxing, allocation, barriers, or shared-pool contention.

`Gatherers.mapConcurrent` is a bounded, ordered tool for independent mapping on virtual threads; it is not a full task-orchestration framework. Parallel Streams are data parallelism, not a replacement for structured concurrency, explicit service-level scheduling, or reactive backpressure.

When a loop is clearer, use it without apology. Streams are valuable when the code reads as a transformation and their algebraic contracts match the problem.

---

<a id="part-x-failures-testing-debugging-and-maintainability"></a>

# Part X — Failures, testing, debugging, and maintainability

## Failure-mode catalog

| Symptom | Cause / incorrect pattern | Correction | Prevention |
|---|---|---|---|
| `IllegalStateException` after a terminal operation | Reuse: `s.count(); s.findFirst()` | Reopen from source or `Supplier<Stream<T>>` | Store data/supplier, never a consumed stream |
| Nothing runs | Pipeline has only intermediate stages | Add the intended terminal operation | Test the result/side effect, not pipeline construction |
| Expected `peek` action missing | Traversal/stage elided, e.g. sized `count` | Use a real terminal action or collect a result | Never make `peek` business logic |
| `ConcurrentModificationException`/undefined result | Lambda mutates source | Produce a separate result | Keep behavioral functions non-interfering |
| Lost/corrupted values in parallel | Shared `ArrayList`/counter in lambda | `collect`, `toList`, primitive sum, or lawful reduction | No external mutable accumulation |
| `IllegalStateException: duplicate key` | Two-arg `toMap` with duplicate keys | Reject earlier or provide explicit associative merge | Treat duplicate policy as a requirement |
| Mutation throws unexpectedly | Assumed `Stream.toList()` mutable | Copy with `new ArrayList<>(result)` | Document result mutability |
| Null failure in find/sort/unmodifiable collector | Null reached a null-hostile operation | Reject, report, map, or flatten by explicit policy | Define null meaning at boundary |
| Sequential/parallel results differ | Wrong identity/non-associative reduce | Use lawful operator/identity or stay ordered sequential | Test regrouping and parallel equivalence |
| Duplicates explode in custom collector | Supplier returns shared object or combiner aliases/adds to itself | Fresh containers and isolated associative merge | Test container identity and partitions |
| Tail batch missing | Stateful gatherer lacks finisher | Push immutable remainder in finisher | Test empty, exact, and partial windows |
| Work continues after downstream limit | Integrator ignores `push(false)` | Return false and check `isRejecting` in finisher | Test short-circuit consumption count |
| Infinite hang | Full barrier before effective limit | Bound before `sorted`/global `distinct`, or redesign | Trace finite/infinite property per stage |
| File descriptor leak | Resource stream escapes/never closes | Terminal operation inside try-with-resources | Make ownership visible in method API |
| Flaky list order | `forEach`, `findAny`, unordered source, concurrent collector | Require order explicitly or assert order-independent result | Separate semantic order from incidental output |

### Duplicate-key example

```java
// Incorrect: ENGINEERING occurs twice.
// Map<Department, String> broken = Fixtures.EMPLOYEES.stream()
//     .collect(Collectors.toMap(Employee::department, Employee::name));

// Correct, explicit deterministic merge.
Map<Department, String> alphabeticallyFirst = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.toMap(
        Employee::department,
        Employee::name,
        BinaryOperator.minBy(Comparator.naturalOrder())));
```

### Wrong identity example

```java
int wrong = IntStream.of(2, 3, 4).reduce(1, Integer::sum); // 10, not 9
int right = IntStream.of(2, 3, 4).sum();                    // 9
```

One is not the identity for addition. It would also be injected into each parallel partition, amplifying the error.

## Exception handling

Stream functional interfaces do not declare checked exceptions. Choose one of four policies at the boundary:

1. perform the checked operation before/after the pipeline;
2. translate a specific checked exception to an appropriate unchecked type and fail the pipeline;
3. map each input to an explicit success/failure value and continue; or
4. use a loop when local recovery/control flow is clearer.

### Translate I/O narrowly

```java
static long fileSize(Path path) {
    try {
        return Files.size(path);
    } catch (IOException ex) {
        throw new UncheckedIOException("Cannot size " + path, ex);
    }
}

List<Long> sizes = Stream.of(Path.of("a.txt"), Path.of("b.txt"))
    .map(path -> fileSize(path))
    .toList();
```

**Explanation:** the named method isolates translation and preserves the path and cause. The first failure terminates traversal. Use an outcome record like `Parsed`/`ParseFailure` when partial success is required.

### Generic adapter—use sparingly

```java
@FunctionalInterface
interface ThrowingFunction<T, R, E extends Exception> {
    R apply(T value) throws E;
}

static <T, R, E extends Exception> Function<T, R> unchecked(
        ThrowingFunction<T, R, E> function) {
    return value -> {
        try {
            return function.apply(value);
        } catch (RuntimeException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new RuntimeException(ex);
        }
    };
}
```

This compiles but loses domain-specific exception meaning unless wrapped again. Prefer specific named adapters such as `fileSize`. Never use “sneaky throw” to hide a checked contract from callers.

### Close exceptions

Try-with-resources preserves a traversal exception as primary and adds close failures as suppressed exceptions. Inspect `getSuppressed()` during diagnosis. `onClose` handlers behave similarly: handlers run in registration order, the first failure is thrown, and later failures are suppressed.

Parallel pipelines can wrap or rethrow worker exceptions with implementation stack frames, and other partition work may already have run. Stream exception propagation is fail-fast computation, not transactional rollback.

## Debugging pipelines

Use this progression:

1. name the source and expected cardinality;
2. extract complex predicates/mappers into named functions;
3. add a temporary, side-effect-free-enough diagnostic `peek` immediately around the suspicious boundary;
4. reduce the input to a deterministic counterexample;
5. switch to sequential mode to simplify observation, without assuming that fixes a parallel law bug;
6. inspect null/order/duplicate/empty contracts; and
7. compare with a simple loop as an executable oracle.

```java
Predicate<Employee> isActiveEngineer = e ->
    e.active() && e.department() == Department.ENGINEERING;
Function<Employee, String> label = e -> e.id() + ":" + e.name();

List<String> labels = Fixtures.EMPLOYEES.stream()
    .peek(e -> System.err.println("source=" + e))
    .filter(isActiveEngineer)
    .peek(e -> System.err.println("selected=" + e.id()))
    .map(label)
    .toList();
```

Remove diagnostic peeks after the issue is understood. Do not test their output count because optimization may elide traversal. Avoid logging sensitive data or high-volume values.

## Testing Streams, collectors, gatherers, and spliterators

Test behavior and laws, not implementation classes.

```java
List<String> actual = Fixtures.EMPLOYEES.stream()
    .filter(Employee::active)
    .map(Employee::name)
    .toList();

assert actual.equals(List.of("Asha", "Ben", "Diya"));
```

JUnit equivalents use `assertEquals`, `assertThrows`, and invariant assertions, but the plain assertions keep guide examples dependency-free.

### Essential test dimensions

- empty, one, many, duplicates, null according to policy;
- already sorted, reverse sorted, and arbitrary order;
- exact ordered result versus set/multiset equality for unordered results;
- overflow boundaries and floating tolerance;
- exceptions with retained cause and message context;
- resource closed on success and failure;
- no source mutation;
- sequential versus parallel equivalence where parallel is claimed;
- custom collector supplier isolation and associative combining;
- custom gatherer empty/exact/partial finishing and downstream rejection; and
- custom spliterator traversal completeness, no duplicates, split completeness, estimates, comparator, and every advertised characteristic.

### Property-style invariant examples

```java
// Splitting must neither lose nor duplicate values.
List<Integer> sequential = IntStream.range(0, 10_000).boxed().toList();
List<Integer> parallel = IntStream.range(0, 10_000).parallel().boxed().toList();
assert sequential.equals(parallel);

// Distinct is idempotent.
List<String> once = input.stream().distinct().toList();
List<String> twice = once.stream().distinct().toList();
assert once.equals(twice);

// Custom collector result is equivalent in both modes.
assert input.stream().collect(topN(10, order))
    .equals(input.parallelStream().collect(topN(10, order)));
```

To test resource closing, wrap a close flag in `onClose`, use try-with-resources, and assert the flag afterward. For short-circuiting, count source advances in a controlled custom spliterator; do not use `peek` as the counter under test.

## Readability and maintainability

A pipeline is readable when it states one transformation at one abstraction level. Extract a named method when a lambda contains branching, exception translation, nested pipelines, or domain logic that deserves its own tests.

Prefer:

```java
List<PaymentCommand> commands = requests.stream()
    .filter(this::isEligible)
    .map(this::toCommand)
    .toList();
```

over a dense chain of nested ternaries, catches, and mutations. Name intermediate materialized results only when they represent a useful boundary or are reused; never split a pipeline by reusing the same Stream object.

Use a loop when it more directly expresses indexes, several mutable accumulators, localized recovery, early `break`/`continue`, or mutation. Use a database for data-local joins/aggregates, explicit concurrency for service-level task control, and reactive processing for backpressure/long-lived asynchronous streams. Choosing another abstraction is part of expert Stream use.

---

<a id="part-xi-practice-and-quick-reference"></a>

# Part XI — Practice and quick reference

## Progressive exercises and explained solutions

Each solution is one valid answer; compare its contracts and cost, not only its syntax.

### Basic (B1–B5)

**B1 — Active names.** Return active employee names in encounter order.

```java
List<String> answer = Fixtures.EMPLOYEES.stream()
    .filter(Employee::active).map(Employee::name).toList();
```

Result: `[Asha, Ben, Diya]`. `O(n)` time; empty input gives an empty unmodifiable list. A loop is equivalent but longer.

**B2 — Even squares.** Square even integers from 1 through 6.

```java
int[] answer = IntStream.rangeClosed(1, 6)
    .filter(n -> n % 2 == 0).map(n -> n * n).toArray();
```

Result: `[4,16,36]`. `O(n)` time; multiplication can overflow for large inputs. A primitive loop avoids the result array only if consuming immediately.

**B3 — Existence.** Determine whether any salary exceeds 100000.

```java
boolean answer = Fixtures.EMPLOYEES.stream()
    .anyMatch(e -> e.salary().compareTo(new BigDecimal("100000")) > 0);
```

Result: `true`; short-circuits at Chen. Empty input returns false. A loop with `break` has the same asymptotic cost.

**B4 — Longest name.** Find the longest name with deterministic tie-breaking.

```java
Optional<String> answer = Fixtures.EMPLOYEES.stream().map(Employee::name)
    .max(Comparator.comparingInt(String::length).thenComparing(Comparator.naturalOrder()));
```

Result: `Optional[Diya]` under “length, then lexicographically greatest.” State the tie policy; empty input is empty. `O(n)` time.

**B5 — Sorted unique values.** Normalize and sort skills.

```java
List<String> answer = Fixtures.EMPLOYEES.stream()
    .flatMap(e -> e.skills().stream())
    .map(s -> s.toLowerCase(Locale.ROOT))
    .distinct().sorted().toList();
```

The invariant is lowercase, unique, ascending values. Cost is expected `O(m + u log u)` for `m` skills and `u` unique skills; a `TreeSet` collector combines uniqueness and sorting.

### Average (A1–A5)

**A1 — Group names by department.**

```java
Map<Department,List<String>> answer = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(Employee::department,
        () -> new EnumMap<>(Department.class),
        Collectors.mapping(Employee::name, Collectors.toList())));
```

Result has all present departments with encounter-ordered names. `O(n)` expected; empty input yields an empty map.

**A2 — Skill frequency.**

```java
Map<String,Long> answer = Fixtures.EMPLOYEES.stream()
    .flatMap(e -> e.skills().stream())
    .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
```

Invariant: each value equals the number of employees listing that exact skill. Normalize first if case-insensitive; expected `O(m)`.

**A3 — Exact order total.**

```java
BigDecimal answer = Fixtures.ORDERS.stream()
    .flatMap(o -> o.items().stream()).map(LineItem::total)
    .reduce(BigDecimal.ZERO, BigDecimal::add);
```

Result: `41.10`; empty input returns zero. `O(items)` time. A loop may be clearer if currency validation accompanies each item.

**A4 — Active/inactive counts.**

```java
Map<Boolean,Long> answer = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.partitioningBy(Employee::active, Collectors.counting()));
```

Result: `{false=1, true=3}` (display order unspecified); both keys exist, even for an empty source.

**A5 — Duplicate-safe name map.** Keep the smallest employee ID for duplicate names.

```java
Map<String,Integer> answer = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.toMap(Employee::name, Employee::id, Math::min));
```

Expected `O(n)`; null/duplicate policy is explicit. If duplicate names are invalid, use the throwing two-argument form and test the failure.

### Intermediate (I1–I5)

**I1 — Preserve empty department groups while filtering active employees.**

```java
Map<Department,List<Employee>> answer = Fixtures.EMPLOYEES.stream()
    .collect(Collectors.groupingBy(Employee::department,
        Collectors.filtering(Employee::active, Collectors.toList())));
```

Engineering remains with Asha; a department with only inactive members remains with an empty list. Upstream filtering would remove such a key.

**I2 — Compute minimum and maximum salary in one pass.**

```java
record Range(BigDecimal min, BigDecimal max) {}
Optional<Range> answer = Fixtures.EMPLOYEES.stream().collect(Collectors.teeing(
    Collectors.mapping(Employee::salary, Collectors.minBy(Comparator.naturalOrder())),
    Collectors.mapping(Employee::salary, Collectors.maxBy(Comparator.naturalOrder())),
    (min, max) -> min.flatMap(a -> max.map(b -> new Range(a, b)))));
```

Result is present with `72000` and `105000`; empty input is empty. `O(n)` time and constant aggregate state.

**I3 — Zip names and scores safely.**

```java
if (names.size() != scores.size()) throw new IllegalArgumentException("size mismatch");
List<Scored> answer = IntStream.range(0, names.size())
    .mapToObj(i -> new Scored(names.get(i), scores.get(i))).toList();
```

`O(n)` only for random-access lists; use iterators or a loop otherwise. The explicit validation prevents silent truncation.

**I4 — Resource-safe nonblank line count.**

```java
long answer;
try (Stream<String> lines = Files.lines(path)) {
    answer = lines.filter(line -> !line.isBlank()).count();
}
```

The invariant is prompt close on success/failure. I/O can fail lazily with `UncheckedIOException`. A buffered loop enables line-specific checked recovery.

**I5 — Reconcile duplicate-sensitive IDs.**

```java
Map<String,Long> expectedCounts = expectedIds.stream()
    .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
Map<String,Long> actualCounts = actualIds.stream()
    .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
boolean answer = expectedCounts.equals(actualCounts);
```

This compares multisets, unlike sets. Expected `O(n+m)` time/space; sort-and-compare uses less hash structure but `O(n log n)` time and copies.

### Advanced (D1–D5)

**D1 — Top 10 without sorting all input.**

```java
List<Integer> answer = input.stream()
    .collect(topN(10, Comparator.naturalOrder()));
```

The helper in Part V returns descending greatest values, supports empty input and parallel combination, costs `O(n log 10)`, and retains bounded partition state. Full sort is simpler for small input.

**D2 — Diagnose a parallel reduction bug.**

```java
// Broken: non-associative.
int broken = input.parallelStream().reduce(0, (a, b) -> a - b);
// Correct meaning “negative sum.”
int answer = -input.parallelStream().mapToInt(Integer::intValue).sum();
```

Regrouping subtraction changes the result; negated associative addition is lawful. Edge case: negating `Integer.MIN_VALUE` overflows—use long/exact arithmetic if invalid.

**D3 — Stream a custom integer range.**

```java
int answer = StreamSupport.intStream(new RangeSpliterator(1, 101), true).sum();
```

Result: `5050`. Test split completeness and characteristics. Prefer `IntStream.rangeClosed(1,100)` in production.

**D4 — Exact parallel monetary total.**

```java
BigDecimal answer = amounts.parallelStream()
    .reduce(BigDecimal.ZERO, BigDecimal::add);
```

`BigDecimal.add` is associative for values under the same exact arithmetic context; zero is identity. If applying a rounding `MathContext` at every addition, regrouping can change rounding—define rounding at the correct domain boundary.

**D5 — Verify a custom collector law.**

```java
List<Integer> sequential = input.stream().collect(topN(5, Comparator.naturalOrder()));
List<Integer> parallel = input.parallelStream().collect(topN(5, Comparator.naturalOrder()));
assert sequential.equals(parallel);
assert sequential.size() <= 5;
assert IntStream.range(1, sequential.size())
    .allMatch(i -> sequential.get(i - 1) >= sequential.get(i));
```

Run randomized, empty, duplicate, and extreme inputs. These invariants support but do not mathematically prove the combiner law.

### Expert (E1–E5)

**E1 — Attach encounter indexes.**

```java
List<Indexed<String>> answer = Stream.of("A","B","C")
    .gather(withIndex()).toList();
```

Result has indexes 0–2. The sequential gatherer is correct for arbitrary ordered streams; an indexed loop is simpler for lists.

**E2 — Consecutive deduplication.**

```java
List<String> answer = Stream.of("A","A","B","B","A")
    .gather(distinctUntilChanged()).toList();
```

Result: `[A,B,A]`, `O(n)` time/`O(1)` state. Global `distinct` would incorrectly remove the final A.

**E3 — Include a stop boundary.**

```java
List<Integer> answer = Stream.of(1,2,5,6,7)
    .gather(takeUntilInclusive(n -> n == 5)).toList();
```

Result: `[1,2,5]`. Test empty/no-boundary/first-boundary/downstream-limit cases. A loop with `break` is often clearer for one isolated use.

**E4 — Parallel gatherer law.**

```java
long sequential = input.stream().gather(countingGatherer()).findFirst().orElseThrow();
long parallel = input.parallelStream().gather(countingGatherer()).findFirst().orElseThrow();
assert sequential == parallel && sequential == input.size();
```

The state combiner uses exact associative addition. Production code uses `count()`; the exercise tests Gatherer partition reasoning.

**E5 — Choose bounded concurrent mapping.**

```java
List<Response> answer = requests.stream()
    .gather(Gatherers.mapConcurrent(20, client::fetch))
    .toList();
```

Invariant: output order matches request order and at most 20 mappings are in flight. The client must be safe for concurrent calls; deadlines/rate limits/retries/transaction context remain explicit responsibilities. Use structured/executor orchestration when each task needs independent lifecycle control.

## Interview questions and answer rubrics

| Question | Incomplete | Correct | Expert follow-up |
|---|---|---|---|
| Stream versus collection? | “Streams are faster collections.” | Stream is one-use computation; collection stores/reuses data. | Discuss internal iteration, laziness, characteristics, operation elision. |
| Why must lambdas be non-interfering/stateless? | “Style.” | Source mutation/shared state breaks traversal/parallel safety. | Explain allowed optimization and why synchronized side effects still harm semantics. |
| `map` vs `flatMap` vs `mapMulti` vs `gather`? | Names only. | One, nested-many, imperative zero-many, cross-input programmable state. | Compare allocation, downstream rejection, windows, concurrency. |
| `findFirst` vs `findAny`? | “Same.” | First honors encounter order; any permits arbitrary match. | Explain parallel coordination and null-selected-element failure. |
| Why can `peek` not implement auditing? | “It is for debugging.” | Lazy/elidable/thread timing unspecified. | Connect sized `count`, short-circuiting, retries, transactional side effects. |
| Reduction identity/associativity? | Gives syntax. | Identity is neutral; operator regrouping must preserve result. | State accumulator/combiner compatibility and rounding/overflow caveats. |
| `toList()` differences? | “Both return ArrayList.” | Stream form unmodifiable; collector form has unspecified mutability/type. | Add null behavior and `toUnmodifiableList` distinction. |
| Duplicate `toMap` keys? | “Last wins.” | Two-arg form throws; merge form defines policy. | Merge must be associative/deterministic; map supplier controls order/type. |
| `groupingBy` vs `partitioningBy`? | “Both group.” | Multi-key classifier versus exactly two Boolean groups. | Both-key guarantee, downstream filtering, concurrency variants. |
| Collector characteristics? | Lists names. | Defines concurrent, unordered, identity-finish facts. | Explain consequences of false claims and concurrent reduction conditions. |
| Gatherer versus collector? | “Gatherer is newer.” | Gatherer is intermediate zero-many/stateful; collector terminates to one result. | Lifecycle, rejection, finisher, sequential sentinel, combiner. |
| Fixed vs sliding window? | Syntax only. | Non-overlap/partial tail versus overlapping/full or one partial short-input window. | Output complexity, unmodifiable windows, eager allocation. |
| What makes a Spliterator parallel-friendly? | “It implements trySplit.” | Balanced cheap splits, accurate size/characteristics. | Late binding, `SUBSIZED`, sorted comparator, source interference. |
| When parallel Stream? | “Large list.” | Lawful, splittable source, substantial independent CPU work, measured. | Shared pool, barriers, ordering, boxing, workload contention, JMH. |
| How test custom extension? | One example. | Edge cases and sequential/parallel equality. | Algebraic laws, split completeness, rejection/finisher, property-generated inputs. |

<a id="operation-selection-guide"></a>

## Operation-selection guide

1. **Need storage/reuse/random access?** Materialize a collection; a Stream is not storage.
2. **Need one result per value?** `map` or a primitive mapping.
3. **Need keep/discard independently?** `filter`.
4. **Need zero/many per value?** `flatMap` for an existing nested source; `mapMulti` for small imperative emission.
5. **Need state across values or controlled concurrency?** built-in/custom `gather`.
6. **Need one final aggregate?** specific terminal (`sum`, `count`, `min`, match/find) or `collect`.
7. **Need mutable grouped/map result?** a built-in collector with explicit duplicate/mutability/order policy.
8. **Need a new source traversal?** custom `Spliterator` + `StreamSupport`.
9. **Need complex control flow, mutation, recovery, or indexes?** prefer a loop.
10. **Need data-local joins/aggregation or asynchronous backpressure?** use the owning database/appropriate async abstraction.

## Classification and behavior tables

### Intermediate versus terminal

| Category | Operations |
|---|---|
| Stateless intermediate | `filter`, mappings, flat maps, `mapMulti`, `peek`, mode/order configuration |
| Stateful intermediate | `distinct`, `sorted`, slicing/prefix operations, many gatherers |
| Short-circuiting intermediate | `limit`, `takeWhile`, short-circuiting custom gatherer |
| Short-circuiting terminal | `findFirst`, `findAny`, three match operations |
| Materializing terminal | `toArray`, `toList`, `collect` |
| Scalar/reduction terminal | `count`, min/max, reduce, primitive numeric operations |
| Side-effect terminal | `forEach`, `forEachOrdered` |

### Null, empty, order, and mutability reminders

| Question | Rule |
|---|---|
| Can a Stream contain null? | Object streams can, but many terminals/collectors cannot represent/accept it. Define policy. |
| Empty `allMatch`/`noneMatch`? | Both true; `anyMatch` false. |
| Empty extrema/find/reduce-without-identity? | Empty optional. |
| Empty sum/count? | Zero. Empty average is optional-empty. |
| `Stream.toList` mutable? | No; encounter-ordered and null-permitting. |
| `Collectors.toList` mutable? | Unspecified; do not rely on it. |
| Unmodifiable collectors accept null? | No. |
| Does `unordered` shuffle? | No; it removes the order constraint. |
| Does parallel preserve order? | Ordered result operations do; `forEach`/`findAny` need not. |
| Must ordinary streams close? | Only when source/resource contract requires it; I/O streams usually do. |

### Source and parallel quick check

| Strong parallel candidate | Weak/unsafe candidate |
|---|---|
| Large arrays/array lists | Iterator/reader/I/O source |
| Expensive independent CPU mapping | Blocking calls without concurrency policy |
| Stateless stages and associative reduction | Shared mutable side effects |
| Unordered result when order irrelevant | Ordered full barriers/prefix operations |
| Accurate balanced spliterator | Unknown/imbalanced/custom incorrect splits |
| Representative benchmark win | Assumption based only on element count |

<a id="api-coverage-matrix"></a>

## API coverage matrix

### `BaseStream<T,S>` — inherited by all stream kinds

| API or use case | Since | Level | Canonical section | Example | Status |
|---|---:|---|---|---|---|
| `iterator()` | 8 | Advanced | [BaseStream controls](#basestream-mode-order-close-and-traversal-controls) | Controlled traversal | Explained + exemplified |
| `spliterator()` | 8 | Advanced | [BaseStream controls](#basestream-mode-order-close-and-traversal-controls) | Source inspection | Explained + exemplified |
| `isParallel()` | 8 | Intermediate | [BaseStream controls](#basestream-mode-order-close-and-traversal-controls) | Mode query | Explained + exemplified |
| `sequential()` | 8 | Intermediate | [BaseStream controls](#basestream-mode-order-close-and-traversal-controls) | Mode switch | Explained + exemplified |
| `parallel()` | 8 | Intermediate | [BaseStream controls](#basestream-mode-order-close-and-traversal-controls) | Mode switch | Explained + exemplified |
| `unordered()` | 8 | Advanced | [BaseStream controls](#basestream-mode-order-close-and-traversal-controls) | Order relaxation | Explained + exemplified |
| `onClose(Runnable)` | 8 | Advanced | [Single use and closing](#single-use-closing-and-unbounded-streams) | Close-handler order | Explained + exemplified |
| `close()` | 8 | Intermediate | [Single use and closing](#single-use-closing-and-unbounded-streams) | Resource stream | Explained + exemplified |

### `Stream<T>`

| API or use case | Since | Level | Canonical section | Example | Status |
|---|---:|---|---|---|---|
| `filter` | 8 | Basic | [Filtering and mapping](#filtering-and-mapping) | Active employees | Explained + exemplified |
| `map` | 8 | Basic | [Filtering and mapping](#filtering-and-mapping) | Name projection | Explained + exemplified |
| `mapToInt`, `mapToLong`, `mapToDouble` | 8 | Average | [Filtering and mapping](#filtering-and-mapping) | Primitive totals | Explained + exemplified |
| `flatMap` | 8 | Average | [Flattening](#flattening-and-zero-or-more-mapping) | Order line items | Explained + exemplified |
| `flatMapToInt/Long/Double` | 8 | Intermediate | [Flattening](#flattening-and-zero-or-more-mapping) | Nested primitive values | Explained + exemplified |
| `mapMulti` | 16 | Intermediate | [Flattening](#flattening-and-zero-or-more-mapping) | Zero-or-many emission | Explained + exemplified |
| `mapMultiToInt/Long/Double` | 16 | Intermediate | [Flattening](#flattening-and-zero-or-more-mapping) | Primitive emission | Explained + exemplified |
| `distinct` | 8 | Basic | [Uniqueness and sorting](#observation-uniqueness-and-sorting) | Stable deduplication | Explained + exemplified |
| `sorted()` and `sorted(Comparator)` | 8 | Basic | [Uniqueness and sorting](#observation-uniqueness-and-sorting) | Stable ranking | Explained + exemplified |
| `peek` | 8 | Intermediate | [Uniqueness and sorting](#observation-uniqueness-and-sorting) | Diagnostic observation | Explained + exemplified |
| `limit`, `skip` | 8 | Basic | [Slicing](#slicing-and-prefix-operations) | Pagination | Explained + exemplified |
| `takeWhile`, `dropWhile` | 9 | Average | [Slicing](#slicing-and-prefix-operations) | Ordered prefix | Explained + exemplified |
| `forEach`, `forEachOrdered` | 8 | Basic | [Traversal](#traversal-and-materialization) | Ordered output | Explained + exemplified |
| `toArray()`, `toArray(generator)` | 8 | Average | [Traversal](#traversal-and-materialization) | Typed array | Explained + exemplified |
| Three `reduce` forms | 8 | Intermediate | [Immutable reduction](#immutable-reduction) | Sum and immutable aggregate | Explained + exemplified |
| Three-argument mutable `collect` | 8 | Intermediate | [Mutable reduction](#mutable-reduction) | Custom container | Explained + exemplified |
| `collect(Collector)` | 8 | Basic | [Mutable reduction](#mutable-reduction) | List/group result | Explained + exemplified |
| `toList()` | 16 | Basic | [Traversal](#traversal-and-materialization) | Unmodifiable snapshot | Explained + exemplified |
| `min`, `max`, `count` | 8 | Basic | [Scalar queries](#scalar-queries-matching-and-finding) | Extremes and count | Explained + exemplified |
| `anyMatch`, `allMatch`, `noneMatch` | 8 | Basic | [Scalar queries](#scalar-queries-matching-and-finding) | Validation | Explained + exemplified |
| `findFirst`, `findAny` | 8 | Basic | [Scalar queries](#scalar-queries-matching-and-finding) | Ordered/parallel lookup | Explained + exemplified |
| `gather` | 24 | Expert | [Gatherer lifecycle](#gatherer-lifecycle-and-laws) | Window/scan pipeline | Explained + exemplified |
| `builder` | 8 | Average | [Collections, arrays, builders](#collections-arrays-and-builders) | Conditional construction | Explained + exemplified |
| `empty`, `of`, `ofNullable` | 8/9 | Basic | [Core factories](#core-object-stream-factories) | Zero/one/many values | Explained + exemplified |
| Both `iterate` forms | 8/9 | Average | [Core factories](#core-object-stream-factories) | Finite and infinite sequence | Explained + exemplified |
| `generate` | 8 | Average | [Core factories](#core-object-stream-factories) | Generated values | Explained + exemplified |
| `concat` | 8 | Average | [Core factories](#core-object-stream-factories) | Ordered concatenation | Explained + exemplified |

### Primitive streams: `IntStream`, `LongStream`, and `DoubleStream`

| API or use case | Since | Level | Canonical section | Example | Status |
|---|---:|---|---|---|---|
| Primitive `filter`, `map`, `flatMap`, `mapMulti` | 8/16 | Average | [Filtering and flattening](#filtering-and-mapping) | Allocation-free numeric pipeline | Explained + exemplified |
| Primitive `IntMapMultiConsumer`, `LongMapMultiConsumer`, `DoubleMapMultiConsumer` `accept` contracts | 16 | Intermediate | [Flattening](#flattening-and-zero-or-more-mapping) | Primitive zero-to-many mapper | Explained + exemplified |
| `mapToObj` and cross-primitive mappings | 8 | Average | [Filtering and mapping](#filtering-and-mapping) | Numeric conversion | Explained + exemplified |
| Primitive `distinct`, `sorted`, `peek` | 8 | Average | [Uniqueness and sorting](#observation-uniqueness-and-sorting) | Numeric normalization | Explained + exemplified |
| Primitive `limit`, `skip`, `takeWhile`, `dropWhile` | 8/9 | Average | [Slicing](#slicing-and-prefix-operations) | Bounded sequence | Explained + exemplified |
| Primitive `forEach`, `forEachOrdered`, `toArray` | 8 | Average | [Traversal](#traversal-and-materialization) | Primitive array | Explained + exemplified |
| Primitive two-form `reduce` | 8 | Intermediate | [Immutable reduction](#immutable-reduction) | Product/maximum | Explained + exemplified |
| Primitive three-argument `collect` | 8 | Intermediate | [Mutable reduction](#mutable-reduction) | Mutable statistics | Explained + exemplified |
| `sum`, `min`, `max`, `count`, `average`, `summaryStatistics` | 8 | Average | [Primitive terminals](#primitive-numeric-terminals) | Numeric summary | Explained + exemplified |
| Primitive match/find families | 8 | Average | [Scalar queries](#scalar-queries-matching-and-finding) | Threshold query | Explained + exemplified |
| `IntStream.asLongStream`, `asDoubleStream` | 8 | Average | [Primitive factories](#primitive-stream-factories) | Widening conversion | Explained + exemplified |
| `LongStream.asDoubleStream` | 8 | Average | [Primitive factories](#primitive-stream-factories) | Widening conversion | Explained + exemplified |
| `boxed` | 8 | Average | [Primitive factories](#primitive-stream-factories) | Object collector bridge | Explained + exemplified |
| Primitive `builder`, `empty`, `of`, `iterate`, `generate`, `concat` | 8/9 | Average | [Primitive factories](#primitive-stream-factories) | Primitive sources | Explained + exemplified |
| `IntStream.range`, `rangeClosed` | 8 | Basic | [Primitive factories](#primitive-stream-factories) | Index/range traversal | Explained + exemplified |
| `LongStream.range`, `rangeClosed` | 8 | Basic | [Primitive factories](#primitive-stream-factories) | Large range | Explained + exemplified |
| Specialized `iterator`, `spliterator`, `sequential`, `parallel` | 8 | Advanced | [BaseStream controls](#basestream-mode-order-close-and-traversal-controls) | Primitive traversal | Explained + exemplified |

### Builders

| API or use case | Since | Level | Canonical section | Example | Status |
|---|---:|---|---|---|---|
| Object/primitive `Builder.accept` | 8 | Average | [Collections, arrays, builders](#collections-arrays-and-builders) | Conditional adds | Explained + exemplified |
| Object/primitive `Builder.add` | 8 | Average | [Collections, arrays, builders](#collections-arrays-and-builders) | Fluent adds | Explained + exemplified |
| Object/primitive `Builder.build` | 8 | Average | [Collections, arrays, builders](#collections-arrays-and-builders) | Build once | Explained + exemplified |

### `Collector`, `Collector.Characteristics`, and `Collectors`

| API or use case | Since | Level | Canonical section | Example | Status |
|---|---:|---|---|---|---|
| `supplier`, `accumulator`, `combiner`, `finisher`, `characteristics` | 8 | Advanced | [Collector lifecycle](#collector-lifecycle-and-laws) | Lifecycle trace | Explained + exemplified |
| Both `Collector.of` forms | 8 | Advanced | [Custom collectors](#custom-collectors) | Immutable/custom result | Explained + exemplified |
| `CONCURRENT`, `UNORDERED`, `IDENTITY_FINISH` | 8 | Advanced | [Collector lifecycle](#collector-lifecycle-and-laws) | Law checks | Explained + exemplified |
| `toCollection` | 8 | Average | [Collection/map collectors](#collection-and-map-collectors) | `TreeSet`/`ArrayDeque` | Explained + exemplified |
| `toList`, `toSet` | 8 | Basic | [Collection/map collectors](#collection-and-map-collectors) | General collection | Explained + exemplified |
| `toUnmodifiableList`, `toUnmodifiableSet` | 10 | Average | [Collection/map collectors](#collection-and-map-collectors) | Immutable result | Explained + exemplified |
| Three `joining` forms | 8 | Basic | [Text/scalar collectors](#text-scalar-numeric-reducing-and-teeing-collectors) | Delimited text | Explained + exemplified |
| `mapping` | 8 | Intermediate | [Downstream adapters](#downstream-adapters) | Names per department | Explained + exemplified |
| `flatMapping` | 9 | Intermediate | [Downstream adapters](#downstream-adapters) | Skills per department | Explained + exemplified |
| `filtering` | 9 | Intermediate | [Downstream adapters](#downstream-adapters) | Preserve empty groups | Explained + exemplified |
| `collectingAndThen` | 8 | Intermediate | [Downstream adapters](#downstream-adapters) | Immutable downstream | Explained + exemplified |
| `counting`, `minBy`, `maxBy` | 8 | Average | [Text/scalar collectors](#text-scalar-numeric-reducing-and-teeing-collectors) | Per-group scalar | Explained + exemplified |
| `summingInt/Long/Double` | 8 | Average | [Text/scalar collectors](#text-scalar-numeric-reducing-and-teeing-collectors) | Per-group totals | Explained + exemplified |
| `averagingInt/Long/Double` | 8 | Average | [Text/scalar collectors](#text-scalar-numeric-reducing-and-teeing-collectors) | Per-group average | Explained + exemplified |
| Three `reducing` forms | 8 | Intermediate | [Text/scalar collectors](#text-scalar-numeric-reducing-and-teeing-collectors) | Downstream reduction | Explained + exemplified |
| Three `groupingBy` forms | 8 | Average | [Grouping](#grouping-and-partitioning) | Nested aggregation | Explained + exemplified |
| Three `groupingByConcurrent` forms | 8 | Advanced | [Grouping](#grouping-and-partitioning) | Concurrent grouping | Explained + exemplified |
| Two `partitioningBy` forms | 8 | Average | [Grouping](#grouping-and-partitioning) | Boolean partition | Explained + exemplified |
| Three `toMap` forms | 8 | Average | [Collection/map collectors](#collection-and-map-collectors) | Duplicate resolution/map supplier | Explained + exemplified |
| Two `toUnmodifiableMap` forms | 10 | Average | [Collection/map collectors](#collection-and-map-collectors) | Immutable map | Explained + exemplified |
| Three `toConcurrentMap` forms | 8 | Advanced | [Collection/map collectors](#collection-and-map-collectors) | Concurrent map | Explained + exemplified |
| `summarizingInt/Long/Double` | 8 | Average | [Text/scalar collectors](#text-scalar-numeric-reducing-and-teeing-collectors) | Summary objects | Explained + exemplified |
| `teeing` | 12 | Advanced | [Text/scalar collectors](#text-scalar-numeric-reducing-and-teeing-collectors) | Two results, one pass | Explained + exemplified |

### `Gatherer`, nested contracts, and `Gatherers`

| API or use case | Since | Level | Canonical section | Example | Status |
|---|---:|---|---|---|---|
| `initializer`, `integrator`, `combiner`, `finisher` | 24 | Expert | [Gatherer lifecycle](#gatherer-lifecycle-and-laws) | Stateful lifecycle | Explained + exemplified |
| `andThen` | 24 | Expert | [Composition](#gatherer-composition-and-selection) | Composed transformation | Explained + exemplified |
| `defaultInitializer`, `defaultCombiner`, `defaultFinisher` | 24 | Expert | [Gatherer lifecycle](#gatherer-lifecycle-and-laws) | Sequential/stateless defaults | Explained + exemplified |
| Four `ofSequential` forms | 24 | Expert | [Custom gatherers](#custom-stateless-and-stateful-gatherers) | Sequential gatherer | Explained + exemplified |
| Three `of` forms | 24 | Expert | [Custom gatherers](#custom-stateless-and-stateful-gatherers) | Parallel-capable gatherer | Explained + exemplified |
| `Downstream.push`, `isRejecting` | 24 | Expert | [Early termination](#early-termination-and-parallel-capable-gatherers) | Rejection-aware emission | Explained + exemplified |
| `Integrator.integrate`, `of`, `ofGreedy` | 24 | Expert | [Gatherer lifecycle](#gatherer-lifecycle-and-laws) | Greedy/non-greedy integrator | Explained + exemplified |
| `Integrator.Greedy` marker | 24 | Expert | [Gatherer lifecycle](#gatherer-lifecycle-and-laws) | Greedy contract | Explained + exemplified |
| `windowFixed` | 24 | Advanced | [Built-ins](#built-in-gatherers) | Fixed batches | Explained + exemplified |
| `windowSliding` | 24 | Advanced | [Built-ins](#built-in-gatherers) | Moving window | Explained + exemplified |
| `fold` | 24 | Advanced | [Built-ins](#built-in-gatherers) | One final aggregate | Explained + exemplified |
| `scan` | 24 | Advanced | [Built-ins](#built-in-gatherers) | Running aggregates | Explained + exemplified |
| `mapConcurrent` | 24 | Expert | [Built-ins](#built-in-gatherers) | Ordered bounded concurrency | Explained + exemplified |

### `StreamSupport`

| API or use case | Since | Level | Canonical section | Example | Status |
|---|---:|---|---|---|---|
| `stream(spliterator, parallel)` | 8 | Advanced | [StreamSupport](#streamsupport) | Custom object source | Explained + exemplified |
| `stream(supplier, characteristics, parallel)` | 8 | Advanced | [StreamSupport](#streamsupport) | Late binding | Explained + exemplified |
| Direct `intStream`, `longStream`, `doubleStream` forms | 8 | Advanced | [StreamSupport](#streamsupport) | Primitive source | Explained + exemplified |
| Supplier `intStream`, `longStream`, `doubleStream` forms | 8 | Advanced | [StreamSupport](#streamsupport) | Late-bound primitive source | Explained + exemplified |

<a id="jdk-stream-source-matrix"></a>

## JDK stream-source matrix

| Source | Stream shape | Finite? | Ordered? | Must close? | Parallel notes | Status |
|---|---|---|---|---|---|---|
| `Collection.stream/parallelStream` | Object | Yes | Source-dependent | No | Usually splittable | Explained + exemplified |
| `Arrays.stream` | Object/int/long/double | Yes | Yes | No | Good splitting | Explained + exemplified |
| `Stream`/primitive factories and builders | Object/primitive | Depends | Usually yes | No | Source-dependent | Explained + exemplified |
| `StreamSupport` + `Spliterator` | Object/primitive | Depends | Characteristics | Source-owned | Implementation-dependent | Explained + exemplified |
| `Files.lines` | Object lines | Yes | Yes | Yes | I/O-bound | Explained + exemplified |
| `BufferedReader.lines` | Object lines | Yes | Yes | Close reader | Poor parallel fit | Explained + exemplified |
| `Files.list`, `walk`, `find` | Paths | Yes | API-dependent | Yes | Close promptly | Explained + exemplified |
| `Pattern.splitAsStream` | Tokens | Yes | Yes | No | Usually sequential | Explained + exemplified |
| `Scanner.tokens`, `findAll` | Tokens/matches | Yes | Yes | Close scanner/source | Poor parallel fit | Explained + exemplified |
| `Matcher.results` | Match results | Yes | Yes | No | Usually sequential | Explained + exemplified |
| `CharSequence.chars/codePoints` | Int code units/points | Yes | Yes | No | Splittable by source | Explained + exemplified |
| `Random`/`RandomGenerator` streams | Primitive | Bounded/unbounded | Encounter sequence | No | Generator-dependent | Explained + exemplified |
| `BitSet.stream` | Set-bit indexes | Yes | Increasing | No | Specialized | Explained + exemplified |
| `JarFile.stream/versionedStream` | JAR entries | Yes | JAR order | Close `JarFile` | I/O-bound | Explained + exemplified |
| `ServiceLoader.stream` | Providers | Yes | Discovery order | No | Side-effectful loading | Explained + exemplified |

<a id="use-case-coverage-matrix"></a>

## Use-case coverage matrix

| API or use case | Since | Level | Canonical section | Example | Status |
|---|---:|---|---|---|---|
| Selection, projection, normalization | 8 | Basic | [Transformation recipes](#transformation-null-and-optional-recipes) | Employees | Explained + exemplified |
| Zero/one/many transformation | 8/9/16/24 | Intermediate | [Transformation recipes](#transformation-null-and-optional-recipes) | Optional/flatMap/mapMulti/gather | Explained + exemplified |
| Flatten nested structures | 8 | Average | [Transformation recipes](#transformation-null-and-optional-recipes) | Orders → items | Explained + exemplified |
| Null and Optional handling | 9 | Average | [Transformation recipes](#transformation-null-and-optional-recipes) | `ofNullable`, `Optional.stream` | Explained + exemplified |
| Deduplication and stable ordering | 8 | Average | [Transformation recipes](#transformation-null-and-optional-recipes) | Stable unique values | Explained + exemplified |
| Grouping, partitioning, nested aggregation | 8 | Average | [Aggregation recipes](#aggregation-and-map-recipes) | Department metrics | Explained + exemplified |
| Map construction, inversion, duplicate resolution | 8/10 | Intermediate | [Aggregation recipes](#aggregation-and-map-recipes) | IDs and aliases | Explained + exemplified |
| Frequency maps and histograms | 8 | Average | [Aggregation recipes](#aggregation-and-map-recipes) | Word counts | Explained + exemplified |
| Inner/left/full lookup joins | 8 | Intermediate | [Relational recipes](#relational-and-positional-recipes) | Orders/customers | Explained + exemplified |
| Cartesian product | 8 | Intermediate | [Relational recipes](#relational-and-positional-recipes) | Pair generation | Explained + exemplified |
| Zip, index, adjacent pairs | 8/24 | Advanced | [Relational recipes](#relational-and-positional-recipes) | Positions and deltas | Explained + exemplified |
| Pagination, ranking, top-N | 8 | Intermediate | [Relational recipes](#relational-and-positional-recipes) | Ranked employees | Explained + exemplified |
| Chunking and fixed/sliding windows | 24 | Advanced | [Temporal recipes](#temporal-and-stateful-recipes) | Event windows | Explained + exemplified |
| Fold, scan, running totals | 24 | Advanced | [Temporal recipes](#temporal-and-stateful-recipes) | Balance history | Explained + exemplified |
| Session segmentation/consecutive dedupe | 24/custom | Expert | [Temporal recipes](#temporal-and-stateful-recipes) | Event sessions | Explained + exemplified |
| Recursive tree traversal and cycles | 8/custom | Advanced | [Traversal recipes](#traversal-text-and-io-recipes) | Tree paths | Explained + exemplified |
| Files, directories, archives, regex, Unicode | JDK-specific | Intermediate | [Traversal recipes](#traversal-text-and-io-recipes) | Text/JAR processing | Explained + exemplified |
| Validation and error accumulation | 8 | Intermediate | [Validation recipes](#validation-errors-statistics-and-reconciliation) | Domain validation | Explained + exemplified |
| Checked-exception boundaries | 8 | Advanced | [Exception handling](#exception-handling) | I/O mapping | Explained + exemplified |
| Exact totals and descriptive statistics | 8 | Intermediate | [Validation recipes](#validation-errors-statistics-and-reconciliation) | Money/statistics | Explained + exemplified |
| Diff, set operations, reconciliation | 8 | Intermediate | [Validation recipes](#validation-errors-statistics-and-reconciliation) | Transactions | Explained + exemplified |
| Infinite streams and safe termination | 8/9 | Intermediate | [Single use](#single-use-closing-and-unbounded-streams) | Generated sequence | Explained + exemplified |
| Custom collector | 8 | Advanced | [Custom collectors](#custom-collectors) | Top-N/aggregate | Explained + exemplified |
| Custom gatherer | 24 | Expert | [Custom gatherers](#custom-stateless-and-stateful-gatherers) | Index/batch/dedupe | Explained + exemplified |
| Custom spliterator/source | 8 | Expert | [Custom sources](#custom-source-examples) | Range/tree/batches | Explained + exemplified |
| Sequential/parallel equivalence | 8 | Advanced | [Correctness laws](#correctness-laws-and-shared-state) | Law checks | Explained + exemplified |
| Performance selection and benchmarking | 8 | Advanced | [Performance](#performance-decision-framework) | Cost model | Explained + exemplified |
| Testing and debugging | 8 | Intermediate | [Testing](#testing-streams-collectors-gatherers-and-spliterators) | Invariants and traces | Explained + exemplified |

<a id="contract-coverage-matrix"></a>

## Cross-cutting contract matrix

| Contract | Canonical section | Status |
|---|---|---|
| Laziness and operation elision | [Pipeline anatomy](#pipeline-anatomy-and-laziness) | Cross-cutting contract |
| Stateless/stateful operations | [Pipeline anatomy](#pipeline-anatomy-and-laziness) | Cross-cutting contract |
| Short-circuiting | [Pipeline anatomy](#pipeline-anatomy-and-laziness) | Cross-cutting contract |
| Encounter order and determinism | [Encounter order](#encounter-order-and-characteristics) | Cross-cutting contract |
| Non-interference and side effects | [Behavioral contracts](#behavioral-contracts) | Cross-cutting contract |
| Null behavior | [Transformation recipes](#transformation-null-and-optional-recipes) | Cross-cutting contract |
| Empty input | [Terminal decision table](#terminal-operation-decision-table) | Cross-cutting contract |
| Result mutability | [Collection/map collectors](#collection-and-map-collectors) | Cross-cutting contract |
| Resource ownership and closing | [Single use](#single-use-closing-and-unbounded-streams) | Cross-cutting contract |
| Thread safety and shared state | [Correctness laws](#correctness-laws-and-shared-state) | Cross-cutting contract |
| Identity, associativity, and combiner laws | [Immutable reduction](#immutable-reduction) | Cross-cutting contract |
| Overflow and numerical accuracy | [Primitive terminals](#primitive-numeric-terminals) | Cross-cutting contract |
| Parallel equivalence | [Correctness laws](#correctness-laws-and-shared-state) | Cross-cutting contract |
| Readability and alternative abstractions | [Readability](#readability-and-maintainability) | Cross-cutting contract |

---

## Official references

- [Java SE 26 `java.util.stream` package](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/package-summary.html)
- [`BaseStream`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/BaseStream.html)
- [`Stream`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/Stream.html)
- [`IntStream`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/IntStream.html), [`LongStream`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/LongStream.html), and [`DoubleStream`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/DoubleStream.html)
- [`Collector`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/Collector.html) and [`Collectors`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/Collectors.html)
- [`Gatherer`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/Gatherer.html) and [`Gatherers`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/Gatherers.html)
- [`StreamSupport`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/StreamSupport.html)
- [OpenJDK JEP 485: Stream Gatherers](https://openjdk.org/jeps/485)

## Verification record

Verified on 2026-08-26:

- Normative API target: Java SE 26; 20 official top-level/nested API pages were reconciled, with zero missing declared method names.
- Local execution runtime/compiler: OpenJDK 25.0.2. Java 26 contracts/signatures were checked against the official Java SE 26 Javadocs because a JDK 26 compiler was not installed locally.
- Coverage inventory: 95 grouped API rows, 15 JDK source rows, 28 use-case rows, and 14 cross-cutting contract rows; zero pending or blank statuses.
- Structure: 223 resolvable anchors, 151 internal links, zero missing targets, zero duplicate explicit anchors, and 344 balanced code fences.
- Examples: 168 Java code blocks, including explanatory fragments and intentional failures. Representative executable examples were consolidated into four JDK smoke suites containing 43 explicit checks; all compiled and passed, including collectors, Gatherers, custom spliterators, parallel equivalence, cookbook transformations, exception translation, and resource operations.
- Sources: all 12 official Oracle/OpenJDK links returned successful responses during verification.
- Safety audit: all code blocks using close-sensitive `Files`, `BufferedReader`, or `JarFile` streams keep traversal inside try-with-resources; every intentionally incorrect example has an adjacent correction or corrected pattern.
