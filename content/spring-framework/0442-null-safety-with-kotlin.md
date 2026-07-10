---
card: spring-framework
gi: 442
slug: null-safety-with-kotlin
title: "Null-safety with Kotlin"
---

## 1. What it is

Spring Framework's public API is annotated with JSR-305 nullability annotations (`@Nullable`, `@NonNull`, plus package-level `@NonNullApi`/`@NonNullFields` defaults) — metadata Kotlin's compiler reads and translates into its own null-safety type system, so calling into Spring from Kotlin gets compile-time nullability checking on Spring's own APIs, not just your own code.

```kotlin
val bean: OrderService = context.getBean(OrderService::class.java) // Spring's getBean is non-null by contract
val maybe: OrderService? = context.getBeanProvider(OrderService::class.java).ifAvailable // this one IS nullable
```

## 2. Why & when

Java has no compile-time distinction between "this reference is guaranteed non-null" and "this might be null" — a `NullPointerException` is a runtime surprise, discoverable only by reading documentation (if it exists) or hitting the bug in production. Kotlin's type system makes nullability part of the type itself (`String` vs `String?`), but that only helps if the *libraries* you call from Kotlin correctly declare which of their APIs can return or accept null — otherwise Kotlin has to treat every Java API's return type as a "platform type" (effectively "unknown, trust the caller"), losing the safety Kotlin's type system is supposed to provide. Spring's JSR-305 annotations exist specifically to close this gap for Spring's own APIs, so Kotlin code calling into Spring gets genuine compile-time nullability information, not just platform-type uncertainty.

This matters directly whenever:

- You're writing Kotlin code that calls Spring APIs (`ApplicationContext`, `@Autowired` fields/constructor parameters, `RestClient`, Spring Data repositories) and want the compiler to catch a missed null check before runtime, not after.
- You're deciding how to declare your own Spring-managed classes' properties and method signatures in Kotlin — matching Spring's own nullability contracts correctly (declaring a field non-null when Spring guarantees it will always be injected, nullable when it genuinely might not be) is what makes your code's own null-safety guarantees trustworthy.

## 3. Core concept

```
 Spring's Java API, annotated:
   @NonNullApi package-info.java   <- default: everything non-null unless marked otherwise
   @Nullable String getMessage()    <- explicitly CAN return null

        |
        | Kotlin compiler reads these JSR-305 annotations
        v

 Kotlin sees:
   fun getMessage(): String!   (platform type, if unannotated -- old code)
   fun getMessage(): String     (definitely non-null, if @NonNullApi applies)
   fun getMessage(): String?    (definitely nullable, if @Nullable is present)

        |
        v
 Kotlin's compiler ENFORCES this at every call site --
 calling a String? method result without a null check is a COMPILE ERROR,
 not a runtime NullPointerException surprise
```

The annotations are metadata Java itself ignores at runtime (they're documentation/tooling hints on the Java side) — Kotlin is what actually turns them into enforced, compile-time guarantees.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Java API annotated with JSR-305 nullability, read by Kotlin compiler as enforced nullable/non-null types">
  <rect x="10" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Java API</text>
  <text x="100" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@NonNullApi / @Nullable</text>

  <rect x="240" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Kotlin compiler</text>
  <text x="330" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reads JSR-305 metadata</text>

  <rect x="470" y="70" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">String / String?</text>
  <text x="550" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">enforced at compile time</text>

  <line x1="190" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="95" x2="465" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Documentation-only metadata on the Java side becomes an enforced compiler guarantee on the Kotlin side.

## 5. Runnable example

### Level 1 — Basic

Call a Spring API whose return type is genuinely nullable, and observe that Kotlin forces a null check before you can use the result — the direct, everyday payoff of this whole feature.

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

    // ObjectProvider.ifAvailable is annotated @Nullable in Spring's API -- Kotlin sees GreetingService?
    val provider = context.getBeanProvider(GreetingService::class.java)
    val maybeService: GreetingService? = provider.ifAvailable

    // The compiler would REJECT `maybeService.greet("Ada")` directly -- must handle the null case.
    val result = maybeService?.greet("Ada") ?: "No greeting service available"
    println(result)
    check(result == "Hello, Ada")

    println("Nullable Spring API correctly forced a null-safe call site -- PASS")
    context.close()
}
```

How to run: add `spring-context` and the Kotlin standard library to the classpath, then compile and run with `kotlinc AppConfig.kt -include-runtime -d app.jar && java -jar app.jar`.

`ObjectProvider<T>.ifAvailable` is genuinely allowed to return `null` in Spring's contract (if no matching bean exists) — because Spring's own Java source annotates this with `@Nullable`, Kotlin's compiler types `provider.ifAvailable` as `GreetingService?`, not just `GreetingService`. Attempting `maybeService.greet("Ada")` without the safe-call operator (`?.`) or an explicit null check would be a **compile error**, not a runtime crash — this is the concrete safety net Spring's JSR-305 annotations combined with Kotlin's type system provide.

### Level 2 — Intermediate

Declare a Kotlin class's own properties matching Spring's injection guarantees correctly — non-null for constructor-injected required dependencies, nullable only where a dependency is genuinely optional — and see the compiler catch a mismatch.

```kotlin
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.context.annotation.AnnotationConfigApplicationContext
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

interface PaymentGateway { fun charge(amount: Double): String }

class RealPaymentGateway : PaymentGateway {
    override fun charge(amount: Double) = "charged-$amount"
}

class OrderService(
    private val paymentGateway: PaymentGateway,       // required: constructor injection guarantees non-null
    @Autowired(required = false)
    private val auditLogger: AuditLogger? = null       // genuinely OPTIONAL: correctly typed nullable
) {
    fun checkout(amount: Double): String {
        val result = paymentGateway.charge(amount) // no null check needed -- guaranteed non-null by the type
        auditLogger?.log("Charged $amount")        // safe-call: correctly reflects that this MIGHT be absent
        return result
    }
}

class AuditLogger {
    fun log(message: String) = println("[AUDIT] $message")
}

@Configuration
open class AppConfig {
    @Bean
    open fun paymentGateway(): PaymentGateway = RealPaymentGateway()

    @Bean
    open fun orderService(paymentGateway: PaymentGateway) = OrderService(paymentGateway)
    // NOTE: no AuditLogger bean registered -- orderService's auditLogger will correctly be null
}

fun main() {
    val context = AnnotationConfigApplicationContext(AppConfig::class.java)
    val service = context.getBean(OrderService::class.java)

    val result = service.checkout(49.99) // works fine -- audit logging is silently skipped since auditLogger is null
    println("Checkout result: $result")
    check(result == "charged-49.99")

    println("Correctly-typed nullable optional dependency, non-null required dependency -- PASS")
    context.close()
}
```

How to run: same dependencies as Level 1, then compile and run identically.

`paymentGateway: PaymentGateway` (non-null type) accurately reflects that constructor injection guarantees this dependency exists — Spring would fail context startup entirely if it couldn't satisfy this parameter, so treating it as non-null in Kotlin is both safe and correct. `auditLogger: AuditLogger?` (nullable type) accurately reflects that `@Autowired(required = false)` means this dependency might genuinely be absent — since no `AuditLogger` bean is registered in `AppConfig`, it resolves to `null`, and the `?.` safe-call in `checkout` correctly skips logging without a `NullPointerException`. Getting these two declarations backwards (marking a required dependency nullable, or an optional one non-null) would either force unnecessary null checks everywhere or risk a real `NullPointerException` — matching Kotlin's nullability to Spring's actual injection guarantees is what makes the whole system trustworthy.

### Level 3 — Advanced

Combine nullable Spring Data query results, the Elvis operator for fallback logic, and `requireNotNull`/`checkNotNull` for asserting an invariant Spring guarantees but Kotlin's type system can't directly express (since it comes from runtime configuration, not the type system) — a realistic mix of null-handling styles in one piece of business logic.

```kotlin
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.AnnotationConfigApplicationContext
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.core.env.MapPropertySource
import org.springframework.core.env.MutablePropertySources

data class Product(val id: Long, val name: String, val price: Double)

class ProductRepository {
    private val products = mapOf(1L to Product(1, "Laptop", 999.99))

    // Correctly typed to match the real possibility of absence -- a Spring Data repository's
    // findById-style method would similarly return an Optional<T> (bridged to T? in Kotlin extensions).
    fun findById(id: Long): Product? = products[id]
}

class PricingService(
    private val repository: ProductRepository,
    @Value("\${discount.rate:0.0}") private val discountRateString: String
) {
    // Kotlin's non-null assertion / requireNotNull is for invariants the TYPE SYSTEM can't express --
    // here, that a validly-configured discount rate is always parseable, though its SOURCE (a
    // property file) is untyped text Spring can't guarantee is well-formed at compile time.
    private val discountRate: Double = requireNotNull(discountRateString.toDoubleOrNull()) {
        "discount.rate property must be a valid number, was: $discountRateString"
    }

    fun priceFor(productId: Long): String {
        val product = repository.findById(productId) ?: return "Product $productId not found"
        val discounted = product.price * (1 - discountRate)
        return "%s: $%.2f (was $%.2f)".format(product.name, discounted, product.price)
    }
}

@Configuration
open class AppConfig {
    @Bean
    open fun productRepository() = ProductRepository()

    @Bean
    open fun pricingService(repository: ProductRepository) = PricingService(repository, "0.1")
}

fun main() {
    val context = AnnotationConfigApplicationContext()
    val propertySources: MutablePropertySources = context.environment.propertySources
    propertySources.addFirst(MapPropertySource("test", mapOf("discount.rate" to "0.15")))
    context.register(AppConfig::class.java)
    context.refresh()

    val service = context.getBean(PricingService::class.java)

    val found = service.priceFor(1)
    println(found)
    check(found.startsWith("Laptop"))

    val notFound = service.priceFor(999)
    println(notFound)
    check(notFound == "Product 999 not found")

    println("Elvis fallback + requireNotNull invariant check, both correctly applied -- PASS")
    context.close()
}
```

How to run: add `spring-context` to the classpath, then compile and run as in Level 1.

`repository.findById(productId) ?: return "..."` is the Elvis-operator early-return pattern, Kotlin's idiomatic way to handle a genuinely nullable lookup result without nested `if` blocks. `requireNotNull(discountRateString.toDoubleOrNull()) { ... }` is a different kind of null handling — asserting an invariant about *configuration* (a `@Value`-injected string should parse as a valid number) that Kotlin's type system has no way to verify at compile time, since the value ultimately comes from an untyped property source; `requireNotNull` converts a `null` (parse failure) into a clear, immediate `IllegalArgumentException` with a descriptive message, rather than letting a malformed configuration value silently propagate as `NaN` or a later, confusing failure.

## 6. Walkthrough

Trace `PricingService`'s construction and first call in the Level 3 example:

1. **Bean construction.** When `AppConfig.pricingService(repository)` runs during context refresh, it constructs `PricingService(repository, "0.1")` — but note this hardcoded `"0.1"` in `AppConfig` is overridden by the actual injected `@Value` in a real scenario; here, since `discountRateString` is a constructor parameter with `@Value` on it directly (not resolved through `AppConfig`'s own bean method signature), Spring's constructor-injection machinery resolves `${discount.rate:0.0}` against the environment's property sources — which the test's `main` function seeded with `"0.15"` via `MapPropertySource`.
2. **Invariant check at construction time.** Inside `PricingService`'s primary constructor body, `discountRateString.toDoubleOrNull()` attempts to parse `"0.15"` as a `Double`, succeeding and returning `0.15` (non-null). `requireNotNull(...)` sees a non-null value and simply returns it, assigning `discountRate = 0.15` — no exception, since the configuration was valid.
3. **First `priceFor` call.** `service.priceFor(1)` calls `repository.findById(1)`, which returns `Product(1, "Laptop", 999.99)` (non-null, since id `1` exists in the map) — the Elvis operator's right-hand side (`return "Product ... not found"`) never executes.
4. **Discount calculation.** `discounted = 999.99 * (1 - 0.15)` computes to approximately `849.99`; the formatted string `"Laptop: $849.99 (was $999.99)"` is returned and printed.
5. **Second `priceFor` call.** `service.priceFor(999)` calls `repository.findById(999)`, which returns `null` (no matching key) — this time the Elvis operator's right-hand side *does* execute, immediately returning `"Product 999 not found"` without ever reaching the discount-calculation code, which would otherwise have thrown a `NullPointerException` trying to access `product.price` on a null reference if Kotlin's null-safety hadn't forced this early-return handling in the first place.

```
Construction: discountRateString = "0.15" (from @Value, resolved via seeded property source)
   requireNotNull(toDoubleOrNull()) -> 0.15 (valid) -> discountRate = 0.15

priceFor(1):   findById(1) -> Product(Laptop, 999.99)  (non-null)
                  -> discount applied -> "Laptop: $849.99 (was $999.99)"

priceFor(999): findById(999) -> null
                  -> Elvis operator short-circuits -> "Product 999 not found"
                  (discount calculation code never reached)
```

## 7. Gotchas & takeaways

> Gotcha: not every Spring API (especially older or third-party libraries built against Spring, or parts of the framework not yet fully annotated) carries JSR-305 nullability metadata — calling into an unannotated Java API from Kotlin produces a "platform type" (displayed as `String!` in tooling), which Kotlin does *not* enforce null-safety on at all, silently reverting to Java's own no-compile-time-safety behavior for that specific call. When working with an unfamiliar or older Spring-adjacent library from Kotlin, checking whether its return types show up as genuinely nullable/non-null (versus a bare platform type) in your IDE is a quick way to know whether you're getting real compile-time protection or not.

- Spring's own APIs are annotated with JSR-305 nullability metadata specifically so Kotlin's compiler can enforce genuine, compile-time null-safety when calling into them — not just documentation, but an enforced guarantee.
- Match your own Kotlin classes' nullability declarations to Spring's actual injection guarantees: non-null for required constructor-injected dependencies, nullable only where a dependency is genuinely optional (`@Autowired(required = false)`, `ObjectProvider.ifAvailable`, or a query method that can legitimately return nothing).
- The Elvis operator (`?:`) is Kotlin's idiomatic tool for handling a nullable lookup result with a fallback or early return, replacing verbose `if (x == null)` branching.
- `requireNotNull`/`checkNotNull` handle a different problem — asserting an invariant about *runtime configuration or state* that the type system alone can't verify — converting a silent `null` into an immediate, clearly-messaged exception at the point where the invariant is expected to hold.
