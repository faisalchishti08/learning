---
card: microservices
gi: 475
slug: spring-boot-graceful-shutdown-for-rolling-deploys
title: "Spring Boot graceful shutdown for rolling deploys"
---

## 1. What it is

**Graceful shutdown** is Spring Boot's built-in behavior (`server.shutdown=graceful`) where, on receiving a termination signal, the embedded web server **stops accepting new requests immediately but keeps running until in-flight requests finish** — up to a configurable grace period — rather than killing every request instantly the moment the process is told to stop. This turns an abrupt process termination into a clean, orderly wind-down.

## 2. Why & when

You enable graceful shutdown on any service that gets restarted as part of normal operations — which, under a [rolling deployment](0450-rolling-deployment.md), is constantly:

- **Every deploy kills and restarts instances.** Without graceful shutdown, any request in flight at the exact moment a container receives its termination signal gets abruptly cut off — the client sees a connection reset or an incomplete response, even though nothing was actually wrong with the request itself.
- **Rolling deployments happen far more often than crashes.** A crash is rare and somewhat expected to be disruptive; a routine deploy happens regularly and should be invisible to users — graceful shutdown is what makes routine restarts non-disruptive.
- **Kubernetes' own termination sequence assumes graceful handling.** Kubernetes sends `SIGTERM`, waits up to `terminationGracePeriodSeconds`, and only then sends `SIGKILL` if the process hasn't exited — that grace window exists specifically so an application *can* finish in-flight work before being forcibly killed, but only if the application actually uses it.
- **You want this enabled on every production service**, essentially without exception — it's a small, standard configuration change with a direct, meaningful reduction in user-visible errors during deploys.

## 3. Core concept

Think of a shop's closing procedure: when closing time arrives, the door is locked (no new customers let in) but the staff finishes serving whoever is already inside, rather than instantly kicking every customer out mid-transaction the second the clock strikes closing time. The shop still closes — it just closes in an orderly way that doesn't leave anyone with a half-finished purchase.

Concretely:

1. **A termination signal arrives** (`SIGTERM`, sent by Kubernetes when it decides to terminate a Pod, e.g. during a rolling deployment).
2. **The server immediately stops accepting new connections/requests** — anything arriving after this point is rejected or, more precisely, never routed to this instance at all once it's removed from the load balancer's routable set.
3. **Requests already in progress are allowed to complete normally**, running to their natural finish rather than being interrupted mid-execution.
4. **A grace period bounds how long this wind-down can take** (`spring.lifecycle.timeout-per-shutdown-phase`, and Kubernetes' own `terminationGracePeriodSeconds`) — if in-flight requests haven't finished by the deadline, the process is forcibly terminated anyway, so one slow request can't hang a deploy indefinitely.
5. **Once every in-flight request completes (or the grace period expires), the process exits cleanly**, and Kubernetes proceeds with the rest of its rolling deployment sequence.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="On SIGTERM, the server stops accepting new requests immediately but lets in-flight requests finish within a grace period before the process exits">
  <line x1="40" y1="110" x2="620" y2="110" stroke="#8b949e" stroke-width="1.5"/>
  <circle cx="60" cy="110" r="5" fill="#f85149"/>
  <text x="60" y="90" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">SIGTERM received</text>

  <rect x="90" y="130" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="165" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">stop accepting NEW requests</text>

  <rect x="260" y="60" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="360" y="84" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">in-flight requests finish normally</text>

  <circle cx="600" cy="110" r="5" fill="#6db33f"/>
  <text x="600" y="90" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">process exits cleanly</text>

  <text x="330" y="190" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">grace period bounds the wait -- SIGKILL forces exit if it's exceeded</text>
</svg>

New requests stop immediately at `SIGTERM`; in-flight requests get to finish within the grace period before the process actually exits.

## 5. Runnable example

Scenario: an in-memory request server simulating graceful shutdown behavior. We start with a basic immediate-shutdown baseline (the problem graceful shutdown fixes), extend it to accept-no-new/finish-in-flight behavior, then handle the hard case: a request that runs longer than the grace period, which must be forcibly cut off rather than hanging the shutdown indefinitely.

### Level 1 — Basic

```java
// File: AbruptShutdownBaseline.java -- models the PROBLEM graceful
// shutdown solves: a request IN FLIGHT when shutdown is triggered gets
// abruptly killed, with no chance to finish.
import java.util.concurrent.*;

public class AbruptShutdownBaseline {
    public static void main(String[] args) throws InterruptedException {
        ExecutorService server = Executors.newFixedThreadPool(4);

        server.submit(() -> {
            System.out.println("[request] started processing order-42, will take 200ms");
            try { Thread.sleep(200); } catch (InterruptedException e) {
                System.out.println("[request] INTERRUPTED mid-processing -- client gets a broken response");
                return;
            }
            System.out.println("[request] finished processing order-42 successfully");
        });

        Thread.sleep(50); // the request has only just started
        System.out.println("[shutdown] SIGTERM received -- shutting down ABRUPTLY, right now");
        server.shutdownNow(); // forcibly interrupts every running task immediately
        server.awaitTermination(1, TimeUnit.SECONDS);
        System.out.println("[shutdown] process exited");
    }
}
```

How to run: `java AbruptShutdownBaseline.java`

`server.shutdownNow()` is called only 50ms into a request that needs 200ms to finish, and it forcibly interrupts every running task immediately — the submitted task's `Thread.sleep(200)` throws `InterruptedException` well before it would have completed naturally, and the "INTERRUPTED mid-processing" branch runs instead of the successful-completion line, modeling exactly the abrupt cutoff graceful shutdown exists to prevent.

### Level 2 — Intermediate

```java
// File: GracefulShutdownBasic.java -- the SAME server, now with GRACEFUL
// shutdown: stop accepting NEW requests immediately, but let the
// IN-FLIGHT request finish normally before the process exits.
import java.util.concurrent.*;

public class GracefulShutdownBasic {
    static volatile boolean acceptingNewRequests = true;

    static void submitIfAccepting(ExecutorService server, String requestId, int durationMs) {
        if (!acceptingNewRequests) {
            System.out.println("[server] REJECTING " + requestId + " -- no longer accepting new requests");
            return;
        }
        server.submit(() -> {
            System.out.println("[request] started processing " + requestId + ", will take " + durationMs + "ms");
            try { Thread.sleep(durationMs); } catch (InterruptedException ignored) {}
            System.out.println("[request] finished processing " + requestId + " successfully");
        });
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService server = Executors.newFixedThreadPool(4);

        submitIfAccepting(server, "order-42", 200);
        Thread.sleep(50); // request is in flight

        System.out.println("[shutdown] SIGTERM received -- stop accepting NEW requests, let in-flight finish");
        acceptingNewRequests = false;
        submitIfAccepting(server, "order-99", 100); // arrives AFTER shutdown began -- rejected

        server.shutdown(); // graceful: lets already-submitted tasks run to completion
        server.awaitTermination(2, TimeUnit.SECONDS);
        System.out.println("[shutdown] process exited, in-flight work completed cleanly");
    }
}
```

How to run: `java GracefulShutdownBasic.java`

`acceptingNewRequests` flips to `false` the moment shutdown begins, and `submitIfAccepting` checks that flag before ever calling `server.submit` — `order-99`'s attempt, arriving after the flag flips, is rejected outright and never runs. `order-42`, already submitted before shutdown began, is untouched by the flag check entirely; `server.shutdown()` (not `shutdownNow()`) lets already-queued and already-running tasks finish naturally, so `order-42` completes successfully despite shutdown having already started.

### Level 3 — Advanced

```java
// File: GracefulShutdownWithGracePeriod.java -- the SAME graceful
// shutdown, now handling the PRODUCTION-FLAVORED hard case: an in-flight
// request that takes LONGER than the configured grace period. It must be
// forcibly cut off once the deadline passes -- otherwise one slow or
// stuck request could hang the entire deploy indefinitely, which is
// exactly the scenario terminationGracePeriodSeconds exists to bound.
import java.util.concurrent.*;

public class GracefulShutdownWithGracePeriod {
    static volatile boolean acceptingNewRequests = true;

    static void submitIfAccepting(ExecutorService server, String requestId, int durationMs) {
        if (!acceptingNewRequests) {
            System.out.println("[server] REJECTING " + requestId + " -- no longer accepting new requests");
            return;
        }
        server.submit(() -> {
            System.out.println("[request] started processing " + requestId + ", will take " + durationMs + "ms");
            try {
                Thread.sleep(durationMs);
                System.out.println("[request] finished processing " + requestId + " successfully");
            } catch (InterruptedException e) {
                System.out.println("[request] " + requestId + " FORCIBLY CUT OFF -- exceeded grace period");
            }
        });
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService server = Executors.newFixedThreadPool(4);
        int gracePeriodMs = 150; // like a short terminationGracePeriodSeconds, for a runnable demo

        submitIfAccepting(server, "order-fast", 50);   // will finish well within the grace period
        submitIfAccepting(server, "order-slow", 500);  // will NOT finish in time
        Thread.sleep(20); // both requests are now in flight

        System.out.println("[shutdown] SIGTERM received -- grace period is " + gracePeriodMs + "ms");
        acceptingNewRequests = false;
        server.shutdown(); // stop accepting new work, let in-flight work attempt to finish

        boolean finishedInTime = server.awaitTermination(gracePeriodMs, TimeUnit.MILLISECONDS);
        if (!finishedInTime) {
            System.out.println("[shutdown] grace period expired -- forcibly terminating remaining work");
            server.shutdownNow(); // the equivalent of Kubernetes escalating from SIGTERM to SIGKILL
        }
        System.out.println("[shutdown] process exited (finished gracefully: " + finishedInTime + ")");
    }
}
```

How to run: `java GracefulShutdownWithGracePeriod.java`

`order-fast` (50ms) and `order-slow` (500ms) are both submitted before shutdown begins, and `server.shutdown()` politely asks both to finish. `server.awaitTermination(gracePeriodMs, ...)` waits up to `150ms` — enough for `order-fast` to complete naturally, but not enough for `order-slow`, which is still running when the deadline passes. `awaitTermination` returns `false` in that case, triggering `server.shutdownNow()`, which forcibly interrupts `order-slow`'s still-running task — its `catch (InterruptedException e)` branch runs instead of its success line, exactly mirroring Kubernetes escalating from a polite `SIGTERM` to a forceful `SIGKILL` once `terminationGracePeriodSeconds` has elapsed.

## 6. Walkthrough

Trace `GracefulShutdownWithGracePeriod.main` in order. **First**, `order-fast` and `order-slow` are both submitted to the pool while `acceptingNewRequests` is still `true`, so both pass the check in `submitIfAccepting` and begin running concurrently on the thread pool.

**Next**, after a brief `20ms` sleep to let both tasks actually start, the shutdown sequence begins: `acceptingNewRequests` is set to `false`, and `server.shutdown()` is called — this stops the pool from accepting *new* submissions but does not interrupt the two tasks already running.

**Then**, `server.awaitTermination(150, TimeUnit.MILLISECONDS)` blocks for up to 150ms, during which `order-fast`'s 50ms sleep completes well within the window — its "finished processing" line prints, and that task's thread exits normally, contributing to (but not by itself satisfying) full pool termination.

**After that**, `order-slow`'s 500ms sleep is nowhere near finished when the 150ms deadline arrives, so `awaitTermination` returns `false` — the grace period genuinely expired with real work still in flight. The `if (!finishedInTime)` branch runs, printing the escalation message and calling `server.shutdownNow()`.

**Finally**, `shutdownNow()` interrupts every still-running task — `order-slow`'s `Thread.sleep(500)` throws `InterruptedException`, its `catch` block runs and prints the forcibly-cut-off message instead of a success line, and `main` prints the final exit line showing `finished gracefully: false`, honestly reporting that the grace period was exceeded rather than silently pretending the shutdown was clean.

```
[request] started processing order-fast, will take 50ms
[request] started processing order-slow, will take 500ms
[shutdown] SIGTERM received -- grace period is 150ms
[request] finished processing order-fast successfully
[shutdown] grace period expired -- forcibly terminating remaining work
[request] order-slow FORCIBLY CUT OFF -- exceeded grace period
[shutdown] process exited (finished gracefully: false)
```

(The two "started processing" lines can print in either order, since both tasks are submitted to the pool almost simultaneously and their thread scheduling isn't guaranteed — but `order-fast` always finishes and `order-slow` is always the one forcibly cut off, regardless of print order.)

## 7. Gotchas & takeaways

> A grace period set too short for your slowest realistic request means every deploy forcibly cuts off legitimate, still-processing work — set `terminationGracePeriodSeconds` (and Spring's matching shutdown timeout) generously enough to cover your genuine worst-case request duration, not just the typical case.
- Graceful shutdown only helps if the *load balancer* also removes the instance from routing before, or at the same time as, the server stops accepting requests — otherwise new requests can still be routed to an instance that's mid-shutdown and rejecting them.
- This pairs directly with [readiness probes](0473-spring-boot-actuator-liveness-readiness-probes-for-kubernete.md): a well-behaved shutdown sequence often flips readiness to "not ready" first, giving Kubernetes a moment to stop routing new traffic before the `SIGTERM`-driven in-flight drain even begins.
- `server.shutdown()` versus `server.shutdownNow()` in the Java concurrency API is a direct, useful mental model for the same distinction Kubernetes makes between `SIGTERM` (graceful) and `SIGKILL` (forced) — one lets existing work finish, the other cuts it off immediately.
- Long-running requests (large file uploads, long-polling connections) deserve special consideration — a grace period tuned for typical fast API calls may be far too short for these, and might need a different draining strategy entirely.
- Test graceful shutdown deliberately, not just assume it works — send a request, trigger a shutdown mid-request, and confirm the client actually receives a complete, successful response rather than a connection error.
