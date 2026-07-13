---
card: spring-integration
gi: 7
slug: programming-models-xml-annotations-java-dsl
title: "Programming models (XML, annotations, Java DSL)"
---

## 1. What it is

Spring Integration supports three distinct ways to declare the same underlying pipes-and-filters concepts (channels, endpoints, and how they're wired together): an original **XML namespace** configuration style (`<int:channel>`, `<int:service-activator>`), an **annotation-driven** style (`@ServiceActivator`, `@Router`, `@Filter` on plain Java methods, as already glimpsed in card 0005), and the modern **Java DSL** (`IntegrationFlow`, a fluent builder API). All three ultimately configure the exact same underlying runtime components — they're different surfaces over identical machinery, not three different messaging systems.

## 2. Why & when

Spring Integration predates the Java DSL by several years, and its original configuration model was XML — verbose, but explicit and easy to visualize as a wiring diagram. As Spring's broader ecosystem shifted toward annotation-driven and then fluent Java-based configuration, Spring Integration followed, adding annotations (letting plain Java methods become endpoints with minimal ceremony, as in card 0005) and eventually the Java DSL (letting an entire flow — channels, endpoints, routing — be expressed as one fluent, type-checked Java expression). All three remain supported today, and a real application often mixes them: annotated endpoint methods wired into flows defined with the Java DSL is a common, idiomatic combination.

Choose based on:

- **Java DSL** for new applications and any flow whose structure benefits from being visible as one connected, type-checked expression — this is generally the recommended default for new code today, given its conciseness and IDE support.
- **Annotations** (`@ServiceActivator` and friends) for exposing a plain, already-existing Java method as an endpoint with minimal fuss, often used *together* with Java DSL-defined channels rather than as a full alternative to it.
- **XML** primarily when maintaining an existing codebase already built that way, or when a visual, declarative wiring diagram genuinely fits a team's existing tooling and conventions better than Java code.

## 3. Core concept

Think of the three programming models as three different notations for writing down the same piece of music — traditional staff notation (XML: explicit, verbose, but precisely visual), a simplified lead sheet with chord symbols (annotations: less ceremony, relies on convention and context to fill in the rest), and a modern digital sequencer's piano-roll view (Java DSL: fluent, visual in its own way, and directly executable). A musician reading any of the three, if fluent in it, ends up understanding and being able to perform the identical piece — the notation is a surface difference, not a difference in the music itself.

```java
// Java DSL: an entire flow as one fluent, connected expression
@Bean
public IntegrationFlow orderFlow() {
    return IntegrationFlow.from("orderInputChannel")
        .filter((String order) -> !order.isBlank())
        .transform((String order) -> order.toUpperCase())
        .handle((order, headers) -> {
            System.out.println("Handling: " + order);
            return null;
        })
        .get();
}
```

```java
// Annotations: the same kind of endpoint, expressed as a plain method plus metadata
@ServiceActivator(inputChannel = "orderInputChannel")
public void handle(String order) {
    System.out.println("Handling: " + order);
}
```

```xml
<!-- XML: the same wiring, expressed declaratively -->
<int:channel id="orderInputChannel"/>
<int:service-activator input-channel="orderInputChannel" ref="orderHandler" method="handle"/>
```

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="XML, annotations, and Java DSL are three different configuration surfaces over the identical underlying channel and endpoint runtime">
  <rect x="20" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">XML namespace</text>

  <rect x="240" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Annotations</text>

  <rect x="460" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Java DSL</text>

  <line x1="110" y1="70" x2="330" y2="130" stroke="#8b949e" stroke-width="1"/>
  <line x1="330" y1="70" x2="330" y2="130" stroke="#8b949e" stroke-width="1"/>
  <line x1="550" y1="70" x2="330" y2="130" stroke="#8b949e" stroke-width="1"/>

  <rect x="220" y="130" width="220" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="150" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">identical underlying</text>
  <text x="330" y="167" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MessageChannel / endpoint beans</text>
</svg>

All three configuration styles compile down to the same runtime channel and endpoint beans.

## 5. Runnable example

The scenario: building the same simple order-processing flow (validate a non-blank order, then log it) using progressively richer capabilities within the Java DSL, since it's the recommended modern default — starting with a single-step flow, then a multi-step flow mixing DSL steps with an annotated handler bean, and finally a flow with conditional branching.

### Level 1 — Basic

```java
// BasicDslFlowConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.integration.dsl.IntegrationFlow;
import org.springframework.integration.channel.DirectChannel;

@Configuration
public class BasicDslFlowConfig {

    @Bean
    public DirectChannel orderInputChannel() {
        return new DirectChannel();
    }

    @Bean
    public IntegrationFlow orderFlow() {
        return IntegrationFlow.from(orderInputChannel())
            .handle((String order, java.util.Map<String, Object> headers) -> {
                System.out.println("Handling order: " + order);
                return null; // null return means no message continues further downstream
            })
            .get();
    }
}
```

**How to run:** run within a Spring Boot application, then send a message via `MessagingTemplate` or an autowired `orderInputChannel`: `messagingTemplate.convertAndSend(orderInputChannel(), "order-123");`. Expected output: `Handling order: order-123` — a complete, working channel-plus-endpoint flow expressed as a single fluent Java expression, with no XML and no separately-annotated class needed.

### Level 2 — Intermediate

Real applications commonly combine the DSL for flow structure with a separately-defined, annotated (or plain) service bean for the actual business logic — keeping the flow's *shape* declarative while keeping business logic in an ordinarily-testable plain class.

```java
// OrderService.java — plain business logic, reusable and testable with no messaging types involved
public class OrderService {
    public String process(String order) {
        return "PROCESSED:" + order;
    }
}
```

```java
// MultiStepDslFlowConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.integration.dsl.IntegrationFlow;
import org.springframework.integration.channel.DirectChannel;

@Configuration
public class MultiStepDslFlowConfig {

    @Bean
    public DirectChannel orderInputChannel() {
        return new DirectChannel();
    }

    @Bean
    public OrderService orderService() {
        return new OrderService();
    }

    @Bean
    public IntegrationFlow orderFlow(OrderService orderService) {
        return IntegrationFlow.from(orderInputChannel())
            .filter((String order) -> !order.isBlank())          // Message Filter pattern, card 0001
            .transform(orderService::process)                     // delegates to plain business logic
            .handle((processed, headers) -> {
                System.out.println("Final result: " + processed);
                return null;
            })
            .get();
    }
}
```

**How to run:** send `"order-123"` through `orderInputChannel`. Expected output: `Final result: PROCESSED:order-123` — the flow's structure (filter, then transform, then handle) is declared fluently in the DSL, while `OrderService.process` remains a plain, independently-unit-testable method with zero messaging types in its own signature, exactly the separation of concerns card 0005 described for endpoints generally.

### Level 3 — Advanced

The DSL supports conditional branching directly, letting a single flow route different orders to different handling logic based on content — the Content-Based Router pattern from card 0001, expressed fluently.

```java
// BranchingDslFlowConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.integration.dsl.IntegrationFlow;
import org.springframework.integration.channel.DirectChannel;

@Configuration
public class BranchingDslFlowConfig {

    @Bean
    public DirectChannel orderInputChannel() {
        return new DirectChannel();
    }

    @Bean
    public IntegrationFlow orderFlow() {
        return IntegrationFlow.from(orderInputChannel())
            .<String, String>route(order -> order.startsWith("EXPRESS") ? "express" : "standard", mapping -> mapping
                .subFlowMapping("express", sf -> sf
                    .handle((order, headers) -> {
                        System.out.println("EXPEDITED handling: " + order);
                        return null;
                    }))
                .subFlowMapping("standard", sf -> sf
                    .handle((order, headers) -> {
                        System.out.println("Standard handling: " + order);
                        return null;
                    }))
            )
            .get();
    }
}
```

**How to run:** send `"EXPRESS-order-999"` and separately `"order-123"` through `orderInputChannel`. Expected output: `EXPEDITED handling: EXPRESS-order-999` for the first message and `Standard handling: order-123` for the second — a single fluently-defined flow routes each message down an entirely different sub-flow purely based on its content, with the routing logic and both branches visible together in one connected Java expression.

## 6. Walkthrough

Tracing `"EXPRESS-order-999"` through `BranchingDslFlowConfig`'s flow, in execution order:

1. The message is sent to `orderInputChannel`, the flow's declared entry point.
2. The `.route(...)` step evaluates its routing function, `order -> order.startsWith("EXPRESS") ? "express" : "standard"`, against the payload `"EXPRESS-order-999"` — since it does start with `"EXPRESS"`, the function returns the key `"express"`.
3. The router consults its `mapping` configuration for a sub-flow registered under the key `"express"`, finding the one defined via `.subFlowMapping("express", ...)`.
4. Execution continues into that specific sub-flow, reaching its `.handle(...)` step, which prints `EXPEDITED handling: EXPRESS-order-999` — the `"standard"` sub-flow is never entered at all for this message.
5. For the second message, `"order-123"`, the same routing function is evaluated, but since it doesn't start with `"EXPRESS"`, it returns `"standard"` instead, and the router dispatches into the `"standard"` sub-flow's `.handle(...)` step, printing `Standard handling: order-123`.

```
"EXPRESS-order-999" -> route(): startsWith("EXPRESS")? YES -> key="express" -> express sub-flow -> EXPEDITED handling
"order-123"          -> route(): startsWith("EXPRESS")? NO  -> key="standard" -> standard sub-flow -> Standard handling
```

## 7. Gotchas & takeaways

> Mixing all three programming models within the *same* flow definition (part XML, part annotations, part DSL, tangled together for no clear reason) is a real maintainability trap — while Spring Integration technically allows components defined in different styles to interoperate (since they compile down to the same underlying beans), a codebase that inconsistently mixes styles without a clear rationale becomes harder for new contributors to follow than one that picks a primary style and uses the others only where they add clear, specific value (like keeping business logic in plain annotated classes referenced from DSL-defined flow structure).

- All three programming models (XML, annotations, Java DSL) configure the identical underlying channel and endpoint infrastructure — there's no functional capability exclusive to one that's fundamentally unavailable in the others, though ergonomics differ substantially.
- The Java DSL is generally the recommended default for new Spring Integration code today, given its conciseness, type-checking, and IDE navigability compared to XML.
- A common, idiomatic combination is DSL-defined flow structure (channels, routing, filtering) calling into plain or lightly-annotated Java classes for the actual business logic — keeping the "shape" of the flow and the "substance" of what it does cleanly separated.
- `@ServiceActivator` and similar annotations remain a good fit for exposing an existing plain method as an endpoint with minimal ceremony, and interoperate cleanly with DSL-defined channels feeding into them.
- When reading or maintaining an existing Spring Integration codebase, expect to encounter any (or a mix) of the three styles depending on the project's age and history — recognizing that all three describe the same underlying concepts (channels, endpoints, routing) is what makes moving between them straightforward.
