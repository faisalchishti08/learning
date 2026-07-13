---
card: microservices
gi: 162
slug: protocol-translation-at-the-edge
title: "Protocol translation at the edge"
---

## 1. What it is

Protocol translation at the edge is the gateway converting between the protocol a client speaks (typically REST/HTTP or GraphQL) and the protocol a backend service actually speaks internally (which might be [gRPC](0085-rpc-model-grpc-and-http2.md), a different message format, or an internal RPC mechanism) — the client and the backend can each use the protocol that best suits them, with the gateway doing the conversion work in between.

## 2. Why & when

Internal services often benefit from a different protocol than external clients should be expected to speak: gRPC's binary, strongly-typed, HTTP/2-based protocol is excellent for efficient internal service-to-service calls but is awkward for browser-based clients (limited native browser support) and unfamiliar to many external API consumers who expect plain REST/JSON. Rather than forcing internal services to expose a REST facade themselves (duplicating the translation logic across every service) or forcing external clients to speak gRPC directly, the gateway performs this translation exactly once, at the boundary — external REST/JSON in, internal gRPC out, and the reverse on the way back.

Reach for edge-level protocol translation when internal services benefit from a protocol (gRPC, an internal binary format) that isn't the right fit for external clients, and centralizing the translation at the gateway avoids duplicating that conversion logic in every service that would otherwise need its own REST facade. This is a specific application of the same "keep cross-cutting concerns at the edge" principle behind other [edge service responsibilities](0158-edge-service-responsibilities.md).

## 3. Core concept

The gateway receives a request in the client's protocol, translates it into a call in the backend's native protocol, and translates the backend's response back into the client's expected protocol — from the client's perspective, it only ever spoke REST/JSON; from the backend's perspective, it only ever spoke gRPC.

```java
// client sends plain REST/JSON
POST /orders  { "customerId": 7, "items": ["widget"] }

// gateway translates into a gRPC call to the backend
OrderRequest grpcRequest = OrderRequest.newBuilder().setCustomerId(7).addItems("widget").build();
OrderResponse grpcResponse = orderServiceGrpcStub.placeOrder(grpcRequest); // backend speaks ONLY gRPC

// gateway translates the gRPC response back into JSON for the client
{ "orderId": 42, "status": "PLACED" }
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client sends a REST/JSON request to the gateway; the gateway translates it into a gRPC call to the backend service, and translates the gRPC response back into JSON before returning it to the client" >
  <rect x="20" y="60" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="85" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">speaks REST/JSON</text>

  <rect x="240" y="55" width="160" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="78" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Gateway</text>
  <text x="320" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">REST &lt;-&gt; gRPC translation</text>

  <rect x="490" y="60" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="555" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">speaks ONLY gRPC</text>

  <line x1="150" y1="82" x2="238" y2="82" stroke="#8b949e" marker-end="url(#arr43)"/>
  <line x1="400" y1="82" x2="488" y2="82" stroke="#8b949e" marker-end="url(#arr43)"/>

  <defs>
    <marker id="arr43" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Neither side needs to know or care what protocol the other speaks; the gateway is the only component fluent in both.

## 5. Runnable example

Scenario: an order-placement request that starts by forcing a browser client to speak the backend's native protocol directly (showing why that's impractical), introduces gateway-level translation between REST/JSON and a simulated internal RPC format, and finally shows the same gateway translating a second, different backend protocol for a different service, demonstrating that clients remain entirely unaware of backend protocol diversity.

### Level 1 — Basic

```java
// File: ClientForcedToSpeakBackendProtocol.java -- the client must construct
// the BACKEND's native (simulated gRPC-style) request format directly -- impractical for external clients.
import java.util.*;

public class ClientForcedToSpeakBackendProtocol {
    record InternalOrderRequest(int customerId, List<String> items, String encoding) {} // backend's OWN format

    public static void main(String[] args) {
        // the CLIENT is forced to know the backend's internal message shape AND encoding directly
        InternalOrderRequest request = new InternalOrderRequest(7, List.of("widget"), "protobuf-binary");
        System.out.println("Client had to construct: " + request);
        System.out.println("A browser-based client would need a gRPC-capable client library just to make THIS call -- often impractical.");
    }
}
```

**How to run:** `javac ClientForcedToSpeakBackendProtocol.java && java ClientForcedToSpeakBackendProtocol` (JDK 17+).

### Level 2 — Intermediate

```java
// File: GatewayTranslatesRestToRpc.java -- the client sends plain REST/JSON;
// the gateway translates it into the backend's native RPC-style format, and back.
import java.util.*;

public class GatewayTranslatesRestToRpc {
    record RestOrderRequest(int customerId, List<String> items) {}      // what the CLIENT sends (JSON-ish)
    record InternalOrderRequest(int customerId, List<String> items, String encoding) {} // what the BACKEND expects
    record InternalOrderResponse(int orderId, String status) {}          // what the BACKEND returns
    record RestOrderResponse(int orderId, String status) {}              // what the CLIENT expects back

    static class Gateway {
        InternalOrderResponse callBackend(InternalOrderRequest req) { // stands in for an actual gRPC stub call
            System.out.println("[backend, native protocol] received: " + req);
            return new InternalOrderResponse(42, "PLACED");
        }

        RestOrderResponse handleClientRequest(RestOrderRequest clientRequest) {
            System.out.println("[gateway] client sent (REST/JSON): " + clientRequest);
            InternalOrderRequest translated = new InternalOrderRequest(clientRequest.customerId(), clientRequest.items(), "protobuf-binary");
            InternalOrderResponse backendResponse = callBackend(translated);
            RestOrderResponse clientResponse = new RestOrderResponse(backendResponse.orderId(), backendResponse.status());
            System.out.println("[gateway] client receives (REST/JSON): " + clientResponse);
            return clientResponse;
        }
    }

    public static void main(String[] args) {
        Gateway gateway = new Gateway();
        gateway.handleClientRequest(new RestOrderRequest(7, List.of("widget")));
        System.out.println("Client only EVER dealt with plain REST/JSON -- never saw the backend's native protocol at all.");
    }
}
```

**How to run:** `javac GatewayTranslatesRestToRpc.java && java GatewayTranslatesRestToRpc` (JDK 17+).

Expected output:
```
[gateway] client sent (REST/JSON): RestOrderRequest[customerId=7, items=[widget]]
[backend, native protocol] received: InternalOrderRequest[customerId=7, items=[widget], encoding=protobuf-binary]
[gateway] client receives (REST/JSON): RestOrderResponse[orderId=42, status=PLACED]
Client only EVER dealt with plain REST/JSON -- never saw the backend's native protocol at all.
```

### Level 3 — Advanced

```java
// File: MultipleBackendProtocolsHiddenUniformly.java -- the SAME gateway translates
// TWO DIFFERENT backend protocols, both hidden equally behind one uniform REST/JSON client contract.
import java.util.*;
import java.util.function.*;

public class MultipleBackendProtocolsHiddenUniformly {
    record RestRequest(String resource, Map<String, Object> body) {}
    record RestResponse(Map<String, Object> body) {}

    // backend 1: order-service speaks a simulated gRPC-style protocol
    record GrpcOrderRequest(int customerId, List<String> items) {}
    record GrpcOrderResponse(int orderId, String status) {}

    // backend 2: legacy-inventory-service speaks a DIFFERENT, older SOAP-XML-style protocol
    record SoapInventoryRequest(String xmlPayload) {}
    record SoapInventoryResponse(String xmlPayload) {}

    static class Gateway {
        RestResponse handle(RestRequest request) {
            return switch (request.resource()) {
                case "orders" -> handleOrders(request);
                case "inventory" -> handleInventory(request);
                default -> new RestResponse(Map.of("error", "unknown resource"));
            };
        }

        RestResponse handleOrders(RestRequest request) {
            GrpcOrderRequest grpcReq = new GrpcOrderRequest((int) request.body().get("customerId"), (List<String>) request.body().get("items"));
            System.out.println("[gateway -> order-service, gRPC-style] " + grpcReq);
            GrpcOrderResponse grpcResp = new GrpcOrderResponse(42, "PLACED"); // simulated backend call
            return new RestResponse(Map.of("orderId", grpcResp.orderId(), "status", grpcResp.status()));
        }

        RestResponse handleInventory(RestRequest request) {
            String sku = (String) request.body().get("sku");
            SoapInventoryRequest soapReq = new SoapInventoryRequest("<CheckStock><Sku>" + sku + "</Sku></CheckStock>");
            System.out.println("[gateway -> legacy-inventory-service, SOAP-XML-style] " + soapReq.xmlPayload());
            SoapInventoryResponse soapResp = new SoapInventoryResponse("<StockLevel>15</StockLevel>"); // simulated backend call
            int stockLevel = Integer.parseInt(soapResp.xmlPayload().replaceAll("[^0-9]", ""));
            return new RestResponse(Map.of("sku", sku, "stockLevel", stockLevel));
        }
    }

    public static void main(String[] args) {
        Gateway gateway = new Gateway();

        RestResponse orderResult = gateway.handle(new RestRequest("orders", Map.of("customerId", 7, "items", List.of("widget"))));
        RestResponse inventoryResult = gateway.handle(new RestRequest("inventory", Map.of("sku", "widget-001")));

        System.out.println("Client's order response (REST/JSON): " + orderResult.body());
        System.out.println("Client's inventory response (REST/JSON): " + inventoryResult.body());
        System.out.println("TWO completely different backend protocols (gRPC-style AND SOAP-XML-style), BOTH hidden behind the SAME uniform client contract.");
    }
}
```

**How to run:** `javac MultipleBackendProtocolsHiddenUniformly.java && java MultipleBackendProtocolsHiddenUniformly` (JDK 17+).

Expected output:
```
[gateway -> order-service, gRPC-style] GrpcOrderRequest[customerId=7, items=[widget]]
[gateway -> legacy-inventory-service, SOAP-XML-style] <CheckStock><Sku>widget-001</Sku></CheckStock>
Client's order response (REST/JSON): {orderId=42, status=PLACED}
Client's inventory response (REST/JSON): {sku=widget-001, stockLevel=15}
TWO completely different backend protocols (gRPC-style AND SOAP-XML-style), BOTH hidden behind the SAME uniform client contract.
```

## 6. Walkthrough

1. **Level 1** — `InternalOrderRequest` is constructed directly by what stands in for client code, including an `encoding` field (`"protobuf-binary"`) that only makes sense in the context of the backend's own wire format — a browser-based client attempting this in reality would need a gRPC-capable client library and protocol buffer definitions, a substantial and often impractical requirement.
2. **Level 2, two distinct type pairs** — `RestOrderRequest`/`RestOrderResponse` represent the client-facing shapes, while `InternalOrderRequest`/`InternalOrderResponse` represent the backend's native shapes; `Gateway.handleClientRequest` is the only code that ever touches both.
3. **Level 2, the translation steps made explicit** — `handleClientRequest` builds `translated` (an `InternalOrderRequest`) from the incoming `clientRequest`'s fields, calls `callBackend` (standing in for an actual gRPC stub invocation) with it, and then builds `clientResponse` (a `RestOrderResponse`) from the backend's `InternalOrderResponse` — two separate, explicit conversion steps, one per direction.
4. **Level 2, the client's isolation from backend protocol** — `main`'s call to `gateway.handleClientRequest` passes and later inspects only `RestOrderRequest`/`RestOrderResponse` types; nothing about `InternalOrderRequest` or its `encoding` field is ever visible outside the `Gateway` class.
5. **Level 3, two entirely different backend protocol styles** — `handleOrders` translates into a `GrpcOrderRequest`, mirroring binary RPC-style calls, while `handleInventory` translates into a `SoapInventoryRequest` carrying a literal XML string, mirroring an older SOAP-based backend — two structurally unrelated protocol shapes, handled by two separate translation methods.
6. **Level 3, one uniform client contract regardless** — both `handleOrders` and `handleInventory` are invoked through the identical `gateway.handle(RestRequest)` method and both return the identical `RestResponse` type, meaning the client's experience (send a `RestRequest`, receive a `RestResponse`) is uniform, entirely unaware that one call was translated into gRPC-style RPC and the other into SOAP-XML underneath.
7. **Level 3, the printed proof** — the two backend-facing log lines show genuinely different wire formats being constructed and (simulated) sent, while `orderResult.body()` and `inventoryResult.body()` both come back as plain, uniform key-value maps — demonstrating that protocol diversity among backend services, however extreme (even including a legacy SOAP system alongside a modern gRPC one), can be fully absorbed at the gateway without a single client-facing inconsistency.

## 7. Gotchas & takeaways

> **Gotcha:** protocol translation is not free — converting between structurally different representations (REST/JSON's dynamic, loosely-typed objects versus gRPC's strongly-typed, schema-defined messages, or SOAP's XML) takes real CPU time and can silently lose fidelity if a source protocol supports something the target protocol doesn't cleanly represent (a REST client sending a field type the backend's protobuf schema doesn't expect); translation logic needs the same care and testing as any other data-mapping code, not an assumption that it "just works."

- Protocol translation at the edge lets clients and backend services each use the protocol best suited to them, with the gateway performing the conversion between them at exactly one boundary point.
- This avoids forcing internal services to expose an external-facing protocol themselves, and avoids forcing external clients to speak an internal-only protocol like gRPC directly.
- The gateway can translate multiple, structurally different backend protocols (RPC-style, SOAP-XML, or others) simultaneously, all hidden behind one uniform client-facing contract.
- This is a specific instance of the broader principle of keeping cross-cutting, boundary-spanning concerns at the edge rather than duplicating them across individual backend services.
- Protocol translation carries real performance cost and fidelity risk, especially when converting between protocols with meaningfully different type systems or capabilities — it deserves careful implementation and testing, not an assumption of transparency.
