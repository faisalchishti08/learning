---
card: system-design
gi: 155
slug: distributed-file-systems-hdfs-gfs
title: Distributed file systems (HDFS/GFS)
---

## 1. What it is

A **distributed file system**, such as the Hadoop Distributed File System (HDFS) or Google's original GFS design it was based on, stores enormous files by splitting each one into large fixed-size chunks (e.g. 128 MB blocks in HDFS) and spreading those chunks across many machines. A single **NameNode** (metadata server) tracks which machines hold which chunks of which file, while the actual chunk data lives on many **DataNodes**. This lets one logical file be far larger than any single disk, and lets many machines read different parts of it in parallel.

## 2. Why & when

A file too large to fit on one machine — think many terabytes of log data or a huge dataset for batch analytics — must be split across many machines' disks, and something must track where every piece went. A distributed file system solves exactly this, and adds automatic replication of each chunk (typically 3 copies, on different machines) so a single disk or server failure does not lose any data. Use it for very large files that need to be processed by many worker machines in parallel, such as the input to a big-data batch job — this is a very different problem from a [network file system](0154-file-network-file-systems.md) sharing modest-sized files among a handful of servers.

## 3. Core concept

- **NameNode (metadata server):** holds the mapping from file paths to the list of chunk IDs that make up each file, and which DataNodes currently hold each chunk — this is the single source of truth for "where is my data."
- **DataNodes:** the many machines that actually store chunk data on their local disks, and serve read/write requests for the chunks they hold.
- **Large, fixed-size chunks:** files are split into large blocks (128 MB is HDFS's classic default) — large enough that the overhead of tracking each chunk's metadata stays small relative to the data it represents.
- **Replication for durability:** each chunk is stored on multiple DataNodes (commonly 3); if one DataNode fails, the NameNode still knows two other machines hold that same chunk, and a new copy is made elsewhere to restore the replication factor.
- **Write-once, append-friendly:** many distributed file systems (HDFS included) are optimized for writing a file once (or appending to it) and reading it many times, rather than for frequent random modification of existing bytes.

## 4. Diagram

```
                       NameNode (metadata only)
                       file "bigdata.log" -> chunks [c1, c2, c3]
                       c1 -> DataNode-A, DataNode-B, DataNode-C
                       c2 -> DataNode-B, DataNode-C, DataNode-D
                       c3 -> DataNode-A, DataNode-C, DataNode-D
                              |
              client asks NameNode: "where is bigdata.log?"
                              |
              NameNode replies: chunk locations (above)
                              |
              client reads/writes chunks DIRECTLY from/to the DataNodes
   DataNode-A   DataNode-B   DataNode-C   DataNode-D
     [c1,c3]      [c1,c2]     [c1,c2,c3]    [c2,c3]
```
*Caption: the NameNode only tracks metadata; the actual chunk data transfer happens directly between the client and the DataNodes, and every chunk lives on several DataNodes for durability.*

## 5. Runnable example

**Level 1 — Basic.** Split a file into fixed-size chunks and record which chunks make it up.

**Level 2 — Replicate each chunk across multiple DataNodes.** Track multiple copies per chunk, the way real HDFS does.

**Level 3 — Handle a DataNode failure.** Detect that a DataNode went down and re-replicate its chunks elsewhere to restore the replication factor.

```java
// DistributedFileSystemDemo.java
import java.util.*;

public class DistributedFileSystemDemo {

    // Level 1: the NameNode - metadata only, no actual chunk data.
    static class NameNode {
        final Map<String, List<String>> fileToChunkIds = new HashMap<>();
        final Map<String, List<String>> chunkToDataNodes = new HashMap<>(); // Level 2: replication

        void registerFile(String path, List<String> chunkIds, List<List<String>> replicaSets) {
            fileToChunkIds.put(path, chunkIds);
            for (int i = 0; i < chunkIds.size(); i++) {
                chunkToDataNodes.put(chunkIds.get(i), new ArrayList<>(replicaSets.get(i)));
            }
        }

        List<String> chunksFor(String path) { return fileToChunkIds.get(path); }
        List<String> dataNodesFor(String chunkId) { return chunkToDataNodes.get(chunkId); }

        // Level 3: replace a failed DataNode with a new replica location for every chunk it held.
        void handleDataNodeFailure(String failedNode, String replacementNode) {
            for (Map.Entry<String, List<String>> entry : chunkToDataNodes.entrySet()) {
                List<String> nodes = entry.getValue();
                if (nodes.remove(failedNode)) {
                    nodes.add(replacementNode);
                    System.out.println("  re-replicated chunk " + entry.getKey() + ": " + failedNode + " -> " + replacementNode);
                }
            }
        }
    }

    public static void main(String[] args) {
        NameNode nameNode = new NameNode();

        // Level 1 & 2: "bigdata.log" split into 3 chunks, each replicated onto 3 DataNodes.
        nameNode.registerFile("bigdata.log",
            List.of("c1", "c2", "c3"),
            List.of(
                List.of("DataNode-A", "DataNode-B", "DataNode-C"),
                List.of("DataNode-B", "DataNode-C", "DataNode-D"),
                List.of("DataNode-A", "DataNode-C", "DataNode-D")
            ));

        System.out.println("chunks for bigdata.log: " + nameNode.chunksFor("bigdata.log"));
        for (String chunkId : nameNode.chunksFor("bigdata.log")) {
            System.out.println("  " + chunkId + " -> " + nameNode.dataNodesFor(chunkId));
        }

        // Level 3: DataNode-C fails - it held a replica of EVERY chunk in this example.
        System.out.println("DataNode-C failed! Re-replicating its chunks onto DataNode-E...");
        nameNode.handleDataNodeFailure("DataNode-C", "DataNode-E");

        System.out.println("chunk locations after recovery:");
        for (String chunkId : nameNode.chunksFor("bigdata.log")) {
            System.out.println("  " + chunkId + " -> " + nameNode.dataNodesFor(chunkId));
        }
    }
}
```

**How to run:** save as `DistributedFileSystemDemo.java`, then run `java DistributedFileSystemDemo.java`.

## 6. Walkthrough

1. `nameNode.registerFile` records that `bigdata.log` consists of chunks `c1`, `c2`, `c3`, and separately records which three DataNodes hold a replica of each chunk — this is the entirety of what the NameNode stores; no actual file bytes ever touch it.
2. The first loop prints each chunk's DataNode list, showing `c1` on `A/B/C`, `c2` on `B/C/D`, and `c3` on `A/C/D` — notice `DataNode-C` happens to hold a replica of every single chunk in this small example.
3. `nameNode.handleDataNodeFailure("DataNode-C", "DataNode-E")` iterates every chunk's replica list; `nodes.remove("DataNode-C")` succeeds for all three chunks (since it held a replica of each), so all three trigger the re-replication branch, adding `DataNode-E` in its place and printing a message per chunk.
4. The final loop re-prints each chunk's DataNode list; every occurrence of `DataNode-C` has been replaced with `DataNode-E`, while the other original DataNodes for each chunk (e.g. `A` and `B` for `c1`) are untouched.
5. At no point did any chunk drop below its intended replication factor of three — the NameNode detected the loss of one replica per chunk and immediately restored it, which is exactly the automated durability guarantee a real HDFS cluster provides when a DataNode actually fails.

## 7. Gotchas & takeaways

> Gotcha: the NameNode is a single, central point holding all the file-to-chunk metadata; if it goes down (or its metadata is lost) with no backup, the cluster has no way to find any chunk anywhere, even though the chunk data itself is still sitting untouched on all the DataNodes. Production HDFS deployments run a standby NameNode with synchronized metadata specifically to avoid this single point of failure.

- A distributed file system splits huge files into large chunks, spread and replicated across many machines, so one logical file can exceed any single disk's capacity.
- The metadata server (NameNode) only tracks *where* chunks are; the actual chunk data transfer happens directly between clients and DataNodes.
- Replication (typically a factor of three) means a lost DataNode triggers automatic re-replication elsewhere, not data loss.
- Related concepts: [File / network file systems](0154-file-network-file-systems.md) (a much smaller-scale, single-server-metadata alternative), [Redundancy & replication](0130-redundancy-replication.md) (the general pattern this durability model is built on), [Erasure coding vs replication for durability](0158-erasure-coding-vs-replication-for-durability.md) (a storage-efficient alternative to full replica copies).
