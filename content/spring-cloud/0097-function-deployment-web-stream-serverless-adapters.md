---
card: spring-cloud
gi: 97
slug: function-deployment-web-stream-serverless-adapters
title: "Function deployment (web, stream, serverless adapters)"
---

## 1. What it is

Spring Cloud Function ships separate adapter starters — `spring-cloud-starter-function-web` (HTTP), `spring-cloud-stream-binder-*` (message broker), and per-cloud-provider adapters (`spring-cloud-function-adapter-aws`, `-azure`, `-gcp`) — and which one is on the application's classpath is the *only* thing that determines how a function bean is invoked; the function's own code never changes across any of these deployment targets.

```xml
<!-- swap this ONE dependency to change HOW the function is invoked -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-function-web</artifactId>
</dependency>
```

```java
@Bean
public Function<String, String> uppercase() { return String::toUpperCase; }
```

## 2. Why & when

A function written against `java.util.function.Function` has no inherent opinion about how it gets invoked — the previous card established that the same bean can serve as an HTTP endpoint, a stream binding, or a serverless handler. The deployment adapter is what actually wires that possibility to reality: adding the web starter causes Spring Cloud Function to auto-configure a `RestController`-equivalent that maps HTTP requests onto function invocations; adding a stream binder causes it to auto-configure a binding onto a broker instead; adding a cloud-provider adapter causes it to auto-configure that provider's specific handler interface (`RequestHandler` for AWS Lambda, `HttpTrigger`-annotated methods for Azure Functions) around the function bean. None of this requires touching the function's own source.

Reach for a specific adapter when:

- The deployment target is HTTP-facing (a typical microservice endpoint) — add `spring-cloud-starter-function-web`, and the function becomes reachable at a path matching its bean name.
- The deployment target is message-driven (part of an event-driven pipeline, as earlier Stream cards covered) — add the appropriate `spring-cloud-stream-binder-*` dependency, and the function becomes a stream binding instead, with `spring.cloud.function.definition` selecting which bean(s).
- The deployment target is a serverless platform (AWS Lambda, Azure Functions, Google Cloud Functions) — add that provider's Spring Cloud Function adapter, which wraps the same function bean in whatever interface that platform's runtime expects to invoke.

## 3. Core concept

```
 ONE function bean:  Function<OrderRequest, OrderConfirmation> placeOrder

 classpath contains spring-cloud-starter-function-web:
   -> auto-configures: POST /placeOrder  (HTTP request body -> function -> HTTP response body)

 classpath contains spring-cloud-stream-binder-kafka:
   -> auto-configures: placeOrder-in-0 / placeOrder-out-0 Kafka bindings
      (Kafka message -> function -> Kafka message)

 classpath contains spring-cloud-function-adapter-aws:
   -> auto-configures: a Lambda RequestHandler wrapping the SAME function
      (Lambda event -> function -> Lambda response)
```

Exactly one deployment adapter is typically active per artifact/jar — the function bean's source code is identical across all three; only the build's dependencies (and, correspondingly, the packaging: a runnable jar, a jar destined for a broker-connected deployment, or a Lambda-shaped zip/jar) differ.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One function bean is packaged three separate times with three different adapter dependencies producing an HTTP deployable a stream deployable and a serverless deployable from identical function source code">
  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">placeOrder function source</text>

  <rect x="30" y="130" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="110" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">+ function-web</text>
  <text x="110" y="166" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; deployable A: HTTP service</text>

  <rect x="240" y="130" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">+ stream-binder-kafka</text>
  <text x="320" y="166" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; deployable B: Kafka consumer</text>

  <rect x="450" y="130" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">+ adapter-aws</text>
  <text x="530" y="166" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; deployable C: Lambda zip</text>

  <defs><marker id="a97" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="66" x2="110" y2="130" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a97)"/>
  <line x1="320" y1="66" x2="320" y2="130" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a97)"/>
  <line x1="360" y1="66" x2="530" y2="130" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a97)"/>
</svg>

Three separate builds of the same source module, distinguished only by which adapter dependency (and matching packaging) each one includes.

## 5. Runnable example

The scenario: one `Function<String, String>` deployed conceptually three ways, modeling exactly what each adapter does to it without pulling in real HTTP/Kafka/Lambda dependencies — three thin adapter simulations wrapping one shared, unmodified function. Start with the function alone, then wrap it with a web-style adapter, then add stream and serverless-style adapters side by side to show all three coexisting against the same function source.

### Level 1 — Basic

The function alone — this is the entire "business logic," with no adapter of any kind.

```java
import java.util.function.Function;

public class DeploymentAdaptersLevel1 {
    // this is the ONLY code that ever changes across web / stream / serverless deployments -- none, in fact
    static Function<String, String> placeOrder = orderText -> "CONFIRMED:" + orderText.toUpperCase();

    public static void main(String[] args) {
        System.out.println(placeOrder.apply("order-123"));
    }
}
```

How to run: `java DeploymentAdaptersLevel1.java`

`placeOrder` has no imports, annotations, or dependencies beyond `java.util.function.Function` — nothing here reveals, or constrains, which deployment target it will eventually run under.

### Level 2 — Intermediate

Wrap `placeOrder` with a simulated web adapter — an HTTP-shaped request in, HTTP-shaped response out, with the function called in between.

```java
import java.util.function.Function;

public class DeploymentAdaptersLevel2 {
    static Function<String, String> placeOrder = orderText -> "CONFIRMED:" + orderText.toUpperCase();

    record HttpRequest(String method, String path, String body) {}
    record HttpResponse(int status, String body) {}

    // models what spring-cloud-starter-function-web auto-configures around the bean
    static HttpResponse webAdapter(Function<String, String> fn, HttpRequest req) {
        if (!req.method().equals("POST")) return new HttpResponse(405, "Method Not Allowed");
        String result = fn.apply(req.body()); // the function itself never sees "HttpRequest" at all
        return new HttpResponse(200, result);
    }

    public static void main(String[] args) {
        HttpResponse response = webAdapter(placeOrder, new HttpRequest("POST", "/placeOrder", "order-123"));
        System.out.println("status=" + response.status() + " body=" + response.body());
    }
}
```

How to run: `java DeploymentAdaptersLevel2.java`

`webAdapter` handles everything HTTP-specific (the method check, wrapping the result in a status code) while `placeOrder` itself only ever sees and returns plain `String` — exactly mirroring how the real web adapter's generated controller extracts the request body, calls the function, and wraps the return value in an HTTP response.

### Level 3 — Advanced

Add stream-style and serverless-style adapters alongside the web adapter, all three wrapping the identical `placeOrder` function, to show every deployment target coexisting against one shared function source.

```java
import java.util.*;
import java.util.function.Function;

public class DeploymentAdaptersLevel3 {
    static Function<String, String> placeOrder = orderText -> "CONFIRMED:" + orderText.toUpperCase();

    record HttpRequest(String method, String body) {}
    record HttpResponse(int status, String body) {}
    record LambdaEvent(String payload) {}
    record LambdaResponse(String result) {}

    static HttpResponse webAdapter(Function<String, String> fn, HttpRequest req) {
        return new HttpResponse(200, fn.apply(req.body()));
    }

    // models a stream adapter: consumes a queue of messages, produces a queue of results, one function call per message
    static List<String> streamAdapter(Function<String, String> fn, List<String> incomingQueue) {
        List<String> outgoingQueue = new ArrayList<>();
        for (String msg : incomingQueue) outgoingQueue.add(fn.apply(msg));
        return outgoingQueue;
    }

    // models a serverless adapter: one invocation per event, wraps the function's return value in the platform's response shape
    static LambdaResponse lambdaAdapter(Function<String, String> fn, LambdaEvent event) {
        return new LambdaResponse(fn.apply(event.payload()));
    }

    public static void main(String[] args) {
        System.out.println("-- web --");
        System.out.println(webAdapter(placeOrder, new HttpRequest("POST", "order-A")));

        System.out.println("-- stream --");
        System.out.println(streamAdapter(placeOrder, List.of("order-B", "order-C")));

        System.out.println("-- serverless --");
        System.out.println(lambdaAdapter(placeOrder, new LambdaEvent("order-D")));
    }
}
```

How to run: `java DeploymentAdaptersLevel3.java`

All three adapters call `fn.apply(...)` against the exact same `placeOrder` reference — the web adapter does it once per HTTP request, the stream adapter does it once per queued message inside a loop, and the Lambda adapter does it once per invocation event — three completely different invocation cardinalities and wrapping shapes, zero differences in the underlying function logic itself.

## 6. Walkthrough

Trace the `streamAdapter` call in Level 3.

1. `streamAdapter(placeOrder, List.of("order-B", "order-C"))` is called with `fn = placeOrder` and `incomingQueue` containing two elements.
2. An empty `outgoingQueue` list is created to collect results.
3. The `for` loop's first iteration takes `msg = "order-B"`, calls `fn.apply("order-B")`, which runs `placeOrder`'s body: `"CONFIRMED:" + "order-B".toUpperCase()`, producing `"CONFIRMED:ORDER-B"`, which is added to `outgoingQueue`.
4. The second iteration takes `msg = "order-C"`, producing `"CONFIRMED:ORDER-C"` by the identical logic, also added to `outgoingQueue`.
5. `streamAdapter` returns `outgoingQueue`, now containing both results in order — this models exactly what a real stream binder does: consume each message off the broker's topic, invoke the function once per message, and publish each result onto the output topic, in order, with the function bean itself never aware it's being called from a loop over a message queue rather than directly.
6. The `println` prints the list `[CONFIRMED:ORDER-B, CONFIRMED:ORDER-C]`, confirming both messages were processed through the identical function logic used by the web and Lambda adapters in the same run.

```
streamAdapter(placeOrder, [order-B, order-C])
  msg="order-B" -> fn.apply -> "CONFIRMED:ORDER-B" -> added to outgoingQueue
  msg="order-C" -> fn.apply -> "CONFIRMED:ORDER-C" -> added to outgoingQueue
  returns ["CONFIRMED:ORDER-B", "CONFIRMED:ORDER-C"]
```

## 7. Gotchas & takeaways

> **Gotcha:** typically only one adapter dependency is active per deployable artifact — bundling `spring-cloud-starter-function-web` and a stream binder in the same jar without deliberately intending a dual-mode deployment can produce ambiguous or unexpected auto-configuration, since both adapters will attempt to wire up the same function bean(s) to their own transport simultaneously. Choose the adapter(s) deliberately per deployment target rather than adding every adapter dependency "just in case."

- The function's own source is the one artifact shared across every deployment target — this is the entire economic argument for writing business logic as plain functions rather than transport-coupled code: one implementation, tested once, deployed multiple ways without rewriting or re-testing the core logic per target.
- Which adapter activates is purely a function of the classpath (which starter/adapter dependency is present) plus configuration (`spring.cloud.function.definition` selecting which bean(s)) — no code-level "if deployed to Lambda, do X" branching is needed or expected inside the function itself.
- Each adapter's cardinality and wrapping differs meaningfully even though the function call itself doesn't: an HTTP adapter typically handles one request per invocation, a stream adapter processes a continuous flow of messages (a later card covers reactive functions handling this as a genuine stream rather than one-at-a-time), and a serverless adapter handles exactly one event per cold or warm invocation.
- Switching an already-built function-based application from one deployment target to another is primarily a build/packaging change (swap the adapter dependency, adjust packaging for the target platform) rather than an application-logic change, which is the practical payoff most teams actually reach for this pattern to get.
