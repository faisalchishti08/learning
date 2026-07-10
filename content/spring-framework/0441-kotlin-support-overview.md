---
card: spring-framework
gi: 441
slug: kotlin-support-overview
title: "Kotlin support overview"
---

## 1. What it is

Spring Framework has first-class Kotlin support, not just "Kotlin happens to run on the JVM so it works" — the framework's own code includes Kotlin-specific extension functions, a Kotlin-idiomatic DSL for bean configuration, automatic null-safety enforcement at the framework boundary, and native support for Kotlin coroutines alongside its existing reactive support. This card is the map of what that support consists of; the following cards in this section each go deeper on one piece.

```kotlin
val context = AnnotationConfigApplicationContext()
context.register(AppConfig::class.java)  // ::class.java bridges Kotlin's reflection to Java's
context.refresh()

val service = context.getBean<OrderService>()  // Kotlin extension: no .java needed, reified generic
```

## 2. Why & when

A framework designed purely around Java's type system and idioms can still be *called* from Kotlin, but it won't feel natural — every generic type needs an explicit `::class.java`, nullability isn't understood or enforced at the API boundary, and Kotlin's more concise syntax (trailing lambdas, extension functions, `data class`) has no dedicated support. Spring's Kotlin support exists to close that gap deliberately: rather than leaving Kotlin developers to work around Java-shaped APIs, the framework provides Kotlin-specific entry points that feel like they were designed for Kotlin from the start.

This support matters when:

- You're building a Spring application in Kotlin (a large and growing share of new Spring projects, especially in the WebFlux/reactive space) and want to use Spring's APIs the way a Kotlin developer would expect, not just the way a Java developer would.
- You're deciding whether to use Kotlin for a new Spring project — knowing the framework has genuine first-class support (not an afterthought) is a real factor in that decision.
- You're reading or maintaining an existing Kotlin-based Spring codebase and need to understand Kotlin-specific patterns (the `beans { }` DSL, `getBean<T>()`, coroutine-returning controller methods) that don't exist in Java-based Spring code.

## 3. Core concept

```
 Spring's Kotlin support, by area (each is its own card in this section):
   1. Null-safety         -- Spring APIs annotated so Kotlin's compiler enforces nullability
   2. Extensions            -- getBean<T>(), and other reified-generic conveniences
   3. Bean DSL               -- beans { } -- a Kotlin-idiomatic alternative to @Configuration classes
   4. Functional registration -- registering beans imperatively, without component scanning
   5. Router DSL              -- a Kotlin DSL for WebFlux/MVC functional routing
   6. Coroutines              -- suspend fun controller methods, Flow as a Kotlin-native reactive type
   7. Spring Data + Kotlin    -- repository interfaces using Kotlin idioms (data classes, nullability)
```

Each of these is additive on top of Spring's existing Java-based APIs — nothing about Kotlin support requires abandoning `@Configuration`, `@Bean`, or any other familiar Spring mechanism; it's a parallel, Kotlin-idiomatic way to express the same underlying concepts.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring's Kotlin support spans null-safety, extensions, DSLs, and coroutines, all layered on the same core framework">
  <rect x="220" y="15" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="39" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Core Spring Framework</text>

  <rect x="20" y="90" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Null-safety</text>

  <rect x="180" y="90" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="250" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Extensions / DSLs</text>

  <rect x="340" y="90" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="410" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Coroutines</text>

  <rect x="500" y="90" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="560" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Data</text>

  <line x1="320" y1="55" x2="90" y2="85" stroke="#8b949e" stroke-width="1"/>
  <line x1="320" y1="55" x2="250" y2="85" stroke="#8b949e" stroke-width="1"/>
  <line x1="320" y1="55" x2="410" y2="85" stroke="#8b949e" stroke-width="1"/>
  <line x1="320" y1="55" x2="560" y2="85" stroke="#8b949e" stroke-width="1"/>
</svg>

Each area of Kotlin support is a layer added on top of the same underlying framework, not a separate framework.

## 5. Runnable example

### Level 1 — Basic

Bootstrap a Spring context and retrieve a bean using plain Java-style interop first, to show the baseline before Kotlin-specific conveniences are introduced.

```kotlin
import org.springframework.context.annotation.AnnotationConfigApplicationContext
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

class GreetingService {
    fun greet(name: String) = "Hello, $name"
}

@Configuration
open class AppConfig {
    @Bean
    open fun greetingService() = GreetingService()
}

fun main() {
    val context = AnnotationConfigApplicationContext(AppConfig::class.java)

    // Java-interop style: explicit .java class reference, no Kotlin-specific convenience yet.
    val service = context.getBean(GreetingService::class.java)
    println(service.greet("Ada"))

    context.close()
}
```

How to run: add `spring-context` and the Kotlin standard library to the classpath, then compile and run with `kotlinc AppConfig.kt -include-runtime -d app.jar && java -jar app.jar` (or run directly via `kotlinc -script` / an IDE's Kotlin run configuration). Note `open class`/`open fun` — Kotlin classes and methods are `final` by default, but Spring's CGLIB-based proxying (for `@Configuration` classes) needs them to be overridable, so Spring's Kotlin support documentation specifically calls out `open` as necessary here (or using the `kotlin-spring` compiler plugin, which adds `open` automatically to Spring-annotated classes).

`GreetingService::class.java` is Kotlin's way of getting a `java.lang.Class` reference from a Kotlin class — necessary because `getBean(Class<T>)` is a Java-shaped API expecting a Java `Class` object, not Kotlin's own `KClass` reflection type.

### Level 2 — Intermediate

Use the Kotlin-specific `getBean<T>()` extension (covered in depth in the next card) alongside a `data class` for bean configuration, showing Kotlin idioms starting to replace the Java-interop boilerplate from Level 1.

```kotlin
import org.springframework.context.annotation.AnnotationConfigApplicationContext
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.beans.factory.getBean

data class Product(val id: Long, val name: String, val price: Double)

class ProductService {
    fun findById(id: Long): Product? =
        if (id == 1L) Product(1, "Laptop", 999.99) else null
}

@Configuration
open class AppConfig {
    @Bean
    open fun productService() = ProductService()
}

fun main() {
    val context = AnnotationConfigApplicationContext(AppConfig::class.java)

    // Kotlin extension: reified generic, no ::class.java needed at all.
    val service = context.getBean<ProductService>()

    val found = service.findById(1)
    println("Found: $found")
    check(found?.name == "Laptop") { "Expected to find Laptop" }

    val notFound = service.findById(999)
    println("Not found result: $notFound")
    check(notFound == null) { "Expected null for a missing product" }

    println("Kotlin extension + data class + nullable return type -- PASS")
    context.close()
}
```

How to run: add `spring-context` to the classpath, then compile/run as in Level 1.

`context.getBean<ProductService>()` uses Spring's Kotlin extension function (defined in `spring-context`'s Kotlin support) with a *reified* generic type parameter — the JVM normally erases generic type information at runtime, but Kotlin's `inline`/`reified` combination (which this extension uses internally) preserves it, letting `getBean<T>()` work without any `Class` argument at all. `Product` as a `data class` gets `equals`/`hashCode`/`toString`/`copy` generated automatically, and `findById`'s `Product?` return type makes the possibility of "not found" part of the function's signature — directly foreshadowing the null-safety card next in this section.

### Level 3 — Advanced

Combine several areas of Kotlin support at once — the bean DSL (`beans { }`, covered fully in its own card), a coroutine-based service method (covered fully in the coroutines card), and Kotlin's null-safety — into one small but representative Kotlin-idiomatic Spring application, demonstrating how these pieces compose in practice rather than existing in isolation.

```kotlin
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import org.springframework.context.support.GenericApplicationContext
import org.springframework.context.support.beans

data class Order(val id: Long, val status: String)

class OrderRepository {
    private val orders = mapOf(1L to Order(1, "PENDING"), 2L to Order(2, "SHIPPED"))

    // A suspend function -- Kotlin's native async style, natively supported by Spring's Kotlin layer.
    suspend fun findById(id: Long): Order? {
        delay(10) // simulates a non-blocking I/O call (e.g. a reactive database driver)
        return orders[id]
    }
}

class OrderService(private val repository: OrderRepository) {
    suspend fun describeOrder(id: Long): String {
        val order = repository.findById(id) ?: return "Order $id not found"
        return "Order ${order.id} is ${order.status}"
    }
}

fun main() = runBlocking {
    // The Bean DSL: a Kotlin-idiomatic alternative to @Configuration + @Bean, using trailing lambdas.
    val beans = beans {
        bean<OrderRepository>()
        bean { OrderService(ref()) } // ref() resolves the OrderRepository bean by type
    }

    val context = GenericApplicationContext()
    beans.initialize(context)
    context.refresh()

    val service = context.getBean(OrderService::class.java)

    val result1 = service.describeOrder(1)
    println(result1)
    check(result1 == "Order 1 is PENDING")

    val result2 = service.describeOrder(999)
    println(result2)
    check(result2 == "Order 999 not found")

    println("Bean DSL + coroutines + null-safe repository lookup, composed together -- PASS")
    context.close()
}
```

How to run: add `spring-context`, `kotlinx-coroutines-core`, and the Kotlin standard library to the classpath, then compile and run as in Level 1.

This single example touches three of the areas the concept map lists: the `beans { }` DSL replaces `@Configuration`/`@Bean` entirely with a programmatic, lambda-based registration style; `OrderRepository.findById` and `OrderService.describeOrder` are `suspend` functions, Kotlin's native asynchronous style, which Spring's coroutine support (its own card later in this section) can invoke directly from a controller without manual `Mono`/`Flux` wrapping; and the `Order?` nullable return type, combined with the Elvis operator (`?:`) for the not-found case, is Kotlin's null-safety model applied directly to business logic, foreshadowing the null-safety card immediately following this one.

## 6. Walkthrough

Trace `main()` in the Level 3 example:

1. **Bean DSL evaluation.** `beans { bean<OrderRepository>(); bean { OrderService(ref()) } }` builds a `BeanDefinitionDsl` describing two bean registrations — this is pure description at this point, no instantiation yet, similar in spirit to how a `@Configuration` class's `@Bean` methods aren't invoked until the context actually needs them.
2. **Context initialization.** `beans.initialize(context)` applies those descriptions to a `GenericApplicationContext`, registering the corresponding `BeanDefinition`s; `context.refresh()` then actually instantiates the singleton beans — `OrderRepository()` first (no dependencies), then `OrderService(ref())`, where `ref()` resolves to the already-created `OrderRepository` instance by type.
3. **Bean retrieval.** `context.getBean(OrderService::class.java)` fetches the constructed `OrderService`.
4. **First coroutine call.** `service.describeOrder(1)` is a `suspend` function call; `runBlocking { }` (wrapping the entire `main` body) provides the coroutine context needed to actually run and await it. Inside, `repository.findById(1)` suspends for 10ms (simulating non-blocking I/O via `delay`), then returns `Order(1, "PENDING")`. Since this isn't null, the Elvis operator's right-hand side never executes, and the function returns `"Order 1 is PENDING"`.
5. **Second coroutine call.** `service.describeOrder(999)` follows the same suspend/resume flow, but `repository.findById(999)` returns `null` (no matching key in the map) — the Elvis operator (`?: return "Order $id not found"`) catches this and returns early with the not-found message, all expressed through Kotlin's null-safety syntax rather than a null check and conditional branch.
6. **Assertions.** Both results are checked against expected strings, confirming the DSL-registered beans, the coroutine-based repository call, and the null-safe not-found handling all worked correctly together.

```
beans { } DSL -> BeanDefinitionDsl (description only)
beans.initialize(context) + context.refresh() -> OrderRepository, OrderService instantiated

runBlocking {
    service.describeOrder(1)   -- suspend fun, delay(10ms), Order found -> "Order 1 is PENDING"
    service.describeOrder(999) -- suspend fun, delay(10ms), Order null  -> Elvis -> "Order 999 not found"
}
```

## 7. Gotchas & takeaways

> Gotcha: Kotlin classes and functions are `final` by default, but Spring's `@Configuration` class proxying (CGLIB-based, used to intercept `@Bean` method calls for singleton semantics) requires the class and its `@Bean` methods to be non-final — forgetting `open` on a Kotlin `@Configuration` class (as both Level 1 and Level 3 use) produces a runtime error about CGLIB being unable to proxy a final class. The `kotlin-spring` Gradle/Maven compiler plugin exists specifically to add `open` automatically to Spring-annotated classes, removing the need to remember this manually in most real projects.

- Spring's Kotlin support is genuinely first-class — null-safety enforcement, reified-generic extensions, dedicated DSLs, and native coroutine support, not just "it happens to compile."
- Every piece of Kotlin support is additive on top of the same core framework — nothing requires abandoning familiar Spring concepts like `@Configuration` or `@Bean`, though the `beans { }` DSL offers a Kotlin-idiomatic alternative.
- `open` on Kotlin `@Configuration` classes and their `@Bean` methods is necessary for CGLIB proxying to work — either add it manually or use the `kotlin-spring` compiler plugin to handle it automatically.
- The rest of this section goes deep on each area introduced here — null-safety, extensions, the bean and router DSLs, functional registration, coroutines, and Spring Data's Kotlin support — each building on the foundation this overview card establishes.
