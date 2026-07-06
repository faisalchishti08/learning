---
card: java
gi: 297
slug: inputstream-outputstream-byte-streams
title: InputStream / OutputStream (byte streams)
---

## 1. What it is

`InputStream` and `OutputStream` are the abstract base classes for reading and writing raw **bytes** in Java — the foundation of `java.io`'s byte-stream hierarchy. `InputStream` defines `read()` (returns the next byte, or `-1` at end of stream) plus bulk `read(byte[])` overloads; `OutputStream` defines the mirror-image `write(int)` and `write(byte[])`. Every concrete byte-stream class (`FileInputStream`, `BufferedInputStream`, `System.out`'s underlying stream) extends one of these two.

```java
import java.io.ByteArrayInputStream;
import java.io.IOException;

public class InputStreamDemo {
    public static void main(String[] args) throws IOException {
        byte[] data = {72, 101, 108, 108, 111}; // "Hello" as raw bytes
        InputStream in = new ByteArrayInputStream(data);

        int b;
        while ((b = in.read()) != -1) {
            System.out.print((char) b);
        }
        System.out.println();
    }
}
```

`read()` returns one byte at a time as an `int` in the range `0`-`255`, or `-1` once the stream is exhausted — the `-1` sentinel is why `read()`'s return type is `int` and not `byte` (a real byte value can be negative when interpreted as `byte`, which would be ambiguous with the end-of-stream marker).

## 2. Why & when

Byte streams exist because, at the lowest level, all I/O — files, network sockets, standard input/output — is fundamentally a sequence of bytes. `InputStream`/`OutputStream` provide one uniform abstraction for "a source (or destination) of bytes," regardless of what's on the other end.

- **Binary data** — images, audio, serialized objects, and any non-text file must be handled byte by byte (or in byte chunks); character encodings don't apply.
- **Universal I/O abstraction** — the same `InputStream` interface works whether the bytes come from a file, a network socket, an in-memory array, or a compressed archive — code written against `InputStream` doesn't need to know or care which.
- **Foundation for everything else** — `Reader`/`Writer` (for text) are ultimately built on top of byte streams plus a character encoding; understanding bytes first makes the text-stream layer make sense.

Use byte streams (`InputStream`/`OutputStream` and their subclasses) for binary data or when you need raw control over bytes; use `Reader`/`Writer` for text, since they handle character-encoding conversion for you and operate in terms of `char`, not raw bytes.

## 3. Core concept

```java
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public class InputStreamCore {
    public static void main(String[] args) throws IOException {
        byte[] source = {1, 2, 3, 4, 5};
        InputStream in = new ByteArrayInputStream(source);
        OutputStream out = new ByteArrayOutputStream();

        byte[] buffer = new byte[2];
        int bytesRead;
        while ((bytesRead = in.read(buffer)) != -1) {
            out.write(buffer, 0, bytesRead); // only write the bytes actually read
        }

        System.out.println(java.util.Arrays.toString(((ByteArrayOutputStream) out).toByteArray()));
    }
}
```

`read(buffer)` fills as much of `buffer` as it can and returns how many bytes it actually placed there (which can be less than `buffer.length`, especially near the end of the stream) — `write(buffer, 0, bytesRead)` uses that exact count so no stale or leftover bytes from a previous fill get written by mistake.

## 4. Diagram

<svg viewBox="0 0 620 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bytes flow from a source through an InputStream into a buffer, and from a buffer through an OutputStream to a destination">
  <rect x="8" y="8" width="604" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="45" width="110" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="74" fill="#e6edf3" font-size="10" text-anchor="middle">Source (file, etc.)</text>

  <line x1="132" y1="70" x2="220" y2="70" stroke="#3fb950" stroke-width="2" marker-end="url(#i1)"/>
  <text x="176" y="60" fill="#3fb950" font-size="9" text-anchor="middle">read()</text>

  <rect x="225" y="45" width="110" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="280" y="74" fill="#e6edf3" font-size="10" text-anchor="middle">byte[] buffer</text>

  <line x1="337" y1="70" x2="425" y2="70" stroke="#79c0ff" stroke-width="2" marker-end="url(#i2)"/>
  <text x="381" y="60" fill="#79c0ff" font-size="9" text-anchor="middle">write()</text>

  <rect x="430" y="45" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="505" y="74" fill="#e6edf3" font-size="10" text-anchor="middle">Destination</text>
  <defs>
    <marker id="i1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="i2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Bytes are pulled from the source into a buffer, then pushed from the buffer to the destination — the same loop shape regardless of what the source/destination actually are.

## 5. Runnable example

Scenario: copying binary data from one in-memory stream to another, evolved from a naive single-byte copy into a buffered copy, then into a robust copy utility that reports total bytes moved and closes resources correctly.

### Level 1 — Basic

```java
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public class StreamBasic {
    public static void main(String[] args) throws IOException {
        byte[] source = "Hello, bytes!".getBytes();
        InputStream in = new ByteArrayInputStream(source);
        ByteArrayOutputStream out = new ByteArrayOutputStream();

        int b;
        while ((b = in.read()) != -1) {
            out.write(b);
        }

        System.out.println(out.toString());
    }
}
```

**How to run:** `java StreamBasic.java`

Copies one byte at a time — simple and correct, but slow for large data since each `read()`/`write()` call has overhead.

### Level 2 — Intermediate

Same copy, now using a buffer to move many bytes per call instead of one, which is how real production I/O code copies data.

```java
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public class StreamIntermediate {
    public static void main(String[] args) throws IOException {
        byte[] source = "Hello, buffered bytes!".getBytes();
        InputStream in = new ByteArrayInputStream(source);
        ByteArrayOutputStream out = new ByteArrayOutputStream();

        byte[] buffer = new byte[8]; // deliberately small, to show multiple fills
        int bytesRead;
        int totalCopied = 0;
        while ((bytesRead = in.read(buffer)) != -1) {
            out.write(buffer, 0, bytesRead);
            totalCopied += bytesRead;
        }

        System.out.println("Copied " + totalCopied + " bytes: " + out.toString());
    }
}
```

**How to run:** `java StreamIntermediate.java`

The 8-byte buffer is refilled and re-written multiple times as the loop progresses; each `read(buffer)` call may return fewer than 8 bytes on the final fill, which is exactly why `write(buffer, 0, bytesRead)` — not `write(buffer)` — is used, to avoid writing stale bytes left over from a previous, fuller fill.

### Level 3 — Advanced

Same copy operation, refactored into a reusable utility method that works with real file streams (guaranteeing resources are closed even on error via try-with-resources) and returns the total byte count to the caller.

```java
import java.io.*;

public class StreamAdvanced {
    static long copy(InputStream in, OutputStream out) throws IOException {
        byte[] buffer = new byte[4096]; // realistic buffer size for real I/O
        long total = 0;
        int bytesRead;
        while ((bytesRead = in.read(buffer)) != -1) {
            out.write(buffer, 0, bytesRead);
            total += bytesRead;
        }
        return total;
    }

    public static void main(String[] args) throws IOException {
        File sourceFile = new File("source.bin");
        File destFile = new File("dest.bin");

        try (OutputStream setup = new FileOutputStream(sourceFile)) {
            setup.write("Hello, real file bytes!".getBytes());
        }

        try (InputStream in = new FileInputStream(sourceFile);
             OutputStream out = new FileOutputStream(destFile)) {
            long copied = copy(in, out);
            System.out.println("Copied " + copied + " bytes from " + sourceFile + " to " + destFile);
        }

        System.out.println("Destination contents: " + new String(java.nio.file.Files.readAllBytes(destFile.toPath())));
    }
}
```

**How to run:** `java StreamAdvanced.java` (creates `source.bin` and `dest.bin` in the current directory)

`try (InputStream in = ...; OutputStream out = ...)` is try-with-resources: both streams are guaranteed to be closed (releasing their underlying file handles) when the block exits, whether normally or via an exception — critical for real file I/O, where leaked open file handles are a genuine resource leak.

## 6. Walkthrough

Trace `StreamAdvanced.main` step by step.

**Setup block.** `try (OutputStream setup = new FileOutputStream(sourceFile))` opens `source.bin` for writing (creating it if absent, truncating it if present), writes the bytes of `"Hello, real file bytes!"`, then automatically closes `setup` when the try block ends — `source.bin` now exists on disk with those exact bytes.

**Main copy block opens both streams.** `new FileInputStream(sourceFile)` opens `source.bin` for reading, positioned at byte 0. `new FileOutputStream(destFile)` opens (or creates) `dest.bin` for writing, initially empty.

**`copy(in, out)` runs.** Inside, `buffer` is a fresh 4096-byte array — far larger than the ~24-byte source data, so in this specific case the entire file is read in a single `in.read(buffer)` call, which returns the actual count of bytes read (24, matching the string's length), not `4096`. `out.write(buffer, 0, 24)` writes exactly those 24 bytes to `dest.bin`. `total` becomes `24`. The next call to `in.read(buffer)` returns `-1` (end of file), ending the loop. `copy` returns `24`.

**Back in `main`.** `copied` is `24`, printed alongside the file paths. The try-with-resources block then closes `in` and `out` (in reverse order of declaration) as it exits.

**Final verification.** `Files.readAllBytes(destFile.toPath())` reads the entire `dest.bin` file fresh from disk into a `byte[]`, and wrapping it in `new String(...)` converts those bytes back to readable text using the platform's default character encoding — confirming `dest.bin` now contains exactly what `source.bin` had.

```
source.bin (written first): "Hello, real file bytes!"  (24 bytes)

copy(in, out):
  buffer = new byte[4096]
  in.read(buffer) -> 24 bytes read (whole file fits in one buffer)
  out.write(buffer, 0, 24)
  in.read(buffer) -> -1  (end of file, loop ends)
  return total = 24

dest.bin (after copy): "Hello, real file bytes!"  (24 bytes, identical)
```

**Output:**
```
Copied 24 bytes from source.bin to dest.bin
Destination contents: Hello, real file bytes!
```

## 7. Gotchas & takeaways

> `read()` returns an `int`, not a `byte`, specifically so that `-1` can unambiguously signal end-of-stream — a real byte value, when widened to `int`, is always in the range `0`-`255` (never negative), so `-1` can never be confused with actual data. Forgetting this and comparing against `0` instead of `-1` is a classic beginner bug that causes the loop to stop reading valid null bytes early.

> `read(buffer)` can return **fewer bytes than `buffer.length`**, even before end-of-stream is reached — this is allowed by the contract and is common with network streams. Always use the returned count (as `write(buffer, 0, bytesRead)` does above), never assume the buffer was completely filled.

- `InputStream`/`OutputStream` are the abstract base for all byte-oriented I/O — files, sockets, in-memory buffers, and more all funnel through this same interface.
- `read()` returns `-1` at end-of-stream; bulk `read(byte[])` returns the actual count of bytes placed in the buffer, which may be less than the buffer's length.
- Always use try-with-resources to guarantee streams are closed, even when an exception occurs mid-copy.
- Use byte streams for binary data; use `Reader`/`Writer` (built on top of byte streams) for text, since they handle character-encoding conversion.
