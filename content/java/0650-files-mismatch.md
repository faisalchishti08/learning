---
card: java
gi: 650
slug: files-mismatch
title: Files.mismatch()
---

## 1. What it is

`Files.mismatch(Path path1, Path path2)`, added in **Java 12**, compares two files byte-by-byte and returns the **index of the first mismatched byte**, or `-1L` if the files are completely identical. It's a single static method on `java.nio.file.Files` that replaces the manual "open two streams, read chunks, compare bytes" loop developers used to write themselves. It short-circuits efficiently: if the files differ in length, it doesn't need to compare every byte to know they're different, and if the two paths refer to the very same file, it returns `-1` immediately without touching the filesystem twice.

## 2. Why & when

Comparing two files for equality — or finding exactly where they diverge — used to require writing your own buffered-reading loop with `InputStream`s, tracking byte offsets manually, and handling edge cases like different file lengths or I/O errors yourself. `Files.mismatch()` does this correctly and efficiently in one call, using memory-mapped or buffered comparison under the hood depending on file size. Reach for it whenever you need to verify two files are byte-identical (deployment artifact checks, build reproducibility tests, deduplication) or want to locate precisely where two similar files start to differ (config diffing, debugging a corrupted download).

## 3. Core concept

```java
Path a = Path.of("file-a.txt");
Path b = Path.of("file-b.txt");

long mismatchIndex = Files.mismatch(a, b);

if (mismatchIndex == -1L) {
    System.out.println("Files are identical");
} else {
    System.out.println("Files differ starting at byte " + mismatchIndex);
}
```

Return value is `-1` for "no mismatch" (identical files) or a **zero-based byte offset** pointing at the first differing byte — including the case where one file is simply shorter, where the offset equals the shorter file's length.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two files compared byte by byte; mismatch returns the index of the first differing byte">
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="monospace">file-a.txt:</text>
  <rect x="120" y="15" width="30" height="24" fill="#1c2430" stroke="#6db33f"/><text x="135" y="32" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">H</text>
  <rect x="150" y="15" width="30" height="24" fill="#1c2430" stroke="#6db33f"/><text x="165" y="32" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">e</text>
  <rect x="180" y="15" width="30" height="24" fill="#1c2430" stroke="#f85149" stroke-width="2"/><text x="195" y="32" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">l</text>
  <rect x="210" y="15" width="30" height="24" fill="#1c2430" stroke="#6db33f"/><text x="225" y="32" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">l</text>
  <rect x="240" y="15" width="30" height="24" fill="#1c2430" stroke="#6db33f"/><text x="255" y="32" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">o</text>

  <text x="20" y="75" fill="#8b949e" font-size="11" font-family="monospace">file-b.txt:</text>
  <rect x="120" y="60" width="30" height="24" fill="#1c2430" stroke="#6db33f"/><text x="135" y="77" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">H</text>
  <rect x="150" y="60" width="30" height="24" fill="#1c2430" stroke="#6db33f"/><text x="165" y="77" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">e</text>
  <rect x="180" y="60" width="30" height="24" fill="#1c2430" stroke="#f85149" stroke-width="2"/><text x="195" y="77" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">y</text>
  <rect x="210" y="60" width="30" height="24" fill="#1c2430" stroke="#6db33f"/><text x="225" y="77" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">l</text>
  <rect x="240" y="60" width="30" height="24" fill="#1c2430" stroke="#6db33f"/><text x="255" y="77" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">o</text>

  <line x1="195" y1="45" x2="195" y2="58" stroke="#f85149" stroke-width="1.5"/>
  <text x="195" y="115" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">index 2</text>
  <text x="195" y="135" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">'l' vs 'y' — first difference</text>
  <text x="20" y="160" fill="#79c0ff" font-size="11" font-family="monospace">Files.mismatch(a, b) → 2</text>
</svg>

Bytes at index 0 and 1 match (`H`, `e`); index 2 is the first divergence, so `mismatch()` returns `2`.

## 5. Runnable example

Scenario: verifying whether two generated report files are identical — first a simple identical-vs-different check, then locating exactly where they diverge, then a small tool that compares many file pairs and reports a summary.

### Level 1 — Basic

```java
// File: MismatchBasic.java
import java.nio.file.*;

public class MismatchBasic {
    public static void main(String[] args) throws Exception {
        Path a = Files.writeString(Path.of("a.txt"), "Hello World");
        Path b = Files.writeString(Path.of("b.txt"), "Hello World");
        Path c = Files.writeString(Path.of("c.txt"), "Hello Earth");

        System.out.println("a vs b: " + Files.mismatch(a, b));
        System.out.println("a vs c: " + Files.mismatch(a, c));
    }
}
```

**How to run:** `java MismatchBasic.java` (creates `a.txt`, `b.txt`, `c.txt` in the current directory).

Expected output:
```
a vs b: -1
a vs c: 6
```

`"Hello World"` and `"Hello Earth"` share `"Hello "` (6 characters, indices 0–5), then diverge at index 6 (`W` vs `E`).

### Level 2 — Intermediate

```java
// File: MismatchLocate.java
import java.nio.file.*;

public class MismatchLocate {
    public static void main(String[] args) throws Exception {
        Path expected = Files.writeString(Path.of("expected.txt"), "line1\nline2\nline3\n");
        Path actual = Files.writeString(Path.of("actual.txt"), "line1\nlineX\nline3\n");

        long idx = Files.mismatch(expected, actual);
        if (idx == -1L) {
            System.out.println("Files match exactly.");
            return;
        }

        String content = Files.readString(expected);
        int line = 1;
        for (int i = 0; i < idx; i++) {
            if (content.charAt(i) == '\n') line++;
        }
        System.out.println("First mismatch at byte " + idx + " (line " + line + ")");
    }
}
```

**How to run:** `java MismatchLocate.java`

Expected output:
```
First mismatch at byte 11 (line 2)
```

This turns the raw byte offset into something human-readable — a line number — by counting newlines up to the mismatch index in the expected file's content, which is a common need when diffing text-like files.

### Level 3 — Advanced

```java
// File: MismatchBatch.java
import java.nio.file.*;
import java.util.*;

public class MismatchBatch {
    record Pair(Path a, Path b) {}

    public static void main(String[] args) throws Exception {
        Path dir = Files.createTempDirectory("mismatch-demo");
        Path a1 = Files.writeString(dir.resolve("a1.txt"), "config=true\ntimeout=30\n");
        Path b1 = Files.writeString(dir.resolve("b1.txt"), "config=true\ntimeout=30\n");
        Path a2 = Files.writeString(dir.resolve("a2.txt"), "config=true\ntimeout=30\n");
        Path b2 = Files.writeString(dir.resolve("b2.txt"), "config=false\ntimeout=30\n");
        Path a3 = Files.writeString(dir.resolve("a3.txt"), "short\n");
        Path b3 = Files.writeString(dir.resolve("b3.txt"), "shorter\n");

        List<Pair> pairs = List.of(new Pair(a1, b1), new Pair(a2, b2), new Pair(a3, b3));

        int identical = 0, different = 0;
        for (Pair p : pairs) {
            long idx = Files.mismatch(p.a(), p.b());
            if (idx == -1L) {
                identical++;
                System.out.println(p.a().getFileName() + " == " + p.b().getFileName() + ": identical");
            } else {
                different++;
                System.out.println(p.a().getFileName() + " vs " + p.b().getFileName()
                    + ": differ at byte " + idx);
            }
        }
        System.out.println("Summary: " + identical + " identical, " + different + " different");
    }
}
```

**How to run:** `java MismatchBatch.java`

Expected output:
```
a1.txt == b1.txt: identical
a2.txt vs b2.txt: differ at byte 7
a3.txt vs b3.txt: differ at byte 5
```
followed by:
```
Summary: 1 identical, 2 different
```

Level 3 wraps `Files.mismatch()` in a small batch tool over multiple file pairs stored in a temp directory — note `a3.txt` vs `b3.txt`: `"short\n"` is a *prefix* of `"shorter\n"`, so the mismatch index (`5`, the length of the shorter file's content before its own newline) lands exactly where the shorter file runs out of bytes.

## 6. Walkthrough

1. `main` creates a temp directory and writes six small files with `Files.writeString`, which returns the `Path` it just wrote — used directly to build the `Pair` records.
2. The loop processes `pairs` in order. For the first pair (`a1.txt`, `b1.txt`), both files contain the exact same text, so `Files.mismatch(p.a(), p.b())` compares every byte, finds no difference across the whole length of both files, and returns `-1L`.
3. Because `idx == -1L`, the `if` branch runs: `identical` increments to `1`, and `"a1.txt == b1.txt: identical"` is printed.
4. For the second pair, `a2.txt` has `"config=true\n..."` and `b2.txt` has `"config=false\n..."`. `mismatch()` compares byte-by-byte from the start: `c`,`o`,`n`,`f`,`i`,`g`,`=` all match (indices 0–6), then index 7 is `t` in `a2` vs `f` in `b2` — the first divergence. `mismatch()` returns `7` immediately without reading the rest of either file.
5. The `else` branch runs: `different` increments, and `"a2.txt vs b2.txt: differ at byte 7"` prints.
6. For the third pair, `a3.txt` is `"short\n"` (6 bytes) and `b3.txt` is `"shorter\n"` (8 bytes). Bytes 0–4 (`s`,`h`,`o`,`r`,`t`) match. At index 5, `a3` has `\n` while `b3` has `e` (continuing "shorter") — that's the first mismatch, so `mismatch()` returns `5`.
7. After the loop, `System.out.println` prints the accumulated summary: `1` identical pair and `2` different pairs, giving a compact report over all comparisons performed.

```
a1 vs b1: bytes equal all the way ──► -1 (identical)
a2 vs b2: bytes equal 0..6, differ at 7 ──► 7
a3 vs b3: bytes equal 0..4, differ at 5 (shorter file ends) ──► 5
```

## 7. Gotchas & takeaways

> `Files.mismatch()` compares raw **bytes**, not characters or lines. If you're comparing text files with different encodings or line-ending conventions (`\n` vs `\r\n`), files that look identical when *printed* can still report a mismatch, because the underlying bytes differ. Normalize encoding/line endings first if that distinction shouldn't count as a difference for your use case.

- Returns `-1L` for byte-identical files (including the case where both paths point to the same file — no I/O needed).
- Returns a zero-based byte offset for the first difference, even when the difference is simply "one file ran out of bytes first."
- It's more efficient than reading both files fully into memory and comparing yourself — it can short-circuit on length or use optimized comparison strategies internally.
- Great for build reproducibility checks, deployment verification, and precise diff tooling.
- Remember the result is a byte index, not a line number — convert it yourself (as in Level 2) if you need line-level reporting.
