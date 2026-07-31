---
card: data-structures
gi: 42
slug: stringbuilder-vs-stringbuffer
title: StringBuilder vs StringBuffer
---

## 1. What it is

`StringBuilder` and `StringBuffer` are both mutable character buffer classes with an almost identical API — `append`, `insert`, `delete`, `reverse`, `toString()`. The one difference is **thread safety**: `StringBuffer`'s methods are `synchronized` (safe to call from multiple threads at once), while `StringBuilder`'s are not. `StringBuffer` is the older class (Java 1.0); `StringBuilder` was added later (Java 5) specifically as a faster, unsynchronized alternative for the common single-threaded case.

## 2. Why & when

Use `StringBuilder` by default — almost all string-building happens within a single method, on a single thread, where synchronization is pure overhead with no benefit. Use `StringBuffer` only in the rare case where the exact same buffer instance is genuinely shared and mutated by multiple threads concurrently, and you specifically want built-in synchronization rather than managing it yourself.

## 3. Core concept

**Same API, different synchronization.** Both classes implement the same operations with the same method signatures, so switching between them (if ever needed) is usually a one-word change. The difference is entirely about whether each method call acquires a lock before running.

**Why `StringBuilder` is generally faster.** Every `synchronized` method call on `StringBuffer` must acquire and release an internal lock, even when no other thread is anywhere near it. This lock overhead is pure waste in single-threaded code — the vast majority of real string-building — which is exactly why `StringBuilder` was introduced.

**Synchronization protects individual method calls, not a whole sequence of them.** Even `StringBuffer` is not automatically safe for a *sequence* of operations across threads (like "check length, then append" without external locking) — each individual method call is atomic, but a sequence of several calls interleaved with another thread's calls can still produce a mixed, unpredictable final result. True multi-thread-safe sequences need external synchronization regardless of which class you pick.

**In practice, prefer confining the buffer to one thread.** Rather than reaching for `StringBuffer`'s built-in locking, it is usually simpler and clearer to build each thread's string independently (each thread gets its own local `StringBuilder`) and combine results afterward — avoiding shared mutable state entirely.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="StringBuilder append running directly with no lock, versus StringBuffer append acquiring and releasing a lock on every call">
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="16" fill="#8b949e" text-anchor="middle">StringBuilder.append() -- no lock</text>
    <rect x="80" y="30" width="160" height="30" fill="#161b22" stroke="#3fb950"/><text x="160" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">append() -&gt; runs directly</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">StringBuffer.append() -- synchronized</text>
    <rect x="400" y="30" width="60" height="30" fill="#161b22" stroke="#f0883e"/><text x="430" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">lock</text>
    <rect x="460" y="30" width="100" height="30" fill="#161b22" stroke="#3fb950"/><text x="510" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">append()</text>
    <rect x="560" y="30" width="60" height="30" fill="#161b22" stroke="#f0883e"/><text x="590" y="50" fill="#e6edf3" text-anchor="middle" font-size="9">unlock</text>
    <text x="320" y="100" fill="#79c0ff" text-anchor="middle">the lock/unlock overhead is wasted work in single-threaded code</text>
  </g>
</svg>

`StringBuilder` runs `append()` directly. `StringBuffer` wraps the same work in a lock acquire/release on every call.

## 5. Runnable example

```java
// StringBuilderVsStringBuffer.java
public class StringBuilderVsStringBuffer {

    // Basic: identical API, used the same way.
    static void basicLevel() {
        StringBuilder sb = new StringBuilder();
        sb.append("Hello").append(", ").append("world").append("!");
        System.out.println("basic: StringBuilder result -> " + sb);

        StringBuffer buf = new StringBuffer();
        buf.append("Hello").append(", ").append("world").append("!");
        System.out.println("basic: StringBuffer result -> " + buf);
    }

    // Intermediate: measuring the synchronization overhead in a single-threaded loop.
    static void intermediateLevel() {
        int n = 2_000_000;

        long t1 = System.nanoTime();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) sb.append('x');
        long sbTime = System.nanoTime() - t1;

        long t2 = System.nanoTime();
        StringBuffer buf = new StringBuffer();
        for (int i = 0; i < n; i++) buf.append('x');
        long bufTime = System.nanoTime() - t2;

        System.out.println("intermediate: StringBuilder time(ns) -> " + sbTime);
        System.out.println("intermediate: StringBuffer time(ns) -> " + bufTime + " (lock overhead on every append)");
    }

    // Advanced: even StringBuffer needs external synchronization for a multi-step sequence to be truly safe.
    static final StringBuffer shared = new StringBuffer();

    static synchronized void appendIfShort(String piece) { // external lock guards the whole check-then-append sequence
        if (shared.length() < 20) { // "check"
            shared.append(piece);   // "then append" -- without the outer synchronized, another thread could interleave here
        }
    }

    static void advancedLevel() throws InterruptedException {
        Thread t1 = new Thread(() -> { for (int i = 0; i < 5; i++) appendIfShort("A"); });
        Thread t2 = new Thread(() -> { for (int i = 0; i < 5; i++) appendIfShort("B"); });
        t1.start(); t2.start();
        t1.join(); t2.join();
        System.out.println("advanced: shared buffer after concurrent, guarded appends -> " + shared);
    }

    public static void main(String[] args) throws InterruptedException {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `StringBuilderVsStringBuffer.java`, then run `java StringBuilderVsStringBuffer.java`.

## 6. Walkthrough

1. `basicLevel()` builds the identical `"Hello, world!"` result using both classes, with identical chained `append()` calls — confirming the API is a drop-in match between the two.
2. `intermediateLevel()` appends 2 million characters using each class in a single-threaded loop, timing both. `StringBuffer`'s total time should be noticeably higher, since every one of its 2 million `append()` calls pays lock acquire/release overhead that `StringBuilder` never incurs.
3. `advancedLevel()` shows that using `StringBuffer` alone is not enough to make a "check length, then append" *sequence* safe — the code wraps `appendIfShort` in its own `synchronized` method, using external locking to guard the whole check-then-append sequence as one atomic unit, not relying on `StringBuffer`'s per-call locking to do that job.
4. Two threads each call `appendIfShort` five times. Because `appendIfShort` itself is `synchronized`, only one thread's check-then-append sequence runs at a time — the final `shared` buffer ends up with a consistent, correctly-bounded result instead of a corrupted interleaving.

## 7. Gotchas & takeaways

> Gotcha: choosing `StringBuffer` "to be safe" for ordinary single-threaded string building only adds unnecessary lock overhead with zero safety benefit — thread safety only matters when the *same* buffer instance is genuinely accessed from multiple threads concurrently, which is rare in typical code.

- `StringBuilder` and `StringBuffer` share the same API; the only difference is that `StringBuffer`'s methods are `synchronized`.
- Default to `StringBuilder` — the overwhelming majority of string-building is single-threaded, where synchronization is pure waste.
- Even `StringBuffer` does not make multi-step *sequences* of operations thread-safe on its own; that requires explicit external synchronization.
- Related concepts: [Concatenation cost & why StringBuilder](0036-concatenation-cost-why-stringbuilder.md), [String immutability in Java](0033-string-immutability-in-java.md).
