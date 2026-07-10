---
card: spring-framework
gi: 444
slug: bean-definition-dsl-beans
title: "Bean definition DSL (beans { })"
---

## 1. What it is

The `beans { }` function is a Kotlin DSL (domain-specific language) for registering Spring beans programmatically, using Kotlin's trailing-lambda syntax to produce configuration that reads like a lightweight, declarative list of beans rather than a Java-shaped `@Configuration` class full of `@Bean`-annotated methods. It's built on `BeanDefinitionDsl`, and it compiles to ordinary `BeanDefinition` registrations underneath — functionally equivalent to `@Configuration`, just expressed differently.

```kotlin
val myBeans = beans {
    bean<GreetingService>()
    bean { OrderService(ref(), env.getProperty("app.name", "default")) }
    profile("prod") {
        bean<RealPaymentGateway>()
    }
}
```

## 2. Why & when

`@Configuration` classes work perfectly well from Kotlin (as the earlier cards in this section demonstrate), but they carry some Java-shaped ceremony that doesn't disappear just because the language changed — `open class`/`open fun` requirements for CGLIB proxying, and a class-and-annotation-based structure that doesn't take advantage of Kotlin's more expressive lambda and DSL capabilities. The `beans { }` DSL exists as an alternative specifically suited to Kotlin: no CGLIB proxying involved at all (so no `open` requirement), bean registration expressed as a sequence of function calls inside a lambda, and built-in support for profile-conditional registration and environment access as first-class DSL constructs rather than separate annotations.

Reach for the bean DSL when:

- You're writing a Kotlin-first Spring application and want configuration that avoids `@Configuration`'s CGLIB-proxying requirements (`open` classes/methods) entirely.
- You want profile-conditional or environment-dependent bean registration expressed inline, as part of the same declarative block, rather than scattered across separate `@Profile`-annotated classes.
- You're building a lightweight, functional-style application (common in Kotlin/WebFlux combinations, discussed further in the functional-bean-registration and router-DSL cards later in this section) where the whole application's wiring benefits from a similarly functional configuration style.

## 3. Core concept

```
 beans {
     bean<GreetingService>()                    <- registers a bean by type, using its primary constructor
     bean { OrderService(ref()) }                 <- registers via a lambda, ref() resolves a dependency by type
     profile("prod") {
         bean<RealPaymentGateway>()               <- only registered if "prod" profile is active
     }
 }
        |
        v
   returns a BeanDefinitionDsl (a description, not yet applied to any context)
        |
        v
   myBeans.initialize(context)   <- applies the described registrations to a GenericApplicationContext
        |
        v
   context.refresh()              <- actually instantiates singleton beans, same as any other context
```

`ref()` inside a `bean { }` lambda is itself a small DSL helper — it looks up another bean by type from the context being built, functioning like an inline `@Autowired` for constructor arguments expressed directly in the lambda.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="beans DSL block produces a description applied to a context, then refreshed like any other configuration style">
  <rect x="10" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">beans { ... }</text>
  <text x="95" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BeanDefinitionDsl</text>

  <rect x="240" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">.initialize(context)</text>

  <rect x="470" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">context.refresh()</text>

  <line x1="180" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="45" x2="465" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Description, then application, then instantiation — the same three-step pattern any Spring context follows, expressed through a different syntax.

## 5. Runnable example

### Level 1 — Basic

A minimal `beans { }` block registering two beans with a dependency between them, using `ref()` to wire the constructor argument.

```kotlin
import org.springframework.context.support.GenericApplicationContext
import org.springframework.context.support.beans

class GreetingService {
    fun greet(name: String) = "Hello, $name"
}

class WelcomeController(private val greetingService: GreetingService) {
    fun handle(name: String) = greetingService.greet(name)
}

fun main() {
    val myBeans = beans {
        bean<GreetingService>()
        bean { WelcomeController(ref()) } // ref() resolves GreetingService by type
    }

    val context = GenericApplicationContext()
    myBeans.initialize(context)
    context.refresh()

    val controller = context.getBean(WelcomeController::class.java)
    val result = controller.handle("Ada")

    println(result)
    check(result == "Hello, Ada")
    println("Bean DSL registration and wiring -- PASS")

    context.close()
}
```

How to run: add `spring-context` and the Kotlin standard library to the classpath, then `kotlinc AppConfig.kt -include-runtime -d app.jar && java -jar app.jar`.

`bean<GreetingService>()` registers `GreetingService` using its primary (and only) constructor, with no dependencies to resolve. `bean { WelcomeController(ref()) }` registers `WelcomeController` via an explicit lambda constructing it directly, where `ref()` — a DSL-scoped function — looks up the already-registered `GreetingService` bean by type and passes it as the constructor argument. Neither class needs `open`, `@Component`, or any Spring annotation at all — the wiring is expressed entirely through the DSL block, not through annotations on the classes themselves.

### Level 2 — Intermediate

Profile-conditional bean registration inline within the DSL, and environment property access — both expressed as part of the same declarative block, contrasted with needing separate `@Profile`-annotated classes in the annotation-based style.

```kotlin
import org.springframework.context.support.GenericApplicationContext
import org.springframework.context.support.beans
import org.springframework.core.env.MapPropertySource
import org.springframework.core.env.MutablePropertySources

interface PaymentGateway { fun charge(amount: Double): String }

class RealPaymentGateway : PaymentGateway {
    override fun charge(amount: Double) = "real-charge-$amount"
}

class FakePaymentGateway : PaymentGateway {
    override fun charge(amount: Double) = "fake-charge-$amount"
}

class OrderService(private val gateway: PaymentGateway, private val appName: String) {
    fun checkout(amount: Double) = "[$appName] ${gateway.charge(amount)}"
}

fun main() {
    val myBeans = beans {
        profile("prod") {
            bean<RealPaymentGateway>()
        }
        profile("!prod") {
            bean<FakePaymentGateway>()
        }
        bean { OrderService(ref(), env.getProperty("app.name", "unnamed-app")) }
    }

    val context = GenericApplicationContext()
    val propertySources: MutablePropertySources = context.environment.propertySources
    propertySources.addFirst(MapPropertySource("test", mapOf("app.name" to "ShopApp")))
    context.environment.setActiveProfiles("dev") // NOT "prod" -- expect the fake gateway

    myBeans.initialize(context)
    context.refresh()

    val orderService = context.getBean(OrderService::class.java)
    val result = orderService.checkout(49.99)

    println(result)
    check(result == "[ShopApp] fake-charge-49.99")
    println("Profile-conditional bean DSL registration and env property access -- PASS")

    context.close()
}
```

How to run: same dependencies as Level 1, then compile and run identically.

`profile("prod") { bean<RealPaymentGateway>() }` and `profile("!prod") { bean<FakePaymentGateway>() }` mirror `@Profile("prod")`/`@Profile("!prod")` from the annotation-based style exactly, but expressed as nested blocks within the same `beans { }` call rather than as separate annotated classes — with `"dev"` active (not `"prod"`), only `FakePaymentGateway` gets registered. `env.getProperty("app.name", "unnamed-app")` accesses the `Environment` directly inside the `bean { }` lambda, resolving `"ShopApp"` from the seeded property source — the DSL gives direct, inline access to environment/profile concerns that would otherwise require separate `@Value`/`@Profile` annotations scattered across multiple classes.

### Level 3 — Advanced

Combine the bean DSL with conditional registration based on a computed condition (not just an active profile), a `ref()` lookup for multiple candidates disambiguated by name, and composing several `beans { }` blocks together — showing the DSL scales to more realistic, multi-concern configuration.

```kotlin
import org.springframework.context.support.GenericApplicationContext
import org.springframework.context.support.beans
import org.springframework.core.env.MapPropertySource

interface CacheProvider { fun describe(): String }

class InMemoryCacheProvider : CacheProvider { override fun describe() = "in-memory cache" }
class DistributedCacheProvider : CacheProvider { override fun describe() = "distributed cache" }

class ReportingService(private val cacheProvider: CacheProvider) {
    fun status() = "Reporting using: ${cacheProvider.describe()}"
}

// A separate beans{} block, focused specifically on infrastructure concerns --
// composable independently of the application-logic beans block below.
val infrastructureBeans = beans {
    bean("inMemory") { InMemoryCacheProvider() }
    bean("distributed") { DistributedCacheProvider() }
}

fun applicationBeans(useDistributedCache: Boolean) = beans {
    // A condition computed from ordinary Kotlin logic, not just a Spring profile name --
    // demonstrates the DSL isn't limited to profile-string matching for conditional registration.
    if (useDistributedCache) {
        bean { ReportingService(ref("distributed")) } // disambiguated by bean NAME, not just type
    } else {
        bean { ReportingService(ref("inMemory")) }
    }
}

fun main() {
    val context = GenericApplicationContext()

    infrastructureBeans.initialize(context)      // register infrastructure beans first
    applicationBeans(useDistributedCache = true).initialize(context) // then application logic, composed on top

    context.refresh()

    val reportingService = context.getBean(ReportingService::class.java)
    val status = reportingService.status()

    println(status)
    check(status == "Reporting using: distributed cache")
    println("Composed beans{} blocks with name-disambiguated ref() lookup -- PASS")

    context.close()
}
```

How to run: same dependencies as Level 1, then compile and run identically.

Two `CacheProvider` beans exist (`"inMemory"` and `"distributed"`), so `ref()` without a name would be ambiguous — `ref("distributed")` disambiguates by bean *name*, the DSL equivalent of `@Qualifier`. `infrastructureBeans` and `applicationBeans(...)` are two entirely separate `beans { }` results, each independently callable, composed together onto the *same* `context` via two separate `.initialize(context)` calls — demonstrating that DSL blocks can be organized into smaller, focused, independently reusable pieces (infrastructure vs. application logic, for instance) rather than one monolithic block, mirroring how a large application might split configuration across multiple `@Configuration` classes.

## 6. Walkthrough

Trace `main()` in the Level 3 example:

1. **Infrastructure beans applied first.** `infrastructureBeans.initialize(context)` registers `BeanDefinition`s for both `"inMemory"` (an `InMemoryCacheProvider`) and `"distributed"` (a `DistributedCacheProvider`), under those exact bean names — no instantiation yet, just registration.
2. **Application beans computed and applied.** `applicationBeans(useDistributedCache = true)` evaluates the Kotlin `if` at the time this function is called (ordinary Kotlin control flow, unrelated to Spring's own conditional mechanisms like `@Conditional`), producing a `beans { }` result containing exactly one registration: `bean { ReportingService(ref("distributed")) }`. Its own `.initialize(context)` call adds this registration to the *same* context object infrastructure beans were already added to.
3. **Context refresh.** `context.refresh()` now actually instantiates every registered bean: first `InMemoryCacheProvider` and `DistributedCacheProvider` (both, even though only one is actually used — the DSL's `if` only controlled which *`ReportingService` wiring*  to register, not which cache provider beans exist at all), then `ReportingService`, whose lambda calls `ref("distributed")` — resolving specifically the bean named `"distributed"`, not `"inMemory"`, disambiguating what would otherwise be an ambiguous type-only lookup.
4. **Retrieval and verification.** `context.getBean(ReportingService::class.java)` fetches the constructed instance; `.status()` calls `cacheProvider.describe()` on the `DistributedCacheProvider` it was wired to, returning `"distributed cache"`, confirming the name-disambiguated `ref()` lookup resolved to the correct bean.

```
infrastructureBeans.initialize(context)  -- registers "inMemory", "distributed" (both CacheProvider)
applicationBeans(useDistributedCache=true).initialize(context)
   -- Kotlin `if` evaluated NOW -> registers ReportingService(ref("distributed"))

context.refresh()
   -> InMemoryCacheProvider instantiated (registered, though unused by ReportingService)
   -> DistributedCacheProvider instantiated
   -> ReportingService -- ref("distributed") resolves BY NAME -> wired to DistributedCacheProvider

reportingService.status() -> "Reporting using: distributed cache"
```

## 7. Gotchas & takeaways

> Gotcha: `beans { }` blocks are evaluated when `.initialize(context)` runs, but the Kotlin code *inside* the block (like the `if (useDistributedCache)` in Level 3) runs at that point too, using whatever values were captured when the `beans { }` lambda was originally constructed — this means dynamic, environment-dependent conditional logic inside the DSL needs to genuinely read from `env`/`profile` (Spring-aware) rather than capturing plain Kotlin variables from an outer scope if you want the condition to reflect the *target context's* actual environment rather than whatever state happened to be available when the function producing the `beans { }` block was called.

- `beans { }` is a Kotlin-idiomatic alternative to `@Configuration`/`@Bean`, avoiding CGLIB-proxying requirements (no `open` needed) and expressing bean registration as a sequence of DSL function calls rather than annotated methods.
- `ref()` inside a `bean { }` lambda resolves a dependency by type (or by name, when disambiguation is needed via `ref("beanName")`), functioning as an inline equivalent of constructor `@Autowired`.
- `profile("name") { ... }` blocks nest directly inside `beans { }`, expressing profile-conditional registration inline rather than through separate `@Profile`-annotated classes.
- `beans { }` results are ordinary values that can be composed, split into smaller reusable pieces, and applied to a context via multiple `.initialize(context)` calls — useful for organizing configuration by concern (infrastructure vs. application logic) the same way multiple `@Configuration` classes would in the annotation-based style.
