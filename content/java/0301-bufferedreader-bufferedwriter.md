---
card: java
gi: 301
slug: bufferedreader-bufferedwriter
title: BufferedReader / BufferedWriter
---

## 1. What it is

`BufferedReader` and `BufferedWriter` wrap another `Reader`/`Writer` and add an internal in-memory buffer, so repeated small reads/writes are batched into fewer, larger underlying operations. `BufferedReader` additionally provides `readLine()`, the standard way to read a text stream one line at a time.

```java
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;

public class BufferedDemo {
    public static void main(String[] args) throws IOException {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("buf.txt"))) {
            writer.write("line one");
            writer.newLine();
            writer.write("line two");
        }

        try (BufferedReader reader = new BufferedReader(new FileReader("buf.txt"))) {
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }
        }
    }
}
```

`BufferedWriter.newLine()` writes the platform-appropriate line separator; `BufferedReader.readLine()` reads up to (and strips) any line terminator, returning `null` only at true end-of-stream.

## 2. Why & when

Every unbuffered `Reader`/`Writer` call to its underlying source ultimately triggers a system call when it reaches the real file or socket. Calling `write` or `read` many times with small amounts of data — one character, one short line — makes many more system calls than necessary, which is measurably slow. Buffering batches those calls.

- **Fewer underlying I/O operations** — `BufferedReader`/`BufferedWriter` accumulate data in memory and only touch the underlying stream when the buffer fills up (on write) or is exhausted (on read), turning many small operations into few large ones.
- **Line-based text processing** — `readLine()` is the standard idiom for "process this file one line at a time," used constantly for logs, CSVs, and configuration files.
- **Negligible overhead when already buffered** — wrapping an already-fast source (like a `StringReader`) in `BufferedReader` costs almost nothing, so it's safe to add defensively.

Wrap essentially every `FileReader`/`FileWriter` (and often `InputStreamReader`/`OutputStreamWriter`) in a `BufferedReader`/`BufferedWriter` unless you have a specific reason not to — the performance cost of forgetting to buffer file I/O that does many small operations can be dramatic, while the cost of buffering something that didn't need it is negligible.

## 3. Core concept

```java
import java.io.BufferedWriter;
import java.io.StringWriter;
import java.io.IOException;

public class BufferedCore {
    public static void main(String[] args) throws IOException {
        StringWriter sw = new StringWriter();
        BufferedWriter writer = new BufferedWriter(sw, 8); // tiny 8-char buffer, to show flushing

        writer.write("hello world"); // 11 chars > buffer size, forces at least one internal flush
        writer.flush(); // explicitly push any remaining buffered chars through

        System.out.println("Underlying content: " + sw.toString());
    }
}
```

Because `"hello world"` (11 characters) exceeds the tiny 8-character buffer, `BufferedWriter` must flush its internal buffer to the underlying `StringWriter` at least once mid-write to make room — `flush()` at the end guarantees any remaining buffered characters are pushed through as well, which matters because a `BufferedWriter` that is never flushed (or closed) can leave data stuck in its buffer, invisible to the underlying destination.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Many small writes accumulate in an in-memory buffer and are flushed to the underlying stream in fewer, larger operations">
  <rect x="8" y="8" width="604" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="10">write("a") write("b") write("c") ...</text>
  <line x1="20" y1="45" x2="20" y2="60" stroke="#8b949e"/>
  <rect x="20" y="65" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="90" fill="#e6edf3" font-size="10" text-anchor="middle">in-memory buffer</text>
  <line x1="230" y1="85" x2="320" y2="85" stroke="#79c0ff" stroke-width="2" marker-end="url(#b1)"/>
  <text x="275" y="75" fill="#79c0ff" font-size="9" text-anchor="middle">flush when full</text>
  <rect x="325" y="65" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="435" y="90" fill="#e6edf3" font-size="10" text-anchor="middle">underlying stream (file, etc.)</text>
  <text x="20" y="135" fill="#8b949e" font-size="9">One system call per flush instead of one per write() call.</text>
  <defs>
    <marker id="b1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Buffering trades a small amount of memory for a large reduction in underlying I/O operations.

## 5. Runnable example

Scenario: writing and reading a multi-line report file, evolved from an unbuffered version into a buffered one, then into a line-counting/processing utility that demonstrates the practical value of `readLine()`.

### Level 1 — Basic

```java
import java.io.FileWriter;
import java.io.FileReader;
import java.io.IOException;

public class BufferedBasic {
    public static void main(String[] args) throws IOException {
        try (FileWriter writer = new FileWriter("report.txt")) {
            for (int i = 1; i <= 5; i++) {
                writer.write("Line " + i + "\n"); // unbuffered: one underlying write per call
            }
        }

        try (FileReader reader = new FileReader("report.txt")) {
            int c;
            while ((c = reader.read()) != -1) { // unbuffered: one underlying read per character
                System.out.print((char) c);
            }
        }
    }
}
```

**How to run:** `java BufferedBasic.java`

Works correctly, but each `write`/`read` call may translate to a separate underlying I/O operation — fine for five short lines, but wasteful at scale.

### Level 2 — Intermediate

Same report, now wrapped in `BufferedWriter`/`BufferedReader`, batching the underlying I/O and switching to line-based reading.

```java
import java.io.BufferedWriter;
import java.io.BufferedReader;
import java.io.FileWriter;
import java.io.FileReader;
import java.io.IOException;

public class BufferedIntermediate {
    public static void main(String[] args) throws IOException {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("report.txt"))) {
            for (int i = 1; i <= 5; i++) {
                writer.write("Line " + i);
                writer.newLine();
            }
        }

        try (BufferedReader reader = new BufferedReader(new FileReader("report.txt"))) {
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println("Read: " + line);
            }
        }
    }
}
```

**How to run:** `java BufferedIntermediate.java`

The same five lines are now written and read with far fewer underlying operations — the writer batches characters internally before touching the file, and `readLine()` reads in larger internal chunks rather than one character at a time.

### Level 3 — Advanced

Same report, now processed as a line-counting and word-counting utility, demonstrating a realistic use of buffered line-based reading over a larger generated file.

```java
import java.io.BufferedWriter;
import java.io.BufferedReader;
import java.io.FileWriter;
import java.io.FileReader;
import java.io.IOException;

public class BufferedAdvanced {
    record Stats(int lineCount, int wordCount) {}

    static Stats analyze(String path) throws IOException {
        int lines = 0, words = 0;
        try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = reader.readLine()) != null) {
                lines++;
                if (!line.isBlank()) {
                    words += line.trim().split("\\s+").length;
                }
            }
        }
        return new Stats(lines, words);
    }

    public static void main(String[] args) throws IOException {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("report.txt"))) {
            for (int i = 1; i <= 1000; i++) {
                writer.write("Report line number " + i + " with a few words");
                writer.newLine();
            }
        }

        Stats stats = analyze("report.txt");
        System.out.println("Lines: " + stats.lineCount() + ", Words: " + stats.wordCount());
    }
}
```

**How to run:** `java BufferedAdvanced.java`

Writing 1000 lines and then scanning all of them for line and word counts is exactly the scenario where buffering pays off measurably — without `BufferedWriter`/`BufferedReader`, this program would still be correct, just doing far more underlying I/O calls to accomplish the same work.

## 6. Walkthrough

Trace `BufferedAdvanced.main` step by step.

**Writing phase.** The `for` loop runs 1000 times, each time calling `writer.write(...)` followed by `writer.newLine()`. Internally, `BufferedWriter` appends each string's characters to its in-memory buffer (default size 8192 characters) rather than immediately writing to the file; only when the buffer fills up does it flush its contents to the underlying `FileWriter` in one larger operation. By the time the try-with-resources block closes `writer`, any remaining buffered characters are flushed automatically as part of closing, and `report.txt` contains all 1000 lines.

**`analyze("report.txt")` is called.** Inside, a fresh `BufferedReader` opens the file. The `while ((line = reader.readLine()) != null)` loop repeats 1000 times, once per line. Internally, `BufferedReader` reads a large chunk of the file into its own buffer on the first call, then serves subsequent `readLine()` calls from that in-memory buffer, refilling from the file only when the buffer is exhausted — far fewer actual file-read operations than 1000 individual reads would require.

**Per-line processing.** For each line, `lines++` increments the line counter. `line.isBlank()` guards against empty lines contributing a spurious word count; for the 1000 generated lines here, none are blank. `line.trim().split("\\s+")` splits on runs of whitespace, and `.length` gives the word count for that line — a line like `"Report line number 1 with a few words"` splits into 8 words.

**Accumulation and return.** `words` accumulates across all 1000 lines (8 words each, so `8000` total), and `lines` ends at `1000`. `analyze` returns `new Stats(1000, 8000)`.

**Final print.** Destructures `stats` via its record accessors and prints both counts.

```
Write phase: 1000 lines buffered internally, flushed to report.txt in large chunks (not 1000 tiny writes)

Read phase: readLine() called 1000 times, but the underlying file is read in large chunks internally
  each line -> lines++ ; word count via split("\\s+") -> words += 8

Final: lines=1000, words=8000
```

**Output:**
```
Lines: 1000, Words: 8000
```

## 7. Gotchas & takeaways

> Forgetting to `close()` (or `flush()`) a `BufferedWriter` can leave data sitting in its internal buffer, never written to the underlying destination — the file can appear truncated or entirely empty even though `write` was called successfully. Try-with-resources (as used throughout) handles this automatically by flushing and closing on block exit.

> `readLine()` returns the line **without** its terminator (`\n`, `\r\n`, or `\r`), and `BufferedWriter.newLine()` writes the **platform-appropriate** terminator, which may not be `\n` on every platform. Manually writing `"\n"` instead of calling `newLine()` works on most systems but is technically less portable.

- `BufferedReader`/`BufferedWriter` add an internal buffer to reduce the number of underlying I/O operations, which matters a great deal for many small reads/writes.
- `readLine()` is the standard way to process text line by line; it strips the terminator and returns `null` at end-of-stream.
- Always wrap `FileReader`/`FileWriter` in buffered versions unless there's a specific reason not to — the cost of doing so is negligible even when unnecessary.
- Always close (ideally via try-with-resources) a `BufferedWriter` to ensure buffered data is actually flushed to the destination.
