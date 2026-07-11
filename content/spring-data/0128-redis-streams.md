---
card: spring-data
gi: 128
slug: redis-streams
title: "Redis Streams"
---

## 1. What it is

A **Redis Stream** is an append-only log of messages, each with a unique, ordered ID, that Redis persists — unlike pub/sub, a consumer that connects late can still read everything published before it arrived. Spring Data Redis exposes streams through `opsForStream()` for producing and `StreamMessageListenerContainer` for consuming, including **consumer groups**, which let multiple consumers split the work of processing a stream without duplicating it.

```java
RecordId id = redisTemplate.opsForStream().add("order-events", Map.of("orderId", "1", "status", "SHIPPED"));

List<MapRecord<String, Object, Object>> messages =
    redisTemplate.opsForStream().read(StreamOffset.fromStart("order-events"));
```

## 2. Why & when

The previous card's pub/sub is fast and simple but loses any message published with no subscriber connected. A Redis Stream solves exactly that gap: every message is appended to a durable, ordered log, so a consumer can read from any point — from the very beginning, from where it last left off, or only new messages going forward — regardless of whether it was "listening" at publish time.

Reach for Redis Streams when:

- Messages must not be lost if a consumer is temporarily down — a stream retains its history until explicitly trimmed, unlike pub/sub's fire-and-forget delivery.
- Multiple consumer *instances* need to split the processing load of one stream without each one seeing every message — a **consumer group** hands each message to exactly one member of the group, load-balancing automatically.
- You want an ordered, replayable event log for something lighter-weight than a full message broker (Kafka, RabbitMQ) but sturdier than pub/sub — an order's event history, an audit trail, a work queue with acknowledgment.

## 3. Core concept

```
 opsForStream().add("order-events", {orderId: "1", status: "CREATED"})   -> id 1-0
 opsForStream().add("order-events", {orderId: "1", status: "PACKED"})    -> id 2-0
 opsForStream().add("order-events", {orderId: "1", status: "SHIPPED"})   -> id 3-0

 Consumer group "shippers" with members A and B:
   XREADGROUP shippers A -> gets id 1-0 (and ONLY 1-0 -- not seen by B)
   XREADGROUP shippers B -> gets id 2-0 (and ONLY 2-0 -- not seen by A)
   -- the group divides work; a plain (non-group) read would give EVERY message to EVERY reader instead
```

Every message has a durable, ordered ID; a consumer group ensures each message is delivered to exactly one group member, splitting throughput across however many consumers are running.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three messages appended to a stream are split between two consumer group members, each getting a different subset">
  <rect x="20" y="20" width="600" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">stream "order-events": [1-0 CREATED] [2-0 PACKED] [3-0 SHIPPED]</text>

  <rect x="60" y="100" width="220" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="170" y="122" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Consumer A (group: shippers)</text>
  <text x="170" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">receives: 1-0, 3-0</text>

  <rect x="360" y="100" width="220" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="122" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Consumer B (group: shippers)</text>
  <text x="470" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">receives: 2-0</text>

  <line x1="150" y1="65" x2="170" y2="95" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>
  <line x1="490" y1="65" x2="470" y2="95" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Each message in the stream is delivered to exactly one consumer group member — the group divides the log, it doesn't duplicate it.

## 5. Runnable example

The scenario: order events flowing through a durable stream, evolving from a basic append-and-read stream, to a consumer that resumes reading from where it left off after a restart, to a consumer group splitting work across two workers with per-message acknowledgment.

### Level 1 — Basic

Model appending to and reading a stream from the beginning — the durable-log behavior pub/sub lacks.

```java
import java.util.*;

public class RedisStreamsLevel1 {
    public static void main(String[] args) {
        RedisStream stream = new RedisStream();

        stream.add(Map.of("orderId", "1", "status", "CREATED"));
        stream.add(Map.of("orderId", "1", "status", "PACKED"));
        stream.add(Map.of("orderId", "1", "status", "SHIPPED"));

        // A consumer that "connects late" -- unlike pub/sub, it can still read everything.
        List<StreamMessage> allMessages = stream.readFromStart();
        System.out.println("Late-connecting consumer still sees all " + allMessages.size() + " messages:");
        for (StreamMessage m : allMessages) System.out.println("  " + m.id + " -> " + m.fields);
    }
}

class StreamMessage { String id; Map<String, String> fields; StreamMessage(String id, Map<String, String> fields) { this.id = id; this.fields = fields; } }

// Stands in for redisTemplate.opsForStream() -- an append-only, ordered, PERSISTED log.
class RedisStream {
    private final List<StreamMessage> log = new ArrayList<>();
    private long nextId = 1;

    String add(Map<String, String> fields) {
        String id = nextId++ + "-0"; // mirrors Redis's <timestamp>-<sequence> stream IDs, simplified here
        log.add(new StreamMessage(id, fields));
        return id;
    }
    List<StreamMessage> readFromStart() { return new ArrayList<>(log); } // XRANGE - $
}
```

How to run: `java RedisStreamsLevel1.java`

`add` mirrors `XADD order-events '*' orderId 1 status CREATED`, appending a durably-ordered entry with its own generated ID. `readFromStart` mirrors reading the stream from its earliest entry (`XRANGE order-events - +`) — crucially, this "consumer" never subscribed before any message was added, and yet it still sees every one of them, which is exactly the durability pub/sub does not provide.

### Level 2 — Intermediate

Track a **read offset** so a consumer resumes exactly where it left off — even after an application restart — rather than re-reading from the start or missing anything published in between.

```java
import java.util.*;

public class RedisStreamsLevel2 {
    public static void main(String[] args) {
        RedisStream stream = new RedisStream();
        stream.add(Map.of("orderId", "1", "status", "CREATED"));  // id 1-0
        stream.add(Map.of("orderId", "1", "status", "PACKED"));   // id 2-0

        String lastSeenId = null;
        List<StreamMessage> firstBatch = stream.readAfter(lastSeenId);
        System.out.println("First read: " + firstBatch.size() + " message(s)");
        lastSeenId = firstBatch.get(firstBatch.size() - 1).id; // save the offset -- this is what survives a restart

        System.out.println("--- consumer restarts, resumes from offset " + lastSeenId + " ---");
        stream.add(Map.of("orderId", "1", "status", "SHIPPED")); // arrives WHILE consumer was down

        List<StreamMessage> secondBatch = stream.readAfter(lastSeenId);
        System.out.println("Second read (after restart): " + secondBatch.size() + " message(s)");
        for (StreamMessage m : secondBatch) System.out.println("  " + m.id + " -> " + m.fields);
    }
}

class StreamMessage { String id; Map<String, String> fields; StreamMessage(String id, Map<String, String> fields) { this.id = id; this.fields = fields; } }

class RedisStream {
    private final List<StreamMessage> log = new ArrayList<>();
    private long nextId = 1;
    String add(Map<String, String> fields) { String id = nextId++ + "-0"; log.add(new StreamMessage(id, fields)); return id; }

    // Mirrors XREAD STREAMS order-events <lastSeenId> -- only entries AFTER lastSeenId.
    List<StreamMessage> readAfter(String lastSeenId) {
        List<StreamMessage> result = new ArrayList<>();
        boolean pastLastSeen = (lastSeenId == null);
        for (StreamMessage m : log) {
            if (pastLastSeen) result.add(m);
            else if (m.id.equals(lastSeenId)) pastLastSeen = true; // found it -- everything AFTER this counts
        }
        return result;
    }
}
```

How to run: `java RedisStreamsLevel2.java`

`readAfter(lastSeenId)` walks the log and only starts collecting once it passes the message matching `lastSeenId`, mirroring `XREAD STREAMS order-events <lastSeenId>`. The consumer saves its offset after the first read, "restarts," and a new message arrives while it's down; on resuming with the saved offset, it correctly picks up only the message it hadn't seen yet — no duplicates, no gaps.

### Level 3 — Advanced

Model a consumer **group**: two workers split the stream's messages between them, with each message acknowledged after successful processing — matching `XREADGROUP`/`XACK`, the pattern for reliably distributing work across multiple consumer instances.

```java
import java.util.*;

public class RedisStreamsLevel3 {
    public static void main(String[] args) {
        RedisStream stream = new RedisStream();
        stream.add(Map.of("orderId", "1", "status", "CREATED"));
        stream.add(Map.of("orderId", "2", "status", "CREATED"));
        stream.add(Map.of("orderId", "3", "status", "CREATED"));

        System.out.println("Two consumers, same group, pulling from the SAME stream:");
        StreamMessage forA = stream.readGroupNext("consumer-A");
        StreamMessage forB = stream.readGroupNext("consumer-B");
        StreamMessage forA2 = stream.readGroupNext("consumer-A"); // asks again -- gets the NEXT undelivered one

        System.out.println("Pending (unacknowledged) before any ack: " + stream.pendingCount());

        stream.ack(forA.id); stream.ack(forB.id); stream.ack(forA2.id);
        System.out.println("Pending (unacknowledged) after all acked: " + stream.pendingCount());
    }
}

class StreamMessage { String id; Map<String, String> fields; StreamMessage(String id, Map<String, String> fields) { this.id = id; this.fields = fields; } }

class RedisStream {
    private final List<StreamMessage> log = new ArrayList<>();
    private long nextId = 1;
    private int nextUndeliveredIndex = 0; // tracks which messages this group hasn't yet HANDED OUT to some consumer
    private final Set<String> pendingAck = new LinkedHashSet<>(); // delivered but not yet acknowledged

    String add(Map<String, String> fields) { String id = nextId++ + "-0"; log.add(new StreamMessage(id, fields)); return id; }

    // Mirrors XREADGROUP GROUP shippers <consumerName> COUNT 1 STREAMS order-events '>'
    // -- hands out the NEXT undelivered message to WHICHEVER consumer asks, round-robin by arrival order.
    StreamMessage readGroupNext(String consumerName) {
        if (nextUndeliveredIndex >= log.size()) return null; // nothing new for the group right now
        StreamMessage m = log.get(nextUndeliveredIndex++);
        pendingAck.add(m.id);
        System.out.println("  delivered " + m.id + " to consumer " + consumerName);
        return m;
    }

    void ack(String messageId) { pendingAck.remove(messageId); } // XACK order-events shippers <id>
    int pendingCount() { return pendingAck.size(); }
}
```

How to run: `java RedisStreamsLevel3.java`

`readGroupNext` hands out each message exactly once, in order, to whichever consumer asks next — `consumer-A` gets message `1-0`, `consumer-B` gets `2-0`, and `consumer-A`'s second call gets `3-0`, since `2-0` was already claimed by `consumer-B`. This is the essential consumer-group behavior: the three messages are split *between* the two consumers, not duplicated to both. Each delivered message stays in `pendingAck` until explicitly acknowledged with `ack`, mirroring Redis's "pending entries list" — a message a consumer crashes before acknowledging stays claimable by another consumer via `XCLAIM`, so work is never silently dropped.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three messages are appended for orders `1`, `2`, and `3`, getting stream IDs `1-0`, `2-0`, `3-0`.

`stream.readGroupNext("consumer-A")` checks `nextUndeliveredIndex` (starts at `0`), takes `log.get(0)` (message `1-0`), increments `nextUndeliveredIndex` to `1`, adds `1-0` to `pendingAck`, and returns it. `stream.readGroupNext("consumer-B")` does the same for index `1` (message `2-0`), advancing `nextUndeliveredIndex` to `2`. `stream.readGroupNext("consumer-A")` again takes index `2` (message `3-0`), advancing `nextUndeliveredIndex` to `3`.

At this point `pendingAck` contains all three message IDs — none have been acknowledged yet — so `stream.pendingCount()` returns `3`. The three `stream.ack(...)` calls each remove one ID from `pendingAck`; after all three, `pendingCount()` returns `0`.

```
Two consumers, same group, pulling from the SAME stream:
  delivered 1-0 to consumer consumer-A
  delivered 2-0 to consumer consumer-B
  delivered 3-0 to consumer consumer-A
Pending (unacknowledged) before any ack: 3
Pending (unacknowledged) after all acked: 0
```

In real Redis, `XREADGROUP GROUP shippers consumer-A COUNT 1 STREAMS order-events >` claims the next undelivered message for `consumer-A` specifically and adds it to that group's Pending Entries List (PEL); `XACK order-events shippers 1-0` removes it from the PEL once processing succeeds. If `consumer-A` crashed before acknowledging `1-0`, the message would remain in the PEL, claimable by another consumer via `XCLAIM` after an idle-time threshold — this is exactly how Redis Streams guarantees at-least-once delivery even when individual consumers fail mid-processing, something plain pub/sub has no mechanism for at all.

## 7. Gotchas & takeaways

> Gotcha: a stream grows unboundedly unless explicitly trimmed (`XTRIM`, or `MAXLEN` on `XADD`) — unlike pub/sub, which stores nothing, a stream retains every message forever by default, which can become a real memory problem for a high-volume stream with no retention policy.

> Gotcha: a message delivered to a consumer group member but never acknowledged (because the consumer crashed) sits in that group's Pending Entries List indefinitely unless something explicitly reclaims it via `XCLAIM` — a monitoring/reclaim strategy is necessary for genuinely reliable processing, not just the read/ack pair shown here.

- Redis Streams persist an ordered, append-only log of messages, so a consumer connecting after messages were published can still read all of them — the key difference from pub/sub.
- A plain stream read delivers every message to every reader; a **consumer group** instead splits messages across group members, so each message is handled by exactly one consumer in the group.
- Consumers acknowledge (`XACK`) messages after successful processing; unacknowledged messages remain reclaimable, giving at-least-once delivery even across consumer crashes.
- Streams need explicit trimming (`XTRIM`/`MAXLEN`) to bound their growth — nothing evicts old entries automatically the way a TTL does for a `@RedisHash` entity.
