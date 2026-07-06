---
card: java
gi: 341
slug: java-nio-buffers-bytebuffer-charbuffer
title: java.nio buffers (ByteBuffer, CharBuffer)
---

## 1. What it is

`java.nio` buffers — `ByteBuffer`, `CharBuffer`, and similar type-specific classes — are fixed-capacity containers for primitive data designed for efficient, bulk I/O operations, distinct from the classic stream-based I/O in `java.io`. A buffer tracks three key pointers as you use it: **position** (where the next read/write happens), **limit** (how far you can read/write), and **capacity** (the buffer's total fixed size) — and the same buffer object is reused for both writing data in and reading it back out, switching modes via `flip()`.

```java
import java.nio.ByteBuffer;

public class BufferDemo {
    public static void main(String[] args) {
        ByteBuffer buffer = ByteBuffer.allocate(16);
        buffer.put((byte) 'H');
        buffer.put((byte) 'i');

        buffer.flip(); // switch from writing mode to reading mode
        while (buffer.hasRemaining()) {
            System.out.println((char) buffer.get());
        }
    }
}
```

`flip()` sets the limit to the current position (where writing stopped) and resets the position to zero, so the very next `get()` calls start reading from the beginning of exactly the data that was just written, not from stale or empty space.

## 2. Why & when

Classic `java.io` streams process data one byte (or char) at a time via a simple, sequential API; `java.nio` buffers exist for higher-throughput scenarios — bulk transfers, non-blocking I/O with `Channel`s, and memory-mapped files — where working with a whole block of data as an addressable, position-tracked structure is more efficient than a purely sequential stream.

- **High-throughput file and network I/O** — `FileChannel` and `SocketChannel` read into and write from buffers directly, avoiding the overhead of many small stream reads.
- **Reusable transfer scratch space** — a single `ByteBuffer` can be filled, drained, and refilled repeatedly (via `clear()`/`compact()`) without allocating a new array each time.
- **Interfacing with native/binary formats** — buffers support reading and writing specific primitive types (`getInt()`, `putLong()`, etc.) directly against a byte layout, useful for binary protocols and file formats.

The position/limit/capacity model is genuinely easy to get backwards at first — forgetting to call `flip()` before reading (or `clear()`/`compact()` before writing again) is the single most common buffer bug, since the buffer object itself doesn't complain about being used in the "wrong" mode; it just silently produces wrong results (like reading zero bytes, or overwriting data you meant to keep).

## 3. Core concept

```java
import java.nio.ByteBuffer;

public class BufferCore {
    public static void main(String[] args) {
        ByteBuffer buffer = ByteBuffer.allocate(8);
        System.out.println("New: pos=" + buffer.position() + " limit=" + buffer.limit() + " cap=" + buffer.capacity());

        buffer.putInt(42);
        System.out.println("After putInt: pos=" + buffer.position() + " limit=" + buffer.limit());

        buffer.flip();
        System.out.println("After flip: pos=" + buffer.position() + " limit=" + buffer.limit());

        int value = buffer.getInt();
        System.out.println("Read value: " + value + ", pos now=" + buffer.position());
    }
}
```

**How to run:** `java BufferCore.java`

Each operation moves `position` forward by the number of bytes consumed (`putInt`/`getInt` each move it by 4, an `int`'s size); `limit` starts equal to `capacity` in write mode, then `flip()` pins `limit` to wherever `position` was, precisely bounding how much can be read back.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a buffer's position advances while writing; flip resets position to zero and sets limit to where writing stopped, bounding the subsequent read">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="10">Write mode: put() advances position; limit == capacity</text>
  <rect x="20" y="40" width="400" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="20" y="40" width="150" height="30" fill="#21362b" stroke="#6db33f"/>
  <text x="95" y="60" fill="#6db33f" font-size="9" text-anchor="middle">written data</text>
  <text x="280" y="60" fill="#8b949e" font-size="9" text-anchor="middle">unused capacity</text>

  <text x="20" y="100" fill="#e6edf3" font-size="10">After flip(): position -&gt; 0, limit -&gt; where position was (150)</text>
  <rect x="20" y="110" width="150" height="30" fill="#21362b" stroke="#6db33f"/>
  <text x="95" y="130" fill="#6db33f" font-size="9" text-anchor="middle">readable region (get())</text>
  <text x="200" y="130" fill="#8b949e" font-size="9">← beyond limit is unreachable until clear()/compact()</text>
</svg>

## 5. Runnable example

Scenario: a small in-memory message encoder/decoder, evolved from writing and reading a single value with manual flip, into one handling multiple values and reuse via `clear()`, into a production-style codec that uses `compact()` to preserve leftover unread data across multiple fill cycles.

### Level 1 — Basic

```java
import java.nio.ByteBuffer;

public class CodecBasic {
    public static void main(String[] args) {
        ByteBuffer buffer = ByteBuffer.allocate(4);
        buffer.putInt(12345);
        buffer.flip();
        System.out.println("Decoded: " + buffer.getInt());
    }
}
```

**How to run:** `java CodecBasic.java`

This encodes and decodes exactly one integer using the minimal write-flip-read cycle — it demonstrates the core pattern but doesn't yet show what happens when the buffer needs to be reused for a second round of data.

### Level 2 — Intermediate

```java
import java.nio.ByteBuffer;

public class CodecIntermediate {
    public static void main(String[] args) {
        ByteBuffer buffer = ByteBuffer.allocate(16);

        buffer.putInt(111);
        buffer.putInt(222);
        buffer.flip();
        System.out.println("First round: " + buffer.getInt() + ", " + buffer.getInt());

        buffer.clear(); // reset position=0, limit=capacity -- ready to write again, old data ignored
        buffer.putInt(333);
        buffer.flip();
        System.out.println("Second round: " + buffer.getInt());
    }
}
```

**How to run:** `java CodecIntermediate.java`

`clear()` resets the buffer to a fresh write state (`position=0`, `limit=capacity`) without erasing the underlying bytes — it just makes them logically ignorable so the buffer can be filled with new data and reused, rather than allocating a brand-new `ByteBuffer` for each round.

### Level 3 — Advanced

```java
import java.nio.ByteBuffer;

public class CodecAdvanced {
    public static void main(String[] args) {
        ByteBuffer buffer = ByteBuffer.allocate(12);

        // Simulate a network read that delivers a PARTIAL message: one full int + 2 stray bytes
        buffer.putInt(100);
        buffer.put((byte) 0xAB);
        buffer.put((byte) 0xCD);
        buffer.flip();

        // Only consume the complete int; leave the 2 stray bytes for the next read
        int firstValue = buffer.getInt();
        System.out.println("Consumed complete value: " + firstValue);
        System.out.println("Remaining unread bytes: " + buffer.remaining());

        buffer.compact(); // preserves unread bytes at the START, repositions for more writing
        System.out.println("After compact: pos=" + buffer.position() + " (2 leftover bytes preserved)");

        // Simulate more data arriving, completing a second int: 0xAB 0xCD + 2 more bytes = 4 bytes
        buffer.put((byte) 0x00);
        buffer.put((byte) 0x00);
        buffer.flip();
        System.out.println("Second complete value: " + buffer.getInt());
    }
}
```

**How to run:** `java CodecAdvanced.java`

`compact()` is the key difference from `clear()`: instead of discarding everything, it shifts any *unread* remaining bytes (the two stray bytes left after consuming one complete `int`) to the start of the buffer and repositions for further writing after them — exactly the pattern needed when reading a stream of data that doesn't arrive in neat, complete-message-sized chunks.

## 6. Walkthrough

Execution starts in `main`, which allocates a 12-byte buffer and writes a complete 4-byte `int` (`100`) followed by 2 extra stray bytes (`0xAB`, `0xCD`) — simulating a network read that delivered one whole message plus the start of a second, incomplete one. `position` is now at 6 (4 bytes for the int + 2 more).

`buffer.flip()` sets `limit` to 6 (where writing stopped) and resets `position` to 0, entering read mode. `buffer.getInt()` reads the first 4 bytes as an `int`, correctly decoding `100`, and advances `position` to 4.

`buffer.remaining()` (limit − position = 6 − 4 = 2) confirms 2 unread bytes are left — these are the stray `0xAB`/`0xCD` bytes belonging to a second, not-yet-complete value.

`buffer.compact()` is the crucial step: it copies those 2 remaining unread bytes to positions 0 and 1, then sets `position` to 2 (right after the copied data, ready for more writes) and `limit` back to `capacity` — the buffer is now back in write mode, but critically, the unread bytes were preserved instead of discarded (which is what `clear()` would have done, silently losing them).

Two more bytes are written (`0x00`, `0x00`), completing the second 4-byte value at positions 0–3. `buffer.flip()` sets `limit` to the current `position` (4) and resets `position` to 0. `buffer.getInt()` now reads those 4 bytes — `0xAB 0xCD 0x00 0x00` — as a complete `int` and prints its decoded value.

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="write a complete value plus stray bytes, read only the complete value, compact to preserve the stray bytes, then complete and read the second value">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">1. write: [int=100][0xAB][0xCD] -&gt; position=6</text>
  <text x="20" y="55" fill="#79c0ff" font-size="10">2. flip() -&gt; limit=6, position=0 -&gt; read mode</text>
  <text x="20" y="80" fill="#6db33f" font-size="10">3. getInt() reads first 4 bytes -&gt; 100 -&gt; position=4, remaining=2 (the stray bytes)</text>
  <text x="20" y="105" fill="#6db33f" font-size="10">4. compact() -&gt; stray 2 bytes moved to start -&gt; position=2, limit=capacity -&gt; write mode again</text>
  <text x="20" y="130" fill="#79c0ff" font-size="10">5. write 2 more bytes -&gt; completes a 4-byte value at [0..3]</text>
  <text x="20" y="155" fill="#6db33f" font-size="10">6. flip() -&gt; getInt() reads the now-complete second value</text>
</svg>

## 7. Gotchas & takeaways

> Forgetting `flip()` before reading is the classic buffer bug: `position` is still wherever writing left it, and `limit` is still `capacity`, so `get()`/`getInt()` either reads garbage leftover data past what you actually wrote, or throws `BufferUnderflowException` once it runs past what was ever written.

- Three pointers to track: **position** (next read/write index), **limit** (how far reads/writes may go), **capacity** (fixed total size, set at allocation).
- `flip()` switches from write mode to read mode: `limit = position`, then `position = 0`.
- `clear()` resets fully for writing (`position = 0`, `limit = capacity`) but does **not** erase old bytes — it just makes them logically inaccessible until overwritten.
- `compact()` is like `clear()` but preserves any *unread remaining* bytes by shifting them to the start first — essential when reading a stream that doesn't arrive in complete, aligned chunks.
- Buffers have a fixed `capacity` set at allocation and cannot grow — if more space is needed than a buffer can hold, you must allocate a new, larger buffer and copy data across.
