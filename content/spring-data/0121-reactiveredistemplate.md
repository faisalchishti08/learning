---
card: spring-data
gi: 121
slug: reactiveredistemplate
title: "ReactiveRedisTemplate"
---

## 1. What it is

`ReactiveRedisTemplate<K, V>` is the non-blocking counterpart to `RedisTemplate`: every operation returns a `Mono` (single value) or `Flux` (stream of values) instead of the value directly, matching the reactive style already seen in the R2DBC and reactive MongoDB cards. It requires a reactive-capable connection factory — Lettuce supports this natively; Jedis, being fundamentally blocking, does not.

```java
@Autowired ReactiveRedisTemplate<String, String> reactiveRedisTemplate;

Mono<Boolean> written = reactiveRedisTemplate.opsForValue().set("order:1:status", "PENDING");
Mono<String> status = reactiveRedisTemplate.opsForValue().get("order:1:status");
```

## 2. Why & when

`RedisTemplate` blocks the calling thread until Redis responds. In a reactive application — one built on WebFlux, R2DBC, and reactive MongoDB, as covered in earlier sections — a blocking Redis call would defeat the whole point of the reactive stack, tying up an event-loop thread while waiting on network I/O. `ReactiveRedisTemplate` closes that gap, giving Redis access that composes naturally with the rest of a reactive pipeline.

Reach for `ReactiveRedisTemplate` when:

- The rest of your call chain is already reactive (a WebFlux controller returning `Mono<Order>` that needs to check or update a Redis-backed cache along the way) — mixing a blocking `RedisTemplate` call into that chain would block an event-loop thread.
- You want to compose Redis operations with other reactive sources — combining a Redis lookup with an R2DBC query via `zipWith`/`flatMap`, for example.
- You're streaming a large result set from Redis (a big `Flux` from a scan or a Redis Stream, covered in a later card) and want backpressure-aware consumption rather than loading everything into memory at once.

## 3. Core concept

```
 RedisTemplate.opsForValue().get(key)              -> String        (BLOCKS the calling thread)
 ReactiveRedisTemplate.opsForValue().get(key)       -> Mono<String>  (returns IMMEDIATELY, subscribe to get the value)

   Mono<String> statusMono = reactiveRedisTemplate.opsForValue().get("order:1:status");
   // nothing has happened with Redis yet -- statusMono is just a description of the operation

   statusMono.subscribe(status -> System.out.println("Got: " + status));
   // NOW the Redis call actually executes, asynchronously
```

Exactly like `Mono<Order>` from `ReactiveMongoTemplate` or `ReactiveCrudRepository`, nothing happens until something subscribes — building the pipeline and running it are two separate steps.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ReactiveRedisTemplate call returns a Mono immediately; the actual Redis round trip only happens once something subscribes">
  <rect x="20" y="20" width="220" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">opsForValue().get(key)</text>

  <rect x="290" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="365" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Mono&lt;String&gt;</text>

  <line x1="240" y1="42" x2="285" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <text x="262" y="32" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">returns instantly</text>

  <rect x="480" y="20" width="140" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="550" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">.subscribe(...)</text>

  <line x1="440" y1="42" x2="475" y2="42" stroke="#8b949e" stroke-width="1.3" stroke-dasharray="4,3"/>

  <text x="320" y="110" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">the Redis network round trip only happens after .subscribe() runs</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Building the reactive pipeline and executing it against Redis are two separate, independent steps.

## 5. Runnable example

The scenario: reading and writing an order's cached status reactively, evolving from a `CompletableFuture`-based stand-in for `Mono` (the same convention used in the earlier R2DBC and reactive MongoDB cards), to composing multiple reactive Redis operations together, to a `Flux`-style batch read across several keys.

### Level 1 — Basic

Model the non-blocking `get`/`set`, returning a handle immediately rather than the value directly.

```java
import java.util.*;
import java.util.concurrent.*;

public class ReactiveRedisLevel1 {
    public static void main(String[] args) throws Exception {
        ReactiveRedisTemplate redisTemplate = new ReactiveRedisTemplate();

        CompletableFuture<Boolean> written = redisTemplate.opsForValue().set("order:1:status", "PENDING");
        System.out.println("set() call returned immediately; write may not be done yet.");
        written.get(); // wait here ONLY for demo purposes

        CompletableFuture<String> statusFuture = redisTemplate.opsForValue().get("order:1:status"); // returns IMMEDIATELY
        System.out.println("get() call returned immediately; value not read yet.");
        String status = statusFuture.get(); // wait here ONLY for demo purposes
        System.out.println("Eventually resolved: " + status);
    }
}

class RedisServer { Map<String, String> data = new HashMap<>(); }

// Stands in for Mono<T>-returning reactive value operations.
class ReactiveValueOperations {
    private final RedisServer server;
    ReactiveValueOperations(RedisServer server) { this.server = server; }
    CompletableFuture<Boolean> set(String key, String value) {
        return CompletableFuture.supplyAsync(() -> { server.data.put(key, value); return true; });
    }
    CompletableFuture<String> get(String key) {
        return CompletableFuture.supplyAsync(() -> server.data.get(key));
    }
}

class ReactiveRedisTemplate {
    private final RedisServer server = new RedisServer();
    private final ReactiveValueOperations valueOps = new ReactiveValueOperations(server);
    ReactiveValueOperations opsForValue() { return valueOps; }
}
```

How to run: `java ReactiveRedisLevel1.java`

`set`/`get` both return a `CompletableFuture` (standing in for `Mono<Boolean>`/`Mono<String>`) the instant they're called, before the underlying Redis operation has necessarily completed — mirroring exactly how `ReactiveMongoTemplate` and R2DBC's `ReactiveCrudRepository` behaved in earlier cards, just applied to Redis.

### Level 2 — Intermediate

Compose two reactive Redis operations together — check a cache flag, then conditionally fetch a value — using `thenCompose`, matching how real reactive code chains `Mono`s with `flatMap`.

```java
import java.util.*;
import java.util.concurrent.*;

public class ReactiveRedisLevel2 {
    public static void main(String[] args) throws Exception {
        ReactiveRedisTemplate redisTemplate = new ReactiveRedisTemplate();
        redisTemplate.opsForValue().set("order:1:cached", "true").get();
        redisTemplate.opsForValue().set("order:1:status", "SHIPPED").get();

        // Mirrors: reactiveRedisTemplate.opsForValue().get("order:1:cached")
        //              .flatMap(cached -> "true".equals(cached)
        //                  ? reactiveRedisTemplate.opsForValue().get("order:1:status")
        //                  : Mono.just("NOT CACHED"))
        CompletableFuture<String> pipeline = redisTemplate.opsForValue().get("order:1:cached")
            .thenCompose(cached -> "true".equals(cached)
                ? redisTemplate.opsForValue().get("order:1:status")
                : CompletableFuture.completedFuture("NOT CACHED"));

        System.out.println("Pipeline built; nothing executed synchronously here.");
        System.out.println("Result: " + pipeline.get()); // .get() used only for demo sequencing
    }
}

class RedisServer { Map<String, String> data = new HashMap<>(); }

class ReactiveValueOperations {
    private final RedisServer server;
    ReactiveValueOperations(RedisServer server) { this.server = server; }
    CompletableFuture<Boolean> set(String key, String value) {
        return CompletableFuture.supplyAsync(() -> { server.data.put(key, value); return true; });
    }
    CompletableFuture<String> get(String key) {
        return CompletableFuture.supplyAsync(() -> server.data.get(key));
    }
}

class ReactiveRedisTemplate {
    private final RedisServer server = new RedisServer();
    private final ReactiveValueOperations valueOps = new ReactiveValueOperations(server);
    ReactiveValueOperations opsForValue() { return valueOps; }
}
```

How to run: `java ReactiveRedisLevel2.java`

`thenCompose` chains a second asynchronous Redis call to run only after the first one resolves and only if the cached flag is `"true"` — exactly the shape `Mono.flatMap` produces in real reactive code. No thread blocks waiting between the two Redis calls; the whole chain is described up front and only executes when something (here, the demo's final `.get()`) triggers it.

### Level 3 — Advanced

Read several keys as a batch, mirroring a `Flux<String>` built from `Flux.fromIterable(keys).flatMap(redisTemplate.opsForValue()::get)` — concurrent reads composed into one stream of results.

```java
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class ReactiveRedisLevel3 {
    public static void main(String[] args) throws Exception {
        ReactiveRedisTemplate redisTemplate = new ReactiveRedisTemplate();
        redisTemplate.opsForValue().set("order:1:status", "PENDING").get();
        redisTemplate.opsForValue().set("order:2:status", "SHIPPED").get();
        redisTemplate.opsForValue().set("order:3:status", "DELIVERED").get();

        List<String> keys = List.of("order:1:status", "order:2:status", "order:3:status", "order:404:status");

        // Mirrors: Flux.fromIterable(keys).flatMap(redisTemplate.opsForValue()::get)
        List<CompletableFuture<String>> futures = keys.stream()
            .map(key -> redisTemplate.opsForValue().get(key)) // all READS launched CONCURRENTLY, not one at a time
            .collect(Collectors.toList());

        System.out.println("All " + futures.size() + " reads launched concurrently; none have necessarily completed yet.");

        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).get(); // wait for the whole batch, demo only
        List<String> results = futures.stream().map(CompletableFuture::join).collect(Collectors.toList());

        for (int i = 0; i < keys.size(); i++) System.out.println(keys.get(i) + " -> " + results.get(i));
    }
}

class RedisServer { Map<String, String> data = new HashMap<>(); }

class ReactiveValueOperations {
    private final RedisServer server;
    ReactiveValueOperations(RedisServer server) { this.server = server; }
    CompletableFuture<Boolean> set(String key, String value) {
        return CompletableFuture.supplyAsync(() -> { server.data.put(key, value); return true; });
    }
    CompletableFuture<String> get(String key) {
        return CompletableFuture.supplyAsync(() -> server.data.get(key));
    }
}

class ReactiveRedisTemplate {
    private final RedisServer server = new RedisServer();
    private final ReactiveValueOperations valueOps = new ReactiveValueOperations(server);
    ReactiveValueOperations opsForValue() { return valueOps; }
}
```

How to run: `java ReactiveRedisLevel3.java`

All four `get` calls are launched up front, without waiting for any single one to finish first — standing in for `Flux.fromIterable(keys).flatMap(...)`, which subscribes to each inner `Mono` concurrently rather than sequentially. The missing key (`order:404:status`) resolves to `null`, exactly like a real Redis `GET` on an absent key, without breaking the batch.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three status values are written and awaited (using `.get()` purely for demo sequencing — a real reactive pipeline wouldn't block here). Then `keys.stream().map(key -> redisTemplate.opsForValue().get(key))` calls `get` for all four keys in a tight loop, immediately collecting four `CompletableFuture<String>` objects into `futures` — none of the underlying reads have necessarily finished by the time this line completes, because each `get` call only *starts* an asynchronous lookup.

`CompletableFuture.allOf(...).get()` then blocks (again, only for this demo's own sequencing) until every one of the four futures has resolved. `futures.stream().map(CompletableFuture::join)` extracts each resolved value in the same order the keys were requested in, giving `results` a value (or `null`) for each key. The final loop pairs each key back up with its resolved result and prints them.

```
All 4 reads launched concurrently; none have necessarily completed yet.
order:1:status -> PENDING
order:2:status -> SHIPPED
order:3:status -> DELIVERED
order:404:status -> null
```

In real reactive code, `Flux.fromIterable(keys).flatMap(reactiveRedisTemplate.opsForValue()::get)` produces a `Flux<String>` that emits results as each underlying Redis call completes — not necessarily in request order unless `flatMapSequential` is used instead of `flatMap` — and the whole pipeline is subscribed to exactly once by whatever consumes the final `Flux` (a WebFlux response body, for example), with backpressure applied automatically if the consumer can't keep up.

## 7. Gotchas & takeaways

> Gotcha: `flatMap` on a `Flux` does **not** guarantee the output order matches the input order, because inner publishers can complete in any sequence — if you need results in the same order the keys were requested, use `flatMapSequential` (which preserves order but loses some concurrency) or `concatMap` (fully sequential).

> Gotcha: mixing a blocking `RedisTemplate` call into an otherwise-reactive WebFlux request path silently blocks a shared event-loop thread — since a small, fixed pool of those threads serves *all* concurrent requests, one blocking call can stall unrelated requests too. Use `ReactiveRedisTemplate` consistently once you're in a reactive call chain.

- `ReactiveRedisTemplate` mirrors `RedisTemplate`'s API shape, but every operation returns `Mono`/`Flux` instead of a direct value, and nothing runs until something subscribes.
- It requires a reactive-capable connection factory (Lettuce); Jedis does not support the reactive style.
- Chain multiple Redis calls with `flatMap`/`then`/`zipWith` rather than blocking between them, to keep the whole pipeline non-blocking end to end.
- Batch reads across many keys via `Flux.fromIterable(...).flatMap(...)` run concurrently by default — use `flatMapSequential` if result order must match request order.
