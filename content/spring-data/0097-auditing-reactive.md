---
card: spring-data
gi: 97
slug: auditing-reactive
title: "Auditing (reactive)"
---

## 1. What it is

`@EnableR2dbcAuditing` activates the same `@CreatedDate`/`@LastModifiedDate`/`@CreatedBy`/`@LastModifiedBy` auditing annotations covered for JPA and JDBC, but with one meaningful reactive-specific twist: `@CreatedBy`/`@LastModifiedBy` are sourced from a `ReactiveAuditorAware<T>` — returning `Mono<T>` instead of a plain value — because determining "who's currently acting" (typically from Spring Security's reactive `SecurityContext`) is itself a non-blocking, asynchronous operation in a reactive application.

```java
@EnableR2dbcAuditing
@SpringBootApplication
class Application { }

class ReactiveSpringSecurityAuditorAware implements ReactiveAuditorAware<String> {
    public Mono<String> getCurrentAuditor() {
        return ReactiveSecurityContextHolder.getContext().map(ctx -> ctx.getAuthentication().getName());
    }
}
```

## 2. Why & when

Both the JPA and JDBC auditing cards showed `AuditorAware<T>.getCurrentAuditor()` returning a plain value directly — trivial in a blocking application, since fetching "the current user" from a thread-bound security context is a synchronous, instant operation. In a reactive application, the security context itself is obtained asynchronously (from the same reactive `Context` mechanism the previous transactions card described), so the auditor lookup has to be reactive too — it can't just call a blocking method to get the answer.

Reach for `@EnableR2dbcAuditing` and `ReactiveAuditorAware` specifically when:

- You want the same automatic `createdAt`/`updatedAt` population as JPA/JDBC auditing, in a fully reactive R2DBC application, without breaking the non-blocking guarantee anywhere in the pipeline.
- You need `@CreatedBy`/`@LastModifiedBy` sourced from a reactive security context (Spring Security's `ReactiveSecurityContextHolder`) rather than a thread-bound one — `ReactiveAuditorAware<T>` is the only correct way to do this without introducing a blocking call.
- You're migrating auditing logic from a blocking JPA/JDBC application to R2DBC and need to know exactly what changes — the annotations stay the same; only the auditor-lookup interface's return type changes from a plain value to `Mono<T>`.

## 3. Core concept

```
 Blocking (JPA/JDBC):  interface AuditorAware<T> { T getCurrentAuditor(); }
                        -- synchronous, instant, thread-bound security context lookup

 Reactive (R2DBC):      interface ReactiveAuditorAware<T> { Mono<T> getCurrentAuditor(); }
                        -- ASYNCHRONOUS lookup, itself a non-blocking operation
                        -- the auditing callback must ALSO become reactive to consume this Mono
```

The auditing mechanism itself is unchanged conceptually — what changes is that "who is currently acting" is now itself an async value, not an instantly-available one.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Blocking auditor lookup returns a value directly, while reactive auditor lookup returns a Mono that must be composed into the save pipeline">
  <rect x="20" y="20" width="270" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">AuditorAware.getCurrentAuditor()</text>
  <text x="155" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">returns String directly, instantly</text>

  <rect x="350" y="20" width="270" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">ReactiveAuditorAware.getCurrentAuditor()</text>
  <text x="485" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">returns Mono&lt;String&gt; -- composed, not blocked on</text>

  <rect x="150" y="95" width="340" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">save() pipeline composes the auditor Mono via .flatMap()</text>
</svg>

The blocking auditor lookup is instant; the reactive one is itself a `Mono` that the save pipeline must compose into, never block on.

## 5. Runnable example

The scenario: creating and updating an order with reactive auditing, evolving from a synchronous auditor baseline (mirroring the JPA/JDBC cards), to the same lookup made asynchronous via `CompletableFuture` (standing in for `Mono`), to composing that async lookup correctly into a save pipeline without ever blocking.

### Level 1 — Basic

Model the blocking-style auditor lookup first, for direct contrast — identical in spirit to the JPA/JDBC auditing cards.

```java
import java.time.Instant;

class Order { long id; String status; Instant createdAt; String createdBy; Order(long id, String status) { this.id = id; this.status = status; } }

interface AuditorAware { String getCurrentAuditor(); } // blocking-style: returns the value directly

public class ReactiveAuditingLevel1 {
    static void save(Order order, AuditorAware auditor) {
        order.createdAt = Instant.now();
        order.createdBy = auditor.getCurrentAuditor(); // instant, synchronous
        System.out.println("Saved: createdBy=" + order.createdBy);
    }

    public static void main(String[] args) {
        AuditorAware auditor = () -> "ada"; // blocking lookup, trivial
        save(new Order(1, "PENDING"), auditor);
    }
}
```

How to run: `java ReactiveAuditingLevel1.java`

`getCurrentAuditor()` returns `"ada"` directly and instantly — this works fine in a blocking application, but assumes the current auditor is always immediately available without any asynchronous step, an assumption that breaks in a reactive application where the security context lookup is itself non-blocking.

### Level 2 — Intermediate

Make the auditor lookup asynchronous, using `CompletableFuture<String>` to stand in for `Mono<String>`, and update the save logic to correctly compose it rather than blocking on it.

```java
import java.time.Instant;
import java.util.concurrent.*;

class Order { long id; String status; Instant createdAt; String createdBy; Order(long id, String status) { this.id = id; this.status = status; } }

// interface ReactiveAuditorAware<String> { Mono<String> getCurrentAuditor(); }
interface ReactiveAuditorAware { CompletableFuture<String> getCurrentAuditor(); }

class SecurityContextAuditorAware implements ReactiveAuditorAware {
    public CompletableFuture<String> getCurrentAuditor() {
        // Simulates ReactiveSecurityContextHolder.getContext().map(ctx -> ctx.getAuthentication().getName())
        return CompletableFuture.supplyAsync(() -> { try { Thread.sleep(10); } catch (InterruptedException ignored) {} return "ada"; });
    }
}

public class ReactiveAuditingLevel2 {
    // The save pipeline COMPOSES the auditor lookup rather than blocking on it.
    static CompletableFuture<Order> save(Order order, ReactiveAuditorAware auditor) {
        return auditor.getCurrentAuditor().thenApply(who -> {
            order.createdAt = Instant.now();
            order.createdBy = who; // set only once the async lookup completes
            return order;
        });
    }

    public static void main(String[] args) throws Exception {
        ReactiveAuditorAware auditor = new SecurityContextAuditorAware();
        Order saved = save(new Order(1, "PENDING"), auditor).get(); // .get() only for demo purposes
        System.out.println("Saved: createdBy=" + saved.createdBy);
    }
}
```

How to run: `java ReactiveAuditingLevel2.java`

`save` no longer calls `getCurrentAuditor()` and expects an instant value back — it composes the async lookup with `.thenApply(who -> ...)`, setting `createdBy` only once the (simulated) reactive security-context lookup actually completes, matching how a real R2DBC auditing callback must `.flatMap()` into a `Mono<String>` rather than trying to synchronously extract a value from it.

### Level 3 — Advanced

Compose the auditor lookup into a full insert-vs-update auditing pipeline (mirroring the JDBC auditing card's insert/update distinction), entirely through reactive composition with no blocking calls anywhere.

```java
import java.time.Instant;
import java.util.concurrent.*;

class Order { Long id; String status; Instant createdAt; Instant updatedAt; String createdBy; String lastModifiedBy; Order(Long id, String status) { this.id = id; this.status = status; } }

interface ReactiveAuditorAware { CompletableFuture<String> getCurrentAuditor(); }

class SecurityContextAuditorAware implements ReactiveAuditorAware {
    private final String user;
    SecurityContextAuditorAware(String user) { this.user = user; }
    public CompletableFuture<String> getCurrentAuditor() {
        return CompletableFuture.supplyAsync(() -> { try { Thread.sleep(5); } catch (InterruptedException ignored) {} return user; });
    }
}

public class ReactiveAuditingLevel3 {
    // Fully reactive save: applies auditing (insert vs. update aware) via composition, never blocking.
    static CompletableFuture<Order> save(Order order, ReactiveAuditorAware auditor) {
        boolean isNew = order.id == null;
        return auditor.getCurrentAuditor().thenApply(who -> {
            Instant now = Instant.now();
            if (isNew) {
                order.createdAt = now;
                order.createdBy = who;
                order.id = 1L; // simulate database-assigned id
            }
            order.updatedAt = now;
            order.lastModifiedBy = who;
            return order;
        });
    }

    public static void main(String[] args) throws Exception {
        Order order = new Order(null, "PENDING");
        Order afterInsert = save(order, new SecurityContextAuditorAware("ada")).get(); // demo-only .get()
        System.out.println("After insert: createdBy=" + afterInsert.createdBy + ", lastModifiedBy=" + afterInsert.lastModifiedBy);
        Instant firstCreatedAt = afterInsert.createdAt;

        Thread.sleep(10);
        afterInsert.status = "SHIPPED";
        Order afterUpdate = save(afterInsert, new SecurityContextAuditorAware("alan")).get();

        System.out.println("After update: createdBy=" + afterUpdate.createdBy + " (unchanged), lastModifiedBy=" + afterUpdate.lastModifiedBy);
        System.out.println("createdAt unchanged? " + afterUpdate.createdAt.equals(firstCreatedAt));
    }
}
```

How to run: `java ReactiveAuditingLevel3.java`

`save` determines `isNew` up front (before the async auditor lookup even starts), then composes the rest of the auditing logic inside `.thenApply(who -> ...)` — once the reactive auditor `CompletableFuture` resolves, both the insert-only fields (`createdAt`, `createdBy`) and the always-updated fields (`updatedAt`, `lastModifiedBy`) are set correctly, all without a single blocking call, mirroring exactly the insert-vs-update-aware auditing behavior from the JDBC auditing card, now composed reactively.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `order` is constructed with `id = null`. `save(order, new SecurityContextAuditorAware("ada"))` runs: `isNew` is computed immediately as `true` (since `order.id == null`), *before* the asynchronous auditor lookup even begins — this ordering matters, because `isNew` must be captured based on the object's state at the start of the save, not after some unrelated async delay.

`auditor.getCurrentAuditor()` returns a `CompletableFuture` that resolves to `"ada"` after a simulated 5ms delay. `.thenApply(who -> ...)` registers the continuation: once `who` (`"ada"`) is available, `now` is captured, and since `isNew` is `true`, `createdAt`, `createdBy`, and a simulated database-assigned `id` (`1L`) are all set; `updatedAt`/`lastModifiedBy` are also set unconditionally. The resulting `afterInsert` has `createdBy="ada", lastModifiedBy="ada"`, and `firstCreatedAt` captures its `createdAt` for later comparison.

After a short sleep and changing `afterInsert.status` to `"SHIPPED"`, `save(afterInsert, new SecurityContextAuditorAware("alan"))` runs again — this time `isNew` evaluates to `false`, since `afterInsert.id` is now `1L` (non-null). The auditor lookup resolves to `"alan"` this time, and inside `.thenApply`, the `if (isNew)` block is skipped entirely — `createdAt`/`createdBy` are left untouched — while `updatedAt`/`lastModifiedBy` are refreshed to the new timestamp and `"alan"`.

The final printed lines confirm: `createdBy` is still `"ada"` while `lastModifiedBy` is now `"alan"`, and `afterUpdate.createdAt.equals(firstCreatedAt)` is `true` — exactly the insert-vs-update auditing distinction from the JDBC card, achieved here entirely through reactive composition with no blocking call anywhere in the pipeline.

```
save(order, auditor="ada"):  isNew=true (id==null)
  auditor.getCurrentAuditor() -> (async) -> "ada"
  .thenApply: createdAt=T1, createdBy=ada, id=1, updatedAt=T1, lastModifiedBy=ada

save(afterInsert, auditor="alan"):  isNew=false (id==1)
  auditor.getCurrentAuditor() -> (async) -> "alan"
  .thenApply: createdAt/createdBy UNCHANGED, updatedAt=T2>T1, lastModifiedBy=alan
```

In a real Spring Data R2DBC application, `@EnableR2dbcAuditing` registers a reactive-aware auditing callback that composes `ReactiveAuditorAware.getCurrentAuditor()`'s `Mono<String>` into the same `BeforeConvertCallback`-style hook the JDBC auditing card described, using `.flatMap()` instead of a direct value read — the insert-vs-update classification (based on the same `id == null`/`Persistable.isNew()` logic from the ID-generation card) still determines which fields get touched, but the actual auditor value is obtained through composition, never a blocking call, keeping the entire `orderRepository.save(order)` pipeline non-blocking end to end.

## 7. Gotchas & takeaways

> Gotcha: implementing `ReactiveAuditorAware.getCurrentAuditor()` by calling a *blocking* security API and wrapping its result in `Mono.just(...)` technically compiles and often "works" in casual testing, but it reintroduces exactly the blocking-call-inside-a-reactive-pipeline problem the reactive-transactions card warned about — the lookup must genuinely be non-blocking (e.g., built on `ReactiveSecurityContextHolder`), not merely wrapped in a reactive type after the fact.

- `@EnableR2dbcAuditing` provides the same auditing annotations as JPA/JDBC, but `@CreatedBy`/`@LastModifiedBy` are sourced from `ReactiveAuditorAware<T>`, returning `Mono<T>` instead of a plain value.
- The auditor lookup being asynchronous reflects that a reactive application's security context is itself obtained non-blockingly — the auditing mechanism has to compose with that, not block on it.
- Insert-vs-update field selection (`@CreatedDate`/`@CreatedBy` only on insert, `@LastModifiedDate`/`@LastModifiedBy` on every save) works identically to the JDBC module — only the auditor-lookup step's asynchrony is new.
- A `ReactiveAuditorAware` implementation must genuinely be non-blocking internally — wrapping a blocking call in `Mono.just(...)` defeats the purpose and risks the same thread-pool-starvation problem as any other blocking call in a reactive pipeline.
