---
card: system-design
gi: 135
slug: retries-with-exponential-backoff-jitter
title: Retries with exponential backoff & jitter
---

## 1. What it is

A **retry** simply tries a failed operation again, on the theory that many failures are transient (a brief network blip, a momentarily overloaded server) and will succeed on a second attempt. **Exponential backoff** waits progressively longer between each retry attempt (e.g. 1s, 2s, 4s, 8s), instead of retrying immediately or at a fixed interval, giving a struggling dependency time to recover rather than hitting it again right away. **Jitter** adds a small random amount to each wait time, so that many clients retrying the same failed dependency do not all retry at exactly the same moment.

## 2. Why & when

Retrying immediately, with no backoff, against a dependency that is failing because it is overloaded makes the overload worse, not better — every failed caller immediately tries again, adding more load to an already-struggling system. Exponential backoff gives the dependency breathing room to recover, with each retry spaced further apart. Jitter solves a second, more subtle problem: if a dependency fails for every caller at once (a brief outage) and every caller retries using the exact same backoff schedule, all their retries land at the same synchronized moments, creating repeated load spikes instead of smoothly spread-out load. Use retries specifically for failures believed to be transient (network timeouts, a 503 response); never retry an error you know is permanent (a 400 Bad Request, a validation failure) since it will simply fail again identically.

## 3. Core concept

- **Only retry transient, idempotent-safe operations:** retrying an operation that has a side effect (charging a card) needs [idempotency](0116-idempotent-consumers.md) to be safe; retrying a clearly permanent failure (invalid input) wastes an attempt on a call guaranteed to fail again.
- **Exponential backoff formula:** wait time typically doubles each attempt, e.g. `baseDelay * 2^attemptNumber`, often capped at a maximum delay so retries do not eventually wait absurdly long.
- **Jitter:** add a random amount to the computed backoff delay (e.g. a random value between 0 and the computed delay, known as "full jitter"), so simultaneous callers' retries spread out over time instead of clustering.
- **Maximum retry count:** retries must be bounded — an operation that keeps failing after several retries should stop retrying and surface the failure (or move to a [fallback](0138-fallbacks-graceful-degradation.md) or a [dead-letter queue](0118-dead-letter-queues-poison-messages.md)), not retry forever.
- **The retry storm risk:** many independent clients retrying the same failing dependency, especially without backoff or jitter, can itself cause or prolong an outage — this is a well-documented cause of real production incidents.

## 4. Diagram

```
NO BACKOFF (retry storm risk):        EXPONENTIAL BACKOFF + JITTER:

  fail -> retry immediately            fail -> wait ~1s (0.5-1.5s w/ jitter) -> retry
  fail -> retry immediately            fail -> wait ~2s (1-3s w/ jitter) -> retry
  fail -> retry immediately            fail -> wait ~4s (2-6s w/ jitter) -> retry
  (hammering an already-struggling     (dependency gets increasing breathing
   dependency, no relief)               room; jitter spreads many clients'
                                         retries instead of clustering them)
```
*Caption: exponential backoff spaces out retries increasingly; jitter prevents many clients' retries from landing at the same synchronized moments.*

## 5. Runnable example

**Level 1 — Basic.** Retry a failing operation a bounded number of times with a fixed delay.

**Level 2 — Exponential backoff.** Increase the delay between each retry attempt.

**Level 3 — Add jitter.** Randomize the delay so multiple simulated clients' retries do not all land at the same moment.

```java
// RetriesBackoffJitter.java
import java.util.*;

public class RetriesBackoffJitter {

    static int attemptsUntilSuccess = 3; // this simulated call succeeds on the 3rd attempt

    static boolean attemptCall(int attemptNumber) {
        return attemptNumber >= attemptsUntilSuccess;
    }

    public static void main(String[] args) {
        // Level 1 & 2: exponential backoff - delay doubles each attempt, capped at a maximum.
        int maxRetries = 5;
        long baseDelayMs = 500;
        long maxDelayMs = 8000;

        System.out.println("--- exponential backoff (no jitter) ---");
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            boolean success = attemptCall(attempt);
            if (success) { System.out.println("attempt " + attempt + ": SUCCESS"); break; }
            long delay = Math.min(baseDelayMs * (1L << (attempt - 1)), maxDelayMs); // baseDelay * 2^(attempt-1), capped
            System.out.println("attempt " + attempt + ": FAILED, waiting " + delay + "ms before retry");
        }

        // Level 3: add jitter - randomize the delay so simultaneous clients don't retry in lockstep.
        System.out.println("--- exponential backoff WITH jitter, 3 simulated clients ---");
        Random rand = new Random(7);
        for (int client = 1; client <= 3; client++) {
            long computedDelay = Math.min(baseDelayMs * (1L << 1), maxDelayMs); // e.g. attempt 2's delay
            long jitteredDelay = (long) (rand.nextDouble() * computedDelay); // "full jitter": random between 0 and computedDelay
            System.out.println("client " + client + ": computed backoff=" + computedDelay + "ms, jittered delay=" + jitteredDelay + "ms");
        }
        System.out.println("-> each client waits a DIFFERENT amount, spreading their retries instead of all landing at " + (baseDelayMs * 2) + "ms together");
    }
}
```

**How to run:** save as `RetriesBackoffJitter.java`, then run `java RetriesBackoffJitter.java`.

## 6. Walkthrough

1. `attemptCall` simulates a call that only succeeds once `attemptNumber` reaches `attemptsUntilSuccess` (3), modeling a transient failure that resolves after a couple of tries.
2. The Level 1/2 loop computes `delay = baseDelayMs * 2^(attempt-1)`, capped at `maxDelayMs`; attempt 1 fails and waits `500ms`, attempt 2 fails and waits `1000ms`, and attempt 3 succeeds — showing the delay growing exponentially between failed attempts, and stopping the moment the call finally succeeds.
3. Level 3 computes the same backoff delay (for a fixed attempt number, to keep the comparison clear) for 3 separate simulated clients, but then multiplies it by a random fraction between 0 and 1 to get `jitteredDelay`.
4. Each client's printed `jitteredDelay` comes out to a different value, even though they all started from the identical `computedDelay` — this is jitter doing its job: spreading what would otherwise be simultaneous, synchronized retry attempts across a range of actual times.
5. The final note makes the payoff explicit: without jitter, all 3 clients would retry at exactly the same `computedDelay` moment, creating a load spike; with jitter, their retries land at different times, smoothing the load the recovering dependency actually experiences.

## 7. Gotchas & takeaways

> Gotcha: retrying an operation that is not idempotent (see [idempotent consumers](0116-idempotent-consumers.md)) can cause the same side effect to happen multiple times if the original attempt actually succeeded but its success response was lost before the caller saw it — always confirm an operation is safe to repeat before wrapping it in a retry loop.

- Retries handle transient failures by trying again, but should never be used for failures known to be permanent.
- Exponential backoff spaces out retry attempts increasingly, giving a struggling dependency room to recover instead of being hit again immediately.
- Jitter randomizes each retry's delay, preventing many simultaneous clients from retrying in lockstep and causing a synchronized load spike.
- Related concepts: [Timeouts](0134-timeouts.md) (what typically triggers the failure a retry responds to), [Idempotent consumers](0116-idempotent-consumers.md) (a prerequisite for safely retrying an operation with side effects), [Circuit breaker](0136-circuit-breaker.md) (stops retries altogether once a dependency is clearly down, rather than retrying forever).
