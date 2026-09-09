---
card: system-design
gi: 158
slug: erasure-coding-vs-replication-for-durability
title: Erasure coding vs replication for durability
---

## 1. What it is

**Replication** protects data by keeping several full copies on different machines — if one fails, another complete copy is still available. **Erasure coding** protects data by splitting it into data fragments plus extra parity (redundancy) fragments, spread across different machines, such that the original data can be fully reconstructed even if some fragments are lost — without needing a full extra copy of everything. Both survive hardware failure; they differ in how much extra storage that safety costs.

## 2. Why & when

Storing three full replicas of every byte (a common replication factor) means using three times the raw storage of the actual data — a real cost at scale. Erasure coding can provide similar (or better) durability while using far less extra storage — for example, splitting data into 6 data fragments plus 3 parity fragments needs only 1.5x the storage instead of 3x, while still surviving the loss of any 3 fragments. The tradeoff is that reconstructing data from surviving fragments takes computation (recomputing missing pieces), which replication does not require — you just read a whole, undamaged copy. Use replication when you need the fastest possible recovery and read latency (a hot, actively-used database); use erasure coding for large, less frequently accessed data where storage cost matters more than instant read speed, such as archival or cold-tier object storage.

## 3. Core concept

- **Replication factor:** the number of full copies kept (commonly 3); storage overhead is `(replication factor) x (data size)`.
- **Erasure coding scheme, "k data + m parity":** data is split into `k` fragments, and `m` additional parity fragments are computed from them; the original data can be reconstructed from any `k` of the total `k+m` fragments — surviving the loss of up to `m` fragments.
- **Storage overhead comparison:** a 6-data + 3-parity scheme needs `9/6 = 1.5x` storage for the same durability profile that 3x replication needs 3x storage for — a substantial saving at scale.
- **Reconstruction cost:** rebuilding a lost fragment (or the original data) from parity requires a computation (similar to how RAID parity works), which takes CPU time and is slower than simply reading an intact replica.
- **Where each fits:** replication favors read speed and simple recovery; erasure coding favors storage efficiency at the cost of reconstruction complexity and (usually) higher latency on the reconstruction path.

## 4. Diagram

```
   REPLICATION (factor 3):                 ERASURE CODING (4 data + 2 parity):
   [ full copy A ]                          [d1][d2][d3][d4][p1][p2]
   [ full copy B ]   3x storage              6 fragments total, 4x data size
   [ full copy C ]                           2.0x storage: any 4 of 6 rebuild the data

   lose copy A:                              lose d2 and p1:
   read from B or C directly                 reconstruct d2 from d1,d3,d4,p2
   (instant, no computation)                 (needs a parity computation first)
```
*Caption: replication keeps whole extra copies for instant recovery; erasure coding keeps cheaper parity fragments that need a computation to rebuild lost data.*

## 5. Runnable example

**Level 1 — Basic.** Model plain replication: multiple full copies, instant recovery from any surviving one.

**Level 2 — Erasure coding with simple parity.** Split data into fragments plus one XOR-based parity fragment, and reconstruct a lost fragment from the survivors.

**Level 3 — Compare storage overhead directly.** Compute and print the actual storage multiplier for each approach on the same data size.

```java
// DurabilityDemo.java
import java.util.*;

public class DurabilityDemo {

    // Level 1: replication - N full copies; losing any (N-1) of them still leaves one intact copy.
    static void demonstrateReplication(byte[] data) {
        byte[][] replicas = { data.clone(), data.clone(), data.clone() }; // replication factor 3
        replicas[0] = null; // simulate losing copy A
        byte[] recovered = replicas[1] != null ? replicas[1] : replicas[2]; // instant - just read a survivor
        System.out.println("replication: lost 1 of 3 copies, recovered instantly from a surviving copy: " + new String(recovered));
    }

    // Level 2: erasure coding - split into fragments + one XOR parity fragment; rebuild a lost fragment.
    static void demonstrateErasureCoding(byte[] data) {
        int fragmentSize = data.length / 2;
        byte[] d1 = Arrays.copyOfRange(data, 0, fragmentSize);
        byte[] d2 = Arrays.copyOfRange(data, fragmentSize, data.length);
        byte[] parity = new byte[fragmentSize];
        for (int i = 0; i < fragmentSize; i++) parity[i] = (byte) (d1[i] ^ d2[i]); // parity = d1 XOR d2

        System.out.println("erasure coding: 2 data fragments + 1 parity fragment computed.");

        // Simulate losing fragment d2 - reconstruct it from d1 and parity (a real computation, not a plain read).
        byte[] reconstructedD2 = new byte[fragmentSize];
        for (int i = 0; i < fragmentSize; i++) reconstructedD2[i] = (byte) (d1[i] ^ parity[i]); // d2 = d1 XOR parity
        boolean matches = Arrays.equals(reconstructedD2, d2);
        System.out.println("lost fragment d2, reconstructed from d1+parity via XOR: matches original = " + matches);
        System.out.println("reconstructed d2 contents: " + new String(reconstructedD2));
    }

    // Level 3: compare the real storage overhead of each approach.
    static void compareStorageOverhead(int dataBytes) {
        int replicationTotal = dataBytes * 3; // factor of 3
        int erasureTotalFor6Plus3 = (dataBytes / 6) * 9; // 6 data + 3 parity fragments
        System.out.println("for " + dataBytes + " bytes of data:");
        System.out.println("  replication (factor 3): " + replicationTotal + " bytes stored (3.0x overhead)");
        System.out.println("  erasure coding (6+3):    " + erasureTotalFor6Plus3 + " bytes stored (1.5x overhead)");
    }

    public static void main(String[] args) {
        byte[] data = "IMPORTANT-FILE-DATA".getBytes(); // 20 bytes, even length for simplicity
        demonstrateReplication(data);
        demonstrateErasureCoding(data);
        compareStorageOverhead(600_000);
    }
}
```

**How to run:** save as `DurabilityDemo.java`, then run `java DurabilityDemo.java`.

## 6. Walkthrough

1. `demonstrateReplication` creates three identical clones of `data`, then sets `replicas[0] = null` to simulate a lost copy; recovery is simply `replicas[1] != null ? replicas[1] : replicas[2]` — a plain read of whichever surviving copy comes first, with no computation involved at all.
2. `demonstrateErasureCoding` splits `data` into two equal halves, `d1` and `d2`, then computes `parity[i] = d1[i] ^ d2[i]` for every byte — this is the simplest possible erasure code, using the XOR operation's property that `a ^ b ^ a = b`.
3. The demo simulates losing `d2` entirely and reconstructs it using only `d1` and `parity`: `reconstructedD2[i] = d1[i] ^ parity[i]`, which algebraically recovers the original `d2[i]` because `d1[i] ^ (d1[i] ^ d2[i]) = d2[i]`.
4. `Arrays.equals(reconstructedD2, d2)` confirms the reconstruction is byte-for-byte correct, and printing its contents as a string shows the original text was fully recovered — even though `d2` itself was never directly stored anywhere after being "lost."
5. `compareStorageOverhead` then makes the cost tradeoff concrete with real numbers: for 600,000 bytes of source data, replication needs 1,800,000 bytes stored (3.0x), while a 6-data + 3-parity erasure scheme needs only 900,000 bytes (1.5x) — half the storage cost, for a comparable (in this simplified example) ability to survive lost fragments.

## 7. Gotchas & takeaways

> Gotcha: the simple XOR parity shown here can only reconstruct data if exactly one fragment among the group is missing — real erasure-coding schemes (like Reed-Solomon) generalize this so that any `m` fragments can be lost and reconstructed from any `k` survivors, but that generalization requires real matrix-based math, not a single XOR; never assume single-parity XOR is enough durability for a scheme meant to survive multiple simultaneous failures.

- Replication gives instant, computation-free recovery at the cost of storing full extra copies; erasure coding gives cheaper storage at the cost of a real reconstruction computation.
- The "k data + m parity" notation describes exactly how many fragment losses a scheme survives, and directly determines its storage overhead multiplier.
- Erasure coding suits large, less latency-sensitive data (archives, cold storage); replication suits actively-read, latency-sensitive data.
- Related concepts: [Redundancy & replication](0130-redundancy-replication.md) (the general durability pattern replication implements), [Distributed file systems (HDFS/GFS)](0155-distributed-file-systems-hdfs-gfs.md) (systems that choose between these two strategies for chunk durability), [Hot / warm / cold storage tiers](0157-hot-warm-cold-storage-tiers.md) (cold-tier storage is where erasure coding is most commonly applied, for its storage savings).
