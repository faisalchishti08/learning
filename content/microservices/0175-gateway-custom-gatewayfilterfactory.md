---
card: microservices
gi: 175
slug: gateway-custom-gatewayfilterfactory
title: "Gateway custom GatewayFilterFactory"
---

## 1. What it is

A custom `GatewayFilterFactory` is how an application extends Spring Cloud Gateway with its own reusable, configurable filter type — beyond the built-in filters (add header, rewrite path, and others), a `GatewayFilterFactory` implementation defines a new named filter, with its own configuration properties, that can then be referenced by name in route configuration exactly like a built-in one.

## 2. Why & when

The built-in filter library covers common, generic needs, but a specific application inevitably has routing logic unique to its own domain — validating a proprietary API key format, enriching a request with data looked up from an internal cache, applying a business-specific header transformation — that no built-in filter expresses. Rather than writing this logic inline and awkwardly (or duplicating it across every route that needs it), a custom `GatewayFilterFactory` packages it as a proper, reusable, named, and independently configurable filter type, usable in route configuration the same way any built-in filter is.

Write a custom `GatewayFilterFactory` when a piece of routing logic is needed across multiple routes, needs its own per-route configuration values (not just a fixed, hard-coded behavior), and doesn't correspond to any built-in filter. For a one-off need on a single route, an inline filter definition is often simpler than the ceremony of a full factory class.

## 3. Core concept

A `GatewayFilterFactory` implementation defines a configuration class (the parameters a route using this filter can set) and a factory method that, given a specific route's configuration values, produces a `GatewayFilter` instance implementing the actual filtering logic — the same factory can produce differently-configured filter instances for different routes.

```java
@Component
public class RequestValidationGatewayFilterFactory extends AbstractGatewayFilterFactory<RequestValidationGatewayFilterFactory.Config> {
    public static class Config { String requiredHeaderPrefix; } // PER-ROUTE configuration

    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            String value = exchange.getRequest().getHeaders().getFirst("X-Api-Key");
            if (value == null || !value.startsWith(config.requiredHeaderPrefix)) {
                exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
                return exchange.getResponse().setComplete();
            }
            return chain.filter(exchange);
        };
    }
}
// used in configuration: .filters(f -> f.filter(new RequestValidationGatewayFilterFactory().apply(config)))
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A GatewayFilterFactory, given two different Config objects, produces two differently-behaving GatewayFilter instances -- one route uses a filter configured to require prefix ORD-, another route uses the same factory configured to require prefix CUST-" >
  <rect x="230" y="60" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">GatewayFilterFactory</text>

  <rect x="20" y="20" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Config: prefix=ORD-</text>

  <rect x="20" y="115" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="137" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Config: prefix=CUST-</text>

  <rect x="480" y="20" width="140" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="550" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">filter for order route</text>

  <rect x="480" y="115" width="140" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="550" y="137" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">filter for customer route</text>

  <line x1="170" y1="38" x2="228" y2="75" stroke="#8b949e" marker-end="url(#arr56)"/>
  <line x1="170" y1="132" x2="228" y2="95" stroke="#8b949e" marker-end="url(#arr56)"/>
  <line x1="410" y1="75" x2="478" y2="38" stroke="#8b949e" marker-end="url(#arr56)"/>
  <line x1="410" y1="95" x2="478" y2="132" stroke="#8b949e" marker-end="url(#arr56)"/>

  <defs>
    <marker id="arr56" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

One factory, reused across routes, produces differently-configured filter instances per route.

## 5. Runnable example

Scenario: an API key validation requirement that starts hard-coded and duplicated across two routes (showing the maintenance problem), refactors into a reusable factory producing differently-configured filter instances per route, and finally adds a third, differently-configured usage to prove the factory genuinely generalizes without any code changes.

### Level 1 — Basic

```java
// File: DuplicatedValidationLogic.java -- the SAME validation logic, hand-copied
// into TWO separate route handlers, with only the required prefix differing.
public class DuplicatedValidationLogic {
    static String handleOrderRoute(String apiKey) {
        if (apiKey == null || !apiKey.startsWith("ORD-")) return "401 Unauthorized"; // DUPLICATED logic #1
        return "200 OK, order route";
    }
    static String handleCustomerRoute(String apiKey) {
        if (apiKey == null || !apiKey.startsWith("CUST-")) return "401 Unauthorized"; // DUPLICATED logic #2, only the prefix differs
        return "200 OK, customer route";
    }

    public static void main(String[] args) {
        System.out.println(handleOrderRoute("ORD-12345"));
        System.out.println(handleCustomerRoute("CUST-67890"));
        System.out.println("Fixing a bug in this validation logic means finding and fixing it in BOTH places, separately.");
    }
}
```

**How to run:** `javac DuplicatedValidationLogic.java && java DuplicatedValidationLogic` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ReusableFilterFactory.java -- ONE factory, configured DIFFERENTLY per
// route, producing two DISTINCT filter behaviors from ONE shared implementation.
import java.util.function.*;

public class ReusableFilterFactory {
    static class Config { String requiredPrefix; Config(String requiredPrefix) { this.requiredPrefix = requiredPrefix; } }

    // the FACTORY: ONE implementation, parameterized by Config
    static class RequestValidationGatewayFilterFactory {
        Function<String, String> apply(Config config) {
            return apiKey -> {
                if (apiKey == null || !apiKey.startsWith(config.requiredPrefix)) return "401 Unauthorized";
                return "200 OK, validated (prefix=" + config.requiredPrefix + ")";
            };
        }
    }

    public static void main(String[] args) {
        RequestValidationGatewayFilterFactory factory = new RequestValidationGatewayFilterFactory();

        // TWO routes, TWO different Configs, SAME factory implementation
        Function<String, String> orderRouteFilter = factory.apply(new Config("ORD-"));
        Function<String, String> customerRouteFilter = factory.apply(new Config("CUST-"));

        System.out.println(orderRouteFilter.apply("ORD-12345"));
        System.out.println(customerRouteFilter.apply("CUST-67890"));
        System.out.println("ONE factory implementation, reused with different Config -- fixing a bug means fixing it in exactly ONE place.");
    }
}
```

**How to run:** `javac ReusableFilterFactory.java && java ReusableFilterFactory` (JDK 17+).

Expected output:
```
200 OK, validated (prefix=ORD-)
200 OK, validated (prefix=CUST-)
ONE factory implementation, reused with different Config -- fixing a bug means fixing it in exactly ONE place.
```

### Level 3 — Advanced

```java
// File: ThirdRouteProvesGeneralization.java -- a THIRD route, with a THIRD
// prefix, added with ZERO changes to the factory's implementation -- proving genuine reuse.
import java.util.function.*;
import java.util.*;

public class ThirdRouteProvesGeneralization {
    static class Config { String requiredPrefix; Config(String requiredPrefix) { this.requiredPrefix = requiredPrefix; } }

    static class RequestValidationGatewayFilterFactory { // UNCHANGED from Level 2
        Function<String, String> apply(Config config) {
            return apiKey -> {
                if (apiKey == null || !apiKey.startsWith(config.requiredPrefix)) return "401 Unauthorized";
                return "200 OK, validated (prefix=" + config.requiredPrefix + ")";
            };
        }
    }

    public static void main(String[] args) {
        RequestValidationGatewayFilterFactory factory = new RequestValidationGatewayFilterFactory();

        // THREE routes now, including a brand NEW shipping route -- the factory ITSELF was never touched
        Map<String, Function<String, String>> routeFilters = Map.of(
            "order-route", factory.apply(new Config("ORD-")),
            "customer-route", factory.apply(new Config("CUST-")),
            "shipping-route", factory.apply(new Config("SHIP-"))); // NEW, added purely via configuration

        List<Map.Entry<String, String>> testRequests = List.of(
            Map.entry("order-route", "ORD-111"),
            Map.entry("customer-route", "CUST-222"),
            Map.entry("shipping-route", "SHIP-333"),
            Map.entry("shipping-route", "ORD-444")); // WRONG prefix for this route -- should be rejected

        for (var entry : testRequests) {
            String result = routeFilters.get(entry.getKey()).apply(entry.getValue());
            System.out.println(entry.getKey() + " with key '" + entry.getValue() + "': " + result);
        }
        System.out.println("A THIRD route was added purely through CONFIGURATION (a new Config value) -- the factory's CODE never changed.");
    }
}
```

**How to run:** `javac ThirdRouteProvesGeneralization.java && java ThirdRouteProvesGeneralization` (JDK 17+).

Expected output:
```
order-route with key 'ORD-111': 200 OK, validated (prefix=ORD-)
customer-route with key 'CUST-222': 200 OK, validated (prefix=CUST-)
shipping-route with key 'SHIP-333': 200 OK, validated (prefix=SHIP-)
shipping-route with key 'ORD-444': 401 Unauthorized
A THIRD route was added purely through CONFIGURATION (a new Config value) -- the factory's CODE never changed.
```

## 6. Walkthrough

1. **Level 1** — `handleOrderRoute` and `handleCustomerRoute` both implement the identical validation *structure* (check for null, check for a specific prefix, return `401` or success), differing only in the literal prefix string; the printed comment states the direct consequence — a bug fix or logic change requires updating both methods separately.
2. **Level 2, the factory as parameterized logic** — `RequestValidationGatewayFilterFactory.apply` takes a `Config` and returns a `Function<String, String>` closing over that specific config's `requiredPrefix`; the actual validation logic (null check, prefix check) is written exactly once, inside this single method.
3. **Level 2, two configured instances from one factory** — `factory.apply(new Config("ORD-"))` and `factory.apply(new Config("CUST-"))` each produce a distinct function object, but both come from calling the identical `apply` method with different `Config` values — this mirrors exactly how a real `GatewayFilterFactory` produces differently-behaving `GatewayFilter` instances per route based on that route's configuration block.
4. **Level 2, the maintenance win realized** — the final printed comment is now literally true of the code: since both `orderRouteFilter` and `customerRouteFilter` are produced by the same `apply` method body, any future bug fix to the validation logic needs to change exactly one place.
5. **Level 3, a third route added purely via configuration** — `routeFilters` gains a `"shipping-route"` entry, produced by calling the *exact same*, completely unmodified `RequestValidationGatewayFilterFactory.apply` method with a new `Config("SHIP-")` value — no new method, no new class, no change to `RequestValidationGatewayFilterFactory` at all.
6. **Level 3, correct behavior including a rejection case** — the fourth test entry pairs `"shipping-route"` with an API key using the *wrong* prefix (`"ORD-444"` instead of the expected `"SHIP-"`); the shipping route's filter correctly rejects it with `"401 Unauthorized"`, proving the per-route configuration genuinely isolates each route's validation rule from the others' — a key intended for the order route does not accidentally satisfy the shipping route's check.
7. **Level 3, what this demonstrates about real Spring Cloud Gateway usage** — this is exactly the pattern a real `GatewayFilterFactory` implementation provides: write the filtering logic once, as a proper Spring-managed component, and then reference it by name with different configuration values across as many routes as needed in `application.yml`, with each route's specific configuration producing its own correctly-scoped, independently-behaving filter instance, all without touching the factory's Java code again after it's written.

## 7. Gotchas & takeaways

> **Gotcha:** a custom `GatewayFilterFactory`'s `Config` class needs proper getters/setters (or, in modern Spring, can leverage records or `@ConfigurationProperties`-style binding) for Spring Cloud Gateway to correctly populate it from `application.yml`'s route configuration — a `Config` class that doesn't follow the expected binding conventions fails silently at startup or produces a filter configured with unexpected default values, which can be confusing to debug since the failure often doesn't surface as an obvious error.

- A custom `GatewayFilterFactory` packages application-specific routing logic as a proper, reusable, named filter type, usable in route configuration exactly like a built-in Spring Cloud Gateway filter.
- The factory pattern separates the filtering logic (written once) from its per-route configuration (a `Config` object), letting the same logic behave differently for different routes based on that configuration.
- This avoids duplicating similar-but-slightly-different filtering logic across multiple routes, concentrating any future logic change to exactly one implementation.
- Adding a new route that needs the same kind of filtering, but with different configuration values, requires no code changes to the factory itself — only a new configuration entry.
- Write a custom factory when logic is reused across multiple routes with varying configuration; for a genuinely one-off need on a single route, an inline filter is often simpler than the ceremony of a full factory implementation.
