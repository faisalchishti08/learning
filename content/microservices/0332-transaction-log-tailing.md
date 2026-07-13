---
card: microservices
gi: 332
slug: transaction-log-tailing
title: "Transaction log tailing"
---

## 1. What it is

**Transaction log tailing** is a way to implement the relay side of the [transactional outbox pattern](0331-transactional-outbox-pattern.md) (or to capture any database change for downstream use) by reading the database's own internal write-ahead/commit log — the durable, ordered record every database already maintains internally to support crash recovery — instead of having application code poll a table for new rows. Every committed change (including outbox inserts) already appears in this log the instant it commits, so tailing it gives a real-time, reliable, low-overhead feed of every change, without adding any extra query load to the database.

## 2. Why & when

A [polling publisher](0334-polling-publisher-pattern.md) that repeatedly queries an outbox table for unsent rows works, but it adds recurring query load to the database and introduces a polling-interval delay between a commit and its detection. The database's transaction log, however, already records every committed write, in commit order, the moment it happens — reading that log directly (rather than issuing new queries against the tables) gets the same information with lower latency and without extra read load on the live tables.

Use transaction log tailing when polling's overhead or latency becomes a real problem, or whenever you want a general-purpose feed of every change to a table (not just outbox rows) for downstream consumption — this is exactly the mechanism behind [Change Data Capture (CDC)](0333-change-data-capture-cdc.md) tools. It requires a tool that understands your specific database's log format (e.g., Debezium reading MySQL's binlog or Postgres's write-ahead log), which is more operational complexity than a simple polling query, so it's a tradeoff of lower latency and load against added infrastructure.

## 3. Core concept

Every committed transaction is appended to the database's internal log in commit order, with enough detail to describe exactly what changed. A log-tailing process attaches to this log as a reader (the same mechanism the database itself uses for replication), decodes each entry into a structured change record, and forwards it downstream — all without the source tables being queried at all for this purpose.

```java
record LogEntry(long logPosition, String table, String operation, String rowDataJson) {} // one per committed row change
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application commits a transaction which is appended to the database's transaction log; a log-tailing process reads new log entries as they appear and forwards them downstream, without querying the tables directly">
  <rect x="20" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">App commits</text>

  <line x1="170" y1="37" x2="240" y2="37" stroke="#8b949e" marker-end="url(#a332)"/>
  <rect x="250" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="325" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Transaction log</text>

  <line x1="325" y1="54" x2="325" y2="90" stroke="#79c0ff" marker-end="url(#a332b)"/>
  <rect x="230" y="90" width="190" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="325" y="112" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Log-tailing process reads it</text>

  <text x="325" y="150" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">The source table is NEVER directly queried by this process.</text>

  <defs>
    <marker id="a332" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a332b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The log-tailing process attaches directly to the durable commit log, seeing every change without querying the live tables.

## 5. Runnable example

Scenario: an outbox-relay implemented first as polling (with its inherent delay), then rebuilt as a simulated log-tailing reader that reacts the instant a commit is appended, and finally hardened to track its exact log position so it resumes correctly after a restart instead of reprocessing or missing entries.

### Level 1 — Basic

```java
// File: PollingRelay.java -- checks the outbox table on a fixed interval;
// there is unavoidable delay between a commit and the poll noticing it.
import java.util.*;

public class PollingRelay {
    static List<String> outboxTable = new ArrayList<>();
    static int lastSeenIndex = 0;

    static void commitOrder(String orderId) {
        outboxTable.add("OrderPlaced:" + orderId);
        System.out.println("committed at index " + (outboxTable.size() - 1) + " -- polling relay hasn't looked yet");
    }

    static void pollOnce() { // simulates one fixed-interval poll cycle
        System.out.println("poll: checking outbox table for new rows since index " + lastSeenIndex + "...");
        for (int i = lastSeenIndex; i < outboxTable.size(); i++) System.out.println("  found and relaying: " + outboxTable.get(i));
        lastSeenIndex = outboxTable.size();
    }

    public static void main(String[] args) {
        commitOrder("order-1");
        System.out.println("--- time passes until the NEXT scheduled poll interval ---");
        pollOnce(); // only NOW does the relay notice the commit -- there was a real delay
    }
}
```

How to run: `java PollingRelay.java`

`commitOrder` writes to `outboxTable` instantly, but nothing reacts to it until `pollOnce` runs — standing in for the fixed interval a real polling loop waits between checks. Every commit sits unnoticed for up to that whole interval, and every poll cycle costs a query against `outboxTable`, whether or not anything new has actually been written.

### Level 2 — Intermediate

```java
// File: LogTailingRelay.java -- a simulated transaction log that the
// relay TAILS (attaches to as a reader); commits are noticed IMMEDIATELY,
// with no fixed polling interval and no query against the outbox table itself.
import java.util.*;
import java.util.function.Consumer;

public class LogTailingRelay {
    static List<String> transactionLog = new ArrayList<>(); // stands in for the database's internal commit log
    static List<Consumer<String>> logTailers = new ArrayList<>(); // relays attached as READERS of the log

    static void commitOrder(String orderId) {
        String entry = "OrderPlaced:" + orderId;
        transactionLog.add(entry);
        System.out.println("commit appended to transaction log: " + entry);
        logTailers.forEach(tailer -> tailer.accept(entry)); // every attached tailer is notified IMMEDIATELY
    }

    public static void main(String[] args) {
        logTailers.add(entry -> System.out.println("relay (tailing the log): saw " + entry + " INSTANTLY, no polling delay, no outbox-table query"));

        commitOrder("order-1"); // the relay reacts in the SAME step, not on some later poll cycle
    }
}
```

How to run: `java LogTailingRelay.java`

The relay is registered as a `logTailer` — a reader attached directly to `transactionLog`. When `commitOrder` runs, it appends to the log and immediately notifies every attached tailer in the same call, with no separate poll cycle and no query issued against any outbox table — the relay reacted the instant the commit happened.

### Level 3 — Advanced

```java
// File: LogTailingWithResumePosition.java -- the relay tracks the exact
// LOG POSITION it has processed up to, persists it, and on "restart"
// resumes from that position -- so a crash doesn't reprocess already-seen
// entries or skip ones it never saw.
import java.util.*;

public class LogTailingWithResumePosition {
    static List<String> transactionLog = new ArrayList<>();
    static Map<String, Long> persistedTailerPosition = new HashMap<>(); // survives a "restart" -- durable checkpoint

    static void commitOrder(String orderId) {
        transactionLog.add("OrderPlaced:" + orderId);
        System.out.println("commit appended at log position " + (transactionLog.size() - 1));
    }

    static void tailFrom(String tailerName) {
        long resumePosition = persistedTailerPosition.getOrDefault(tailerName, 0L);
        System.out.println(tailerName + ": resuming from persisted log position " + resumePosition);
        for (long pos = resumePosition; pos < transactionLog.size(); pos++) {
            System.out.println("  " + tailerName + " processing position " + pos + ": " + transactionLog.get((int) pos));
            persistedTailerPosition.put(tailerName, pos + 1); // checkpoint AFTER each entry, so a crash mid-batch resumes correctly
        }
    }

    public static void main(String[] args) {
        commitOrder("order-1");
        commitOrder("order-2");

        tailFrom("relay-1"); // processes both, checkpointing after each

        System.out.println("--- relay-1 CRASHES and restarts here ---");
        commitOrder("order-3"); // a NEW commit happens while relay-1 was down

        tailFrom("relay-1"); // resumes from its persisted position -- does NOT reprocess order-1 or order-2
    }
}
```

How to run: `java LogTailingWithResumePosition.java`

The first `tailFrom("relay-1")` call starts at `resumePosition=0` (nothing persisted yet), processes both existing log entries, and checkpoints `persistedTailerPosition` to `1` and then `2` as it goes. After a simulated crash and a new commit (`order-3`, landing at position `2`), the second `tailFrom("relay-1")` call reads `persistedTailerPosition.getOrDefault("relay-1", 0L)`, which is now `2` — so it resumes exactly at position `2`, correctly processing only `order-3` and never touching the two entries it already handled before the simulated crash.

## 6. Walkthrough

Trace `LogTailingWithResumePosition.main` in order. **First**, two `commitOrder` calls append `"OrderPlaced:order-1"` at position `0` and `"OrderPlaced:order-2"` at position `1` to `transactionLog`.

**Next**, `tailFrom("relay-1")` runs for the first time. `persistedTailerPosition.getOrDefault("relay-1", 0L)` returns `0L`, since nothing has been persisted yet. The loop runs from `pos=0` to `pos=1`: at `pos=0` it processes `order-1`'s entry and immediately checkpoints `persistedTailerPosition.put("relay-1", 1)`; at `pos=1` it processes `order-2`'s entry and checkpoints to `2`.

**Then**, the program prints a message marking a simulated crash, and `commitOrder("order-3")` runs, appending a third entry at position `2` — this happens while, conceptually, `relay-1` was down and not tailing.

**Finally**, `tailFrom("relay-1")` runs again, representing the relay restarting. `persistedTailerPosition.getOrDefault("relay-1", 0L)` now returns `2` (from the earlier checkpoint), so the loop starts at `pos=2` — it processes only `order-3`'s entry and checkpoints to `3`. Neither `order-1` nor `order-2` is reprocessed, because the persisted position correctly remembered exactly how far this tailer had gotten before it went down.

```
commitOrder(order-1) @ pos 0    commitOrder(order-2) @ pos 1
tailFrom(relay-1) 1st run  -> resume@0 -> process pos 0,1 -> checkpoint=2
[relay-1 CRASHES]
commitOrder(order-3) @ pos 2   (while relay-1 was down)
tailFrom(relay-1) 2nd run  -> resume@2 -> process pos 2 ONLY -> checkpoint=3
```

## 7. Gotchas & takeaways

> Tailing a transaction log ties the relay to that specific database engine's log format — a MySQL binlog reader can't tail a Postgres write-ahead log. This is real added operational complexity compared to polling, which is why polling remains a perfectly reasonable choice for lower-throughput services that don't need the lower latency.

- Log tailing reads the database's own durable commit log directly, giving near-real-time change detection with no added query load on the source tables, unlike polling.
- A tailer must persist its exact log position and checkpoint it as it processes entries, so a crash resumes correctly without reprocessing or skipping.
- This mechanism is the foundation of [Change Data Capture (CDC)](0333-change-data-capture-cdc.md) tools, and is one of the two common ways to implement the relay side of the [transactional outbox pattern](0331-transactional-outbox-pattern.md), the other being the simpler [polling publisher](0334-polling-publisher-pattern.md).
- It requires database-specific tooling (e.g., Debezium) that understands the exact log format, trading operational complexity for lower latency and load.
