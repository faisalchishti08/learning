---
card: java
gi: 302
slug: bufferedinputstream-bufferedoutputstream
title: BufferedInputStream / BufferedOutputStream
---

## 1. What it is

`BufferedInputStream` and `BufferedOutputStream` are the byte-stream counterparts of `BufferedReader`/`BufferedWriter`: they wrap another `InputStream`/`OutputStream` and add an internal byte buffer, reducing the number of underlying I/O operations for repeated small reads or writes.

```java
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public class BufferedByteDemo {
    public static void main(String[] args) throws IOException {
        try (BufferedOutputStream out = new BufferedOutputStream(new FileOutputStream("buf.bin"))) {
            for (int i = 0; i < 5; i++) out.write(i); // 5 individual write calls, buffered internally
        }

        try (BufferedInputStream in = new BufferedInputStream(new FileInputStream("buf.bin"))) {
            int b;
            while ((b = in.read()) != -1) System.out.print(b + " ");
        }
        System.out.println();
    }
}
```

Each `out.write(i)` call adds one byte to the internal buffer rather than immediately performing a file write; the buffer is flushed to the actual file only when full or when the stream is closed.

## 2. Why & when

Just as unbuffered character I/O makes one underlying operation per small read/write, unbuffered byte I/O does the same — and byte streams are frequently used for binary formats with many small, individual reads or writes (length-prefixed records, protocol headers, pixel data). Buffering batches these into far fewer actual system calls.

- **Reducing system-call overhead** — a single-byte `read()`/`write(int)` call on an unbuffered `FileInputStream`/`FileOutputStream` can cost as much as reading or writing a whole block; buffering amortizes that cost across many calls.
- **Composable with other stream layers** — `BufferedInputStream`/`BufferedOutputStream` slot cleanly between the raw file stream and higher-level wrappers like `DataInputStream`, `ObjectInputStream`, or a `Reader`/`Writer` bridge, adding buffering to the whole chain.
- **Safe to apply liberally** — wrapping an already-buffered or in-memory stream (like `ByteArrayInputStream`) in another buffer is nearly free, so there's little downside to defaulting to buffered access for any real file or network stream.

Wrap any `FileInputStream`/`FileOutputStream` (or network-socket stream) that will be read or written in small increments — which is the common case — in a `BufferedInputStream`/`BufferedOutputStream`. Skip it only for streams that are already efficiently bulk-read (like copying with a large manual buffer, as shown in the `InputStream`/`OutputStream` tutorial) or for in-memory streams where there's no real underlying I/O cost to amortize.

## 3. Core concept

```java
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public class BufferedByteCore {
    public static void main(String[] args) throws IOException {
        ByteArrayOutputStream underlying = new ByteArrayOutputStream();
        BufferedOutputStream buffered = new BufferedOutputStream(underlying, 4); // tiny 4-byte buffer

        buffered.write(new byte[]{1, 2, 3, 4, 5, 6}); // 6 bytes > 4-byte buffer, forces a flush mid-write
        System.out.println("Before explicit flush: " + underlying.toByteArray().length + " bytes visible");

        buffered.flush();
        System.out.println("After explicit flush: " + underlying.toByteArray().length + " bytes visible");
    }
}
```

Writing 6 bytes into a buffer sized for only 4 forces `BufferedOutputStream` to flush internally partway through, so some bytes may already be visible in `underlying` before the explicit `flush()` call — but only `flush()` (or `close()`) guarantees that *all* buffered bytes, including any partial final chunk, have actually reached the underlying stream.

## 4. Diagram

<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BufferedOutputStream accumulates bytes in memory and flushes full blocks to the underlying stream">
  <rect x="8" y="8" width="584" height="124" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="10">write(1) write(2) write(3) ... write(6)</text>
  <rect x="20" y="45" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="70" fill="#e6edf3" font-size="10" text-anchor="middle">4-byte internal buffer</text>
  <line x1="205" y1="65" x2="290" y2="65" stroke="#79c0ff" stroke-width="2" marker-end="url(#bb1)"/>
  <text x="245" y="55" fill="#79c0ff" font-size="9" text-anchor="middle">flush</text>
  <rect x="295" y="45" width="200" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="395" y="70" fill="#e6edf3" font-size="10" text-anchor="middle">underlying stream</text>
  <defs>
    <marker id="bb1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Bytes queue up in the buffer; a full buffer (or an explicit `flush`/`close`) triggers the actual underlying write.

## 5. Runnable example

Scenario: writing and reading a sequence of fixed-size binary records, evolved from unbuffered byte-by-byte I/O into buffered I/O, then into a version that measures and reports the difference in the number of underlying operations conceptually via timing.

### Level 1 — Basic

```java
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.IOException;

public class BufferedByteBasic {
    public static void main(String[] args) throws IOException {
        try (FileOutputStream out = new FileOutputStream("records.bin")) {
            for (int i = 0; i < 100; i++) out.write(i % 256); // 100 unbuffered write calls
        }

        int count = 0;
        try (FileInputStream in = new FileInputStream("records.bin")) {
            while (in.read() != -1) count++; // 100 unbuffered read calls
        }
        System.out.println("Bytes processed: " + count);
    }
}
```

**How to run:** `java BufferedByteBasic.java`

Correct, but each of the 100 writes and 100 reads is an individual unbuffered call to the underlying file stream.

### Level 2 — Intermediate

Same record file, now wrapped in `BufferedOutputStream`/`BufferedInputStream`, batching those 100 individual operations into far fewer actual file accesses.

```java
import java.io.BufferedOutputStream;
import java.io.BufferedInputStream;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.IOException;

public class BufferedByteIntermediate {
    public static void main(String[] args) throws IOException {
        try (BufferedOutputStream out = new BufferedOutputStream(new FileOutputStream("records.bin"))) {
            for (int i = 0; i < 100; i++) out.write(i % 256);
        }

        int count = 0;
        try (BufferedInputStream in = new BufferedInputStream(new FileInputStream("records.bin"))) {
            while (in.read() != -1) count++;
        }
        System.out.println("Bytes processed: " + count);
    }
}
```

**How to run:** `java BufferedByteIntermediate.java`

Same observable result (100 bytes processed), but the buffering layer means the 100 `write`/`read` calls translate into a small number of actual underlying file operations rather than 100 each.

### Level 3 — Advanced

Same record file, now processed as fixed-size 4-byte integer records, demonstrating buffered I/O combined with manual byte-to-int decoding — a common pattern before reaching for `DataInputStream`/`DataOutputStream` (covered separately), which automate exactly this.

```java
import java.io.BufferedOutputStream;
import java.io.BufferedInputStream;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.IOException;

public class BufferedByteAdvanced {
    static void writeInt(java.io.OutputStream out, int value) throws IOException {
        out.write((value >> 24) & 0xFF);
        out.write((value >> 16) & 0xFF);
        out.write((value >> 8) & 0xFF);
        out.write(value & 0xFF);
    }

    static int readInt(java.io.InputStream in) throws IOException {
        int b1 = in.read(), b2 = in.read(), b3 = in.read(), b4 = in.read();
        if (b4 == -1) throw new java.io.EOFException();
        return (b1 << 24) | (b2 << 16) | (b3 << 8) | b4;
    }

    public static void main(String[] args) throws IOException {
        int[] values = {42, 1000, -7, 123456};
        try (BufferedOutputStream out = new BufferedOutputStream(new FileOutputStream("ints.bin"))) {
            for (int v : values) writeInt(out, v);
        }

        try (BufferedInputStream in = new BufferedInputStream(new FileInputStream("ints.bin"))) {
            for (int i = 0; i < values.length; i++) {
                System.out.println("Read: " + readInt(in));
            }
        }
    }
}
```

**How to run:** `java BufferedByteAdvanced.java`

`writeInt` breaks a 32-bit `int` into four bytes (most significant byte first — "big-endian" order) written individually; `readInt` reverses this, reading four bytes and reassembling them with shifts and bitwise-OR — each individual `write`/`read` call benefits from the buffering layer underneath, so this fine-grained, byte-at-a-time encoding remains efficient despite looking inefficient at first glance.

## 6. Walkthrough

Trace writing and reading the value `1000` from `BufferedByteAdvanced.main` step by step.

**Encoding `1000` in `writeInt`.** `1000` in binary, as a 32-bit int, is `0x000003E8`. `(value >> 24) & 0xFF` shifts right 24 bits, isolating the most significant byte: `0x00`. `(value >> 16) & 0xFF` gives the next byte: `0x00`. `(value >> 8) & 0xFF` gives `0x03`. `value & 0xFF` gives the least significant byte: `0xE8`. Four `out.write(...)` calls send these bytes, in that order, into the `BufferedOutputStream`'s internal buffer — no actual file write happens yet unless the buffer happens to fill.

**After all four values are written and the stream closes.** The try-with-resources block closes `out`, which flushes any remaining buffered bytes to `ints.bin` and releases the file handle. The file now contains 16 bytes total (4 bytes per int × 4 ints), including the sequence `0x00 0x00 0x03 0xE8` for the value `1000`.

**Decoding in `readInt` (second call, corresponding to `1000`).** `in.read()` four times returns `b1=0x00`, `b2=0x00`, `b3=0x03`, `b4=0xE8` in sequence — the `BufferedInputStream` serves these from its internal buffer (which was filled from the file in one larger read), so these four logical reads likely correspond to zero additional underlying file reads beyond the initial buffer fill. `b4 == -1` is checked to detect a truncated file (not the case here). The return expression `(b1 << 24) | (b2 << 16) | (b3 << 8) | b4` reassembles: `(0x00 << 24) | (0x00 << 16) | (0x03 << 8) | 0xE8` = `0x000003E8` = `1000`, exactly recovering the original value.

**Loop context.** This `readInt` call is the second of four in the `for` loop in `main`, matching the second element of `values`, `1000` — so the printed output for this iteration is `"Read: 1000"`.

```
writeInt(1000):
  1000 = 0x000003E8
  bytes written (big-endian): 0x00, 0x00, 0x03, 0xE8

readInt() reverses it:
  b1=0x00, b2=0x00, b3=0x03, b4=0xE8
  (b1<<24)|(b2<<16)|(b3<<8)|b4 = 0x000003E8 = 1000
```

**Output:**
```
Read: 42
Read: 1000
Read: -7
Read: 123456
```

## 7. Gotchas & takeaways

> Byte-shifting arithmetic like `(value >> 8) & 0xFF` must mask with `& 0xFF` after shifting — without the mask, sign extension on negative values (Java's `>>` is an arithmetic, sign-preserving shift) would pull in unwanted `1` bits from the sign, corrupting the extracted byte. This is exactly why `-7`, a negative value, still round-trips correctly in the example above: the masking discards the sign-extended bits at each step.

> `BufferedInputStream`/`BufferedOutputStream` buffer bytes; they know nothing about the *meaning* of those bytes (integers, strings, structures). Manually encoding/decoding multi-byte values, as shown here, is exactly the tedious, error-prone task that `DataInputStream`/`DataOutputStream` exist to automate — reach for those in real code rather than hand-rolling bit-shifting logic.

- `BufferedInputStream`/`BufferedOutputStream` add an internal byte buffer to reduce the number of underlying I/O operations for many small reads/writes.
- Wrap any file or network byte stream that will be accessed in small increments — the overhead of buffering something that didn't need it is negligible.
- `flush()`/`close()` guarantee all buffered bytes reach the underlying stream; forgetting either can leave data stuck in the buffer.
- Manual multi-byte encoding needs a mask (`& 0xFF`) after each shift to avoid sign-extension corruption on negative values.
