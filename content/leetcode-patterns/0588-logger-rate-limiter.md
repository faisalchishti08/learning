---
card: leetcode-patterns
gi: 588
slug: logger-rate-limiter
title: Logger Rate Limiter
---

## 1. What it is

Design a `Logger` class that suppresses repeated messages: `shouldPrintMessage(timestamp, message)` returns `true` and allows the message to print only if that exact message was **not** printed in the last 10 seconds (i.e., its previous print, if any, was strictly before `timestamp - 10`); otherwise it returns `false`. Example: `shouldPrintMessage(1, "foo")` → `true`, `shouldPrintMessage(2, "foo")` → `false` (too soon), `shouldPrintMessage(11, "foo")` → `true` (exactly 10 seconds later — allowed again).

## 2. Why & when

Unlike [Design Hit Counter](0586-design-hit-counter.md), which needs a global window over *all* events, this problem needs a *per-message* window — each distinct message string has its own independent last-printed timestamp. A `HashMap<message, lastPrintedTimestamp>` handles this directly: on each call, look up the message's own history rather than scanning a shared queue of events across all messages.

## 3. Core concept

**Key idea:** store, for every message ever seen, the timestamp of its most recent allowed print. On each call, compare the new `timestamp` against that message's stored timestamp; if the message has never been seen, or enough time has passed, allow it and update the stored timestamp.

**Steps:**
1. `shouldPrintMessage(timestamp, message)`: look up `lastPrinted.get(message)`.
2. If the message is not in the map, or `timestamp - lastPrinted.get(message) >= 10`, allow it: update `lastPrinted.put(message, timestamp)` and return `true`.
3. Otherwise, deny it: return `false` without updating the stored timestamp (a denied message does not reset its own cooldown).

**Why not updating the timestamp on a denial matters:** if a denied call *did* update `lastPrinted`, a burst of rapid-fire repeated messages could each individually extend the cooldown from their own timestamp, potentially blocking a message that should have become eligible again. Only a successful (allowed) print should reset the 10-second window for that message.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A HashMap tracking each message's own last-printed timestamp, independent of other messages">
  <g font-family="sans-serif" font-size="12">
    <rect x="30" y="30" width="180" height="35" fill="#161b22" stroke="#3fb950"/><text x="120" y="52" fill="#e6edf3" text-anchor="middle" font-size="11">"foo" -&gt; last printed at t=1</text>
    <rect x="30" y="75" width="180" height="35" fill="#161b22" stroke="#f0883e"/><text x="120" y="97" fill="#e6edf3" text-anchor="middle" font-size="11">"bar" -&gt; last printed at t=5</text>
    <text x="470" y="55" fill="#79c0ff" text-anchor="middle">shouldPrintMessage(2, "foo"): 2-1=1 &lt; 10 -&gt; false</text>
    <text x="470" y="100" fill="#79c0ff" text-anchor="middle">shouldPrintMessage(15, "bar"): 15-5=10 &gt;= 10 -&gt; true</text>
  </g>
</svg>

Each message string is an independent key with its own cooldown clock — one message being suppressed has no effect on any other message.

## 5. Runnable example

**Level 1 — Brute force.** Store a list of every `(timestamp, message)` pair ever seen; on each call, scan the whole list for the same message within the last 10 seconds. O(total calls so far) per call.

**KEY INSIGHT:** only the *most recent* printed timestamp for a given message ever matters for future decisions — there is no need to remember every past occurrence, only the latest one, so a single `HashMap` entry per message replaces an ever-growing scan.

**Level 2 — Optimal.** `HashMap<String, Integer>` mapping message to its last-allowed timestamp, O(1) average per call.

**Level 3 — Hardened.** Correctly leaves the stored timestamp unchanged on a denial, and correctly treats the boundary `timestamp - lastPrinted == 10` as allowed (inclusive), matching the problem's "not printed in the last 10 seconds" wording.

```java
// Logger.java
import java.util.*;

public class Logger {

    private final Map<String, Integer> lastPrinted = new HashMap<>();

    public boolean shouldPrintMessage(int timestamp, String message) {
        Integer last = lastPrinted.get(message);
        if (last == null || timestamp - last >= 10) {
            lastPrinted.put(message, timestamp);
            return true;
        }
        return false;
    }

    public static void main(String[] args) {
        Logger logger = new Logger();
        System.out.println(logger.shouldPrintMessage(1, "foo"));  // true
        System.out.println(logger.shouldPrintMessage(2, "foo"));  // false, too soon
        System.out.println(logger.shouldPrintMessage(11, "foo")); // true, exactly 10s later
        System.out.println(logger.shouldPrintMessage(11, "bar")); // true, first time for "bar"
    }
}
```

**How to run:** save as `Logger.java`, then run `java Logger.java`.

## 6. Walkthrough

Trace `shouldPrintMessage(1,"foo")`, `shouldPrintMessage(2,"foo")`, `shouldPrintMessage(11,"foo")`:

| call | lastPrinted before | check | lastPrinted after | return |
|---|---|---|---|---|
| (1,"foo") | {} | not present -> allow | {"foo":1} | true |
| (2,"foo") | {"foo":1} | `2-1=1 < 10` -> deny | {"foo":1} (unchanged) | false |
| (11,"foo") | {"foo":1} | `11-1=10 >= 10` -> allow | {"foo":11} | true |

The denial at `timestamp=2` does not touch the stored timestamp, so the cooldown is still measured from the original print at `timestamp=1` — correctly making `timestamp=11` (exactly 10 seconds later) eligible.

## 7. Gotchas & takeaways

> Gotcha: updating `lastPrinted` on every call (including denials) instead of only on allowed prints would incorrectly reset the cooldown clock on each attempt — a burst of many rapid duplicate messages could then indefinitely delay when the message becomes printable again.

- Signal: "suppress a repeated event/message within a rolling time window, independently per key" is the per-key-HashMap-of-last-timestamp signal, distinct from a single shared sliding-window queue.
- Only successful (allowed) events should update the stored timestamp; denied events must leave the cooldown clock untouched.
- Related problems: Design Hit Counter (a single shared window across all events, not per-key), Design a Number Container System (per-key state, but for a different query, tracking the smallest index of a value).
