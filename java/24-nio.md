# Java NIO (New I/O)

## Overview

NIO (`java.nio`) introduced in Java 1.4 provides buffer-oriented, non-blocking I/O. NIO.2 (Java 7) added the `Path`/`Files` API, watch service, and async I/O. Key concepts: **Buffers**, **Channels**, **Selectors**, **Path/Files**.

---

## 1. Path and Files API [Java 7+]

### What is it

`Path` replaces `java.io.File`. `Files` provides factory methods for reading, writing, walking, copying, watching. More powerful and more expressive than the old `File` API.

### Visual Diagram

```
Path:
  Path.of("/home/user/docs/report.txt")
       └── absolute path: /home/user/docs/report.txt
  
  path.getFileName()    → report.txt
  path.getParent()      → /home/user/docs
  path.getRoot()        → /
  path.getNameCount()   → 4
  path.getName(0)       → home
  
  Relative: Path.of("docs/report.txt")
  Resolve:  Path.of("/home/user").resolve("docs/report.txt")
          → /home/user/docs/report.txt
  
  Normalize: Path.of("/a/b/../c").normalize() → /a/c
  Relativize: /home/user.relativize(/home/user/docs) → docs
```

### Example 1 — Path Operations

```java
import java.nio.file.*;

public class PathDemo {
    public static void main(String[] args) {
        Path p = Path.of("/home/user/docs/report.txt");

        System.out.println(p.getFileName());  // report.txt
        System.out.println(p.getParent());    // /home/user/docs
        System.out.println(p.getRoot());      // /
        System.out.println(p.getNameCount()); // 4

        // Build paths
        Path dir  = Path.of("/home/user");
        Path file = dir.resolve("docs/report.txt"); // /home/user/docs/report.txt
        System.out.println(file);

        // Relative paths
        Path from = Path.of("/home/user");
        Path to   = Path.of("/home/user/docs/report.txt");
        System.out.println(from.relativize(to)); // docs/report.txt

        // Normalize — remove .. and .
        Path messy = Path.of("/home/user/../user/./docs");
        System.out.println(messy.normalize()); // /home/user/docs

        // Check existence
        System.out.println(Files.exists(p));      // true/false
        System.out.println(Files.isDirectory(p)); // false
        System.out.println(Files.isReadable(p));  // true/false

        // Convert to/from old File API
        java.io.File f = p.toFile();
        Path backToPath = f.toPath();
    }
}
```

**What this does:** `Path` is immutable and represents a path string with structure. `resolve()` joins paths cleanly. `relativize()` computes relative path between two absolutes.

### Example 2 — Files Operations

```java
import java.nio.file.*;
import java.nio.charset.*;
import java.io.IOException;

public class FilesAPI {
    public static void main(String[] args) throws Exception {
        Path dir = Path.of("/tmp/nio-demo");

        // Create directories
        Files.createDirectories(dir); // creates all missing ancestors

        Path file = dir.resolve("test.txt");

        // Write
        Files.writeString(file, "Hello NIO", StandardCharsets.UTF_8);

        // Read
        System.out.println(Files.readString(file)); // Hello NIO

        // Append
        Files.writeString(file, "\nAppended", StandardCharsets.UTF_8,
            StandardOpenOption.APPEND);

        // Copy
        Path copy = dir.resolve("copy.txt");
        Files.copy(file, copy, StandardCopyOption.REPLACE_EXISTING);

        // Move/rename
        Path moved = dir.resolve("renamed.txt");
        Files.move(copy, moved, StandardCopyOption.REPLACE_EXISTING);

        // Get metadata
        System.out.println(Files.size(file));                          // bytes
        System.out.println(Files.getLastModifiedTime(file));          // timestamp
        System.out.println(Files.getAttribute(file, "basic:size"));  // attribute

        // Delete
        Files.delete(moved);
        Files.deleteIfExists(Path.of("/tmp/nonexistent")); // no exception if missing
    }
}
```

**What this does:** `Files` static methods handle the common file operations. `createDirectories` creates the full chain — unlike `mkdir()` which fails if parent doesn't exist. Always use `StandardCopyOption.REPLACE_EXISTING` explicitly.

---

## 2. Walking and Directory Traversal

### Example 1 — Files.walk and Files.find

```java
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.stream.*;
import java.io.IOException;

public class DirectoryWalking {
    public static void main(String[] args) throws Exception {
        // Setup
        Path root = Path.of("/tmp/walk-demo");
        Files.createDirectories(root.resolve("a/b"));
        Files.createDirectories(root.resolve("a/c"));
        Files.writeString(root.resolve("a/b/x.txt"), "x");
        Files.writeString(root.resolve("a/b/y.java"), "y");
        Files.writeString(root.resolve("a/c/z.txt"), "z");

        // walk — stream all paths (BFS/DFS)
        System.out.println("All paths:");
        try (Stream<Path> paths = Files.walk(root)) {
            paths.forEach(System.out::println);
        }

        // walk with depth limit
        System.out.println("\nDepth 1 only:");
        try (Stream<Path> paths = Files.walk(root, 1)) {
            paths.forEach(System.out::println);
        }

        // find — walk + filter by attribute
        System.out.println("\n.txt files:");
        try (Stream<Path> txts = Files.find(root, Integer.MAX_VALUE,
                (path, attrs) -> attrs.isRegularFile() && path.toString().endsWith(".txt"))) {
            txts.forEach(System.out::println);
        }

        // list — direct children only (like ls)
        System.out.println("\nDirect children:");
        try (Stream<Path> children = Files.list(root)) {
            children.forEach(System.out::println);
        }
    }
}
```

**What this does:** `Files.walk()` produces a lazy depth-first stream. `Files.find()` combines walking with an attribute-based filter — efficient for finding files by type, size, or modification time. Always use try-with-resources — the stream holds an open directory handle.

---

## 3. WatchService — File Change Notifications

### Example 1 — Monitor Directory for Changes

```java
import java.nio.file.*;

public class WatchServiceDemo {
    public static void main(String[] args) throws Exception {
        Path dir = Path.of("/tmp/watch-demo");
        Files.createDirectories(dir);

        WatchService watcher = FileSystems.getDefault().newWatchService();

        // Register for create, modify, delete events
        dir.register(watcher,
            StandardWatchEventKinds.ENTRY_CREATE,
            StandardWatchEventKinds.ENTRY_MODIFY,
            StandardWatchEventKinds.ENTRY_DELETE);

        System.out.println("Watching: " + dir);

        // Simulate changes in another thread
        new Thread(() -> {
            try {
                Thread.sleep(100);
                Files.writeString(dir.resolve("new.txt"), "created");
                Thread.sleep(100);
                Files.writeString(dir.resolve("new.txt"), "modified",
                    StandardOpenOption.APPEND);
                Thread.sleep(100);
                Files.delete(dir.resolve("new.txt"));
            } catch (Exception e) { e.printStackTrace(); }
        }).start();

        // Watch loop — poll for events
        for (int i = 0; i < 3; i++) {
            WatchKey key = watcher.take(); // blocks until event
            for (WatchEvent<?> event : key.pollEvents()) {
                System.out.printf("Event: %s on %s%n",
                    event.kind().name(), event.context());
            }
            key.reset(); // MUST reset to receive more events
        }

        watcher.close();
    }
}
```

**What this does:** `WatchService` delivers OS-native file system events. Critical: always call `key.reset()` after processing events — without it, the key becomes invalid and no further events arrive.

> ⚠️ **Pitfall:** `WatchService` may deliver `OVERFLOW` events if events arrive faster than they're consumed. Always handle `StandardWatchEventKinds.OVERFLOW`.

---

## 4. Buffers and Channels

### What is it

NIO channels transfer data into/out of `Buffer` objects. Buffers are typed byte containers with `position`, `limit`, `capacity`. The read→flip→write cycle is fundamental.

### Visual Diagram — Buffer State Machine

```
Buffer lifecycle:

1. allocate(8):
   [_, _, _, _, _, _, _, _]
    position=0, limit=8, capacity=8

2. put("ABC"):
   [A, B, C, _, _, _, _, _]
    position=3, limit=8

3. flip() — switch to read mode:
   [A, B, C, _, _, _, _, _]
    position=0, limit=3  ← limit = old position

4. get() × 3 reads A, B, C:
   [A, B, C, _, _, _, _, _]
    position=3, limit=3  ← position = limit means exhausted

5. clear() — reset for writing:
   position=0, limit=8

Key methods:
  flip()    write→read mode  (position=0, limit=old position)
  clear()   reset            (position=0, limit=capacity)
  rewind()  re-read          (position=0, limit unchanged)
  remaining() = limit - position
```

### Example 1 — ByteBuffer

```java
import java.nio.*;

public class ByteBufferDemo {
    public static void main(String[] args) {
        // Allocate
        ByteBuffer buf = ByteBuffer.allocate(16);
        System.out.println("After allocate: pos=" + buf.position() + " lim=" + buf.limit());
        // pos=0 lim=16

        // Write (put)
        buf.put((byte) 'H');
        buf.put((byte) 'e');
        buf.put((byte) 'l');
        buf.put((byte) 'l');
        buf.put((byte) 'o');
        System.out.println("After writes: pos=" + buf.position() + " lim=" + buf.limit());
        // pos=5 lim=16

        // Flip — prepare to read
        buf.flip();
        System.out.println("After flip: pos=" + buf.position() + " lim=" + buf.limit());
        // pos=0 lim=5

        // Read (get)
        byte[] bytes = new byte[buf.remaining()];
        buf.get(bytes);
        System.out.println("Read: " + new String(bytes)); // Hello

        // Wrap existing array
        ByteBuffer wrapped = ByteBuffer.wrap(new byte[]{1, 2, 3, 4});
        System.out.println("Wrapped: " + wrapped.get()); // 1

        // Direct buffer — off-heap (faster for I/O, no GC)
        ByteBuffer direct = ByteBuffer.allocateDirect(1024);
        System.out.println("Is direct: " + direct.isDirect()); // true
    }
}
```

**What this does:** The put/flip/get cycle is the NIO Buffer contract. `flip()` is the most important — without it, you read garbage (reading unwritten positions). `allocateDirect()` allocates off-heap memory for zero-copy I/O with channels.

### Dry Run — put/flip/get

```
allocate(8): pos=0 lim=8
put('A'):    pos=1 lim=8   buf=[A,_,_,_,_,_,_,_]
put('B'):    pos=2 lim=8   buf=[A,B,_,_,_,_,_,_]
put('C'):    pos=3 lim=8   buf=[A,B,C,_,_,_,_,_]
flip():      pos=0 lim=3   ← limit becomes 3 (how many were written)
get():       returns 'A', pos=1
get():       returns 'B', pos=2
get():       returns 'C', pos=3
remaining(): 0 (done)
clear():     pos=0 lim=8   (ready to write again)
```

---

## 5. FileChannel — File I/O with Buffers

### Example 1 — Read and Write with FileChannel

```java
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;
import java.nio.charset.*;

public class FileChannelDemo {
    public static void main(String[] args) throws Exception {
        Path path = Path.of("/tmp/channel.txt");

        // Write with FileChannel
        try (FileChannel fc = FileChannel.open(path,
                StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            ByteBuffer buf = ByteBuffer.wrap("Hello NIO Channel".getBytes(StandardCharsets.UTF_8));
            fc.write(buf);
        }

        // Read with FileChannel
        try (FileChannel fc = FileChannel.open(path, StandardOpenOption.READ)) {
            ByteBuffer buf = ByteBuffer.allocate(1024);
            int bytesRead = fc.read(buf);
            buf.flip();
            String content = StandardCharsets.UTF_8.decode(buf).toString();
            System.out.println("Read: " + content); // Hello NIO Channel
        }

        // Memory-mapped file — maps file into virtual memory (fastest for large files)
        try (FileChannel fc = FileChannel.open(path,
                StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            MappedByteBuffer mmap = fc.map(FileChannel.MapMode.READ_WRITE, 0, fc.size());
            // Read first byte
            System.out.println((char) mmap.get(0)); // H
            // Write directly
            mmap.put(0, (byte) 'h'); // lowercase h
        }

        System.out.println(Files.readString(path)); // hello NIO Channel
    }
}
```

**What this does:** `FileChannel` gives direct access to OS file I/O. Memory-mapped files (`map()`) are the fastest approach for large files — the OS maps the file into virtual memory, avoiding explicit read/write calls.

---

## 6. Files.newBufferedReader / newBufferedWriter [Java 7+]

### Example 1 — Idiomatic NIO Text I/O

```java
import java.nio.file.*;
import java.nio.charset.*;
import java.io.*;

public class NIOTextIO {
    public static void main(String[] args) throws Exception {
        Path path = Path.of("/tmp/nio-text.txt");

        // Write
        try (BufferedWriter w = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
            w.write("line 1");
            w.newLine();
            w.write("line 2");
        }

        // Read
        try (BufferedReader r = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            r.lines().forEach(System.out::println);
        }

        // Stream lines directly
        try (var lines = Files.lines(path, StandardCharsets.UTF_8)) {
            long count = lines.filter(l -> l.contains("1")).count();
            System.out.println("Lines with '1': " + count); // 1
        }
    }
}
```

**What this does:** `Files.newBufferedReader/Writer` is the preferred NIO.2 way to do text I/O — always buffered, explicit charset, integrates with try-with-resources.

---

## Quick Reference

```
Path:
  Path.of("/a/b/c")                create path
  path.resolve(other)              join paths
  path.relativize(other)           compute relative path
  path.normalize()                 remove . and ..
  path.getFileName()               last component
  path.getParent()                 parent path

Files operations:
  Files.exists(p)                  check existence
  Files.createDirectories(p)       mkdir -p
  Files.readString(p)              [Java 11] read all as String
  Files.writeString(p, s)          [Java 11] write String
  Files.copy(src, dst, opts)       copy file
  Files.move(src, dst, opts)       move/rename
  Files.delete(p)                  delete (throws if not exists)
  Files.deleteIfExists(p)          delete safely
  Files.walk(root, depth)          recursive stream
  Files.find(root, depth, filter)  filtered walk
  Files.list(dir)                  direct children

Buffer cycle:
  allocate(n) → put() × n → flip() → get() × n → clear()

FileChannel:
  FileChannel.open(path, opts)
  fc.read(buffer)
  fc.write(buffer)
  fc.map(mode, pos, size)          memory-mapped

WatchService:
  dir.register(watcher, events)
  watcher.take()                   block for next key
  key.pollEvents()                 drain events
  key.reset()                      REQUIRED after processing
```
