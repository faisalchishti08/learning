---
card: java
gi: 800
slug: iterable
title: Iterable
---

## 1. What it is

`Iterable<T>` is the single-method root interface that makes an object usable in a **for-each loop**. Any class that implements it has exactly one job: hand out an `Iterator<T>` on request via `iterator()`. Every collection in the Java Collections Framework — `List`, `Set`, `Map`'s key/value/entry views, `Queue`, `Deque` — implements `Iterable`, which is why `for (X x : collection)` works uniformly across all of them. You can also implement it yourself on a completely custom class to make *your* data structure walkable with the same syntax, without exposing how it stores its elements internally.

## 2. Why & when

Before `Iterable` existed as a language-level contract, traversing different collection types meant learning a different API for each one — an array used an index, a linked list used `.next()`, and so on. `Iterable` (introduced alongside the for-each loop and generics in Java 5) unifies all of that behind one interface: if a type can produce an `Iterator`, the compiler can desugar `for (X x : it)` into a `while` loop that calls `hasNext()`/`next()` for you. You implement `Iterable` yourself whenever you have a custom data structure — a `Grid`, a `Tree`, a sequence generator — and want callers to walk it with plain for-each syntax instead of exposing a raw array or an internal `List`. The alternative, exposing `getElements()` returning an internal collection, leaks your storage choice and lets callers mutate internals directly; implementing `Iterable` keeps that boundary clean.

## 3. Core concept

```java
public interface Iterable<T> {
    Iterator<T> iterator();
    // default methods forEach(Consumer) and spliterator() also exist
}
```

The for-each loop is pure syntactic sugar. Writing:

```java
for (String s : someIterable) {
    System.out.println(s);
}
```

is compiled into exactly this:

```java
Iterator<String> it = someIterable.iterator();
while (it.hasNext()) {
    String s = it.next();
    System.out.println(s);
}
```

`Iterable` says nothing about storage, order guarantees, or mutability — it only promises that an `Iterator` is obtainable. Each call to `iterator()` should return a **fresh** iterator, independent of any others already in progress, so two separate for-each loops over the same `Iterable` don't interfere with each other.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A for-each loop over an Iterable is compiled into a call to iterator() followed by a hasNext/next while loop">
  <rect x="20" y="30" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="52" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">for (T x : iterable)</text>
  <text x="120" y="68" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">source code</text>

  <line x1="220" y1="55" x2="270" y2="55" stroke="#79c0ff" stroke-width="2" marker-end="url(#a800)"/>
  <defs><marker id="a800" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="280" y="30" width="200" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="52" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">iterable.iterator()</text>
  <text x="380" y="68" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">compiler-generated</text>

  <line x1="380" y1="80" x2="380" y2="115" stroke="#79c0ff" stroke-width="2" marker-end="url(#a800)"/>

  <rect x="240" y="120" width="280" height="70" rx="8" fill="#0f1620" stroke="#8b949e" stroke-dasharray="4"/>
  <text x="380" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">while (it.hasNext())</text>
  <text x="380" y="163" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">T x = it.next();</text>
  <text x="380" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the actual bytecode loop</text>
</svg>

*The for-each loop is sugar: the compiler rewrites it into `iterator()` plus a `hasNext`/`next` loop.*

## 5. Runnable example

Scenario: a custom `FibonacciSequence` class that generates Fibonacci numbers up to a bound, made walkable with a plain for-each loop by implementing `Iterable<Long>`.

### Level 1 — Basic

```java
import java.util.Iterator;
import java.util.NoSuchElementException;

public class FibonacciBasic implements Iterable<Long> {
    private final int count;

    public FibonacciBasic(int count) {
        this.count = count;
    }

    @Override
    public Iterator<Long> iterator() {
        return new Iterator<Long>() {
            int produced = 0;
            long a = 0, b = 1;

            @Override
            public boolean hasNext() {
                return produced < count;
            }

            @Override
            public Long next() {
                if (!hasNext()) throw new NoSuchElementException();
                long value = a;
                long next = a + b;
                a = b;
                b = next;
                produced++;
                return value;
            }
        };
    }

    public static void main(String[] args) {
        FibonacciBasic fib = new FibonacciBasic(8);
        for (long n : fib) {
            System.out.print(n + " ");
        }
        System.out.println();
    }
}
```

**How to run:** `java FibonacciBasic.java` (JDK 17+).

Expected output:
```
0 1 1 2 3 5 8 13
```

This is the minimum contract: `iterator()` returns a fresh `Iterator<Long>` object whose `hasNext`/`next` pair drives the for-each loop. Each field (`produced`, `a`, `b`) lives inside the anonymous iterator instance, not on `FibonacciBasic` itself — so the sequence's traversal state never touches the `FibonacciBasic` object.

### Level 2 — Intermediate

```java
import java.util.Iterator;
import java.util.NoSuchElementException;

public class FibonacciIndependent implements Iterable<Long> {
    private final int count;

    public FibonacciIndependent(int count) {
        if (count < 0) throw new IllegalArgumentException("count must be >= 0");
        this.count = count;
    }

    @Override
    public Iterator<Long> iterator() {
        return new Iterator<Long>() {
            int produced = 0;
            long a = 0, b = 1;

            @Override
            public boolean hasNext() {
                return produced < count;
            }

            @Override
            public Long next() {
                if (!hasNext()) throw new NoSuchElementException("no more Fibonacci terms");
                long value = a;
                long next = a + b;
                a = b;
                b = next;
                produced++;
                return value;
            }
        };
    }

    public static void main(String[] args) {
        FibonacciIndependent fib = new FibonacciIndependent(5);

        // Two independent for-each loops over the SAME Iterable must not interfere.
        for (long n : fib) {
            System.out.print(n + " ");
        }
        System.out.println("(first pass)");

        for (long n : fib) {
            System.out.print(n + " ");
        }
        System.out.println("(second pass, starts over cleanly)");
    }
}
```

**How to run:** `java FibonacciIndependent.java`.

Expected output:
```
0 1 1 2 3 (first pass)
0 1 1 2 3 (second pass, starts over cleanly)
```

The real-world concern added: guarding the constructor input, and — more importantly — proving that `iterator()` returns **independent** state every time it's called. Because `a`, `b`, and `produced` live inside a brand-new anonymous `Iterator` object per call, running two separate for-each loops over the same `fib` instance doesn't corrupt or share progress between them. If those counters had instead been fields on `FibonacciIndependent` itself, the second loop would silently continue from where the first left off (or throw), which is exactly the bug this design avoids.

### Level 3 — Advanced

```java
import java.util.Iterator;
import java.util.NoSuchElementException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class FibonacciConcurrent implements Iterable<Long> {
    private final int count;

    public FibonacciConcurrent(int count) {
        this.count = count;
    }

    @Override
    public Iterator<Long> iterator() {
        return new Iterator<Long>() {
            int produced = 0;
            long a = 0, b = 1;

            @Override
            public synchronized boolean hasNext() {
                return produced < count;
            }

            @Override
            public synchronized Long next() {
                if (!hasNext()) throw new NoSuchElementException();
                long value = a;
                long next = a + b;
                a = b;
                b = next;
                produced++;
                return value;
            }
        };
    }

    public static void main(String[] args) throws InterruptedException {
        FibonacciConcurrent fib = new FibonacciConcurrent(6);
        ExecutorService pool = Executors.newFixedThreadPool(2);

        // Each thread calls fib.iterator() itself, getting its OWN independent iterator —
        // so both threads can walk the full sequence from the start at the same time,
        // safely, with no shared mutable state between them.
        Runnable task = () -> {
            StringBuilder sb = new StringBuilder(Thread.currentThread().getName() + ": ");
            for (long n : fib) {
                sb.append(n).append(" ");
            }
            System.out.println(sb);
        };

        pool.submit(task);
        pool.submit(task);
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

**How to run:** `java FibonacciConcurrent.java`.

Expected output (line order may vary, values per line never do):
```
pool-1-thread-1: 0 1 1 2 3 5 
pool-1-thread-2: 0 1 1 2 3 5 
```

This adds the production-flavored hard case: two threads iterating the same `Iterable` concurrently. Because `iterator()` hands each caller a brand-new object with its own `a`, `b`, and `produced` fields, the two threads never touch each other's traversal state — each sees the complete sequence `0 1 1 2 3 5`, not an interleaved mess. The `synchronized` on `hasNext`/`next` guards only the shared-nothing case where a single iterator instance were (incorrectly) reused across threads; here it's a defensive habit, not a requirement, since each thread already owns a private iterator.

## 6. Walkthrough

Tracing `FibonacciConcurrent.main`:

1. `main` creates one `FibonacciConcurrent(6)` instance and a two-thread pool.
2. Both submitted tasks run the same `Runnable`, which starts a for-each loop: `for (long n : fib)`.
3. The compiler expands that into `Iterator<Long> it = fib.iterator(); while (it.hasNext()) { long n = it.next(); ... }` for **each thread independently** — so `iterator()` is called twice total, once per thread, each call producing a fresh anonymous `Iterator` object with its own `produced = 0, a = 0, b = 1`.
4. Inside each iterator, `next()` computes the next Fibonacci value, advances `a`/`b`, increments `produced`, and returns the old `a` — the same recurrence (`next = a + b`, shift `a←b`, `b←next`) as the earlier levels, just now running twice in parallel with zero shared state.
5. `hasNext()` stops each loop once `produced` reaches `count` (6), so each thread appends exactly six numbers to its own `StringBuilder`.
6. Each task prints its thread name and full accumulated sequence; because the executor runs both tasks concurrently, the two print lines can appear in either order, but each line's *content* is always the complete, correct sequence — proof that per-call iterator independence, not synchronization, is what makes this safe.

## 7. Gotchas & takeaways

> **Gotcha:** `Iterable` only promises `iterator()`. It says nothing about whether the *same* iterator can be reused, whether elements can be removed mid-traversal, or what happens if the underlying data changes during iteration — those guarantees belong to `Iterator` and to the specific collection, not to `Iterable` itself.

- `Iterable<T>` has one abstract method, `iterator()`, plus default methods `forEach(Consumer<? super T>)` and `spliterator()`.
- The for-each loop is compiler sugar for a `hasNext()`/`next()` while-loop built on `iterator()` — nothing more.
- Every call to `iterator()` should return an **independent** iterator so multiple concurrent or sequential traversals don't interfere with each other.
- Implement `Iterable` on your own types to make them for-each-friendly without exposing internal storage.
- Every standard collection (`List`, `Set`, `Queue`, `Deque`, and `Map`'s `keySet()`/`values()`/`entrySet()`) already implements `Iterable` — that's why the same for-each syntax works across all of them.
