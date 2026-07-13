---
card: microservices
gi: 239
slug: why-distributed-systems-fail-partial-failure
title: "Why distributed systems fail (partial failure)"
---

## 1. What it is

Partial failure is the defining failure mode of distributed systems: instead of a system either fully working or fully crashing, individual components — one service instance, one network link, one dependency — can fail independently while everything else keeps running, and the caller often can't immediately tell whether a failed call meant "the request never happened," "the request happened but the response was lost," or "the request is still being processed."

## 2. Why & when

A single-process, single-machine program either runs or crashes — there's no in-between state where "half the program" is broken while the rest keeps going. A distributed system built from many independently deployed, independently failing services has no such guarantee: `order-service` can be perfectly healthy while `inventory-service` is down, a network partition can make a healthy `payment-service` unreachable without either side crashing, and a slow response is genuinely ambiguous — it might mean the remote service is still working on it, or that the response already came back and was lost in transit. Every resiliency pattern covered in the rest of this section — [circuit breakers](0248-circuit-breaker-pattern.md), retries, timeouts, bulkheads — exists specifically to handle this ambiguity safely, because ignoring it (treating a distributed call like a reliable, always-succeeds local function call) is precisely what causes [cascading failures](0243-cascading-failures.md) across an entire system.

Internalize partial failure as the starting assumption for any code making a network call to another service — it's not an edge case to occasionally handle, it's the normal operating condition of a distributed system. Code that doesn't account for it (no timeout, no handling for "connection failed" versus "response never arrived") is incomplete, not just unlucky when it eventually breaks in production.

## 3. Core concept

A remote call can fail in more distinct ways than a local call ever can, and each failure mode implies a different, specific uncertainty about whether the remote side actually did anything — conflating them (treating every failure as "it definitely didn't happen," for instance) leads directly to bugs like duplicate charges or lost orders.

```java
// a LOCAL call: either it runs and returns, or it throws -- NO ambiguity about whether it "happened"
int result = localAdd(2, 3); // deterministic: ran, or didn't

// a REMOTE call has THREE genuinely different failure modes, each with DIFFERENT implications:
try {
    orderService.charge(orderId, amount);
} catch (ConnectException e) {
    // the request likely NEVER REACHED the remote service -- probably safe to retry
} catch (SocketTimeoutException e) {
    // UNKNOWN whether the remote side received AND processed it -- retrying risks a DUPLICATE charge
} catch (HttpServerErrorException e) {
    // the remote side DID receive it and responded with an error -- the OUTCOME is known
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request can fail at three different points -- before reaching the remote service, after being received but before a response returns, or with a clear error response -- and each point implies a different level of certainty about what actually happened on the remote side" >
  <rect x="20" y="75" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="99" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Caller</text>

  <line x1="140" y1="95" x2="300" y2="95" stroke="#8b949e" stroke-dasharray="4,4"/>
  <text x="220" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">1. connection refused -- SAFE to assume not received</text>

  <line x1="140" y1="130" x2="300" y2="130" stroke="#8b949e"/>
  <text x="220" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">2. timeout waiting for response -- UNKNOWN if processed</text>

  <rect x="300" y="75" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="99" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Remote service</text>

  <text x="500" y="45" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">3. error response received -- KNOWN outcome</text>
  <line x1="420" y1="95" x2="140" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr239)"/>

  <defs>
    <marker id="arr239" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The point of failure determines how much certainty exists about what the remote side actually did.

## 5. Runnable example

Scenario: a payment-charging call that starts naively treating any exception the same way (as if failure always means "nothing happened," risking duplicate charges), refactors to distinguish the three failure modes explicitly and handle each with the correct level of caution, and finally adds an idempotency key so that even an ambiguous timeout can be safely retried without risking a duplicate charge — the actual production-grade answer to partial failure's uncertainty.

### Level 1 — Basic

```java
// File: NaiveUniformFailureHandling.java -- treats EVERY failure
// identically, assuming it's ALWAYS safe to retry -- DANGEROUS, since a
// timeout doesn't actually guarantee the charge never happened.
import java.util.*;

public class NaiveUniformFailureHandling {
    static int callCount = 0;

    // simulates: sometimes the charge actually SUCCEEDED remotely before the response was lost
    static boolean chargeAndMaybeLoseResponse(String orderId) {
        callCount++;
        if (callCount == 1) { System.out.println("  [remote] charge PROCESSED, but response LOST (simulated timeout)"); return true; /* charge happened! */ }
        return false; // not reached in this demo
    }

    public static void main(String[] args) {
        boolean succeeded = chargeAndMaybeLoseResponse("order-42");
        if (!succeeded) {
            System.out.println("Retrying blindly...");
            chargeAndMaybeLoseResponse("order-42");
        } else {
            System.out.println("Naive code assumes failure = didn't happen, and might retry ANYWAY elsewhere -- risking a DOUBLE CHARGE.");
        }
    }
}
```

**How to run:** `javac NaiveUniformFailureHandling.java && java NaiveUniformFailureHandling` (JDK 17+).

### Level 2 — Intermediate

```java
// File: DistinguishFailureModes.java -- distinguishes the THREE failure
// modes explicitly, handling each with the appropriate level of caution.
import java.util.*;

public class DistinguishFailureModes {
    enum FailureMode { CONNECTION_REFUSED, TIMEOUT, ERROR_RESPONSE, SUCCESS }

    static FailureMode attemptCharge(String orderId, FailureMode simulatedOutcome) { return simulatedOutcome; }

    static void handleChargeAttempt(String orderId, FailureMode outcome) {
        switch (outcome) {
            case CONNECTION_REFUSED -> System.out.println("  CONNECTION_REFUSED: request never reached remote -- SAFE to retry");
            case TIMEOUT -> System.out.println("  TIMEOUT: UNKNOWN if processed -- do NOT blindly retry without an idempotency safeguard");
            case ERROR_RESPONSE -> System.out.println("  ERROR_RESPONSE: remote KNOWS it failed -- safe to retry per the error's nature");
            case SUCCESS -> System.out.println("  SUCCESS: confirmed -- do NOT retry");
        }
    }

    public static void main(String[] args) {
        for (FailureMode mode : FailureMode.values()) {
            System.out.println("Outcome: " + mode);
            handleChargeAttempt("order-42", mode);
        }
    }
}
```

**How to run:** `javac DistinguishFailureModes.java && java DistinguishFailureModes` (JDK 17+).

Expected output:
```
Outcome: CONNECTION_REFUSED
  CONNECTION_REFUSED: request never reached remote -- SAFE to retry
Outcome: TIMEOUT
  TIMEOUT: UNKNOWN if processed -- do NOT blindly retry without an idempotency safeguard
Outcome: ERROR_RESPONSE
  ERROR_RESPONSE: remote KNOWS it failed -- safe to retry per the error's nature
Outcome: SUCCESS
  SUCCESS: confirmed -- do NOT retry
```

### Level 3 — Advanced

```java
// File: IdempotencyKeyResolvesTimeoutAmbiguity.java -- uses an IDEMPOTENCY
// KEY so that even a TIMEOUT's ambiguity can be safely resolved by
// retrying -- the remote side recognizes a repeat and does NOT double-charge.
import java.util.*;

public class IdempotencyKeyResolvesTimeoutAmbiguity {
    // simulates the REMOTE service's own state, tracking which idempotency keys it has ALREADY processed
    static Map<String, Double> processedCharges = new HashMap<>();
    static int attemptNumber = 0;

    static double remoteChargeEndpoint(String idempotencyKey, double amount) {
        if (processedCharges.containsKey(idempotencyKey)) {
            System.out.println("  [remote] idempotency key already processed -- returning SAME result, NOT charging again");
            return processedCharges.get(idempotencyKey); // returns the ORIGINAL result, no new charge
        }
        processedCharges.put(idempotencyKey, amount); // FIRST time seeing this key -- process it for real
        System.out.println("  [remote] NEW charge processed for key " + idempotencyKey);
        return amount;
    }

    static double chargeWithRetryOnTimeout(String orderId, double amount) {
        String idempotencyKey = "charge-" + orderId; // STABLE across retries for the SAME logical operation
        attemptNumber++;

        if (attemptNumber == 1) {
            // simulate: the remote side actually PROCESSED it, but the response was LOST (a timeout)
            remoteChargeEndpoint(idempotencyKey, amount);
            System.out.println("  (response lost due to simulated timeout on attempt 1)");
            return chargeWithRetryOnTimeout(orderId, amount); // SAFE to retry -- same idempotency key
        }
        // attempt 2: the response actually arrives this time
        return remoteChargeEndpoint(idempotencyKey, amount);
    }

    public static void main(String[] args) {
        double result = chargeWithRetryOnTimeout("order-42", 25.00);
        System.out.println("Final charged amount: $" + result);
        System.out.println("Total DISTINCT charges recorded remotely: " + processedCharges.size() + " (NOT 2, despite 2 attempts)");
    }
}
```

**How to run:** `javac IdempotencyKeyResolvesTimeoutAmbiguity.java && java IdempotencyKeyResolvesTimeoutAmbiguity` (JDK 17+).

Expected output:
```
  [remote] NEW charge processed for key charge-order-42
  (response lost due to simulated timeout on attempt 1)
  [remote] idempotency key already processed -- returning SAME result, NOT charging again
Final charged amount: $25.0
Total DISTINCT charges recorded remotely: 1 (NOT 2, despite 2 attempts)
```

## 6. Walkthrough

1. **Level 1, the dangerous assumption** — `chargeAndMaybeLoseResponse` returns `true` on its first call, meaning the remote charge genuinely succeeded, but the surrounding code's structure (checking `!succeeded` before deciding to retry) shows the flawed mental model: real code following this same "just retry on any failure" instinct, without knowing the charge already succeeded, risks calling the charge endpoint a second time for the same order.
2. **Level 2, naming the distinct outcomes** — `FailureMode` enumerates the four genuinely different states a remote call attempt can end in, and `handleChargeAttempt` responds to each with a distinct, appropriate action rather than a single uniform "retry or don't" decision.
3. **Level 2, why TIMEOUT gets special treatment** — of the four cases, only `TIMEOUT` is printed with an explicit warning against blind retrying, because it's the one outcome that provides no information about whether the remote side actually completed the operation — `CONNECTION_REFUSED` at least indicates the request never arrived, and `ERROR_RESPONSE`/`SUCCESS` both indicate the remote side did respond with a definite outcome.
4. **Level 3, a stable key across retries** — `idempotencyKey` is derived deterministically from `orderId` alone (`"charge-" + orderId`), meaning every retry attempt for the *same* logical charge operation sends the *identical* key, letting the remote side recognize repeats regardless of how many times the client actually calls it.
5. **Level 3, the remote side's own deduplication** — `remoteChargeEndpoint` checks `processedCharges.containsKey(idempotencyKey)` *before* processing anything; on the first call for a given key it performs the real charge and records it, but on any subsequent call with the *same* key, it returns the previously recorded result without charging again — this is the mechanism that makes retrying after a timeout genuinely safe.
6. **Level 3, the full sequence and its outcome** — `chargeWithRetryOnTimeout`'s first attempt calls `remoteChargeEndpoint` (which actually processes the charge, exactly modeling the "processed but response lost" timeout scenario), then recursively retries; the second attempt calls `remoteChargeEndpoint` again with the identical `idempotencyKey`, and because that key is already in `processedCharges`, no second charge occurs — the final printed count of `1` distinct recorded charge, despite two total attempts, is the concrete proof that idempotency keys resolve exactly the ambiguity a bare timeout otherwise leaves unresolved.

## 7. Gotchas & takeaways

> **Gotcha:** idempotency keys only work if *both* sides honor them correctly — a remote endpoint that doesn't check for and deduplicate repeated keys provides no actual protection, no matter how carefully the calling side generates and reuses them; verify that any endpoint being retried against genuinely supports idempotency before relying on this pattern to make retries safe.

- Partial failure — where some components fail while others keep running, with genuine ambiguity about what a failed remote call actually accomplished — is the normal, expected condition of distributed systems, not an edge case.
- A remote call can fail in distinct ways (connection refused, timeout, error response), and each implies a different level of certainty about what the remote side actually did — treating them all identically is a common, serious mistake.
- A timeout specifically carries no information about whether the remote operation completed, making blind retries after a timeout risky for any non-idempotent operation like a payment charge.
- Idempotency keys let even a timeout's ambiguity be resolved safely, by letting the remote side recognize and deduplicate a retried request rather than processing it twice.
- Every resiliency pattern in the rest of this section exists specifically to handle this foundational uncertainty; understanding partial failure is the prerequisite for understanding why patterns like [circuit breakers](0248-circuit-breaker-pattern.md) and retries are designed the way they are.
