---
card: spring-cloud
gi: 53
slug: loadbalanced-resttemplate-webclient-restclient
title: "@LoadBalanced RestTemplate / WebClient / RestClient"
---

## 1. What it is

`@LoadBalanced` is a qualifier annotation applied to a `RestTemplate`, `WebClient.Builder`, or `RestClient.Builder` bean: it tells Spring Cloud to intercept every HTTP call made through that client and route logical service names (`http://billing-service/...`) through LoadBalancer (the previous card) instead of treating them as literal, resolvable hostnames.

```java
@Configuration
class ClientConfig {
    @Bean
    @LoadBalanced
    RestTemplate loadBalancedRestTemplate() {
        return new RestTemplate();
    }

    @Bean
    @LoadBalanced
    WebClient.Builder loadBalancedWebClientBuilder() {
        return WebClient.builder();
    }
}
```

```java
@Autowired RestTemplate restTemplate; // the @LoadBalanced-qualified bean, injected by type + qualifier

Invoice invoice = restTemplate.getForObject("http://billing-service/invoices/{id}", Invoice.class, 42);
```

## 2. Why & when

Without `@LoadBalanced`, a plain `RestTemplate` or `WebClient` treats `http://billing-service/...` as a literal hostname to resolve via DNS — which fails, since `billing-service` isn't a real DNS entry, it's a logical name registered with a discovery client. `@LoadBalanced` is the single annotation that flips that behavior: it registers an interceptor that recognizes the "hostname" is actually a service name, resolves it through LoadBalancer, and rewrites the request to the chosen instance's real address before it's sent.

Reach for `@LoadBalanced` whenever:

- Application code should call other services by logical name, not hardcoded addresses — which is essentially always true for inter-service calls within a discovery-managed system.
- Multiple `RestTemplate`/`WebClient` beans exist in the same application for different purposes (one for internal service calls, one for a genuinely external third-party API) — `@LoadBalanced` cleanly distinguishes which bean gets discovery-aware behavior and which doesn't.
- Migrating between `RestTemplate` (blocking, older, still common), `WebClient` (reactive), or `RestClient` (Spring 6.1+'s blocking-but-fluent client) — `@LoadBalanced` works identically across all three, so the choice of HTTP client library is independent of the load-balancing behavior.

## 3. Core concept

```
 plain client:            http://billing-service/... -> DNS lookup for "billing-service" -> FAILS (not a real host)

 @LoadBalanced client:    http://billing-service/...
                                |
                          interceptor recognizes "billing-service" as a logical name
                                |
                          LoadBalancer resolves it to a real instance: 10.0.2.2:8080
                                |
                          actual request sent to http://10.0.2.2:8080/...
```

The annotation is what activates the interception step — without it, the exact same URL string would simply fail to resolve.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A LoadBalanced RestTemplate intercepts a call to a logical service name, resolves it through LoadBalancer, and rewrites the request to the chosen real instance address before sending it">
  <rect x="20" y="70" width="170" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">restTemplate.getForObject(</text>
  <text x="105" y="107" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">"http://billing-service/...")</text>

  <rect x="240" y="60" width="180" height="60" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@LoadBalanced interceptor</text>
  <text x="330" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">rewrite host -&gt; real instance</text>

  <rect x="470" y="70" width="150" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="545" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">http://10.0.2.2:8080/...</text>

  <line x1="190" y1="90" x2="238" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a53)"/>
  <line x1="420" y1="90" x2="468" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a53)"/>

  <defs><marker id="a53" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same code, calling the same logical URL, gets silently rewritten to a real instance address by the interceptor before the network call happens.

## 5. Runnable example

The scenario: model the `@LoadBalanced` interceptor mechanism for a `billing-service` call. Start with a plain client that fails on a logical name, then add the interceptor that rewrites logical names to real addresses, then extend it to work identically across two different client "styles" (standing in for RestTemplate vs WebClient vs RestClient).

### Level 1 — Basic

A plain client — a logical service name simply doesn't resolve.

```java
public class LoadBalancedClientLevel1 {
    static String plainClientCall(String url) {
        if (url.contains("billing-service")) {
            throw new IllegalStateException("UnknownHostException: billing-service (not a real DNS entry)");
        }
        return "GET " + url; // would only work for a real, resolvable hostname
    }

    public static void main(String[] args) {
        try {
            System.out.println(plainClientCall("http://billing-service/invoices/42"));
        } catch (IllegalStateException e) {
            System.out.println("failed: " + e.getMessage());
        }
    }
}
```

How to run: `java LoadBalancedClientLevel1.java`

`billing-service` is a logical name, not a real hostname — a plain client has no mechanism to translate it, so the call fails exactly as it would with a genuine DNS resolution failure.

### Level 2 — Intermediate

Add the `@LoadBalanced`-equivalent interceptor: recognize the logical name, resolve it through a discovery-backed load balancer, and rewrite the URL before "sending" it.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class LoadBalancedClientLevel2 {
    static Map<String, List<String>> registry = Map.of(
            "billing-service", List.of("10.0.2.1:8080", "10.0.2.2:8080")
    );
    static AtomicInteger counter = new AtomicInteger(0);

    static String loadBalancedInterceptor(String url) {
        // parse out the "host" segment -- in a real interceptor this uses proper URI parsing
        String withoutScheme = url.substring("http://".length());
        String serviceName = withoutScheme.substring(0, withoutScheme.indexOf('/'));
        String path = withoutScheme.substring(withoutScheme.indexOf('/'));

        List<String> instances = registry.get(serviceName);
        if (instances == null) return url; // not a known service name -- pass through untouched (a real external host)

        String chosen = instances.get(counter.getAndIncrement() % instances.size());
        return "http://" + chosen + path;
    }

    static String loadBalancedClientCall(String url) {
        String rewritten = loadBalancedInterceptor(url);
        return "GET " + rewritten;
    }

    public static void main(String[] args) {
        for (int i = 0; i < 3; i++) {
            System.out.println(loadBalancedClientCall("http://billing-service/invoices/" + i));
        }
    }
}
```

How to run: `java LoadBalancedClientLevel2.java`

`loadBalancedInterceptor` extracts the "host" portion of the URL, checks whether it's a known service name in `registry`, and if so rewrites it to a real, load-balanced instance address before the "request" is made — this is the essential behavior `@LoadBalanced` adds. Each of the three calls resolves to a different instance in turn, courtesy of the shared round-robin counter.

### Level 3 — Advanced

Extend the interceptor to work identically across two different client "flavors" (standing in for `RestTemplate` vs `WebClient`/`RestClient`), confirming the load-balancing behavior is independent of which HTTP client style is used — exactly the point of `@LoadBalanced` working the same way across all three real client types.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;

public class LoadBalancedClientLevel3 {
    static Map<String, List<String>> registry = Map.of(
            "billing-service", List.of("10.0.2.1:8080", "10.0.2.2:8080"),
            "orders-service", List.of("10.0.1.5:8080")
    );
    static AtomicInteger counter = new AtomicInteger(0);

    static String loadBalancedInterceptor(String url) {
        String withoutScheme = url.substring("http://".length());
        String serviceName = withoutScheme.substring(0, withoutScheme.indexOf('/'));
        String path = withoutScheme.substring(withoutScheme.indexOf('/'));
        List<String> instances = registry.get(serviceName);
        if (instances == null) return url;
        String chosen = instances.get(counter.getAndIncrement() % instances.size());
        return "http://" + chosen + path;
    }

    // two different "client styles" -- both wrap the SAME interceptor, mirroring how
    // RestTemplate, WebClient, and RestClient all share the same @LoadBalanced interceptor mechanism
    static Function<String, String> restTemplateStyleGet = url ->
            "RestTemplate.getForObject(" + loadBalancedInterceptor(url) + ")";

    static Function<String, String> webClientStyleGet = url ->
            "WebClient.get().uri(" + loadBalancedInterceptor(url) + ").retrieve()";

    public static void main(String[] args) {
        System.out.println(restTemplateStyleGet.apply("http://billing-service/invoices/1"));
        System.out.println(webClientStyleGet.apply("http://billing-service/invoices/2"));
        System.out.println(restTemplateStyleGet.apply("http://orders-service/orders/7"));
        System.out.println(webClientStyleGet.apply("http://unknown-service/whatever")); // not registered -- passes through
    }
}
```

How to run: `java LoadBalancedClientLevel3.java`

Both `restTemplateStyleGet` and `webClientStyleGet` call the exact same `loadBalancedInterceptor` function — confirming that the load-balancing logic itself doesn't care which client API style wraps it. The `billing-service` calls alternate between its two instances via the shared counter regardless of which "client style" made the call, `orders-service` (a single instance) always resolves to the same address, and the unregistered `unknown-service` passes through unchanged, exactly as a genuine external hostname would with a real `@LoadBalanced` interceptor.

## 6. Walkthrough

Trace the four calls in Level 3 in order.

1. `restTemplateStyleGet.apply("http://billing-service/invoices/1")` runs first — it calls `loadBalancedInterceptor`, which parses `serviceName="billing-service"` and `path="/invoices/1"`, finds it in `registry`, and picks `instances.get(0 % 2 = 0)` — `10.0.2.1:8080`. The counter increments to `1`.
2. `webClientStyleGet.apply("http://billing-service/invoices/2")` runs next — same interceptor, same registry lookup, but the counter is now `1`, so `instances.get(1 % 2 = 1)` picks `10.0.2.2:8080`. Note that both calls used the *same shared counter*, even though they went through two different "client style" wrappers — this models how a single, application-wide LoadBalancer state is consistently applied regardless of which client bean initiated the call.
3. `restTemplateStyleGet.apply("http://orders-service/orders/7")` runs — `serviceName="orders-service"` resolves to its single-instance list; `instances.get(2 % 1 = 0)` always picks the only address, `10.0.1.5:8080`, regardless of the counter's value.
4. `webClientStyleGet.apply("http://unknown-service/whatever")` runs last — `registry.get("unknown-service")` returns `null`, so `loadBalancedInterceptor` returns the URL completely unchanged. This models a real, genuinely external hostname passing through the interceptor untouched — `@LoadBalanced` only rewrites URLs whose host matches a known, discoverable service name.

```
call 1 (RestTemplate-style): billing-service -> counter=0 -> 10.0.2.1:8080
call 2 (WebClient-style):    billing-service -> counter=1 -> 10.0.2.2:8080
call 3 (RestTemplate-style): orders-service  -> single instance -> 10.0.1.5:8080
call 4 (WebClient-style):    unknown-service -> not in registry -> passed through unchanged
```

## 7. Gotchas & takeaways

> **Gotcha:** forgetting `@LoadBalanced` on a client bean that's meant to call other services by logical name doesn't fail loudly at startup — it fails at request time with a DNS/connection error, since the "hostname" genuinely isn't resolvable without the interceptor. Conversely, adding `@LoadBalanced` to a client meant for genuinely external URLs is usually harmless (unregistered hosts pass through unchanged, as shown in Level 3), but it's still worth keeping the qualifier scoped to its intended purpose for clarity.

- `@LoadBalanced` is a qualifier, not a client type — it works identically whether the underlying bean is `RestTemplate`, `WebClient.Builder`, or `RestClient.Builder`, which makes migrating between them independent of load-balancing concerns.
- Multiple client beans, some `@LoadBalanced` and some not, can coexist in one application — a clean way to distinguish "calls to our own discoverable services" from "calls to genuine third-party external APIs."
- The interceptor mechanism only activates for hostnames that match a known, registered service name — anything else passes through as an ordinary, literal URL.
- Because `@LoadBalanced` delegates to LoadBalancer (the previous card) for actual instance selection, everything covered there — round-robin default, pluggable strategies, discovery-client-backed instance lists — applies transparently to any call made through an `@LoadBalanced` client.
