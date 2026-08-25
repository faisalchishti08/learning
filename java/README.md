# Java Complete Tutorial

One-stop Java revision resource. 52 topic files covering every Java concept from basics to Java 21, with code examples, dry runs, visual diagrams, and pitfall callouts.

**Baseline:** Java 21 (current LTS). Features tagged `[Java X+]` where introduced.

---

## Core Java

| File | Topics |
|------|--------|
| [01-basics.md](01-basics.md) | Primitives, reference types, literals, type casting, autoboxing, operators, precedence |
| [02-control-flow.md](02-control-flow.md) | if/else, switch (classic + enhanced), for/while/do-while, break/continue/labeled |
| [03-strings.md](03-strings.md) | Immutability, String pool/interning, String vs StringBuilder vs StringBuffer, all methods, text blocks [Java 15+] |
| [04-arrays.md](04-arrays.md) | 1D/2D/jagged arrays, Arrays utility, varargs, covariance pitfall |
| [09-exceptions.md](09-exceptions.md) | Exception hierarchy, checked/unchecked, try-with-resources [Java 7+], multi-catch, custom exceptions |

---

## Object-Oriented Programming

| File | Topics |
|------|--------|
| [05-oop-fundamentals.md](05-oop-fundamentals.md) | Class anatomy, object creation, constructors, this keyword, static members, access modifiers |
| [06-oop-inheritance.md](06-oop-inheritance.md) | extends, super, overriding vs overloading, final, instanceof pattern matching [Java 16+], Object methods |
| [07-abstract-interfaces.md](07-abstract-interfaces.md) | Abstract classes, interfaces pre/post Java 8, default/static/private methods, diamond problem |
| [08-nested-classes.md](08-nested-classes.md) | Static nested, inner, local, anonymous classes |
| [10-generics.md](10-generics.md) | Generic classes/methods, bounds, wildcards, PECS, type erasure, raw types |

---

## Collections (Deep Dive)

| File | Topics |
|------|--------|
| [11-collections.md](11-collections.md) | **DEEP DIVE** — Full hierarchy, ArrayList (resize dry run), LinkedList, HashSet, TreeSet, HashMap (bucket diagram + put dry run), LinkedHashMap (LRU cache), TreeMap, PriorityQueue (heap dry run), ArrayDeque, all Collections utility methods, immutable [Java 9+], Comparable vs Comparator, O() complexity table, decision guide |

---

## Functional Programming (Java 8+)

| File | Topics |
|------|--------|
| [12-functional-interfaces.md](12-functional-interfaces.md) | @FunctionalInterface, Predicate/Function/BiFunction/Consumer/Supplier/UnaryOp/BinaryOp, composition, primitive specializations |
| [13-lambdas.md](13-lambdas.md) | Syntax, effectively final, variable capture, lambda vs anonymous class (this semantics), all 4 method reference types |
| [14-streams.md](14-streams.md) | Pipeline concept, all creation methods, all intermediate ops (filter/map/flatMap/distinct/sorted/peek/limit/skip/takeWhile/dropWhile/mapMulti), all terminal ops, all Collectors, parallel streams |
| [15-optional.md](15-optional.md) | Creation, checking/getting, transforming (map/flatMap/filter/or), stream() [Java 9+], anti-patterns |

---

## Date and Time

| File | Topics |
|------|--------|
| [16-date-time.md](16-date-time.md) | Legacy problems, LocalDate/Time/DateTime/ZonedDateTime/Instant, Duration vs Period, DateTimeFormatter, TemporalAdjusters, legacy bridge |

---

## Concurrency

| File | Topics |
|------|--------|
| [17-concurrency.md](17-concurrency.md) | Thread lifecycle (6-state diagram), creating threads, thread methods, race conditions, synchronized, volatile, AtomicInteger |
| [18-locks-executors.md](18-locks-executors.md) | Lock/ReentrantLock/ReadWriteLock/StampedLock, ExecutorService, Executors factory, Future, Callable, ScheduledExecutor |
| [19-completable-future.md](19-completable-future.md) | supplyAsync/runAsync, thenApply/Accept/Run, thenCompose, thenCombine/allOf/anyOf, exceptionally/handle/whenComplete, timeout [Java 9+] |
| [20-concurrent-collections.md](20-concurrent-collections.md) | ConcurrentHashMap (all atomic ops), CopyOnWriteArrayList, BlockingQueue (Array/Linked/Priority/Synchronous), ConcurrentLinkedQueue |
| [21-synchronization-primitives.md](21-synchronization-primitives.md) | CountDownLatch, CyclicBarrier, Semaphore (tryAcquire), Exchanger, Phaser |
| [22-virtual-threads.md](22-virtual-threads.md) | [Java 21] Architecture, scale demo (1M threads), StructuredConcurrency, pinning pitfalls, ThreadLocal dangers |
| [34-java-memory-model.md](34-java-memory-model.md) | Visibility/reordering problems, happens-before rules, volatile, safe publication, CAS operations |

---

## I/O and Serialization

| File | Topics |
|------|--------|
| [23-io-streams.md](23-io-streams.md) | Byte/character stream hierarchy, FileReader/Writer, BufferedReader/Writer, PrintWriter, try-with-resources, buffering impact |
| [24-nio.md](24-nio.md) | Path/Files API [Java 7+], Files.walk/find, WatchService, ByteBuffer (put/flip/get cycle), FileChannel, memory-mapped files |
| [25-serialization.md](25-serialization.md) | Serializable, serialVersionUID, transient, custom writeObject/readObject, Externalizable, security (ObjectInputFilter), JSON alternatives |

---

## Advanced Java

| File | Topics |
|------|--------|
| [26-reflection.md](26-reflection.md) | Class object, inspecting fields/methods, setAccessible, invoking methods, field access, annotation reflection, generic type info, dynamic proxy |
| [27-annotations.md](27-annotations.md) | Built-in annotations, custom annotation syntax, @Retention/@Target, runtime processing, repeatable [Java 8+], compile-time processing (APT) |
| [28-modules.md](28-modules.md) | [Java 9+] JPMS, module-info.java, exports/requires/opens/provides/uses, jlink, migration strategy |
| [33-jvm-internals.md](33-jvm-internals.md) | Architecture, runtime data areas (heap/stack/metaspace), class loading phases, generational GC, G1/ZGC comparison, JIT compilation, escape analysis |

---

## Modern Java Features

| File | Topics |
|------|--------|
| [29-records.md](29-records.md) | [Java 16+] Syntax, auto-generated members, compact constructors, adding methods, record patterns [Java 21], use cases |
| [30-sealed-classes.md](30-sealed-classes.md) | [Java 17+] sealed/final/non-sealed hierarchy, exhaustive switch, Result type pattern, JSON AST example |
| [31-pattern-matching.md](31-pattern-matching.md) | [Java 16-21] instanceof patterns, switch type patterns, guards (when), null case, record patterns (nested destructuring) |
| [32-enums.md](32-enums.md) | Basic enum, fields/constructors/methods, abstract per-constant, interface impl, EnumSet (bit vector), EnumMap, singleton pattern |

---

## Design and Best Practices

| File | Topics |
|------|--------|
| [35-design-patterns.md](35-design-patterns.md) | Creational (Singleton/Factory/Builder/Prototype), Structural (Decorator/Adapter/Composite/Proxy), Behavioral (Strategy/Observer/Command/Template/Chain) with Java 8+ lambda modernizations |
| [36-best-practices.md](36-best-practices.md) | Immutability, equals/hashCode contract, API design, null handling, exception rules, collection best practices, string handling, concurrency rules, modern Java idioms |

---

## Java Version History

| File | Java Version | Key Features |
|------|-------------|--------------|
| [java5-features.md](java5-features.md) | Java 5 (2004) | Generics, for-each, autoboxing, enums, annotations, varargs, java.util.concurrent |
| [java7-features.md](java7-features.md) | Java 7 (2011) | Diamond `<>`, try-with-resources, multi-catch, String switch, underscore literals, NIO.2, ForkJoinPool |
| [java8-features.md](java8-features.md) | Java 8 (2014) | **Lambdas, Streams, Optional, default methods, method references, java.time, CompletableFuture** |
| [java9-features.md](java9-features.md) | Java 9 (2017) | JPMS modules, List/Set/Map.of(), takeWhile/dropWhile, Optional.or/stream, private interface methods, Flow API |
| [java10-features.md](java10-features.md) | Java 10 (2018) | `var` type inference, List/Set/Map.copyOf(), Collectors.toUnmodifiableList |
| [java11-features.md](java11-features.md) | Java 11 LTS (2018) | String.isBlank/strip/lines/repeat, Files.readString/writeString, HttpClient, `var` in lambdas |
| [java12-features.md](java12-features.md) | Java 12 (2019) | Switch expressions (preview), Collectors.teeing, String.indent/transform |
| [java13-features.md](java13-features.md) | Java 13 (2019) | Text blocks (preview), yield keyword |
| [java14-features.md](java14-features.md) | Java 14 (2020) | Switch expressions (final), helpful NPEs, records (preview), instanceof pattern (preview) |
| [java15-features.md](java15-features.md) | Java 15 (2020) | Text blocks (final), sealed classes (preview), ZGC production-ready |
| [java16-features.md](java16-features.md) | Java 16 (2021) | Records (final), instanceof pattern (final), Stream.toList() |
| [java17-features.md](java17-features.md) | Java 17 LTS (2021) | Sealed classes (final), strong encapsulation enforced, enhanced PRNG |
| [java18-features.md](java18-features.md) | Java 18 (2022) | UTF-8 default charset, simple web server, @snippet Javadoc |
| [java19-features.md](java19-features.md) | Java 19 (2022) | Virtual threads (preview), structured concurrency (incubating), record patterns (preview) |
| [java20-features.md](java20-features.md) | Java 20 (2023) | Virtual threads (2nd preview), scoped values (incubating) |
| [java21-features.md](java21-features.md) | Java 21 LTS (2023) | **Virtual threads (final), pattern matching switch (final), record patterns (final), sequenced collections** |

---

## Quick Decision Guides

### Which Collection?
```
Need fast random access by index      → ArrayList
Need fast insert/remove at ends       → ArrayDeque (or LinkedList)
Need unique elements, fast contains   → HashSet
Need unique elements, sorted          → TreeSet
Need key-value, fast get/put          → HashMap
Need key-value, insertion order       → LinkedHashMap
Need key-value, sorted keys           → TreeMap
Need priority ordering                → PriorityQueue
Thread-safe map                       → ConcurrentHashMap
Producer-consumer queue               → ArrayBlockingQueue / LinkedBlockingQueue
```

### Which Concurrency Primitive?
```
One-shot wait-for-N events            → CountDownLatch
Repeated thread sync checkpoint       → CyclicBarrier
Limit concurrent resource access      → Semaphore
Exchange data between thread pair     → Exchanger
Thread-per-request server             → Executors.newVirtualThreadPerTaskExecutor() [Java 21]
Async pipeline                        → CompletableFuture
```

### Which GC?
```
Balanced (most apps)                  → G1GC (default Java 9+)
Low latency (<1ms pauses)             → ZGC [Java 15+]
High throughput batch                 → ParallelGC
Memory-constrained                    → SerialGC
```

### Which Pattern?
```
New object creation                   → Builder or Factory
Extend behavior without subclass      → Decorator
Convert incompatible interface        → Adapter
One-to-many notification              → Observer (EventBus)
Swappable algorithm                   → Strategy (lambda in Java 8+)
Undo support                          → Command
```

---

## Study Guide by Experience Level

### Beginner (fundamentals)
01 → 02 → 03 → 04 → 05 → 06 → 07 → 09

### Intermediate (Java 8+)
10 → 11 → 12 → 13 → 14 → 15 → 16 → 32 → 29

### Advanced (concurrency + JVM)
17 → 18 → 19 → 20 → 21 → 22 → 34 → 33

### Modern Java (Java 16-21)
29 → 30 → 31 → 22 → java16-features → java17-features → java21-features

### Interview Prep
11 (collections) → 14 (streams) → 17-22 (concurrency) → 35 (patterns) → 36 (best practices)
