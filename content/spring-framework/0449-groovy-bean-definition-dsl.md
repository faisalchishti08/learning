---
card: spring-framework
gi: 449
slug: groovy-bean-definition-dsl
title: "Groovy bean definition DSL"
---

## 1. What it is

Spring's Groovy Bean Definition DSL (`GroovyBeanDefinitionReader`) lets you declare Spring beans using a compact, closure-based Groovy syntax — predating and conceptually similar to the Kotlin `beans { }` DSL covered earlier in this section, but for Groovy, and older (part of Spring since the Groovy-integration era of the framework). A `.groovy` configuration file reads almost like a simplified property file, with bean names as method-call-looking entries and their constructor arguments as parentheses.

```groovy
beans {
    greetingService(GreetingService)
    welcomeController(WelcomeController, ref('greetingService'))
}
```

## 2. Why & when

Before Java had lambdas (pre-Java 8) and before Spring's Java-based `@Configuration` classes became the dominant style, XML was the primary way to configure a Spring application — verbose, but at least declarative. Groovy, with its concise closure syntax and Spring's own `GroovyBeanDefinitionReader`, offered a considerably less verbose alternative to XML for teams comfortable with Groovy, while still being fully declarative and readable. It predates most of the more modern Kotlin-based approaches covered elsewhere in this section, and remains relevant primarily for understanding or maintaining existing Groovy-configured Spring applications (including, historically, Grails applications, which used this exact mechanism for their own bean configuration).

Understanding the Groovy bean DSL matters when:

- You're maintaining an existing Spring or Grails application that uses `.groovy` configuration files, and need to read or extend that configuration.
- You're comparing configuration styles across the JVM ecosystem — the Groovy DSL, the Kotlin `beans { }` DSL, and XML configuration are all declarative alternatives to `@Configuration`/`@Bean`, and understanding one illuminates the shared underlying pattern across all three.
- You want the absolute minimum ceremony for a small, script-like Spring application — the Groovy DSL can be genuinely terser than any of the alternatives for very simple configurations.

## 3. Core concept

```
 beans {
     greetingService(GreetingService)                        <- no-arg constructor
     welcomeController(WelcomeController, ref('greetingService'))  <- constructor arg, by bean name
     xmlns aop: 'http://www.springframework.org/schema/aop'   <- can even mix in XML namespace support
 }
        |
        v
 GroovyBeanDefinitionReader parses this closure-based DSL
        |
        v
 registers BeanDefinitions against a GenericApplicationContext,
 conceptually identical to what @Bean methods or XML <bean> elements produce
        |
        v
 context.refresh()  -- ordinary Spring bean instantiation from here on
```

The DSL's bean-name-as-method-call syntax (`greetingService(GreetingService)`) is Groovy's dynamic method dispatch being used creatively — `GroovyBeanDefinitionReader` intercepts these "method calls" and translates them into bean registrations rather than them being real method invocations.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Groovy beans block parsed by GroovyBeanDefinitionReader into BeanDefinitions, same as any other configuration style">
  <rect x="10" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">beans { ... }</text>
  <text x="95" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Groovy closure DSL</text>

  <rect x="230" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GroovyBeanDefinitionReader</text>

  <rect x="480" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BeanDefinitions</text>
  <text x="555" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same as any style</text>

  <line x1="180" y1="45" x2="225" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="430" y1="45" x2="475" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Same destination (registered bean definitions) as every other configuration style, via Groovy's own concise syntax.

## 5. Runnable example

### Level 1 — Basic

A minimal Groovy DSL script registering two beans with a constructor dependency, loaded and refreshed programmatically.

```groovy
import org.springframework.context.support.GenericGroovyApplicationContext

class GreetingService {
    String greet(String name) { "Hello, ${name}" }
}

class WelcomeController {
    GreetingService greetingService
    WelcomeController(GreetingService greetingService) { this.greetingService = greetingService }
    String handle(String name) { greetingService.greet(name) }
}

def context = new GenericGroovyApplicationContext()
context.reader.beans {
    greetingService(GreetingService)
    welcomeController(WelcomeController, ref('greetingService'))
}
context.refresh()

def controller = context.getBean(WelcomeController)
def result = controller.handle('Ada')

println result
assert result == 'Hello, Ada'
println 'Groovy bean DSL registration and wiring -- PASS'

context.close()
```

How to run: add `spring-context` and Groovy (`org.codehaus.groovy:groovy`) to the classpath, then run directly with `groovy AppConfig.groovy` (the Groovy runtime compiles and executes it in one step, no separate compile phase needed).

`GenericGroovyApplicationContext` bundles a `GroovyBeanDefinitionReader` (accessible via `.reader`) specifically for consuming this DSL syntax. `greetingService(GreetingService)` registers a bean named `"greetingService"` of type `GreetingService`, constructed via its no-arg constructor. `welcomeController(WelcomeController, ref('greetingService'))` registers `"welcomeController"`, passing `ref('greetingService')` — a reference to the bean registered just above — as the constructor argument, resolved by bean name.

### Level 2 — Intermediate

Named property setting (Groovy DSL's equivalent of setter injection) and a nested closure for configuring bean properties after construction, contrasted with the pure-constructor style from Level 1.

```groovy
import org.springframework.context.support.GenericGroovyApplicationContext

class RetryPolicy {
    int maxAttempts = 3
    long delayMillis = 100
}

class OrderService {
    RetryPolicy retryPolicy
    String describe() { "Order service with maxAttempts=${retryPolicy.maxAttempts}, delay=${retryPolicy.delayMillis}ms" }
}

def context = new GenericGroovyApplicationContext()
context.reader.beans {
    // Property-based configuration via a nested closure -- Groovy DSL's setter-injection equivalent.
    retryPolicy(RetryPolicy) {
        maxAttempts = 5
        delayMillis = 200
    }
    orderService(OrderService) {
        retryPolicy = ref('retryPolicy') // setter injection, referencing the bean above
    }
}
context.refresh()

def orderService = context.getBean(OrderService)
def result = orderService.describe()

println result
assert result == 'Order service with maxAttempts=5, delay=200ms'
println 'Property-based (setter injection) Groovy DSL configuration -- PASS'

context.close()
```

How to run: same dependencies as Level 1, then `groovy AppConfig.groovy`.

The closure passed to `retryPolicy(RetryPolicy) { ... }` sets properties on the bean *after* construction — `maxAttempts = 5` and `delayMillis = 200` are Groovy property assignments, translated by the DSL into calls to the corresponding JavaBean-style setter methods (`setMaxAttempts(5)`, `setDelayMillis(200)`) on the constructed `RetryPolicy` instance. `orderService(OrderService) { retryPolicy = ref('retryPolicy') }` similarly uses setter injection (via the `retryPolicy` property setter) rather than constructor injection, showing the DSL supports both wiring styles depending on which is more natural for a given bean.

### Level 3 — Advanced

Profile-conditional registration and importing another Groovy configuration file — showing the DSL scales to slightly more realistic, multi-concern configuration, mirroring the `profile { }` block from the Kotlin `beans { }` DSL card.

```groovy
import org.springframework.context.support.GenericGroovyApplicationContext

interface PaymentGateway { String charge(double amount) }

class RealPaymentGateway implements PaymentGateway {
    String charge(double amount) { "real-charge-${amount}" }
}

class FakePaymentGateway implements PaymentGateway {
    String charge(double amount) { "fake-charge-${amount}" }
}

class OrderService {
    PaymentGateway paymentGateway
    OrderService(PaymentGateway paymentGateway) { this.paymentGateway = paymentGateway }
    String checkout(double amount) { paymentGateway.charge(amount) }
}

def context = new GenericGroovyApplicationContext()
context.environment.setActiveProfiles('dev') // NOT 'prod' -- expect the fake gateway

context.reader.beans {
    profile('prod') {
        realPaymentGateway(RealPaymentGateway)
    }
    profile('!prod') {
        fakePaymentGateway(FakePaymentGateway)
    }
}

context.refresh()

// Manually resolve whichever gateway bean actually got registered, since the bean NAME
// differs between profiles -- a realistic pattern when profile-gated beans aren't uniformly named.
def gatewayBeanNames = context.getBeanNamesForType(PaymentGateway)
assert gatewayBeanNames.length == 1 : "Expected exactly one PaymentGateway bean under the active profile"

def gateway = context.getBean(gatewayBeanNames[0], PaymentGateway)
def orderService = new OrderService(gateway)
def result = orderService.checkout(49.99)

println "Active profile resolved to: ${gatewayBeanNames[0]}"
println result
assert result == 'fake-charge-49.99'
println 'Profile-conditional Groovy DSL registration -- PASS'

context.close()
```

How to run: same dependencies as Level 1, then `groovy AppConfig.groovy`.

`context.environment.setActiveProfiles('dev')` is set *before* `context.refresh()`, so when the DSL's `profile('prod') { ... }`/`profile('!prod') { ... }` blocks are evaluated during refresh, only the `!prod`-gated block's contents (`fakePaymentGateway`) actually get registered — `realPaymentGateway` never becomes a real bean, exactly mirroring `@Profile` and the Kotlin DSL's own `profile { }` block behavior. Since the two profile branches register beans under *different* names (`realPaymentGateway` vs. `fakePaymentGateway`), the example resolves the actual registered bean by type lookup (`getBeanNamesForType`) rather than assuming a fixed bean name — a realistic pattern when profile variants aren't given a uniform name.

## 6. Walkthrough

Trace `context.refresh()` in the Level 3 example:

1. **Profile set before refresh.** `context.environment.setActiveProfiles('dev')` configures the environment's active profile set *before* any bean definitions are processed — this ordering matters, since profile matching happens during bean-definition registration/refresh, not retroactively.
2. **DSL block evaluated.** `context.reader.beans { ... }` was already called earlier (registering the described bean definitions, including the profile-gated blocks), but the actual profile-matching decision — which of `profile('prod') { ... }` or `profile('!prod') { ... }` actually contributes its bean definitions — is resolved as part of this registration process, consulting the already-set active profiles from step 1.
3. **Profile matching.** `profile('prod')` checks whether `'prod'` is among the active profiles (`['dev']`) — it isn't, so `realPaymentGateway`'s bean definition is never registered. `profile('!prod')` checks the negation — `'prod'` is indeed *not* active — so `fakePaymentGateway`'s bean definition *is* registered.
4. **Refresh instantiates.** `context.refresh()` (called after the DSL block, in the actual code) instantiates every *registered* bean definition — only `FakePaymentGateway` gets constructed; `RealPaymentGateway` was never registered at all, so it's never touched.
5. **Type-based lookup.** `context.getBeanNamesForType(PaymentGateway)` searches the context for every bean whose type matches `PaymentGateway` — since only `fakePaymentGateway` was ever registered, this returns an array containing exactly that one bean name, confirmed by the `assert gatewayBeanNames.length == 1` check.
6. **Manual wiring and use.** `context.getBean(gatewayBeanNames[0], PaymentGateway)` retrieves the actual `FakePaymentGateway` instance; `new OrderService(gateway)` wires it manually (this example doesn't register `OrderService` itself as a Spring bean, to keep the profile-resolution logic visible in `main`-equivalent code rather than hidden inside another DSL closure); `orderService.checkout(49.99)` calls through to `FakePaymentGateway.charge(49.99)`, returning `"fake-charge-49.99"`.

```
setActiveProfiles('dev')  -- BEFORE refresh

beans { } DSL block:
   profile('prod')  { realPaymentGateway(...) }   -- 'prod' NOT active -> NOT registered
   profile('!prod')  { fakePaymentGateway(...) }   -- 'prod' NOT active, so !prod holds -> registered

context.refresh() -> only FakePaymentGateway instantiated

getBeanNamesForType(PaymentGateway) -> ["fakePaymentGateway"]
getBean("fakePaymentGateway", PaymentGateway).charge(49.99) -> "fake-charge-49.99"
```

## 7. Gotchas & takeaways

> Gotcha: the Groovy DSL's bean-name-as-method-call syntax (`greetingService(GreetingService)`) relies on Groovy's dynamic `methodMissing`-style dispatch inside the `beans { }` closure — this means a typo in a bean name, or accidentally calling what looks like a bean registration outside of a `beans { }` block, doesn't fail with a clear compile error the way a genuine Java/Kotlin method-call typo would; Groovy's dynamism, which is exactly what makes the terse DSL syntax possible, also means certain classes of configuration mistakes surface only at runtime rather than at compile time.

- The Groovy bean DSL predates and closely parallels the more modern Kotlin `beans { }` DSL — both are closure/lambda-based, declarative alternatives to `@Configuration`/`@Bean` or XML, ultimately producing the same kind of `BeanDefinition` registrations underneath.
- It's most relevant today for reading and maintaining existing Groovy-configured Spring or Grails applications, rather than as a first choice for new projects, where the Kotlin DSL or `@Configuration` classes are more commonly used.
- The DSL supports both constructor-argument-style registration (`bean(Type, arg1, arg2)`) and property/setter-style configuration (via a nested closure), matching whichever wiring style a given bean naturally uses.
- `profile('name') { ... }` blocks nest inside `beans { }` exactly like the Kotlin DSL's own profile blocks, letting profile-conditional bean registration be expressed inline rather than through separate profile-annotated configuration units.
