---
card: system-design
gi: 102
slug: replication-lag-read-your-writes
title: Replication lag & read-your-writes
---

## 1. What it is

**Replication lag** is the delay between a write landing on the leader and that same write becoming visible on a follower. **Read-your-writes consistency** is a guarantee that a user who just made a write will always see that write in their own subsequent reads, even if replication lag would otherwise let them read stale data from a follower.

## 2. Why & when

Replication lag is unavoidable with [asynchronous replication](0101-synchronous-vs-asynchronous-replication.md): followers always take some non-zero time to catch up. This becomes a visible bug when a user updates their own profile, then immediately reloads the page and sees their *old* profile, because the read was served by a follower that had not yet applied the write. You need a read-your-writes strategy any time users perform a write and then, in the same session, expect to see the result of that write — which is most interactive applications.

## 3. Core concept

- **The bug scenario:** user writes to the leader, the leader confirms, the write starts replicating; a read immediately after is routed to a follower that has not received it yet; the user sees stale data.
- **Fix 1 — read your own writes from the leader:** for a short window after a user's write, route that user's reads to the leader instead of a follower, since the leader always has the latest data.
- **Fix 2 — track a replication position:** the client remembers a marker (e.g. a log sequence number) from its last write; a read is only served by a follower once that follower has caught up to at least that marker.
- **Fix 3 — session stickiness:** route all of a user's requests, for some window of time, to the same follower they last wrote through — while this does not eliminate lag, it means the user's later reads at least come from a node that is consistently catching up, not different followers with different lag amounts.
- **The trade-off:** any read-your-writes fix pushes some reads (or all of one user's reads) away from the load-balanced pool of followers, reducing some of replication's read-scaling benefit for that traffic.

## 4. Diagram

```
Without read-your-writes:
  t=0: user writes "bio = X" to Leader. Leader confirms.
  t=1: user reloads page. Read routed to Follower (lag: not caught up yet).
       Follower still shows "bio = (old value)" -> confusing to the user.

With read-your-writes (marker-based):
  t=0: user writes "bio = X" to Leader. Leader confirms with marker=57.
  t=1: user reloads page. Read checks: has Follower reached marker >= 57?
       NO -> route this read to the Leader instead (or wait briefly).
       User sees "bio = X" correctly.
```
*Caption: a read-your-writes check compares a follower's replication progress to the user's own last-write marker before trusting it.*

## 5. Runnable example

**Level 1 — Basic.** Model replication lag: a follower's data lags behind the leader by a delay counter.

**Level 2 — Detecting the bug.** Read immediately after a write from a lagging follower and observe stale data.

**Level 3 — Read-your-writes fix.** Track each write's marker, and route the read to the leader when the follower has not caught up.

```java
// ReplicationLag.java
import java.util.*;

public class ReplicationLag {

    static Map<String, String> leaderData = new HashMap<>();
    static Map<String, String> followerData = new HashMap<>();
    static long leaderMarker = 0;
    static long followerAppliedMarker = 0;

    static long write(String key, String value) {
        leaderData.put(key, value);
        leaderMarker++;
        return leaderMarker; // the marker the client should remember for read-your-writes
    }

    static void followerCatchesUpTo(long marker) { // simulates replication finally applying up to this marker
        followerData.putAll(leaderData);
        followerAppliedMarker = marker;
    }

    static String readNaive(String key) {
        return followerData.get(key); // always reads from the follower, ignoring lag
    }

    static String readYourWrites(String key, long myLastWriteMarker) {
        if (followerAppliedMarker >= myLastWriteMarker) {
            return followerData.get(key); // follower is caught up enough for this user's own writes
        }
        return leaderData.get(key); // not caught up yet - fall back to the leader for correctness
    }

    public static void main(String[] args) {
        // Level 1 & 2: write, then read immediately before replication has caught up.
        long marker = write("bio", "Loves hiking");
        System.out.println("write confirmed, marker=" + marker);
        System.out.println("naive read (from lagging follower) right after write: " + readNaive("bio"));
        System.out.println("-> stale! follower has not applied marker " + marker + " yet");

        // Level 3: read-your-writes fix - detect the lag and fall back to the leader.
        System.out.println("read-your-writes result: " + readYourWrites("bio", marker));
        System.out.println("-> correct, served from the leader since the follower was behind");

        // Now let replication actually catch up.
        followerCatchesUpTo(marker);
        System.out.println("after replication catches up, naive read: " + readNaive("bio"));
        System.out.println("read-your-writes result now: " + readYourWrites("bio", marker) + " (follower is trusted again)");
    }
}
```

**How to run:** save as `ReplicationLag.java`, then run `java ReplicationLag.java`.

## 6. Walkthrough

1. `write("bio", "Loves hiking")` updates `leaderData` and increments `leaderMarker` to `1`, returning that marker to represent "the point in the replication stream this write happened at".
2. `readNaive("bio")` reads directly from `followerData`, which is still empty at this point, because `followerCatchesUpTo` has not run yet — this reproduces the stale-read bug plainly.
3. `readYourWrites("bio", marker)` compares `followerAppliedMarker` (still `0`) against the write's `marker` (`1`); since the follower has not caught up, it falls back to reading `leaderData`, returning the correct, fresh value.
4. `followerCatchesUpTo(marker)` then copies all of `leaderData` into `followerData` and sets `followerAppliedMarker` to `1`, simulating replication finally applying that write.
5. Both `readNaive` and `readYourWrites` now return the correct value from the follower — showing the read-your-writes check is only a temporary detour to the leader, used exactly while the follower is behind, and it stops being necessary once replication catches up.

## 7. Gotchas & takeaways

> Gotcha: read-your-writes only protects *the user who made the write* from seeing their own stale data — it says nothing about other users. A second user reading the same key from the same lagging follower will still see the old value, since they have no "last write marker" of their own referencing this update. Read-your-writes is a per-user guarantee, not a system-wide one.

- Replication lag is the normal, expected delay between a write on the leader and its visibility on a follower under asynchronous replication.
- Read-your-writes consistency specifically fixes the case where a user's own read follows their own write too quickly for a follower to have caught up.
- Common fixes track a replication marker or route a user's own reads to the leader for a short window after their write.
- Related concepts: [Synchronous vs asynchronous replication](0101-synchronous-vs-asynchronous-replication.md) (the root cause of lag), [Eventual consistency](0104-eventual-consistency.md) (the broader consistency model this staleness falls under).
