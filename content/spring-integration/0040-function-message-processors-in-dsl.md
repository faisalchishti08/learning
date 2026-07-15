---
card: spring-integration
gi: 40
slug: function-message-processors-in-dsl
title: "Function & message processors in DSL"
---

## 1. What it is

A `MessageProcessor` is the underlying abstraction every DSL step (card 0037) actually compiles down to — a component that takes a `Message` and produces a result, whether that's a `boolean` (for `.filter`), a new payload (for `.transform`), or side-effecting work (for `.handle`). When you pass a lambda to a DSL method, Spring Integration wraps it in a `MessageProcessor` implementation automatically; you can also implement `MessageProcessor` directly for cases the simpler functional-interface shapes (`Function`, `Predicate`, `GenericHandler`) don't cleanly cover — most notably, when a step needs access to the full `Message` (headers and all), not just its payload.

## 2. Why & when

You reach for the full `MessageProcessor` (or a lambda taking a `Message<T>`/headers argument) specifically when a step's logic genuinely needs more than just the payload:

- **A step's logic depends on headers, not just the payload** — a discount rate that varies by a `customerTier` header, a routing decision based on a `region` header — the simpler `Function<T, R>` shape used for most `.transform(...)` calls only receives the payload; a `GenericTransformer` or a two-argument lambda `(payload, headers) -> ...` is what's needed instead.
- **A step needs to produce a result that itself carries new headers**, not just a new payload — returning a full `Message` (built via `MessageBuilder`) instead of a plain object lets a step control both the payload and headers of what it emits.
- **You're implementing genuinely reusable, non-trivial logic as its own named class** rather than an inline lambda (echoing card 0038's inline-vs-extracted guidance) — implementing `MessageProcessor` (or a compatible functional interface) directly gives that logic a proper, independently testable home with full access to the message.

## 3. Core concept

Think of the difference between a `Function<T, R>` and a full `MessageProcessor` like the difference between a form that only shows you one field of an application ("just tell me the amount") versus a clerk with the entire application file in front of them, able to reference any field on it ("what's the amount, but also check what tier this customer is and what region they're in"). Most of the time, the single-field form is all a step actually needs; but for logic that genuinely depends on more than one thing about the incoming message, the full file is what's required.

```java
// Function<T,R> shape: only sees the payload
.transform((Order o) -> o.withDiscount(0.9))

// MessageProcessor / two-arg lambda shape: sees payload AND headers
.transform((Order o, java.util.Map<String, Object> headers) -> {
    String tier = (String) headers.get("customerTier");
    double rate = "gold".equals(tier) ? 0.75 : 0.95;
    return o.withDiscount(rate);
})
```

Both compile to a `MessageProcessor` underneath, but the second form explicitly requests access to the headers a plain `Function<T, R>` lambda wouldn't be able to see at all.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A payload-only Function sees just the payload; a MessageProcessor or two-argument lambda sees both payload and headers from the full Message">
  <rect x="20" y="30" width="180" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Function&lt;T,R&gt;</text>
  <text x="110" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">sees: payload ONLY</text>

  <rect x="240" y="30" width="220" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="350" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">MessageProcessor</text>
  <text x="350" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">sees: payload + ALL headers</text>

  <rect x="500" y="15" width="120" height="85" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="40" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Message</text>
  <text x="560" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">payload</text>
  <text x="560" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">headers{...}</text>

  <line x1="460" y1="60" x2="498" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#mp1)"/>
  <line x1="200" y1="60" x2="238" y2="60" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>

  <defs>
    <marker id="mp1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Both forms compile down to `MessageProcessor` underneath — the visible difference is purely which parts of the message the lambda's signature exposes.

## 5. Runnable example

The scenario: header-dependent discount pricing, starting with a payload-only transform baseline, then a header-aware transform, and finally a step producing a full `Message` (payload plus new headers) rather than just a plain payload.

### Level 1 — Basic

```java
// PayloadOnlyBaselineDemo.java
// Establishes the baseline: a payload-only Function, unable to see headers even if it needed to.
import java.util.function.Function;

public class PayloadOnlyBaselineDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        Function<Order, Order> discountByAmountOnly = o -> new Order(o.id(), o.amount() * 0.95); // FIXED rate — can't vary by tier
        Order result = discountByAmountOnly.apply(new Order("ORD-1", 100.0));
        System.out.println("Discounted (payload-only, fixed rate): " + result);
    }
}
```

How to run: `java PayloadOnlyBaselineDemo.java`. Expected output: `Discounted (payload-only, fixed rate): Order[id=ORD-1, amount=95.0]` — the discount rate is hardcoded, since this shape has no way to see a `customerTier` header even if one exists on the incoming message.

### Level 2 — Intermediate

A header-aware transform (the `MessageProcessor` shape) reads a header to vary its behavior per message, something the payload-only `Function` shape from Level 1 fundamentally cannot do.

```java
// HeaderAwareTransformDemo.java
import java.util.Map;
import java.util.function.BiFunction;

public class HeaderAwareTransformDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        // BiFunction<payload, headers, result> stands in for the DSL's (T, headers) -> R lambda shape
        BiFunction<Order, Map<String, Object>, Order> tieredDiscount = (o, headers) -> {
            String tier = (String) headers.get("customerTier");
            double rate = "gold".equals(tier) ? 0.75 : "silver".equals(tier) ? 0.85 : 0.95;
            return new Order(o.id(), o.amount() * rate);
        };

        Order goldResult = tieredDiscount.apply(new Order("ORD-1", 100.0), Map.of("customerTier", "gold"));
        Order standardResult = tieredDiscount.apply(new Order("ORD-2", 100.0), Map.of("customerTier", "bronze"));

        System.out.println("Gold tier: " + goldResult);
        System.out.println("Standard tier: " + standardResult);
    }
}
```

How to run: `java HeaderAwareTransformDemo.java`. Expected output: `Gold tier: Order[id=ORD-1, amount=75.0]` then `Standard tier: Order[id=ORD-2, amount=95.0]` — the *same* transform logic produced two different discount rates purely by reading a header the payload-only shape in Level 1 could never have accessed.

### Level 3 — Advanced

A step can return a full `Message` (built via `MessageBuilder`) instead of a plain payload, letting it control both the outgoing payload *and* new headers in one step — useful when a transform needs to both change the payload's shape and stamp metadata about that change (e.g., which discount tier was actually applied) for downstream steps or logging to read.

```java
// FullMessageOutputDemo.java
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.Map;
import java.util.function.BiFunction;

public class FullMessageOutputDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) {
        // returns a full Message, not just a plain Order — carries BOTH the new payload and new headers
        BiFunction<Order, Map<String, Object>, Message<Order>> tieredDiscountWithAudit = (o, headers) -> {
            String tier = (String) headers.getOrDefault("customerTier", "bronze");
            double rate = "gold".equals(tier) ? 0.75 : "silver".equals(tier) ? 0.85 : 0.95;
            Order discounted = new Order(o.id(), o.amount() * rate);
            return MessageBuilder.withPayload(discounted)
                .setHeader("appliedTier", tier)
                .setHeader("appliedRate", rate)
                .build();
        };

        Message<Order> result = tieredDiscountWithAudit.apply(
            new Order("ORD-1", 200.0), Map.of("customerTier", "gold"));

        System.out.println("Payload: " + result.getPayload());
        System.out.println("Audit headers: appliedTier=" + result.getHeaders().get("appliedTier")
            + ", appliedRate=" + result.getHeaders().get("appliedRate"));
    }
}
```

How to run: `java FullMessageOutputDemo.java`. Expected output: `Payload: Order[id=ORD-1, amount=150.0]` then `Audit headers: appliedTier=gold, appliedRate=0.75` — the step produced both a transformed payload and new, self-documenting audit headers in one operation, something neither the plain `Function<T,R>` nor the `BiFunction<T, headers, R>` shape can do, since both are restricted to returning just a payload.

## 6. Walkthrough

Tracing `FullMessageOutputDemo` in execution order:

1. `tieredDiscountWithAudit.apply(...)` is called with an `Order` payload and a headers map containing `customerTier=gold`.
2. Inside the lambda, `headers.getOrDefault("customerTier", "bronze")` reads the tier — `"gold"`, since it's present in the supplied map.
3. The rate lookup evaluates `"gold".equals(tier)`, which is `true`, setting `rate` to `0.75`.
4. A new `Order` is constructed with `amount = 200.0 * 0.75 = 150.0` — the actual payload transformation, identical in spirit to Level 2's header-aware transform.
5. Instead of returning that `Order` directly, the lambda calls `MessageBuilder.withPayload(discounted)` and chains `.setHeader("appliedTier", tier)` and `.setHeader("appliedRate", rate)` before `.build()` — this is where the step goes beyond a plain payload transform, attaching self-documenting metadata about *how* the transformation was computed.
6. The caller receives the full `Message<Order>`, and can independently inspect both the transformed payload (`result.getPayload()`) and the audit headers (`result.getHeaders().get(...)`) — a downstream logging or monitoring step could read `appliedTier`/`appliedRate` without needing to re-derive them from the order's raw amount.

```
input: Order(amount=200), headers{customerTier=gold}
  -> tier="gold", rate=0.75
  -> discounted Order(amount=150.0)
  -> MessageBuilder: payload=discounted, headers+={appliedTier=gold, appliedRate=0.75}
  -> full Message<Order> returned (payload AND new headers, together)
```

## 7. Gotchas & takeaways

> Reaching for the full `Message`/`MessageProcessor` shape by default, even when a step genuinely only needs the payload, adds unnecessary noise — every reader of that step now has to check whether headers are actually being used, when a plain `Function<T, R>` would have signaled "this step only cares about the payload" immediately. Use the payload-only shape as the default, and only step up to the header-aware or full-`Message` shape when a step's logic genuinely needs it — mirroring the same "don't over-engineer for hypothetical needs" judgment that applies throughout this project's endpoint archetypes.

- Every DSL step ultimately compiles to a `MessageProcessor`, which has full access to a message's payload and headers — the simpler `Function<T, R>`/`Predicate<T>` lambda shapes most steps use are a narrower, payload-only view of that same underlying mechanism.
- Use the header-aware (`MessageProcessor`, or a two-argument `(payload, headers) -> ...`) shape specifically when a step's logic genuinely depends on header values, not just the payload.
- A step can return a full `Message` (via `MessageBuilder`) instead of a plain payload, letting it control both the outgoing payload and new headers together — useful for attaching audit/metadata information alongside a transformation's actual result.
- Default to the simplest shape (`Function<T, R>` for transforms, `Predicate<T>` for filters) that satisfies a step's actual needs; reach for the fuller `MessageProcessor` shape only when payload-only access genuinely isn't enough.
- This same payload-only-vs-full-message distinction applies across every DSL step type (`.filter`, `.transform`, `.handle`, `.route`), not just transforms — each has both a simpler, payload-only overload and a fuller, header-aware overload available.
