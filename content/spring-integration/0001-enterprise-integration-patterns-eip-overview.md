---
card: spring-integration
gi: 1
slug: enterprise-integration-patterns-eip-overview
title: "Enterprise Integration Patterns (EIP) overview"
---

## 1. What it is

Enterprise Integration Patterns (EIP) is a catalogue of reusable, named solutions — documented in the well-known 2003 book by Gregor Hohpe and Bobby Woolf — for the recurring problems that show up whenever independent systems need to exchange data asynchronously through messages. Spring Integration is, at its core, a direct Java implementation of that catalogue: nearly every class you'll meet in this card (`Message`, channels, endpoints, routers, filters, transformers) corresponds one-to-one with a named pattern from the book, given a concrete, Spring-flavored API.

## 2. Why & when

Before EIP was cataloged, every team building message-based integration between systems tended to reinvent the same handful of solutions from scratch, under different names, with subtly different behavior — one team's ad hoc "only forward messages matching some condition" logic is really the **Message Filter** pattern; another team's "split one message into several and process independently" is the **Splitter** pattern. EIP exists to give these recurring solutions common names and well-understood semantics, so integration designs can be discussed and diagrammed using a shared vocabulary instead of each codebase inventing its own dialect. Spring Integration exists to turn that shared vocabulary directly into working code, so learning the patterns and learning the framework are largely the same activity.

Reach for EIP thinking (and Spring Integration specifically) when:

- Building an application that needs to react to messages arriving from multiple sources (files, HTTP, message brokers, FTP) with non-trivial routing, filtering, or transformation logic between the source and the eventual business logic.
- Decoupling producers and consumers of data so each can change independently, without direct method-call coupling between them.
- The problem at hand — "route based on content," "aggregate several related messages into one," "retry a failing step" — already has a well-known named pattern, meaning a proven design (and often a ready-made Spring Integration component) already exists rather than needing to be invented.

## 3. Core concept

Think of EIP as the standardized symbols on a real-world plumbing or electrical diagram — a valve, a junction, a filter, a pump — each with an agreed meaning, so any plumber reading the diagram understands exactly what each symbol does without needing the original designer to explain it from scratch. Spring Integration is the toolbox that lets you actually build a system using those exact symbols: a `MessageChannel` is the pipe, a `MessageEndpoint` is a component attached to the pipe (a filter, a pump, a valve), and a `Message` is whatever's flowing through the pipe. The overarching architectural style all of this serves is called **pipes-and-filters** (card 0006 covers this directly): independent processing steps (filters) connected by channels (pipes), each filter unaware of what's upstream or downstream beyond the channel it reads from and writes to.

A few of the most foundational patterns, each with a direct Spring Integration counterpart covered in later cards of this section:

- **Message** — the basic unit of data flowing through the system (card 0002).
- **Message Channel** — the conduit connecting producers and consumers (card 0004; concrete implementations in cards 0008–0012).
- **Message Endpoint** — a component that connects application code to the messaging system (card 0005).
- **Pipes and Filters** — the overall architectural style tying channels and endpoints together (card 0006).

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A pipes-and-filters chain: independent filter components connected by channels, each unaware of anything beyond its own input and output channel">
  <rect x="20" y="80" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Filter A</text>

  <line x1="140" y1="105" x2="190" y2="105" stroke="#79c0ff" stroke-width="3"/>
  <text x="165" y="95" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">channel</text>

  <rect x="190" y="80" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="250" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Filter B</text>

  <line x1="310" y1="105" x2="360" y2="105" stroke="#79c0ff" stroke-width="3"/>
  <text x="335" y="95" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">channel</text>

  <rect x="360" y="80" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Filter C</text>

  <line x1="480" y1="105" x2="530" y2="105" stroke="#79c0ff" stroke-width="3"/>

  <rect x="530" y="80" width="110" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="585" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Business logic</text>

  <text x="330" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">each filter only knows its own input and output channel — never the ones further up or downstream</text>
</svg>

Named EIP components (filters, routers, transformers) connected by channels form a pipeline where each step is independently replaceable.

## 5. Runnable example

The scenario: processing incoming order notifications, starting with a single hardcoded processing step, then splitting it into a named-pattern pipeline (filter, transform, handle), and finally routing different order types to different handlers — each step growing in EIP vocabulary while solving the same underlying problem.

### Level 1 — Basic

```java
// MonolithicOrderProcessor.java
public class MonolithicOrderProcessor {
    public static void main(String[] args) {
        String[] rawOrders = {"ORDER:123:PENDING", "ORDER:124:CANCELLED", "ORDER:125:PENDING"};

        for (String raw : rawOrders) {
            // Everything — filtering, parsing, handling — is tangled together in one place.
            String[] parts = raw.split(":");
            if (parts[2].equals("PENDING")) {
                System.out.println("Processing order #" + parts[1]);
            }
        }
    }
}
```

**How to run:** compile and run with `java MonolithicOrderProcessor.java`. Expected output: `Processing order #123` and `Processing order #125` — `CANCELLED` orders are silently skipped, but the filtering and processing logic are inseparable, hard to test independently, and hard to extend without touching the same block of code.

### Level 2 — Intermediate

Separating the same logic into named EIP roles — a **filter** and a **handler**, connected conceptually by a channel — makes each piece independently understandable and testable, even before introducing Spring Integration's actual channel classes (covered starting card 0004).

```java
// FilteredOrderProcessor.java
import java.util.function.Predicate;
import java.util.function.Consumer;
import java.util.List;

public class FilteredOrderProcessor {

    record Order(String id, String status) {}

    // The Message Filter pattern: a predicate deciding what continues downstream.
    static final Predicate<Order> isPending = order -> order.status().equals("PENDING");

    // The endpoint that actually does something with what passes the filter.
    static final Consumer<Order> processPending = order ->
        System.out.println("Processing order #" + order.id());

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("123", "PENDING"),
            new Order("124", "CANCELLED"),
            new Order("125", "PENDING")
        );

        orders.stream().filter(isPending).forEach(processPending);
    }
}
```

**How to run:** run `java FilteredOrderProcessor.java`. Expected output: identical to Level 1 (`Processing order #123`, `Processing order #125`), but `isPending` and `processPending` are now separately named, independently testable pieces — directly recognizable as the **Message Filter** and **Message Endpoint** patterns, even without Spring Integration's runtime yet.

### Level 3 — Advanced

Real order-processing needs to route different order types to entirely different handling logic (a **Content-Based Router** pattern) rather than a single filter-and-process step — this level adds routing on top of filtering, foreshadowing how Spring Integration's actual router components (covered in a later section) generalize this.

```java
// RoutedOrderProcessor.java
import java.util.Map;
import java.util.function.Consumer;
import java.util.List;

public class RoutedOrderProcessor {

    record Order(String id, String status) {}

    // The Content-Based Router pattern: dispatch based on a property of the message.
    static final Map<String, Consumer<Order>> routes = Map.of(
        "PENDING", order -> System.out.println("Processing order #" + order.id()),
        "CANCELLED", order -> System.out.println("Issuing refund for order #" + order.id()),
        "SHIPPED", order -> System.out.println("Sending tracking email for order #" + order.id())
    );

    static final Consumer<Order> deadLetter = order ->
        System.err.println("Unknown status for order #" + order.id() + ", routing to dead letter");

    public static void main(String[] args) {
        List<Order> orders = List.of(
            new Order("123", "PENDING"),
            new Order("124", "CANCELLED"),
            new Order("125", "SHIPPED"),
            new Order("126", "UNKNOWN_STATUS")
        );

        for (Order order : orders) {
            routes.getOrDefault(order.status(), deadLetter).accept(order);
        }
    }
}
```

**How to run:** run `java RoutedOrderProcessor.java`. Expected output:
```
Processing order #123
Issuing refund for order #124
Sending tracking email for order #125
Unknown status for order #126 for order #126, routing to dead letter
```
Each order type is routed to its own dedicated handler based purely on its `status` field, and an order with an unrecognized status falls through to a dead-letter handler instead of being silently dropped or crashing the whole batch — directly recognizable as the **Content-Based Router** plus **Dead Letter Channel** patterns working together.

## 6. Walkthrough

Tracing `RoutedOrderProcessor` processing its four orders, in execution order:

1. `routes` is built once as a `Map` from status string to handling `Consumer` — this is the router's configuration, defined declaratively before any order is processed.
2. The `for` loop iterates the four orders one at a time, in the order they appear in the list.
3. For order `#123` (`PENDING`), `routes.getOrDefault("PENDING", deadLetter)` finds a matching entry and returns the pending-order handler, which prints the "Processing" message.
4. For order `#124` (`CANCELLED`), the router finds the cancelled-order handler and prints the "Issuing refund" message — a structurally identical dispatch to step 3, but landing on different logic entirely because the routing key differs.
5. For order `#125` (`SHIPPED`), the same dispatch mechanism finds the shipped-order handler.
6. For order `#126` (`UNKNOWN_STATUS`), `routes.getOrDefault(...)` finds no matching key in the map, so it falls back to the supplied default, `deadLetter`, which logs the order to standard error instead of silently dropping it or throwing an exception that would halt the rest of the batch.

```
for each order:
  routes.getOrDefault(order.status(), deadLetter).accept(order)

  "PENDING"       -> found in map -> process handler
  "CANCELLED"     -> found in map -> refund handler
  "SHIPPED"       -> found in map -> tracking-email handler
  "UNKNOWN_STATUS"-> NOT found    -> deadLetter fallback
```

## 7. Gotchas & takeaways

> Reinventing an EIP pattern under a different, project-specific name is a common trap — a routing `Map` like the one above genuinely *is* the Content-Based Router pattern, and recognizing that connects the code to decades of prior art (known variations, known pitfalls, known Spring Integration components already built for it) rather than treating it as a bespoke, one-off design.

- EIP's value is primarily vocabulary and proven design, not any single implementation — Spring Integration is one concrete realization of the catalogue, but the patterns themselves predate and outlive any specific framework.
- Recognizing which named pattern a piece of ad hoc logic actually implements (a filter, a router, a splitter) is often the first step toward simplifying it — usually there's already a well-understood, tested component for exactly that shape of problem.
- A **dead letter** path (routing unrecognized or unprocessable messages somewhere visible, rather than silently dropping or crashing on them) is itself a named EIP pattern (Dead Letter Channel) worth applying broadly, not just in message-broker contexts.
- The remaining cards in this section (Message, channels, endpoints, pipes-and-filters) build up the concrete Spring Integration vocabulary and API that implements these same ideas directly, with real `Message` objects and real channel implementations.
- Approaching an integration problem by first asking "which EIP pattern is this?" before writing code tends to produce a design that's both easier to explain to others and more likely to reuse an existing, battle-tested Spring Integration component instead of custom glue code.
