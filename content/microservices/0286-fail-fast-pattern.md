---
card: microservices
gi: 286
slug: fail-fast-pattern
title: "Fail fast pattern"
---

## 1. What it is

The fail-fast pattern, in a resiliency context, means rejecting a request or aborting an operation at the *earliest possible point* once it's known to be doomed or invalid — before spending any real resources (threads, connections, downstream calls) on work that cannot succeed. This is distinct from the general fail-fast-vs-fail-silent [philosophy](0283-fail-fast-vs-fail-silent.md) about whether to surface errors loudly; this pattern is specifically about *when* in the request's lifecycle the rejection happens: as close to the entry point as possible, rather than deep inside a call chain after resources have already been committed.

## 2. Why & when

Every step a request takes before failing — acquiring a connection, entering a thread pool, calling a downstream service, waiting on a lock — costs resources that are then wasted if the request was always going to fail anyway. Under load, this waste compounds: if 30% of incoming requests are invalid or targeting a known-unhealthy dependency, letting all of them proceed partway through expensive processing before failing means the system is spending real capacity on work with zero chance of succeeding, capacity that could have served the other 70% of legitimate requests instead.

Fail-fast checks belong at the boundary of a component, checked *before* any expensive work begins: input validation, authentication/authorization, a already-open [circuit breaker](0250-circuit-breaker-pattern.md) for a known-unhealthy dependency, or a [bulkhead](0267-bulkhead-pattern.md)/[rate limiter](0273-rate-limiter-pattern.md) that's already at capacity. Use it anywhere a cheap, early check can definitively rule out success, so that capacity is reserved for requests that actually have a chance.

## 3. Core concept

Order matters: cheap, definitive checks run first and reject immediately; expensive work only starts once every cheap check has passed.

```java
Response handle(Request request) {
    if (!isValid(request)) return reject(400, "invalid request");        // CHEAPEST check first
    if (!isAuthorized(request)) return reject(403, "not authorized");    // still cheap, no I/O
    if (circuitBreaker.getState() == State.OPEN) return reject(503, "dependency known unhealthy"); // no network call attempted
    if (!bulkhead.tryAcquire()) return reject(503, "at capacity");        // no thread/connection consumed
    // ONLY NOW, after every cheap check passed, do the expensive work:
    return callExpensiveDownstreamService(request);
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A chain of cheap checks runs first, each able to reject the request immediately and cheaply; only once every cheap check passes does the expensive downstream work begin, so resources are never wasted on requests that were always going to fail">
  <rect x="20" y="60" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="65" y="84" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">validate</text>

  <rect x="130" y="60" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="175" y="84" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">authorize</text>

  <rect x="240" y="60" width="110" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="295" y="84" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">circuit open?</text>

  <rect x="370" y="60" width="90" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="415" y="84" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">capacity?</text>

  <rect x="480" y="60" width="130" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="84" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">expensive call</text>

  <line x1="110" y1="80" x2="130" y2="80" stroke="#8b949e" marker-end="url(#arr286)"/>
  <line x1="220" y1="80" x2="240" y2="80" stroke="#8b949e" marker-end="url(#arr286)"/>
  <line x1="350" y1="80" x2="370" y2="80" stroke="#8b949e" marker-end="url(#arr286)"/>
  <line x1="460" y1="80" x2="480" y2="80" stroke="#8b949e" marker-end="url(#arr286)"/>

  <text x="65" y="120" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">reject: cheapest</text>
  <text x="545" y="120" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">only reached once ALL checks pass</text>
  <defs><marker id="arr286" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Cheap checks run first and can reject immediately; the expensive work only ever runs once every cheap check has passed.

## 5. Runnable example

Scenario: a request handler that validates input only after already having made an expensive downstream call, extended to reorder checks so cheap validation happens first, and finally adding a full ordered chain — validation, authorization, a circuit-breaker check, and a capacity check — all before the expensive call, measuring how much wasted work is avoided under a realistic mixed workload.

### Level 1 — Basic

```java
// File: LateValidationWastesWork.java -- the expensive downstream call
// happens BEFORE the cheap input validation, so invalid requests still
// pay the full cost of the expensive call before being rejected.
public class LateValidationWastesWork {
    static int expensiveCallCount = 0;
    static String callExpensiveDownstream(String payload) {
        expensiveCallCount++;
        try { Thread.sleep(50); } catch (InterruptedException ignored) {} // simulate real work
        return "processed:" + payload;
    }

    static boolean isValid(String payload) { return payload != null && !payload.isBlank(); }

    static String handle(String payload) {
        String result = callExpensiveDownstream(payload); // WASTEFUL: runs even for invalid input
        if (!isValid(payload)) return "400 Bad Request";
        return "200 OK: " + result;
    }

    public static void main(String[] args) {
        String[] requests = { "valid-1", "", null, "valid-2", "  " };
        for (String req : requests) System.out.println("Request '" + req + "' -> " + handle(req));
        System.out.println("Expensive calls made: " + expensiveCallCount + " (for " + requests.length + " requests, 3 of which were invalid)");
    }
}
```

How to run: `java LateValidationWastesWork.java`

Five requests come in, three of them invalid (empty, null, blank). But `handle` calls the expensive downstream operation *before* checking validity, so all five requests — including the three that were always going to be rejected — pay the full 50ms cost of the expensive call. The expensive-call counter reads 5, even though only 2 requests could ever have succeeded.

### Level 2 — Intermediate

```java
// File: EarlyValidationSavesWork.java -- the SAME requests, but
// validation now runs FIRST; invalid requests are rejected immediately
// and never reach the expensive call.
public class EarlyValidationSavesWork {
    static int expensiveCallCount = 0;
    static String callExpensiveDownstream(String payload) {
        expensiveCallCount++;
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return "processed:" + payload;
    }

    static boolean isValid(String payload) { return payload != null && !payload.isBlank(); }

    static String handle(String payload) {
        if (!isValid(payload)) return "400 Bad Request"; // FAIL FAST: cheapest check, first
        String result = callExpensiveDownstream(payload); // only reached for VALID input
        return "200 OK: " + result;
    }

    public static void main(String[] args) {
        String[] requests = { "valid-1", "", null, "valid-2", "  " };
        for (String req : requests) System.out.println("Request '" + req + "' -> " + handle(req));
        System.out.println("Expensive calls made: " + expensiveCallCount + " (for " + requests.length + " requests, 3 of which were invalid)");
    }
}
```

How to run: `java EarlyValidationSavesWork.java`

Same five requests, same three invalid ones, but `handle` now checks `isValid` before anything else. The three invalid requests are rejected in microseconds without ever touching `callExpensiveDownstream`. The expensive-call counter reads 2 instead of 5 — exactly matching the two genuinely valid requests, eliminating 100% of the wasted work the previous version incurred.

### Level 3 — Advanced

```java
// File: FullFailFastChain.java -- a complete ordered chain: validation,
// authorization, a circuit-breaker check, and a capacity check, ALL
// before the expensive call, run over a realistic mixed batch of
// requests to show the cumulative savings.
import java.util.concurrent.atomic.AtomicInteger;

public class FullFailFastChain {
    enum CircuitState { CLOSED, OPEN }
    static CircuitState circuitState = CircuitState.CLOSED;
    static final int capacity = 3;
    static AtomicInteger inFlight = new AtomicInteger(0);
    static AtomicInteger expensiveCallCount = new AtomicInteger(0);

    record Request(String payload, boolean authorized) {}

    static boolean isValid(Request r) { return r.payload() != null && !r.payload().isBlank(); }

    static String callExpensiveDownstream(String payload) {
        expensiveCallCount.incrementAndGet();
        return "processed:" + payload;
    }

    static String handle(Request request) {
        if (!isValid(request)) return "400 Bad Request";                          // cheapest: no I/O, no locks
        if (!request.authorized()) return "403 Forbidden";                        // still cheap
        if (circuitState == CircuitState.OPEN) return "503 Dependency Unhealthy"; // no network attempted
        if (inFlight.get() >= capacity) return "503 At Capacity";                 // no thread/connection consumed
        inFlight.incrementAndGet();
        try {
            return "200 OK: " + callExpensiveDownstream(request.payload());       // ONLY reached after all checks pass
        } finally {
            inFlight.decrementAndGet();
        }
    }

    public static void main(String[] args) {
        circuitState = CircuitState.OPEN; // simulate: downstream dependency is currently known-unhealthy
        Request[] requests = {
                new Request("", true),               // fails validation
                new Request("payload-1", false),      // fails authorization
                new Request("payload-2", true),       // would pass both, but circuit is OPEN
                new Request(null, true),               // fails validation
        };
        for (Request r : requests) System.out.println("Request " + r + " -> " + handle(r));
        System.out.println("Expensive calls made: " + expensiveCallCount.get()
                + " (zero, because the circuit was OPEN -- the dependency was fully protected)");
    }
}
```

How to run: `java FullFailFastChain.java`

Four requests are sent while `circuitState` is deliberately set to `OPEN`, simulating a known-unhealthy downstream dependency. The first request fails at the validation check (empty payload). The second fails at the authorization check. The third would have passed both of those, but is caught by the circuit-breaker check before any network attempt is made. The fourth fails validation again (null payload). Every single request is rejected by a cheap, in-memory check — the expensive-call counter stays at 0 for the entire batch, meaning the already-struggling downstream dependency received zero additional load from this batch, exactly the outcome fail-fast ordering is meant to produce.

## 6. Walkthrough

Trace `FullFailFastChain.main` in order for the third request, `new Request("payload-2", true)` — the interesting case, since it is valid and authorized and would otherwise proceed. **First**, `handle` checks `isValid(request)`: `payload()` is `"payload-2"`, non-null and non-blank, so this check passes and execution continues.

**Next**, `handle` checks `request.authorized()`: `true`, so this check also passes.

**Next**, `handle` checks `circuitState == CircuitState.OPEN`. Because `main` set `circuitState = CircuitState.OPEN` before sending any requests (modeling a dependency already known to be unhealthy from a prior [circuit breaker](0250-circuit-breaker-pattern.md) trip), this check evaluates to `true`, and `handle` immediately returns `"503 Dependency Unhealthy"` — without ever incrementing `inFlight`, without ever calling `callExpensiveDownstream`, and without making any network attempt at all.

**Contrast with what would happen without this ordering**: if the circuit-breaker check were placed *after* the expensive call (or omitted), this exact same request would have proceeded to call the already-struggling dependency, adding load to a system that is already failing — precisely the kind of pile-on that turns one dependency's partial failure into a fleet-wide cascading failure.

**For the fourth request**, `new Request(null, true)`, execution never even reaches the authorization or circuit-breaker checks: `isValid` immediately returns `false` because `payload()` is `null`, and `handle` returns `"400 Bad Request"` on the very first line of meaningful logic.

**Final state**: across all four requests, `expensiveCallCount` remains at 0 — every single one was rejected by a cheap, purely in-memory check before reaching the point where it would have consumed a connection slot or added load to the unhealthy dependency.

```
request -> isValid()? --no--> 400 (cheapest, returns here)
              |yes
           authorized()? --no--> 403
              |yes
           circuit OPEN? --yes--> 503 (no network attempted)
              |no (closed)
           capacity available? --no--> 503
              |yes
           [ONLY NOW] expensive downstream call -> 200 OK
```

## 7. Gotchas & takeaways

> Ordering the checks matters as much as having them — a validation check placed after an expensive call provides zero resource protection, even though the request is still eventually rejected "correctly." Fail-fast is about *when* the rejection happens, not just *that* it happens.

- Order checks from cheapest/most-certain to most-expensive: input validation and authorization (pure CPU, no I/O) before circuit-breaker and capacity checks (still cheap, in-memory) before the actual expensive call.
- A fail-fast check that references a circuit breaker's current state, rather than attempting the call and catching the resulting failure, avoids even the overhead of a doomed network attempt — this is the specific mechanism by which an open circuit breaker protects both the caller and the struggling dependency.
- Fail-fast checks compound: in a request that fans out to several dependencies, failing fast on the first known-bad one avoids wasting time and resources on the others that would have run in parallel or in sequence after it.
- This pattern is complementary to, not a replacement for, [fallback methods](0282-fallback-methods-default-responses.md) — a fail-fast rejection can itself be followed by a fallback (e.g., cached data) rather than a bare error, combining both patterns for the best outcome.
