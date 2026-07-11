---
card: spring-cloud
gi: 47
slug: tls-ssl
title: "TLS & SSL"
---

## 1. What it is

Gateway can terminate TLS on the client-facing side (accepting `https://` connections from callers using a certificate configured on the gateway itself) and separately decide whether to use TLS on the backend-facing side (talking to backend services over plain HTTP inside a trusted network, or re-encrypting with its own client certificate for mutual TLS).

```yaml
server:
  ssl:
    enabled: true
    key-store: classpath:gateway-keystore.p12
    key-store-password: ${KEYSTORE_PASSWORD}
    key-store-type: PKCS12

spring:
  cloud:
    gateway:
      routes:
        - id: orders-route
          uri: https://orders-service.internal:8443  # TLS re-established to the backend too
```

## 2. Why & when

A gateway sitting at the network edge is exactly where TLS termination belongs: it's the one place external traffic enters the system, so it's the natural place to hold the public-facing certificate, decrypt incoming HTTPS, and decide what happens next — plain HTTP within a trusted internal network (simpler, faster, common inside a single VPC) or re-encrypted TLS all the way to the backend (defense in depth, required by some compliance regimes, essential for zero-trust network models).

Configure TLS deliberately based on:

- Whether external clients require HTTPS (almost always yes for anything public-facing) — the gateway holds the public certificate so individual backend services don't each need their own.
- Whether the internal network between gateway and backends is itself trusted — many deployments terminate TLS at the gateway and use plain HTTP internally, accepting that tradeoff for simplicity and performance.
- Whether compliance or zero-trust requirements mandate encryption in transit even for internal, same-network traffic — in which case the gateway re-establishes TLS (possibly mutual TLS) to each backend.

## 3. Core concept

```
 client --- HTTPS (TLS terminated here, using gateway's cert) ---> Gateway
                                                                        |
                                     Gateway ------- backend connection -------> backend
                                          (plain HTTP, trusted network)
                                                   OR
                                          (re-encrypted HTTPS/mTLS, zero-trust)
```

TLS termination and the choice of backend transport are two independent decisions — a gateway can (and often does) speak encrypted HTTPS outward while speaking plain HTTP or a separately-configured TLS connection inward.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client connects over HTTPS to the gateway, which terminates TLS there and then connects onward to the backend either over plain HTTP inside a trusted network or over re-established TLS">
  <rect x="20" y="70" width="120" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">client</text>

  <line x1="140" y1="90" x2="230" y2="90" stroke="#6db33f" stroke-width="1.6" marker-end="url(#a47)"/>
  <text x="185" y="80" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">HTTPS</text>

  <rect x="235" y="60" width="170" height="60" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Gateway</text>
  <text x="320" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">TLS terminated here</text>

  <line x1="405" y1="80" x2="475" y2="50" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a47)"/>
  <text x="450" y="40" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">plain HTTP (trusted net)</text>
  <rect x="480" y="25" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="550" y="46" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">orders-service</text>

  <line x1="405" y1="100" x2="475" y2="130" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a47)"/>
  <text x="450" y="150" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">re-encrypted TLS/mTLS</text>
  <rect x="480" y="115" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="550" y="136" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billing-service</text>

  <defs><marker id="a47" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The client-facing hop is always encrypted; the backend-facing hop is a separate, independently configured decision.

## 5. Runnable example

The scenario: model a gateway deciding, per route, whether to re-encrypt to the backend. Start with a plain HTTP-only model, then add TLS termination awareness at the client edge, then add per-route backend transport policy including mutual TLS for a sensitive route.

### Level 1 — Basic

Plain HTTP end to end — the baseline with no TLS modeling at all.

```java
public class TlsSslLevel1 {
    record Route(String id, String backendUri) {}

    public static void main(String[] args) {
        Route ordersRoute = new Route("orders-route", "http://orders-service:8080");
        System.out.println("forwarding to: " + ordersRoute.backendUri());
    }
}
```

How to run: `java TlsSslLevel1.java`

No encryption modeled anywhere — useful as a baseline, but doesn't reflect the reality that the client-facing hop virtually always needs TLS.

### Level 2 — Intermediate

Model TLS termination at the client edge: the gateway accepts HTTPS from clients, decrypts, then forwards over plain HTTP internally.

```java
public class TlsSslLevel2 {
    record ClientRequest(String scheme, String path) {}
    record Route(String id, String backendUri) {}

    static ClientRequest terminateTls(ClientRequest incoming, String gatewayCertSubject) {
        if (!"https".equals(incoming.scheme())) {
            throw new IllegalStateException("gateway requires HTTPS from clients");
        }
        System.out.println("[TLS] terminated using cert: " + gatewayCertSubject);
        return incoming; // decrypted content now available for routing
    }

    public static void main(String[] args) {
        ClientRequest incoming = new ClientRequest("https", "/orders/42");
        ClientRequest decrypted = terminateTls(incoming, "CN=api.example.com");

        Route ordersRoute = new Route("orders-route", "http://orders-service:8080"); // plain HTTP internally
        System.out.println("forwarding " + decrypted.path() + " to: " + ordersRoute.backendUri() + " (plain HTTP, trusted network)");
    }
}
```

How to run: `java TlsSslLevel2.java`

`terminateTls` models the gateway's TLS handshake completing using its own certificate (`CN=api.example.com`) before the request's actual content is available for routing — from that point forward, the gateway forwards over plain HTTP, a common and reasonable choice when the backend network is itself trusted (a private VPC, a service mesh with its own network-layer protections).

### Level 3 — Advanced

Add per-route backend transport policy: most routes stay plain HTTP internally, but a sensitive `payments` route re-encrypts using mutual TLS, verifying both sides' certificates.

```java
import java.util.*;

public class TlsSslLevel3 {
    record ClientRequest(String scheme, String path) {}

    enum BackendTransport { PLAIN_HTTP, TLS, MUTUAL_TLS }

    record Route(String id, String backendUri, BackendTransport transport) {}

    static ClientRequest terminateTls(ClientRequest incoming) {
        if (!"https".equals(incoming.scheme())) throw new IllegalStateException("gateway requires HTTPS from clients");
        return incoming;
    }

    static String forward(Route route, ClientRequest req, String gatewayClientCertSubject) {
        return switch (route.transport()) {
            case PLAIN_HTTP -> "HTTP  " + route.backendUri() + req.path() + " (no re-encryption)";
            case TLS -> "HTTPS " + route.backendUri() + req.path() + " (gateway verifies backend cert)";
            case MUTUAL_TLS -> "HTTPS " + route.backendUri() + req.path()
                    + " (mutual TLS -- gateway presents " + gatewayClientCertSubject + ", backend verifies it too)";
        };
    }

    public static void main(String[] args) {
        Map<String, Route> routes = Map.of(
                "/orders/", new Route("orders-route", "http://orders-service:8080", BackendTransport.PLAIN_HTTP),
                "/payments/", new Route("payments-route", "https://payments-service:8443", BackendTransport.MUTUAL_TLS)
        );

        List<String> incomingPaths = List.of("/orders/42", "/payments/99");
        for (String path : incomingPaths) {
            ClientRequest req = terminateTls(new ClientRequest("https", path));
            Route matched = routes.entrySet().stream()
                    .filter(e -> path.startsWith(e.getKey())).map(Map.Entry::getValue).findFirst().orElseThrow();
            System.out.println(forward(matched, req, "CN=gateway-internal.example.com"));
        }
    }
}
```

How to run: `java TlsSslLevel3.java`

`/orders/42` matches `orders-route`, configured `PLAIN_HTTP` — the gateway forwards it internally without re-encryption, appropriate for a trusted internal network segment. `/payments/99` matches `payments-route`, configured `MUTUAL_TLS` — the gateway re-establishes an encrypted connection *and* presents its own client certificate for the backend to verify, ensuring only the genuine gateway (not an arbitrary caller inside the network) can reach the payments backend, a materially stronger guarantee appropriate for a sensitive route.

## 6. Walkthrough

Trace both requests through Level 3.

1. `terminateTls` runs for `/orders/42` first — it checks `incoming.scheme() == "https"`, which is true (all client-facing traffic is HTTPS in this model), so it passes through unchanged. This models the gateway's TLS handshake with the client completing successfully using the gateway's public certificate.
2. The route lookup finds `orders-route`, configured with `BackendTransport.PLAIN_HTTP`. `forward` matches the `PLAIN_HTTP` case and produces a plain `HTTP` connection string to `orders-service:8080` — no re-encryption happens for this hop, a deliberate choice reflecting a trusted internal network.
3. The same `terminateTls` check runs for `/payments/99`, again passing (the client connection is HTTPS either way, regardless of which backend route it eventually matches).
4. The route lookup finds `payments-route`, configured with `BackendTransport.MUTUAL_TLS`. `forward` matches the `MUTUAL_TLS` case: it produces an `HTTPS` connection string to `payments-service:8443`, and critically notes that the gateway presents its own client certificate (`CN=gateway-internal.example.com`) as part of the handshake — the payments backend can then verify that certificate against a trusted CA before accepting the connection, rejecting any caller inside the network that isn't the genuine gateway.
5. The two printed lines make the divergence concrete: identical routing logic, but one hop trusts the network and skips re-encryption, while the other treats the network as untrusted and requires both sides to prove their identity.

```
/orders/42   -> orders-route  (PLAIN_HTTP)   -> plain HTTP to orders-service, no re-encryption
/payments/99 -> payments-route (MUTUAL_TLS)  -> re-encrypted HTTPS, gateway presents its own cert,
                                                  backend verifies it before accepting the connection
```

## 7. Gotchas & takeaways

> **Gotcha:** terminating TLS at the gateway means the gateway itself now holds the private key for the public certificate — a compromise of the gateway process or its keystore is a compromise of the ability to impersonate the service to every client. Keystore secrets (as in section 1's `${KEYSTORE_PASSWORD}`) should come from a secrets manager or environment injection, never committed to source control.

- TLS termination (client-facing) and backend transport choice (internal) are independent configuration decisions — a gateway can, and very often does, use different security postures for each hop.
- Plain HTTP internally is a reasonable, common choice when the internal network itself is trusted (a private VPC, an isolated Kubernetes cluster network) — it's simpler and has less latency/CPU overhead than re-encrypting every hop.
- Mutual TLS on specific sensitive routes (payments, PII-handling services) adds real defense in depth: even an attacker who gains network access inside the trusted zone still can't impersonate the gateway without its private key.
- A zero-trust network model treats every hop as potentially untrusted, which pushes toward TLS (often mutual TLS) everywhere — the right choice depends on the organization's actual threat model, not a one-size-fits-all default.
