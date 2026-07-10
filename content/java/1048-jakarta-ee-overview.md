---
card: java
gi: 1048
slug: jakarta-ee-overview
title: Jakarta EE overview
---

## 1. What it is

Jakarta EE (formerly Java EE, before Oracle transferred it to the Eclipse Foundation) is a collection of specifications for enterprise Java — standardized APIs for web services (Jakarta RESTful Web Services, formerly JAX-RS), persistence (Jakarta Persistence, the JPA specification covered in [JPA / Hibernate ORM](1045-jpa-hibernate-orm.md)), dependency injection (Jakarta CDI, Contexts and Dependency Injection), and more. Being a *specification* means multiple vendors provide compatible implementations — WildFly, Payara, and Open Liberty are all **application servers** that implement the full Jakarta EE specification set, and code written against the standard APIs can, in principle, run on any of them without changes.

## 2. Why & when

Before standardization, enterprise Java frameworks were largely vendor-specific — code written for one application server often didn't run on another without significant rework, locking organizations into whichever vendor they initially chose. Jakarta EE's specifications exist so that application code depends only on standard interfaces (`jakarta.persistence.EntityManager`, `jakarta.ws.rs.GET`) rather than any specific vendor's implementation classes, meaning the same application code can, in principle, be deployed to WildFly, Payara, or any other compliant server, and a team isn't permanently tied to one vendor's specific runtime.

Jakarta EE (deployed to a full application server, or via a lighter runtime like Open Liberty or Payara Micro) suits organizations wanting standardized, vendor-neutral APIs and are willing to deploy to (or already operate) a compliant application server. Spring Boot has become the more common choice for many new applications specifically because of its auto-configuration and embedded-server simplicity (see [Spring Boot](1047-spring-boot.md)) — though it's worth noting Spring itself implements and builds on several Jakarta EE specifications internally (JPA, Bean Validation) rather than replacing them entirely; the choice between "full Jakarta EE on an application server" and "Spring Boot" is largely about deployment model and ecosystem preference, not fundamentally different underlying technology for persistence or dependency injection.

## 3. Core concept

```java
// Jakarta RESTful Web Services (JAX-RS): a standard, vendor-neutral annotation
// for defining a REST endpoint -- runs on ANY compliant Jakarta EE server.
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

@Path("/hello")
public class GreetingResource {
    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String hello() {
        return "Hello from Jakarta EE!";
    }
}

// Jakarta CDI: standard dependency injection, analogous to Spring's @Component/@Autowired
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

interface PaymentGateway { boolean charge(double amount); }

@ApplicationScoped
class StripeGateway implements PaymentGateway {
    public boolean charge(double amount) { return true; }
}

@ApplicationScoped
class OrderService {
    @Inject PaymentGateway gateway; // CDI container injects this automatically
    void placeOrder(double amount) { gateway.charge(amount); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same application code written against standard Jakarta EE APIs being deployable to any compliant application server -- WildFly, Payara, or Open Liberty -- without code changes">
  <rect x="30" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">App code (standard APIs)</text>

  <rect x="280" y="10" width="110" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="335" y="31" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">WildFly</text>
  <rect x="280" y="70" width="110" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="335" y="91" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Payara</text>
  <rect x="280" y="130" width="110" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="335" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Open Liberty</text>

  <line x1="210" y1="80" x2="280" y2="27" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="210" y1="85" x2="280" y2="87" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="210" y1="90" x2="280" y2="147" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same code, written against standard APIs, deploys unchanged to any compliant Jakarta EE server.

## 5. Runnable example

Scenario: a small REST resource with a dependency, evolving from vendor-specific coupling into fully standard Jakarta EE APIs deployable to any compliant server.

### Level 1 — Basic

```java
// File: HardcodedResource.java -- imagines coupling directly to a specific
// vendor's proprietary API instead of a standard one (illustrative, not runnable
// as-is against a real vendor library, since this demonstrates the PROBLEM).
public class HardcodedResource {
    // Suppose this imported "com.somevendor.rest.Endpoint" instead of a
    // standard annotation -- this code would ONLY run on that one vendor's server.
    public String hello() {
        return "Hello, tightly coupled to one vendor!";
    }

    public static void main(String[] args) {
        System.out.println(new HardcodedResource().hello());
    }
}
```

**How to run:** save as `HardcodedResource.java`, then `javac HardcodedResource.java && java HardcodedResource` (JDK 17+).

Expected output:
```
Hello, tightly coupled to one vendor!
```

This illustrates the pre-standardization problem conceptually: if this class depended on annotations and interfaces specific to one vendor's proprietary API (rather than a standard specification), deploying the same code to a different vendor's server would require rewriting those dependencies entirely.

### Level 2 — Intermediate

```java
// File: src/main/java/com/example/GreetingResource.java
package com.example;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

// A STANDARD Jakarta RESTful Web Services (JAX-RS) resource -- these annotations
// come from the jakarta.ws.rs specification package, not any specific vendor.
@Path("/hello")
public class GreetingResource {
    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String hello() {
        return "Hello from a standard Jakarta EE resource!";
    }
}
```

```java
// File: src/main/java/com/example/RestActivator.java
package com.example;

import jakarta.ws.rs.ApplicationPath;
import jakarta.ws.rs.core.Application;

@ApplicationPath("/api")
public class RestActivator extends Application {
    // Activates JAX-RS scanning for @Path-annotated resources under /api
}
```

**How to run:** package as a WAR and deploy to any Jakarta EE 10-compliant server (WildFly, Payara, or Open Liberty), then request `http://localhost:8080/<app-name>/api/hello`.

Expected output (HTTP response body):
```
Hello from a standard Jakarta EE resource!
```

The real-world concern added: `GreetingResource` depends only on `jakarta.ws.rs` annotations — a genuine Jakarta EE specification package, not any specific vendor's implementation classes. This exact same code, unchanged, is deployable to WildFly, Payara, or Open Liberty, since all three provide compliant implementations of the same JAX-RS specification.

### Level 3 — Advanced

```java
// File: src/main/java/com/example/PaymentGateway.java
package com.example;

public interface PaymentGateway {
    boolean charge(double amount);
}
```

```java
// File: src/main/java/com/example/StripeGateway.java
package com.example;

import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped // standard Jakarta CDI: application-wide singleton scope
public class StripeGateway implements PaymentGateway {
    public boolean charge(double amount) {
        System.out.println("Charging $" + amount + " via Stripe (Jakarta EE / CDI)");
        return true;
    }
}
```

```java
// File: src/main/java/com/example/OrderResource.java
package com.example;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

@Path("/order")
public class OrderResource {
    // Standard Jakarta CDI dependency injection -- the container supplies
    // a StripeGateway instance automatically, analogous to Spring's @Autowired.
    @Inject
    PaymentGateway gateway;

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String placeOrder() {
        boolean success = gateway.charge(19.99);
        return success ? "Order placed successfully!" : "Order failed.";
    }
}
```

**How to run:** package as a WAR (with the `RestActivator` class from Level 2 also included) and deploy to any Jakarta EE 10-compliant server, then request `http://localhost:8080/<app-name>/api/order`.

Expected output (HTTP response body, plus a server-log line from the `System.out.println`):
```
Order placed successfully!
```

Server log (from `StripeGateway.charge`):
```
Charging $19.99 via Stripe (Jakarta EE / CDI)
```

The production-flavored hard case: `OrderResource` depends on the `PaymentGateway` interface via standard `@Inject` (Jakarta CDI), with the container supplying a `StripeGateway` instance automatically — this dependency-injection mechanism, along with the REST endpoint annotations, are both standard Jakarta EE specifications, meaning this entire application (unchanged) could be redeployed to a different compliant server without any code modification.

## 6. Walkthrough

Tracing what happens when a request hits `GET /api/order` on a running Jakarta EE server:

1. The application server's request-routing layer (implementing the JAX-RS specification) receives the request and, based on `RestActivator`'s `@ApplicationPath("/api")` combined with `OrderResource`'s `@Path("/order")`, determines this request should be dispatched to `OrderResource`'s `@GET`-annotated method, `placeOrder`.
2. Before invoking `placeOrder`, the server's CDI container ensures `OrderResource` itself is instantiated (if not already) and that its `@Inject`-annotated field, `gateway`, is populated — the container looks up which bean satisfies the `PaymentGateway` type, finds `StripeGateway` (the only implementation, annotated `@ApplicationScoped`), and either reuses an existing application-wide instance or constructs one, assigning it to `gateway`.
3. `placeOrder()` executes: `gateway.charge(19.99)` dispatches to `StripeGateway.charge`, which prints `"Charging $19.99 via Stripe (Jakarta EE / CDI)"` to the server's log output and returns `true`.
4. Back in `placeOrder`, `success` is `true`, so the method returns the string `"Order placed successfully!"`.
5. Because the method is annotated `@Produces(MediaType.TEXT_PLAIN)`, the JAX-RS runtime writes this returned string directly as the HTTP response body, with the `Content-Type` header set to `text/plain`.
6. The client (a browser, `curl`, or any HTTP client) receives `"Order placed successfully!"` as the response body — and critically, every piece of this flow (routing, dependency injection, response serialization) was driven entirely by standard `jakarta.*` annotations, meaning the exact same WAR file, unmodified, could be deployed to a completely different compliant application server and behave identically.

## 7. Gotchas & takeaways

> **Gotcha:** "compliant with the specification" doesn't mean "behaviorally identical in every edge case" — different Jakarta EE server implementations can have subtly different default behaviors, configuration mechanisms, or performance characteristics even while both correctly implementing the same standard API surface; portability across servers is strong for straightforward usage but isn't an absolute guarantee for every corner case.

- Jakarta EE (formerly Java EE) is a set of vendor-neutral specifications for enterprise Java — REST APIs (JAX-RS), persistence (JPA), and dependency injection (CDI) among them.
- Being a specification means multiple compliant application servers (WildFly, Payara, Open Liberty) can run the same application code, since it depends only on standard `jakarta.*` interfaces and annotations, not vendor-specific implementation classes.
- Jakarta CDI's `@Inject`/`@ApplicationScoped` play a role directly analogous to Spring's `@Autowired`/`@Component` — both are dependency-injection mechanisms, just standardized differently.
- Spring Boot has become the more common choice for many new applications due to its auto-configuration and embedded-server simplicity (see [Spring Boot](1047-spring-boot.md)), but Spring itself builds on several of the same underlying Jakarta EE specifications (JPA, Bean Validation) rather than replacing them.
- The choice between full Jakarta EE (on an application server) and Spring Boot is largely about deployment model, ecosystem, and team preference — not a fundamentally different underlying approach to persistence or dependency injection.
- Portability across compliant servers is strong for standard usage patterns but isn't an absolute guarantee for every configuration detail or edge case — always verify against the specific target server when portability genuinely matters.
