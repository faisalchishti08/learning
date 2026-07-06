---
card: java
gi: 298
slug: reader-writer-character-streams
title: Reader / Writer (character streams)
---

## 1. What it is

`Reader` and `Writer` are the abstract base classes for reading and writing **text** in Java, operating in terms of `char` rather than raw bytes. They sit on top of the byte-stream world (`InputStream`/`OutputStream`), handling the conversion between bytes and characters according to a specified (or platform-default) character encoding, such as UTF-8.

```java
import java.io.StringReader;
import java.io.IOException;

public class ReaderDemo {
    public static void main(String[] args) throws IOException {
        Reader reader = new StringReader("Hello, chars!");

        int c;
        while ((c = reader.read()) != -1) {
            System.out.print((char) c);
        }
        System.out.println();
    }
}
```

`read()` returns the next character as an `int` (again using `-1` as the end-of-stream sentinel, for the same reason `InputStream.read()` does), which must be cast back to `char` to use as text — this mirrors byte streams' `read()` pattern exactly, just one abstraction level higher.

## 2. Why & when

`Reader`/`Writer` exist because text is not simply "a sequence of bytes" — the same character can be represented by a different number of bytes depending on the encoding (UTF-8 encodes ASCII characters as one byte but many other characters as two, three, or four bytes). Working with text at the byte level means constantly reasoning about encoding; `Reader`/`Writer` abstract that away.

- **Correct encoding handling** — `InputStreamReader`/`OutputStreamWriter` bridge byte streams to character streams using an explicit (or platform-default) `Charset`, so multi-byte characters are decoded/encoded correctly rather than corrupted.
- **Natural text operations** — reading line by line (`BufferedReader.readLine()`), reading whole files as strings, and writing formatted text are all built on the `Reader`/`Writer` hierarchy.
- **Encoding portability** — code that explicitly specifies `UTF-8` (rather than relying on the platform default, which varies by OS and locale) behaves identically everywhere it runs.

Use `Reader`/`Writer` (and their subclasses like `BufferedReader`, `FileReader`, `PrintWriter`) whenever you're working with text; use raw `InputStream`/`OutputStream` for binary data where character-encoding concepts don't apply.

## 3. Core concept

```java
import java.io.StringReader;
import java.io.StringWriter;
import java.io.IOException;

public class ReaderCore {
    public static void main(String[] args) throws IOException {
        Reader reader = new StringReader("abc");
        Writer writer = new StringWriter();

        char[] buffer = new char[2];
        int charsRead;
        while ((charsRead = reader.read(buffer)) != -1) {
            writer.write(buffer, 0, charsRead);
        }

        System.out.println(writer.toString());
    }
}
```

`read(char[])` fills the character buffer and returns how many characters were actually placed there — exactly the same buffered-copy pattern used for byte streams, but operating on `char[]` instead of `byte[]`, which is the essential difference between the two hierarchies.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A byte stream is decoded through a character set into a Reader, and a Writer is encoded through a character set into a byte stream">
  <rect x="8" y="8" width="604" height="154" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="57" fill="#e6edf3" font-size="10" text-anchor="middle">InputStream (bytes)</text>
  <line x1="152" y1="52" x2="230" y2="52" stroke="#3fb950" stroke-width="2" marker-end="url(#r1)"/>
  <text x="190" y="42" fill="#3fb950" font-size="9" text-anchor="middle">decode (UTF-8)</text>
  <rect x="235" y="30" width="130" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="300" y="57" fill="#e6edf3" font-size="10" text-anchor="middle">Reader (chars)</text>

  <rect x="20" y="100" width="130" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="127" fill="#e6edf3" font-size="10" text-anchor="middle">Writer (chars)</text>
  <line x1="152" y1="122" x2="230" y2="122" stroke="#79c0ff" stroke-width="2" marker-end="url(#r2)"/>
  <text x="190" y="112" fill="#79c0ff" font-size="9" text-anchor="middle">encode (UTF-8)</text>
  <rect x="235" y="100" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="300" y="127" fill="#e6edf3" font-size="10" text-anchor="middle">OutputStream (bytes)</text>
  <defs>
    <marker id="r1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="r2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Character streams are byte streams plus an explicit encoding step in each direction.

## 5. Runnable example

Scenario: reading and writing a small text file, evolved from a basic character-by-character copy into a line-based copy, then into an explicit-encoding version that correctly handles non-ASCII text.

### Level 1 — Basic

```java
import java.io.StringReader;
import java.io.StringWriter;
import java.io.IOException;

public class ReaderBasic {
    public static void main(String[] args) throws IOException {
        Reader reader = new StringReader("Plain text.");
        Writer writer = new StringWriter();

        int c;
        while ((c = reader.read()) != -1) {
            writer.write(c);
        }

        System.out.println(writer.toString());
    }
}
```

**How to run:** `java ReaderBasic.java`

Copies one character at a time from an in-memory `Reader` to an in-memory `Writer` — the character-stream equivalent of the byte-by-byte copy seen with `InputStream`/`OutputStream`.

### Level 2 — Intermediate

Same idea, now reading actual text line by line with `BufferedReader`, which is how most real text-processing code reads files.

```java
import java.io.BufferedReader;
import java.io.StringReader;
import java.io.IOException;

public class ReaderIntermediate {
    public static void main(String[] args) throws IOException {
        String text = "line one\nline two\nline three";
        BufferedReader reader = new BufferedReader(new StringReader(text));

        String line;
        int lineNumber = 1;
        while ((line = reader.readLine()) != null) {
            System.out.println(lineNumber + ": " + line);
            lineNumber++;
        }
    }
}
```

**How to run:** `java ReaderIntermediate.java`

`BufferedReader` wraps a plain `Reader` and adds `readLine()`, which reads characters internally until it finds a line terminator and returns everything before it (without the terminator itself) as a `String` — `readLine()` returns `null` (not `-1`) at end-of-stream, since it deals in `String`, not `char`.

### Level 3 — Advanced

Same file-processing idea, now with real files and an explicit UTF-8 encoding specified on both the reading and writing side, so text containing non-ASCII characters (like accented letters) round-trips correctly regardless of the platform's default encoding.

```java
import java.io.*;
import java.nio.charset.StandardCharsets;

public class ReaderAdvanced {
    public static void main(String[] args) throws IOException {
        File file = new File("notes.txt");
        String original = "Café résumé — naïve\nSecond line.";

        try (Writer writer = new OutputStreamWriter(new FileOutputStream(file), StandardCharsets.UTF_8)) {
            writer.write(original);
        }

        StringBuilder rebuilt = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (rebuilt.length() > 0) rebuilt.append("\n");
                rebuilt.append(line);
            }
        }

        System.out.println("Round-trip successful: " + original.equals(rebuilt.toString()));
        System.out.println(rebuilt);
    }
}
```

**How to run:** `java ReaderAdvanced.java` (creates `notes.txt` in the current directory)

`OutputStreamWriter(..., StandardCharsets.UTF_8)` explicitly encodes every character (including the accented `é`, `à`, `ï`, and the em dash `—`) as UTF-8 bytes on write, and `InputStreamReader(..., StandardCharsets.UTF_8)` explicitly decodes those same bytes back to the identical characters on read — specifying the charset on **both** ends guarantees correctness regardless of what the JVM's platform-default encoding happens to be, which can otherwise vary between operating systems and locales.

## 6. Walkthrough

Trace `ReaderAdvanced.main` step by step.

**Writing.** `original` contains multi-byte characters (`é`, `—`, etc.) alongside plain ASCII. `new OutputStreamWriter(new FileOutputStream(file), StandardCharsets.UTF_8)` creates a `Writer` that, for every character passed to `write`, encodes it as one or more UTF-8 bytes and passes those bytes down to the underlying `FileOutputStream` — an ASCII character like `C` becomes one byte, while `é` becomes two bytes. `writer.write(original)` triggers this encoding for the entire string in one call. The try-with-resources block closes the writer, flushing any buffered bytes to `notes.txt` on disk.

**Reading.** `new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8)` creates a `Reader` that does the reverse: it reads raw bytes from the file and decodes them back into `char` values according to UTF-8's rules — correctly recognizing that certain byte sequences represent a single multi-byte character rather than two separate ASCII characters. Wrapping this in `BufferedReader` adds `readLine()`.

**Line-by-line reconstruction.** The first `readLine()` call returns `"Café résumé — naïve"` (everything up to, but not including, the `\n`). `rebuilt` is currently empty, so the `if` check fails and the line is simply appended. The second `readLine()` call returns `"Second line."`; this time `rebuilt.length() > 0` is `true`, so a `\n` is appended first (restoring the line break that `readLine()` had stripped out), followed by the line itself. The third `readLine()` call returns `null` (end of file), ending the loop.

**Verification.** `rebuilt.toString()` now reads `"Café résumé — naïve\nSecond line."` — character-for-character identical to `original`, including every accented letter and the em dash — so `original.equals(rebuilt.toString())` is `true`.

```
original:  "Café résumé — naïve\nSecond line."
             |
             v  encode as UTF-8 (multi-byte for é, é, —, ï)
notes.txt (bytes on disk, UTF-8 encoded)
             |
             v  decode as UTF-8 (reconstructs the same characters)
rebuilt:   "Café résumé — naïve\nSecond line."   <- identical to original
```

**Output:**
```
Round-trip successful: true
Café résumé — naïve
Second line.
```

## 7. Gotchas & takeaways

> Constructing `FileReader`/`FileWriter` (or `InputStreamReader`/`OutputStreamWriter`) **without** specifying a `Charset` uses the JVM's *platform default* encoding — which can differ between your development machine, a colleague's machine, and a production server. This has caused countless "works on my machine" text-corruption bugs. Always specify `StandardCharsets.UTF_8` (or another explicit charset) unless you have a specific, well-understood reason not to.

> `readLine()` strips the line terminator and returns `null` at end-of-stream — mixing this up with `read()`'s `-1` sentinel (used for single characters) is an easy off-by-one-style mistake when switching between the two methods.

- `Reader`/`Writer` are the character-stream counterparts of `InputStream`/`OutputStream`, operating in `char` rather than raw bytes.
- `InputStreamReader`/`OutputStreamWriter` bridge the byte and character worlds, applying a `Charset` in each direction.
- Always specify an explicit charset (typically `StandardCharsets.UTF_8`) rather than relying on the platform default, for portable, correct text handling.
- `BufferedReader.readLine()` returns `null` at end-of-stream (not `-1`, which is for single-character `read()`), and strips the line terminator from each returned line.
