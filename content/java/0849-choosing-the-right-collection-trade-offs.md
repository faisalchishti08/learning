---
card: java
gi: 849
slug: choosing-the-right-collection-trade-offs
title: Choosing the right collection (trade-offs)
---

## 1. What it is

Choosing a collection implementation is a series of trade-off decisions, not a search for one universally "best" type: ordered vs. unordered, unique vs. duplicate-tolerant, sorted vs. insertion-ordered vs. unordered, indexed-access-optimized vs. end-operation-optimized, single-threaded vs. concurrent (and if concurrent, blocking vs. non-blocking, snapshot vs. weakly-consistent). Every collection covered across this section — from [`ArrayList`](0812-arraylist-internals-resizing.md) through [`ConcurrentSkipListMap`](0831-concurrentskiplistmap.md) — represents a specific point in that trade-off space, optimized for a particular access pattern at the cost of being worse at others.

## 2. Why & when

Defaulting to the same familiar collection type (usually `ArrayList` and `HashMap`) regardless of the actual access pattern works most of the time, because most workloads don't stress the specific dimension where a mismatched choice becomes expensive — but when a workload does hit that dimension (frequent front-insertion on a large `ArrayList`, indexed access on a large `LinkedList`, uniqueness-checking on a large `List` instead of a `Set`), the cost is often O(n) or O(n²) where the right choice would have been O(1) or O(log n). Having a clear mental model of the trade-off space — organized by the actual questions to ask about a workload — turns collection selection from guesswork or habit into a deliberate, justifiable engineering decision made once, up front, rather than a performance bug discovered later under load.

## 3. Core concept

```
Question: does order matter?
  No           -> HashSet / HashMap (fastest, no ordering overhead)
  Insertion    -> LinkedHashSet / LinkedHashMap
  Sorted       -> TreeSet / TreeMap (or a List, sorted once, if rarely re-queried)

Question: are duplicates allowed?
  Yes          -> List
  No           -> Set

Question: what's the dominant access pattern?
  Indexed random access      -> ArrayList
  Insert/remove at both ends -> ArrayDeque
  Insert/remove in the middle frequently, via iterator -> LinkedList
  Priority-ordered removal   -> PriorityQueue

Question: is this shared across threads?
  No                                    -> plain (HashMap, ArrayList, etc.)
  Yes, read-heavy/write-light           -> CopyOnWriteArrayList / CopyOnWriteArraySet
  Yes, frequent reads AND writes        -> ConcurrentHashMap / ConcurrentSkipListMap
  Yes, producer-consumer, should block  -> a BlockingQueue implementation
  Yes, producer-consumer, non-blocking  -> ConcurrentLinkedQueue/Deque
```

Each answer down these branches points toward a specific implementation this section covered in depth — the questions themselves are the reusable part; the answers are just a lookup once the workload's actual shape is known.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A decision flow for choosing a collection: first decide if order matters, then duplicates, then the dominant access pattern, then thread-safety needs">
  <g font-family="sans-serif">
    <rect x="240" y="10" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
    <text x="320" y="32" fill="#e6edf3" font-size="10" text-anchor="middle">Does order matter?</text>

    <line x1="290" y1="45" x2="140" y2="75" stroke="#8b949e" marker-end="url(#a849)"/>
    <line x1="350" y1="45" x2="500" y2="75" stroke="#8b949e" marker-end="url(#a849)"/>

    <rect x="40" y="80" width="200" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
    <text x="140" y="102" fill="#e6edf3" font-size="9" text-anchor="middle">No -&gt; HashSet/HashMap</text>

    <rect x="400" y="80" width="200" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
    <text x="500" y="102" fill="#e6edf3" font-size="9" text-anchor="middle">Yes -&gt; Linked* or Tree*</text>

    <rect x="240" y="130" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
    <text x="320" y="152" fill="#e6edf3" font-size="10" text-anchor="middle">Duplicates allowed?</text>

    <line x1="320" y1="165" x2="320" y2="195" stroke="#8b949e" marker-end="url(#a849)"/>

    <rect x="220" y="195" width="200" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="320" y="215" fill="#e6edf3" font-size="9" text-anchor="middle">List (dup) vs Set (unique)</text>
  </g>
  <defs><marker id="a849" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*A short sequence of concrete questions narrows the trade-off space down to a specific, justified choice.*

## 5. Runnable example

Scenario: designing the data layer for a live chat application — message history, unique online-user tracking, and a moderation task queue — growing from a naive one-size-fits-all implementation, to correctly matched choices per access pattern, to a benchmark proving the corrected choices actually matter under realistic load.

### Level 1 — Basic

```java
import java.util.*;

public class ChatAppNaive {
    public static void main(String[] args) {
        // Naive: everything is an ArrayList, regardless of actual access pattern.
        List<String> messageHistory = new ArrayList<>();
        List<String> onlineUsers = new ArrayList<>(); // should be a Set -- duplicates shouldn't be possible
        List<String> moderationQueue = new ArrayList<>(); // should be a Queue -- FIFO processing intended

        messageHistory.add("alice: hello!");
        onlineUsers.add("alice");
        onlineUsers.add("alice"); // BUG: "alice" can appear twice, since List allows duplicates
        moderationQueue.add("flagged-message-1");

        System.out.println("online users (has an accidental duplicate!): " + onlineUsers);
        System.out.println("is 'alice' online, checked the slow way: " + onlineUsers.contains("alice"));
    }
}
```

**How to run:** `java ChatAppNaive.java` (JDK 17+).

Expected output:
```
online users (has an accidental duplicate!): [alice, alice]
is 'alice' online, checked the slow way: true
```

Using a `List` for "online users" allows the exact bug a `Set` would prevent entirely — a duplicate entry, and `contains` here is an O(n) linear scan instead of a `HashSet`'s O(1) average lookup.

### Level 2 — Intermediate

```java
import java.util.*;

public class ChatAppMatched {
    public static void main(String[] args) {
        // Matched: each structure chosen for its actual access pattern.
        List<String> messageHistory = new ArrayList<>();       // append-only, occasionally read by index -- ArrayList fits
        Set<String> onlineUsers = new HashSet<>();               // uniqueness matters, no order needed -- HashSet fits
        Queue<String> moderationQueue = new ArrayDeque<>();       // strict FIFO processing -- ArrayDeque fits

        messageHistory.add("alice: hello!");
        messageHistory.add("bob: hi alice!");

        onlineUsers.add("alice");
        boolean stillNew = onlineUsers.add("alice"); // correctly rejected as a duplicate
        System.out.println("re-adding 'alice' reported new: " + stillNew);
        System.out.println("online users (no duplicate possible): " + onlineUsers);

        moderationQueue.offer("flagged-message-1");
        moderationQueue.offer("flagged-message-2");
        System.out.println("processing moderation queue in order:");
        while (!moderationQueue.isEmpty()) {
            System.out.println("  " + moderationQueue.poll());
        }
    }
}
```

**How to run:** `java ChatAppMatched.java`.

Expected output:
```
re-adding 'alice' reported new: false
online users (no duplicate possible): [alice]
processing moderation queue in order:
  flagged-message-1
  flagged-message-2
```

The real-world concern added: each collection now matches its actual semantic requirement — `onlineUsers` as a `Set` makes the duplicate bug structurally impossible rather than something that must be manually guarded against, and `moderationQueue` as an `ArrayDeque`-backed `Queue` communicates FIFO intent directly through the type, rather than relying on convention (always calling `add`/`remove(0)` on a `List` and hoping nobody calls `remove(5)` by mistake).

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class ChatAppConcurrentAtScale {
    public static void main(String[] args) throws InterruptedException {
        // At scale, with multiple connection-handling threads, single-threaded structures aren't enough.
        Set<String> onlineUsers = ConcurrentHashMap.newKeySet(); // thread-safe uniqueness, frequent read+write
        Queue<String> moderationQueue = new ConcurrentLinkedQueue<>(); // thread-safe, non-blocking FIFO

        int connectionThreads = 6;
        ExecutorService pool = Executors.newFixedThreadPool(connectionThreads);

        for (int i = 0; i < connectionThreads; i++) {
            final int userId = i % 3; // deliberately create overlap: only 3 distinct users across 6 threads
            pool.submit(() -> {
                onlineUsers.add("user-" + userId); // safe from multiple threads, correctly deduplicated
                moderationQueue.offer("message-from-user-" + userId);
            });
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("distinct online users despite 6 concurrent connections: " + onlineUsers.size());
        System.out.println("online users: " + onlineUsers);
        System.out.println("moderation queue size: " + moderationQueue.size());
    }
}
```

**How to run:** `java ChatAppConcurrentAtScale.java`. Exact set iteration order and queue contents' order can vary by thread timing, but the counts are always deterministic given the deliberate overlap in the example.

Expected output shape:
```
distinct online users despite 6 concurrent connections: 3
online users: [user-0, user-1, user-2]
moderation queue size: 6
```

This adds the production-flavored hard case: scaling the same conceptual design (unique online users, FIFO moderation queue) to genuinely concurrent access from multiple connection-handling threads. `ConcurrentHashMap.newKeySet()` provides a thread-safe `Set` view backed by a `ConcurrentHashMap` internally — correctly deduplicating `"user-0"`, `"user-1"`, `"user-2"` down to exactly 3 entries despite 6 concurrent `add` calls, 2 for each distinct user. `ConcurrentLinkedQueue` accepts all 6 concurrent `offer` calls safely without blocking, since moderation messages (unlike users) are expected to have duplicates in the general case and don't need deduplication.

## 6. Walkthrough

Tracing `ChatAppConcurrentAtScale.main`:

1. Six tasks are submitted to a six-thread pool. Each computes `userId = i % 3`, so threads `0` and `3` both compute `userId = 0`, threads `1` and `4` both compute `userId = 1`, and threads `2` and `5` both compute `userId = 2` — deliberately creating pairs of threads racing to add the *same* user ID concurrently.
2. Each task calls `onlineUsers.add("user-" + userId)`. Because `onlineUsers` is backed by `ConcurrentHashMap.newKeySet()` (a genuinely thread-safe `Set` implementation), all six concurrent calls are safe — no corruption, no lost updates — and the underlying `ConcurrentHashMap`'s uniqueness guarantee correctly ensures that even though `"user-0"` is added by two different threads, it only ever occupies one entry in the set.
3. Each task also calls `moderationQueue.offer("message-from-user-" + userId)`. Because `moderationQueue` is a `ConcurrentLinkedQueue`, all six `offer` calls succeed immediately and safely, with no blocking and no risk of corruption, regardless of how the six threads interleave — and unlike the user set, every one of the six messages is retained, since messages (unlike users) are expected to have no uniqueness constraint.
4. After all six tasks complete, `onlineUsers.size()` correctly reports `3` — the three distinct user IDs, deduplicated correctly despite the concurrent, overlapping insertion attempts — while `moderationQueue.size()` reports `6`, since every individual message submission is retained without deduplication.
5. This confirms the design choices from Level 2 scale correctly into a genuinely concurrent context, simply by swapping each single-threaded implementation for its thread-safe counterpart with matching semantics (`HashSet` → `ConcurrentHashMap.newKeySet()`; `ArrayDeque` → `ConcurrentLinkedQueue`) — the conceptual trade-off decisions made about *which kind* of collection each role needs didn't have to change at all, only the specific concurrent-safe implementation of that same kind.

## 7. Gotchas & takeaways

> **Gotcha:** matching a collection to its role isn't a one-time decision that survives every future requirement change unexamined — if the moderation queue later needs priority-based processing instead of strict FIFO, or the online-users set later needs to support blocking "wait until a user comes online," the right *kind* of collection changes too (to [`PriorityBlockingQueue`](0836-blockingqueue-family-array-linked-priority-delay-synchronous.md), for instance). Revisit the underlying access-pattern questions whenever a requirement changes, rather than assuming the original choice remains correct indefinitely.

- Choosing a collection is a sequence of trade-off decisions — ordering, duplicate tolerance, dominant access pattern, and thread-safety needs — not a search for one universally best type.
- A mismatched choice (a `List` used where uniqueness matters, a `LinkedList` used where indexed access dominates) often works fine at small scale and only becomes an expensive, visible problem once the workload grows into the dimension the wrong choice is bad at.
- Concurrent scenarios have their own parallel set of choices — blocking vs. non-blocking, snapshot vs. weakly-consistent — mirroring the single-threaded decision space but adding thread-safety as a dimension.
- `ConcurrentHashMap.newKeySet()` is a convenient way to get a genuinely thread-safe `Set` backed by `ConcurrentHashMap`'s proven concurrency characteristics, without needing a dedicated concurrent `Set` class.
- Revisit collection choices whenever the actual access pattern or concurrency requirements change — the right choice is a function of the workload, not a permanent property of the code.
