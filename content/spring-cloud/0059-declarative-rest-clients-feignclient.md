---
card: spring-cloud
gi: 59
slug: declarative-rest-clients-feignclient
title: "Declarative REST clients (@FeignClient)"
---

## 1. What it is

`@FeignClient` lets you declare an HTTP client as a plain Java interface — method signatures with mapping annotations (`@GetMapping`, `@PostMapping`, familiar from Spring MVC controllers) — and Spring generates a working implementation at startup that translates each method call into an actual HTTP request, integrated with LoadBalancer for service-name resolution automatically.

```java
@FeignClient(name = "billing-service")
public interface BillingClient {
    @GetMapping("/invoices/{id}")
    Invoice getInvoice(@PathVariable("id") String id);

    @PostMapping("/invoices")
    Invoice createInvoice(@RequestBody Invoice invoice);
}
```

```java
@Autowired BillingClient billingClient; // just an interface -- Spring provides the real implementation

Invoice invoice = billingClient.getInvoice("42"); // looks like a local method call, is actually an HTTP GET
```

## 2. Why & when

Calling another service through `@LoadBalanced RestTemplate`/`WebClient` (covered earlier) means manually building URLs, handling serialization, and threading through path variables and request bodies at every call site — repetitive and error-prone across many call sites. Feign instead lets the *interface* describe the contract once, and every caller just calls a regular-looking Java method; the URL construction, serialization, and load-balanced call all happen automatically underneath.

Reach for `@FeignClient` when:

- A downstream service is called from multiple places in the codebase, and repeating manual `RestTemplate`/`WebClient` boilerplate at each call site would be redundant and inconsistent.
- The team wants the calling contract to read like a typed Java API (method names, parameter types, return types) rather than string-based URL construction — genuine compile-time safety on the call signature, even though the actual call still happens over the network.
- The downstream service's API is stable enough to be usefully described as an interface — Feign shines most when there's a clear, relatively fixed contract to declare.

## 3. Core concept

```
 interface BillingClient {
     @GetMapping("/invoices/{id}")
     Invoice getInvoice(@PathVariable String id);
 }

 Spring, at startup, generates a real implementation of this interface:
   method call billingClient.getInvoice("42")
       -> builds: GET http://billing-service/invoices/42
       -> resolves "billing-service" through LoadBalancer (as covered in earlier cards)
       -> sends the actual HTTP request
       -> deserializes the JSON response body into an Invoice object
       -> returns it, as if it were a normal method's return value
```

The interface is a contract; Feign's generated proxy is the implementation that turns each call into a real, load-balanced HTTP request.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling a method on a Feign client interface is translated by a generated proxy into an actual load balanced HTTP request, with the JSON response deserialized back into the return type">
  <rect x="20" y="70" width="170" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billingClient.getInvoice("42")</text>

  <line x1="190" y1="90" x2="240" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a59)"/>

  <rect x="245" y="60" width="170" height="60" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Feign generated proxy</text>
  <text x="330" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">build request, load-balance, call</text>

  <rect x="450" y="70" width="160" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">GET /invoices/42</text>

  <line x1="415" y1="90" x2="448" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a59)"/>

  <text x="330" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">response JSON deserialized back into an Invoice, returned as if it were a normal method result</text>

  <defs><marker id="a59" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The interface method call and the actual network request are two sides of the same generated proxy — the caller only ever sees the Java method call.

## 5. Runnable example

The scenario: model Feign's interface-to-HTTP-call translation for `BillingClient`. Start with the manual approach Feign replaces, then build a simplified dynamic proxy that mimics Feign's generation, then extend it to handle path variables and request bodies together.

### Level 1 — Basic

The manual approach — what every call site would look like without Feign.

```java
import java.util.*;

public class FeignClientLevel1 {
    record Invoice(String id, double amount) {}

    static Map<String, Invoice> billingBackend = Map.of("42", new Invoice("42", 199.99));

    static Invoice getInvoiceManually(String id) {
        // in reality: build a URL, call RestTemplate/WebClient, deserialize the response
        System.out.println("GET http://billing-service/invoices/" + id);
        return billingBackend.get(id);
    }

    public static void main(String[] args) {
        Invoice invoice = getInvoiceManually("42");
        System.out.println("received: " + invoice);
    }
}
```

How to run: `java FeignClientLevel1.java`

This repeats the same URL-building and call pattern manually — fine for one call site, tedious and error-prone repeated across dozens.

### Level 2 — Intermediate

Build a simplified dynamic proxy that mimics what Feign generates from an interface at startup — turning an interface method call into a described HTTP request.

```java
import java.lang.reflect.*;
import java.util.*;

public class FeignClientLevel2 {
    record Invoice(String id, double amount) {}

    interface BillingClient {
        Invoice getInvoice(String id); // mirrors @GetMapping("/invoices/{id}")
    }

    static Map<String, Invoice> billingBackend = Map.of("42", new Invoice("42", 199.99));

    // a simplified stand-in for Feign's proxy generation
    static BillingClient createClient() {
        return (BillingClient) Proxy.newProxyInstance(
                FeignClientLevel2.class.getClassLoader(),
                new Class<?>[]{BillingClient.class},
                (proxy, method, args) -> {
                    if (method.getName().equals("getInvoice")) {
                        String id = (String) args[0];
                        System.out.println("[Feign proxy] GET http://billing-service/invoices/" + id);
                        return billingBackend.get(id); // stands in for the real HTTP call + deserialization
                    }
                    throw new UnsupportedOperationException();
                });
    }

    public static void main(String[] args) {
        BillingClient billingClient = createClient();
        Invoice invoice = billingClient.getInvoice("42"); // reads exactly like calling a plain interface method
        System.out.println("received: " + invoice);
    }
}
```

How to run: `java FeignClientLevel2.java`

`Proxy.newProxyInstance` generates a runtime implementation of `BillingClient` whose `getInvoice` implementation is the lambda — every call to `billingClient.getInvoice(id)` actually runs through that lambda, which is exactly the mechanism (a much more elaborate version of it) Feign itself uses to turn an annotated interface into working code at application startup.

### Level 3 — Advanced

Extend the proxy to handle multiple methods with different HTTP semantics (`GET` and `POST`), modeling a more realistic `BillingClient` with both a query and a create operation.

```java
import java.lang.reflect.*;
import java.util.*;

public class FeignClientLevel3 {
    record Invoice(String id, double amount) {}

    interface BillingClient {
        Invoice getInvoice(String id);       // @GetMapping("/invoices/{id}")
        Invoice createInvoice(Invoice draft); // @PostMapping("/invoices")
    }

    static Map<String, Invoice> billingBackend = new HashMap<>(Map.of("42", new Invoice("42", 199.99)));
    static int nextId = 43;

    static BillingClient createClient() {
        return (BillingClient) Proxy.newProxyInstance(
                FeignClientLevel3.class.getClassLoader(),
                new Class<?>[]{BillingClient.class},
                (proxy, method, args) -> {
                    return switch (method.getName()) {
                        case "getInvoice" -> {
                            String id = (String) args[0];
                            System.out.println("[Feign proxy] GET http://billing-service/invoices/" + id);
                            yield billingBackend.get(id);
                        }
                        case "createInvoice" -> {
                            Invoice draft = (Invoice) args[0];
                            String newId = String.valueOf(nextId++);
                            Invoice created = new Invoice(newId, draft.amount());
                            System.out.println("[Feign proxy] POST http://billing-service/invoices  body=" + draft);
                            billingBackend.put(newId, created);
                            yield created;
                        }
                        default -> throw new UnsupportedOperationException(method.getName());
                    };
                });
    }

    public static void main(String[] args) {
        BillingClient billingClient = createClient();

        Invoice existing = billingClient.getInvoice("42");
        System.out.println("fetched: " + existing);

        Invoice created = billingClient.createInvoice(new Invoice(null, 49.50));
        System.out.println("created: " + created);

        Invoice fetchedAfterCreate = billingClient.getInvoice(created.id());
        System.out.println("fetched newly created: " + fetchedAfterCreate);
    }
}
```

How to run: `java FeignClientLevel3.java`

The proxy's `switch` on `method.getName()` dispatches to different simulated HTTP semantics depending on which interface method was called — `getInvoice` performs a read against the existing backend map, while `createInvoice` performs a write, assigning a new ID and storing it. Both calls read identically at the call site (`billingClient.methodName(...)`), even though one maps to a `GET` and the other to a `POST` — exactly the abstraction `@FeignClient` provides over real HTTP semantics.

## 6. Walkthrough

Trace the three calls in Level 3.

1. `billingClient.getInvoice("42")` runs first — the proxy's invocation handler receives `method.getName() == "getInvoice"`, extracts `id = "42"` from `args[0]`, prints the simulated `GET` request line, and looks up `billingBackend.get("42")`, returning the existing `Invoice("42", 199.99)`. This models a Feign `@GetMapping("/invoices/{id})")` call resolving `{id}` from the method's `@PathVariable`-annotated parameter, sending the request, and deserializing the JSON response body into the method's declared return type.
2. `billingClient.createInvoice(new Invoice(null, 49.50))` runs next — the handler matches `"createInvoice"`, extracts the `draft` argument, assigns it a new ID (`"43"`), constructs the `created` invoice, prints the simulated `POST` request line including the request body, stores it in `billingBackend`, and returns it. This models a Feign `@PostMapping` method serializing its `@RequestBody`-annotated parameter into the outgoing request's JSON body, and deserializing the response (here, presumably the server's canonical representation of the newly created resource, including its assigned ID) back into the return value.
3. `billingClient.getInvoice(created.id())` runs last, using the ID (`"43"`) returned from the previous create call — it performs the same `getInvoice` path as step 1, but this time finds the just-created invoice in `billingBackend`, confirming the two calls (a write followed by a read of what was just written) correctly interacted with the same shared backend state.

```
getInvoice("42")              -> GET  /invoices/42        -> Invoice(42, 199.99)   (existing)
createInvoice(Invoice(null, 49.50)) -> POST /invoices      -> Invoice(43, 49.50)    (newly created, ID assigned)
getInvoice("43")              -> GET  /invoices/43         -> Invoice(43, 49.50)    (confirms the write)
```

## 7. Gotchas & takeaways

> **Gotcha:** because Feign generates its implementation from the interface's annotations at startup, a mismatch between the interface's declared method signature and the actual backend API's contract (a wrong path variable name, a missing `@RequestBody`, a return type that doesn't match the response JSON's shape) typically isn't caught until the method is actually called at runtime, not at compile time — the interface gives call-site type safety, but not full contract verification against the real backend without additional tooling (contract testing, integration tests).

- `@FeignClient` turns repetitive manual HTTP client boilerplate into a declared interface, generating the actual request-building, load-balancing, and (de)serialization logic automatically.
- The interface method signature is the entire contract — parameter annotations (`@PathVariable`, `@RequestBody`, `@RequestParam`) map directly to how the request is constructed, mirroring the same annotations used on the *server* side in a Spring MVC/WebFlux controller.
- Feign clients integrate with LoadBalancer automatically (the `name` in `@FeignClient(name = "billing-service")` is resolved exactly like `@LoadBalanced` client calls) — everything covered in the earlier LoadBalancer cards (algorithms, zone/hint filtering, retry) applies transparently to Feign calls too.
- Because the generated implementation is just another Spring bean, Feign clients can be mocked or stubbed in tests exactly like any other injected interface — a real testability advantage over hand-rolled `RestTemplate` call sites scattered through application code.
