---
card: microservices
gi: 169
slug: gateway-routing-vs-service-mesh-ingress
title: "Gateway routing vs service mesh ingress"
---

## 1. What it is

Gateway routing handles traffic entering the system from outside — external clients reaching internal services through an [API gateway](0157-api-gateway-pattern.md). Service mesh ingress is the entry point of a service mesh (like Istio or Linkerd), which additionally governs traffic *between* internal services (service-to-service routing, retries, mutual TLS) once it's already inside the system. The two solve related but distinct problems: one is about the boundary between outside and inside, the other is about traffic patterns entirely within the inside.

## 2. Why & when

An API gateway's job ends once a request has been routed to the right backend service; what happens *next* — that service calling three other internal services to fulfill the request, each of those calls needing its own retry policy, load balancing, and encryption — is a separate concern a plain gateway typically doesn't address at all. A service mesh fills that gap by installing a lightweight proxy (a sidecar) alongside every service instance, uniformly handling service-to-service traffic concerns without any of that logic living in application code. The mesh's own ingress gateway is just the mesh's entry point for external traffic, distinguishing it from the mesh's internal, service-to-service traffic handling.

Use a plain API gateway when the primary need is a clean external entry point — routing, auth, rate limiting, aggregation — for a system that either has modest internal service-to-service complexity or doesn't yet need uniform, infrastructure-level policy for internal traffic. Reach for a full service mesh once the *internal* traffic between services has grown complex enough that per-service retry logic, mutual TLS, and fine-grained traffic control (canary releases, uniform observability) are needed consistently across many services — a heavier-weight investment, appropriate once that internal complexity genuinely exists, not before.

## 3. Core concept

An API gateway sits at one boundary, routing external requests to internal services; a service mesh's sidecar proxies sit *everywhere*, next to every service instance, uniformly intercepting and managing all service-to-service traffic, with the mesh's own ingress gateway being simply the mesh's version of the external entry point, built on the same sidecar-proxy technology as the rest of the mesh.

```java
// API GATEWAY: external client -> ONE entry point -> internal service
externalRequest -> gateway.route() -> orderService

// SERVICE MESH: EVERY internal call, EVERYWHERE, goes through a sidecar proxy uniformly
orderService -> [sidecar proxy: retry, mTLS, load balance] -> paymentService
paymentService -> [sidecar proxy: retry, mTLS, load balance] -> inventoryService
// the mesh's OWN ingress gateway is just its entry point FOR external traffic, using the SAME proxy technology
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An external client enters through the API gateway, which routes to order-service; order-service then calls payment-service and inventory-service, with each internal call passing through a sidecar proxy that the service mesh manages uniformly, independent of the gateway" >
  <rect x="20" y="70" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Client</text>

  <rect x="170" y="70" width="120" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="230" y="94" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">API Gateway</text>

  <rect x="340" y="70" width="110" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="395" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">order-service</text>

  <rect x="490" y="20" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">payment-service</text>
  <text x="555" y="10" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">via sidecar (mesh)</text>

  <rect x="490" y="105" width="130" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="127" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">inventory-service</text>
  <text x="555" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">via sidecar (mesh)</text>

  <line x1="120" y1="90" x2="168" y2="90" stroke="#8b949e" marker-end="url(#arr50)"/>
  <line x1="290" y1="90" x2="338" y2="90" stroke="#8b949e" marker-end="url(#arr50)"/>
  <line x1="450" y1="85" x2="488" y2="45" stroke="#8b949e" marker-end="url(#arr50)"/>
  <line x1="450" y1="95" x2="488" y2="115" stroke="#8b949e" marker-end="url(#arr50)"/>

  <defs>
    <marker id="arr50" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The gateway handles the outside-to-inside boundary; the mesh handles traffic entirely within the inside.

## 5. Runnable example

Scenario: an order-placement flow that starts with external routing handled by a gateway but internal service-to-service calls left entirely unmanaged (showing the gap a mesh fills), adds mesh-style uniform sidecar behavior (retry, consistent policy) applied to every internal call, and finally demonstrates the two working together — one external request triggering gateway routing followed by mesh-managed internal fan-out, each handled by its own distinct layer.

### Level 1 — Basic

```java
// File: GatewayOnlyNoInternalManagement.java -- gateway routes external traffic;
// internal service-to-service calls are BARE, with no uniform retry/policy at all.
public class GatewayOnlyNoInternalManagement {
    static class ApiGateway {
        String route(String path) {
            System.out.println("[gateway] routing external request: " + path);
            return OrderService.placeOrder();
        }
    }

    static class OrderService {
        static String placeOrder() {
            // internal calls: BARE, no retry, no consistent policy -- each service reinvents this itself, or doesn't
            String paymentResult = callPaymentServiceDirectly();
            String inventoryResult = callInventoryServiceDirectly();
            return "Order placed: " + paymentResult + ", " + inventoryResult;
        }
        static String callPaymentServiceDirectly() { System.out.println("  [order-service] calling payment-service DIRECTLY, no retry/policy"); return "payment OK"; }
        static String callInventoryServiceDirectly() { System.out.println("  [order-service] calling inventory-service DIRECTLY, no retry/policy"); return "inventory OK"; }
    }

    public static void main(String[] args) {
        ApiGateway gateway = new ApiGateway();
        System.out.println(gateway.route("/orders"));
        System.out.println("The GATEWAY handled the external hop well; the INTERNAL hops have NO uniform management at all.");
    }
}
```

**How to run:** `javac GatewayOnlyNoInternalManagement.java && java GatewayOnlyNoInternalManagement` (JDK 17+).

### Level 2 — Intermediate

```java
// File: MeshSidecarUniformPolicy.java -- EVERY internal call passes through a
// SIDECAR-style wrapper applying UNIFORM retry policy, mirroring a service mesh's behavior.
import java.util.function.*;

public class MeshSidecarUniformPolicy {
    // simulates a mesh SIDECAR proxy: wraps ANY internal call with uniform policy, transparently
    static class SidecarProxy {
        String callWithMeshPolicy(String targetService, Supplier<String> actualCall) {
            System.out.println("  [sidecar] intercepting call to " + targetService + " -- applying retry + policy UNIFORMLY");
            int maxRetries = 2;
            for (int attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    return actualCall.get(); // the SAME retry logic, applied to ANY service, without that service's code knowing
                } catch (RuntimeException e) {
                    System.out.println("    [sidecar] attempt " + attempt + " failed, retrying...");
                }
            }
            return "FAILED after " + maxRetries + " attempts";
        }
    }

    static class OrderService {
        SidecarProxy sidecar = new SidecarProxy(); // every service gets ITS OWN sidecar, but they all behave IDENTICALLY

        String placeOrder() {
            String paymentResult = sidecar.callWithMeshPolicy("payment-service", () -> "payment OK");
            String inventoryResult = sidecar.callWithMeshPolicy("inventory-service", () -> "inventory OK");
            return "Order placed: " + paymentResult + ", " + inventoryResult;
        }
    }

    public static void main(String[] args) {
        OrderService orderService = new OrderService();
        System.out.println(orderService.placeOrder());
        System.out.println("BOTH internal calls got the SAME uniform retry policy, with ZERO retry code written inside OrderService's business logic.");
    }
}
```

**How to run:** `javac MeshSidecarUniformPolicy.java && java MeshSidecarUniformPolicy` (JDK 17+).

Expected output:
```
  [sidecar] intercepting call to payment-service -- applying retry + policy UNIFORMLY
  [sidecar] intercepting call to inventory-service -- applying retry + policy UNIFORMLY
Order placed: payment OK, inventory OK
BOTH internal calls got the SAME uniform retry policy, with ZERO retry code written inside OrderService's business logic.
```

### Level 3 — Advanced

```java
// File: GatewayAndMeshTogether.java -- ONE external request flows through BOTH
// layers: the GATEWAY handles the external hop, the MESH (sidecars) handles
// EVERY subsequent internal hop, each layer doing its OWN distinct job.
import java.util.function.*;

public class GatewayAndMeshTogether {
    static class SidecarProxy {
        String callWithMeshPolicy(String targetService, Supplier<String> actualCall) {
            System.out.println("    [mesh sidecar] " + targetService + ": retry + mTLS + load-balance, uniformly");
            return actualCall.get(); // simplified: succeeds on first try in this example
        }
    }

    static class ApiGateway {
        String route(String path) {
            System.out.println("[api gateway] EXTERNAL boundary: routing " + path + " to order-service");
            return new OrderService().placeOrder();
        }
    }

    static class OrderService {
        SidecarProxy sidecar = new SidecarProxy();
        String placeOrder() {
            String payment = sidecar.callWithMeshPolicy("payment-service", () -> new PaymentService().charge());
            String inventory = sidecar.callWithMeshPolicy("inventory-service", () -> new InventoryService().reserve());
            return "Order placed: " + payment + ", " + inventory;
        }
    }
    static class PaymentService {
        SidecarProxy sidecar = new SidecarProxy();
        String charge() {
            // payment-service ITSELF also calls fraud-service internally -- ANOTHER mesh-managed hop
            String fraudCheck = sidecar.callWithMeshPolicy("fraud-service", () -> "fraud check passed");
            return "charged (" + fraudCheck + ")";
        }
    }
    static class InventoryService { String reserve() { return "reserved"; } }

    public static void main(String[] args) {
        ApiGateway gateway = new ApiGateway(); // ONE gateway, at the EXTERNAL boundary only
        String result = gateway.route("/orders");
        System.out.println(result);
        System.out.println("ONE external hop (gateway) triggered THREE internal hops (mesh-managed) -- each layer handled EXACTLY its own responsibility.");
    }
}
```

**How to run:** `javac GatewayAndMeshTogether.java && java GatewayAndMeshTogether` (JDK 17+).

Expected output:
```
[api gateway] EXTERNAL boundary: routing /orders to order-service
    [mesh sidecar] payment-service: retry + mTLS + load-balance, uniformly
    [mesh sidecar] fraud-service: retry + mTLS + load-balance, uniformly
    [mesh sidecar] inventory-service: retry + mTLS + load-balance, uniformly
Order placed: charged (fraud check passed), reserved
ONE external hop (gateway) triggered THREE internal hops (mesh-managed) -- each layer handled EXACTLY its own responsibility.
```

## 6. Walkthrough

1. **Level 1** — `ApiGateway.route` handles exactly one external-to-internal hop, and its printed log line reflects that; `OrderService.placeOrder`'s two internal calls (`callPaymentServiceDirectly`, `callInventoryServiceDirectly`) are made with no wrapping logic at all, no retry, no consistent policy — this is the gap between "gateway handles the external boundary" and "nothing handles the internal traffic."
2. **Level 2, the sidecar as a uniform wrapper** — `SidecarProxy.callWithMeshPolicy` accepts *any* `Supplier<String>` representing an arbitrary internal call, and applies retry logic around it without that logic needing to know anything about what service it's calling — this genericity is what lets a real service mesh apply identical policy to every service's traffic without touching that service's own code.
3. **Level 2, both calls getting the same treatment** — `OrderService.placeOrder` routes both its internal calls through `sidecar.callWithMeshPolicy`, and the printed log shows the identical interception message for both `"payment-service"` and `"inventory-service"`, despite `OrderService`'s own business logic containing zero explicit retry code.
4. **Level 3, distinguishing the two layers explicitly** — `ApiGateway.route` is called exactly once, at the very start, representing the single external-to-internal boundary crossing; every subsequent call (`order-service` to `payment-service`, `payment-service` to `fraud-service`, `order-service` to `inventory-service`) goes through a `SidecarProxy`, representing mesh-managed internal traffic.
5. **Level 3, the mesh applying uniformly, even to a nested call** — `PaymentService.charge()` itself makes an additional internal call to `fraud-service`, and this call is *also* wrapped in `sidecar.callWithMeshPolicy`, exactly like every other internal call — demonstrating that mesh-style policy applies uniformly no matter how deep in the internal call graph a service-to-service call occurs, not just for calls made directly by the entry-point service.
6. **Level 3, tracing the full flow** — `gateway.route("/orders")` triggers exactly one gateway-level log line, followed by three mesh-sidecar log lines (for `payment-service`, `fraud-service`, and `inventory-service` respectively), reflecting the actual sequence of one external hop followed by three internal hops.
7. **Level 3, the division of responsibility made concrete** — the final printed statement summarizes what the trace demonstrated: the gateway's job began and ended with routing the single external request to `order-service`; everything that happened afterward, no matter how many internal services were involved or how deeply nested the calls became, was the mesh's uniform responsibility — two genuinely distinct layers, each doing exactly one job, working together without overlap.

## 7. Gotchas & takeaways

> **Gotcha:** it's a common misconception that adopting a service mesh replaces the need for an API gateway, or vice versa — they solve different problems (external boundary vs. internal traffic) and many production systems run both simultaneously, with the mesh's own ingress gateway sometimes even sitting *behind* a separate, dedicated API gateway that handles external-specific concerns (client authentication, public API versioning) the mesh's ingress isn't designed for.

- Gateway routing handles the boundary between external clients and the internal system; service mesh ingress and the broader mesh handle traffic entirely within the internal system, service-to-service.
- A service mesh applies uniform policy (retry, load balancing, mutual TLS) to every internal call via sidecar proxies, without that logic living in any individual service's application code.
- The two are complementary, not competing — many production systems use both, an API gateway at the external edge and a service mesh managing everything behind it.
- A service mesh is a heavier-weight investment, appropriate once internal service-to-service traffic complexity genuinely justifies uniform, infrastructure-level management across many services.
- The mesh's own ingress gateway is built on the same sidecar-proxy technology as the rest of the mesh, distinguishing it from a standalone API gateway product even though both serve an external-entry-point role.
