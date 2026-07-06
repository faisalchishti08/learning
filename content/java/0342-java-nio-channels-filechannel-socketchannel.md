---
card: java
gi: 342
slug: java-nio-channels-filechannel-socketchannel
title: java.nio channels (FileChannel, SocketChannel)
---

## 1. What it is

`java.nio` channels — `FileChannel` for files, `SocketChannel` for TCP connections, and related classes — are the bulk-transfer counterpart to `java.io` streams, designed to work directly with `Buffer` objects instead of one byte or char at a time. A channel's `read(buffer)` fills the given buffer with data from the underlying source, and `write(buffer)` drains the buffer's remaining content to the underlying destination — both operate on whatever is between the buffer's current position and limit.

```java
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class ChannelDemo {
    public static void main(String[] args) throws Exception {
        Path path = Path.of("channel-demo.txt");
        try (FileChannel channel = FileChannel.open(path,
                StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.wrap("Hello NIO".getBytes());
            channel.write(buffer); // drains the buffer's remaining bytes to the file
        }
        System.out.println("Wrote to " + path.toAbsolutePath());
    }
}
```

`ByteBuffer.wrap(bytes)` creates a buffer backed directly by the given byte array, already positioned to read from the start — `channel.write(buffer)` then writes every remaining byte in that buffer out to the file.

## 2. Why & when

Classic `java.io` streams (`FileInputStream`, `Socket.getInputStream()`) are simple and sequential, one byte or array-chunk at a time; NIO channels exist for scenarios where buffer reuse, non-blocking operation, or direct memory mapping matter — higher-throughput file and network I/O, especially under concurrent or high-volume load.

- **High-throughput file I/O** — `FileChannel` supports efficient bulk reads/writes, memory-mapped files (`map()`), and direct file-to-file transfers (`transferTo`/`transferFrom`) without routing all the bytes through application-level buffers.
- **Non-blocking network I/O** — `SocketChannel` (paired with a `Selector`) can be configured non-blocking, letting a single thread manage many connections at once instead of dedicating a thread per connection.
- **Interoperating with buffers directly** — code that already works with `ByteBuffer` (e.g., for binary protocol parsing) can read and write through channels without converting to and from stream-based APIs.

Channels themselves don't replace all of `java.io` — for simple, low-volume, single-threaded file or socket handling, the classic stream APIs remain simpler to write and read; channels earn their added complexity specifically when buffer reuse, bulk transfer efficiency, or non-blocking behavior are actually needed.

## 3. Core concept

```java
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class ChannelCore {
    public static void main(String[] args) throws Exception {
        Path path = Path.of("channel-core.txt");
        try (FileChannel writeChannel = FileChannel.open(path,
                StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            writeChannel.write(ByteBuffer.wrap("data-payload".getBytes()));
        }

        try (FileChannel readChannel = FileChannel.open(path, StandardOpenOption.READ)) {
            ByteBuffer buffer = ByteBuffer.allocate(64);
            int bytesRead = readChannel.read(buffer); // fills buffer from the file
            buffer.flip(); // switch to read mode before extracting bytes
            byte[] data = new byte[bytesRead];
            buffer.get(data);
            System.out.println("Read " + bytesRead + " bytes: " + new String(data));
        }
    }
}
```

**How to run:** `java ChannelCore.java`

`readChannel.read(buffer)` returns the number of bytes actually read (which can be less than the buffer's capacity), and — exactly as with any buffer used for reading after writing — `flip()` must be called before extracting the data that was just read in.

## 4. Diagram

<svg viewBox="0 0 620 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a channel transfers data directly between an underlying resource (file or socket) and a Buffer object, in either direction">
  <rect x="8" y="8" width="604" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="45" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="70" fill="#79c0ff" font-size="10" text-anchor="middle">File / Socket</text>

  <text x="200" y="60" fill="#8b949e" font-size="9">read() →</text>
  <text x="200" y="85" fill="#8b949e" font-size="9">← write()</text>

  <rect x="270" y="45" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="345" y="70" fill="#8b949e" font-size="10" text-anchor="middle">Channel</text>

  <text x="440" y="60" fill="#8b949e" font-size="9">fills →</text>
  <text x="440" y="85" fill="#8b949e" font-size="9">← drains</text>

  <rect x="500" y="45" width="100" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="550" y="70" fill="#6db33f" font-size="9" text-anchor="middle">Buffer</text>
</svg>

## 5. Runnable example

Scenario: a small file-copy utility, evolved from a single fixed-size buffer copy that assumes the file fits in one read, into a version handling files of any size via a read/write loop, into a production-style copier using `transferTo` for efficient whole-file transfer with a manual fallback loop shown for comparison.

### Level 1 — Basic

```java
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class CopyBasic {
    public static void main(String[] args) throws Exception {
        Path source = Path.of("copy-basic-source.txt");
        Files.writeString(source, "small file contents");
        Path dest = Path.of("copy-basic-dest.txt");

        try (FileChannel in = FileChannel.open(source, StandardOpenOption.READ);
             FileChannel out = FileChannel.open(dest, StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.allocate(1024); // assumes the whole file fits in one buffer
            in.read(buffer);
            buffer.flip();
            out.write(buffer);
        }
        System.out.println("Copied: " + Files.readString(dest));
    }
}
```

**How to run:** `java CopyBasic.java`

This only works because the test file is smaller than the 1024-byte buffer — a single `read()` call is never guaranteed to fill the buffer completely or read the entire file in one call for larger files, so this approach silently truncates any file bigger than the buffer.

### Level 2 — Intermediate

```java
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class CopyIntermediate {
    public static void main(String[] args) throws Exception {
        Path source = Path.of("copy-intermediate-source.txt");
        Files.writeString(source, "a".repeat(5000)); // deliberately larger than one buffer
        Path dest = Path.of("copy-intermediate-dest.txt");

        try (FileChannel in = FileChannel.open(source, StandardOpenOption.READ);
             FileChannel out = FileChannel.open(dest, StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            ByteBuffer buffer = ByteBuffer.allocate(1024);
            int bytesRead;
            while ((bytesRead = in.read(buffer)) != -1) { // loop until end-of-file (-1)
                buffer.flip();
                out.write(buffer);
                buffer.clear(); // reset for the next read
            }
        }
        System.out.println("Copied " + Files.size(dest) + " bytes, matches source: "
                + (Files.size(dest) == Files.size(source)));
    }
}
```

**How to run:** `java CopyIntermediate.java`

Looping `while ((bytesRead = in.read(buffer)) != -1)` correctly handles files of any size, refilling and draining the same reusable buffer repeatedly until `read()` returns `-1` (end of file) — `clear()` resets the buffer for the next fill after each `flip()`-then-`write()` cycle.

### Level 3 — Advanced

```java
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class CopyAdvanced {
    public static void main(String[] args) throws Exception {
        Path source = Path.of("copy-advanced-source.txt");
        Files.writeString(source, "b".repeat(50_000));
        Path dest = Path.of("copy-advanced-dest.txt");

        try (FileChannel in = FileChannel.open(source, StandardOpenOption.READ);
             FileChannel out = FileChannel.open(dest, StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            long size = in.size();
            long transferred = 0;
            // transferTo may transfer fewer bytes than requested in one call, so loop until done
            while (transferred < size) {
                transferred += in.transferTo(transferred, size - transferred, out);
            }
            System.out.println("Transferred " + transferred + " of " + size + " bytes via transferTo.");
        }
        System.out.println("Sizes match: " + (Files.size(dest) == Files.size(source)));
    }
}
```

**How to run:** `java CopyAdvanced.java`

`transferTo` lets the operating system perform the file-to-file copy directly (often via a zero-copy kernel operation, bypassing application-level buffers entirely), which is faster than a manual read/write loop for whole-file copies — but its contract only guarantees it *may* transfer fewer bytes than requested in a single call, so a loop tracking cumulative `transferred` bytes is still required for full correctness on large files.

## 6. Walkthrough

Execution starts in `main`, which writes a 50,000-character source file, then opens both `in` (read) and `out` (create/write) `FileChannel`s.

`in.size()` reports the total byte count of the source file (50,000). The `while (transferred < size)` loop begins with `transferred = 0`.

Each iteration calls `in.transferTo(transferred, size - transferred, out)` — the first argument is the starting position in the source to transfer from, the second is how many bytes are being requested this call, and `out` is the destination channel. The underlying OS moves as many bytes as it can in one internal operation (which may be the full remaining amount, or fewer, depending on OS and channel-type specifics) directly from the source file to the destination file, without those bytes passing through any `ByteBuffer` in this Java code at all. The method returns the actual number of bytes transferred in that call, which is added to `transferred`.

The loop continues, calling `transferTo` again with an updated starting offset (`transferred`) and updated remaining count (`size - transferred`), until `transferred` reaches `size` — at which point the entire file has been copied, potentially across one or several underlying `transferTo` calls, even though the application code never manually managed a single buffer for the copy itself.

After the loop, `main` prints the total bytes transferred and confirms via `Files.size` that source and destination now have identical sizes.

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="transferTo is called in a loop, each call moving some or all remaining bytes directly between channels at the OS level, until the full file size has been transferred">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">transferred=0, size=50000</text>
  <text x="20" y="55" fill="#6db33f" font-size="10">loop: transferTo(transferred, size-transferred, out) -&gt; moves N bytes directly (OS-level, no app buffer)</text>
  <text x="20" y="80" fill="#6db33f" font-size="10">      transferred += N -&gt; repeat until transferred == size</text>
  <text x="20" y="110" fill="#8b949e" font-size="10">Result: full file copied, possibly across multiple transferTo calls, sizes match</text>
</svg>

## 7. Gotchas & takeaways

> `channel.read(buffer)` and `transferTo`/`transferFrom` are not guaranteed to process the full requested amount in a single call — always loop, checking the return value, until you've consumed or transferred everything you intended, rather than assuming one call suffices.

- Channels move data to and from `Buffer` objects in bulk, rather than one byte/char at a time like classic `java.io` streams.
- `read()` returns `-1` at end-of-stream (for a file channel) — the standard way to detect "no more data" in a read loop.
- Always `flip()` a buffer after reading into it (before writing its contents elsewhere) and `clear()` it before reusing it for another read.
- `FileChannel.transferTo`/`transferFrom` can perform efficient, often zero-copy, file-to-file transfers at the OS level — faster than manual buffer-based loops for whole-file copies, but still needs a loop for full correctness since a single call isn't guaranteed to transfer everything requested.
- Reach for NIO channels when bulk throughput, buffer reuse, or non-blocking behavior genuinely matter; for simple, low-volume I/O, classic `java.io` streams are usually simpler to write and read correctly.
