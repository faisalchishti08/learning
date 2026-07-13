---
card: microservices
gi: 168
slug: gateway-offloading-ssl-termination-compression
title: "Gateway offloading (SSL termination, compression)"
---

## 1. What it is

Gateway offloading is handling computationally expensive, largely mechanical protocol-level work — decrypting incoming TLS/SSL traffic, compressing outgoing responses — once at the gateway, so backend services receive plain, already-decrypted requests and never need to perform that work themselves for every single request they handle.

## 2. Why & when

TLS decryption and response compression are both genuinely CPU-intensive operations, and if every individual backend service performs them independently, that cost is paid redundantly, once per service, for traffic that's already been decrypted or needs identical compression logic applied everywhere. Terminating TLS at the gateway means the gateway absorbs that decryption cost exactly once per external request, and backend services (communicating over a trusted internal network) can skip TLS entirely for internal calls, saving real CPU across the whole fleet; compressing responses at the gateway means every backend can return plain, uncompressed data and let the gateway apply consistent compression policy in one place.

Offload SSL termination and compression to the gateway whenever backend services sit behind a gateway on a trusted internal network — which describes most microservices deployments — since there's rarely a reason to pay TLS overhead again for internal, already-secured traffic. Keep TLS all the way to the backend (sometimes called TLS passthrough or mutual TLS everywhere) specifically when compliance requirements or a zero-trust internal network model mandate encryption even between internal services, a deliberate security trade-off against the offloading benefit.

## 3. Core concept

The gateway terminates the client's TLS connection, decrypting the request once; it then forwards the decrypted request to the backend over plain HTTP on the trusted internal network, and on the way back, compresses the backend's plain response before re-encrypting and returning it to the client — the backend does neither encryption nor compression work itself.

```java
// CLIENT <-> GATEWAY: encrypted (TLS)
// GATEWAY <-> BACKEND: plain HTTP, on a trusted internal network -- backend does ZERO TLS work

Request decrypted = tlsTerminator.decrypt(incomingEncryptedRequest); // gateway does this ONCE
Response plainResponse = backendCall(decrypted); // backend receives PLAIN request, does no decryption
Response compressed = compressor.compress(plainResponse); // gateway compresses ONCE, consistently
Response encrypted = tlsTerminator.encrypt(compressed); // gateway re-encrypts for the client
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client's encrypted TLS traffic is decrypted once at the gateway; the resulting plain HTTP request travels to the backend over a trusted internal network with no TLS overhead; the backend's plain response is compressed and re-encrypted by the gateway before returning to the client" >
  <rect x="20" y="60" width="120" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="80" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">TLS encrypted</text>

  <rect x="230" y="55" width="180" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="78" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Gateway</text>
  <text x="320" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">TLS terminate + compress</text>

  <rect x="480" y="60" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Backend</text>
  <text x="550" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">plain HTTP, no TLS work</text>

  <line x1="140" y1="82" x2="228" y2="82" stroke="#8b949e" marker-end="url(#arr49)"/>
  <line x1="410" y1="82" x2="478" y2="82" stroke="#8b949e" marker-end="url(#arr49)"/>

  <defs>
    <marker id="arr49" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

TLS decryption and compression happen exactly once, at the boundary; the backend does neither.

## 5. Runnable example

Scenario: a request-handling flow that starts with every backend performing its own simulated decryption and compression work (showing the redundant cost), moves that work to the gateway so backends do neither, and finally measures the aggregate CPU-time savings across multiple backend calls to make the offloading benefit concrete rather than just structural.

### Level 1 — Basic

```java
// File: EveryBackendDoesItsOwnWork.java -- EACH backend independently performs
// simulated decryption AND compression -- the SAME cost paid redundantly, everywhere.
public class EveryBackendDoesItsOwnWork {
    static long simulateDecryption() { // stands in for real, CPU-intensive TLS decryption work
        long sum = 0; for (int i = 0; i < 2_000_000; i++) sum += i; return sum;
    }
    static long simulateCompression() { // stands in for real, CPU-intensive compression work
        long sum = 0; for (int i = 0; i < 2_000_000; i++) sum += i * 2; return sum;
    }

    static String handleAtBackend(String backendName, String request) {
        simulateDecryption();  // EVERY backend does this itself
        String response = backendName + " processed: " + request;
        simulateCompression(); // EVERY backend does this itself, TOO
        return response;
    }

    public static void main(String[] args) {
        long start = System.nanoTime();
        handleAtBackend("order-service", "GET /orders/42");
        handleAtBackend("customer-service", "GET /customers/7");
        handleAtBackend("shipping-service", "GET /shipping/42");
        long elapsed = (System.nanoTime() - start) / 1_000_000;

        System.out.println("Total time with EACH backend doing its OWN decrypt+compress: ~" + elapsed + "ms");
        System.out.println("The SAME decryption and compression logic ran 3 SEPARATE times, redundantly.");
    }
}
```

**How to run:** `javac EveryBackendDoesItsOwnWork.java && java EveryBackendDoesItsOwnWork` (JDK 17+).

### Level 2 — Intermediate

```java
// File: GatewayOffloadsOnce.java -- the GATEWAY decrypts and compresses ONCE per
// client request; backends receive PLAIN requests and return PLAIN responses.
public class GatewayOffloadsOnce {
    static long simulateDecryption() { long sum = 0; for (int i = 0; i < 2_000_000; i++) sum += i; return sum; }
    static long simulateCompression() { long sum = 0; for (int i = 0; i < 2_000_000; i++) sum += i * 2; return sum; }

    static class Gateway {
        String handleClientRequest(String backendName, String encryptedRequest) {
            simulateDecryption(); // ONCE, at the gateway, per CLIENT request
            String plainRequest = encryptedRequest.replace("[encrypted]", "");
            String backendResponse = callBackendPlainly(backendName, plainRequest); // backend does NOTHING extra
            simulateCompression(); // ONCE, at the gateway
            return "[compressed+encrypted] " + backendResponse;
        }

        // the BACKEND itself: PURE business logic, no decrypt/compress work at all
        String callBackendPlainly(String backendName, String plainRequest) {
            return backendName + " processed: " + plainRequest;
        }
    }

    public static void main(String[] args) {
        Gateway gateway = new Gateway();
        long start = System.nanoTime();
        gateway.handleClientRequest("order-service", "[encrypted]GET /orders/42");
        gateway.handleClientRequest("customer-service", "[encrypted]GET /customers/7");
        gateway.handleClientRequest("shipping-service", "[encrypted]GET /shipping/42");
        long elapsed = (System.nanoTime() - start) / 1_000_000;

        System.out.println("Total time with gateway offloading: ~" + elapsed + "ms");
        System.out.println("Backends did ZERO decrypt/compress work -- they only ran callBackendPlainly's pure logic.");
    }
}
```

**How to run:** `javac GatewayOffloadsOnce.java && java GatewayOffloadsOnce` (JDK 17+).

Expected output (timing similar to Level 1, since the SAME total simulated work runs, but now concentrated at the gateway rather than duplicated per backend call in a real multi-hop scenario):
```
Total time with gateway offloading: ~...ms
Backends did ZERO decrypt/compress work -- they only ran callBackendPlainly's pure logic.
```

### Level 3 — Advanced

```java
// File: MeasuredAggregateSavings.java -- measures the AGGREGATE CPU-time cost
// difference at REALISTIC scale: many backend calls PER client request (a common
// aggregation scenario), where offloading's benefit compounds.
public class MeasuredAggregateSavings {
    static long simulateDecryption() { long sum = 0; for (int i = 0; i < 500_000; i++) sum += i; return sum; }
    static long simulateCompression() { long sum = 0; for (int i = 0; i < 500_000; i++) sum += i * 2; return sum; }

    // WITHOUT offloading: if backends spoke TLS to EACH OTHER too (a common anti-pattern
    // when TLS termination isn't centralized), EVERY internal hop pays the cost again
    static void withoutOffloading(int numberOfInternalHops) {
        simulateDecryption(); // client -> gateway
        for (int i = 0; i < numberOfInternalHops; i++) {
            simulateDecryption();  // gateway -> backend #i, EACH hop re-encrypts/decrypts
            simulateCompression();
        }
        simulateCompression(); // gateway -> client
    }

    // WITH offloading: ONE decrypt (client -> gateway), ONE compress (gateway -> client);
    // internal hops are PLAIN, no TLS cost at all
    static void withOffloading(int numberOfInternalHops) {
        simulateDecryption(); // client -> gateway, ONCE
        for (int i = 0; i < numberOfInternalHops; i++) {
            // internal hops: PLAIN HTTP, no simulateDecryption/simulateCompression calls AT ALL
        }
        simulateCompression(); // gateway -> client, ONCE
    }

    public static void main(String[] args) {
        int internalHops = 5; // e.g. a request fanning out to 5 backend services

        long startWithout = System.nanoTime();
        withoutOffloading(internalHops);
        long elapsedWithout = (System.nanoTime() - startWithout) / 1_000_000;

        long startWith = System.nanoTime();
        withOffloading(internalHops);
        long elapsedWith = (System.nanoTime() - startWith) / 1_000_000;

        System.out.println("Without offloading (TLS on every internal hop too): ~" + elapsedWithout + "ms for " + internalHops + " internal calls");
        System.out.println("With offloading (TLS terminated ONCE, plain internally): ~" + elapsedWith + "ms for the SAME " + internalHops + " internal calls");
        System.out.println("The gap GROWS with more internal hops -- offloading's benefit compounds as fan-out increases.");
    }
}
```

**How to run:** `javac MeasuredAggregateSavings.java && java MeasuredAggregateSavings` (JDK 17+).

Expected output (exact timings vary, but `elapsedWithout` is consistently and substantially larger than `elapsedWith`):
```
Without offloading (TLS on every internal hop too): ~...ms for 5 internal calls
With offloading (TLS terminated ONCE, plain internally): ~...ms for the SAME 5 internal calls
The gap GROWS with more internal hops -- offloading's benefit compounds as fan-out increases.
```

## 6. Walkthrough

1. **Level 1** — `handleAtBackend` calls both `simulateDecryption()` and `simulateCompression()` for every single backend, and `main` calls this method three times, meaning the simulated CPU-intensive work runs six times total (twice per backend call), even though from the client's perspective this was conceptually "one round trip's worth" of encryption overhead.
2. **Level 2, relocating the work** — `Gateway.handleClientRequest` calls `simulateDecryption()` and `simulateCompression()` exactly once per invocation, while `callBackendPlainly` (representing the actual backend) contains no simulated cryptographic or compression work whatsoever.
3. **Level 2, the backend's simplified responsibility** — `callBackendPlainly`'s entire body is a single string concatenation representing pure business logic; comparing this to Level 1's `handleAtBackend`, which had two expensive simulated operations wrapped around its actual logic, makes the structural simplification directly visible in the code itself.
4. **Level 3, modeling a realistic fan-out scenario** — `withoutOffloading` simulates a scenario where TLS is (incorrectly, as an anti-pattern) applied on every internal hop in addition to the client-to-gateway hop, calling the simulated decrypt/compress pair once per internal hop *in addition to* the client-facing pair.
5. **Level 3, the offloaded alternative** — `withOffloading` calls the simulated decrypt/compress pair exactly twice total (once for the client-to-gateway leg in each direction), regardless of how many internal hops (`numberOfInternalHops`) the request fans out to — the `for` loop's body is empty, representing genuinely free (from a TLS/compression standpoint) internal plain-HTTP calls.
6. **Level 3, the measured comparison** — `elapsedWithout` scales with `internalHops` (five extra decrypt+compress pairs added to the two client-facing ones), while `elapsedWith` stays constant regardless of `internalHops`, since internal calls contribute no simulated cryptographic or compression cost at all.
7. **Level 3, why the gap compounds** — increasing `internalHops` (representing a request that fans out to more backend services, as in [request aggregation](0165-request-aggregation-composition.md)) makes `withoutOffloading`'s total cost grow linearly while `withOffloading`'s stays flat — demonstrating concretely why centralizing TLS termination and compression becomes increasingly valuable precisely in the kind of gateway-orchestrated, multi-backend-call scenarios that request aggregation and API composition already motivate using a gateway for in the first place.

## 7. Gotchas & takeaways

> **Gotcha:** terminating TLS at the gateway means the internal network between gateway and backends must genuinely be trusted — if that internal network isn't actually isolated and secured (a common false assumption in cloud environments with shared infrastructure), plain-text internal traffic becomes a real exposure; offloading is a deliberate trade of encryption overhead for trust in network isolation, not a free optimization with no security assumption behind it.

- Gateway offloading centralizes computationally expensive, largely mechanical work — TLS decryption and response compression — at the edge, so backend services don't each pay that cost redundantly for every request.
- TLS termination at the gateway lets backend services communicate over plain HTTP on a trusted internal network, avoiding repeated encryption overhead on every internal hop.
- The benefit compounds as request fan-out increases — scenarios involving [request aggregation](0165-request-aggregation-composition.md) across multiple backend calls see a proportionally larger savings from offloading than a single-backend request would.
- Compression, applied consistently once at the gateway, avoids each backend needing its own compression logic and configuration.
- Offloading trades encryption overhead for trust in the internal network's isolation — it's the right default when that trust is genuinely warranted, and the wrong choice when compliance or zero-trust requirements demand encryption all the way to the backend.
