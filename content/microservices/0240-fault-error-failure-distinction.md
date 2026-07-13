---
card: microservices
gi: 240
slug: fault-error-failure-distinction
title: "Fault, error, failure distinction"
---

## 1. What it is

Fault, error, and failure name three distinct stages in how something goes wrong in a system: a *fault* is the underlying defect or condition (a bug, a disk filling up, a network cable failing), an *error* is the incorrect internal state that fault causes (a corrupted variable, a stuck connection), and a *failure* is the externally observable deviation from correct behavior that results (a request returning the wrong answer, or none at all) — a fault only becomes a failure if it isn't contained before reaching the system's boundary.

## 2. Why & when

Conflating these three terms — treating "a bug exists," "the system is in a bad state," and "the system visibly misbehaves" as the same thing — makes it hard to reason precisely about where resilience mechanisms should intervene. The distinction matters because most resilience techniques work specifically by breaking the chain between one stage and the next: a fault doesn't have to become an error if it's detected and handled (a null check catching a bad input before it corrupts state), and an error doesn't have to become an externally visible failure if it's contained (a [circuit breaker](0248-circuit-breaker-pattern.md) failing fast internally rather than letting a slow, degraded dependency cause a visible timeout for the end user). Precision about which stage a given resilience mechanism operates on clarifies what it actually protects against.

Use this three-stage vocabulary when designing or reasoning about resilience mechanisms — asking "does this technique prevent a fault, contain an error, or just handle a failure gracefully after it's already visible" clarifies what a given pattern actually buys a system, and where the gaps in a resilience strategy are.

## 3. Core concept

The chain runs fault → error → failure, and each stage can either be *contained* (stopped from propagating to the next stage) or *propagate* (become the next, more visible stage); most defensive code exists specifically to break this chain at one of these two transition points.

```java
// FAULT: the underlying defect -- a null value slipping into a field that shouldn't be null
String customerEmail = fetchCustomerEmail(customerId); // returns null due to a data issue -- this IS the fault

// if UNHANDLED, the fault becomes an ERROR: incorrect internal state
String domain = customerEmail.split("@")[1]; // NullPointerException -- internal state is now broken

// if the ERROR propagates further, it becomes a FAILURE: externally visible misbehavior
// -- e.g. an HTTP 500 returned to the end user, or a silently corrupted database row

// CONTAINING the fault BEFORE it becomes an error:
if (customerEmail == null) {
    log.warn("customer {} has no email on file", customerId); // FAULT handled -- no error, no failure
    return DEFAULT_DOMAIN;
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A fault progresses toward becoming an error and then a failure unless it is contained at one of the two transition points -- fault to error, or error to failure" >
  <rect x="20" y="65" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Fault</text>

  <rect x="255" y="65" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Error</text>

  <rect x="490" y="65" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Failure (visible)</text>

  <line x1="150" y1="87" x2="253" y2="87" stroke="#8b949e" marker-end="url(#arr240)"/>
  <line x1="385" y1="87" x2="488" y2="87" stroke="#8b949e" marker-end="url(#arr240)"/>

  <text x="200" y="40" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">contained here: no error</text>
  <line x1="200" y1="45" x2="200" y2="63" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr240g)"/>

  <text x="435" y="40" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">contained here: no failure</text>
  <line x1="435" y1="45" x2="435" y2="63" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr240g)"/>

  <defs>
    <marker id="arr240" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arr240g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Resilience mechanisms work by intervening at one of these two transition points, stopping the chain from progressing further.

## 5. Runnable example

Scenario: an order-total calculation where a data fault flows uncontained all the way to a visible failure, refactored to contain the fault at the first transition point (preventing an error state), and finally showing a second layer that contains an error that does occur, preventing it from becoming a visible failure — demonstrating containment at both transition points in the same scenario.

### Level 1 — Basic

```java
// File: FaultPropagatesUncontained.java -- a FAULT (a missing discount
// rate) flows unchecked all the way to a visible FAILURE.
public class FaultPropagatesUncontained {
    static Double lookupDiscountRate(String customerId) { return null; } // FAULT: data issue, returns null

    static double calculateTotal(String customerId, double subtotal) {
        Double discountRate = lookupDiscountRate(customerId); // FAULT enters here
        return subtotal * (1 - discountRate); // ERROR: unboxing null -- NullPointerException
    }

    public static void main(String[] args) {
        try {
            double total = calculateTotal("cust-1", 100.0);
            System.out.println("Total: " + total);
        } catch (NullPointerException e) {
            System.out.println("FAILURE: request crashed with " + e.getClass().getSimpleName() + " -- visible to the caller as a 500 error");
        }
    }
}
```

**How to run:** `javac FaultPropagatesUncontained.java && java FaultPropagatesUncontained` (JDK 17+).

### Level 2 — Intermediate

```java
// File: FaultContainedBeforeError.java -- the SAME fault is now CAUGHT
// and HANDLED before it can corrupt internal state -- no error, no failure.
public class FaultContainedBeforeError {
    static Double lookupDiscountRate(String customerId) { return null; } // the SAME underlying fault

    static double calculateTotal(String customerId, double subtotal) {
        Double discountRate = lookupDiscountRate(customerId);
        if (discountRate == null) { // CONTAIN the fault HERE -- before it becomes an error
            System.out.println("  [contained] no discount rate on file for " + customerId + " -- defaulting to 0%");
            discountRate = 0.0;
        }
        return subtotal * (1 - discountRate); // internal state is now CORRECT -- no error occurred
    }

    public static void main(String[] args) {
        double total = calculateTotal("cust-1", 100.0);
        System.out.println("Total: " + total + " (computed successfully -- the fault never became a visible failure)");
    }
}
```

**How to run:** `javac FaultContainedBeforeError.java && java FaultContainedBeforeError` (JDK 17+).

Expected output:
```
  [contained] no discount rate on file for cust-1 -- defaulting to 0%
Total: 100.0 (computed successfully -- the fault never became a visible failure)
```

### Level 3 — Advanced

```java
// File: ErrorContainedBeforeFailure.java -- a DIFFERENT fault (a downstream
// service returning malformed data) DOES cause an internal ERROR, but a
// SECOND containment layer catches THAT error before it becomes a
// visible FAILURE -- containment at the SECOND transition point instead.
public class ErrorContainedBeforeFailure {
    // simulates a downstream pricing service occasionally returning MALFORMED data -- the FAULT
    static String fetchRawDiscountRate(String customerId) { return "not-a-number"; }

    static double parseDiscountRate(String customerId) { // this method can ITSELF produce an ERROR
        String raw = fetchRawDiscountRate(customerId);
        return Double.parseDouble(raw); // throws NumberFormatException -- an ERROR: bad internal state about to form
    }

    static double calculateTotalSafely(String customerId, double subtotal) {
        double discountRate;
        try {
            discountRate = parseDiscountRate(customerId); // the ERROR occurs INSIDE this call
        } catch (NumberFormatException e) {
            // CONTAIN the error HERE -- before it propagates out as a visible FAILURE
            System.out.println("  [contained] malformed discount rate for " + customerId + " -- defaulting to 0%, error NOT propagated");
            discountRate = 0.0;
        }
        return subtotal * (1 - discountRate);
    }

    public static void main(String[] args) {
        double total = calculateTotalSafely("cust-1", 100.0);
        System.out.println("Total: " + total + " (the underlying fault caused an internal error, but it was contained -- no visible failure)");
    }
}
```

**How to run:** `javac ErrorContainedBeforeFailure.java && java ErrorContainedBeforeFailure` (JDK 17+).

Expected output:
```
  [contained] malformed discount rate for cust-1 -- defaulting to 0%, error NOT propagated
Total: 100.0 (the underlying fault caused an internal error, but it was contained -- no visible failure)
```

## 6. Walkthrough

1. **Level 1, the full uncontained chain** — `lookupDiscountRate` returning `null` is the *fault*; `subtotal * (1 - discountRate)` attempting to unbox that `null` and throwing `NullPointerException` is the *error* (internal state — the method's execution — is now broken); the caught exception printed as a message to the (simulated) end user is the *failure* — the point where the problem becomes externally visible.
2. **Level 2, containing at the fault-to-error boundary** — `calculateTotal` explicitly checks `discountRate == null` immediately after the fault-producing call, before that value is used in any computation; because the check happens *before* the null value can be involved in an operation that would throw, the fault is contained and no error state (a thrown exception, a corrupted computation) ever occurs.
3. **Level 2, the clean outcome** — `calculateTotal` returns a normal, correct-looking result (`100.0`, using a 0% default), and nothing about the method's execution or its caller's experience indicates anything went wrong internally — this is containment at the *first* transition point: fault contained, so no error, so certainly no failure.
4. **Level 3, a fault that does become an error** — `parseDiscountRate` receives malformed data (`"not-a-number"`) from `fetchRawDiscountRate` (the fault) and calls `Double.parseDouble` on it directly, with no check beforehand — this call throws `NumberFormatException`, meaning the fault *did* progress into an error this time, unlike Level 2's contained case.
5. **Level 3, containing at the error-to-failure boundary instead** — `calculateTotalSafely` wraps the call to `parseDiscountRate` in a `try`/`catch` block; when the `NumberFormatException` (the error) is thrown, the `catch` block intercepts it before it can propagate out of `calculateTotalSafely` itself, substituting a safe default value instead of letting the exception continue upward to whatever called `calculateTotalSafely`.
6. **Level 3, the same clean outward result via a different containment point** — despite an error genuinely occurring internally this time (unlike Level 2, where no error happened at all), `calculateTotalSafely`'s caller sees the identical outcome as Level 2: a successfully computed total, with no visible sign that anything went wrong — demonstrating that containment can happen at either transition point (fault-to-error, as in Level 2, or error-to-failure, as in Level 3) and still achieve the same ultimate goal of preventing a visible failure, though catching earlier (Level 2's approach) is generally preferable since it avoids the error state's disruption (a thrown exception, an aborted computation) altogether.

## 7. Gotchas & takeaways

> **Gotcha:** containing an error to prevent a visible failure (as Level 3 does) is strictly better than an uncontained failure, but it's not "free" — the exception was still thrown, the stack was still unwound, and if this happens frequently under load, the overhead and log noise from repeatedly hitting and catching the same avoidable error can itself become a performance or observability problem; where practical, prefer containing at the fault stage (validating before use, as Level 2 does) over containing at the error stage (catching after the fact, as Level 3 does).

- A fault is the underlying defect or bad condition; an error is the resulting corrupted internal state; a failure is the externally visible misbehavior that results if neither is contained.
- Most resilience mechanisms work by intervening at one of the two transition points — preventing a fault from becoming an error, or preventing an error from becoming a visible failure.
- Containing earlier (at the fault stage, via validation) is generally preferable to containing later (at the error stage, via exception handling), since it avoids the disruption of the error state occurring at all.
- This vocabulary sharpens design discussions: asking which stage a given resilience technique actually protects against clarifies what it buys a system and where gaps remain.
- Frequently hitting and catching the same avoidable error, even when successfully contained, still carries real cost (exception overhead, log noise) and is a signal that containing further upstream, at the fault stage, would be worth the refactor.
