---
card: spring-integration
gi: 68
slug: rmi-legacy
title: "RMI (legacy)"
---

## 1. What it is

RMI support (`Rmi.inboundGateway(...)`/`Rmi.outboundGateway(...)`) connects a flow to Java Remote Method Invocation — a protocol that lets one JVM call a method on an object living in another JVM as though it were a local call, serializing the arguments and return value across the network transparently. It predates HTTP-based service invocation in the Spring Integration adapter lineup and is explicitly marked legacy: newer flows reach for HTTP (card 0054) or a message broker instead.

## 2. Why & when

You reach for RMI support in one narrow situation: interoperating with an existing system that already exposes or consumes RMI, and where introducing a new protocol isn't worth the migration cost:

- **An existing internal system already speaks RMI** — some older Java-only internal services were built on RMI before REST and messaging became the default; a flow bridging to one of them without rewriting it uses `Rmi.outboundGateway` to call it, or `Rmi.inboundGateway` to expose a flow as an RMI-invokable target for it.
- **Both ends are guaranteed to be Java** — RMI's wire format is Java's native object serialization, so both caller and callee must be JVMs; it cannot interoperate with a non-Java client the way HTTP or AMQP can.
- **New integrations should not choose RMI** — for anything not constrained by an existing RMI-only system, HTTP, gRPC, or a message broker offers broader interoperability, better tooling, and avoids Java serialization's well-documented security exposure.

## 3. Core concept

Think of a normal local method call as walking into a colleague's office and asking a question face to face — instant, no translation needed. RMI is like a special phone line wired specifically between two Java offices: you dial it, the words get faithfully carried across (via Java serialization), and it feels almost like you're in the same room — but that phone line only works between two people who speak the exact same internal language (Java objects), and it can't be handed to someone speaking a different vocabulary (a non-Java client).

```java
@Bean
public IntegrationFlow rmiOutboundFlow() {
    return IntegrationFlow.from("legacyLookupRequests")
        .handle(Rmi.outboundGateway("rmi://legacy-host:1099/AccountLookupService"))
        .get();
}
```

A message sent to `legacyLookupRequests` is serialized, sent over RMI to the named remote object, and the deserialized return value comes back as the reply — bridging a modern flow to an old RMI-only service without rewriting it.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RMI outbound gateway serializes a message, invokes a remote Java object over RMI, and deserializes the reply, working only between two JVMs" >
  <rect x="20" y="30" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Flow (JVM A)</text>
  <text x="110" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Rmi.outboundGateway</text>

  <line x1="200" y1="45" x2="420" y2="45" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arrow2)"/>
  <text x="310" y="38" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">Java-serialized call</text>
  <line x1="420" y1="70" x2="200" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arrow2)"/>
  <text x="310" y="88" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">Java-serialized reply</text>

  <rect x="420" y="30" width="200" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="520" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Legacy service (JVM B)</text>
  <text x="520" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">exported RMI remote object</text>

  <text x="320" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Both ends must be JVMs — RMI's wire format is Java's own serialization, not a portable format like JSON.</text>
  <defs><marker id="arrow2" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
</svg>

RMI feels like a local call across the network, but only ever between two Java processes.

## 5. Runnable example

The scenario: bridging a modern flow to a legacy account-lookup service, simulated with a plain local method call standing in for the RMI round trip (genuinely runnable without an RMI registry, since the point is the bridging logic, not RMI's wire mechanics), starting with a direct call, then adding a timeout for an unresponsive legacy service, then adding a fallback when the legacy call fails outright.

### Level 1 — Basic

```java
// RmiBridgeDemo.java
public class RmiBridgeDemo {
    // Stand-in for a remote object reached via Rmi.outboundGateway("rmi://host:1099/AccountLookupService")
    static class LegacyAccountLookupService {
        String lookup(String accountId) { return "Account[" + accountId + "]: balance=1000.00"; }
    }

    public static void main(String[] args) {
        LegacyAccountLookupService service = new LegacyAccountLookupService();
        String result = service.lookup("ACC-42");
        System.out.println("Lookup result: " + result);
    }
}
```

How to run: `java RmiBridgeDemo.java`. Expected output: `Lookup result: Account[ACC-42]: balance=1000.00` — the bridging call, standing in for what an `Rmi.outboundGateway` does over the wire.

### Level 2 — Intermediate

```java
// RmiBridgeDemo.java
import java.util.concurrent.*;

public class RmiBridgeDemo {
    static class LegacyAccountLookupService {
        String lookup(String accountId) throws InterruptedException {
            Thread.sleep(300); // simulates a slow legacy service call over the network
            return "Account[" + accountId + "]: balance=1000.00";
        }
    }

    // Real-world concern: RMI calls are still remote calls -- they can hang. A production
    // outbound gateway configures a receive timeout so a slow legacy service can't stall the flow.
    static String lookupWithTimeout(LegacyAccountLookupService service, String accountId, long timeoutMillis)
            throws Exception {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<String> future = executor.submit(() -> service.lookup(accountId));
        try {
            return future.get(timeoutMillis, TimeUnit.MILLISECONDS);
        } finally {
            executor.shutdownNow();
        }
    }

    public static void main(String[] args) throws Exception {
        LegacyAccountLookupService service = new LegacyAccountLookupService();
        String result = lookupWithTimeout(service, "ACC-42", 1000);
        System.out.println("Lookup result: " + result);
    }
}
```

How to run: `java RmiBridgeDemo.java`. Expected output: `Lookup result: Account[ACC-42]: balance=1000.00`, returned within the 1000ms timeout window — demonstrating the timeout wrapper a real RMI outbound gateway configuration applies so a slow or hung legacy service can't stall the calling flow indefinitely.

### Level 3 — Advanced

```java
// RmiBridgeDemo.java
import java.util.concurrent.*;

public class RmiBridgeDemo {
    static class LegacyAccountLookupService {
        boolean shouldFail;
        LegacyAccountLookupService(boolean shouldFail) { this.shouldFail = shouldFail; }
        String lookup(String accountId) throws InterruptedException {
            Thread.sleep(300);
            if (shouldFail) throw new RuntimeException("legacy service unreachable");
            return "Account[" + accountId + "]: balance=1000.00";
        }
    }

    static String lookupWithTimeout(LegacyAccountLookupService service, String accountId, long timeoutMillis)
            throws Exception {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<String> future = executor.submit(() -> service.lookup(accountId));
        try {
            return future.get(timeoutMillis, TimeUnit.MILLISECONDS);
        } finally {
            executor.shutdownNow();
        }
    }

    // Production concern: RMI's networked, Java-serialization-based call can fail in ways a
    // local call never would (connection refused, deserialization error, timeout) -- the
    // bridging flow needs an explicit fallback rather than propagating a raw remote exception.
    static String lookupWithFallback(LegacyAccountLookupService service, String accountId) {
        try {
            return lookupWithTimeout(service, accountId, 1000);
        } catch (Exception ex) {
            System.out.println("Legacy lookup failed (" + ex.getCause() + "), using fallback");
            return "Account[" + accountId + "]: balance=UNKNOWN (cached/default)";
        }
    }

    public static void main(String[] args) {
        LegacyAccountLookupService healthyService = new LegacyAccountLookupService(false);
        LegacyAccountLookupService downService = new LegacyAccountLookupService(true);

        System.out.println(lookupWithFallback(healthyService, "ACC-42"));
        System.out.println(lookupWithFallback(downService, "ACC-99"));
    }
}
```

How to run: `java RmiBridgeDemo.java`. Expected output: the first lookup succeeds normally; the second prints a `Legacy lookup failed (...)` message and falls back to an `UNKNOWN` balance default — the resilience pattern a production RMI bridge needs since a legacy service, and the network path to it, can fail in ways a local method call never does.

## 6. Walkthrough

Trace a request through an RMI-bridging flow end to end.

1. **Message arrives**: a request needing account data enters the flow's input channel, addressed to `legacyLookupRequests`.
2. **Outbound gateway invokes**: `Rmi.outboundGateway("rmi://legacy-host:1099/AccountLookupService")` serializes the message payload using Java's native serialization and sends it over the network to the RMI registry at the given host and port.
3. **Registry lookup**: the RMI registry on the legacy host resolves `AccountLookupService` to the actual exported remote object and forwards the invocation to it.
4. **Remote execution**: the legacy JVM executes its method, producing a return value, which RMI serializes and sends back over the same connection.
5. **Deserialization and reply**: the outbound gateway deserializes the reply into a Java object and emits it as the flow's reply message, continuing downstream exactly like any other gateway's response.
6. **Failure handling**: if the legacy host is unreachable, the call times out, or deserialization fails, the gateway raises an exception that the flow must handle explicitly — a fallback value, an error channel route, or a retry — since there's no way to distinguish "answer is null" from "the whole exchange failed" without that explicit handling.

```
message -> Rmi.outboundGateway
  -> serialize (Java native serialization)
    -> RMI registry lookup on legacy host
      -> remote method executes
        -> serialize return value
          -> deserialize locally -> reply message
             (or: timeout/exception -> fallback/error channel)
```

## 7. Gotchas & takeaways

> **Gotcha:** RMI's wire format is Java's native object serialization, which has well-documented deserialization-based security vulnerabilities when the remote end (or the network path) isn't fully trusted — RMI should only ever be used between systems on a trusted internal network, never exposed to untrusted or external clients.

- RMI only works JVM-to-JVM; it cannot be the integration point for anything written in a non-Java language, unlike HTTP, AMQP, or Kafka adapters.
- Treat RMI adapters as a bridge to be retired, not a foundation to build new integrations on — Spring's own documentation marks RMI support as legacy, present for compatibility with existing systems rather than as a recommended choice.
- Always configure explicit timeouts on an RMI outbound gateway; a networked call with no timeout can hang a flow indefinitely if the remote JVM stops responding.
- Because both ends must run compatible class definitions for serialization to succeed, RMI is more tightly coupled to the exact Java types on both sides than a JSON-based protocol would be — a class change on one side without redeploying the other can break the bridge outright.
