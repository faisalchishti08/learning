---
card: spring-cloud
gi: 1
slug: what-spring-cloud-is-the-12-factor-cloud-native-context
title: "What Spring Cloud is & the 12-factor / cloud-native context"
---

## 1. What it is

Spring Cloud is a family of projects that add distributed-systems infrastructure — service discovery, configuration management, load balancing, circuit breaking, distributed tracing — on top of Spring Boot. Where Spring Boot makes it easy to build one well-configured application, Spring Cloud makes it easy to build *many* of them that need to find each other, share configuration, and stay resilient when any one of them fails.

```java
@SpringBootApplication
@EnableDiscoveryClient // Spring Cloud: register with, and discover, other services
class OrderServiceApplication {
    public static void main(String[] args) { SpringApplication.run(OrderServiceApplication.class, args); }
}
```

## 2. Why & when

This card opens a new project in this course: Spring Cloud, covering the tools for building distributed, cloud-native systems out of many independently deployable Spring Boot applications — the same microservices architecture whose broader principles a later card in this course covers, but here focused specifically on Spring's toolkit for it. The "12-factor app" methodology — externalized config, stateless processes, disposability, treating backing services as attached resources — is the design philosophy Spring Cloud's components are built around; each Spring Cloud module addresses one specific factor or cross-cutting concern that shows up once an application stops being the only one of its kind running.

Reach for Spring Cloud when:

- An application is one of several services that need to locate each other at runtime, without hardcoding hostnames and ports — service discovery.
- Configuration needs to be centralized and changeable without redeploying every service that depends on it — externalized, dynamic configuration.
- Calls between services need resilience patterns — retries, circuit breakers, load balancing — that a single-application Spring Boot setup never had to think about.

## 3. Core concept

```
 Single Spring Boot app:                    Distributed Spring Cloud system:

 [ Order Service ]                          [ Order Service ] <--discovery--> [ Registry ]
   - owns its own config                          |                                ^
   - talks to its own database                    v                                |
                                              [ Payment Service ] <--discovery------+
                                                    |
                                              [ Inventory Service ]

 Each service still IS a Spring Boot app -- Spring Cloud adds the connective tissue between them.
```

Spring Cloud doesn't replace Spring Boot — every service in a Spring Cloud system is still a normal Spring Boot application, with Spring Cloud libraries added for the concerns that only exist once there's more than one of them.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three Spring Boot services connect to a shared registry and config server, forming a Spring Cloud system">
  <rect x="20" y="20" width="150" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Order Service</text>

  <rect x="20" y="90" width="150" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="117" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Payment Service</text>

  <rect x="20" y="130" width="0" height="0"/>
  <rect x="20" y="145" width="150" height="35" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="167" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Inventory Service</text>

  <rect x="420" y="55" width="200" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service Registry</text>

  <rect x="420" y="120" width="200" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="150" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Config Server</text>

  <line x1="170" y1="42" x2="410" y2="70" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="170" y1="112" x2="410" y2="145" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="170" y1="162" x2="410" y2="150" stroke="#8b949e" stroke-width="1.2"/>
</svg>

Each independently deployable Spring Boot service connects to shared cross-cutting infrastructure — a registry and config server — rather than to each other directly.

## 5. Runnable example

The scenario: an order service that needs to call a payment service, evolving from a hardcoded connection (works for one instance, breaks the moment there's more than one), to a discovery-based lookup honoring the "don't hardcode locations" 12-factor principle, to a resilient call incorporating a basic retry — the shape of concern Spring Cloud modules exist to address, built here from first principles before the later cards introduce the real Spring Cloud components.

### Level 1 — Basic

Show the hardcoded-hostname baseline — brittle the moment a service has more than one instance or moves.

```java
import java.util.*;

public class SpringCloudIntroLevel1 {
    public static void main(String[] args) {
        OrderService orderService = new OrderService("payment-service.internal:8081"); // hardcoded, single instance
        System.out.println(orderService.chargeCustomer("c1", 49.99));
    }
}

class OrderService {
    private final String paymentServiceAddress; // fixed at construction time -- can't adapt to change
    OrderService(String paymentServiceAddress) { this.paymentServiceAddress = paymentServiceAddress; }

    String chargeCustomer(String customerId, double amount) {
        // In reality: an HTTP call to paymentServiceAddress. If it moves, scales, or fails over, this breaks.
        return "Charged " + customerId + " $" + amount + " via " + paymentServiceAddress;
    }
}
```

How to run: `java SpringCloudIntroLevel1.java`

`paymentServiceAddress` is fixed at construction — if the payment service is redeployed to a new host, or scaled to three instances behind a load balancer, this hardcoded value silently becomes wrong, with no mechanism to adapt.

### Level 2 — Intermediate

Add a discovery-style lookup: instead of a hardcoded address, the order service asks a registry for the payment service's *current* location(s) at call time.

```java
import java.util.*;

public class SpringCloudIntroLevel2 {
    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        registry.register("payment-service", "10.0.1.5:8081");
        registry.register("payment-service", "10.0.1.6:8081"); // a second instance -- scaled out

        OrderService orderService = new OrderService(registry);
        System.out.println(orderService.chargeCustomer("c1", 49.99));
        System.out.println(orderService.chargeCustomer("c2", 19.99)); // may resolve to a DIFFERENT instance
    }
}

class ServiceRegistry {
    private final Map<String, List<String>> instances = new HashMap<>();
    void register(String serviceName, String address) {
        instances.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(address);
    }
    // Stands in for a DiscoveryClient looking up current instances of a named service.
    List<String> instancesOf(String serviceName) { return instances.getOrDefault(serviceName, List.of()); }
}

class OrderService {
    private final ServiceRegistry registry;
    private int roundRobinIndex = 0;
    OrderService(ServiceRegistry registry) { this.registry = registry; }

    String chargeCustomer(String customerId, double amount) {
        List<String> instances = registry.instancesOf("payment-service"); // looked up FRESH, every call
        String address = instances.get(roundRobinIndex % instances.size());
        roundRobinIndex++;
        return "Charged " + customerId + " $" + amount + " via " + address;
    }
}
```

How to run: `java SpringCloudIntroLevel2.java`

`chargeCustomer` never hardcodes an address — it asks `registry.instancesOf(...)` fresh on every call, and picks between whichever instances currently happen to be registered, so scaling the payment service up or down doesn't require any change to `OrderService` at all.

### Level 3 — Advanced

Add basic resilience — retrying against a different instance if the first one fails — modeling the kind of cross-cutting reliability concern Spring Cloud's resilience components (covered in later cards) address more thoroughly.

```java
import java.util.*;

public class SpringCloudIntroLevel3 {
    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();
        registry.register("payment-service", "10.0.1.5:8081"); // this one will simulate a failure
        registry.register("payment-service", "10.0.1.6:8081"); // this one will succeed

        FaultyPaymentClient client = new FaultyPaymentClient(Set.of("10.0.1.5:8081")); // fails for this address
        OrderService orderService = new OrderService(registry, client);
        System.out.println(orderService.chargeCustomer("c1", 49.99));
    }
}

class ServiceRegistry {
    private final Map<String, List<String>> instances = new HashMap<>();
    void register(String serviceName, String address) {
        instances.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(address);
    }
    List<String> instancesOf(String serviceName) { return instances.getOrDefault(serviceName, List.of()); }
}

// Stands in for an unreliable network call to a specific service instance.
class FaultyPaymentClient {
    private final Set<String> failingAddresses;
    FaultyPaymentClient(Set<String> failingAddresses) { this.failingAddresses = failingAddresses; }
    String charge(String address, String customerId, double amount) {
        if (failingAddresses.contains(address)) throw new RuntimeException("connection refused: " + address);
        return "Charged " + customerId + " $" + amount + " via " + address;
    }
}

class OrderService {
    private final ServiceRegistry registry;
    private final FaultyPaymentClient client;
    OrderService(ServiceRegistry registry, FaultyPaymentClient client) { this.registry = registry; this.client = client; }

    String chargeCustomer(String customerId, double amount) {
        List<String> instances = registry.instancesOf("payment-service");
        RuntimeException lastFailure = null;
        for (String address : instances) { // retry across instances -- basic resilience
            try {
                return client.charge(address, customerId, amount);
            } catch (RuntimeException e) {
                System.out.println("Instance " + address + " failed, trying next: " + e.getMessage());
                lastFailure = e;
            }
        }
        throw new IllegalStateException("all instances failed", lastFailure);
    }
}
```

How to run: `java SpringCloudIntroLevel3.java`

`chargeCustomer` loops over every discovered instance, catching a failure from one and trying the next, rather than propagating the very first failure straight to the caller — this is the conceptual seed of what Spring Cloud's load balancer and resilience libraries (covered in dedicated later cards) provide as production-hardened, configurable behavior.

## 6. Walkthrough

Execution starts in `main` for Level 3. Two payment-service instances are registered; the client is configured to fail specifically for `10.0.1.5:8081`. `orderService.chargeCustomer("c1", 49.99)` runs.

The `for` loop iterates `instances` in registration order, trying `10.0.1.5:8081` first. `client.charge(...)` throws, since that address is in `failingAddresses` — the `catch` block logs the failure and the loop continues rather than propagating the exception:

```
Instance 10.0.1.5:8081 failed, trying next: connection refused: 10.0.1.5:8081
```

The loop's next iteration tries `10.0.1.6:8081`, which isn't in `failingAddresses`, so `client.charge` succeeds and returns immediately from `chargeCustomer`:

```
Charged c1 $49.99 via 10.0.1.6:8081
```

This entire flow — discover instances, try one, retry against another on failure — is the conceptual shape every later card in this Spring Cloud section formalizes: `DiscoveryClient` for the lookup (a later card this section), a load balancer for the instance selection strategy, and a circuit breaker for smarter failure handling than a simple linear retry. This card exists to establish *why* those pieces are needed before introducing each one individually.

## 7. Gotchas & takeaways

> Gotcha: hand-rolling service discovery and retry logic (as this card's examples do, for teaching purposes) is exactly what *not* to do in a real application — every one of these concerns has a battle-tested Spring Cloud component, covered in this section's later cards, handling edge cases (partial registry updates, exponential backoff, circuit-breaking after repeated failures) that a simple loop like Level 3's does not.

> Gotcha: Spring Cloud is a family of separate projects (Spring Cloud Netflix, Spring Cloud Gateway, Spring Cloud Config, Spring Cloud Sleuth/Micrometer Tracing, and others), each with its own release cadence — the next card covers how Spring Cloud's release-train versioning keeps a compatible set of these separately versioned projects working together.

- Spring Cloud adds distributed-systems infrastructure (discovery, configuration, resilience) on top of Spring Boot — every service in a Spring Cloud system is still a regular Spring Boot application underneath.
- The 12-factor app methodology's principles (externalized config, disposability, no hardcoded backing-service locations) are the design philosophy behind Spring Cloud's individual components.
- Concerns that don't exist for a single application — finding other services, adapting to instances scaling up or down, tolerating a single failed instance — are exactly what Spring Cloud's modules, introduced one at a time across this section, exist to solve.
- This card built the underlying problem from first principles; the rest of this section replaces each hand-rolled piece with its real, production-ready Spring Cloud counterpart.
