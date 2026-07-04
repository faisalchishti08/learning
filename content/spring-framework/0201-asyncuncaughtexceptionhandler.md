---
card: spring-framework
gi: 201
slug: asyncuncaughtexceptionhandler
title: AsyncUncaughtExceptionHandler
---

## 1. What it is

`AsyncUncaughtExceptionHandler` is Spring's safety net for exceptions thrown inside `@Async` methods that return `void`. Because `void` methods have no `Future` for the caller to inspect, exceptions thrown in the background thread would otherwise vanish silently. This interface lets you intercept those exceptions and handle them — log them, alert ops, record them in a database.

You implement the single method `handleUncaughtException(Throwable ex, Method method, Object... params)` and register it by implementing `AsyncConfigurer` on a `@Configuration` class.

## 2. Why & when

When an `@Async` method returns `CompletableFuture`, the exception is captured inside the future and the caller can retrieve it with `.get()` or `.exceptionally(…)`. For `void` methods, there is no such carrier — the background thread dies silently.

You need `AsyncUncaughtExceptionHandler` whenever:
- Fire-and-forget `@Async void` methods do real work that can fail (email sending, webhook delivery, audit writes).
- You want centralised error logging instead of try/catch in every async method.
- You need to trigger alerts, metrics, or retry logic on async failure.

Without it you will have failing background tasks and no evidence in the logs.

## 3. Core concept

Think of it as a dead-letter queue for async exceptions. Normally a thread's uncaught exception goes to the JVM's default `UncaughtExceptionHandler` (usually just stderr). Spring intercepts it earlier, before the task's `Runnable` wrapper catches the `Throwable`, and routes it to your registered handler.

The interface:

```java
public interface AsyncUncaughtExceptionHandler {
    void handleUncaughtException(Throwable ex, Method method, Object... params);
}
```

- `ex` — the thrown exception.
- `method` — the `java.lang.reflect.Method` that threw it (name, parameter types, declaring class — useful for logging).
- `params` — the actual argument values passed to the method when it was called.

You register it via `AsyncConfigurer`:

```java
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {
    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return new MyHandler();
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg">
  <!-- Caller -->
  <rect x="20" y="85" width="110" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="113" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Caller thread</text>

  <!-- Arrow: call -->
  <line x1="130" y1="110" x2="200" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ar)"/>
  <text x="165" y="103" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">call</text>

  <!-- Proxy -->
  <rect x="200" y="85" width="110" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="255" y="108" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">@Async Proxy</text>
  <text x="255" y="125" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">submits task</text>

  <!-- Async thread -->
  <rect x="370" y="55" width="130" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="435" y="78" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Async thread</text>
  <text x="435" y="95" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">throws Exception</text>

  <!-- Arrow: submit -->
  <line x1="310" y1="95" x2="370" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ar)"/>

  <!-- Handler -->
  <rect x="370" y="140" width="150" height="50" rx="7" fill="#1c2430" stroke="#e06c75" stroke-width="1.5"/>
  <text x="445" y="163" fill="#e06c75" font-size="12" text-anchor="middle" font-family="sans-serif">Uncaught</text>
  <text x="445" y="180" fill="#e06c75" font-size="11" text-anchor="middle" font-family="sans-serif">ExceptionHandler</text>

  <!-- Arrow: exception routed -->
  <line x1="435" y1="105" x2="435" y2="140" stroke="#e06c75" stroke-width="1.5" marker-end="url(#ar2)"/>
  <text x="475" y="127" fill="#e06c75" font-size="10" font-family="sans-serif">exception</text>

  <defs>
    <marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
    <marker id="ar2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#e06c75"/>
    </marker>
  </defs>
</svg>

The caller sees nothing — it got control back immediately. The exception travels from the background thread directly to the handler, bypassing the caller.

## 5. Runnable example

Scenario: a **webhook delivery service** that fires notifications asynchronously — first just showing that exceptions vanish, then catching them with a handler, then a full production handler that records failures and triggers retries.

### Level 1 — Basic

Show the problem: an exception in a `void @Async` method is silent without a handler.

```java
// AsyncExceptionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableAsync
@ComponentScan
public class AsyncExceptionDemo {
    public static void main(String[] args) throws InterruptedException {
        var ctx = new AnnotationConfigApplicationContext(AsyncExceptionDemo.class);
        var svc = ctx.getBean(WebhookService.class);
        svc.deliver("http://bad-url.invalid", "{\"event\":\"signup\"}");
        System.out.println("Main thread: call returned immediately");
        Thread.sleep(2000);
        System.out.println("Main thread: finished — notice no error was printed");
        ctx.close();
    }
}

@Service
class WebhookService {
    @Async
    public void deliver(String url, String payload) {
        System.out.println("Delivering to " + url);
        throw new RuntimeException("Connection refused: " + url);
        // exception disappears — no output after this line
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. AsyncExceptionDemo.java`

"Connection refused" is thrown on the background thread. Without a handler, it propagates to Spring's task wrapper, which catches it and discards it. The main thread never knows.

---

### Level 2 — Intermediate

Register an `AsyncUncaughtExceptionHandler` to log failures with the method name and arguments.

```java
// AsyncExceptionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.stereotype.*;
import java.lang.reflect.*;
import java.util.*;

@Configuration
@EnableAsync
@ComponentScan
public class AsyncExceptionDemo implements AsyncConfigurer {

    @Override
    public org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler
            getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) -> {
            System.err.printf("[ASYNC ERROR] method=%s.%s args=%s%n  -> %s: %s%n",
                method.getDeclaringClass().getSimpleName(),
                method.getName(),
                Arrays.toString(params),
                ex.getClass().getSimpleName(),
                ex.getMessage());
        };
    }

    public static void main(String[] args) throws InterruptedException {
        var ctx = new AnnotationConfigApplicationContext(AsyncExceptionDemo.class);
        var svc = ctx.getBean(WebhookService.class);
        svc.deliver("http://ok.example.com", "{\"event\":\"login\"}");
        svc.deliver("http://bad.invalid", "{\"event\":\"signup\"}");
        Thread.sleep(2000);
        ctx.close();
    }
}

@Service
class WebhookService {
    @Async
    public void deliver(String url, String payload) throws InterruptedException {
        Thread.sleep(300);
        if (url.contains("invalid")) {
            throw new RuntimeException("Connection refused: " + url);
        }
        System.out.println("Delivered to " + url);
    }
}
```

How to run: same as Level 1

Now the handler prints: `[ASYNC ERROR] method=WebhookService.deliver args=[http://bad.invalid, {"event":"signup"}] -> RuntimeException: Connection refused`. The `method` parameter gives the declaring class, name, and parameter types for precise diagnosis.

---

### Level 3 — Advanced

Production concern: the handler records failures to an in-memory failure store and queues failed deliveries for retry, bounded by a max-attempt counter.

```java
// AsyncExceptionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.stereotype.*;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

@Configuration
@EnableAsync
@ComponentScan
public class AsyncExceptionDemo implements AsyncConfigurer {

    @Override
    public org.springframework.aop.interceptor.AsyncUncaughtExceptionHandler
            getAsyncUncaughtExceptionHandler() {
        return ctx.getBean(WebhookFailureHandler.class)::handle;
    }

    // self-reference trick for handler bean
    static AnnotationConfigApplicationContext ctx;

    public static void main(String[] args) throws InterruptedException {
        ctx = new AnnotationConfigApplicationContext(AsyncExceptionDemo.class);
        var svc = ctx.getBean(WebhookService.class);
        svc.deliver("http://good.example.com", "payload-1");
        svc.deliver("http://bad.invalid", "payload-2");
        svc.deliver("http://bad.invalid", "payload-2"); // second attempt
        Thread.sleep(3000);
        var handler = ctx.getBean(WebhookFailureHandler.class);
        System.out.println("Failure log: " + handler.getLog());
        ctx.close();
    }
}

@Service
class WebhookService {
    @Async
    public void deliver(String url, String payload) throws InterruptedException {
        Thread.sleep(200);
        if (url.contains("invalid"))
            throw new RuntimeException("Connect failed: " + url);
        System.out.println("OK: " + url);
    }
}

@org.springframework.stereotype.Component
class WebhookFailureHandler {
    private final List<String> log = new CopyOnWriteArrayList<>();
    private final Map<String, AtomicInteger> attempts = new ConcurrentHashMap<>();

    public void handle(Throwable ex, Method method, Object... params) {
        String url = params.length > 0 ? String.valueOf(params[0]) : "unknown";
        int count = attempts.computeIfAbsent(url, k -> new AtomicInteger())
                            .incrementAndGet();
        String entry = String.format("FAIL #%d url=%s err=%s", count, url, ex.getMessage());
        log.add(entry);
        System.err.println("[Handler] " + entry);
        if (count < 3) System.err.println("[Handler] Queued for retry #" + (count + 1));
        else           System.err.println("[Handler] Max retries reached for " + url);
    }

    List<String> getLog() { return Collections.unmodifiableList(log); }
}
```

How to run: same classpath

`WebhookFailureHandler` is a Spring bean injected into the handler registration. It tracks per-URL failure counts using `ConcurrentHashMap<String, AtomicInteger>` (thread-safe because multiple async threads may fail concurrently). After three failures it stops retrying.

## 6. Walkthrough

**The problem path (Level 1):**
1. `svc.deliver(…)` → proxy intercepts, submits `Runnable` to `SimpleAsyncTaskExecutor`, returns void to caller.
2. Background thread: `WebhookService.deliver()` throws `RuntimeException`.
3. Spring's `AsyncExecutionAspectSupport.doSubmit()` wraps the `Callable` in a try/catch.
4. The caught exception is passed to `getAsyncUncaughtExceptionHandler().handleUncaughtException(…)`.
5. Default handler: Spring's `SimpleAsyncUncaughtExceptionHandler` just logs at WARN level using the configured logger — easy to miss.

**The handler path (Level 2/3):**
1. Same submission and execution as above.
2. Exception is caught by `AsyncExecutionAspectSupport`.
3. Your registered `AsyncUncaughtExceptionHandler.handleUncaughtException(ex, method, params)` is called.
4. `method` carries `WebhookService.deliver` via reflection — `method.getName()` = `"deliver"`, `method.getDeclaringClass()` = `WebhookService.class`.
5. `params` = `["http://bad.invalid", "payload-2"]` — the actual argument values at the time of the call.

**Level 3 thread-safety deep dive:**
- Multiple background threads can fail concurrently (both "bad.invalid" calls land ~200 ms apart).
- `CopyOnWriteArrayList` for `log` is safe for concurrent adds.
- `ConcurrentHashMap.computeIfAbsent` + `AtomicInteger.incrementAndGet` is safe for concurrent counter updates.
- The handler bean itself is a singleton, shared across all async threads — it must be thread-safe.

**What you can see:**
```
OK: http://good.example.com
[Handler] FAIL #1 url=http://bad.invalid err=Connect failed: http://bad.invalid
[Handler] Queued for retry #2
[Handler] FAIL #2 url=http://bad.invalid err=Connect failed: http://bad.invalid
[Handler] Queued for retry #3
Failure log: [FAIL #1 url=http://bad.invalid err=..., FAIL #2 url=http://bad.invalid err=...]
```

## 7. Gotchas & takeaways

> **This handler only fires for `void` `@Async` methods.** If the method returns `CompletableFuture`, the exception is embedded in the future — the handler is never called. The caller must use `.exceptionally(…)` or `.get()` to observe it.

> **Handler runs on the async thread.** Don't do slow, blocking work in the handler itself — it occupies the thread pool thread. For heavy remediation, submit to another executor or use a non-blocking queue.

- `AsyncConfigurer.getAsyncUncaughtExceptionHandler()` is called once at startup; the returned handler is reused for all exceptions — make it thread-safe (a stateless lambda is simplest).
- `params` gives you the argument *values*, not types — cast carefully (e.g. `(String) params[0]`).
- The default `SimpleAsyncUncaughtExceptionHandler` logs at WARN — check your log level isn't suppressing it before assuming there's no handler.
- Override both `getAsyncUncaughtExceptionHandler()` *and* `getAsyncExecutor()` in the same `AsyncConfigurer` to keep thread-pool and error handling in one place.
- In Spring Boot, you can also define a `@Bean` of type `AsyncUncaughtExceptionHandler` — Spring Boot's `TaskExecutionAutoConfiguration` picks it up automatically.
