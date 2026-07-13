---
card: microservices
gi: 334
slug: polling-publisher-pattern
title: "Polling publisher pattern"
---

## 1. What it is

The **polling publisher pattern** is the simplest way to implement the relay side of the [transactional outbox pattern](0331-transactional-outbox-pattern.md): a process periodically queries the outbox table for unsent rows (`SELECT * FROM outbox WHERE sent = false ORDER BY id`), publishes each one to the message broker, and marks it sent — all on a fixed schedule, using nothing more exotic than an ordinary database query and a scheduler.

## 2. Why & when

Compared to [transaction log tailing](0332-transaction-log-tailing.md) / [CDC](0333-change-data-capture-cdc.md), polling trades some latency and database load for dramatically less operational complexity — it needs no database-specific log-reading tool, no replication-client setup, nothing beyond code your team already knows how to write and operate: a query, a loop, a scheduler. For services with moderate event volume and no strict requirement for sub-second propagation, this simplicity usually outweighs the cost.

Use polling as the default choice for implementing an outbox relay, especially early on or for lower-throughput services, and reach for log tailing/CDC only once polling's latency (bounded by the poll interval) or its added query load on the database becomes a measured, real problem — not preemptively.

## 3. Core concept

On a fixed interval, the poller queries for unsent outbox rows in a stable order (usually by an auto-incrementing ID or timestamp, so nothing is skipped or reordered), publishes each to the broker, and marks it sent — typically in the same transaction as the publish confirmation, or immediately after, so a crash between publish and mark-sent results in, at worst, a harmless duplicate delivery (which idempotent consumers already tolerate).

```java
// Runs every N seconds:
List<OutboxRow> unsent = outboxRepository.findBySentFalseOrderById();
for (OutboxRow row : unsent) { broker.publish(row.payload()); outboxRepository.markSent(row.id()); }
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A scheduler triggers a poll every fixed interval; each poll queries the outbox table for unsent rows, publishes them, and marks them sent">
  <rect x="20" y="60" width="130" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Scheduler (every 2s)</text>

  <line x1="150" y1="77" x2="220" y2="77" stroke="#8b949e" marker-end="url(#a334)"/>
  <rect x="230" y="60" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="305" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Query unsent outbox rows</text>

  <line x1="380" y1="77" x2="450" y2="77" stroke="#8b949e" marker-end="url(#a334)"/>
  <rect x="460" y="60" width="160" height="34" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="540" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Publish + mark sent</text>

  <text x="320" y="140" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Simple, but every cycle costs a query, and nothing is noticed BETWEEN polls.</text>

  <defs><marker id="a334" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A fixed-interval loop queries, publishes, and marks each outbox row sent — simple, at the cost of a bounded but real delay.

## 5. Runnable example

Scenario: an outbox poller that starts out naively re-querying and republishing every row on each cycle, then fixed to track the last-seen ID so it only processes new rows, and finally extended to back off its polling interval when the outbox is empty, saving query load during quiet periods.

### Level 1 — Basic

```java
// File: NaivePollerReprocesses.java -- BUG: queries and republishes the
// WHOLE outbox table every cycle, not just new rows.
import java.util.*;

public class NaivePollerReprocesses {
    static List<String> outboxTable = new ArrayList<>();

    static void pollAndPublish() { // WRONG: no memory of what was already published
        System.out.println("poll: querying ENTIRE outbox table...");
        for (String row : outboxTable) System.out.println("  publishing (again!): " + row);
    }

    public static void main(String[] args) {
        outboxTable.add("OrderPlaced:order-1");
        pollAndPublish(); // publishes order-1

        outboxTable.add("OrderPlaced:order-2");
        pollAndPublish(); // publishes order-1 AGAIN, plus order-2 -- order-1 is now a DUPLICATE publish
    }
}
```

How to run: `java NaivePollerReprocesses.java`

`pollAndPublish` has no memory of which rows were already published, so every cycle republishes the entire table from scratch — `order-1` gets published twice purely because the poller ran twice, which is unnecessary broker load even if downstream idempotency happens to absorb the duplicate.

### Level 2 — Intermediate

```java
// File: PollerTracksLastSeen.java -- FIXED: tracks the last processed
// row's ID and only queries/publishes rows AFTER it each cycle.
import java.util.*;

public class PollerTracksLastSeen {
    record OutboxRow(int id, String payload) {}
    static List<OutboxRow> outboxTable = new ArrayList<>();
    static int lastPublishedId = -1; // persisted in a real system, alongside the marking-sent step

    static void pollAndPublish() {
        System.out.println("poll: querying rows with id > " + lastPublishedId + "...");
        for (OutboxRow row : outboxTable) {
            if (row.id() <= lastPublishedId) continue; // already published, SKIP
            System.out.println("  publishing: " + row.payload());
            lastPublishedId = row.id();
        }
    }

    public static void main(String[] args) {
        outboxTable.add(new OutboxRow(1, "OrderPlaced:order-1"));
        pollAndPublish();

        outboxTable.add(new OutboxRow(2, "OrderPlaced:order-2"));
        pollAndPublish(); // only order-2 is published this time -- order-1 correctly skipped
    }
}
```

How to run: `java PollerTracksLastSeen.java`

`lastPublishedId` remembers the highest ID processed so far. The second `pollAndPublish` call skips row `1` (already published) and publishes only row `2` — the fix is simply querying and tracking "what's new since last time" instead of reprocessing everything on every cycle.

### Level 3 — Advanced

```java
// File: PollerWithBackoff.java -- extends the tracked-position poller
// with ADAPTIVE polling: the interval grows when the outbox is empty
// (saving query load during quiet periods) and resets to the fast
// interval the moment new rows are found.
import java.util.*;

public class PollerWithBackoff {
    record OutboxRow(int id, String payload) {}
    static List<OutboxRow> outboxTable = new ArrayList<>();
    static int lastPublishedId = -1;
    static int currentIntervalMs = 100; // fast baseline
    static final int MAX_INTERVAL_MS = 800;

    static boolean pollAndPublish() { // returns true if anything new was found
        boolean foundNew = false;
        for (OutboxRow row : outboxTable) {
            if (row.id() <= lastPublishedId) continue;
            System.out.println("  publishing: " + row.payload());
            lastPublishedId = row.id();
            foundNew = true;
        }
        return foundNew;
    }

    static void runCycle() {
        System.out.println("poll cycle (interval=" + currentIntervalMs + "ms)...");
        boolean foundNew = pollAndPublish();
        if (foundNew) {
            currentIntervalMs = 100; // reset to fast polling -- activity means more might be coming soon
            System.out.println("  found new rows -- interval reset to " + currentIntervalMs + "ms");
        } else {
            currentIntervalMs = Math.min(currentIntervalMs * 2, MAX_INTERVAL_MS); // back off -- quiet outbox, poll less often
            System.out.println("  outbox empty -- backing off to " + currentIntervalMs + "ms");
        }
    }

    public static void main(String[] args) {
        outboxTable.add(new OutboxRow(1, "OrderPlaced:order-1"));
        runCycle(); // finds order-1, stays fast

        runCycle(); // nothing new -- backs off
        runCycle(); // still nothing -- backs off further

        outboxTable.add(new OutboxRow(2, "OrderPlaced:order-2"));
        runCycle(); // finds order-2 -- resets back to fast
    }
}
```

How to run: `java PollerWithBackoff.java`

The first `runCycle` finds `order-1` (`foundNew=true`), so `currentIntervalMs` stays reset at `100`. The next two cycles find nothing new (`foundNew=false` each time), so `currentIntervalMs` doubles each time: `100 -> 200 -> 400`. When `order-2` is then added and a fourth cycle runs, it finds new work again and resets `currentIntervalMs` straight back to `100` — during busy periods the poller stays responsive (short interval), and during quiet periods it backs off automatically, reducing needless queries against an empty outbox.

## 6. Walkthrough

Trace `PollerWithBackoff.main` in order. **First**, `outboxTable` gets one row (`id=1`), and `runCycle()` runs: `pollAndPublish` finds `row.id()=1 > lastPublishedId=-1`, publishes it, updates `lastPublishedId` to `1`, and returns `true`. Back in `runCycle`, `foundNew` is `true`, so `currentIntervalMs` is reset to `100`.

**Next**, `runCycle()` runs again with no new rows added. `pollAndPublish` iterates `outboxTable`, finds only `row.id()=1`, which is not greater than `lastPublishedId=1`, so it's skipped — the method returns `false`. Back in `runCycle`, the `else` branch doubles `currentIntervalMs` from `100` to `200`.

**Then**, `runCycle()` runs a third time, again with no new rows. The same skip happens, `foundNew` is `false` again, and `currentIntervalMs` doubles again, from `200` to `400`.

**Finally**, a new row (`id=2`) is added, and `runCycle()` runs a fourth time. This time `pollAndPublish` finds `row.id()=2 > lastPublishedId=1`, publishes it, updates `lastPublishedId` to `2`, and returns `true` — `runCycle` resets `currentIntervalMs` straight back down to `100`, ready to respond quickly if more activity follows.

```
runCycle #1: order-1 found       -> interval reset to 100ms
runCycle #2: nothing found       -> interval backs off to 200ms
runCycle #3: nothing found       -> interval backs off to 400ms
runCycle #4: order-2 found       -> interval reset to 100ms
```

## 7. Gotchas & takeaways

> A poller that queries `SELECT * FROM outbox WHERE sent = false` without an index on `sent` (or on the ID/timestamp used for ordering) will do a full table scan every cycle as the outbox grows — index the column the poller filters and orders by, just as you would for any frequently-run query.

- Polling is the simplest way to implement an outbox relay: a scheduled query, publish, and mark-sent loop, needing no database-specific tooling.
- Track the last-processed position (an ID or timestamp) so each poll only queries and republishes genuinely new rows.
- An adaptive polling interval (fast when busy, backing off when idle) reduces needless database load during quiet periods without sacrificing responsiveness during busy ones.
- Reach for [transaction log tailing](0332-transaction-log-tailing.md) / [CDC](0333-change-data-capture-cdc.md) only once polling's latency or query load becomes a measured problem — it is not the default starting point.
