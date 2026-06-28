---
card: spring-boot
gi: 96
slug: using-a-log-shutdown-hook
title: Using a log shutdown hook
---

## 1. What it is

A **log shutdown hook** is a JVM shutdown hook that tells the logging system to flush its buffers and cleanly shut down when the JVM exits. Without it, asynchronous log appenders may not write their last few messages before the process terminates, resulting in **lost log lines** at shutdown.

Spring Boot automatically registers a Logback shutdown hook unless the application context provides its own lifecycle management or an incompatible JVM setup is detected. The feature is controlled by:

```properties
logging.register-shutdown-hook=true   # default
```

The hook calls `LogbackLoggingSystem.cleanUp()`, which invokes Logback's `LoggerContext.stop()`, draining any async appender queues and releasing file handles before the JVM exits.

## 2. Why & when

Logback's `AsyncAppender` writes log events to a background queue and a dedicated worker thread flushes the queue to the underlying appender (file, socket, etc.) asynchronously. This improves throughput because the application thread doesn't wait for disk I/O. The tradeoff: when the JVM exits abruptly, the worker thread may not have flushed the queue.

Symptoms of missing shutdown hook:
- The last N log lines (typically the shutdown sequence) are absent from the log file.
- File handles are not released, causing issues when the log file is rotated externally.
- Socket appenders (Logstash TCP) lose buffered events.

The shutdown hook solves all three. It is essential when:
- You use an `AsyncAppender` (default in Spring Boot 2.x file appender; opt-in in 3.x).
- You use a socket/network appender to a log aggregator.
- You care about the shutdown log lines appearing (e.g. `APPLICATION STOPPED` for audit trails).

## 3. Core concept

JVM shutdown hooks are threads registered with `Runtime.getRuntime().addShutdownHook(Thread)`. They run in parallel when the JVM begins shutdown (triggered by `System.exit()`, SIGTERM, or process end). Logback's shutdown hook drains the async queue sequentially before the thread ends.

Spring Boot's auto-registration:
```
SpringApplication starts
  → prepareEnvironment()
  → LoggingApplicationListener.onApplicationStartingEvent()
  → LogbackLoggingSystem.initialize(…)
  → if (logging.register-shutdown-hook=true)
     Runtime.getRuntime().addShutdownHook(new LogbackShutdownHook())
```

The hook is NOT registered when:
- `logging.register-shutdown-hook=false`.
- The application runs inside a servlet container (Tomcat/Jetty manage shutdown hooks themselves).
- A `logback-spring.xml` configures its own `<shutdownHook>` element (Spring Boot detects this and skips auto-registration to avoid duplicates).

Logback also provides its own `<shutdownHook>` XML element as an alternative:
```xml
<configuration>
  <shutdownHook class="ch.qos.logback.core.hook.DelayingShutdownHook">
    <delay>2000</delay>
  </shutdownHook>
  …
</configuration>
```

The `DelayingShutdownHook` waits a fixed delay before stopping — useful when other shutdown hooks (Spring context, datasource) need to log during their own teardown.

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Shutdown sequence: SIGTERM triggers JVM shutdown hooks including the Logback hook that drains the async queue before process exit">
  <rect x="8" y="8" width="664" height="254" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Log Shutdown Hook — JVM Termination Sequence</text>

  <!-- SIGTERM / System.exit -->
  <rect x="30" y="50" width="150" height="36" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="105" y="64" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">SIGTERM</text>
  <text x="105" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">or System.exit()</text>

  <defs><marker id="sha" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="182" y1="68" x2="218" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sha)"/>

  <!-- JVM shutdown hooks (parallel) -->
  <rect x="220" y="40" width="180" height="56" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="310" y="58" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM shutdown hooks</text>
  <text x="310" y="73" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">Spring context hook</text>
  <text x="310" y="87" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">Logback shutdown hook ←</text>

  <line x1="402" y1="68" x2="438" y2="68" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sha)"/>

  <!-- Logback shutdown detail -->
  <rect x="440" y="40" width="210" height="56" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="545" y="58" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">LoggerContext.stop()</text>
  <text x="545" y="73" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">drain AsyncAppender queue</text>
  <text x="545" y="87" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">flush &amp; close file handles</text>

  <!-- Without hook -->
  <rect x="30" y="135" width="300" height="70" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="180" y="153" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Without shutdown hook</text>
  <text x="180" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">async queue not drained</text>
  <text x="180" y="182" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">last N log lines lost</text>
  <text x="180" y="196" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">file handles not released</text>

  <!-- With hook -->
  <rect x="350" y="135" width="300" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="153" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">With shutdown hook (default)</text>
  <text x="500" y="168" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">queue drained before exit</text>
  <text x="500" y="182" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">all buffered events written</text>
  <text x="500" y="196" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">clean file handle release</text>

  <rect x="30" y="224" width="620" height="24" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="240" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">logging.register-shutdown-hook=true (default) — set false only if another mechanism handles Logback cleanup</text>
</svg>

The shutdown hook ensures buffered log events reach the underlying appender before the JVM exits.

## 5. Runnable example

```java
// LogShutdownHook.java — run: java LogShutdownHook.java  (JDK 17+)
// Demonstrates JVM shutdown hooks and simulates async log buffer draining.

import java.util.*;
import java.util.concurrent.*;

public class LogShutdownHook {

    // Simulated async log buffer (represents AsyncAppender queue)
    static final Queue<String> asyncQueue = new ConcurrentLinkedQueue<>();
    static volatile boolean hookRegistered = false;

    static void enqueueLogEvent(String event) {
        asyncQueue.offer(event);
        // In real Logback, a background thread drains this queue to the appender.
        // On immediate JVM exit without a shutdown hook, unflushed events are lost.
    }

    static void registerLogbackShutdownHook() {
        hookRegistered = true;
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("[ShutdownHook] Logback shutdown hook triggered");
            System.out.println("[ShutdownHook] Draining " + asyncQueue.size() + " buffered events...");
            String event;
            while ((event = asyncQueue.poll()) != null) {
                System.out.println("[FLUSHED]      " + event);
            }
            System.out.println("[ShutdownHook] Logback context stopped. File handles released.");
        }, "logback-shutdown-hook"));
        System.out.println("Shutdown hook registered (logging.register-shutdown-hook=true)");
    }

    public static void main(String[] args) throws Exception {
        registerLogbackShutdownHook();

        // Normal application log events (synchronous — always written)
        System.out.println("[SYNC-LOG]  Application started");
        System.out.println("[SYNC-LOG]  Processing 3 orders...");

        // Async log events enqueued but not yet flushed to disk
        enqueueLogEvent("INFO  c.e.OrderService - Order 101 accepted");
        enqueueLogEvent("INFO  c.e.OrderService - Order 102 accepted");
        enqueueLogEvent("INFO  c.e.OrderService - Order 103 accepted");

        // Shutdown starts — without hook these 3 events would be lost
        System.out.println("[SYNC-LOG]  Application shutting down (SIGTERM received)");
        enqueueLogEvent("INFO  c.e.App         - Spring context closing");
        enqueueLogEvent("INFO  c.e.App         - DataSource pool closed");
        enqueueLogEvent("INFO  c.e.App         - APPLICATION STOPPED");

        System.out.println("[SYNC-LOG]  JVM exit — shutdown hooks will run now...");
        // System.exit() triggers the hook; normal main() end also triggers it
    }
}
```

**How to run:** `java LogShutdownHook.java`

## 6. Walkthrough

- `asyncQueue` represents Logback's `AsyncAppender` queue — a `BlockingQueue` holding `ILoggingEvent` objects. The background `Worker` thread continuously polls this queue and writes to the wrapped appender (file, socket, etc.).
- `registerLogbackShutdownHook()` simulates `LogbackLoggingSystem` registering a JVM shutdown hook via `Runtime.getRuntime().addShutdownHook`. The thread name `"logback-shutdown-hook"` is the actual name Spring Boot uses.
- The three async log events representing order acceptance are enqueued but not yet written when the main thread begins shutdown. Without the hook, the JVM exits before the background worker flushes them.
- The shutdown hook thread runs during JVM teardown, drains the entire queue, and prints `[FLUSHED]` for each event. In real Logback, `LoggerContext.stop()` calls `AsyncAppender.stop()` which joins the worker thread, waiting up to `maxFlushTime` milliseconds (default 1000 ms).
- The three `APPLICATION STOPPED`, `DataSource pool closed`, and context-closing events are the ones most likely to be lost in practice — they are emitted by Spring's own shutdown listeners, which run just before `System.exit`.

## 7. Gotchas & takeaways

> **Disable the auto-registered hook (`logging.register-shutdown-hook=false`) only if you manage Logback lifecycle yourself** — for example, via a custom `logback-spring.xml` with a `<shutdownHook>` element. If you disable it without a replacement, you will lose log events at shutdown, which is often invisible in tests and surfaces only under load in production.

> **The shutdown hook does not guarantee all events are written.** The default `maxFlushTime` for `AsyncAppender` is 1000 ms. If the queue has more events than can be written in 1 second (high load during shutdown), remaining events are dropped. Increase `maxFlushTime` in your `logback-spring.xml` if this is a concern.

- The hook is most important when using `AsyncAppender`, a socket appender, or any network-based log sink (Logstash, Graylog).
- In servlet-container deployments (WAR in Tomcat), the container manages shutdown hooks; Spring Boot skips auto-registration to avoid conflicts.
- For `DelayingShutdownHook` (Logback XML), set the delay long enough for all Spring shutdown listeners to finish logging — typically 500–2000 ms.
- On containerized deployments, `SIGTERM` is the normal shutdown signal from Kubernetes. The hook runs in response to `SIGTERM` unless the pod's `terminationGracePeriodSeconds` expires and the kernel sends `SIGKILL` — `SIGKILL` cannot be caught and skips all hooks.
- Check your shutdown logs (search for "APPLICATION STOPPED" or the Spring banner shutdown message) — their presence confirms the hook ran successfully.
