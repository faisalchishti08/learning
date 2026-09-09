---
card: system-design
gi: 152
slug: object-blob-storage-s3-like
title: Object / blob storage (S3-like)
---

## 1. What it is

**Object storage** (also called blob storage), like Amazon S3, stores data as whole, opaque objects — a file's full bytes plus a unique key and some metadata — inside flat containers called buckets. There is no folder tree the storage system itself understands; a key like `photos/2024/vacation.jpg` just looks like a path, but it is really one flat string. You read or write an entire object at once, by its key, over a simple HTTP-style API (`PUT`, `GET`, `DELETE`).

## 2. Why & when

A traditional file system organizes data in nested directories and lets you open a file and modify just a few bytes in the middle of it — but that model does not scale well to billions of files spread across thousands of machines. Object storage gives up in-place partial edits and a real directory tree, and in exchange gets something that scales almost without limit: keys are distributed across many servers by hashing, so there is no single directory node that becomes a bottleneck. Use object storage for anything you write once and read many times as a whole unit — images, videos, backups, log archives, and static website assets — rather than as a shared, actively-edited disk.

## 3. Core concept

- **Bucket:** a flat, top-level container with a globally unique name; every object lives inside exactly one bucket.
- **Key:** the unique string identifying an object inside its bucket; the "/" characters in a key are purely cosmetic — the store has no real nested folders.
- **Object:** the actual data (bytes) plus metadata (content type, custom tags, last-modified time) and a version ID if versioning is enabled.
- **Whole-object operations:** you `PUT` an entire object to write it, and `GET` the entire object to read it — there is no API to modify just a few bytes inside an existing object; you must rewrite the whole thing.
- **Eventual vs. strong consistency:** many object stores now offer strong read-after-write consistency (a `GET` right after a `PUT` always sees the new data), but older or distributed designs historically offered only eventual consistency, so it is worth confirming which your store provides.

## 4. Diagram

```
   bucket: "user-photos"
   +----------------------------------------------------+
   | key: "alice/2024/beach.jpg"   -> object (bytes + metadata)
   | key: "alice/2024/hike.jpg"    -> object (bytes + metadata)
   | key: "bob/profile.png"        -> object (bytes + metadata)
   +----------------------------------------------------+
          ^                                    ^
          |                                    |
     PUT (write whole object)          GET (read whole object)
          |                                    |
      client uploads                     client downloads
      the full file                      the full file
```
*Caption: a bucket is a flat namespace of keys; there is no real folder hierarchy, only key strings that look like paths.*

## 5. Runnable example

**Level 1 — Basic.** A whole-object `put`/`get` store, keyed by a flat string.

**Level 2 — Metadata and content type.** Store metadata alongside the object, and let a `GET` return both.

**Level 3 — Versioning.** Keep every version of an object ever written to a key, and let a caller retrieve an older version, not just the latest.

```java
// ObjectStoreDemo.java
import java.util.*;

public class ObjectStoreDemo {

    static class StoredObject {
        final byte[] data;
        final Map<String, String> metadata;
        final int version;
        StoredObject(byte[] data, Map<String, String> metadata, int version) {
            this.data = data;
            this.metadata = metadata;
            this.version = version;
        }
    }

    static class ObjectStore {
        // key -> list of versions, oldest first; the LAST entry is always the current version.
        final Map<String, List<StoredObject>> bucket = new HashMap<>();

        // Level 1 & 2: write a whole new object (with metadata) under a flat key.
        void put(String key, byte[] data, Map<String, String> metadata) {
            List<StoredObject> versions = bucket.computeIfAbsent(key, k -> new ArrayList<>());
            int nextVersion = versions.size() + 1;
            versions.add(new StoredObject(data, metadata, nextVersion));
        }

        // Level 1: read the CURRENT (latest) version of the whole object.
        StoredObject get(String key) {
            List<StoredObject> versions = bucket.get(key);
            if (versions == null || versions.isEmpty()) return null;
            return versions.get(versions.size() - 1);
        }

        // Level 3: read a SPECIFIC older version, not just the latest.
        StoredObject getVersion(String key, int version) {
            List<StoredObject> versions = bucket.get(key);
            if (versions == null) return null;
            for (StoredObject o : versions) if (o.version == version) return o;
            return null;
        }
    }

    public static void main(String[] args) {
        ObjectStore store = new ObjectStore();
        String key = "alice/2024/beach.jpg";

        // Level 1 & 2: first upload, with content-type metadata.
        store.put(key, "photo-bytes-v1".getBytes(), Map.of("Content-Type", "image/jpeg"));
        StoredObject current = store.get(key);
        System.out.println("after v1 upload -> current version=" + current.version + ", data=" + new String(current.data));

        // Level 3: overwrite the SAME key with a new version - the old version is NOT deleted.
        store.put(key, "photo-bytes-v2-edited".getBytes(), Map.of("Content-Type", "image/jpeg"));
        current = store.get(key);
        System.out.println("after v2 upload -> current version=" + current.version + ", data=" + new String(current.data));

        StoredObject oldVersion = store.getVersion(key, 1);
        System.out.println("fetching version 1 explicitly -> data=" + new String(oldVersion.data));
    }
}
```

**How to run:** save as `ObjectStoreDemo.java`, then run `java ObjectStoreDemo.java`.

## 6. Walkthrough

1. The first `store.put(key, ...)` call finds no existing versions for the key, creates a new list, and adds a `StoredObject` with `version = 1` — this models a plain `PUT` to a fresh key.
2. `store.get(key)` returns `versions.get(versions.size() - 1)`, which is the single entry just added, so the demo prints "current version=1" with the original bytes.
3. The second `store.put(key, ...)` call reuses the *same* key; it appends a *new* `StoredObject` with `version = 2` to the same list, rather than overwriting the first entry — this models how object storage with versioning enabled never truly deletes an old version on overwrite.
4. `store.get(key)` now returns the last entry in the list (`version = 2`), so the demo prints the newly-edited bytes as the current version, matching how a plain `GET` (without a version ID) always returns the latest object.
5. `store.getVersion(key, 1)` explicitly scans for `version == 1` and finds the original `StoredObject` still intact in the list, proving the "old" data was never lost — only the store's notion of "current" moved forward, exactly the guarantee object-store versioning provides.

## 7. Gotchas & takeaways

> Gotcha: because there is no API to edit part of an object in place, a workload that needs to append to or tweak a large object repeatedly (a growing log file, a database) will end up re-uploading the entire object every time — a costly and slow pattern. Object storage suits write-once/read-many data; for frequently-mutated data, use [block storage](0153-block-storage.md) or a real database instead.

- Object storage trades a real directory hierarchy and in-place edits for near-limitless scale, achieved by treating every key as an independent, whole unit.
- Keys only *look* like file paths; the store itself has no folder concept, which is exactly what lets it distribute keys evenly across many servers.
- Versioning keeps every past version of an object under a key, letting you recover an overwritten or deleted object.
- Related concepts: [Block storage](0153-block-storage.md) (the alternative for data that needs in-place, byte-level edits), [Distributed file systems (HDFS/GFS)](0155-distributed-file-systems-hdfs-gfs.md) (a different distributed-storage model built for large sequential files), [Hot / warm / cold storage tiers](0157-hot-warm-cold-storage-tiers.md) (how object stores price and place data by access frequency).
