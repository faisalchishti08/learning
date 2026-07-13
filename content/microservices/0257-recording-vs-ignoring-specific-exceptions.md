---
card: microservices
gi: 257
slug: recording-vs-ignoring-specific-exceptions
title: "Recording vs ignoring specific exceptions"
---

## 1. What it is

Recording versus ignoring specific exceptions is a circuit breaker configuration that classifies which thrown exception types should count toward the tracked [failure rate](0250-failure-rate-threshold.md) and which should be explicitly excluded — not every exception a protected call throws actually indicates the dependency itself is unhealthy, and treating all of them uniformly as "failures" can trip a breaker for the wrong reason entirely.

## 2. Why & when

A call can fail for reasons that have nothing to do with the dependency's actual health — a request rejected because it failed input validation (a client error, not a server problem), a business-rule exception like "insufficient inventory" (an entirely expected, valid outcome the calling code needs to handle, not a sign anything is broken) — and counting these toward the breaker's failure rate conflates "the dependency is unhealthy" with "this particular request was invalid or represented a legitimate business outcome." A breaker that can't distinguish these will trip based on a spike of perfectly ordinary validation errors or expected business exceptions, cutting off traffic to a dependency that's actually working exactly as intended.

Explicitly configure which exception types should be ignored (not counted as failures) whenever a protected call can throw exceptions representing expected, non-health-related outcomes — validation failures, business rule violations, "not found" results modeled as exceptions. Exceptions genuinely indicating the dependency's unavailability or malfunction (connection failures, timeouts, server errors) should always be recorded as real failures.

## 3. Core concept

The breaker checks each thrown exception's type against a configured `ignoreExceptions` (or equivalent) list before deciding whether to count it toward the failure rate — an ignored exception still propagates normally to the caller (the business logic handling it is unaffected), it simply doesn't contribute to the breaker's health tracking.

```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .recordExceptions(ConnectException.class, SocketTimeoutException.class, ServerErrorException.class) // COUNT these as failures
    .ignoreExceptions(ValidationException.class, InsufficientInventoryException.class) // do NOT count these -- expected outcomes
    .build();

// a call throwing InsufficientInventoryException:
// -- STILL propagates normally to the caller, who handles it as an expected business outcome
// -- does NOT increment the breaker's tracked failure count AT ALL
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two different exceptions thrown by a protected call are both propagated to the caller, but only the connection failure is recorded toward the breaker's tracked failure rate; the business rule exception, though it still reaches the caller, is explicitly ignored by the breaker's health tracking" >
  <rect x="20" y="65" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Protected call</text>

  <rect x="220" y="20" width="180" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ConnectException -- RECORDED</text>

  <rect x="220" y="110" width="180" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="310" y="135" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">InsufficientInventory -- IGNORED</text>

  <rect x="460" y="65" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Caller (both propagate)</text>

  <line x1="160" y1="85" x2="218" y2="40" stroke="#8b949e" marker-end="url(#arr257)"/>
  <line x1="160" y1="85" x2="218" y2="130" stroke="#8b949e" marker-end="url(#arr257)"/>
  <line x1="400" y1="40" x2="458" y2="80" stroke="#8b949e" marker-end="url(#arr257)"/>
  <line x1="400" y1="130" x2="458" y2="90" stroke="#8b949e" marker-end="url(#arr257)"/>
</svg>

Both exceptions reach the caller normally; only the one indicating actual dependency unhealthiness feeds the breaker's tracking.

## 5. Runnable example

Scenario: a breaker that treats every thrown exception uniformly as a failure, incorrectly tripping from a burst of ordinary validation errors, refactored to explicitly ignore validation and business-rule exceptions while still recording genuine dependency-health exceptions, and finally demonstrating both exception categories occurring together, with only the health-indicating one contributing to the tracked failure rate.

### Level 1 — Basic

```java
// File: EveryExceptionCountsAsFailure.java -- treats ANY thrown
// exception identically as a "failure" -- a burst of ORDINARY
// validation errors incorrectly trips the breaker.
public class EveryExceptionCountsAsFailure {
    static class ValidationException extends RuntimeException { ValidationException(String m) { super(m); } }
    static boolean breakerOpen = false;
    static int consecutiveFailures = 0;

    static String processOrder(boolean validInput) {
        if (!validInput) throw new ValidationException("missing required field"); // an EXPECTED, ORDINARY outcome
        return "order processed";
    }

    static String protectedCall(boolean validInput) {
        if (breakerOpen) return "REJECTED (breaker open)";
        try {
            return processOrder(validInput);
        } catch (RuntimeException e) {
            if (++consecutiveFailures >= 3) breakerOpen = true; // counts EVERY exception, even validation errors
            throw e;
        }
    }

    public static void main(String[] args) {
        for (int i = 0; i < 3; i++) {
            try { protectedCall(false); } catch (ValidationException e) { System.out.println("Client sent bad input #" + (i + 1) + ": " + e.getMessage()); }
        }
        System.out.println("Breaker state: " + (breakerOpen ? "OPEN (tripped from ORDINARY validation errors, not a real outage!)" : "CLOSED"));
    }
}
```

**How to run:** `javac EveryExceptionCountsAsFailure.java && java EveryExceptionCountsAsFailure` (JDK 17+).

Expected output:
```
Client sent bad input #1: missing required field
Client sent bad input #2: missing required field
Client sent bad input #3: missing required field
Breaker state: OPEN (tripped from ORDINARY validation errors, not a real outage!)
```

### Level 2 — Intermediate

```java
// File: IgnoredExceptionsDontCount.java -- ValidationException is
// explicitly IGNORED by the breaker's health tracking; it still
// propagates normally, but does NOT count toward tripping.
public class IgnoredExceptionsDontCount {
    static class ValidationException extends RuntimeException { ValidationException(String m) { super(m); } }
    static class DependencyConnectionException extends RuntimeException { DependencyConnectionException(String m) { super(m); } }

    static boolean breakerOpen = false;
    static int consecutiveFailures = 0;

    static String processOrder(boolean validInput) {
        if (!validInput) throw new ValidationException("missing required field");
        return "order processed";
    }

    static boolean isIgnoredByBreaker(RuntimeException e) {
        return e instanceof ValidationException; // EXPLICITLY classified as NOT a health signal
    }

    static String protectedCall(boolean validInput) {
        if (breakerOpen) return "REJECTED (breaker open)";
        try {
            return processOrder(validInput);
        } catch (RuntimeException e) {
            if (!isIgnoredByBreaker(e)) { // ONLY non-ignored exceptions count
                if (++consecutiveFailures >= 3) breakerOpen = true;
            }
            throw e; // STILL propagates normally either way -- the caller still needs to handle it
        }
    }

    public static void main(String[] args) {
        for (int i = 0; i < 3; i++) {
            try { protectedCall(false); } catch (ValidationException e) { System.out.println("Client sent bad input #" + (i + 1) + " (still handled normally by caller)"); }
        }
        System.out.println("Breaker state: " + (breakerOpen ? "OPEN" : "CLOSED (correctly NOT tripped -- these were validation errors, not dependency failures)"));
    }
}
```

**How to run:** `javac IgnoredExceptionsDontCount.java && java IgnoredExceptionsDontCount` (JDK 17+).

Expected output:
```
Client sent bad input #1 (still handled normally by caller)
Client sent bad input #2 (still handled normally by caller)
Client sent bad input #3 (still handled normally by caller)
Breaker state: CLOSED (correctly NOT tripped -- these were validation errors, not dependency failures)
```

### Level 3 — Advanced

```java
// File: MixedExceptionsOnlyRealFailuresCount.java -- a MIX of ignored
// and recorded exceptions occurring together -- ONLY the ones actually
// indicating dependency unhealthiness contribute toward tripping.
public class MixedExceptionsOnlyRealFailuresCount {
    static class ValidationException extends RuntimeException { ValidationException(String m) { super(m); } }
    static class DependencyConnectionException extends RuntimeException { DependencyConnectionException(String m) { super(m); } }

    static boolean breakerOpen = false;
    static int consecutiveRealFailures = 0;
    static int totalCallsSeen = 0;
    static int ignoredCount = 0;

    static boolean isIgnoredByBreaker(RuntimeException e) { return e instanceof ValidationException; }

    static String protectedCall(int callIndex) {
        totalCallsSeen++;
        if (breakerOpen) return "REJECTED (breaker open)";
        try {
            // simulate a MIX: calls 0,2,4 are validation errors; calls 1,3,5 are genuine connection failures
            if (callIndex % 2 == 0) throw new ValidationException("bad input on call " + callIndex);
            else throw new DependencyConnectionException("connection refused on call " + callIndex);
        } catch (RuntimeException e) {
            if (isIgnoredByBreaker(e)) {
                ignoredCount++;
                System.out.println("  call " + callIndex + ": " + e.getClass().getSimpleName() + " -- IGNORED, doesn't count");
            } else {
                consecutiveRealFailures++;
                System.out.println("  call " + callIndex + ": " + e.getClass().getSimpleName() + " -- RECORDED as failure #" + consecutiveRealFailures);
                if (consecutiveRealFailures >= 3) breakerOpen = true;
            }
            return "handled: " + e.getClass().getSimpleName();
        }
    }

    public static void main(String[] args) {
        for (int i = 0; i < 6; i++) protectedCall(i);
        System.out.println("\nTotal calls: " + totalCallsSeen + ", ignored (validation): " + ignoredCount + ", real failures recorded: " + consecutiveRealFailures);
        System.out.println("Breaker: " + (breakerOpen ? "OPEN (tripped by the 3 GENUINE connection failures, NOT the 3 validation errors mixed in)" : "CLOSED"));
    }
}
```

**How to run:** `javac MixedExceptionsOnlyRealFailuresCount.java && java MixedExceptionsOnlyRealFailuresCount` (JDK 17+).

Expected output:
```
  call 0: ValidationException -- IGNORED, doesn't count
  call 1: DependencyConnectionException -- RECORDED as failure #1
  call 2: ValidationException -- IGNORED, doesn't count
  call 3: DependencyConnectionException -- RECORDED as failure #2
  call 4: ValidationException -- IGNORED, doesn't count
  call 5: DependencyConnectionException -- RECORDED as failure #3

Total calls: 6, ignored (validation): 3, real failures recorded: 3
Breaker: OPEN (tripped by the 3 GENUINE connection failures, NOT the 3 validation errors mixed in)
```

## 6. Walkthrough

1. **Level 1, the undifferentiated counting** — `protectedCall`'s `catch` block increments `consecutiveFailures` for *any* caught `RuntimeException`, including `ValidationException`, which represents nothing more than a client sending malformed input — three such ordinary validation errors incorrectly cross the trip threshold, incorrectly declaring the breaker open even though the dependency itself never had any actual problem.
2. **Level 2, classifying exceptions explicitly** — `isIgnoredByBreaker` checks whether the caught exception is a `ValidationException`, and `protectedCall`'s `catch` block only increments `consecutiveFailures` when that check returns `false`; critically, `throw e` still executes unconditionally afterward, meaning the caller still receives and must handle the `ValidationException` exactly as before — only the breaker's internal health tracking is affected by the classification.
3. **Level 2, the correct outcome** — running the identical three-validation-error scenario from Level 1 through this classification-aware logic correctly leaves the breaker `CLOSED`, since none of the three exceptions were counted toward `consecutiveFailures` at all.
4. **Level 3, a realistic mix of both categories** — `protectedCall` alternates between throwing `ValidationException` (even-indexed calls) and `DependencyConnectionException` (odd-indexed calls), modeling a realistic production scenario where both ordinary client errors and genuine dependency problems occur interleaved with each other.
5. **Level 3, each exception type handled according to its classification** — the printed log shows each call's exception type and, for `ValidationException`, an explicit "IGNORED" label, while `DependencyConnectionException` occurrences are labeled "RECORDED as failure #N," with that counter incrementing only for the latter category.
6. **Level 3, the breaker tripping for the right reason** — after all six calls, exactly three `DependencyConnectionException` occurrences have been recorded (crossing the threshold of 3 and tripping the breaker), while the three interleaved `ValidationException` occurrences contributed nothing to that count — the final printed summary makes explicit that the breaker tripped specifically because of genuine connection failures, not because of the validation errors that happened to occur alongside them, which is exactly the correct, discriminating behavior this configuration is designed to produce.

## 7. Gotchas & takeaways

> **Gotcha:** ignoring an exception type for circuit-breaker purposes doesn't mean ignoring it entirely — as both examples show, the exception still propagates normally to the caller, who must still handle it as a real outcome (a validation failure still needs to be reported to whoever sent the bad input); "ignored" here specifically means "excluded from the breaker's health tracking," not "suppressed" or "swallowed," and conflating those two meanings is an easy misunderstanding when first configuring this behavior.

- Recording versus ignoring specific exceptions lets a circuit breaker distinguish exceptions that genuinely indicate dependency unhealthiness from ones representing expected outcomes like validation failures or business rule violations.
- Treating every exception type uniformly as a "failure" risks tripping the breaker based on ordinary, expected error conditions that have nothing to do with the dependency's actual health.
- An ignored exception still propagates normally to the caller, exactly as before — the classification only affects whether it's counted toward the breaker's internal failure-rate tracking, not whether the caller receives and handles it.
- This configuration should be applied deliberately per exception type, distinguishing genuine health signals (connection failures, timeouts, server errors) from expected business or validation outcomes.
- Misclassifying "ignored for breaker purposes" as "suppressed entirely" is a common point of confusion — the two are distinct, and getting this wrong either hides a real failure from the breaker or accidentally swallows an exception the caller actually needed to see.
