---
card: system-design
gi: 153
slug: block-storage
title: Block storage
---

## 1. What it is

**Block storage** divides a storage device into fixed-size chunks called blocks (e.g. 4 KB each), each identified only by a numeric address. It has no idea what a "file" is — that concept is added on top by a file system (like ext4 or NTFS) that the operating system layers over the raw blocks. A cloud "virtual disk" (such as an AWS EBS volume) is block storage: you attach it to a server, and the server's own file system decides how to organize files across its blocks.

## 2. Why & when

Databases, virtual machine disks, and any application that needs to change a small part of a large file in place — without rewriting the whole thing — need block storage's ability to read or write one specific block at a time. This is fundamentally different from [object storage](0152-object-blob-storage-s3-like.md), where you must rewrite an entire object to change even one byte. Use block storage for a database's data files, a virtual machine's boot disk, or any workload doing frequent, small, random reads and writes to parts of a larger dataset.

## 3. Core concept

- **Fixed-size blocks:** the device is divided into equal-size chunks (e.g. 4 KB, 8 KB); every read or write operation happens in whole-block units, addressed by a block number.
- **No structure of its own:** raw block storage does not know about files, directories, or names — a file system built on top maintains a map from file paths to the list of block numbers holding that file's data.
- **Random access:** you can read or write block #500 without touching blocks #1 through #499, letting an application (or database) change one small part of a large file cheaply, unlike rewriting a whole object.
- **Attached, not shared over the network by default:** a block device is normally attached to and used by one server at a time (like a local disk), though network-attached variants (SAN) exist; this differs from object storage, which every client reaches over HTTP by design.
- **Where a database uses this directly:** a database engine often manages its own block layout on top of raw block storage (or a thin file system), reading and writing individual pages/blocks as it updates rows and indexes.

## 4. Diagram

```
   raw block device (numbered, fixed-size blocks)
   +------+------+------+------+------+------+------+
   |  b0  |  b1  |  b2  |  b3  |  b4  |  b5  |  b6  |
   +------+------+------+------+------+------+------+
              ^                        ^
              |                        |
      write ONLY block b1      read ONLY block b5
      (rest untouched)          (rest untouched)

   file system layered on top:
   "report.pdf" -> blocks [b2, b4, b6]   <- the file system tracks WHICH blocks belong to which file
```
*Caption: block storage only understands numbered, fixed-size chunks; the notion of a "file" is entirely added by a layer above it.*

## 5. Runnable example

**Level 1 — Basic.** A raw block device: fixed-size blocks, addressed and modified individually.

**Level 2 — Random access.** Read or write one specific block without touching any others, the key advantage over whole-object rewrites.

**Level 3 — A tiny file system on top.** Map a file name to a list of block numbers, and reconstruct the file's contents from just those blocks.

```java
// BlockStorageDemo.java
import java.util.*;

public class BlockStorageDemo {

    // Level 1: a raw block device - fixed-size blocks, addressed by number.
    static class BlockDevice {
        final int blockSize;
        final byte[][] blocks;

        BlockDevice(int blockCount, int blockSize) {
            this.blockSize = blockSize;
            this.blocks = new byte[blockCount][blockSize];
        }

        // Level 2: write/read exactly ONE block, leaving every other block untouched.
        void writeBlock(int blockNumber, byte[] data) {
            System.arraycopy(data, 0, blocks[blockNumber], 0, Math.min(data.length, blockSize));
        }

        byte[] readBlock(int blockNumber) {
            return blocks[blockNumber];
        }
    }

    // Level 3: a minimal file system layered on top of the raw block device.
    static class TinyFileSystem {
        final BlockDevice device;
        final Map<String, List<Integer>> fileToBlocks = new HashMap<>();

        TinyFileSystem(BlockDevice device) { this.device = device; }

        void writeFile(String fileName, List<Integer> blockNumbers, List<byte[]> blockContents) {
            for (int i = 0; i < blockNumbers.size(); i++) {
                device.writeBlock(blockNumbers.get(i), blockContents.get(i));
            }
            fileToBlocks.put(fileName, blockNumbers);
        }

        // Reconstruct the file by reading ONLY the blocks the file system recorded for it.
        String readFile(String fileName) {
            StringBuilder sb = new StringBuilder();
            for (int blockNumber : fileToBlocks.get(fileName)) {
                sb.append(new String(device.readBlock(blockNumber)).trim());
            }
            return sb.toString();
        }
    }

    public static void main(String[] args) {
        BlockDevice device = new BlockDevice(8, 8); // 8 blocks, 8 bytes each
        TinyFileSystem fs = new TinyFileSystem(device);

        // Level 3: "report.pdf" is scattered across blocks 2, 4, and 6 - not contiguous, and that's fine.
        fs.writeFile("report.pdf", List.of(2, 4, 6),
            List.of("PART-ONE".getBytes(), "PART-TWO".getBytes(), "PARTTHR".getBytes()));
        System.out.println("report.pdf contents: " + fs.readFile("report.pdf"));

        // Level 2: update ONLY block 4 (the middle part), without touching blocks 2 or 6.
        device.writeBlock(4, "PARTMOD".getBytes());
        System.out.println("report.pdf after modifying only block 4: " + fs.readFile("report.pdf"));

        // Confirm block 2 and block 6 were never touched by that single-block write.
        System.out.println("block 2 unchanged: " + new String(device.readBlock(2)).trim());
        System.out.println("block 6 unchanged: " + new String(device.readBlock(6)).trim());
    }
}
```

**How to run:** save as `BlockStorageDemo.java`, then run `java BlockStorageDemo.java`.

## 6. Walkthrough

1. `fs.writeFile("report.pdf", ...)` calls `device.writeBlock` three separate times, placing `"PART-ONE"` into block 2, `"PART-TWO"` into block 4, and `"PARTTHR"` into block 6 — the blocks are not contiguous, showing the file system, not the device, is what tracks which scattered blocks belong to this file.
2. `fs.readFile("report.pdf")` looks up `fileToBlocks.get("report.pdf")`, getting back `[2, 4, 6]`, then reads exactly those three blocks in that order and concatenates them, reconstructing the original text.
3. `device.writeBlock(4, "PARTMOD".getBytes())` is called directly on the device, bypassing the file system's `writeFile` method entirely — this models a database or application that manages its own block updates, writing only block 4's bytes.
4. Calling `fs.readFile("report.pdf")` again re-reads blocks 2, 4, and 6; block 4 now returns `"PARTMOD"` instead of `"PART-TWO"`, while blocks 2 and 6 are untouched, so the reconstructed string shows only the middle part changed.
5. The final two prints read blocks 2 and 6 directly and confirm their original bytes are exactly as first written — proving the single-block write in step 3 genuinely modified only that one block, the central advantage block storage has over rewriting an entire object to change one part of it.

## 7. Gotchas & takeaways

> Gotcha: because raw block storage has no idea what a "file" is, corrupting or losing the file system's own block-mapping metadata (as simulated here by `fileToBlocks`) makes every file on the device unreadable, even though the actual block data is still perfectly intact — this is why file system metadata corruption is often far more damaging than losing a few data blocks.

- Block storage's fixed-size, individually-addressable blocks let you change a small part of a large dataset without rewriting the whole thing — the opposite tradeoff from object storage.
- The concept of a "file" is entirely a layer built on top of raw blocks; the block device itself only ever deals in block numbers.
- Databases and virtual machine disks are the classic use cases, precisely because they need frequent, small, random reads and writes.
- Related concepts: [Object / blob storage (S3-like)](0152-object-blob-storage-s3-like.md) (the whole-object alternative), [File / network file systems](0154-file-network-file-systems.md) (a shared-access model built on top of block-like storage), [Erasure coding vs replication for durability](0158-erasure-coding-vs-replication-for-durability.md) (how the underlying blocks survive disk failure).
