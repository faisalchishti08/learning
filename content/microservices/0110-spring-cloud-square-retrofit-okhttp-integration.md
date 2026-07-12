---
card: microservices
gi: 110
slug: spring-cloud-square-retrofit-okhttp-integration
title: "Spring Cloud Square (Retrofit / OkHttp) integration"
---

## 1. What it is

Spring Cloud Square integrates Square's popular Retrofit declarative HTTP client library (and its underlying OkHttp transport) with the Spring Cloud ecosystem — letting a Retrofit-style interface (annotated with Retrofit's own `@GET`/`@POST`/etc., not Spring's) be wired up as a Spring bean, and, notably, resolved through Spring Cloud's [client-side load balancing](0097-client-side-load-balancing-vs-server-side.md) machinery the same way a [Feign client](0106-spring-cloud-openfeign-declarative-rest-clients.md) can be, if you specifically want Retrofit's particular API design and OkHttp's connection handling instead of Spring's own client stack.

## 2. Why & when

Teams already using Retrofit elsewhere (in an Android client, or an existing non-Spring service) sometimes want to bring that same familiar client library and its API conventions into a Spring Cloud microservice, rather than learning [`@HttpExchange`](0105-spring-http-interface-httpexchange-declarative-clients.md) or [Feign](0106-spring-cloud-openfeign-declarative-rest-clients.md)'s different annotation styles. Spring Cloud Square exists specifically to bridge that gap — Retrofit's interface declaration style plus OkHttp's transport, but wired into Spring's dependency injection and, when configured, Spring Cloud's load-balancer-aware service resolution, exactly like a `@FeignClient`.

This is a narrower-audience tool than `@HttpExchange` or Feign — reach for it specifically when Retrofit/OkHttp familiarity or a specific OkHttp feature (like its particular interceptor model or HTTP/2 handling) is a genuine requirement, not as a default choice for new Spring Cloud service-to-service clients, where `@HttpExchange` or Feign are the more conventional, better-documented options within the Spring ecosystem itself.

## 3. Core concept

A Retrofit-style interface, annotated with Retrofit's own annotations, is declared and built via a `Retrofit.Builder`; Spring Cloud Square's contribution is making that builder aware of Spring Cloud's load-balanced service resolution, exactly paralleling how Feign resolves a logical service name.

```java
interface OrderClient { // Retrofit-style declaration -- @GET/@POST are Retrofit's OWN annotations
    @GET("/orders/{id}")
    Call<Order> getOrder(@Path("id") int id);
}

// wiring: Spring Cloud Square makes "http://order-service" resolve through the load balancer,
// exactly like a @FeignClient(name = "order-service") would
Retrofit retrofit = new Retrofit.Builder()
    .baseUrl("http://order-service")
    .build();
OrderClient orderClient = retrofit.create(OrderClient.class);
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three declarative client options in the Spring ecosystem each generate a working implementation from an annotated interface, differing mainly in which annotation style and underlying transport they use">
  <rect x="20" y="20" width="180" height="100" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">@HttpExchange</text>
  <text x="110" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Spring's own,</text>
  <text x="110" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">RestClient/WebClient</text>

  <rect x="230" y="20" width="180" height="100" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Feign</text>
  <text x="320" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@FeignClient,</text>
  <text x="320" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Spring Cloud native</text>

  <rect x="440" y="20" width="180" height="100" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Cloud Square</text>
  <text x="530" y="65" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Retrofit annotations,</text>
  <text x="530" y="80" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">OkHttp transport</text>
</svg>

Three declarative client approaches in the Spring ecosystem, differing in annotation style and underlying transport.

## 5. Runnable example

Scenario: an `OrderClient` interface, first declared and generated Feign-style (for direct comparison), then declared Retrofit-style with its own distinct annotation conventions (`@GET`, `@Path`) and generated via a simulated `Retrofit.create`-style factory, then extended to show that same Retrofit-style client resolved through the same load-balancer mechanism Feign uses, demonstrating the Spring Cloud integration's actual contribution.

### Level 1 — Basic

```java
// File: FeignStyleForComparison.java -- Feign-style declaration, for
// direct comparison with Retrofit's different annotation conventions.
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class FeignStyleForComparison {
    @Retention(RetentionPolicy.RUNTIME) @interface GetMapping { String value(); } // Spring/Feign-style

    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    interface OrderClient {
        @GetMapping("/orders/{id}")
        Order getOrder(int id);
    }

    static <T> T createClient(Class<T> iface) {
        return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, (proxy, method, args) -> {
            GetMapping mapping = method.getAnnotation(GetMapping.class);
            int id = (int) args[0];
            System.out.println("  [Feign-style: GET " + mapping.value().replace("{id}", String.valueOf(id)) + "]");
            return orders.get(id);
        });
    }

    public static void main(String[] args) {
        OrderClient client = createClient(OrderClient.class);
        System.out.println(client.getOrder(42));
    }
}
```

**How to run:** `javac FeignStyleForComparison.java && java FeignStyleForComparison` (JDK 17+).

Expected output:
```
  [Feign-style: GET /orders/42]
Order[id=42, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: RetrofitStyleClient.java -- the SAME kind of client, declared
// with RETROFIT'S OWN distinct annotations (@GET, @Path) instead of
// Spring/Feign's (@GetMapping, @PathVariable).
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class RetrofitStyleClient {
    @Retention(RetentionPolicy.RUNTIME) @interface GET { String value(); }  // Retrofit's OWN annotation
    @Retention(RetentionPolicy.RUNTIME) @interface Path { String value(); } // Retrofit's OWN annotation

    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    interface OrderClient {
        @GET("/orders/{id}")
        Order getOrder(@Path("id") int id); // Retrofit's parameter-level annotation style
    }

    static <T> T retrofitCreate(Class<T> iface) { // stands in for retrofit.create(OrderClient.class)
        return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, (proxy, method, args) -> {
            GET getAnnotation = method.getAnnotation(GET.class);
            int id = (int) args[0];
            System.out.println("  [Retrofit-style: GET " + getAnnotation.value().replace("{id}", String.valueOf(id)) + "]");
            return orders.get(id);
        });
    }

    public static void main(String[] args) {
        OrderClient client = retrofitCreate(OrderClient.class);
        System.out.println(client.getOrder(42));
    }
}
```

**How to run:** `javac RetrofitStyleClient.java && java RetrofitStyleClient` (JDK 17+).

Expected output:
```
  [Retrofit-style: GET /orders/42]
Order[id=42, status=PLACED]
```

### Level 3 — Advanced

```java
// File: RetrofitWithLoadBalancing.java -- the RETROFIT-style client,
// now resolved through the SAME load-balancer mechanism Feign uses --
// the specific contribution Spring Cloud Square adds on top of plain
// Retrofit.
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class RetrofitWithLoadBalancing {
    @Retention(RetentionPolicy.RUNTIME) @interface GET { String value(); }

    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    interface OrderClient {
        @GET("/orders/{id}")
        Order getOrder(int id);
    }

    static class LoadBalancer { // the SAME load-balancing concept Feign integration uses
        List<String> instances = List.of("order-service-1:8080", "order-service-2:8080");
        int roundRobinIndex = 0;
        String pick() {
            String chosen = instances.get(roundRobinIndex % instances.size());
            roundRobinIndex++;
            return chosen;
        }
    }

    static <T> T retrofitCreateLoadBalanced(Class<T> iface, LoadBalancer loadBalancer) { // Spring Cloud Square's contribution
        return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, (proxy, method, args) -> {
            String instance = loadBalancer.pick(); // resolved via Spring Cloud LoadBalancer, just like Feign
            GET getAnnotation = method.getAnnotation(GET.class);
            int id = (int) args[0];
            String path = getAnnotation.value().replace("{id}", String.valueOf(id));
            System.out.println("  [Retrofit client, load-balanced -> " + instance + ": GET " + path + "]");
            return orders.get(id);
        });
    }

    public static void main(String[] args) {
        LoadBalancer loadBalancer = new LoadBalancer();
        OrderClient client = retrofitCreateLoadBalanced(OrderClient.class, loadBalancer);
        System.out.println(client.getOrder(42));
        System.out.println(client.getOrder(42)); // resolves to a DIFFERENT instance, same Retrofit-style interface
    }
}
```

**How to run:** `javac RetrofitWithLoadBalancing.java && java RetrofitWithLoadBalancing` (JDK 17+).

Expected output:
```
  [Retrofit client, load-balanced -> order-service-1:8080: GET /orders/42]
Order[id=42, status=PLACED]
  [Retrofit client, load-balanced -> order-service-2:8080: GET /orders/42]
Order[id=42, status=PLACED]
```

## 6. Walkthrough

1. **Level 1** — `FeignStyleForComparison.OrderClient.getOrder` is annotated with `@GetMapping`, Spring/Feign's naming convention, and `createClient`'s proxy handler reads that annotation directly. `main` calls it and gets the expected order back — establishing the baseline "Spring-flavored" declarative style for direct comparison.
2. **Level 2 — Retrofit's distinct annotation style** — `RetrofitStyleClient.OrderClient.getOrder` uses `@GET` (not `@GetMapping`) and `@Path("id")` (not `@PathVariable`) on the method parameter — Retrofit's own, differently-named annotation conventions, reflecting that Retrofit is a separate library with its own API design predating and independent of Spring. `retrofitCreate`'s proxy handler reads the `@GET` annotation instead of `@GetMapping`, but performs conceptually the identical dispatch: extract the path template, substitute the argument, "call" the resulting path. `main` calls `client.getOrder(42)` and gets the same order back, printed with a "Retrofit-style" diagnostic label distinguishing it from Level 1's Feign-style one.
3. **Level 3 — adding Spring Cloud's load-balancing integration** — `retrofitCreateLoadBalanced` takes an additional `LoadBalancer` parameter, and its proxy handler calls `loadBalancer.pick()` *before* constructing the request path — resolving a target instance the same way Feign's Spring Cloud LoadBalancer integration does (see [Feign with Spring Cloud LoadBalancer](0107-feign-with-spring-cloud-loadbalancer.md)), just applied to a Retrofit-style client instead of a Feign one.
4. **Tracing `main`'s two calls** — the first `client.getOrder(42)` calls `loadBalancer.pick()`, which (round-robin, starting at index 0) returns `order-service-1:8080`, printed alongside the Retrofit-style path. The second call to `client.getOrder(42)` calls `loadBalancer.pick()` again, now returning `order-service-2:8080` (round-robin index incremented) — demonstrating that the *same* Retrofit-declared interface, unchanged between the two calls, is genuinely being load-balanced across multiple resolved instances, exactly matching the behavior Feign clients get from the same underlying Spring Cloud LoadBalancer component.
5. **What Spring Cloud Square specifically contributes** — comparing Level 2 and Level 3 makes the library's actual value proposition concrete: plain Retrofit (Level 2) gives you Retrofit's familiar annotation style and OkHttp transport, but with no inherent connection to Spring Cloud's service-discovery/load-balancing ecosystem — you'd need to build that integration yourself. Spring Cloud Square (Level 3) is specifically the bridge that lets a Retrofit-declared interface participate in that same load-balanced resolution that Feign clients get natively, without giving up Retrofit's own annotation conventions and client library.

## 7. Gotchas & takeaways

> **Gotcha:** adopting Spring Cloud Square specifically to get Retrofit's annotation style means your team now needs familiarity with *two* different declarative client annotation conventions if any other part of the codebase already uses `@HttpExchange` or Feign — consider whether the specific Retrofit/OkHttp features you need are worth that consistency cost across the codebase, versus standardizing on one declarative client approach throughout.

- Spring Cloud Square bridges Retrofit's own annotation style (`@GET`, `@Path`, etc.) and OkHttp's transport with Spring Cloud's dependency injection and, notably, its load-balancer-aware service resolution.
- The specific value it adds over plain Retrofit is exactly that Spring Cloud LoadBalancer integration — the same logical-name-to-instance resolution [Feign](0106-spring-cloud-openfeign-declarative-rest-clients.md) provides, but for Retrofit-declared interfaces.
- This is a narrower-audience tool than `@HttpExchange` or Feign — reach for it specifically when Retrofit/OkHttp familiarity or a specific OkHttp feature is a genuine, deliberate requirement.
- For new Spring Cloud service-to-service clients without a specific Retrofit dependency already in play, [`@HttpExchange`](0105-spring-http-interface-httpexchange-declarative-clients.md) or [Feign](0106-spring-cloud-openfeign-declarative-rest-clients.md) remain the more conventional, better-integrated choices within the Spring ecosystem.
- All three declarative client approaches (`@HttpExchange`, Feign, Spring Cloud Square/Retrofit) share the same underlying pattern: an annotated interface plus a proxy-generation mechanism, differing mainly in annotation vocabulary and default transport.
