---
card: spring-boot
gi: 254
slug: graceful-shutdown-in-production
title: Graceful shutdown in production
---

## 1. What it is

**Graceful shutdown** means the application finishes all in-flight requests before terminating, rather than dropping them mid-processing when the process receives a shutdown signal.

Spring Boot 2.3+ ships built-in graceful shutdown support, enabled with a single property:

```properties
server.shutdown=graceful
spring.lifecycle.timeout-per-shutdown-phase=30s
```

When the JVM receives `SIGTERM` (the standard stop signal from systemd, Kubernetes, Docker, and cloud platforms), Spring Boot:

1. **Refuses new requests** — the embedded server (Tomcat/Netty/Undertow/Jetty) stops accepting new connections immediately.
2. **Waits** for active requests to complete, up to `timeout-per-shutdown-phase`.
3. **Closes remaining connections** if the timeout expires.
4. **Runs `@PreDestroy` / `DisposableBean` callbacks** and shuts down the application context.
5. Exits the JVM.

## 2. Why & when

Without graceful shutdown, a rolling update, scale-in event, or service restart drops all active HTTP requests at the moment the process is killed. Users see `500` errors or broken downloads. Database transactions are rolled back mid-flight.

Graceful shutdown matters most when:

- You do **rolling updates** in Kubernetes (pods are replaced one at a time — the old pod must drain).
- You use **Cloud Foundry or Heroku dynos** (platform sends SIGTERM before force-killing after 30 s).
- Requests are **long-lived** (file uploads, report generation, payment processing).
- You have **database transactions** that must complete cleanly.

Even for fast APIs (< 500 ms response time), graceful shutdown is a production best practice — traffic spikes mean requests overlap with shutdown signals regularly.

## 3. Core concept

Think of graceful shutdown like a restaurant closing at midnight. At 11:58 the staff stops seating new customers (refuse new requests). Existing customers who ordered before midnight are served their full meal (in-flight requests complete). At 12:30 the kitchen closes regardless (timeout), even if one table is still eating.

The shutdown sequence in Spring Boot:

```
SIGTERM received
  ↓
SmartLifecycle.stop() called on embedded server
  ↓
Server: no longer accepts new connections (HTTP 503 to load balancer)
  ↓
Server waits up to 'timeout-per-shutdown-phase' for active requests
  ↓
Spring ApplicationContext: calls @PreDestroy, closes beans (connection pools, caches)
  ↓
JVM exits (code 0 = clean, 143 = SIGTERM)
```

Kubernetes uses two probes to coordinate: the **readiness probe** fails first (removing the pod from the load balancer rotation), then SIGTERM arrives. This ensures no new requests reach the pod while it drains.

## 4. Diagram

<svg viewBox="0 0 700 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Graceful shutdown timeline showing SIGTERM, drain phase, and context close">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Timeline -->
  <line x1="30" y1="130" x2="670" y2="130" stroke="#8b949e" stroke-width="1"/>

  <!-- SIGTERM -->
  <line x1="100" y1="110" x2="100" y2="150" stroke="#ff7b72" stroke-width="2"/>
  <text x="100" y="100" fill="#ff7b72" font-size="11" text-anchor="middle" font-family="sans-serif">SIGTERM</text>

  <!-- Refuse new requests -->
  <rect x="100" y="80" width="130" height="30" rx="4" fill="#1c2430" stroke="#ff7b72" stroke-width="1"/>
  <text x="165" y="100" fill="#ff7b72" font-size="10" text-anchor="middle" font-family="sans-serif">Refuse new requests</text>

  <!-- Drain phase -->
  <rect x="100" y="140" width="280" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="240" y="160" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Drain: in-flight requests complete (up to timeout)</text>

  <!-- Active request 1 -->
  <line x1="120" y1="185" x2="280" y2="185" stroke="#6db33f" stroke-width="2"/>
  <text x="200" y="200" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">request-1 (completes)</text>

  <!-- Active request 2 -->
  <line x1="160" y1="210" x2="340" y2="210" stroke="#6db33f" stroke-width="2"/>
  <text x="250" y="225" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">request-2 (completes before timeout)</text>

  <!-- Context close -->
  <rect x="380" y="140" width="140" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="160" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Context close (@PreDestroy)</text>

  <!-- Exit -->
  <line x1="540" y1="110" x2="540" y2="150" stroke="#6db33f" stroke-width="2"/>
  <text x="540" y="100" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Exit 0</text>

  <!-- Timeout marker -->
  <line x1="380" y1="110" x2="380" y2="175" stroke="#8b949e" stroke-width="1" stroke-dasharray="4"/>
  <text x="380" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">timeout</text>

  <text x="350" y="255" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Requests started before SIGTERM finish normally; new connections see 503 immediately</text>
</svg>

SIGTERM triggers the drain window; active requests complete before the context is closed and the process exits.

## 5. Runnable example

```java
// GracefulShutdownDemo.java — run with: java GracefulShutdownDemo.java
// Simulates the Spring Boot graceful shutdown sequence:
// stops accepting new work, drains active tasks, then shuts down.

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class GracefulShutdownDemo {

    // State flags — equivalent to Spring's embedded server state
    static final AtomicBoolean acceptingRequests = new AtomicBoolean(true);
    static final List<Future<?>> inFlight = new CopyOnWriteArrayList<>();
    static final ExecutorService requestPool = Executors.newFixedThreadPool(4);

    static final long TIMEOUT_MS = 5_000; // matches spring.lifecycle.timeout-per-shutdown-phase

    public static void main(String[] args) throws Exception {
        System.out.println("=== Graceful Shutdown Demo ===\n");

        // Start some "in-flight requests" before SIGTERM
        for (int i = 1; i <= 3; i++) {
            final int id = i;
            Future<?> f = requestPool.submit(() -> simulateRequest(id, 2000 + id * 500));
            inFlight.add(f);
        }
        Thread.sleep(500); // requests are now mid-flight

        // --- SIGTERM arrives ---
        System.out.println("\n[SIGTERM] Shutdown signal received");
        gracefulShutdown();

        System.out.println("\n[EXIT 0] All done.");
        requestPool.shutdownNow();
    }

    static void simulateRequest(int id, long durationMs) {
        System.out.printf("  [request-%d] Started (will take %d ms)%n", id, durationMs);
        try {
            Thread.sleep(durationMs);
            System.out.printf("  [request-%d] Completed successfully%n", id);
        } catch (InterruptedException e) {
            System.out.printf("  [request-%d] INTERRUPTED by timeout!%n", id);
            Thread.currentThread().interrupt();
        }
    }

    static void gracefulShutdown() throws Exception {
        // Step 1: stop accepting new connections
        acceptingRequests.set(false);
        System.out.println("[shutdown] Stopped accepting new requests");

        // Step 2: wait for in-flight requests to complete
        System.out.println("[shutdown] Draining " + inFlight.size() + " in-flight requests (timeout=" + TIMEOUT_MS + "ms)...");
        long deadline = System.currentTimeMillis() + TIMEOUT_MS;
        for (Future<?> f : inFlight) {
            long remaining = deadline - System.currentTimeMillis();
            if (remaining <= 0) {
                f.cancel(true); // timeout expired — force cancel
            } else {
                try {
                    f.get(remaining, TimeUnit.MILLISECONDS);
                } catch (TimeoutException e) {
                    f.cancel(true);
                    System.out.println("[shutdown] Timeout expired — cancelling remaining requests");
                }
            }
        }

        // Step 3: close application context (simulate @PreDestroy)
        System.out.println("[shutdown] Closing Spring context (@PreDestroy callbacks)");
        System.out.println("[shutdown] Connection pool closed");
        System.out.println("[shutdown] Cache evicted");
    }
}
```

**How to run:** `java GracefulShutdownDemo.java`

## 6. Walkthrough

- **`acceptingRequests.set(false)`** — models what Spring's embedded server does when it receives SIGTERM: the HTTP listener stops accepting new TCP connections immediately. In-flight requests already in the thread pool continue.
- **`TIMEOUT_MS = 5_000`** — matches `spring.lifecycle.timeout-per-shutdown-phase=30s` in production. The demo uses 5 s for speed. In real Spring Boot, each lifecycle phase (server drain, `SmartLifecycle` beans, context close) gets its own timeout.
- **`f.get(remaining, TimeUnit.MILLISECONDS)`** — waits for each in-flight request future to complete, but no longer than the remaining timeout. This is exactly what Spring's `GracefulShutdown` class does internally with the active request counter.
- **`f.cancel(true)` on timeout** — forced cancellation after the deadline. The thread is interrupted; requests that don't handle `InterruptedException` cleanly may leave database transactions in an uncertain state — another reason to use short timeouts for DB calls inside long requests.
- **Step 3 (`@PreDestroy`)** — runs *after* the drain phase. Connection pools, caches, and message consumers are closed here. Closing them before drain would break in-flight requests that need the DB.

## 7. Gotchas & takeaways

> **Kubernetes `terminationGracePeriodSeconds` must be longer than your shutdown timeout.** If `terminationGracePeriodSeconds=30` (default) but `timeout-per-shutdown-phase=60s`, Kubernetes force-kills the pod mid-drain. Set `terminationGracePeriodSeconds` to at least `timeout + 10` seconds.

> **The readiness probe must fail *before* SIGTERM.** In Kubernetes, `preStop` sleep (e.g., 5 s) before the actual shutdown gives the load balancer time to stop routing traffic. Without it, requests arrive during the drain window even as the pod is marked for deletion.

- Minimal config: `server.shutdown=graceful` + `spring.lifecycle.timeout-per-shutdown-phase=30s`.
- Kubernetes: add `lifecycle.preStop.exec.command: ["sleep", "5"]` to the pod spec so the endpoint is removed from the Service before SIGTERM.
- Use `/actuator/health/readiness` (not `/liveness`) as the Kubernetes `readinessProbe` — Spring marks it `DOWN` during shutdown automatically.
- Default (without `server.shutdown=graceful`) is `immediate` — existing connections are dropped instantly. Never use `immediate` in production.
- Test graceful shutdown locally: `curl -s localhost:8080/api/slow & kill -SIGTERM $(pgrep -f myapp.jar)` — the curl should complete.
