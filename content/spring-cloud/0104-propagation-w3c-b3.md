---
card: spring-cloud
gi: 104
slug: propagation-w3c-b3
title: "Propagation (W3C, B3)"
---

## 1. What it is

Propagation is the mechanism by which trace context — the `traceId`, the calling span's id (to become the next span's `parentId`), and the sampling decision — travels from one service to the next across a network call, typically carried as HTTP headers; B3 (Zipkin's original header format, `X-B3-TraceId` etc., or the single-header `b3` variant) and the W3C Trace Context standard (`traceparent`/`tracestate` headers) are the two formats Spring applications commonly use, and both the sending and receiving service must agree on the same format for propagation to work.

```
B3 (multi-header):
  X-B3-TraceId: 80f198ee56343ba864fe8b2a57d3eff7
  X-B3-SpanId: e457b5a2e4d86bd1
  X-B3-Sampled: 1

W3C Trace Context (single header):
  traceparent: 00-80f198ee56343ba864fe8b2a57d3eff7-e457b5a2e4d86bd1-01
```

```properties
management.tracing.propagation.type=W3C
# or: B3, or B3_MULTI, or a comma-separated combination for compatibility during migration
```

## 2. Why & when

A trace is only as complete as its propagation is consistent — if service A sends B3 headers but service B only understands W3C headers, service B has no way to associate its own new span with the incoming request's trace, and the trace tree breaks into two disconnected fragments at that boundary. Because different organizations, tools, and legacy systems adopted different header formats at different times (B3 predates the W3C standard and was Zipkin/Sleuth's original format; W3C Trace Context is now the vendor-neutral, standardized format most new tooling defaults to), a Spring application needs to know explicitly which format(s) its upstream callers and downstream dependencies actually use, and configure propagation accordingly — including, during a migration, temporarily supporting both formats simultaneously.

Reach for explicit propagation configuration when:

- Integrating with external systems or partner services whose header format is already fixed — matching their format (rather than assuming a default) is required for the trace to actually connect across that boundary.
- Migrating a fleet from B3 (a Sleuth-era default) to W3C Trace Context — configuring dual support (`B3,W3C`) during the transition period lets services upgrade independently without breaking trace continuity for services still on the old format.
- Debugging a broken or fragmented trace where the tree unexpectedly starts over at a particular service boundary — mismatched propagation format between the caller and that service is one of the most common root causes.

## 3. Core concept

```
 service A (W3C) --HTTP call, header: traceparent: 00-<traceId>-<spanId>-01--> service B

 IF service B also expects W3C:
   service B reads traceparent, extracts traceId + parentId, creates its own child span correctly
   -> trace tree is CONTINUOUS across A and B

 IF service B only expects B3 (and never sees a traceparent header):
   service B finds NO recognized trace context header
   -> service B starts a BRAND NEW trace, with a NEW traceId
   -> the tree FRAGMENTS: A's spans and B's spans are now in TWO SEPARATE, disconnected traces
```

Propagation format compatibility is a pairwise contract between every direct caller/callee pair in the system — one mismatched pair breaks continuity at exactly that boundary, without affecting continuity elsewhere in the trace.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Service A using W3C propagation calls service B which also understands W3C keeping the trace continuous but service B calling service C which only understands B3 causes the trace to fragment into two separate traces at that boundary">
  <rect x="20" y="20" width="130" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="85" y="44" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">service A (W3C)</text>

  <rect x="255" y="20" width="130" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="320" y="44" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">service B (W3C)</text>

  <rect x="480" y="20" width="140" height="40" rx="7" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="550" y="44" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">service C (B3 only)</text>

  <defs><marker id="a104" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="150" y1="40" x2="255" y2="40" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a104)"/>
  <text x="202" y="30" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">traceparent</text>

  <line x1="385" y1="40" x2="480" y2="40" stroke="#f85149" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#a104)"/>
  <text x="432" y="30" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">traceparent (unread!)</text>

  <text x="85" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">trace-1 continues</text>
  <text x="320" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">into trace-1</text>
  <text x="550" y="100" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">starts NEW trace-2</text>
</svg>

The dashed line marks the header service C never understood — trace-1 stops there, and trace-2 begins fresh with no link back to trace-1.

## 5. Runnable example

The scenario: model header-based trace propagation across a chain of services, some agreeing on format and one deliberately mismatched — showing exactly where and why a trace fragments. Start with matched-format propagation working correctly end to end, then introduce a mismatched service and observe the fragmentation, then add dual-format support as the fix, restoring continuity without requiring every service to upgrade simultaneously.

### Level 1 — Basic

Two services agreeing on one format (W3C-style `traceparent`), propagating correctly.

```java
import java.util.*;

public class PropagationLevel1 {
    record TraceContext(String traceId, String spanId) {}

    static class Service {
        String name;
        Service(String name) { this.name = name; }

        // simulates receiving an incoming header and creating a span from it
        TraceContext handleRequest(Map<String, String> headers) {
            String traceparent = headers.get("traceparent");
            if (traceparent == null) {
                String newTraceId = UUID.randomUUID().toString().substring(0, 8);
                System.out.println(name + ": no traceparent found, starting NEW trace " + newTraceId);
                return new TraceContext(newTraceId, "span-root");
            }
            String[] parts = traceparent.split("-");
            String traceId = parts[1];
            System.out.println(name + ": continuing existing trace " + traceId);
            return new TraceContext(traceId, "span-" + name);
        }

        Map<String, String> callDownstream(TraceContext ctx) {
            return Map.of("traceparent", "00-" + ctx.traceId() + "-" + ctx.spanId() + "-01");
        }
    }

    public static void main(String[] args) {
        Service a = new Service("A");
        Service b = new Service("B");

        TraceContext ctxA = a.handleRequest(Map.of()); // origin -- no incoming header
        Map<String, String> headersToB = a.callDownstream(ctxA);
        TraceContext ctxB = b.handleRequest(headersToB); // B reads A's traceparent correctly
    }
}
```

How to run: `java PropagationLevel1.java`

`b.handleRequest` finds the `traceparent` header `a.callDownstream` produced and extracts the same `traceId` A started with — both services print references to the identical trace id, confirming propagation succeeded because both sides agree on the header name and format.

### Level 2 — Intermediate

Extend the chain to three services, with the third one deliberately expecting a different header (`X-B3-TraceId`) that was never sent — demonstrating exactly where and how a trace fragments.

```java
import java.util.*;

public class PropagationLevel2 {
    record TraceContext(String traceId, String spanId) {}

    static class W3cService {
        String name;
        W3cService(String name) { this.name = name; }
        TraceContext handleRequest(Map<String, String> headers) {
            String traceparent = headers.get("traceparent");
            if (traceparent == null) {
                String newTraceId = "trace-" + name;
                System.out.println(name + ": no traceparent -- starting NEW trace " + newTraceId);
                return new TraceContext(newTraceId, "span-root");
            }
            String traceId = traceparent.split("-")[1];
            System.out.println(name + ": continuing trace " + traceId + " (read from traceparent)");
            return new TraceContext(traceId, "span-" + name);
        }
        Map<String, String> callDownstream(TraceContext ctx) {
            return Map.of("traceparent", "00-" + ctx.traceId() + "-" + ctx.spanId() + "-01");
        }
    }

    // service C only understands B3 headers -- it will NEVER find a traceparent header useful
    static class B3OnlyService {
        String name;
        B3OnlyService(String name) { this.name = name; }
        TraceContext handleRequest(Map<String, String> headers) {
            String b3TraceId = headers.get("X-B3-TraceId"); // looks for the WRONG header name for what was sent
            if (b3TraceId == null) {
                String newTraceId = "trace-" + name;
                System.out.println(name + ": no X-B3-TraceId found -- starting NEW trace " + newTraceId + " (FRAGMENTED)");
                return new TraceContext(newTraceId, "span-root");
            }
            System.out.println(name + ": continuing trace " + b3TraceId);
            return new TraceContext(b3TraceId, "span-" + name);
        }
    }

    public static void main(String[] args) {
        W3cService a = new W3cService("A");
        W3cService b = new W3cService("B");
        B3OnlyService c = new B3OnlyService("C");

        TraceContext ctxA = a.handleRequest(Map.of());
        TraceContext ctxB = b.handleRequest(a.callDownstream(ctxA));
        TraceContext ctxC = c.handleRequest(b.callDownstream(ctxB)); // B sends traceparent; C only reads X-B3-TraceId
    }
}
```

How to run: `java PropagationLevel2.java`

`A` and `B` continue the same trace correctly (both use `traceparent`), but `C.handleRequest` looks for `"X-B3-TraceId"` in the headers `B` sent (which only contains `"traceparent"`), finds nothing, and starts a brand-new trace — the fragmentation happens at exactly the B-to-C boundary, the one place the two services disagree on header format.

### Level 3 — Advanced

Fix the fragmentation by having services send *both* header formats simultaneously (dual propagation, the standard migration strategy), letting a mismatched downstream service still find a format it understands.

```java
import java.util.*;

public class PropagationLevel3 {
    record TraceContext(String traceId, String spanId) {}

    // sends BOTH formats -- lets EITHER a W3C-only or B3-only downstream service correctly continue the trace
    static Map<String, String> callDownstreamDual(TraceContext ctx) {
        Map<String, String> headers = new HashMap<>();
        headers.put("traceparent", "00-" + ctx.traceId() + "-" + ctx.spanId() + "-01");
        headers.put("X-B3-TraceId", ctx.traceId());
        headers.put("X-B3-SpanId", ctx.spanId());
        return headers;
    }

    static class B3OnlyService {
        String name;
        B3OnlyService(String name) { this.name = name; }
        TraceContext handleRequest(Map<String, String> headers) {
            String b3TraceId = headers.get("X-B3-TraceId");
            if (b3TraceId == null) {
                String newTraceId = "trace-" + name;
                System.out.println(name + ": no X-B3-TraceId -- starting NEW trace " + newTraceId + " (FRAGMENTED)");
                return new TraceContext(newTraceId, "span-root");
            }
            System.out.println(name + ": continuing trace " + b3TraceId + " (read from X-B3-TraceId)");
            return new TraceContext(b3TraceId, "span-" + name);
        }
    }

    public static void main(String[] args) {
        TraceContext ctxA = new TraceContext("trace-A", "span-root");
        System.out.println("A: starting trace " + ctxA.traceId());

        Map<String, String> headersToC = callDownstreamDual(ctxA); // A now sends BOTH formats

        B3OnlyService c = new B3OnlyService("C");
        TraceContext ctxC = c.handleRequest(headersToC); // C finds X-B3-TraceId THIS time
    }
}
```

How to run: `java PropagationLevel3.java`

`callDownstreamDual` populates both `"traceparent"` and `"X-B3-TraceId"`/`"X-B3-SpanId"` in the outgoing headers, so `B3OnlyService.handleRequest`, which only ever looks for `"X-B3-TraceId"`, now finds it and correctly continues `"trace-A"` — no fragmentation, and critically, no change was required to `B3OnlyService`'s own code at all; only the *caller's* propagation behavior changed, which is precisely why dual-format propagation is the standard way to migrate a fleet incrementally without requiring every service to upgrade in lockstep.

## 6. Walkthrough

Trace `c.handleRequest(headersToC)` in Level 3.

1. `callDownstreamDual(ctxA)` builds a `headers` map containing three entries: `"traceparent"` (the W3C-style combined header), `"X-B3-TraceId"`, and `"X-B3-SpanId"` (the B3-style separate headers) — all derived from the same `ctxA` (`traceId="trace-A"`, `spanId="span-root"`).
2. `c.handleRequest(headersToC)` is called — inside it, `headers.get("X-B3-TraceId")` looks specifically for the B3-format header, which is now present (unlike in Level 2, where only `"traceparent"` had been sent).
3. Because `b3TraceId` is now `"trace-A"` (non-null), the `if (b3TraceId == null)` branch is skipped entirely — the method proceeds to the success path.
4. `println` prints `"C: continuing trace trace-A (read from X-B3-TraceId)"`, and a new `TraceContext("trace-A", "span-C")` is returned — the trace correctly continues under the same `traceId` it started with at `A`.
5. Compare this to Level 2's identical call: there, `headers` contained only `"traceparent"`, so `headers.get("X-B3-TraceId")` returned `null`, forcing the fragmentation branch — the *only* difference between the two runs is what the caller included in the outgoing headers; `B3OnlyService`'s own code is completely unchanged between Level 2 and Level 3.

```
Level 2: headers = {traceparent: "..."}                          -> C looks for X-B3-TraceId -> NOT FOUND -> fragments
Level 3: headers = {traceparent: "...", X-B3-TraceId: "trace-A"} -> C looks for X-B3-TraceId -> FOUND -> continues trace-A
```

## 7. Gotchas & takeaways

> **Gotcha:** dual-format propagation (sending both B3 and W3C headers) is a deliberate migration strategy, not a permanent end state to leave in place indefinitely — it roughly doubles the header overhead on every outgoing call and adds ongoing configuration complexity; once every service in a fleet has been confirmed to understand the target format, dropping the legacy format from propagation configuration (`management.tracing.propagation.type=W3C` alone, rather than `B3,W3C`) is the appropriate cleanup step.

- Propagation format is a pairwise agreement between a caller and the specific service it calls — a fleet doesn't need one single fleet-wide setting so much as it needs every direct caller/callee pair to agree, which in practice usually does mean standardizing fleet-wide, but the failure mode is always local to a specific mismatched boundary.
- A fragmented trace (a new `traceId` appearing partway through what should be one logical request) is one of the most reliable symptoms of a propagation format mismatch specifically — it's worth checking header format agreement early when debugging unexpectedly incomplete traces.
- `management.tracing.propagation.type` accepts a comma-separated list (`B3,W3C`) specifically to support sending and accepting multiple formats simultaneously during a migration window, letting services upgrade independently rather than requiring a coordinated, fleet-wide simultaneous cutover.
- W3C Trace Context is the vendor-neutral, now-standardized format most new tooling defaults to; B3 remains common in Sleuth-era or Zipkin-centric systems — knowing which format(s) a given system's upstream and downstream dependencies actually use is a prerequisite for correct propagation configuration, not something to assume by default.
