---
card: java
gi: 303
slug: datainputstream-dataoutputstream
title: DataInputStream / DataOutputStream
---

## 1. What it is

`DataInputStream` and `DataOutputStream` wrap another stream and add methods to read and write Java's primitive types (`int`, `long`, `double`, `boolean`, `UTF`-encoded `String`, and more) directly as their standard binary representations — automating exactly the manual byte-shifting that hand-rolled binary encoding requires.

```java
import java.io.DataOutputStream;
import java.io.DataInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ByteArrayInputStream;
import java.io.IOException;

public class DataStreamDemo {
    public static void main(String[] args) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        DataOutputStream out = new DataOutputStream(baos);
        out.writeInt(42);
        out.writeUTF("hello");

        DataInputStream in = new DataInputStream(new ByteArrayInputStream(baos.toByteArray()));
        System.out.println(in.readInt());
        System.out.println(in.readUTF());
    }
}
```

`writeInt`/`readInt` and `writeUTF`/`readUTF` handle the exact binary layout automatically; values must be read back in the **same order** they were written, since the underlying byte stream has no field names or structure — just a sequence of bytes.

## 2. Why & when

Manually encoding a multi-byte value (as shown when building `BufferedInputStream`/`BufferedOutputStream` intuition) is tedious and error-prone: shifting the wrong number of bits, forgetting the `& 0xFF` mask, or getting byte order backward are all easy mistakes. `DataInputStream`/`DataOutputStream` implement this encoding once, correctly, for every Java primitive type.

- **Compact, portable binary format** — `DataOutputStream` writes primitives in a fixed, well-documented big-endian binary layout, portable across any JVM regardless of platform.
- **String support via `writeUTF`/`readUTF`** — encodes a `String` with a length prefix followed by a modified UTF-8 encoding, so strings of arbitrary length can be written and read back without needing a separate delimiter.
- **Foundation for custom binary protocols** — before higher-level serialization mechanisms, `DataInputStream`/`DataOutputStream` were (and still are) a common way to define a simple, explicit binary wire format.

Use `DataInputStream`/`DataOutputStream` when you need a simple, explicit binary format for primitives and strings without the overhead or "any Java object" flexibility of full object serialization (`ObjectInputStream`/`ObjectOutputStream`). For structured records with many fields, consider whether Java serialization, JSON, or a schema-based format (Protocol Buffers, Avro) fits better than hand-assembling fields with `DataOutputStream`.

## 3. Core concept

```java
import java.io.DataOutputStream;
import java.io.DataInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ByteArrayInputStream;
import java.io.IOException;

public class DataStreamCore {
    public static void main(String[] args) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        DataOutputStream out = new DataOutputStream(baos);
        out.writeInt(1);
        out.writeDouble(2.5);
        out.writeBoolean(true);

        DataInputStream in = new DataInputStream(new ByteArrayInputStream(baos.toByteArray()));
        System.out.println(in.readInt());     // must match write order exactly
        System.out.println(in.readDouble());
        System.out.println(in.readBoolean());
    }
}
```

Three different primitive types are written back to back with no delimiters between them — the reader knows exactly how many bytes each `readXxx` call consumes (4 for `int`, 8 for `double`, 1 for `boolean`) because that size is fixed by the type, which is why the read order and types must exactly mirror the write order and types.

## 4. Diagram

<svg viewBox="0 0 620 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An int, a double, and a boolean are written back to back as a contiguous sequence of bytes with no delimiters">
  <rect x="8" y="8" width="604" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="40" width="90" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="65" y="65" fill="#e6edf3" font-size="10" text-anchor="middle">int (4 bytes)</text>
  <rect x="110" y="40" width="150" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="185" y="65" fill="#e6edf3" font-size="10" text-anchor="middle">double (8 bytes)</text>
  <rect x="260" y="40" width="90" height="40" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="305" y="65" fill="#e6edf3" font-size="10" text-anchor="middle">bool (1 byte)</text>
  <text x="20" y="105" fill="#8b949e" font-size="9">No field names, no delimiters -- read order and types must match the write side exactly.</text>
</svg>

Each primitive type has a fixed byte width, letting `readXxx` consume exactly the right number of bytes with no delimiter needed.

## 5. Runnable example

Scenario: a small binary "player score" record, evolved from a basic single-record write/read into a multi-record file, then into a version that includes a `writeUTF` name field and handles end-of-file detection to read an unknown number of records.

### Level 1 — Basic

```java
import java.io.DataOutputStream;
import java.io.DataInputStream;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.IOException;

public class DataStreamBasic {
    public static void main(String[] args) throws IOException {
        try (DataOutputStream out = new DataOutputStream(new FileOutputStream("score.bin"))) {
            out.writeInt(12345);  // player ID
            out.writeInt(9800);   // score
        }

        try (DataInputStream in = new DataInputStream(new FileInputStream("score.bin"))) {
            int id = in.readInt();
            int score = in.readInt();
            System.out.println("Player " + id + " scored " + score);
        }
    }
}
```

**How to run:** `java DataStreamBasic.java`

Writes two ints back to back; reads them back in the same order they were written — 8 bytes total on disk, with no delimiter needed between the two fields.

### Level 2 — Intermediate

Same score record, now extended with a player name (`writeUTF`) and repeated for multiple players in a single file.

```java
import java.io.DataOutputStream;
import java.io.DataInputStream;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.IOException;

public class DataStreamIntermediate {
    public static void main(String[] args) throws IOException {
        String[] names = {"Alice", "Bob", "Carol"};
        int[] scores = {9800, 7600, 8900};

        try (DataOutputStream out = new DataOutputStream(new FileOutputStream("scores.bin"))) {
            for (int i = 0; i < names.length; i++) {
                out.writeUTF(names[i]);
                out.writeInt(scores[i]);
            }
        }

        try (DataInputStream in = new DataInputStream(new FileInputStream("scores.bin"))) {
            for (int i = 0; i < names.length; i++) {
                String name = in.readUTF();
                int score = in.readInt();
                System.out.println(name + ": " + score);
            }
        }
    }
}
```

**How to run:** `java DataStreamIntermediate.java`

`writeUTF` prefixes each string with its encoded byte length, so `readUTF` knows exactly how many bytes to consume for the name before the fixed 4-byte `int` score that follows — even though `"Alice"`, `"Bob"`, and `"Carol"` have different lengths, each record is self-delimiting.

### Level 3 — Advanced

Same multi-record file, now read back **without knowing the record count in advance**, using `readUTF`'s `EOFException` at end-of-file to know when to stop — a realistic scenario when a file's record count isn't stored separately.

```java
import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class DataStreamAdvanced {
    record PlayerScore(String name, int score) {}

    public static void main(String[] args) throws IOException {
        String[] names = {"Alice", "Bob", "Carol", "Dave"};
        int[] scores = {9800, 7600, 8900, 6100};

        try (DataOutputStream out = new DataOutputStream(new FileOutputStream("scores2.bin"))) {
            for (int i = 0; i < names.length; i++) {
                out.writeUTF(names[i]);
                out.writeInt(scores[i]);
            }
        }

        List<PlayerScore> results = new ArrayList<>();
        try (DataInputStream in = new DataInputStream(new FileInputStream("scores2.bin"))) {
            while (true) {
                try {
                    String name = in.readUTF();
                    int score = in.readInt();
                    results.add(new PlayerScore(name, score));
                } catch (EOFException e) {
                    break; // no more records
                }
            }
        }

        results.forEach(r -> System.out.println(r.name() + ": " + r.score()));
        System.out.println("Total records read: " + results.size());
    }
}
```

**How to run:** `java DataStreamAdvanced.java`

Rather than a `for` loop bounded by a known count, this reads in an unbounded `while (true)` loop until `readUTF()` (or `readInt()`, if a record were truncated mid-way) throws `EOFException`, signaling that no complete record remains — the exception here is used as the expected, structural signal for "end of data," not as an error condition.

## 6. Walkthrough

Trace the reading loop in `DataStreamAdvanced.main` step by step.

**File contents.** `scores2.bin` contains four records back to back, each being a `writeUTF`-encoded name followed by a 4-byte `int` score — no record count is stored anywhere in the file.

**First loop iteration.** `in.readUTF()` reads the length-prefixed string `"Alice"`, consuming exactly the bytes that record occupies. `in.readInt()` reads the next 4 bytes as `9800`. `results.add(new PlayerScore("Alice", 9800))` stores the pair. No exception occurs, so the loop continues.

**Second and third iterations.** Identically process `"Bob"`/`7600` and `"Carol"`/`8900`.

**Fourth iteration.** Processes `"Dave"`/`6100` — the last complete record in the file.

**Fifth iteration attempt.** `in.readUTF()` is called again, but the underlying stream has no more bytes — internally, this attempts to read the 2-byte length prefix that `readUTF` expects at the start of every UTF record, and finds nothing there. This causes `DataInputStream` to throw `EOFException`. The `catch (EOFException e) { break; }` clause catches it and exits the `while (true)` loop cleanly.

**After the loop.** `results` contains exactly four `PlayerScore` entries, in the order they were written. `results.forEach(...)` prints each one; `results.size()` confirms `4`.

```
scores2.bin (no stored count, just 4 records back to back):
  [len]"Alice"[9800] [len]"Bob"[7600] [len]"Carol"[8900] [len]"Dave"[6100]

Read loop:
  iter 1: readUTF -> "Alice", readInt -> 9800   -> added
  iter 2: readUTF -> "Bob",   readInt -> 7600   -> added
  iter 3: readUTF -> "Carol", readInt -> 8900   -> added
  iter 4: readUTF -> "Dave",  readInt -> 6100   -> added
  iter 5: readUTF -> EOFException -> break
```

**Output:**
```
Alice: 9800
Bob: 7600
Carol: 8900
Dave: 6100
Total records read: 4
```

## 7. Gotchas & takeaways

> Fields must be read back in **exactly** the same order and with the exact same types they were written — `DataInputStream`/`DataOutputStream` store no field names or type tags. Reading an `int` where a `double` was written will silently produce garbage (misinterpreting the first 4 of the 8 written bytes), not necessarily an obvious error.

> `writeUTF`/`readUTF` use a **modified** UTF-8 encoding (with a 2-byte length prefix), not the same as `String.getBytes(StandardCharsets.UTF_8)` — mixing `writeUTF` on one side with manual byte decoding assuming plain UTF-8 on the other will corrupt data. Always pair `writeUTF` with `readUTF`, and standard `getBytes`/`new String(bytes, charset)` with each other, never crossed.

- `DataInputStream`/`DataOutputStream` read and write Java primitives (and UTF-8 strings via `writeUTF`/`readUTF`) in a fixed, portable binary format.
- Data has no field names or delimiters between fixed-width primitives — the reader must know the exact type and order to decode correctly.
- `readUTF` (and other read methods) throw `EOFException` when the stream ends before a complete value can be read — a useful, expected signal for "no more records" when record count isn't stored separately.
- Reach for this pair when you need a simple, explicit binary format for primitives and strings, without the broader flexibility (and overhead) of full object serialization.
