---
card: microservices
gi: 109
slug: spring-hateoas-for-hypermedia-links
title: "Spring HATEOAS for hypermedia links"
---

## 1. What it is

Spring HATEOAS is Spring's library for building [HATEOAS](0080-hateoas-hypermedia.md)-compliant API responses in a Spring MVC or WebFlux application, providing `EntityModel<T>` (a wrapper adding a `links` collection around your domain object) and `Link` (a `rel`/`href` pair) types, plus a `WebMvcLinkBuilder` helper that constructs links by referencing your controller's own methods — so a link's URL is generated from the actual route mapping rather than hand-built as a raw string that could drift out of sync with the real route.

## 2. Why & when

Building hypermedia links as raw, hand-typed strings (`"/orders/" + id + "/cancel"`) works until a controller's route mapping changes — at which point every hand-built link string referencing that route needs to be found and updated manually, with no compiler or framework help catching a stale one. Spring HATEOAS's `WebMvcLinkBuilder.linkTo(methodOn(OrderController.class).cancelOrder(id))` style instead derives the link's URL from the *actual* controller method and its real `@GetMapping`/`@PostMapping` annotation — if that route mapping changes, every link built this way updates automatically, since it's generated from the live mapping rather than duplicated as a separate string.

Use Spring HATEOAS whenever you're building genuinely hypermedia-driven API responses (see [HATEOAS's own guidance](0080-hateoas-hypermedia.md) on when that investment is worthwhile) within a Spring application — it removes the risk of link strings drifting out of sync with actual route definitions, and integrates with Spring MVC's/WebFlux's standard JSON serialization to produce a HAL-formatted response (the common hypermedia response format) with minimal extra code.

## 3. Core concept

`EntityModel.of(domainObject)` wraps your plain object; `.add(Link.of(...))` attaches links; `WebMvcLinkBuilder` generates a link's actual URL from a real controller method reference rather than a hand-typed string.

```java
EntityModel<Order> resource = EntityModel.of(order);
resource.add(linkTo(methodOn(OrderController.class).getOrder(order.getId())).withSelfRel());
if (order.getStatus() == PLACED) {
    resource.add(linkTo(methodOn(OrderController.class).cancelOrder(order.getId())).withRel("cancel"));
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EntityModel wraps a plain domain object with a links collection, where each link's URL is generated from a real controller method reference via WebMvcLinkBuilder rather than a hand-typed string">
  <rect x="20" y="30" width="180" height="90" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Order (plain object)</text>
  <text x="110" y="75" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">id=42</text>
  <text x="110" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">status=PLACED</text>

  <rect x="240" y="20" width="200" height="110" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">EntityModel&lt;Order&gt;</text>
  <text x="340" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">links generated from</text>
  <text x="340" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">real controller methods</text>

  <rect x="470" y="35" width="150" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">self -&gt; /orders/42</text>
  <rect x="470" y="80" width="150" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="102" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">cancel -&gt; /orders/42/cancel</text>

  <line x1="200" y1="75" x2="240" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="440" y1="52" x2="470" y2="52" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="440" y1="97" x2="470" y2="97" stroke="#6db33f" stroke-width="1.5"/>
</svg>

Links are generated from real controller method references, not duplicated as hand-typed strings.

## 5. Runnable example

Scenario: an order response, first with hand-typed link strings (showing the drift risk), then rewritten using a simulated `EntityModel`/link-builder pattern that generates a link's URL by reading a real (simulated) controller's route mapping annotation, then extended to show the link automatically updating when the controller's route mapping changes — with zero change needed at the link-construction call site.

### Level 1 — Basic

```java
// File: HandTypedLinks.java -- link URLs are HAND-TYPED strings,
// duplicating the route path that ALSO lives in the controller mapping.
public class HandTypedLinks {
    record Order(int id, String status) {}
    record Link(String rel, String href) {}

    static Link cancelLink(Order order) {
        return new Link("cancel", "/orders/" + order.id() + "/cancel"); // HAND-TYPED -- must match the real route
    }

    public static void main(String[] args) {
        Order order = new Order(42, "PLACED");
        System.out.println(cancelLink(order));
    }
}
```

**How to run:** `javac HandTypedLinks.java && java HandTypedLinks` (JDK 17+).

Expected output:
```
Link[rel=cancel, href=/orders/42/cancel]
```

### Level 2 — Intermediate

```java
// File: GeneratedFromControllerMapping.java -- generate the link's URL
// by reading the CONTROLLER'S OWN route mapping annotation via
// reflection -- exactly what WebMvcLinkBuilder.linkTo(methodOn(...)) does.
import java.lang.annotation.*;
import java.lang.reflect.*;

public class GeneratedFromControllerMapping {
    @Retention(RetentionPolicy.RUNTIME) @interface PostMapping { String value(); }

    record Order(int id, String status) {}
    record Link(String rel, String href) {}

    static class OrderController { // the REAL controller -- route mapping lives HERE, in ONE place
        @PostMapping("/orders/{id}/cancel")
        void cancelOrder(int id) { /* real implementation would go here */ }
    }

    static Link linkTo(Class<?> controller, String methodName, int id) throws Exception { // simulates WebMvcLinkBuilder
        Method method = controller.getDeclaredMethod(methodName, int.class);
        PostMapping mapping = method.getAnnotation(PostMapping.class);
        String href = mapping.value().replace("{id}", String.valueOf(id)); // read from the REAL annotation
        return new Link("cancel", href);
    }

    public static void main(String[] args) throws Exception {
        Order order = new Order(42, "PLACED");
        Link cancelLink = linkTo(OrderController.class, "cancelOrder", order.id());
        System.out.println(cancelLink);
    }
}
```

**How to run:** `javac GeneratedFromControllerMapping.java && java GeneratedFromControllerMapping` (JDK 17+).

Expected output:
```
Link[rel=cancel, href=/orders/42/cancel]
```

### Level 3 — Advanced

```java
// File: RouteChangePropagatesAutomatically.java -- change the
// CONTROLLER'S route mapping -- the generated link updates AUTOMATICALLY,
// with ZERO change to the link-construction call site.
import java.lang.annotation.*;
import java.lang.reflect.*;

public class RouteChangePropagatesAutomatically {
    @Retention(RetentionPolicy.RUNTIME) @interface PostMapping { String value(); }

    record Order(int id, String status) {}
    record Link(String rel, String href) {}

    // v1: route is /orders/{id}/cancel
    static class OrderControllerV1 {
        @PostMapping("/orders/{id}/cancel")
        void cancelOrder(int id) {}
    }

    // v2: route CHANGED to /api/v2/orders/{id}/cancel -- a realistic API versioning change
    static class OrderControllerV2 {
        @PostMapping("/api/v2/orders/{id}/cancel")
        void cancelOrder(int id) {}
    }

    static Link linkTo(Class<?> controller, String methodName, int id) throws Exception {
        Method method = controller.getDeclaredMethod(methodName, int.class);
        PostMapping mapping = method.getAnnotation(PostMapping.class);
        String href = mapping.value().replace("{id}", String.valueOf(id));
        return new Link("cancel", href);
    }

    public static void main(String[] args) throws Exception {
        Order order = new Order(42, "PLACED");

        Link linkV1 = linkTo(OrderControllerV1.class, "cancelOrder", order.id());
        System.out.println("With V1 controller: " + linkV1);

        // the link-BUILDING code is IDENTICAL -- only the controller class reference changed
        Link linkV2 = linkTo(OrderControllerV2.class, "cancelOrder", order.id());
        System.out.println("With V2 controller: " + linkV2);
        System.out.println("(link URL updated automatically -- no hand-typed string needed changing)");
    }
}
```

**How to run:** `javac RouteChangePropagatesAutomatically.java && java RouteChangePropagatesAutomatically` (JDK 17+).

Expected output:
```
With V1 controller: Link[rel=cancel, href=/orders/42/cancel]
With V2 controller: Link[rel=cancel, href=/api/v2/orders/42/cancel]
```

## 6. Walkthrough

1. **Level 1** — `cancelLink` builds a `Link` by string-concatenating `"/orders/" + order.id() + "/cancel"` directly — this path string exists purely inside `cancelLink`, with no connection to wherever the real `/orders/{id}/cancel` route is actually mapped in a controller. If that route's mapping ever changed, nothing would automatically catch or reflect that here.
2. **Level 2 — deriving the link from the real route mapping** — `OrderController.cancelOrder` is annotated with `@PostMapping("/orders/{id}/cancel")` — the single place the route's real path lives. `linkTo` uses reflection to look up `cancelOrder`'s `@PostMapping` annotation and read its `value()` directly, substituting in the actual `id`, rather than having any separately hand-typed path string. `main` calls `linkTo(OrderController.class, "cancelOrder", 42)`, producing the identical link string as Level 1 — but this time, generated *from* the controller's own real mapping, not duplicated independently.
3. **Level 3 — proving the link tracks route changes automatically** — two controller classes, `OrderControllerV1` and `OrderControllerV2`, each declare `cancelOrder` with a *different* `@PostMapping` path — `/orders/{id}/cancel` versus `/api/v2/orders/{id}/cancel`, simulating a realistic API versioning change to the route. `linkTo` itself is entirely unchanged between the two calls in `main` — it's the exact same method, doing the exact same reflection-based lookup.
4. **Tracing `main`'s two calls** — `linkTo(OrderControllerV1.class, "cancelOrder", 42)` reads `OrderControllerV1.cancelOrder`'s mapping, producing `/orders/42/cancel`. `linkTo(OrderControllerV2.class, "cancelOrder", 42)` reads `OrderControllerV2.cancelOrder`'s *different* mapping, producing `/api/v2/orders/42/cancel` — and the only thing that changed between the two calls was which controller *class* was passed in; the link-generation logic itself needed zero modification to reflect the new route.
5. **Why this matters for a real, evolving API** — this is exactly the practical benefit Spring HATEOAS's `linkTo(methodOn(OrderController.class).cancelOrder(id))` style provides in a real application: because the link is generated by referencing the *actual* controller method (which Spring resolves against its real, live `@PostMapping` annotation at runtime), any change to that route's mapping automatically and correctly propagates to every place that builds a link to it — eliminating an entire category of "we changed the route but forgot to update this one hand-typed link string somewhere" bugs.

## 7. Gotchas & takeaways

> **Gotcha:** Spring HATEOAS's `methodOn(...)` helper works by creating a proxy of your controller class and recording which method was called on it — this means the controller method being referenced must be a real, invokable method with a normal signature; static analysis tricks or heavily customized method resolution can occasionally trip up this proxy-based mechanism in edge cases, so test link generation for any unusually-structured controller method.

- `EntityModel<T>` wraps a plain domain object with an attachable collection of `Link`s, matching the [HATEOAS](0080-hateoas-hypermedia.md) representation shape.
- `WebMvcLinkBuilder`'s `linkTo(methodOn(Controller.class).method(args))` pattern generates a link's URL from the controller's real, live route mapping, rather than requiring a separately hand-typed, drift-prone string.
- A route mapping change on the referenced controller method automatically propagates to every link built by referencing that method — no manual string updates needed anywhere else.
- This tooling is specifically valuable when you're already committed to building [genuinely hypermedia-driven responses](0080-hateoas-hypermedia.md) — it removes a real maintenance risk (stale hand-typed links) from that investment, but doesn't change the underlying cost/benefit decision of adopting HATEOAS in the first place.
- Spring HATEOAS integrates with standard Spring MVC/WebFlux JSON serialization to produce HAL-formatted responses with minimal additional code beyond constructing the `EntityModel` and its links.
