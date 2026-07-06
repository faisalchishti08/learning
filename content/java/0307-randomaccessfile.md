---
card: java
gi: 307
slug: randomaccessfile
title: RandomAccessFile
---

## 1. What it is

`RandomAccessFile` allows reading from and writing to a file at **arbitrary positions**, unlike `FileInputStream`/`FileOutputStream`, which only ever move forward sequentially from the beginning. It maintains a file pointer that can be moved (`seek`) to any byte offset, and it supports both reading and writing on the same object, in either order.

```java
import java.io.RandomAccessFile;
import java.io.IOException;

public class RandomAccessDemo {
    public static void main(String[] args) throws IOException {
        try (RandomAccessFile raf = new RandomAccessFile("data.bin", "rw")) {
            raf.writeInt(100);
            raf.writeInt(200);
            raf.writeInt(300);

            raf.seek(4); // jump directly to the second int, skipping the first
            System.out.println(raf.readInt()); // 200
        }
    }
}
```

The mode string `"rw"` opens the file for both reading and writing; `seek(4)` moves the file pointer to byte offset 4 (skipping the first `int`, which occupies bytes 0-3), so the next `readInt()` reads the second value directly, without reading past the first.

## 2. Why & when

Sequential streams are the right model for most I/O, but some tasks genuinely need to jump around within a file: updating a specific fixed-size record without rewriting the whole file, reading a file's trailer/index before its main content, or implementing a simple fixed-record database.

- **Fixed-size record access** — if every record in a file is the same size, `seek(recordIndex * recordSize)` jumps straight to any record by index, without reading through everything before it.
- **In-place updates** — modifying part of a file without rewriting the entire thing (impossible with plain sequential streams, which would require reading everything, changing it in memory, and writing it all back out).
- **Combined read/write on one file handle** — unlike separate `FileInputStream`/`FileOutputStream` objects, a single `RandomAccessFile` can both read and write the same file, useful for read-modify-write patterns.

Use `RandomAccessFile` when you genuinely need non-sequential access or in-place updates to fixed-size data; for simple sequential reading or writing, plain streams (possibly buffered) remain simpler and are the better default. For very large files or performance-critical random access, `java.nio`'s `FileChannel` with memory-mapped buffers is the more modern, more scalable alternative.

## 3. Core concept

```java
import java.io.RandomAccessFile;
import java.io.IOException;

public class RandomAccessCore {
    public static void main(String[] args) throws IOException {
        try (RandomAccessFile raf = new RandomAccessFile("pointer.bin", "rw")) {
            raf.writeInt(111);
            System.out.println("Pointer after write: " + raf.getFilePointer()); // 4

            raf.seek(0);
            System.out.println("Pointer after seek(0): " + raf.getFilePointer()); // 0
            System.out.println("Re-read value: " + raf.readInt()); // 111
            System.out.println("Pointer after read: " + raf.getFilePointer()); // 4 again
        }
    }
}
```

Every read or write operation advances the file pointer by however many bytes it consumed; `getFilePointer()` reports the current position, and `seek(position)` explicitly resets it — reading the same 4 bytes twice (once implicitly moved past, once explicitly returned to) demonstrates that position is just a number you fully control.

## 4. Diagram

<svg viewBox="0 0 600 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A file pointer can seek directly to any byte offset instead of only moving forward sequentially">
  <rect x="8" y="8" width="584" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="40" width="560" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <rect x="20" y="40" width="140" height="30" fill="#6db33f" opacity="0.3"/>
  <text x="90" y="60" fill="#e6edf3" font-size="9" text-anchor="middle">record 0</text>
  <rect x="160" y="40" width="140" height="30" fill="#79c0ff" opacity="0.3"/>
  <text x="230" y="60" fill="#e6edf3" font-size="9" text-anchor="middle">record 1</text>
  <rect x="300" y="40" width="140" height="30" fill="#f85149" opacity="0.3"/>
  <text x="370" y="60" fill="#e6edf3" font-size="9" text-anchor="middle">record 2</text>
  <text x="230" y="30" fill="#79c0ff" font-size="9" text-anchor="middle">seek(recordSize * 1) jumps straight here</text>
  <line x1="230" y1="35" x2="230" y2="40" stroke="#79c0ff" stroke-width="2" marker-end="url(#ra1)"/>
  <defs>
    <marker id="ra1" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`seek(offset)` jumps directly to any byte position, unlike sequential streams which can only move forward.

## 5. Runnable example

Scenario: a fixed-size employee record file, evolved from basic sequential writes into direct-index reads via `seek`, then into an in-place update that modifies one record without touching any others.

### Level 1 — Basic

```java
import java.io.RandomAccessFile;
import java.io.IOException;

public class RandomAccessBasic {
    static final int RECORD_SIZE = 4 + 4; // id (int) + salary (int), each 4 bytes

    public static void main(String[] args) throws IOException {
        try (RandomAccessFile raf = new RandomAccessFile("employees.dat", "rw")) {
            raf.writeInt(101); raf.writeInt(50000); // record 0
            raf.writeInt(102); raf.writeInt(60000); // record 1
            raf.writeInt(103); raf.writeInt(55000); // record 2
        }
        System.out.println("Wrote 3 fixed-size records.");
    }
}
```

**How to run:** `java RandomAccessBasic.java`

Writes three records, each exactly 8 bytes (a 4-byte ID and a 4-byte salary), sequentially — establishing the fixed-size layout that makes direct-offset access possible later.

### Level 2 — Intermediate

Same employee file, now read back by directly seeking to any record's offset, without reading the records before it.

```java
import java.io.RandomAccessFile;
import java.io.IOException;

public class RandomAccessIntermediate {
    static final int RECORD_SIZE = 8;

    public static void main(String[] args) throws IOException {
        try (RandomAccessFile raf = new RandomAccessFile("employees.dat", "rw")) {
            raf.writeInt(101); raf.writeInt(50000);
            raf.writeInt(102); raf.writeInt(60000);
            raf.writeInt(103); raf.writeInt(55000);

            // Jump directly to record index 2, skipping records 0 and 1 entirely.
            raf.seek(2L * RECORD_SIZE);
            int id = raf.readInt();
            int salary = raf.readInt();
            System.out.println("Record 2 -> id=" + id + ", salary=" + salary);
        }
    }
}
```

**How to run:** `java RandomAccessIntermediate.java`

`raf.seek(2L * RECORD_SIZE)` computes byte offset 16 (`2 * 8`) and jumps straight there — the file pointer never visits records 0 or 1 at all, demonstrating true random (non-sequential) access.

### Level 3 — Advanced

Same file, now with an in-place update: increasing employee 102's salary by seeking directly to that record's salary field, overwriting only those 4 bytes, and leaving every other record completely untouched.

```java
import java.io.RandomAccessFile;
import java.io.IOException;

public class RandomAccessAdvanced {
    static final int RECORD_SIZE = 8; // id (4 bytes) + salary (4 bytes)
    static final int SALARY_OFFSET_IN_RECORD = 4;

    static void giveRaise(RandomAccessFile raf, int recordIndex, int raiseAmount) throws IOException {
        long salaryPosition = (long) recordIndex * RECORD_SIZE + SALARY_OFFSET_IN_RECORD;
        raf.seek(salaryPosition);
        int currentSalary = raf.readInt();

        raf.seek(salaryPosition); // seek back -- readInt() moved the pointer forward by 4
        raf.writeInt(currentSalary + raiseAmount);
    }

    public static void main(String[] args) throws IOException {
        try (RandomAccessFile raf = new RandomAccessFile("employees2.dat", "rw")) {
            raf.writeInt(101); raf.writeInt(50000);
            raf.writeInt(102); raf.writeInt(60000);
            raf.writeInt(103); raf.writeInt(55000);

            giveRaise(raf, 1, 5000); // employee 102 (record index 1) gets a 5000 raise

            for (int i = 0; i < 3; i++) {
                raf.seek((long) i * RECORD_SIZE);
                int id = raf.readInt();
                int salary = raf.readInt();
                System.out.println("id=" + id + ", salary=" + salary);
            }
        }
    }
}
```

**How to run:** `java RandomAccessAdvanced.java`

`giveRaise` seeks to the exact byte offset of the target record's salary field, reads the current value, seeks **back** to that same offset (since `readInt()` advanced the pointer past it), and writes the new value — only those 4 bytes change; the ID fields and the other two records' data are never touched or rewritten.

## 6. Walkthrough

Trace `giveRaise(raf, 1, 5000)` in `RandomAccessAdvanced.main` step by step.

**Computing the target position.** `recordIndex = 1` refers to the second record (employee 102). `salaryPosition = 1 * 8 + 4 = 12` — byte offset 12 is where that record's salary field begins (record 1 starts at offset 8; its ID occupies bytes 8-11, its salary occupies bytes 12-15).

**First seek and read.** `raf.seek(12)` moves the file pointer directly to byte 12. `raf.readInt()` reads the 4 bytes at offset 12-15, interpreting them as the salary `60000`, and — as a side effect of reading 4 bytes — advances the file pointer to byte 16.

**Seeking back.** Because the pointer is now at 16 (past the field just read), `raf.seek(salaryPosition)` — using the same `salaryPosition = 12` computed earlier — moves the pointer back to byte 12, exactly where the salary field starts. This step is essential: without it, the subsequent write would land at byte 16 (the start of record 2) instead of overwriting record 1's salary.

**Writing the new value.** `raf.writeInt(currentSalary + raiseAmount)` writes `60000 + 5000 = 65000` as 4 bytes starting at byte 12, overwriting exactly the old salary value and nothing else — record 1's ID (bytes 8-11) and all of record 2 (bytes 16-23) remain completely untouched.

**Verification loop.** Back in `main`, the `for` loop seeks to the start of each record in turn (`0`, `8`, `16`) and reads both fields, printing them — record 0 and record 2 show their original values, while record 1 now shows the updated salary.

```
File layout (bytes):
  [0-3]  id=101   [4-7]  salary=50000     <- record 0, untouched
  [8-11] id=102   [12-15] salary=60000    <- record 1, salary field updated in place
  [16-19] id=103  [20-23] salary=55000    <- record 2, untouched

giveRaise(raf, 1, 5000):
  seek(12) -> readInt() -> 60000, pointer now at 16
  seek(12) -> writeInt(65000)             <- overwrites bytes [12-15] only
```

**Output:**
```
id=101, salary=50000
id=102, salary=65000
id=103, salary=55000
```

## 7. Gotchas & takeaways

> Reading advances the file pointer just as writing does — after `readInt()`, the pointer sits **past** the value just read, not at its start. If you intend to overwrite the value you just read (a "read, compute, write back" pattern), you must `seek` back to the original position before writing, exactly as `giveRaise` does — forgetting this writes to the wrong location, silently corrupting the *next* record instead of the intended one.

> `RandomAccessFile`'s mode string matters: `"r"` opens read-only (any write attempt throws `IOException`), while `"rw"` opens for both reading and writing, creating the file if it doesn't exist. There is no plain write-only mode.

- `RandomAccessFile` supports reading and writing at arbitrary byte offsets via `seek(position)`, unlike sequential streams.
- `getFilePointer()` reports the current position; both reads and writes advance it by the number of bytes consumed/produced.
- Ideal for fixed-size record files where you need direct index-based access or in-place updates without rewriting the whole file.
- Remember to `seek` back to a position after reading it if you intend to overwrite that same data — reads move the pointer forward just like writes do.
