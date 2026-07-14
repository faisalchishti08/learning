---
card: microservices
gi: 564
slug: spring-petclinic-microservices-reference
title: "Spring PetClinic microservices reference"
---

## 1. What it is

**Spring PetClinic Microservices** is Spring's own official reference implementation, maintained alongside the classic single-module PetClinic sample, demonstrating how a simple veterinary-clinic management application (owners, pets, vets, visits) can be restructured as a small fleet of independently deployable Spring Cloud services — a Config Server, a Discovery Server, an API Gateway, and separate Customers/Vets/Visits services — wired together using exactly the Spring Cloud modules discussed throughout this section. It's valuable specifically because it's a complete, runnable, officially-maintained example of the whole ecosystem assembled correctly, rather than isolated snippets demonstrating one module at a time.

## 2. Why & when

You study the PetClinic microservices reference specifically when you want to see the full ecosystem assembled correctly, in a real, runnable codebase, rather than piecing it together purely from documentation:

- **Individual module documentation shows how to use one piece in isolation** — a Config Server here, a Feign client there — but doesn't necessarily show how a real, multi-service application's `pom.xml` dependencies, `application.yml` configuration, and service boundaries are actually structured together, consistently, across an entire small system.
- **It's officially maintained by the Spring team**, meaning it reflects current, recommended practice for wiring these modules together — as Spring Cloud evolves (the Sleuth-to-Micrometer-Tracing migration, for instance), the reference implementation is updated accordingly, making it a reasonably reliable signal of "this is how these pieces are meant to fit together right now," rather than a potentially-outdated blog post or tutorial.
- **Its deliberately simple domain (pets, owners, vets) keeps the business logic itself trivial**, so studying the codebase's *structure* — how services are split, how they discover and call each other, how configuration and resiliency are wired in — isn't obscured by complex business rules; the interesting parts of the reference are entirely architectural, not domain-specific.
- **You reach for it when starting a new Spring Cloud-based project and want a proven starting structure to adapt**, or when you want to verify your own project's module wiring against a known-correct reference, rather than guessing at the "right" way to combine Config Server, Discovery, Gateway, and resiliency patterns from scratch.

## 3. Core concept

Think of the PetClinic microservices reference as a furniture assembly instruction booklet that shows the *complete*, finished piece of furniture fully assembled, with every joint and connection point visible in context — versus separate diagrams for "how to attach a hinge" and "how a drawer slide works" shown in isolation, which don't reveal how those individual pieces actually come together into one working item. The reference's value isn't in teaching any single Spring Cloud module better than its own dedicated documentation would; it's in showing the *complete, assembled result*, letting you see every module's role in the context of the others, exactly as [the previous topic's composed request walkthrough](0563-putting-it-together-gateway-discovery-config-resiliency-trac.md) discussed conceptually — here, made concrete in a real, runnable codebase.

Concretely, the reference application's structure includes:

1. **A Config Server module**, serving centralized configuration for every other service, backed by a Git-style configuration repository (bundled locally in the reference for ease of running, though the same principle applies to a real remote Git repo).
2. **A Discovery Server module** (Eureka-based), which every other service registers with at startup, and which the API Gateway and inter-service Feign clients use to resolve logical service names to real instances.
3. **An API Gateway module**, built on Spring Cloud Gateway, routing external requests to the appropriate backend service (customers, vets, visits) based on path, exactly mirroring the [edge routing](0543-spring-cloud-gateway-edge-routing.md) pattern discussed earlier.
4. **Separate Customers, Vets, and Visits service modules**, each an independently deployable Spring Boot application with its own data, communicating with each other (where needed) via declarative Feign clients, and each instrumented with Micrometer Tracing so a request spanning multiple services can be traced end to end.
5. **An Admin Server module** (Spring Boot Admin, a related but separate project) providing a dashboard over the running fleet's health and metrics, complementing what Config Server, Discovery, and tracing already provide individually.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The PetClinic microservices reference assembles a Config Server, Discovery Server, API Gateway, and separate Customers/Vets/Visits services into one coherent, runnable system">
  <rect x="20" y="20" width="150" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="95" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Config Server</text>
  <rect x="190" y="20" width="150" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="265" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Discovery Server</text>

  <rect x="20" y="80" width="620" height="34" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="101" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">API Gateway</text>

  <rect x="40" y="140" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="130" y="165" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Customers Service</text>
  <rect x="240" y="140" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="165" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Vets Service</text>
  <rect x="440" y="140" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="530" y="165" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Visits Service</text>
</svg>

Config and Discovery underpin every other service; the Gateway fronts three independently deployable business services.

## 5. Runnable example

Scenario: reconstructing the essential shape of the PetClinic reference's owner-lookup flow. We start with a simplified, single-service version of "look up an owner," extend it to split Customers and Visits into separate services communicating via Feign, then handle the hard case: routing both through a gateway with discovery and a fallback for a temporarily unavailable Visits service.

### Level 1 — Basic

```java
// File: MonolithOwnerLookup.java -- models the SIMPLE, single-module
// starting point: one service handles BOTH owner and visit data directly.
import java.util.*;

public class MonolithOwnerLookup {
    static Map<String, String> owners = Map.of("1", "George Franklin");
    static Map<String, List<String>> visitsByOwner = Map.of("1", List.of("2026-01-05: Rabies shot", "2026-03-10: Check-up"));

    static String getOwnerWithVisits(String ownerId) {
        String ownerName = owners.get(ownerId);
        List<String> visits = visitsByOwner.get(ownerId);
        return "{\"owner\":\"" + ownerName + "\",\"visits\":" + visits + "}";
    }

    public static void main(String[] args) {
        System.out.println(getOwnerWithVisits("1"));
        System.out.println("ONE service, direct in-process access to both owner and visit data.");
    }
}
```

How to run: `java MonolithOwnerLookup.java`

Both owner and visit data live in the same process, accessed directly — this is the starting point every microservices reference (including the classic single-module PetClinic) begins from, before any service-splitting decisions are made.

### Level 2 — Intermediate

```java
// File: SplitServicesWithFeign.java -- models SPLITTING owner and visit
// data into SEPARATE services, communicating via a DECLARATIVE client
// interface (the Feign pattern), mirroring the real reference's structure.
import java.util.*;

public class SplitServicesWithFeign {
    // --- Visits Service (a separate deployable in the real reference) ---
    static class VisitsService {
        Map<String, List<String>> visitsByOwner = Map.of("1", List.of("2026-01-05: Rabies shot", "2026-03-10: Check-up"));
        List<String> getVisits(String ownerId) { return visitsByOwner.getOrDefault(ownerId, List.of()); }
    }

    // --- a Feign-style declarative client interface, as Customers Service would use to call Visits ---
    interface VisitsClient { List<String> getVisits(String ownerId); }

    // --- Customers Service (a separate deployable, calling Visits via the client above) ---
    static class CustomersService {
        Map<String, String> owners = Map.of("1", "George Franklin");
        VisitsClient visitsClient;
        CustomersService(VisitsClient visitsClient) { this.visitsClient = visitsClient; }

        String getOwnerWithVisits(String ownerId) {
            String ownerName = owners.get(ownerId);
            List<String> visits = visitsClient.getVisits(ownerId); // calls the OTHER service, not local data
            return "{\"owner\":\"" + ownerName + "\",\"visits\":" + visits + "}";
        }
    }

    public static void main(String[] args) {
        VisitsService visitsService = new VisitsService();
        VisitsClient client = visitsService::getVisits; // stands in for a real Feign-generated implementation
        CustomersService customersService = new CustomersService(client);

        System.out.println(customersService.getOwnerWithVisits("1"));
        System.out.println("TWO separate services now -- Customers calls Visits through a declarative client, not direct data access.");
    }
}
```

How to run: `java SplitServicesWithFeign.java`

`CustomersService` no longer has direct access to visit data — it calls `visitsClient.getVisits(ownerId)`, modeling exactly how the real PetClinic reference's Customers Service calls the Visits Service through a declarative Feign client, resolved via discovery in the actual application, rather than accessing another service's data directly.

### Level 3 — Advanced

```java
// File: GatewayDiscoveryFallbackAssembled.java -- the FULL assembled
// shape: a Gateway routes to Customers Service (resolved via discovery),
// which calls Visits Service through a CIRCUIT-BREAKER-PROTECTED client
// with a FALLBACK, mirroring the reference application's resiliency layer.
import java.util.*;
import java.util.function.Function;

public class GatewayDiscoveryFallbackAssembled {
    static Map<String, String> owners = Map.of("1", "George Franklin");
    static boolean visitsServiceHealthy = false; // simulating Visits Service being temporarily down

    static List<String> callVisitsServiceProtected(String ownerId) {
        if (!visitsServiceHealthy) {
            System.out.println("[CircuitBreaker] Visits Service unavailable -- using FALLBACK, empty visit list");
            return List.of(); // fallback: degrade gracefully instead of failing the whole owner lookup
        }
        return List.of("2026-01-05: Rabies shot");
    }

    static String customersServiceHandle(String ownerId) {
        String ownerName = owners.get(ownerId);
        List<String> visits = callVisitsServiceProtected(ownerId);
        return "{\"owner\":\"" + ownerName + "\",\"visits\":" + visits + "}";
    }

    static String apiGatewayRoute(String path) {
        String ownerId = path.substring(path.lastIndexOf('/') + 1);
        System.out.println("[Gateway] routing " + path + " -> Customers Service (resolved via discovery)");
        return customersServiceHandle(ownerId);
    }

    public static void main(String[] args) {
        System.out.println(apiGatewayRoute("/api/customer/owners/1"));
        System.out.println("Owner lookup SUCCEEDS even with Visits Service down -- gracefully degraded, not failed entirely.");
    }
}
```

How to run: `java GatewayDiscoveryFallbackAssembled.java`

`apiGatewayRoute` models the API Gateway routing an external request to Customers Service (resolved via discovery in the real application); `customersServiceHandle` calls Visits Service through `callVisitsServiceProtected`, which, because `visitsServiceHealthy` is simulated `false`, returns the fallback empty list rather than failing the request entirely — the owner's name is still correctly returned even though visit history is temporarily unavailable, exactly the graceful-degradation behavior the real reference application's resiliency configuration provides.

## 6. Walkthrough

Trace `GatewayDiscoveryFallbackAssembled.main` end to end, mapping each step onto its real PetClinic reference counterpart:

1. **`apiGatewayRoute("/api/customer/owners/1")` is called.** In the real reference application, this corresponds to a request arriving at the API Gateway module, matching a route predicate for `/api/customer/**`, and being forwarded (via discovery-resolved load balancing) to a running Customers Service instance.
2. **`customersServiceHandle("1")` is called**, corresponding to the Customers Service's actual controller method handling the forwarded request.
3. **`owners.get("1")` retrieves `"George Franklin"`** — in the real reference, this is a database lookup against the Customers Service's own data store, entirely local to that service.
4. **`callVisitsServiceProtected("1")` is called**, corresponding to the real reference's Feign client call to the Visits Service, wrapped with a circuit breaker (in the real application, typically Resilience4j via Spring Cloud Circuit Breaker, as discussed earlier in this section).
5. **Because `visitsServiceHealthy` is `false`** (simulating the real Visits Service being down or its circuit breaker already open from prior failures), the fallback path executes, returning an empty list rather than propagating a failure.
6. **`customersServiceHandle` builds its response using the real owner name and the (empty, fallback) visits list**, and this response flows back up through the simulated Gateway to the original caller — the overall request succeeds with partial, gracefully-degraded data, rather than failing outright because one dependency (Visits) was unavailable.

In the real, fully-assembled PetClinic microservices reference application, this exact resiliency behavior is one of its deliberately demonstrated features: killing the Visits Service instance while the application is running and observing that owner lookups still succeed (showing an empty or cached visit history) rather than failing entirely — a hands-on, runnable demonstration of exactly the composed resiliency pattern discussed conceptually in [the previous topic](0563-putting-it-together-gateway-discovery-config-resiliency-trac.md).

## 7. Gotchas & takeaways

> **Gotcha:** because the reference application is intentionally simple (a trivial pet-clinic domain), it's tempting to assume its architecture scales unchanged to a much larger, more complex real system — in practice, the reference demonstrates the *wiring pattern* correctly, but a real system with dozens of services, much higher traffic, and more complex data relationships will need additional considerations (more sophisticated service boundaries, more nuanced resiliency tuning, more elaborate observability) beyond what a three-service reference application needs to illustrate its point.

- The PetClinic microservices reference is valuable specifically for showing how Config Server, Discovery, Gateway, resiliency, and tracing fit together in one real, runnable codebase — not for teaching any single module better than its own dedicated documentation.
- Being officially maintained by the Spring team makes it a reasonably current signal of recommended practice as the ecosystem evolves, rather than a potentially stale third-party tutorial.
- Its deliberately trivial domain keeps the architecture, not the business logic, as the interesting part to study — use it as a structural reference, adapting the wiring pattern to your own domain.
- Don't assume a simple reference application's architecture scales unchanged to a much larger real system — treat it as a correct starting pattern to adapt, not a finished blueprint for arbitrary scale.
