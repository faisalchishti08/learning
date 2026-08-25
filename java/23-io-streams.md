# Java I/O Streams

## Overview

Java I/O is built on stream abstractions — pipes that move bytes or characters sequentially. Two hierarchies: **byte streams** (`InputStream`/`OutputStream`) and **character streams** (`Reader`/`Writer`). Decorators (wrappers) add buffering, compression, encoding, etc.

---

## 1. Stream Hierarchy

### Visual Diagram

```
Byte Streams:
InputStream (abstract)
├── FileInputStream          reads bytes from file
├── ByteArrayInputStream     reads bytes from byte[]
├── PipedInputStream         reads from connected PipedOutputStream
└── FilterInputStream (abstract)
    ├── BufferedInputStream  adds buffering (default 8KB)
    ├── DataInputStream      reads primitives (readInt, readDouble...)
    └── ObjectInputStream    deserializes objects

OutputStream (abstract)
├── FileOutputStream         writes bytes to file
├── ByteArrayOutputStream    writes bytes to growing byte[]
├── PipedOutputStream        writes to connected PipedInputStream
└── FilterOutputStream (abstract)
    ├── BufferedOutputStream adds buffering
    ├── DataOutputStream     writes primitives
    └── ObjectOutputStream   serializes objects

Character Streams (auto handles charset encoding):
Reader (abstract)
├── FileReader               reads chars from file (default charset)
├── StringReader             reads chars from String
├── InputStreamReader        bridges byte→char (with charset)
└── BufferedReader           buffered + readLine()

Writer (abstract)
├── FileWriter               writes chars to file
├── StringWriter             writes chars to StringBuffer
├── OutputStreamWriter       bridges char→byte (with charset)
├── BufferedWriter           buffered + newLine()
└── PrintWriter              printf/println convenience

Decorator pattern:
  new BufferedReader(new FileReader("file.txt"))
  new BufferedInputStream(new FileInputStream("file.bin"))
```

---

## 2. File I/O — Basic Reading and Writing

### Example 1 — Reading Files (All Modern Ways)

```java
import java.io.*;
import java.nio.file.*;
import java.nio.charset.*;

public class FileReading {
    public static void main(String[] args) throws Exception {
        String path = "/tmp/test.txt";
        Files.writeString(Path.of(path), "line1\nline2\nline3");

        // Method 1: BufferedReader (classic, efficient for large files)
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = br.readLine()) != null) {
                System.out.println("BR: " + line);
            }
        }

        // Method 2: Files.readAllLines [Java 7] — all lines as List
        java.util.List<String> lines = Files.readAllLines(Path.of(path), StandardCharsets.UTF_8);
        System.out.println("All lines: " + lines);

        // Method 3: Files.readString [Java 11] — whole file as String
        String content = Files.readString(Path.of(path), StandardCharsets.UTF_8);
        System.out.println("Content: " + content);

        // Method 4: Files.lines [Java 8] — lazy stream (memory-efficient)
        try (var stream = Files.lines(Path.of(path), StandardCharsets.UTF_8)) {
            stream.filter(l -> l.contains("2"))
                  .forEach(System.out::println); // line2
        }
    }
}
```

**What this does:** Four approaches for different needs. `BufferedReader.readLine()` is the classic. `Files.readString` is cleanest for small files. `Files.lines()` is memory-efficient for huge files — streams lazily.

### Example 2 — Writing Files

```java
import java.io.*;
import java.nio.file.*;
import java.nio.charset.*;

public class FileWriting {
    public static void main(String[] args) throws Exception {
        String path = "/tmp/output.txt";

        // Method 1: BufferedWriter (classic)
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(path))) {
            bw.write("line 1");
            bw.newLine(); // platform-independent newline
            bw.write("line 2");
        }

        // Method 2: PrintWriter — printf/println convenience
        try (PrintWriter pw = new PrintWriter(new BufferedWriter(new FileWriter(path, true)))) {
            pw.println("line 3");
            pw.printf("value: %d%n", 42);
        }

        // Method 3: Files.writeString [Java 11] — cleanest for small content
        Files.writeString(Path.of(path), "new content", StandardCharsets.UTF_8,
            StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);

        // Method 4: Files.write — byte array or lines
        Files.write(Path.of(path), java.util.List.of("a", "b", "c"),
            StandardCharsets.UTF_8);

        System.out.println(Files.readString(Path.of(path)));
    }
}
```

**What this does:** Always buffer writes — `FileWriter` alone does unbuffered char I/O (slow). `PrintWriter` wraps `BufferedWriter` which wraps `FileWriter`. `Files.write/writeString` handle open/close automatically.

> ⚠️ **Pitfall:** `new FileWriter(path)` truncates existing file by default. Use `new FileWriter(path, true)` to append.

---

## 3. Byte Streams — Binary I/O

### Example 1 — DataInputStream/DataOutputStream

```java
import java.io.*;

public class BinaryIO {
    public static void main(String[] args) throws Exception {
        String path = "/tmp/data.bin";

        // Write primitives in binary
        try (DataOutputStream dos = new DataOutputStream(
                new BufferedOutputStream(new FileOutputStream(path)))) {
            dos.writeInt(42);
            dos.writeDouble(3.14);
            dos.writeUTF("hello");    // length-prefixed UTF-8
            dos.writeBoolean(true);
        }

        // Read back in SAME ORDER
        try (DataInputStream dis = new DataInputStream(
                new BufferedInputStream(new FileInputStream(path)))) {
            int i       = dis.readInt();
            double d    = dis.readDouble();
            String s    = dis.readUTF();
            boolean b   = dis.readBoolean();
            System.out.printf("int=%d, double=%.2f, str=%s, bool=%b%n", i, d, s, b);
            // int=42, double=3.14, str=hello, bool=true
        }
    }
}
```

**What this does:** `DataOutputStream` writes typed primitives as raw bytes. Must read in the same order with `DataInputStream`. `writeUTF` stores the length first — always paired with `readUTF`.

### Example 2 — ByteArrayOutputStream (in-memory buffer)

```java
import java.io.*;

public class InMemoryBuffer {
    public static void main(String[] args) throws Exception {
        // Write to in-memory byte array
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (DataOutputStream dos = new DataOutputStream(baos)) {
            dos.writeInt(1);
            dos.writeInt(2);
            dos.writeInt(3);
        }

        byte[] bytes = baos.toByteArray(); // [0,0,0,1, 0,0,0,2, 0,0,0,3]
        System.out.println("Bytes: " + bytes.length); // 12

        // Read back from same byte array
        try (DataInputStream dis = new DataInputStream(new ByteArrayInputStream(bytes))) {
            System.out.println(dis.readInt()); // 1
            System.out.println(dis.readInt()); // 2
            System.out.println(dis.readInt()); // 3
        }
    }
}
```

**What this does:** `ByteArrayOutputStream` builds bytes in memory — useful for building binary payloads before sending over network or comparing in tests.

---

## 4. Reader/Writer — Character Streams

### Example 1 — StringWriter (in-memory String building)

```java
import java.io.*;

public class StringWriterDemo {
    public static void main(String[] args) throws Exception {
        StringWriter sw = new StringWriter();
        PrintWriter pw = new PrintWriter(sw);
        pw.printf("Name: %s%n", "Alice");
        pw.printf("Age: %d%n", 30);
        pw.flush();
        System.out.println(sw.toString());
        // Name: Alice
        // Age: 30

        // StringReader — read from String
        StringReader sr = new StringReader("Hello World");
        BufferedReader br = new BufferedReader(sr);
        System.out.println(br.readLine()); // Hello World
    }
}
```

### Example 2 — InputStreamReader (charset bridge)

```java
import java.io.*;
import java.nio.charset.*;

public class CharsetBridge {
    public static void main(String[] args) throws Exception {
        // Reading a UTF-8 file explicitly
        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(
                    new FileInputStream("/tmp/test.txt"), StandardCharsets.UTF_8))) {
            br.lines().forEach(System.out::println);
        }

        // Writing UTF-8 explicitly
        try (BufferedWriter bw = new BufferedWriter(
                new OutputStreamWriter(
                    new FileOutputStream("/tmp/out.txt"), StandardCharsets.UTF_8))) {
            bw.write("こんにちは"); // Japanese characters
        }

        // Verify
        System.out.println(
            java.nio.file.Files.readString(java.nio.file.Path.of("/tmp/out.txt"),
                StandardCharsets.UTF_8)
        );
    }
}
```

**What this does:** `InputStreamReader` bridges byte stream → character stream with explicit charset. Always specify charset explicitly — default charset is platform-dependent and causes bugs when moving between systems.

---

## 5. try-with-resources [Java 7+]

### Example 1 — Proper Resource Handling

```java
import java.io.*;

public class TryWithResources {
    public static void main(String[] args) {
        // Pre-Java 7: manual close in finally (error-prone)
        BufferedReader brOld = null;
        try {
            brOld = new BufferedReader(new FileReader("/tmp/test.txt"));
            System.out.println(brOld.readLine());
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            if (brOld != null) {
                try { brOld.close(); } catch (IOException e) { e.printStackTrace(); }
            }
        }

        // Java 7+: try-with-resources — auto-closes in declaration order (reverse)
        try (BufferedReader br = new BufferedReader(new FileReader("/tmp/test.txt"))) {
            System.out.println(br.readLine());
        } catch (IOException e) {
            e.printStackTrace();
        }

        // Multiple resources — closed in REVERSE order
        try (FileInputStream  fis = new FileInputStream("/tmp/test.txt");
             BufferedInputStream bis = new BufferedInputStream(fis)) {
            System.out.println(bis.read()); // first byte
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
```

**What this does:** Any class implementing `AutoCloseable` works with try-with-resources. Resources declared in the `try(...)` are closed automatically — `bis` closes first, then `fis`. Even if an exception occurs, close is called.

### Dry Run — Close Order

```
try (A a = new A(); B b = new B()) { ... }

Declaration order:  A → B
Close order:        B.close() first, then A.close()

If exception in body:
  1. body throws ex
  2. B.close() called (may throw suppressed ex)
  3. A.close() called (may throw suppressed ex)
  4. original ex propagates (suppressed exes attached to it)
```

---

## 6. BufferedInputStream vs FileInputStream

### Visual Diagram — Buffering Impact

```
Without buffering (FileInputStream):
  read() → syscall → OS → 1 byte
  read() → syscall → OS → 1 byte
  read() → syscall → OS → 1 byte
  1000 reads = 1000 syscalls (SLOW)

With buffering (BufferedInputStream, 8192 bytes default):
  read() → syscall → OS → 8192 bytes (fill buffer)
  read() → buffer[1]   (no syscall!)
  read() → buffer[2]   (no syscall!)
  ...
  8192 reads = 1 syscall (FAST)
```

### Example 1 — Buffering Matters

```java
import java.io.*;
import java.nio.file.*;

public class BufferingPerf {
    public static void main(String[] args) throws Exception {
        // Create 10MB file
        byte[] data = new byte[10_000_000];
        Files.write(Path.of("/tmp/big.bin"), data);

        // Without buffering — slow
        long start = System.currentTimeMillis();
        try (FileInputStream fis = new FileInputStream("/tmp/big.bin")) {
            while (fis.read() != -1) {} // byte by byte
        }
        System.out.println("Unbuffered: " + (System.currentTimeMillis() - start) + "ms");

        // With buffering — fast
        start = System.currentTimeMillis();
        try (BufferedInputStream bis = new BufferedInputStream(
                new FileInputStream("/tmp/big.bin"))) {
            while (bis.read() != -1) {} // reads 8192 bytes per syscall
        }
        System.out.println("Buffered: " + (System.currentTimeMillis() - start) + "ms");
        // Buffered is typically 10-100x faster
    }
}
```

> ⚠️ **Pitfall:** Never read a file byte-by-byte without buffering. Always wrap `FileInputStream`/`FileOutputStream` with `Buffered*` variants unless using `read(byte[])` with your own buffer.

---

## Quick Reference

```
Reading text files:
  Files.readString(path)              [Java 11] whole file → String
  Files.readAllLines(path, charset)   [Java 7]  all lines → List<String>
  Files.lines(path)                   [Java 8]  lazy stream
  new BufferedReader(new FileReader(path)).readLine()  classic

Writing text files:
  Files.writeString(path, str)        [Java 11] simplest
  Files.write(path, lines, charset)   list of lines
  new PrintWriter(new BufferedWriter(new FileWriter(path))) classic

Binary:
  DataOutputStream/DataInputStream    typed primitives
  BufferedOutputStream/InputStream    wrap FileStream for performance
  ByteArrayOutputStream               in-memory byte accumulator

Charset:
  InputStreamReader(stream, charset)  bridge byte→char
  OutputStreamWriter(stream, charset) bridge char→byte
  Always use StandardCharsets.UTF_8   never rely on default

Resource management:
  try (Resource r = ...) {}           auto-close [Java 7+]
  Closed in reverse declaration order
```
