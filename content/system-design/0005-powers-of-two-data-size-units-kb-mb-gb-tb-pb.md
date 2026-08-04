---
card: system-design
gi: 5
slug: powers-of-two-data-size-units-kb-mb-gb-tb-pb
title: Powers of two & data-size units (KB/MB/GB/TB/PB)
---

## 1. What it is

Computers store data in units built from powers of two, because memory addresses are binary. The common units, each 1,024 (2^10) times the one before it, are: **byte** (8 bits), **kilobyte (KB)**, **megabyte (MB)**, **gigabyte (GB)**, **terabyte (TB)**, and **petabyte (PB)**. Knowing these units, and being able to convert between them quickly, is the basic vocabulary every storage and bandwidth estimate in a system design interview is spoken in.

Think of it like knowing that 12 inches make a foot and 3 feet make a yard: you do not re-derive it each time, you just know it, so you can focus on the actual estimate.

## 2. Why & when

Every capacity estimate — how much storage a system needs, how much bandwidth it uses — ends in a unit like GB/day or PB/year. If you cannot quickly convert "500 million records at 1 KB each" into "about 500 GB", you will stall doing arithmetic instead of reasoning about the design. This tutorial gives you the fixed numbers so later estimation tutorials (storage, bandwidth) can move fast.

You use this constantly, anywhere a number needs a unit: sizing a database, sizing a cache, deciding if data fits in memory or needs disk.

## 3. Core concept

**The exact powers of two**, and the round numbers worth memorizing:

| Unit | Exact value (bytes) | Approx. (round number) |
|---|---|---|
| 1 KB (kilobyte) | 2^10 = 1,024 | ~10^3 (1 thousand) |
| 1 MB (megabyte) | 2^20 = 1,048,576 | ~10^6 (1 million) |
| 1 GB (gigabyte) | 2^30 ≈ 1.07 × 10^9 | ~10^9 (1 billion) |
| 1 TB (terabyte) | 2^40 ≈ 1.10 × 10^12 | ~10^12 (1 trillion) |
| 1 PB (petabyte) | 2^50 ≈ 1.13 × 10^15 | ~10^15 (1 quadrillion) |

**The interview shortcut:** in a live interview, nobody expects exact binary math. Round KB to 10^3, MB to 10^6, GB to 10^9, and so on. The error this introduces is about 7% to 13%, which does not change any architecture decision. Speed and correct order of magnitude matter far more than precision.

**How to convert between units fast:** count how many steps apart the two units are (each step is ×1,024, or ×1,000 rounded), and multiply or divide that many times. Going from bytes to GB is three steps down (÷1,000 three times); going from GB to bytes is three steps up (×1,000 three times).

## 4. Diagram

```
 byte --x1024--> KB --x1024--> MB --x1024--> GB --x1024--> TB --x1024--> PB
   1                1,024      ~10^6         ~10^9         ~10^12        ~10^15
                    (~10^3)

 Rounded for speed:   x1000 each step, instead of x1024.
```
*Caption: each unit is roughly 1,000× (exactly 1,024×) the one before it; round to 1,000 for fast mental math.*

## 5. Runnable example

### Artifact: a Java unit-conversion calculator using rounded powers of ten

```java
public class DataSizeConverter {

    // Rounded, interview-style conversion: 1 KB = 10^3 bytes, and so on.
    static double bytesToUnit(long bytes, String unit) {
        return switch (unit) {
            case "KB" -> bytes / 1_000.0;
            case "MB" -> bytes / 1_000_000.0;
            case "GB" -> bytes / 1_000_000_000.0;
            case "TB" -> bytes / 1_000_000_000_000.0;
            case "PB" -> bytes / 1_000_000_000_000_000.0;
            default -> bytes;
        };
    }

    public static void main(String[] args) {
        long recordSizeBytes = 500; // e.g. a tweet with metadata
        long recordCount = 500_000_000L; // 500 million records

        long totalBytes = recordSizeBytes * recordCount;

        System.out.println("Total bytes: " + totalBytes);
        System.out.printf("= %.2f KB%n", bytesToUnit(totalBytes, "KB"));
        System.out.printf("= %.2f MB%n", bytesToUnit(totalBytes, "MB"));
        System.out.printf("= %.2f GB%n", bytesToUnit(totalBytes, "GB"));
        System.out.printf("= %.4f TB%n", bytesToUnit(totalBytes, "TB"));
    }
}
```

**How to run:** save as `DataSizeConverter.java`, run `java DataSizeConverter.java` (JDK 17+).

## 6. Walkthrough

1. `bytesToUnit` takes a byte count and a target unit string, and divides by the rounded power of ten for that unit — 10^3 for KB, 10^6 for MB, and so on.
2. `main` sets up a realistic scenario: 500 million records of 500 bytes each, matching a plausible tweet-with-metadata size.
3. It multiplies `recordSizeBytes * recordCount` to get `totalBytes`, then converts that same number into KB, MB, GB, and TB using the helper.
4. Output:
```
Total bytes: 250000000000
= 250000000.00 KB
= 250000.00 MB
= 250.00 GB
= 0.2500 TB
```
5. This is the exact calculation you would do by hand in an interview: multiply record size by count, then shift the decimal point three digits at a time to name a bigger unit, until you reach a number that is easy to say and reason about (here, "250 GB").

## 7. Gotchas & takeaways

> **Gotcha:** confusing bits and bytes. Network bandwidth is usually quoted in bits per second (Mbps), while storage is quoted in bytes (MB). Forgetting the ÷8 or ×8 conversion between them silently makes every bandwidth estimate wrong by a factor of eight.

- Memorize the round numbers: KB ≈ 10^3, MB ≈ 10^6, GB ≈ 10^9, TB ≈ 10^12, PB ≈ 10^15 bytes.
- Round aggressively in interviews; exact powers of 1,024 are not worth the time.
- Always double-check whether a number is in bits or bytes before using it in a calculation.
