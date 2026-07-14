---
card: microservices
gi: 480
slug: traffic-management-routing-splitting-mirroring
title: "Traffic management (routing, splitting, mirroring)"
---

## 1. What it is

**Traffic management** is a service mesh's ability to control exactly how requests flow between services, beyond simple load balancing — including **routing** (sending requests to a specific version based on rules, like headers or paths), **splitting** (sending a defined percentage of traffic to one version versus another, for canary releases), and **mirroring** (duplicating live traffic to a second destination for testing, without that destination's response affecting the real caller at all). All of this is configured centrally and enforced entirely inside the mesh's [sidecar proxies](0479-sidecar-proxy-envoy.md), with zero application code changes.

## 2. Why & when

You reach for mesh-level traffic management whenever you need fine-grained control over request flow that would otherwise require custom application logic or a separate piece of infrastructure:

- **Canary releases need gradual, controlled traffic shifting.** Traffic splitting lets you send 5% of live traffic to a new version and watch its behavior before committing further — a capability that's awkward to build correctly inside application code, but a natural, declarative mesh configuration.
- **Header- or path-based routing enables testing in production safely.** Routing rules can send requests carrying a specific test header to a new version, while every other request goes to the stable version — letting a team validate a change against real infrastructure without affecting real users.
- **Traffic mirroring lets you test a new version against real traffic patterns with zero risk.** The mirrored destination's response is simply discarded — the real caller only ever sees the response from the primary destination, so a badly broken mirrored version can't affect production traffic at all, only itself.
- **You configure this at the mesh level specifically because it needs to apply consistently across every caller**, without every calling service needing to know a routing decision is even being made — the decision belongs to the mesh, not to each individual client.

## 3. Core concept

Think of a highway that splits into two lanes leading to two different, functionally identical rest stops — some percentage of cars are directed to the new rest stop to see how it holds up under real traffic, while a mirrored security camera feed of the highway is also sent to a testing facility that just watches, never actually diverting any cars there. Drivers experience one of these behaviors (getting routed) but never notice or are affected by the other (being watched).

Concretely:

1. **Routing rules** match on request attributes (a header, a path prefix, a source identity) and direct matching requests to a specific destination — everything else falls through to a default.
2. **Traffic splitting** divides requests to a single logical destination across multiple actual versions by percentage — 95% to the stable version, 5% to the canary, with the proxy making that probabilistic decision per request.
3. **Traffic mirroring** duplicates a request to a secondary destination in parallel with sending it to the primary — the primary's response is what the real caller receives; the mirrored destination's response (or failure) is discarded entirely, invisible to the caller.
4. **All three are configured declaratively** through the mesh's [control plane](0478-data-plane-vs-control-plane.md) — an operator changes a percentage or a routing rule, and every proxy in the fleet picks up the new behavior without any application redeploy.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Traffic splitting sends a percentage of requests to a canary version; mirroring duplicates requests to a test destination whose response is discarded" >
  <rect x="20" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">incoming request</text>

  <rect x="240" y="20" width="150" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">v1 (stable) -- 95%</text>

  <rect x="240" y="80" width="150" height="45" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="315" y="107" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">v2 (canary) -- 5%</text>

  <rect x="460" y="80" width="170" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="545" y="107" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mirror target (response discarded)</text>

  <line x1="160" y1="45" x2="240" y2="42" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="160" y1="45" x2="240" y2="102" stroke="#f0883e" marker-end="url(#a1)"/>
  <line x1="160" y1="45" x2="460" y2="102" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Splitting divides traffic by percentage across versions; mirroring duplicates traffic to a target whose response never reaches the real caller.

## 5. Runnable example

Scenario: a proxy applying traffic management rules to a stream of requests. We start with basic path-based routing, extend it to percentage-based traffic splitting for a canary, then handle the hard case: mirroring traffic to a test destination whose failure must never affect the real response the caller receives.

### Level 1 — Basic

```java
// File: TrafficRoutingBasic.java -- models HEADER-based routing: requests
// carrying a specific test header go to a canary version, everything else
// goes to the stable version -- a rule applied entirely by the proxy.
import java.util.*;

public class TrafficRoutingBasic {
    static String routeRequest(Map<String, String> headers) {
        if ("true".equals(headers.get("x-canary-test"))) {
            return "inventory-service-v2 (canary, matched test header)";
        }
        return "inventory-service-v1 (stable, default route)";
    }

    public static void main(String[] args) {
        System.out.println("[proxy] " + routeRequest(Map.of()));
        System.out.println("[proxy] " + routeRequest(Map.of("x-canary-test", "true")));
    }
}
```

How to run: `java TrafficRoutingBasic.java`

`routeRequest` inspects the `headers` map for a specific test marker and branches its destination accordingly — a request without that header falls through to the stable default, while one carrying it is routed to the canary, with the routing decision made entirely by this proxy-level logic rather than by the caller choosing a destination itself.

### Level 2 — Intermediate

```java
// File: TrafficSplittingPercentage.java -- the SAME routing concept, now
// applying PERCENTAGE-based traffic splitting across a stream of ordinary
// requests -- roughly 90% to stable, 10% to canary, decided per-request.
import java.util.*;

public class TrafficSplittingPercentage {
    static Random random = new Random(42); // fixed seed for reproducible demo output

    static String splitRequest(int canaryPercentage) {
        int roll = random.nextInt(100);
        if (roll < canaryPercentage) {
            return "inventory-service-v2 (canary)";
        }
        return "inventory-service-v1 (stable)";
    }

    public static void main(String[] args) {
        int canaryPercentage = 10;
        Map<String, Integer> counts = new HashMap<>();
        for (int i = 1; i <= 20; i++) {
            String destination = splitRequest(canaryPercentage);
            counts.merge(destination, 1, Integer::sum);
        }
        System.out.println("[proxy] traffic distribution over 20 requests: " + counts);
    }
}
```

How to run: `java TrafficSplittingPercentage.java`

`splitRequest` rolls a random number per request and compares it against `canaryPercentage` to decide the destination — over many requests, this produces roughly the configured percentage split without any single request "knowing" it's part of a canary rollout; the decision is made fresh, independently, for each one.

### Level 3 — Advanced

```java
// File: TrafficMirroringIsolated.java -- the SAME proxy, now handling the
// PRODUCTION-FLAVORED hard case: MIRRORING traffic to a test destination
// that is COMPLETELY BROKEN. The mirrored destination's failure must be
// caught and discarded entirely -- the REAL caller must always receive
// the PRIMARY destination's response, unaffected by whatever happens to
// the mirror.
public class TrafficMirroringIsolated {
    static String callPrimary(String request) {
        return "response from stable primary: " + request + " processed successfully";
    }

    // The mirror target is badly broken -- it throws on every single call.
    static String callMirrorTarget(String request) {
        throw new RuntimeException("mirror target is completely broken, crashes on every request");
    }

    static String handleRequest(String request) {
        // Fire the mirror call, but its outcome must NEVER affect the real response.
        try {
            String mirrorResponse = callMirrorTarget(request);
            System.out.println("[proxy] mirror responded (discarded): " + mirrorResponse);
        } catch (RuntimeException e) {
            System.out.println("[proxy] mirror call FAILED (" + e.getMessage() + ") -- discarded, no effect on real caller");
        }

        // The primary call is entirely separate and always determines the real response.
        String primaryResponse = callPrimary(request);
        return primaryResponse;
    }

    public static void main(String[] args) {
        String realResponse = handleRequest("check-stock sku-123");
        System.out.println("[caller] received: " + realResponse);
    }
}
```

How to run: `java TrafficMirroringIsolated.java`

`handleRequest` calls `callMirrorTarget` inside a `try` block whose `catch` swallows any exception and only logs it — nothing from that `catch` block propagates further or influences `primaryResponse` in any way. `primaryResponse` is computed by an entirely separate call to `callPrimary`, made after the mirror attempt regardless of whether it succeeded or failed, and it's `primaryResponse` — never anything from the mirror path — that `handleRequest` actually returns to the real caller.

## 6. Walkthrough

Trace `TrafficMirroringIsolated.main` in order. **First**, `handleRequest("check-stock sku-123")` is called, entering its `try` block and calling `callMirrorTarget("check-stock sku-123")`.

**Next**, `callMirrorTarget` immediately throws a `RuntimeException`, since it's modeled as completely broken — this exception is caught by the surrounding `catch (RuntimeException e)` block right there inside `handleRequest`, which prints a failure message naming the exception's content, explicitly noting it's discarded and has no effect on the real caller.

**Then**, execution continues past the `try`/`catch` block entirely normally — Java's exception handling means once a `catch` block completes, execution resumes at the next statement after the whole `try`/`catch` construct, with no lingering effect from the exception that was caught.

**After that**, `callPrimary("check-stock sku-123")` runs — a completely separate, unrelated method call that has no dependency on anything that happened during the mirror attempt. It returns its success response normally, and `handleRequest` assigns that to `primaryResponse`.

**Finally**, `handleRequest` returns `primaryResponse`, and `main` prints it as what the real caller received — demonstrating that a total, unhandled-looking failure on the mirror side (a `RuntimeException` thrown on every single call) never once affected the actual response delivered to the real caller, exactly matching the guarantee mesh-level mirroring is supposed to provide.

```
[proxy] mirror call FAILED (mirror target is completely broken, crashes on every request) -- discarded, no effect on real caller
[caller] received: response from stable primary: check-stock sku-123 processed successfully
```

## 7. Gotchas & takeaways

> Mirrored traffic still has real-world side effects if the mirrored destination performs writes (to a database, to a downstream service) — mirroring is genuinely safe for the *caller* (the response is always discarded), but it's not automatically safe for *the mirrored destination's own side effects*. Mirror to an isolated environment, or ensure the mirrored version is read-only, before mirroring genuinely sensitive production traffic.
- Traffic splitting percentages should typically ramp gradually (1% → 5% → 25% → 100%) as confidence in a canary grows, rather than jumping straight to a large percentage — this is the practical mechanism behind a cautious [rolling deployment](0450-rolling-deployment.md)'s canary phase.
- Routing rules based on headers are a powerful way to let internal testers or specific user cohorts opt into a new version deliberately, without affecting the general population at all.
- All three traffic management capabilities are configured centrally and enforced by proxies uniformly — no calling service needs its own logic to participate in a canary, a header-routed test, or a mirror; it's entirely transparent to them.
- Isolating a mirror's failure from the real response path (Level 3) is the single most important correctness property mirroring must guarantee — a mirroring implementation that lets the mirror target's failure or slowness affect the real caller has broken its core promise.
