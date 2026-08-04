---
card: system-design
gi: 25
slug: long-polling-vs-short-polling
title: Long polling vs short polling
---

## 1. What it is

**Short polling** is a client repeatedly sending a request every fixed interval (e.g. every 3 seconds) asking "is there anything new?", getting an immediate reply either way. **Long polling** is a client sending a request that the *server deliberately holds open* — not replying immediately — until either new data becomes available or a timeout is reached; the client then immediately opens a new long-poll request to keep waiting for the next update.

## 2. Why & when

Both are workarounds for getting near-real-time updates from a server using only plain, ordinary HTTP request-response, without needing WebSocket or SSE support. You reach for one of these when a client (often an older system, or one behind infrastructure that does not support WebSocket) needs semi-real-time updates but you cannot use a persistent-connection protocol.

## 3. Core concept

**Short polling** is simple to implement, but wasteful: most requests return "nothing new", yet each one still pays the full cost of a request (and a database or cache lookup on the server) for that empty answer. There is also an inherent latency floor equal to the poll interval — if you poll every 3 seconds, an update can be up to 3 seconds old before the client learns about it.

**Long polling** removes most of the wasted "nothing new" replies: the server only responds once it actually has something to say (or the timeout passes), so nearly every response carries real data. This dramatically reduces the number of empty round trips compared to short polling, while still working over plain HTTP. Its downside is that it ties up a server-side connection (and often a server thread or resource) for the entire time it is waiting, which can strain server capacity if many clients are long-polling simultaneously.

**Comparing the three approaches on this section's continuum:**

| Approach | Requests for N updates over time | Update latency | Server resource cost |
|---|---|---|---|
| Short polling | Many (most return empty) | Up to one poll interval | Cheap per request, but many requests |
| Long polling | Roughly one per real update | Near-instant | Holds a connection open while waiting |
| WebSocket/SSE | One connection total | Instant (pushed) | One long-lived connection, no repeated requests |

## 4. Diagram

```
 SHORT POLLING (poll every 3s)              LONG POLLING (hold open until data)
 req -> "nothing new" (0.1s)                 req -> ... waiting ...
 wait 3s                                             ... waiting ...
 req -> "nothing new" (0.1s)                        -> "here's the update!" (2.7s later)
 wait 3s                                     req (new one immediately) -> ... waiting ...
 req -> "update!" (0.1s)                            -> "here's the update!" (1.1s later)

 many wasted round trips                     few round trips, each one useful
```
*Caption: short polling pays for many empty replies at a fixed cadence; long polling waits for real data before replying.*

## 5. Runnable example

### Artifact: a Java simulation comparing the total request count of short polling vs long polling for the same sequence of update arrival times

```java
import java.util.*;

public class PollingSim {

    public static void main(String[] args) {
        // Updates actually become available at these times (seconds from start).
        List<Integer> updateArrivalTimes = List.of(7, 8, 20);
        int totalDurationSeconds = 21;
        int shortPollIntervalSeconds = 3;

        // Short polling: one request every fixed interval, regardless of data.
        int shortPollRequests = totalDurationSeconds / shortPollIntervalSeconds;

        // Long polling: roughly one request per actual update, since the
        // server holds each request open until data (or a timeout) arrives.
        int longPollRequests = updateArrivalTimes.size();

        System.out.println("Simulated duration: " + totalDurationSeconds + "s, updates at: " + updateArrivalTimes);
        System.out.println("Short polling (every " + shortPollIntervalSeconds + "s): " + shortPollRequests + " requests total");
        System.out.println("Long polling: " + longPollRequests + " requests total (one per real update)");
        System.out.printf("Short polling makes %.1fx more requests for the same updates%n",
            (double) shortPollRequests / longPollRequests);
    }
}
```

**How to run:** save as `PollingSim.java`, run `java PollingSim.java` (JDK 17+).

## 6. Walkthrough

1. `updateArrivalTimes` lists the moments, in seconds, when real updates actually become available — only 3 real updates across a 21-second window.
2. `shortPollRequests` computes how many requests short polling would make regardless of whether any update is ready, simply based on the fixed 3-second interval: `21 / 3 = 7` requests.
3. `longPollRequests` reflects that, in long polling, the server holds each request open until real data arrives, so roughly one request corresponds to one real update — 3 requests total.
4. Output:
```
Simulated duration: 21s, updates at: [7, 8, 20]
Short polling (every 3s): 7 requests total
Long polling: 3 requests total (one per real update)
Short polling makes 2.3x more requests for the same updates
```
5. Most of short polling's 7 requests (4 of them) returned "nothing new" — wasted round trips that long polling avoids by waiting for real data before replying, at the cost of holding a connection open on the server in the meantime.

## 7. Gotchas & takeaways

> **Gotcha:** deploying long polling at very large scale without accounting for the resource cost of many simultaneously held-open requests. Each waiting long-poll request can tie up a server thread or connection slot; at high concurrent client counts, this can exhaust server capacity faster than short polling would, even though it sends fewer total requests.

- Short polling is simple but wasteful, with a latency floor equal to the poll interval.
- Long polling reduces wasted requests significantly, but holds server resources open while waiting.
- If the client and infrastructure both support it, WebSocket or SSE remove polling's overhead entirely — prefer them when available.
