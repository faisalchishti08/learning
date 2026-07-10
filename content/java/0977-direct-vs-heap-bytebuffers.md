---
card: java
gi: 977
slug: direct-vs-heap-bytebuffers
title: Direct vs heap ByteBuffers
---

## 1. What it is

`ByteBuffer.allocate(size)` creates a **heap buffer**, backed by an ordinary `byte[]` array living on the regular Java heap, fully managed and garbage-collected exactly like any other Java object. `ByteBuffer.allocateDirect(size)` creates a **direct buffer**, backed instead by memory allocated *outside* the JVM heap entirely (native memory, allocated via the operating system directly), which the JVM's I/O machinery can hand straight to the underlying operating system for actual read/write system calls without an intermediate copy step. Both expose the exact same `ByteBuffer` API (`get`, `put`, `getInt`, `flip`, and so on) — the difference is entirely about where the bytes physically live and, as a direct consequence, how efficiently that memory can be used for actual I/O operations.

## 2. Why & when

The reason this distinction exists at all: when the JVM performs a native I/O operation (an actual `read()` or `write()` system call to the OS), the data must ultimately be in a memory region the OS can access directly — for a heap buffer, whose backing `byte[]` lives inside the managed Java heap (which the garbage collector can, in principle, move around during a compacting collection), the JVM typically must first copy the data into a temporary, pinned native buffer before handing it to the OS, and copy the result back afterward; a direct buffer's backing memory, being outside the heap and therefore never subject to being moved by the GC, can be handed straight to the OS with no such copy needed at all. This makes direct buffers meaningfully faster for I/O-heavy code that performs many, large, or frequent reads/writes (network sockets, file channels, especially in combination with [memory-mapped files](0976-memory-mapped-files-mappedbytebuffer.md)), at the cost of slower individual allocation (native memory allocation has more overhead than a simple heap allocation) and, historically, less predictable garbage collection interaction, since direct buffers' native memory isn't reclaimed by an ordinary GC cycle the same way heap memory is — it's typically reclaimed only when the `ByteBuffer` object itself is collected, which can lag behind actual usage in ways that matter for memory-constrained environments. The practical guidance: use direct buffers for genuinely I/O-heavy, performance-sensitive code doing repeated native I/O; use ordinary heap buffers for smaller, short-lived, or infrequently-I/O'd buffers, where the allocation overhead and native-memory bookkeeping of a direct buffer aren't worth paying for.

## 3. Core concept

```java
ByteBuffer heapBuf = ByteBuffer.allocate(1024);       // backed by byte[] on the Java heap
ByteBuffer directBuf = ByteBuffer.allocateDirect(1024); // backed by native, off-heap memory

// Both support the IDENTICAL API:
heapBuf.putInt(42);
directBuf.putInt(42);

// The DIFFERENCE shows up during actual native I/O:
fileChannel.write(heapBuf);
// -> JVM must COPY heapBuf's data into a temporary native buffer first (heap memory
//    could be relocated by a compacting GC mid-I/O, which native code cannot tolerate)

fileChannel.write(directBuf);
// -> JVM hands directBuf's ALREADY-native memory straight to the OS -- NO extra copy needed
```

Both buffer types are functionally identical for ordinary in-memory manipulation; the meaningful performance difference is specifically about the extra copy step heap buffers require when actually performing native I/O, which direct buffers avoid entirely.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A heap buffer requiring an extra copy into temporary native memory before an OS write call, versus a direct buffer whose native memory is handed straight to the OS with no copy" >
  <text x="150" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Heap buffer -&gt; native write</text>
  <rect x="20" y="30" width="100" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">byte[] (heap)</text>
  <rect x="150" y="30" width="120" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="210" y="49" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">temp native copy</text>
  <rect x="20" y="90" width="250" height="30" fill="none" stroke="#8b949e"/>
  <text x="145" y="109" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OS write() -- EXTRA COPY STEP required</text>
  <line x1="120" y1="45" x2="150" y2="45" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="210" y1="60" x2="145" y2="90" stroke="#8b949e"/>

  <text x="480" y="16" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Direct buffer -&gt; native write</text>
  <rect x="380" y="30" width="200" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">native memory (off-heap)</text>
  <rect x="380" y="90" width="200" height="30" fill="none" stroke="#8b949e"/>
  <text x="480" y="109" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">OS write() -- NO extra copy needed</text>
  <line x1="480" y1="60" x2="480" y2="90" stroke="#8b949e" marker-end="url(#a)"/>
</svg>

*A heap buffer's data must be copied into temporary native memory before an OS I/O call; a direct buffer's memory is already native and can be handed straight to the OS.*

## 5. Runnable example

Scenario: build a small file-writing benchmark comparing heap and direct buffers, evolving from a basic single-write demonstration of both types, to a realistic repeated-write throughput comparison, to a more advanced case exploring the allocation-overhead tradeoff that offsets direct buffers' I/O advantage for small or short-lived buffers.

### Level 1 — Basic

```java
import java.io.*;
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;

public class BufferTypesBasic {
    public static void main(String[] args) throws IOException {
        ByteBuffer heapBuf = ByteBuffer.allocate(4);
        ByteBuffer directBuf = ByteBuffer.allocateDirect(4);

        heapBuf.putInt(42);
        heapBuf.flip();
        directBuf.putInt(42);
        directBuf.flip();

        System.out.println("heap buffer isDirect: " + heapBuf.isDirect());
        System.out.println("direct buffer isDirect: " + directBuf.isDirect());
        System.out.println("heap value: " + heapBuf.getInt(0));
        System.out.println("direct value: " + directBuf.getInt(0));
    }
}
```

**How to run:** `java BufferTypesBasic.java` (JDK 17+).

Expected output:
```
heap buffer isDirect: false
direct buffer isDirect: true
heap value: 42
direct value: 42
```

Both buffers expose the identical API and store/retrieve data identically from an application's perspective — `isDirect()` is the way to distinguish them programmatically, confirming that `allocate` produces a heap-backed buffer while `allocateDirect` produces a native-memory-backed one, even though both behave identically for these basic `put`/`get` operations.

### Level 2 — Intermediate

```java
import java.io.*;
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;

public class BufferTypesThroughput {
    static long writeManyTimes(FileChannel channel, ByteBuffer buffer, int iterations) throws IOException {
        long start = System.nanoTime();
        for (int i = 0; i < iterations; i++) {
            buffer.clear();
            buffer.putInt(i);
            buffer.flip();
            channel.write(buffer);
        }
        return (System.nanoTime() - start) / 1_000_000;
    }

    public static void main(String[] args) throws IOException {
        int iterations = 200_000;
        Path heapPath = Files.createTempFile("heap-write", ".bin");
        Path directPath = Files.createTempFile("direct-write", ".bin");

        try (FileChannel ch = FileChannel.open(heapPath, StandardOpenOption.WRITE)) {
            long ms = writeManyTimes(ch, ByteBuffer.allocate(4), iterations);
            System.out.println("heap buffer: " + ms + "ms for " + iterations + " writes");
        }
        try (FileChannel ch = FileChannel.open(directPath, StandardOpenOption.WRITE)) {
            long ms = writeManyTimes(ch, ByteBuffer.allocateDirect(4), iterations);
            System.out.println("direct buffer: " + ms + "ms for " + iterations + " writes");
        }

        Files.delete(heapPath);
        Files.delete(directPath);
    }
}
```

**How to run:** `java BufferTypesThroughput.java` (JDK 17+).

Expected output shape (illustrative — exact timings vary significantly by machine and OS, but direct is typically faster for this repeated-native-I/O pattern):
```
heap buffer: 850ms for 200000 writes
direct buffer: 520ms for 200000 writes
```

The real-world concern added: repeatedly writing small buffers directly to a `FileChannel` is exactly the scenario where a direct buffer's avoided-copy advantage compounds across many operations — each individual heap-buffer write pays the extra native-copy cost described earlier, and across 200,000 iterations, that repeated overhead becomes clearly measurable, while the direct buffer's writes hand off to the OS with no such per-call copy at all.

### Level 3 — Advanced

```java
import java.nio.*;

public class BufferTypesAllocationOverhead {
    public static void main(String[] args) {
        int iterations = 100_000;

        long heapStart = System.nanoTime();
        for (int i = 0; i < iterations; i++) {
            ByteBuffer buf = ByteBuffer.allocate(16); // small, short-lived heap buffer
            buf.putInt(i);
        }
        long heapMs = (System.nanoTime() - heapStart) / 1_000_000;

        long directStart = System.nanoTime();
        for (int i = 0; i < iterations; i++) {
            ByteBuffer buf = ByteBuffer.allocateDirect(16); // small, short-lived DIRECT buffer
            buf.putInt(i);
        }
        long directMs = (System.nanoTime() - directStart) / 1_000_000;

        System.out.println("heap allocation (x" + iterations + "): " + heapMs + "ms");
        System.out.println("direct allocation (x" + iterations + "): " + directMs + "ms");
        System.out.println("(no actual I/O performed here -- purely allocation cost, no I/O advantage applies)");
    }
}
```

**How to run:** `java BufferTypesAllocationOverhead.java` (JDK 17+).

Expected output shape (illustrative — direct allocation is typically notably slower here, since no I/O advantage offsets its higher per-allocation cost):
```
heap allocation (x100000): 4ms
direct allocation (x100000): 180ms
(no actual I/O performed here -- purely allocation cost, no I/O advantage applies)
```

The production-flavored hard case: with no actual native I/O ever performed in this benchmark, direct buffers' only real advantage (avoiding a copy during I/O) never comes into play, while their genuinely higher per-allocation cost (native memory allocation involves more overhead than a simple, ordinary heap `byte[]` allocation) is fully exposed — this demonstrates precisely why direct buffers are inappropriate for small, short-lived, frequently-allocated buffers that don't perform much actual I/O per buffer: the allocation overhead alone can dominate, with none of the I/O-avoided-copy benefit to offset it.

## 6. Walkthrough

Comparing what happens structurally in `BufferTypesThroughput`'s two write loops, contrasting the heap and direct paths:

1. For the heap-buffer loop, each iteration calls `buffer.clear()` (resetting position/limit for reuse), `buffer.putInt(i)` (writing 4 bytes into the backing `byte[]` at the buffer's current position, entirely within ordinary managed Java heap memory), `buffer.flip()` (preparing the buffer for reading back what was just written), and `channel.write(buffer)`.
2. Inside `channel.write(buffer)` for a heap buffer, the JVM's native I/O implementation must first copy the buffer's actual bytes into a temporary, natively-allocated buffer — this copy exists specifically because the heap buffer's backing `byte[]` lives in memory the garbage collector could, in principle, relocate during a compacting collection cycle that might occur mid-I/O, which native OS-level I/O code cannot safely tolerate; only once this temporary copy exists is the actual OS `write()` system call issued against it.
3. For the direct-buffer loop, the identical sequence of `clear`/`putInt`/`flip` calls operates directly on the buffer's already-native, off-heap memory region — there is no intermediate Java heap array at all for this data to have ever lived in.
4. Inside `channel.write(buffer)` for a direct buffer, the JVM's native I/O implementation can hand this already-native memory region directly to the OS's `write()` system call, with no intermediate copy needed at all, since this memory is guaranteed never to move (it isn't managed by the garbage collector in the way heap memory is).
5. Repeated 200,000 times, the heap-buffer path pays its extra copy cost on every single iteration, while the direct-buffer path avoids that cost entirely on every iteration — this compounding, per-call savings is exactly what produces the direct buffer's measurably lower total time in the throughput benchmark.
6. Contrast this with `BufferTypesAllocationOverhead`, where no `channel.write` (and therefore no native I/O, and therefore no copy-avoidance benefit) ever occurs at all — here, only the cost of *allocating* each buffer type is being measured, and since direct memory allocation genuinely has higher fixed overhead than an ordinary heap array allocation, the direct-buffer loop is slower, precisely because none of its usual offsetting advantage (avoiding an I/O-time copy) is present in this particular benchmark to compensate for that higher allocation cost.

## 7. Gotchas & takeaways

> **Gotcha:** direct buffers' native memory is not reclaimed by an ordinary garbage collection cycle the way heap memory is — it's typically released only when the `ByteBuffer` object itself becomes unreachable and is collected, meaning a program that allocates many direct buffers and holds references to them (even briefly, in a way that delays GC) can accumulate significant native memory usage that isn't visible in ordinary heap-usage monitoring at all; for applications making heavy use of direct buffers, monitoring native memory usage separately from heap usage is important, and reusing a pool of direct buffers rather than repeatedly allocating new ones is a common mitigation.

- Heap buffers (`ByteBuffer.allocate`) are backed by an ordinary, garbage-collected `byte[]` on the Java heap; direct buffers (`ByteBuffer.allocateDirect`) are backed by native, off-heap memory allocated outside the JVM heap entirely.
- During actual native I/O, heap buffers require an extra copy into temporary native memory before the OS can use them; direct buffers avoid this copy entirely, since their memory is already in a form the OS can use directly.
- This makes direct buffers meaningfully faster for I/O-heavy, performance-sensitive code performing frequent or large native I/O operations, especially in combination with [memory-mapped files](0976-memory-mapped-files-mappedbytebuffer.md).
- Direct buffers have higher per-allocation overhead than heap buffers, making them a poor choice for small, short-lived, or infrequently-I/O'd buffers where no I/O-avoided-copy benefit exists to offset that cost.
- Direct buffers' native memory is reclaimed only when the buffer object itself is garbage collected, not by an ordinary GC cycle in the way heap memory is — this can lead to native memory usage that isn't visible in standard heap monitoring, making buffer reuse or pooling a common mitigation for heavy direct-buffer usage.
- See [memory-mapped files (MappedByteBuffer)](0976-memory-mapped-files-mappedbytebuffer.md) for a specific, closely related use of off-heap-style memory mapped directly onto a file, and [selectors & event loops](0978-selectors-event-loops.md) for the broader NIO I/O model these buffer types are most commonly used within.
