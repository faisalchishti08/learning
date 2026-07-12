---
card: microservices
gi: 88
slug: remote-procedure-call-rpc-model
title: "Remote Procedure Call (RPC) model"
---

## 1. What it is

RPC (Remote Procedure Call) is a style of service-to-service communication that makes a network call look and feel like an ordinary local method call: `inventoryClient.checkStock("widget")` reads exactly like calling a method on a local object, even though under the hood it serializes the arguments, sends them over the network, and deserializes the response. This differs from REST's resource-and-verb model (see [RESTful APIs over HTTP](0076-restful-apis-over-http.md)) by centering the API around *procedures* (actions) rather than *resources* (nouns) — `checkStock(sku)` rather than `GET /inventory/{sku}`.

## 2. Why & when

RPC's core appeal is developer ergonomics: calling a remote service reads exactly like calling a local one, with a generated client stub handling all the networking, serialization, and error translation behind a plain method signature. This maps naturally onto operations that are genuinely action-shaped rather than resource-shaped — `calculateShippingCost(order)` or `validateCreditCard(cardDetails)` don't map cleanly onto REST's noun-and-verb model, but map directly onto an RPC method call. The tradeoff is tighter coupling: an RPC client typically needs a generated stub built from the exact service definition, versioned and distributed alongside it, whereas a REST client can often be written against just documentation and a general-purpose HTTP library.

Reach for RPC (concretely, usually [gRPC](0089-grpc-and-http-2.md) in modern microservices) when the operation is naturally action-shaped, when strong typed contracts and code generation are valuable, or when performance (binary serialization, HTTP/2 multiplexing) matters more than REST's tooling ubiquity. Reach for REST when the operation maps cleanly onto resources, or when broad client compatibility and human-debuggability matter most.

## 3. Core concept

The client calls a method with a normal-looking signature; a generated stub handles marshaling the call across the network, and the server-side implementation runs as if it had been called directly.

```
Client code:                          What actually happens:
   int stock = inventoryClient        1. stub serializes "checkStock" + args
                .checkStock("widget");  2. sends over the network
                                       3. server deserializes, calls the REAL method
                                       4. server serializes the result, sends back
                                       5. stub deserializes it, returns to caller
```

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client calls a method on a local-looking stub, which serializes the call, sends it over the network to the server, and returns the deserialized result, all hidden behind the plain method call">
  <rect x="20" y="60" width="140" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="88" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Client code</text>

  <rect x="210" y="40" width="180" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Generated stub</text>
  <text x="300" y="82" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">serialize, send,</text>
  <text x="300" y="97" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">deserialize result</text>

  <rect x="440" y="60" width="180" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Server: real checkStock()</text>

  <line x1="160" y1="85" x2="210" y2="85" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="390" y1="85" x2="440" y2="85" stroke="#8b949e" stroke-width="1.5"/>
</svg>

The stub makes the network entirely invisible to the calling code's syntax.

## 5. Runnable example

Scenario: an `InventoryService` call, first made with raw manual networking-style code exposed directly to the caller, then wrapped behind a generated-style stub that hides the networking entirely behind a plain method call, then extended to show the stub also translating a remote failure into a normal exception, exactly as a local method call's exception would behave.

### Level 1 — Basic

```java
// File: RawNetworkCall.java -- the CALLER has to know about
// serialization and the network call directly -- no RPC abstraction.
import java.util.*;

public class RawNetworkCall {
    static Map<String, Integer> stock = new HashMap<>(Map.of("widget", 5));

    static String sendRawRequest(String procedureName, String arg) {
        // simulates: serialize, send over network, get raw response back
        if (procedureName.equals("checkStock")) {
            return String.valueOf(stock.getOrDefault(arg, 0));
        }
        return "ERROR";
    }

    public static void main(String[] args) {
        String rawResponse = sendRawRequest("checkStock", "widget"); // caller manually builds the "call"
        int quantity = Integer.parseInt(rawResponse); // caller manually deserializes
        System.out.println("Stock for widget: " + quantity);
    }
}
```

**How to run:** `javac RawNetworkCall.java && java RawNetworkCall` (JDK 17+).

Expected output:
```
Stock for widget: 5
```

The caller has to know the procedure's name as a string, how to encode its argument, and how to parse the raw response — none of it reads like a normal method call.

### Level 2 — Intermediate

```java
// File: GeneratedStubStyle.java -- wrap the SAME networking behind a
// stub with a plain method signature -- this is what a real RPC code
// generator (like gRPC's protoc plugin) produces automatically.
import java.util.*;

public class GeneratedStubStyle {
    static Map<String, Integer> stock = new HashMap<>(Map.of("widget", 5));

    interface InventoryClient { // the GENERATED interface -- looks like any local interface
        int checkStock(String sku);
    }

    static class InventoryClientStub implements InventoryClient { // the GENERATED implementation
        public int checkStock(String sku) {
            String rawResponse = sendRawRequest("checkStock", sku); // networking HIDDEN inside here
            return Integer.parseInt(rawResponse);
        }
        private String sendRawRequest(String procedureName, String arg) {
            if (procedureName.equals("checkStock")) return String.valueOf(stock.getOrDefault(arg, 0));
            return "ERROR";
        }
    }

    public static void main(String[] args) {
        InventoryClient inventoryClient = new InventoryClientStub();
        int quantity = inventoryClient.checkStock("widget"); // reads EXACTLY like a local method call
        System.out.println("Stock for widget: " + quantity);
    }
}
```

**How to run:** `javac GeneratedStubStyle.java && java GeneratedStubStyle` (JDK 17+).

Expected output:
```
Stock for widget: 5
```

`main`'s call, `inventoryClient.checkStock("widget")`, is now indistinguishable in syntax from calling a plain local method — the serialization and raw response parsing from Level 1 are completely hidden inside `InventoryClientStub`.

### Level 3 — Advanced

```java
// File: StubTranslatesRemoteFailure.java -- the stub also translates a
// REMOTE failure into a normal, typed EXCEPTION -- exactly how a local
// method call's failure would surface, completing the illusion.
import java.util.*;

public class StubTranslatesRemoteFailure {
    static Map<String, Integer> stock = new HashMap<>(Map.of("widget", 5));

    static class SkuNotFoundException extends RuntimeException { // a normal, typed exception
        SkuNotFoundException(String sku) { super("no such SKU: " + sku); }
    }

    interface InventoryClient {
        int checkStock(String sku); // throws SkuNotFoundException -- just like a local method would
    }

    static class InventoryClientStub implements InventoryClient {
        public int checkStock(String sku) {
            RemoteResult result = sendRawRequest("checkStock", sku);
            if (result.errorCode() != null) {
                if (result.errorCode().equals("NOT_FOUND")) throw new SkuNotFoundException(sku); // translate!
                throw new RuntimeException("unexpected remote error: " + result.errorCode());
            }
            return Integer.parseInt(result.body());
        }
        private record RemoteResult(String body, String errorCode) {}
        private RemoteResult sendRawRequest(String procedureName, String arg) {
            if (!stock.containsKey(arg)) return new RemoteResult(null, "NOT_FOUND"); // simulated remote error
            return new RemoteResult(String.valueOf(stock.get(arg)), null);
        }
    }

    public static void main(String[] args) {
        InventoryClient inventoryClient = new InventoryClientStub();

        int found = inventoryClient.checkStock("widget");
        System.out.println("Stock for widget: " + found);

        try {
            inventoryClient.checkStock("nonexistent-sku");
        } catch (SkuNotFoundException e) {
            System.out.println("Caught local-looking exception: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac StubTranslatesRemoteFailure.java && java StubTranslatesRemoteFailure` (JDK 17+).

Expected output:
```
Stock for widget: 5
Caught local-looking exception: no such SKU: nonexistent-sku
```

## 6. Walkthrough

1. **Level 1** — `sendRawRequest` simulates a raw network call: the caller passes the procedure's name as a string and its argument, and gets back an unstructured raw response. `main` has to know to parse that response with `Integer.parseInt` itself — every piece of the RPC mechanics is exposed directly to the calling code.
2. **Level 2 — hiding the mechanics behind a stub** — `InventoryClient` is a plain interface with a normal-looking `checkStock(String sku)` signature; `InventoryClientStub` implements it, and *internally* calls `sendRawRequest` and parses the result — but none of that internal work is visible to `main`. `main`'s call, `inventoryClient.checkStock("widget")`, looks and reads exactly like a call to any ordinary local method, even though a network round-trip (simulated here, but structurally the same as a real one) is happening underneath.
3. **Level 3 — translating remote failure into a local-looking exception** — `sendRawRequest` now returns a `RemoteResult` that can carry an `errorCode` alongside (or instead of) a body, simulating what a real RPC transport error response looks like. `checkStock` checks for that error code and, if present, throws `SkuNotFoundException` — a plain Java exception the caller can catch with an ordinary `try`/`catch`, with no knowledge that the failure actually originated from a remote server rather than local logic.
4. **Tracing `main`'s two calls** — `inventoryClient.checkStock("widget")` calls `sendRawRequest`, which finds `"widget"` in `stock` and returns a `RemoteResult` with a body and no error code; `checkStock` sees `errorCode() == null`, so it skips the exception-throwing branch and returns `Integer.parseInt(result.body())`, which `main` prints directly. `inventoryClient.checkStock("nonexistent-sku")` calls `sendRawRequest`, which finds no entry for that sku and returns a `RemoteResult` with `errorCode = "NOT_FOUND"`; `checkStock` sees the error code, matches the `"NOT_FOUND"` case, and throws `SkuNotFoundException("nonexistent-sku")` — `main`'s `try`/`catch` catches it and prints the caught message.
5. **What makes this genuinely RPC, not just "a client library"** — the defining characteristic demonstrated across all three levels is progressive concealment of the network: by Level 3, `main`'s code contains zero references to serialization, raw responses, or network error codes — every interaction with `InventoryClient` reads and behaves exactly as if `InventoryService` were a local object, including how its failures surface as ordinary typed exceptions. This is precisely the ergonomic promise RPC frameworks like gRPC deliver via generated code, built from a shared interface definition (see [Protocol Buffers IDL](0090-protocol-buffers-protobuf-idl.md)).

## 7. Gotchas & takeaways

> **Gotcha:** making a remote call *look* exactly like a local call is also RPC's biggest trap — a local method call is essentially free and instantaneous, while a remote call carries real network latency, can partially fail in ways a local call never can (see [failure propagation across synchronous chains](0098-failure-propagation-across-synchronous-chains.md)), and needs its own timeout and retry handling. Never let RPC's ergonomic illusion cause a caller to reason about a remote call as if it carried the same reliability guarantees as an in-process one.

- RPC centers the API around procedures (actions) rather than resources (nouns), which fits naturally for operations that don't map cleanly onto REST's resource model.
- A generated client stub is what makes the remote call read like a local one — it hides serialization, the network round trip, and response parsing behind a plain method signature.
- Translating remote failures into normal, typed exceptions (as `SkuNotFoundException` does here) completes the local-call illusion, letting callers use ordinary `try`/`catch` error handling.
- The tradeoff for this ergonomic convenience is tighter coupling — RPC clients typically need a generated stub built from the exact, versioned service definition, unlike REST's looser, documentation-driven client compatibility.
- See [gRPC and HTTP/2](0089-grpc-and-http-2.md) for the concrete, modern implementation of this RPC model used throughout most microservices systems today.
