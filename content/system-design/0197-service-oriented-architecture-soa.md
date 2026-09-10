---
card: system-design
gi: 197
slug: service-oriented-architecture-soa
title: Service-oriented architecture (SOA)
---

## 1. What it is

**Service-oriented architecture (SOA)** splits a system into reusable services that communicate through a shared middleware layer, most often called an **Enterprise Service Bus (ESB)**. Every service publishes its capability to the bus; other services and applications call it through the bus rather than talking to each other directly.

## 2. Why & when

Large enterprises with many separate applications (billing, inventory, HR, a website) often end up with each application calling every other application directly, using different protocols and formats. SOA's answer is to put one shared bus in the middle: every service connects to the bus once, and the bus handles protocol translation, message routing, and format conversion between them. This turns an N-to-N integration problem into an N-to-1 problem — each service integrates with the bus, not with every other service.

SOA was the dominant enterprise architecture through the 2000s, especially where SOAP and XML were standard. It has fallen out of favor for new systems in favor of [microservices](0196-microservices.md), because the ESB itself becomes a bottleneck: it is a single shared piece of infrastructure that every team depends on, and changing routing logic in it requires a central team's involvement. Recognize SOA when you see an existing enterprise system with a central bus product (e.g. MuleSoft, IBM WebSphere ESB) mediating between many services — you will likely be integrating with it, not replacing it outright.

## 3. Core concept

- **The Enterprise Service Bus (ESB).** A shared piece of middleware that every service connects to. The bus receives a message from one service, transforms it if needed, and routes it to the right destination service.
- **Contract-first services.** Each service publishes a formal contract (classically a WSDL — Web Services Description Language — document) describing its operations, inputs, and outputs, so any consumer can generate a client from the contract without reading the service's code.
- **Protocol and format mediation.** The bus can translate between protocols (e.g. a legacy service that only speaks a proprietary format, called through the bus by a modern SOAP client) — this mediation is the bus's main value and also its main risk, since business logic can creep into it.
- **Orchestration inside the bus.** Complex, multi-step business processes are often implemented as an orchestration flow defined inside the ESB itself, rather than in any one service — a difference from [microservices](0196-microservices.md), where orchestration logic usually lives in a specific owning service.
- **Reuse over independence.** SOA optimizes for reusing existing services across many consumers via the bus. Microservices optimize for each team owning and deploying its service independently — a difference in priority, not just technology.

## 4. Diagram

```
   Billing App        Website           HR System         Inventory App
       |                 |                   |                    |
       v                 v                   v                    v
 +---------------------------------------------------------------------+
 |                    Enterprise Service Bus (ESB)                     |
 |   - routes messages to the right service                            |
 |   - translates protocols/formats (SOAP <-> legacy format)           |
 |   - can hold orchestration logic for multi-step processes           |
 +---------------------------------------------------------------------+
       |                 |                   |                    |
       v                 v                   v                    v
 CustomerService    OrderService       PayrollService      StockService
 (WSDL contract)   (WSDL contract)     (WSDL contract)     (WSDL contract)
```
*Caption: every consumer and every service connects to the ESB once. No service calls another service directly — the bus is always in the middle.*

## 5. Runnable example

This models the ESB's role: routing, contract validation, and protocol translation, in one file. A real ESB is a deployed middleware product; this shows the pattern it implements.

**Level 1 — Basic.** A bus that routes a message to the correct service by name.

**Level 2 — Contract validation.** Each service publishes a simple contract (allowed operations); the bus rejects a message that does not match the contract before it ever reaches the service.

**Level 3 — Protocol/format mediation.** The bus translates an incoming "modern" JSON-style request into the legacy key-value format one specific service still expects, so the caller never needs to know the service is legacy.

```java
// SoaEsbDemo.java
import java.util.*;

public class SoaEsbDemo {

    interface Service {
        String contractName();
        List<String> supportedOperations();
        String handle(String operation, Map<String, String> payload);
    }

    // ---------- Level 1 & 2: a modern service with a published contract ----------
    static class CustomerService implements Service {
        public String contractName() { return "CustomerService v1"; }
        public List<String> supportedOperations() { return List.of("getCustomer", "updateAddress"); }
        public String handle(String operation, Map<String, String> payload) {
            return "CustomerService executed " + operation + " for id=" + payload.get("id");
        }
    }

    // ---------- Level 3: a legacy service that only understands old field names ----------
    static class LegacyPayrollService implements Service {
        public String contractName() { return "PayrollService (legacy, 2004 format)" ; }
        public List<String> supportedOperations() { return List.of("RUN_PAYROLL"); }
        public String handle(String operation, Map<String, String> payload) {
            // Legacy service expects "EMP_ID" and "AMT_CENTS", not modern field names.
            return "LegacyPayrollService ran payroll for EMP_ID=" + payload.get("EMP_ID") +
                   ", AMT_CENTS=" + payload.get("AMT_CENTS");
        }
    }

    static class EnterpriseServiceBus {
        private final Map<String, Service> registry = new HashMap<>();

        void register(String routeName, Service service) {
            registry.put(routeName, service);
            System.out.println("  [ESB] registered route \"" + routeName + "\" -> " + service.contractName());
        }

        // Level 1 + 2: route and validate against the service's published contract.
        String route(String routeName, String operation, Map<String, String> payload) {
            Service service = registry.get(routeName);
            if (service == null) return "[ESB] no route named " + routeName;
            if (!service.supportedOperations().contains(operation)) {
                return "[ESB] rejected: " + operation + " not in contract " + service.contractName();
            }
            return service.handle(operation, payload);
        }

        // Level 3: translate a modern request shape into the legacy shape before routing.
        String routeWithTranslation(String routeName, String operation, Map<String, String> modernPayload) {
            Map<String, String> legacyPayload = new HashMap<>();
            legacyPayload.put("EMP_ID", modernPayload.get("employeeId"));
            legacyPayload.put("AMT_CENTS", String.valueOf(
                (int) (Double.parseDouble(modernPayload.get("amountDollars")) * 100)));
            System.out.println("  [ESB] translated " + modernPayload + " -> " + legacyPayload);
            return route(routeName, operation, legacyPayload);
        }
    }

    public static void main(String[] args) {
        EnterpriseServiceBus bus = new EnterpriseServiceBus();
        bus.register("customers", new CustomerService());
        bus.register("payroll", new LegacyPayrollService());

        System.out.println("\nLevel 1 - basic routing:");
        System.out.println("  " + bus.route("customers", "getCustomer", Map.of("id", "C-42")));

        System.out.println("\nLevel 2 - contract validation rejects an unknown operation:");
        System.out.println("  " + bus.route("customers", "deleteCustomer", Map.of("id", "C-42")));

        System.out.println("\nLevel 3 - protocol/format mediation to a legacy service:");
        Map<String, String> modernRequest = Map.of("employeeId", "E-9", "amountDollars", "1500.00");
        System.out.println("  " + bus.routeWithTranslation("payroll", "RUN_PAYROLL", modernRequest));
    }
}
```

**How to run:** `java SoaEsbDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **`bus.register(...)` runs twice**, adding `CustomerService` under the route name `"customers"` and `LegacyPayrollService` under `"payroll"`. In a real ESB, this registration step corresponds to deploying the service's WSDL contract to the bus.
2. **Level 1:** `bus.route("customers", "getCustomer", ...)` looks up the `"customers"` route, finds `CustomerService`, checks that `"getCustomer"` is in its `supportedOperations()` list, and forwards the call. The response comes back through the bus, not directly from the service to the caller.
3. **Level 2:** `bus.route("customers", "deleteCustomer", ...)` looks up the same service, but `"deleteCustomer"` is not in `supportedOperations()`. The bus rejects the call itself — `CustomerService.handle(...)` is never invoked. This is contract enforcement happening centrally, at the bus, rather than inside every service.
4. **Level 3:** the caller sends a modern-shaped payload, `{employeeId: "E-9", amountDollars: "1500.00"}`, with no idea that `LegacyPayrollService` only understands `EMP_ID` and `AMT_CENTS` in whole cents. `routeWithTranslation` builds the legacy-shaped map first, prints the translation so you can see it happen, then calls the normal `route(...)` path.
5. `LegacyPayrollService.handle(...)` receives `EMP_ID=E-9, AMT_CENTS=150000` and runs — the caller never had to know the target service's internal format. This translation step is exactly the mediation role the ESB plays in a real SOA deployment.

## 7. Gotchas & takeaways

> **Gotcha:** because the ESB is shared infrastructure, business logic (like the modern-to-legacy translation above) tends to accumulate inside it over time. Eventually the bus itself becomes a monolith that only one central team understands — the exact problem SOA was meant to solve, now moved into the middleware layer.

- Recognize SOA by its central bus and contract-first (WSDL-style) service design — this is different from microservices, where each service usually calls others directly (often through an API gateway for external traffic only, not internal routing).
- SOA's reuse-through-the-bus model works well for stable, slow-changing enterprise integrations, but resists the frequent independent deployment that modern teams often want.
- When integrating a new service with an existing SOA/ESB estate, keep your side of the contract clean even if the bus does translation — do not let legacy formats leak into your own service's code.
- If you are designing a new system from scratch today, prefer [microservices](0196-microservices.md) or a [modular monolith](0195-monolith-modular-monolith.md) over introducing a new ESB — SOA is best understood as the architecture you integrate with, not the one you build new.
