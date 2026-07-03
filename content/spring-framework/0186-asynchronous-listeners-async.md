---
card: spring-framework
gi: 186
slug: asynchronous-listeners-async
title: "Asynchronous listeners (@Async)"
---

## 1. What it is

By default `publishEvent` dispatches synchronously: all listeners run on the publisher's thread before the call returns. Adding `@Async` to an `@EventListener` method makes that specific listener run on a configured thread pool, allowing the publisher to return immediately.

```java
@EnableAsync     // required on @Configuration class
@Component
class NotificationService {

    @Async
    @EventListener
    public void send(OrderPlacedEvent event) {
        // runs on a TaskExecutor thread — publisher doesn't wait
        emailClient.send(event.getEmail(), "Your order is placed");
    }
}
```

`@Async` requires `@EnableAsync` on a `@Configuration` class and a `TaskExecutor` bean (or Spring uses a default `SimpleAsyncTaskExecutor`).

## 2. Why & when

- **Slow I/O** — sending emails, making HTTP calls, writing audit records: blocking the publisher thread for these wastes throughput. Async dispatch frees it immediately.
- **Isolation** — an exception in an async listener does NOT propagate to the publisher (only logged). For fire-and-forget reactions this is desirable; for must-succeed reactions it is dangerous.
- **Parallel fan-out** — multiple `@Async` listeners for the same event all start concurrently instead of sequentially, reducing total latency when each listener does independent I/O.
- **Avoid @Async** when the listener MUST complete within the publishing transaction: use `@TransactionalEventListener` instead, which can be combined with async.
- **Avoid @Async** when listeners must run in strict order — async listeners don't respect `@Order` between each other.

## 3. Core concept

`@EnableAsync` installs `AsyncAnnotationBeanPostProcessor`. It wraps methods annotated with `@Async` in an AOP proxy that submits the method call to a `TaskExecutor` instead of calling it directly.

**Thread pool resolution order:**
1. A `TaskExecutor` bean named `"taskExecutor"` (highest priority).
2. A single `TaskExecutor` bean of any name.
3. `SimpleAsyncTaskExecutor` as fallback (creates a new thread per invocation — fine for low load, dangerous for high concurrency).

**Exception handling:** async `@EventListener` exceptions are passed to the thread pool's uncaught exception handler. To log or alert on failures, configure an `AsyncUncaughtExceptionHandler`:

```java
@Configuration
@EnableAsync
class AsyncConfig implements AsyncConfigurer {
    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) ->
            System.err.println("Async error in " + method.getName() + ": " + ex.getMessage());
    }
}
```

**`@Order` and async:** `@Order` controls the sequence of *synchronous* listener invocations. Async listeners are submitted concurrently and their order of completion depends on the thread pool scheduler — `@Order` has no meaningful effect between async listeners.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="asa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="asb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Publisher thread -->
  <rect x="5" y="5" width="690" height="45" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="15" y="24" fill="#8b949e" font-size="9" font-family="sans-serif" font-weight="bold">Publisher thread</text>
  <text x="15" y="38" fill="#e6edf3" font-size="8" font-family="sans-serif">OrderService.place() → publishEvent() → [sync listener A] → [submit async B to pool] → [submit async C to pool] → returns</text>

  <!-- Sync listener A -->
  <rect x="5" y="60" width="210" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="75" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">SyncAuditListener (no @Async)</text>
  <text x="110" y="88" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">runs on publisher thread, blocks publish return</text>
  <line x1="110" y1="52" x2="110" y2="58" stroke="#6db33f" stroke-width="1.5" marker-end="url(#asa)"/>

  <!-- Thread pool -->
  <rect x="230" y="60" width="465" height="120" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="462" y="76" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">TaskExecutor thread pool</text>

  <rect x="245" y="85" width="200" height="30" rx="4" fill="#79c0ff" opacity="0.15"/>
  <text x="345" y="99" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">@Async EmailSender.send() — thread-1</text>
  <text x="345" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">exception → AsyncUncaughtExceptionHandler</text>

  <rect x="460" y="85" width="220" height="30" rx="4" fill="#79c0ff" opacity="0.15"/>
  <text x="570" y="99" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">@Async SlackNotifier.notify() — thread-2</text>
  <text x="570" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">runs concurrently with thread-1</text>

  <line x1="340" y1="52" x2="345" y2="83" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#asb)"/>
  <line x1="540" y1="52" x2="570" y2="83" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#asb)"/>

  <text x="462" y="152" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">publisher does NOT wait for async listeners — returns after submitting tasks</text>
  <text x="462" y="165" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">async exceptions are isolated — they cannot roll back the publisher's transaction</text>
</svg>

Sync listeners block the publisher; `@Async` listeners are submitted to the thread pool and run concurrently — the publisher returns without waiting.

## 5. Runnable example

The scenario is an **order notification system** — order placement triggers email, Slack, and audit reactions, growing to a correctly configured thread pool.

### Level 1 — Basic

`@Async` + `@EventListener` with `@EnableAsync` enabled.

```java
// AsyncListenerBasic.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.stereotype.*;

class OrderPlacedEvent extends ApplicationEvent {
    private final String orderId;
    OrderPlacedEvent(Object src, String id) { super(src); orderId=id; }
    public String getOrderId() { return orderId; }
}

@Component
class SyncAudit {
    @EventListener
    public void log(OrderPlacedEvent e) {
        System.out.println("[SYNC Audit] " + Thread.currentThread().getName()
            + " - " + e.getOrderId());
    }
}

@Component
class AsyncEmail {
    @Async
    @EventListener
    public void send(OrderPlacedEvent e) throws InterruptedException {
        Thread.sleep(50);  // simulate slow email send
        System.out.println("[ASYNC Email] " + Thread.currentThread().getName()
            + " - sent for " + e.getOrderId());
    }
}

@Service
class OrderService {
    private final ApplicationEventPublisher pub;
    OrderService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void place(String id) {
        System.out.println("[OrderService] placing " + id);
        pub.publishEvent(new OrderPlacedEvent(this, id));
        System.out.println("[OrderService] publishEvent returned (async email still running)");
    }
}

@Configuration
@ComponentScan
@EnableAsync   // activates @Async processing
class AsyncConfig { }

public class AsyncListenerBasic {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AsyncConfig.class);
        ctx.getBean(OrderService.class).place("ORD-001");
        Thread.sleep(200);  // let async thread finish before context closes
        ctx.close();
    }
}
```

How to run: `java AsyncListenerBasic.java`

The output shows `[OrderService] publishEvent returned` printed *before* `[ASYNC Email]` — proof the publisher didn't wait. `[SYNC Audit]` prints before the return because it runs synchronously. `Thread.sleep(200)` in `main` prevents the JVM from exiting before the async thread completes.

### Level 2 — Intermediate

Configure a named thread pool and an `AsyncUncaughtExceptionHandler` to capture failures.

```java
// AsyncListenerIntermediate.java
import org.springframework.aop.interceptor.*;
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.scheduling.concurrent.*;
import org.springframework.stereotype.*;
import java.lang.reflect.Method;
import java.util.concurrent.*;

class ShipmentEvent extends ApplicationEvent {
    private final String shipmentId;
    ShipmentEvent(Object src, String id) { super(src); shipmentId=id; }
    public String getShipmentId() { return shipmentId; }
}

@Component
class CarrierNotifier {
    @Async("notificationExecutor")  // use named executor
    @EventListener
    public void notify(ShipmentEvent e) throws InterruptedException {
        System.out.println("[Carrier] " + Thread.currentThread().getName()
            + " notifying for " + e.getShipmentId());
        Thread.sleep(30);
    }
}

@Component
class FailingListener {
    @Async("notificationExecutor")
    @EventListener
    public void fail(ShipmentEvent e) {
        System.out.println("[Failing] about to throw");
        throw new RuntimeException("Carrier API down for " + e.getShipmentId());
    }
}

@Configuration
@ComponentScan
@EnableAsync
class AsyncInterConfig implements AsyncConfigurer {

    @Bean("notificationExecutor")
    public Executor notificationExecutor() {
        var exec = new ThreadPoolTaskExecutor();
        exec.setCorePoolSize(3);
        exec.setMaxPoolSize(6);
        exec.setQueueCapacity(100);
        exec.setThreadNamePrefix("notif-");
        exec.initialize();
        return exec;
    }

    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return new AsyncUncaughtExceptionHandler() {
            @Override
            public void handleUncaughtException(Throwable ex, Method method, Object... params) {
                System.err.println("[AsyncError] " + method.getName() + ": " + ex.getMessage());
            }
        };
    }
}

public class AsyncListenerIntermediate {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AsyncInterConfig.class);
        var pub = ctx.getBean(ApplicationEventPublisher.class);
        pub.publishEvent(new ShipmentEvent(pub, "SHP-007"));
        Thread.sleep(300);
        ctx.close();
    }
}
```

How to run: `java AsyncListenerIntermediate.java`

`@Async("notificationExecutor")` pins the listener to a named `ThreadPoolTaskExecutor` — thread names show `notif-1`, `notif-2`, etc. The `FailingListener` throws; `AsyncUncaughtExceptionHandler.handleUncaughtException` catches it and logs the error without affecting `CarrierNotifier` or the publisher. Both async listeners run concurrently on pool threads.

### Level 3 — Advanced

Multiple events fan-out in parallel; verify listener execution in tests using a `CountDownLatch`.

```java
// AsyncListenerAdvanced.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.event.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.scheduling.concurrent.*;
import org.springframework.stereotype.*;
import java.util.*;
import java.util.concurrent.*;

class ReportReadyEvent extends ApplicationEvent {
    private final String reportId; private final String type;
    ReportReadyEvent(Object src, String id, String t) { super(src); reportId=id; type=t; }
    public String getReportId() { return reportId; }
    public String getType()     { return type; }
}

@Component
class PdfExporter {
    @Async("reportPool")
    @EventListener
    public void export(ReportReadyEvent e) throws InterruptedException {
        Thread.sleep(50);
        System.out.println("[PDF] " + Thread.currentThread().getName() + " exported " + e.getReportId());
    }
}

@Component
class EmailDelivery {
    @Async("reportPool")
    @EventListener
    public void deliver(ReportReadyEvent e) throws InterruptedException {
        Thread.sleep(30);
        System.out.println("[Email] " + Thread.currentThread().getName() + " delivered " + e.getReportId());
    }
}

@Component
class SlackPoster {
    @Async("reportPool")
    @EventListener
    public void post(ReportReadyEvent e) throws InterruptedException {
        Thread.sleep(20);
        System.out.println("[Slack] " + Thread.currentThread().getName() + " posted " + e.getReportId());
    }
}

@Service
class ReportService {
    private final ApplicationEventPublisher pub;
    ReportService(ApplicationEventPublisher pub) { this.pub = pub; }
    public void generate(String id) {
        System.out.println("[Report] generated " + id + " — notifying listeners");
        pub.publishEvent(new ReportReadyEvent(this, id, "MONTHLY"));
        System.out.println("[Report] publishEvent returned — listeners running async");
    }
}

@Configuration
@ComponentScan
@EnableAsync
class AsyncAdvancedConfig {
    @Bean("reportPool")
    public Executor reportPool() {
        var exec = new ThreadPoolTaskExecutor();
        exec.setCorePoolSize(5);
        exec.setThreadNamePrefix("report-");
        exec.initialize();
        return exec;
    }
}

public class AsyncListenerAdvanced {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AsyncAdvancedConfig.class);
        var svc = ctx.getBean(ReportService.class);

        // Publish two events — all listeners fan out concurrently
        long t0 = System.currentTimeMillis();
        svc.generate("RPT-2024-01");
        svc.generate("RPT-2024-02");
        System.out.println("[main] Both events published in " +
            (System.currentTimeMillis() - t0) + " ms");

        Thread.sleep(300);  // wait for async completions
        ctx.close();
    }
}
```

How to run: `java AsyncListenerAdvanced.java`

Three `@Async` listeners receive each event and run concurrently on the `report-` thread pool. Two events are published back-to-back; six async tasks are submitted (3 listeners �� 2 events). The `[main]` timestamp shows publishing completed in < 5ms even though the listeners together take 50ms+ — the publisher never waited. The slowest listener (`PdfExporter`, 50ms) determines when work finishes, not the sum.

## 6. Walkthrough

Tracing `svc.generate("RPT-2024-01")` in the Level 3 app:

**Step 1 — `generate` called on publisher thread:**
- Prints `[Report] generated RPT-2024-01 �� notifying listeners`.
- `pub.publishEvent(new ReportReadyEvent(...))`.

**Step 2 — Context dispatches to async listeners:**
For each listener, Spring's `@Async` AOP proxy intercepts the `onApplicationEvent` call:
- `PdfExporter` — proxy submits `pdf.export(event)` to `reportPool` → returns immediately.
- `EmailDelivery` — proxy submits `email.deliver(event)` to `reportPool` → returns immediately.
- `SlackPoster` — proxy submits `slack.post(event)` to `reportPool` → returns immediately.

All three submissions happen in < 1ms. `publishEvent` returns.

**Step 3 — `publishEvent` returns:** prints `[Report] publishEvent returned`.

**Step 4 — Pool threads run concurrently (approx timeline):**

```
t=0ms   : PdfExporter starts (report-1), EmailDelivery starts (report-2), SlackPoster starts (report-3)
t=20ms  : SlackPoster completes → "[Slack] report-3 posted RPT-2024-01"
t=30ms  : EmailDelivery completes → "[Email] report-2 delivered RPT-2024-01"
t=50ms  : PdfExporter completes → "[PDF] report-1 exported RPT-2024-01"
```

Total wall-clock time ≈ 50ms (max of any listener), not 100ms (sum). True parallel fan-out.

## 7. Gotchas & takeaways

> **Async listener exceptions are silently discarded without `AsyncUncaughtExceptionHandler`.** Without it, `RuntimeException` in an async listener is logged at WARN level and dropped. Always configure a handler in production, at minimum to alert/record failures.

> **`@Async` on `@EventListener` breaks transaction propagation.** An async listener runs on a completely different thread with no transaction context from the publisher. If the listener must run inside or after a transaction, use `@TransactionalEventListener` (next topic) — which can also be made async by combining both annotations.

- `@EnableAsync` must be on a `@Configuration` class, not just anywhere — placing it on a `@Component` works in some versions but is unreliable.
- The fallback executor (`SimpleAsyncTaskExecutor`) creates a new thread per task with no pool limit — safe for demos, dangerous in production under load. Always define a named `ThreadPoolTaskExecutor`.
- `Thread.sleep` in tests is fragile; prefer `CountDownLatch` or `CompletableFuture` to reliably wait for async listener completion in tests.
- Async listeners that write to a shared `List` or counter need thread-safe data structures — they run concurrently.
