---
card: spring-integration
gi: 39
slug: sub-flows-nested-flows
title: "Sub-flows & nested flows"
---

## 1. What it is

A sub-flow is a fluent DSL chain (card 0037) nested inside another DSL method — most commonly inside `.route(...)`'s branch configuration, `.publishSubscribeChannel(...)`'s per-subscriber configuration, or `.gateway(...)`'s wrapped invocation — rather than being declared as a fully separate, independently-named top-level flow. It lets a router's individual branches (each potentially several steps long) be defined inline, right where the branch is chosen, instead of routing to a separately-declared external flow by channel name.

## 2. Why & when

You reach for sub-flows specifically when a branch or nested continuation needs more than one step, but doesn't warrant being promoted to a fully separate, independently-referenced flow:

- **A router's branches each need multiple processing steps**, not just a single handler — a sub-flow lets each branch be its own mini fluent chain, defined inline within the router's configuration, keeping the branch's logic visible right where the routing decision that leads to it is made.
- **You want a flow's structure to stay self-contained and readable end to end**, without a reader needing to jump to a separately-declared flow bean just to see what a particular branch actually does — nesting keeps closely related logic physically close together.
- **A sub-flow's logic is genuinely specific to one particular router/branch and unlikely to be reused elsewhere** — that's exactly the signal that nesting it inline (rather than extracting a separate top-level flow) is the right call; the moment a sub-flow's logic *is* reused, that's the signal to promote it to its own named flow instead.

## 3. Core concept

Think of a sub-flow like a footnote that itself contains several sentences, versus a full separate appendix referenced by a page number. A router's branch, if it's just one simple step, reads naturally as an inline footnote right where the decision point is; if a branch needs paragraphs of its own processing, nesting that entire mini-narrative right there (a sub-flow) still keeps it attached to its context, without forcing the reader to flip to a completely separate section (a fully separate top-level flow) just to follow one branch's logic.

```java
@Bean
public IntegrationFlow orderRoutingFlow() {
    return IntegrationFlow.from("orders")
        .route(Order.class, order -> order.amount() > 100 ? "highValue" : "standard", mapping -> mapping
            .subFlowMapping("highValue", sf -> sf                     // SUB-FLOW: several steps, inline
                .transform((Order o) -> o.withPriorityFlag(true))
                .handle((Order o, h) -> prioritySrv.expedite(o)))
            .subFlowMapping("standard", sf -> sf                      // a SECOND sub-flow, also inline
                .handle((Order o, h) -> standardSrv.process(o))))
        .get();
}
```

Both `sf -> sf....` blocks are complete fluent chains in their own right, nested entirely within the router's configuration — neither branch needed to be declared as its own separate `@Bean`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A router's branches are each defined as an inline sub-flow with multiple steps, rather than routed to separately-declared top-level flows">
  <rect x="20" y="75" width="100" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="70" y="99" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">.route(...)</text>

  <line x1="120" y1="85" x2="180" y2="35" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sf1)"/>
  <line x1="120" y1="105" x2="180" y2="155" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sf1)"/>

  <rect x="190" y="15" width="220" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="300" y="32" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">sub-flow: highValue</text>
  <text x="300" y="47" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">.transform(...).handle(...)</text>

  <rect x="190" y="130" width="220" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="300" y="147" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">sub-flow: standard</text>
  <text x="300" y="162" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">.handle(...)</text>

  <text x="530" y="95" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">both defined INLINE,</text>
  <text x="530" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no separate top-level Beans</text>

  <defs>
    <marker id="sf1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Each branch is a self-contained multi-step chain, kept visually and structurally close to the routing decision that leads to it.

## 5. Runnable example

The scenario: order routing with each branch requiring multiple steps, starting with a basic two-branch sub-flow router, then a sub-flow that itself contains a nested filter, and finally comparing an inline sub-flow against extracting one branch into a separately-referenced flow once it grows large.

### Level 1 — Basic

```java
// BasicSubFlowRoutingDemo.java
// Simulates the DSL's sub-flow mapping mechanics directly, since the real .route(...).subFlowMapping(...)
// API requires a Spring ApplicationContext to actually construct and wire the nested flows.
import java.util.function.Consumer;
import java.util.Map;

public class BasicSubFlowRoutingDemo {
    record Order(String id, double amount) {}

    // sub-flow 1: two steps, inline
    static void highValueSubFlow(Order o) {
        Order flagged = new Order(o.id(), o.amount()); // "transform" step (a real flag would be added here)
        System.out.println("[highValue sub-flow, step 1: flag] " + flagged);
        System.out.println("[highValue sub-flow, step 2: expedite] shipped with priority: " + flagged);
    }

    // sub-flow 2: one step, inline
    static void standardSubFlow(Order o) {
        System.out.println("[standard sub-flow, step 1: process] " + o);
    }

    public static void main(String[] args) {
        Map<String, Consumer<Order>> subFlows = Map.of(
            "highValue", BasicSubFlowRoutingDemo::highValueSubFlow,
            "standard", BasicSubFlowRoutingDemo::standardSubFlow);

        Order order1 = new Order("ORD-1", 199.99);
        Order order2 = new Order("ORD-2", 25.00);

        subFlows.get(order1.amount() > 100 ? "highValue" : "standard").accept(order1);
        subFlows.get(order2.amount() > 100 ? "highValue" : "standard").accept(order2);
    }
}
```

How to run: `java BasicSubFlowRoutingDemo.java`. Expected output: two lines for `ORD-1` (`[highValue sub-flow, step 1...]` and `step 2...]`), then one line for `ORD-2` (`[standard sub-flow, step 1...]`) — each order's routing decision selected a completely different multi-step (or single-step) continuation, entirely self-contained within its own branch.

### Level 2 — Intermediate

A sub-flow can itself contain any of the other endpoint archetypes, including a nested filter — showing that sub-flows aren't a restricted, simplified mini-DSL; they're the *same* full DSL, just scoped to one branch's context.

```java
// SubFlowWithNestedFilterDemo.java
import java.util.function.Consumer;

public class SubFlowWithNestedFilterDemo {
    record Order(String id, double amount, boolean fraudFlag) {}

    // sub-flow WITH its own internal filter step, nested one level deeper than the outer router
    static void highValueSubFlow(Order o) {
        System.out.println("[highValue sub-flow] step 1: transform (flag priority)");
        // nested filter step, local to THIS sub-flow only
        if (o.fraudFlag()) {
            System.out.println("[highValue sub-flow] step 2: INTERNAL FILTER rejected — fraud flag set");
            return;
        }
        System.out.println("[highValue sub-flow] step 3: expedite shipped: " + o);
    }

    public static void main(String[] args) {
        Consumer<Order> route = o -> {
            if (o.amount() > 100) highValueSubFlow(o);
            else System.out.println("[standard] processed: " + o);
        };

        route.accept(new Order("ORD-1", 199.99, false)); // passes internal filter
        route.accept(new Order("ORD-2", 250.00, true));  // rejected by internal filter
    }
}
```

How to run: `java SubFlowWithNestedFilterDemo.java`. Expected output for `ORD-1`: all three `[highValue sub-flow]` step lines, ending in a successful ship. For `ORD-2`: only the first two `[highValue sub-flow]` lines, the second being the internal filter's rejection — step 3 never runs, exactly like a top-level `Filter` (card 0022) short-circuiting a flow, just scoped entirely within this one sub-flow's own branch.

### Level 3 — Advanced

Comparing a small, still-inline sub-flow against the same branch's logic once it's grown large enough to warrant extraction into a separately-referenced top-level flow (invoked via `.gateway(...)` from within the router) shows exactly where that promotion decision applies in practice.

```java
// SubFlowVsExtractedFlowDemo.java
import java.util.function.Function;

public class SubFlowVsExtractedFlowDemo {
    record Order(String id, double amount) {}
    record ShippingResult(String orderId, String carrier, String trackingId) {}

    // once a branch's logic grows this large — multiple steps, its own error handling,
    // its own retry logic — it's a signal to EXTRACT it as its own named, separately-testable flow
    static ShippingResult extractedHighValueFlow(Order order) {
        System.out.println("[extracted flow] step 1: validate address");
        System.out.println("[extracted flow] step 2: select carrier based on region");
        String carrier = order.amount() > 500 ? "premium-carrier" : "standard-carrier";
        System.out.println("[extracted flow] step 3: generate tracking ID");
        String trackingId = "TRK-" + order.id();
        System.out.println("[extracted flow] step 4: notify customer");
        return new ShippingResult(order.id(), carrier, trackingId);
    }

    // a genuinely small branch: STILL appropriate to keep as an inline sub-flow, not extracted
    static void standardInlineSubFlow(Order o) {
        System.out.println("[inline sub-flow] processed: " + o);
    }

    public static void main(String[] args) {
        Function<Order, Object> route = o -> o.amount() > 100
            ? extractedHighValueFlow(o)       // routed to a SEPARATELY-DEFINED flow (via a gateway, conceptually)
            : (Runnable) () -> standardInlineSubFlow(o); // routed to logic that stayed INLINE

        Object highValueResult = route.apply(new Order("ORD-1", 600.0));
        System.out.println("Result: " + highValueResult);

        Object standardResult = route.apply(new Order("ORD-2", 25.0));
        ((Runnable) standardResult).run();
    }
}
```

How to run: `java SubFlowVsExtractedFlowDemo.java`. Expected output: four `[extracted flow] step N...]` lines followed by `Result: ShippingResult[orderId=ORD-1, carrier=premium-carrier, trackingId=TRK-ORD-1]` for the high-value order, then `[inline sub-flow] processed: Order[id=ORD-2, amount=25.0]` for the standard order — the high-value branch's genuinely complex, multi-concern logic lives in its own named, independently-callable method (standing in for a separately-declared flow reached via a gateway), while the standard branch's simple one-line logic stayed as an inline sub-flow.

## 6. Walkthrough

Tracing `SubFlowVsExtractedFlowDemo` for the high-value order in execution order:

1. `route.apply(new Order("ORD-1", 600.0))` evaluates the routing condition `o.amount() > 100`, which is `true` for `600.0`, selecting the branch that calls `extractedHighValueFlow(o)` directly (standing in for the DSL routing to a separately-declared flow via `.gateway("highValueOrderFlow")`).
2. Inside `extractedHighValueFlow`, four distinct steps run in sequence, each printing its own progress line — this method has grown to encompass address validation, carrier selection (itself with its own conditional logic), tracking ID generation, and customer notification — genuinely substantial, multi-concern logic.
3. The carrier-selection step's own condition (`order.amount() > 500`) evaluates `600.0 > 500` as `true`, selecting `"premium-carrier"`.
4. `extractedHighValueFlow` constructs and returns a `ShippingResult` record summarizing everything that happened across its four internal steps.
5. Back in `main`, that returned `ShippingResult` is printed directly, since `route.apply(...)` returned it as a plain `Object`.
6. For the standard order (`ORD-2`, amount `25.0`), the routing condition is `false`, so the *other* branch is selected — one that simply wraps a single call to `standardInlineSubFlow` in a `Runnable`, reflecting how much simpler this branch's logic genuinely is: a single line, appropriately left inline rather than promoted to its own named flow.

```
ORD-1 (amount=600) -> route: amount>100 TRUE -> extractedHighValueFlow(order)
    step1 -> step2 (carrier: 600>500 -> premium) -> step3 -> step4 -> ShippingResult

ORD-2 (amount=25)  -> route: amount>100 FALSE -> inline sub-flow: standardInlineSubFlow(order)
```

## 7. Gotchas & takeaways

> There's no hard rule for exactly when a sub-flow has grown "too large" and should be extracted into a separately-declared flow — but a useful signal is whether the branch's logic would ever need to be tested, reused, or reasoned about independently of the specific router it's nested under. `SubFlowVsExtractedFlowDemo`'s `extractedHighValueFlow` earned its extraction by having its own multi-step internal structure worth testing on its own; `standardInlineSubFlow`'s single line clearly hadn't. Erring toward keeping things inline until that need for independence actually appears avoids premature, unnecessary structural complexity.

- A sub-flow is a fluent DSL chain (card 0037) nested inside another DSL construct — most commonly a router's branch — rather than declared as a fully separate, independently-named top-level flow.
- Use sub-flows to keep a branch's multi-step logic visually and structurally close to the routing decision that leads to it, avoiding the indirection of jumping to a separately-declared flow bean.
- A sub-flow has access to the full DSL vocabulary, including its own nested filters, transformers, and further routing — it's not a restricted subset, just a scoped context.
- Promote a sub-flow to a fully separate, independently-referenced flow once its logic grows complex enough to warrant its own testing, reuse, or independent reasoning — there's no fixed size threshold, just a judgment call about genuine independence.
- Keeping genuinely simple branches inline, and only extracting genuinely complex ones, avoids both extremes: overly bloated single flows, and excessive fragmentation into many tiny, rarely-reused separate flows.
