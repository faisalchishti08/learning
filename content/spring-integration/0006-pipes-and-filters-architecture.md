---
card: spring-integration
gi: 6
slug: pipes-and-filters-architecture
title: "Pipes-and-filters architecture"
---

## 1. What it is

Pipes-and-filters is the overarching architectural style that ties together everything covered so far in this section: messages (card 0002) flow through pipes (channels, card 0004) connecting independent processing steps called filters (a generic term here, distinct from the specific "Message Filter" EIP pattern — in this architectural sense, a filter is any endpoint, card 0005, that transforms or acts on what flows through it). Spring Integration's entire design is an implementation of this style: build a system as a graph of small, focused, independently-testable processing steps connected by channels, rather than one large, monolithic piece of logic.

## 2. Why & when

A single large method or class that reads input, validates it, transforms it, decides what to do based on its content, and produces output all in one place is hard to test in isolation, hard to reuse pieces of, and hard to change without risking the rest. Pipes-and-filters exists as an architectural answer: decompose that same overall behavior into a sequence of small, independent steps, each doing one focused thing, connected by explicit channels — each step can then be tested, replaced, reordered, or reused entirely independently of the others, as long as the channel contract (what kind of message flows through) stays consistent.

Recognize pipes-and-filters as the right architectural lens when:

- A processing pipeline naturally decomposes into distinct sequential (or branching) steps — validate, then transform, then route, then handle — each of which could plausibly be described in one sentence.
- Different parts of the pipeline may need to evolve, be tested, or be reused independently — a validation step useful in one flow might be equally useful in a completely different one, if it's genuinely decoupled.
- Flexibility in wiring matters more than raw throughput — pipes-and-filters trades a small amount of overhead (message passing between decoupled steps) for substantially greater flexibility in composition and reconfiguration.

## 3. Core concept

Think of pipes-and-filters exactly like a real assembly line in a factory: raw material enters at one end, and a sequence of independent stations — one that cuts, one that welds, one that paints, one that inspects — each perform one focused task and pass the work along a conveyor belt (the pipe) to the next station. Critically, the welding station doesn't need to know anything about how the cutting station works, only what shape of material it expects to receive on its own conveyor segment — this is exactly what lets a factory swap in a better welding machine without touching the cutting or painting stations at all, as long as the shape of material handed off between stations stays consistent.

```java
// Each "filter" in the pipes-and-filters sense is a small, independently-testable step.
Function<String, String> validate = raw -> {
    if (raw == null || raw.isBlank()) throw new IllegalArgumentException("blank order");
    return raw;
};
Function<String, Order> parse = raw -> new Order(raw.split(":")[0], Double.parseDouble(raw.split(":")[1]));
Function<Order, Order> applyDiscount = order -> order.amount() > 100 ? order.withDiscount(0.1) : order;
Consumer<Order> persist = order -> System.out.println("Saving: " + order);

// Composed as a "pipe": each step's output is the exact shape the next step expects as input.
persist.accept(applyDiscount.apply(parse.apply(validate.apply("order-123:150.00"))));
```

In a real Spring Integration application, each of these steps would instead be a distinct endpoint connected by named channels, configured declaratively — but the underlying architectural idea (independent steps, explicit hand-off contracts, no step aware of anything beyond its immediate neighbors) is identical either way.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A pipes-and-filters pipeline: validate, parse, apply discount, and persist, each an independent step connected by channels, mirroring an assembly line">
  <rect x="10" y="80" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">validate</text>

  <line x1="140" y1="105" x2="180" y2="105" stroke="#79c0ff" stroke-width="3"/>

  <rect x="180" y="80" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="245" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">parse</text>

  <line x1="310" y1="105" x2="350" y2="105" stroke="#79c0ff" stroke-width="3"/>

  <rect x="350" y="80" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">applyDiscount</text>

  <line x1="490" y1="105" x2="530" y2="105" stroke="#79c0ff" stroke-width="3"/>

  <rect x="530" y="80" width="120" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="590" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">persist</text>

  <text x="330" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">each station only knows the shape of what it receives and produces — nothing about the others</text>
</svg>

Four independent stations connected by pipes — each replaceable, testable, and reusable without touching the others.

## 5. Runnable example

The scenario: processing an order string end to end, starting as one tangled method, then decomposed into an explicit pipes-and-filters chain, and finally made resilient to a failure at any single stage without the whole pipeline crashing uninformatively.

### Level 1 — Basic

```java
// TangledOrderPipeline.java
public class TangledOrderPipeline {
    public static void main(String[] args) {
        String raw = "order-123:150.00";

        // Everything tangled together: validation, parsing, business logic, and output all inline.
        if (raw != null && !raw.isBlank()) {
            String[] parts = raw.split(":");
            String id = parts[0];
            double amount = Double.parseDouble(parts[1]);
            if (amount > 100) {
                amount = amount * 0.9;
            }
            System.out.println("Saving order " + id + " with final amount " + amount);
        }
    }
}
```

**How to run:** run `java TangledOrderPipeline.java`. Expected output: `Saving order order-123 with final amount 135.0` — correct, but every concern (validation, parsing, discounting, persistence) is inseparable from every other, impossible to test or reuse any single piece independently.

### Level 2 — Intermediate

Decomposing the same logic into an explicit chain of small, independent functions — each with a clear input/output contract — is the pipes-and-filters architecture applied directly, even before wiring in real Spring Integration channels.

```java
// DecomposedOrderPipeline.java
import java.util.function.Function;
import java.util.function.Consumer;

public class DecomposedOrderPipeline {
    record Order(String id, double amount) {
        Order withDiscount(double rate) { return new Order(id, amount * (1 - rate)); }
    }

    static final Function<String, String> validate = raw -> {
        if (raw == null || raw.isBlank()) throw new IllegalArgumentException("blank order");
        return raw;
    };

    static final Function<String, Order> parse = raw -> {
        String[] parts = raw.split(":");
        return new Order(parts[0], Double.parseDouble(parts[1]));
    };

    static final Function<Order, Order> applyDiscount = order ->
        order.amount() > 100 ? order.withDiscount(0.1) : order;

    static final Consumer<Order> persist = order ->
        System.out.println("Saving order " + order.id() + " with final amount " + order.amount());

    public static void main(String[] args) {
        persist.accept(applyDiscount.apply(parse.apply(validate.apply("order-123:150.00"))));
    }
}
```

**How to run:** run `java DecomposedOrderPipeline.java`. Expected output: `Saving order order-123 with final amount 135.0` — identical result to Level 1, but `validate`, `parse`, `applyDiscount`, and `persist` are each independently testable (a unit test can call `applyDiscount` directly with a hand-built `Order`, with zero involvement from parsing or string validation at all) and independently reusable in a different pipeline.

### Level 3 — Advanced

A real pipeline needs to handle a failure at any single stage (malformed input reaching `parse`, for instance) without either crashing the whole batch of orders being processed or silently losing the failed one — this level processes a batch through the same pipeline, isolating and reporting per-item failures (echoing the dead-letter idea from card 0001) while letting the rest of the batch continue.

```java
// ResilientBatchPipeline.java
import java.util.function.Function;
import java.util.List;
import java.util.ArrayList;

public class ResilientBatchPipeline {
    record Order(String id, double amount) {
        Order withDiscount(double rate) { return new Order(id, amount * (1 - rate)); }
    }

    static final Function<String, String> validate = raw -> {
        if (raw == null || raw.isBlank()) throw new IllegalArgumentException("blank order");
        return raw;
    };

    static final Function<String, Order> parse = raw -> {
        String[] parts = raw.split(":");
        return new Order(parts[0], Double.parseDouble(parts[1]));
    };

    static final Function<Order, Order> applyDiscount = order ->
        order.amount() > 100 ? order.withDiscount(0.1) : order;

    static String runPipeline(String raw) {
        Order order = applyDiscount.apply(parse.apply(validate.apply(raw)));
        return "Saved order " + order.id() + " with final amount " + order.amount();
    }

    public static void main(String[] args) {
        List<String> rawOrders = List.of(
            "order-123:150.00",
            "order-124:MALFORMED_AMOUNT", // will fail at the parse stage
            "order-125:75.00",
            ""                             // will fail at the validate stage
        );

        List<String> results = new ArrayList<>();
        List<String> failures = new ArrayList<>();

        for (String raw : rawOrders) {
            try {
                results.add(runPipeline(raw));
            } catch (Exception e) {
                // A failure at ANY single stage is caught per-item — the rest of the batch keeps going.
                failures.add("Failed to process '" + raw + "': " + e.getClass().getSimpleName());
            }
        }

        results.forEach(System.out::println);
        failures.forEach(System.err::println);
        System.out.println("Processed " + results.size() + " successfully, " + failures.size() + " failed.");
    }
}
```

**How to run:** run `java ResilientBatchPipeline.java`. Expected output:
```
Saved order order-123 with final amount 135.0
Saved order order-125 with final amount 75.0
Failed to process 'order-124:MALFORMED_AMOUNT': NumberFormatException
Failed to process '': IllegalArgumentException
Processed 2 successfully, 2 failed.
```
Two of the four raw orders fail — one at the `parse` stage (a `NumberFormatException` from trying to parse `"MALFORMED_AMOUNT"` as a `double`), one at the `validate` stage (an `IllegalArgumentException` for a blank string) — but both failures are isolated per-item, and the two valid orders still process successfully as if the failures never happened to the rest of the batch.

## 6. Walkthrough

Tracing the batch loop processing `"order-124:MALFORMED_AMOUNT"`, in execution order, alongside its well-formed neighbors:

1. The loop's third iteration (`"order-124:MALFORMED_AMOUNT"`) calls `runPipeline(raw)`, which first calls `validate.apply(raw)` — the string is non-blank, so validation passes through unchanged.
2. `parse.apply(...)` is called next; `raw.split(":")` correctly splits into `["order-124", "MALFORMED_AMOUNT"]`, but `Double.parseDouble("MALFORMED_AMOUNT")` throws `NumberFormatException`, since that text isn't a valid number.
3. This exception propagates immediately out of `parse`, out of `runPipeline`, and is caught by the surrounding `try`/`catch` in the batch loop — critically, `applyDiscount` for this particular order is never even reached, since the exception already occurred one stage earlier.
4. The `catch` block appends a descriptive failure message (including the exact raw input and the exception type) to the `failures` list, and the loop moves on to its next iteration — the failure is fully contained to this one item.
5. The fourth iteration (the blank string) similarly fails, but one stage *earlier* — at `validate.apply("")`, which throws `IllegalArgumentException` before `parse` is ever reached at all — demonstrating that different malformed inputs can fail at different stages of the same pipeline, and the surrounding per-item error handling doesn't need to know or care which stage was responsible.
6. After all four items have been attempted, the loop has accumulated two successful results and two failure messages, both printed separately at the end — a complete, honest account of the whole batch's outcome, with no single bad item able to derail the rest.

```
for each raw order:
  try: runPipeline(raw) = applyDiscount(parse(validate(raw)))
     "order-123:150.00"        -> validate OK -> parse OK -> discount OK -> SUCCESS
     "order-124:MALFORMED..."  -> validate OK -> parse THROWS (NumberFormatException) -> caught, recorded
     "order-125:75.00"         -> validate OK -> parse OK -> discount OK -> SUCCESS
     ""                        -> validate THROWS (IllegalArgumentException) -> caught, recorded
```

## 7. Gotchas & takeaways

> Decomposing a pipeline into independent stages (Level 2/3) only pays off if each stage's input/output contract is genuinely kept clean and consistent — a "filter" that reaches into global state, has hidden side effects beyond its stated output, or depends on the internal details of an adjacent stage undermines the whole point of pipes-and-filters, since stages are then no longer safely independent or reusable, whatever their surface-level function signatures suggest.

- Pipes-and-filters is the architectural umbrella; `Message`, `MessageChannel`, and message endpoints (cards 0002, 0004, 0005) are the concrete Spring Integration vocabulary that implements it directly.
- Decomposing a monolithic process into small, focused stages pays off most clearly in testability (each stage can be unit-tested with plain inputs and outputs, no messaging infrastructure required) and in reuse (a validation or transformation stage useful in one pipeline is often equally useful in another).
- Isolating per-item failures within a batch (Level 3) rather than letting one bad item abort the whole batch is a direct, practical application of the broader architectural principle: independent stages should fail independently too, not take down unrelated work with them.
- The tradeoff pipes-and-filters accepts is some overhead (message passing, decoupling machinery) in exchange for flexibility — reordering, replacing, or reusing individual stages without touching the rest of the pipeline — a worthwhile trade whenever a system's requirements are expected to keep evolving.
- When a pipeline feels tangled and hard to test (Level 1's shape), the fix is usually to ask "what are the distinct stages here, and what's the exact shape of data handed from one to the next" — answering that question is most of the work of applying pipes-and-filters to an existing piece of logic.
