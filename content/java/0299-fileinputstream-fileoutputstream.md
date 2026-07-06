---
card: java
gi: 299
slug: fileinputstream-fileoutputstream
title: FileInputStream / FileOutputStream
---

## 1. What it is

`FileInputStream` and `FileOutputStream` are concrete `InputStream`/`OutputStream` subclasses that read from and write to files on disk as raw bytes. `FileInputStream` opens an existing file for reading; `FileOutputStream` opens (creating if necessary, and by default truncating) a file for writing.

```java
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public class FileStreamDemo {
    public static void main(String[] args) throws IOException {
        try (FileOutputStream out = new FileOutputStream("greeting.txt")) {
            out.write("Hello, file!".getBytes());
        }

        try (FileInputStream in = new FileInputStream("greeting.txt")) {
            byte[] buffer = new byte[100];
            int bytesRead = in.read(buffer);
            System.out.println(new String(buffer, 0, bytesRead));
        }
    }
}
```

`new FileOutputStream("greeting.txt")` creates the file if it doesn't exist (or truncates it to empty if it does) and opens it for writing; `new FileInputStream("greeting.txt")` opens the existing file for reading, throwing `FileNotFoundException` if it doesn't exist.

## 2. Why & when

`FileInputStream`/`FileOutputStream` provide the most direct route from "bytes in a program" to "bytes in a file on disk," making them the foundation for any file-based persistence: saving binary data, reading configuration or resource files, and building higher-level readers/writers on top.

- **Direct file access** — the simplest way to read or write a file's raw bytes, with no buffering, encoding conversion, or formatting layered on top.
- **Building block for higher-level streams** — `BufferedInputStream`, `DataInputStream`, `ObjectInputStream`, and character-stream classes like `InputStreamReader` all commonly wrap a `FileInputStream` to add functionality.
- **Binary file handling** — images, serialized objects, and any file whose content is not meant to be interpreted as text.

For text files, wrap these in `InputStreamReader`/`OutputStreamWriter` with an explicit charset (or use `Files.readString`/`Files.writeString` from `java.nio.file` for simple whole-file text operations) rather than working with raw bytes directly. For performance on many small reads/writes, wrap in `BufferedInputStream`/`BufferedOutputStream` — unbuffered file I/O makes one system call per `read`/`write`, which is slow when called repeatedly with small amounts of data.

## 3. Core concept

```java
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.IOException;

public class FileStreamCore {
    public static void main(String[] args) throws IOException {
        try (FileOutputStream out = new FileOutputStream("data.bin", true)) { // append mode
            out.write(new byte[]{1, 2, 3});
        }
        try (FileOutputStream out = new FileOutputStream("data.bin", true)) { // append again
            out.write(new byte[]{4, 5, 6});
        }

        try (FileInputStream in = new FileInputStream("data.bin")) {
            System.out.println(java.util.Arrays.toString(in.readAllBytes()));
        }
    }
}
```

`new FileOutputStream("data.bin", true)` opens the file in **append** mode — the second `true` argument means existing content is preserved and new writes are added at the end, rather than the default behavior of truncating the file to empty on open; running this twice results in all six bytes present, not just the last three.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FileOutputStream in default mode truncates the file before writing, in append mode it writes after existing content">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="250" height="90" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="52" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">new FileOutputStream(f)</text>
  <text x="155" y="72" fill="#8b949e" font-size="9" text-anchor="middle">default: truncate to empty</text>
  <text x="155" y="90" fill="#8b949e" font-size="9" text-anchor="middle">old content is LOST</text>

  <rect x="320" y="30" width="250" height="90" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="445" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">new FileOutputStream(f, true)</text>
  <text x="445" y="72" fill="#8b949e" font-size="9" text-anchor="middle">append mode</text>
  <text x="445" y="90" fill="#8b949e" font-size="9" text-anchor="middle">old content preserved, new bytes added after</text>
</svg>

The boolean append flag is the single most consequential argument to `FileOutputStream`'s constructor.

## 5. Runnable example

Scenario: a simple append-only event log written to a file, evolved from a basic single-write into a multi-write append log, then into a version that safely handles the case where the log file doesn't exist yet and reports its total size.

### Level 1 — Basic

```java
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.IOException;

public class FileStreamBasic {
    public static void main(String[] args) throws IOException {
        try (FileOutputStream out = new FileOutputStream("events.log")) {
            out.write("Event: startup\n".getBytes());
        }

        try (FileInputStream in = new FileInputStream("events.log")) {
            System.out.print(new String(in.readAllBytes()));
        }
    }
}
```

**How to run:** `java FileStreamBasic.java`

Writes one line to `events.log` (truncating any previous content, since no append flag is given) and reads it straight back.

### Level 2 — Intermediate

Same log file, now with multiple events appended across separate `FileOutputStream` instances, showing that append mode preserves everything written in earlier runs or earlier blocks.

```java
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.IOException;

public class FileStreamIntermediate {
    static void logEvent(String message) throws IOException {
        try (FileOutputStream out = new FileOutputStream("events.log", true)) { // append
            out.write((message + "\n").getBytes());
        }
    }

    public static void main(String[] args) throws IOException {
        try (FileOutputStream out = new FileOutputStream("events.log")) { /* truncate to start clean */ }

        logEvent("Event: startup");
        logEvent("Event: user logged in");
        logEvent("Event: shutdown");

        try (FileInputStream in = new FileInputStream("events.log")) {
            System.out.print(new String(in.readAllBytes()));
        }
    }
}
```

**How to run:** `java FileStreamIntermediate.java`

Each `logEvent` call opens, appends one line, and closes the file independently — this mirrors how a real logging function would be called repeatedly over the life of an application, opening and closing the file handle each time rather than holding it open indefinitely.

### Level 3 — Advanced

Same event log, now as a small reusable logger that reports the file's total size after each write and gracefully handles the very first call, when the log file doesn't exist yet.

```java
import java.io.*;

public class FileStreamAdvanced {
    static long logEvent(String logPath, String message) throws IOException {
        File file = new File(logPath);
        try (FileOutputStream out = new FileOutputStream(file, true)) { // creates the file if absent
            out.write((message + "\n").getBytes());
        }
        return file.length(); // total size after this write
    }

    public static void main(String[] args) throws IOException {
        String logPath = "app-events.log";
        new File(logPath).delete(); // start with a clean slate for this demo

        String[] events = {"startup", "config loaded", "ready"};
        for (String event : events) {
            long size = logEvent(logPath, "Event: " + event);
            System.out.println("Logged \"" + event + "\" -- file is now " + size + " bytes");
        }

        try (FileInputStream in = new FileInputStream(logPath)) {
            System.out.print("\nFull log:\n" + new String(in.readAllBytes()));
        }
    }
}
```

**How to run:** `java FileStreamAdvanced.java`

`new FileOutputStream(file, true)` in append mode creates the file automatically on its very first call if it doesn't already exist (append mode doesn't require the file to be pre-created) — so `logEvent` works correctly whether `app-events.log` is missing, empty, or already has prior entries, and `file.length()` (a `File` method that queries the filesystem) reports the cumulative size after each append.

## 6. Walkthrough

Trace `FileStreamAdvanced.main` step by step.

**Cleanup.** `new File(logPath).delete()` removes any leftover `app-events.log` from a previous run, so the demo starts from a guaranteed-absent file — `delete()` returns `false` harmlessly if the file didn't exist, which is fine here since the return value isn't checked.

**First loop iteration, `event = "startup"`.** `logEvent(logPath, "Event: startup")` runs: `new File(logPath)` wraps the path (no filesystem interaction yet). `new FileOutputStream(file, true)` opens in append mode — since the file doesn't exist, it is created fresh, empty. `out.write("Event: startup\n".getBytes())` writes 15 bytes (`"Event: startup\n"` is 15 characters, all ASCII). The stream closes, flushing to disk. `file.length()` queries the filesystem and returns `15`. Printed as `Logged "startup" -- file is now 15 bytes`.

**Second iteration, `event = "config loaded"`.** `logEvent` opens the *now-existing* file in append mode — its existing 15 bytes are preserved. `out.write("Event: config loaded\n".getBytes())` adds 22 more bytes at the end. `file.length()` now returns `37` (`15 + 22`). Printed as `Logged "config loaded" -- file is now 37 bytes`.

**Third iteration, `event = "ready"`.** Same pattern: appends `"Event: ready\n"` (13 bytes) after the existing 37, bringing the total to `50`. Printed as `Logged "ready" -- file is now 50 bytes`.

**Final read.** `new FileInputStream(logPath)` opens the completed file from the beginning; `readAllBytes()` reads the entire 50 bytes in one call, and wrapping in `new String(...)` renders it as the three log lines, one after another, in the exact order they were appended.

```
delete() -- ensure clean start

logEvent("startup")        -> create file, write 15 bytes -> size = 15
logEvent("config loaded")  -> append 22 bytes              -> size = 37
logEvent("ready")          -> append 13 bytes               -> size = 50

readAllBytes() -> all 50 bytes, in append order
```

**Output:**
```
Logged "startup" -- file is now 15 bytes
Logged "config loaded" -- file is now 37 bytes
Logged "ready" -- file is now 50 bytes

Full log:
Event: startup
Event: config loaded
Event: ready
```

## 7. Gotchas & takeaways

> `new FileOutputStream(path)` (without the boolean append argument, or with it explicitly `false`) **truncates the file to zero length immediately upon opening** — even before any `write` call happens. Opening a file this way "just to check something" and then deciding not to write anything still destroys its previous contents. Always use the two-argument constructor with `true` when appending is intended.

> `FileInputStream`/`FileOutputStream` perform **unbuffered** I/O — each `read`/`write` call typically triggers a system call. Calling `write` or `read` many times with small amounts of data (as opposed to using a buffer or wrapping in `BufferedInputStream`/`BufferedOutputStream`) is measurably slower than it needs to be for anything beyond trivial file sizes.

- `FileInputStream` reads an existing file's bytes; `FileOutputStream` writes bytes to a file, truncating by default or appending when constructed with `true`.
- Always use try-with-resources so the underlying file handle is released even if an exception occurs mid-operation.
- The append-mode constructor creates the file if it doesn't already exist — no separate "create" step is needed.
- Wrap in `BufferedInputStream`/`BufferedOutputStream` for performance when doing many small reads or writes; use `Files.readAllBytes`/`Files.write` from `java.nio.file` for simple whole-file operations.
