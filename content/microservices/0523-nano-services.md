---
card: microservices
gi: 523
slug: nano-services
title: "Nano-services"
---

## 1. What it is

**Nano-services** is the anti-pattern of splitting a system into services so small and fine-grained that the overhead of running and coordinating them — network calls, deployment pipelines, monitoring, operational burden — outweighs any benefit gained from separating them. A service that just wraps a single database table with basic CRUD, or exists only to hold one tiny function that's always called by exactly one other service, is usually a sign the boundary was drawn too fine: it adds a network hop and a whole separate deployable for something that could have been one class or one module inside a larger service.

## 2. Why & when

You watch for nano-services because "smaller services are always better" is a misreading of what microservices are actually meant to optimize for:

- **Every service, no matter how small, carries a fixed operational cost** — its own deployment pipeline, its own monitoring and alerting, its own on-call runbook, its own database connection pool, its own container/process overhead. A service handling one trivial endpoint pays exactly the same fixed cost as one handling a rich, meaningful piece of business capability.
- **Splitting too finely multiplies network calls for what used to be a single in-process function call** — logic that's always used together, always deployed together, and always owned by the same team gains nothing from being separated by a network boundary, and loses the ability to just call a method directly.
- **The right granularity is driven by business capability and team ownership, not by "how small can we make it."** A service should represent something a team can reason about, own end to end, and deploy independently *because it genuinely has an independent lifecycle* — not because someone drew the smallest possible boundary around a single database table or a single function.
- **The fix is consolidation**: merging nano-services that are always deployed together, always called by the same caller, and owned by the same team back into one coherent service — trading "many tiny independently-deployable things" for "one thing that's actually independently meaningful."

## 3. Core concept

Think of a company that, in an effort to give employees clear individual responsibilities, hires a separate person to staple documents, another separate person to walk those documents down the hall, and a third separate person to file them — each with their own desk, their own manager, their own performance review. The work genuinely could be done by one person with a stapler at their own desk; splitting it into three roles doesn't make any of them more independently useful, it just adds two handoffs (and two people's overhead) to a task that never benefited from being divided. A microservice boundary should exist where a real, independent responsibility exists — not just because a task *can* be split off.

Concretely:

1. **A service boundary is justified when the thing behind it has its own reason to change independently** — its own business rules that evolve on their own schedule, its own scaling needs, its own team that owns it.
2. **A service boundary is not justified purely by "this is a distinct piece of logic"** — plenty of distinct logic belongs together as classes or modules *inside* one service, without needing a network boundary between them.
3. **The telltale sign of a nano-service is a 1:1 relationship with exactly one caller and no independent lifecycle** — if Service X is only ever called by Service Y, always changes in lockstep with Y, and has no other reason to exist, the network boundary between X and Y is pure overhead.
4. **Consolidating nano-services back together loses nothing that was actually being gained** — if two "services" never scale independently, never deploy independently in practice, and are owned by the same team, merging them into one deployable removes the network hop and the duplicated operational overhead without sacrificing any real flexibility.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Nano-services: three tiny services each with full operational overhead, always deployed and called together; consolidated into one service with the same logic as internal classes">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Nano-services (over-split)</text>
  <rect x="20" y="35" width="90" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="65" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">validate-</text>
  <text x="65" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">address-svc</text>
  <rect x="130" y="35" width="90" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="175" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">format-</text>
  <text x="175" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">address-svc</text>
  <rect x="240" y="35" width="90" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="285" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">geocode-</text>
  <text x="285" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">address-svc</text>
  <text x="175" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">3 pipelines, 3 on-call rotations, 2 network hops</text>
  <text x="175" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">for logic ALWAYS called together, by one caller, one team</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Consolidated</text>
  <rect x="420" y="35" width="180" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">AddressService</text>
  <text x="510" y="74" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">validate / format / geocode</text>
  <text x="510" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">as internal classes, 1 pipeline</text>
</svg>

Three network-separated nano-services with always-together lifecycles cost more to run than one service containing the same logic as internal modules.

## 5. Runnable example

Scenario: address processing split into three "services" that are always called together in sequence. We start with the over-split version communicating over simulated network calls, extend it to show the operational cost this adds, then handle the fix: consolidating into one service with the same logic as plain internal method calls.

### Level 1 — Basic

```java
// File: NanoServicesOverSplit.java -- THREE separate "services" for
// validate/format/geocode, communicating via simulated network calls,
// even though they're ALWAYS called together in this exact order.
public class NanoServicesOverSplit {
    static String validateAddressServiceCall(String raw) throws InterruptedException {
        Thread.sleep(20); // simulated network round-trip
        if (raw == null || raw.isBlank()) throw new IllegalArgumentException("invalid address");
        return raw.trim();
    }
    static String formatAddressServiceCall(String validated) throws InterruptedException {
        Thread.sleep(20); // simulated network round-trip
        return validated.toUpperCase();
    }
    static String geocodeAddressServiceCall(String formatted) throws InterruptedException {
        Thread.sleep(20); // simulated network round-trip
        return formatted + " -> (lat=40.7,lon=-74.0)";
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        String result = geocodeAddressServiceCall(formatAddressServiceCall(validateAddressServiceCall("123 Main St")));
        System.out.println(result);
        System.out.println("Total: " + (System.currentTimeMillis() - start) + "ms across 3 'services', 3 deploy pipelines, 3 on-call rotations");
    }
}
```

How to run: `java NanoServicesOverSplit.java`

Each step is modeled as its own "service" with its own simulated network round-trip, even though the three are always called in the exact same order, by the exact same caller, and would always be deployed together in practice. The 60ms total latency here (3 x 20ms) is pure overhead compared to calling three plain methods directly — none of these three steps has any independent reason to scale, fail, or deploy separately from the others.

### Level 2 — Intermediate

```java
// File: OperationalCostShown.java -- makes the HIDDEN COST explicit:
// tracking how many deploy pipelines, on-call rotations, and network
// hops the over-split version above actually requires to operate.
import java.util.*;

public class OperationalCostShown {
    record ServiceOperationalCost(String name, int deployPipelines, int onCallRotations, int monitoringDashboards) {}

    public static void main(String[] args) {
        List<ServiceOperationalCost> overSplit = List.of(
            new ServiceOperationalCost("validate-address-svc", 1, 1, 1),
            new ServiceOperationalCost("format-address-svc", 1, 1, 1),
            new ServiceOperationalCost("geocode-address-svc", 1, 1, 1)
        );
        int totalPipelines = overSplit.stream().mapToInt(ServiceOperationalCost::deployPipelines).sum();
        int totalRotations = overSplit.stream().mapToInt(ServiceOperationalCost::onCallRotations).sum();
        int totalDashboards = overSplit.stream().mapToInt(ServiceOperationalCost::monitoringDashboards).sum();
        int networkHopsPerRequest = overSplit.size() - 1; // calls between the "services" per single logical operation

        System.out.println("Nano-services: " + overSplit.size() + " services, " + totalPipelines + " pipelines, "
            + totalRotations + " on-call rotations, " + totalDashboards + " dashboards, "
            + networkHopsPerRequest + " network hops PER address processed");
        System.out.println("All three: same caller, same order every time, same owning team -- zero independent lifecycle gained");
    }
}
```

How to run: `java OperationalCostShown.java`

This makes the invisible cost concrete: three tiny services multiply pipelines, on-call rotations, and dashboards by three, and add two network hops to every single address processed — for logic with no independent scaling needs, no independent failure domain, and no independent ownership. This overhead is paid on every deploy, every incident, and every request, regardless of how small the actual logic inside each "service" is.

### Level 3 — Advanced

```java
// File: ConsolidatedFix.java -- the FIX: ONE service, with the same
// validate/format/geocode logic as plain internal methods -- no
// network hops, one deploy pipeline, one on-call rotation.
public class ConsolidatedFix {
    static class AddressService {
        // internal methods -- callable directly, no network round-trip, no separate deployable
        private String validate(String raw) {
            if (raw == null || raw.isBlank()) throw new IllegalArgumentException("invalid address");
            return raw.trim();
        }
        private String format(String validated) { return validated.toUpperCase(); }
        private String geocode(String formatted) { return formatted + " -> (lat=40.7,lon=-74.0)"; }

        // the ONE public entry point this service actually needs to expose externally
        public String process(String rawAddress) {
            return geocode(format(validate(rawAddress)));
        }
    }

    public static void main(String[] args) {
        long start = System.currentTimeMillis();
        AddressService service = new AddressService();
        String result = service.process("123 Main St");
        System.out.println(result);
        System.out.println("Total: " + (System.currentTimeMillis() - start) + "ms, ONE deploy pipeline, ONE on-call rotation");
    }
}
```

How to run: `java ConsolidatedFix.java`

`validate`, `format`, and `geocode` are now plain private methods inside one `AddressService` class, called directly with zero network overhead — the elapsed time drops from ~60ms to effectively instant, and there's exactly one deployable, one pipeline, one on-call rotation, and one thing to monitor, covering the same functional behavior as the three-service version. Only `process(...)` is exposed publicly, because it's the one operation any external caller actually needs — the internal steps stay internal, exactly where they belong when they have no independent reason to be separately deployable.

## 6. Walkthrough

Trace `ConsolidatedFix.main` end to end, contrasting the call path with Level 1:

1. **`main` constructs one `AddressService` instance** — a single object, backed by a single class, that will be deployed as one process/container in a real system.
2. **`main` calls `service.process("123 Main St")`** — this is the one and only externally-facing call, whether invoked directly in-process here or, in a real deployment, via one HTTP/RPC call to this one service.
3. **Inside `process`, `validate("123 Main St")` runs as a plain method call** — no network involved, returning `"123 Main St"` (trimmed) essentially instantly.
4. **`format(...)` is called next, directly on the validated result**, uppercasing it to `"123 MAIN ST"` — again a plain in-process call, not a hop to another deployable.
5. **`geocode(...)` is called last, directly on the formatted result**, appending the simulated coordinates and producing the final string `"123 MAIN ST -> (lat=40.7,lon=-74.0)"`.
6. **`process` returns this final string directly to `main`**, which prints it along with the elapsed time — effectively zero, since no network round-trips occurred anywhere in this path.

Contrast with Level 1: there, the exact same three steps happened, in the exact same order, producing the exact same final output — but each step paid a simulated 20ms network round-trip, because each was modeled as its own deployable service. The *business logic* is identical; the only difference is whether the boundary between steps is a network call (services) or a method call (classes inside one service) — and since these three steps are never independently scaled, deployed, or owned, the method-call version loses nothing while eliminating three services' worth of fixed operational cost.

## 7. Gotchas & takeaways

> **Gotcha:** the instinct to "split it into its own service so it's testable/reusable in isolation" doesn't require a network boundary — a well-designed class with a clear interface is just as independently testable and reusable *within* a service as a separate microservice would be, without paying for a deploy pipeline, an on-call rotation, or a network hop to get that benefit.

- A service boundary should track an independent business capability, scaling need, or team ownership boundary — not simply "this logic is conceptually distinct," which classes and modules already handle fine within one service.
- The telltale sign of a nano-service is a 1:1 relationship with exactly one caller, always invoked in the same sequence, always deployed together — that's a strong signal the boundary should be a method call, not a network call.
- Every additional service carries fixed operational overhead (pipeline, on-call, monitoring, connection pools) regardless of how trivial its logic is — that cost has to be justified by a real independent lifecycle, not assumed away.
- Consolidating over-split services back together is a legitimate, common refactor, not a failure or a step backward — recognizing over-fragmentation and merging it is exactly what "the right granularity" means in practice.
