---
card: java
gi: 984
slug: methodhandles-varhandles
title: MethodHandles & VarHandles
---

## 1. What it is

`MethodHandle` (introduced in Java 7) and `VarHandle` (introduced in Java 9) are lower-level, JVM-native alternatives to classic reflection (`Method`, `Field`) for invoking methods and accessing fields dynamically — both are designed from the ground up to be resolved and, critically, optimized by the JVM's JIT compiler far more effectively than `Method.invoke`/`Field.get` ever can be, since a `MethodHandle` behaves, from the JIT's perspective, much closer to an ordinary direct call than a reflective one does. `MethodHandles.Lookup` provides the mechanism for finding a specific method or field (`lookup.findVirtual(...)`, `lookup.findStatic(...)`, `lookup.findGetter(...)`) and producing a `MethodHandle` or `VarHandle` for it, which can then be invoked directly (`handle.invoke(args)`) with performance that, after JIT warm-up, can approach that of a genuinely direct, compile-time-checked method call — a meaningfully different performance profile than classic reflection's `Method.invoke`, which carries a heavier, harder-to-optimize-away overhead on every single call.

## 2. Why & when

This API exists specifically because classic reflection, while functionally complete, has real performance costs that matter for infrastructure code executed extremely frequently — a dynamic language implementation running on the JVM (this API was, in fact, originally designed to support exactly this use case, particularly for `invokedynamic`), a high-performance serialization library, or any framework doing dynamic dispatch in a genuinely hot path. `VarHandle` specifically also provides atomic and memory-ordering operations directly (`compareAndSet`, `getVolatile`, `setRelease`, and others) as first-class, built-in capabilities — giving fine-grained, low-level concurrent-programming primitives similar in spirit to `sun.misc.Unsafe` (the internal, unsupported API many concurrency libraries historically had to rely on before `VarHandle` existed) but through a proper, publicly supported, standard API. Reach for `MethodHandle`/`VarHandle` specifically when classic reflection's overhead has been measured and shown to matter for your actual workload, or when you need `VarHandle`'s atomic/volatile field access capabilities directly — for ordinary, infrequent dynamic dispatch, classic reflection's simpler API is usually the more approachable and sufficient choice.

## 3. Core concept

```java
class Point {
    int x;
    public int getX() { return x; }
}

MethodHandles.Lookup lookup = MethodHandles.lookup();

// MethodHandle: find and invoke a method dynamically, JIT-friendly
MethodType type = MethodType.methodType(int.class);
MethodHandle getXHandle = lookup.findVirtual(Point.class, "getX", type);
int value = (int) getXHandle.invoke(new Point()); // resolved once, then optimized like a direct call

// VarHandle: find and access a FIELD dynamically, with atomic/volatile operations built in
VarHandle xHandle = lookup.findVarHandle(Point.class, "x", int.class);
Point p = new Point();
xHandle.set(p, 42);                        // ordinary write
int current = (int) xHandle.get(p);         // ordinary read
boolean swapped = xHandle.compareAndSet(p, 42, 100); // ATOMIC compare-and-swap, built in
```

`MethodHandle` targets *invoking* methods with better JIT optimization potential than classic reflection; `VarHandle` targets *accessing fields* with the same optimization benefit, plus a rich, standard set of atomic and memory-ordering operations built directly into the API itself.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Classic reflection's Method.invoke compared against a MethodHandle, both dynamically resolving a method call, but the MethodHandle path being far more amenable to JIT optimization toward a direct call" >
  <rect x="20" y="30" width="260" height="60" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="50" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Method.invoke(obj, args)</text>
  <text x="150" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">heavier per-call overhead,</text>
  <text x="150" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">harder for JIT to optimize away</text>

  <rect x="340" y="30" width="260" height="60" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">methodHandle.invoke(obj, args)</text>
  <text x="470" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">JIT-friendly, can approach</text>
  <text x="470" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">direct-call performance after warm-up</text>
</svg>

*Both resolve a method dynamically at runtime, but MethodHandle's design lets the JIT compiler optimize repeated calls far more aggressively than classic reflection's Method.invoke.*

## 5. Runnable example

Scenario: build a small dynamic dispatch and concurrent counter utility, evolving from a basic MethodHandle-based dynamic method call, to a realistic VarHandle-based field accessor comparison against classic reflection, to a more advanced case using VarHandle's atomic compare-and-set for lock-free concurrent state updates.

### Level 1 — Basic

```java
import java.lang.invoke.*;

public class MethodHandleBasic {
    static class Greeting {
        public String greet(String name) { return "Hello, " + name + "!"; }
    }

    public static void main(String[] args) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();
        MethodType type = MethodType.methodType(String.class, String.class);
        MethodHandle greetHandle = lookup.findVirtual(Greeting.class, "greet", type);

        Greeting greeting = new Greeting();
        String result = (String) greetHandle.invoke(greeting, "Ada");

        System.out.println(result);
    }
}
```

**How to run:** `java MethodHandleBasic.java` (JDK 17+).

Expected output:
```
Hello, Ada!
```

`lookup.findVirtual` resolves the `greet` method once, given its declaring class, name, and `MethodType` (return type plus parameter types), producing a `MethodHandle` — invoking it via `.invoke(greeting, "Ada")` calls `greet` dynamically, similarly to classic reflection's `Method.invoke`, but structured in a way the JIT compiler can optimize far more effectively for repeated calls.

### Level 2 — Intermediate

```java
import java.lang.invoke.*;
import java.lang.reflect.*;

public class VarHandleFieldAccess {
    static class Point {
        int x;
    }

    public static void main(String[] args) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();
        VarHandle xHandle = lookup.findVarHandle(Point.class, "x", int.class);

        Point p = new Point();
        xHandle.set(p, 42);
        System.out.println("via VarHandle: " + (int) xHandle.get(p));

        // Compare against classic reflection doing the equivalent operation:
        Field xField = Point.class.getDeclaredField("x");
        xField.setAccessible(true);
        xField.set(p, 99);
        System.out.println("via reflection: " + xField.get(p));
        System.out.println("via VarHandle (after reflection's write): " + (int) xHandle.get(p));
    }
}
```

**How to run:** `java VarHandleFieldAccess.java` (JDK 17+).

Expected output:
```
via VarHandle: 42
via reflection: 99
via VarHandle (after reflection's write): 99
```

The real-world concern added: `VarHandle` and classic reflection's `Field` both provide dynamic access to the *same* underlying field — writing via one and reading via the other confirms they operate on the identical piece of memory, demonstrating `VarHandle` is a genuine, interoperable alternative to reflective field access, not a separate, disconnected mechanism, while offering the additional atomic and memory-ordering operations explored in the next example.

### Level 3 — Advanced

```java
import java.lang.invoke.*;
import java.util.concurrent.*;

public class VarHandleAtomicCounter {
    static class Counter {
        volatile int count = 0;
    }

    public static void main(String[] args) throws Throwable {
        MethodHandles.Lookup lookup = MethodHandles.lookup();
        VarHandle countHandle = lookup.findVarHandle(Counter.class, "count", int.class);

        Counter counter = new Counter();
        int threadCount = 8;
        int incrementsPerThread = 10_000;

        ExecutorService pool = Executors.newFixedThreadPool(threadCount);
        for (int t = 0; t < threadCount; t++) {
            pool.submit(() -> {
                for (int i = 0; i < incrementsPerThread; i++) {
                    int current;
                    int updated;
                    do {
                        current = (int) countHandle.getVolatile(counter);
                        updated = current + 1;
                    } while (!countHandle.compareAndSet(counter, current, updated)); // lock-free retry loop
                }
            });
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);

        System.out.println("final count: " + counter.count);
        System.out.println("expected: " + (threadCount * incrementsPerThread));
    }
}
```

**How to run:** `java VarHandleAtomicCounter.java` (JDK 17+).

Expected output:
```
final count: 80000
expected: 80000
```

The production-flavored hard case: `countHandle.compareAndSet(counter, current, updated)` performs an atomic compare-and-swap directly on the `count` field, entirely without any explicit `synchronized` block or lock — the retry loop (read the current value, compute the desired update, attempt the atomic swap, retry if another thread beat it to the update) is the classic lock-free concurrent-update pattern, here implemented directly against an ordinary field via `VarHandle`, achieving the exact correctness `AtomicInteger` provides but demonstrating the same underlying mechanism `VarHandle` exposes as a general, reusable capability applicable to any field, not just a dedicated atomic wrapper class.

## 6. Walkthrough

Tracing one thread's execution of the increment loop in `VarHandleAtomicCounter.main`, focusing on how the lock-free retry pattern ensures correctness under concurrent access:

1. A thread reads the current value of `counter.count` via `countHandle.getVolatile(counter)` — using the volatile-read variant specifically ensures this thread sees the most recently completed write to `count` from *any* thread, not a possibly-stale, thread-local cached value.
2. It computes `updated = current + 1` — this computation happens entirely locally to this thread, based on the value it just read, with no coordination with any other thread yet.
3. `countHandle.compareAndSet(counter, current, updated)` then attempts an atomic operation: "if `count`'s current value is still exactly `current` (unchanged since I read it a moment ago), update it to `updated`; otherwise, do nothing and report failure" — this entire check-and-update happens as one indivisible, hardware-supported atomic operation, so no other thread can observe or interfere with it partway through.
4. If no other thread modified `count` between this thread's read and its compare-and-set attempt, the operation succeeds, `compareAndSet` returns `true`, and the `do`/`while` loop's condition (`!true`, i.e., `false`) ends the loop — this thread's increment is now durably reflected in `count`.
5. If, however, another thread's own increment happened to complete in between this thread's read and its compare-and-set attempt, `count`'s actual current value no longer matches `current`, so `compareAndSet` fails, returning `false` — the loop's condition (`!false`, i.e., `true`) causes it to retry: re-read the now-updated `current` value, recompute `updated` based on that fresh value, and attempt the compare-and-set again.
6. This retry-until-success pattern repeats as many times as necessary for each individual increment, across all 8 threads and 80,000 total increment attempts — because every single successful `compareAndSet` genuinely, atomically incorporates exactly one increment with no possibility of two threads' updates silently overwriting each other (the exact race condition explored in [pure functions & immutability](0971-pure-functions-immutability.md)'s parallel-stream example), the final count is guaranteed to be exactly `80,000`, correctly reflecting every single increment from every thread, achieved with no `synchronized` block or explicit lock anywhere in the code.

## 7. Gotchas & takeaways

> **Gotcha:** a `compareAndSet`-based retry loop, while lock-free, is not literally free of all contention cost — under very high contention (many threads simultaneously attempting to update the exact same field), the number of failed, retried attempts can grow significantly, and in pathological cases a thread could theoretically retry many times before succeeding (though genuine indefinite starvation is extremely unlikely in practice on real hardware); for workloads with very high contention on a single shared value, a different concurrency strategy (partitioning the counter across multiple values, or using a higher-level construct like `LongAdder`, which is specifically designed to reduce contention for exactly this scenario) may outperform a naive single-field compare-and-set loop.

- `MethodHandle` and `VarHandle` are JVM-native alternatives to classic reflection's `Method`/`Field`, designed to be far more amenable to JIT optimization, letting repeated dynamic invocations or field accesses approach direct-call performance after warm-up.
- `MethodHandles.Lookup` provides the mechanism for resolving a specific method or field into a `MethodHandle` or `VarHandle`, given its declaring class, name, and type information.
- `VarHandle` additionally provides atomic and memory-ordering operations (`compareAndSet`, `getVolatile`, `setRelease`, and others) as a standard, publicly supported alternative to the internal, unsupported `sun.misc.Unsafe` API many concurrency libraries historically relied on.
- A `compareAndSet`-based retry loop is the classic lock-free concurrent-update pattern: read the current value, compute the desired update, attempt an atomic swap, and retry if another thread's concurrent update was observed instead.
- Reach for `MethodHandle`/`VarHandle` specifically when classic reflection's measured overhead matters, or when you need `VarHandle`'s atomic field-access capabilities directly — classic reflection remains simpler and sufficient for ordinary, infrequent dynamic dispatch needs.
- See [Reflection API deep dive](0983-reflection-api-deep-dive.md) for the classic alternative this API improves upon for performance-sensitive use cases, and [pure functions & immutability](0971-pure-functions-immutability.md) for the race-condition risk that atomic operations like `compareAndSet` are specifically designed to eliminate.
