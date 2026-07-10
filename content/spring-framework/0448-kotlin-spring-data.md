---
card: spring-framework
gi: 448
slug: kotlin-spring-data
title: "Kotlin & Spring Data"
---

## 1. What it is

Spring Data works with Kotlin idiomatically: repository interfaces can declare `suspend fun` query methods (returning results non-blockingly, bridged the same way WebFlux controller methods are), `data class` entities express immutable, concise domain models with Kotlin's null-safety directly reflecting which fields are genuinely optional, and Kotlin extension functions (like `findByIdOrNull`) smooth over a few JPA/Spring Data APIs that were originally designed around Java's `Optional<T>` rather than Kotlin's native nullable types.

```kotlin
interface ProductRepository : CoroutineCrudRepository<Product, Long> {
    suspend fun findByNameContaining(name: String): List<Product>
}

data class Product(@Id val id: Long? = null, val name: String, val price: Double)
```

## 2. Why & when

Spring Data's repository interfaces are already minimal — you declare an interface, Spring Data generates the implementation — but a few of the underlying conventions (Java's `Optional<T>` for possibly-missing results, mutable JavaBean-style entities with no-arg constructors) don't map perfectly onto idiomatic Kotlin. Kotlin support in Spring Data closes those gaps: reactive/coroutine repository variants (`CoroutineCrudRepository`) let query methods be `suspend fun`s returning plain nullable types instead of `Optional<T>`, and `data class` entities work directly with Spring Data's persistence mechanisms (JPA, R2DBC, MongoDB) without needing a mutable JavaBean shape.

This matters when:

- You're modeling domain entities in Kotlin and want them as `data class`es — concise, immutable by default, with generated `equals`/`hashCode`/`copy` — rather than verbose, mutable Java-style entity classes.
- You're using Spring Data with a reactive or coroutine-based data access technology (R2DBC, reactive MongoDB) and want repository methods expressed as `suspend fun`s rather than `Mono`/`Flux`-returning Java-style methods.
- You want query results that might be absent expressed as Kotlin's native `T?` rather than wrapping every possibly-empty result in `Optional<T>`, which the null-safety card in this section already established as the more idiomatic Kotlin approach wherever Spring's APIs support it.

## 3. Core concept

```
 Blocking Spring Data (works fine from Kotlin, Java-shaped API):
   interface ProductRepository : CrudRepository<Product, Long> {
       fun findByName(name: String): Optional<Product>   <- Java's Optional
   }

 Coroutine-based Spring Data (Kotlin-idiomatic):
   interface ProductRepository : CoroutineCrudRepository<Product, Long> {
       suspend fun findByName(name: String): Product?     <- Kotlin's native nullable type
   }

 data class Product(
     @Id val id: Long? = null,     <- null before persistence, non-null after
     val name: String,
     val price: Double
 )
```

The generated implementation behavior is conceptually identical either way — Spring Data still derives the query from the method name or an explicit `@Query` — only the surrounding type signatures differ, matched to each language's own idioms.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kotlin data class entities and suspend repository methods layered on the same Spring Data query-derivation mechanism">
  <rect x="10" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">data class Product</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Id val id: Long?</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CoroutineCrudRepository</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">suspend fun findByName</text>

  <rect x="470" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Query derivation</text>
  <text x="550" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same mechanism as Java</text>

  <line x1="190" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="465" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Kotlin-specific types and syntax, same underlying Spring Data query-generation machinery.

## 5. Runnable example

Since a real JPA/R2DBC setup needs an actual database driver and schema, this example uses an in-memory repository implementing the same `CoroutineCrudRepository`-shaped contract by hand — letting the focus stay on the Kotlin-specific typing and API idioms (nullable results, `data class` entities, `suspend fun` methods) rather than database/driver setup, while still being genuinely runnable in one file.

### Level 1 — Basic

A `data class` entity and a repository-shaped interface with `suspend fun` methods returning Kotlin-native nullable types, backed by an in-memory implementation.

```kotlin
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking

data class Product(val id: Long? = null, val name: String, val price: Double)

interface ProductRepository {
    suspend fun findById(id: Long): Product?
    suspend fun save(product: Product): Product
}

class InMemoryProductRepository : ProductRepository {
    private val storage = mutableMapOf<Long, Product>()
    private var nextId = 1L

    override suspend fun findById(id: Long): Product? {
        delay(5) // simulates real I/O latency
        return storage[id]
    }

    override suspend fun save(product: Product): Product {
        delay(5)
        val id = product.id ?: nextId++
        val saved = product.copy(id = id) // data class copy(): new instance, only id changed
        storage[id] = saved
        return saved
    }
}

fun main() = runBlocking {
    val repository: ProductRepository = InMemoryProductRepository()

    val saved = repository.save(Product(name = "Laptop", price = 999.99))
    println("Saved: $saved")
    check(saved.id != null) { "Expected an id to be assigned after saving" }

    val found = repository.findById(saved.id!!)
    println("Found: $found")
    check(found == saved) { "data class equals() should treat identical field values as equal" }

    val notFound = repository.findById(999)
    println("Not found result: $notFound")
    check(notFound == null)

    println("data class entity + suspend repository methods -- PASS")
}
```

How to run: add `kotlinx-coroutines-core` and the Kotlin standard library to the classpath, then `kotlinc AppConfig.kt -include-runtime -d app.jar && java -jar app.jar`.

`Product(id: Long? = null, ...)` reflects the real lifecycle of an entity's identifier: `null` before it's ever been saved (the database hasn't assigned an id yet), non-null afterward — exactly the pattern Spring Data JPA/R2DBC entities use in Kotlin. `product.copy(id = id)` uses the `data class`-generated `copy()` method to produce a new, otherwise-identical `Product` with just the `id` field set — since `data class` instances are conventionally treated as immutable, "updating" a field means creating a new copy rather than mutating in place. `found == saved` relies on `data class`'s auto-generated structural `equals()`, comparing field values rather than object identity.

### Level 2 — Intermediate

Query-derivation-style method naming (mirroring Spring Data's `findBy...` convention) and a collection-returning `suspend fun`, plus the `findByIdOrNull`-style Kotlin extension pattern for bridging a Java `Optional`-returning API.

```kotlin
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import java.util.Optional

data class Product(val id: Long? = null, val name: String, val category: String, val price: Double)

interface ProductRepository {
    suspend fun findAll(): List<Product>
    suspend fun findByCategory(category: String): List<Product> // mirrors Spring Data's derived-query naming
    fun findByIdBlockingJavaStyle(id: Long): Optional<Product>   // simulates an older, blocking, Optional-based API
}

class InMemoryProductRepository(seed: List<Product>) : ProductRepository {
    private val storage = seed.associateBy { it.id!! }

    override suspend fun findAll(): List<Product> {
        delay(5)
        return storage.values.toList()
    }

    override suspend fun findByCategory(category: String): List<Product> {
        delay(5)
        return storage.values.filter { it.category == category }
    }

    override fun findByIdBlockingJavaStyle(id: Long): Optional<Product> =
        Optional.ofNullable(storage[id])
}

// A Kotlin extension bridging a Java Optional-returning method into Kotlin's native nullable style --
// the same pattern Spring Data's own findByIdOrNull extension (on CrudRepository) follows.
fun ProductRepository.findByIdOrNull(id: Long): Product? =
    findByIdBlockingJavaStyle(id).orElse(null)

fun main() = runBlocking {
    val repository: ProductRepository = InMemoryProductRepository(listOf(
            Product(1, "Laptop", "Electronics", 999.99),
            Product(2, "Desk", "Furniture", 249.99),
            Product(3, "Mouse", "Electronics", 19.99)
    ))

    val electronics = repository.findByCategory("Electronics")
    println("Electronics: ${electronics.map { it.name }}")
    check(electronics.size == 2)

    val viaExtension = repository.findByIdOrNull(2)
    println("Found via findByIdOrNull extension: $viaExtension")
    check(viaExtension?.name == "Desk")

    val missingViaExtension = repository.findByIdOrNull(999)
    println("Missing via findByIdOrNull extension: $missingViaExtension")
    check(missingViaExtension == null)

    println("Derived-style query method + Optional-bridging extension -- PASS")
}
```

How to run: same dependencies as Level 1, then compile and run identically.

`findByCategory(category: String): List<Product>` mirrors Spring Data's derived-query method naming convention (`findByCategory` would generate a `WHERE category = ?` query automatically in a real Spring Data repository) — here implemented by hand for the in-memory version, but the *interface shape* is exactly what a real `CoroutineCrudRepository` subinterface would declare. `findByIdOrNull` is a hand-written extension following the same bridging pattern Spring Data itself provides via `org.springframework.data.repository.findByIdOrNull` for `CrudRepository`, converting a Java `Optional<T>`-returning method into Kotlin's more idiomatic `T?` at the call site.

### Level 3 — Advanced

A more complete, realistic repository interface with a custom query-like method, combined with a coroutine-based service layer doing validation and computing an aggregate — demonstrating how Kotlin/Spring Data idioms compose into a small but representative piece of business logic.

```kotlin
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking

data class Product(val id: Long? = null, val name: String, val category: String, val price: Double)

class ProductValidationException(message: String) : RuntimeException(message)

interface ProductRepository {
    suspend fun findById(id: Long): Product?
    suspend fun findByCategory(category: String): List<Product>
    suspend fun save(product: Product): Product
}

class InMemoryProductRepository : ProductRepository {
    private val storage = mutableMapOf<Long, Product>()
    private var nextId = 1L

    override suspend fun findById(id: Long): Product? {
        delay(5)
        return storage[id]
    }

    override suspend fun findByCategory(category: String): List<Product> {
        delay(5)
        return storage.values.filter { it.category == category }
    }

    override suspend fun save(product: Product): Product {
        delay(5)
        val id = product.id ?: nextId++
        val saved = product.copy(id = id)
        storage[id] = saved
        return saved
    }
}

class ProductService(private val repository: ProductRepository) {
    suspend fun createProduct(name: String, category: String, price: Double): Product {
        if (price <= 0) throw ProductValidationException("Price must be positive, was $price")
        if (name.isBlank()) throw ProductValidationException("Name must not be blank")
        return repository.save(Product(name = name, category = category, price = price))
    }

    suspend fun averagePriceInCategory(category: String): Double? {
        val products = repository.findByCategory(category)
        return if (products.isEmpty()) null else products.map { it.price }.average()
    }

    suspend fun applyDiscount(productId: Long, rate: Double): Product {
        val product = repository.findById(productId)
                ?: throw NoSuchElementException("Product $productId not found")
        val discounted = product.copy(price = product.price * (1 - rate))
        return repository.save(discounted)
    }
}

fun main() = runBlocking {
    val service = ProductService(InMemoryProductRepository())

    val laptop = service.createProduct("Laptop", "Electronics", 999.99)
    val mouse = service.createProduct("Mouse", "Electronics", 19.99)
    println("Created: $laptop, $mouse")

    val avgPrice = service.averagePriceInCategory("Electronics")
    println("Average Electronics price: $avgPrice")
    check(avgPrice != null && Math.abs(avgPrice - 509.99) < 0.01)

    val discounted = service.applyDiscount(laptop.id!!, 0.1)
    println("Discounted laptop: $discounted")
    check(Math.abs(discounted.price - 899.991) < 0.01)

    val emptyCategoryAvg = service.averagePriceInCategory("Nonexistent")
    println("Average for empty category: $emptyCategoryAvg")
    check(emptyCategoryAvg == null)

    try {
        service.createProduct("", "Electronics", 10.0)
        error("Expected validation failure for blank name")
    } catch (e: ProductValidationException) {
        println("Correctly rejected: ${e.message}")
    }

    println("Kotlin + Spring-Data-style repository, validation, and aggregate logic -- PASS")
}
```

How to run: same dependencies as Level 1, then compile and run identically.

`averagePriceInCategory` returning `Double?` (rather than throwing or returning `0.0`) correctly models that "average of an empty list" is genuinely undefined, not zero — Kotlin's null-safety makes this an explicit, compiler-checked part of the function's contract rather than an implicit convention callers have to remember. `applyDiscount` combines a nullable repository lookup (with an Elvis-operator-style early throw via `?:`) and `data class.copy()` for the immutable "update" pattern, tying together several of this card's Kotlin/Spring-Data idioms in one realistic method.

## 6. Walkthrough

Trace `service.applyDiscount(laptop.id!!, 0.1)`:

1. **Repository lookup.** `repository.findById(productId)` is a `suspend fun` call; it suspends for ~5ms (simulated I/O), then returns the stored `Product` for `laptop.id` — a `data class` instance with `price = 999.99`.
2. **Null check via Elvis operator.** `?: throw NoSuchElementException(...)` would only execute if `findById` returned `null` — since the laptop genuinely exists, this branch is skipped, and `product` is bound to the found, non-null `Product`.
3. **Immutable update via `copy()`.** `product.copy(price = product.price * (1 - rate))` computes `999.99 * (1 - 0.1) = 899.991` and creates a *new* `Product` instance with that updated price, leaving every other field (`id`, `name`, `category`) unchanged and the original `product` instance itself untouched — `data class` instances are conventionally never mutated in place.
4. **Persist the update.** `repository.save(discounted)` is called with this new instance; inside `InMemoryProductRepository.save`, since `discounted.id` is already non-null (it was copied from the original, already-persisted product), `product.id ?: nextId++` uses the existing id rather than generating a new one — the Elvis operator here serves double duty (both "generate on first save" and "preserve on update") depending on whether `id` is null or not.
5. **Storage updated.** `storage[id] = saved` overwrites the map entry for that id with the discounted product.
6. **Return.** The saved (discounted) `Product` is returned up through `applyDiscount` to `main`, where the assertion confirms the price reflects the 10% discount correctly.

```
applyDiscount(laptopId, 0.1)
   findById(laptopId) -> Product(price=999.99)   (suspend, ~5ms)
   null check: found, not null -> continue
   copy(price = 999.99 * 0.9) -> new Product(price=899.991), SAME id
   save(discounted) -> id already non-null -> reuse it -> storage updated
   return discounted Product
```

## 7. Gotchas & takeaways

> Gotcha: `data class` entities used directly with JPA (as opposed to R2DBC/MongoDB, which are more naturally suited to immutable data classes) can run into friction with JPA's requirement for a no-arg constructor and mutable, lazily-populated proxy fields for lazy-loaded associations — Kotlin's `kotlin-jpa` compiler plugin exists specifically to work around this by auto-generating the no-arg constructor JPA needs, but `data class` entities with JPA still sometimes need `var` properties (not `val`) for fields JPA needs to set reflectively after construction, which is a real trade-off against the "always immutable" ideal `data class` usually represents elsewhere in Kotlin code.

- `CoroutineCrudRepository` (and its reactive/coroutine-flavored siblings) let Spring Data repository methods be `suspend fun`s returning Kotlin-native nullable types (`T?`) instead of Java's `Optional<T>`, matching the null-safety idioms established elsewhere in this section.
- `data class` entities give concise, immutable-by-convention domain models with generated `equals`/`hashCode`/`copy` — `copy()` is the idiomatic way to produce an "updated" version of an entity without mutating the original.
- Extension functions like `findByIdOrNull` bridge older, Java-`Optional`-based Spring Data APIs into Kotlin's native nullable style, following the same reified/extension pattern covered in this section's dedicated extensions card.
- JPA specifically has some friction with pure `data class` entities (the no-arg constructor requirement, lazy-loading proxies) that R2DBC/MongoDB don't share as strongly — the `kotlin-jpa` compiler plugin and occasional `var` properties are the practical accommodations for JPA-backed Kotlin entities.
