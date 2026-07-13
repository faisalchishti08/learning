---
card: microservices
gi: 137
slug: cloudevents-specification
title: "CloudEvents specification"
---

## 1. What it is

CloudEvents is a CNCF (Cloud Native Computing Foundation) specification that standardizes the *envelope* around an event — a fixed set of metadata attributes like `id`, `source`, `type`, and `time` — so that different tools, brokers, and services from different vendors can all agree on how to identify, route, and route on events, regardless of what broker technology carries them or what the event's own business payload looks like.

## 2. Why & when

Without a shared envelope format, every team, service, and vendor tool that needs to inspect an event's basic metadata (what kind of event is this, who produced it, when did it happen) ends up inventing its own slightly different structure — one service nests a `type` field under `meta.eventType`, another calls it `event_name` at the top level, a third only encodes it implicitly in the channel name. That inconsistency makes generic, event-agnostic tooling (routing rules, logging middleware, event gateways, cross-vendor integrations) far harder to build, because each has to special-case every producer's particular envelope shape.

Adopt CloudEvents when interoperability across different tools, teams, or vendors is a real concern — event routers, serverless triggers, and many managed cloud event services (AWS EventBridge, Azure Event Grid, Knative Eventing) already speak it natively, so producing CloudEvents-formatted events lets a service plug into that ecosystem with minimal translation. For a single team's internal, single-broker pipeline where no cross-vendor tooling is in play, a simpler homegrown envelope is a reasonable, lower-ceremony choice — CloudEvents earns its complexity specifically at integration boundaries.

## 3. Core concept

Every CloudEvent carries a small set of required and optional context attributes as an envelope wrapping the actual business data (the `data` field), so any CloudEvents-aware tool can read `type`, `source`, and `id` uniformly, without needing to understand the specific shape of the payload inside `data`.

```java
// the REQUIRED CloudEvents context attributes, wrapping an arbitrary business payload
record CloudEvent(
    String id,           // unique event id
    String source,        // URI identifying WHERE this event originated
    String specversion,   // CloudEvents spec version, e.g. "1.0"
    String type,           // what KIND of event this is, e.g. "com.example.order.placed"
    Object data            // the actual business payload -- CloudEvents doesn't care what shape this is
) {}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A CloudEvents envelope wraps a standard set of context attributes (id, source, type, specversion, time) around an opaque data payload; generic tooling can route on the envelope without understanding the payload's shape" >
  <rect x="60" y="30" width="520" height="130" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">CloudEvents envelope</text>
  <text x="90" y="72" fill="#79c0ff" font-size="8" font-family="sans-serif">id: "evt-8f3a"</text>
  <text x="90" y="88" fill="#79c0ff" font-size="8" font-family="sans-serif">source: "/order-service"</text>
  <text x="90" y="104" fill="#79c0ff" font-size="8" font-family="sans-serif">type: "com.example.order.placed"</text>
  <text x="90" y="120" fill="#79c0ff" font-size="8" font-family="sans-serif">specversion: "1.0"</text>
  <text x="90" y="136" fill="#79c0ff" font-size="8" font-family="sans-serif">time: "2026-07-13T10:00:00Z"</text>

  <rect x="380" y="65" width="170" height="80" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="465" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">data: { ...opaque</text>
  <text x="465" y="104" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">business payload,</text>
  <text x="465" y="118" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">any shape }</text>
</svg>

Generic tools can route and filter using only the standardized envelope fields, without ever needing to parse the `data` payload's specific shape.

## 5. Runnable example

Scenario: an event routing system that starts with an ad-hoc, inconsistent envelope shape per producer (showing why generic tooling struggles), standardizes on CloudEvents' required attributes so one router works uniformly across producers, and finally uses CloudEvents' extension attributes and content-type field to route and filter events without any producer-specific code in the router.

### Level 1 — Basic

```java
// File: AdHocInconsistentEnvelopes.java -- each producer invents its OWN envelope
// shape, forcing any generic router to special-case every single one.
import java.util.*;

public class AdHocInconsistentEnvelopes {
    public static void main(String[] args) {
        Map<String, Object> fromOrderService = Map.of("event_name", "order.placed", "payload", Map.of("orderId", 42));
        Map<String, Object> fromPaymentService = Map.of("meta", Map.of("eventType", "payment.captured"), "body", Map.of("paymentId", 7));

        System.out.println("Routing requires SPECIAL-CASE code per producer:");
        String orderType = (String) fromOrderService.get("event_name"); // different key...
        System.out.println("  order-service event type (via 'event_name'): " + orderType);

        @SuppressWarnings("unchecked")
        Map<String, Object> paymentMeta = (Map<String, Object>) fromPaymentService.get("meta");
        String paymentType = (String) paymentMeta.get("eventType"); // ...different nesting, different key
        System.out.println("  payment-service event type (via 'meta.eventType'): " + paymentType);

        System.out.println("A generic router would need a special branch for EVERY producer's shape.");
    }
}
```

**How to run:** `javac AdHocInconsistentEnvelopes.java && java AdHocInconsistentEnvelopes` (JDK 17+).

Reading "what type of event is this" requires entirely different code for each producer, because nothing standardizes where that information lives — exactly the interoperability problem CloudEvents solves.

### Level 2 — Intermediate

```java
// File: StandardizedCloudEvents.java -- both producers now emit the SAME envelope
// shape; ONE routing function works uniformly for both.
import java.util.*;

public class StandardizedCloudEvents {
    record CloudEvent(String id, String source, String specversion, String type, Object data) {}

    static CloudEvent fromOrderService() {
        return new CloudEvent("evt-1", "/order-service", "1.0", "com.example.order.placed", Map.of("orderId", 42));
    }
    static CloudEvent fromPaymentService() {
        return new CloudEvent("evt-2", "/payment-service", "1.0", "com.example.payment.captured", Map.of("paymentId", 7));
    }

    // ONE generic function, works for ANY CloudEvents-compliant producer
    static void route(CloudEvent event) {
        System.out.println("Routing event id=" + event.id() + " type=" + event.type() + " from source=" + event.source());
        if (event.type().startsWith("com.example.order.")) System.out.println("  -> routed to order-handlers");
        if (event.type().startsWith("com.example.payment.")) System.out.println("  -> routed to payment-handlers");
    }

    public static void main(String[] args) {
        route(fromOrderService());
        route(fromPaymentService());
        System.out.println("The SAME 'route' method handled both, with zero producer-specific branches.");
    }
}
```

**How to run:** `javac StandardizedCloudEvents.java && java StandardizedCloudEvents` (JDK 17+).

Expected output:
```
Routing event id=evt-1 type=com.example.order.placed from source=/order-service
  -> routed to order-handlers
Routing event id=evt-2 type=com.example.payment.captured from source=/payment-service
  -> routed to payment-handlers
The SAME 'route' method handled both, with zero producer-specific branches.
```

### Level 3 — Advanced

```java
// File: ExtensionAttributesAndContentType.java -- CloudEvents' extension attributes
// and datacontenttype let a router filter and dispatch WITHOUT parsing the data payload at all.
import java.util.*;
import java.util.function.*;

public class ExtensionAttributesAndContentType {
    record CloudEvent(
        String id, String source, String specversion, String type,
        String datacontenttype, Map<String, String> extensions, // extension attributes: custom, still standardized
        Object data
    ) {}

    static class EventRouter {
        Map<String, List<Consumer<CloudEvent>>> handlersByType = new HashMap<>();
        void onType(String type, Consumer<CloudEvent> handler) { handlersByType.computeIfAbsent(type, k -> new ArrayList<>()).add(handler); }

        void dispatch(CloudEvent event) {
            // routing decision made ENTIRELY from envelope fields -- 'data' is never inspected here
            System.out.println("Dispatching id=" + event.id() + " type=" + event.type() + " datacontenttype=" + event.datacontenttype());
            String priority = event.extensions().getOrDefault("priority", "normal"); // a CUSTOM extension attribute
            if (priority.equals("high")) System.out.println("  [HIGH PRIORITY -- routed to expedited queue]");

            handlersByType.getOrDefault(event.type(), List.of()).forEach(h -> h.accept(event));
        }
    }

    public static void main(String[] args) {
        EventRouter router = new EventRouter();
        router.onType("com.example.order.placed", e -> System.out.println("  [order-handler] processing order event"));

        CloudEvent normalOrder = new CloudEvent("evt-3", "/order-service", "1.0", "com.example.order.placed",
            "application/json", Map.of(), Map.of("orderId", 42));

        CloudEvent urgentOrder = new CloudEvent("evt-4", "/order-service", "1.0", "com.example.order.placed",
            "application/json", Map.of("priority", "high"), Map.of("orderId", 99)); // extension attribute set

        router.dispatch(normalOrder);
        router.dispatch(urgentOrder);
        System.out.println("Priority routing worked entirely from the STANDARD envelope + extension attribute -- 'data' shape was irrelevant to the router.");
    }
}
```

**How to run:** `javac ExtensionAttributesAndContentType.java && java ExtensionAttributesAndContentType` (JDK 17+).

Expected output:
```
Dispatching id=evt-3 type=com.example.order.placed datacontenttype=application/json
  [order-handler] processing order event
Dispatching id=evt-4 type=com.example.order.placed datacontenttype=application/json
  [HIGH PRIORITY -- routed to expedited queue]
  [order-handler] processing order event
Priority routing worked entirely from the STANDARD envelope + extension attribute -- 'data' shape was irrelevant to the router.
```

## 6. Walkthrough

1. **Level 1** — extracting "what type of event is this" from `fromOrderService` requires reading the `"event_name"` key directly, while the semantically identical question for `fromPaymentService` requires first unwrapping a nested `"meta"` map and then reading `"eventType"` — two completely different code paths for the same conceptual piece of metadata.
2. **Level 2, the shared envelope shape** — `CloudEvent` defines exactly one place `type` (and `id`, `source`, `specversion`) live, and both `fromOrderService` and `fromPaymentService` populate a `CloudEvent` using that identical shape, despite representing entirely different kinds of business events.
3. **Level 2, one router for every producer** — `route(CloudEvent event)` reads `event.type()` and `event.source()` using the exact same field access regardless of which producer created the event; the `if` branches inside `route` check `event.type()`'s value, not its structural location, which is now guaranteed identical everywhere.
4. **Level 2, the payoff made visible** — both calls to `route` in `main` succeed through the identical method, with no producer-specific branch anywhere in `route` itself — directly solving the Level 1 problem of needing separate extraction code per producer.
5. **Level 3, extension attributes** — `extensions` is a standardized *slot* for custom, producer- or domain-specific metadata that still lives in a predictable place in the envelope (rather than being invented ad hoc inside `data`); `urgentOrder` sets `"priority" -> "high"` in this slot.
6. **Level 3, routing without touching `data`** — `EventRouter.dispatch` reads `event.extensions().getOrDefault("priority", "normal")` and branches on it *before* ever looking at `event.data()` — the routing decision for priority is made entirely from envelope-level information, meaning this exact routing logic would work identically no matter what business payload shape `data` happened to hold.
7. **Level 3, the two dispatch calls compared** — `normalOrder` (no `priority` extension set) triggers only the ordinary handler output; `urgentOrder` (with `"priority": "high"`) triggers both the "HIGH PRIORITY" line and the ordinary handler — demonstrating that generic, payload-agnostic routing logic, built once against the standard envelope and its extension mechanism, correctly handles both cases without any change.

## 7. Gotchas & takeaways

> **Gotcha:** CloudEvents standardizes the *envelope*, not the business payload inside `data` — two producers can both emit perfectly valid CloudEvents while using completely incompatible shapes for their actual event data; CloudEvents solves cross-vendor tooling and routing interoperability, not payload schema compatibility, which still needs its own discipline (see [event schema versioning](0134-event-schema-versioning.md)).

- CloudEvents is a CNCF specification standardizing an event's envelope (`id`, `source`, `type`, `specversion`, and more) so generic, producer-agnostic tooling can route, filter, and log events without understanding each producer's custom shape.
- The specification's value is strongest at integration boundaries — cross-team, cross-vendor, or cross-tool — where inconsistent ad hoc envelopes force special-case handling per producer.
- Many managed cloud event services and event-routing tools already speak CloudEvents natively, making it a practical default when plugging into that broader ecosystem.
- Extension attributes provide a standardized slot for custom metadata (like a priority hint) that generic routing logic can act on without inspecting the business payload at all.
- CloudEvents does not standardize or constrain the shape of `data` itself — payload schema compatibility across producer and consumer versions remains a separate concern, handled by [event schema versioning](0134-event-schema-versioning.md) practices.
