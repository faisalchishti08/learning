---
card: system-design
gi: 10
slug: read-write-ratio-its-design-impact
title: Read:write ratio & its design impact
---

## 1. What it is

The **read:write ratio** is the proportion of read operations to write operations a system handles, usually written as a ratio like "100:1" meaning 100 reads for every 1 write. It is one number that summarizes the entire *shape* of a workload, and that shape drives many of the most important architecture decisions in a design: whether to cache, how to index, and which database model fits best.

Think of a library: if patrons mostly browse and rarely donate new books, you optimize for fast browsing (many catalog copies, good search). If donations pour in constantly and browsing is rare, you optimize for fast intake instead. The ratio of one activity to the other decides where you invest.

## 2. Why & when

Almost every real system is read-heavy or write-heavy, rarely balanced. Knowing which one you are dealing with tells you, immediately, whether a cache will help (it helps enormously for read-heavy systems, barely at all for write-heavy ones), and whether you should optimize your database schema for fast lookups or fast inserts. You compute or estimate this ratio right after gathering functional requirements, since "how do users interact with this system" naturally reveals which action dominates.

## 3. Core concept

**How to estimate the ratio:** count the functional requirements that read data versus those that write data, and weigh them by how often each happens. For a social feed: posting a tweet (write) happens rarely per user per day, while viewing a timeline (read) happens many times per day, and each view scans many other users' tweets. This naturally produces a heavily read-skewed ratio, often 100:1 or higher in real systems like Twitter.

**What a read-heavy ratio implies for the design:**
- Add a **cache** (like Redis or an in-memory cache) in front of the database, since the same data is read far more often than it changes.
- Add **read replicas**: multiple copies of the database that only serve reads, so read traffic can be spread across many machines while writes go to one primary.
- Optimize the data model for fast lookups, even if that costs some write-time work (like pre-computing a timeline when a tweet is posted, so reading it later is instant).

**What a write-heavy ratio implies for the design:**
- A cache helps less, since data changes before it would be reused from cache.
- Optimize for fast, durable writes: batching, write-ahead logs, or a message queue to absorb write bursts.
- Consider a database optimized for write throughput over complex read queries.

## 4. Diagram

```
       READ-HEAVY (e.g. 100:1)                 WRITE-HEAVY (e.g. 1:10)
       [R][R][R][R][R][R]...[W]                [W][W][W][W][W][W][W][R]

       ==> add a CACHE                         ==> optimize WRITE PATH
       ==> add READ REPLICAS                   ==> batch / queue writes
       ==> precompute reads on write            ==> cache helps far less
```
*Caption: the dominant operation in the ratio decides which side of the system you optimize.*

## 5. Runnable example

### Artifact: a Java program that computes the ratio and recommends a strategy

```java
public class ReadWriteRatioAdvisor {

    static double ratio(long readsPerDay, long writesPerDay) {
        return (double) readsPerDay / writesPerDay;
    }

    static String recommend(double ratio) {
        if (ratio >= 10) {
            return "Read-heavy: add a cache and read replicas; precompute reads on write.";
        } else if (ratio <= 0.1) {
            return "Write-heavy: optimize the write path; batch or queue writes; cache helps little.";
        } else {
            return "Balanced: weigh cache benefit against write-invalidation cost carefully.";
        }
    }

    public static void main(String[] args) {
        long readsPerDay = 10_000_000_000L;   // 10 billion timeline reads/day
        long writesPerDay = 100_000_000L;     // 100 million new tweets/day

        double r = ratio(readsPerDay, writesPerDay);
        System.out.printf("Read:write ratio = %.0f:1%n", r);
        System.out.println(recommend(r));
    }
}
```

**How to run:** save as `ReadWriteRatioAdvisor.java`, run `java ReadWriteRatioAdvisor.java` (JDK 17+).

## 6. Walkthrough

1. `ratio` divides daily reads by daily writes, producing a single number representing "how many reads per write".
2. `recommend` checks that number against two thresholds: 10 or more marks a clearly read-heavy system, 0.1 or less marks a clearly write-heavy one, and anything between is treated as balanced.
3. `main` plugs in a Twitter-like scenario: 10 billion timeline reads a day against 100 million new tweets a day.
4. Output:
```
Read:write ratio = 100:1
Read-heavy: add a cache and read replicas; precompute reads on write.
```
5. This single computed ratio, spoken out loud in an interview ("reads outnumber writes about 100 to 1, so I'll prioritize caching and read replicas over write optimization"), directly justifies the next architecture decision you make, instead of adding a cache just because caches are generally considered good practice.

## 7. Gotchas & takeaways

> **Gotcha:** adding a cache to a write-heavy system out of habit. If data changes as often as, or more often than, it is read, a cache spends more effort staying invalidated and up to date than it saves on reads — it can even slow the system down.

- Always compute or estimate the read:write ratio before deciding whether to cache.
- A ratio of 10:1 or higher is a strong signal to invest in read-side optimizations (cache, replicas, precomputation).
- A ratio near 1:1 or write-skewed is a signal to focus on the write path instead, and to be cautious about caching.
