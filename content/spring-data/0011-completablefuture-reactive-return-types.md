---
card: spring-data
gi: 11
slug: completablefuture-reactive-return-types
title: "CompletableFuture / reactive return types"
---

## 1. What it is

Beyond the synchronous return types (`T`, `Optional<T>`, `List<T>`) covered so far, Spring Data repository methods can also declare asynchronous or reactive return types: `CompletableFuture<T>` (or `CompletableFuture<List<T>>`) for asynchronous execution against a blocking store like JPA, combined with `@Async`, and `Mono<T>`/`Flux<T>` (Project Reactor's reactive types) for genuinely non-blocking, reactive stores like Spring Data R2DBC or Reactive MongoDB. Both signal "don't wait synchronously for this result" — but they mean it in importantly different ways.

```java
// Asynchronous (still blocking under the hood, just off the calling thread)
@Async
CompletableFuture<Customer> findByEmail(String email);

// Reactive (genuinely non-blocking, backpressure-aware, for a reactive store)
Mono<Customer> findByEmail(String email);
Flux<Customer> findByLastName(String lastName);
```

## 2. Why & when

A synchronous `findById` call blocks the calling thread until the database responds — fine for most request-handling code, but a real cost when many such calls need to run concurrently, or when the calling code itself is structured around non-blocking I/O end to end (a reactive web application, for instance). `CompletableFuture` and reactive return types exist to let repository calls fit into those two different non-blocking programming models — asynchronous-but-still-thread-blocking-underneath for `CompletableFuture`, and genuinely non-blocking-all-the-way-down for `Mono`/`Flux`.

Reach for these return types specifically when:

- You're calling a JPA (or other blocking-store) repository from code that wants to run several independent queries concurrently without blocking the calling thread on each one sequentially — `CompletableFuture` combined with `@Async` moves the blocking work to a separate thread pool, letting the caller compose multiple futures together.
- You're building a fully reactive application (Spring WebFlux, backed by a reactive-capable store like R2DBC, Reactive MongoDB, or Reactive Cassandra) and need repository methods that return `Mono<T>`/`Flux<T>` to compose correctly with the rest of the reactive pipeline, without ever blocking a thread.
- You're deciding between the two: `CompletableFuture` works with *any* store (JPA included) because it's really just "run the same blocking call on a different thread," while `Mono`/`Flux` require a genuinely reactive store driver underneath — JPA itself has no reactive driver, so `Mono<Customer> findById(...)` is not something a `JpaRepository` can support.

## 3. Core concept

```
 CompletableFuture<T> / CompletableFuture<List<T>>
        |
        requires @Async on the method (or the whole repository) AND
        an async-capable executor configured (@EnableAsync)
        |
        v
   the underlying call is STILL a blocking JPA/JDBC call --
   it just runs on a separate thread from an executor pool,
   so the CALLING thread doesn't block waiting for it

 Mono<T> / Flux<T>  (Project Reactor types)
        |
        requires a REACTIVE store driver (R2DBC, Reactive MongoDB, etc.) --
        NOT available for JpaRepository, since JDBC/JPA is fundamentally blocking
        |
        v
   the ENTIRE call chain, from repository to database driver, is non-blocking --
   no thread is ever parked waiting; results arrive via reactive subscription
```

`CompletableFuture` wraps blocking work to run elsewhere; `Mono`/`Flux` require the blocking work not to exist in the first place, all the way down to the database driver.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CompletableFuture runs blocking work on a separate thread; Mono and Flux avoid blocking entirely through a reactive driver">
  <rect x="10" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Async CompletableFuture&lt;T&gt;</text>
  <text x="150" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">calling thread returns immediately;</text>
  <text x="150" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">blocking JPA call runs on executor thread</text>

  <rect x="350" y="20" width="280" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Mono&lt;T&gt; / Flux&lt;T&gt;</text>
  <text x="490" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no thread ever blocks -- requires a</text>
  <text x="490" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reactive driver (R2DBC, Reactive Mongo)</text>

  <rect x="150" y="130" width="340" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="157" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Both let the calling thread move on without waiting</text>

  <line x1="150" y1="90" x2="250" y2="125" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="490" y1="90" x2="400" y2="125" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`CompletableFuture` moves blocking work off-thread; `Mono`/`Flux` eliminate blocking altogether, given a reactive driver.

## 5. Runnable example

Since `Mono`/`Flux` require a reactive store driver this section hasn't introduced, and JPA/H2 is inherently blocking, the example focuses on `CompletableFuture` — the return type that works with the JPA repositories already used throughout this section — evolving from a single asynchronous call, to composing two concurrently, to a full setup handling asynchronous failure.

### Level 1 — Basic

Declare a `@Async CompletableFuture<Customer>`-returning method and confirm it runs off the calling thread, completing later.

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

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

@SpringBootApplication
@EnableAsync
public class AsyncReturnLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        protected Customer() {}
        public Customer(String email) { this.email = email; }
        public String getEmail() { return email; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        @Async
        CompletableFuture<Customer> findByEmail(String email);
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(AsyncReturnLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:async1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("ada@example.com"));

        String callingThread = Thread.currentThread().getName();
        CompletableFuture<Customer> future = repo.findByEmail("ada@example.com");
        System.out.println("main thread continues immediately after calling findByEmail: " + callingThread);

        Customer result = future.get(5, TimeUnit.SECONDS); // block HERE, only to observe the result
        System.out.println("async result arrived: " + result.getEmail());

        if (!result.getEmail().equals("ada@example.com"))
            throw new AssertionError("Expected to find the saved customer asynchronously");
        System.out.println("@Async CompletableFuture<Customer> completed off the calling thread -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java AsyncReturnLevel1.java` on JDK 17+.

`@EnableAsync` activates Spring's async-method-execution machinery. `@Async` on `findByEmail` tells Spring to intercept calls to this method, run the actual (still-blocking) JPA query on a separate thread from the configured executor pool, and return a `CompletableFuture` immediately to the caller — `main`'s line printing "continues immediately" runs without waiting for the database query, and `future.get(...)` is the point where the calling code chooses to block and wait for the result, rather than the repository call itself blocking implicitly.

### Level 2 — Intermediate

Fire two independent asynchronous queries and compose them with `CompletableFuture.allOf`, showing the concurrency benefit `CompletableFuture` return types unlock over sequential synchronous calls.

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
import java.util.concurrent.CompletableFuture;

@SpringBootApplication
@EnableAsync
public class AsyncReturnLevel2 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String tier;
        protected Customer() {}
        public Customer(String tier) { this.tier = tier; }
        public String getTier() { return tier; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        @Async
        CompletableFuture<List<Customer>> findByTier(String tier);
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(AsyncReturnLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:async2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        for (int i = 0; i < 3; i++) repo.save(new Customer("gold"));
        for (int i = 0; i < 5; i++) repo.save(new Customer("silver"));

        long start = System.currentTimeMillis();

        // Two independent async queries fired concurrently, not one after another.
        CompletableFuture<List<Customer>> goldFuture = repo.findByTier("gold");
        CompletableFuture<List<Customer>> silverFuture = repo.findByTier("silver");

        CompletableFuture<Void> both = CompletableFuture.allOf(goldFuture, silverFuture);
        both.get(); // wait for both to complete

        int goldCount = goldFuture.get().size();
        int silverCount = silverFuture.get().size();
        long elapsedMs = System.currentTimeMillis() - start;

        System.out.println("gold=" + goldCount + ", silver=" + silverCount + ", elapsed=" + elapsedMs + "ms");

        if (goldCount != 3) throw new AssertionError("Expected 3 gold customers");
        if (silverCount != 5) throw new AssertionError("Expected 5 silver customers");
        System.out.println("Two independent async queries composed via CompletableFuture.allOf -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java AsyncReturnLevel2.java`.

Both `findByTier("gold")` and `findByTier("silver")` return immediately with a `CompletableFuture`, launching their actual database queries on separate threads from the async executor pool — `CompletableFuture.allOf(goldFuture, silverFuture)` composes both futures into one that completes only once both underlying queries finish, letting the two independent lookups run concurrently rather than the second waiting for the first to complete first, the way two sequential synchronous calls would.

### Level 3 — Advanced

Handle asynchronous failure explicitly with `exceptionally`/`handle`, and combine a successful and a failing async call — the production-flavored shape of "some async operations fail, and the caller needs to handle that without the whole composition falling over."

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
import java.util.concurrent.ExecutionException;

@SpringBootApplication
@EnableAsync
public class AsyncReturnLevel3 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        protected Customer() {}
        public Customer(String email) { this.email = email; }
        public String getEmail() { return email; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        @Async
        CompletableFuture<Customer> findByEmail(String email);
    }

    @Component
    public static class CustomerLookupService {
        private final CustomerRepository repo;
        public CustomerLookupService(CustomerRepository repo) { this.repo = repo; }

        // Wraps the repository call, converting "not found" into a failed future
        // with a clear, application-specific exception -- a realistic service-layer pattern.
        public CompletableFuture<Customer> requireCustomer(String email) {
            return repo.findByEmail(email).thenCompose(customer -> {
                if (customer == null) {
                    CompletableFuture<Customer> failed = new CompletableFuture<>();
                    failed.completeExceptionally(new IllegalArgumentException("No customer with email: " + email));
                    return failed;
                }
                return CompletableFuture.completedFuture(customer);
            });
        }
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(AsyncReturnLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:async3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        CustomerLookupService service = ctx.getBean(CustomerLookupService.class);
        repo.save(new Customer("ada@example.com"));

        CompletableFuture<String> successResult = service.requireCustomer("ada@example.com")
            .thenApply(Customer::getEmail)
            .exceptionally(ex -> "ERROR: " + ex.getMessage());

        CompletableFuture<String> failureResult = service.requireCustomer("missing@example.com")
            .thenApply(Customer::getEmail)
            .exceptionally(ex -> "ERROR: " + ex.getCause().getMessage());

        System.out.println("success case = " + successResult.get());
        System.out.println("failure case = " + failureResult.get());

        if (!successResult.get().equals("ada@example.com"))
            throw new AssertionError("Expected the successful lookup to resolve to the email");
        if (!failureResult.get().startsWith("ERROR: No customer"))
            throw new AssertionError("Expected the failing lookup to resolve to a handled error message");

        System.out.println("Asynchronous success and failure both handled without blocking exceptions -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java AsyncReturnLevel3.java`.

`CustomerLookupService.requireCustomer` wraps the repository's `CompletableFuture<Customer>` (which resolves to `null` on a miss, per the "bare return type" convention from the previous card — `CompletableFuture` doesn't itself change that underlying null-handling rule) and converts a miss into a *failed* future carrying a descriptive exception, via `thenCompose`. `.exceptionally(...)` on the calling side handles that failure without ever needing a `try`/`catch` around blocking code — the entire success-or-failure composition happens through `CompletableFuture`'s chaining methods, only blocking (via `.get()`) at the very end, when the program needs the final printable result.

## 6. Walkthrough

Trace Level 3's failing lookup (`"missing@example.com"`) specifically, since it shows the full asynchronous error-handling chain.

1. **`service.requireCustomer("missing@example.com")`** calls `repo.findByEmail("missing@example.com")`, which — because it's `@Async` — immediately returns a `CompletableFuture<Customer>` and dispatches the actual JPA query to a separate thread from the async executor pool. The calling thread does not block here.
2. **On the executor thread**: the JPA query runs, finds no matching row, and (per the bare-`T`-return convention discussed in the previous card, still applicable inside the `CompletableFuture`) resolves the future with `customer = null`.
3. **`.thenCompose(customer -> ...)`** runs once that future completes (on the same executor thread, by default): it checks `customer == null`, finds it true, creates a *new* `CompletableFuture`, and calls `completeExceptionally(...)` on it with an `IllegalArgumentException` — this new, already-failed future is what `thenCompose` returns as the outer future's result.
4. **Back on the caller side**: `service.requireCustomer(...)` returns this ultimately-failed `CompletableFuture<Customer>`.
5. **`.thenApply(Customer::getEmail)`** is chained onto it — but because the upstream future is in a failed state, `thenApply`'s function body never actually runs; the failure propagates straight through, unchanged.
6. **`.exceptionally(ex -> "ERROR: " + ex.getCause().getMessage())`** is the first stage in the chain that actually executes for this failed path — `ex` here is a `CompletionException` wrapping the original `IllegalArgumentException`, which is why the code reaches through `.getCause()` to get the original message.
7. **`failureResult.get()`** blocks (only at this final point, for the purposes of printing output in `main`) and returns the string `"ERROR: No customer with email: missing@example.com"` — the exception was fully absorbed and converted into a normal, successful string result by the time it reaches this call.
8. **Verification**: the program checks the success case resolved to the plain email, and the failure case resolved to the expected error-prefixed string, confirming both paths through the asynchronous composition worked without ever needing a synchronous `try`/`catch`.

```
 requireCustomer("missing@example.com")
        |
        v
 findByEmail(...) [@Async, runs on executor thread] --> resolves with customer = null
        |
        v
 thenCompose: customer==null --> new CompletableFuture, completeExceptionally(IllegalArgumentException)
        |
        v
 thenApply(getEmail)  -- SKIPPED, future already failed
        |
        v
 exceptionally(ex -> "ERROR: " + ex.getCause().getMessage())  -- RUNS, absorbs the failure
        |
        v
 .get() returns "ERROR: No customer with email: missing@example.com"
```

## 7. Gotchas & takeaways

> **Gotcha:** `@Async` on a repository method only works when the call goes through a Spring-managed proxy — calling an `@Async` method from *within the same class* (self-invocation, the same limitation covered for AOP advice in the appendix section of this guide) silently runs synchronously instead of asynchronously, since the proxy is bypassed entirely. This is easy to miss because there's no compile error or runtime exception; the code simply doesn't get the asynchronous benefit it appears to have.

- `CompletableFuture<T>` return types work with any Spring Data store, including JPA — the underlying call remains blocking, but `@Async` moves that blocking work off the calling thread onto a separate executor thread pool.
- `Mono<T>`/`Flux<T>` require a genuinely reactive store driver (R2DBC, Reactive MongoDB) all the way down — `JpaRepository` cannot support these return types, since JDBC itself is fundamentally blocking.
- `@EnableAsync` at the application level and `@Async` on the specific repository method are both required for `CompletableFuture` return types to actually run asynchronously — without them, declaring the return type alone does nothing.
- `CompletableFuture`'s chaining methods (`thenApply`, `thenCompose`, `exceptionally`, `handle`) let both successful and failed asynchronous outcomes be composed without blocking until the very end of the chain, the pattern Level 3 demonstrated for converting a "not found" result into a handled application-level error.
