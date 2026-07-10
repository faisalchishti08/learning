---
card: spring-framework
gi: 445
slug: functional-bean-registration
title: "Functional bean registration"
---

## 1. What it is

Functional bean registration is registering beans directly against a `GenericApplicationContext` via its `registerBean(...)` method (or, from Kotlin, the `beans { }` DSL covered in the previous card, which is itself built on this same mechanism) — imperative, programmatic bean definition with no component scanning, no annotation processing, and no CGLIB proxying involved at all. It's the lowest-level building block both `@Configuration`-class-based and Kotlin-DSL-based configuration ultimately compile down to.

```kotlin
val context = GenericApplicationContext()
context.registerBean(GreetingService::class.java)
context.registerBean(WelcomeController::class.java) { WelcomeController(context.getBean()) }
context.refresh()
```

## 2. Why & when

Component scanning and `@Configuration` classes are convenient, but they come with real runtime cost — the classpath scanning itself, and (for `@Configuration`) CGLIB proxy generation for every configuration class. Functional registration removes both: you tell the context exactly what beans exist and how to build them, with no scanning and no proxying, which matters specifically for startup-time-sensitive scenarios (serverless functions, GraalVM native images before AOT processing existed as thoroughly as it does today, or any context where every millisecond of startup counts).

Reach for functional bean registration when:

- Startup time is a hard constraint and avoiding classpath scanning/CGLIB proxying overhead genuinely matters — historically the primary motivation for Spring Cloud Function and similar fast-startup-focused projects.
- You're building the `beans { }` DSL's own kind of tooling, or otherwise need the lowest-level control over exactly which beans get registered and how, without any annotation-driven "magic" deciding it for you.
- You want to understand what `@Configuration`/`@Bean` and the Kotlin `beans { }` DSL are actually doing underneath — both ultimately call this same `registerBean`-style API.

## 3. Core concept

```
 GenericApplicationContext (empty, no configuration yet)
        |
        v
 context.registerBean(GreetingService::class.java)
        |
        | registers a BeanDefinition directly -- no scanning, no annotations processed
        v
 context.registerBean(WelcomeController::class.java) { supplier lambda }
        |
        | the supplier lambda has FULL control over construction --
        | can call context.getBean(...) to wire dependencies manually
        v
 context.refresh()
        |
        v
 beans instantiated, in registration order (respecting dependencies resolved via the supplier lambdas)
```

Every other configuration style in Spring — `@ComponentScan`, `@Configuration`/`@Bean`, XML configuration, the Kotlin `beans { }` DSL — is, underneath, a mechanism that eventually calls something functionally equivalent to `registerBean` against the context's underlying `BeanDefinitionRegistry`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple configuration styles all funnel down to the same underlying functional bean registration mechanism">
  <rect x="10" y="15" width="140" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="37" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@ComponentScan</text>

  <rect x="10" y="60" width="140" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Configuration/@Bean</text>

  <rect x="10" y="105" width="140" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">beans { } DSL</text>

  <rect x="350" y="55" width="260" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="77" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">registerBean(...)</text>
  <text x="480" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">functional bean registration</text>

  <line x1="150" y1="32" x2="345" y2="70" stroke="#8b949e" stroke-width="1"/>
  <line x1="150" y1="77" x2="345" y2="78" stroke="#8b949e" stroke-width="1"/>
  <line x1="150" y1="122" x2="345" y2="88" stroke="#8b949e" stroke-width="1"/>
</svg>

Every higher-level configuration style ultimately reduces to this same functional core.

## 5. Runnable example

### Level 1 — Basic

Register two beans directly against a `GenericApplicationContext`, with the second's supplier lambda manually resolving the first as a dependency — no scanning, no annotations.

```kotlin
import org.springframework.context.support.GenericApplicationContext

class GreetingService {
    fun greet(name: String) = "Hello, $name"
}

class WelcomeController(private val greetingService: GreetingService) {
    fun handle(name: String) = greetingService.greet(name)
}

fun main() {
    val context = GenericApplicationContext()

    context.registerBean(GreetingService::class.java)
    context.registerBean(WelcomeController::class.java) {
        WelcomeController(context.getBean(GreetingService::class.java))
    }

    context.refresh()

    val controller = context.getBean(WelcomeController::class.java)
    val result = controller.handle("Ada")

    println(result)
    check(result == "Hello, Ada")
    println("Functional bean registration, no scanning or annotations -- PASS")

    context.close()
}
```

How to run: add `spring-context` and the Kotlin standard library to the classpath, then `kotlinc AppConfig.kt -include-runtime -d app.jar && java -jar app.jar`.

`context.registerBean(GreetingService::class.java)` with no supplier lambda tells Spring to construct `GreetingService` via its default (no-argument) constructor — the simplest form. `context.registerBean(WelcomeController::class.java) { ... }` supplies an explicit lambda that Spring calls to actually construct the bean, inside which `context.getBean(GreetingService::class.java)` manually looks up the already-registered dependency — this is imperative, explicit wiring, in contrast to `@Autowired`'s declarative, reflection-driven approach.

### Level 2 — Intermediate

Register multiple beans of the same interface type with explicit names, and use conditional registration based on plain Kotlin logic — showing functional registration's flexibility for scenarios that would need `@Profile`/`@ConditionalOnProperty` in the annotation-based style.

```kotlin
import org.springframework.beans.factory.config.BeanDefinition
import org.springframework.context.support.GenericApplicationContext

interface Notifier { fun send(message: String): String }

class EmailNotifier : Notifier { override fun send(message: String) = "EMAIL: $message" }
class SmsNotifier : Notifier { override fun send(message: String) = "SMS: $message" }

class AlertService(private val notifiers: List<Notifier>) {
    fun broadcast(message: String): List<String> = notifiers.map { it.send(message) }
}

fun main() {
    val context = GenericApplicationContext()

    // Explicit bean NAMES, both implementing the same interface -- functional registration
    // makes multi-implementation registration straightforward without @Qualifier ceremony,
    // since AlertService below collects them all via a List<Notifier> constructor parameter.
    context.registerBean("emailNotifier", Notifier::class.java) { EmailNotifier() }
    context.registerBean("smsNotifier", Notifier::class.java) { SmsNotifier() }

    context.registerBean(AlertService::class.java) {
        // Manually collecting all registered Notifier beans -- functional registration gives
        // full imperative control over exactly how dependencies are gathered.
        val notifiers = context.getBeansOfType(Notifier::class.java).values.toList()
        AlertService(notifiers)
    }

    context.refresh()

    val alertService = context.getBean(AlertService::class.java)
    val results = alertService.broadcast("System maintenance at midnight")

    println(results)
    check(results.size == 2)
    check(results.any { it.startsWith("EMAIL:") })
    check(results.any { it.startsWith("SMS:") })
    println("Multi-implementation functional registration and manual collection -- PASS")

    context.close()
}
```

How to run: same dependencies as Level 1, then compile and run identically.

`registerBean("emailNotifier", Notifier::class.java) { EmailNotifier() }` registers under an explicit bean name with an explicit target type (`Notifier`, the interface, not `EmailNotifier`, the implementation) — useful when you want the bean registered as its interface type specifically. `context.getBeansOfType(Notifier::class.java).values.toList()` manually gathers every registered `Notifier` bean inside `AlertService`'s own supplier lambda — the functional equivalent of Spring's automatic `List<Notifier>` collection-injection behavior, but expressed explicitly rather than inferred from the constructor parameter type.

### Level 3 — Advanced

A function that conditionally registers different beans based on runtime configuration (simulating a fast-startup, serverless-style entry point), measuring and printing actual startup time to make the "no scanning, no proxying" performance argument concrete rather than just asserted.

```kotlin
import org.springframework.context.support.GenericApplicationContext
import kotlin.system.measureTimeMillis

interface DataStore { fun get(key: String): String? }

class InMemoryDataStore : DataStore {
    private val data = mapOf("greeting" to "Hello from in-memory store")
    override fun get(key: String) = data[key]
}

class ConfigService(private val dataStore: DataStore) {
    fun resolve(key: String): String = dataStore.get(key) ?: "not configured"
}

// Models a fast-startup entry point (the kind of scenario functional registration
// was originally designed for -- e.g., a serverless function's cold-start path).
fun buildFastStartupContext(): GenericApplicationContext {
    val context = GenericApplicationContext()

    context.registerBean(DataStore::class.java) { InMemoryDataStore() }
    context.registerBean(ConfigService::class.java) {
        ConfigService(context.getBean(DataStore::class.java))
    }

    context.refresh()
    return context
}

fun main() {
    var context: GenericApplicationContext? = null

    val elapsedMs = measureTimeMillis {
        context = buildFastStartupContext()
    }

    val configService = context!!.getBean(ConfigService::class.java)
    val result = configService.resolve("greeting")

    println("Startup took ${elapsedMs}ms (functional registration, no scanning/proxying)")
    println("Resolved value: $result")
    check(result == "Hello from in-memory store")

    println("Fast-startup-oriented functional registration pattern -- PASS")
    context!!.close()
}
```

How to run: same dependencies as Level 1, then compile and run identically.

`buildFastStartupContext()` builds and refreshes an entire, working `ApplicationContext` using only functional registration — no `@ComponentScan`, no `@Configuration` classes to CGLIB-proxy, no annotation processing to run. `measureTimeMillis { }` wraps this construction to print the actual elapsed time, making concrete (on a real, if small, example) the startup-speed argument this card's "why" section makes — in a real serverless/fast-startup scenario with many more beans, the gap between this approach and full component-scanning-based configuration becomes considerably more pronounced.

## 6. Walkthrough

Trace `buildFastStartupContext()`'s execution:

1. **Empty context created.** `GenericApplicationContext()` starts with zero registered beans and zero configuration — nothing has been scanned or processed yet, because nothing *will* be; every bean this context ever knows about will be registered explicitly by this function's own code.
2. **First registration.** `context.registerBean(DataStore::class.java) { InMemoryDataStore() }` adds a `BeanDefinition` describing "when asked for a `DataStore`, call this lambda to build one" — still no instantiation, just a registered description, exactly like `@Bean` methods aren't invoked until the context actually needs them.
3. **Second registration.** `context.registerBean(ConfigService::class.java) { ConfigService(context.getBean(DataStore::class.java)) }` similarly registers a description for `ConfigService`, whose supplier lambda — when eventually called — will look up the `DataStore` bean by type and pass it to `ConfigService`'s constructor.
4. **Refresh.** `context.refresh()` is the point where actual instantiation happens: it processes registered `BeanDefinition`s and, for singleton beans, calls their suppliers — first `InMemoryDataStore()`'s lambda runs (since nothing else depends on anything before it), then `ConfigService`'s lambda runs, which itself triggers the `context.getBean(DataStore::class.java)` call inside it, retrieving the already-instantiated `InMemoryDataStore` singleton.
5. **Return.** The fully-refreshed context is returned; `measureTimeMillis { }` in `main()` captures the total wall-clock time this entire sequence (steps 1–4) took.
6. **Usage.** `context.getBean(ConfigService::class.java).resolve("greeting")` calls into the constructed `ConfigService`, which delegates to its `DataStore` dependency, retrieving `"Hello from in-memory store"` from the map — confirming the whole functionally-registered, dependency-wired context works correctly end to end.

```
GenericApplicationContext() -- empty, no scanning
registerBean(DataStore) { InMemoryDataStore() }       -- description only
registerBean(ConfigService) { ConfigService(getBean(DataStore)) } -- description only

context.refresh()
   -> InMemoryDataStore() constructed (supplier called)
   -> ConfigService(...) constructed -- supplier calls getBean(DataStore) -> gets the instance above

configService.resolve("greeting") -> dataStore.get("greeting") -> "Hello from in-memory store"
```

## 7. Gotchas & takeaways

> Gotcha: functional registration's supplier lambdas resolve dependencies via explicit `context.getBean(...)` calls *inside* the lambda — this means the order beans are registered in doesn't strictly matter (Spring resolves dependencies lazily, when a supplier lambda actually runs during refresh), but a supplier lambda that captures and calls `context.getBean(...)` for a bean that was never registered at all fails at *refresh* time with a clear "no such bean" error, not at registration time — a subtle but real difference from `@Autowired`'s compile-adjacent (via `@Configuration` class structure) dependency wiring, worth keeping in mind when debugging a functionally-registered context that fails to start.

- Functional bean registration (`registerBean(...)` against a `GenericApplicationContext`) is the lowest-level bean-registration mechanism in Spring — every other configuration style (`@ComponentScan`, `@Configuration`/`@Bean`, the Kotlin `beans { }` DSL) ultimately reduces to something functionally equivalent.
- It avoids classpath scanning and CGLIB proxying entirely, which matters specifically for startup-time-sensitive scenarios like serverless functions or fast-cold-start deployments.
- Supplier lambdas give full imperative control over bean construction and dependency resolution — including patterns like collecting multiple same-type beans manually — at the cost of losing `@Autowired`'s declarative, less-boilerplate-heavy convenience.
- Understanding this mechanism demystifies what `@Configuration`/`@Bean` and the Kotlin `beans { }` DSL are actually doing underneath, since both are higher-level, more convenient facades over this same functional core.
