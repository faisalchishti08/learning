---
card: microservices
gi: 546
slug: spring-cloud-openfeign-declarative-clients
title: "Spring Cloud OpenFeign (declarative clients)"
---

## 1. What it is

**Spring Cloud OpenFeign** lets you define an HTTP client as a plain Java interface, annotated with the same familiar Spring MVC-style annotations (`@GetMapping`, `@PostMapping`, `@PathVariable`) used to *define* endpoints — but here used to *declare a client's* calling contract. Spring generates a concrete implementation of that interface at runtime, wiring in [service discovery and client-side load balancing](0544-spring-cloud-loadbalancer-client-side-lb.md) automatically, so calling a downstream service becomes as simple as calling a regular Java method, with no manual `RestTemplate`/`WebClient` boilerplate at every call site.

## 2. Why & when

You reach for OpenFeign whenever a service calls another service's REST API repeatedly, and hand-writing the same `RestTemplate`/`WebClient` request-building boilerplate at every call site feels repetitive and error-prone:

- **Manually building HTTP requests (setting the URL, path variables, request body, parsing the response) is boilerplate that has nothing to do with business logic** — the same `restTemplate.getForObject(url, ResponseType.class)` pattern repeats at every call site that talks to the same downstream service, with plenty of opportunity for small inconsistencies (a typo in a path, an incorrectly-typed response) to creep in across different call sites.
- **OpenFeign flips this around: you declare the *interface* the downstream service exposes**, annotated exactly like you'd annotate a Spring MVC controller method for that same endpoint, and Spring generates the actual HTTP-calling implementation for you — calling code just calls a method on an injected interface, with no manual request construction at all.
- **It integrates service discovery and load balancing automatically** — a Feign client's `name` attribute names the logical service to call, and Spring resolves and load-balances across that service's healthy instances exactly as `@LoadBalanced` `RestTemplate`/`WebClient` calls would, without any additional configuration beyond declaring the interface.
- **You reach for it specifically for calling other services' REST APIs from within a Spring application** — it's a client-side convenience layered on top of the same underlying HTTP-calling and discovery mechanisms already discussed, not a replacement for those mechanisms, and a service still needs a discovery client and (usually) a load-balancer dependency for a Feign client's discovery-based resolution to actually work.

## 3. Core concept

Think of a form you fill out and hand to an assistant, versus personally making a phone call, dialing the number, navigating a phone tree, and transcribing the response yourself every single time you need something from a particular office. The form approach lets you simply write down what you want ("get me order 42's details") in a structured, pre-agreed format, and hand it to an assistant who already knows how to make that specific call correctly, every time, without you personally repeating the mechanics of dialing and transcribing. A Feign client interface is that form: you declare, once, what the call looks like (an annotated method signature), and Spring's generated implementation is the assistant that actually places the call correctly, every time it's invoked.

Concretely:

1. **`@FeignClient(name = "order-service")` on an interface** names the logical downstream service — resolved via service discovery exactly like a `lb://` gateway route or an `@LoadBalanced` client call.
2. **Each method on the interface, annotated with `@GetMapping`/`@PostMapping` and parameter annotations (`@PathVariable`, `@RequestBody`)**, describes one specific HTTP call — the method's return type is what the response body is expected to deserialize into.
3. **Spring generates a concrete implementation of this interface at startup** (a dynamic proxy), registering it as a Spring bean — any other bean can simply `@Autowired` (or constructor-inject) the interface and call its methods directly, with no manual HTTP client code anywhere in the calling code.
4. **Feign clients typically integrate with the same resiliency mechanisms discussed elsewhere** — a Feign client method can be wrapped with a [circuit breaker](0545-spring-cloud-circuit-breaker-resiliency-abstraction.md) via a configured fallback factory, layering failure protection on top of the declarative calling style without abandoning it.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Feign client interface, annotated like a controller, is turned into a real HTTP-calling implementation by Spring at startup, resolved through discovery and load balancing automatically">
  <rect x="20" y="30" width="220" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@FeignClient(name="order-service")</text>
  <text x="130" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">interface OrderClient {</text>
  <text x="130" y="84" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">  @GetMapping getOrder(id); }</text>

  <line x1="240" y1="65" x2="290" y2="65" stroke="#8b949e" marker-end="url(#a11)"/>
  <text x="265" y="55" fill="#8b949e" font-size="7">Spring generates</text>

  <rect x="300" y="30" width="180" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="390" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">real HTTP-calling</text>
  <text x="390" y="76" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">proxy implementation</text>

  <line x1="480" y1="65" x2="530" y2="65" stroke="#8b949e" marker-end="url(#a11)"/>
  <rect x="540" y="30" width="100" height="70" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="590" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">discovery +</text>
  <text x="590" y="76" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">load balancer</text>
  <defs><marker id="a11" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Declaring an annotated interface is all a Feign client needs; Spring generates the actual HTTP-calling implementation, wired into discovery and load balancing.

## 5. Runnable example

Scenario: calling an order-lookup endpoint from another service. We start with a plain Java model illustrating the boilerplate a declarative client eliminates, extend it to a hand-rolled dynamic proxy modeling how Feign generates its implementation, then show the real `@FeignClient` shape.

### Level 1 — Basic

```java
// File: ManualHttpCallBoilerplate.java -- models the BOILERPLATE a
// declarative client eliminates: manually building the URL, making the
// call, and parsing the response, REPEATED at every call site.
import java.util.*;

public class ManualHttpCallBoilerplate {
    // simulates a "RestTemplate"-style manual call
    static String getForObject(String url) {
        System.out.println("Manually building and sending GET " + url);
        return "{\"orderId\":\"" + url.substring(url.lastIndexOf('/') + 1) + "\"}";
    }

    static String getOrder(String orderId) {
        String url = "http://order-service/orders/" + orderId; // manually built, every call site repeats this
        return getForObject(url);
    }

    public static void main(String[] args) {
        System.out.println(getOrder("42"));
        System.out.println("Every NEW call site needing order-service repeats this same URL-building pattern.");
    }
}
```

How to run: `java ManualHttpCallBoilerplate.java`

`getOrder` manually constructs the URL string and calls a generic `getForObject` — functional, but this exact pattern (building a URL, calling a generic method, parsing the response) has to be re-written, correctly, at every place in the codebase that needs to call `order-service`, with no compile-time guarantee different call sites stay consistent with each other.

### Level 2 — Intermediate

```java
// File: DynamicProxyModel.java -- models HOW Feign actually works
// internally: given an ANNOTATED INTERFACE, generate a real implementation
// via a dynamic proxy, so calling code never manually builds a request.
import java.lang.reflect.*;
import java.util.*;

public class DynamicProxyModel {
    interface OrderClient {
        String getOrder(String orderId); // the DECLARED contract, no implementation
    }

    // a simplified stand-in for what Feign's proxy-generation does at startup
    static OrderClient createProxy() {
        return (OrderClient) Proxy.newProxyInstance(
            OrderClient.class.getClassLoader(),
            new Class[]{OrderClient.class},
            (proxy, method, args) -> {
                String orderId = (String) args[0];
                String url = "http://order-service/orders/" + orderId; // the proxy builds the request, NOT the caller
                System.out.println("[generated proxy] calling " + url);
                return "{\"orderId\":\"" + orderId + "\"}";
            });
    }

    public static void main(String[] args) {
        OrderClient client = createProxy(); // Spring does exactly this for @FeignClient interfaces at startup
        System.out.println(client.getOrder("42")); // looks like a NORMAL method call -- no manual URL-building here
    }
}
```

How to run: `java DynamicProxyModel.java`

`createProxy` uses `java.lang.reflect.Proxy` to generate a real implementation of `OrderClient` at runtime — calling code (`client.getOrder("42")`) looks like an ordinary method call, with zero knowledge of URLs or HTTP mechanics; the actual request construction happens inside the generated proxy's invocation handler. This is precisely the mechanism (a more sophisticated version, driven by the interface's Spring MVC annotations) that Feign uses to turn a declared interface into a real, working HTTP client.

### Level 3 — Advanced

```java
// File: OpenFeignRealShape.java -- the REAL Spring Cloud OpenFeign shape:
// @FeignClient interface with a FALLBACK, resolved via discovery and
// wrapped with circuit-breaker protection automatically.
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.*;

public class OpenFeignRealShape {

    @FeignClient(name = "order-service", fallback = OrderClientFallback.class)
    interface OrderClient {
        @GetMapping("/orders/{orderId}")
        String getOrder(@PathVariable("orderId") String orderId);

        @PostMapping("/orders")
        String createOrder(@RequestBody String orderRequestJson);
    }

    // invoked automatically if the real call fails or the circuit is open (requires
    // spring-cloud-starter-circuitbreaker-resilience4j + feign.circuitbreaker.enabled=true)
    @Component
    static class OrderClientFallback implements OrderClient {
        public String getOrder(String orderId) {
            return "{\"orderId\":\"" + orderId + "\",\"status\":\"unavailable\",\"fallback\":true}";
        }
        public String createOrder(String orderRequestJson) {
            throw new RuntimeException("Cannot create orders while order-service is unavailable");
        }
    }

    // Calling code, elsewhere in the application, just does:
    // @Autowired OrderClient orderClient;
    // String result = orderClient.getOrder("42"); -- looks like a plain method call
}
```

How to run: requires `spring-cloud-starter-openfeign` plus a discovery client dependency (Eureka, Consul, or Kubernetes) and `@EnableFeignClients` on a configuration class; run in a Spring Boot application, `@Autowired OrderClient` into any bean, and call `orderClient.getOrder("42")` to see it resolved and dispatched to a real `order-service` instance, with `OrderClientFallback` automatically invoked if that call fails or the circuit is open.

`OrderClient` is a plain interface with no implementation written anywhere — `@FeignClient(name = "order-service", ...)` tells Spring to generate one, resolving `"order-service"` through discovery exactly as an `@LoadBalanced` client or gateway `lb://` route would. `@GetMapping("/orders/{orderId}")` and `@PathVariable` describe the exact HTTP call to make, mirroring how the same annotations would describe an endpoint if `order-service` itself were defining it — the declarative symmetry between defining an endpoint and declaring a client for it is OpenFeign's central idea.

## 6. Walkthrough

Trace a call to `orderClient.getOrder("42")` (from `OpenFeignRealShape`) end to end, assuming `order-service` is healthy:

1. **The calling bean invokes `orderClient.getOrder("42")`** on the injected `OrderClient` interface — from the calling code's perspective, this is indistinguishable from calling a plain, local method.
2. **Spring's generated Feign proxy intercepts this call.** It inspects the `@GetMapping("/orders/{orderId}")` and `@PathVariable("orderId")` annotations on the interface method (read once, at startup, via reflection) to determine the HTTP method (`GET`) and URL template (`/orders/{orderId}`), substituting the actual argument `"42"` for the `{orderId}` path segment.
3. **The proxy resolves the logical service name `"order-service"`** (from `@FeignClient(name = "order-service", ...)`) through the same discovery and client-side load-balancing machinery discussed for [Spring Cloud LoadBalancer](0544-spring-cloud-loadbalancer-client-side-lb.md) — say, resolving to instance `10.0.5.2:8080`.
4. **The proxy issues the actual HTTP request**: `GET http://10.0.5.2:8080/orders/42`.
5. **`order-service` handles this request normally and returns a response**, say `200 OK` with body `{"orderId":"42","status":"SUBMITTED"}`.
6. **The Feign proxy deserializes the response body into the method's declared return type** (`String`, in this simplified example — in practice, often a more specific DTO type) and returns it as the result of the original `getOrder("42")` call.

Now trace the same call assuming `order-service` is entirely down: step 4's HTTP request fails (connection refused or timeout). Because `feign.circuitbreaker.enabled=true` is configured and `fallback = OrderClientFallback.class` is declared, the proxy catches this failure and instead invokes `orderClientFallback.getOrder("42")`, which returns the fallback response `{"orderId":"42","status":"unavailable","fallback":true}` — the calling code's `getOrder("42")` call still returns *something* usable, rather than propagating a raw connection exception, all without the calling code needing any explicit error-handling logic around the call itself.

## 7. Gotchas & takeaways

> **Gotcha:** a Feign client's fallback class must implement every method on the client interface, even ones the current call path doesn't use — if a new method is added to the interface later and the fallback class isn't updated to implement it too, the application fails to start (a compile-time interface-implementation mismatch), which is a useful safety net, but can be a confusing error if you don't immediately recognize the fallback class needs updating whenever the interface changes.

- Feign clients let you declare a downstream service's calling contract as a plain, annotated interface, with Spring generating the actual HTTP-calling implementation — eliminating repeated manual `RestTemplate`/`WebClient` boilerplate at every call site.
- The same `@GetMapping`/`@PathVariable`-style annotations used to *define* an endpoint are reused here to *declare a client* for calling one, giving a consistent, symmetric annotation vocabulary across both sides.
- Feign integrates with the same discovery and client-side load-balancing mechanisms used elsewhere in Spring Cloud — `@FeignClient(name = "...")` names a logical service, resolved and load-balanced automatically.
- Combine with a fallback class (and `feign.circuitbreaker.enabled=true`) to layer resiliency directly onto the declarative calling style, so a downstream failure doesn't propagate as a raw, unhandled exception to calling code.
