---
card: spring-framework
gi: 360
slug: async-request-processing-callable-deferredresult-webasynctas
title: "Async request processing (Callable, DeferredResult, WebAsyncTask)"
---

## 1. What it is

`Callable<T>`, `DeferredResult<T>`, and `WebAsyncTask<T>` are handler method return types that let Spring MVC release the servlet request-handling thread back to the container's thread pool while the actual response is computed elsewhere, then resume and complete the HTTP response once a result becomes available. This is Spring MVC's Servlet-based async processing model — distinct from, but related in spirit to, `SseEmitter`/`StreamingResponseBody` (which stream *multiple* chunks) — these three types are for a **single** eventual result, computed asynchronously.

```java
@GetMapping("/reports/{id}")
public Callable<Report> generate(@PathVariable long id) {
    return () -> reportService.generateSlowly(id);   // runs on a separate thread
}
```

## 2. Why & when

A normal synchronous handler method ties up one servlet container thread for the entire duration of request processing — if generating a response takes 5 seconds (a slow external API call, a heavy computation, waiting on another service), that thread is blocked and unavailable for any other request the whole time. Under load, this can exhaust the thread pool and cause the server to reject or queue new requests even though most of the "work" is just waiting, not actual CPU usage.

Use async processing when:
- A handler's response depends on a slow I/O operation (calling another service, a slow database query, waiting on a message) where the thread would otherwise sit idle blocked on I/O.
- You want to decouple request-handling threads (a limited, precious resource) from the actual work-performing threads (which can use a differently-sized, independently-tuned thread pool, or come from a completely different subsystem like a message listener).
- You're building a system where results become available from an external event (a message arrives, a long-running job completes) rather than from a direct, synchronous call chain.

Choose based on where the async work originates: `Callable` for work you submit to Spring's own task executor; `DeferredResult` for results that arrive from an entirely separate thread/system (a callback, a message listener) that Spring didn't initiate; `WebAsyncTask` when you need a `Callable` plus explicit timeout/executor control.

## 3. Core concept

```
Callable<T>:
  handler returns a Callable — Spring MVC submits it to a
  TaskExecutor itself, on a thread it manages
  request thread RELEASED while Callable.call() executes elsewhere
  when call() returns T, Spring resumes and completes the response

DeferredResult<T>:
  handler returns a DeferredResult immediately (usually empty/pending)
  request thread RELEASED right away
  SOME OTHER THREAD/SYSTEM (not Spring's own executor) later calls
    deferredResult.setResult(value)
  Spring resumes and completes the response AT THAT POINT
  — the handler method itself doesn't block or wait at all

WebAsyncTask<T>:
  wraps a Callable, adding explicit timeout + custom executor + timeout/error callbacks
  same execution model as Callable, with more configuration knobs

Timeline (Callable):
  Request thread: [preHandle] [return Callable] --RELEASED--
  Executor thread:                [call() executes...] [returns T]
  Request thread:                                        [--RESUMED--] [write response]
```

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Request thread released while async work runs elsewhere</text>

  <rect x="20" y="50" width="180" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="75" text-anchor="middle" fill="#6db33f" font-size="10">Request thread: dispatch</text>

  <line x1="200" y1="70" x2="260" y2="70" stroke="#8b949e" marker-end="url(#a36)"/>

  <rect x="260" y="50" width="180" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="350" y="75" text-anchor="middle" fill="#8b949e" font-size="10">RELEASED back to pool</text>

  <rect x="260" y="110" width="180" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="350" y="135" text-anchor="middle" fill="#79c0ff" font-size="10">Executor thread: works</text>

  <line x1="350" y1="90" x2="350" y2="110" stroke="#8b949e" stroke-dasharray="2,2" marker-end="url(#a36)"/>
  <line x1="440" y1="130" x2="500" y2="70" stroke="#6db33f" marker-end="url(#a36)"/>

  <rect x="500" y="50" width="180" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="590" y="75" text-anchor="middle" fill="#6db33f" font-size="10">RESUMED, response written</text>

  <text x="360" y="180" text-anchor="middle" fill="#8b949e" font-size="10">The SAME servlet-container thread pool serves other requests during the gap</text>

  <defs>
    <marker id="a36" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The original request thread is freed for other work while the async computation runs, then a (possibly different) thread resumes and completes the response.*

## 5. Runnable example

### Level 1 — Basic

A slow report generation offloaded via `Callable`, freeing the request thread during the wait:

```java
// ReportController.java
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.Callable;

@RestController
public class ReportController {

    record Report(long id, String summary) {}

    @GetMapping("/reports/{id}")
    public Callable<Report> generate(@PathVariable long id) {
        return () -> {
            Thread.sleep(3000);   // simulates a slow external call or heavy computation
            return new Report(id, "Q3 sales summary");
        };
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

time curl http://localhost:8080/reports/1
# {"id":1,"summary":"Q3 sales summary"}
# real  0m3.0xx s
```

The handler method returns almost instantly (it just builds and returns a `Callable`, not the actual `Report`) — Spring MVC submits that `Callable` to its configured async task executor, releases the original servlet thread, and resumes/completes the HTTP response only once `call()` finishes 3 seconds later. During those 3 seconds, the freed servlet thread is available to serve other, unrelated requests.

### Level 2 — Intermediate

`DeferredResult` fed from a completely separate thread — simulating a result that arrives from an external event (a message listener, a webhook callback) rather than work Spring itself initiated:

```java
// ReportController.java (extended)
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.async.DeferredResult;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

@RestController
public class ReportController {

    record Report(long id, String summary) {}

    private final ScheduledExecutorService externalSystemSimulator = Executors.newScheduledThreadPool(2);
    private final Map<Long, DeferredResult<Report>> pending = new ConcurrentHashMap<>();

    @GetMapping("/reports/{id}/async")
    public DeferredResult<Report> generateAsync(@PathVariable long id) {
        DeferredResult<Report> deferredResult = new DeferredResult<>(10_000L);   // 10s timeout
        pending.put(id, deferredResult);

        // Simulates an EXTERNAL system (e.g. a message queue consumer) completing
        // the result later, on ITS OWN thread — Spring MVC did not initiate this work.
        externalSystemSimulator.schedule(() -> {
            Report report = new Report(id, "Generated by external worker");
            DeferredResult<Report> waiting = pending.remove(id);
            if (waiting != null) waiting.setResult(report);
        }, 2, TimeUnit.SECONDS);

        deferredResult.onTimeout(() -> deferredResult.setErrorResult("Report generation timed out"));
        return deferredResult;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

time curl http://localhost:8080/reports/1/async
# {"id":1,"summary":"Generated by external worker"}
# real  0m2.0xx s
```

**What changed:** `generateAsync` returns the `DeferredResult` object immediately (well under the timeout), with no result set yet. The actual `Report` arrives 2 seconds later from `externalSystemSimulator` — a *completely separate* thread pool Spring MVC never submitted work to directly. When that external thread calls `deferredResult.setResult(report)`, Spring MVC (which had been watching this specific `DeferredResult` instance) wakes up and completes the HTTP response from wherever that call happened to occur. This models integrating with genuinely external async systems (message consumers, webhook handlers) rather than work Spring itself dispatches.

### Level 3 — Advanced

Production concern: `WebAsyncTask` with explicit timeout handling and a dedicated executor (never relying on Spring's default async executor, which is not production-tuned out of the box), plus correct error propagation:

```java
// AsyncConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

@Configuration
public class AsyncConfig {

    @Bean
    public ThreadPoolTaskExecutor reportTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(8);
        executor.setQueueCapacity(50);
        executor.setThreadNamePrefix("report-async-");
        executor.initialize();
        return executor;
    }
}
```

```java
// ReportController.java (production version)
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.request.async.WebAsyncTask;

import java.util.concurrent.Callable;
import java.util.concurrent.Executor;

@RestController
public class ReportController {

    record Report(long id, String summary) {}

    private final Executor reportTaskExecutor;
    public ReportController(Executor reportTaskExecutor) { this.reportTaskExecutor = reportTaskExecutor; }

    @GetMapping("/reports/{id}")
    public WebAsyncTask<Report> generate(@PathVariable long id) {
        Callable<Report> work = () -> {
            if (id < 0) throw new IllegalArgumentException("Invalid report id: " + id);
            Thread.sleep(3000);
            return new Report(id, "Q3 sales summary");
        };

        WebAsyncTask<Report> task = new WebAsyncTask<>(5_000L, reportTaskExecutor, work);   // 5s timeout, DEDICATED executor
        task.onTimeout(() -> new Report(id, "Report is taking longer than expected — check back shortly"));
        task.onError(() -> new Report(id, "Report generation failed"));
        return task;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

time curl http://localhost:8080/reports/1
# {"id":1,"summary":"Q3 sales summary"}
# real  0m3.0xx s   (uses "report-async-" threads, NOT Spring's shared default executor)

curl http://localhost:8080/reports/-1
# {"id":-1,"summary":"Report generation failed"}    <- onError callback's fallback value used
```

**What changed and why:**
- A **dedicated** `ThreadPoolTaskExecutor` (`reportTaskExecutor`) is used instead of Spring's built-in default `SimpleAsyncTaskExecutor` (which creates a new, unbounded thread per task with no pooling — genuinely unsafe under real load, since it provides no backpressure). Explicit `corePoolSize`/`maxPoolSize`/`queueCapacity` bound how many concurrent async report-generation tasks the application allows, protecting the system from being overwhelmed if requests to this endpoint spike.
- `onTimeout`/`onError` callbacks give the handler explicit, controlled fallback behavior for the two failure modes async processing introduces beyond a normal synchronous handler: taking too long, or throwing an exception on the async thread — without these, a timeout or async exception would otherwise produce a generic, less informative error response.
- Naming the executor's threads (`"report-async-"`) makes production thread-dump debugging dramatically easier — an operator investigating a stuck or slow request can immediately identify which subsystem's threads are involved, rather than seeing generic, unlabeled thread names.

## 6. Walkthrough

**Request: `GET /reports/1` (Level 3 code, successful path).**

1. `DispatcherServlet` dispatches to `ReportController.generate(1)`. The method builds a `Callable<Report>` lambda (capturing `id = 1`) and wraps it in a `WebAsyncTask` configured with a `5000ms` timeout and the dedicated `reportTaskExecutor`. It returns this `WebAsyncTask` object — the method itself completes in microseconds, having done no actual report-generation work yet.
2. Spring MVC's `WebAsyncManager` recognizes the async return type. It submits the wrapped `Callable` to the configured `reportTaskExecutor` (not Spring's shared default) and — critically — puts the *original* servlet request thread into an async-started state, then **releases** it back to the servlet container's thread pool, where it becomes available to handle other, unrelated incoming requests immediately.
3. On a `report-async-` prefixed thread from the dedicated pool: the `Callable`'s body executes. `id (1) < 0` is `false`, so it proceeds past the validation check. `Thread.sleep(3000)` simulates slow work — this thread is occupied for 3 seconds, but it's a *report-generation* thread, entirely separate from the servlet container's request-handling thread pool, so it has zero impact on the application's ability to accept new HTTP connections during this time.
4. After 3 seconds, the lambda returns `new Report(1, "Q3 sales summary")`.
5. Spring MVC's async machinery detects the `Callable` completed successfully (within the 5-second timeout, so `onTimeout` never fires), and dispatches an **async completion** back into the servlet container — this typically resumes on a servlet container thread (potentially a *different* one than originally handled the initial dispatch), which then proceeds through the normal return-value-handling pipeline (the `Report` object is serialized to JSON, exactly as if it had been returned directly from a synchronous handler).
6. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"summary":"Q3 sales summary"}
   ```

**Request: `GET /reports/-1` (Level 3 code, async exception path).**

1–2. Identical dispatch and thread-release steps, with `id = -1` captured in the `Callable`.
3. On the async executor thread: `id (-1) < 0` is `true` → the lambda throws `new IllegalArgumentException("Invalid report id: -1")` instead of returning normally.
4. Spring MVC's async machinery catches this exception on the async thread and, because a `WebAsyncTask` was used (not a bare `Callable`), consults the registered `onError` callback: `task.onError(() -> new Report(id, "Report generation failed"))` — note this callback captures `id` from the enclosing scope and produces a *fallback* `Report` value rather than re-throwing.
5. This fallback value is treated as the successful result for response-writing purposes — it flows through the same JSON serialization path as a genuinely successful result would have.
6. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":-1,"summary":"Report generation failed"}
   ```

## 7. Gotchas & takeaways

> **A bare `Callable<T>` (without `WebAsyncTask`) has no built-in timeout or error-recovery mechanism of its own beyond Spring's application-wide `spring.mvc.async.request-timeout` property** — an exception thrown inside a plain `Callable` propagates as a generic async processing error, typically resulting in a `500`, unless handled by an `@ExceptionHandler`/`@ControllerAdvice` capable of catching it. Use `WebAsyncTask` when you need per-endpoint timeout/error customization rather than relying on the application-wide default.

> **Never rely on Spring's default `SimpleAsyncTaskExecutor`** (used implicitly if no `TaskExecutor` bean is configured and `Callable` is used directly without `WebAsyncTask`) **in production** — it creates an unbounded number of new threads with no pooling or queuing, which under sustained load can exhaust system resources far faster than a bounded, tuned `ThreadPoolTaskExecutor` would. Always configure and inject a dedicated, bounded executor for real async workloads, as shown in Level 3.

> **`DeferredResult` requires *someone* to eventually call `setResult`/`setErrorResult`, or the request will hang until the configured timeout fires.** A common bug is registering a `DeferredResult` and then losing track of it (e.g. a race condition where the external event fires before the `DeferredResult` is even registered in a tracking map) — always design the registration and completion paths carefully to avoid a `DeferredResult` that's never resolved.

- `Callable<T>` offloads work to Spring's task executor, freeing the request thread during execution; `DeferredResult<T>` is for results arriving from an external system Spring didn't initiate; `WebAsyncTask<T>` adds explicit timeout/executor/callback control on top of `Callable`.
- Always configure and use a dedicated, bounded `ThreadPoolTaskExecutor` for real async workloads — never rely on the unbounded default executor in production.
- `WebAsyncTask`'s `onTimeout`/`onError` callbacks provide controlled, predictable fallback behavior for the two new failure modes async processing introduces.
- Async processing trades request-thread occupancy for coordination complexity — reach for it specifically when I/O-bound work would otherwise tie up precious servlet threads, not as a default for every handler.
