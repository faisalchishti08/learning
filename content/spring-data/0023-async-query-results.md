---
card: spring-data
gi: 23
slug: async-query-results
title: "Async query results"
---

## 1. What it is

This card goes one level deeper than the earlier `CompletableFuture` card: it covers *how* asynchronous repository query execution is actually configured and controlled — which executor thread pool `@Async` repository methods run on, how to size and name that pool deliberately instead of relying on Spring's default, and how timeouts and cancellation propagate (or don't) through an asynchronous query call.

```java
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {
    @Override
    public Executor getAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(8);
        executor.setThreadNamePrefix("repo-async-");
        executor.initialize();
        return executor;
    }
}
```

## 2. Why & when

The earlier `CompletableFuture` card showed `@Async` making a repository call non-blocking from the caller's perspective — but it didn't address *where* that async work actually runs. Without explicit configuration, `@Async` falls back to Spring's `SimpleAsyncTaskExecutor`, which creates a brand-new thread for every single invocation and never reuses or pools them — fine for a demo, a genuine liability under real load, since unbounded thread creation can exhaust system resources under enough concurrent async calls. Understanding executor configuration, timeouts, and cancellation is what turns "my repository method returns a `CompletableFuture`" into "my application's async query load is actually under control."

This matters specifically when:

- You're moving `@Async` repository methods from a demo/prototype into production and need a properly bounded, named thread pool instead of the unbounded default `SimpleAsyncTaskExecutor`.
- You need to bound how long an async query is allowed to run before the caller gives up on it — `CompletableFuture.get(timeout, unit)` (or `orTimeout(...)`) is how a caller enforces this, since the underlying database call itself typically won't self-cancel just because the caller stopped waiting.
- You're debugging thread-pool exhaustion, unexpectedly slow async queries, or unclear thread names in a profiler/thread dump — all three trace back to how the async executor is (or isn't) configured.

## 3. Core concept

```
 Default (no configuration): SimpleAsyncTaskExecutor
   -- creates a NEW THREAD for every @Async call, never pools or reuses them
   -- no upper bound -- under high concurrent load, this can create
      an unbounded number of threads

 Explicit configuration via AsyncConfigurer + @EnableAsync:
   ThreadPoolTaskExecutor
     corePoolSize    -- threads kept alive even when idle
     maxPoolSize     -- hard ceiling on concurrent async work
     queueCapacity   -- how many pending tasks queue up before rejecting new ones
     threadNamePrefix -- makes thread dumps/profiler output actually readable

 TIMEOUT / CANCELLATION:
   future.get(5, TimeUnit.SECONDS)   -- caller gives up waiting after 5s
      -- BUT: this does NOT necessarily stop the underlying database query
         from continuing to run on its executor thread -- true cancellation
         needs cooperation from the underlying JDBC driver/query itself
```

Configuring the executor is a one-time, application-wide decision; timeout handling is a per-call decision the caller makes independently — both matter, and neither substitutes for the other.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unbounded default executor creates a thread per call, while a configured ThreadPoolTaskExecutor bounds and reuses a fixed pool">
  <rect x="10" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SimpleAsyncTaskExecutor (default)</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new thread PER CALL, unbounded</text>
  <text x="150" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">risk: thread exhaustion under load</text>

  <rect x="350" y="20" width="280" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ThreadPoolTaskExecutor (configured)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">bounded pool, reused threads</text>
  <text x="490" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">core/max size, queue, named threads</text>

  <rect x="150" y="120" width="340" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="142" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">production code should always configure the executor explicitly</text>
</svg>

The default executor's unbounded thread creation is a demo convenience, not a production-safe default.

## 5. Runnable example

The scenario: a search service backed by async repository calls, evolving from observing the default executor's per-call thread creation, to a properly bounded custom executor, to timeout handling that demonstrates what a `get(timeout, unit)` call actually does and doesn't cancel.

### Level 1 — Basic

Run several `@Async` calls with no executor configuration and observe the default `SimpleAsyncTaskExecutor` creating a distinct thread per call.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.EnableAsync;

import java.util.List;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

@SpringBootApplication
@EnableAsync
public class AsyncQueryLevel1 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {
        @Async
        CompletableFuture<List<Product>> findAllAsync();
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(AsyncQueryLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:asyncq1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget"));

        Set<String> threadNames = ConcurrentHashMap.newKeySet();
        CompletableFuture<?>[] futures = new CompletableFuture[5];
        for (int i = 0; i < 5; i++) {
            futures[i] = repo.findAllAsync().thenAccept(list -> threadNames.add(Thread.currentThread().getName()));
        }
        CompletableFuture.allOf(futures).get();

        System.out.println("distinct thread names used across 5 async calls: " + threadNames.size());
        System.out.println("names: " + threadNames);

        if (threadNames.size() < 2)
            throw new AssertionError("Expected the default SimpleAsyncTaskExecutor to use MULTIPLE distinct threads");
        System.out.println("Default executor created a new thread per call, with no pooling -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java AsyncQueryLevel1.java` on JDK 17+.

With no `AsyncConfigurer` bean supplied, `@EnableAsync` falls back to `SimpleAsyncTaskExecutor`, which spins up a fresh thread for every single `@Async` invocation and never reuses one — running 5 async calls typically produces close to 5 distinct thread names (rather than a small, reused pool), directly observable by collecting `Thread.currentThread().getName()` from within each call's continuation.

### Level 2 — Intermediate

Configure a properly bounded `ThreadPoolTaskExecutor` and confirm async calls now reuse a small, fixed set of named threads instead of creating a new one each time.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.List;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executor;

@SpringBootApplication
@EnableAsync
public class AsyncQueryLevel2 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {
        @Async
        CompletableFuture<List<Product>> findAllAsync();
    }

    @Configuration
    public static class AsyncConfig implements AsyncConfigurer {
        @Override
        public Executor getAsyncExecutor() {
            ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
            executor.setCorePoolSize(2);
            executor.setMaxPoolSize(2);
            executor.setThreadNamePrefix("repo-async-");
            executor.initialize();
            return executor;
        }
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(AsyncQueryLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:asyncq2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget"));

        Set<String> threadNames = ConcurrentHashMap.newKeySet();
        CompletableFuture<?>[] futures = new CompletableFuture[10];
        for (int i = 0; i < 10; i++) {
            futures[i] = repo.findAllAsync().thenAccept(list -> threadNames.add(Thread.currentThread().getName()));
        }
        CompletableFuture.allOf(futures).get();

        System.out.println("distinct thread names used across 10 async calls: " + threadNames.size());
        System.out.println("names: " + threadNames);

        boolean allNamedCorrectly = threadNames.stream().allMatch(n -> n.startsWith("repo-async-"));
        if (threadNames.size() > 2)
            throw new AssertionError("Expected at most 2 distinct threads from the bounded pool (maxPoolSize=2), got " + threadNames.size());
        if (!allNamedCorrectly) throw new AssertionError("Expected every thread name to use the configured prefix");
        System.out.println("Configured ThreadPoolTaskExecutor reused a bounded, named pool -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java AsyncQueryLevel2.java`.

`AsyncConfig implements AsyncConfigurer` overrides `getAsyncExecutor()`, returning a `ThreadPoolTaskExecutor` capped at 2 threads (`corePoolSize`/`maxPoolSize` both 2) with a readable `"repo-async-"` name prefix. Running 10 async calls through this configuration reuses at most 2 threads total (versus close to 10 with the default executor from Level 1), and every thread name is recognizably prefixed — exactly the kind of bounded, identifiable thread pool a production deployment needs.

### Level 3 — Advanced

Demonstrate what `CompletableFuture.get(timeout, unit)` actually does — and doesn't do — by timing out on a deliberately slow async query and showing the underlying database call keeps running to completion regardless, since a client-side timeout doesn't automatically cancel server-side work.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;

@SpringBootApplication
@EnableAsync
public class AsyncQueryLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    @Component
    public static class SlowSearchService {
        private final ProductRepository repo;
        final AtomicBoolean underlyingWorkCompleted = new AtomicBoolean(false);
        final CountDownLatch underlyingWorkFinishedLatch = new CountDownLatch(1);

        public SlowSearchService(ProductRepository repo) { this.repo = repo; }

        @Async
        public CompletableFuture<Long> slowCount() {
            try {
                Thread.sleep(2000); // simulate a genuinely slow query/computation
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
            }
            long count = repo.count(); // the "real work" -- runs regardless of caller timeout
            underlyingWorkCompleted.set(true);
            underlyingWorkFinishedLatch.countDown();
            return CompletableFuture.completedFuture(count);
        }
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(AsyncQueryLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:asyncq3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget"));

        SlowSearchService service = ctx.getBean(SlowSearchService.class);
        CompletableFuture<Long> future = service.slowCount();

        boolean timedOut = false;
        try {
            future.get(500, TimeUnit.MILLISECONDS); // caller gives up after 500ms
        } catch (TimeoutException expected) {
            timedOut = true;
            System.out.println("caller timed out after 500ms, as expected");
        }

        System.out.println("immediately after timeout, has underlying work finished? " + service.underlyingWorkCompleted.get());

        // Wait for the underlying (still-running) work to ACTUALLY finish, to prove it wasn't cancelled.
        boolean underlyingFinished = service.underlyingWorkFinishedLatch.await(5, TimeUnit.SECONDS);
        System.out.println("underlying work eventually completed anyway? " + underlyingFinished);

        if (!timedOut) throw new AssertionError("Expected the caller to time out after 500ms on a 2-second operation");
        if (!underlyingFinished) throw new AssertionError("Expected the underlying async work to complete despite the caller's timeout");
        System.out.println("Confirmed: a caller timeout does NOT cancel the underlying async work -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java AsyncQueryLevel3.java` on JDK 17+.

`future.get(500, TimeUnit.MILLISECONDS)` on a call that takes roughly 2 seconds throws `TimeoutException` after 500ms — but this only stops the *caller* from waiting any longer; it does nothing to the async task itself, which keeps running on its executor thread to completion. `underlyingWorkFinishedLatch.await(...)` afterward confirms the "slow" work genuinely finished anyway, roughly 1.5 seconds after the caller had already given up — proving a `CompletableFuture` timeout is purely a client-side waiting decision, not a cancellation signal to the work in progress.

## 6. Walkthrough

Trace Level 3's timeline.

1. **`service.slowCount()` is called**: because it's `@Async`, Spring immediately dispatches the actual method body to an executor thread and returns a `CompletableFuture<Long>` to `main` right away, without waiting for anything.
2. **On the executor thread**: `Thread.sleep(2000)` begins, simulating slow work — no query has run yet at this point.
3. **`main` calls `future.get(500, TimeUnit.MILLISECONDS)`**: this blocks the calling thread, waiting for the future to complete, but only for up to 500 milliseconds.
4. **At the 500ms mark**: the future still hasn't completed (the executor thread is still deep in its 2-second sleep), so `get(...)` throws `TimeoutException` — control returns to `main`, but *nothing happens to the executor thread*, which is completely unaware this timeout occurred.
5. **`main` checks `underlyingWorkCompleted.get()`** immediately after catching the timeout — it's still `false`, since the executor thread is still sleeping, roughly 1.5 seconds away from finishing.
6. **The executor thread continues independently**: at the 2-second mark, `Thread.sleep` returns, `repo.count()` executes (a real, if brief, database query), `underlyingWorkCompleted` is set `true`, and `underlyingWorkFinishedLatch` counts down — all of this happens whether or not anyone is still waiting for the result.
7. **`main`'s `underlyingWorkFinishedLatch.await(5, TimeUnit.SECONDS)`** blocks until that countdown occurs, confirming the work did eventually finish successfully — its result (the count) is simply never retrieved by `main`, since the original `future.get(...)` call already gave up and threw.
8. **Verification**: the program confirms both that the timeout genuinely occurred (as evidence the caller-side wait was bounded) and that the underlying work genuinely completed afterward anyway (as evidence a timeout is not a cancellation).

```
 t=0ms     slowCount() called --> dispatched to executor thread, future returned immediately
 t=0ms     executor thread: Thread.sleep(2000) begins
 t=500ms   main: future.get(500ms) THROWS TimeoutException -- main proceeds, unaware of executor state
 t=2000ms  executor thread: sleep ends, repo.count() runs, work completes -- but no one is "waiting" anymore
 t=2000ms+ main: underlyingWorkFinishedLatch confirms the work finished, LONG after the timeout fired
```

## 7. Gotchas & takeaways

> **Gotcha:** because a `CompletableFuture` timeout doesn't cancel the underlying work, code that retries an operation after a timeout (a common pattern) can end up with *multiple* copies of that "slow" work still running concurrently in the background — the original, abandoned one, plus each retry — all consuming executor threads and database connections, none of which the caller has any further visibility into or control over. True cancellation requires cooperation from the underlying operation itself (checking an interruption flag, or the JDBC driver supporting query cancellation), not just a client-side timeout.

- The default `SimpleAsyncTaskExecutor` creates an unbounded new thread per `@Async` call — appropriate for demos, a real production risk under load; always configure an explicit, bounded `ThreadPoolTaskExecutor` via `AsyncConfigurer` before relying on `@Async` in production.
- `corePoolSize`, `maxPoolSize`, `queueCapacity`, and `threadNamePrefix` are the key `ThreadPoolTaskExecutor` settings to tune deliberately — the last one, easy to overlook, makes thread dumps and profiler output actually attributable to your async repository work.
- `CompletableFuture.get(timeout, unit)` bounds how long the *caller* waits — it is not a cancellation mechanism for the underlying asynchronous work, which continues running to completion (or failure) regardless of whether anyone is still waiting for its result.
- When genuine cancellation matters (not just "stop waiting, but let it keep running"), it needs to be built explicitly — checking `Thread.interrupted()` within long-running work, or using a cancellable JDBC/database-level mechanism — `@Async`/`CompletableFuture` alone doesn't provide it.
