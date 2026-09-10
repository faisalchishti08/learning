# Java Senior Technical Lead — Complete Mastery Roadmap (10 YOE)

> A single source of truth for everything a senior Java technical lead is expected to know.
> Organized as **Parts → Sections → Topics → Micro-topics**, every leaf is a checkbox so progress is measurable.

---

## 0. How To Use This File

### 0.1 Legend

| Marker | Meaning |
|---|---|
| `- [ ]` | Not started |
| `- [~]` | In progress (edit the `x` manually to `~`) |
| `- [x]` | Done — can explain it on a whiteboard *and* code it |
| 🔴 | **Must-know.** Interview blocker / daily job requirement |
| 🟡 | **Should-know.** Comes up regularly, differentiates senior from mid |
| 🟢 | **Good-to-know.** Depth/breadth signal, situational |

### 0.2 Depth Levels — grade yourself per topic

| Level | Name | Test |
|---|---|---|
| L1 | Aware | Can define it, know when it applies |
| L2 | Working | Can use it correctly with docs open |
| L3 | Fluent | Can use it from memory, know the pitfalls |
| L4 | Deep | Know the internals / implementation / failure modes |
| L5 | Authoritative | Can teach it, make architectural trade-off calls, debug it in prod |

**Target for a Senior Tech Lead:** L4–L5 on 🔴, L3–L4 on 🟡, L2–L3 on 🟢.

### 0.3 Suggested Study Loop (per topic)

1. **Read** the canonical source (JLS/JEP/spec/official docs — not blog posts first).
2. **Code** a minimal reproduction or demo.
3. **Break it** — force the failure mode deliberately.
4. **Explain it** out loud in 3 minutes without notes.
5. **Write** 5 flashcard Q&As + 1 "when would I *not* use this".
6. Mark the checkbox and record the date + depth level.

### 0.4 Progress Dashboard

| Part | Area | Priority Weight | Status | Depth | Date Completed |
|---|---|---|---|---|---|
| 1 | Core Java Language | 🔴 Critical | ☐ | | |
| 2 | JVM Internals, Memory & GC | 🔴 Critical | ☐ | | |
| 3 | Concurrency & Parallelism | 🔴 Critical | ☐ | | |
| 4 | Software Design & Patterns | 🔴 Critical | ☐ | | |
| 5 | Architecture & Distributed Systems | 🔴 Critical | ☐ | | |
| 6 | Spring Ecosystem | 🔴 Critical | ☐ | | |
| 7 | Persistence, JPA & Databases | 🔴 Critical | ☐ | | |
| 8 | Messaging & Event Streaming | 🟡 High | ☐ | | |
| 9 | APIs & Integration | 🔴 Critical | ☐ | | |
| 10 | Testing & Quality Engineering | 🔴 Critical | ☐ | | |
| 11 | Build, Dependency & Release | 🟡 High | ☐ | | |
| 12 | Cloud, Containers & Platform | 🟡 High | ☐ | | |
| 13 | Observability & Production Ops | 🔴 Critical | ☐ | | |
| 14 | Security & Compliance | 🔴 Critical | ☐ | | |
| 15 | Performance Engineering | 🟡 High | ☐ | | |
| 16 | Engineering Practices & Craft | 🟡 High | ☐ | | |
| 17 | Data, Analytics & AI Adjacency | 🟢 Medium | ☐ | | |
| 18 | Alternative JVM Stacks & Languages | 🟢 Medium | ☐ | | |
| 19 | Technical Leadership | 🔴 Critical | ☐ | | |
| 20 | Interview Preparation Playbook | 🔴 Critical | ☐ | | |

---
---

# PART 1 — CORE JAVA LANGUAGE

## 1.1 Language Fundamentals & Type System

### 1.1.1 Primitives, Wrappers, Literals 🔴
- [ ] All 8 primitive types: exact bit widths, ranges, default values
- [ ] `char` is unsigned 16-bit; UTF-16 code unit vs code point
- [ ] Integer overflow/underflow semantics; `Math.addExact` / `Math.toIntExact`
- [ ] `Math.floorDiv` / `Math.floorMod` vs `/` and `%` for negatives
- [ ] Floating point: IEEE 754, `float` vs `double` precision, `0.1 + 0.2` problem
- [ ] `NaN` semantics: `NaN != NaN`, `Double.compare` vs `==`, `Double.NaN` in collections
- [ ] `-0.0` vs `0.0`; `Double.equals` vs `==` divergence
- [ ] `strictfp` (and why it became default in Java 17)
- [ ] `BigDecimal`: scale, precision, `MathContext`, `RoundingMode`, why `new BigDecimal(0.1)` is wrong
- [ ] `BigDecimal.equals` vs `compareTo` (scale sensitivity)
- [ ] `BigInteger` arithmetic, `modPow`, use in crypto
- [ ] Autoboxing/unboxing rules, boxing in hot loops (perf cost)
- [ ] Integer cache (-128..127), `==` on boxed Integers, `-XX:AutoBoxCacheMax`
- [ ] `NullPointerException` on unboxing a null wrapper (ternary operator trap)
- [ ] Literal forms: binary `0b`, octal, hex, underscores in literals, `L`/`f`/`d` suffixes
- [ ] Numeric promotion and widening/narrowing conversion rules
- [ ] Casting rules, lossy conversions, `(byte)(int)` truncation

### 1.1.2 Operators & Expressions 🔴
- [ ] Operator precedence & associativity table
- [ ] Short-circuit `&&`/`||` vs non-short-circuit `&`/`|`
- [ ] Bitwise ops, `>>` vs `>>>` (arithmetic vs logical shift), shift-distance masking
- [ ] Ternary operator type-inference and autoboxing pitfalls
- [ ] Compound assignment implicit cast (`byte b; b += 1;` compiles, `b = b + 1` doesn't)
- [ ] Evaluation order guarantees (left-to-right), sequence points
- [ ] `instanceof` and pattern-matching `instanceof`
- [ ] String concatenation compilation: `StringConcatFactory` / `invokedynamic` (Java 9+)

### 1.1.3 Control Flow 🔴
- [ ] `if`/`else`, `while`, `do-while`, classic `for`, enhanced `for`
- [ ] Labeled `break` / `continue`
- [ ] Classic `switch` statement: fallthrough, allowed types, `default`
- [ ] `switch` expressions (Java 14+): arrow form, `yield`, exhaustiveness
- [ ] Pattern matching for `switch` (Java 21): type patterns, guards (`when`), `null` case
- [ ] Record patterns & nested deconstruction (Java 21)
- [ ] Exhaustiveness checking with sealed hierarchies
- [ ] Unnamed patterns and variables `_` (Java 22+)
- [ ] `var` (local variable type inference): rules, limits, readability guidelines

### 1.1.4 Classes, Objects, Members 🔴
- [ ] Class vs instance members, static initialization order
- [ ] Instance initializer blocks vs constructors vs field initializers — exact order
- [ ] Constructor chaining: `this(...)`, `super(...)`, implicit no-arg super call
- [ ] Constructors calling overridable methods (the initialization-order bug)
- [ ] `final` on fields/params/locals/methods/classes; `final` and safe publication
- [ ] `static` nested class vs inner class (implicit outer reference & memory leaks)
- [ ] Local classes, anonymous classes, effectively-final capture
- [ ] Access modifiers: `public`/`protected`/package-private/`private` — exact visibility matrix
- [ ] Varargs: array under the hood, heap pollution, `@SafeVarargs`, ambiguity in overloads
- [ ] Method overloading resolution: phases (no boxing → boxing → varargs), most-specific rule
- [ ] Method overriding: covariant returns, exception narrowing, access widening
- [ ] Method hiding (static) vs overriding (instance)
- [ ] `this` escaping during construction
- [ ] Initialization-on-demand holder idiom

### 1.1.5 `Object` Contract 🔴
- [ ] `equals` contract: reflexive, symmetric, transitive, consistent, null-false
- [ ] `hashCode` contract & consequences of violating it in `HashMap`/`HashSet`
- [ ] `equals`/`hashCode` with inheritance — the symmetry problem, `getClass()` vs `instanceof`
- [ ] `Objects.equals`, `Objects.hash`, `Objects.requireNonNull`, `Objects.hashCode`
- [ ] `toString` conventions, `@Override` discipline
- [ ] `clone()` and `Cloneable` — why it's broken; shallow vs deep copy; copy constructors/factories
- [ ] `finalize()` deprecation & removal; `Cleaner` API; `AutoCloseable` instead
- [ ] `getClass()`, identity hash code, `System.identityHashCode`
- [ ] `Comparable` vs `Comparator`, consistency-with-equals, `compare` contract
- [ ] `Comparator` combinators: `comparing`, `thenComparing`, `reversed`, `nullsFirst`/`nullsLast`
- [ ] Integer-overflow bug in naive `compare` implementations

### 1.1.6 Interfaces & Abstraction 🔴
- [ ] Interface evolution: default methods, static methods, private methods (Java 9)
- [ ] Diamond problem resolution rules; `Interface.super.method()`
- [ ] Class-wins rule, most-specific-interface rule
- [ ] Marker interfaces vs annotations
- [ ] Functional interfaces, `@FunctionalInterface`, SAM conversion
- [ ] Abstract class vs interface — decision criteria
- [ ] Sealed types (`sealed`, `non-sealed`, `permits`) — Java 17
- [ ] Sealed + records + pattern matching = algebraic data types in Java

### 1.1.7 Enums 🟡
- [ ] Enum as singleton, serialization guarantees
- [ ] Constant-specific method bodies (per-constant class bodies)
- [ ] Enums implementing interfaces; strategy-via-enum
- [ ] `EnumMap` / `EnumSet` internals (bit vector / array-backed) and performance
- [ ] `values()` defensive copying cost; caching pattern
- [ ] `valueOf` and `IllegalArgumentException`; safe lookup maps
- [ ] `ordinal()` fragility; never persist `ordinal()`
- [ ] Enums in `switch` and exhaustiveness

### 1.1.8 Records 🔴
- [ ] Canonical, compact, and custom constructors
- [ ] Auto-generated `equals`/`hashCode`/`toString`/accessors
- [ ] Validation & normalization in compact constructor
- [ ] Immutability caveat: mutable components need defensive copies
- [ ] Records + serialization semantics
- [ ] Local records; records as DTOs / value objects / multi-return
- [ ] Record patterns, nested deconstruction
- [ ] Restrictions: no extends, implicitly final, no instance fields

### 1.1.9 Annotations 🟡
- [ ] Built-in: `@Override`, `@Deprecated(forRemoval, since)`, `@SuppressWarnings`, `@FunctionalInterface`, `@SafeVarargs`
- [ ] Meta-annotations: `@Retention`, `@Target`, `@Inherited`, `@Documented`, `@Repeatable`
- [ ] Retention policies SOURCE/CLASS/RUNTIME and their tooling implications
- [ ] Type annotations (JSR 308) and pluggable type checkers
- [ ] Writing custom annotations
- [ ] Annotation processing (JSR 269): `AbstractProcessor`, rounds, generating sources
- [ ] Real processors: Lombok (how it hacks the AST), MapStruct, Immutables, Dagger
- [ ] `javax.annotation.processing` vs runtime reflection trade-offs

### 1.1.10 Generics 🔴
- [ ] Type erasure — what's kept, what's lost, bridge methods
- [ ] Bounded type parameters `<T extends Comparable<? super T>>`
- [ ] Wildcards: `? extends` (producer), `? super` (consumer), PECS
- [ ] Unbounded wildcard `<?>` vs raw type vs `<Object>`
- [ ] Generic methods & explicit type witnesses `Collections.<String>emptyList()`
- [ ] Recursive generic bound (`<T extends Enum<T>>`, self-referential builders)
- [ ] Heap pollution, unchecked warnings, `@SuppressWarnings("unchecked")` discipline
- [ ] Why you can't create `new T[]`; array covariance vs generic invariance
- [ ] `ArrayStoreException` and why arrays are broken
- [ ] Reifiable vs non-reifiable types
- [ ] Type tokens: `Class<T>`, super type tokens (`TypeReference`, Guava `TypeToken`)
- [ ] Generic type inference: target typing, diamond `<>`, `var` interaction
- [ ] Intersection types `<T extends A & B>`
- [ ] Generics in interop with reflection: `ParameterizedType`, `getGenericSuperclass`
- [ ] Common compile errors and how to read them

### 1.1.11 Strings & Text 🔴
- [ ] String immutability & its consequences (thread safety, caching, security)
- [ ] String pool, `intern()`, `-XX:StringTableSize`, compile-time constant folding
- [ ] Compact Strings (JEP 254) — LATIN1 vs UTF16 byte arrays
- [ ] `String` vs `StringBuilder` vs `StringBuffer`; when concatenation in a loop matters
- [ ] `substring()` memory behavior pre/post Java 7u6
- [ ] `equals` vs `==` vs `equalsIgnoreCase` vs `contentEquals`
- [ ] `hashCode` caching and the zero-hash edge case
- [ ] `split()` semantics: regex, trailing empties, limit parameter
- [ ] `String.format`, `Formatter`, `MessageFormat`, `formatted()`
- [ ] Text blocks (Java 15): incidental whitespace, escapes `\` and `\s`
- [ ] `String` templates status/history (preview, withdrawn) 🟢
- [ ] `Charset`, encode/decode, `StandardCharsets`, default charset (UTF-8 by default in Java 18+)
- [ ] Unicode: code points, surrogate pairs, grapheme clusters, normalization (NFC/NFD)
- [ ] `String.chars()` vs `codePoints()`
- [ ] Locale-sensitive operations: `toUpperCase(Locale)`, the Turkish-I bug
- [ ] `Collator` for locale-correct sorting
- [ ] `StringJoiner`, `String.join`, `Collectors.joining`
- [ ] `strip()` vs `trim()`, `isBlank`, `lines()`, `repeat()`, `indent()`

### 1.1.12 Regular Expressions 🟡
- [ ] `Pattern` / `Matcher` API; compile-once-reuse
- [ ] Greedy vs reluctant vs possessive quantifiers
- [ ] Capturing vs non-capturing groups, named groups
- [ ] Backreferences, lookahead/lookbehind
- [ ] Flags: CASE_INSENSITIVE, MULTILINE, DOTALL, UNICODE_CASE, COMMENTS
- [ ] Catastrophic backtracking / ReDoS — recognizing and preventing 🔴
- [ ] `matches` vs `find` vs `lookingAt`
- [ ] `Matcher.replaceAll` with function (Java 9+), `Matcher.results()`
- [ ] `Pattern.splitAsStream`, `Pattern.quote`

### 1.1.13 Arrays 🟡
- [ ] Multidimensional (jagged) arrays, memory layout
- [ ] `Arrays` utility: `sort`, `parallelSort`, `binarySearch`, `fill`, `copyOf`, `copyOfRange`
- [ ] `Arrays.asList` — fixed-size view gotcha; `List.of` vs `Arrays.asList` on nulls
- [ ] `Arrays.equals` vs `deepEquals`, `hashCode` vs `deepHashCode`
- [ ] `System.arraycopy` and intrinsics
- [ ] `Arrays.mismatch`, `compare` (Java 9+)
- [ ] Dual-pivot quicksort for primitives, TimSort for objects; `IllegalArgumentException: Comparison method violates its general contract!`
- [ ] Array covariance danger

## 1.2 Exceptions & Error Handling

### 1.2.1 Exception Model 🔴
- [ ] `Throwable` hierarchy: `Error` / `Exception` / `RuntimeException`
- [ ] Checked vs unchecked — design guidance and the modern debate
- [ ] `try`/`catch`/`finally` semantics; `finally` overriding return values
- [ ] try-with-resources: `AutoCloseable`, resource close order, effectively-final resources (Java 9)
- [ ] Suppressed exceptions (`getSuppressed`, `addSuppressed`)
- [ ] Multi-catch `catch (A | B e)` and its effectively-final type
- [ ] Precise rethrow (Java 7)
- [ ] Exception chaining / `initCause` / cause-preserving wrapping
- [ ] Stack trace capture cost; `fillInStackTrace` override for control-flow exceptions
- [ ] Stackless exceptions, `writableStackTrace` constructor
- [ ] Helpful NullPointerException messages (JEP 358) 🟡
- [ ] `StackOverflowError`, `OutOfMemoryError` variants (heap, metaspace, GC overhead, direct buffer, thread)
- [ ] `Thread.UncaughtExceptionHandler`, default handler
- [ ] Exceptions across thread boundaries (`ExecutionException`, `CompletionException`)

### 1.2.2 Error-Handling Design 🔴
- [ ] Fail-fast vs fail-safe
- [ ] Exception translation at layer boundaries
- [ ] Domain exceptions vs technical exceptions
- [ ] Error codes, problem details (RFC 7807/9457) for APIs
- [ ] Result/Either types vs exceptions; when to use `Optional`
- [ ] Anti-patterns: swallowing, `catch (Exception e) { log; }`, exceptions for control flow, logging *and* rethrowing
- [ ] Retryable vs non-retryable classification
- [ ] Global exception handling (`@ControllerAdvice`, servlet error pages)
- [ ] Idempotency and partial failure cleanup

### 1.2.3 `Optional` 🔴
- [ ] Intent: return type, not field/parameter
- [ ] `map`, `flatMap`, `filter`, `or`, `ifPresentOrElse`, `stream`
- [ ] `orElse` vs `orElseGet` (eager vs lazy evaluation cost)
- [ ] `orElseThrow`, `get()` deprecation-in-spirit
- [ ] `Optional` and serialization / JPA fields / Jackson
- [ ] `OptionalInt`/`OptionalLong`/`OptionalDouble`
- [ ] Anti-patterns: `Optional.isPresent() + get()`, `Optional<Collection>`, nested `Optional`

## 1.3 Collections Framework 🔴

### 1.3.1 Interfaces & Hierarchy
- [ ] `Iterable` → `Collection` → `List`/`Set`/`Queue`/`Deque`
- [ ] `Map` (not a `Collection`), `SortedMap`, `NavigableMap`
- [ ] `SequencedCollection` / `SequencedSet` / `SequencedMap` (Java 21): `getFirst`, `reversed()`
- [ ] `Iterator`, `ListIterator`, `Spliterator` (characteristics, `trySplit`, `estimateSize`)
- [ ] Fail-fast iterators & `modCount`; `ConcurrentModificationException`
- [ ] Fail-safe (weakly consistent) iterators in concurrent collections

### 1.3.2 List Implementations
- [ ] `ArrayList`: growth factor, `ensureCapacity`, `trimToSize`, `System.arraycopy` cost
- [ ] `LinkedList`: node overhead, when it's actually never the right choice
- [ ] `CopyOnWriteArrayList`: use cases, write cost, snapshot iterator
- [ ] `Vector`/`Stack` legacy and why to avoid
- [ ] `List.of` immutable lists; null-hostility; `Collections.unmodifiableList` view vs copy
- [ ] `subList` view semantics & `ConcurrentModificationException` traps
- [ ] `removeIf`, `replaceAll`, `sort` default methods

### 1.3.3 Map Implementations 🔴
- [ ] `HashMap` internals: buckets, hash spreading, load factor, resize/rehash, treeification (≥8 nodes, ≥64 buckets)
- [ ] `HashMap` in multithreaded use — infinite loop (Java 7) / lost updates
- [ ] `LinkedHashMap`: insertion vs access order, `removeEldestEntry` → LRU cache
- [ ] `TreeMap`: red-black tree, `NavigableMap` ops (`floorKey`, `ceilingKey`, `headMap`, `subMap`)
- [ ] `Hashtable` legacy
- [ ] `IdentityHashMap`, `WeakHashMap` (and its leak pitfalls), `EnumMap`
- [ ] `ConcurrentHashMap`: CAS + synchronized bins, `computeIfAbsent` atomicity & deadlock risk, `forEach`/`reduce`/`search`, `mappingCount`
- [ ] `ConcurrentSkipListMap` for sorted concurrent access
- [ ] `Map.of` / `Map.ofEntries` / `Map.entry`
- [ ] Default methods: `getOrDefault`, `putIfAbsent`, `compute`, `computeIfAbsent`, `computeIfPresent`, `merge`
- [ ] Null key/value support matrix across implementations
- [ ] Mutable keys → lost entries

### 1.3.4 Set Implementations
- [ ] `HashSet` (HashMap-backed), `LinkedHashSet`, `TreeSet`, `EnumSet`
- [ ] `CopyOnWriteArraySet`, `ConcurrentSkipListSet`, `Collections.newSetFromMap`
- [ ] Set algebra: `retainAll`, `removeAll`, `addAll` performance characteristics

### 1.3.5 Queues & Deques
- [ ] `ArrayDeque` (preferred stack & queue), `PriorityQueue` (binary heap, not sorted iteration)
- [ ] `BlockingQueue` family: `ArrayBlockingQueue`, `LinkedBlockingQueue`, `SynchronousQueue`, `PriorityBlockingQueue`, `DelayQueue`, `LinkedTransferQueue`
- [ ] `BlockingDeque`, work-stealing deques
- [ ] `offer`/`poll`/`peek` vs `add`/`remove`/`element` (exception vs special value vs blocking vs timeout matrix)

### 1.3.6 Utilities & Practices
- [ ] `Collections`: `unmodifiable*`, `synchronized*`, `singleton*`, `empty*`, `nCopies`, `shuffle`, `rotate`, `frequency`, `disjoint`
- [ ] Immutable vs unmodifiable vs defensive copy
- [ ] Choosing a collection: decision matrix by access pattern (Big-O table memorized) 🔴
- [ ] Memory footprint of collections (object headers, boxing, entry overhead)
- [ ] Primitive collections: Eclipse Collections, fastutil, HPPC, Agrona, Trove 🟢
- [ ] Guava collections: `Multimap`, `Multiset`, `BiMap`, `Table`, `RangeMap`, `ImmutableX` 🟡
- [ ] Apache Commons Collections 🟢
- [ ] Initial capacity sizing to avoid rehash

## 1.4 Streams & Functional Java 🔴

### 1.4.1 Lambdas & Method References
- [ ] Lambda syntax, target typing, effectively-final capture
- [ ] `this` semantics in lambda vs anonymous class
- [ ] Compilation: `invokedynamic` + `LambdaMetafactory` (not anonymous classes)
- [ ] Capturing vs non-capturing lambdas & instance caching
- [ ] Method references: static, instance-bound, instance-unbound, constructor, array constructor
- [ ] Lambda serialization 🟢
- [ ] Lambda performance & warmup cost 🟢

### 1.4.2 Functional Interfaces
- [ ] `Function`, `BiFunction`, `UnaryOperator`, `BinaryOperator`
- [ ] `Predicate`, `BiPredicate`, `Supplier`, `Consumer`, `BiConsumer`
- [ ] Primitive specializations (`IntFunction`, `ToIntFunction`, `IntPredicate`, …) — why they exist
- [ ] Composition: `andThen`, `compose`, `negate`, `and`, `or`, `identity`
- [ ] Checked exceptions in lambdas — wrapper patterns, `@SneakyThrows`, `Try` types
- [ ] Writing your own functional interfaces

### 1.4.3 Stream API
- [ ] Stream sources: collections, `Stream.of`, `iterate`, `generate`, `Arrays.stream`, `Files.lines`, `Random.ints`
- [ ] Lazy evaluation & the terminal-operation trigger
- [ ] Intermediate ops: `filter`, `map`, `flatMap`, `mapMulti` (Java 16), `distinct`, `sorted`, `peek`, `limit`, `skip`, `takeWhile`, `dropWhile`
- [ ] Terminal ops: `forEach`, `forEachOrdered`, `collect`, `reduce`, `count`, `min`/`max`, `anyMatch`/`allMatch`/`noneMatch`, `findFirst`/`findAny`, `toArray`, `toList` (Java 16)
- [ ] Short-circuiting & infinite streams
- [ ] Stateful vs stateless operations and their cost
- [ ] Ordering & encounter order; when `unordered()` helps
- [ ] Primitive streams: `IntStream`/`LongStream`/`DoubleStream`, `boxed`, `asLongStream`, `summaryStatistics`
- [ ] `Collectors`: `toList`, `toSet`, `toMap` (+ merge fn + map supplier), `toUnmodifiableX`
- [ ] `groupingBy`, `partitioningBy`, downstream collectors, `counting`, `mapping`, `flatMapping`, `filtering`, `reducing`, `collectingAndThen`, `teeing` (Java 12)
- [ ] `joining`, `averagingX`, `summingX`, `summarizingX`, `minBy`/`maxBy`
- [ ] Custom `Collector`: supplier/accumulator/combiner/finisher/characteristics
- [ ] `reduce` — identity, associativity, and the 3-arg form's combiner
- [ ] `Stream.gatherers` / `Gatherer` API (Java 24 stream gatherers) 🟢
- [ ] Streams and checked exceptions
- [ ] Streams vs loops: readability & performance realities
- [ ] Debugging streams; why `peek` is not a debugger
- [ ] Reusing a stream → `IllegalStateException`
- [ ] Closing streams from I/O sources

### 1.4.4 Parallel Streams 🟡
- [ ] Common `ForkJoinPool` and why it's shared (and dangerous)
- [ ] Running a parallel stream in a custom pool
- [ ] Splitting quality by source (ArrayList good, LinkedList bad, `Files.lines` bad)
- [ ] NQ model: when parallelism pays off
- [ ] Side effects & non-thread-safe accumulators
- [ ] `Collectors.toConcurrentMap`, `groupingByConcurrent`, CONCURRENT/UNORDERED characteristics
- [ ] Blocking work inside parallel streams — pool starvation
- [ ] Measuring rather than guessing (JMH)

## 1.5 Date, Time & Internationalization 🟡
- [ ] Legacy: `Date`, `Calendar`, `SimpleDateFormat` (not thread-safe), `TimeZone`
- [ ] `java.time` core: `Instant`, `LocalDate`, `LocalTime`, `LocalDateTime`, `ZonedDateTime`, `OffsetDateTime`
- [ ] `Duration` vs `Period`; `ChronoUnit`, `TemporalAdjusters`
- [ ] `ZoneId`, `ZoneOffset`, tzdata updates, DST gaps & overlaps
- [ ] `Clock` abstraction for testability (`Clock.fixed`, `Clock.offset`)
- [ ] `DateTimeFormatter`: predefined, pattern, localized, strict/lenient `ResolverStyle`
- [ ] ISO-8601, RFC 3339, epoch millis/seconds/nanos
- [ ] Storing time in DBs: `TIMESTAMP WITH TIME ZONE` vs UTC epoch; JDBC/JPA mapping
- [ ] Leap seconds, leap years, `Year.isLeap`
- [ ] Monotonic time: `System.nanoTime` vs `currentTimeMillis` (never subtract wall clocks)
- [ ] i18n: `Locale`, `ResourceBundle`, `NumberFormat`, `CurrencyUnit`, ICU4J 🟢
- [ ] Currency & money: never `double`; `BigDecimal` or JSR-354 (Moneta)

## 1.6 I/O, NIO & Files 🟡
- [ ] Byte streams vs character streams; decorator pattern in `java.io`
- [ ] Buffering and why unbuffered I/O kills throughput
- [ ] `Reader`/`Writer` and charset handling
- [ ] `java.nio.file`: `Path`, `Paths`, `Files`, `FileSystem`, `WatchService`
- [ ] `Files.walk`/`walkFileTree`/`find`/`lines`/`readString`/`writeString`/`mismatch`
- [ ] Atomic file operations: `ATOMIC_MOVE`, temp-file-then-rename, `fsync`
- [ ] `ByteBuffer`: heap vs direct, position/limit/capacity/mark, `flip`/`clear`/`compact`, endianness
- [ ] Memory-mapped files `MappedByteBuffer`, unmapping problem
- [ ] `FileChannel`, `transferTo`/`transferFrom` (zero-copy), `FileLock`
- [ ] Scatter/gather I/O
- [ ] NIO selectors, `SelectableChannel`, non-blocking sockets, reactor pattern
- [ ] `AsynchronousFileChannel` / `AsynchronousSocketChannel` (NIO.2)
- [ ] Resource leaks: always close; `try-with-resources`; leak detection
- [ ] Temp files, `deleteOnExit` leak, `Files.createTempFile` security
- [ ] File permissions/POSIX attributes, symbolic links
- [ ] Foreign Memory API replacing `sun.misc.Unsafe` for off-heap 🟢

## 1.7 Reflection, Bytecode & Metaprogramming 🟡
- [ ] `Class` object, `getDeclaredX` vs `getX`, `setAccessible` and JPMS strong encapsulation
- [ ] Reflection performance cost & caching `Method`/`Field` handles
- [ ] `MethodHandles`, `MethodType`, `Lookup`, `VarHandle` (fences, atomic access modes)
- [ ] `invokedynamic` and call-site linkage
- [ ] Dynamic proxies: `java.lang.reflect.Proxy`, `InvocationHandler`
- [ ] Bytecode manipulation: ASM, ByteBuddy, Javassist, CGLIB
- [ ] Class Files API (JEP 484) 🟢
- [ ] Java agents: `premain`, `agentmain`, `Instrumentation`, retransformation
- [ ] Classloaders: delegation model, custom loaders, context classloader, leaks in app servers
- [ ] `ServiceLoader` / SPI mechanism
- [ ] `Unsafe` — what it was used for and its replacements

## 1.8 Java Platform Module System (JPMS) 🟢
- [ ] `module-info.java`: `requires`, `exports`, `opens`, `uses`, `provides`
- [ ] `requires transitive`, `requires static`
- [ ] Named vs automatic vs unnamed modules; classpath vs module path
- [ ] Split packages problem
- [ ] Strong encapsulation, `--add-opens`/`--add-exports`, illegal-access changes by version
- [ ] `jlink` custom runtime images; `jdeps`, `jmod`
- [ ] Why most enterprise apps still ship on the classpath

## 1.9 Java Version Feature Map 🔴
- [ ] Java 8: lambdas, streams, `java.time`, default methods, Nashorn, PermGen→Metaspace
- [ ] Java 9: modules, JShell, `List.of`, `Flow` API, compact strings, G1 default
- [ ] Java 10: `var`, app class-data sharing
- [ ] Java 11 (LTS): HttpClient, `String` methods, single-file source launch, Flight Recorder open-sourced, ZGC/Epsilon experimental
- [ ] Java 14: switch expressions, helpful NPE, records preview
- [ ] Java 15: text blocks, sealed preview, ZGC/Shenandoah production
- [ ] Java 16: records, pattern matching `instanceof`, `Stream.toList`, strong encapsulation by default
- [ ] Java 17 (LTS): sealed classes, enhanced pseudo-random generators, deprecate Security Manager
- [ ] Java 18: UTF-8 default, simple web server
- [ ] Java 19–20: virtual threads / structured concurrency / scoped values (preview)
- [ ] Java 21 (LTS): **virtual threads**, pattern matching for switch, record patterns, sequenced collections, generational ZGC
- [ ] Java 22: unnamed variables, FFM API final, multi-file source programs
- [ ] Java 23–24: stream gatherers, class-file API, structured concurrency evolution, compact object headers
- [ ] Java 25 (LTS): finalized structured concurrency/scoped values direction, compact source files & instance main methods, ahead-of-time class loading
- [ ] Migration strategy 8→11→17→21→25: classpath breakage, removed APIs, `jdeprscan`, `jdeps`
- [ ] LTS cadence, vendor distributions (Temurin, Corretto, Zulu, Liberica, Oracle, GraalVM), licensing

---
---

# PART 2 — JVM INTERNALS, MEMORY & GARBAGE COLLECTION

## 2.1 JVM Architecture 🔴
- [ ] JVM vs JRE vs JDK; HotSpot vs OpenJ9 vs GraalVM vs Azul Zing/Prime
- [ ] Class file format: magic, constant pool, access flags, fields, methods, attributes
- [ ] Class loading phases: loading → linking (verify, prepare, resolve) → initialization
- [ ] Class initialization triggers (JLS §12.4) & `<clinit>` locking / deadlock
- [ ] Classloader hierarchy: bootstrap, platform, application; parent delegation & breaking it
- [ ] Runtime data areas: heap, metaspace, thread stacks, PC register, native method stack, code cache
- [ ] Frames, operand stack, local variable table
- [ ] Bytecode instruction families; `javap -c` reading skill
- [ ] `invokevirtual` / `invokestatic` / `invokeinterface` / `invokespecial` / `invokedynamic`
- [ ] Object layout: mark word, klass pointer, alignment/padding, compressed oops
- [ ] Compact object headers (JEP 450/519) 🟢
- [ ] JOL (Java Object Layout) for measuring object size

## 2.2 JIT Compilation & Optimization 🟡
- [ ] Interpreter → C1 → C2 tiered compilation; tier levels 0–4
- [ ] Profiling, hot method detection, invocation & backedge counters
- [ ] OSR (on-stack replacement)
- [ ] Inlining: `MaxInlineSize`, `FreqInlineSize`, inlining depth, megamorphic call sites
- [ ] Monomorphic / bimorphic / polymorphic inline caches
- [ ] Escape analysis → scalar replacement & lock elision
- [ ] Loop unrolling, range-check elimination, vectorization/SuperWord
- [ ] Constant folding, dead code elimination, null-check elimination
- [ ] Deoptimization & uncommon traps; why a benchmark can get slower
- [ ] Code cache: size, fragmentation, "CodeCache is full" flush
- [ ] `-XX:+PrintCompilation`, `-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining`, JITWatch
- [ ] Graal JIT vs C2 🟢
- [ ] AOT: GraalVM native-image, Project Leyden, CDS/AppCDS, AOT class loading (Java 24+)
- [ ] Warmup problem in short-lived / serverless workloads

## 2.3 Memory Management & GC 🔴
- [ ] Heap generations: eden, survivor spaces (S0/S1), old gen; TLAB allocation
- [ ] Weak generational hypothesis; promotion, tenuring threshold, premature promotion
- [ ] Card table, remembered sets, write barriers
- [ ] GC roots & reachability; safepoints and time-to-safepoint
- [ ] Reference types: strong, soft, weak, phantom; `ReferenceQueue`; `Cleaner`
- [ ] Stop-the-world vs concurrent vs incremental collection
- [ ] **Serial GC** — when it's right (small heaps, containers)
- [ ] **Parallel GC** — throughput-oriented
- [ ] **G1 GC** — regions, humongous objects, mixed collections, pause target, IHOP, `to-space exhausted`
- [ ] **ZGC** — colored pointers, load barriers, generational ZGC, sub-ms pauses, terabyte heaps
- [ ] **Shenandoah** — Brooks pointers / load-reference barriers, concurrent evacuation
- [ ] **Epsilon** — no-op GC for testing
- [ ] Choosing a collector: latency vs throughput vs footprint 🔴
- [ ] Key flags: `-Xms`, `-Xmx`, `-Xmn`, `-XX:MaxGCPauseMillis`, `-XX:MaxMetaspaceSize`, `-XX:MaxDirectMemorySize`
- [ ] Container awareness: `UseContainerSupport`, `MaxRAMPercentage`, cgroup limits, why `-Xmx` in k8s matters
- [ ] Metaspace: sizing, leaks from classloaders/dynamic proxies
- [ ] Direct/off-heap memory & `OutOfMemoryError: Direct buffer memory`
- [ ] Native memory tracking (`-XX:NativeMemoryTracking`)
- [ ] GC logging: unified logging `-Xlog:gc*`, parsing, GCEasy/GCViewer
- [ ] Allocation rate, promotion rate, live set size — the three numbers that matter
- [ ] Humongous allocation problems in G1
- [ ] Object pooling: when it's a pessimization
- [ ] Memory leak patterns in Java: static collections, unclosed resources, `ThreadLocal` in pooled threads, listener registration, classloader leaks, `ByteBuffer` retention
- [ ] Heap dump acquisition (`jmap`, `-XX:+HeapDumpOnOutOfMemoryError`) and analysis in Eclipse MAT (dominator tree, shallow vs retained heap, leak suspects)

## 2.4 JVM Tuning & Troubleshooting Toolbox 🔴
- [ ] `jcmd` (the swiss army knife): `Thread.print`, `GC.heap_info`, `VM.native_memory`, `JFR.start`
- [ ] `jstack`, `jmap`, `jinfo`, `jstat`, `jps`
- [ ] JFR (Java Flight Recorder): events, settings profiles, continuous recording, low overhead
- [ ] JDK Mission Control: reading a recording, hot methods, allocation profiling, lock contention
- [ ] async-profiler: CPU, alloc, lock, wall-clock modes; flame graphs; why it beats safepoint-biased profilers
- [ ] `perf` + perf-map-agent 🟢
- [ ] Thread dump analysis: BLOCKED/WAITING/TIMED_WAITING, deadlock detection, lock ownership
- [ ] Diagnosing high CPU (`top -H` → `nid` → thread dump)
- [ ] Diagnosing high memory / OOM triage runbook
- [ ] Diagnosing long GC pauses vs long safepoints (`-Xlog:safepoint`)
- [ ] Crash triage: `hs_err_pid` file anatomy, core dumps
- [ ] Remote debugging (JDWP) and its production risks
- [ ] JMX: MBeans, `MBeanServer`, JConsole/VisualVM, exposing custom MBeans

---
---

# PART 3 — CONCURRENCY & PARALLELISM 🔴

## 3.1 Java Memory Model (JMM)
- [ ] Happens-before relation — all rules (program order, monitor lock, volatile, thread start/join, final field, transitivity)
- [ ] Visibility vs atomicity vs ordering — three distinct problems
- [ ] Reordering: compiler, CPU, cache; memory barriers/fences
- [ ] `volatile` semantics: read/write barriers, no atomicity for compound ops
- [ ] Data race definition; benign races are (almost always) a myth
- [ ] Safe publication idioms (static init, volatile, final field, concurrent collection, synchronized)
- [ ] Final field semantics & freeze action; why unsafe publication breaks immutability
- [ ] Double-checked locking — broken vs fixed with `volatile`
- [ ] Word tearing, `long`/`double` non-atomicity (non-volatile)
- [ ] Sequential consistency vs data-race-free guarantee
- [ ] `VarHandle` access modes: plain, opaque, acquire/release, volatile
- [ ] `Thread.onSpinWait`, `Runtime.availableProcessors` in containers

## 3.2 Threads Fundamentals
- [ ] `Thread` lifecycle & states (NEW, RUNNABLE, BLOCKED, WAITING, TIMED_WAITING, TERMINATED)
- [ ] `Runnable` vs `Callable`; `Thread` creation costs
- [ ] Daemon vs non-daemon threads; JVM shutdown semantics; shutdown hooks
- [ ] Thread priorities (and why they're mostly ignored)
- [ ] `Thread.sleep` vs `Object.wait` vs `LockSupport.park`
- [ ] Interruption: cooperative cancellation, `InterruptedException` handling rules, restoring the flag 🔴
- [ ] Deprecated `stop`/`suspend`/`resume` and why
- [ ] `ThreadLocal`: use cases, memory leaks in thread pools, `InheritableThreadLocal`, `remove()` discipline
- [ ] `ThreadFactory`, naming threads (critical for debugging)
- [ ] Uncaught exception handling in threads and pools

## 3.3 Synchronization Primitives
- [ ] `synchronized` methods & blocks; monitor/intrinsic lock; reentrancy
- [ ] Lock coarsening, lock elision, biased locking (removed in 15/18)
- [ ] Object monitor states: thin/inflated locks, `ObjectMonitor`
- [ ] `wait`/`notify`/`notifyAll` — always in a loop, always with a condition predicate
- [ ] Lost wakeup and spurious wakeup
- [ ] `ReentrantLock`: `tryLock`, timed lock, interruptible lock, fairness cost
- [ ] `Condition` objects, multiple wait sets
- [ ] `ReentrantReadWriteLock`: write starvation, lock downgrading (not upgrading)
- [ ] `StampedLock`: optimistic reads, `validate`, not reentrant 🟡
- [ ] `AbstractQueuedSynchronizer` (AQS) internals: state, CLH queue, exclusive vs shared 🟡
- [ ] Deadlock: 4 Coffman conditions, lock ordering, `tryLock` with timeout, detection
- [ ] Livelock, starvation, priority inversion, convoying
- [ ] Lock granularity: coarse vs fine, lock striping, lock splitting
- [ ] Monitor pattern, confinement (thread/stack/instance)

## 3.4 Atomics & Lock-Free Programming 🟡
- [ ] `AtomicInteger`/`AtomicLong`/`AtomicBoolean`/`AtomicReference`
- [ ] CAS semantics, `compareAndSet`, `getAndUpdate`, `accumulateAndGet`
- [ ] ABA problem & `AtomicStampedReference`/`AtomicMarkableReference`
- [ ] `LongAdder`/`DoubleAdder`/`LongAccumulator` — striped counters, when to prefer over `AtomicLong`
- [ ] `AtomicIntegerFieldUpdater` and `VarHandle` alternatives
- [ ] Non-blocking algorithms: Treiber stack, Michael-Scott queue
- [ ] False sharing, cache lines, `@Contended` 🟢
- [ ] Memory barriers cost per architecture (x86 TSO vs ARM weak) 🟢

## 3.5 Executors & Thread Pools 🔴
- [ ] `Executor`, `ExecutorService`, `ScheduledExecutorService`
- [ ] `ThreadPoolExecutor` parameters: core/max pool size, keep-alive, work queue, thread factory, rejection handler
- [ ] Pool sizing: CPU-bound (`N+1`) vs IO-bound (Little's law / Brian Goetz formula)
- [ ] Unbounded queue trap in `Executors.newFixedThreadPool` (max size never reached, OOM)
- [ ] `newCachedThreadPool` unbounded thread creation trap
- [ ] `newSingleThreadExecutor` and task-ordering guarantees
- [ ] Rejection policies: Abort, CallerRuns, Discard, DiscardOldest; custom policies & backpressure
- [ ] Graceful shutdown: `shutdown` vs `shutdownNow` vs `awaitTermination` vs `close` (Java 19)
- [ ] `Future`: `get`, timeout, `cancel(mayInterruptIfRunning)`, `isDone`
- [ ] `CompletionService` / `ExecutorCompletionService`
- [ ] `invokeAll` / `invokeAny`
- [ ] `ScheduledThreadPoolExecutor`: `scheduleAtFixedRate` vs `scheduleWithFixedDelay`, task-failure kills the schedule
- [ ] Monitoring pools: queue depth, active count, completed tasks → metrics
- [ ] `ForkJoinPool`: work stealing, `RecursiveTask`/`RecursiveAction`, `ManagedBlocker`, common pool parallelism flag
- [ ] Thread pool isolation / bulkheads per dependency

## 3.6 Coordination Utilities 🟡
- [ ] `CountDownLatch` (one-shot) vs `CyclicBarrier` (reusable, barrier action)
- [ ] `Semaphore`: permits, fairness, as a rate limiter/bulkhead
- [ ] `Phaser`: dynamic parties, arrival/advance
- [ ] `Exchanger`
- [ ] `BlockingQueue` as a producer-consumer channel; poison pill shutdown
- [ ] `TransferQueue` handoff semantics

## 3.7 CompletableFuture & Async Composition 🔴
- [ ] `supplyAsync`/`runAsync` and default executor (common FJ pool!) — always pass your own
- [ ] `thenApply` vs `thenCompose` vs `thenCombine`; `*Async` variants and which thread runs what
- [ ] `allOf`, `anyOf`, collecting results from `allOf`
- [ ] Exception handling: `exceptionally`, `handle`, `whenComplete`, `completeExceptionally`
- [ ] `CompletionException` unwrapping
- [ ] Timeouts: `orTimeout`, `completeOnTimeout` (Java 9)
- [ ] Cancellation semantics (and why `cancel` doesn't interrupt the work)
- [ ] Blocking inside a CF chain → pool starvation
- [ ] Building async pipelines with retries, fallbacks, fan-out/fan-in
- [ ] Context propagation (MDC, security context, tracing) across async boundaries 🔴

## 3.8 Virtual Threads & Structured Concurrency (Project Loom) 🔴
- [ ] Platform threads vs virtual threads; carrier threads & continuation mounting/unmounting
- [ ] `Thread.ofVirtual()`, `Executors.newVirtualThreadPerTaskExecutor()`
- [ ] Thread-per-request model returns; when virtual threads help (blocking IO) and when they don't (CPU-bound)
- [ ] **Pinning**: `synchronized` blocks (pre-Java 24), native frames; detection with `jdk.tracePinnedThreads`
- [ ] JEP 491 — synchronized no longer pins (Java 24) 🟡
- [ ] Migrating from `synchronized` to `ReentrantLock` for Loom-readiness
- [ ] Don't pool virtual threads; don't use `ThreadLocal` heavily → `ScopedValue`
- [ ] `ScopedValue`: immutable, structured, inheritance to child tasks
- [ ] Structured concurrency: `StructuredTaskScope`, `ShutdownOnFailure`/`ShutdownOnSuccess`, `join`/`throwIfFailed`
- [ ] Observability of millions of threads; thread dumps in JSON
- [ ] Interaction with connection pools, semaphores for limiting, database pool sizing
- [ ] Framework support: Spring Boot 3.2+ `spring.threads.virtual.enabled`, Tomcat/Jetty virtual executors

## 3.9 Reactive Programming 🟡
- [ ] Reactive Streams spec: `Publisher`/`Subscriber`/`Subscription`/`Processor`
- [ ] Backpressure strategies: buffer, drop, latest, error
- [ ] `java.util.concurrent.Flow` API
- [ ] Project Reactor: `Mono`, `Flux`, cold vs hot, `subscribeOn` vs `publishOn`, schedulers
- [ ] Operators: `map`, `flatMap`, `concatMap`, `switchMap`, `zip`, `merge`, `window`, `buffer`, `retryWhen`, `timeout`
- [ ] Context propagation in Reactor (`Context`, `ContextView`, Micrometer context-propagation)
- [ ] RxJava 3 basics & differences 🟢
- [ ] Debugging reactive: `checkpoint()`, `Hooks.onOperatorDebug`, BlockHound
- [ ] Reactive vs virtual threads — the modern decision 🔴
- [ ] Where reactive still wins: streaming, backpressure, high fan-out, low thread footprint

## 3.10 Concurrency Design & Testing 🟡
- [ ] Immutability as the primary concurrency strategy
- [ ] Thread-safety documentation (`@ThreadSafe`, `@GuardedBy`, `@Immutable` — JCIP annotations)
- [ ] Producer-consumer, pipeline, fork-join, actor, CSP models
- [ ] Actor model on JVM: Akka/Pekko basics 🟢
- [ ] Disruptor / ring buffer, mechanical sympathy 🟢
- [ ] Testing concurrent code: `CountDownLatch` choreography, stress tests, `Awaitility`
- [ ] jcstress for JMM-level testing 🟢
- [ ] Deterministic testing, `Thread.yield` tricks, flaky test causes
- [ ] Static analysis for concurrency (ErrorProne `@GuardedBy` checks)
- [ ] Common bugs checklist: check-then-act, read-modify-write, unsafe publication, escaping `this`, mutable shared state, non-atomic compound ops on concurrent collections

---
---

# PART 4 — SOFTWARE DESIGN, PATTERNS & CODE CRAFT

## 4.1 Design Principles 🔴
- [ ] **S**ingle Responsibility — "one reason to change", how to actually apply it
- [ ] **O**pen/Closed — extension points, strategy injection
- [ ] **L**iskov Substitution — preconditions/postconditions/invariants, square-rectangle, `List`/`ImmutableList`
- [ ] **I**nterface Segregation — role interfaces, fat interface smells
- [ ] **D**ependency Inversion — depend on abstractions; DI is not DIP
- [ ] DRY, WET, and the rule of three; when duplication is cheaper than the wrong abstraction
- [ ] KISS, YAGNI, Occam's razor for architecture
- [ ] Law of Demeter / Tell-Don't-Ask
- [ ] Composition over inheritance; fragile base class problem
- [ ] Program to an interface, not an implementation
- [ ] GRASP: information expert, creator, controller, low coupling, high cohesion, polymorphism, pure fabrication, indirection, protected variations
- [ ] Cohesion types (functional → coincidental); coupling types (data → content)
- [ ] Connascence (name, type, meaning, position, algorithm, execution, timing, value, identity) 🟢
- [ ] CUPID properties as a modern alternative to SOLID 🟢
- [ ] Encapsulation, information hiding, invariants
- [ ] Immutability & value semantics
- [ ] Defensive programming vs design-by-contract; preconditions/postconditions/invariants
- [ ] Principle of least astonishment
- [ ] Separation of concerns, layering, dependency direction rules

## 4.2 Gang of Four Patterns 🔴

### 4.2.1 Creational
- [ ] Singleton — enum singleton, holder idiom, DI-scoped alternative, testability problems
- [ ] Factory Method
- [ ] Abstract Factory
- [ ] Builder — classic, fluent, staged/step builder, records + builder, Lombok `@Builder`
- [ ] Prototype — and why `clone()` is a poor fit
- [ ] Object Pool — connection pools, when pooling hurts (GC-friendly objects)
- [ ] Dependency Injection / Service Locator (and why Service Locator is an anti-pattern)

### 4.2.2 Structural
- [ ] Adapter (object vs class adapter)
- [ ] Bridge
- [ ] Composite
- [ ] Decorator — `java.io`, Spring's wrapping proxies
- [ ] Facade
- [ ] Flyweight — `Integer` cache, string pool
- [ ] Proxy — virtual, remote, protection; JDK dynamic proxy vs CGLIB, self-invocation problem 🔴

### 4.2.3 Behavioral
- [ ] Chain of Responsibility — servlet filters, Spring Security filter chain, interceptors
- [ ] Command — undo/redo, task queues
- [ ] Interpreter
- [ ] Iterator — external vs internal iteration
- [ ] Mediator
- [ ] Memento
- [ ] Observer — listeners, event buses, and their leak/ordering pitfalls
- [ ] State — vs enum-based state machines
- [ ] Strategy — the everyday workhorse; strategy map + enum
- [ ] Template Method — and its inheritance cost vs strategy
- [ ] Visitor — double dispatch; replaced by sealed types + pattern matching in modern Java
- [ ] Null Object
- [ ] Pattern recognition in JDK & Spring source — be able to name real examples for each

## 4.3 Enterprise & Integration Patterns 🟡
- [ ] PoEAA: Domain Model, Transaction Script, Table Module, Service Layer
- [ ] Data source patterns: Row Data Gateway, Table Data Gateway, Active Record, Data Mapper
- [ ] Object-relational: Identity Map, Unit of Work, Lazy Load, Identity Field, Foreign Key Mapping
- [ ] Inheritance mapping: single table, class table, concrete table
- [ ] Repository pattern (true DDD repository vs Spring Data interface)
- [ ] Specification pattern
- [ ] DTO, Assembler/Mapper, Value Object, Entity
- [ ] Front Controller, MVC, MVP, MVVM
- [ ] Session state: client, server, database session state
- [ ] Enterprise Integration Patterns (Hohpe): message channel, message router, splitter, aggregator, resequencer, content enricher, normalizer, claim check, dead letter channel, idempotent receiver, correlation identifier, wire tap
- [ ] Anti-corruption layer, gateway, adapter, strangler fig

## 4.4 Domain-Driven Design 🔴

### 4.4.1 Strategic Design
- [ ] Ubiquitous language and why it changes code
- [ ] Bounded context — definition, boundaries, one model per context
- [ ] Context map & relationship patterns: shared kernel, customer/supplier, conformist, anticorruption layer, open host service, published language, separate ways, partnership
- [ ] Core / supporting / generic subdomains and where to invest
- [ ] Domain storytelling, event storming (big picture → process → design level)
- [ ] Bounded contexts → microservice boundaries (and why they're not always 1:1)

### 4.4.2 Tactical Design
- [ ] Entities (identity, lifecycle) vs Value Objects (equality by value, immutable)
- [ ] Aggregates: aggregate root, invariant boundary, transactional consistency boundary
- [ ] Aggregate design rules: small aggregates, reference by identity, eventual consistency across aggregates
- [ ] Repositories (one per aggregate root)
- [ ] Domain services vs application services vs infrastructure services
- [ ] Domain events, integration events, event publishing from aggregates
- [ ] Factories in DDD
- [ ] Modules/packages as bounded-context boundaries
- [ ] Anemic domain model vs rich domain model — the trade-off honestly
- [ ] CQRS as a DDD complement; read models/projections
- [ ] Event sourcing: event store, snapshots, replay, versioning/upcasting, GDPR deletion problem
- [ ] Mapping DDD to Java/Spring: package structure, JPA vs domain purity, ports & adapters

## 4.5 Clean Code & Refactoring 🔴
- [ ] Naming: intention-revealing, searchable, pronounceable, no encodings
- [ ] Function design: small, one level of abstraction, few args, no flag args, no side effects
- [ ] Comments: what to write, what to delete, self-documenting code limits, Javadoc conventions
- [ ] Formatting & consistency; automated formatting (Spotless, google-java-format)
- [ ] Boundaries, error handling readability
- [ ] Code smells catalogue: long method, large class, primitive obsession, data clumps, feature envy, inappropriate intimacy, shotgun surgery, divergent change, message chains, middle man, speculative generality, refused bequest, temporal coupling
- [ ] Refactoring catalogue: extract/inline method, extract class, move method/field, replace conditional with polymorphism, introduce parameter object, replace temp with query, decompose conditional, replace magic number, encapsulate collection, replace inheritance with delegation, split phase
- [ ] Refactoring safely: characterization tests, seams, sprout method/class, wrap method
- [ ] Working Effectively with Legacy Code techniques 🔴
- [ ] Strangler fig migration for legacy systems
- [ ] Mikado method for large refactors 🟢
- [ ] Boy scout rule; refactoring as part of feature work vs big-bang rewrite
- [ ] Technical debt: types (deliberate/inadvertent × prudent/reckless), tracking, paying down, communicating to stakeholders 🔴

## 4.6 API & Library Design 🟡
- [ ] Effective Java items as a design checklist (all 90) 🔴
- [ ] Minimize accessibility; design for inheritance or prohibit it
- [ ] Static factory methods vs constructors
- [ ] Builder for many parameters; telescoping-constructor anti-pattern
- [ ] Prefer immutability; make defensive copies
- [ ] Return empty collections, not null
- [ ] Fail fast on invalid parameters
- [ ] Overload resolution safety; avoid ambiguous overloads
- [ ] Backward compatibility: source vs binary vs behavioral compatibility 🔴
- [ ] Semantic versioning; deprecation policy; migration guides
- [ ] Package/module structure, `internal` packages, JPMS `exports`
- [ ] Javadoc quality: `@param`, `@return`, `@throws`, `@implSpec`, `@apiNote`, `{@code}`, `{@link}`
- [ ] Fluent/DSL API design, method chaining, staged builders
- [ ] Null handling policy: `@Nullable`/`@NonNull`, JSpecify, package-level defaults
- [ ] Designing for testability: seams, injectable clocks/randoms, avoiding statics

## 4.7 Low-Level Design (LLD) Practice 🔴
- [ ] Class diagrams, sequence diagrams, state diagrams (UML basics that still matter)
- [ ] Translating requirements → entities → relationships → interfaces
- [ ] Classic LLD exercises: parking lot, elevator, library management, vending machine, ATM, chess/tic-tac-toe, splitwise, BookMyShow, food delivery, ride hailing, rate limiter, LRU cache, logging framework, notification service, in-memory key-value store, file system, snake & ladder, cab booking, hotel booking, inventory, order management
- [ ] Concurrency in LLD answers (locking strategy, idempotency)
- [ ] Extensibility discussion: what changes next quarter?
- [ ] Trade-off narration: why this pattern, what you rejected

---
---

# PART 5 — ARCHITECTURE & DISTRIBUTED SYSTEMS

## 5.1 Architectural Thinking 🔴
- [ ] Architecture vs design; what decisions are "architecturally significant"
- [ ] Quality attributes / architecture characteristics: performance, scalability, availability, reliability, security, maintainability, testability, deployability, observability, elasticity, portability, cost
- [ ] Trade-off analysis; "everything is a trade-off, there are no best practices"
- [ ] Architecture Decision Records (ADR): format, when to write, storing in repo 🔴
- [ ] C4 model: context, container, component, code; when each diagram is useful
- [ ] arc42 / 4+1 view model 🟢
- [ ] Fitness functions & evolutionary architecture; ArchUnit as executable architecture
- [ ] Conway's law & inverse Conway maneuver; Team Topologies (stream-aligned, platform, enabling, complicated-subsystem)
- [ ] Architecture governance without becoming an ivory tower
- [ ] Build vs buy vs open source evaluation
- [ ] Risk storming, threat modeling as architecture inputs
- [ ] Documenting architecture: living docs, diagrams-as-code (Structurizr, PlantUML, Mermaid)

## 5.2 Architecture Styles 🔴
- [ ] Layered / n-tier — pros, the "sinkhole" anti-pattern
- [ ] Modular monolith — module boundaries, enforcement (Spring Modulith, ArchUnit), why it's often the right default 🔴
- [ ] Hexagonal (ports & adapters), onion, clean architecture — dependency rule, mapping to Java packages
- [ ] Microservices — decomposition strategies, sizing, data ownership, distributed monolith anti-pattern
- [ ] Service-oriented architecture, ESB legacy
- [ ] Event-driven architecture: broker vs mediator topology, choreography vs orchestration
- [ ] CQRS — command/query separation at the architecture level, read model sync lag
- [ ] Event sourcing — full lifecycle and operational cost
- [ ] Serverless / FaaS — cold starts on JVM, GraalVM/SnapStart, when it fits
- [ ] Space-based / grid architecture 🟢
- [ ] Microkernel / plugin architecture
- [ ] Pipes and filters, batch architecture
- [ ] Cell-based architecture 🟢
- [ ] Monolith → microservices migration: strangler fig, branch by abstraction, seams, data decomposition
- [ ] Microservices → monolith consolidation (when it's correct)

## 5.3 Distributed Systems Theory 🔴
- [ ] Fallacies of distributed computing (all 8)
- [ ] CAP theorem — precise statement, common misinterpretations
- [ ] PACELC — the latency half everyone forgets
- [ ] Consistency models: linearizability, sequential, causal, read-your-writes, monotonic reads, eventual
- [ ] ACID vs BASE
- [ ] Consensus: Paxos (concept), Raft (leader election, log replication, safety), ZAB
- [ ] Quorums: R + W > N, sloppy quorums, hinted handoff
- [ ] Leader election, split brain, fencing tokens
- [ ] Failure detection, heartbeats, phi-accrual, gossip protocols
- [ ] Time: physical clocks, NTP drift, logical clocks, Lamport timestamps, vector clocks, hybrid logical clocks, TrueTime
- [ ] Partitioning/sharding: range, hash, consistent hashing, virtual nodes, rebalancing, hotspots
- [ ] Replication: leader-follower, multi-leader, leaderless; sync vs async; replication lag
- [ ] Conflict resolution: LWW, CRDTs, application-level merge
- [ ] Distributed transactions: 2PC, 3PC, XA, blocking coordinator problem
- [ ] Saga pattern: choreography vs orchestration, compensating transactions, semantic locks 🔴
- [ ] Transactional outbox / inbox, CDC-based publishing 🔴
- [ ] Idempotency: keys, dedupe stores, natural idempotency, at-least-once + idempotent = effectively-once 🔴
- [ ] Delivery semantics: at-most-once, at-least-once, exactly-once (and why it's really "effectively once")
- [ ] Message ordering guarantees and how to preserve them
- [ ] Distributed locking: Redis Redlock debate, ZooKeeper/etcd, DB advisory locks, lease + fencing
- [ ] Backpressure & flow control across services
- [ ] Cascading failures, retry storms, thundering herd, metastable failures 🔴
- [ ] Head-of-line blocking
- [ ] Tail latency amplification; hedged requests; the "tail at scale" problem

## 5.4 Resilience & Reliability Patterns 🔴
- [ ] Timeouts everywhere (connect, read, total, per-hop budgets)
- [ ] Retries: idempotency prerequisite, exponential backoff, full/decorrelated jitter, retry budgets, max attempts
- [ ] Circuit breaker: states, sliding window (count/time), half-open probes, tuning
- [ ] Bulkhead: thread pool vs semaphore isolation
- [ ] Rate limiting: token bucket, leaky bucket, fixed/sliding window, distributed limiters
- [ ] Load shedding, admission control, priority queues
- [ ] Fallbacks & graceful degradation; static/cached responses
- [ ] Failover, health checks (liveness/readiness/startup), outlier detection
- [ ] Redundancy: active-active, active-passive, multi-AZ, multi-region
- [ ] Disaster recovery: RTO/RPO, backup strategy, restore drills
- [ ] Chaos engineering: hypothesis, blast radius, game days, tools (Chaos Monkey, LitmusChaos)
- [ ] Resilience4j: `CircuitBreaker`, `RateLimiter`, `Bulkhead`, `Retry`, `TimeLimiter`, `Cache`, decorator composition order 🔴
- [ ] Hystrix legacy & why it's in maintenance
- [ ] Service mesh–level resilience (Istio retries/timeouts/outlier detection) vs library-level
- [ ] SLI/SLO/SLA and error budgets driving reliability work 🔴

## 5.5 Scalability & Caching 🔴
- [ ] Vertical vs horizontal scaling; stateless service design
- [ ] Session management: sticky sessions vs distributed sessions vs stateless JWT
- [ ] Load balancing: L4 vs L7, algorithms (RR, least-conn, EWMA, consistent hash), client-side LB
- [ ] Autoscaling: HPA/VPA, metrics-based, predictive; JVM warmup vs autoscaling
- [ ] Read replicas, write scaling, sharding strategies
- [ ] Caching layers: client, CDN, reverse proxy, application, distributed, database
- [ ] Cache patterns: cache-aside, read-through, write-through, write-behind, refresh-ahead
- [ ] Eviction policies: LRU, LFU, FIFO, TinyLFU (Caffeine), size vs time-based
- [ ] TTL vs invalidation; cache stampede/thundering herd; probabilistic early expiry; request coalescing
- [ ] Cache penetration (null caching, bloom filters), cache avalanche
- [ ] Consistency: cache invalidation strategies, versioned keys, event-driven invalidation
- [ ] Local (Caffeine, Ehcache) vs distributed (Redis, Hazelcast, Memcached, Infinispan)
- [ ] Near-cache / two-level caching
- [ ] Spring Cache abstraction: `@Cacheable`, `@CacheEvict`, `@CachePut`, key generators, self-invocation trap
- [ ] Redis data structures & when to use each; pipelining, Lua scripts, cluster mode, persistence (RDB/AOF)
- [ ] Redis as: cache, lock, rate limiter, queue (Streams), session store, leaderboard
- [ ] CDN & edge caching, cache headers (`Cache-Control`, `ETag`, `Last-Modified`, `Vary`)
- [ ] Content negotiation & compression (gzip, brotli)
- [ ] Database connection pool sizing as a scalability lever
- [ ] Estimating capacity: back-of-envelope math, QPS, storage, bandwidth 🔴

## 5.6 System Design Practice 🔴
- [ ] Requirements clarification framework (functional, non-functional, scale, constraints)
- [ ] Capacity estimation, API design, high-level diagram, data model, deep dives, bottlenecks, trade-offs
- [ ] Classic designs: URL shortener, rate limiter, news feed, chat/messaging, notification system, web crawler, search autocomplete, YouTube/Netflix, Uber/ride-share, payment system, ticket booking, ad click aggregation, distributed job scheduler, metrics/monitoring system, distributed cache, object storage, key-value store, distributed queue, real-time leaderboard, collaborative editor, e-commerce checkout, inventory reservation, fraud detection pipeline
- [ ] Domain-specific for enterprise Java: order management, billing/subscription, multi-tenant SaaS, data ingestion pipeline, reporting/analytics service, workflow engine, document management, audit trail service
- [ ] Multi-tenancy: silo vs pool vs bridge, tenant isolation, per-tenant data/config, noisy neighbor
- [ ] Migration designs: zero-downtime schema change, dual writes, backfill, shadow traffic, cutover, rollback plan 🔴

---
---

# PART 6 — SPRING ECOSYSTEM 🔴

## 6.1 Spring Core
- [ ] IoC container: `BeanFactory` vs `ApplicationContext`
- [ ] Bean definition sources: `@Component` scan, `@Bean` in `@Configuration`, XML legacy, functional registration
- [ ] Dependency injection: constructor (preferred) vs setter vs field; circular dependency handling & `@Lazy`
- [ ] Bean scopes: singleton, prototype, request, session, application, websocket, custom; scoped proxies
- [ ] Bean lifecycle: instantiation → populate → aware callbacks → `BeanPostProcessor` before → `@PostConstruct`/`afterPropertiesSet`/init-method → after → use → `@PreDestroy`/`DisposableBean`
- [ ] `BeanFactoryPostProcessor` vs `BeanPostProcessor`; `@Configuration` CGLIB enhancement (proxyBeanMethods)
- [ ] `@Primary`, `@Qualifier`, `@Order`, `@Priority`, injecting `List<T>`/`Map<String,T>`
- [ ] `@Conditional` family, `@Profile`, `@ConditionalOnProperty/Class/Bean/MissingBean`
- [ ] `ApplicationContext` events, `@EventListener`, `@TransactionalEventListener`, async events
- [ ] `Environment`, `PropertySource` ordering, `@Value`, SpEL syntax & pitfalls
- [ ] `@ConfigurationProperties`: relaxed binding, validation, records, nested, `@ConstructorBinding`
- [ ] Resource abstraction, `ResourceLoader`
- [ ] `ObjectProvider`, `ApplicationContextAware`, and why to avoid container coupling
- [ ] Spring AOP: proxy-based (JDK dynamic vs CGLIB), pointcut expressions, advice types, `@Aspect`
- [ ] **Self-invocation problem** (why `@Transactional`/`@Cacheable`/`@Async` silently do nothing) 🔴
- [ ] `AopContext.currentProxy()`, self-injection, or refactor — the three fixes
- [ ] Proxy limitations: final classes/methods, private methods
- [ ] AspectJ weaving (compile-time, load-time) when proxies aren't enough
- [ ] Spring Expression Language depth 🟢

## 6.2 Spring Boot 🔴
- [ ] Auto-configuration mechanism: `@EnableAutoConfiguration`, `AutoConfiguration.imports`, ordering, `@AutoConfigureBefore/After`
- [ ] Writing your own starter & auto-configuration
- [ ] Debugging autoconfig: `--debug` condition evaluation report
- [ ] Externalized configuration: precedence order (all ~17 levels), profiles, `application-{profile}.yml`, `spring.config.import`
- [ ] Config in k8s: ConfigMaps, Secrets, env vars, Spring Cloud Config, Vault
- [ ] Relaxed binding rules, `@ConfigurationProperties` validation
- [ ] Actuator: health (composite, groups, custom indicators), info, metrics, env, loggers, threaddump, heapdump, httpexchanges, mappings, conditions
- [ ] Actuator security & exposure in production 🔴
- [ ] Graceful shutdown, `server.shutdown=graceful`, lifecycle timeout
- [ ] Embedded servers: Tomcat vs Jetty vs Undertow vs Netty; tuning threads/connections
- [ ] Fat jar structure, `JarLauncher`, layered jars for Docker caching
- [ ] Buildpacks / `spring-boot:build-image`
- [ ] Spring Boot 3.x: Jakarta namespace, Java 17 baseline, native support, observability rewrite (Micrometer Observation API), virtual threads flag
- [ ] Boot 2 → 3 migration checklist 🔴
- [ ] `spring-boot-devtools`, restart classloader
- [ ] Failure analyzers, startup failure diagnostics
- [ ] Application startup tracing (`ApplicationStartup`, `BufferingApplicationStartup`)
- [ ] Testing slices: `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`, `@JsonTest`, `@RestClientTest`, `@TestConfiguration`, `@MockitoBean`/`@MockBean`
- [ ] Context caching in tests & why your suite is slow 🔴

## 6.3 Spring MVC & Web 🔴
- [ ] `DispatcherServlet` flow: handler mapping → adapter → controller → view resolver → render
- [ ] `@RestController`, `@RequestMapping` and shortcuts, path patterns (`PathPattern` vs `AntPathMatcher`)
- [ ] Argument resolvers: `@PathVariable`, `@RequestParam`, `@RequestBody`, `@RequestHeader`, `@CookieValue`, `@ModelAttribute`, `@MatrixVariable`
- [ ] `HttpMessageConverter` chain, content negotiation, `produces`/`consumes`
- [ ] `ResponseEntity`, status codes, headers, `@ResponseStatus`
- [ ] Validation: `@Valid`/`@Validated`, group validation, custom `ConstraintValidator`, cross-field
- [ ] Exception handling: `@ExceptionHandler`, `@ControllerAdvice`, `ResponseEntityExceptionHandler`, `ProblemDetail` (RFC 9457)
- [ ] Interceptors vs filters vs `HandlerMethodArgumentResolver` — when to use which
- [ ] CORS configuration (global + per-endpoint)
- [ ] File upload/download, streaming responses, `StreamingResponseBody`, SSE
- [ ] Async MVC: `Callable`, `DeferredResult`, `WebAsyncTask`, servlet 3 async
- [ ] `RestTemplate` (maintenance), `WebClient`, `RestClient` (Boot 3.2), `@HttpExchange` declarative clients
- [ ] Client-side timeouts, connection pooling, retry/circuit breaker integration
- [ ] WebFlux: `@Controller` vs functional `RouterFunction`, Netty, reactive filters, backpressure
- [ ] WebSocket & STOMP, SockJS
- [ ] GraphQL with Spring for GraphQL: schema-first, `@QueryMapping`, dataloader/N+1
- [ ] gRPC on Spring 🟢
- [ ] Server-side rendering options (Thymeleaf) 🟢

## 6.4 Spring Data & Transactions 🔴
- [ ] `Repository` hierarchy: `CrudRepository`, `PagingAndSortingRepository`, `JpaRepository`, `ListCrudRepository`
- [ ] Derived query methods & their limits; `@Query` (JPQL & native), named queries
- [ ] Projections: interface-based (closed/open), DTO/class-based, dynamic
- [ ] `Pageable`, `Slice`, `Page`, `Sort`; count query cost; keyset (seek) pagination
- [ ] Specifications / Criteria API; QueryDSL; Query by Example
- [ ] `@Modifying` queries, `clearAutomatically`, `flushAutomatically`
- [ ] Auditing: `@CreatedDate`, `@LastModifiedBy`, `AuditorAware`
- [ ] Custom repository implementations
- [ ] Spring Data JDBC vs JPA — aggregate-oriented persistence 🟡
- [ ] Spring Data MongoDB / Redis / Elasticsearch / Cassandra basics
- [ ] `@Transactional`: propagation (REQUIRED, REQUIRES_NEW, NESTED, SUPPORTS, NOT_SUPPORTED, MANDATORY, NEVER) 🔴
- [ ] Isolation levels via Spring; `readOnly=true` semantics & optimizations
- [ ] Rollback rules: unchecked rolls back, checked doesn't (unless `rollbackFor`) 🔴
- [ ] Transaction proxy pitfalls: self-invocation, private methods, `final`
- [ ] `TransactionTemplate`, programmatic transactions
- [ ] `TransactionSynchronizationManager`, `afterCommit` hooks
- [ ] Transaction boundaries & the "open session in view" anti-pattern 🔴
- [ ] Distributed transactions/JTA in Spring; why to avoid; saga instead
- [ ] `@Transactional` + `@Async` + virtual threads interactions

## 6.5 Spring Security 🔴
- [ ] Filter chain architecture, `SecurityFilterChain` bean (Boot 3 lambda DSL)
- [ ] `SecurityContext`, `SecurityContextHolder`, strategies (ThreadLocal/Inheritable), async propagation
- [ ] `AuthenticationManager`, `AuthenticationProvider`, `UserDetailsService`, `UserDetails`
- [ ] Password encoding: `DelegatingPasswordEncoder`, bcrypt/scrypt/argon2, upgrade strategy
- [ ] Authorization: `authorizeHttpRequests`, `@PreAuthorize`/`@PostAuthorize`/`@Secured`, SpEL in security
- [ ] Method security & AOP ordering
- [ ] CSRF: when needed, when not (stateless APIs), token repositories
- [ ] Session management: fixation protection, concurrency control, `SessionCreationPolicy.STATELESS`
- [ ] CORS + security ordering pitfalls
- [ ] Form login, HTTP Basic, remember-me
- [ ] OAuth2 resource server: JWT validation, JWK set, issuer, audience, scopes → authorities
- [ ] OAuth2 client: authorization code + PKCE, client credentials, token relay, refresh
- [ ] OIDC login; ID token vs access token
- [ ] Spring Authorization Server 🟢
- [ ] SAML 2.0 support 🟢
- [ ] mTLS / X.509 authentication
- [ ] Security headers: HSTS, CSP, X-Frame-Options, referrer policy
- [ ] Multi-tenancy in security (tenant resolution, per-tenant issuers)
- [ ] Testing: `@WithMockUser`, `@WithSecurityContext`, `SecurityMockMvcRequestPostProcessors`
- [ ] Common misconfigurations & how to audit them 🔴

## 6.6 Spring Cloud & Ecosystem 🟡
- [ ] Spring Cloud Config Server/Client, refresh scope, `@RefreshScope`, bus
- [ ] Service discovery: Eureka, Consul, k8s-native discovery
- [ ] Spring Cloud Gateway: routes, predicates, filters, rate limiting, circuit breaker integration
- [ ] Spring Cloud OpenFeign: declarative clients, error decoders, interceptors
- [ ] Spring Cloud LoadBalancer
- [ ] Spring Cloud CircuitBreaker (Resilience4j)
- [ ] Spring Cloud Stream: binders (Kafka/Rabbit), functional model, DLQ, partitioning
- [ ] Spring Cloud Sleuth → Micrometer Tracing migration
- [ ] Spring Cloud Contract (consumer-driven contracts)
- [ ] Spring Cloud Kubernetes
- [ ] Spring Batch: job/step/chunk, readers/processors/writers, restartability, partitioning, remote chunking, job repository 🟡
- [ ] Spring Integration: channels, endpoints, EIP implementation 🟢
- [ ] Spring Modulith: modules, verification, events, documentation 🟡
- [ ] Spring Shell, Spring StateMachine 🟢
- [ ] Spring AI: chat clients, embeddings, vector stores, RAG, function calling, MCP 🟡
- [ ] Spring Native / GraalVM AOT: hints, reflection config, build-time initialization

## 6.7 Jakarta EE & Alternatives 🟢
- [ ] Jakarta EE 9/10/11: namespace change, profiles (core, web, platform)
- [ ] CDI: beans, scopes, qualifiers, producers, interceptors, decorators, events
- [ ] JAX-RS/Jakarta REST, JSON-B, JSON-P
- [ ] EJB legacy: stateless/stateful/singleton, why it faded
- [ ] Servlet API: lifecycle, filters, listeners, async servlets, `ServletContext`
- [ ] Application servers: WildFly, Payara, Open Liberty, WebLogic, WebSphere
- [ ] **Quarkus**: build-time DI, live reload, native image, extensions, Panache 🟡
- [ ] **Micronaut**: AOT DI, low memory, GraalVM-first 🟡
- [ ] **Helidon** (SE/MP), **Vert.x** (event loop, verticles), **Dropwizard**, **Javalin**, **Ktor** 🟢
- [ ] Choosing a framework: startup time, memory, ecosystem, team skills, serverless fit

---
---

# PART 7 — PERSISTENCE, JPA & DATABASES 🔴

## 7.1 JDBC Fundamentals
- [ ] `DriverManager` vs `DataSource`; JDBC URL anatomy
- [ ] `Connection`, `Statement`, `PreparedStatement`, `CallableStatement`
- [ ] SQL injection and why `PreparedStatement` is mandatory 🔴
- [ ] `ResultSet`: types, concurrency, holdability, fetch size, streaming large results
- [ ] Batch updates, `addBatch`/`executeBatch`, `rewriteBatchedStatements` (MySQL)
- [ ] Transaction control: `setAutoCommit`, `commit`, `rollback`, savepoints
- [ ] Isolation levels via JDBC
- [ ] Connection pooling: HikariCP config (`maximumPoolSize`, `connectionTimeout`, `idleTimeout`, `maxLifetime`, `leakDetectionThreshold`), sizing formula 🔴
- [ ] Pool exhaustion diagnosis
- [ ] `JdbcTemplate` / `NamedParameterJdbcTemplate` / `JdbcClient` (Spring 6.1)
- [ ] Result mapping: `RowMapper`, `ResultSetExtractor`
- [ ] `SQLException` hierarchy, vendor error codes, Spring's `DataAccessException` translation
- [ ] R2DBC for reactive access 🟢

## 7.2 JPA & Hibernate 🔴
- [ ] JPA spec vs Hibernate implementation vs EclipseLink
- [ ] Entity lifecycle states: transient, managed, detached, removed
- [ ] `EntityManager` / `Session` API; persistence context as first-level cache
- [ ] Dirty checking & automatic flush; `FlushModeType`
- [ ] `persist` vs `merge` vs `save`/`saveOrUpdate`; `getReference` vs `find`
- [ ] Identity generation: `IDENTITY` (kills batching), `SEQUENCE`, `TABLE`, `UUID`, allocation size & `pooled` optimizers 🔴
- [ ] Mappings: `@Entity`, `@Table`, `@Column`, `@Embedded`/`@Embeddable`, `@ElementCollection`
- [ ] Relationships: `@OneToOne`, `@OneToMany`, `@ManyToOne`, `@ManyToMany`; owning side, `mappedBy`, join tables
- [ ] Bidirectional consistency helper methods
- [ ] `FetchType.LAZY` vs `EAGER`; why EAGER is almost always wrong 🔴
- [ ] `LazyInitializationException` — real fixes vs OSIV band-aid
- [ ] **N+1 select problem**: detection and fixes (`JOIN FETCH`, `@EntityGraph`, batch size, subselect) 🔴
- [ ] `@BatchSize`, `@Fetch(SUBSELECT)`, `hibernate.default_batch_fetch_size`
- [ ] Entity graphs (static & dynamic)
- [ ] Cascade types: PERSIST, MERGE, REMOVE, REFRESH, DETACH, ALL; `orphanRemoval`
- [ ] Inheritance strategies: SINGLE_TABLE, JOINED, TABLE_PER_CLASS, `@MappedSuperclass` — trade-offs
- [ ] `equals`/`hashCode` for entities (natural id vs business key vs id) 🔴
- [ ] JPQL/HQL: joins, fetch joins, constructor expressions, `DISTINCT` and its pass-through hint
- [ ] Criteria API & metamodel generation; QueryDSL alternative
- [ ] Native queries & result set mapping, `@SqlResultSetMapping`
- [ ] Stored procedure calls
- [ ] DTO projections for read paths — the biggest performance lever 🔴
- [ ] Second-level cache: providers (Ehcache, Infinispan, Hazelcast), cache concurrency strategies, query cache & its dangers
- [ ] Locking: optimistic (`@Version`, `OptimisticLockException`), pessimistic (`PESSIMISTIC_READ/WRITE`, `FOR UPDATE`, `NOWAIT`, `SKIP LOCKED`) 🔴
- [ ] Batch inserts/updates: `hibernate.jdbc.batch_size`, `order_inserts`, `order_updates`, flush+clear loop
- [ ] Stateless session for bulk operations
- [ ] Bulk JPQL update/delete and stale persistence context
- [ ] Mapping enums (`@Enumerated`), JSON columns, arrays, custom `UserType`/`AttributeConverter`
- [ ] `@Formula`, `@Where`/`@SQLRestriction`, `@Filter`, soft deletes
- [ ] Multi-tenancy in Hibernate: schema, database, discriminator
- [ ] Hibernate statistics, SQL logging (`show_sql` vs proper logging), Hypersistence utils, datasource-proxy
- [ ] Hibernate 6 changes: `SqmQuery`, new type system, performance 🟡
- [ ] Schema generation — never `ddl-auto=update` in production 🔴
- [ ] When NOT to use JPA (reporting, bulk, complex SQL) → jOOQ/JdbcTemplate/MyBatis 🔴

## 7.3 SQL & Relational Modeling 🔴
- [ ] SQL fundamentals: SELECT, JOIN types (inner, left/right/full outer, cross, self), subqueries, correlated subqueries
- [ ] Aggregation, `GROUP BY`, `HAVING`, `GROUPING SETS`/`ROLLUP`/`CUBE`
- [ ] Window functions: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`/`LEAD`, `SUM() OVER`, frames 🔴
- [ ] CTEs & recursive CTEs
- [ ] Set operations: UNION/UNION ALL, INTERSECT, EXCEPT
- [ ] `EXISTS` vs `IN` vs `JOIN` performance
- [ ] NULL semantics & three-valued logic
- [ ] `MERGE`/upsert (`ON CONFLICT`, `ON DUPLICATE KEY`)
- [ ] Normalization 1NF→BCNF; when to denormalize
- [ ] Keys: primary, natural vs surrogate, composite, foreign keys, unique constraints
- [ ] Constraints & check constraints; enforcing invariants in DB vs app
- [ ] Data types: numeric precision, `VARCHAR` vs `TEXT`, `TIMESTAMPTZ`, JSON/JSONB, arrays, UUID storage
- [ ] Indexes: B-tree, hash, GIN/GiST, bitmap, covering index, partial index, expression index, composite index column order 🔴
- [ ] Index selectivity, cardinality, statistics, when indexes hurt writes
- [ ] Query plans: `EXPLAIN`/`EXPLAIN ANALYZE`, seq scan vs index scan vs bitmap scan, nested loop vs hash join vs merge join 🔴
- [ ] Query tuning workflow: find slow query → plan → index/rewrite → verify
- [ ] Partitioning: range, list, hash; partition pruning
- [ ] Materialized views, refresh strategies
- [ ] Triggers, stored procedures — pros/cons in modern architectures
- [ ] Views and security

## 7.4 Transactions & Concurrency in Databases 🔴
- [ ] ACID in depth
- [ ] Isolation levels: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE
- [ ] Anomalies: dirty read, non-repeatable read, phantom read, lost update, write skew, read skew
- [ ] MVCC: how Postgres/MySQL implement it, snapshots, vacuum/bloat, undo log
- [ ] Locking: row/page/table locks, shared vs exclusive, gap locks & next-key locks (InnoDB), intention locks
- [ ] Deadlocks: detection, victim selection, prevention by lock ordering, diagnosing from logs 🔴
- [ ] `SELECT ... FOR UPDATE`, `SKIP LOCKED` for queue tables
- [ ] Long-running transactions & their damage
- [ ] Advisory locks
- [ ] Serializable snapshot isolation (SSI) & retry-on-serialization-failure
- [ ] Optimistic concurrency at API level (ETag/If-Match)

## 7.5 Database Operations & Evolution 🔴
- [ ] Migration tools: Flyway (versioned/repeatable/baseline) & Liquibase (changelog, contexts, rollback)
- [ ] Migration in CI/CD, per-environment, and in k8s (init containers, jobs)
- [ ] Zero-downtime schema changes: expand/contract, backward-compatible steps, dual-write, backfill, cleanup 🔴
- [ ] Adding a NOT NULL column / renaming a column safely
- [ ] Online DDL tools (pt-online-schema-change, gh-ost) 🟢
- [ ] Backups: full/incremental, PITR, restore testing
- [ ] Replication setup & lag monitoring; read-your-writes with replicas
- [ ] Failover & connection handling; retry on connection reset
- [ ] Monitoring: slow query log, pg_stat_statements, wait events, connections, cache hit ratio, bloat
- [ ] Capacity: table growth, archival, TTL/partition drop, cold storage
- [ ] Data lifecycle: GDPR deletion, anonymization, retention policies

## 7.6 NoSQL & Polyglot Persistence 🟡
- [ ] When NOT to use a relational DB — honest criteria
- [ ] Document stores: MongoDB (documents, indexes, aggregation pipeline, transactions, sharding, replica sets, read/write concerns)
- [ ] Key-value: Redis, DynamoDB (partition/sort key, GSI/LSI, single-table design, capacity modes, hot partitions)
- [ ] Wide-column: Cassandra/ScyllaDB (partition key design, clustering columns, tunable consistency, tombstones, compaction, anti-patterns)
- [ ] Search: Elasticsearch/OpenSearch (inverted index, analyzers, mappings, relevance/BM25, aggregations, shards/replicas, index lifecycle)
- [ ] Graph: Neo4j, Cypher basics 🟢
- [ ] Time series: InfluxDB, TimescaleDB, Prometheus TSDB 🟢
- [ ] Vector DBs: pgvector, Milvus, Pinecone, Qdrant — HNSW/IVF, similarity metrics 🟢
- [ ] Object storage: S3 semantics, consistency, presigned URLs, multipart upload, lifecycle rules
- [ ] Choosing a datastore: access patterns first, then consistency, then scale
- [ ] Polyglot persistence cost: operational burden, consistency across stores
- [ ] Data synchronization: CDC (Debezium), dual writes danger, outbox

---
---

# PART 8 — MESSAGING & EVENT STREAMING 🟡

## 8.1 Messaging Fundamentals 🔴
- [ ] Queue vs topic; point-to-point vs pub/sub
- [ ] Push vs pull consumption
- [ ] Message anatomy: headers, key, payload, metadata
- [ ] Delivery guarantees: at-most-once, at-least-once, exactly-once
- [ ] Acknowledgement models: auto, manual, client-side, transactional
- [ ] Ordering guarantees & partition/key-based ordering
- [ ] Consumer groups & competing consumers
- [ ] Dead letter queues, parking lot, poison message handling 🔴
- [ ] Retry topics vs in-place retry vs blocking retry
- [ ] Idempotent consumers & dedupe strategies
- [ ] Message schema & evolution: backward/forward/full compatibility 🔴
- [ ] Serialization formats: JSON, Avro, Protobuf, Thrift, MessagePack — trade-offs
- [ ] Schema registry: compatibility modes, subject naming
- [ ] Poison pill, head-of-line blocking, consumer lag
- [ ] Backpressure & flow control
- [ ] Message size limits, claim check pattern for large payloads
- [ ] Event vs command vs document message semantics
- [ ] Event notification vs event-carried state transfer vs event sourcing

## 8.2 Apache Kafka 🔴
- [ ] Architecture: brokers, topics, partitions, replicas, leader/follower, ISR
- [ ] Log structure: segments, offsets, retention (time/size/compaction), tiered storage
- [ ] Log compaction semantics & tombstones
- [ ] ZooKeeper vs KRaft mode
- [ ] Producer: acks (0/1/all), `min.insync.replicas`, batching (`linger.ms`, `batch.size`), compression, `max.in.flight`, retries, idempotent producer, partitioner (default/sticky/custom)
- [ ] Producer transactions & exactly-once semantics (EOS), `transactional.id`
- [ ] Consumer: group coordinator, rebalance protocols (eager vs cooperative sticky), static membership
- [ ] Offset management: auto-commit dangers, manual commit sync/async, offset reset policies
- [ ] `max.poll.records`, `max.poll.interval.ms`, `session.timeout.ms`, heartbeat thread
- [ ] Consumer lag: measuring, alerting, causes, fixes
- [ ] Partition assignment strategies & scaling consumers
- [ ] Replication, unclean leader election, durability trade-offs
- [ ] Kafka Streams: KStream/KTable/GlobalKTable, state stores, RocksDB, windowing, joins, exactly-once, topology, interactive queries 🟡
- [ ] ksqlDB 🟢
- [ ] Kafka Connect: source/sink connectors, SMTs, converters, distributed mode, Debezium CDC 🟡
- [ ] Security: SASL (PLAIN/SCRAM/GSSAPI/OAUTHBEARER), TLS, ACLs, quotas
- [ ] Operations: partition count planning, rebalancing partitions, adding brokers, monitoring (JMX metrics that matter), disk/network sizing
- [ ] Multi-datacenter: MirrorMaker 2, cluster linking 🟢
- [ ] Spring Kafka: `@KafkaListener`, containers, error handlers, `DefaultErrorHandler`, retry topics, `KafkaTemplate`, transactions, batch listeners 🔴
- [ ] Testing Kafka: embedded Kafka, Testcontainers
- [ ] Common production incidents: rebalance storms, lag spikes, ISR shrink, duplicate processing

## 8.3 Other Brokers 🟡
- [ ] JMS API: `ConnectionFactory`, `Session`, ack modes, durable subscriptions, selectors
- [ ] RabbitMQ / AMQP: exchanges (direct, topic, fanout, headers), bindings, routing keys, queues, TTL, DLX, priority, quorum vs classic queues, publisher confirms, prefetch/QoS
- [ ] Spring AMQP: `RabbitTemplate`, `@RabbitListener`, retry/recovery
- [ ] ActiveMQ / Artemis 🟢
- [ ] Apache Pulsar: topics, subscriptions (exclusive/shared/failover/key_shared), tiered storage 🟢
- [ ] AWS SQS (standard vs FIFO, visibility timeout, long polling) / SNS / EventBridge 🟡
- [ ] Google Pub/Sub, Azure Service Bus 🟢
- [ ] NATS / NATS JetStream 🟢
- [ ] Redis Streams as a lightweight queue
- [ ] Database-backed queues (`SKIP LOCKED`) — when they're the right call
- [ ] Choosing a broker: throughput, ordering, retention, replay, ops cost 🔴

---
---

# PART 9 — APIs & INTEGRATION 🔴

## 9.1 HTTP & Web Fundamentals 🔴
- [ ] HTTP/1.1 semantics: methods, safe/idempotent/cacheable matrix, status codes (full 1xx–5xx working knowledge)
- [ ] Headers: content negotiation, caching, conditional requests, auth, CORS, forwarding (`X-Forwarded-*`, `Forwarded`)
- [ ] Connection management: keep-alive, pipelining, connection pools
- [ ] HTTP/2: multiplexing, HPACK, server push (deprecated), head-of-line blocking at TCP
- [ ] HTTP/3 / QUIC basics 🟢
- [ ] TLS handshake, ALPN, SNI, session resumption, mTLS
- [ ] Cookies: attributes (`HttpOnly`, `Secure`, `SameSite`), scoping
- [ ] URI design, encoding, query vs path vs header vs body
- [ ] Chunked transfer, streaming, SSE, WebSocket upgrade
- [ ] Proxies, reverse proxies, gateways, CDN behavior
- [ ] DNS basics, TTL, service discovery interplay
- [ ] TCP essentials: 3-way handshake, TIME_WAIT, backlog, Nagle, keepalive, MTU
- [ ] Debugging: curl mastery, `tcpdump`/Wireshark basics, `ss`/`netstat`

## 9.2 REST API Design 🔴
- [ ] Richardson maturity model; HATEOAS reality check
- [ ] Resource modeling, nouns vs verbs, sub-resources, actions that aren't CRUD
- [ ] Idempotency: PUT vs POST, idempotency keys for POST 🔴
- [ ] Pagination: offset/limit vs cursor/keyset; total counts; consistent ordering
- [ ] Filtering, sorting, sparse fieldsets, search endpoints
- [ ] Bulk & batch endpoints; partial success semantics
- [ ] Error format: RFC 9457 `ProblemDetail`, error codes, machine-readable vs human-readable
- [ ] Versioning: URI, header, media-type, query param — trade-offs and org reality 🔴
- [ ] Backward compatibility rules; additive change discipline; deprecation & sunset headers
- [ ] Long-running operations: 202 + status resource, polling, callbacks/webhooks
- [ ] Webhooks: signing, retries, ordering, replay protection, subscriber management
- [ ] Rate limiting & quota headers (`RateLimit-*`, `Retry-After`)
- [ ] Conditional requests: `ETag`/`If-Match` for optimistic concurrency
- [ ] Caching strategy for APIs
- [ ] Content negotiation, media types, vendor media types
- [ ] Security: authn/authz per endpoint, object-level authorization (BOLA/IDOR) 🔴
- [ ] OpenAPI 3.1: writing specs, code-first vs spec-first, generators, linting (Spectral)
- [ ] API documentation & developer experience; Swagger UI, Redoc
- [ ] API governance: style guides, review process, catalog/portal
- [ ] API gateway responsibilities vs service responsibilities
- [ ] BFF (backend-for-frontend) pattern

## 9.3 Other API Styles 🟡
- [ ] gRPC: protobuf IDL, unary/server/client/bidi streaming, deadlines, metadata, interceptors, error model, load balancing, reflection
- [ ] Protobuf schema evolution rules (field numbers, reserved, optional)
- [ ] gRPC vs REST decision criteria
- [ ] GraphQL: schema, resolvers, queries/mutations/subscriptions, N+1 & DataLoader, query complexity/depth limiting, persisted queries, federation
- [ ] GraphQL vs REST trade-offs; when GraphQL is a mistake
- [ ] SOAP/WSDL/XSD legacy, JAX-WS 🟢
- [ ] AsyncAPI for event-driven contracts 🟢
- [ ] JSON:API, HAL, OData 🟢
- [ ] Server-Sent Events vs WebSocket vs long polling
- [ ] File transfer integration: SFTP, S3 handoff, batch file contracts

## 9.4 Serialization & Data Interchange 🔴
- [ ] Jackson: `ObjectMapper` configuration, modules, `@JsonProperty`, `@JsonIgnore`, `@JsonInclude`, `@JsonCreator`, `@JsonView`, polymorphic types (`@JsonTypeInfo`) and their security risk
- [ ] Jackson performance: reuse `ObjectMapper`, streaming API, `ObjectReader`/`ObjectWriter`
- [ ] Custom serializers/deserializers, `JavaTimeModule`, `Jdk8Module`, records support
- [ ] Failing on unknown properties — tolerant reader pattern
- [ ] Gson, JSON-B, DSL-JSON, Moshi 🟢
- [ ] XML: JAXB, StAX/SAX/DOM, XXE prevention 🔴
- [ ] Binary: Protobuf, Avro (schema resolution), Thrift, Kryo, CBOR, MessagePack, SBE 🟡
- [ ] Java native serialization: risks, `serialVersionUID`, `readObject` gadget chains, serialization filters (JEP 290) 🔴
- [ ] Mapping libraries: MapStruct (compile-time), ModelMapper (runtime) — why compile-time wins
- [ ] Lombok: annotations, `@Data` on entities danger, delombok, IDE/build integration debate

---
---

# PART 10 — TESTING & QUALITY ENGINEERING 🔴

## 10.1 Testing Strategy 🔴
- [ ] Test pyramid vs testing trophy vs honeycomb — pick and justify
- [ ] Unit / integration / component / contract / end-to-end / smoke / regression definitions in *your* org
- [ ] Test doubles: dummy, stub, spy, mock, fake — precise differences
- [ ] London (mockist) vs Chicago (classicist) schools
- [ ] What to test and what not to; testing behavior not implementation
- [ ] Coverage: line vs branch vs mutation; coverage targets as a lagging indicator
- [ ] Flaky tests: causes (time, order, concurrency, shared state, network), quarantine policy, fixing culture 🔴
- [ ] Test data management: builders, object mothers, fixtures, factories
- [ ] Deterministic tests: clocks, randoms, UUIDs, time zones
- [ ] Test naming & structure (Given/When/Then, AAA)
- [ ] Test speed as a first-class concern; parallel execution
- [ ] Testing in production: canaries, synthetic monitoring, feature flags, dark launching

## 10.2 JUnit 5 & Core Tools 🔴
- [ ] Jupiter/Vintage/Platform architecture
- [ ] Lifecycle: `@BeforeEach`, `@AfterEach`, `@BeforeAll`, `@AfterAll`, `@TestInstance(PER_CLASS)`
- [ ] `@DisplayName`, `@Nested`, `@Tag`, `@Disabled`, conditional execution annotations
- [ ] Parameterized tests: `@ValueSource`, `@CsvSource`, `@MethodSource`, `@EnumSource`, `@ArgumentsSource`, converters/aggregators
- [ ] Repeated tests, dynamic tests (`@TestFactory`)
- [ ] Extensions model: `BeforeEachCallback`, `ParameterResolver`, `TestExecutionExceptionHandler`, `@ExtendWith`, `@RegisterExtension`
- [ ] Parallel execution config, thread-safety of tests
- [ ] Assertions: `assertAll`, `assertThrows`, `assertTimeout`, custom messages
- [ ] AssertJ fluent assertions, soft assertions, custom assertions, `extracting`, `usingRecursiveComparison` 🔴
- [ ] Hamcrest 🟢
- [ ] Mockito: `mock`, `spy`, `when/thenReturn`, `doThrow`, argument matchers, `ArgumentCaptor`, `verify` modes, `InOrder`, `@Mock`/`@InjectMocks`, strict stubs, mocking static/final (`mockito-inline`), `MockedConstruction` 🔴
- [ ] When mocking is a smell; mocking types you don't own
- [ ] Test containers vs mocks for infrastructure
- [ ] JSON assertions: JSONAssert, JsonPath
- [ ] Awaitility for async assertions
- [ ] Approval/snapshot testing 🟢

## 10.3 Integration & Specialized Testing 🔴
- [ ] Testcontainers: containers per test/class/singleton, reuse, `@ServiceConnection` (Boot 3.1), compose support, custom images 🔴
- [ ] Database integration tests: real DB vs H2 (and why H2 lies)
- [ ] WireMock / MockWebServer for HTTP stubbing; fault injection, delays
- [ ] Contract testing: Pact (consumer-driven), Spring Cloud Contract (producer-driven), broker, can-i-deploy 🟡
- [ ] Spring test slices & context caching optimization
- [ ] `MockMvc` vs `WebTestClient` vs `TestRestTemplate` vs full server
- [ ] Security testing in Spring (`@WithMockUser`, OAuth2 test support)
- [ ] Kafka/Rabbit integration testing
- [ ] ArchUnit: layer rules, naming rules, dependency rules, cycles, freezing violations 🟡
- [ ] Mutation testing with PIT: mutators, strength, CI integration 🟡
- [ ] Property-based testing: jqwik / QuickTheories 🟢
- [ ] Fuzzing (Jazzer) 🟢
- [ ] BDD: Cucumber/JBehave, Gherkin, living documentation, when it pays off 🟢
- [ ] UI/E2E: Selenium, Playwright, Cypress — flakiness management, page objects 🟢
- [ ] Performance testing: JMeter, Gatling, k6, Locust; open vs closed workload models 🟡
- [ ] JMH microbenchmarking: warmup, forks, blackholes, dead-code elimination, `@State`, `@Setup`, profilers 🟡
- [ ] Load/soak/spike/stress test types & what each finds
- [ ] Chaos/fault injection tests
- [ ] Accessibility & compliance testing awareness 🟢

## 10.4 TDD & Quality Practices 🔴
- [ ] Red-green-refactor loop discipline
- [ ] Writing the test first for bug fixes (regression-first)
- [ ] Outside-in vs inside-out TDD
- [ ] Refactoring under green
- [ ] Legacy code: characterization tests, breaking dependencies, seams
- [ ] Code review: what to look for, review size limits, tone, async vs synchronous review 🔴
- [ ] Pair & mob programming; when each is worth it
- [ ] Definition of Done including tests, docs, observability, rollback
- [ ] Static analysis: SonarQube quality gates, SpotBugs, PMD, Checkstyle, ErrorProne, NullAway 🔴
- [ ] Formatting & lint automation: Spotless, EditorConfig, pre-commit hooks
- [ ] Dependency/vulnerability scanning in CI (see Part 14)
- [ ] Quality metrics that matter vs vanity metrics
- [ ] DORA metrics: deployment frequency, lead time, change failure rate, MTTR 🔴

---
---

# PART 11 — BUILD, DEPENDENCIES & RELEASE 🟡

## 11.1 Maven 🔴
- [ ] POM structure, coordinates, packaging types
- [ ] Build lifecycle: clean/default/site; phases & goal binding
- [ ] Dependency scopes: compile, provided, runtime, test, system, import
- [ ] Transitive dependencies, nearest-wins mediation, `dependencyManagement`, BOMs
- [ ] Conflict resolution & `mvn dependency:tree`, `dependency:analyze`
- [ ] Exclusions, optional dependencies
- [ ] Parent POMs, aggregation vs inheritance, multi-module reactor
- [ ] Profiles & activation
- [ ] Properties, versions plugin, `flatten-maven-plugin`
- [ ] Key plugins: compiler, surefire, failsafe, shade, assembly, jar, enforcer, jacoco, spring-boot, versions, release
- [ ] Repositories, mirrors, `settings.xml`, authentication, snapshots vs releases
- [ ] Reproducible builds, `maven.build.timestamp`
- [ ] Maven daemon (mvnd), build caching, parallel builds `-T`

## 11.2 Gradle 🟡
- [ ] Groovy vs Kotlin DSL
- [ ] Task graph, task types, inputs/outputs, up-to-date checks, build cache
- [ ] Configuration avoidance, configuration cache, daemon
- [ ] Dependency configurations: `implementation` vs `api` vs `compileOnly` vs `runtimeOnly`
- [ ] Version catalogs (`libs.versions.toml`), platforms/BOM
- [ ] Multi-project builds, composite builds, convention plugins (`buildSrc`)
- [ ] Custom tasks & plugins
- [ ] Gradle vs Maven — honest trade-offs and migration cost
- [ ] Build scans & profiling builds

## 11.3 Dependency & Supply Chain Management 🔴
- [ ] Semantic versioning & version ranges (why ranges are dangerous)
- [ ] Dependency hygiene: minimizing, auditing, removing unused
- [ ] Diamond dependency problem, shading/relocation
- [ ] Renovate/Dependabot automation policy
- [ ] SBOM: CycloneDX/SPDX generation
- [ ] Vulnerability scanning: OWASP Dependency-Check, Snyk, Trivy, Grype, GitHub Advisory
- [ ] License compliance (GPL/AGPL/Apache/MIT), license scanning
- [ ] Artifact repositories: Nexus, Artifactory, GitHub Packages; proxy/caching
- [ ] Artifact signing, provenance, SLSA levels, Sigstore/cosign
- [ ] Typosquatting & dependency confusion attacks
- [ ] Internal library publishing, versioning & deprecation policy
- [ ] Monorepo vs polyrepo trade-offs; build tooling implications (Bazel, Nx) 🟢

## 11.4 CI/CD & Release Engineering 🔴
- [ ] Pipeline stages: build → test → scan → package → publish → deploy → verify
- [ ] Build reproducibility & hermetic builds
- [ ] Caching strategies for fast pipelines
- [ ] Jenkins (declarative pipelines, shared libraries, agents), GitHub Actions (workflows, matrix, reusable workflows, OIDC to cloud), GitLab CI, CircleCI, Tekton, Argo Workflows
- [ ] Trunk-based development vs GitFlow vs GitHub Flow — release cadence implications 🔴
- [ ] Feature flags: LaunchDarkly/Unleash/FF4J, flag lifecycle & debt, kill switches 🔴
- [ ] Branch protection, required checks, signed commits
- [ ] Versioning strategy: semver, calver, git-describe, auto-versioning
- [ ] Release notes & changelog automation (conventional commits)
- [ ] Deployment strategies: recreate, rolling, blue-green, canary, shadow/dark, A/B 🔴
- [ ] Progressive delivery (Argo Rollouts, Flagger), automated rollback on SLO breach
- [ ] GitOps: Argo CD, Flux; declarative desired state, drift detection
- [ ] Database migrations in the pipeline (ordering with app deploys) 🔴
- [ ] Environment strategy: dev/test/staging/prod, ephemeral preview environments
- [ ] Secrets in CI (never in logs), OIDC federation over long-lived keys
- [ ] Artifact promotion vs rebuild per environment
- [ ] Rollback & forward-fix decision making; backward-compatible deploys
- [ ] Release checklists, change management, freeze windows, approval flows

## 11.5 Version Control Mastery 🟡
- [ ] Git object model: blobs, trees, commits, refs, packfiles
- [ ] `merge` vs `rebase` vs `cherry-pick` vs `revert`; when each is correct
- [ ] Interactive rebase, squashing, fixup commits, autosquash
- [ ] `reflog` recovery, `reset` (soft/mixed/hard), `restore`, `stash`
- [ ] `bisect` for regression hunting 🔴
- [ ] `blame`, `log -S`/`-G` (pickaxe), `log --follow`
- [ ] Submodules vs subtrees
- [ ] Hooks (local & server-side), `core.hooksPath`
- [ ] Large files: Git LFS
- [ ] `worktree` for parallel work
- [ ] Conflict resolution strategies, rerere
- [ ] Commit message conventions; atomic commits
- [ ] PR hygiene: size, description, linked issues, review checklist
- [ ] Rewriting history safely; `filter-repo` for secret removal 🔴

---
---

# PART 12 — CLOUD, CONTAINERS & PLATFORM 🟡

## 12.1 Containers & Docker 🔴
- [ ] Images vs containers; layers, union filesystem, content addressing
- [ ] Dockerfile best practices: layer ordering, multi-stage builds, `.dockerignore`, minimal base images (distroless, alpine + JVM caveats)
- [ ] JVM-specific images: JRE vs JDK, `jlink` custom runtime, layered Spring Boot jars, Jib, Buildpacks
- [ ] Container-aware JVM: cgroup CPU/memory detection, `MaxRAMPercentage`, `ActiveProcessorCount` 🔴
- [ ] Why `-Xmx` + off-heap + metaspace must fit under the container limit (OOMKilled diagnosis) 🔴
- [ ] Non-root users, read-only filesystems, capabilities dropping
- [ ] Image scanning & signing; base image update policy
- [ ] Registry: tagging strategy, immutability, garbage collection
- [ ] Container networking (bridge, host), volumes, bind mounts
- [ ] docker compose for local dev environments
- [ ] Container runtimes: containerd, CRI-O; OCI spec 🟢

## 12.2 Kubernetes 🟡
- [ ] Architecture: API server, etcd, scheduler, controller manager, kubelet, kube-proxy, CNI
- [ ] Core objects: Pod, ReplicaSet, Deployment, StatefulSet, DaemonSet, Job, CronJob
- [ ] Service types: ClusterIP, NodePort, LoadBalancer, ExternalName, headless
- [ ] Ingress & Gateway API; ingress controllers (nginx, Traefik, Istio)
- [ ] ConfigMap & Secret; mounting vs env; secret encryption at rest; external secret operators
- [ ] Probes: liveness, readiness, startup — correct semantics for JVM apps 🔴
- [ ] Resource requests/limits, QoS classes, CPU throttling & its effect on JVM latency 🔴
- [ ] HPA/VPA/KEDA autoscaling; cluster autoscaler
- [ ] PodDisruptionBudget, topology spread, affinity/anti-affinity, taints/tolerations
- [ ] Graceful shutdown: `preStop` hook, `terminationGracePeriodSeconds`, SIGTERM handling in Spring Boot 🔴
- [ ] Rolling update parameters (maxSurge/maxUnavailable), readiness gate correctness
- [ ] Namespaces, ResourceQuota, LimitRange
- [ ] RBAC: roles, bindings, service accounts, least privilege
- [ ] NetworkPolicy
- [ ] Persistent volumes, storage classes, StatefulSet storage
- [ ] Init containers, sidecars (and native sidecar containers)
- [ ] CRDs & operators; when to write one 🟢
- [ ] Helm: charts, values, templating, releases, upgrade/rollback; Kustomize overlays
- [ ] Debugging: `kubectl` mastery, `describe`, `logs -p`, `exec`, ephemeral debug containers, events
- [ ] Common failure modes: CrashLoopBackOff, ImagePullBackOff, OOMKilled, pending pods, DNS issues 🔴
- [ ] Multi-tenancy & cluster isolation strategies
- [ ] Service mesh: Istio/Linkerd — mTLS, traffic shifting, retries, observability; sidecar vs ambient; cost 🟢

## 12.3 Cloud Platforms 🟡
- [ ] Shared responsibility model; regions, AZs, edge locations
- [ ] IAM: users/roles/policies, least privilege, assume-role, workload identity/IRSA
- [ ] Compute: VMs, containers (ECS/EKS/GKE/AKS), serverless (Lambda/Functions/Cloud Run)
- [ ] Java on serverless: cold starts, SnapStart, GraalVM native, provisioned concurrency
- [ ] Networking: VPC, subnets, security groups/NACLs, NAT, private link, load balancers, DNS
- [ ] Storage: object (S3/GCS/Blob), block, file; storage classes & lifecycle
- [ ] Managed databases: RDS/Aurora, Cloud SQL, Cosmos, DynamoDB — failover & maintenance behavior
- [ ] Managed messaging: SQS/SNS/Kinesis/MSK, Pub/Sub, Event Hubs
- [ ] Secrets: Secrets Manager, Parameter Store, Key Vault, KMS envelope encryption
- [ ] Observability services: CloudWatch, X-Ray, Stackdriver, Application Insights
- [ ] Cost management/FinOps: right-sizing, spot/preemptible, reserved/savings plans, tagging, budget alerts, cost per request 🔴
- [ ] Multi-region & DR patterns; data residency
- [ ] Well-Architected Framework pillars
- [ ] Cloud-agnostic vs cloud-native trade-off

## 12.4 Infrastructure as Code & Platform Engineering 🟢
- [ ] Terraform: providers, state (remote, locking), modules, workspaces, plan/apply, drift, `import`
- [ ] Terragrunt, OpenTofu 🟢
- [ ] Pulumi / CDK / CDKTF 🟢
- [ ] Ansible for configuration management 🟢
- [ ] Policy as code: OPA/Rego, Conftest, Kyverno
- [ ] Golden paths & internal developer platforms (Backstage) 🟡
- [ ] Environment provisioning automation; ephemeral environments
- [ ] Immutable infrastructure principle
- [ ] Runbooks & operational documentation as code

---
---

# PART 13 — OBSERVABILITY & PRODUCTION OPERATIONS 🔴

## 13.1 Logging 🔴
- [ ] SLF4J facade; Logback vs Log4j2 vs JUL; bridging (`jul-to-slf4j`, `log4j-over-slf4j`)
- [ ] Log levels & when to use each; level discipline in libraries
- [ ] Parameterized logging (`log.debug("{}", x)`) and guard clauses
- [ ] Structured/JSON logging: `logstash-logback-encoder`, ECS format, key-value pairs 🔴
- [ ] MDC: correlation IDs, trace IDs, tenant, user; propagation across threads/async/reactive 🔴
- [ ] Log correlation with traces (trace_id/span_id injection)
- [ ] What never to log: PII, secrets, tokens, full payloads; masking/redaction 🔴
- [ ] Async appenders, buffer sizing, and log-loss trade-offs
- [ ] Log volume & cost control; sampling; dynamic level changes (Actuator `/loggers`)
- [ ] Log aggregation: ELK/OpenSearch, Loki, Splunk, Datadog; index/retention strategy
- [ ] Log4Shell lessons: JNDI lookups, patching discipline 🔴
- [ ] Audit logging vs application logging (immutability, retention, compliance)

## 13.2 Metrics 🔴
- [ ] Metric types: counter, gauge, timer/histogram, summary, distribution summary
- [ ] Micrometer: `MeterRegistry`, tags/dimensions, naming conventions, base units
- [ ] Cardinality explosion — the #1 metrics mistake 🔴
- [ ] Percentiles: client-side vs server-side computation, histogram buckets, why averaging percentiles is wrong 🔴
- [ ] Spring Boot Actuator metrics: HTTP, JVM, GC, threads, datasource, cache, Kafka
- [ ] Custom business metrics; instrumenting what matters
- [ ] Prometheus: pull model, exposition format, scrape config, service discovery, PromQL (rate, histogram_quantile, aggregation, joins), recording rules, alerting rules
- [ ] Long-term storage: Thanos, Cortex/Mimir, VictoriaMetrics 🟢
- [ ] Grafana dashboards: RED (rate, errors, duration), USE (utilization, saturation, errors), four golden signals 🔴
- [ ] Dashboard design: what a good on-call dashboard shows in 10 seconds
- [ ] Alerting: symptom-based vs cause-based, alert fatigue, runbook links, severity levels, paging policy 🔴
- [ ] SLI definition, SLO targets, error budgets, burn-rate alerts 🔴

## 13.3 Tracing & Profiling 🟡
- [ ] Distributed tracing concepts: trace, span, parent/child, baggage, context propagation
- [ ] W3C Trace Context, B3 headers
- [ ] OpenTelemetry: API vs SDK, auto-instrumentation java agent, manual spans, resource attributes, exporters (OTLP), collector pipelines 🔴
- [ ] Micrometer Observation API & Micrometer Tracing (Boot 3)
- [ ] Sampling strategies: head-based, tail-based, adaptive; cost vs fidelity
- [ ] Jaeger/Tempo/Zipkin/Datadog/Honeycomb backends
- [ ] Tracing async & reactive code; context loss debugging
- [ ] Span attributes & semantic conventions; DB/HTTP/messaging conventions
- [ ] Continuous profiling in production (Pyroscope, Datadog Profiler, JFR streaming) 🟡
- [ ] Correlating logs + metrics + traces + profiles (the four pillars)
- [ ] eBPF-based observability awareness 🟢

## 13.4 Production Operations & Incident Management 🔴
- [ ] On-call: rotations, escalation, handoff quality, sustainable load
- [ ] Incident lifecycle: detect → triage → mitigate → resolve → learn
- [ ] Incident command: roles (IC, comms, ops), severity classification, status updates 🔴
- [ ] Mitigation before root cause: rollback, feature flag off, scale up, failover, traffic shift
- [ ] Blameless postmortems: timeline, contributing factors, action items with owners 🔴
- [ ] MTTD/MTTA/MTTR; measuring reliability improvement
- [ ] Runbooks & playbooks; automation of repetitive remediation
- [ ] Change management & correlating incidents with deploys
- [ ] Capacity planning & load forecasting
- [ ] Toil reduction, error budget policy, SRE practices
- [ ] Production readiness review checklist (a tech-lead deliverable) 🔴
- [ ] Common JVM production incidents runbook: OOM, GC storm, thread pool exhaustion, connection pool exhaustion, deadlock, memory leak, CPU spike, disk full, downstream latency, cascading failure 🔴
- [ ] Debugging in production safely: JFR, heap dump impact, thread dumps, dynamic log levels, no debuggers in prod
- [ ] Traffic replay & shadow testing for verification

---
---

# PART 14 — SECURITY & COMPLIANCE 🔴

## 14.1 Application Security Fundamentals 🔴
- [ ] CIA triad, defense in depth, least privilege, fail securely, complete mediation
- [ ] Threat modeling: STRIDE, attack trees, data flow diagrams, trust boundaries 🔴
- [ ] OWASP Top 10 (current): broken access control, crypto failures, injection, insecure design, security misconfiguration, vulnerable components, auth failures, integrity failures, logging failures, SSRF 🔴
- [ ] OWASP API Security Top 10 (BOLA, broken auth, property-level authz, resource consumption, function-level authz, business flow abuse, SSRF, misconfig, inventory, unsafe API consumption) 🔴
- [ ] OWASP ASVS as a requirements checklist
- [ ] CWE/CVE/CVSS, exploitability vs severity, patch prioritization
- [ ] Secure SDLC, security champions, shift-left

## 14.2 Java-Specific Vulnerabilities 🔴
- [ ] SQL injection & ORM injection (native queries, dynamic JPQL)
- [ ] Insecure deserialization: Java native serialization gadget chains, `ObjectInputFilter`, Jackson polymorphic typing RCE 🔴
- [ ] XXE in XML parsers — hardening `DocumentBuilderFactory`/`SAXParser`/`XMLInputFactory` 🔴
- [ ] SSRF: URL fetching, allowlists, metadata endpoint protection
- [ ] Path traversal & zip slip in file handling
- [ ] Command injection via `Runtime.exec`/`ProcessBuilder`
- [ ] Expression language injection (SpEL, OGNL, MVEL) 🔴
- [ ] Log injection & Log4Shell-class JNDI issues
- [ ] Unsafe reflection & classloading
- [ ] Race conditions/TOCTOU in file & auth checks
- [ ] Sensitive data in memory, heap dumps, and logs
- [ ] Weak randomness: `Random` vs `SecureRandom`, seeding, `/dev/urandom` blocking
- [ ] Timing attacks & constant-time comparison (`MessageDigest.isEqual`)
- [ ] Regex ReDoS
- [ ] XSS in server-rendered templates; output encoding, CSP
- [ ] CSRF in stateful apps
- [ ] Mass assignment / over-posting (`@JsonIgnore`, explicit DTOs)
- [ ] Open redirect
- [ ] Security Manager removal — what replaces it

## 14.3 Cryptography & Key Management 🔴
- [ ] Symmetric vs asymmetric; AES-GCM, ChaCha20-Poly1305; never ECB 🔴
- [ ] IV/nonce handling, authenticated encryption, padding oracle awareness
- [ ] Hashing vs encryption vs encoding (the classic confusion)
- [ ] Password hashing: bcrypt/scrypt/Argon2, work factors, salting, peppering 🔴
- [ ] HMAC, digital signatures, RSA vs ECDSA vs EdDSA
- [ ] Key derivation: PBKDF2, HKDF
- [ ] JCA/JCE architecture, providers, BouncyCastle
- [ ] Keystores: JKS/PKCS12, truststores, `keytool`
- [ ] TLS configuration: protocol versions, cipher suites, certificate validation, hostname verification (never disable) 🔴
- [ ] Certificate lifecycle: CSR, CA, chain, expiry monitoring, rotation, ACME/Let's Encrypt
- [ ] mTLS setup and troubleshooting
- [ ] Secrets management: Vault (dynamic secrets, transit, leases), cloud secret managers, sealed secrets 🔴
- [ ] Secret rotation without downtime
- [ ] Encryption at rest & in transit; field-level encryption; tokenization
- [ ] Crypto-agility & post-quantum awareness 🟢

## 14.4 Identity, AuthN & AuthZ 🔴
- [ ] Authentication factors, MFA, passwordless, WebAuthn/passkeys 🟢
- [ ] Session-based vs token-based auth; where to store tokens (and why not localStorage)
- [ ] OAuth 2.0 / 2.1: roles, grant types (auth code + PKCE, client credentials, device, refresh), deprecated grants (implicit, password) 🔴
- [ ] OpenID Connect: ID token, userinfo, discovery, scopes/claims
- [ ] JWT: structure, signing (HS/RS/ES), validation checklist (`alg` confusion, `kid`, issuer, audience, expiry, clock skew), revocation problem 🔴
- [ ] Opaque tokens & introspection; token exchange
- [ ] SAML 2.0 basics 🟢
- [ ] API keys, HMAC request signing
- [ ] Service-to-service auth: mTLS, SPIFFE/SPIRE, workload identity
- [ ] Authorization models: RBAC, ABAC, ReBAC (Zanzibar/OpenFGA), policy engines (OPA, Cedar) 🟡
- [ ] Multi-tenant authorization & tenant isolation enforcement 🔴
- [ ] Object-level authorization checks everywhere (IDOR prevention)
- [ ] Privilege escalation paths & admin functionality protection
- [ ] Identity providers: Keycloak, Auth0, Okta, Cognito, Entra ID

## 14.5 Security Operations & Compliance 🟡
- [ ] SAST, DAST, IAST, SCA — where each fits in the pipeline
- [ ] Secret scanning (gitleaks, trufflehog), pre-commit prevention, rotation after exposure 🔴
- [ ] Container & image scanning; base image patching cadence
- [ ] Penetration testing & bug bounty handling
- [ ] Security headers & TLS config verification
- [ ] Rate limiting & bot/abuse protection, WAF
- [ ] DDoS mitigation basics
- [ ] Audit logging & tamper evidence
- [ ] Incident response for security events; disclosure process
- [ ] Data classification & handling; PII inventory
- [ ] GDPR: lawful basis, data subject rights, right to erasure vs event sourcing, DPIA, cross-border transfer 🟡
- [ ] PCI-DSS scope reduction, tokenization 🟢
- [ ] HIPAA / SOC 2 / ISO 27001 — what engineering must produce 🟢
- [ ] Privacy by design, data minimization, retention enforcement
- [ ] Vendor/third-party security review

---
---

# PART 15 — PERFORMANCE ENGINEERING 🟡

## 15.1 Performance Mindset 🔴
- [ ] Latency vs throughput vs utilization; they trade off
- [ ] Percentiles p50/p90/p99/p99.9; why averages lie; coordinated omission 🔴
- [ ] Little's Law: `L = λW` and how to use it for pool sizing 🔴
- [ ] Amdahl's law & Universal Scalability Law (contention + coherence) 🟡
- [ ] Queueing theory basics: utilization vs latency knee (>70% is dangerous)
- [ ] Performance requirements as SLOs, not vibes
- [ ] "Measure, don't guess" — profile before optimizing
- [ ] Premature optimization vs architectural performance decisions
- [ ] The performance testing environment problem (prod-like data & traffic)

## 15.2 Measuring & Profiling 🔴
- [ ] Building a repeatable benchmark; warmup, steady state, variance
- [ ] JMH pitfalls: dead code elimination, constant folding, loop optimization, blackholes, `@State` scope
- [ ] Profiling types: sampling vs instrumenting; safepoint bias
- [ ] async-profiler modes (cpu, alloc, lock, wall) & flame graph reading 🔴
- [ ] JFR event streaming & custom events
- [ ] Allocation profiling → reducing garbage
- [ ] Lock contention profiling
- [ ] Heap analysis with MAT: dominator tree, retained size, leak suspects, OQL
- [ ] Off-heap & native memory analysis (NMT, jemalloc profiling)
- [ ] OS-level tools: `top`, `htop`, `vmstat`, `iostat`, `pidstat`, `sar`, `ss`, `perf`, `strace`
- [ ] Interpreting CPU steal, iowait, context switches, run queue
- [ ] Network latency measurement, `tcpdump` analysis

## 15.3 JVM & Code-Level Optimization 🟡
- [ ] Reducing allocation: object reuse, primitive collections, avoiding boxing, avoiding stream overhead in hot paths
- [ ] String optimization: builders, `intern` caution, avoiding regex in hot loops
- [ ] Collection choice & pre-sizing
- [ ] Avoiding megamorphic call sites; keeping hot methods inlinable
- [ ] Branch prediction & data-oriented layout awareness 🟢
- [ ] Cache locality, false sharing, padding 🟢
- [ ] Avoiding excessive logging/serialization in hot paths
- [ ] Lazy initialization vs eager cost
- [ ] Batch processing & chunking; reducing round trips (chatty vs chunky)
- [ ] Async & parallelism where it actually helps
- [ ] Zero-copy IO, direct buffers, `transferTo`
- [ ] GC tuning as a last resort after allocation reduction
- [ ] Startup time optimization: CDS/AppCDS, lazy beans, native image, Leyden 🟡

## 15.4 System-Level Performance 🔴
- [ ] Finding the bottleneck: app vs DB vs network vs downstream 🔴
- [ ] Database performance as the usual culprit (N+1, missing index, lock waits, connection pool)
- [ ] Connection pool sizing math (and why bigger is usually worse)
- [ ] Thread pool sizing & queueing behavior
- [ ] Timeouts & their effect on tail latency; timeout budgets across hops
- [ ] Caching as a performance lever (see Part 5)
- [ ] Payload size, compression, pagination
- [ ] Chattiness reduction: batching, GraphQL/BFF, denormalized read models
- [ ] Load testing methodology: baseline, ramp, soak, spike; realistic data
- [ ] Capacity model: requests → CPU/memory/IO → instances → cost
- [ ] Performance regression detection in CI
- [ ] Real user monitoring vs synthetic

---
---

# PART 16 — ENGINEERING PRACTICES & CRAFT 🟡

## 16.1 Algorithms & Data Structures (Interview + Judgment) 🔴
- [ ] Big-O/Θ/Ω, amortized analysis, space complexity
- [ ] Arrays, strings, two pointers, sliding window, prefix sums
- [ ] Hash tables: collision handling, load factor, when hashing degrades
- [ ] Linked lists, stacks, queues, deques, monotonic stack/queue
- [ ] Trees: BST, balanced (AVL, red-black), traversals, LCA, tries
- [ ] Heaps/priority queues, top-K problems
- [ ] Graphs: representation, BFS/DFS, topological sort, Dijkstra, union-find, cycle detection
- [ ] Sorting: comparison sorts, stability, TimSort, counting/radix, external sort
- [ ] Binary search & its variants (on answer, on rotated arrays)
- [ ] Recursion, backtracking, memoization
- [ ] Dynamic programming: 1D/2D, knapsack, LCS/LIS, interval DP
- [ ] Greedy & interval scheduling
- [ ] Bit manipulation tricks
- [ ] Probabilistic structures: Bloom filter, Count-Min sketch, HyperLogLog 🟡
- [ ] Consistent hashing, skip lists, LSM trees vs B-trees 🟡
- [ ] Rate limiter algorithms, LRU/LFU implementation
- [ ] Concurrency-flavored DSA problems (thread-safe LRU, bounded buffer, printer scheduler)

## 16.2 Documentation & Communication Artifacts 🔴
- [ ] README that actually onboards someone
- [ ] ADRs, RFCs / design docs: structure, audience, review process 🔴
- [ ] Technical specs: problem, goals, non-goals, options, decision, risks, rollout, metrics
- [ ] Diagrams-as-code (Mermaid, PlantUML, Structurizr); keeping diagrams current
- [ ] API docs & changelogs
- [ ] Runbooks, on-call docs, postmortems
- [ ] Onboarding docs & knowledge management; docs rot prevention
- [ ] Writing for executives vs writing for engineers 🔴

## 16.3 Developer Experience & Tooling 🟢
- [ ] IDE mastery (IntelliJ): refactorings, debugger (conditional breakpoints, evaluate expression, stream debugger, drop frame), profiler integration, live templates, structural search
- [ ] Debugging methodology: reproduce → isolate → hypothesize → test → fix → prevent 🔴
- [ ] Remote/attach debugging & its limits
- [ ] Local environment: docker compose, Testcontainers dev services, Tilt/Skaffold
- [ ] Shell productivity: grep/ripgrep, jq, awk, sed, find, xargs, http tooling
- [ ] Build speed & feedback loop as a team-productivity lever
- [ ] AI-assisted development: code assistants, review assistants, prompt hygiene, verification discipline, what not to paste 🟡

---
---

# PART 17 — DATA, ANALYTICS & AI ADJACENCY 🟢

## 17.1 Data Engineering Basics 🟡
- [ ] OLTP vs OLAP; row vs columnar storage
- [ ] ETL vs ELT; batch vs streaming
- [ ] Data warehouse vs data lake vs lakehouse
- [ ] File formats: Parquet, ORC, Avro; partitioning & compaction
- [ ] Table formats: Iceberg, Delta Lake, Hudi 🟢
- [ ] Apache Spark basics: RDD/DataFrame, transformations vs actions, shuffles, partitioning, broadcast joins 🟢
- [ ] Apache Flink basics: event time, watermarks, state, checkpointing 🟢
- [ ] Orchestration: Airflow, Dagster, Temporal 🟡
- [ ] Data quality, lineage, contracts, catalogs
- [ ] Idempotent, replayable pipelines & late/duplicate data handling
- [ ] Batch processing in Java: Spring Batch, chunking, restartability, partitioning 🟡

## 17.2 AI/LLM Integration for Java Teams 🟡
- [ ] LLM basics: tokens, context window, temperature, embeddings
- [ ] Prompt engineering & structured output; JSON schema/function calling
- [ ] RAG pipeline: chunking, embedding, vector store, retrieval, reranking, evaluation
- [ ] Vector databases & similarity search (HNSW, cosine/dot/L2)
- [ ] Java libraries: Spring AI, LangChain4j, Anthropic/OpenAI SDKs
- [ ] Agents & tool use; MCP (Model Context Protocol) awareness
- [ ] Streaming responses, timeouts, retries, cost control, caching
- [ ] Evaluation: golden sets, LLM-as-judge, regression tests for prompts
- [ ] Guardrails: prompt injection, output validation, PII redaction, allowlisting tools 🔴
- [ ] Observability & cost tracking for AI features
- [ ] When AI is the wrong solution (deterministic rules, compliance-critical paths)

---
---

# PART 18 — JVM LANGUAGES & ADJACENT STACKS 🟢

- [ ] Kotlin: null safety, data classes, extension functions, coroutines & structured concurrency, sealed classes, Java interop, Kotlin+Spring 🟡
- [ ] Kotlin vs Java decision for a team (hiring, tooling, build time, migration path)
- [ ] Scala basics & where it survives (Spark, Akka) 🟢
- [ ] Groovy (Gradle, Spock testing) 🟢
- [ ] Clojure awareness 🟢
- [ ] GraalVM: native image, reachability metadata, reflection config, build time vs peak throughput, Truffle/polyglot 🟡
- [ ] Project Valhalla (value objects, primitive classes) — why it matters 🟢
- [ ] Project Panama (FFM API) — replacing JNI 🟢
- [ ] Project Leyden (AOT, startup) 🟢
- [ ] Project Babylon 🟢
- [ ] JNI & native interop basics 🟢
- [ ] WASM on/off the JVM awareness 🟢
- [ ] Frontend literacy for a backend lead: SPA basics, bundling, CORS/auth flows, BFF, SSR vs CSR, what to demand in an API contract 🟡

---
---

# PART 19 — TECHNICAL LEADERSHIP 🔴

## 19.1 The Tech Lead Role 🔴
- [ ] Tech lead vs staff engineer vs architect vs engineering manager — scope and accountability
- [ ] Individual output → team output → org output (the leverage shift)
- [ ] Time allocation: coding vs design vs review vs unblocking vs planning
- [ ] Deciding what to delegate vs do yourself
- [ ] Setting technical direction & getting buy-in without authority
- [ ] Being the "glue" work owner and making it visible
- [ ] Managing up: expectation setting, escalation, saying no with alternatives 🔴
- [ ] Career ladders & how senior/staff levels are actually evaluated

## 19.2 Team Leadership & People 🔴
- [ ] 1:1s: structure, listening, career conversations, feedback loops
- [ ] Mentoring & coaching: situational leadership, growing juniors vs seniors
- [ ] Feedback: SBI model, radical candor, timely & specific, receiving feedback well
- [ ] Delegation with clear ownership and support level
- [ ] Psychological safety & how a lead creates it
- [ ] Handling underperformance (with the manager, not around them)
- [ ] Conflict resolution between engineers; disagreements about architecture
- [ ] Onboarding new team members; ramp-up plans and buddy systems
- [ ] Distributed/remote/async team practices, timezone fairness
- [ ] Team health signals: churn, morale, bus factor, WIP, interrupt load
- [ ] Recognition & promotion advocacy; writing effective promo/impact narratives

## 19.3 Planning, Delivery & Process 🔴
- [ ] Agile in practice: Scrum ceremonies, Kanban flow, WIP limits, when process is theater
- [ ] Estimation: story points vs time, relative sizing, reference classes, planning poker
- [ ] Why estimates are wrong & how to communicate uncertainty (ranges, confidence, cone of uncertainty) 🔴
- [ ] Breaking down epics → stories → tasks; vertical slicing
- [ ] Roadmapping, quarterly planning, dependency management across teams
- [ ] Prioritization frameworks: RICE, MoSCoW, WSJF, cost of delay, opportunity cost
- [ ] Scope negotiation & trade-off conversations with product
- [ ] Risk management: identify, assess, mitigate, contingency; risk register
- [ ] Handling scope creep and mid-sprint changes
- [ ] Tracking progress honestly; leading vs lagging indicators
- [ ] Managing technical debt as a portfolio (allocation %, debt register, business framing) 🔴
- [ ] Incident-driven vs roadmap-driven work balance
- [ ] Working with QA, SRE, security, data, design, and support functions
- [ ] Vendor & third-party management

## 19.4 Decision-Making & Influence 🔴
- [ ] Reversible (two-way door) vs irreversible (one-way door) decisions 🔴
- [ ] Decision frameworks: RAPID/DACI, disagree-and-commit
- [ ] Making decisions with incomplete information; time-boxing analysis
- [ ] Spikes & prototypes to buy information
- [ ] Build vs buy vs open source: TCO, lock-in, ops burden, differentiation
- [ ] Technology selection criteria & avoiding resume-driven development 🔴
- [ ] Writing persuasive design docs; pre-reads; running a design review
- [ ] Influencing without authority; stakeholder mapping
- [ ] Communicating trade-offs to non-technical stakeholders (business language: cost, risk, time-to-market) 🔴
- [ ] Handling pushback & escalations; when to hold the line on quality
- [ ] Cross-team architecture alignment; architecture guilds/review boards

## 19.5 Hiring & Interviewing 🟡
- [ ] Defining a role & scorecard; competency framework
- [ ] Structured interviewing, question design, calibration
- [ ] Conducting coding, system design, and behavioral interviews as the interviewer
- [ ] Bias awareness & fair evaluation
- [ ] Take-home vs live coding trade-offs
- [ ] Debrief facilitation & hiring decisions
- [ ] Candidate experience & employer branding
- [ ] Team composition & seniority balance

## 19.6 Business & Product Acumen 🟡
- [ ] Understanding the business model & how your service makes/saves money
- [ ] Unit economics; cost per transaction/tenant; FinOps ownership 🔴
- [ ] Metrics literacy: activation, retention, conversion, churn
- [ ] Working with product managers; discovery vs delivery
- [ ] Customer empathy: support tickets, user research, dogfooding
- [ ] Compliance/regulatory awareness for your domain
- [ ] Communicating engineering value to leadership

---
---

# PART 20 — INTERVIEW PREPARATION PLAYBOOK 🔴

## 20.1 Rounds You Will Face
- [ ] Recruiter/HR screen — comp, motivation, notice period narrative
- [ ] Coding/DSA round (medium LeetCode level, 2 problems / 45 min)
- [ ] Java deep-dive / core Java round
- [ ] Low-level design / OOD round
- [ ] High-level system design round
- [ ] Machine coding / take-home (2–3 hours, working code)
- [ ] Database & SQL round
- [ ] Spring/framework-specific round
- [ ] Debugging/troubleshooting round (given a prod scenario)
- [ ] Code review round (critique a PR)
- [ ] Behavioral/leadership round
- [ ] Hiring manager round (scope, impact, ways of working)
- [ ] Bar raiser / cross-functional round
- [ ] Architecture presentation of a past project 🔴

## 20.2 High-Frequency Java Interview Topics 🔴
- [ ] `HashMap` internals end-to-end (asked in ~80% of Java interviews)
- [ ] `ConcurrentHashMap` vs `Hashtable` vs `synchronizedMap`
- [ ] `equals`/`hashCode` contract & consequences
- [ ] String immutability & string pool
- [ ] `volatile` vs `synchronized` vs `Atomic*`
- [ ] Thread pool internals & sizing
- [ ] `CompletableFuture` composition
- [ ] Virtual threads: what changes, what doesn't 🔴
- [ ] GC types & choosing one; how to diagnose a long pause
- [ ] Memory leak diagnosis walkthrough
- [ ] `@Transactional` propagation & why it didn't roll back
- [ ] Spring bean lifecycle & proxy/self-invocation
- [ ] N+1 problem & fixes
- [ ] Isolation levels & anomalies
- [ ] Kafka consumer rebalance & exactly-once
- [ ] Idempotency design
- [ ] Circuit breaker & retry design
- [ ] Design patterns with real code examples you've written
- [ ] Java 8 → 21 feature evolution
- [ ] Stream API tricky outputs (lazy evaluation, short-circuit, ordering)

## 20.3 Behavioral Preparation (STAR) 🔴
Prepare **written** 2–3 minute stories with metrics for each:
- [ ] Led a project end-to-end (scope, team, outcome, metrics)
- [ ] Made a difficult architectural decision & its trade-offs
- [ ] Disagreed with a manager/peer and how it resolved
- [ ] Handled a production incident (your specific actions)
- [ ] Mentored someone to a measurable improvement
- [ ] Dealt with an underperforming teammate
- [ ] Missed a deadline / project failed — what you learned
- [ ] Pushed back on scope or timeline
- [ ] Improved team process/velocity/quality with numbers
- [ ] Paid down significant technical debt & justified it to the business
- [ ] Introduced a new technology & managed the risk
- [ ] Influenced across teams without authority
- [ ] Handled ambiguity with no clear requirements
- [ ] Received hard feedback and changed
- [ ] Made a decision that turned out wrong & how you recovered
- [ ] Balanced quality vs speed under pressure
- [ ] Scaled a system for growth (before/after numbers)
- [ ] Reduced cost or improved efficiency (with $ or %)

## 20.4 Your Own Project Narrative 🔴
- [ ] One-page architecture diagram of your current/most impressive system
- [ ] Scale numbers memorized: QPS, data volume, latency SLOs, team size, uptime
- [ ] Key decisions and the alternatives you rejected (with reasons)
- [ ] What you'd redesign today and why
- [ ] Your specific contribution vs the team's
- [ ] Hardest bug you debugged, end to end
- [ ] Biggest performance win with before/after metrics
- [ ] Prepared answers for "why are you leaving" and "what do you want next"

## 20.5 Interview Execution Skills 🟡
- [ ] Clarifying requirements before coding/designing
- [ ] Thinking aloud & structured communication
- [ ] Whiteboard/diagram discipline in remote interviews
- [ ] Time management within a round
- [ ] Recovering from a wrong turn gracefully
- [ ] Asking good questions of the interviewer
- [ ] Negotiation: comp bands, competing offers, level negotiation
- [ ] Mock interviews & feedback loop

---
---

# APPENDIX A — SUGGESTED SEQUENCING

A senior lead with 10 YOE has most of this partially; the value is in closing gaps, not linear reading. Suggested order if starting cold:

| Phase | Focus | Parts | Rationale |
|---|---|---|---|
| **1. Foundation audit** | Core Java, JVM, Concurrency | 1, 2, 3 | Everything else assumes these; interview blockers live here |
| **2. Design fluency** | Patterns, DDD, Clean Code | 4 | Required for LLD rounds and daily review quality |
| **3. Stack depth** | Spring, JPA, SQL | 6, 7 | Where production bugs actually come from |
| **4. Distributed thinking** | Architecture, Messaging, APIs | 5, 8, 9 | Required for HLD rounds and staff-level scope |
| **5. Production ownership** | Testing, Observability, Security, Perf | 10, 13, 14, 15 | Separates senior from mid conclusively |
| **6. Platform** | Build/Release, Cloud/K8s | 11, 12 | Necessary literacy, rarely the deciding factor |
| **7. Leadership** | Leadership, Interview prep | 16, 19, 20 | Compounding; start Part 19 stories early, they take weeks to refine |
| **8. Breadth** | Data/AI, JVM languages | 17, 18 | Differentiators, do last |

**Parallel track from day 1:** write one STAR story per week (Part 20.3) — they need iteration, not cramming.

---

# APPENDIX B — SELF-ASSESSMENT QUESTIONS PER PART

Use these as a gate before marking a Part complete. If you can't answer in 3 minutes without notes, the part isn't done.

- **Part 1:** Explain type erasure and what breaks because of it. Why does `HashMap` treeify?
- **Part 2:** Walk through diagnosing a 4-second GC pause in production, step by step, naming tools.
- **Part 3:** Explain happens-before. Now explain why double-checked locking without `volatile` is broken.
- **Part 4:** Take a fat service class and describe the refactor sequence, naming each refactoring.
- **Part 5:** Design an idempotent payment API across two services. Where does the outbox go, and why not 2PC?
- **Part 6:** Why did `@Transactional` not roll back? Give three distinct causes.
- **Part 7:** A query got slow after a deploy. Give your diagnostic sequence from app to index.
- **Part 8:** Your consumer lag is climbing and rebalances are frequent. Name five causes and their fixes.
- **Part 9:** Design API versioning for a breaking change with 40 external consumers.
- **Part 10:** Your test suite takes 40 minutes and is 8% flaky. Give a concrete 90-day plan.
- **Part 11:** Design a pipeline that deploys a schema change and app change with zero downtime and safe rollback.
- **Part 12:** Your pod is OOMKilled but heap usage looks fine. Explain what's happening.
- **Part 13:** Define SLIs and SLOs for a checkout service and the alerts you'd page on.
- **Part 14:** Threat model a file-upload feature. List controls in order of importance.
- **Part 15:** p99 latency is 10× p50 with low CPU. Give your hypothesis list, ordered.
- **Part 16:** Explain a design decision you made to a CFO in 90 seconds.
- **Part 17:** When would you refuse to use an LLM for a feature?
- **Part 18:** Make the case for and against adopting Kotlin on your team.
- **Part 19:** Two senior engineers disagree on architecture and the sprint is blocked. What do you do today?
- **Part 20:** Deliver your architecture story in 5 minutes with numbers, unprompted.

---

# APPENDIX C — CORE REFERENCES

### Books — Java & JVM
- [ ] *Effective Java* — Joshua Bloch (3rd ed.) — **non-negotiable**
- [ ] *Java Concurrency in Practice* — Goetz et al. — still the JMM canon
- [ ] *Optimizing Java* — Evans, Gough, Newland
- [ ] *Java Performance* — Scott Oaks (2nd ed.)
- [ ] *The Well-Grounded Java Developer* (2nd ed.) — modern Java
- [ ] *Modern Java in Action* — streams & functional
- [ ] *Inside the Java Virtual Machine* / JVM Spec (for depth)
- [ ] *Java Persistence with Spring Data and Hibernate* — Catalin Tudose
- [ ] *High-Performance Java Persistence* — Vlad Mihalcea — **best JPA/SQL perf resource**

### Books — Design & Architecture
- [ ] *Designing Data-Intensive Applications* — Kleppmann — **non-negotiable**
- [ ] *Domain-Driven Design* — Evans; *Implementing DDD* — Vernon; *Learning DDD* — Khononov
- [ ] *Fundamentals of Software Architecture* & *Software Architecture: The Hard Parts* — Richards & Ford
- [ ] *Building Microservices* (2nd ed.) — Sam Newman
- [ ] *Monolith to Microservices* — Sam Newman
- [ ] *Clean Architecture* — Martin; *Clean Code* — Martin (read critically)
- [ ] *Refactoring* (2nd ed.) — Fowler; *Patterns of Enterprise Application Architecture* — Fowler
- [ ] *Design Patterns* — GoF; *Head First Design Patterns* (approachable)
- [ ] *Working Effectively with Legacy Code* — Feathers
- [ ] *Enterprise Integration Patterns* — Hohpe & Woolf
- [ ] *Release It!* (2nd ed.) — Nygard — **stability patterns canon**
- [ ] *Understanding Distributed Systems* — Vitillo

### Books — Practice, Ops & Leadership
- [ ] *Site Reliability Engineering* + *The SRE Workbook* — Google
- [ ] *Accelerate* — Forsgren, Humble, Kim
- [ ] *Continuous Delivery* — Humble & Farley
- [ ] *Observability Engineering* — Majors et al.
- [ ] *The Manager's Path* — Camille Fournier — **the tech lead chapter**
- [ ] *Staff Engineer* — Will Larson; *The Staff Engineer's Path* — Tanya Reilly
- [ ] *An Elegant Puzzle* — Will Larson
- [ ] *Team Topologies* — Skelton & Pais
- [ ] *Crucial Conversations*; *Thinking in Systems* — Meadows
- [ ] *Designing Data-Intensive Applications* revisited for system design interviews
- [ ] *System Design Interview* Vol 1 & 2 — Alex Xu

### Primary Sources (prefer over blogs)
- [ ] JLS & JVM Specification
- [ ] JEP index (openjdk.org/jeps) — read the JEP for every feature you claim to know
- [ ] Spring Framework & Spring Boot reference docs
- [ ] Hibernate User Guide
- [ ] Kafka documentation & KIPs
- [ ] Kubernetes docs & CNCF project docs
- [ ] OWASP Cheat Sheet Series, ASVS, Top 10
- [ ] RFCs: 7231/9110 (HTTP), 6749/9700 (OAuth), 7519 (JWT), 9457 (Problem Details)

### Ongoing
- [ ] Inside Java / Java newsletters (JEP Café, Inside Java Newscast)
- [ ] Vlad Mihalcea, Baeldung (verify, don't trust blindly), Thorben Janssen
- [ ] InfoQ architecture trends report (annual)
- [ ] Conference talks: Devoxx, JVMLS, GOTO, QCon, SpringOne
- [ ] Read one real open-source Java codebase per quarter (Spring, Hibernate, Kafka, Caffeine, Netty)

---

# APPENDIX D — PROGRESS LOG

| Date | Part / Section | Topics Covered | Depth Reached | Notes / Gaps Found |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

---

*Generated as a living document — edit freely, add micro-topics you hit in real work, and delete what your target roles genuinely don't require.*



