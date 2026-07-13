---
card: microservices
gi: 444
slug: graceful-startup-shutdown
title: "Graceful startup & shutdown"
---

## 1. What it is

**Graceful startup** means a service doesn't advertise itself as ready to receive traffic until it genuinely is — connections to its database established, caches warmed, dependent clients initialized — so an orchestrator or load balancer never routes a request to an instance that can't yet handle it. **Graceful shutdown** means a service, on receiving a termination signal, stops accepting *new* work immediately but finishes any *in-flight* requests before actually exiting, rather than dropping active connections mid-response. Both are about the same underlying problem from opposite ends of an instance's lifecycle: never let the outside world assume an instance is available when it isn't actually able to do the work correctly.

## 2. Why & when

These disciplines matter every single time an instance starts or stops — which, in an autoscaled, frequently-deployed microservices fleet, happens constantly:

- **Rolling deployments depend on it.** A rolling update replaces old instances with new ones a few at a time; if a new instance is added to the load balancer's pool before it's actually ready, or an old instance is removed before it finishes in-flight requests, users experience errors during every single deployment, not just rare edge cases.
- **Autoscaling depends on it.** When an orchestrator scales a fleet down (e.g., after a traffic spike subsides), the instances chosen for termination may well have active connections — a hard kill drops those requests; a graceful shutdown lets them complete first.
- **Fast, correct startup avoids a "thundering restart" failure mode.** If a service reports itself healthy before its database connection pool is actually established, early requests fail, retries pile up, and the resulting load can make the still-initializing instance's problem worse, not better.
- **Container orchestrators send a real signal you must handle.** Kubernetes sends `SIGTERM` and then waits a configurable grace period before sending `SIGKILL` if the process hasn't exited — an application that ignores `SIGTERM` gets forcibly killed mid-request every single time, losing whatever was in flight.

You need graceful startup and shutdown on every service that runs behind a load balancer or under an orchestrator's control — which, again, is essentially every containerized microservice — because the alternative isn't a rare failure mode, it's a *guaranteed* one that fires on every deploy, every scale event, and every instance replacement.

## 3. Core concept

Think of a shop with a "closing soon" sign versus one that just slams the door at closing time regardless of who's still inside. A graceful shop puts up a "no new customers" sign at closing time but lets everyone already inside finish shopping and check out — nobody gets locked in mid-purchase, and nobody who arrives after the sign goes up wastes a trip walking in only to be turned away at the register. A store that just locks the door at the stroke of closing, with customers still mid-checkout, forces those customers to abandon their carts entirely.

Concretely, both halves work through explicit lifecycle signaling:

1. **Startup: readiness is separate from "the process is running."** A process can be running (its main method has started, the JVM is alive) while still being unready (database connection pool not yet established, caches not yet warmed). An orchestrator should only route traffic once *readiness* is confirmed, not merely once the process has started — this is the distinction behind [health checks for orchestrators](0445-health-checks-for-orchestrators.md)'s separate liveness and readiness probes.
2. **Shutdown: stop accepting new work, then wait for existing work to finish.** On receiving `SIGTERM`, a service should immediately mark itself not-ready (so the load balancer stops routing new requests to it), reject any brand-new incoming connections, but let requests already in flight run to completion, up to a bounded grace period.
3. **A grace period is a deadline, not a suggestion.** If in-flight work genuinely can't finish within the configured grace period, the orchestrator will forcibly kill the process (`SIGKILL`) regardless — graceful shutdown logic should aim to finish well inside that window, and log or track any requests that had to be abandoned when the window closed.
4. **The orchestrator and the application cooperate.** The orchestrator removes an instance from load-balancer routing *before* sending `SIGTERM` (giving in-flight connections a head start on draining) and waits a grace period before force-killing; the application handles `SIGTERM` by draining and exiting cleanly *before* that grace period elapses.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Startup sequence: process starts, dependencies initialize, readiness flips true, traffic is routed. Shutdown sequence: SIGTERM received, readiness flips false, new traffic stops, in-flight requests drain, process exits before the grace period ends" >
  <text x="160" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Graceful startup</text>
  <rect x="30" y="35" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="59" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">process starts</text>
  <rect x="140" y="35" width="90" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="185" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">deps init</text>
  <text x="185" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">not ready yet</text>
  <rect x="250" y="35" width="90" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="295" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">readiness=true</text>
  <text x="295" y="66" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">now takes traffic</text>
  <line x1="120" y1="55" x2="140" y2="55" stroke="#8b949e"/>
  <line x1="230" y1="55" x2="250" y2="55" stroke="#8b949e"/>

  <text x="480" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Graceful shutdown</text>
  <rect x="360" y="35" width="80" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="400" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SIGTERM</text>
  <text x="400" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">readiness=false</text>
  <rect x="450" y="35" width="80" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="490" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">drain</text>
  <text x="490" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">finish in-flight</text>
  <rect x="540" y="35" width="80" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="580" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">exit(0)</text>
  <text x="580" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">before grace ends</text>
  <line x1="440" y1="55" x2="450" y2="55" stroke="#8b949e"/>
  <line x1="530" y1="55" x2="540" y2="55" stroke="#8b949e"/>

  <line x1="30" y1="110" x2="620" y2="110" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">readiness flips true only once genuinely able to serve; flips false the instant shutdown begins</text>
  <text x="320" y="148" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">SIGKILL fires if shutdown isn't done before the grace period elapses -- design to finish well inside it</text>
</svg>

Readiness gates traffic on the way in during startup, and gates traffic off immediately during shutdown, while in-flight work drains safely within a bounded grace period.

## 5. Runnable example

Scenario: an `order-service` instance's full lifecycle. We model startup readiness gating first, then shutdown that drains in-flight requests, then a production-flavored case: a shutdown hook racing against a hard grace-period deadline, correctly abandoning work that genuinely can't finish in time rather than hanging forever.

### Level 1 — Basic

```java
// File: StartupReadinessBasic.java -- models the CORE idea: "process is
// running" and "process is ready for traffic" are DIFFERENT states, and
// only the second should let the load balancer route requests in.
public class StartupReadinessBasic {
    static class OrderServiceInstance {
        volatile boolean processRunning = false;
        volatile boolean ready = false;

        void start() throws InterruptedException {
            processRunning = true;
            System.out.println("Process started -- but NOT yet accepting traffic.");

            System.out.println("Initializing database connection pool...");
            Thread.sleep(50); // simulated connection setup time
            System.out.println("Warming caches...");
            Thread.sleep(30); // simulated cache warm-up time

            ready = true;
            System.out.println("Readiness=true -- load balancer may now route traffic here.");
        }

        String handleRequest(String orderId) {
            if (!ready) {
                return "503 Service Unavailable -- not ready yet";
            }
            return "200 OK -- processed " + orderId;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        OrderServiceInstance instance = new OrderServiceInstance();

        // A request that arrives BEFORE start() completes -- simulating a
        // premature health check or race in a naive deployment.
        System.out.println("Early request result: " + instance.handleRequest("order-1"));

        instance.start();

        System.out.println("Post-startup request result: " + instance.handleRequest("order-2"));
    }
}
```

How to run: `java StartupReadinessBasic.java`

`processRunning` and `ready` are tracked as separate flags — exactly the distinction between Kubernetes's liveness and readiness. A request arriving before `start()` finishes correctly gets a `503`, because `ready` is still `false` even though the process object already exists; only after the simulated connection pool and cache warm-up complete does `ready` flip `true`, and subsequent requests succeed.

### Level 2 — Intermediate

```java
// File: GracefulDrainIntermediate.java -- the SAME instance, now handling
// SHUTDOWN: on a termination signal, stop accepting NEW work immediately,
// but let IN-FLIGHT work finish before exiting.
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class GracefulDrainIntermediate {
    static class OrderServiceInstance {
        volatile boolean ready = true;
        volatile boolean shuttingDown = false;
        final AtomicInteger inFlightRequests = new AtomicInteger(0);

        String handleRequest(String orderId) throws InterruptedException {
            if (shuttingDown) {
                return "503 Service Unavailable -- draining, not accepting new work";
            }
            inFlightRequests.incrementAndGet();
            try {
                System.out.println("[" + orderId + "] processing started, in-flight=" + inFlightRequests.get());
                Thread.sleep(80); // simulated work
                return "200 OK -- processed " + orderId;
            } finally {
                inFlightRequests.decrementAndGet();
                System.out.println("[" + orderId + "] processing finished, in-flight=" + inFlightRequests.get());
            }
        }

        void shutdown() throws InterruptedException {
            System.out.println("SIGTERM received -- entering shutdown");
            ready = false;         // stop being routed NEW traffic
            shuttingDown = true;   // reject any brand-new request that slips through anyway
            System.out.println("Waiting for " + inFlightRequests.get() + " in-flight request(s) to finish...");
            while (inFlightRequests.get() > 0) {
                Thread.sleep(10);
            }
            System.out.println("All in-flight requests finished. Exiting cleanly.");
        }
    }

    public static void main(String[] args) throws Exception {
        OrderServiceInstance instance = new OrderServiceInstance();
        ExecutorService pool = Executors.newFixedThreadPool(2);

        // Two requests already in flight when the shutdown signal arrives.
        Future<String> f1 = pool.submit(() -> instance.handleRequest("order-1"));
        Future<String> f2 = pool.submit(() -> instance.handleRequest("order-2"));
        Thread.sleep(20); // let them get into "processing" before we trigger shutdown

        instance.shutdown();

        System.out.println("order-1 result: " + f1.get());
        System.out.println("order-2 result: " + f2.get());
        System.out.println("Late request during shutdown: " + instance.handleRequest("order-3"));

        pool.shutdown();
    }
}
```

How to run: `java GracefulDrainIntermediate.java`

`shutdown()` immediately flips `ready` and `shuttingDown` to signal no new work should arrive, then busy-waits until `inFlightRequests` drops to zero before printing that it's exiting cleanly. Because `order-1` and `order-2` were already inside `handleRequest`'s try block when `shutdown()` was called, they're allowed to finish normally (their `finally` block correctly decrements the counter); `order-3`, submitted *after* shutdown began, is immediately rejected with a `503` rather than being accepted and then abandoned.

### Level 3 — Advanced

```java
// File: ShutdownWithGracePeriodAdvanced.java -- the SAME drain logic, now
// handling a PRODUCTION-FLAVORED hard case: a HARD grace-period deadline.
// If in-flight work doesn't finish in time, shutdown must proceed anyway
// (the orchestrator will SIGKILL regardless) -- logging what was abandoned
// rather than hanging forever waiting for work that will never finish.
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.*;

public class ShutdownWithGracePeriodAdvanced {
    static class OrderServiceInstance {
        volatile boolean shuttingDown = false;
        final AtomicInteger inFlightRequests = new AtomicInteger(0);
        final Set<String> stuckRequestIds = ConcurrentHashMap.newKeySet();

        String handleRequest(String orderId, long simulatedWorkMs) throws InterruptedException {
            if (shuttingDown) return "503 Service Unavailable -- draining";
            inFlightRequests.incrementAndGet();
            stuckRequestIds.add(orderId);
            try {
                Thread.sleep(simulatedWorkMs);
                return "200 OK -- processed " + orderId;
            } finally {
                inFlightRequests.decrementAndGet();
                stuckRequestIds.remove(orderId);
            }
        }

        // Returns true if shutdown finished cleanly within the grace period,
        // false if the grace period elapsed with work still outstanding.
        boolean shutdown(long gracePeriodMs) throws InterruptedException {
            System.out.println("SIGTERM received -- grace period = " + gracePeriodMs + "ms");
            shuttingDown = true;
            long deadline = System.currentTimeMillis() + gracePeriodMs;

            while (inFlightRequests.get() > 0 && System.currentTimeMillis() < deadline) {
                Thread.sleep(10);
            }

            if (inFlightRequests.get() == 0) {
                System.out.println("Drained cleanly within the grace period.");
                return true;
            } else {
                System.out.println("GRACE PERIOD EXCEEDED: " + inFlightRequests.get()
                        + " request(s) still in flight and will be forcibly terminated by SIGKILL: " + stuckRequestIds);
                return false;
            }
        }
    }

    public static void main(String[] args) throws Exception {
        OrderServiceInstance instance = new OrderServiceInstance();
        ExecutorService pool = Executors.newFixedThreadPool(3);

        Future<String> quick = pool.submit(() -> instance.handleRequest("order-quick", 30));
        // A pathological, slow request -- e.g. stuck on a downstream call
        // that's hanging -- takes far longer than any reasonable grace period.
        Future<String> stuck = pool.submit(() -> instance.handleRequest("order-stuck-on-downstream", 5000));
        Thread.sleep(15);

        boolean cleanShutdown = instance.shutdown(200); // realistic grace period, e.g. Kubernetes terminationGracePeriodSeconds

        System.out.println("Shutdown completed cleanly: " + cleanShutdown);
        System.out.println("quick request result: " + quick.get());
        // We do NOT wait for 'stuck' -- in production, the process would
        // already have been SIGKILLed; we just report what was abandoned.
        System.out.println("stuck request: abandoned, never completed within the grace period.");

        pool.shutdownNow();
    }
}
```

How to run: `java ShutdownWithGracePeriodAdvanced.java`

The hard case is that graceful shutdown cannot wait indefinitely — `shutdown(gracePeriodMs)` computes a hard `deadline` and stops waiting once it passes, even if `inFlightRequests` is still nonzero. `order-quick` (30ms of work) finishes comfortably inside the 200ms grace period; `order-stuck-on-downstream` (5000ms of simulated work, standing in for a request hung on a slow or unresponsive downstream dependency) does not, and `shutdown` correctly returns `false`, logging exactly which request IDs were still outstanding when time ran out — the same information a real orchestrator's forced-kill log entry should let you correlate back to.

## 6. Walkthrough

Trace `ShutdownWithGracePeriodAdvanced.main` in order. **First**, `quick` is submitted with `simulatedWorkMs = 30` and `stuck` with `simulatedWorkMs = 5000`; both call `handleRequest`, which increments `inFlightRequests` to `2` and adds both order IDs to `stuckRequestIds` before starting their respective `Thread.sleep` calls.

**Next**, after a 15ms pause (long enough for both requests to have started, short enough that neither has finished), `instance.shutdown(200)` is called. It immediately sets `shuttingDown = true` and computes `deadline` as roughly 200ms from now. The `while` loop then polls every 10ms, checking both `inFlightRequests.get() > 0` and whether the deadline has passed.

**Then**, at around 15ms into the wait, `order-quick`'s `Thread.sleep(30)` completes (its own timeline started slightly before shutdown was called, so it finishes around the 30ms mark overall) — its `finally` block decrements `inFlightRequests` to `1` and removes `"order-quick"` from `stuckRequestIds`. The `while` loop keeps polling, because `inFlightRequests` is still `1` (from `order-stuck-on-downstream`) and the 200ms deadline hasn't passed yet.

**Finally**, once roughly 200ms have elapsed, the loop's deadline condition becomes false, so it exits even though `inFlightRequests.get()` is still `1`. `shutdown` checks `inFlightRequests.get() == 0`, finds it's not, prints the "GRACE PERIOD EXCEEDED" message naming `order-stuck-on-downstream` specifically (via `stuckRequestIds`), and returns `false`. `main` prints `cleanShutdown` as `false`, `quick.get()` as its successful result, and notes that `stuck` was abandoned rather than waited for — mirroring exactly what happens in production when Kubernetes's own grace period elapses and issues a `SIGKILL` regardless of what the application was still doing.

```
SIGTERM received -- grace period = 200ms
GRACE PERIOD EXCEEDED: 1 request(s) still in flight and will be forcibly terminated by SIGKILL: [order-stuck-on-downstream]
Shutdown completed cleanly: false
quick request result: 200 OK -- processed order-quick
stuck request: abandoned, never completed within the grace period.
```

## 7. Gotchas & takeaways

> A common, subtle bug is flipping readiness to "not ready" only *after* starting the drain wait, rather than immediately upon receiving the termination signal — this leaves a window where the load balancer keeps sending fresh traffic to an instance that's already trying to shut down, extending the drain time and sometimes never letting it finish before the grace period expires. Always flip readiness to false as the very first action in a shutdown handler, before anything else.

- Readiness and "the process has started" are different states; gate traffic on readiness, not merely on the process being alive — this is the core mechanism behind [health checks for orchestrators](0445-health-checks-for-orchestrators.md)'s separate liveness and readiness probes.
- A graceful shutdown handler must set a hard deadline and stop waiting once it passes — the orchestrator's grace period is enforced with a `SIGKILL` regardless of what your application is doing, so design to finish comfortably inside it, not to use all of it.
- Set the configured grace period meaningfully longer than your typical request duration, but not so long that a genuinely stuck instance blocks a deployment or scale-down for an unreasonable amount of time.
- These lifecycle disciplines are direct expressions of the [twelve-factor app principles](0442-twelve-factor-app-principles.md)'s disposability factor — fast startup and graceful shutdown are what make instances cheap to create and destroy on demand.
- In Spring Boot, `server.shutdown=graceful` combined with a configured `spring.lifecycle.timeout-per-shutdown-phase` implements most of this drain-then-exit behavior directly, and Actuator's readiness/liveness health groups implement the startup half — prefer these built-ins over hand-rolled lifecycle management.
