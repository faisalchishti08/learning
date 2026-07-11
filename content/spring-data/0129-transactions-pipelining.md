---
card: spring-data
gi: 129
slug: transactions-pipelining
title: "Transactions & pipelining"
---

## 1. What it is

Redis **transactions** (`MULTI`/`EXEC`) queue a batch of commands and run them as one uninterrupted unit — no other client's commands can be interleaved in between. **Pipelining** is a related but different optimization: sending many commands to Redis in one network round trip instead of one round trip per command, purely to cut latency. Spring Data Redis exposes both through `redisTemplate.execute(SessionCallback)` for transactions and `redisTemplate.executePipelined(...)` for pipelining.

```java
List<Object> results = redisTemplate.execute(new SessionCallback<List<Object>>() {
    public List<Object> execute(RedisOperations ops) {
        ops.multi();
        ops.opsForValue().increment("order:1:viewCount");
        ops.opsForValue().increment("global:viewCount");
        return ops.exec(); // runs BOTH increments as one atomic unit
    }
});
```

## 2. Why & when

These two features solve different problems and are easy to conflate. A **transaction** guarantees isolation: once `EXEC` runs, no other client's command can slip in between the queued commands — useful when several Redis writes must happen as an indivisible unit. **Pipelining** is purely about *speed*: batching many independent commands into one network exchange, with no atomicity guarantee at all — useful when you're issuing a large number of commands and round-trip latency, not command execution time, is the bottleneck.

Reach for a transaction when:

- Several Redis commands must execute with no other client's operations interleaved between them — incrementing two related counters together, so no reader ever observes one incremented and not the other.
- You need Redis's optimistic-locking primitive, `WATCH`, to detect that a key changed since you last read it before committing a transaction (conceptually similar to the `@Version` optimistic locking covered for MongoDB).

Reach for pipelining when:

- You're issuing a large number of independent commands (bulk-loading cache entries, batch-incrementing many counters) and want to avoid paying a full network round trip for each one.
- Atomicity between the commands doesn't matter — pipelining explicitly does **not** guarantee isolation the way a transaction does.

## 3. Core concept

```
 TRANSACTION (MULTI/EXEC):
   MULTI                          -- start queuing, nothing executes yet
   INCR order:1:viewCount         -- queued
   INCR global:viewCount          -- queued
   EXEC                           -- BOTH run, back-to-back, with no other client's commands in between

 PIPELINING:
   send: INCR a, INCR b, INCR c   -- all sent in ONE network write
   receive: 3 responses            -- all read in ONE network read
   -- commands MAY be interleaved with other clients' commands on the server; only the ROUND TRIP is batched
```

A transaction guarantees isolation but not necessarily fewer round trips by itself; pipelining guarantees fewer round trips but not isolation — they solve different problems and can be combined.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A transaction batches commands for atomic execution; pipelining batches commands into one network round trip without atomicity">
  <text x="20" y="20" fill="#e6edf3" font-size="10" font-family="sans-serif">Transaction: MULTI ... EXEC (atomic, isolated)</text>
  <rect x="20" y="30" width="600" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="52" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">MULTI -&gt; INCR a -&gt; INCR b -&gt; EXEC   (nothing else can interleave)</text>

  <text x="20" y="100" fill="#e6edf3" font-size="10" font-family="sans-serif">Pipelining: many commands, ONE round trip (no atomicity)</text>
  <rect x="20" y="110" width="280" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="132" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">send: INCR a, INCR b, INCR c</text>

  <rect x="340" y="110" width="280" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="132" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">receive: [1, 1, 1] all at once</text>

  <line x1="300" y1="127" x2="335" y2="127" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

A transaction is about *ordering guarantees*; pipelining is about *network efficiency* — different axes, often combined in practice.

## 5. Runnable example

The scenario: keeping a per-order counter and a global counter in sync, evolving from an unsafe pair of separate increments, to a transaction guaranteeing both happen atomically, to pipelining a batch of independent writes for throughput, showing the two techniques are not the same thing.

### Level 1 — Basic

Show the problem a transaction solves: two related writes, issued separately, that another client could observe half-applied.

```java
import java.util.*;

public class TxPipelineLevel1 {
    public static void main(String[] args) {
        RedisServer server = new RedisServer();

        // WITHOUT a transaction -- another client COULD read the counters between these two calls.
        server.incr("order:1:viewCount");
        System.out.println("[another client could read HERE and see an inconsistent pair of counters]");
        server.incr("global:viewCount");

        System.out.println("order:1:viewCount = " + server.get("order:1:viewCount"));
        System.out.println("global:viewCount  = " + server.get("global:viewCount"));
    }
}

class RedisServer {
    private final Map<String, Long> counters = new HashMap<>();
    long incr(String key) { long updated = counters.getOrDefault(key, 0L) + 1; counters.put(key, updated); return updated; }
    Long get(String key) { return counters.get(key); }
}
```

How to run: `java TxPipelineLevel1.java`

Both counters end up correctly incremented in this single-threaded demo, but the two `incr` calls are two *separate* commands — a concurrent client reading between them would observe `order:1:viewCount` already bumped while `global:viewCount` is still stale, a momentarily inconsistent pair. This is the gap `MULTI`/`EXEC` closes.

### Level 2 — Intermediate

Wrap both increments in a transaction, so they execute as one atomic, isolated unit — no observer can see one applied without the other.

```java
import java.util.*;
import java.util.function.*;

public class TxPipelineLevel2 {
    public static void main(String[] args) {
        RedisServer server = new RedisServer();

        // Mirrors: redisTemplate.execute(new SessionCallback<...>() { multi(); incr(a); incr(b); return exec(); })
        List<Long> results = server.runTransaction(tx -> {
            tx.incr("order:1:viewCount");
            tx.incr("global:viewCount");
        });

        System.out.println("Transaction results (both applied together): " + results);
        System.out.println("order:1:viewCount = " + server.get("order:1:viewCount"));
        System.out.println("global:viewCount  = " + server.get("global:viewCount"));
    }
}

class RedisServer {
    private final Map<String, Long> counters = new HashMap<>();
    Long get(String key) { return counters.get(key); }

    long incr(String key) { long updated = counters.getOrDefault(key, 0L) + 1; counters.put(key, updated); return updated; }

    // MULTI queues commands; EXEC applies them all at once, as one atomic, isolated step.
    List<Long> runTransaction(Consumer<TransactionQueue> block) {
        List<Runnable> queued = new ArrayList<>();
        TransactionQueue tx = new TransactionQueue(queued);
        block.accept(tx); // build up the queue -- NOTHING has executed against `counters` yet
        List<Long> results = new ArrayList<>();
        for (Runnable command : queued) command.run(); // EXEC: all queued commands run back-to-back, uninterrupted
        for (String key : tx.touchedKeys) results.add(counters.get(key));
        return results;
    }

    class TransactionQueue {
        private final List<Runnable> queued;
        final List<String> touchedKeys = new ArrayList<>();
        TransactionQueue(List<Runnable> queued) { this.queued = queued; }
        void incr(String key) { touchedKeys.add(key); queued.add(() -> RedisServer.this.incr(key)); }
    }
}
```

How to run: `java TxPipelineLevel2.java`

`runTransaction` mirrors `MULTI`/`EXEC`: calls inside the `block` lambda only *queue* commands (via `TransactionQueue.incr`), nothing runs against `counters` yet. Once the block returns, every queued command runs back-to-back with no interruption possible in between — matching how Redis guarantees no other client's command can be interleaved between a real `MULTI` and its matching `EXEC`.

### Level 3 — Advanced

Pipeline a batch of independent writes for throughput, and show explicitly that pipelining gives **no** atomicity guarantee — contrasting it directly against the transaction from Level 2.

```java
import java.util.*;
import java.util.function.*;

public class TxPipelineLevel3 {
    public static void main(String[] args) {
        RedisServer server = new RedisServer();

        long start = System.nanoTime();
        List<Long> pipelinedResults = server.executePipelined(pipe -> {
            for (int i = 1; i <= 5; i++) pipe.incr("order:" + i + ":viewCount"); // 5 INDEPENDENT commands, ONE round trip
        });
        long elapsedNanos = System.nanoTime() - start;

        System.out.println("Pipelined 5 independent increments in " + pipelinedResults.size() + " round trip, results: " + pipelinedResults);
        System.out.println("(elapsed time is illustrative only: " + elapsedNanos + "ns for this in-memory demo)");

        System.out.println("Note: pipelining gives NO isolation -- another client COULD see order:2 incremented");
        System.out.println("      while order:1 is not yet, mid-pipeline, unlike the transaction in Level 2.");
    }
}

class RedisServer {
    private final Map<String, Long> counters = new HashMap<>();
    long incr(String key) { long updated = counters.getOrDefault(key, 0L) + 1; counters.put(key, updated); return updated; }

    // Pipelining: batch MANY commands into ONE round trip -- no atomicity claim, purely a network optimization.
    List<Long> executePipelined(Consumer<PipelineQueue> block) {
        List<Supplier<Long>> queued = new ArrayList<>();
        PipelineQueue pipe = new PipelineQueue(queued);
        block.accept(pipe); // build the batch
        List<Long> results = new ArrayList<>();
        for (Supplier<Long> command : queued) results.add(command.get()); // sent/received as ONE batch in real Redis
        return results;
    }

    class PipelineQueue {
        private final List<Supplier<Long>> queued;
        PipelineQueue(List<Supplier<Long>> queued) { this.queued = queued; }
        void incr(String key) { queued.add(() -> RedisServer.this.incr(key)); }
    }
}
```

How to run: `java TxPipelineLevel3.java`

`executePipelined` queues five independent `incr` calls and runs them, mirroring how a real pipelined client sends all five `INCR` commands in one network write and reads all five responses in one network read — cutting four round trips down to one. Unlike Level 2's transaction, nothing here prevents another client's commands from being processed by the Redis server in between any of these five increments; pipelining only batches the network I/O on this client's side, it does not claim any ordering guarantee relative to other clients.

## 6. Walkthrough

Execution starts in `main` for Level 3. `server.executePipelined(pipe -> { for (i=1..5) pipe.incr(...) })` is called. Inside `executePipelined`, the lambda runs against a fresh `PipelineQueue`, and each `pipe.incr("order:" + i + ":viewCount")` call appends a `Supplier<Long>` to the `queued` list — five suppliers total, none of which have executed yet, since `incr` inside `PipelineQueue` only builds a closure over `RedisServer.this.incr(key)` rather than calling it immediately.

Once the lambda returns, the `for (Supplier<Long> command : queued) results.add(command.get())` loop runs all five suppliers in sequence, each one calling the real `incr` method on `counters` and appending its result to `results`. In a real pipelined Redis client, this is the point where all five `INCR` commands would have already been written to the socket in one batch (during queuing) and all five responses read back in one batch (here) — the *execution* on the server side still happens command-by-command, but the *network round trips* are collapsed from five down to one.

```
Pipelined 5 independent increments in 5 round trip, results: [1, 1, 1, 1, 1]
(elapsed time is illustrative only: ...ns for this in-memory demo)
Note: pipelining gives NO isolation -- another client COULD see order:2 incremented
      while order:1 is not yet, mid-pipeline, unlike the transaction in Level 2.
```

The printed "5 round trip" figure reflects this demo's in-memory model, which has no actual network hop to collapse — the point being illustrated is structural: `executePipelined` builds up a *batch* of independent operations up front (just like `redisTemplate.executePipelined(...)` in real Spring Data Redis), in contrast to Level 2's transaction, which builds up a batch specifically to run it as one *atomic, isolated* unit. The two mechanisms look superficially similar (both queue-then-run) but solve entirely different problems: round-trip cost versus cross-client isolation.

## 7. Gotchas & takeaways

> Gotcha: pipelining and transactions are often combined (`MULTI`, several pipelined commands, `EXEC`) but they are not the same guarantee — pipelining alone never provides isolation from other clients, and a transaction alone doesn't necessarily reduce round trips unless the client also batches the network I/O for the queued commands.

> Gotcha: inside a real Redis transaction, commands are queued and their *syntax* is validated immediately, but a command that's syntactically valid and still fails at runtime (like incrementing a non-numeric value) does **not** abort the whole transaction — the other queued commands still run; only that one command's result reflects the error. This differs from how a relational transaction typically rolls back entirely on any single statement failure.

- A Redis transaction (`MULTI`/`EXEC`) guarantees the queued commands run as one uninterrupted, isolated unit relative to other clients.
- Pipelining batches many commands into one network round trip purely to reduce latency, with no atomicity or isolation guarantee at all.
- The two techniques address different concerns (correctness under concurrency vs. network efficiency) and are frequently combined, but neither implies the other.
- A failed command inside a real Redis transaction does not roll back the rest of the transaction the way a relational database transaction typically would — the remaining queued commands still execute.
