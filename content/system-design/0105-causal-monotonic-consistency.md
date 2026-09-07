---
card: system-design
gi: 105
slug: causal-monotonic-consistency
title: Causal & monotonic consistency
---

## 1. What it is

**Causal consistency** guarantees that if one operation *causally depends* on another — for example, a reply to a comment can only exist after the comment itself — every node shows them in that same cause-and-effect order. It does not order unrelated operations relative to each other, only ones that are actually connected. **Monotonic reads** is a narrower, simpler guarantee: once a user has read a value, they will never read an *older* value than that on a later read, even if they hit a different replica. Both sit between the strict ordering of [strong consistency](0103-strong-consistency.md) and the "no ordering promises at all" of plain [eventual consistency](0104-eventual-consistency.md).

## 2. Why & when

Plain eventual consistency can produce results that look outright broken to a user, even though no data was lost: seeing a reply to a comment before the comment itself appears, because the reply happened to replicate faster on the path the reader took. Causal consistency fixes exactly this class of bug, without paying the full coordination cost of strong consistency, by only ordering things that are genuinely related. Monotonic reads fixes a related annoyance: a user refreshing a page and seeing their friend list shrink back down, because a later read landed on a replica that is further behind than the one an earlier read hit. Use causal consistency for systems with visible cause-and-effect relationships (comments, chat threads, social feeds); use monotonic reads whenever a user might issue several reads in a row and should never see time run backwards.

## 3. Core concept

- **Causal consistency — the "happens-before" relationship:** operation B causally depends on operation A if B could only have been created after A was known (a reply references a comment; a "like" references a post). Causally related operations must be seen everywhere in that order.
- **Concurrent (unrelated) operations are unordered:** two users each posting an unrelated comment at the same time have no causal relationship, so different nodes may show them in either order — this is fine and expected.
- **How it's tracked:** systems commonly attach a marker to each write recording which prior writes it depended on (a vector clock or a simple "last seen version" token), so a replica can check "have I applied everything this write depends on?" before showing it.
- **Monotonic reads — per-user replica pinning:** the simplest implementation is routing all of one user's reads to the same replica for their session, so their replica's data only ever moves forward in time from their own perspective, never backward.
- **Monotonic reads via a version floor:** alternatively, the client remembers the highest version number it has seen and rejects (or retries elsewhere) any read that would return something older than that.

## 4. Diagram

```
CAUSAL CONSISTENCY:
  Comment "Great post!" (op A) posted first.
  Reply "Thanks!" (op B) posted second, causally depends on A.

  Every node MUST show A before B:
    Node1: [A, B]   Node2: [A, B]   -- correct, causal order preserved
    Node3: [B, A]   -- WRONG: reply shown before the comment it replies to

MONOTONIC READS:
  User's read #1 (from Replica X, caught up to v10): sees 10 friends.
  User's read #2 (from Replica Y, only caught up to v7): would see 8 friends.
  Monotonic reads REJECTS read #2's stale result / redirects it,
  so the user never sees their friend count go backward.
```
*Caption: causal consistency orders only related events correctly; monotonic reads stops a user's own view of the data from moving backward in time.*

## 5. Runnable example

**Level 1 — Basic.** Model causal dependency between a comment and its reply, and reject an order that violates it.

**Level 2 — Monotonic reads.** A user's reads track the highest version seen, and reject a replica's stale answer.

**Level 3 — Concurrent, unrelated writes stay unordered.** Two unrelated comments have no causal link, so either order is valid.

```java
// CausalMonotonicConsistency.java
import java.util.*;

public class CausalMonotonicConsistency {

    record Op(String id, String content, String dependsOn, long version) {} // dependsOn = null if no causal parent

    static boolean isValidOrder(List<Op> observedOrder) {
        Set<String> seen = new HashSet<>();
        for (Op op : observedOrder) {
            if (op.dependsOn() != null && !seen.contains(op.dependsOn())) {
                return false; // dependency not seen yet - causal order violated
            }
            seen.add(op.id());
        }
        return true;
    }

    public static void main(String[] args) {
        // Level 1: causal consistency - a reply depends on its comment.
        Op comment = new Op("c1", "Great post!", null, 1);
        Op reply = new Op("r1", "Thanks!", "c1", 2);

        System.out.println("order [comment, reply] valid? " + isValidOrder(List.of(comment, reply)));
        System.out.println("order [reply, comment] valid? " + isValidOrder(List.of(reply, comment)));
        System.out.println("-> the second order violates causal consistency: reply shown before its dependency");

        // Level 2: monotonic reads - track the highest version this user has seen.
        long userHighestVersionSeen = 0;
        Map<String, Long> replicaXState = Map.of("friendCount", 10L);
        Map<Long, Long> replicaXVersion = Map.of(10L, 10L); // replica X is caught up to version 10

        long replicaXVersionNow = 10;
        userHighestVersionSeen = Math.max(userHighestVersionSeen, replicaXVersionNow);
        System.out.println("read #1 from replica X (v" + replicaXVersionNow + "): friendCount=10, user's high-water mark now v" + userHighestVersionSeen);

        long replicaYVersionNow = 7; // replica Y is behind
        if (replicaYVersionNow < userHighestVersionSeen) {
            System.out.println("read #2 from replica Y (v" + replicaYVersionNow + ") REJECTED: older than user's high-water mark v" + userHighestVersionSeen);
            System.out.println("-> client retries against a more caught-up replica instead of showing stale data");
        }

        // Level 3: two unrelated comments, posted concurrently, have no causal link - either order is valid.
        Op commentA = new Op("cA", "Nice weather today", null, 3);
        Op commentB = new Op("cB", "Anyone tried the new cafe?", null, 4);
        System.out.println("order [A, B] valid? " + isValidOrder(List.of(commentA, commentB)));
        System.out.println("order [B, A] valid? " + isValidOrder(List.of(commentB, commentA)));
        System.out.println("-> both orders are valid: A and B are unrelated, so causal consistency makes no promise about their order");
    }
}
```

**How to run:** save as `CausalMonotonicConsistency.java`, then run `java CausalMonotonicConsistency.java`.

## 6. Walkthrough

1. `isValidOrder` walks a list of operations, tracking which ids it has already "seen"; if it reaches an operation whose `dependsOn` has not been seen yet, the order is invalid.
2. `[comment, reply]` passes, because `comment` (`c1`) is seen before `reply` (which depends on `c1`) is checked. `[reply, comment]` fails, because when `reply` is checked first, `c1` is not yet in `seen`.
3. Level 2 models monotonic reads: after reading from replica X at version 10, the user's `userHighestVersionSeen` becomes 10. When a second read would come from replica Y, which is only at version 7, the code detects `7 < 10` and rejects that stale answer rather than showing it.
4. This rejection is the concrete mechanism behind "the user never sees their friend count go backward" — the stale read is caught before it reaches the user.
5. Level 3 checks two unrelated comments, `commentA` and `commentB`, neither depending on the other; `isValidOrder` returns `true` for *both* possible orderings, showing causal consistency correctly leaves genuinely unrelated events unordered, unlike strong consistency which would force one global order on everything.

## 7. Gotchas & takeaways

> Gotcha: causal consistency only orders operations that have an explicit, tracked dependency. If your system fails to record a real dependency (for example, a "like" that references a post but isn't tagged as depending on it), causal consistency cannot protect that relationship — the guarantee is only as good as the dependency tracking behind it.

- Causal consistency preserves cause-and-effect order for related operations, while leaving unrelated, concurrent operations free to appear in any order on different nodes.
- Monotonic reads guarantees a single user's sequence of reads never goes backward in time, typically via replica pinning or a version high-water mark.
- Both sit between strong consistency's full ordering guarantee and eventual consistency's lack of any ordering guarantee, at a lower coordination cost than strong consistency.
- Related concepts: [Eventual consistency](0104-eventual-consistency.md) (the weaker baseline these guarantees improve on), [Strong consistency](0103-strong-consistency.md) (the stricter guarantee these avoid the full cost of), [Conflict resolution](0109-conflict-resolution-last-write-wins-vector-clocks-crdts.md) (vector clocks, used to track causal dependencies).
