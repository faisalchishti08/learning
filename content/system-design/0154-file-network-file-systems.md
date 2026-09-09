---
card: system-design
gi: 154
slug: file-network-file-systems
title: File / network file systems
---

## 1. What it is

A **file system** organizes data into named files inside a tree of directories, and a **network file system** (like NFS or SMB) lets multiple separate computers access that same directory tree over the network, as if it were a local disk. Unlike [object storage](0152-object-blob-storage-s3-like.md), a file system supports opening a file, seeking to a byte offset inside it, and reading or writing just that part — much closer to how block storage behaves, but wrapped in a familiar hierarchy of folders and file names.

## 2. Why & when

Applications, especially older or off-the-shelf ones, are usually written to expect a real file system: `open()`, `read()`, `write()`, `close()`, organized under directories. A network file system lets many machines share that exact interface over a network, so several servers can read and write the same files as if each had its own local disk — something raw block storage cannot do safely, since two machines writing to the same raw blocks would corrupt each other's data. Use a network file system when multiple servers genuinely need to share the same mutable files (shared configuration, a shared upload directory, a legacy application that only knows how to talk to a file system) rather than independent, whole objects.

## 3. Core concept

- **Hierarchical namespace:** files live inside directories, which live inside other directories, forming a real tree — unlike an object store's flat key namespace.
- **Byte-range operations:** a client can open a file and read or write specific byte ranges within it, not just the whole file at once.
- **Network protocol:** NFS (common on Linux) and SMB/CIFS (common on Windows) define how a client sends "open this path", "read these bytes", and "write these bytes" requests over the network to a file server.
- **Shared, concurrent access:** because multiple clients can open the same file at once, network file systems need locking mechanisms so two clients writing to the same region do not corrupt each other's changes.
- **POSIX semantics (or an approximation of them):** many network file systems try to behave like a local file system would — the same open/read/write/close calls, the same directory operations — so existing applications can use them with little or no code change.

## 4. Diagram

```
   server-A  \                     +------------------------------+
   server-B   >---- NFS protocol --| file server                  |
   server-C  /     (open/read/     |  /shared/                    |
                     write/close)  |    config.yml                |
                                   |    uploads/                  |
                                   |      photo1.jpg               |
                                   |      photo2.jpg               |
                                   +------------------------------+

   server-A opens /shared/config.yml, reads bytes 0-99
   server-B opens the SAME file, writes bytes 100-199
      -> both see one shared, consistent directory tree
```
*Caption: several independent machines share one real directory tree over the network, each able to open and partially read or write the same files.*

## 5. Runnable example

**Level 1 — Basic.** A hierarchical namespace of directories and files, with byte-range writes.

**Level 2 — Multiple clients sharing the same file server.** Two separate "clients" open and modify the same file.

**Level 3 — Locking to prevent concurrent-write corruption.** A simple lock stops two clients from writing the same file region at the same time.

```java
// NetworkFileSystemDemo.java
import java.util.*;
import java.util.concurrent.locks.*;

public class NetworkFileSystemDemo {

    // Level 1: a hierarchical file, addressable by byte offset (mirrors byte-range writes).
    static class SharedFile {
        final StringBuilder contents = new StringBuilder();
        final ReentrantLock lock = new ReentrantLock(); // Level 3: guards concurrent writers

        void writeAt(int offset, String data, String clientName) {
            lock.lock(); // Level 3: only one client can modify this file's bytes at a time
            try {
                while (contents.length() < offset) contents.append(' ');
                contents.replace(offset, Math.min(contents.length(), offset + data.length()), data);
                if (offset + data.length() > contents.length()) contents.append(data.substring(contents.length() - offset));
                System.out.println(clientName + " wrote at offset " + offset + ": \"" + data + "\"");
            } finally {
                lock.unlock();
            }
        }

        String readRange(int offset, int length) {
            return contents.substring(offset, Math.min(contents.length(), offset + length));
        }
    }

    // Level 1: a hierarchical directory tree, like a real network file system exposes.
    static class NetworkFileServer {
        final Map<String, SharedFile> filesByPath = new HashMap<>();

        SharedFile open(String path) {
            return filesByPath.computeIfAbsent(path, p -> new SharedFile());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        NetworkFileServer server = new NetworkFileServer();

        // Level 2: two different "server" clients open the SAME path on the shared file server.
        SharedFile fileForServerA = server.open("/shared/config.yml");
        SharedFile fileForServerB = server.open("/shared/config.yml"); // resolves to the SAME SharedFile object

        // Level 3: run both clients' writes concurrently - the lock keeps them from corrupting each other.
        Thread clientA = new Thread(() -> fileForServerA.writeAt(0, "timeout=30", "server-A"));
        Thread clientB = new Thread(() -> fileForServerB.writeAt(20, "retries=5", "server-B"));
        clientA.start();
        clientB.start();
        clientA.join();
        clientB.join();

        SharedFile finalFile = server.open("/shared/config.yml");
        System.out.println("final shared file contents: \"" + finalFile.readRange(0, 29) + "\"");
    }
}
```

**How to run:** save as `NetworkFileSystemDemo.java`, then run `java NetworkFileSystemDemo.java`.

## 6. Walkthrough

1. `server.open("/shared/config.yml")` is called twice, once as `fileForServerA` and once as `fileForServerB`; `computeIfAbsent` finds the path already mapped to one `SharedFile` object after the first call, so both variables actually point to the *same* underlying file — this models two machines opening the same path on a shared network file server.
2. `clientA` and `clientB` are started as separate threads, each calling `writeAt` on what is really the same `SharedFile` at different byte offsets (0 and 20).
3. Each `writeAt` call first acquires the `SharedFile`'s own `lock`; whichever thread gets there first (the order is not guaranteed) holds the lock for its entire write, printing its message, before releasing it — the second thread blocks on `lock.lock()` until the first thread finishes, rather than writing concurrently and risking a corrupted intermediate state.
4. Because `clientA` writes at offset 0 and `clientB` writes at offset 20, their writes affect different byte ranges of the same file — both regions end up correctly present in the final contents, regardless of which thread ran first, since the lock only prevents a genuinely simultaneous write, not sequential ones to different ranges.
5. The final `readRange` call, made through yet another `server.open(...)` call, returns the same `SharedFile` object again and reads back both writes correctly combined — confirming that both "clients" were really operating on one consistent, shared file the whole time, exactly the property a network file system provides across real separate machines.

## 7. Gotchas & takeaways

> Gotcha: if two clients write to the *same* byte range at the same time without any locking, the result is a race — whichever write's bytes land last simply overwrite the other's, silently discarding data with no error raised. Real network file systems provide file-locking APIs (e.g. NFS's `flock`) specifically so applications can coordinate this themselves; the file system does not automatically prevent overlapping writes just because it is shared.

- A network file system gives multiple machines the same familiar hierarchical, byte-range file interface a local disk provides, just reached over a network protocol.
- This shared-write capability is exactly what raw block storage or object storage cannot safely offer to more than one uncoordinated writer at once.
- Locking is the application's (or protocol's) responsibility — the file system does not automatically serialize overlapping writes to the same file region.
- Related concepts: [Block storage](0153-block-storage.md) (the lower-level, single-writer-oriented alternative this is often built on), [Object / blob storage (S3-like)](0152-object-blob-storage-s3-like.md) (flat and whole-object, instead of hierarchical and byte-range), [Distributed file systems (HDFS/GFS)](0155-distributed-file-systems-hdfs-gfs.md) (a network file system designed to scale across thousands of machines).
