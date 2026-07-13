---
card: microservices
gi: 456
slug: sidecar-pattern
title: "Sidecar pattern"
---

## 1. What it is

The **sidecar pattern** deploys a helper process alongside a main application process — typically as a second container inside the same [Pod](0447-pods-deployments-services-ingress.md) — to handle a cross-cutting concern on the main application's behalf: logging, metrics collection, mTLS termination, configuration reloading, or proxying. The main application delegates that concern to its sidecar instead of implementing it itself, and the two are deployed, scaled, and (usually) share a network namespace together, but remain separate processes with a clear responsibility boundary between them.

## 2. Why & when

You reach for a sidecar when a concern is genuinely cross-cutting — needed by many services, largely identical in every service, and awkward to keep reimplementing or upgrading inside each one:

- **Cross-cutting concerns don't belong in business logic.** TLS termination, log shipping, and metrics export are the same problem in every service; implementing each one natively inside every service's codebase means N different implementations to test, secure, and upgrade instead of one.
- **A sidecar can be upgraded independently of the application it serves.** If the mTLS library needs a security patch, or the logging format needs to change, updating the sidecar image doesn't require touching, rebuilding, or redeploying application code at all.
- **It works uniformly across languages and frameworks.** A sidecar written once (often as part of a service mesh, like Envoy) provides the same TLS or observability behavior to a Java service, a Python service, and a Go service without each needing its own language-specific library for the concern.
- **You reach for this pattern for genuinely cross-cutting, infrastructure-level concerns** — not for business logic, which belongs in the main application, and not for concerns only one service needs, where the deployment overhead of a second container isn't worth it.

## 3. Core concept

A useful analogy is a motorcycle sidecar itself: it travels everywhere the motorcycle goes, shares its journey and its fate, but carries a separate kind of cargo and could — in principle — be swapped out for a different sidecar without touching the motorcycle's engine at all. The main application is the motorcycle, focused entirely on its own job; the sidecar rides alongside, handling something else, coupled in deployment but decoupled in implementation.

Concretely, the mechanics are:

1. **The sidecar runs as a separate process** — in Kubernetes, a second container in the same Pod, sharing the Pod's network namespace so the two can communicate over `localhost`.
2. **The main application delegates a specific concern** to the sidecar rather than implementing it: it makes a plain local call, and the sidecar does the harder work (wrapping it in mTLS, batching and shipping it to a log aggregator, exposing it as metrics).
3. **The two are deployed and scaled together** — when the Pod scales, both containers scale with it; when the Pod is replaced, both are replaced together. This is what distinguishes a sidecar from a wholly separate service.
4. **Failure handling must be deliberate, and differs by concern.** If the sidecar handling a *non-essential* concern (like logging) crashes, the main application should keep working without it (fail open). If the sidecar handling a *security-critical* concern (like mTLS termination) crashes, the main application must refuse to proceed insecurely rather than silently degrade (fail closed) — the two failure policies are opposite, and choosing the wrong one for a given concern is a real production risk.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A main application container delegates cross-cutting concerns to sidecar containers in the same pod over localhost, with different failure policies for non-critical versus security-critical sidecars">
  <rect x="20" y="30" width="600" height="150" rx="12" fill="#1c2430" stroke="#8b949e" stroke-dasharray="4,3"/>
  <text x="320" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">one Pod</text>

  <rect x="60" y="70" width="180" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="150" y="100" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="150" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">main application</text>

  <rect x="290" y="50" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="360" y="72" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">logging sidecar</text>
  <text x="360" y="88" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">fail OPEN if down</text>

  <rect x="290" y="115" width="140" height="50" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="360" y="137" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">mTLS sidecar</text>
  <text x="360" y="153" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">fail CLOSED if down</text>

  <line x1="240" y1="90" x2="290" y2="75" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="240" y1="105" x2="290" y2="140" stroke="#f85149" marker-end="url(#a2)"/>
  <text x="255" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">localhost</text>

  <rect x="470" y="80" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="530" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">external services</text>
  <line x1="430" y1="140" x2="470" y2="105" stroke="#f85149" stroke-dasharray="3,2"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f85149"/></marker>
  </defs>
</svg>

Both sidecars share the Pod with the main application and are reached over localhost, but they require opposite failure policies: the logging sidecar can fail open, while the mTLS sidecar must fail closed.

## 5. Runnable example

Scenario: an `order-service` main application delegating two concerns to sidecars. We start with a logging sidecar handling log shipping, add an mTLS sidecar handling secure transport for outbound calls, then handle the hard case: both sidecars crashing, requiring the application to apply two deliberately opposite failure policies — fail open for logging, fail closed for mTLS.

### Level 1 — Basic

```java
// File: SidecarLoggingBasic.java -- models the CORE idea: the main
// application container does ONLY its business logic; a separate,
// companion "sidecar" process/object handles a CROSS-CUTTING concern
// (here, structured logging) on the main container's behalf.
public class SidecarLoggingBasic {
    // The sidecar: a separate component, deployed alongside the main app,
    // responsible ONLY for the cross-cutting concern of log shipping.
    static class LoggingSidecar {
        void ship(String appName, String message) {
            System.out.println("[logging-sidecar] shipping to central log store: {app=" + appName + ", msg=\"" + message + "\"}");
        }
    }

    // The main application: knows NOTHING about how logs are transported,
    // stored, or formatted for the central system -- it just emits events.
    static class OrderServiceApp {
        final LoggingSidecar sidecar;
        OrderServiceApp(LoggingSidecar sidecar) { this.sidecar = sidecar; }

        void handleOrder(String orderId) {
            System.out.println("[order-service] processing " + orderId);
            sidecar.ship("order-service", "processed " + orderId);
        }
    }

    public static void main(String[] args) {
        LoggingSidecar sidecar = new LoggingSidecar();
        OrderServiceApp app = new OrderServiceApp(sidecar);

        app.handleOrder("order-1");
        app.handleOrder("order-2");
    }
}
```

How to run: `java SidecarLoggingBasic.java`

`OrderServiceApp` holds a reference to `LoggingSidecar` and delegates the "ship this to the central log store" concern entirely — it has no idea how logs are formatted, batched, or transported once they leave `ship()`. This is the core sidecar shape: the main application focuses purely on its own logic (`handleOrder`) and hands the cross-cutting concern off completely.

### Level 2 — Intermediate

```java
// File: SidecarMtlsProxy.java -- the SAME sidecar idea, now handling a
// DIFFERENT cross-cutting concern: mTLS termination. The main app speaks
// plain, unencrypted "localhost" calls to its sidecar; the sidecar is the
// only thing that actually establishes and terminates mutual TLS with the
// outside world. The app never touches certificates at all.
public class SidecarMtlsProxy {
    static class MtlsSidecar {
        final String serviceCert = "order-service-cert.pem"; // the sidecar owns cert material, not the app

        String sendOverMtls(String plainRequest, String destination) {
            System.out.println("[mtls-sidecar] wrapping request in mTLS using " + serviceCert + ", sending to " + destination);
            return "mtls-response-for(" + plainRequest + ")";
        }
    }

    static class OrderServiceApp {
        final MtlsSidecar sidecar;
        OrderServiceApp(MtlsSidecar sidecar) { this.sidecar = sidecar; }

        String callPaymentService(String orderId) {
            // The app makes a PLAIN call to its own sidecar over localhost --
            // it has no idea mTLS is even involved.
            System.out.println("[order-service] calling payment-service for " + orderId + " (plain call to localhost sidecar)");
            return sidecar.sendOverMtls("charge(" + orderId + ")", "payment-service");
        }
    }

    public static void main(String[] args) {
        OrderServiceApp app = new OrderServiceApp(new MtlsSidecar());
        String response = app.callPaymentService("order-1");
        System.out.println("[order-service] received: " + response);
    }
}
```

How to run: `java SidecarMtlsProxy.java`

`OrderServiceApp.callPaymentService` makes what looks like a completely ordinary local call to `sidecar.sendOverMtls`, with no certificates, no TLS handshake code, no knowledge of `payment-service`'s network location beyond a logical name. `MtlsSidecar` owns all of that complexity (`serviceCert` and everything a real mTLS handshake requires) — the same delegation shape as Level 1, applied to a security concern instead of an observability one, echoing the mutual TLS discipline from [Spring Security mTLS (X.509 authentication)](0407-spring-security-mtls-x-509-authentication.md).

### Level 3 — Advanced

```java
// File: SidecarFailureHandlingAdvanced.java -- the SAME two sidecars
// (logging and mTLS), now handling a PRODUCTION-FLAVORED hard case: the
// sidecar process CRASHES. The correct reaction is DIFFERENT for each
// sidecar: a logging sidecar should FAIL OPEN (the app keeps working,
// just without shipped logs -- losing logs is bad, but not as bad as
// refusing to serve). An mTLS sidecar should FAIL CLOSED (the app must
// REFUSE to send the request, because sending it without mTLS would leak
// data or allow an unauthenticated call -- a security regression is worse
// than a dropped request).
public class SidecarFailureHandlingAdvanced {
    static class LoggingSidecar {
        boolean healthy = true;
        void ship(String appName, String message) {
            if (!healthy) throw new IllegalStateException("logging sidecar unreachable");
            System.out.println("[logging-sidecar] shipped: " + message);
        }
    }

    static class MtlsSidecar {
        boolean healthy = true;
        String sendOverMtls(String plainRequest, String destination) {
            if (!healthy) throw new IllegalStateException("mtls sidecar unreachable");
            System.out.println("[mtls-sidecar] sent " + plainRequest + " to " + destination + " over mTLS");
            return "mtls-response-for(" + plainRequest + ")";
        }
    }

    static class OrderServiceApp {
        final LoggingSidecar loggingSidecar;
        final MtlsSidecar mtlsSidecar;
        OrderServiceApp(LoggingSidecar loggingSidecar, MtlsSidecar mtlsSidecar) {
            this.loggingSidecar = loggingSidecar; this.mtlsSidecar = mtlsSidecar;
        }

        void handleOrder(String orderId) {
            System.out.println("[order-service] processing " + orderId);

            // FAIL OPEN: a logging failure must never block the business operation.
            try {
                loggingSidecar.ship("order-service", "processed " + orderId);
            } catch (IllegalStateException e) {
                System.out.println("[order-service] logging sidecar down (" + e.getMessage() + ") -- continuing WITHOUT logs (fail open)");
            }

            // FAIL CLOSED: an mTLS failure must block the call, not silently send it insecurely.
            try {
                String response = mtlsSidecar.sendOverMtls("charge(" + orderId + ")", "payment-service");
                System.out.println("[order-service] payment response: " + response);
            } catch (IllegalStateException e) {
                System.out.println("[order-service] mTLS sidecar down (" + e.getMessage() + ") -- REFUSING to send unencrypted (fail closed), order " + orderId + " FAILS");
            }
        }
    }

    public static void main(String[] args) {
        LoggingSidecar loggingSidecar = new LoggingSidecar();
        MtlsSidecar mtlsSidecar = new MtlsSidecar();
        OrderServiceApp app = new OrderServiceApp(loggingSidecar, mtlsSidecar);

        System.out.println("--- both sidecars healthy ---");
        app.handleOrder("order-1");

        System.out.println();
        System.out.println("--- logging sidecar crashes ---");
        loggingSidecar.healthy = false;
        app.handleOrder("order-2");

        System.out.println();
        System.out.println("--- mTLS sidecar ALSO crashes ---");
        mtlsSidecar.healthy = false;
        app.handleOrder("order-3");
    }
}
```

How to run: `java SidecarFailureHandlingAdvanced.java`

`handleOrder` wraps each sidecar call in its own `try`/`catch`, but the two `catch` blocks do opposite things: the logging failure is caught, logged as a warning, and execution continues to the payment call regardless. The mTLS failure is caught, but the method explicitly reports the *order itself* as failed rather than falling through to any insecure alternative — there is no code path in this method that could accidentally send `charge(...)` without going through `mtlsSidecar`.

## 6. Walkthrough

Trace `SidecarFailureHandlingAdvanced.main` in order. **First**, `app.handleOrder("order-1")` runs with both sidecars healthy: `loggingSidecar.ship` succeeds and prints confirmation, then `mtlsSidecar.sendOverMtls` succeeds and returns a response, which is printed — the fully healthy path.

**Next**, `loggingSidecar.healthy` is set to `false`, and `app.handleOrder("order-2")` runs. Inside, `loggingSidecar.ship(...)` now throws `IllegalStateException`, which the `catch` block in the logging section handles by printing the "continuing WITHOUT logs (fail open)" message — execution then falls through to the mTLS section entirely normally, since `mtlsSidecar.healthy` is still `true`. `order-2`'s payment call succeeds exactly as before; only its logs are missing.

**Then**, `mtlsSidecar.healthy` is also set to `false`, and `app.handleOrder("order-3")` runs. The logging section behaves identically to the previous call (still down, still fails open). But now the mTLS section's `try` block also throws — `mtlsSidecar.sendOverMtls` sees `healthy == false` and throws its own `IllegalStateException`. This time the `catch` block does *not* attempt any fallback; it prints that the order fails outright, because there's no code path left that could deliver `charge("order-3")` to `payment-service` without going through the (now-down) mTLS sidecar.

**Finally**, comparing `order-2`'s outcome (succeeded, but unlogged) against `order-3`'s outcome (refused entirely) makes the two failure policies concrete: losing observability is tolerated, but losing the security guarantee is not — the code enforces that distinction structurally, not just as a comment.

```
--- both sidecars healthy ---
[order-service] processing order-1
[logging-sidecar] shipped: processed order-1
[mtls-sidecar] sent charge(order-1) to payment-service over mTLS
[order-service] payment response: mtls-response-for(charge(order-1))

--- logging sidecar crashes ---
[order-service] processing order-2
[order-service] logging sidecar down (logging sidecar unreachable) -- continuing WITHOUT logs (fail open)
[mtls-sidecar] sent charge(order-2) to payment-service over mTLS
[order-service] payment response: mtls-response-for(charge(order-2))

--- mTLS sidecar ALSO crashes ---
[order-service] processing order-3
[order-service] logging sidecar down (logging sidecar unreachable) -- continuing WITHOUT logs (fail open)
[order-service] mTLS sidecar down (mtls sidecar unreachable) -- REFUSING to send unencrypted (fail closed), order order-3 FAILS
```

## 7. Gotchas & takeaways

> Applying the same failure policy to every sidecar, regardless of what it does, is a common and dangerous shortcut. Failing open on a security-critical sidecar (silently sending requests unencrypted when the mTLS sidecar is down) trades an outage for a much worse, quieter security regression; failing closed on a purely observational sidecar (refusing to serve because logging is briefly unavailable) trades a minor loss of visibility for an unnecessary outage. Choose deliberately, per sidecar, not by default.

- A sidecar shares the main application's Pod lifecycle — it scales, deploys, and (usually) restarts with the application, which is what distinguishes it from a fully independent service the application merely calls over the network.
- Cross-cutting infrastructure concerns (TLS, logging, metrics, config sync) are good sidecar candidates; business logic never is — a sidecar handling business rules just fragments the application's logic across two processes for no benefit.
- Service mesh implementations (like Envoy-based meshes) are essentially a standardized sidecar deployed automatically alongside every service in the cluster, providing mTLS, retries, and observability uniformly without each service implementing any of it.
- Sidecar communication over `localhost` is fast and simple, but it's still a separate process — network-style failure modes (the sidecar being down, slow, or partially initialized) are real and must be handled explicitly, as Level 3 demonstrates.
- A related but distinct pattern — a companion proxying *outbound* calls to remote services on the main application's behalf, rather than handling an internal cross-cutting concern — is covered in [ambassador pattern](0457-ambassador-pattern.md).
