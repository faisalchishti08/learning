---
card: spring-framework
gi: 447
slug: kotlin-coroutines-support-suspend-functions-flow
title: "Kotlin coroutines support (suspend functions, Flow)"
---

## 1. What it is

Spring WebFlux and related reactive modules natively support Kotlin coroutines as an alternative to `Mono`/`Flux` — a `@RestController` method can be a `suspend fun` returning a plain value, and `Flow<T>` (Kotlin's coroutine-based streaming type) works as a drop-in alternative to `Flux<T>` for multi-value responses. Spring automatically bridges between coroutines and Reactor underneath, so both styles interoperate freely.

```kotlin
@RestController
class ProductController(private val repository: ProductRepository) {
    @GetMapping("/products/{id}")
    suspend fun getProduct(@PathVariable id: Long): Product =
        repository.findById(id) ?: throw ProductNotFoundException(id)

    @GetMapping("/products/stream")
    fun streamProducts(): Flow<Product> = repository.findAllAsFlow()
}
```

## 2. Why & when

`Mono`/`Flux` are Reactor's reactive types, and they work fine from Kotlin — but they carry Reactor's own operator vocabulary (`map`, `flatMap`, `zip`, and dozens more) on top of what Kotlin already offers natively through coroutines and `Flow`. Coroutines let you write asynchronous, non-blocking code that *reads* like ordinary sequential code (`val product = repository.findById(id)` instead of `.flatMap { ... }` chains), while still being genuinely non-blocking underneath — the compiler transforms `suspend` functions into state machines that yield control during actual I/O waits, without ever blocking a thread. Spring's coroutine support exists so Kotlin developers can use this idiom directly in Spring applications, rather than being forced into Reactor's chain-based style just because the underlying transport is reactive.

Reach for coroutines over `Mono`/`Flux` in a Kotlin Spring application when:

- You want asynchronous code that reads sequentially rather than as an operator chain — genuinely easier for many developers to read and reason about, especially for logic with several sequential dependent steps.
- Your team is already comfortable with Kotlin coroutines from other parts of the codebase (Android, other Kotlin services) and wants consistency in async style.
- You need to call other `suspend fun`-based libraries or code directly, without wrapping/unwrapping between coroutines and Reactor at every boundary.

`Flux`/`Mono` remain fully supported and interoperate seamlessly — this isn't an either/or decision forced on the whole codebase; individual controller methods or service classes can use whichever style fits, and Spring bridges between them automatically where needed.

## 3. Core concept

```
 suspend fun getProduct(id: Long): Product
        |
        | Spring's coroutine adapter (built on kotlinx-coroutines-reactor)
        | wraps this in a Mono<Product> internally for the reactive dispatch machinery
        v
 DispatcherHandler dispatches exactly as it would for a Mono-returning method
        |
        v
 the suspend function's actual execution:
   suspends at each `suspend fun` call site that does real I/O
   (e.g. a coroutine-based repository call) -- WITHOUT blocking the thread
        |
        v
 resumes when the I/O completes, continues execution, eventually returns Product
```

```
 Flow<Product>
        |
        | bridged to Flux<Product> internally for reactive dispatch
        v
 same request-handling machinery as a Flux-returning method,
 just described using Kotlin's Flow builder/operator vocabulary instead of Reactor's
```

Both bridges are implemented once, inside Spring's WebFlux integration — application code never needs to manually convert between `suspend`/`Flow` and `Mono`/`Flux`; the framework does it transparently at the dispatch boundary.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Suspend functions and Flow are bridged to Mono and Flux by Spring's coroutine integration, transparently to application code">
  <rect x="10" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">suspend fun / Flow</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Kotlin coroutines</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring bridge</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">kotlinx-coroutines-reactor</text>

  <rect x="470" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Mono / Flux</text>
  <text x="550" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same dispatch machinery</text>

  <line x1="190" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="465" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two async styles, one underlying dispatch mechanism, bridged transparently.

## 5. Runnable example

### Level 1 — Basic

A `suspend fun` service method called from `runBlocking` (standing in for Spring's own coroutine dispatch, which would call it non-blockingly in a real WebFlux request), showing suspension without threading complexity yet.

```kotlin
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking

data class Product(val id: Long, val name: String)

class ProductRepository {
    private val products = mapOf(1L to Product(1, "Laptop"))

    suspend fun findById(id: Long): Product? {
        delay(20) // simulates a non-blocking I/O call (e.g. R2DBC, a reactive HTTP client)
        return products[id]
    }
}

class ProductService(private val repository: ProductRepository) {
    suspend fun getProduct(id: Long): Product =
        repository.findById(id) ?: throw NoSuchElementException("Product $id not found")
}

fun main() = runBlocking {
    val service = ProductService(ProductRepository())

    val product = service.getProduct(1)
    println("Found: $product")
    check(product.name == "Laptop")

    try {
        service.getProduct(999)
        error("Expected an exception for a missing product")
    } catch (e: NoSuchElementException) {
        println("Correctly threw for missing product: ${e.message}")
    }

    println("Sequential-reading suspend function chain -- PASS")
}
```

How to run: add `kotlinx-coroutines-core` and the Kotlin standard library to the classpath, then `kotlinc AppConfig.kt -include-runtime -d app.jar && java -jar app.jar`.

`repository.findById(id)` reads like an ordinary, blocking function call — `service.getProduct(id)`'s body has no `.flatMap`, no callback, just sequential code with an Elvis-operator null check — but `delay(20)` genuinely suspends the coroutine without blocking the underlying thread, exactly the non-blocking behavior `Mono`/`Flux` provide, just expressed through Kotlin's native async syntax instead of Reactor's operator chains.

### Level 2 — Intermediate

A `suspend fun` Spring WebFlux controller method, tested via `WebTestClient` — showing coroutines actually integrated with Spring's real dispatch machinery, not just standalone Kotlin code.

```kotlin
import org.springframework.test.web.reactive.server.WebTestClient
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RestController
import kotlinx.coroutines.delay

data class Product(val id: Long, val name: String)

class ProductNotFoundException(id: Long) : RuntimeException("Product $id not found")

class ProductRepository {
    private val products = mapOf(1L to Product(1, "Laptop"))
    suspend fun findById(id: Long): Product? {
        delay(20)
        return products[id]
    }
}

@RestController
class ProductController(private val repository: ProductRepository) {
    @GetMapping("/products/{id}")
    suspend fun getProduct(@PathVariable id: Long): Product =
        repository.findById(id) ?: throw ProductNotFoundException(id)
}

fun main() {
    val controller = ProductController(ProductRepository())
    val client = WebTestClient.bindToController(controller).build()

    client.get().uri("/products/1")
        .exchange()
        .expectStatus().isOk
        .expectBody()
        .jsonPath("$.name").isEqualTo("Laptop")

    println("suspend fun controller method dispatched correctly by WebTestClient -- PASS")
}
```

How to run: add `spring-webflux`, `spring-test`, `kotlinx-coroutines-core`, `kotlinx-coroutines-reactor`, Jackson, and the Kotlin standard library to the classpath, then compile and run identically.

`suspend fun getProduct(...): Product` is a genuine `@GetMapping`-annotated controller method — Spring's WebFlux integration recognizes the `suspend` modifier and automatically wraps the call using `kotlinx-coroutines-reactor`'s bridging (via `mono { }` internally), so `WebTestClient`'s request dispatch works exactly as it would against a `Mono<Product>`-returning method, with the coroutine machinery entirely transparent to both the controller code and the test.

### Level 3 — Advanced

A `Flow<T>`-returning streaming endpoint, plus a coroutine-based error-handling and concurrency pattern (`coroutineScope` with parallel `async` calls) — demonstrating both of the section's core concept map's coroutine capabilities together.

```kotlin
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.reactive.asFlow
import kotlinx.coroutines.runBlocking
import org.springframework.test.web.reactive.server.WebTestClient
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController

data class Product(val id: Long, val name: String, val price: Double)
data class Inventory(val productId: Long, val quantity: Int)
data class ProductWithStock(val product: Product, val inStock: Int)

class ProductRepository {
    private val products = listOf(
            Product(1, "Laptop", 999.99), Product(2, "Mouse", 19.99), Product(3, "Keyboard", 49.99))

    fun streamAll(): Flow<Product> = flow {
        for (product in products) {
            delay(5) // simulates each row arriving incrementally from a reactive data source
            emit(product)
        }
    }

    suspend fun findById(id: Long): Product? {
        delay(10)
        return products.find { it.id == id }
    }
}

class InventoryService {
    suspend fun getStock(productId: Long): Int {
        delay(15) // simulates an independent, slower downstream call
        return (productId * 3).toInt()
    }
}

class CatalogService(
        private val productRepository: ProductRepository,
        private val inventoryService: InventoryService
) {
    // Fetches product AND inventory data CONCURRENTLY, not sequentially --
    // coroutineScope + async is the coroutine-native way to parallelize suspend calls.
    suspend fun getProductWithStock(id: Long): ProductWithStock = coroutineScope {
        val productDeferred = async { productRepository.findById(id) }
        val stockDeferred = async { inventoryService.getStock(id) }

        val product = productDeferred.await() ?: throw NoSuchElementException("Product $id not found")
        val stock = stockDeferred.await()
        ProductWithStock(product, stock)
    }
}

@RestController
class CatalogController(private val repository: ProductRepository, private val catalog: CatalogService) {
    @GetMapping("/products/stream")
    fun streamProducts(): Flow<Product> = repository.streamAll()
}

fun main() = runBlocking {
    val repository = ProductRepository()
    val inventory = InventoryService()
    val catalog = CatalogService(repository, inventory)

    // Test 1: Flow-based streaming, collected via WebTestClient (Spring integration)
    val controller = CatalogController(repository, catalog)
    val client = WebTestClient.bindToController(controller).build()

    val streamedProducts = client.get().uri("/products/stream")
            .exchange()
            .expectStatus().isOk
            .returnResult(Product::class.java)
            .responseBody // a reactor.core.publisher.Flux<Product>

    // main() is already inside runBlocking, so this suspend call can run directly here --
    // asFlow() (kotlinx-coroutines-reactive) bridges the Flux back into a Kotlin Flow to collect.
    val collected = streamedProducts.asFlow().toList()
    println("Streamed ${collected.size} products via Flow")
    check(collected.size == 3)

    // Test 2: concurrent suspend calls via coroutineScope + async
    val startMs = System.currentTimeMillis()
    val result = catalog.getProductWithStock(1)
    val elapsedMs = System.currentTimeMillis() - startMs

    println("Result: $result (took ${elapsedMs}ms)")
    check(result.product.name == "Laptop")
    check(result.inStock == 3)
    // Concurrent (not sequential): should take close to max(10ms, 15ms), NOT their sum (25ms).
    check(elapsedMs < 25) { "Expected concurrent execution to be faster than sequential" }

    println("Flow streaming + concurrent suspend calls via coroutineScope/async -- PASS")
}
```

How to run: add `spring-webflux`, `spring-test`, `kotlinx-coroutines-core`, `kotlinx-coroutines-reactor`, `kotlinx-coroutines-reactive`, Jackson, and the Kotlin standard library to the classpath, then compile and run identically.

`coroutineScope { async { ... }; async { ... } }` launches both the product lookup and the inventory lookup *concurrently* — `productDeferred.await()` and `stockDeferred.await()` each suspend until their respective result is ready, but because both `async` blocks started running immediately and independently, the total elapsed time reflects the *slower* of the two calls (roughly 15ms), not their sum (25ms) — the coroutine-native equivalent of `Mono.zip(...)`'s concurrent-combination behavior from the reactive `WebClient` card earlier in this content. `Flow<Product>` from `streamAll()` is returned directly from a `@GetMapping` method exactly like a `Flux<Product>` would be, with Spring's bridging making the two interchangeable from the framework's perspective.

## 6. Walkthrough

Trace `catalog.getProductWithStock(1)` in `main()`:

1. **`coroutineScope` entered.** This creates a new coroutine scope tied to the calling coroutine — any child coroutines launched within it (the two `async` blocks) must complete before `coroutineScope` itself returns, providing structured concurrency (no orphaned background work).
2. **Both `async` blocks launch immediately.** `productDeferred = async { productRepository.findById(1) }` and `stockDeferred = async { inventoryService.getStock(1) }` both start executing right away, concurrently — neither waits for the other to begin.
3. **Both suspend independently.** `productRepository.findById(1)` hits its `delay(10)`, suspending that coroutine for ~10ms; `inventoryService.getStock(1)` hits its own `delay(15)`, suspending for ~15ms — both suspensions happen in parallel, on whatever underlying dispatcher coroutines are running on (non-blocking, so no threads are tied up waiting).
4. **First `await()` call.** `productDeferred.await()` suspends the calling code until the product lookup's coroutine completes — which happens after ~10ms, returning `Product(1, "Laptop", 999.99)`. Since this is non-null, the Elvis operator's fallback (`throw NoSuchElementException`) never executes.
5. **Second `await()` call.** `stockDeferred.await()` suspends until the inventory lookup completes — but since that coroutine started at the same time as the product lookup and only needs ~15ms total, and 10ms have already elapsed while `await()`ing the product, this second `await()` only needs to wait roughly ~5 more milliseconds (the remainder of its 15ms delay), not a fresh 15ms — because it was running concurrently the whole time, not started only after the first `await()` returned.
6. **Result constructed.** `ProductWithStock(product, stock)` combines both results; `coroutineScope { }` returns this value once both child coroutines have completed.
7. **Timing confirms concurrency.** The measured `elapsedMs` comes out close to 15ms (the slower of the two calls), not 25ms (their sum) — proving the two `suspend` calls genuinely ran in parallel rather than one after another, confirmed by the `check(elapsedMs < 25)` assertion.

```
coroutineScope {
    async { findById(1) }     -- starts immediately, suspends ~10ms
    async { getStock(1) }     -- starts immediately (concurrently), suspends ~15ms

    productDeferred.await()   -- waits ~10ms -> Product(Laptop)
    stockDeferred.await()     -- ALREADY ~10ms into its own 15ms wait -> waits ~5 more ms -> 3

    -> ProductWithStock(Laptop, 3)
}
Total elapsed: ~15ms (the SLOWER call), not 10+15=25ms (proves concurrency, not sequencing)
```

## 7. Gotchas & takeaways

> Gotcha: writing `productRepository.findById(id)` followed by `inventoryService.getStock(id)` as two sequential `suspend fun` calls (without `coroutineScope`/`async`) runs them **sequentially**, not concurrently — `suspend` alone doesn't imply parallelism, it only implies "this call can suspend without blocking a thread while it waits." Genuine concurrency between multiple independent `suspend` calls requires explicitly launching them with `async` (or `launch`) inside a `coroutineScope`, exactly as Level 3 does — a common mistake is assuming sequential `suspend fun` calls are automatically parallel just because they're non-blocking.

- Spring's coroutine support bridges `suspend fun` and `Flow<T>` to `Mono`/`Flux` transparently at the WebFlux dispatch boundary — application code never manually converts between the two styles, and both interoperate freely within the same codebase.
- Coroutines let asynchronous, non-blocking code read as ordinary sequential logic, in contrast to Reactor's operator-chain style — a readability trade-off some teams strongly prefer, without sacrificing non-blocking behavior.
- Sequential `suspend fun` calls run sequentially, not concurrently — use `coroutineScope { async { ... }; async { ... } }` to explicitly parallelize independent suspend calls, the coroutine-native equivalent of `Mono.zip(...)`.
- `Flow<T>` returned directly from a `@GetMapping` method works exactly like `Flux<T>` from Spring's dispatch perspective — choose whichever reactive-type vocabulary (Reactor or coroutines) fits your team's style, since Spring treats them as interchangeable at the framework boundary.
