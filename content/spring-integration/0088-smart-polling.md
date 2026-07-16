---
card: spring-integration
gi: 88
slug: smart-polling
title: "Smart polling"
---

## 1. What it is

Smart polling refers to configuring a poller's behavior to adapt to actual conditions rather than firing at a rigid fixed interval regardless of circumstances — using triggers like `PeriodicTrigger` with `maxMessagesPerPoll`, dynamic triggers that adjust their own interval based on recent results, or conditional polling that only fires when a precondition holds. Rather than always polling every N seconds no matter what, a smart-polling configuration might poll more frequently when work is flowing in, back off when a source is quiet, or skip a poll entirely when a precondition (like an open circuit breaker) says there's no point.

## 2. Why & when

You reach for smart polling when a fixed polling interval either wastes resources during quiet periods or reacts too slowly during busy ones:

- **Workload arrives unevenly, and a single fixed interval is wrong for both extremes** — a fixed interval fast enough to keep up during a busy period polls needlessly often during a quiet one, and an interval sized for the quiet period reacts too slowly when a burst arrives; a dynamically adjusting trigger backs off during quiet periods and speeds up when messages are actively flowing.
- **`maxMessagesPerPoll` needs tuning to the downstream capacity, not just the polling frequency** — capping how many messages a single poll cycle pulls (even if the source has more available) prevents one poll from overwhelming downstream processing, complementing (not replacing) interval tuning.
- **Polling should pause entirely under a known bad condition** — if a downstream dependency's circuit breaker (card 0086) is open, polling for more work to hand to that dependency is often pointless; a smart-polling setup can skip poll cycles while that condition holds, resuming automatically once it clears.

## 3. Core concept

Think of a fixed-interval poller as a delivery driver who checks a specific mailbox exactly every 10 minutes, regardless of whether the mail is piling up or the box has been empty for hours. A smart poller is more like a driver who speeds up their rounds when they know a busy sender has started shipping a lot (recent polls returned messages), and slows down or skips a round when the box has been empty for a while (recent polls returned nothing) — adapting the schedule to the actual, observed rate of new work rather than following a rigid, unchanging clock.

```java
@Bean
public IntegrationFlow adaptivePollingFlow() {
    return IntegrationFlow.from(
            () -> queueClient.receive(),
            e -> e.poller(Pollers.trigger(adaptiveTrigger()).maxMessagesPerPoll(20)))
        .handle(order -> orderService.process(order))
        .get();
}

@Bean
public Trigger adaptiveTrigger() {
    // A trigger implementation that shortens its next-fire interval after a poll returns
    // messages, and lengthens it after a poll returns nothing -- backing off during quiet
    // periods and tightening up as soon as real work starts arriving again.
    return new AdaptivePollSkippingTrigger(Duration.ofMillis(200), Duration.ofSeconds(10));
}
```

The trigger's own interval shrinks toward 200ms when messages are actively arriving and grows toward 10 seconds during quiet stretches, rather than staying fixed at either extreme.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A fixed-interval poller checks at the same rate whether busy or quiet; a smart poller shortens its interval when messages are flowing and lengthens it during quiet periods, adapting to actual load" >
  <text x="160" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Fixed interval</text>
  <rect x="20" y="30" width="280" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">| 5s | 5s | 5s | 5s | 5s | 5s |</text>
  <text x="160" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">same rate whether busy or empty</text>

  <text x="480" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Smart polling</text>
  <rect x="340" y="30" width="280" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">|200ms|200ms|1s|3s|10s|10s|200ms|</text>
  <text x="480" y="80" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">tight when busy, backs off when quiet</text>
</svg>

The interval itself becomes a function of recent activity rather than a fixed constant.

## 5. Runnable example

The scenario: polling a work queue whose arrival rate varies over time, simulated with a queue that alternates between busy and quiet periods (no real message broker or trigger implementation needed to demonstrate the adaptive-interval logic), starting with a fixed-interval poll, then adding an interval that shrinks and grows based on recent poll results, then adding a skip-poll condition tied to a simulated circuit-breaker state.

### Level 1 — Basic

```java
// SmartPollingDemo.java
import java.util.*;

public class SmartPollingDemo {
    static List<Integer> pollFixed(Queue<Integer> workQueue, int maxPerPoll) {
        List<Integer> batch = new ArrayList<>();
        for (int i = 0; i < maxPerPoll && !workQueue.isEmpty(); i++) batch.add(workQueue.poll());
        return batch;
    }

    public static void main(String[] args) {
        Queue<Integer> workQueue = new LinkedList<>(List.of(1, 2, 3));
        for (int poll = 1; poll <= 3; poll++) {
            System.out.println("Poll " + poll + " (fixed interval): " + pollFixed(workQueue, 5));
        }
    }
}
```

How to run: `java SmartPollingDemo.java`. Expected output: poll 1 retrieves `[1, 2, 3]`, polls 2 and 3 return `[]` — the same fixed polling rhythm continues even once the queue is empty, with no adjustment to how often it checks.

### Level 2 — Intermediate

```java
// SmartPollingDemo.java
import java.util.*;

public class SmartPollingDemo {
    // Real-world concern: checking on a fixed schedule wastes cycles when the queue is empty
    // and reacts too slowly if it doesn't check often enough during a burst. An adaptive
    // interval shrinks after a productive poll and grows after an empty one.
    static class AdaptiveInterval {
        private long currentMillis;
        private final long minMillis, maxMillis;

        AdaptiveInterval(long initialMillis, long minMillis, long maxMillis) {
            this.currentMillis = initialMillis;
            this.minMillis = minMillis;
            this.maxMillis = maxMillis;
        }

        void recordPollResult(int messagesReceived) {
            if (messagesReceived > 0) {
                currentMillis = Math.max(minMillis, currentMillis / 2); // speed up
            } else {
                currentMillis = Math.min(maxMillis, currentMillis * 2); // back off
            }
        }

        long currentIntervalMillis() { return currentMillis; }
    }

    public static void main(String[] args) {
        Queue<Integer> workQueue = new LinkedList<>(List.of(1, 2, 3));
        AdaptiveInterval interval = new AdaptiveInterval(1000, 200, 10_000);

        for (int poll = 1; poll <= 5; poll++) {
            List<Integer> batch = new ArrayList<>();
            for (int i = 0; i < 2 && !workQueue.isEmpty(); i++) batch.add(workQueue.poll());
            interval.recordPollResult(batch.size());
            System.out.println("Poll " + poll + ": received " + batch.size()
                + ", next interval = " + interval.currentIntervalMillis() + "ms");
        }
    }
}
```

How to run: `java SmartPollingDemo.java`. Expected output: the interval shrinks toward the 200ms floor while messages are still being received, then grows back toward the 10-second ceiling once the queue empties out — the poller automatically tightening its rhythm during the burst and relaxing once things go quiet, unlike Level 1's unchanging schedule.

### Level 3 — Advanced

```java
// SmartPollingDemo.java
import java.util.*;

public class SmartPollingDemo {
    static class AdaptiveInterval {
        private long currentMillis;
        private final long minMillis, maxMillis;
        AdaptiveInterval(long initialMillis, long minMillis, long maxMillis) {
            this.currentMillis = initialMillis; this.minMillis = minMillis; this.maxMillis = maxMillis;
        }
        void recordPollResult(int messagesReceived) {
            currentMillis = messagesReceived > 0
                ? Math.max(minMillis, currentMillis / 2)
                : Math.min(maxMillis, currentMillis * 2);
        }
        long currentIntervalMillis() { return currentMillis; }
    }

    // Production concern: if a downstream circuit breaker is open (card 0086), polling for more
    // work to hand it is pointless -- a smart poller should check that condition and SKIP the
    // poll entirely while it holds, rather than pulling messages it can't currently process.
    static class ConditionalPoller {
        boolean downstreamCircuitOpen = false;

        List<Integer> pollIfAllowed(Queue<Integer> workQueue, int maxPerPoll) {
            if (downstreamCircuitOpen) {
                System.out.println("Downstream circuit open, skipping this poll entirely");
                return List.of();
            }
            List<Integer> batch = new ArrayList<>();
            for (int i = 0; i < maxPerPoll && !workQueue.isEmpty(); i++) batch.add(workQueue.poll());
            return batch;
        }
    }

    public static void main(String[] args) {
        Queue<Integer> workQueue = new LinkedList<>(List.of(1, 2, 3, 4));
        ConditionalPoller poller = new ConditionalPoller();
        AdaptiveInterval interval = new AdaptiveInterval(1000, 200, 10_000);

        for (int pollNum = 1; pollNum <= 4; pollNum++) {
            if (pollNum == 2) poller.downstreamCircuitOpen = true;  // simulate downstream outage
            if (pollNum == 4) poller.downstreamCircuitOpen = false; // simulate recovery

            List<Integer> batch = poller.pollIfAllowed(workQueue, 2);
            interval.recordPollResult(batch.size());
            System.out.println("Poll " + pollNum + ": received " + batch.size()
                + ", next interval = " + interval.currentIntervalMillis() + "ms");
        }
    }
}
```

How to run: `java SmartPollingDemo.java`. Expected output: poll 1 retrieves messages normally; poll 2 and 3 print "Downstream circuit open, skipping this poll entirely" and receive nothing (even though the queue still has messages waiting); poll 4, once the circuit recovers, resumes pulling messages normally — the poller correctly avoiding wasted work while a known-bad downstream condition holds, rather than blindly continuing to pull messages it has nowhere useful to send.

## 6. Walkthrough

Trace a poller's behavior across a burst, a quiet period, and a downstream outage.

1. **Busy period**: incoming work arrives faster than the poller's current interval — each poll returns a full batch (up to `maxMessagesPerPoll`), and the adaptive trigger shortens its next-fire interval in response, checking again sooner to keep pace with the burst.
2. **Transition to quiet**: as the source empties out, polls start returning fewer or zero messages; the adaptive trigger lengthens its interval correspondingly, backing off toward its configured maximum rather than continuing to poll at the tight, busy-period rate against an empty source.
3. **Downstream outage begins**: independently of the source's activity level, a downstream dependency's circuit breaker (card 0086) opens due to sustained failures; a smart-polling configuration checks this condition before each poll and, finding it open, skips the poll cycle entirely rather than pulling messages that have nowhere productive to go.
4. **Outage persists**: for as long as the circuit remains open, every scheduled poll attempt is skipped, leaving messages queued at the source rather than pulled into an application that can't currently process them anyway.
5. **Recovery**: once the downstream circuit closes again (the trial call in its half-open state succeeds), the poller resumes normal operation on its next scheduled check, and the adaptive interval logic picks back up based on whatever the actual arrival rate turns out to be at that point.

```
scheduled poll check
  -> downstream circuit open? -> yes: skip poll entirely
                               -> no: poll up to maxMessagesPerPoll
                                   messages received > 0 -> shorten next interval
                                   messages received = 0 -> lengthen next interval
```

## 7. Gotchas & takeaways

> **Gotcha:** an adaptive interval with no configured floor can shrink toward zero during a sustained burst, effectively busy-waiting and consuming CPU on near-continuous polling — always set a sensible minimum interval (as `minMillis` does in the example) so "speed up when busy" doesn't degrade into "poll as fast as physically possible."

- Smart polling is about matching effort to actual, observed conditions — busy periods get tighter polling, quiet periods get looser polling, and known-bad downstream conditions get skipped polling entirely, rather than treating every poll cycle identically regardless of context.
- `maxMessagesPerPoll` and interval tuning are complementary, not substitutes for each other — capping batch size protects downstream capacity per poll, while interval adjustment controls how often those capped batches are pulled in the first place.
- Skipping a poll when a downstream circuit is open (or another known precondition fails) avoids pulling work the application currently has no way to process, keeping it queued at the source instead of buffered uselessly inside the application.
- Always bound both ends of an adaptive interval (a floor to prevent busy-waiting, a ceiling to prevent unacceptably slow reaction to a new burst after a long quiet period) — an unbounded adaptive trigger can misbehave at either extreme just as badly as a poorly-chosen fixed interval would.
