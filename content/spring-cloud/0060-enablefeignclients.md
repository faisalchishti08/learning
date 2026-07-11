---
card: spring-cloud
gi: 60
slug: enablefeignclients
title: "@EnableFeignClients"
---

## 1. What it is

`@EnableFeignClients`, placed on a configuration or application class, tells Spring to scan for interfaces annotated with `@FeignClient` and generate a working proxy bean for each one — without it, `@FeignClient` interfaces are just plain interfaces sitting unused, since nothing triggers Feign's proxy-generation and bean-registration machinery.

```java
@SpringBootApplication
@EnableFeignClients // scans the application's base package(s) for @FeignClient interfaces
public class OrdersServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrdersServiceApplication.class, args);
    }
}
```

```java
@EnableFeignClients(basePackages = "com.example.clients") // explicit package, for when clients live elsewhere
```

## 2. Why & when

Spring doesn't scan for and activate every annotation type by default — `@EnableFeignClients` is the explicit opt-in that turns on component scanning specifically for `@FeignClient` interfaces, the same pattern as other `@Enable*` annotations throughout Spring (`@EnableDiscoveryClient`, `@EnableEurekaServer`, `@EnableScheduling`). Without it, injecting a `@FeignClient`-annotated interface fails at startup with a `NoSuchBeanDefinitionException`, since no bean was ever created for it.

Reach for `@EnableFeignClients` (place it) when:

- Any `@FeignClient` interface exists anywhere in the application — it's a strict prerequisite, not optional configuration.
- The `@FeignClient` interfaces live outside the main application class's package (or its sub-packages), requiring the explicit `basePackages` or `clients` attribute to point scanning at the right location.
- Multiple Feign clients need shared default configuration (a common encoder, decoder, or interceptor, covered in a later card) — `@EnableFeignClients(defaultConfiguration = SharedFeignConfig.class)` applies it across every scanned client at once.

## 3. Core concept

```
 @SpringBootApplication
 @EnableFeignClients            <- activates scanning
 class OrdersServiceApplication { ... }

 scanning finds:
   @FeignClient(name = "billing-service") interface BillingClient { ... }
   @FeignClient(name = "promotions-service") interface PromotionsClient { ... }

 for EACH one found:
   Spring generates a proxy implementation
   registers it as a bean
   -> now injectable via @Autowired, just like any other Spring bean
```

`@EnableFeignClients` is the switch; the interfaces it discovers are what actually get turned into working clients.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EnableFeignClients triggers a scan of the base package that finds every FeignClient annotated interface and registers a generated proxy bean for each one" >
  <rect x="30" y="70" width="200" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@EnableFeignClients</text>

  <line x1="230" y1="90" x2="280" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a60)"/>
  <text x="255" y="80" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">scans</text>

  <rect x="285" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="360" y="41" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">BillingClient</text>

  <rect x="285" y="65" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="360" y="86" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">PromotionsClient</text>

  <rect x="285" y="110" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="360" y="131" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(not @FeignClient -- skipped)</text>

  <line x1="435" y1="37" x2="480" y2="37" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a60)"/>
  <line x1="435" y1="82" x2="480" y2="82" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a60)"/>

  <rect x="485" y="15" width="140" height="34" rx="6" fill="#1c2430" stroke="#e6edf3" stroke-width="1"/>
  <text x="555" y="36" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">registered bean</text>
  <rect x="485" y="60" width="140" height="34" rx="6" fill="#1c2430" stroke="#e6edf3" stroke-width="1"/>
  <text x="555" y="81" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">registered bean</text>

  <defs><marker id="a60" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Only annotated interfaces within the scanned scope become real beans; everything else is left untouched.

## 5. Runnable example

The scenario: model the scanning-and-registration process `@EnableFeignClients` triggers. Start with a naive "no scanning" state where a client interface is inert, then add a scanner that finds annotated interfaces and registers proxies, then extend it to scope scanning to specific packages.

### Level 1 — Basic

Without scanning: an annotated interface exists but nothing ever activates it.

```java
import java.lang.annotation.*;

public class EnableFeignClientsLevel1 {
    @Retention(RetentionPolicy.RUNTIME)
    @interface FeignClient { String name(); }

    @FeignClient(name = "billing-service")
    interface BillingClient {
        String getInvoice(String id);
    }

    static Map<Class<?>, Object> beanRegistry = new java.util.HashMap<>();

    public static void main(String[] args) {
        // nothing scans for @FeignClient here -- BillingClient is just an interface, never registered
        Object bean = beanRegistry.get(BillingClient.class);
        System.out.println("BillingClient bean: " + bean); // null -- would fail with NoSuchBeanDefinitionException in Spring
    }
}
```

How to run: `java EnableFeignClientsLevel1.java`

`BillingClient` is a perfectly valid annotated interface, but with no scanning mechanism active, `beanRegistry` never gets an entry for it — this is exactly the state of a real Spring application missing `@EnableFeignClients`: the annotation exists, but nothing does anything with it.

### Level 2 — Intermediate

Add a scanner that finds `@FeignClient`-annotated interfaces in a given set of classes and registers a generated proxy for each.

```java
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class EnableFeignClientsLevel2 {
    @Retention(RetentionPolicy.RUNTIME)
    @interface FeignClient { String name(); }

    @FeignClient(name = "billing-service")
    interface BillingClient { String getInvoice(String id); }

    @FeignClient(name = "promotions-service")
    interface PromotionsClient { String getPromotion(String code); }

    interface NotAFeignClient { void doSomething(); } // no annotation -- should be skipped

    static Map<Class<?>, Object> beanRegistry = new HashMap<>();

    static void enableFeignClients(List<Class<?>> candidateInterfaces) {
        for (Class<?> iface : candidateInterfaces) {
            FeignClient annotation = iface.getAnnotation(FeignClient.class);
            if (annotation == null) continue; // not a Feign client -- skip, exactly what scanning does
            Object proxy = Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface},
                    (p, method, args) -> "[" + annotation.name() + "] " + method.getName() + "(" + args[0] + ")");
            beanRegistry.put(iface, proxy);
            System.out.println("registered Feign client bean for: " + iface.getSimpleName());
        }
    }

    public static void main(String[] args) {
        enableFeignClients(List.of(BillingClient.class, PromotionsClient.class, NotAFeignClient.class));

        BillingClient billingClient = (BillingClient) beanRegistry.get(BillingClient.class);
        System.out.println(billingClient.getInvoice("42"));

        System.out.println("NotAFeignClient bean: " + beanRegistry.get(NotAFeignClient.class)); // still null
    }
}
```

How to run: `java EnableFeignClientsLevel2.java`

`enableFeignClients` mirrors `@EnableFeignClients`'s scanning behavior: it iterates candidate interfaces, checks each for the `@FeignClient` annotation, and only registers a generated proxy bean for the ones that have it — `NotAFeignClient`, lacking the annotation, is correctly skipped and never appears in `beanRegistry`, exactly like a plain interface would be ignored by real Feign scanning.

### Level 3 — Advanced

Add package-scoped scanning: only interfaces within a configured "base package" get scanned, modeling the `basePackages` attribute for when Feign clients live outside the main application's default scan scope.

```java
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class EnableFeignClientsLevel3 {
    @Retention(RetentionPolicy.RUNTIME)
    @interface FeignClient { String name(); }

    // simulate package structure via a "package" field, since real Java packages can't be faked this simply
    record CandidateInterface(Class<?> type, String simulatedPackage) {}

    @FeignClient(name = "billing-service")
    interface BillingClient { String getInvoice(String id); }

    @FeignClient(name = "internal-audit-service")
    interface AuditClient { String logEvent(String event); }

    static Map<Class<?>, Object> beanRegistry = new HashMap<>();

    static void enableFeignClients(List<CandidateInterface> candidates, String basePackage) {
        for (CandidateInterface candidate : candidates) {
            if (!candidate.simulatedPackage().startsWith(basePackage)) {
                System.out.println("skipping " + candidate.type().getSimpleName()
                        + " -- outside base package " + basePackage);
                continue; // out of scan scope entirely, even if annotated
            }
            FeignClient annotation = candidate.type().getAnnotation(FeignClient.class);
            if (annotation == null) continue;
            Object proxy = Proxy.newProxyInstance(candidate.type().getClassLoader(), new Class<?>[]{candidate.type()},
                    (p, method, args) -> "[" + annotation.name() + "] " + method.getName() + "(" + args[0] + ")");
            beanRegistry.put(candidate.type(), proxy);
            System.out.println("registered: " + candidate.type().getSimpleName());
        }
    }

    public static void main(String[] args) {
        List<CandidateInterface> candidates = List.of(
                new CandidateInterface(BillingClient.class, "com.example.clients"),
                new CandidateInterface(AuditClient.class, "com.example.internal.clients") // different subtree
        );

        // configuration only scans com.example.clients, not com.example.internal.clients
        enableFeignClients(candidates, "com.example.clients");

        System.out.println("BillingClient registered: " + (beanRegistry.get(BillingClient.class) != null));
        System.out.println("AuditClient registered: " + (beanRegistry.get(AuditClient.class) != null));
    }
}
```

How to run: `java EnableFeignClientsLevel3.java`

`AuditClient` lives in `com.example.internal.clients`, which doesn't start with the configured `basePackage` (`com.example.clients`) — even though it's correctly annotated with `@FeignClient`, it's skipped entirely before the annotation is even checked, because it's outside the configured scan scope. `BillingClient`, inside the scanned package, is found and registered normally. This mirrors a common real-world gotcha: a perfectly valid `@FeignClient` interface silently never becomes a usable bean simply because it lives in a package `@EnableFeignClients` was never told to look in.

## 6. Walkthrough

Trace `enableFeignClients` in Level 3.

1. `enableFeignClients(candidates, "com.example.clients")` runs, iterating the two-element `candidates` list. For `BillingClient`, `candidate.simulatedPackage()` is `"com.example.clients"`, which does start with `basePackage` (`"com.example.clients"`) — the scope check passes, so processing continues.
2. `BillingClient.class.getAnnotation(FeignClient.class)` returns a non-null annotation (its `name()` is `"billing-service"`), so a proxy is generated via `Proxy.newProxyInstance` and stored in `beanRegistry`, with a confirmation message printed.
3. For `AuditClient`, `candidate.simulatedPackage()` is `"com.example.internal.clients"`, which does *not* start with `"com.example.clients"` (it's a sibling subtree, not a sub-package) — the scope check fails immediately, printing the "skipping" message, and the loop moves to the next candidate without ever checking for the `@FeignClient` annotation at all.
4. The two final `println` calls confirm the outcome directly: `BillingClient registered: true`, `AuditClient registered: false` — `AuditClient`'s annotation was entirely correct, but because it fell outside the configured scan scope, it never became a usable Spring bean, exactly the class of startup failure (`NoSuchBeanDefinitionException` when something tries to `@Autowired` it) that misconfigured `@EnableFeignClients` scoping produces in a real application.

```
basePackage = "com.example.clients"

BillingClient (com.example.clients)          -> in scope -> @FeignClient found -> REGISTERED
AuditClient   (com.example.internal.clients) -> NOT in scope -> skipped before annotation is even checked
```

## 7. Gotchas & takeaways

> **Gotcha:** `@EnableFeignClients` with no arguments defaults to scanning from the package of the class it's declared on, downward — if `@FeignClient` interfaces live in a sibling package (not a sub-package) of wherever `@EnableFeignClients` is placed, they're silently never scanned, exactly as `AuditClient` was in Level 3. This is a very common real-world source of "why is my Feign client's bean missing" confusion, especially in multi-module projects where clients are deliberately placed in a separate module/package for reuse.

- `@EnableFeignClients` is a strict prerequisite for any `@FeignClient` interface to become a usable, injectable bean — the annotation alone does nothing without it.
- Scanning scope defaults to the declaring class's package and its sub-packages — use `basePackages` (or the type-safe `basePackageClasses`) explicitly whenever Feign clients live outside that default scope.
- Because scanning happens once at startup, a missing or misconfigured `@EnableFeignClients` typically manifests as an immediate startup failure (`NoSuchBeanDefinitionException`) at the first attempted injection, not a subtle runtime bug — a fast, if sometimes puzzling, failure mode.
- `@EnableFeignClients(defaultConfiguration = ...)` applies shared configuration (encoders, decoders, interceptors — covered in a later card) across every client discovered by that same scan, a convenient way to keep cross-cutting Feign configuration in one place.
