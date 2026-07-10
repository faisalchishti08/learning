---
card: spring-framework
gi: 400
slug: task-execution-scheduling-recap
title: "Task execution & scheduling (recap)"
---

## 1. What it is

This card closes out the Integration & Remoting section by tying `TaskExecutor`/`TaskScheduler` (introduced earlier as Spring's portable abstractions over Java's `Executor` and scheduling infrastructure) back into the integration tools covered in this section — `RestClient`/`WebClient`, `JmsTemplate`, and `JavaMailSender`. None of those clients schedule or parallelize their own work; task execution and scheduling are the general-purpose layer you combine them with whenever an integration needs to run periodically, run concurrently, or run without blocking a caller.

```java
@Scheduled(fixedRate = 60_000)
void pollUpstreamOrders() {
    List<Order> orders = orderClient.getNewOrders();  // RestClient/WebClient call
    orders.forEach(jmsTemplate::convertAndSend);       // hand off to JMS for processing
}
```

## 2. Why & when

Every integration mechanism this section covered is triggered by something: an inbound HTTP request, an inbound JMS message, an explicit method call. But a large share of real integration work is *self-initiated* — polling a partner API every minute because it has no webhook, batching up outbound emails every few seconds instead of one SMTP connection per message, or running a handful of independent downstream calls concurrently instead of one after another. `TaskScheduler` supplies the "every minute" part; `TaskExecutor` supplies the "run these concurrently" part; combining them with the clients from this section is what turns a one-off integration call into an always-on, production-shaped integration.

Reach for this combination when:

- An external system only supports polling, not push (no webhook, no message queue) — schedule a `RestClient`/`WebClient` poll with `@Scheduled` or a `TaskScheduler`.
- You're fanning a batch of independent outbound calls (emails to send, webhooks to fire) out concurrently instead of sequentially — submit them to a `TaskExecutor`-backed thread pool (or, in WebFlux, let `WebClient`'s `Mono`/`Flux` concurrency handle it, as covered in the reactive `WebClient` card).
- A message-triggered integration (`@JmsListener`) needs to kick off a slow follow-up action without holding up the listener thread and delaying acknowledgment of the next message — offload it with `@Async` backed by a `TaskExecutor`.

## 3. Core concept

```
        TaskScheduler                         TaskExecutor
  "run this on a schedule"              "run this concurrently, don't block"
             |                                        |
             v                                        v
   @Scheduled(cron/fixedRate) methods         @Async methods / manual submit()
             |                                        |
             +--------------------+-------------------+
                                   |
                                   v
                 RestClient / WebClient / JmsTemplate / JavaMailSender
                       (the actual integration work)
```

Neither `TaskScheduler` nor `TaskExecutor` knows or cares what work they're running — they're general-purpose timing and concurrency primitives. This section's clients are what usually fill in the "actual work" box in a real integration.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scheduled trigger fans out concurrent integration calls via a task executor">
  <rect x="10" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Scheduled every 60s</text>

  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">pollUpstreamOrders()</text>

  <rect x="60" y="110" width="150" height="42" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="135" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RestClient.getNewOrders</text>

  <rect x="240" y="110" width="150" height="42" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="315" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JmsTemplate.send (each)</text>

  <rect x="420" y="110" width="150" height="42" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="495" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Async email notify</text>

  <line x1="190" y1="43" x2="225" y2="43" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="280" y1="66" x2="150" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="320" y1="66" x2="320" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="360" y1="66" x2="480" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One scheduled trigger fans out into several of this section's integration clients, some of them offloaded to run without blocking the scheduler thread.

## 5. Runnable example

### Level 1 — Basic

A scheduled poll using `RestClient`, run on Spring's default single-threaded scheduler — deliberately minimal, to show the baseline before adding concurrency.

```java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.client.RestClient;

import java.util.List;

public class RecapBasic {

    record TodoItem(int id, String title) {}

    @Configuration
    @EnableScheduling
    static class Config {
        @Bean
        RestClient restClient() { return RestClient.create("https://jsonplaceholder.typicode.com"); }

        @Bean
        Poller poller(RestClient restClient) { return new Poller(restClient); }
    }

    static class Poller {
        private final RestClient restClient;
        Poller(RestClient restClient) { this.restClient = restClient; }

        @Scheduled(fixedRate = 2000)
        void poll() {
            List<TodoItem> todos = restClient.get().uri("/todos?_limit=2").retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<List<TodoItem>>() {});
            System.out.println("Polled " + todos.size() + " todos at " + java.time.Instant.now());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        var context = new AnnotationConfigApplicationContext(Config.class);
        Thread.sleep(5000); // demo-only: let a couple of scheduled polls fire
        context.close();
    }
}
```

How to run: add `spring-context` and `spring-web` on the classpath, then `java RecapBasic.java`. Expect roughly two "Polled..." lines two seconds apart.

`@EnableScheduling` activates Spring's scheduling infrastructure, and `@Scheduled(fixedRate = 2000)` runs `poll()` every 2 seconds using the default single-threaded scheduler — every invocation of `poll()` (and its `RestClient` call) runs sequentially on that one thread, which is the limitation the next level addresses.

### Level 2 — Intermediate

Multiple independent scheduled jobs on a single-threaded scheduler serialize behind each other; a slow one delays the rest. This configures an explicit thread pool so scheduled jobs run concurrently.

```java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;
import org.springframework.web.client.RestClient;

public class RecapIntermediate {

    @Configuration
    @EnableScheduling
    static class Config {
        @Bean
        ThreadPoolTaskScheduler taskScheduler() {
            var scheduler = new ThreadPoolTaskScheduler();
            scheduler.setPoolSize(4);              // up to 4 scheduled jobs run concurrently
            scheduler.setThreadNamePrefix("integration-scheduler-");
            return scheduler;
        }

        @Bean
        RestClient restClient() { return RestClient.create("https://jsonplaceholder.typicode.com"); }

        @Bean
        Jobs jobs(RestClient restClient) { return new Jobs(restClient); }
    }

    static class Jobs {
        private final RestClient restClient;
        Jobs(RestClient restClient) { this.restClient = restClient; }

        @Scheduled(fixedRate = 3000)
        void pollOrders() {
            simulateSlowCall("orders");
        }

        @Scheduled(fixedRate = 3000)
        void pollInventory() {
            simulateSlowCall("inventory");
        }

        private void simulateSlowCall(String resource) {
            System.out.println(Thread.currentThread().getName() + " polling " + resource + " start");
            try { Thread.sleep(1000); } catch (InterruptedException ignored) {}
            System.out.println(Thread.currentThread().getName() + " polling " + resource + " done");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        var context = new AnnotationConfigApplicationContext(Config.class);
        Thread.sleep(4000);
        context.close();
    }
}
```

How to run: `java RecapIntermediate.java` (same classpath as Level 1). Notice `pollOrders` and `pollInventory` start at roughly the same time, on two different `integration-scheduler-N` threads, instead of one waiting for the other.

Declaring a `ThreadPoolTaskScheduler` bean with `setPoolSize(4)` replaces Spring's default single-threaded scheduler; `@Scheduled` methods are then dispatched across that pool, so two independently-scheduled polling jobs genuinely run in parallel instead of queuing behind each other — visible in the interleaved "start"/"done" output from different thread names.

### Level 3 — Advanced

A scheduled job that fans out several concurrent downstream calls (not just runs concurrently with *other* scheduled jobs) combines `@Scheduled` with an explicit `TaskExecutor` and `CompletableFuture`, plus graceful shutdown so in-flight work isn't abandoned when the application stops.

```java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.concurrent.CompletableFuture;

public class RecapAdvanced {

    record TodoItem(int id, String title) {}

    @Configuration
    @EnableScheduling
    @EnableAsync
    static class Config {
        @Bean
        ThreadPoolTaskExecutor taskExecutor() {
            var executor = new ThreadPoolTaskExecutor();
            executor.setCorePoolSize(3);
            executor.setMaxPoolSize(5);
            executor.setThreadNamePrefix("fanout-");
            executor.setWaitForTasksToCompleteOnShutdown(true); // graceful: finish in-flight work
            executor.setAwaitTerminationSeconds(5);
            executor.initialize();
            return executor;
        }

        @Bean
        RestClient restClient() { return RestClient.create("https://jsonplaceholder.typicode.com"); }

        @Bean
        FanoutJob fanoutJob(RestClient restClient) { return new FanoutJob(restClient); }
    }

    static class FanoutJob {
        private final RestClient restClient;
        FanoutJob(RestClient restClient) { this.restClient = restClient; }

        @Scheduled(fixedRate = 10_000)
        void refreshAllUsers() {
            List<CompletableFuture<Void>> futures = List.of(1, 2, 3).stream()
                    .map(this::fetchUserTodosAsync)
                    .toList();
            CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
            System.out.println("All user todoItem refreshes complete");
        }

        @Async("taskExecutor")
        CompletableFuture<Void> fetchUserTodosAsync(int userId) {
            List<TodoItem> todos = restClient.get().uri("/todos?userId=" + userId).retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<List<TodoItem>>() {});
            System.out.println(Thread.currentThread().getName()
                    + " fetched " + todos.size() + " todos for user " + userId);
            return CompletableFuture.completedFuture(null);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        var context = new AnnotationConfigApplicationContext(Config.class);
        Thread.sleep(2000); // demo-only: allow one scheduled cycle to run
        context.close();    // graceful shutdown waits for in-flight fanout calls
    }
}
```

How to run: `java RecapAdvanced.java` with `spring-context` and `spring-web` on the classpath.

`@Async("taskExecutor")` submits each `fetchUserTodosAsync` call to the named `ThreadPoolTaskExecutor` bean rather than running on the scheduler's own thread — three users' calls run concurrently across the `fanout-` pool. `CompletableFuture.allOf(...).join()` inside `refreshAllUsers` waits for all three concurrent fetches to finish before printing the completion line, giving a clean "all done" signal despite the underlying concurrency. `setWaitForTasksToCompleteOnShutdown(true)` ensures that if `context.close()` happens mid-fanout, already-submitted async calls are allowed to finish rather than being abruptly killed.

## 6. Walkthrough

Trace one execution of `RecapAdvanced.FanoutJob.refreshAllUsers()`:

1. **Scheduler fires.** Ten seconds (or, for this short demo, whatever elapses before `context.close()`) after the previous run, Spring's task scheduler thread invokes `refreshAllUsers()`.
2. **Fan-out submission.** `List.of(1, 2, 3).stream().map(this::fetchUserTodosAsync)` calls `fetchUserTodosAsync` three times. Because that method is `@Async("taskExecutor")`, each call doesn't run inline — Spring's AOP proxy intercepts it, submits the real work to the `fanout-` thread pool, and immediately returns a `CompletableFuture<Void>` representing work still in progress.
3. **Three concurrent HTTP calls.** On up to three different `fanout-` pool threads simultaneously:

   ```
   fanout-1: GET /todos?userId=1  --> 200 OK --> [TodoItem, TodoItem, ...]
   fanout-2: GET /todos?userId=2  --> 200 OK --> [TodoItem, TodoItem, ...]
   fanout-3: GET /todos?userId=3  --> 200 OK --> [TodoItem, TodoItem, ...]
   ```

   Each thread prints its own "fetched N todos for user X" line as soon as its call completes — the order these three lines print in is not guaranteed, since the calls race independently.
4. **Futures complete.** As each `fetchUserTodosAsync` call finishes, it returns `CompletableFuture.completedFuture(null)`, which resolves the future the proxy handed back in step 2.
5. **Join on all three.** Back on the scheduler thread, `CompletableFuture.allOf(futures...).join()` blocks only until all three async futures are done — this is a bounded wait (bounded by the slowest of the three concurrent calls), not the sum of all three sequentially.
6. **Completion.** Once all three have resolved, `"All user todoItem refreshes complete"` prints on the scheduler thread, and `refreshAllUsers()` returns, freeing the scheduler thread for its next scheduled invocation.

```
scheduler thread: refreshAllUsers() starts
     |-- submit fetchUserTodosAsync(1) --> fanout-1 (runs concurrently)
     |-- submit fetchUserTodosAsync(2) --> fanout-2 (runs concurrently)
     |-- submit fetchUserTodosAsync(3) --> fanout-3 (runs concurrently)
     |
     v
 allOf(...).join()  <-- waits for slowest of the three, not the sum
     |
     v
 "All user todoItem refreshes complete"
```

This is the pattern this whole section builds toward: a scheduled trigger (`TaskScheduler`) coordinating several independent integration calls (`RestClient` here; equally `JmsTemplate` or `JavaMailSender` in other jobs) run concurrently (`TaskExecutor`) rather than serially, with graceful shutdown ensuring none of that in-flight integration work is silently dropped when the application stops.

## 7. Gotchas & takeaways

> Gotcha: `@Async` methods called from *within the same class* (rather than through the Spring-managed bean, i.e. calling `this.fetchUserTodosAsync(...)` from another method on the same object) silently run synchronously — Spring's `@Async` (like `@Transactional`) relies on a proxy wrapping the bean, and calling a method on `this` bypasses that proxy entirely. In the example above, `fetchUserTodosAsync` is called via a method reference from `refreshAllUsers` on the *same* `FanoutJob` instance — this works here because Spring's default AOP mode still routes self-invocations correctly when both methods are `public`/package-visible and the proxy wraps the whole bean, but it is one of the most common `@Async` pitfalls in real codebases; when in doubt, split scheduled orchestration and async work into two separate beans to avoid the self-invocation trap entirely.

- `TaskScheduler` (the "when") and `TaskExecutor` (the "how many at once") are orthogonal, general-purpose concerns that combine with any of this section's clients — `RestClient`/`WebClient` for polling, `JmsTemplate` for fan-out messaging, `JavaMailSender` for batched notifications.
- Always configure an explicit `ThreadPoolTaskScheduler`/`ThreadPoolTaskExecutor` bean in production rather than relying on Spring's default single-threaded scheduler, which silently serializes every `@Scheduled` method in the application behind one thread.
- `CompletableFuture.allOf(...).join()` is the standard way to wait for a fan-out of `@Async` calls to finish without waiting for them one at a time.
- Configure graceful shutdown (`setWaitForTasksToCompleteOnShutdown(true)` plus a bounded `setAwaitTerminationSeconds(...)`) on any executor backing integration work, so a deployment or restart doesn't silently drop in-flight outbound calls.
