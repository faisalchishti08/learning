---
card: java
gi: 976
slug: memory-mapped-files-mappedbytebuffer
title: Memory-mapped files (MappedByteBuffer)
---

## 1. What it is

Memory-mapped file I/O maps a file's contents directly into a process's virtual address space, so that reading or writing bytes at a given position in memory is, transparently, reading or writing that same position in the underlying file, with the operating system's virtual memory system handling the actual disk I/O behind the scenes, on demand, as pages are accessed. In Java, this is exposed through `FileChannel.map(mode, position, size)`, which returns a `MappedByteBuffer` — a `ByteBuffer` subclass whose backing memory is the mapped file region itself, rather than ordinary heap or off-heap allocated memory — letting you read and write file contents using ordinary `ByteBuffer` methods (`getInt`, `putLong`, and so on) instead of explicit `read`/`write` system calls through a stream or channel.

## 2. Why & when

Memory-mapped files matter for workloads that need very fast, repeated random access into large files — a database engine's own storage layer, a large binary index file accessed at many scattered offsets, or any scenario where the overhead of separate `read`/`write` system calls for each access would dominate the actual work being done. Because the operating system manages the mapping, pages are loaded from disk lazily, only as they're actually touched (rather than requiring the whole file to be read upfront), and the OS's own page cache — already used for ordinary file I/O — is shared transparently, meaning multiple processes mapping the same file can see a consistent, cached view without extra application-level caching logic. The tradeoffs to weigh: mapping a very large file consumes a correspondingly large chunk of virtual address space (rarely a practical problem on a 64-bit system, but worth knowing), changes made to a writable mapping aren't guaranteed to be durably persisted to disk until explicitly flushed (`MappedByteBuffer.force()`), and — a specific, historically painful Java limitation — there was for a long time no reliable, portable way to explicitly unmap a `MappedByteBuffer` before the object was garbage collected, which could cause file-deletion or file-replacement operations to fail unexpectedly on some platforms (notably Windows) while a mapping was still active.

## 3. Core concept

```java
try (FileChannel channel = FileChannel.open(path, StandardOpenOption.READ, StandardOpenOption.WRITE)) {
    MappedByteBuffer buffer = channel.map(FileChannel.MapMode.READ_WRITE, 0, channel.size());

    int value = buffer.getInt(100);      // reads 4 bytes starting at file offset 100 --
                                           // the OS transparently loads that page from disk if needed
    buffer.putInt(100, value + 1);        // writes 4 bytes back -- modifies the MAPPED page in memory;
                                           // NOT guaranteed durably on disk until force() is called

    buffer.force();                       // explicitly flush modified pages to disk
}
```

`MappedByteBuffer` behaves like an ordinary in-memory `ByteBuffer` for read/write operations, but its backing storage is the operating system's page cache for the mapped file region — reads transparently trigger disk I/O on a page fault if the data isn't already cached, and writes modify pages that must eventually be written back to disk, either by the OS's own periodic write-back or by an explicit `force()` call.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A file on disk mapped directly into a process's virtual address space, with reads and writes to the mapped buffer transparently reflected in the underlying file pages via the operating system" >
  <rect x="20" y="30" width="220" height="100" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Process virtual memory</text>
  <rect x="40" y="65" width="180" height="50" fill="none" stroke="#79c0ff"/>
  <text x="130" y="95" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">MappedByteBuffer region</text>

  <rect x="400" y="30" width="220" height="100" fill="#1c2430" stroke="#f0883e"/>
  <text x="510" y="50" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">File on disk</text>
  <rect x="420" y="65" width="180" height="50" fill="none" stroke="#e6edf3"/>
  <text x="510" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">same bytes, same offsets</text>

  <line x1="240" y1="90" x2="400" y2="90" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="320" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OS page cache maps</text>
  <line x1="400" y1="105" x2="240" y2="105" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="320" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">writes eventually flushed back</text>
</svg>

*Reading or writing to the mapped buffer is transparently reading or writing the corresponding bytes of the underlying file, mediated by the OS page cache.*

## 5. Runnable example

Scenario: build a small binary record-store using a memory-mapped file, evolving from a basic single-value read/write, to a realistic fixed-size record layout supporting random access by index, to a more advanced case demonstrating explicit durability control via `force()` and safely closing a mapped resource.

### Level 1 — Basic

```java
import java.io.*;
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;

public class MappedFileBasic {
    public static void main(String[] args) throws IOException {
        Path path = Files.createTempFile("mapped-demo", ".bin");

        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            MappedByteBuffer buffer = channel.map(FileChannel.MapMode.READ_WRITE, 0, 16);
            buffer.putInt(0, 42);
            buffer.putInt(4, 99);
        }

        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.READ)) {
            MappedByteBuffer buffer = channel.map(FileChannel.MapMode.READ_ONLY, 0, 16);
            System.out.println("value at offset 0: " + buffer.getInt(0));
            System.out.println("value at offset 4: " + buffer.getInt(4));
        }

        Files.delete(path);
    }
}
```

**How to run:** `java MappedFileBasic.java` (JDK 17+).

Expected output:
```
value at offset 0: 42
value at offset 4: 99
```

The first block maps a 16-byte region of a fresh file as writable and writes two integers at specific byte offsets (`0` and `4`); the second block reopens the *same* file with a fresh channel and mapping, reading back the identical values from the identical offsets — confirming that the written data genuinely persisted to the underlying file, not just to some in-memory-only buffer.

### Level 2 — Intermediate

```java
import java.io.*;
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;

public class MappedFileFixedRecords {
    static final int RECORD_SIZE = 12; // 4 bytes id + 8 bytes double value

    static void writeRecord(MappedByteBuffer buffer, int index, int id, double value) {
        int offset = index * RECORD_SIZE;
        buffer.putInt(offset, id);
        buffer.putDouble(offset + 4, value);
    }

    static void printRecord(MappedByteBuffer buffer, int index) {
        int offset = index * RECORD_SIZE;
        int id = buffer.getInt(offset);
        double value = buffer.getDouble(offset + 4);
        System.out.println("record " + index + ": id=" + id + ", value=" + value);
    }

    public static void main(String[] args) throws IOException {
        Path path = Files.createTempFile("records-demo", ".bin");
        int recordCount = 5;

        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            MappedByteBuffer buffer = channel.map(FileChannel.MapMode.READ_WRITE, 0, (long) recordCount * RECORD_SIZE);
            for (int i = 0; i < recordCount; i++) {
                writeRecord(buffer, i, 1000 + i, i * 1.5);
            }
            // Random access: read record 3 without touching records 0, 1, 2, or 4 sequentially.
            printRecord(buffer, 3);
        }

        Files.delete(path);
    }
}
```

**How to run:** `java MappedFileFixedRecords.java` (JDK 17+).

Expected output:
```
record 3: id=1003, value=4.5
```

The real-world concern added: each record occupies a fixed 12-byte slot (`RECORD_SIZE`), letting `writeRecord`/`printRecord` compute any record's byte offset directly (`index * RECORD_SIZE`) and access it in constant time, regardless of file size or how many other records exist — this is exactly the kind of random-access pattern memory-mapped files excel at, since jumping directly to offset `36` (record 3) requires no sequential scanning through the file, and the OS only needs to fault in the specific page containing that offset, not the entire file.

### Level 3 — Advanced

```java
import java.io.*;
import java.lang.ref.*;
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;

public class MappedFileForceAndCleanup {
    public static void main(String[] args) throws IOException {
        Path path = Files.createTempFile("durable-demo", ".bin");

        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            MappedByteBuffer buffer = channel.map(FileChannel.MapMode.READ_WRITE, 0, 8);
            buffer.putLong(0, 123456789L);

            // force() explicitly flushes modified pages to disk -- without this call,
            // the write might only exist in the OS page cache, not yet durably on disk,
            // if the process or machine were to crash immediately afterward.
            buffer.force();
            System.out.println("wrote and forced value to disk");

            // 'buffer' itself holds a reference to the mapped region; letting it go out
            // of scope (and eventually be garbage collected) is historically the only
            // portable way to fully release the underlying OS-level mapping in older
            // JDKs -- explicit unmapping only became directly and portably available
            // via FileChannel.close() interactions and newer APIs in more recent JDKs.
        }

        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.READ)) {
            MappedByteBuffer buffer = channel.map(FileChannel.MapMode.READ_ONLY, 0, 8);
            System.out.println("read back: " + buffer.getLong(0));
        }

        Files.delete(path);
        System.out.println("temp file deleted successfully");
    }
}
```

**How to run:** `java MappedFileForceAndCleanup.java` (JDK 17+).

Expected output:
```
wrote and forced value to disk
read back: 123456789
temp file deleted successfully
```

The production-flavored hard case: `buffer.force()` explicitly requests that any modified pages within the mapped region be written back to durable storage immediately, rather than relying on the operating system's own, unpredictable write-back timing — this matters for any application with a genuine durability requirement (a database's write-ahead log, for instance), where "the write eventually reaches disk at some point" is not sufficient and "the write is confirmed durable before proceeding" is required; the successful `Files.delete` afterward also confirms the mapping did not leave the file locked or otherwise inaccessible once the channel was closed.

## 6. Walkthrough

Tracing `MappedFileForceAndCleanup.main` end to end:

1. A fresh temporary file is created, and a `FileChannel` is opened against it in read/write mode — `channel.map(FileChannel.MapMode.READ_WRITE, 0, 8)` then requests the operating system map the first 8 bytes of this file directly into the process's virtual address space, returning a `MappedByteBuffer` representing that mapped region.
2. `buffer.putLong(0, 123456789L)` writes the 8-byte long value starting at offset 0 within the mapped region — at this point, the write has modified the in-memory page backing this mapping, but the operating system may or may not have yet propagated that modified page back to the physical storage device; from the application's perspective alone, without further action, this is not yet a guaranteed-durable write.
3. `buffer.force()` explicitly instructs the operating system to flush any modified pages in this mapped region to durable storage immediately, blocking until that flush completes — after this call returns, the write is genuinely guaranteed to survive even an immediate process crash or power loss, which is precisely the guarantee a plain `putLong` call alone does not provide.
4. The `try`-with-resources block ends, closing the `FileChannel` — this releases the channel's own resources, though the underlying OS-level memory mapping associated with `buffer` itself may, on some JDK versions and platforms, persist until the `MappedByteBuffer` object itself becomes eligible for garbage collection and is actually collected, a historical quirk specific to how Java's memory-mapped file support was originally designed.
5. A second `FileChannel` is opened against the same file, this time read-only, and a fresh mapping is created over the same 8-byte region — `buffer.getLong(0)` reads back the value, and because the earlier `force()` call guaranteed durability, this read correctly returns `123456789`, confirming the write genuinely reached the underlying file rather than existing only transiently in memory.
6. Finally, `Files.delete(path)` successfully removes the temporary file — printing "temp file deleted successfully" confirms that neither of the two mappings created during this program's run left the file locked or otherwise inaccessible for deletion, which historically was a real, platform-specific concern (particularly on Windows) if a `MappedByteBuffer` mapping wasn't properly released before attempting to delete or replace its underlying file.

## 7. Gotchas & takeaways

> **Gotcha:** on some platforms (historically and most notably Windows), attempting to delete or replace a file while a `MappedByteBuffer` mapping onto it is still active (even after its `FileChannel` has been closed) can fail, because the underlying OS-level mapping isn't guaranteed to be released until the `MappedByteBuffer` object itself is garbage collected — if your application needs to reliably delete or replace a mapped file immediately after use, either avoid relying on garbage collection timing by minimizing how long you hold a reference to the buffer, or use newer JDK APIs and platform-specific workarounds designed to address this historical limitation directly.

- `FileChannel.map` returns a `MappedByteBuffer` whose backing memory is a direct mapping of a region of a file into the process's virtual address space, letting ordinary `ByteBuffer` read/write operations transparently become file I/O, mediated by the operating system's page cache.
- Memory-mapped files excel at fast, repeated random access into large files, since the OS loads only the specific pages actually touched, on demand, rather than requiring the whole file to be read upfront.
- Writes to a writable mapping are not guaranteed durably persisted to disk until explicitly flushed via `MappedByteBuffer.force()` — relying on the OS's own unpredictable write-back timing is insufficient for any genuine durability requirement.
- Historically, there was no fully reliable, portable way to explicitly unmap a `MappedByteBuffer` before it was garbage collected, which could cause file-deletion or replacement operations to fail unexpectedly on some platforms while a mapping remained active.
- A fixed-size record layout, computed by simple offset arithmetic (`index * recordSize`), is a natural, efficient fit for memory-mapped random access, since any record can be reached in constant time regardless of file size.
- See [direct vs heap ByteBuffers](0977-direct-vs-heap-bytebuffers.md) for how `MappedByteBuffer`'s memory characteristics compare to the other `ByteBuffer` variants in the NIO API.
