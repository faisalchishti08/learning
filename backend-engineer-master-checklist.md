# Senior Backend Engineer (10 YOE, Java/Spring) — Master Knowledge & Interview Checklist

> A complete macro → micro topic map of what a 10-year backend engineer / technical lead is expected to know,
> both to **clear interviews** (DSA, LLD, HLD, behavioral) and to **be** a strong senior engineer.
> Tick `[ ]` → `[x]` as you go. Rate yourself 1–5 next to each macro topic and revisit weekly.

## Legend

| Tag | Meaning |
|-----|---------|
| **P0** | Must know deeply — asked in almost every senior interview. Be able to explain, whiteboard, and code it. |
| **P1** | Should know well — commonly asked, expected at 10 YOE. |
| **P2** | Awareness — know what it is, when to use it, and the trade-offs. |
| 🎯 | Frequently asked interview questions for that area |

---

## Table of Contents

**Part A — Language & Runtime Foundations**
1. [Core Java](#1-core-java-p0)
2. [Java Versions & Modern Java (8 → 25)](#2-java-versions--modern-java-8--25-p0)
3. [JVM Internals, GC & Troubleshooting](#3-jvm-internals-gc--troubleshooting-p0)
4. [Concurrency & Multithreading](#4-concurrency--multithreading-p0)

**Part B — Problem Solving**
5. [Data Structures & Algorithms](#5-data-structures--algorithms-p0)
6. [Object-Oriented Design / LLD & Design Patterns](#6-object-oriented-design--lld--design-patterns-p0)
7. [Machine Coding Round](#7-machine-coding-round-p0-for-product-companies)

**Part C — Spring Ecosystem**
8. [Spring Framework Core (IoC, DI, AOP)](#8-spring-framework-core-p0)
9. [Spring Boot](#9-spring-boot-p0)
10. [Spring Web MVC & REST](#10-spring-web-mvc--rest-p0)
11. [Reactive: Spring WebFlux & Project Reactor](#11-reactive-spring-webflux--project-reactor-p1)
12. [Data Access: JDBC, JPA, Hibernate, Spring Data](#12-data-access-jdbc-jpa-hibernate-spring-data-p0)
13. [Transactions](#13-transactions-p0)
14. [Spring Security, AuthN & AuthZ](#14-spring-security-authn--authz-p0)
15. [Spring Cloud & Microservices Infrastructure](#15-spring-cloud--microservices-infrastructure-p0)
16. [Other Spring Projects](#16-other-spring-projects-p1)
17. [Testing in Java & Spring](#17-testing-in-java--spring-p0)

**Part D — Data**
18. [SQL & Relational Databases](#18-sql--relational-databases-p0)
19. [NoSQL, Search & Storage](#19-nosql-search--storage-p0)
20. [Caching & Redis](#20-caching--redis-p0)

**Part E — Distributed Systems & Architecture**
21. [Messaging & Event Streaming (Kafka, RabbitMQ, SQS)](#21-messaging--event-streaming-p0)
22. [Distributed Systems Theory](#22-distributed-systems-theory-p0)
23. [Microservices Architecture](#23-microservices-architecture-p0)
24. [Domain-Driven Design](#24-domain-driven-design-p1)
25. [Architecture Styles & Documentation](#25-architecture-styles--documentation-p1)
26. [Resilience, Fault Tolerance & High Availability](#26-resilience-fault-tolerance--high-availability-p0)
27. [Rate Limiting & Throttling](#27-rate-limiting--throttling-p0)
28. [API Design (REST, gRPC, GraphQL, Async)](#28-api-design-p0)

**Part F — System Design (HLD)**
29. [System Design Interview Framework](#29-system-design-interview-framework-p0)
30. [Back-of-the-Envelope Estimation](#30-back-of-the-envelope-estimation-p0)
31. [System Design Building Blocks & Techniques](#31-system-design-building-blocks--techniques-p0)
32. [Classic System Design Problems](#32-classic-system-design-problems-p0)
33. [Data Engineering & Stream Processing](#33-data-engineering--stream-processing-p1)

**Part G — Infrastructure & Operations**
34. [Networking](#34-networking-p0)
35. [Operating Systems & Linux](#35-operating-systems--linux-p1)
36. [Docker & Kubernetes](#36-docker--kubernetes-p0)
37. [CI/CD, DevOps & IaC](#37-cicd-devops--iac-p1)
38. [Cloud (AWS-first, map to GCP/Azure)](#38-cloud-aws-first-p1)
39. [Observability](#39-observability-p0)
40. [Performance Engineering](#40-performance-engineering-p0)
41. [Security](#41-security-p0)

**Part H — Engineering Practice**
42. [Build Tools, Code Quality & Git](#42-build-tools-code-quality--git-p1)
43. [Production Engineering & Incident Management](#43-production-engineering--incident-management-p0)
44. [AI/LLM for Backend Engineers (2026)](#44-aillm-for-backend-engineers-p1)
45. [Domain Knowledge (Payments, E-commerce, etc.)](#45-domain-knowledge-p1)

**Part I — Leadership, Behavioral & Career**
46. [Technical Leadership Competencies](#46-technical-leadership-competencies-p0)
47. [Behavioral Interviews](#47-behavioral-interviews-p0)
48. [Project Deep-Dive Preparation](#48-project-deep-dive-preparation-p0)
49. [Resume, Job Search & Negotiation](#49-resume-job-search--negotiation-p0)
50. [Interview Formats by Company Type](#50-interview-formats-by-company-type)

**Part J — Execution**
51. [Cross-Topic Rapid-Fire Questions (Top 100)](#51-cross-topic-rapid-fire-questions-top-100)
52. [12-Week Preparation Plan](#52-12-week-preparation-plan)
53. [Resources](#53-resources)
54. [Final Readiness Checklist](#54-final-readiness-checklist)

---

# PART A — LANGUAGE & RUNTIME FOUNDATIONS

## 1. Core Java (P0)

### 1.1 OOP Fundamentals
- [ ] **Four pillars** — encapsulation, inheritance, polymorphism (compile-time vs runtime), abstraction
- [ ] **Abstract class vs interface** — default/static/private interface methods, multiple inheritance of behavior, diamond problem resolution
- [ ] **Composition over inheritance** — fragile base class problem, delegation
- [ ] **Overloading vs overriding** — rules: covariant return types, exception narrowing, access widening, static methods are hidden not overridden
- [ ] **Static vs dynamic binding**, method dispatch, `final`/`private`/`static` methods and binding
- [ ] **Keywords** — `final`, `static`, `this`, `super`, `transient`, `volatile`, `synchronized`, `native`, `strictfp`
- [ ] **Nested classes** — static nested, inner, local, anonymous; memory-leak risk of inner classes holding outer reference
- [ ] **Access modifiers** — private, package-private, protected, public; module-level encapsulation
- [ ] **Initialization order** — static blocks → instance initializers → constructors; parent before child; class loading triggers
- [ ] **Pass-by-value** semantics for primitives and references
- [ ] **`Object` class methods** — `equals`, `hashCode`, `toString`, `clone`, `finalize` (deprecated), `wait/notify/notifyAll`, `getClass`

### 1.2 equals / hashCode / compareTo / clone
- [ ] **equals–hashCode contract** — reflexive, symmetric, transitive, consistent; what breaks in HashMap/HashSet if violated
- [ ] **Mutable keys in hash collections** — why it's dangerous
- [ ] **`compareTo` consistent with equals** — TreeSet/TreeMap behaviour (`BigDecimal` example)
- [ ] **Cloning** — shallow vs deep copy, `Cloneable` flaws, copy constructors/static factories as alternatives

### 1.3 Strings
- [ ] **Immutability** — why (security, caching hashCode, thread-safety, string pool)
- [ ] **String pool**, `intern()`, `new String("x")` vs literal, `==` vs `equals`
- [ ] **StringBuilder vs StringBuffer**, concatenation in loops, `invokedynamic`-based concat (Java 9+)
- [ ] **Compact strings** (Latin-1 vs UTF-16), text blocks, `String.format`/`formatted`, `strip` vs `trim`, `repeat`, `isBlank`
- [ ] **Character encodings** — UTF-8/UTF-16, `char` vs code points, `getBytes(StandardCharsets.UTF_8)`

### 1.4 Immutability & Value Types
- [ ] **How to write an immutable class** — final class, private final fields, no setters, defensive copies in/out
- [ ] **Records** — compact constructors, validation, immutability caveats (shallow), records as DTOs
- [ ] **Unmodifiable vs immutable collections** — `Collections.unmodifiableList` (view) vs `List.of`/`List.copyOf`

### 1.5 Primitives, Wrappers & Numbers
- [ ] **Autoboxing/unboxing pitfalls** — NPE on unboxing, performance in loops
- [ ] **Integer cache** (−128..127) and `==` surprises
- [ ] **Floating-point issues** — never use `double` for money
- [ ] **BigDecimal** — scale, `RoundingMode`, `equals` vs `compareTo`, `new BigDecimal(double)` trap, `valueOf`
- [ ] **Integer overflow** — `Math.addExact`, `long` usage, `(a+b)/2` → `a+(b-a)/2`

### 1.6 Exceptions
- [ ] **Hierarchy** — `Throwable` → `Error` / `Exception` → `RuntimeException`
- [ ] **Checked vs unchecked** — when to use which; modern preference
- [ ] **try-with-resources**, `AutoCloseable`, suppressed exceptions
- [ ] **finally semantics** — return in finally, finally not running (System.exit, kill)
- [ ] **Custom exceptions**, exception chaining/translation, don't swallow, don't log-and-rethrow
- [ ] **Cost of exceptions** — stack trace capture, using exceptions for control flow anti-pattern
- [ ] **Multi-catch**, rethrow with precise types

### 1.7 Generics
- [ ] **Type erasure** — consequences (no `new T()`, no `instanceof List<String>`, no generic arrays)
- [ ] **Bounded types** — `<T extends Comparable<T>>`, multiple bounds
- [ ] **Wildcards & PECS** — `? extends` (producer) vs `? super` (consumer), `Collections.copy` example
- [ ] **Generic methods**, type inference, diamond operator
- [ ] **Raw types**, heap pollution, `@SafeVarargs`, bridge methods
- [ ] **Invariance** of generics vs covariance of arrays (`ArrayStoreException`)

### 1.8 Collections Framework
- [ ] **Hierarchy** — Iterable → Collection → List/Set/Queue/Deque; Map separate; SequencedCollection (Java 21)
- [ ] **ArrayList internals** — backing array, growth 1.5x, `RandomAccess`, removal cost
- [ ] **LinkedList** — doubly linked, when (almost never) to use
- [ ] **HashMap internals** — hash spreading, buckets, load factor 0.75, resize & rehash, treeification (TREEIFY_THRESHOLD 8, MIN_TREEIFY_CAPACITY 64), null key, iteration order, why capacity is power of 2
- [ ] **LinkedHashMap** — insertion vs access order, `removeEldestEntry` → LRU cache
- [ ] **TreeMap/TreeSet** — red-black tree, `floorKey`, `ceilingKey`, `headMap`, `tailMap`, `subMap`
- [ ] **HashSet** (backed by HashMap), LinkedHashSet
- [ ] **Specialized** — EnumMap, EnumSet, WeakHashMap, IdentityHashMap, BitSet
- [ ] **Queue/Deque** — ArrayDeque (use as stack), PriorityQueue (binary heap, not sorted iteration)
- [ ] **Concurrent collections** — ConcurrentHashMap (Java 8: CAS + synchronized on bin head, no segment locking, `compute`/`merge` atomicity, no null keys/values, size estimation), CopyOnWriteArrayList, ConcurrentSkipListMap/Set, ConcurrentLinkedQueue
- [ ] **BlockingQueue family** — ArrayBlockingQueue, LinkedBlockingQueue, PriorityBlockingQueue, DelayQueue, SynchronousQueue, LinkedTransferQueue
- [ ] **Fail-fast vs fail-safe (weakly consistent) iterators**, `ConcurrentModificationException`, `modCount`
- [ ] **Comparable vs Comparator** — `Comparator.comparing().thenComparing().reversed()`, null handling
- [ ] **Utility pitfalls** — `Arrays.asList` fixed-size, `List.of` nulls not allowed, `subList` views
- [ ] **Big-O of every common operation** for each collection

### 1.9 Functional Programming & Streams
- [ ] **Lambdas** — effectively final capture, `this` semantics vs anonymous classes
- [ ] **Functional interfaces** — Function, BiFunction, Supplier, Consumer, Predicate, UnaryOperator, BinaryOperator, primitive specializations, `@FunctionalInterface`
- [ ] **Method references** — static, bound, unbound, constructor
- [ ] **Optional** — correct usage (return types only), `orElse` vs `orElseGet`, `map`/`flatMap`, anti-patterns (`get()`, fields, params)
- [ ] **Stream pipeline** — source → intermediate (lazy) → terminal; short-circuiting; stateful ops (`sorted`, `distinct`)
- [ ] **Collectors** — `toList`, `toMap` (merge function, duplicate key exception), `groupingBy` (downstream collectors, `counting`, `mapping`), `partitioningBy`, `joining`, `teeing`, `collectingAndThen`
- [ ] **flatMap, reduce, iterate, generate, takeWhile/dropWhile**, `Stream.toList()` (unmodifiable)
- [ ] **Parallel streams** — ForkJoin common pool, when they hurt (I/O, small data, ordering, shared state)
- [ ] **Stream Gatherers** (Java 24) — custom intermediate operations (awareness)

### 1.10 Enums, Annotations, Reflection, Proxies
- [ ] **Enums** — fields, constructors, abstract methods per constant, enum singleton, `values()`, `valueOf`, switch
- [ ] **Annotations** — retention (SOURCE/CLASS/RUNTIME), target, meta-annotations, writing custom annotations
- [ ] **Annotation processing** at compile time — Lombok, MapStruct, how they work
- [ ] **Reflection** — Class, Method, Field, Constructor, `setAccessible`, performance cost, module restrictions
- [ ] **Dynamic proxies** — JDK `Proxy` (interfaces only) vs CGLIB/ByteBuddy (subclassing) — **the basis of Spring AOP**
- [ ] **MethodHandles & VarHandles** (awareness)

### 1.11 Serialization & Data Formats
- [ ] **Java serialization** — `Serializable`, `serialVersionUID`, `transient`, `Externalizable`, `readResolve` for singletons
- [ ] **Deserialization vulnerabilities** — gadget chains, why to avoid native serialization
- [ ] **Jackson** — ObjectMapper (thread-safe, reuse), annotations (`@JsonProperty`, `@JsonIgnore`, `@JsonInclude`, `@JsonFormat`, `@JsonCreator`), unknown properties handling, polymorphic types (`@JsonTypeInfo`), custom (de)serializers, Java time module, Jackson 3 (Spring Boot 4) awareness
- [ ] **Binary formats** — Protobuf, Avro, Thrift, MessagePack; schema evolution rules

### 1.12 I/O & NIO
- [ ] **Byte vs character streams**, buffering, decorators (`BufferedReader(new InputStreamReader(...))`)
- [ ] **NIO** — Channels, Buffers (flip/clear/compact), Selectors, non-blocking I/O
- [ ] **NIO.2** — `Path`, `Files`, `WatchService`, walking file trees
- [ ] **Memory-mapped files**, direct buffers, **zero-copy** (`FileChannel.transferTo` → sendfile; why Kafka is fast)
- [ ] **Reading huge files** line by line / streaming without OOM

### 1.13 Date & Time
- [ ] **java.time** — Instant, LocalDate/Time, ZonedDateTime, OffsetDateTime, Duration vs Period, ZoneId, DateTimeFormatter (thread-safe)
- [ ] **Why `Date`/`SimpleDateFormat` are bad** (mutable, not thread-safe)
- [ ] **Timezone best practices** — store UTC, convert at edges, DST pitfalls, `Clock` injection for testability

### 1.14 Common Libraries Every Senior Java Dev Uses
- [ ] **Logging** — SLF4J facade, Logback, Log4j2 (async loggers), parameterized logging, Log4Shell lesson
- [ ] **Lombok** — `@Data` pitfalls on JPA entities, `@Builder`, `@Value`, `@RequiredArgsConstructor`, `@Slf4j`
- [ ] **MapStruct** — compile-time mappers vs ModelMapper (reflection)
- [ ] **Guava / Apache Commons / Caffeine / Resilience4j / Micrometer / Jackson / Testcontainers** — know what each is for

### 1.15 Effective Java — Key Items to Be Able to Discuss
- [ ] Static factory methods over constructors; Builder for many params
- [ ] Enforce singleton with enum; non-instantiability with private constructor
- [ ] Prefer dependency injection to hardwiring resources
- [ ] Avoid creating unnecessary objects; eliminate obsolete references (memory leaks)
- [ ] Minimize mutability; minimize accessibility; favor composition
- [ ] Prefer interfaces to abstract classes; design for inheritance or prohibit it
- [ ] Use EnumMap instead of ordinal indexing; prefer lambdas & method refs
- [ ] Check parameters for validity; make defensive copies; return empty collections not null
- [ ] Use exceptions only for exceptional conditions; favor standard exceptions
- [ ] Prefer executors/tasks/streams to threads; prefer concurrency utilities to wait/notify

### 1.16 Memory Leaks in Java (classic senior question)
- [ ] Static collections growing unbounded, caches without eviction
- [ ] Unclosed resources (streams, connections)
- [ ] ThreadLocal in thread pools not removed
- [ ] Listeners/callbacks not deregistered
- [ ] Inner classes holding outer references
- [ ] ClassLoader leaks on redeploy; interned strings; improper `equals/hashCode` keys in maps

### 🎯 Frequently Asked — Core Java
- How does HashMap work internally? What changed in Java 8? What happens on collision and resize?
- Why is String immutable? How would you make a class immutable?
- equals/hashCode contract — what breaks if you override only one?
- ConcurrentHashMap vs `Collections.synchronizedMap` vs Hashtable
- Checked vs unchecked exceptions — your team's policy and why
- Explain PECS with an example
- How would you implement an LRU cache in Java (LinkedHashMap and from scratch)?
- `Comparable` vs `Comparator`; `fail-fast` vs `fail-safe`
- Stream: `map` vs `flatMap`; `findFirst` vs `findAny`; why parallel streams can be slower

---

## 2. Java Versions & Modern Java (8 → 25) (P0)

| Version | Key features you should be able to explain and use |
|---------|-----------------------------------------------------|
| **8** (LTS) | Lambdas, Streams, Optional, `java.time`, default/static interface methods, CompletableFuture, Metaspace replaces PermGen |
| **9** | JPMS modules, `List.of/Set.of/Map.of`, JShell, private interface methods, `Optional` improvements, compact strings, G1 default |
| **10** | `var` local type inference, container awareness improvements |
| **11** (LTS) | `HttpClient` (HTTP/2), `String` methods (`isBlank`, `lines`, `strip`, `repeat`), run single-file source, `Files.readString`, ZGC (experimental), Epsilon GC |
| **12–13** | Switch expressions (preview), text blocks (preview) |
| **14** | Switch expressions (final), helpful NullPointerExceptions, records (preview) |
| **15** | Text blocks (final), ZGC & Shenandoah production-ready, sealed classes (preview), biased locking disabled |
| **16** | Records (final), pattern matching for `instanceof` (final), `Stream.toList()` |
| **17** (LTS) | Sealed classes (final), strong encapsulation of JDK internals, new macOS rendering; Spring Boot 3 baseline |
| **18–20** | UTF-8 default charset, simple web server, virtual threads (preview), record patterns (preview) |
| **21** (LTS) | **Virtual threads (final)**, pattern matching for switch, record patterns, sequenced collections, generational ZGC, string templates (preview, later withdrawn) |
| **22** | Unnamed variables & patterns (`_`), Foreign Function & Memory API (final), launch multi-file programs |
| **23–24** | Markdown doc comments, **Stream Gatherers (final, 24)**, virtual threads no longer pin on `synchronized` (24), class-file API, AOT class loading (Leyden), quantum-resistant crypto |
| **25** (LTS) | Scoped values (final), module import declarations, compact source files & instance `main`, flexible constructor bodies, compact object headers, generational Shenandoah; structured concurrency still preview |

- [ ] **Know your LTS migration story** — 8 → 11 → 17 → 21 (→ 25): what broke (javax → jakarta, removed internals, illegal reflective access), how you migrated
- [ ] **Records + sealed interfaces + pattern matching switch** → algebraic data types / exhaustive handling
- [ ] **Virtual threads** — covered in §4.8
- [ ] **Release cadence** — 6-month releases, LTS every 2 years; vendor distributions (Temurin, Corretto, Zulu, GraalVM)

---

## 3. JVM Internals, GC & Troubleshooting (P0)

### 3.1 JVM Architecture
- [ ] **JDK vs JRE vs JVM**, bytecode, `javac` → `.class` → class loader → execution engine
- [ ] **Class loading** — Bootstrap / Platform / Application loaders, parent-delegation model, custom class loaders, why delegation (security, uniqueness)
- [ ] **Loading → Linking (verify, prepare, resolve) → Initialization**; when a class is initialized
- [ ] **`ClassNotFoundException` vs `NoClassDefFoundError`**; dependency conflicts at runtime

### 3.2 Runtime Memory Areas
- [ ] **Heap** — Young (Eden, S0, S1) and Old generation; object promotion & tenuring threshold
- [ ] **Metaspace** (native memory, replaced PermGen in 8) — class metadata, leaks
- [ ] **Thread stacks** — frames, local vars, operand stack; `StackOverflowError`; `-Xss`
- [ ] **PC register, native method stack, code cache, direct (off-heap) memory**
- [ ] **Object layout** — header (mark word + klass pointer), compressed oops, padding/alignment, compact object headers (Java 25)
- [ ] **TLAB** (thread-local allocation buffers), escape analysis → stack allocation/scalar replacement
- [ ] **String deduplication** (G1)

### 3.3 Garbage Collection
- [ ] **Reachability & GC roots** (thread stacks, static fields, JNI refs)
- [ ] **Algorithms** — mark-sweep, mark-compact, copying; generational hypothesis
- [ ] **Stop-the-world, safepoints**, card tables, write/load barriers, remembered sets
- [ ] **Minor vs Major vs Full GC**
- [ ] **Collectors** — Serial, Parallel (throughput), CMS (removed in 14), **G1** (regions, mixed collections, humongous objects, pause target `MaxGCPauseMillis`), **ZGC** (concurrent, colored pointers, load barriers, sub-ms pauses, generational in 21+), **Shenandoah** (concurrent compaction, Brooks pointers), Epsilon (no-op)
- [ ] **Choosing a GC** — latency-sensitive APIs vs batch throughput vs small containers
- [ ] **Reference types** — strong, soft (caches), weak (WeakHashMap), phantom (cleanup), `Cleaner`; why `finalize` is deprecated

### 3.4 Execution & JIT
- [ ] **Interpreter + JIT** — C1, C2, tiered compilation, hot-method thresholds
- [ ] **Optimizations** — inlining, escape analysis, loop unrolling, lock elision/coarsening, dead code elimination
- [ ] **Deoptimization, OSR**, warm-up effects on latency after deploy
- [ ] **Startup optimization** — CDS/AppCDS, GraalVM native image (AOT, closed-world, reflection config), CRaC, Project Leyden

### 3.5 JVM Tuning Flags
- [ ] `-Xms`, `-Xmx` (set equal in prod?), `-Xss`, `-XX:MaxMetaspaceSize`, `-XX:MaxDirectMemorySize`
- [ ] **Container awareness** — `-XX:MaxRAMPercentage`, `-XX:ActiveProcessorCount`, CPU limits vs GC/JIT thread counts
- [ ] `-XX:+UseG1GC / UseZGC`, `-XX:MaxGCPauseMillis`
- [ ] `-XX:+HeapDumpOnOutOfMemoryError`, `-XX:HeapDumpPath`, `-XX:+ExitOnOutOfMemoryError`
- [ ] **Unified GC logging** — `-Xlog:gc*:file=gc.log:time,uptime`

### 3.6 OutOfMemoryError Types
- [ ] `Java heap space` · `GC overhead limit exceeded` · `Metaspace` · `unable to create new native thread` · `Direct buffer memory` · `Requested array size exceeds VM limit` · container OOMKilled (exit 137) vs Java OOM

### 3.7 Troubleshooting Toolkit
- [ ] **CLI** — `jps`, `jcmd` (swiss-army knife), `jstack`, `jmap`, `jstat`, `jinfo`
- [ ] **Profilers** — JFR + JDK Mission Control, async-profiler (CPU, alloc, lock, wall-clock), flame graphs, VisualVM, YourKit/JProfiler
- [ ] **Heap dump analysis** — Eclipse MAT: dominator tree, retained vs shallow size, leak suspects, GC roots path
- [ ] **Thread dump analysis** — states (RUNNABLE, BLOCKED, WAITING, TIMED_WAITING), deadlock detection, taking 3 dumps 5–10s apart, fastThread
- [ ] **GC log analysis** — GCeasy, pause times, allocation rate, promotion rate

### 3.8 Production Scenarios (be ready with a structured approach)
- [ ] CPU at 100% on one pod → `top -H` → thread id → hex → `jstack` → hot frame / or async-profiler
- [ ] Memory growing slowly → heap dumps over time → compare → leak suspects
- [ ] Latency spikes every N minutes → GC logs → Full GCs / humongous allocations → tune or fix allocation
- [ ] App slow after deploy → JIT warm-up, cold caches, connection pool warm-up
- [ ] Too many threads → thread dump → unbounded executors / blocked I/O

### 🎯 Frequently Asked — JVM
- Explain JVM memory model areas; where do objects, static vars, local vars, and class metadata live?
- How does G1 work? G1 vs ZGC — when would you choose each?
- How do you debug a memory leak / high CPU in production?
- What is a safepoint? Why do long time-to-safepoint pauses happen?
- How do you size heap for a container with a 2 GB limit?

---

## 4. Concurrency & Multithreading (P0)

### 4.1 Basics
- [ ] **Process vs thread**, context switching cost, user vs kernel threads
- [ ] **Thread lifecycle states** — NEW, RUNNABLE, BLOCKED, WAITING, TIMED_WAITING, TERMINATED
- [ ] **Creating tasks** — Thread, Runnable, Callable; daemon threads; thread naming
- [ ] **`sleep` vs `wait` vs `yield` vs `join`**; `wait` releases the monitor, `sleep` doesn't
- [ ] **Interruption** — cooperative cancellation, `InterruptedException` handling (restore the flag!)

### 4.2 Java Memory Model (JMM)
- [ ] **Visibility, atomicity, ordering** — the three concurrency problems
- [ ] **Happens-before rules** — program order, monitor lock, volatile, thread start/join, final fields
- [ ] **volatile** — visibility & ordering, not atomicity (`count++` still unsafe)
- [ ] **Safe publication** — final fields, static initializers, volatile, concurrent collections
- [ ] **Double-checked locking** — why it needs `volatile`; holder-class idiom; enum singleton
- [ ] **Instruction reordering**, CPU caches, memory barriers (conceptual)
- [ ] **False sharing** — cache lines, `@Contended`, padding

### 4.3 Locks & Synchronization
- [ ] **`synchronized`** — instance vs static vs block; reentrancy; monitor; lock on `this` vs private lock object
- [ ] **`wait/notify/notifyAll`** — always in a loop (spurious wakeups), with the monitor held
- [ ] **ReentrantLock** — fairness, `tryLock(timeout)`, `lockInterruptibly`, always unlock in `finally`
- [ ] **Condition variables** — multiple wait-sets (`notFull`, `notEmpty`)
- [ ] **ReadWriteLock / ReentrantReadWriteLock** — read-heavy workloads, writer starvation
- [ ] **StampedLock** — optimistic reads
- [ ] **synchronized vs ReentrantLock** — when to choose which
- [ ] **LockSupport.park/unpark**, AQS (AbstractQueuedSynchronizer) basics

### 4.4 Atomics & Lock-Free
- [ ] **CAS (compare-and-swap)** — how it works, spin loops, contention
- [ ] **AtomicInteger/Long/Boolean/Reference**, `updateAndGet`, `accumulateAndGet`
- [ ] **ABA problem** & AtomicStampedReference
- [ ] **LongAdder vs AtomicLong** — striped counters under contention
- [ ] **Lock-free vs wait-free** (awareness)

### 4.5 Synchronizers
- [ ] **CountDownLatch** (one-shot), **CyclicBarrier** (reusable, barrier action), **Semaphore** (permits, resource pools, limiting concurrency), **Phaser**, **Exchanger**
- [ ] Use-case mapping for each

### 4.6 Executors & Thread Pools
- [ ] **ThreadPoolExecutor parameters** — corePoolSize, maximumPoolSize, keepAliveTime, workQueue, ThreadFactory, RejectedExecutionHandler
- [ ] **Task submission flow** — core threads → queue → extra threads up to max → reject (why an unbounded queue means max is never reached)
- [ ] **Rejection policies** — Abort, CallerRuns (backpressure), Discard, DiscardOldest
- [ ] **Executors factory pitfalls** — `newFixedThreadPool`/`newSingleThreadExecutor` (unbounded queue → OOM), `newCachedThreadPool` (unbounded threads)
- [ ] **Sizing** — CPU-bound ≈ N cores (+1); I/O-bound ≈ N × (1 + wait/compute); measure, don't guess
- [ ] **ScheduledExecutorService** — `scheduleAtFixedRate` vs `scheduleWithFixedDelay`, exception kills subsequent runs
- [ ] **ForkJoinPool** — work stealing, RecursiveTask, common pool (used by parallel streams & CompletableFuture default)
- [ ] **Graceful shutdown** — `shutdown` → `awaitTermination` → `shutdownNow`
- [ ] **Monitoring pools** — active count, queue size, rejected count (Micrometer `ExecutorServiceMetrics`)

### 4.7 Futures & Async Composition
- [ ] **Future** limitations (blocking `get`, no composition)
- [ ] **CompletableFuture** — `supplyAsync`/`runAsync` (always pass a custom executor), `thenApply` vs `thenCompose` vs `thenCombine`, `allOf`/`anyOf`, `exceptionally`/`handle`/`whenComplete`, `orTimeout`/`completeOnTimeout`, `*Async` variants and which thread runs callbacks
- [ ] **Fan-out / fan-in** of N remote calls with timeouts and partial failure handling

### 4.8 Virtual Threads & Structured Concurrency (Java 21+)
- [ ] **What they are** — lightweight threads scheduled on carrier (ForkJoin) threads; mount/unmount on blocking
- [ ] **When to use** — high-concurrency I/O-bound thread-per-request; **not** for CPU-bound work
- [ ] **Pinning** — `synchronized` (fixed in 24), native frames; detect with `-Djdk.tracePinnedThreads` / JFR
- [ ] **Don't pool virtual threads**; limit concurrency with Semaphore instead
- [ ] **ThreadLocal cost** with millions of threads → **Scoped Values**
- [ ] **Downstream impact** — DB connection pool becomes the bottleneck; rate-limit downstream
- [ ] **Spring Boot** — `spring.threads.virtual.enabled=true` (Tomcat, `@Async`, schedulers)
- [ ] **Structured concurrency** (preview) — `StructuredTaskScope`, fail-fast subtasks, cancellation propagation
- [ ] **Virtual threads vs reactive (WebFlux)** — trade-offs

### 4.9 Concurrency Hazards
- [ ] **Race conditions** — check-then-act, read-modify-write
- [ ] **Deadlock** — 4 Coffman conditions, prevention (lock ordering, tryLock with timeout), detection via thread dump
- [ ] **Livelock, starvation**, priority inversion
- [ ] **Thread-safety strategies** — confinement, immutability, synchronization, concurrent data structures
- [ ] **ThreadLocal** — use cases (request context, SimpleDateFormat legacy), leaks in thread pools, InheritableThreadLocal
- [ ] **Context propagation** across threads — MDC, SecurityContext, tracing (TaskDecorator, Micrometer context-propagation)

### 4.10 Classic Concurrency Coding Problems (practice writing them)
- [ ] Producer–consumer (with `wait/notify` and with `BlockingQueue`)
- [ ] Print odd/even numbers alternately with 2 threads; print sequence with N threads (round-robin)
- [ ] Implement a bounded blocking queue (Lock + 2 Conditions)
- [ ] Thread-safe singleton (all variants)
- [ ] Implement a simple thread pool
- [ ] Thread-safe LRU cache
- [ ] Rate limiter (token bucket) thread-safe
- [ ] Read-write lock from scratch
- [ ] Dining philosophers; deadlock-free bank transfer (lock ordering by account id)
- [ ] Parallel web crawler / parallel merge sort with ForkJoin
- [ ] Delayed task scheduler (DelayQueue / PriorityQueue + condition)
- [ ] CompletableFuture: call 3 services in parallel, combine with timeout & fallback

### 🎯 Frequently Asked — Concurrency
- volatile vs synchronized vs AtomicInteger
- How does ConcurrentHashMap achieve thread safety?
- Explain ThreadPoolExecutor's behavior when tasks exceed capacity
- What is a deadlock? How do you detect and prevent it in production?
- thenApply vs thenCompose; how do you handle exceptions in CompletableFuture?
- Virtual threads: how do they work, what is pinning, would you migrate your service?
- How do you propagate MDC/trace IDs across async threads?

---

# PART B — PROBLEM SOLVING

## 5. Data Structures & Algorithms (P0)

> Target: **250–300 quality problems** (Blind 75 → NeetCode 150 → company-tagged). Senior bar = Medium in ~25 min with clean code, edge cases and complexity, plus handling a Hard with hints.

### 5.1 Complexity Analysis
- [ ] Big-O / Big-Θ / Big-Ω, best/average/worst case
- [ ] Amortized analysis (dynamic array append, union-find)
- [ ] Space complexity incl. recursion stack
- [ ] Recurrences & Master theorem (merge sort, binary search)
- [ ] Input-size → acceptable complexity cheat sheet (n ≤ 20 → 2ⁿ, n ≤ 10³ → n², n ≤ 10⁵–10⁶ → n log n, n ≥ 10⁸ → n / log n)

### 5.2 Data Structures
- [ ] **Arrays & Strings** — in-place ops, prefix sums, difference arrays, 2D matrices
- [ ] **Hash tables** — hashing, collisions (chaining vs open addressing), load factor
- [ ] **Linked lists** — singly, doubly, circular; dummy head technique
- [ ] **Stacks & Queues**, Deque, **monotonic stack/queue**
- [ ] **Heaps / Priority queues** — heapify O(n), push/pop O(log n), top-K, k-way merge, two heaps (median)
- [ ] **Trees** — binary tree, BST (insert/delete/validate), traversals (pre/in/post/level, iterative & recursive, Morris P2), LCA, diameter, serialization
- [ ] **Balanced trees** — AVL/Red-Black (concept), **B-tree / B+tree** (concept — database index relevance)
- [ ] **Tries** — insert/search/startsWith, word search, autocomplete
- [ ] **Graphs** — adjacency list/matrix, directed/undirected, weighted, implicit graphs (grids, word ladders)
- [ ] **Disjoint Set Union** — union by rank/size, path compression
- [ ] **Segment tree / Fenwick tree (BIT)** — range queries & point updates (P1)
- [ ] **Bit manipulation** — XOR tricks, masks, counting bits, power of two
- [ ] **Design-type structures** — LRU, LFU, min-stack, hit counter, time-based KV store, randomized set
- [ ] **Probabilistic** (crossover to system design) — Bloom filter, Count-Min Sketch, HyperLogLog, skip list

### 5.3 Algorithms
- [ ] **Sorting** — merge sort, quicksort (Lomuto/Hoare partition, pivot choice), heap sort, counting/radix/bucket sort, stability; Java uses dual-pivot quicksort for primitives and TimSort for objects
- [ ] **Quickselect** — kth largest in O(n) average
- [ ] **Binary search** — classic, lower/upper bound, rotated array, search on answer space (min capacity, Koko bananas)
- [ ] **Recursion & backtracking** — subsets, permutations, combinations, N-Queens, sudoku, word search; pruning
- [ ] **Divide & conquer**
- [ ] **Greedy** — interval scheduling, jump game, gas station, task scheduler; proving greedy choice
- [ ] **Dynamic programming** — memoization vs tabulation, state definition, space optimization
  - [ ] 1D DP (climbing stairs, house robber, decode ways, word break)
  - [ ] 2D/grid DP (unique paths, min path sum)
  - [ ] Knapsack 0/1 & unbounded (coin change, partition equal subset, target sum)
  - [ ] LIS (O(n log n) patience sorting), LCS, edit distance
  - [ ] Interval DP (burst balloons, matrix chain) — P1
  - [ ] DP on trees (house robber III, max path sum)
  - [ ] Stock buy/sell state machine series
  - [ ] Bitmask DP / digit DP — P2
- [ ] **Graph algorithms**
  - [ ] BFS (shortest path unweighted, multi-source BFS, 0-1 BFS), DFS (iterative & recursive)
  - [ ] Cycle detection (directed: colors/DFS; undirected: DSU/parent)
  - [ ] Topological sort — Kahn's (BFS) and DFS; course schedule
  - [ ] Dijkstra (with PriorityQueue), Bellman-Ford (negative edges), Floyd-Warshall
  - [ ] MST — Kruskal (DSU), Prim
  - [ ] Bipartite check, connected components, islands
  - [ ] SCC (Tarjan/Kosaraju), bridges & articulation points — P2
  - [ ] A* (awareness)
- [ ] **String algorithms** — KMP, Rabin-Karp (rolling hash), anagram/palindrome techniques; Z-algo/Manacher (P2)
- [ ] **Math** — GCD/LCM, sieve of Eratosthenes, modular arithmetic & fast exponentiation, combinatorics, reservoir sampling, Fisher-Yates shuffle

### 5.4 Problem-Solving Patterns (recognize the pattern first)
- [ ] Two pointers (opposite ends, same direction)
- [ ] Sliding window (fixed & variable size, with hashmap counts)
- [ ] Fast & slow pointers (cycle detection, middle of list)
- [ ] Merge intervals / interval scheduling / sweep line
- [ ] Cyclic sort (missing/duplicate numbers in 1..n)
- [ ] In-place linked-list reversal
- [ ] Tree BFS / Tree DFS
- [ ] Two heaps (running median, IPO)
- [ ] Subsets / permutations / combinations (backtracking)
- [ ] Modified binary search
- [ ] Top-K elements (heap / quickselect / bucket)
- [ ] K-way merge
- [ ] Topological sort
- [ ] Monotonic stack (next greater element, histogram)
- [ ] Prefix sum + hashmap (subarray sum equals K)
- [ ] Union-find
- [ ] Trie
- [ ] Matrix traversal (spiral, rotate, flood fill)
- [ ] Bitwise XOR
- [ ] Greedy
- [ ] DP patterns (above)
- [ ] Design data structure

### 5.5 Must-Practice Problems by Category (LeetCode names)
- [ ] **Arrays/Hashing** — Two Sum, Contains Duplicate, Valid Anagram, Group Anagrams, Top K Frequent Elements, Product of Array Except Self, Longest Consecutive Sequence, Subarray Sum Equals K, Majority Element, Next Permutation, Rotate Array, Encode/Decode Strings
- [ ] **Two Pointers** — Valid Palindrome, 3Sum, Container With Most Water, Trapping Rain Water, Sort Colors, Remove Duplicates
- [ ] **Sliding Window** — Best Time to Buy & Sell Stock, Longest Substring Without Repeating Characters, Longest Repeating Character Replacement, Permutation in String, Minimum Window Substring, Sliding Window Maximum
- [ ] **Stack** — Valid Parentheses, Min Stack, Evaluate RPN, Daily Temperatures, Car Fleet, Largest Rectangle in Histogram, Decode String, Basic Calculator II
- [ ] **Binary Search** — Search in Rotated Sorted Array, Find Min in Rotated Array, Koko Eating Bananas, Time Based Key-Value Store, Median of Two Sorted Arrays, Capacity to Ship Packages
- [ ] **Linked List** — Reverse List, Merge Two Lists, Linked List Cycle (I & II), Reorder List, Remove Nth From End, Copy List with Random Pointer, Add Two Numbers, Merge K Sorted Lists, Reverse Nodes in k-Group, **LRU Cache**
- [ ] **Trees** — Invert, Max Depth, Diameter, Balanced, Same Tree, Subtree, LCA (BST & BT), Level Order, Right Side View, Validate BST, Kth Smallest in BST, Build Tree from Preorder/Inorder, Max Path Sum, Serialize/Deserialize
- [ ] **Tries** — Implement Trie, Add & Search Words, Word Search II
- [ ] **Heap** — Kth Largest in Stream, Last Stone Weight, K Closest Points, Task Scheduler, Design Twitter, Find Median from Data Stream
- [ ] **Backtracking** — Subsets I/II, Combination Sum I/II, Permutations I/II, Word Search, Palindrome Partitioning, Letter Combinations, N-Queens
- [ ] **Graphs** — Number of Islands, Clone Graph, Max Area of Island, Pacific Atlantic, Surrounded Regions, Rotting Oranges, Course Schedule I/II, Redundant Connection, Number of Connected Components, Graph Valid Tree, Word Ladder, Accounts Merge
- [ ] **Advanced Graphs** — Network Delay Time, Cheapest Flights Within K Stops, Min Cost to Connect Points, Swim in Rising Water, Reconstruct Itinerary, Alien Dictionary
- [ ] **1D DP** — Climbing Stairs, House Robber I/II, Longest Palindromic Substring, Palindromic Substrings, Decode Ways, Coin Change, Max Product Subarray, Word Break, LIS, Partition Equal Subset Sum
- [ ] **2D DP** — Unique Paths, LCS, Best Time with Cooldown, Coin Change II, Target Sum, Interleaving String, Edit Distance, Longest Increasing Path in Matrix, Distinct Subsequences, Regular Expression Matching (P1)
- [ ] **Greedy** — Maximum Subarray (Kadane), Jump Game I/II, Gas Station, Hand of Straights, Partition Labels, Valid Parenthesis String
- [ ] **Intervals** — Insert Interval, Merge Intervals, Non-overlapping Intervals, Meeting Rooms I/II, Minimum Interval to Include Each Query
- [ ] **Math & Bits** — Rotate Image, Spiral Matrix, Set Matrix Zeroes, Pow(x,n), Single Number, Number of 1 Bits, Counting Bits, Reverse Bits, Missing Number, Sum of Two Integers
- [ ] **Design** — LRU Cache, LFU Cache, Design Hit Counter, Logger Rate Limiter, Insert Delete GetRandom O(1), Design Underground System, Snapshot Array

### 5.6 Java Idioms for Coding Interviews
- [ ] `Deque<Integer> stack = new ArrayDeque<>()` (not `Stack`)
- [ ] `PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(a[0], b[0]))` — avoid `a-b` overflow
- [ ] `map.getOrDefault`, `merge(k, 1, Integer::sum)`, `computeIfAbsent(k, x -> new ArrayList<>())`
- [ ] `TreeMap.floorKey/ceilingKey/firstEntry/pollFirstEntry`
- [ ] `Arrays.sort`, `Arrays.fill`, `Collections.reverse`, `Arrays.asList`, `List.of`, `int[]` vs `Integer[]` sorting with comparator
- [ ] `StringBuilder` (`reverse`, `insert`, `deleteCharAt`), `char - 'a'` indexing, `Character.isLetterOrDigit`
- [ ] `Integer.MAX_VALUE` overflow guards, `long` for sums, `Math.floorMod`

### 5.7 Interview Execution Protocol
- [ ] Clarify inputs/outputs/constraints, ask about edge cases (empty, duplicates, negatives, huge input)
- [ ] Walk through 1–2 examples by hand
- [ ] State brute force + complexity, then optimize (identify the pattern)
- [ ] Get buy-in on the approach **before** coding
- [ ] Write clean, modular code with meaningful names
- [ ] Dry-run with an example; test edge cases; state time & space complexity
- [ ] Discuss follow-ups (streaming input, distributed, memory-constrained)
- [ ] Think aloud throughout

---

## 6. Object-Oriented Design / LLD & Design Patterns (P0)

### 6.1 Design Principles
- [ ] **SOLID** — SRP, OCP, LSP (rectangle/square), ISP, DIP — with a real code example of each from your work
- [ ] **DRY, KISS, YAGNI**, Law of Demeter, Tell-Don't-Ask
- [ ] **Composition over inheritance**, program to interfaces
- [ ] **High cohesion, low coupling**, separation of concerns
- [ ] **GRASP** (information expert, creator, controller) — P2
- [ ] **Design by contract**, invariants, fail-fast

### 6.2 UML (enough for whiteboarding)
- [ ] Class diagrams — association, aggregation, composition, inheritance, realization, dependency, multiplicity
- [ ] Sequence diagrams, state diagrams, activity diagrams, use-case diagrams

### 6.3 GoF Design Patterns — intent + Java/Spring real-world example
**Creational**
- [ ] **Singleton** — eager, lazy, synchronized, double-checked, holder, enum; Spring singleton scope vs GoF singleton; why it's an anti-pattern for testability
- [ ] **Factory Method** — `Calendar.getInstance`, Spring `FactoryBean`
- [ ] **Abstract Factory** — families of related objects (e.g., cloud provider clients)
- [ ] **Builder** — `StringBuilder`, Lombok `@Builder`, `UriComponentsBuilder`, `WebClient.builder()`
- [ ] **Prototype** — clone, Spring prototype scope
- [ ] **Object Pool** — connection pools, thread pools

**Structural**
- [ ] **Adapter** — `Arrays.asList`, Spring `HandlerAdapter`, legacy integration
- [ ] **Bridge** — JDBC driver abstraction, SLF4J
- [ ] **Composite** — tree structures, UI components, file system
- [ ] **Decorator** — `java.io` streams, `Collections.synchronizedList`, Spring `BeanPostProcessor` wrapping
- [ ] **Facade** — `JdbcTemplate`, service layer
- [ ] **Flyweight** — Integer cache, String pool
- [ ] **Proxy** — Spring AOP, `@Transactional`, JPA lazy loading proxies, remote proxies

**Behavioral**
- [ ] **Strategy** — Comparator, payment strategies, pricing rules; Spring `Map<String, Strategy>` injection
- [ ] **Observer** — Spring `ApplicationEvent`/`@EventListener`, listeners, pub/sub
- [ ] **Template Method** — `JdbcTemplate`, `RestTemplate`, `AbstractController`
- [ ] **Chain of Responsibility** — Servlet filters, Spring Security filter chain, interceptors, validation pipelines
- [ ] **Command** — `Runnable`, undo/redo, job queues
- [ ] **State** — order lifecycle, vending machine, TCP connection
- [ ] **Iterator**, **Mediator** (chat room, `DispatcherServlet`), **Memento** (undo), **Visitor** (AST, double dispatch), **Interpreter** (SpEL — P2), **Null Object**

### 6.4 Enterprise / Application Patterns
- [ ] Layered: Controller → Service → Repository; DTO vs Entity vs Domain model; mappers
- [ ] **Repository, DAO, Unit of Work, Identity Map, Lazy Load** (Fowler PoEAA)
- [ ] **Specification pattern**, **Pipeline/Filter**, **Rules engine** pattern
- [ ] **Dependency Injection & IoC**, Service Locator (anti-pattern)
- [ ] **Event-driven in-process design** (domain events)
- [ ] **Retry, circuit breaker, idempotency** as LLD components

### 6.5 LLD Problems to Practice (design classes + key methods + concurrency + extensibility)
- [ ] Parking Lot (multi-level, spot types, pricing strategy, concurrency on spot allocation)
- [ ] Elevator System (scheduling algorithms, state machine)
- [ ] Vending Machine (State pattern)
- [ ] ATM (State + Chain of Responsibility for cash dispensing)
- [ ] Library Management System
- [ ] Splitwise / Expense Sharing (balance simplification)
- [ ] BookMyShow / Movie Ticket Booking (seat locking, concurrency, expiry)
- [ ] Hotel / Meeting Room Booking, Calendar scheduler
- [ ] Snake & Ladder, Tic-Tac-Toe, Chess (move validation)
- [ ] LRU/LFU Cache with pluggable eviction policy & TTL
- [ ] **Rate Limiter** (pluggable algorithms: token bucket, sliding window)
- [ ] Logger framework (levels, appenders, chain of responsibility, async)
- [ ] In-memory Pub-Sub / Message Queue (topics, consumers, offsets, retries)
- [ ] Task Scheduler / Cron / Delayed job executor
- [ ] Ride Sharing (Uber) — matching strategy, trip state machine
- [ ] Food Delivery (Swiggy/Zomato) — order lifecycle, assignment
- [ ] E-commerce Cart & Inventory, Coupon/Discount engine
- [ ] Payment system / Digital Wallet (idempotency, ledger)
- [ ] Notification Service (channels via Strategy, templates, retries)
- [ ] In-memory Key-Value store with TTL & transactions
- [ ] In-memory File System (Composite)
- [ ] Stack Overflow / Q&A, Social network feed
- [ ] Traffic Signal controller, Car Rental, Amazon Locker, Coffee Machine
- [ ] Stock Exchange order-matching engine (order book with price-time priority)
- [ ] Circuit Breaker, Event Bus, Workflow engine, Feature-flag system, Job retry framework
- [ ] URL Shortener (LLD view), Distributed ID generator (Snowflake)

### 6.6 LLD Interview Approach
- [ ] Clarify requirements & scope; list use cases and actors
- [ ] Identify core entities, relationships, enums, and state machines
- [ ] Define interfaces/APIs of key services
- [ ] Draw class diagram; apply patterns only where they earn their place
- [ ] Address concurrency (which operations race? lock granularity?)
- [ ] Code key flows; discuss extensibility (new vehicle type, new pricing rule) and testing

---

## 7. Machine Coding Round (P0 for product companies)

- [ ] **Format** — 90–120 min to build a working, runnable, in-memory application (e.g., Splitwise, Snake & Ladder, parking lot, cab booking, rate limiter, KV store)
- [ ] **Evaluation criteria** — working code > perfect design; modularity; extensibility; readability; separation of concerns; SOLID; handling edge cases; concurrency awareness; tests/demo driver
- [ ] **Prepared skeleton** in your head — `model/`, `service/`, `repository/` (in-memory maps), `strategy/`, `exception/`, `Main` driver
- [ ] **Time plan** — 10 min requirements & design, 70 min code, 15 min test/demo, 5 min refactor
- [ ] **Practice set** — build 8–10 problems end-to-end under a timer
- [ ] **Common gotchas** — no input validation, God classes, hard-coded strategies, not thread-safe repositories (`ConcurrentHashMap`), missing custom exceptions

---

# PART C — SPRING ECOSYSTEM

## 8. Spring Framework Core (P0)

### 8.1 IoC & Dependency Injection
- [ ] **IoC vs DI** concepts; why containers exist
- [ ] **BeanFactory vs ApplicationContext** (eager init, events, i18n, AOP integration)
- [ ] **Injection types** — constructor (preferred: immutability, required deps, testability), setter (optional deps), field (avoid)
- [ ] **Stereotypes** — `@Component`, `@Service`, `@Repository` (persistence exception translation), `@Controller`/`@RestController`
- [ ] **Java config** — `@Configuration` + `@Bean`; full mode (CGLIB proxied, `proxyBeanMethods=true`) vs lite mode; `@Import`, `@ComponentScan`, `@PropertySource`
- [ ] **Autowiring resolution** — by type → `@Qualifier` → `@Primary` → by name; `@Priority`; injecting `List<T>`/`Map<String,T>` of all implementations (Strategy pattern); `Optional<T>`, `ObjectProvider<T>`
- [ ] **Circular dependencies** — why constructor injection fails fast, Boot 2.6+ prohibits by default, fixes: redesign, `@Lazy`, events, setter injection (last resort)
- [ ] **Bean scopes** — singleton (default, not thread-safe by itself), prototype, request, session, application, websocket; custom scopes; thread scope
- [ ] **Prototype-in-singleton problem** — solutions: `ObjectProvider`, `@Lookup` method injection, scoped proxy (`proxyMode = TARGET_CLASS`)
- [ ] **Stateless singletons** — why shared mutable state in beans is a concurrency bug

### 8.2 Bean Lifecycle (be able to draw it)
- [ ] Instantiate → populate properties → `BeanNameAware`/`BeanFactoryAware`/`ApplicationContextAware` → `BeanPostProcessor#postProcessBeforeInitialization` → `@PostConstruct` → `InitializingBean#afterPropertiesSet` → custom `init-method` → `BeanPostProcessor#postProcessAfterInitialization` (**AOP proxies created here**) → bean in use → `@PreDestroy` → `DisposableBean#destroy` → `destroy-method`
- [ ] **BeanFactoryPostProcessor vs BeanPostProcessor** (modify definitions vs modify instances); `PropertySourcesPlaceholderConfigurer`
- [ ] **BeanDefinitionRegistryPostProcessor**, `ImportBeanDefinitionRegistrar` (how `@EnableXxx` works)
- [ ] **FactoryBean** (`&beanName`), `SmartInitializingSingleton`, `SmartLifecycle` (phased start/stop)
- [ ] `@Lazy`, `@DependsOn`, `@Order`/`Ordered`
- [ ] **ApplicationContext refresh() steps** (high-level)

### 8.3 Configuration, Environment & Conditions
- [ ] **Environment & PropertySources** hierarchy; `@Value("${...}")`, defaults, SpEL `#{...}`
- [ ] **Profiles** — `@Profile`, `spring.profiles.active`, profile-specific config
- [ ] **`@Conditional`** and custom `Condition` (foundation of Boot auto-config)
- [ ] **Type conversion** — `ConversionService`, `Converter`, `Formatter`
- [ ] **Resource abstraction** — `classpath:`, `file:`, `ResourceLoader`
- [ ] **MessageSource** & i18n

### 8.4 Events
- [ ] `ApplicationEventPublisher`, `@EventListener`, ordering, conditional listeners
- [ ] **Synchronous by default**; `@Async` listeners
- [ ] **`@TransactionalEventListener`** — phases (BEFORE_COMMIT, AFTER_COMMIT, AFTER_ROLLBACK, AFTER_COMPLETION); why AFTER_COMMIT is used to publish to Kafka/send emails; caveat: writes in AFTER_COMMIT listener need REQUIRES_NEW
- [ ] Built-in events — ContextRefreshed, ApplicationReady, ContextClosed

### 8.5 Validation
- [ ] **Bean Validation (Jakarta Validation / Hibernate Validator)** — `@NotNull`, `@NotBlank`, `@Size`, `@Pattern`, `@Email`, `@Positive`, `@Future`, nested `@Valid`
- [ ] `@Valid` vs `@Validated` (groups, method-level validation on services)
- [ ] Custom constraint annotations + `ConstraintValidator`; cross-field validation
- [ ] Validation groups & sequences

### 8.6 AOP (P0 — explains half of Spring's "magic")
- [ ] **Concepts** — aspect, join point, pointcut, advice, target, proxy, weaving, introduction
- [ ] **Advice types** — `@Before`, `@After`, `@AfterReturning`, `@AfterThrowing`, `@Around` (`ProceedingJoinPoint.proceed()`)
- [ ] **Pointcut expressions** — `execution(...)`, `within`, `@annotation`, `bean()`, combining
- [ ] **Spring AOP (runtime proxies, method-level only) vs AspectJ (compile/load-time weaving, fields/constructors)**
- [ ] **JDK dynamic proxy vs CGLIB** — interface-based vs subclass; Boot defaults to CGLIB (`proxyTargetClass=true`); final classes/methods can't be proxied
- [ ] **Self-invocation problem** — calling `this.method()` bypasses the proxy → `@Transactional`, `@Async`, `@Cacheable`, `@Retryable`, `@PreAuthorize` silently don't apply; fixes: move to another bean, self-injection, `AopContext.currentProxy()`, AspectJ mode
- [ ] **Private methods** are never advised
- [ ] **Aspect ordering** — `@Order`
- [ ] **Use cases** — logging, metrics/timing, auditing, security, transactions, retries, caching, multi-tenancy, idempotency guard

### 8.7 Spring Framework 6 / 7 Changes
- [ ] **Spring 6 / Boot 3** — Java 17 baseline, `javax.*` → `jakarta.*`, AOT processing & GraalVM native, Micrometer Observation API, `RestClient`, `JdbcClient`, HTTP interface clients (`@HttpExchange`), `ProblemDetail` (RFC 7807/9457), virtual-thread support
- [ ] **Spring 7 / Boot 4 (late 2025)** — Jakarta EE 11, JSpecify null-safety annotations, first-class API versioning, built-in resilience annotations (`@Retryable`, `@ConcurrencyLimit`), Jackson 3, more modular auto-configuration — awareness level, know what changed if asked about upgrades

### 🎯 Frequently Asked — Spring Core
- Explain the bean lifecycle. Where are proxies created?
- Why doesn't `@Transactional` work when called from the same class?
- Constructor vs field injection — which and why?
- How do you inject a prototype bean into a singleton?
- How would you choose between multiple implementations of an interface at runtime?
- How does `@Configuration` differ from `@Component` with `@Bean` methods?

---

## 9. Spring Boot (P0)

### 9.1 Auto-Configuration
- [ ] **`@SpringBootApplication`** = `@SpringBootConfiguration` + `@EnableAutoConfiguration` + `@ComponentScan`
- [ ] **How auto-config is discovered** — `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (previously `spring.factories`)
- [ ] **Conditional annotations** — `@ConditionalOnClass`, `@ConditionalOnMissingBean` (lets you override), `@ConditionalOnProperty`, `@ConditionalOnBean`, `@ConditionalOnWebApplication`, `@ConditionalOnResource`
- [ ] **Debugging auto-config** — `--debug` / conditions evaluation report, `/actuator/conditions`
- [ ] **Excluding auto-configs** — `exclude = DataSourceAutoConfiguration.class`
- [ ] **Writing a custom starter** — autoconfigure module + starter module, `@AutoConfiguration`, `@ConfigurationProperties`, ordering (`before`/`after`)

### 9.2 Startup Flow
- [ ] `SpringApplication.run()` — bootstrap context → environment preparation → banner → create ApplicationContext → refresh (bean creation, embedded server start) → `CommandLineRunner`/`ApplicationRunner` → `ApplicationReadyEvent`
- [ ] `ApplicationContextInitializer`, `SpringApplicationRunListener`, `EnvironmentPostProcessor`
- [ ] **Startup time optimization** — lazy init, fewer starters, AOT, CDS, native image, `ApplicationStartup` tracking

### 9.3 Externalized Configuration
- [ ] **Precedence order** — command-line args > `SPRING_APPLICATION_JSON` > OS env vars > profile-specific `application-{profile}.yml` > `application.yml` > `@PropertySource` > defaults
- [ ] **Relaxed binding** (`MY_APP_TIMEOUT` → `my.app.timeout`)
- [ ] **`@ConfigurationProperties`** (type-safe, validated with `@Validated`, immutable via constructor binding/records) vs `@Value`
- [ ] **Profiles & profile groups**, `spring.config.import`, multi-document YAML, `spring.config.activate.on-profile`
- [ ] **Secrets** — never in git; env vars, Vault, AWS Secrets Manager, K8s Secrets; config refresh

### 9.4 Embedded Servers & Tuning
- [ ] Tomcat (default), Jetty, Undertow, Netty (WebFlux)
- [ ] **Tomcat thread model** — `server.tomcat.threads.max` (200), `min-spare`, `accept-count`, `max-connections`, `connection-timeout`, NIO connector
- [ ] **Graceful shutdown** — `server.shutdown=graceful`, `spring.lifecycle.timeout-per-shutdown-phase`; K8s preStop interplay
- [ ] HTTP/2, compression, SSL config, `server.forward-headers-strategy` behind a proxy

### 9.5 Actuator (P0 for production readiness)
- [ ] Endpoints — `health`, `info`, `metrics`, `prometheus`, `env`, `configprops`, `beans`, `mappings`, `loggers` (change log level at runtime), `threaddump`, `heapdump`, `httpexchanges`, `conditions`, `scheduledtasks`
- [ ] **Health groups** — `liveness` vs `readiness` probes for Kubernetes; why DB down should fail readiness, not liveness
- [ ] **Custom HealthIndicator, InfoContributor, custom endpoints**
- [ ] **Securing actuator** — separate management port, expose minimal endpoints
- [ ] **Micrometer integration** — auto JVM/HTTP/DB pool metrics, common tags

### 9.6 Logging
- [ ] Logback default; `logback-spring.xml`, springProfile blocks
- [ ] Log levels per package, runtime change via actuator
- [ ] **Structured logging** (JSON — built in since Boot 3.4: ECS/Logstash/GELF formats)
- [ ] **MDC** with traceId/spanId (Micrometer Tracing adds automatically)
- [ ] Async appenders, log rotation, not logging PII

### 9.7 Packaging & Deployment
- [ ] **Executable fat JAR** layout (`BOOT-INF/classes`, `BOOT-INF/lib`, launcher), WAR deployment (legacy)
- [ ] **Layered JARs** for Docker layer caching; Cloud Native Buildpacks (`spring-boot:build-image`)
- [ ] **GraalVM native images** — fast startup, lower memory; limits (reflection, build time, dynamic proxies)
- [ ] **Docker Compose support** & **Testcontainers at dev time** (`@ServiceConnection`)
- [ ] DevTools (restart, live reload) — dev only

### 🎯 Frequently Asked — Spring Boot
- How does auto-configuration work internally? How would you override an auto-configured bean?
- How would you build a custom starter used across 30 microservices?
- Liveness vs readiness — what should each check?
- How do you manage configs/secrets across environments?
- How do you make a Boot service start faster / use less memory?

---

## 10. Spring Web MVC & REST (P0)

### 10.1 Request Processing
- [ ] **Servlet fundamentals** — container, Servlet lifecycle, filters, listeners, thread-per-request
- [ ] **DispatcherServlet flow** — Filter chain → DispatcherServlet → HandlerMapping → HandlerExecutionChain (interceptors `preHandle`) → HandlerAdapter → argument resolvers → controller → return value handlers / `HttpMessageConverter` → `postHandle` → `afterCompletion` → exception resolvers
- [ ] **Filter vs HandlerInterceptor vs AOP** — what each can see and when to use (auth/CORS/logging in filter; handler-aware logic in interceptor; business cross-cutting in AOP); `OncePerRequestFilter`

### 10.2 Controllers
- [ ] `@RestController` vs `@Controller` + `@ResponseBody`
- [ ] `@RequestMapping`, `@GetMapping`/`@PostMapping`/`@PutMapping`/`@PatchMapping`/`@DeleteMapping`
- [ ] `@PathVariable`, `@RequestParam`, `@RequestBody`, `@RequestHeader`, `@CookieValue`, `@ModelAttribute`, `@MatrixVariable` (P2)
- [ ] `ResponseEntity`, `@ResponseStatus`, `Location` header on 201
- [ ] **Content negotiation**, `produces`/`consumes`, custom `HttpMessageConverter`
- [ ] **Custom argument resolvers** (`HandlerMethodArgumentResolver`) — e.g., inject current user/tenant
- [ ] **Validation** — `@Valid @RequestBody`, `MethodArgumentNotValidException`, `@Validated` for path/query params

### 10.3 Error Handling
- [ ] `@ExceptionHandler`, `@RestControllerAdvice` (global), ordering of advices
- [ ] `ResponseStatusException`, `ResponseEntityExceptionHandler`
- [ ] **ProblemDetail** (RFC 9457) responses; consistent error contract (code, message, traceId, field errors)
- [ ] Don't leak stack traces; map domain exceptions → HTTP status

### 10.4 Advanced Web Topics
- [ ] **CORS** — global `WebMvcConfigurer` vs `@CrossOrigin`; preflight; CORS with Spring Security
- [ ] **File upload/download** — multipart limits, streaming large files (`StreamingResponseBody`, `Resource`), pre-signed S3 URLs instead of proxying
- [ ] **Async request processing** — `Callable`, `DeferredResult`, `CompletableFuture` return types, `SseEmitter` (server-sent events), `ResponseBodyEmitter`
- [ ] **Pagination & sorting** — `Pageable`, `Page` vs `Slice`, max page size
- [ ] **API versioning** — URI, header, media type (built-in support in Spring 7)
- [ ] **OpenAPI** — springdoc-openapi, API-first with OpenAPI Generator
- [ ] **HATEOAS** (Spring HATEOAS) — P2
- [ ] **Idempotency** filter/interceptor for POST with `Idempotency-Key`
- [ ] **Request/response logging**, correlation-ID filter
- [ ] **WebSocket & STOMP** — `@MessageMapping`, broker relay, scaling with sticky sessions + pub/sub — P1

### 10.5 HTTP Clients (P0 — every service calls other services)
- [ ] **RestTemplate** (maintenance mode) vs **RestClient** (Spring 6.1+, sync fluent) vs **WebClient** (reactive) vs **HTTP interface `@HttpExchange`** vs **OpenFeign**
- [ ] **Timeouts** — connect, read/response, connection-pool acquire; never use defaults (often infinite)
- [ ] **Connection pooling** — Apache HttpClient 5 / Reactor Netty pool: max total, max per route, idle eviction, keep-alive
- [ ] **Error handling** — `onStatus`, `ResponseErrorHandler`, mapping 4xx/5xx
- [ ] **Retries** — only idempotent requests, backoff + jitter (Resilience4j / Spring Retry)
- [ ] **Propagating headers** — auth tokens, trace context, correlation IDs
- [ ] **Interceptors** — `ClientHttpRequestInterceptor`, `ExchangeFilterFunction`

### 🎯 Frequently Asked — Web
- Walk me through what happens from the moment a request hits Tomcat until JSON is returned
- Filter vs Interceptor — give a use case for each
- How do you design global error handling for 20 microservices consistently?
- How do you handle a 2 GB file upload?
- How do you configure timeouts and retries for downstream calls?

---

## 11. Reactive: Spring WebFlux & Project Reactor (P1)

- [ ] **Why reactive** — Reactive Manifesto, non-blocking I/O, fewer threads, event loop (Netty)
- [ ] **Reactive Streams spec** — Publisher, Subscriber, Subscription, Processor; **backpressure** via `request(n)`
- [ ] **Mono vs Flux**; nothing happens until you subscribe; cold vs hot publishers; `share`, `cache`, `Sinks`
- [ ] **Operators** — `map`, `flatMap` (concurrent, unordered), `concatMap` (ordered), `switchMap`, `filter`, `zip`, `merge`, `concat`, `collectList`, `buffer`, `window`, `groupBy`, `delayElements`, `timeout`
- [ ] **Error handling** — `onErrorResume`, `onErrorReturn`, `onErrorMap`, `retryWhen(Retry.backoff(...))`, `doOnError`
- [ ] **Schedulers** — `publishOn` vs `subscribeOn`; `boundedElastic` for wrapping blocking calls; `parallel`
- [ ] **Never block the event loop** — BlockHound to detect
- [ ] **Context propagation** — Reactor `Context` vs ThreadLocal; MDC/tracing in reactive chains
- [ ] **WebFlux** — annotated controllers vs functional endpoints (`RouterFunction`/`HandlerFunction`), `WebClient`, `WebFilter`
- [ ] **Reactive data** — R2DBC, reactive MongoDB/Redis/Cassandra; reactive transactions
- [ ] **Debugging** — `checkpoint()`, `log()`, `Hooks.onOperatorDebug()`, ReactorDebugAgent
- [ ] **Testing** — `StepVerifier`, `WebTestClient`, virtual time
- [ ] **Decision: MVC + virtual threads vs WebFlux** — team skills, debuggability, ecosystem (JDBC/JPA blocking), streaming needs, gateway use cases (Spring Cloud Gateway is reactive)
- [ ] **Kotlin coroutines** with Spring — P2

---

## 12. Data Access: JDBC, JPA, Hibernate, Spring Data (P0)

### 12.1 JDBC & Connection Pooling
- [ ] JDBC basics — `DataSource`, `Connection`, `PreparedStatement` (SQL injection prevention, statement caching), `ResultSet`, batch updates
- [ ] `JdbcTemplate`, `NamedParameterJdbcTemplate`, `JdbcClient` (6.1), `RowMapper`, `SimpleJdbcInsert`
- [ ] **HikariCP** — `maximumPoolSize` (small! ~ cores×2 + spindles as a starting point), `minimumIdle`, `connectionTimeout`, `idleTimeout`, `maxLifetime` (< DB/firewall timeout), `leakDetectionThreshold`
- [ ] **Pool exhaustion** — symptoms (`Connection is not available, request timed out`), causes (long transactions, remote calls inside transactions, leaks, too many app instances × pool size > DB `max_connections`)
- [ ] **Total connections math** across replicas/pods; PgBouncer/RDS Proxy

### 12.2 JPA / Hibernate Core
- [ ] **ORM concepts** — impedance mismatch, when NOT to use an ORM (bulk/reporting)
- [ ] **EntityManager & Persistence Context** — first-level cache, identity guarantee, scope = transaction
- [ ] **Entity states** — transient, managed, detached, removed; `persist` vs `merge` vs `save` (Spring Data `isNew` logic) vs `update`
- [ ] **Dirty checking**, write-behind, **flush modes** (AUTO, COMMIT), flush ordering
- [ ] **ID generation** — IDENTITY (disables JDBC batch inserts), SEQUENCE (pooled/pooled-lo optimizers, `allocationSize`), TABLE (avoid), UUID (v4 vs time-ordered v7 for index locality)
- [ ] **Associations** — `@OneToOne`, `@OneToMany`, `@ManyToOne`, `@ManyToMany`; owning side vs inverse (`mappedBy`); `@JoinColumn` vs join table; unidirectional `@OneToMany` pitfalls; bidirectional sync helper methods
- [ ] **Cascade types** & `orphanRemoval`; dangers of `CascadeType.ALL` on `@ManyToOne`/`@ManyToMany`
- [ ] **Fetch types** — defaults (`*ToOne` EAGER, `*ToMany` LAZY); make everything LAZY
- [ ] **LazyInitializationException** — causes and correct fixes (fetch in query, DTO projection) vs wrong fixes (EAGER, OSIV)
- [ ] **Open Session In View** — why to disable (`spring.jpa.open-in-view=false`)
- [ ] **N+1 select problem** — detection (SQL logs, Hibernate statistics, datasource-proxy, tests asserting query count) and fixes: `JOIN FETCH`, `@EntityGraph`, `@BatchSize`/`default_batch_fetch_size`, DTO projections, subselect fetch
- [ ] **MultipleBagFetchException** / Cartesian product — use `Set` or multiple queries
- [ ] **Pagination + fetch join** → in-memory pagination warning (HHH90003004); two-query approach (ids then fetch)
- [ ] **Inheritance mapping** — `SINGLE_TABLE`, `JOINED`, `TABLE_PER_CLASS`, `@MappedSuperclass`; trade-offs
- [ ] **Embeddables** (`@Embeddable`/`@Embedded`), `@ElementCollection`, `AttributeConverter`, enums (`EnumType.STRING` always)
- [ ] **equals/hashCode for entities** — business key or id-based with null handling; Lombok `@Data` danger
- [ ] **Locking** — optimistic (`@Version`, `OptimisticLockException` → retry), pessimistic (`@Lock(PESSIMISTIC_WRITE)` → `SELECT … FOR UPDATE`, lock timeouts, `SKIP LOCKED` for job queues)
- [ ] **Second-level cache** — regions, concurrency strategies (READ_ONLY, NONSTRICT_READ_WRITE, READ_WRITE, TRANSACTIONAL), query cache pitfalls, providers (Ehcache/JCache, Hazelcast, Infinispan, Redis via Redisson)
- [ ] **Querying** — JPQL, Criteria API, native SQL, named queries; `@SqlResultSetMapping`; window functions & CTEs in Hibernate 6
- [ ] **Projections** — interface-based, class/record DTO (`select new ...`), Tuple
- [ ] **Bulk operations** — `@Modifying` JPQL updates bypass persistence context (`clearAutomatically`, `flushAutomatically`)
- [ ] **Batching** — `hibernate.jdbc.batch_size`, `order_inserts`, `order_updates`; `StatelessSession` for bulk; periodic `flush()`+`clear()` in loops
- [ ] **Lifecycle callbacks** — `@PrePersist`, `@PreUpdate`, entity listeners
- [ ] **Auditing** — Spring Data `@CreatedDate`/`@LastModifiedBy` + `@EnableJpaAuditing`; Hibernate Envers for history
- [ ] **Soft deletes** — `@SQLDelete` + `@SQLRestriction` (Hibernate 6.3+ `@SoftDelete`)
- [ ] **Read-only queries** — `@Transactional(readOnly = true)`, query hints, skipping dirty checking
- [ ] **Hibernate statistics & slow query logging**

### 12.3 Spring Data
- [ ] **Repository hierarchy** — `Repository` → `CrudRepository`/`ListCrudRepository` → `PagingAndSortingRepository` → `JpaRepository`
- [ ] **Derived query methods** (`findByEmailAndStatusOrderByCreatedAtDesc`), limits of naming
- [ ] `@Query` (JPQL/native), `@Param`, SpEL in queries
- [ ] **Specifications** (dynamic filters), **QueryDSL**, **Query by Example**
- [ ] **Pagination** — `Page` (extra count query cost) vs `Slice` vs keyset/**Scroll API** (`Window`, `KeysetScrollPosition`)
- [ ] **Custom repository fragments** (`XxxRepositoryCustom` + `Impl`)
- [ ] **`save()` semantics** — `isNew` check, assigned IDs causing `merge` + extra SELECT, `Persistable`
- [ ] **Projections & DTOs**, `@EntityGraph` on repo methods
- [ ] **Spring Data modules** — MongoDB, Redis, Elasticsearch, Cassandra, R2DBC, JDBC (aggregate-oriented, no lazy loading), Spring Data REST (P2)

### 12.4 Schema & Data Management
- [ ] **Migrations** — Flyway (versioned & repeatable scripts) / Liquibase (changelogs); never `ddl-auto=update` in prod
- [ ] **Zero-downtime schema changes** — expand → migrate → contract; backward-compatible deploys; renaming columns safely; large table backfills in batches
- [ ] **Multiple datasources**, **read/write splitting** (`AbstractRoutingDataSource` + `@Transactional(readOnly)`), replica lag
- [ ] **Multi-tenancy** — database-per-tenant, schema-per-tenant, discriminator column (Hibernate `@TenantId`); tenant resolution & isolation

### 🎯 Frequently Asked — JPA/Hibernate
- What is the N+1 problem and how do you fix it? How do you detect it?
- Explain the persistence context and dirty checking
- `persist` vs `merge`; why does `save()` sometimes fire a SELECT first?
- Optimistic vs pessimistic locking — give a real scenario for each
- Why does IDENTITY generation break batch inserts?
- How do you load 1 million rows without running out of memory?
- What problems have you faced with Hibernate in production?

---

## 13. Transactions (P0)

- [ ] **ACID** — what each letter means and how DBs implement it (WAL, locks, MVCC)
- [ ] **Spring transaction abstraction** — `PlatformTransactionManager` (`DataSourceTransactionManager`, `JpaTransactionManager`, `JtaTransactionManager`), `ReactiveTransactionManager`
- [ ] **Declarative (`@Transactional`) vs programmatic (`TransactionTemplate`)** — when to use programmatic (fine-grained scope, avoid holding connection during remote calls)
- [ ] **How `@Transactional` works** — AOP proxy → `TransactionInterceptor` → bind connection to thread (`TransactionSynchronizationManager`) → commit/rollback
- [ ] **Propagation** — `REQUIRED` (default), `REQUIRES_NEW` (suspends outer; audit logs), `NESTED` (savepoints, JDBC only), `SUPPORTS`, `NOT_SUPPORTED`, `MANDATORY`, `NEVER` — explain each with a use case
- [ ] **Isolation levels** — READ_UNCOMMITTED, READ_COMMITTED, REPEATABLE_READ, SERIALIZABLE; anomalies: dirty read, non-repeatable read, phantom read, **lost update**, **write skew**; DB defaults (Postgres = RC, MySQL InnoDB = RR)
- [ ] **Rollback rules** — rolls back on unchecked exceptions and `Error` only; **checked exceptions commit** unless `rollbackFor`; `noRollbackFor`
- [ ] **`UnexpectedRollbackException`** — inner REQUIRED method marked rollback-only, outer caught the exception
- [ ] **`readOnly = true`** — flush mode MANUAL, no dirty checking, may route to replica; not a security guarantee
- [ ] **Timeouts** — `@Transactional(timeout = …)`
- [ ] **Pitfalls** — self-invocation; private/final methods; swallowing exceptions; `@Transactional` on controllers; long transactions holding locks & connections; **remote HTTP/Kafka calls inside a DB transaction**; `@Async` + `@Transactional` on the same method; transactions in tests (rollback hides flush bugs)
- [ ] **Transaction synchronization** — `TransactionSynchronization#afterCommit`, `@TransactionalEventListener`
- [ ] **Distributed transactions** — JTA/XA & 2PC (why most teams avoid them) → Saga, Outbox, idempotent consumers (see §21–22)
- [ ] **Kafka + DB consistency** — dual-write problem; `ChainedTransactionManager` (deprecated); outbox is the answer

### 🎯 Frequently Asked — Transactions
- Explain all propagation types; when did you use REQUIRES_NEW?
- A checked exception was thrown but data committed — why?
- How do you prevent lost updates when two users edit the same record?
- How do you keep a DB write and a Kafka publish consistent?
- What isolation level does your system use and why?

---

## 14. Spring Security, AuthN & AuthZ (P0)

### 14.1 Spring Security Architecture
- [ ] **Filter-based design** — `DelegatingFilterProxy` → `FilterChainProxy` → one or more `SecurityFilterChain`s (matched by request matcher)
- [ ] **Important filters & order** — CORS, CSRF, logout, authentication filters (UsernamePassword, BearerToken, Basic), `SecurityContextHolderFilter`, `ExceptionTranslationFilter`, `AuthorizationFilter`
- [ ] **SecurityContextHolder** — ThreadLocal strategy, `MODE_INHERITABLETHREADLOCAL`, propagating to `@Async`/executors (`DelegatingSecurityContextExecutor`)
- [ ] **Authentication flow** — `Authentication` → `AuthenticationManager` (`ProviderManager`) → `AuthenticationProvider`s → `UserDetailsService` + `PasswordEncoder`
- [ ] **PasswordEncoder** — BCrypt (cost factor), Argon2, SCrypt, `DelegatingPasswordEncoder` (`{bcrypt}` prefix) for migrations
- [ ] **Configuration** — `SecurityFilterChain` bean with lambda DSL (`WebSecurityConfigurerAdapter` removed in 6)
- [ ] **Authorization** — `authorizeHttpRequests` + `requestMatchers`; `AuthorizationManager`; roles vs authorities (`ROLE_` prefix); role hierarchy
- [ ] **Method security** — `@EnableMethodSecurity`, `@PreAuthorize("hasRole('ADMIN') or #id == authentication.name")`, `@PostAuthorize`, `@PostFilter`, `@Secured`, custom `PermissionEvaluator`
- [ ] **401 vs 403** — `AuthenticationEntryPoint` vs `AccessDeniedHandler`
- [ ] **CSRF** — what it is, synchronizer token, `SameSite` cookies; why it's usually disabled for stateless bearer-token APIs (and when it must not be)
- [ ] **CORS** with Security (must be configured in the chain)
- [ ] **Session management** — stateless (`SessionCreationPolicy.STATELESS`), session fixation protection, concurrent session control, Spring Session (Redis)
- [ ] **Security headers** — HSTS, X-Content-Type-Options, X-Frame-Options, CSP
- [ ] **Testing** — `@WithMockUser`, `@WithUserDetails`, `SecurityMockMvcRequestPostProcessors.jwt()`

### 14.2 Authentication Mechanisms
- [ ] **Session/cookie vs token-based** auth — trade-offs (revocation, scaling, CSRF, mobile)
- [ ] **HTTP Basic, form login, API keys** (hashing stored keys, rotation, scoping)
- [ ] **JWT** — structure (header.payload.signature), base64url (not encryption), standard claims (`iss`, `sub`, `aud`, `exp`, `iat`, `nbf`, `jti`), signing algorithms (HS256 shared secret vs RS256/ES256 asymmetric), `alg:none` & algorithm confusion attacks, validation checklist
- [ ] **JWT lifecycle** — short-lived access tokens + refresh tokens, refresh token rotation & reuse detection, revocation strategies (short TTL, denylist by `jti`, token version per user), logout semantics
- [ ] **Where to store tokens in browsers** — HttpOnly Secure SameSite cookies vs localStorage (XSS risk); BFF pattern
- [ ] **JWKS endpoints & key rotation** (`kid` header)
- [ ] **JWS vs JWE**; opaque tokens + introspection (RFC 7662) vs self-contained JWTs
- [ ] **OAuth 2.0** — roles (resource owner, client, authorization server, resource server); grants: **Authorization Code + PKCE** (web/mobile/SPA), **Client Credentials** (service-to-service), Device Code, Refresh Token; deprecated: Implicit, Password (ROPC); scopes & consent; OAuth 2.1 consolidation
- [ ] **OpenID Connect** — ID token vs access token, UserInfo, discovery (`.well-known/openid-configuration`), nonce, SSO
- [ ] **Spring implementations** — OAuth2 Resource Server (JWT/opaque), OAuth2 Client (login, `WebClient` token relay), **Spring Authorization Server**
- [ ] **Identity providers** — Keycloak, Okta, Auth0, AWS Cognito, Azure Entra ID; SAML 2.0 (enterprise SSO) awareness
- [ ] **Service-to-service auth** — client credentials JWT, mTLS, SPIFFE/SPIRE (P2), token exchange (RFC 8693) for user context propagation
- [ ] **MFA/2FA** (TOTP), **Passkeys/WebAuthn** (supported in Spring Security 6.4+), magic links/one-time tokens

### 14.3 Authorization Models
- [ ] **RBAC** (roles), **ABAC** (attributes/policies), **ReBAC** (relationship-based — Google Zanzibar, OpenFGA, SpiceDB)
- [ ] **Policy engines** — OPA/Rego, AWS Cedar (P2)
- [ ] **Multi-tenant authorization** — tenant isolation in every query, row-level security (Postgres RLS)
- [ ] **Object-level authorization (prevent IDOR/BOLA)** — never trust IDs from the client

### 🎯 Frequently Asked — Security
- Explain the Spring Security filter chain and how a JWT request is authenticated
- Session vs JWT — how do you revoke a JWT?
- Walk through the OAuth2 Authorization Code + PKCE flow
- How do services authenticate each other in your architecture?
- How do you store passwords? Why BCrypt over SHA-256?

---

## 15. Spring Cloud & Microservices Infrastructure (P0)

### 15.1 Configuration
- [ ] **Spring Cloud Config Server** — Git/Vault backends, encryption, `@RefreshScope`, `/actuator/refresh`, Spring Cloud Bus for broadcast refresh
- [ ] **Kubernetes-native config** — ConfigMaps/Secrets mounted as files/env, Spring Cloud Kubernetes (P2)
- [ ] **Vault integration** — dynamic DB credentials, lease renewal

### 15.2 Service Discovery & Load Balancing
- [ ] **Client-side discovery** (Eureka + Spring Cloud LoadBalancer) vs **server-side** (K8s Services, AWS ALB)
- [ ] Eureka — registration, heartbeats, self-preservation mode, eventual consistency
- [ ] Consul, ZooKeeper (awareness)
- [ ] Spring Cloud LoadBalancer (Ribbon is dead), algorithms, zone preference
- [ ] **In Kubernetes** you usually don't need Eureka — DNS-based discovery

### 15.3 API Gateway
- [ ] **Spring Cloud Gateway** — routes, predicates (path, host, header, method, weight), filters (rewrite path, add headers, retry, circuit breaker, **RequestRateLimiter** with Redis token bucket), global filters, reactive (Netty) vs Server MVC variant
- [ ] Gateway responsibilities — routing, authentication/token validation, rate limiting, request/response transformation, aggregation, CORS, TLS termination, canary routing
- [ ] **BFF (Backend for Frontend)** pattern
- [ ] Alternatives — Kong, NGINX, Envoy, AWS API Gateway, Apigee; Netflix Zuul (legacy)

### 15.4 Inter-Service Communication
- [ ] **OpenFeign** — declarative clients, `ErrorDecoder`, retries, timeouts, interceptors for auth headers, fallback with circuit breaker
- [ ] **WebClient / RestClient / HTTP interfaces**
- [ ] **Spring Cloud Stream** — binder abstraction (Kafka/RabbitMQ), functional model (`Supplier`/`Function`/`Consumer` beans), consumer groups, partitioning, DLQ
- [ ] **Spring Cloud Function** (serverless-friendly)

### 15.5 Resilience (Resilience4j)
- [ ] **CircuitBreaker** — states (CLOSED → OPEN → HALF_OPEN), count- vs time-based sliding window, `failureRateThreshold`, `slowCallRateThreshold`, `waitDurationInOpenState`, `permittedNumberOfCallsInHalfOpenState`, recorded vs ignored exceptions
- [ ] **Retry** — max attempts, exponential backoff with jitter, retry only on transient errors
- [ ] **RateLimiter**, **Bulkhead** (semaphore vs thread-pool), **TimeLimiter**
- [ ] **Decorator order** — Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( call ) ) ) ) ) and why
- [ ] **Fallbacks** — cached/default responses, degrade gracefully, don't hide failures
- [ ] **Spring Cloud CircuitBreaker** abstraction; Hystrix (deprecated) history
- [ ] **Metrics/events** from Resilience4j into Micrometer & alerting

### 15.6 Observability in Spring Cloud
- [ ] Spring Cloud Sleuth → **Micrometer Tracing** (Boot 3) with Brave or OpenTelemetry bridge; exporters (Zipkin, OTLP → Jaeger/Tempo)
- [ ] Trace propagation across HTTP, Kafka, `@Async`

### 15.7 Other Spring Cloud Projects
- [ ] **Spring Cloud Contract** — consumer-driven contract tests, stubs
- [ ] **Spring Cloud Vault**, **Spring Cloud Kubernetes**, **Spring Cloud Task / Data Flow** (P2), **Spring Cloud AWS** (SQS, SNS, S3, Parameter Store)

---

## 16. Other Spring Projects (P1)

### 16.1 Spring for Apache Kafka (P0 if you use Kafka)
- [ ] `KafkaTemplate` (sync vs async send, callbacks), `@KafkaListener`, `ConcurrentKafkaListenerContainerFactory` (concurrency ≤ partitions)
- [ ] **Ack modes** — RECORD, BATCH, MANUAL, MANUAL_IMMEDIATE; commit semantics
- [ ] **Error handling** — `DefaultErrorHandler` with `BackOff`, `DeadLetterPublishingRecoverer`, non-retryable exceptions, **`@RetryableTopic`** non-blocking retries (retry topics + DLT) and ordering trade-off
- [ ] **Deserialization errors** — `ErrorHandlingDeserializer` (poison pills)
- [ ] **Transactions & exactly-once** — `transactional.id`, `KafkaTransactionManager`, consume-process-produce
- [ ] Batch listeners, filtering, `@SendTo` replies, `ReplyingKafkaTemplate`
- [ ] Serialization — JSON (type headers, trusted packages), Avro/Protobuf with Schema Registry
- [ ] Testing — `@EmbeddedKafka`, Testcontainers Kafka

### 16.2 Spring AMQP (RabbitMQ)
- [ ] `RabbitTemplate`, `@RabbitListener`, declaring exchanges/queues/bindings, message converters
- [ ] Acknowledgement modes, prefetch, concurrency, DLX/DLQ, retry interceptors, publisher confirms & returns

### 16.3 Spring Batch
- [ ] **Concepts** — Job, Step, JobInstance, JobExecution, StepExecution, JobParameters, JobRepository
- [ ] **Chunk-oriented processing** — ItemReader → ItemProcessor → ItemWriter, commit interval
- [ ] **Tasklet steps**
- [ ] **Fault tolerance** — skip, retry, restartability from last committed chunk, idempotent writers
- [ ] **Scaling** — multi-threaded steps, parallel steps, partitioning (local/remote), remote chunking
- [ ] Readers/writers — `JdbcCursorItemReader`, `JdbcPagingItemReader`, `FlatFileItemReader`, `KafkaItemReader`
- [ ] Scheduling & triggering jobs; Spring Batch on K8s (Jobs/CronJobs)

### 16.4 Caching Abstraction
- [ ] `@EnableCaching`, `@Cacheable`, `@CachePut`, `@CacheEvict` (`allEntries`, `beforeInvocation`), `@Caching`, `@CacheConfig`
- [ ] Keys — default `SimpleKey`, SpEL keys, custom `KeyGenerator`; `condition`/`unless`; `sync = true` (stampede protection per node)
- [ ] Providers — Caffeine (local), Redis (`RedisCacheManager` with per-cache TTLs), JCache/Ehcache, Hazelcast
- [ ] Pitfalls — self-invocation, caching mutable objects, serializing entities, no TTL, caching nulls

### 16.5 Scheduling & Async
- [ ] `@EnableScheduling`, `@Scheduled(fixedRate | fixedDelay | cron, zone)`; default single-threaded scheduler → configure pool
- [ ] **Distributed scheduling** — multiple pods run the same job → ShedLock, Quartz clustered (JDBC JobStore), K8s CronJob, DB-based leader election
- [ ] `@EnableAsync`, `@Async` with custom `ThreadPoolTaskExecutor`, return `CompletableFuture`, `AsyncUncaughtExceptionHandler`, `TaskDecorator` for MDC/SecurityContext propagation, self-invocation pitfall

### 16.6 Retry
- [ ] **Spring Retry** — `@Retryable`, `@Recover`, `RetryTemplate`, backoff policies; Spring 7 core `@Retryable` / `@ConcurrencyLimit`

### 16.7 Spring Session
- [ ] Externalized HTTP sessions (Redis/JDBC) for horizontally scaled stateful apps

### 16.8 Spring Modulith (P1 — modular monoliths are trending)
- [ ] Application modules by package, verifying module boundaries, `@ApplicationModuleListener`, event publication registry (outbox-like), documentation generation

### 16.9 Spring for GraphQL
- [ ] Schema-first, `@QueryMapping`, `@MutationMapping`, `@SchemaMapping`, `@BatchMapping`/DataLoader (N+1), subscriptions, security

### 16.10 Spring AI (P1 in 2026)
- [ ] `ChatClient`, prompt templates, structured output to POJOs, chat memory, advisors
- [ ] Embeddings, `VectorStore` (pgvector, Redis, Pinecone…), ETL for documents, RAG
- [ ] Tool/function calling, MCP client/server support, observability of LLM calls
- [ ] Alternatives — LangChain4j

### 16.11 Others (awareness)
- [ ] Spring Integration (Enterprise Integration Patterns: channels, routers, splitters, aggregators)
- [ ] Spring State Machine, Spring Shell, Spring HATEOAS, Spring REST Docs, Spring Web Services (SOAP, legacy enterprise), Spring LDAP, Spring Vault, Spring Pulsar

### 16.12 Micrometer
- [ ] Meter types — `Counter`, `Gauge`, `Timer`, `DistributionSummary`, `LongTaskTimer`
- [ ] Tags/dimensions and **cardinality** control (never tag by userId/orderId)
- [ ] Percentiles vs histograms (`publishPercentileHistogram` for Prometheus aggregation), SLO buckets
- [ ] `@Timed`, `@Counted`, **Observation API** (one instrumentation → metrics + traces)
- [ ] Registries — Prometheus, Datadog, CloudWatch, OTLP

---

## 17. Testing in Java & Spring (P0)

### 17.1 Strategy
- [ ] **Test pyramid** vs testing trophy/honeycomb (microservices favour integration tests)
- [ ] Unit vs integration vs component vs contract vs end-to-end vs smoke vs regression
- [ ] **Test doubles** — dummy, stub, spy, mock, fake (in-memory repo)
- [ ] **TDD** (red-green-refactor) and **BDD** (Given-When-Then, Cucumber)
- [ ] What makes a good test — fast, isolated, repeatable, self-validating, timely (FIRST); test behaviour not implementation
- [ ] Code coverage — meaning and limits; **mutation testing** (PIT) as a better quality signal
- [ ] **Flaky tests** — causes (time, ordering, shared state, async, network) and fixes
- [ ] Test data management — builders/object mothers, fixtures

### 17.2 Tools
- [ ] **JUnit 5** — lifecycle (`@BeforeEach/All`), `@Nested`, `@ParameterizedTest` (`@CsvSource`, `@MethodSource`), `@Tag`, extensions, `assertThrows`, `assertTimeout`
- [ ] **Mockito** — `mock` vs `spy`, `when/thenReturn`, `doReturn/doThrow` (for spies/void), `verify` (times, never, inOrder), `ArgumentCaptor`, argument matchers, strict stubs, mocking static/final (inline mock maker), BDDMockito
- [ ] **AssertJ** fluent assertions; Hamcrest
- [ ] **Testcontainers** — real Postgres/Kafka/Redis/Localstack in tests, reusable containers, `@ServiceConnection`
- [ ] **WireMock / MockWebServer** — stubbing HTTP dependencies, fault injection (delays, 500s)
- [ ] **Awaitility** — testing async/eventual outcomes
- [ ] **ArchUnit** — enforce layering & package rules
- [ ] **JMH** — microbenchmarks (P1)
- [ ] **Property-based testing** (jqwik) — P2

### 17.3 Spring Testing
- [ ] `@SpringBootTest` (`webEnvironment = RANDOM_PORT/MOCK`), `TestRestTemplate`, `WebTestClient`
- [ ] **Slice tests** — `@WebMvcTest` (+ `MockMvc`), `@DataJpaTest` (in-memory vs Testcontainers with `@AutoConfigureTestDatabase(replace = NONE)`), `@JsonTest`, `@RestClientTest`, `@WebFluxTest`, `@DataMongoTest`, `@DataRedisTest`
- [ ] `@MockitoBean`/`@MockitoSpyBean` (Spring 6.2; replaces deprecated `@MockBean`)
- [ ] **Context caching** — why many unique contexts slow the suite; avoid `@DirtiesContext`
- [ ] `@DynamicPropertySource`, `@TestConfiguration`, `@Sql`, `@ActiveProfiles`
- [ ] **`@Transactional` tests** — auto-rollback; hides lazy-loading & flush bugs; when to avoid
- [ ] Testing security, Kafka listeners (`@EmbeddedKafka`), scheduled jobs, async code
- [ ] **Contract testing** — Spring Cloud Contract / Pact (consumer-driven)

### 17.4 Non-Functional Testing
- [ ] Load/stress/soak/spike tests (Gatling, JMeter, k6) — see §40
- [ ] Chaos testing (Chaos Monkey for Spring Boot, Toxiproxy)
- [ ] Security testing (SAST/DAST/dependency scans) — see §41

---

# PART D — DATA

## 18. SQL & Relational Databases (P0)

### 18.1 SQL Fluency
- [ ] **Joins** — INNER, LEFT/RIGHT/FULL OUTER, CROSS, SELF; semi-join (`EXISTS`), anti-join (`NOT EXISTS` vs `NOT IN` with NULLs)
- [ ] **Aggregation** — `GROUP BY`, `HAVING`, `COUNT(*)` vs `COUNT(col)`, `DISTINCT`
- [ ] **Subqueries** — correlated vs non-correlated; `IN` vs `EXISTS`
- [ ] **CTEs** (`WITH`), **recursive CTEs** (hierarchies, org charts)
- [ ] **Window functions** — `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `LAG`/`LEAD`, `FIRST_VALUE`, running totals with `SUM() OVER (PARTITION BY … ORDER BY …)`, frame clauses
- [ ] `UNION` vs `UNION ALL`, `INTERSECT`, `EXCEPT`
- [ ] **NULL semantics** — three-valued logic, `COALESCE`, `NULLIF`
- [ ] `CASE` expressions, conditional aggregation, pivoting
- [ ] **Upserts** — `INSERT … ON CONFLICT` (Postgres), `ON DUPLICATE KEY UPDATE` (MySQL), `MERGE`
- [ ] **Pagination** — `OFFSET/LIMIT` (slow for deep pages) vs **keyset/seek** (`WHERE (created_at, id) < (?, ?)`)
- [ ] JSON columns & operators (Postgres `jsonb`)
- [ ] **Classic SQL interview problems** — Nth highest salary, delete duplicates keeping one, employees earning more than their manager, top 3 salaries per department, consecutive login days (gaps & islands), running totals, median, month-over-month growth, users who did X but not Y, second most recent order per customer

### 18.2 Data Modeling
- [ ] **ER modeling** — entities, relationships, cardinality, junction tables
- [ ] **Normalization** — 1NF, 2NF, 3NF, BCNF; anomalies (insert/update/delete)
- [ ] **Denormalization** — when and how (read-heavy, reporting, NoSQL-style); keeping it consistent
- [ ] **Keys** — primary, foreign, unique, composite, surrogate vs natural; **auto-increment vs UUIDv4 vs UUIDv7/ULID/Snowflake** and B-tree insert locality
- [ ] **Constraints** — NOT NULL, CHECK, UNIQUE, FK (and their performance/locking cost), exclusion constraints (Postgres)
- [ ] **Common modeling patterns** — audit columns, soft delete, versioning/history tables, temporal data (valid from/to), polymorphic associations, tree structures (adjacency list, materialized path, nested sets, closure table), EAV (anti-pattern mostly), tags, money (DECIMAL + currency), status/state columns, multi-tenant schemas

### 18.3 Indexing (P0)
- [ ] **B+tree index internals** — pages, fan-out, height, leaf linked list, range scans
- [ ] **Clustered vs non-clustered (secondary)** — InnoDB clustered by PK, secondary index stores PK → double lookup; Postgres heap + indexes
- [ ] **Composite indexes** — column order, **leftmost-prefix rule**, equality columns first then range
- [ ] **Covering indexes / index-only scans**, `INCLUDE` columns
- [ ] **Selectivity & cardinality**; when the optimizer ignores an index
- [ ] **Partial/filtered indexes**, **expression/functional indexes** (`lower(email)`)
- [ ] Index types — B-tree, Hash, GIN (jsonb, arrays, full-text), GiST/SP-GiST (geo), BRIN (time-series), bitmap (Oracle/analytics), full-text indexes
- [ ] **Index killers** — functions on columns, implicit type conversion, leading wildcard `LIKE '%x'`, `OR` across columns, `!=`
- [ ] **Cost of indexes** — write amplification, storage, lock contention; unused index detection
- [ ] Index on foreign keys (avoids lock escalation/full scans on delete)

### 18.4 Query Optimization
- [ ] **Reading `EXPLAIN` / `EXPLAIN ANALYZE`** — seq scan, index scan, index-only scan, bitmap heap scan, rows estimate vs actual, cost, loops
- [ ] **Join algorithms** — nested loop, hash join, merge join; when each is chosen
- [ ] **Statistics** — `ANALYZE`, histograms, stale stats causing bad plans; plan caching & parameter sniffing
- [ ] **Slow query log**, `pg_stat_statements`, Performance Schema
- [ ] **Techniques** — avoid `SELECT *`, batch reads/writes, avoid N+1, rewrite correlated subqueries, pagination via keyset, materialized views, summary tables, partition pruning

### 18.5 Transactions, Concurrency & Locking (P0)
- [ ] **How ACID is implemented** — WAL/redo log (durability), undo log (atomicity/MVCC), locks/MVCC (isolation), constraints (consistency)
- [ ] **Isolation levels & anomalies** (dirty read, non-repeatable read, phantom, lost update, write skew, read skew) — which level prevents which, per DB
- [ ] **MVCC** — Postgres (tuple versions, xmin/xmax, VACUUM, bloat, transaction ID wraparound), InnoDB (undo logs, read views)
- [ ] **Snapshot Isolation vs Serializable** (Postgres SSI)
- [ ] **Lock types** — shared/exclusive, row vs table, intention locks, **gap & next-key locks (InnoDB)**, predicate locks; lock escalation (SQL Server)
- [ ] **`SELECT … FOR UPDATE`**, `FOR SHARE`, `NOWAIT`, **`SKIP LOCKED`** (job queues in a DB)
- [ ] **Deadlocks** — how DBs detect them, how to avoid (consistent lock ordering, short transactions, proper indexes), retry on deadlock
- [ ] **Optimistic concurrency** — version column / `WHERE version = ?`, compare-and-set updates (`UPDATE … SET stock = stock - 1 WHERE id = ? AND stock > 0`)
- [ ] **Advisory locks** (Postgres) for app-level coordination
- [ ] **Long-running transactions** — impact on vacuum, replication, locks

### 18.6 Scaling Relational Databases (P0)
- [ ] **Vertical scaling** limits; **connection scaling** (poolers: PgBouncer transaction mode, RDS Proxy, ProxySQL)
- [ ] **Read replicas** — async replication lag, **read-your-writes** consistency solutions (read from primary after write, session stickiness, LSN tracking)
- [ ] **Replication types** — synchronous, asynchronous, semi-synchronous; statement vs row-based vs mixed (MySQL binlog); physical (streaming) vs logical replication (Postgres)
- [ ] **Failover** — automatic promotion, split-brain risk, Patroni, Orchestrator, RDS Multi-AZ, data loss window (RPO)
- [ ] **Partitioning (within one DB)** — range (time), list, hash; partition pruning; dropping old partitions for retention
- [ ] **Sharding (across DBs)** — strategies (hash, range, directory/lookup, geo, tenant-based), **shard key selection**, hot shards, resharding/rebalancing, cross-shard queries/joins/transactions, global secondary indexes, ID generation across shards; tooling: Vitess, Citus, ShardingSphere
- [ ] **CQRS read models**, caching, archiving cold data, federation (split by function)
- [ ] **Distributed SQL / NewSQL** — Google Spanner (TrueTime), CockroachDB, YugabyteDB, TiDB; **Amazon Aurora** (shared storage, 6 copies across 3 AZs, log-is-the-database)

### 18.7 Storage Engine Internals (P1)
- [ ] **B-tree vs LSM-tree** — LSM: memtable → WAL → SSTables → compaction (size-tiered vs leveled); read/write/space amplification; bloom filters per SSTable (Cassandra, RocksDB, LevelDB)
- [ ] Pages, buffer pool/shared buffers, page cache, `fsync`, double-write buffer
- [ ] Row stores vs column stores (OLTP vs OLAP)

### 18.8 Specific Databases
- [ ] **PostgreSQL** — MVCC & VACUUM/autovacuum, bloat, HOT updates, TOAST, JSONB + GIN, extensions (PostGIS, pgvector, pg_partman, TimescaleDB), logical replication, `LISTEN/NOTIFY`, RLS, sequences
- [ ] **MySQL / InnoDB** — clustered index, buffer pool, redo/undo/binlog, gap locks under RR, `innodb_flush_log_at_trx_commit`, online DDL, gh-ost/pt-online-schema-change
- [ ] **Oracle / SQL Server** — awareness if from enterprise background

### 18.9 Database Operations
- [ ] **Backups** — logical (pg_dump) vs physical (base backup + WAL), **PITR**, testing restores
- [ ] **Online schema changes** on big tables; adding a NOT NULL column with default; adding indexes concurrently (`CREATE INDEX CONCURRENTLY`)
- [ ] **Data migrations/backfills** — batched, throttled, idempotent, resumable
- [ ] **Data retention & archival**, GDPR deletion
- [ ] Monitoring — connections, replication lag, slow queries, lock waits, cache hit ratio, disk/IOPS, vacuum progress

### 🎯 Frequently Asked — Databases
- How does a B+tree index work? Why is a composite index on (a, b) not used for `WHERE b = ?`?
- Explain isolation levels with anomalies; what does MVCC solve?
- How would you shard a 5 TB orders table? How do you choose the shard key?
- How do you handle replication lag for read-after-write?
- How do you add a column / index to a 500M-row table with zero downtime?
- A query became slow suddenly — walk me through your debugging
- SQL vs NoSQL — how do you decide?

---

## 19. NoSQL, Search & Storage (P0)

### 19.1 Fundamentals
- [ ] **SQL vs NoSQL decision framework** — data model, access patterns, consistency needs, scale, query flexibility, transactions, team expertise
- [ ] **BASE** vs ACID; eventual consistency; tunable consistency
- [ ] **Access-pattern-driven modeling**, denormalization, duplication, precomputed views
- [ ] NoSQL categories — key-value, document, wide-column, graph, time-series, search, vector

### 19.2 Key-Value — Amazon DynamoDB (P1)
- [ ] Partition key, sort key, item size limit (400 KB), **GSI vs LSI**
- [ ] **Single-table design**, adjacency list pattern, overloading keys
- [ ] Capacity modes (on-demand vs provisioned), RCU/WCU, adaptive capacity, **hot partitions**, write sharding
- [ ] Consistency — eventually vs strongly consistent reads; conditional writes (optimistic locking), transactions (`TransactWriteItems`)
- [ ] DynamoDB Streams (CDC), TTL, global tables (multi-region active-active, LWW), DAX cache
- [ ] Query vs Scan; pagination with `LastEvaluatedKey`

### 19.3 Document — MongoDB (P1)
- [ ] Documents/BSON, **embedding vs referencing** decision, 16 MB limit, schema design patterns (bucket, outlier, computed, subset, extended reference)
- [ ] Indexes — single, compound (ESR rule: Equality, Sort, Range), multikey, text, TTL, partial, wildcard
- [ ] **Aggregation pipeline** — `$match`, `$group`, `$lookup`, `$unwind`, `$project`
- [ ] **Replica sets** — primary election, oplog, read preferences, **write concern / read concern**
- [ ] **Sharding** — shard key choice (cardinality, frequency, monotonic keys problem), chunks, balancer, hashed vs ranged
- [ ] Multi-document transactions (since 4.0) and their cost; change streams

### 19.4 Wide-Column — Apache Cassandra (P1)
- [ ] **Architecture** — masterless ring, consistent hashing with vnodes, partitioner (Murmur3), gossip, snitches
- [ ] **Replication factor** & strategies (NetworkTopologyStrategy)
- [ ] **Tunable consistency** — ONE, QUORUM, LOCAL_QUORUM, ALL; **R + W > N** for strong consistency
- [ ] **Data model** — partition key + clustering columns, query-first table design, one table per query, wide partitions & partition size limits
- [ ] **Write path** — commit log → memtable → SSTable; compaction strategies (STCS, LCS, TWCS for time-series)
- [ ] **Read path** — bloom filters, partition index, key cache
- [ ] **Tombstones** & their performance problems; TTLs; avoid deletes-heavy patterns
- [ ] **Repair mechanisms** — hinted handoff, read repair, anti-entropy repair (Merkle trees)
- [ ] Lightweight transactions (Paxos) — cost
- [ ] Related — ScyllaDB, HBase/Bigtable (awareness)

### 19.5 Graph & Time-Series & Others (P2)
- [ ] **Graph DBs** — Neo4j (Cypher), Neptune; use cases (social graphs, fraud, recommendations)
- [ ] **Time-series** — InfluxDB, TimescaleDB, Prometheus TSDB; downsampling, retention, high-cardinality issues
- [ ] **In-memory data grids** — Hazelcast, Apache Ignite
- [ ] **Columnar analytics** — ClickHouse, Apache Druid, Pinot (see §33)

### 19.6 Search — Elasticsearch / OpenSearch (P1)
- [ ] **Inverted index**, analyzers (character filters, tokenizers, token filters), stemming, synonyms, n-grams for autocomplete
- [ ] **Mappings** — `text` vs `keyword`, dynamic mapping pitfalls, multi-fields
- [ ] **Cluster** — nodes, primary/replica shards, shard sizing, routing, master nodes
- [ ] **Near-real-time** — refresh interval, translog, segment merging
- [ ] **Relevance** — TF-IDF → BM25, boosting, function score
- [ ] **Query DSL** — `bool` (must/should/filter/must_not), `match`, `term`, `range`, `multi_match`, filter vs query context (caching, no scoring)
- [ ] **Aggregations** — terms, date histogram, cardinality (HLL), nested
- [ ] **Pagination** — `from/size` limits, `search_after`, point-in-time; scroll (legacy)
- [ ] **Keeping ES in sync with the DB** — dual writes (bad) vs CDC (Debezium → Kafka → ES), reindexing with aliases (zero downtime)
- [ ] Hybrid search (BM25 + vector kNN)

### 19.7 Vector Databases (P1 in 2026)
- [ ] Embeddings & similarity (cosine, dot product, Euclidean)
- [ ] ANN indexes — **HNSW**, IVF, PQ; recall vs latency trade-off
- [ ] Options — pgvector, Pinecone, Weaviate, Milvus, Qdrant, OpenSearch kNN, Redis vector search

### 19.8 Object & File Storage
- [ ] **Amazon S3** — buckets/keys, strong read-after-write consistency, storage classes & lifecycle rules, versioning, multipart upload, **pre-signed URLs** (direct client upload/download), event notifications, encryption (SSE-S3/SSE-KMS), S3 as data lake
- [ ] Block vs file vs object storage — EBS vs EFS vs S3
- [ ] Storing large files — metadata in DB, blob in object storage, CDN in front
- [ ] Distributed file systems — HDFS/GFS concepts (awareness)

### 🎯 Frequently Asked — NoSQL
- When would you choose Cassandra over Postgres? DynamoDB over MongoDB?
- How do you model a chat/messages table in Cassandra?
- What is a hot partition and how do you fix it?
- How do you keep Elasticsearch in sync with your primary DB?
- Explain R + W > N with an example

---

## 20. Caching & Redis (P0)

### 20.1 Caching Fundamentals
- [ ] **Why cache** — latency, throughput, cost, protect the DB; **when not to** (low hit ratio, strong consistency needs, highly personalized data)
- [ ] **Cache layers** — browser/client → CDN/edge → API gateway → application local (in-process) → distributed cache → DB buffer pool
- [ ] **Local vs distributed cache** — Caffeine/Guava vs Redis/Memcached; consistency across instances; memory per pod
- [ ] **Hit ratio, TTL selection**, working set size, 80/20 rule

### 20.2 Caching Strategies
- [ ] **Cache-aside (lazy loading)** — most common; read: cache → miss → DB → populate; write: update DB → **delete** cache
- [ ] **Read-through**, **write-through**, **write-behind (write-back)**, **write-around**, **refresh-ahead**
- [ ] Trade-offs of each (consistency, latency, data-loss risk)

### 20.3 Eviction Policies
- [ ] LRU, LFU, FIFO, MRU, random, TTL-based; **W-TinyLFU** (Caffeine)
- [ ] Redis `maxmemory-policy` — `noeviction`, `allkeys-lru`, `volatile-lru`, `allkeys-lfu`, `volatile-ttl`…

### 20.4 Cache Consistency & Invalidation
- [ ] "Two hard things in CS" — invalidation strategies: TTL, explicit delete on write, event-driven invalidation (CDC/Kafka), versioned keys
- [ ] **Why delete instead of update** on write; race conditions between concurrent read-miss and write; **delayed double delete**
- [ ] Invalidating local caches across N instances (Redis pub/sub, Kafka broadcast, short TTL)
- [ ] Cache + DB transaction ordering (invalidate after commit)

### 20.5 Caching Failure Modes (P0 — very common senior questions)
- [ ] **Cache stampede / thundering herd / dog-piling** — many requests miss on a hot key simultaneously → mutex/lock on rebuild, request coalescing (single-flight), **probabilistic early expiration (XFetch)**, stale-while-revalidate, background refresh
- [ ] **Cache penetration** — requests for non-existent keys → cache negative results (short TTL), **Bloom filter**, input validation
- [ ] **Cache avalanche** — many keys expire together or cache cluster dies → **TTL jitter**, multi-level cache, circuit breaker to DB, warm-up, HA cache
- [ ] **Hot keys** — single key overwhelming one shard → local L1 cache, key replication/splitting (`key#1..N`), read replicas
- [ ] **Big keys** — huge values/collections → split, compress, avoid O(N) commands
- [ ] **Cold start** after deploy/failover → cache warming
- [ ] **Serialization** cost & format compatibility across deployments (versioned cache keys)

### 20.6 Redis Deep Dive (P0)
- [ ] **Architecture** — single-threaded command execution (event loop, I/O threads since 6.0), in-memory, why it's fast
- [ ] **Data types & use cases**
  - [ ] String (counters `INCR`, caching, distributed locks)
  - [ ] Hash (objects), List (queues, `LPUSH/BRPOP`), Set (unique members, tags), **Sorted Set** (leaderboards, rate limiting sliding window, priority queues, delayed jobs)
  - [ ] Bitmap (daily active users), **HyperLogLog** (unique counts), Geo (nearby search), **Streams** (consumer groups, log-like messaging), Pub/Sub (fire-and-forget), JSON & search modules
- [ ] **Expiration** — lazy + active expiry, `EXPIRE`, `TTL`
- [ ] **Persistence** — RDB snapshots vs AOF (fsync `always/everysec/no`), AOF rewrite, hybrid
- [ ] **Replication** — async primary-replica, `WAIT` command
- [ ] **High availability** — Redis Sentinel (monitoring, auto-failover, quorum)
- [ ] **Redis Cluster** — 16384 hash slots, sharding, **hash tags `{user123}`** for multi-key ops, `MOVED`/`ASK` redirects, resharding, cluster limitations (multi-key, Lua across slots)
- [ ] **Atomicity** — single commands are atomic; `MULTI/EXEC` (no rollback), `WATCH` (optimistic locking), **Lua scripts** / Redis Functions (atomic multi-step logic)
- [ ] **Pipelining** for throughput
- [ ] **Distributed locks** — `SET key value NX PX ttl`, unique value + Lua for safe release, lock renewal (watchdog in Redisson), **Redlock** and Martin Kleppmann's critique, **fencing tokens**; when to use DB/ZooKeeper/etcd instead
- [ ] **Common use cases** — session store, rate limiter, leaderboard, idempotency keys store, dedupe, job queue, pub/sub notifications, feature flags, geo lookups, counting
- [ ] **Performance anti-patterns** — `KEYS *` (use `SCAN`), big keys, O(N) commands on large collections, missing TTLs, no connection pooling
- [ ] **Java clients** — Lettuce (default in Spring, async/Netty), Jedis, **Redisson** (locks, rate limiters, distributed collections)
- [ ] **Redis vs Memcached**; Valkey (open-source fork), Dragonfly, KeyDB (awareness); managed — ElastiCache/MemoryDB

### 20.7 CDN & HTTP Caching
- [ ] **HTTP caching headers** — `Cache-Control` (`max-age`, `s-maxage`, `no-cache` vs `no-store`, `private`/`public`, `stale-while-revalidate`), `ETag`/`If-None-Match`, `Last-Modified`/`If-Modified-Since`, `Vary`, 304 Not Modified
- [ ] **CDN** — edge PoPs, pull vs push CDNs, cache keys, invalidation/purge, versioned asset URLs, origin shielding, edge compute (Lambda@Edge, Cloudflare Workers), caching API responses at edge
- [ ] Providers — CloudFront, Cloudflare, Akamai, Fastly

### 🎯 Frequently Asked — Caching
- How do you keep cache and DB consistent?
- What is a cache stampede and how do you prevent it?
- Design a distributed cache; how do you handle a hot key?
- How do you implement a distributed lock with Redis? What are its weaknesses?
- Local cache vs Redis — how do you invalidate local caches across 50 pods?

---

# PART E — DISTRIBUTED SYSTEMS & ARCHITECTURE

## 21. Messaging & Event Streaming (P0)

### 21.1 Fundamentals
- [ ] **Why async messaging** — temporal decoupling, load leveling/buffering, fan-out, resilience, scaling consumers independently
- [ ] **Queue (point-to-point) vs pub/sub vs log-based stream** (Kafka retains & replays; queues delete on ack)
- [ ] **Push vs pull** consumers
- [ ] **Message vs event vs command**; event notification vs event-carried state transfer vs event sourcing
- [ ] **Delivery semantics** — at-most-once, **at-least-once** (the realistic default), exactly-once (= at-least-once + idempotent processing / transactional)
- [ ] **Ordering guarantees** — global vs per-key/partition ordering; what breaks ordering (retries, parallel consumers, DLQ)
- [ ] **Idempotent consumers** — dedup by message ID (processed-messages table / Redis SETNX with TTL), natural idempotency, upserts
- [ ] **Poison messages & DLQ**, retry with backoff (blocking vs non-blocking retry topics), parking lots, replay from DLQ tooling
- [ ] **Backpressure** & consumer lag; message TTL; priority queues; delayed/scheduled messages
- [ ] **Schema evolution** — versioned events, backward/forward compatibility, schema registry, tolerant reader
- [ ] **Message size limits** — claim-check pattern (store payload in S3, send reference)

### 21.2 Apache Kafka Deep Dive (P0)
- [ ] **Architecture** — brokers, topics, partitions, segments, offsets, replicas, leader/followers, **ISR**, controller; **KRaft** (ZooKeeper removed in Kafka 4.0)
- [ ] **Storage** — append-only log segments, index files, retention by time/size, **log compaction** (latest value per key; changelog/state topics), tiered storage
- [ ] **Why Kafka is fast** — sequential disk I/O, OS page cache, **zero-copy (sendfile)**, batching, compression, partition parallelism
- [ ] **Producer** — partitioner (key hash → partition; sticky partitioner for null keys), `acks=0/1/all`, `min.insync.replicas`, retries & `delivery.timeout.ms`, **idempotent producer** (PID + sequence numbers; default on), `max.in.flight.requests.per.connection` and ordering, batching (`linger.ms`, `batch.size`), compression (lz4/zstd/snappy), `buffer.memory`, sync vs async send
- [ ] **Durability config** — RF=3, `min.insync.replicas=2`, `acks=all`, `unclean.leader.election.enable=false`
- [ ] **Consumer** — consumer groups, one partition → max one consumer in a group, **scaling limited by partition count**
- [ ] **Partition assignment** — range, round-robin, sticky, **cooperative sticky** (incremental rebalance); **static membership** (`group.instance.id`)
- [ ] **Rebalancing** — triggers, stop-the-world impact, rebalance storms; `max.poll.interval.ms`, `max.poll.records`, `session.timeout.ms`, `heartbeat.interval.ms`; new consumer rebalance protocol (KIP-848)
- [ ] **Offset management** — auto-commit (risk of loss/duplication) vs manual commit (sync/async), commit after processing = at-least-once, `auto.offset.reset` (earliest/latest), `__consumer_offsets`, seeking/replaying
- [ ] **Exactly-once semantics (EOS)** — idempotent producer + transactions (`transactional.id`) + consumers with `isolation.level=read_committed`; consume-transform-produce; EOS does **not** cover external side effects (DB/HTTP)
- [ ] **Ordering** — per-partition only; choose key = entity id (orderId); retries + in-flight > 1 without idempotence break ordering
- [ ] **Partition count sizing** — throughput per partition, consumer parallelism, can increase but not decrease, key → partition remapping on increase
- [ ] **Hot partitions** — skewed keys; salting keys, custom partitioner
- [ ] **Consumer lag monitoring** — Burrow, Kafka Exporter, alerting on lag & lag growth
- [ ] **Schema Registry** — Avro/Protobuf/JSON Schema, subject naming, compatibility modes (BACKWARD, FORWARD, FULL, TRANSITIVE)
- [ ] **Kafka Connect** — source/sink connectors, **Debezium CDC**, SMTs, distributed mode
- [ ] **Kafka Streams** — KStream vs KTable vs GlobalKTable, stateless/stateful ops, joins, windowing (tumbling, hopping, sliding, session), state stores (RocksDB) & changelog topics, interactive queries, exactly-once
- [ ] ksqlDB, Flink with Kafka (awareness)
- [ ] **Multi-DC** — MirrorMaker 2, Confluent replicator/cluster linking, active-passive vs active-active
- [ ] **Security** — TLS, SASL (SCRAM, OAUTHBEARER), ACLs, quotas
- [ ] **Queues for Kafka / share groups** (KIP-932, Kafka 4.x) — awareness
- [ ] **Operations** — under-replicated partitions, ISR shrink, disk usage, broker failure handling, rolling upgrades, managed options (MSK, Confluent Cloud)

### 21.3 RabbitMQ (P1)
- [ ] AMQP model — producer → **exchange** → binding (routing key) → **queue** → consumer
- [ ] Exchange types — direct, topic (wildcards `*`/`#`), fanout, headers
- [ ] Acks/nacks/requeue, **prefetch (QoS)**, durable queues & persistent messages, publisher confirms
- [ ] DLX (dead-letter exchanges), message & queue TTL, delayed-message plugin, priority queues
- [ ] **Quorum queues** (Raft-based) vs classic mirrored (deprecated); RabbitMQ Streams
- [ ] Competing consumers, work queues, RPC pattern

### 21.4 Kafka vs RabbitMQ vs SQS — be able to compare
- [ ] Retention & replay · ordering · throughput · routing flexibility · consumer model (pull vs push) · ops complexity · exactly-once support · per-message acks · priority/delay support · cost

### 21.5 Cloud Messaging (P1)
- [ ] **AWS SQS** — standard (at-least-once, best-effort order) vs **FIFO** (message group ID, dedup ID, throughput limits), **visibility timeout**, long polling, DLQ & redrive, max message size (256 KB → claim check), delay queues
- [ ] **AWS SNS** — topics, fan-out to SQS (SNS+SQS pattern), filtering policies
- [ ] **EventBridge** (event bus, rules, schema registry), **Kinesis Data Streams** (shards), **Amazon MSK**
- [ ] GCP Pub/Sub, Azure Service Bus / Event Hubs; Apache Pulsar (segment storage, multi-tenancy); NATS; ActiveMQ/JMS (legacy)

### 21.6 Messaging Patterns (P0)
- [ ] **Dual-write problem** — writing to DB and broker non-atomically
- [ ] **Transactional Outbox** — write event to outbox table in the same DB transaction → relay via polling publisher or **CDC (Debezium)** → broker; ordering, cleanup, at-least-once
- [ ] **Inbox pattern / idempotent consumer**
- [ ] **Change Data Capture (CDC)** — log-based (binlog/WAL) vs trigger vs polling
- [ ] **Choreography vs orchestration** (sagas)
- [ ] **Competing consumers**, **publish-subscribe**, **fan-out/fan-in**, **scatter-gather**, request-reply over messaging (correlation IDs, reply queues)
- [ ] **Event-driven architecture** pitfalls — event spaghetti, hard debugging, eventual consistency UX, event versioning, "who owns this event"
- [ ] **Event ordering & sequence numbers**, handling out-of-order events (version checks, last-write-wins)
- [ ] **Replay & reprocessing** strategies

### 🎯 Frequently Asked — Messaging
- How does Kafka guarantee ordering? How would you process 1 million msgs/min with ordering per customer?
- How do you avoid duplicate processing? Is exactly-once real?
- What happens when a consumer crashes mid-batch? When a broker dies?
- Explain consumer rebalancing and how you'd reduce its impact
- How do you publish an event reliably after a DB commit? (Outbox)
- How do you handle a poison message? Retry topics vs DLQ — ordering implications?
- Kafka vs RabbitMQ — when would you choose each?

---

## 22. Distributed Systems Theory (P0)

### 22.1 Foundations
- [ ] **8 fallacies of distributed computing** (network is reliable, latency is zero, bandwidth is infinite, network is secure, topology doesn't change, one administrator, transport cost is zero, network is homogeneous)
- [ ] **Failure modes** — crash-stop, crash-recovery, omission, timing, Byzantine; partial failures; gray failures
- [ ] **Timeouts can't distinguish slow from dead**; failure detectors (heartbeats, phi-accrual)

### 22.2 CAP, PACELC & Consistency Models
- [ ] **CAP theorem** — correct interpretation (during a partition choose C or A); CP vs AP system examples (ZooKeeper/etcd/HBase vs Cassandra/Dynamo)
- [ ] **PACELC** — else (no partition) trade latency vs consistency
- [ ] **Consistency models** — linearizability (strong), sequential, causal, PRAM, **read-your-writes**, monotonic reads, monotonic writes, consistent prefix, **eventual consistency**
- [ ] **Linearizability vs serializability** (single-object recency vs multi-object transactions); strict serializability
- [ ] **Session guarantees** and how to provide them in practice

### 22.3 Replication
- [ ] **Single-leader** (most RDBMS, Kafka partitions), **multi-leader** (multi-DC, offline clients — conflict resolution required), **leaderless** (Dynamo-style: Cassandra, Riak)
- [ ] Sync vs async vs semi-sync replication; replication lag problems
- [ ] **Conflict resolution** — last-write-wins (clock dependency, data loss), version vectors, application-level merge, **CRDTs** (G-Counter, PN-Counter, OR-Set, LWW-Register)
- [ ] **Quorums** — N, R, W; R + W > N; sloppy quorums & hinted handoff; read repair; anti-entropy with Merkle trees

### 22.4 Partitioning
- [ ] Range vs hash partitioning; skew & hot spots
- [ ] **Consistent hashing** — ring, virtual nodes, minimal data movement on node add/remove; rendezvous (HRW) hashing; jump consistent hash
- [ ] Rebalancing strategies — fixed number of partitions, dynamic splitting, proportional to nodes
- [ ] Secondary indexes — local (document-partitioned, scatter-gather reads) vs global (term-partitioned, async updates)
- [ ] Request routing — client-aware, routing tier, gossip/ZooKeeper metadata

### 22.5 Time & Ordering
- [ ] **Physical clocks** — drift, NTP, clock skew, leap seconds, monotonic vs wall clock (`System.nanoTime` vs `currentTimeMillis`)
- [ ] **Logical clocks** — Lamport timestamps (total order, not causality detection), **vector clocks** (causality, concurrent detection)
- [ ] **Hybrid logical clocks** (CockroachDB), **TrueTime** (Spanner: commit wait)
- [ ] Why you can't rely on timestamps for ordering across machines

### 22.6 Consensus & Coordination
- [ ] **The consensus problem**; FLP impossibility (awareness)
- [ ] **Paxos** (concept: proposers, acceptors, learners; Multi-Paxos)
- [ ] **Raft** (P0 conceptually) — leader election (terms, randomized timeouts, votes), log replication (append entries, commit index, majority), safety, membership changes; used in etcd, Consul, CockroachDB, Kafka KRaft, RabbitMQ quorum queues
- [ ] **ZAB / ZooKeeper** — znodes, ephemeral & sequential nodes, watches; recipes: leader election, distributed locks, service registry, config
- [ ] **etcd** — K8s backing store, leases, watches
- [ ] **Leader election** patterns — consensus-based, lease-based, DB-row-based, bully algorithm (awareness)
- [ ] **Distributed locks & leases**, lock expiry hazards (GC pause), **fencing tokens**
- [ ] **Split brain** — causes and prevention (quorum, STONITH, fencing)
- [ ] **Gossip protocols** — membership & failure detection (SWIM, Cassandra gossip)
- [ ] **Byzantine fault tolerance**, PBFT — awareness only (blockchains)

### 22.7 Distributed Transactions
- [ ] **Two-Phase Commit (2PC)** — prepare/commit, coordinator as SPOF, blocking on coordinator failure, XA/JTA; why it's avoided in microservices
- [ ] **Three-Phase Commit** — awareness
- [ ] **Saga pattern** — sequence of local transactions + **compensating transactions**; **choreography** (events) vs **orchestration** (central coordinator); semantic locks, countermeasures for lack of isolation (pending states, commutative updates, re-reading values); pivot transactions; retriable vs compensatable steps
- [ ] **TCC (Try-Confirm/Cancel)** — reservation-based
- [ ] **Outbox + idempotent consumers** as the practical foundation
- [ ] **Workflow/orchestration engines** — Temporal, Camunda/Zeebe, AWS Step Functions, Netflix Conductor
- [ ] **Exactly-once processing** in practice = idempotency + dedup + atomic offset/state commits

### 22.8 Idempotency (P0 — cross-cutting)
- [ ] Idempotent vs safe operations; natural idempotency (`SET x = 5`) vs non-idempotent (`x = x + 5`)
- [ ] **Idempotency keys** — client-generated, stored with request hash & response, TTL, concurrent duplicate handling (lock/unique constraint), replaying the stored response
- [ ] **Dedup tables / unique constraints** as the source of truth
- [ ] Idempotency across retries, message redelivery, webhooks, payment gateways

### 22.9 Unique ID Generation (P0)
- [ ] Requirements — uniqueness, ordering (time-sortable?), size (64 vs 128 bit), coordination-free, index locality
- [ ] Options — DB auto-increment (single point), **ticket server** (Flickr), multi-master with step offsets, **UUIDv4** (random, bad index locality), **UUIDv7 / ULID / KSUID** (time-ordered), **Twitter Snowflake** (41-bit timestamp + 10-bit machine + 12-bit sequence), hi/lo & segment allocation (Leaf), clock-rollback handling

### 22.10 Probabilistic Data Structures & Algorithms
- [ ] **Bloom filter** (false positives, no false negatives, sizing), Counting Bloom filter, Cuckoo filter
- [ ] **Count-Min Sketch** (frequency estimation, heavy hitters)
- [ ] **HyperLogLog** (cardinality estimation, ~12 KB for billions)
- [ ] **Merkle trees** (anti-entropy, data sync, blockchains)
- [ ] Reservoir sampling, t-digest (percentiles), skip lists, geohash

### 22.11 Queueing & Load
- [ ] **Little's Law** — L = λ × W (concurrency = throughput × latency) — use it for thread pool & connection pool sizing
- [ ] **Utilization vs latency** curve (latency explodes as utilization → 100%)
- [ ] **Tail latency** amplification in fan-out (p99 of N calls), hedged requests, "The Tail at Scale"
- [ ] **Backpressure**, load shedding, admission control
- [ ] Amdahl's law & Universal Scalability Law (contention + coherence)

### 22.12 Landmark Papers & Systems (know the key idea of each)
- [ ] Amazon **Dynamo** · Google **GFS**, **MapReduce**, **Bigtable**, **Chubby**, **Spanner**, **Zanzibar** · **Raft** ("In Search of an Understandable Consensus Algorithm") · LinkedIn **Kafka** · Facebook **TAO**, Memcache scaling paper · Netflix chaos engineering · "The Tail at Scale"

### 🎯 Frequently Asked — Distributed Systems
- Explain CAP with a real system you've built. Was it CP or AP?
- How does consistent hashing work? Why virtual nodes?
- How does Raft elect a leader? What happens during a network partition?
- Design a distributed lock. What can go wrong?
- 2PC vs Saga — implement order → payment → inventory with a Saga and describe compensation
- How do you generate unique, sortable IDs across 100 servers?

---

## 23. Microservices Architecture (P0)

### 23.1 When & Why
- [ ] **Monolith vs modular monolith vs microservices vs SOA** — trade-offs (deployability, team autonomy, scaling, complexity, latency, data consistency, ops overhead)
- [ ] **When NOT to use microservices** — small teams, unclear domain, early-stage product
- [ ] **Conway's Law** & Inverse Conway Maneuver; Team Topologies (stream-aligned, platform, enabling, complicated-subsystem teams)
- [ ] **Anti-patterns** — distributed monolith, shared database, chatty services, nanoservices, synchronous call chains, shared domain libraries, "microservices envy"

### 23.2 Decomposition
- [ ] By **business capability**, by **subdomain/bounded context** (DDD), by volatility, by scalability needs
- [ ] Service granularity heuristics; cohesion & coupling (afferent/efferent)
- [ ] **Migration from monolith** — **Strangler Fig**, branch by abstraction, anti-corruption layer, parallel run, data migration strategies, extracting the DB last vs first
- [ ] **Your own migration story** — prepare it in detail

### 23.3 Communication
- [ ] **Synchronous** (REST, gRPC) vs **asynchronous** (events/messages) — coupling, latency, availability math (99.9%ⁿ)
- [ ] **API Gateway**, **BFF**, API composition / aggregator
- [ ] **Service discovery** (client-side vs server-side), **load balancing** (client-side vs proxy)
- [ ] **Service mesh** — Istio/Linkerd: sidecar (Envoy) data plane + control plane; mTLS, retries, timeouts, traffic shifting, observability; ambient/sidecarless mode; when a mesh is overkill
- [ ] **Avoiding cascading synchronous chains** — async, caching, data replication via events

### 23.4 Data Management
- [ ] **Database per service** (private tables/schema/DB) vs shared DB anti-pattern
- [ ] **Querying across services** — API composition, **CQRS** with read models fed by events, data replication, data lake for reporting
- [ ] **Consistency** — sagas, outbox, eventual consistency, compensations, idempotency
- [ ] **Event sourcing** (when appropriate)
- [ ] Reference data & shared lookup data handling

### 23.5 Cross-Cutting Concerns
- [ ] Externalized configuration, secrets management
- [ ] **Observability** — centralized structured logging, metrics, distributed tracing, **correlation IDs**, health checks
- [ ] **Security** — edge authentication at gateway, token propagation, service-to-service auth (mTLS/JWT), zero trust, least privilege
- [ ] **Resilience** — timeouts, retries, circuit breakers, bulkheads everywhere (§26)
- [ ] **Chassis/platform** — shared starters for logging/tracing/security (Microservice Chassis pattern) without coupling domain logic
- [ ] **12-Factor App** — codebase, dependencies, config, backing services, build/release/run, processes (stateless), port binding, concurrency, disposability, dev/prod parity, logs as event streams, admin processes; + API-first, telemetry, auth (Beyond 12-factor)

### 23.6 Deployment & Release
- [ ] One service per container; independent pipelines
- [ ] Rolling, **blue-green**, **canary** (metric-based promotion), A/B, **feature flags**, dark launches, **shadow/mirrored traffic**
- [ ] **Backward compatibility** of APIs & events during rolling deploys (N and N-1 coexist); expand/contract
- [ ] Database migrations decoupled from code deploys

### 23.7 Testing Microservices
- [ ] Unit → component (service in isolation with stubs) → **contract tests** (Pact / Spring Cloud Contract) → integration → few E2E
- [ ] Testing in production — canaries, synthetic transactions
- [ ] Ephemeral environments, test data across services

### 23.8 Microservices Pattern Catalog (microservices.io) — know each
- [ ] Decomposition: by business capability, by subdomain, strangler application, anti-corruption layer
- [ ] Data: database per service, shared database, saga, API composition, CQRS, event sourcing, transactional outbox, transaction log tailing, polling publisher, domain event
- [ ] Communication: remote procedure invocation, messaging, idempotent consumer
- [ ] External API: API gateway, BFF
- [ ] Discovery: client-side, server-side, service registry, self-registration, 3rd-party registration
- [ ] Reliability: circuit breaker
- [ ] Observability: log aggregation, application metrics, audit logging, distributed tracing, exception tracking, health check API, log deployments & changes
- [ ] Deployment: service per container, serverless, service mesh, sidecar
- [ ] Security: access token
- [ ] Cross-cutting: microservice chassis, externalized configuration, service template

### 🎯 Frequently Asked — Microservices
- How did you decide service boundaries in your system?
- How do you handle a transaction spanning 3 services?
- How do you query data that lives in multiple services?
- How do you trace a request across 10 services?
- What problems did you face moving to microservices? Would you do it again?
- How do you version APIs and events without breaking consumers?

---

## 24. Domain-Driven Design (P1)

### 24.1 Strategic Design
- [ ] **Domain, subdomains** — core, supporting, generic (build vs buy decisions)
- [ ] **Ubiquitous language**
- [ ] **Bounded contexts** — model boundaries; same word, different meaning (e.g., "Customer" in Sales vs Support)
- [ ] **Context mapping** — partnership, shared kernel, customer–supplier, conformist, **anti-corruption layer**, open host service, published language, separate ways, big ball of mud
- [ ] **Event Storming** — discovering events, commands, aggregates, policies, bounded contexts

### 24.2 Tactical Design
- [ ] **Entities** (identity) vs **Value Objects** (immutable, equality by value — Money, Address, DateRange)
- [ ] **Aggregates & aggregate roots** — consistency boundary, invariants enforced inside, **one transaction = one aggregate**, reference other aggregates by ID, keep aggregates small
- [ ] **Domain services** vs **application services** vs infrastructure services
- [ ] **Repositories** (per aggregate), **factories**
- [ ] **Domain events** vs **integration events**
- [ ] **Specifications**, policies
- [ ] **Rich domain model vs anemic domain model**
- [ ] Mapping DDD to Spring/JPA (aggregate = entity graph, `@DomainEvents`/`AbstractAggregateRoot`, jMolecules)

---

## 25. Architecture Styles & Documentation (P1)

### 25.1 Styles
- [ ] **Layered (n-tier)** — presentation, application, domain, infrastructure; strict vs relaxed
- [ ] **Hexagonal (Ports & Adapters)**, **Clean Architecture**, **Onion** — dependency rule, domain at center, framework at edges; testability
- [ ] **Modular monolith** — enforced module boundaries (Spring Modulith, ArchUnit), path to microservices
- [ ] **Microservices** (§23), **SOA/ESB** (history, why it fell out of favor)
- [ ] **Event-driven architecture** — broker topology vs mediator topology
- [ ] **CQRS** — separate write and read models; when it's worth the complexity; eventual consistency of read side
- [ ] **Event sourcing** — event store as source of truth, rebuilding state, snapshots, projections, upcasting/versioning events, GDPR deletion challenges (crypto-shredding), when NOT to use; tools (Axon, EventStoreDB)
- [ ] **Serverless / FaaS** — cold starts (Java: SnapStart, GraalVM), limits (duration, payload), cost model, vendor lock-in
- [ ] **Space-based architecture**, **microkernel/plugin** architecture, **pipe-and-filter**
- [ ] **Cell-based architecture** (blast-radius isolation), shuffle sharding
- [ ] **Multi-tenant SaaS** — silo vs pool vs bridge models, noisy neighbors, tenant isolation, per-tenant config & throttling
- [ ] **Micro-frontends** — awareness
- [ ] **Lambda vs Kappa** data architectures (§33)

### 25.2 Architecture Practice (expected from a tech lead)
- [ ] **Quality attributes (-ilities)** — scalability, availability, reliability, performance, security, maintainability, testability, deployability, observability, cost — and **trade-off analysis** (ATAM awareness)
- [ ] **C4 model** — Context, Container, Component, Code diagrams
- [ ] **Architecture Decision Records (ADRs)** — context, decision, consequences, status
- [ ] **Design docs / RFCs** — structure (problem, goals/non-goals, options considered, decision, risks, rollout, metrics)
- [ ] **Fitness functions** & evolutionary architecture
- [ ] **Technical debt** — types (deliberate/inadvertent, reckless/prudent quadrant), measuring, prioritizing, paying down incrementally
- [ ] **Build vs buy vs open-source** decision framework
- [ ] **Reversible vs irreversible decisions** (one-way vs two-way doors)

---

## 26. Resilience, Fault Tolerance & High Availability (P0)

### 26.1 Failure Modes to Know
- [ ] Cascading failures; retry storms / retry amplification across layers
- [ ] Thundering herd after recovery; synchronized clients
- [ ] Slow dependencies (worse than dead ones) → thread/connection exhaustion
- [ ] Resource exhaustion — threads, connections, file descriptors, memory, disk, ephemeral ports
- [ ] GC pauses causing heartbeats to miss; network partitions; poison pills; **metastable failures**; noisy neighbors; clock skew; certificate expiry; DNS failures; config pushes

### 26.2 Resilience Patterns
- [ ] **Timeouts** — on every remote call; connect vs read vs total; **deadline propagation** across hops; timeout budget
- [ ] **Retries** — only for transient errors & idempotent operations; **exponential backoff + jitter**; max attempts; **retry budgets**; retry at one layer only
- [ ] **Circuit breaker** — closed/open/half-open; fail-fast; per-dependency
- [ ] **Bulkhead** — isolate thread pools/connection pools per dependency or tenant
- [ ] **Rate limiting & throttling** (§27), **load shedding** (drop low-priority work under overload), **admission control**
- [ ] **Backpressure** — bounded queues, reject early, signal upstream
- [ ] **Fallbacks & graceful degradation** — cached/stale data, default values, feature degradation, read-only mode
- [ ] **Health checks** — liveness vs readiness vs startup; deep vs shallow checks
- [ ] **Redundancy & failover** — active-active, active-passive; N+1/N+2 capacity
- [ ] **Hedged requests**, request coalescing
- [ ] **Queue-based load leveling**
- [ ] **Idempotency** to make retries safe
- [ ] **Fail-fast vs fail-safe**; steady state (auto-cleanup of logs/data)
- [ ] **Shuffle sharding & cell-based isolation** to limit blast radius

### 26.3 High Availability & Disaster Recovery
- [ ] **Availability math** — 99% (3.65 days/yr), 99.9% (8.76 h/yr, 43.8 min/mo), 99.95% (4.38 h/yr), 99.99% (52.6 min/yr), 99.999% (5.26 min/yr); series (multiply) vs parallel (1 − Π(1−a)) components
- [ ] **SPOF elimination** at every layer (LB, app, DB, cache, broker, DNS, region)
- [ ] **Multi-AZ vs multi-region**; active-passive vs active-active; data replication across regions & conflict handling
- [ ] **RTO & RPO** definitions; DR strategies — backup & restore, pilot light, warm standby, multi-site active-active (cost vs RTO/RPO)
- [ ] **DR drills**, game days, failover testing
- [ ] **Graceful shutdown & startup** — draining connections, finishing in-flight work, deregistering from LB

### 26.4 Chaos Engineering
- [ ] Principles — steady-state hypothesis, real-world events, run in production carefully, minimize blast radius
- [ ] Tools — Chaos Monkey, Gremlin, LitmusChaos, AWS Fault Injection Service, Toxiproxy

### 🎯 Frequently Asked — Resilience
- A downstream service is slow and your service starts failing — what's happening and how do you protect it?
- How do you configure retries without causing a retry storm?
- Explain circuit breaker states and how you'd tune it
- How would you make your system survive an AZ / region failure?
- What's the difference between rate limiting, load shedding, and backpressure?

---

## 27. Rate Limiting & Throttling (P0)

### 27.1 Why & Where
- [ ] **Purposes** — prevent abuse/DoS/brute force, fairness across tenants, protect downstream & DB, cost control, enforce paid tiers/SLAs, smooth traffic spikes
- [ ] **Where** — client SDK, CDN/WAF (Cloudflare, AWS WAF), load balancer/reverse proxy (Nginx, Envoy), **API gateway**, service mesh, **application layer**, outbound (protect 3rd-party APIs you call), DB/queue level
- [ ] **Keys/dimensions** — per user, API key, IP (NAT caveats), tenant/org, endpoint, method, global; combinations (user × endpoint)
- [ ] **Rate limit vs quota** (per second vs per month), burst vs sustained, concurrency limits (in-flight requests)
- [ ] **Rate limiting vs throttling vs load shedding vs backpressure vs debouncing**

### 27.2 Algorithms (P0 — explain, compare, and code)
- [ ] **Token bucket** — capacity (burst) + refill rate; tokens consumed per request; allows bursts; most common (AWS, Stripe, Bucket4j, Guava)
- [ ] **Leaky bucket** — fixed outflow rate; as a queue (smooths traffic) or as a meter; Nginx `limit_req`
- [ ] **Fixed window counter** — simple, low memory; **boundary problem** (2× burst at window edges)
- [ ] **Sliding window log** — store timestamps (e.g., Redis sorted set); accurate; memory O(requests)
- [ ] **Sliding window counter** — weighted current + previous window; good approximation, low memory (Cloudflare)
- [ ] **GCRA** (Generic Cell Rate Algorithm) — single timestamp per key (redis-cell, Stripe-like)
- [ ] **Concurrency limiter** — semaphore on in-flight requests
- [ ] **Adaptive limits** — AIMD, gradient/Vegas-based (Netflix `concurrency-limits`), load-aware throttling
- [ ] **Comparison table** — accuracy, burst handling, memory, implementation complexity, distributed friendliness

### 27.3 Distributed Rate Limiting (P0)
- [ ] **Centralized store** — Redis counters: `INCR` + `EXPIRE` (fixed window), sorted sets (sliding log), **Lua scripts for atomic check-and-decrement** (token bucket)
- [ ] **Race conditions** in read-then-write; atomicity via Lua / `INCR` semantics
- [ ] **Latency overhead** of a network hop per request → local token buckets with periodic sync, batch token leasing, approximate counting
- [ ] **Hybrid local + global** limits (per-pod local limiter + global Redis limiter)
- [ ] **Consistency vs accuracy trade-off**; tolerating slight over-admission
- [ ] **Redis failure** — **fail-open vs fail-closed** decision; fallback to local limits
- [ ] **Multi-region** — per-region limits vs global sync (eventual), CRDT counters
- [ ] **Hot keys** in Redis (one huge tenant) → sharding keys
- [ ] **Rules management** — config store (DB/config service), hot reload, per-tier rules, overrides/allowlists
- [ ] **Observability** — metrics on throttled requests per key/rule, alerting, dashboards; shadow mode (log-only) before enforcing

### 27.4 Client-Facing Contract
- [ ] **HTTP 429 Too Many Requests** + `Retry-After`; **503** for load shedding
- [ ] Headers — `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`; IETF `RateLimit`/`RateLimit-Policy` headers draft
- [ ] Client behavior — exponential backoff with jitter, respecting `Retry-After`, client-side throttling

### 27.5 Implementations & Tools
- [ ] **Bucket4j** (JCache/Redis/Hazelcast backends) · **Resilience4j RateLimiter** · **Guava RateLimiter** (SmoothBursty / SmoothWarmingUp) · **Redisson RRateLimiter**
- [ ] **Spring Cloud Gateway `RequestRateLimiter`** (Redis token bucket, `KeyResolver`)
- [ ] **Nginx** `limit_req` / `limit_conn` · **Envoy** local & global rate limit service · **Kong**, **AWS API Gateway** (throttling, usage plans, API keys), Cloudflare rate limiting
- [ ] **DDoS protection** — L3/L4 (volumetric, SYN floods) vs L7 (HTTP floods); AWS Shield, Cloudflare, WAF rules, CAPTCHA challenges

### 27.6 Practice
- [ ] **Code** — thread-safe token bucket in Java (lazy refill on each request using `System.nanoTime`), fixed window, sliding window log, sliding window counter
- [ ] **LLD** — rate limiter with pluggable strategy, per-client config, thread-safety
- [ ] **HLD** — "Design a distributed rate limiter for an API platform serving 1M RPS": requirements, algorithm choice, where to place it, Redis cluster design, Lua script, failure handling, multi-region, monitoring

---

## 28. API Design (P0)

### 28.1 REST Fundamentals
- [ ] **REST constraints** — client-server, stateless, cacheable, uniform interface, layered system, code-on-demand; **Richardson Maturity Model** (levels 0–3, HATEOAS)
- [ ] **Resource naming** — nouns, plural, hierarchy (`/customers/{id}/orders`), avoid verbs (except actions like `/orders/{id}:cancel` or `/orders/{id}/cancellation`)
- [ ] **HTTP method semantics** — safe (GET, HEAD, OPTIONS) and **idempotent** (GET, PUT, DELETE, HEAD, OPTIONS); POST not idempotent; PATCH not guaranteed
- [ ] **PUT vs PATCH vs POST**; JSON Merge Patch (RFC 7396) vs JSON Patch (RFC 6902)
- [ ] **Status codes** — 200, **201 + Location**, **202 Accepted** (async), 204, 301/302/307/308, 304, 400, **401 vs 403**, 404, 405, **409 Conflict**, 410, **412 Precondition Failed**, 415, **422 Unprocessable**, **429**, 500, **502 vs 503 vs 504**
- [ ] **Error format** — RFC 9457 Problem Details (`type`, `title`, `status`, `detail`, `instance` + extensions: error code, traceId, field errors)

### 28.2 Practical API Design
- [ ] **Pagination** — offset/limit vs **cursor/keyset** (opaque next-page tokens); total counts cost; stable ordering
- [ ] **Filtering, sorting, field selection (sparse fieldsets), search**
- [ ] **Bulk & batch operations**, partial success reporting (207 Multi-Status)
- [ ] **Long-running operations** — 202 + status resource polling, callbacks/webhooks, SSE
- [ ] **Idempotency keys** for POST (Stripe model) — header, storage, TTL, fingerprinting request body, concurrent in-flight duplicates (409), replaying the stored response
- [ ] **Optimistic concurrency** — `ETag` + `If-Match` → 412
- [ ] **Caching** — `Cache-Control`, `ETag`, conditional GETs
- [ ] **Content negotiation**, compression (gzip/br), Unicode, date formats (ISO-8601 UTC), money (amount in minor units + currency), IDs as strings
- [ ] **Versioning** — URI (`/v1`), header, media type, query param; **deprecation** policy (`Deprecation`/`Sunset` headers); avoid versioning by evolving compatibly
- [ ] **Backward-compatible changes** — additive fields, optional params, never repurpose fields, tolerant reader, consumer-driven contracts
- [ ] **API-first** — OpenAPI spec as contract, code generation, mock servers, linting (Spectral), API style guides (Google AIP, Zalando, Microsoft)
- [ ] **Documentation & DX** — examples, error catalog, SDKs, changelogs, sandbox environments
- [ ] **Security** — authN/authZ per endpoint, object-level authorization, input validation, mass assignment protection (DTOs!), rate limits, no sensitive data in URLs, **OWASP API Security Top 10** (BOLA, broken authentication, BOPLA, unrestricted resource consumption, BFLA, SSRF, misconfiguration, improper inventory, unsafe consumption of APIs)
- [ ] **Webhooks design** — HMAC signatures + timestamp (replay protection), retries with backoff, idempotent receivers, event IDs, ordering not guaranteed, delivery logs, endpoint verification
- [ ] **Multi-tenant API concerns** — tenant scoping, per-tenant limits

### 28.3 gRPC (P1)
- [ ] **Protocol Buffers** — messages, field numbers (never reuse), optional/repeated, oneof, well-known types, schema evolution rules
- [ ] **HTTP/2 transport** — multiplexing, binary, header compression
- [ ] **RPC types** — unary, server streaming, client streaming, bidirectional streaming
- [ ] **Deadlines/timeouts**, cancellation, status codes, metadata, interceptors, retries (service config)
- [ ] **Load balancing challenges** — long-lived connections need L7/client-side LB (Envoy, xDS)
- [ ] gRPC-Web, gRPC-Gateway/transcoding, reflection, health checking
- [ ] **REST vs gRPC** — internal service-to-service (gRPC) vs public APIs (REST)

### 28.4 GraphQL (P1)
- [ ] Schema & types, queries, mutations, subscriptions, resolvers
- [ ] **N+1 problem & DataLoader** batching
- [ ] Over/under-fetching solved; **caching challenges** (POST, single endpoint) → persisted queries
- [ ] **Query complexity/depth limiting**, rate limiting by cost
- [ ] Federation (Apollo) / schema stitching for microservices
- [ ] Error handling (200 with errors), versioning (schema evolution, `@deprecated`)
- [ ] When GraphQL vs REST

### 28.5 Real-Time & Async APIs
- [ ] **Short polling vs long polling vs SSE vs WebSockets** — trade-offs, scaling, proxies/LB support
- [ ] **WebSocket scaling** — sticky sessions, connection registries, pub/sub fan-out (Redis/Kafka) across nodes, heartbeats, reconnection
- [ ] **AsyncAPI** spec for event-driven APIs
- [ ] SOAP/WSDL (legacy enterprise integrations) — awareness

### 🎯 Frequently Asked — API Design
- Design the REST API for an order management system (resources, methods, status codes, errors, pagination)
- How do you make a payment POST endpoint idempotent?
- How do you version APIs? How do you deprecate one used by 200 clients?
- REST vs gRPC vs GraphQL — when each?
- 401 vs 403; 502 vs 503 vs 504; PUT vs PATCH

---

# PART F — SYSTEM DESIGN (HLD)

## 29. System Design Interview Framework (P0)

> Senior/lead bar: **you drive** the conversation, quantify, make explicit trade-offs, go deep on 2–3 hard parts, and cover failure modes, operations, security, and evolution — without being prompted.

- [ ] **1. Requirements (5–8 min)** — functional (core features, prioritize 3–4; explicitly call out what's out of scope); non-functional (scale, latency targets p99, availability, consistency, durability, security/compliance, cost); users & read/write patterns
- [ ] **2. Estimation (3–5 min)** — DAU, QPS (avg & peak), read:write ratio, storage/year, bandwidth, cache size (§30)
- [ ] **3. API design (3–5 min)** — key endpoints/events with request/response, idempotency, pagination
- [ ] **4. Data model (5 min)** — entities, schema, DB choice with justification, partition/shard keys, indexes
- [ ] **5. High-level design (10 min)** — clients → DNS/CDN → LB → gateway → services → caches → DBs → queues → workers → storage; walk through main read & write flows
- [ ] **6. Deep dives (15–20 min)** — bottlenecks, scaling the hottest path, consistency/concurrency, hot keys, failure scenarios, data partitioning, caching strategy, async processing
- [ ] **7. Wrap-up (3–5 min)** — monitoring/alerting & SLOs, security, deployment, cost, future evolution, what you'd do differently at 10× scale
- [ ] **Communication habits** — think aloud, check in with interviewer, draw clean diagrams, state assumptions, "it depends → here's what it depends on → here's my choice"
- [ ] **Common senior-level signals** — trade-off articulation, operational maturity, simplicity first then scale, data-driven numbers, recognizing when *not* to add a component

---

## 30. Back-of-the-Envelope Estimation (P0)

- [ ] **Powers of 2 / 10** — 2¹⁰ ≈ 1 thousand (KB), 2²⁰ ≈ 1 million (MB), 2³⁰ ≈ 1 billion (GB), 2⁴⁰ ≈ 1 trillion (TB), PB
- [ ] **Time** — 1 day ≈ 86,400 s ≈ **10⁵ s**; 1 month ≈ 2.5 × 10⁶ s; 1 year ≈ 3 × 10⁷ s
- [ ] **QPS** — DAU × actions per user ÷ 86,400; peak ≈ 2–5× average
- [ ] **Storage** — writes/day × object size × retention × replication factor
- [ ] **Bandwidth** — QPS × payload size (ingress vs egress)
- [ ] **Cache memory** — 20% of daily read volume (80/20 rule)
- [ ] **Servers needed** — peak QPS ÷ per-server capacity (e.g., ~1–5k RPS for a typical Java API pod, depends on work)
- [ ] **Latency numbers every engineer should know** (orders of magnitude):
  - L1 cache ~1 ns · L2 ~4 ns · mutex lock ~20–100 ns · main memory ~100 ns
  - Compress 1 KB (fast codec) ~2 µs · read 1 MB sequentially from memory ~3–10 µs
  - SSD random read ~16–150 µs · read 1 MB from SSD ~50–200 µs
  - Round trip within same datacenter ~0.5 ms · read 1 MB over 1 Gbps network ~10 ms
  - HDD seek ~2–10 ms · read 1 MB from HDD ~1–20 ms
  - Cross-continent round trip ~100–150 ms
- [ ] **Typical capacities** (rough) — a Redis node ~100k+ ops/s; a well-tuned Postgres primary ~10k–50k simple TPS; a Kafka partition ~10 MB/s+; a single Kafka broker 100s of MB/s
- [ ] **Practice** — estimate for Twitter, YouTube, WhatsApp, URL shortener, Uber location updates

---

## 31. System Design Building Blocks & Techniques (P0)

### 31.1 Components (know purpose, how it scales, failure modes, and tech choices)
- [ ] **DNS** — resolution, TTLs, GeoDNS/latency-based routing, DNS failover
- [ ] **CDN** — static & dynamic content, edge caching (§20.7)
- [ ] **Load balancer** — L4 (TCP) vs L7 (HTTP); algorithms (round robin, weighted, least connections, least response time, IP hash, consistent hashing, power of two choices); health checks; sticky sessions; TLS termination; HA pairs; global server load balancing; Anycast
- [ ] **Reverse proxy** — Nginx, HAProxy, Envoy; buffering, compression, caching
- [ ] **API gateway** (§15.3)
- [ ] **Stateless application tier** — externalize sessions, horizontal autoscaling
- [ ] **Cache** (§20) · **Relational DB** (§18) · **NoSQL** (§19) · **Search** (§19.6) · **Object storage** (§19.8)
- [ ] **Message queue / event stream** (§21)
- [ ] **Workers & job queues** — async processing, scheduling, retries, priority queues
- [ ] **Distributed scheduler / cron**
- [ ] **Unique ID generator** (§22.9) · **Rate limiter** (§27)
- [ ] **Service discovery & config service** · **Feature flag service**
- [ ] **Notification service** (push/email/SMS via providers: APNs, FCM, SES, Twilio)
- [ ] **Monitoring/logging/tracing stack** (§39)
- [ ] **Analytics pipeline / data warehouse** (§33)
- [ ] **Blob processing pipelines** (thumbnailing, transcoding)
- [ ] **Coordination service** — ZooKeeper/etcd

### 31.2 Scaling Techniques
- [ ] Vertical vs horizontal scaling; stateless services
- [ ] **Replication** (read scaling, HA), **partitioning/sharding** (write scaling)
- [ ] **Caching** at every layer; **CDN** for static/media
- [ ] **Async processing** & queues to absorb spikes
- [ ] **Denormalization & precomputation** — materialized views, counters, aggregates
- [ ] **Fan-out on write (push) vs fan-out on read (pull)** vs hybrid (celebrity/hot users)
- [ ] **Batching & compression**, connection pooling, keep-alive
- [ ] **Autoscaling** — reactive (CPU/RPS/queue-depth based) vs scheduled/predictive; scale-in safety
- [ ] **Multi-region** deployments — latency, data residency, active-active conflicts
- [ ] **Read-heavy vs write-heavy** design strategies (e.g., write-heavy → LSM stores, append-only logs, batching, Kafka buffering)

### 31.3 Communication Patterns
- [ ] Request/response vs async messaging vs streaming
- [ ] Client ↔ server real-time — polling, long polling, SSE, WebSockets (§28.5)
- [ ] Push notifications (mobile), webhooks (server-to-server)

### 31.4 Storage Selection Cheat Sheet
- [ ] Structured + transactions + joins → **RDBMS** (Postgres/MySQL/Aurora)
- [ ] Massive write throughput, simple key access, multi-DC → **Cassandra/DynamoDB**
- [ ] Flexible documents → **MongoDB**
- [ ] Low-latency ephemeral/hot data → **Redis**
- [ ] Full-text/fuzzy search & faceting → **Elasticsearch/OpenSearch**
- [ ] Blobs/media/backups → **S3**
- [ ] Time-series metrics → **Prometheus/TimescaleDB/InfluxDB**
- [ ] Analytics/OLAP → **ClickHouse/BigQuery/Redshift/Snowflake/Druid/Pinot**
- [ ] Relationships/graph traversals → **Neo4j/Neptune**
- [ ] Semantic similarity → **vector DB / pgvector**
- [ ] Event log / stream → **Kafka**

### 31.5 Specialized Techniques (frequently needed in deep dives)
- [ ] **Geospatial indexing** — geohash, quadtree, Google S2, Uber H3, R-tree, PostGIS, Redis GEO
- [ ] **Full-text search** — inverted index, tokenization, ranking
- [ ] **Autocomplete** — trie with top-K per node, prefix caching, Elasticsearch completion suggester
- [ ] **Top-K / heavy hitters** — count-min sketch + heap, stream processing with windowing
- [ ] **Counting at scale** — sharded counters, approximate (HLL), batching increments
- [ ] **Leaderboards** — Redis sorted sets, sharding by score range
- [ ] **Feed generation & ranking** — fan-out, timelines in Redis, ranking signals
- [ ] **Deduplication** — Bloom filters, content hashing (SHA-256), idempotency keys
- [ ] **Chunking & delta sync** — content-defined chunking, rolling hashes (Dropbox/rsync)
- [ ] **Video pipeline** — upload → transcode (multiple bitrates/codecs) → segment → CDN; adaptive bitrate (HLS/DASH)
- [ ] **Collaborative editing** — Operational Transformation (OT) vs CRDTs
- [ ] **Presence & online status** — heartbeats, TTL keys, pub/sub
- [ ] **Seat/inventory reservation under contention** — pessimistic locks, optimistic CAS, Redis atomic decrements, temporary holds with TTL, virtual waiting rooms/queues
- [ ] **Money movement** — double-entry ledger, immutable journal, idempotency, reconciliation, eventual settlement, exactly-once illusions
- [ ] **Scheduling at scale** — time-bucketed tables, delay queues, hierarchical timing wheels
- [ ] **Sharded counters / like counts**, write-behind aggregation
- [ ] **Bloom filters for "has the user seen this"**, **HyperLogLog for unique visitors**
- [ ] **Consistent hashing** for cache/storage node placement

---

## 32. Classic System Design Problems (P0)

> For each: requirements → estimates → APIs → data model → HLD → 2–3 deep dives → failure handling → monitoring. Practice **at least 25** end-to-end, out loud, with a timer.

| # | Problem | Key deep-dive topics |
|---|---------|----------------------|
| 1 | [ ] **URL Shortener (TinyURL/bit.ly)** | ID generation (base62, counter vs hash, KGS), 301 vs 302, caching hot links, analytics pipeline, custom aliases, expiry |
| 2 | [ ] **Pastebin** | Object storage for blobs, metadata DB, expiry cleanup |
| 3 | [ ] **Distributed Rate Limiter** | Algorithm choice, Redis + Lua, placement, fail-open, multi-region (§27) |
| 4 | [ ] **Distributed Key-Value Store (Dynamo)** | Consistent hashing, replication, quorum, vector clocks, gossip, hinted handoff, Merkle trees |
| 5 | [ ] **Distributed Cache (Memcached/Redis)** | Partitioning, eviction, replication, hot keys, consistency |
| 6 | [ ] **Unique ID Generator** | Snowflake, clock skew, sortable IDs |
| 7 | [ ] **Web Crawler** | URL frontier & prioritization, politeness, dedupe (Bloom filter, content hash), robots.txt, DNS caching, distributed workers, traps |
| 8 | [ ] **Notification System** | Multi-channel (push/SMS/email), templates, user preferences, priority queues, retries, rate limits per provider, dedupe, tracking |
| 9 | [ ] **News Feed / Twitter Timeline** | Fan-out on write vs read, celebrity problem (hybrid), timeline cache, ranking, pagination |
| 10 | [ ] **Instagram / Photo Sharing** | Media upload (pre-signed URLs), processing pipeline, CDN, feed, follower graph |
| 11 | [ ] **Chat System (WhatsApp/Slack/Messenger)** | WebSockets & connection gateways, message ordering (per-conversation sequence), delivery/read receipts, offline sync, group fan-out, presence, storage (Cassandra/HBase), E2E encryption |
| 12 | [ ] **Search Autocomplete / Typeahead** | Trie with top-K, data collection pipeline, caching at CDN/browser, personalization |
| 13 | [ ] **YouTube / Netflix (video streaming)** | Upload & transcoding DAG, adaptive bitrate, CDN/Open Connect, metadata, view counts, recommendations (high level) |
| 14 | [ ] **Google Drive / Dropbox (file sync)** | Chunking, dedupe, delta sync, metadata DB, conflict resolution, notifications via long poll, versioning |
| 15 | [ ] **Uber / Lyft (ride hailing)** | Location ingestion at scale, geospatial index (geohash/H3/quadtree), matching/dispatch, trip state machine, surge pricing, ETA |
| 16 | [ ] **Yelp / Proximity Service (nearby places)** | Geospatial indexing, read-heavy caching, search radius expansion |
| 17 | [ ] **Google Maps (awareness)** | Tiles, routing graph (Dijkstra/A*/contraction hierarchies), traffic, ETA |
| 18 | [ ] **Ticketmaster / BookMyShow** | Seat locking with TTL holds, high contention flash sales, virtual waiting room, idempotent booking, payment timeout handling |
| 19 | [ ] **Hotel / Airbnb Reservation** | Inventory per date, double-booking prevention (constraints/locks), overbooking policies, search with availability |
| 20 | [ ] **E-commerce (Amazon)** | Catalog, search, cart, checkout saga, inventory reservation, order state machine, flash sales, recommendations |
| 21 | [ ] **Payment System (Stripe/PayPal/Razorpay)** | Idempotency keys, PSP integration, double-entry ledger, state machine, retries & reconciliation, webhooks, exactly-once money movement, PCI scope |
| 22 | [ ] **Digital Wallet / P2P Money Transfer** | Ledger, balance consistency, distributed transactions (saga/TCC), event sourcing, audit, fraud checks |
| 23 | [ ] **Stock Exchange / Order Matching Engine** | Order book data structures, price-time priority, low latency, sequencer, event sourcing, market data fan-out |
| 24 | [ ] **Distributed Job Scheduler (cron at scale / Airflow)** | Time-partitioned task storage, leader election, at-least-once execution, idempotent jobs, retries, DAG dependencies |
| 25 | [ ] **Distributed Message Queue (Kafka-like)** | Partitions, append-only log, replication & ISR, consumer groups & offsets, retention |
| 26 | [ ] **Metrics Monitoring & Alerting (Datadog/Prometheus)** | Time-series storage, push vs pull, downsampling, cardinality, alert evaluation, dashboards |
| 27 | [ ] **Centralized Logging (ELK)** | Ingestion agents, buffering via Kafka, indexing, retention tiers, querying, cost |
| 28 | [ ] **Ad Click Aggregation** | Stream processing (Flink), windowing, exactly-once, late data/watermarks, reconciliation with batch, OLAP store |
| 29 | [ ] **Top-K Trending (heavy hitters)** | Count-min sketch, sliding windows, MapReduce/stream hybrid |
| 30 | [ ] **Real-time Gaming Leaderboard** | Redis sorted sets, sharding, ties, historical leaderboards |
| 31 | [ ] **Google Docs (collaborative editing)** | OT vs CRDT, WebSockets, document versioning, presence/cursors |
| 32 | [ ] **Email Service (Gmail)** | SMTP ingestion, storage, search indexing, spam filtering, attachments |
| 33 | [ ] **Distributed File System (GFS/HDFS)** | Master/metadata, chunk servers, replication, leases |
| 34 | [ ] **Web Search Engine (high level)** | Crawling, indexing, ranking, serving |
| 35 | [ ] **Food Delivery (Swiggy/Zomato/DoorDash)** | Restaurant search, order lifecycle, delivery partner assignment, live tracking, ETAs |
| 36 | [ ] **Online Judge (LeetCode)** | Sandboxed code execution, queueing, scaling workers, security isolation |
| 37 | [ ] **Live Streaming & Live Comments (Twitch/FB Live)** | Ingest, transcoding, low-latency delivery, comment fan-out at scale |
| 38 | [ ] **API Gateway** | Routing, auth, rate limiting, plugins, config propagation, HA |
| 39 | [ ] **Feature Flag / Remote Config Service** | Low-latency evaluation (SDK local cache), streaming updates, targeting rules, audit |
| 40 | [ ] **Coupon / Promotion / Loyalty System** | Rule engine, redemption limits under concurrency, idempotency, abuse prevention |
| 41 | [ ] **Distributed Lock Service (Chubby)** | Consensus, leases, fencing tokens |
| 42 | [ ] **Webhook Delivery Platform** | Retries with backoff, per-endpoint queues, signing, DLQ, observability for customers |
| 43 | [ ] **Multi-tenant SaaS Platform** | Tenant isolation models, noisy neighbors, per-tenant limits, data partitioning |
| 44 | [ ] **Recommendation System (high level)** | Candidate generation, ranking, feature store, offline/online pipelines |
| 45 | [ ] **Inventory Management / Flash Sale** | Pre-allocation, Redis atomic counters, queue-based ordering, oversell prevention |
| 46 | [ ] **LLM Chat App / RAG Service (2026)** | Streaming tokens (SSE), conversation storage, vector retrieval, LLM gateway (rate limits, fallback models, caching), cost control, guardrails |
| 47 | [ ] **Bulk File Import (e.g., 10 GB CSV upload)** | Pre-signed upload, chunked parallel processing, Spring Batch, progress tracking, partial failures, idempotent re-runs |
| 48 | [ ] **Audit Log / Activity Feed System** | Append-only, immutability, query patterns, retention |

---

## 33. Data Engineering & Stream Processing (P1)

- [ ] **OLTP vs OLAP**; row vs columnar storage
- [ ] **Batch processing** — MapReduce concepts, Apache Spark (RDD/DataFrame, partitions, shuffles), when batch suffices
- [ ] **Stream processing** — Apache Flink, Kafka Streams, Spark Structured Streaming; event time vs processing time; **windowing** (tumbling, sliding/hopping, session); **watermarks & late data**; stateful processing & checkpoints; exactly-once
- [ ] **Lambda vs Kappa architecture**
- [ ] **ETL vs ELT**; orchestration with **Airflow**/Dagster; dbt
- [ ] **Data warehouses** — Snowflake, BigQuery, Redshift; star/snowflake schema, fact & dimension tables, SCD types
- [ ] **Data lakes & lakehouses** — S3 + Parquet/ORC, Apache Iceberg/Delta Lake/Hudi (ACID tables, time travel)
- [ ] **Real-time OLAP** — ClickHouse, Druid, Pinot
- [ ] **CDC pipelines** — Debezium → Kafka → sinks (warehouse, search, cache)
- [ ] **Data quality, lineage, schema evolution**, PII governance
- [ ] **Feature stores** & ML pipelines (awareness)

---

# PART G — INFRASTRUCTURE & OPERATIONS

## 34. Networking (P0)

- [ ] **OSI vs TCP/IP model** — which layer each protocol/device lives on (L4 vs L7 load balancers!)
- [ ] **IP addressing** — IPv4/IPv6, CIDR notation, subnets, private ranges (10/8, 172.16/12, 192.168/16), NAT, public vs private IPs
- [ ] **TCP** — 3-way handshake, 4-way teardown, **TIME_WAIT** & port exhaustion, sequence numbers & ACKs, retransmission, flow control (receive window), congestion control (slow start, AIMD, CUBIC, BBR), Nagle's algorithm & `TCP_NODELAY`, keep-alive, head-of-line blocking, SYN floods
- [ ] **UDP** — connectionless, use cases (DNS, video, gaming, QUIC)
- [ ] **Sockets & ports** — ephemeral ports, `SO_REUSEADDR`, backlog/accept queue, file descriptors per connection
- [ ] **HTTP/1.0 → 1.1** (persistent connections, chunked transfer, pipelining issues, Host header)
- [ ] **HTTP/2** — binary framing, multiplexed streams, HPACK, flow control, (server push deprecated); TCP-level HOL blocking remains
- [ ] **HTTP/3 & QUIC** — over UDP, 0-RTT, connection migration, no TCP HOL blocking
- [ ] **HTTP semantics** — methods, status codes, headers (`Host`, `Content-Type`, `Accept`, `Authorization`, `Cache-Control`, `Connection`, `X-Forwarded-For`, `Forwarded`), cookies (`Secure`, `HttpOnly`, `SameSite`, `Domain`, `Path`)
- [ ] **TLS/HTTPS** — TLS 1.2 vs 1.3 handshake (1-RTT, 0-RTT), certificates, CA chain & trust stores, SNI, session resumption, cipher suites, perfect forward secrecy, **mTLS**, cert rotation & expiry incidents, TLS termination at LB vs end-to-end, Java keystore/truststore
- [ ] **DNS** — recursive vs authoritative resolvers, resolution flow, record types (A, AAAA, CNAME, ALIAS, MX, TXT, NS, SOA, SRV, PTR), TTL & caching, DNS-based load balancing & failover, GeoDNS, JVM DNS caching (`networkaddress.cache.ttl`)
- [ ] **"What happens when you type a URL into the browser?"** — full answer: DNS → TCP → TLS → HTTP request → LB → server → response → rendering
- [ ] **Proxies** — forward vs reverse proxy; transparent proxy; sidecar proxy
- [ ] **Load balancers** — L4 vs L7, connection draining, health checks, preserving client IP (Proxy Protocol, `X-Forwarded-For`)
- [ ] **CDN & Anycast**
- [ ] **WebSockets** — upgrade handshake, framing, ping/pong, scaling (§28.5); **SSE**; long polling
- [ ] **CORS** — same-origin policy, simple vs preflight requests, `Access-Control-*` headers
- [ ] **Network security** — firewalls, security groups vs NACLs, VPN, bastion hosts, private links, zero trust
- [ ] **Latency vs bandwidth vs throughput**, RTT, MTU/fragmentation, packet loss impact
- [ ] **Connection pooling & keep-alive** — why reusing connections matters (TLS handshakes are expensive)
- [ ] **Tools** — `curl -v`, `dig`, `nslookup`, `ping`, `traceroute`/`mtr`, `netstat`/`ss`, `tcpdump`, Wireshark, `nc`, `openssl s_client`, `lsof -i`

### 🎯 Frequently Asked — Networking
- What happens when you type `https://google.com` and press enter?
- TCP vs UDP; HTTP/1.1 vs HTTP/2 vs HTTP/3
- How does TLS work? What is mTLS and where would you use it?
- L4 vs L7 load balancer — which would you choose for gRPC and why?
- What is TIME_WAIT and how can it cause outages?

---

## 35. Operating Systems & Linux (P1)

### 35.1 OS Concepts
- [ ] Process vs thread; process states; PCB; context switching; scheduling (CFS)
- [ ] User mode vs kernel mode; system calls
- [ ] **Virtual memory**, paging, page tables, TLB, page faults, swapping, thrashing
- [ ] **Page cache** & its role in databases/Kafka; `fsync` and durability
- [ ] **Memory-mapped files**
- [ ] **File descriptors** & `ulimit -n` ("Too many open files")
- [ ] **I/O models** — blocking, non-blocking, I/O multiplexing (`select`/`poll`/**`epoll`**), signal-driven, async I/O (`io_uring`) — basis of Netty/NIO
- [ ] **Signals** — SIGTERM (graceful) vs SIGKILL (no cleanup) vs SIGINT vs SIGHUP; JVM shutdown hooks
- [ ] **cgroups & namespaces** — the foundation of containers; CPU shares/quotas & throttling
- [ ] **OOM killer**, overcommit
- [ ] Inodes, hard vs soft links, permissions (rwx, chmod, chown, umask), sticky bit
- [ ] Concurrency primitives at OS level — mutex, semaphore, spinlock, futex
- [ ] Deadlock conditions (OS view)

### 35.2 Linux Commands for Backend Engineers
- [ ] **Processes & resources** — `top`/`htop` (`-H` for threads), `ps aux`, `pidstat`, `uptime` (load average meaning), `free -m`, `vmstat`, `iostat`, `sar`, `mpstat`
- [ ] **Files & disk** — `df -h`, `du -sh`, `lsof`, `find`, `ncdu`, log rotation (`logrotate`)
- [ ] **Text processing** — `grep`, `awk`, `sed`, `sort`, `uniq -c`, `cut`, `wc`, `head`/`tail -f`, `less`, `jq`, `xargs`
- [ ] **Network** — `ss -tanp`, `netstat`, `curl`, `dig`, `tcpdump`, `iptables` (awareness)
- [ ] **Debugging** — `strace`, `perf`, `dmesg`, `journalctl`, `kill -3` (thread dump for JVM)
- [ ] **Misc** — `ssh`, `scp`, `rsync`, `tmux`, `cron`/`crontab`, `systemctl`, `nohup`, `chmod`, environment variables, shell scripting basics

### 35.3 Debugging Scenarios
- [ ] High CPU · high memory/swap · disk full (deleted-but-open files!) · too many open files · high load with low CPU (I/O wait) · zombie processes · port already in use · slow DNS

---

## 36. Docker & Kubernetes (P0)

### 36.1 Docker / Containers
- [ ] **Containers vs VMs**; images vs containers; layers & union filesystem; registries
- [ ] **Dockerfile best practices** — multi-stage builds, minimal base images (distroless, slim; alpine/musl caveats for Java), layer ordering for cache hits, `.dockerignore`, non-root user, pin versions, `HEALTHCHECK`, `ENTRYPOINT` vs `CMD`, exec form (signals reach PID 1)
- [ ] **Java in containers** — container-aware JVM (`MaxRAMPercentage`), CPU limits affecting GC/JIT threads and `availableProcessors`, Spring Boot layered jars, jlink custom runtimes, image size optimization
- [ ] **Networking** — bridge, host, overlay; port mapping
- [ ] **Volumes** & bind mounts; stateless containers
- [ ] **Docker Compose** for local dev
- [ ] **Image security** — scanning (Trivy, Grype), signing (cosign), SBOMs, minimal attack surface
- [ ] Container runtimes — containerd, CRI-O; OCI spec (awareness)

### 36.2 Kubernetes
- [ ] **Architecture** — control plane (kube-apiserver, etcd, scheduler, controller-manager, cloud-controller-manager) & nodes (kubelet, kube-proxy, container runtime); reconciliation loop / desired state
- [ ] **Workloads** — Pod, ReplicaSet, **Deployment**, **StatefulSet** (stable identity, ordered, PVC per pod — for DBs/Kafka), DaemonSet, Job, CronJob
- [ ] **Networking** — Service types (ClusterIP, NodePort, LoadBalancer, headless, ExternalName), kube-proxy (iptables/IPVS), CoreDNS, **Ingress** & Ingress controllers (NGINX, ALB), **Gateway API**, NetworkPolicies, CNI plugins (Calico, Cilium)
- [ ] **Config** — ConfigMaps, Secrets (base64 ≠ encrypted; external secrets operator, sealed secrets, Vault)
- [ ] **Storage** — Volumes, PV, PVC, StorageClass, dynamic provisioning
- [ ] **Probes** — liveness (restart), readiness (remove from Service endpoints), startup (slow-starting JVMs); map to Spring Boot actuator health groups; common misconfigurations (liveness checking DB → restart storms)
- [ ] **Resources** — requests vs limits, QoS classes (Guaranteed, Burstable, BestEffort), **CPU throttling** (CFS quota) hurting JVM latency, memory limit → **OOMKilled (exit 137)**, right-sizing
- [ ] **Autoscaling** — **HPA** (CPU/memory/custom metrics), VPA, Cluster Autoscaler/Karpenter, **KEDA** (scale on Kafka lag/queue depth)
- [ ] **Deployments** — rolling updates (`maxSurge`, `maxUnavailable`), rollbacks, blue-green & canary (Argo Rollouts, Flagger), readiness gates
- [ ] **Graceful shutdown** — SIGTERM → preStop hook (sleep to let endpoints update) → app drains → `terminationGracePeriodSeconds` → SIGKILL
- [ ] **Scheduling** — node selectors, affinity/anti-affinity (spread replicas across AZs), taints & tolerations, topology spread constraints, priority & preemption
- [ ] **Availability** — PodDisruptionBudgets, multiple replicas, multi-AZ node groups
- [ ] **Security** — RBAC, ServiceAccounts, Pod Security Standards, IRSA/Workload Identity, image policies, network policies
- [ ] **Packaging** — **Helm** (charts, values, templating, releases), Kustomize (overlays)
- [ ] **Operators & CRDs** (Strimzi for Kafka, Postgres operators)
- [ ] **Service mesh** on K8s (Istio/Linkerd)
- [ ] **Observability** — kube-state-metrics, Prometheus Operator, logging via DaemonSets (Fluent Bit)
- [ ] **Troubleshooting** — `kubectl get/describe/logs (--previous)/exec/top/port-forward/events`; CrashLoopBackOff, ImagePullBackOff, Pending (insufficient resources/affinity), OOMKilled, readiness failing, DNS issues, evictions
- [ ] Managed K8s — EKS, GKE, AKS

### 🎯 Frequently Asked — Containers/K8s
- How do you configure probes for a Spring Boot service? What happens if liveness checks the DB?
- Your pod keeps getting OOMKilled but heap is only 60% — why? (metaspace, threads, direct memory, native)
- How do you achieve zero-downtime deployments in Kubernetes?
- Requests vs limits — should you set CPU limits for JVM services?
- How do you scale consumers based on Kafka lag?

---

## 37. CI/CD, DevOps & IaC (P1)

- [ ] **CI pipeline stages** — checkout → build → unit tests → static analysis → SCA/SAST → package → container build & scan → integration/contract tests → publish artifact → deploy to env → smoke tests → promote
- [ ] **Tools** — Jenkins (pipelines as code), GitHub Actions, GitLab CI, CircleCI, Tekton; artifact repos (Nexus, Artifactory, ECR)
- [ ] **CD & GitOps** — ArgoCD, Flux; declarative environments; drift detection
- [ ] **Branching strategies** — **trunk-based development** vs GitFlow vs GitHub flow; short-lived branches; feature flags for incomplete work
- [ ] **Release strategies** — rolling, blue-green, canary (automated analysis), A/B, dark launches, shadow traffic, ring deployments
- [ ] **Rollback strategy** — fast rollback, roll-forward, DB compatibility (expand/contract)
- [ ] **Feature flags** — LaunchDarkly, Unleash, Flagsmith, OpenFeature; flag hygiene & cleanup; kill switches
- [ ] **Versioning** — SemVer, release notes, changelogs, conventional commits
- [ ] **Infrastructure as Code** — **Terraform** (providers, state & remote backends, locking, modules, plan/apply, drift, workspaces), CloudFormation/CDK, Pulumi; immutable infrastructure
- [ ] **Configuration management** — Ansible/Chef/Puppet (awareness)
- [ ] **Secrets in pipelines** — OIDC federation to cloud (no long-lived keys), Vault, secret scanning (gitleaks)
- [ ] **Supply chain security** — SBOM (CycloneDX/SPDX), signing (Sigstore/cosign), SLSA levels, dependency pinning, Dependabot/Renovate
- [ ] **DORA metrics** — deployment frequency, lead time for changes, change failure rate, time to restore (MTTR)
- [ ] **Environments** — dev/QA/staging/prod parity, ephemeral preview environments
- [ ] **Platform engineering** — internal developer platforms, golden paths, Backstage (awareness)

---

## 38. Cloud (AWS-first) (P1)

> Map each AWS service to its GCP/Azure equivalent if your target companies use those.

- [ ] **Fundamentals** — regions, AZs, edge locations; shared responsibility model; pricing models
- [ ] **Compute** — EC2 (instance families, AMIs, Auto Scaling Groups, spot/on-demand/reserved), **Lambda** (cold starts, Java SnapStart, concurrency & reserved concurrency, timeouts, event sources), **ECS/Fargate**, **EKS**, Elastic Beanstalk/App Runner (P2)
- [ ] **Networking** — **VPC**, public/private subnets, route tables, Internet Gateway, **NAT Gateway** (cost!), security groups (stateful) vs NACLs (stateless), VPC peering, Transit Gateway, **PrivateLink/VPC endpoints**, **Route 53** (routing policies: simple, weighted, latency, failover, geolocation), **CloudFront**, **ALB vs NLB** vs GWLB, **API Gateway** (REST vs HTTP APIs, throttling, usage plans, authorizers), Global Accelerator
- [ ] **Storage** — **S3** (§19.8), EBS (gp3, io2), EFS, FSx, Glacier, Storage Gateway
- [ ] **Databases** — **RDS** (Multi-AZ standby vs read replicas), **Aurora** (storage architecture, replicas, Serverless v2, Global Database), **DynamoDB** (§19.2), **ElastiCache/MemoryDB**, DocumentDB, Keyspaces, Neptune, **OpenSearch**, Redshift, Timestream
- [ ] **Integration** — **SQS**, **SNS**, **EventBridge**, **Kinesis**, **MSK**, **Step Functions**, Amazon MQ, AppSync
- [ ] **Security & identity** — **IAM** (users, groups, roles, policies, least privilege, assume role, permission boundaries, SCPs), IRSA/EKS Pod Identity, **KMS** (envelope encryption), **Secrets Manager** vs Parameter Store, **Cognito**, **WAF**, **Shield**, GuardDuty, Security Hub, ACM (certificates), Macie
- [ ] **Observability** — **CloudWatch** (metrics, logs, alarms, Logs Insights), **X-Ray**, **CloudTrail** (audit), AWS Config
- [ ] **Well-Architected Framework** — 6 pillars: operational excellence, security, reliability, performance efficiency, cost optimization, sustainability
- [ ] **Cost optimization** — Savings Plans/RIs, spot, right-sizing, autoscaling, S3 lifecycle, **data transfer costs** (cross-AZ, NAT, egress), Graviton (ARM) instances
- [ ] **Multi-account strategy** — AWS Organizations, Control Tower (awareness)
- [ ] **DR on AWS** — backup/restore, pilot light, warm standby, multi-site active-active; cross-region replication (S3 CRR, Aurora Global, DynamoDB Global Tables)
- [ ] **Certifications** (optional signal) — AWS Solutions Architect Associate/Professional

---

## 39. Observability (P0)

### 39.1 Concepts
- [ ] **Monitoring vs observability** (known unknowns vs unknown unknowns)
- [ ] **Three pillars** — logs, metrics, traces (+ profiles, events)
- [ ] **Four Golden Signals** — latency, traffic, errors, saturation
- [ ] **RED method** (services) — Rate, Errors, Duration; **USE method** (resources) — Utilization, Saturation, Errors

### 39.2 Logging
- [ ] **Structured (JSON) logging**, consistent fields (timestamp, level, service, traceId, spanId, userId/tenantId where safe)
- [ ] **Log levels** discipline; what to log at INFO vs DEBUG; don't log in tight loops
- [ ] **Correlation IDs / trace IDs** via MDC, propagated across HTTP & messaging
- [ ] **PII/secret masking**, compliance
- [ ] **Aggregation stacks** — ELK/EFK (Elasticsearch, Logstash/Fluentd/Fluent Bit, Kibana), Grafana Loki, Splunk, CloudWatch Logs, Datadog
- [ ] **Cost control** — sampling, retention tiers, dropping noisy logs
- [ ] **Audit logs** vs application logs

### 39.3 Metrics
- [ ] Metric types — counter, gauge, histogram, summary
- [ ] **Percentiles (p50/p95/p99/p999) vs averages**; why you can't average percentiles; histograms for aggregation
- [ ] **Cardinality** — label explosion and its cost
- [ ] **Prometheus** — pull model, scraping, exporters, PromQL basics (`rate`, `histogram_quantile`, `sum by`), recording rules, Alertmanager; long-term storage (Thanos, Cortex/Mimir, VictoriaMetrics)
- [ ] **Grafana** dashboards — service overview, dependency health, JVM, DB pool, Kafka lag
- [ ] **What to measure in a Java service** — request rate/latency/errors per endpoint, JVM heap/GC pauses/threads, connection pool active/pending, thread pool queue sizes, cache hit ratio, Kafka consumer lag, downstream call latency, business KPIs (orders/min, payment success rate)

### 39.4 Distributed Tracing
- [ ] Traces, spans, parent/child, span attributes & events
- [ ] **Context propagation** — W3C `traceparent`/`tracestate`, B3 headers; across Kafka (headers) and thread pools
- [ ] **Sampling** — head-based vs tail-based; probabilistic; always sample errors
- [ ] **OpenTelemetry** — API/SDK, auto-instrumentation Java agent, OTel Collector (receivers, processors, exporters), OTLP; semantic conventions
- [ ] Backends — Jaeger, Zipkin, Grafana Tempo, Datadog APM, AWS X-Ray, Honeycomb
- [ ] Using traces to find the critical path & N+1 remote calls

### 39.5 SRE Practices
- [ ] **SLI / SLO / SLA** definitions with examples (e.g., 99.9% of requests < 300 ms over 30 days)
- [ ] **Error budgets** & error budget policies (freeze releases when exhausted)
- [ ] **Burn-rate alerting** (multi-window, multi-burn-rate)
- [ ] **Alerting philosophy** — alert on symptoms not causes, actionable alerts only, avoid alert fatigue, every alert has a runbook
- [ ] **Dashboards** design (top-down: business → service → infrastructure)
- [ ] **Synthetic monitoring**, uptime checks, RUM (awareness)
- [ ] **Continuous profiling** (Pyroscope, Datadog profiler), **exception tracking** (Sentry)
- [ ] **APM tools** — Datadog, New Relic, Dynatrace, AppDynamics, Elastic APM

### 🎯 Frequently Asked — Observability
- How do you know your service is healthy? What dashboards and alerts do you have?
- p99 latency doubled after a deploy — walk me through the investigation
- Define SLOs for a payments API; how do you alert on them?
- How do you trace a request through Kafka consumers?

---

## 40. Performance Engineering (P0)

- [ ] **Methodology** — define goals (SLOs), measure baseline, find the bottleneck (CPU, memory/GC, I/O, network, locks, DB, downstream), change one thing, re-measure; avoid premature optimization
- [ ] **Laws** — Little's Law, Amdahl's Law, Universal Scalability Law
- [ ] **Latency vs throughput**; **tail latency** and its causes (GC, queueing, noisy neighbors, cold caches, retries)
- [ ] **Load testing** — types: load, stress, soak/endurance, spike, breakpoint/capacity; tools: **Gatling**, **JMeter**, **k6**, Locust; realistic data & traffic mix; **coordinated omission**; testing in prod-like environments; open vs closed workload models
- [ ] **Capacity planning** — headroom, growth projections, per-instance throughput, autoscaling thresholds
- [ ] **JVM performance** — reduce allocation rate, right GC, heap sizing, JIT warm-up, avoid excessive logging/reflection/exceptions, string handling, boxing, efficient collections (pre-size), escape analysis friendliness
- [ ] **Profiling** — async-profiler (CPU, alloc, lock, wall), JFR, flame graphs; finding lock contention & hot methods
- [ ] **Benchmarking** — **JMH** (warm-up, forks, blackholes, dead-code elimination pitfalls)
- [ ] **Application-level** — connection pooling, HTTP keep-alive, batching (DB & Kafka), caching, async/non-blocking I/O, parallelizing independent remote calls, pagination, streaming large responses, compression, payload size reduction, efficient serialization (Protobuf vs JSON), avoid N+1 (DB & HTTP), lazy loading where appropriate
- [ ] **Database-level** — indexes, query plans, connection pool sizing, read replicas, denormalization, partitioning, avoiding long transactions & lock contention
- [ ] **Thread pool & connection pool tuning** with Little's Law
- [ ] **Network** — reduce round trips, co-locate services, HTTP/2, CDN
- [ ] **Have a performance story ready** — "reduced p99 from X to Y by doing Z", with metrics

---

## 41. Security (P0)

### 41.1 Web & Application Security
- [ ] **OWASP Top 10** (know both 2021 and the 2025 refresh) — Broken Access Control, Cryptographic Failures, **Injection** (SQL, NoSQL, OS command, LDAP, expression language), Insecure Design, Security Misconfiguration, Vulnerable & Outdated Components / Software Supply Chain Failures, Identification & Authentication Failures, Software & Data Integrity Failures (insecure deserialization, unsigned updates), Security Logging & Monitoring Failures, SSRF, mishandling of exceptional conditions
- [ ] **OWASP API Security Top 10** (§28.2)
- [ ] **XSS** (stored, reflected, DOM) — output encoding, CSP
- [ ] **CSRF** — tokens, SameSite cookies
- [ ] **SSRF** — validating outbound URLs, blocking metadata endpoints (169.254.169.254), IMDSv2
- [ ] **XXE**, insecure deserialization, path traversal, open redirects, clickjacking, HTTP request smuggling (awareness), **ReDoS**, log injection / **Log4Shell** (JNDI lookup), mass assignment, IDOR/BOLA, race conditions (TOCTOU — double spending), timing attacks (constant-time comparison)
- [ ] **Input validation** (allowlists) & output encoding; parameterized queries everywhere
- [ ] **Security headers** — HSTS, CSP, X-Content-Type-Options, X-Frame-Options/frame-ancestors, Referrer-Policy
- [ ] **Brute force & credential stuffing** protection — rate limits, lockouts, CAPTCHA, MFA, breached password checks; account enumeration prevention

### 41.2 Cryptography Basics
- [ ] **Encoding vs hashing vs encryption vs signing**
- [ ] **Hashing** — SHA-256 (integrity), not for passwords; **password hashing** — bcrypt, scrypt, **Argon2id**, PBKDF2; salts & peppers
- [ ] **Symmetric** — AES-GCM (authenticated encryption), modes, IV/nonce reuse dangers
- [ ] **Asymmetric** — RSA, ECC (ECDSA, Ed25519), key exchange (ECDHE)
- [ ] **HMAC** — message authentication (webhooks, API signing)
- [ ] **Digital signatures & certificates**, PKI, CA, certificate pinning (awareness)
- [ ] **Key management** — KMS/HSM, **envelope encryption**, key rotation, never hard-code keys
- [ ] **Encryption at rest vs in transit**; field-level encryption for PII; tokenization (PCI)
- [ ] `SecureRandom` vs `Random`; UUIDs aren't secrets
- [ ] Post-quantum crypto (awareness)

### 41.3 Secure SDLC & Infrastructure
- [ ] **Threat modeling** — STRIDE (Spoofing, Tampering, Repudiation, Information disclosure, DoS, Elevation of privilege), data flow diagrams, trust boundaries
- [ ] **SAST** (SonarQube, Semgrep, CodeQL), **DAST** (OWASP ZAP, Burp), **SCA** (OWASP Dependency-Check, Snyk, Dependabot), **container scanning** (Trivy), **secret scanning** (gitleaks, GitHub secret scanning), IaC scanning (Checkov, tfsec)
- [ ] **Secrets management** — Vault, AWS Secrets Manager; rotation; no secrets in env dumps/logs/actuator
- [ ] **Least privilege** — IAM, DB users per service, network segmentation
- [ ] **Zero trust**, mTLS between services, service identity
- [ ] **Penetration testing**, bug bounty programs (awareness)
- [ ] **Security incident response** basics

### 41.4 Data Protection & Compliance
- [ ] **PII handling** — classification, minimization, masking in logs, encryption, access audit
- [ ] **GDPR** (lawful basis, right to access/erasure, data residency), **DPDP Act (India)** if relevant, CCPA
- [ ] **PCI-DSS** (payments: never store CVV, tokenize PAN, reduce scope), **SOC 2**, **HIPAA**, ISO 27001 (awareness)
- [ ] **Audit trails**, data retention & deletion policies, right-to-be-forgotten in event-sourced/backup systems

### 🎯 Frequently Asked — Security
- How do you prevent SQL injection in JPA native queries?
- How do you securely store API keys/secrets for 50 microservices?
- How would you secure service-to-service communication?
- How do you protect against IDOR in a multi-tenant API?
- Hashing vs encryption — how do you store passwords vs credit card numbers?

---

# PART H — ENGINEERING PRACTICE

## 42. Build Tools, Code Quality & Git (P1)

### 42.1 Maven
- [ ] **Lifecycle phases** — validate → compile → test → package → verify → install → deploy; clean & site lifecycles
- [ ] **POM** — coordinates (GAV), packaging, parent POM, `<dependencyManagement>` vs `<dependencies>`, **BOMs** (`spring-boot-dependencies`), properties
- [ ] **Dependency scopes** — compile, provided, runtime, test, system, import
- [ ] **Transitive dependencies** — "nearest wins" conflict resolution, exclusions, `mvn dependency:tree`, `dependency:analyze`, enforcer plugin (dependency convergence)
- [ ] **Multi-module projects**, reactor builds, `-pl -am`
- [ ] **Plugins** — compiler, surefire (unit) vs failsafe (integration), shade/assembly, jacoco, spring-boot-maven-plugin
- [ ] Profiles, settings.xml, private repositories (Nexus/Artifactory), snapshot vs release

### 42.2 Gradle
- [ ] Tasks & task graph, Groovy vs **Kotlin DSL**, plugins
- [ ] Configurations — `implementation` vs `api` vs `compileOnly` vs `runtimeOnly` vs `testImplementation`
- [ ] Version catalogs (`libs.versions.toml`), platforms/BOMs, dependency constraints & resolution strategies
- [ ] Incremental builds, build cache, configuration cache, Gradle daemon
- [ ] **Maven vs Gradle** trade-offs

### 42.3 Code Quality & Craftsmanship
- [ ] **Clean Code** — meaningful names, small functions, single level of abstraction, no side effects, command-query separation, comments explain *why*
- [ ] **Code smells & refactorings** (Fowler) — long method, large class, feature envy, primitive obsession, shotgun surgery, divergent change, data clumps; extract method/class, replace conditional with polymorphism, introduce parameter object
- [ ] **Static analysis** — SonarQube (quality gates), Checkstyle, PMD, SpotBugs, Error Prone, NullAway
- [ ] **Null safety** — Optional for return types, JSpecify `@Nullable`/`@NonNull`
- [ ] **Code review practices** — what to look for (correctness, design, tests, security, readability, performance), giving kind & specific feedback, small PRs, review SLAs, automating style
- [ ] **Documentation** — READMEs, runbooks, ADRs, API docs, onboarding docs
- [ ] **Legacy code** — characterization tests, seams, strangler refactoring (Working Effectively with Legacy Code)

### 42.4 Git
- [ ] **Internals** (awareness) — blobs, trees, commits, refs, HEAD
- [ ] **Merge vs rebase** (and when not to rebase shared branches), squash merges, fast-forward
- [ ] `cherry-pick`, `revert` vs `reset` (soft/mixed/hard), `stash`, **`bisect`** (find a regression), **`reflog`** (recover lost commits), `blame`, `log --graph`
- [ ] Resolving merge conflicts; `rerere` (P2)
- [ ] Branching strategies (§37), tags & releases, conventional commits, signed commits
- [ ] Hooks (pre-commit), monorepo vs polyrepo trade-offs
- [ ] PR hygiene — small, focused, descriptive, linked tickets

---

## 43. Production Engineering & Incident Management (P0)

### 43.1 Incident Lifecycle
- [ ] **Detect** (alerts, customers) → **triage** (severity, impact, scope) → **mitigate first** (rollback, feature flag off, failover, scale up, shed load) → **resolve root cause** → **postmortem** → **follow-up actions**
- [ ] **Severity levels** (SEV1–SEV4) and escalation paths
- [ ] **Roles** — incident commander, communications lead, ops/subject-matter experts, scribe
- [ ] **Communication** — status page, stakeholder updates cadence, war rooms
- [ ] **Blameless postmortems** — timeline, impact, root cause(s), contributing factors, what went well, action items with owners & deadlines; **5 Whys**, fishbone diagrams
- [ ] **On-call practices** — rotations, handoffs, runbooks, alert quality, burnout prevention, follow-the-sun
- [ ] **Change management** — most incidents come from changes; deploy windows, progressive rollouts, automatic rollback
- [ ] **MTTD, MTTA, MTTR, MTBF** metrics

### 43.2 Production Debugging Workflow
- [ ] Dashboards (what changed? which endpoints? which pods/AZ?) → logs (errors, correlation IDs) → traces (slow span) → JVM diagnostics (thread/heap dumps, GC logs, profiles) → DB (slow queries, locks, connections) → infra (CPU throttling, network, DNS)
- [ ] Correlate with deploys, config changes, traffic spikes, dependency incidents

### 43.3 Scenarios You Should Have Stories or Clear Answers For
- [ ] Memory leak causing OOM restarts
- [ ] Thread pool / Tomcat thread exhaustion due to slow downstream
- [ ] DB connection pool exhaustion
- [ ] Slow query after data growth / missing index / bad plan after stats change
- [ ] Cascading failure / retry storm from a dependency outage
- [ ] Kafka consumer lag spike / rebalance loop / poison message blocking a partition
- [ ] Cache stampede after cache flush or deploy
- [ ] Deadlocks in DB or application
- [ ] Disk full due to logs; inode exhaustion
- [ ] TLS certificate expiry; DNS misconfiguration; clock skew breaking JWT validation
- [ ] Bad deploy breaking backward compatibility (API/event/schema)
- [ ] Data corruption / accidental deletion — recovery via backups/PITR/event replay
- [ ] Duplicate payments/orders due to retries without idempotency
- [ ] Noisy neighbor tenant degrading everyone
- [ ] Third-party provider outage (payment gateway, SMS provider) — failover strategy

### 43.4 SRE Concepts
- [ ] Toil and its reduction through automation
- [ ] Error budgets (§39.5); reliability as a feature
- [ ] Capacity planning, load testing before peaks (sales events)
- [ ] Runbooks & automation (self-healing)
- [ ] Production readiness reviews / checklists (§54 includes one)

---

## 44. AI/LLM for Backend Engineers (P1)

> In 2026 interviews, expect: "How do you use AI tools in your workflow?" and sometimes "Design an LLM-backed feature."

- [ ] **LLM fundamentals** — tokens, context windows, temperature/top-p, embeddings, hallucinations, non-determinism, latency & cost per token
- [ ] **Prompt engineering** — system prompts, few-shot, structured outputs (JSON schema), chain-of-thought (awareness)
- [ ] **RAG (Retrieval-Augmented Generation)** — document ingestion, chunking strategies, embeddings, vector search (HNSW), hybrid search (BM25 + vector), reranking, citations, freshness/re-indexing
- [ ] **Tool/function calling & agents** — agent loops, **Model Context Protocol (MCP)** servers/clients, guardrails on tool permissions
- [ ] **Java frameworks** — **Spring AI**, LangChain4j
- [ ] **LLM gateway design** — provider abstraction, rate limiting by tokens, retries/fallback models, **semantic caching**, streaming (SSE), cost tracking & quotas per tenant, prompt/version management, PII redaction
- [ ] **Evaluation & observability** — offline eval sets, LLM-as-judge, tracing prompts/responses, latency/cost dashboards
- [ ] **Security** — **prompt injection** (direct & indirect), data exfiltration via tools, output validation, OWASP Top 10 for LLM applications
- [ ] **Using AI coding assistants responsibly** — productivity gains, reviewing generated code, security & licensing concerns, team guidelines — have a concrete point of view
- [ ] **Vector DBs** (§19.7)

---

## 45. Domain Knowledge (P1)

> Interviewers love candidates who understand the business domain. Go deep on **your** domain; know the basics of the domains of your target companies.

- [ ] **Payments / Fintech** — auth vs capture vs settlement vs refund vs chargeback; payment gateways vs processors vs acquirers; card networks; UPI/IMPS/NEFT (India) or ACH/SEPA; 3-D Secure; **double-entry ledger**; reconciliation; idempotency; PCI-DSS; KYC/AML; FX & rounding; maker-checker
- [ ] **E-commerce** — catalog, pricing & promotions, cart, checkout, inventory reservation, order management state machines, fulfillment & logistics, returns, search & recommendations
- [ ] **Banking/Insurance/Healthcare** — regulatory constraints, audit, batch processing, legacy integration (mainframes, SOAP, MQ, ISO 8583/20022)
- [ ] **Ride-hailing / Delivery / Logistics** — geo, dispatch, ETAs, real-time tracking
- [ ] **Social / Media / Messaging** — feeds, fan-out, notifications, media pipelines, content moderation
- [ ] **SaaS / B2B** — multi-tenancy, billing/subscriptions/metering, RBAC, SSO/SCIM, audit logs, data export
- [ ] **AdTech / Analytics** — high-volume event ingestion, aggregation, attribution
- [ ] **General** — money handling, time zones, i18n/l10n, regulatory data residency

---

# PART I — LEADERSHIP, BEHAVIORAL & CAREER

## 46. Technical Leadership Competencies (P0)

> At 10 YOE you're evaluated as a **Senior / Staff / Lead**. Decide your target track — **Staff/Principal IC** vs **Engineering Manager** — and tailor your stories.

### 46.1 Technical Direction
- [ ] Setting technical vision & multi-quarter roadmaps aligned with business goals
- [ ] Driving architecture decisions — RFCs/design docs, ADRs, design reviews, getting buy-in
- [ ] **Build vs buy**, vendor evaluation, open-source adoption
- [ ] **Tech debt strategy** — quantifying (incidents, velocity, cost), prioritizing against features, carving capacity (e.g., 20%)
- [ ] **Large migrations** — planning, risk management, incremental delivery, rollback plans, measuring progress
- [ ] Standards & guardrails — coding standards, golden paths, shared libraries, platform thinking
- [ ] Managing technical risk; knowing when "good enough" beats "perfect"
- [ ] Cross-team technical alignment; working with architects/platform teams

### 46.2 Execution & Delivery
- [ ] Breaking down ambiguous problems into milestones; critical path & dependency management
- [ ] **Estimation** — techniques (t-shirt sizing, story points, three-point estimates), communicating uncertainty, buffers
- [ ] Scope negotiation — MVP thinking, cutting scope vs moving dates
- [ ] Agile/Scrum/Kanban — ceremonies, what you'd change; OKRs/KPIs
- [ ] Delivery metrics — DORA, cycle time, predictability
- [ ] Quality ownership — testing culture, code review standards, operational readiness
- [ ] Running effective meetings, async communication, status reporting

### 46.3 People & Team
- [ ] **Mentoring & coaching** — growing juniors to mid, mid to senior; specific examples
- [ ] **Delegation** — what you delegate, how you support without micromanaging
- [ ] **Feedback** — giving (SBI: Situation-Behavior-Impact) and receiving; difficult conversations
- [ ] Handling **underperformance** (and when to escalate to manager)
- [ ] **Conflict resolution** within the team and across teams
- [ ] **Hiring** — interviewing, raising the bar, designing interview loops, onboarding
- [ ] Building psychological safety, team culture, morale during crunch/layoffs
- [ ] 1:1s, career conversations (if EM track)
- [ ] Knowledge sharing — tech talks, documentation, pairing, guilds

### 46.4 Stakeholder & Business
- [ ] Partnering with Product, Design, QA, SRE, Security, Business
- [ ] **Pushing back / saying no** with data and alternatives
- [ ] Communicating with executives — concise, impact-first, options with trade-offs
- [ ] **Business acumen** — product metrics, revenue/cost impact of engineering decisions, cloud cost ownership, customer empathy
- [ ] Managing expectations, escalations, and bad news early

---

## 47. Behavioral Interviews (P0)

### 47.1 Answer Format
- [ ] **STAR** (Situation, Task, Action, Result) or **STAR-L** (+ Learnings); CAR for short answers
- [ ] 2–3 minutes per story; 10–15% situation, 60–70% actions, 20% results/learnings
- [ ] Say **"I"** for your actions (not "we"), but credit the team
- [ ] **Quantify results** — latency, cost, revenue, incidents, delivery time, team growth
- [ ] Show **trade-offs and judgment**, not just heroics
- [ ] Failure stories must be real failures with genuine ownership and learnings
- [ ] Prepare **follow-up depth** — interviewers dig ("what would you do differently?", "what did your manager think?")

### 47.2 Story Bank — prepare 15–20 stories mapped to these themes
- [ ] 1. Most technically challenging problem you solved
- [ ] 2. Largest/most impactful project you led end to end (architecture + delivery + impact)
- [ ] 3. A significant design decision and the trade-offs you made
- [ ] 4. A major production incident you handled (and the postmortem outcome)
- [ ] 5. A failure or mistake you made and what you learned
- [ ] 6. Conflict with a peer / disagreement with your manager or an architect
- [ ] 7. Disagree and commit
- [ ] 8. Influencing without authority / driving cross-team alignment
- [ ] 9. Mentoring someone and the outcome of their growth
- [ ] 10. Handling an underperforming team member
- [ ] 11. Tight deadline / prioritization under pressure
- [ ] 12. Working with ambiguous or changing requirements
- [ ] 13. Pushing back on product/business (saying no)
- [ ] 14. Convincing stakeholders to invest in tech debt / platform work
- [ ] 15. Improving team process or developer productivity (CI/CD, testing, on-call)
- [ ] 16. Customer obsession — going beyond to solve a customer problem
- [ ] 17. Innovation — a new idea you proposed and drove to production
- [ ] 18. A data-driven decision
- [ ] 19. Receiving critical feedback and acting on it
- [ ] 20. Delivering bad news / missing a commitment
- [ ] 21. Scope creep / shifting priorities
- [ ] 22. Hiring and building a team
- [ ] 23. A migration (monolith → microservices, on-prem → cloud, DB migration, Java upgrade)
- [ ] 24. A performance optimization with measurable impact
- [ ] 25. A security or compliance issue you handled
- [ ] 26. A calculated risk you took
- [ ] 27. Simplifying a complex system / saying no to over-engineering
- [ ] 28. Learning a new technology quickly
- [ ] 29. Handling burnout/morale issues in the team
- [ ] 30. A time you had to make a decision without complete data

### 47.3 Common Questions — prepare crisp answers
- [ ] **"Tell me about yourself"** — 90–120 s: present role & scope → 2–3 career highlights with impact → why you're looking → what you want next
- [ ] **"Why are you leaving / why did you leave?"** — positive, forward-looking
- [ ] **"Why the gap?"** — you're taking 2–3 months for focused preparation; frame it as intentional upskilling (deep-dived into system design, modern Java, etc.) — confident, no apology
- [ ] Why this company / this role?
- [ ] Strengths & weaknesses (real weakness + what you're doing about it)
- [ ] Greatest achievement; proudest project
- [ ] What would your manager/team say about you? What feedback have you received?
- [ ] Where do you see yourself in 3–5 years? IC vs manager?
- [ ] How do you stay current with technology?
- [ ] How do you handle stress / competing priorities?
- [ ] How do you make technical decisions in a team?
- [ ] What kind of culture/manager do you thrive in?
- [ ] Why should we hire you?

### 47.4 Company-Specific Frameworks
- [ ] **Amazon Leadership Principles (16)** — Customer Obsession, Ownership, Invent and Simplify, Are Right A Lot, Learn and Be Curious, Hire and Develop the Best, Insist on the Highest Standards, Think Big, Bias for Action, Frugality, Earn Trust, Dive Deep, Have Backbone; Disagree and Commit, Deliver Results, Strive to be Earth's Best Employer, Success and Scale Bring Broad Responsibility — have 2 stories per principle
- [ ] **Google** — Googleyness (comfort with ambiguity, collaboration, humility, bias to action) & leadership
- [ ] **Meta** — behavioral signals: driving results, conflict resolution, growth, ambiguity, communication
- [ ] **Microsoft** — growth mindset, collaboration
- [ ] **Startups** — ownership, speed, wearing multiple hats, scrappiness
- [ ] Read each target company's **values page** and map your stories

### 47.5 Questions to Ask Interviewers
- [ ] What does success look like in this role in 6/12 months?
- [ ] What are the biggest technical challenges the team faces right now?
- [ ] How are technical decisions made? How is tech debt prioritized?
- [ ] What does the on-call and incident culture look like?
- [ ] How is engineering performance evaluated and how do people grow to Staff/Principal?
- [ ] Team composition, roadmap, how product & engineering collaborate
- [ ] (Hiring manager) What would make you excited about a candidate in this role?

---

## 48. Project Deep-Dive Preparation (P0)

> Almost every senior loop has a round where you whiteboard **your own** system and get grilled. This is where 10 YOE candidates win or lose.

- [ ] Pick **2–3 flagship projects** from the last 5 years
- [ ] For each, prepare:
  - [ ] Business problem & why it mattered (revenue, cost, users, risk)
  - [ ] **Scale numbers** — users, RPS/QPS, data volume, latency SLOs, team size, timeline
  - [ ] **Architecture diagram** you can draw in 5 minutes (components, data flow, tech choices)
  - [ ] **Your specific role** vs the team's
  - [ ] Key **design decisions & alternatives considered** (why Kafka not RabbitMQ, why Postgres not Mongo, why microservices, why this partition key)
  - [ ] Hardest technical challenges & how you solved them
  - [ ] Failure modes & how the system handles them (what if Kafka/DB/downstream is down?)
  - [ ] Consistency, idempotency, concurrency approach
  - [ ] Testing, deployment, monitoring & alerting approach
  - [ ] Production incidents that happened and fixes
  - [ ] **Measured impact** — before/after metrics
  - [ ] What you'd do differently today / how it would scale 10×
- [ ] Rehearse aloud; expect "why?" five levels deep
- [ ] Be careful with confidentiality — abstract proprietary details

---

## 49. Resume, Job Search & Negotiation (P0)

### 49.1 Resume
- [ ] 1–2 pages; senior summary (3 lines) at top: years, domain, scale, leadership
- [ ] Bullets in **XYZ format** — "Accomplished X, as measured by Y, by doing Z"
- [ ] **Quantify** — latency ↓, throughput ↑, cost ↓, incidents ↓, revenue enabled, team size led
- [ ] Highlight leadership (led team of N, mentored, drove architecture), scale, and ownership
- [ ] Skills section aligned with target JDs (Java 17/21, Spring Boot, microservices, Kafka, AWS, K8s, Postgres, Redis, system design)
- [ ] ATS-friendly formatting; tailored versions per role type
- [ ] Everything on the resume is fair game — be ready to deep-dive any line

### 49.2 Online Presence
- [ ] LinkedIn — headline, about section, experience mirroring resume, skills, "Open to work" (recruiters only), recommendations
- [ ] GitHub/blog (optional but a plus) — a well-documented sample project (e.g., Spring Boot microservices with Kafka, Testcontainers, observability)

### 49.3 Job Search Strategy
- [ ] **Target list** in tiers — dream / strong / practice companies
- [ ] **Referrals** > recruiters > cold applications
- [ ] **Sequence interviews** — practice companies first, dream companies after 4–6 weeks of prep
- [ ] **Start applying by week 4–6** — pipelines take 3–8 weeks end to end
- [ ] Track everything (spreadsheet: company, stage, dates, contacts, notes, feedback)
- [ ] Debrief after every interview — write down questions asked & gaps found

### 49.4 Offer & Negotiation
- [ ] Research levels & compensation (levels.fyi, Glassdoor, AmbitionBox, peers)
- [ ] Understand components — base, variable/bonus, RSUs/ESOPs (vesting, cliff, refreshers, liquidity for startups), joining bonus, relocation, notice-period buyout, benefits
- [ ] Avoid giving the first number; anchor on market data & competing offers
- [ ] Negotiate **level** as well as compensation (level determines long-term trajectory)
- [ ] Be polite, enthusiastic, specific; get everything in writing
- [ ] Evaluate beyond money — team, manager, tech, growth, stability, work-life balance

---

## 50. Interview Formats by Company Type

| Company type | Typical loop for a 10 YOE backend engineer | Prep emphasis |
|--------------|--------------------------------------------|---------------|
| **Big Tech / FAANG-like** | 1–2 DSA (Medium/Hard) · 1–2 System Design (HLD) · sometimes LLD · Behavioral/Leadership · Hiring Manager | DSA patterns, HLD at scale, leadership stories |
| **Product unicorns / scale-ups** | DSA · **Machine coding** (LLD in 90–120 min) · HLD · Hiring Manager / Tech deep dive · Culture | Machine coding, LLD, HLD, project deep-dive |
| **Fintech / Banks / Enterprises** | Java & Spring deep dive · microservices & DB · coding (easier DSA) · system design · managerial | Core Java, JVM, concurrency, Spring internals, transactions |
| **Startups** | Take-home or live practical coding · system design · founder/culture fit | Pragmatic design, ownership, speed, breadth |
| **Service / consulting** | Java/Spring/microservices Q&A · coding · client-facing round | Breadth of frameworks, communication |
| **Staff/Principal-level loops** | Architecture review of past work · HLD with ambiguity · cross-team leadership · strategy | Influence, technical strategy, trade-offs, written design docs |

---

# PART J — EXECUTION

## 51. Cross-Topic Rapid-Fire Questions (Top 100)

> If you can answer each of these confidently in 2–3 minutes, you're in strong shape. Practice them aloud.

**Java & JVM**
1. [ ] How does HashMap work, and what changed in Java 8?
2. [ ] How does ConcurrentHashMap achieve thread safety without locking the whole map?
3. [ ] Why is String immutable? How do you design an immutable class?
4. [ ] equals/hashCode contract and what breaks if violated
5. [ ] Explain the Java Memory Model and happens-before
6. [ ] volatile vs synchronized vs atomic classes
7. [ ] How does G1 GC work? When would you choose ZGC?
8. [ ] How do you troubleshoot a memory leak in production?
9. [ ] How do you troubleshoot 100% CPU in a Java process?
10. [ ] What are virtual threads, and when would you not use them?
11. [ ] ThreadPoolExecutor internals — what happens when the queue is full?
12. [ ] CompletableFuture — combine 3 async calls with timeout and fallback
13. [ ] What's new in Java 17 and 21 that you actually use?
14. [ ] Records vs Lombok `@Value`; sealed classes use cases
15. [ ] Checked vs unchecked exceptions — your design guidelines

**Spring**
16. [ ] Spring bean lifecycle and where AOP proxies are created
17. [ ] Why does `@Transactional` not work on a self-invoked method?
18. [ ] How does Spring Boot auto-configuration work?
19. [ ] How do you create a custom Spring Boot starter?
20. [ ] Constructor vs field injection; circular dependencies
21. [ ] Bean scopes; injecting prototype into singleton
22. [ ] DispatcherServlet request flow end to end
23. [ ] Filter vs Interceptor vs Aspect
24. [ ] Global exception handling design for REST APIs
25. [ ] Transaction propagation types with real use cases
26. [ ] Isolation levels and the anomalies each prevents
27. [ ] Why did my checked exception not roll back the transaction?
28. [ ] N+1 problem — detection and fixes
29. [ ] Optimistic vs pessimistic locking in JPA
30. [ ] Spring Security filter chain; how is a JWT validated?
31. [ ] OAuth2 Authorization Code + PKCE vs Client Credentials
32. [ ] How do you configure timeouts/retries/circuit breakers for downstream calls?
33. [ ] Liveness vs readiness probes with Actuator
34. [ ] `@Async` pitfalls and context propagation
35. [ ] How do you run a `@Scheduled` job only once across 10 pods?

**Databases & Caching**
36. [ ] How does a B+tree index work? Composite index and leftmost prefix
37. [ ] Clustered vs non-clustered index
38. [ ] How would you debug a slow query?
39. [ ] MVCC — how does Postgres/InnoDB implement it?
40. [ ] How do you prevent double booking / overselling?
41. [ ] Replication lag and read-your-writes
42. [ ] Sharding strategy and shard key selection for an orders table
43. [ ] Zero-downtime schema migration for a huge table
44. [ ] SQL vs NoSQL decision for a given use case
45. [ ] Cassandra data model for a chat application
46. [ ] Cache-aside vs write-through; cache/DB consistency
47. [ ] Cache stampede, penetration, avalanche — prevention
48. [ ] Redis data structures and real use cases
49. [ ] Redis distributed lock — implementation and pitfalls
50. [ ] Keyset vs offset pagination

**Messaging & Distributed Systems**
51. [ ] Kafka architecture: partitions, replicas, ISR, consumer groups
52. [ ] How does Kafka guarantee ordering? How does it break?
53. [ ] At-least-once vs exactly-once in Kafka
54. [ ] Consumer rebalancing — problems and mitigations
55. [ ] Handling poison messages; retry topics vs DLQ
56. [ ] Transactional outbox pattern and CDC
57. [ ] Kafka vs RabbitMQ vs SQS
58. [ ] CAP and PACELC with real examples
59. [ ] Consistency models — strong vs eventual vs read-your-writes
60. [ ] Consistent hashing and virtual nodes
61. [ ] Raft leader election and log replication
62. [ ] 2PC vs Saga; choreography vs orchestration
63. [ ] Idempotency — design an idempotent payment API
64. [ ] Unique ID generation (Snowflake, UUIDv7)
65. [ ] Distributed locks and fencing tokens

**Microservices, APIs & Resilience**
66. [ ] How do you decide microservice boundaries?
67. [ ] Monolith → microservices migration strategy (Strangler Fig)
68. [ ] How do you query data spread across services?
69. [ ] API Gateway vs service mesh responsibilities
70. [ ] REST API design for a resource; status codes; error format
71. [ ] API versioning and backward compatibility for APIs & events
72. [ ] REST vs gRPC vs GraphQL
73. [ ] Circuit breaker states and tuning
74. [ ] Retries with exponential backoff & jitter; retry storms
75. [ ] Bulkhead, rate limiting, load shedding, backpressure — differences
76. [ ] Rate limiting algorithms compared; implement token bucket
77. [ ] Design a distributed rate limiter
78. [ ] Webhooks — reliable delivery and security
79. [ ] Distributed tracing across HTTP and Kafka
80. [ ] Contract testing between services

**System Design (be able to design end-to-end)**
81. [ ] URL shortener
82. [ ] Notification system
83. [ ] Chat system (WhatsApp)
84. [ ] News feed (Twitter)
85. [ ] Payment system with ledger
86. [ ] Ticket booking (BookMyShow) under contention
87. [ ] Ride hailing (Uber) with geospatial matching
88. [ ] Video streaming (YouTube)
89. [ ] File sync (Dropbox)
90. [ ] Distributed job scheduler

**Infra, Ops & Leadership**
91. [ ] What happens when you type a URL into a browser?
92. [ ] Zero-downtime deployment in Kubernetes
93. [ ] Pod OOMKilled while heap usage looks fine — why?
94. [ ] SLI/SLO/SLA and error budgets
95. [ ] Walk me through a major incident you handled
96. [ ] How do you secure service-to-service communication?
97. [ ] How do you manage secrets across environments?
98. [ ] How do you balance tech debt vs features?
99. [ ] How do you mentor engineers and raise the team's bar?
100. [ ] Tell me about a decision you made that turned out wrong

---

## 52. 12-Week Preparation Plan

### Daily Template (≈ 8–9 focused hours, 6 days/week; day 7 = light review + rest)
| Block | Time | Activity |
|-------|------|----------|
| Morning | 2.5–3 h | **DSA** — 3–4 problems by pattern (timed), review solutions, log mistakes |
| Midday | 2 h | **System design** — 1 problem end-to-end OR 1 concept deep dive (read + draw + explain aloud) |
| Afternoon | 2 h | **Backend core** — Java/JVM/Spring/DB/Kafka topic of the week (read, code small demos, write notes) |
| Evening | 1 h | **LLD / machine coding** (alternate days) or **behavioral** stories |
| End of day | 15 min | Update this checklist, spaced-repetition review (Anki) of mistakes |

### Week-by-Week
| Week | DSA | System Design / LLD | Backend Core | Behavioral / Career |
|------|-----|---------------------|--------------|---------------------|
| **1** | Arrays, hashing, two pointers, sliding window | HLD framework, estimation, building blocks (§29–31) | Core Java, collections internals (§1–2) | Update resume & LinkedIn; draft "Tell me about yourself" |
| **2** | Stack, monotonic stack, binary search, linked lists | LB, caching, CDN, DB scaling; **URL shortener**, **rate limiter** | JVM, GC, troubleshooting (§3) | List 30 story candidates (§47.2) |
| **3** | Trees, BST, tree DFS/BFS | **Key-value store**, **unique ID generator**, **notification system** | Concurrency deep dive + coding problems (§4) | Write 5 STAR stories |
| **4** | Heaps, intervals, greedy | **News feed**, **chat system**; LLD: parking lot, elevator | Spring core, AOP, Boot internals (§8–9) | Write 5 more stories; build target-company list; ask for referrals |
| **5** | Graphs I — BFS/DFS, islands, topo sort, union-find | **Distributed message queue**, **job scheduler**; LLD: BookMyShow, Splitwise | Spring MVC/REST, HTTP clients, Security, OAuth2/JWT (§10, §14) | **Start applying** to practice-tier companies |
| **6** | Graphs II — Dijkstra, MST; tries | **Uber**, **proximity service**, **typeahead**; machine coding mock #1 | JPA/Hibernate, transactions (§12–13) | Project deep-dive #1 prepared (§48) |
| **7** | Backtracking | **Ticketmaster**, **e-commerce**, **payment system** | SQL & DB internals, indexing, locking (§18) | Project deep-dive #2; first mock interviews |
| **8** | DP I — 1D, knapsack | **YouTube**, **Dropbox**, **Google Docs** | NoSQL, Redis, caching (§19–20) | Apply to strong-tier companies; 2 mocks/week |
| **9** | DP II — 2D, LIS/LCS, edit distance | **Metrics/logging**, **ad click aggregation**, **top-K** | Kafka & messaging, distributed systems theory (§21–22) | Behavioral mocks; refine stories |
| **10** | Mixed + company-tagged problems | Own-system deep dives; machine coding mock #2–3 | Microservices, resilience, rate limiting, API design (§23–28) | Apply to dream-tier companies |
| **11** | Timed mixed sets (2 Mediums in 45 min) | Mock HLDs (3+), mock LLDs | K8s, cloud, observability, security, performance (§34–41) | Negotiation prep; salary research |
| **12** | Revise mistake log; weak patterns | Revise all 25+ designs (one-page summaries) | Rapid-fire 100 (§51) | Final mocks; rest before big loops |

### Throughout
- [ ] **Mock interviews** — at least 10 (DSA ×4, HLD ×4, LLD/behavioral ×2) with peers or paid platforms
- [ ] **Mistake log** — every wrong DSA attempt and every design gap, reviewed weekly
- [ ] **One-page summaries** for each system design problem and each macro topic
- [ ] **Build one small project** (optional, weeks 6–10): Spring Boot 3 microservices + Kafka + Postgres + Redis + outbox + Resilience4j + Testcontainers + OpenTelemetry + Docker Compose/K8s — gives you fresh, hands-on talking points
- [ ] **Health** — sleep, exercise, breaks; 2–3 months is a marathon

---

## 53. Resources

### Books
- [ ] **Designing Data-Intensive Applications** — Martin Kleppmann (*the* most important book for senior backend)
- [ ] **System Design Interview Vol. 1 & 2** — Alex Xu (& Sahn Lam)
- [ ] **Effective Java (3rd ed.)** — Joshua Bloch
- [ ] **Java Concurrency in Practice** — Brian Goetz
- [ ] **Optimizing Java / Java Performance** — Evans et al. / Scott Oaks
- [ ] **Spring Boot in Action / Spring in Action / Pro Spring 6** + official Spring reference docs
- [ ] **High-Performance Java Persistence** — Vlad Mihalcea
- [ ] **Microservices Patterns** — Chris Richardson; **Building Microservices (2nd ed.)** — Sam Newman
- [ ] **Release It! (2nd ed.)** — Michael Nygard (resilience)
- [ ] **Kafka: The Definitive Guide** — Shapira et al.
- [ ] **Database Internals** — Alex Petrov; **High Performance MySQL**; **The Art of PostgreSQL**
- [ ] **Domain-Driven Design Distilled** — Vaughn Vernon; **Learning Domain-Driven Design** — Vlad Khononov
- [ ] **Fundamentals of Software Architecture** & **Software Architecture: The Hard Parts** — Richards & Ford
- [ ] **Site Reliability Engineering** & **The SRE Workbook** — Google (free online)
- [ ] **Clean Code**, **Clean Architecture** — Robert C. Martin; **Refactoring** — Martin Fowler; **Head First Design Patterns**
- [ ] **Cracking the Coding Interview**; **Elements of Programming Interviews (Java)**
- [ ] **The Staff Engineer's Path** — Tanya Reilly; **Staff Engineer** — Will Larson; **An Elegant Puzzle** — Will Larson
- [ ] **Understanding Distributed Systems** — Roberto Vitillo (concise and practical)

### Practice Platforms
- [ ] **DSA** — LeetCode (Blind 75, NeetCode 150, company-tagged), NeetCode.io roadmap
- [ ] **System design** — ByteByteGo, Hello Interview, DesignGurus (Grokking), Exponent
- [ ] **Mocks** — Pramp, interviewing.io, peers/ex-colleagues
- [ ] **LLD / machine coding** — practice repos & timed self-mocks

### Blogs & Docs
- [ ] Official docs — Spring, Hibernate, Kafka, PostgreSQL, Redis, Kubernetes, AWS
- [ ] **Baeldung** (Java/Spring), **Vlad Mihalcea** (JPA/Hibernate), **Martin Fowler** (architecture), **microservices.io** (patterns), **High Scalability**
- [ ] Engineering blogs — Netflix, Uber, Stripe, Discord, Shopify, Airbnb, LinkedIn, Meta, Cloudflare, Slack, Pinterest, Flipkart, Swiggy, Zomato, Razorpay
- [ ] Papers — Dynamo, Bigtable, GFS, MapReduce, Spanner, Raft, Kafka, Zanzibar, "The Tail at Scale"
- [ ] Newsletters — ByteByteGo, The Pragmatic Engineer, InfoQ

---

## 54. Final Readiness Checklist

### Interview Readiness
- [ ] Solved 250+ DSA problems; can recognize patterns within 2–3 minutes
- [ ] Can solve 2 Mediums in 45 minutes with clean code and tests
- [ ] Designed 25+ systems end-to-end aloud; have one-page notes for each
- [ ] Built 8+ machine-coding problems under 2 hours
- [ ] Can whiteboard 2–3 of your own systems with numbers and trade-offs
- [ ] 15–20 STAR stories written, rehearsed, and mapped to company values
- [ ] Polished 2-minute introduction and a confident career-gap narrative
- [ ] Answered all 100 rapid-fire questions aloud (§51)
- [ ] Completed 10+ mock interviews and fixed the gaps found
- [ ] Resume tailored, LinkedIn updated, referrals requested, offers research done

### Production Readiness Checklist (also a great interview answer: "What makes a service production-ready?")
- [ ] **API** — versioned, documented (OpenAPI), validated input, consistent errors, idempotent writes, pagination
- [ ] **Resilience** — timeouts on all calls, retries with backoff + jitter, circuit breakers, bulkheads, graceful degradation, rate limiting
- [ ] **Data** — migrations via Flyway/Liquibase, backward-compatible schema changes, indexes reviewed, backups & PITR tested, retention policy
- [ ] **Messaging** — idempotent consumers, DLQ, outbox for reliable publishing, schema compatibility
- [ ] **Observability** — structured logs with trace IDs, RED/USE metrics, distributed tracing, dashboards, SLOs, actionable alerts with runbooks
- [ ] **Security** — authN/authZ, secrets in a vault, TLS/mTLS, dependency & image scanning, least-privilege IAM, PII protection, audit logs
- [ ] **Scalability** — stateless, horizontally scalable, load tested, autoscaling configured, capacity plan
- [ ] **Deployability** — CI/CD, automated tests (unit, integration, contract), canary/blue-green, fast rollback, feature flags
- [ ] **Operability** — health probes (liveness/readiness/startup), graceful shutdown, config externalized, on-call ownership, documentation
- [ ] **Availability** — multi-AZ, no SPOFs, DR plan with RTO/RPO, tested failover
- [ ] **Cost** — right-sized resources, cost dashboards, tagging

---

> **Final advice:** Depth beats breadth at 10 YOE. Interviewers forgive not knowing a niche tool; they don't forgive shallow understanding of fundamentals you've claimed on your resume (transactions, concurrency, caching, Kafka, system trade-offs). For every topic, aim to explain **what**, **how it works internally**, **when to use / not use**, **trade-offs**, and **a real experience** where you applied it.
