---
card: microservices
gi: 300
slug: spring-boot-graceful-shutdown
title: "Spring Boot graceful shutdown"
---

## 1. What it is

Graceful shutdown is the process by which a Spring Boot application, upon receiving a termination signal, stops accepting *new* requests but allows *in-flight* requests to finish processing (up to a configured timeout) before the process actually exits. Spring Boot supports this natively via `server.shutdown=graceful` (paired with a configured `spring.lifecycle.timeout-per-shutdown-phase`), rather than the default abrupt shutdown, where in-flight requests are simply cut off mid-processing the instant the process receives its termination signal.

## 2. Why & when

Modern deployment platforms (Kubernetes, most container orchestrators) routinely terminate instances during normal operation — scaling down, rolling deployments, node maintenance — by sending a termination signal and expecting the process to exit within a grace period. Without graceful shutdown, every one of these routine terminations abruptly kills whatever requests happen to be mid-flight at that exact moment, producing user-visible errors (a dropped connection, an incomplete response) purely as a side effect of normal, planned infrastructure operations — not an actual outage.

Graceful shutdown eliminates this class of self-inflicted failure: the application stops accepting new connections immediately (so the orchestrator's traffic-draining and this shutdown coordinate correctly) but lets already-accepted requests complete normally, up to a bounded timeout, before exiting. This is essential for anything doing rolling deployments, autoscaling, or routine instance replacement — which describes essentially every production Spring Boot service running on modern infrastructure. Use it always, tuned with a timeout appropriate to the service's typical and worst-case request duration.

## 3. Core concept

```yaml
server:
  shutdown: graceful   # instead of the default "immediate"
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s   # maximum time to wait for in-flight requests before forcing exit
```

```java
// Conceptual behavior Spring Boot's embedded server implements internally
// once graceful shutdown is enabled -- application code doesn't write this,
// but understanding it clarifies what actually happens on SIGTERM.
class GracefulShutdownCoordinator {
    volatile boolean acceptingNewRequests = true;
    final java.util.concurrent.atomic.AtomicInteger inFlightRequests = new java.util.concurrent.atomic.AtomicInteger(0);

    void onShutdownSignal(long timeoutMillis) throws InterruptedException {
        acceptingNewRequests = false;              // STOP accepting NEW requests immediately
        long deadline = System.currentTimeMillis() + timeoutMillis;
        while (inFlightRequests.get() > 0 && System.currentTimeMillis() < deadline) {
            Thread.sleep(50); // WAIT for in-flight requests to drain, up to the timeout
        }
        // proceed with actual JVM exit here, whether drained cleanly or timed out
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="On a termination signal, the server immediately stops accepting new connections while already in-flight requests continue processing normally; once all in-flight requests complete, or a configured timeout elapses, the process exits, avoiding abruptly cutting off requests that were already underway">
  <line x1="30" y1="80" x2="610" y2="80" stroke="#8b949e"/>
  <text x="150" y="30" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">SIGTERM received</text>
  <line x1="150" y1="35" x2="150" y2="75" stroke="#e6edf3" stroke-dasharray="2,2"/>

  <rect x="30" y="60" width="120" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="84" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">accepting new requests</text>

  <rect x="150" y="60" width="200" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="250" y="78" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">NEW requests REJECTED</text>
  <text x="250" y="92" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">in-flight requests still DRAINING</text>

  <line x1="350" y1="80" x2="450" y2="80" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="400" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">drained or timeout</text>

  <rect x="450" y="60" width="120" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="84" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">process exits</text>
</svg>

New requests are rejected immediately on shutdown signal; already in-flight work drains before the process actually exits.

## 5. Runnable example

Scenario: an abrupt shutdown that cuts off in-flight work the instant a termination signal is simulated, extended to a graceful shutdown that stops accepting new work but lets in-flight work finish, and finally adding a bounded timeout so a stuck or unusually slow in-flight request cannot delay shutdown forever, matching the real `timeout-per-shutdown-phase` behavior.

### Level 1 — Basic

```java
// File: AbruptShutdown.java -- simulates the DEFAULT (non-graceful)
// shutdown: the instant a termination signal arrives, ALL in-flight
// work is simply abandoned, regardless of how close to completion it was.
import java.util.concurrent.*;

public class AbruptShutdown {
    public static void main(String[] args) throws InterruptedException {
        ExecutorService server = Executors.newFixedThreadPool(4);
        // Simulate 3 in-flight requests, each needing 500ms to complete.
        for (int i = 1; i <= 3; i++) {
            int reqId = i;
            server.submit(() -> {
                try { Thread.sleep(500); System.out.println("  Request " + reqId + " COMPLETED normally"); }
                catch (InterruptedException e) { System.out.println("  Request " + reqId + " ABANDONED mid-flight!"); }
            });
        }

        Thread.sleep(100); // termination signal arrives 100ms in, while requests are still running
        System.out.println("SIGTERM received -- shutting down IMMEDIATELY (default behavior)");
        server.shutdownNow(); // interrupts EVERY running task instantly, no draining
        server.awaitTermination(1, TimeUnit.SECONDS);
        System.out.println("Process exited.");
    }
}
```

How to run: `java AbruptShutdown.java`

Three simulated requests each need 500ms to finish, but the termination signal arrives after only 100ms. `shutdownNow()` interrupts every running task immediately — the output shows all three requests being "ABANDONED mid-flight" instead of completing, exactly what happens to real in-flight HTTP requests when a Spring Boot app with the default (non-graceful) shutdown receives SIGTERM during normal Kubernetes pod termination.

### Level 2 — Intermediate

```java
// File: GracefulShutdownDrains.java -- simulates server.shutdown=graceful:
// on the termination signal, NEW work is rejected immediately, but
// ALREADY in-flight requests are allowed to finish normally.
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class GracefulShutdownDrains {
    static AtomicBoolean acceptingNewRequests = new AtomicBoolean(true);

    public static void main(String[] args) throws InterruptedException {
        ExecutorService server = Executors.newFixedThreadPool(4);
        for (int i = 1; i <= 3; i++) {
            int reqId = i;
            server.submit(() -> {
                try { Thread.sleep(500); System.out.println("  Request " + reqId + " COMPLETED normally (allowed to finish)"); }
                catch (InterruptedException e) { System.out.println("  Request " + reqId + " interrupted"); }
            });
        }

        Thread.sleep(100); // termination signal arrives while requests are in-flight
        System.out.println("SIGTERM received -- GRACEFUL shutdown starting");
        acceptingNewRequests.set(false); // reject NEW requests from this point

        // A new request attempted DURING shutdown:
        if (!acceptingNewRequests.get()) {
            System.out.println("  New request during shutdown: REJECTED (server draining, not accepting new work)");
        }

        server.shutdown(); // do NOT interrupt running tasks -- let them finish
        boolean drainedCleanly = server.awaitTermination(2, TimeUnit.SECONDS); // wait for in-flight work
        System.out.println("Drained cleanly: " + drainedCleanly + " -- process exits now.");
    }
}
```

How to run: `java GracefulShutdownDrains.java`

The same three 500ms requests are already running when the simulated SIGTERM arrives at 100ms. This time, `acceptingNewRequests` is flipped to `false` immediately (any *new* request attempted after this point is rejected, as shown by the explicit check), but `server.shutdown()` (not `shutdownNow()`) is used, which lets already-submitted tasks run to completion. `awaitTermination(2, TimeUnit.SECONDS)` waits up to 2 seconds — comfortably more than the 400ms remaining on the longest in-flight request — so all three requests print "COMPLETED normally," and `drainedCleanly` is `true`.

### Level 3 — Advanced

```java
// File: GracefulShutdownWithTimeout.java -- adds a BOUNDED timeout
// (mirroring spring.lifecycle.timeout-per-shutdown-phase): if in-flight
// work does NOT drain within the configured window, the process exits
// anyway rather than waiting indefinitely for a stuck or unusually slow request.
import java.util.concurrent.*;

public class GracefulShutdownWithTimeout {
    public static void main(String[] args) throws InterruptedException {
        ExecutorService server = Executors.newFixedThreadPool(4);
        // One request is NORMAL (500ms); one is ABNORMALLY SLOW (5000ms, e.g. a stuck downstream call).
        server.submit(() -> {
            try { Thread.sleep(500); System.out.println("  Request A COMPLETED normally within the timeout"); }
            catch (InterruptedException e) { System.out.println("  Request A interrupted"); }
        });
        server.submit(() -> {
            try { Thread.sleep(5000); System.out.println("  Request B COMPLETED (this line should NOT print -- exceeds timeout)"); }
            catch (InterruptedException e) { System.out.println("  Request B force-interrupted after exceeding the shutdown timeout"); }
        });

        Thread.sleep(100);
        System.out.println("SIGTERM received -- graceful shutdown, timeout-per-shutdown-phase=1500ms");
        server.shutdown();

        long timeoutMillis = 1500; // configured maximum grace period
        boolean drainedCleanly = server.awaitTermination(timeoutMillis, TimeUnit.MILLISECONDS);
        if (!drainedCleanly) {
            System.out.println("Timeout of " + timeoutMillis + "ms EXCEEDED -- forcing remaining in-flight work to stop");
            server.shutdownNow(); // force-interrupt whatever is STILL running past the grace period
        }
        System.out.println("Process exits now. Drained cleanly within timeout: " + drainedCleanly);
    }
}
```

How to run: `java GracefulShutdownWithTimeout.java`

Request A (500ms) comfortably finishes within the configured 1500ms grace period and prints its "COMPLETED normally" message. Request B (5000ms) does not — after the full 1500ms timeout elapses with Request B still running, `awaitTermination` returns `false`, and the code falls back to `server.shutdownNow()`, force-interrupting Request B, which then prints its "force-interrupted" message instead of its completion message. This mirrors exactly what `spring.lifecycle.timeout-per-shutdown-phase` enforces in a real Spring Boot application: graceful shutdown waits for in-flight work, but only up to a bounded maximum — an unusually slow or genuinely stuck request cannot hold up shutdown indefinitely and delay a rolling deployment or scale-down operation.

## 6. Walkthrough

Trace `GracefulShutdownWithTimeout.main` in order. **First**, two tasks are submitted to a 4-thread pool: Request A (sleeps 500ms) and Request B (sleeps 5000ms), both starting to run immediately on separate pool threads.

**At 100ms**, the main thread wakes from its own `Thread.sleep(100)`, simulating the arrival of a termination signal, and prints the shutdown-starting message.

**`server.shutdown()` is called** — critically, this is the non-forceful shutdown method: it stops the pool from accepting *new* submissions but does not interrupt tasks already running. Both Request A and Request B continue executing exactly as if nothing happened.

**`server.awaitTermination(1500, TimeUnit.MILLISECONDS)` is called**, blocking the main thread for up to 1500ms or until all pool tasks finish, whichever comes first.

**At around 500ms of total elapsed time** (400ms after `awaitTermination` started waiting), Request A's `Thread.sleep(500)` completes, it prints "COMPLETED normally within the timeout," and its pool thread becomes idle — but the pool as a whole is still not terminated, since Request B is still running.

**At 1500ms of waiting** (the full timeout), Request B is still asleep (it needs 5000ms total, of which only about 1600ms of real time has elapsed since it started). `awaitTermination` gives up and returns `false`.

**Back in `main`**, `drainedCleanly` is `false`, so the `if (!drainedCleanly)` branch executes: it prints the "Timeout EXCEEDED" message and calls `server.shutdownNow()` — this time, the forceful variant, which sends an interrupt to every still-running task. Request B's `Thread.sleep(5000)` is interrupted partway through, throwing `InterruptedException`, caught by its own `catch` block, which prints "force-interrupted after exceeding the shutdown timeout" instead of ever reaching its intended completion message.

**Finally**, `main` prints the closing summary line showing `drainedCleanly=false`, and the process would exit — Request A completed cleanly within the grace period, but Request B, exceeding it, was forcibly cut off, exactly the bounded-but-not-indefinite behavior `timeout-per-shutdown-phase` is designed to provide.

```
t=0ms:    Request A and B both start
t=100ms:  SIGTERM simulated -- server.shutdown() called, no new work accepted, A and B continue
t=500ms:  Request A finishes normally
t=1600ms: awaitTermination(1500ms) times out -- B still running -- shutdownNow() force-interrupts B
```

## 7. Gotchas & takeaways

> A `timeout-per-shutdown-phase` set too short can abort legitimately-in-progress work that would have finished on its own moments later, while one set too long can delay rolling deployments and cause the orchestrator's own termination grace period to expire first, resulting in a hard `SIGKILL` that skips graceful shutdown's cleanup entirely. Tune it to comfortably exceed the service's typical (and reasonable worst-case) request duration, but keep it well under the orchestrator's own termination grace period.

- `server.shutdown=graceful` is not enabled by default in Spring Boot; it must be explicitly configured, alongside a `spring.lifecycle.timeout-per-shutdown-phase` appropriate to the service's actual request durations.
- Graceful shutdown eliminates a whole class of self-inflicted errors caused by routine, planned infrastructure operations (rolling deploys, autoscaling, node maintenance) rather than genuine outages — this makes it high-value for essentially every production service.
- The orchestrator's own termination grace period (e.g., Kubernetes' `terminationGracePeriodSeconds`) must be configured to exceed the application's `timeout-per-shutdown-phase`, or the orchestrator will `SIGKILL` the process before graceful shutdown's own timeout has a chance to complete its bounded wait.
- Graceful shutdown pairs naturally with [health checks for self-healing](0290-health-checks-for-self-healing.md): a well-behaved readiness probe should start failing the instant shutdown begins (before new-request rejection even happens at the server level), so the orchestrator stops routing new traffic to the terminating instance as early as possible.
