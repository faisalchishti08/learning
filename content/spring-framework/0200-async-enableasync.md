---
card: spring-framework
gi: 200
slug: async-enableasync
title: "@Async & @EnableAsync"
---

## 1. What it is

`@EnableAsync` activates Spring's asynchronous method execution infrastructure. `@Async` marks a Spring bean method so that each invocation runs in a separate thread rather than the caller's thread — the caller gets control back immediately, and the work happens in the background.

When you call an `@Async` method, Spring intercepts it (via a proxy), submits the method body to an `Executor`, and returns. If the method returns `void`, the caller simply moves on. If it returns `CompletableFuture<T>`, the caller gets a future it can wait on later, compose, or ignore.

## 2. Why & when

Anything that takes time but doesn't need to block the current thread is a candidate:

- Sending an email after a user registers — the HTTP response should not wait for the SMTP round-trip.
- Generating a PDF report triggered by an API call.
- Fan-out: calling three independent external APIs and combining the results.
- Fire-and-forget audit log writes.

Without `@Async` you'd manage `ExecutorService` and `Future` manually, scattering threading concerns across the business logic. `@Async` is a clean annotation-driven separation.

**Do not use `@Async` for:** transactional work that must commit in the caller's transaction (the new thread has no transaction), tasks requiring strict ordering, or tasks the caller must wait for synchronously (just call the method normally).

## 3. Core concept

Think of `@Async` as dropping a task envelope in an outbox tray. You write the letter (the method call), drop it in the tray, and walk away. A mail-room worker (the thread pool) picks it up and delivers it later.

Spring achieves this with a **proxy**. When you `@Autowire` an `@Async`-annotated bean, Spring gives you a proxy wrapper. Every method call on that proxy submits the real method to an `Executor` and returns a completed/in-progress `CompletableFuture` (or nothing for `void`).

Key rules:
1. The method must be called **through the proxy** — i.e., from *outside* the bean (or via `self` injection). `this.asyncMethod()` inside the same class bypasses the proxy and runs synchronously.
2. Return type must be `void`, `Future<T>`, or `CompletableFuture<T>`.
3. `@EnableAsync` goes on a `@Configuration` class.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg">
  <!-- Caller -->
  <rect x="15" y="90" width="110" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="118" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Caller thread</text>

  <!-- Arrow to proxy -->
  <line x1="125" y1="115" x2="195" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- Proxy -->
  <rect x="195" y="90" width="110" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="250" y="111" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">@Async</text>
  <text x="250" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Proxy</text>

  <!-- Proxy submits to executor -->
  <line x1="305" y1="100" x2="375" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="370" y="50" fill="#8b949e" font-size="10" font-family="sans-serif">submit task</text>

  <!-- Executor -->
  <rect x="375" y="60" width="120" height="45" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="435" y="83" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ThreadPoolExecutor</text>
  <text x="435" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(background thread)</text>

  <!-- Proxy returns immediately to caller -->
  <line x1="305" y1="130" x2="375" y2="170" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="370" y="190" fill="#8b949e" font-size="10" font-family="sans-serif">return immediately</text>

  <!-- CompletableFuture -->
  <rect x="375" y="155" width="130" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="440" y="178" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">CompletableFuture</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>
</svg>

The proxy intercepts the call, submits work to the pool, and returns a `CompletableFuture` to the caller — all before the real method even starts.

## 5. Runnable example

Scenario: a **notification service** that sends notifications out-of-band — first basic fire-and-forget, then returning a future for result tracking, then a production-grade fan-out with a custom thread pool.

### Level 1 — Basic

Send a notification asynchronously so the caller returns instantly.

```java
// AsyncDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableAsync
@ComponentScan
public class AsyncDemo {
    public static void main(String[] args) throws InterruptedException {
        var ctx = new AnnotationConfigApplicationContext(AsyncDemo.class);
        var svc = ctx.getBean(NotificationService.class);

        System.out.println("Before send: " + Thread.currentThread().getName());
        svc.sendEmail("user@example.com", "Welcome!");
        System.out.println("After send (returned immediately): " + Thread.currentThread().getName());

        Thread.sleep(2000); // wait for async work
        ctx.close();
    }
}

@Service
class NotificationService {
    @Async
    public void sendEmail(String to, String subject) throws InterruptedException {
        System.out.println("Sending to " + to + " on " + Thread.currentThread().getName());
        Thread.sleep(500); // simulate SMTP
        System.out.println("Sent: " + subject);
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. AsyncDemo.java`

The main thread prints "After send" *before* "Sending to …" appears — proof that `sendEmail` runs on a different thread. The caller does not block.

---

### Level 2 — Intermediate

Result tracking concern: the caller needs to know if the notification succeeded, so `sendEmail` returns a `CompletableFuture<String>`.

```java
// AsyncDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.stereotype.*;
import java.util.concurrent.*;

@Configuration
@EnableAsync
@ComponentScan
public class AsyncDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AsyncDemo.class);
        var svc = ctx.getBean(NotificationService.class);

        CompletableFuture<String> f1 = svc.sendEmail("alice@example.com", "Invoice");
        CompletableFuture<String> f2 = svc.sendEmail("bob@example.com", "Receipt");

        // Both emails are in-flight simultaneously
        CompletableFuture.allOf(f1, f2).join();
        System.out.println("Results: " + f1.get() + ", " + f2.get());
        ctx.close();
    }
}

@Service
class NotificationService {
    @Async
    public CompletableFuture<String> sendEmail(String to, String subject)
            throws InterruptedException {
        Thread.sleep(600); // simulate latency
        System.out.println("Sent '" + subject + "' to " + to
            + " on " + Thread.currentThread().getName());
        return CompletableFuture.completedFuture("OK:" + to);
    }
}
```

How to run: same classpath as Level 1

Both emails fire in parallel (Spring submits both before either returns). `CompletableFuture.allOf` waits for both. Total wall-clock time ≈ 600 ms instead of 1 200 ms.

---

### Level 3 — Advanced

Production concern: configure a named, bounded thread pool for notifications so slow SMTP can't exhaust the shared pool; use `@Async("notificationExecutor")` to target it explicitly.

```java
// AsyncDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.scheduling.concurrent.*;
import org.springframework.stereotype.*;
import java.util.concurrent.*;

@Configuration
@EnableAsync
@ComponentScan
public class AsyncDemo {

    @org.springframework.context.annotation.Bean("notificationExecutor")
    public java.util.concurrent.Executor notificationExecutor() {
        var exec = new ThreadPoolTaskExecutor();
        exec.setCorePoolSize(4);
        exec.setMaxPoolSize(10);
        exec.setQueueCapacity(50);
        exec.setThreadNamePrefix("notify-");
        exec.setRejectedExecutionHandler(new java.util.concurrent.ThreadPoolExecutor.CallerRunsPolicy());
        exec.initialize();
        return exec;
    }

    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(AsyncDemo.class);
        var svc = ctx.getBean(NotificationService.class);

        var futures = new java.util.ArrayList<CompletableFuture<String>>();
        for (int i = 1; i <= 6; i++) {
            futures.add(svc.sendEmail("user" + i + "@example.com", "Alert #" + i));
        }
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
        futures.forEach(f -> {
            try { System.out.println(f.get()); } catch (Exception e) { e.printStackTrace(); }
        });
        ctx.close();
    }
}

@Service
class NotificationService {
    @Async("notificationExecutor")
    public CompletableFuture<String> sendEmail(String to, String subject)
            throws InterruptedException {
        Thread.sleep(400);
        String result = "Sent '" + subject + "' to " + to
            + " [" + Thread.currentThread().getName() + "]";
        System.out.println(result);
        return CompletableFuture.completedFuture(result);
    }
}
```

How to run: same classpath

`@Async("notificationExecutor")` routes calls to the named bean. The `CallerRunsPolicy` means if all 10 threads are busy and the queue is full, the *calling* thread executes the task itself — graceful degradation rather than `RejectedExecutionException`. Thread names `notify-1` … `notify-4` confirm the right pool is used.

## 6. Walkthrough

**Startup:** `@EnableAsync` registers `AsyncAnnotationBeanPostProcessor`. After all beans are instantiated, the post-processor inspects each bean for `@Async`-annotated methods.

**Proxy creation:** `NotificationService` is wrapped in a JDK dynamic proxy (or CGLIB subclass if it has no interface). When you call `ctx.getBean(NotificationService.class)`, you receive the proxy.

**Call interception (Level 3 example, 6 calls):**
1. Main thread calls `svc.sendEmail("user1@…", "Alert #1")`.
2. The proxy's `invoke` method is called instead of the real method.
3. The proxy looks up the `Executor` named `"notificationExecutor"`.
4. It creates a `Callable` wrapping `NotificationService.sendEmail` and submits it to the executor.
5. The executor places the task in the queue (or directly to a thread if a core thread is idle).
6. The proxy constructs a new `CompletableFuture`, links it to the submitted task, and returns it to the main thread.
7. Steps 1–6 repeat for calls 2–6 — all six are submitted before any finishes.

**Thread pool dispatch:** With `corePoolSize=4`, the first four tasks start immediately on threads `notify-1` … `notify-4`. Tasks 5 and 6 wait in the queue until a thread finishes.

**Result delivery:** When `sendEmail` completes on `notify-1`, it calls `CompletableFuture.complete(result)`, which unblocks any `CompletableFuture.allOf` waiter.

**`allOf().join()` in main:** The main thread blocks here until all six futures are complete. Total wall time ≈ 400 ms × 2 batches = ~800 ms (4 parallel + 2 parallel), far less than 6 × 400 ms = 2 400 ms sequential.

**Data state at each stage:**
- Before `allOf`: 6 `CompletableFuture` objects, each `PENDING`.
- After `notify-1..4` finish (≈400 ms): 4 futures `COMPLETED`, 2 still `PENDING`.
- After all finish (≈800 ms): all 6 `COMPLETED` with result strings.

## 7. Gotchas & takeaways

> **`this.asyncMethod()` is a trap.** Calling an `@Async` method from within the same bean bypasses the proxy, so it runs synchronously. Inject the bean into itself (`@Autowired private NotificationService self`) or restructure to call from outside.

> **Default executor is unbounded.** Without a custom `Executor` bean, Spring uses `SimpleAsyncTaskExecutor`, which creates a *new thread per task* — no pooling, no backpressure. Always configure a `ThreadPoolTaskExecutor` for production.

- Return type must be `void`, `Future`, or `CompletableFuture`. Returning a plain `String` compiles but throws at runtime.
- Exceptions in `void` `@Async` methods are swallowed by default — use `AsyncUncaughtExceptionHandler` (next topic) to capture them.
- If `@Async` and `@Transactional` are both on the same method, the async thread gets a *new* transaction, not the caller's — this is usually correct but occasionally surprising.
- `@EnableAsync(proxyTargetClass = true)` forces CGLIB proxying; useful when the bean has no interface.
- Name your executor bean and reference it explicitly to avoid accidental coupling to the shared default executor.
