---
card: spring-cloud
gi: 98
slug: aws-lambda-azure-functions-gcf-adapters
title: "AWS Lambda / Azure Functions / GCF adapters"
---

## 1. What it is

`spring-cloud-function-adapter-aws`, its Azure and Google Cloud Functions counterparts, are thin, provider-specific translation layers that implement each platform's required handler interface (`RequestHandler` for AWS, an `@FunctionName`-annotated method for Azure, a `HttpFunction`/background function signature for GCF) and internally forward every invocation straight through to a Spring Cloud Function bean already discovered from the application context — letting one function bean run unmodified on any of the three major serverless platforms.

```java
// AWS Lambda: the ONLY class needed beyond the function bean itself
public class OrderHandler extends SpringBootRequestHandler<OrderRequest, OrderConfirmation> {}
```

```yaml
# AWS SAM / Lambda config
Handler: com.example.OrderHandler::handleRequest
Runtime: java17
```

## 2. Why & when

Each serverless platform mandates its own handler contract — AWS Lambda expects a class implementing `RequestHandler<I,O>` with a `handleRequest` method, Azure Functions expects a method annotated `@FunctionName` with an `HttpTrigger`-annotated parameter, GCF expects a class implementing `HttpFunction` or a background-function-specific interface — and writing business logic directly against any one of these contracts locks that logic to that one platform, and makes it awkward to test outside of the platform's own tooling. The Spring Cloud Function adapters absorb all of that platform-specific boilerplate into a small, mostly-configuration adapter class, so the actual function bean stays exactly what earlier cards already established: a plain `Function`/`Supplier`/`Consumer`, testable and runnable identically whether it happens to be invoked by AWS's runtime, Azure's runtime, GCF's runtime, or a local JUnit test.

Reach for a specific serverless adapter when:

- The chosen deployment target is a specific serverless platform, and the team wants business logic that stays portable — genuinely runnable outside that platform for local testing — rather than tightly coupled to that platform's own SDK types throughout the codebase.
- Migrating (or planning to potentially migrate) between serverless platforms, or between serverless and a container/web deployment, is a live concern — keeping the function bean and its tests platform-agnostic keeps that migration cheap, since only the adapter class and packaging need to change.
- Cold-start latency needs tuning — the adapters differ somewhat in that AWS's adapter benefits from disabling unnecessary Spring Boot auto-configuration classes to minimize context startup time, and each platform's own build/packaging conventions apply on top of the shared function-bean approach.

## 3. Core concept

```
 function bean:  Function<OrderRequest, OrderConfirmation> placeOrder

 AWS:    class OrderHandler extends SpringBootRequestHandler<..,..> {}
         Lambda invokes OrderHandler.handleRequest(event) -> internally calls placeOrder.apply(event)

 Azure:  @FunctionName("placeOrder")
         public OrderConfirmation run(@HttpTrigger(...) OrderRequest req) { return handler.handleRequest(req); }
         Azure invokes run(req) -> internally calls placeOrder.apply(req)

 GCF:    class OrderFunction implements HttpFunction {
             public void service(HttpRequest req, HttpResponse res) { ... calls placeOrder.apply(...) ... }
         }
         GCF invokes service(req,res) -> internally calls placeOrder.apply(...)
```

Each adapter class is small and almost entirely boilerplate — the actual decision logic inside `placeOrder` never appears in any of the three, and is written and tested exactly once.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One placeOrder function bean is invoked from three different thin adapter classes each implementing a different cloud providers required handler interface">
  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">placeOrder function bean</text>

  <rect x="20" y="130" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="105" y="150" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderHandler</text>
  <text x="105" y="164" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">extends SpringBootRequestHandler (AWS)</text>

  <rect x="235" y="130" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="150" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@FunctionName run()</text>
  <text x="320" y="164" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Azure Functions</text>

  <rect x="450" y="130" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="535" y="150" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderFunction</text>
  <text x="535" y="164" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">implements HttpFunction (GCF)</text>

  <defs><marker id="a98" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="66" x2="105" y2="130" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a98)"/>
  <line x1="320" y1="66" x2="320" y2="130" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a98)"/>
  <line x1="360" y1="66" x2="535" y2="130" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a98)"/>
</svg>

Three thin, provider-mandated adapter classes, each translating that one provider's own invocation contract into a call against the identical shared function bean.

## 5. Runnable example

The scenario: model each cloud provider's handler interface as a minimal Java interface, then implement one adapter class per provider that internally forwards to the same shared `placeOrder` function — proving all three adapters are pure translation with zero duplicated business logic. Start with just the AWS-style handler, then add the Azure-style handler alongside it, then add GCF and a shared test harness verifying all three produce identical results for the same input.

### Level 1 — Basic

A minimal AWS-style `RequestHandler` interface and one adapter class implementing it, forwarding to `placeOrder`.

```java
import java.util.function.Function;

public class ServerlessAdaptersLevel1 {
    interface RequestHandler<I, O> { O handleRequest(I input); } // models AWS Lambda's own interface

    static Function<String, String> placeOrder = orderText -> "CONFIRMED:" + orderText.toUpperCase();

    // this is the ENTIRE AWS adapter class -- no business logic lives here, only forwarding
    static class OrderHandlerAws implements RequestHandler<String, String> {
        public String handleRequest(String input) { return placeOrder.apply(input); }
    }

    public static void main(String[] args) {
        OrderHandlerAws handler = new OrderHandlerAws();
        System.out.println(handler.handleRequest("order-123"));
    }
}
```

How to run: `java ServerlessAdaptersLevel1.java`

`OrderHandlerAws` contains exactly one line of real code, and that line is a forward, not logic — this mirrors how `SpringBootRequestHandler` in the real adapter looks up the function bean from the Spring context and calls it, with the concrete subclass typically needing to add nothing beyond the input/output type parameters.

### Level 2 — Intermediate

Add an Azure-style handler alongside the AWS one, both forwarding to the identical `placeOrder` function, proving the same bean serves both provider contracts unmodified.

```java
import java.util.function.Function;

public class ServerlessAdaptersLevel2 {
    interface RequestHandler<I, O> { O handleRequest(I input); }

    static Function<String, String> placeOrder = orderText -> "CONFIRMED:" + orderText.toUpperCase();

    static class OrderHandlerAws implements RequestHandler<String, String> {
        public String handleRequest(String input) { return placeOrder.apply(input); }
    }

    // models an Azure Functions-style @FunctionName method -- different shape, same forwarding role
    static class OrderHandlerAzure {
        String run(String httpTriggerBody) { return placeOrder.apply(httpTriggerBody); }
    }

    public static void main(String[] args) {
        OrderHandlerAws awsHandler = new OrderHandlerAws();
        OrderHandlerAzure azureHandler = new OrderHandlerAzure();

        String input = "order-456";
        String awsResult = awsHandler.handleRequest(input);
        String azureResult = azureHandler.run(input);

        System.out.println("AWS result: " + awsResult);
        System.out.println("Azure result: " + azureResult);
        System.out.println("identical output across providers: " + awsResult.equals(azureResult));
    }
}
```

How to run: `java ServerlessAdaptersLevel2.java`

`awsResult` and `azureResult` are computed through two structurally different adapter shapes (`handleRequest` vs. `run`) but both simply delegate to `placeOrder.apply`, so `awsResult.equals(azureResult)` prints `true` — the business decision (`"CONFIRMED:" + uppercase`) was made exactly once, in `placeOrder`, regardless of which provider-shaped entry point triggered it.

### Level 3 — Advanced

Add a GCF-style adapter and a shared test harness that invokes all three adapters with the same input set and asserts every provider produces identical output — the kind of portability check that justifies keeping business logic out of provider-specific classes in the first place.

```java
import java.util.*;
import java.util.function.Function;

public class ServerlessAdaptersLevel3 {
    interface RequestHandler<I, O> { O handleRequest(I input); }

    static Function<String, String> placeOrder = orderText -> "CONFIRMED:" + orderText.toUpperCase();

    static class OrderHandlerAws implements RequestHandler<String, String> {
        public String handleRequest(String input) { return placeOrder.apply(input); }
    }

    static class OrderHandlerAzure {
        String run(String httpTriggerBody) { return placeOrder.apply(httpTriggerBody); }
    }

    // models a GCF HttpFunction-style adapter -- service() takes a request, writes a response
    static class OrderHandlerGcf {
        String service(String requestBody) { return placeOrder.apply(requestBody); }
    }

    static void assertEqual(String label, String expected, String actual) {
        if (!expected.equals(actual)) throw new AssertionError(label + ": expected " + expected + " but got " + actual);
        System.out.println(label + ": OK (" + actual + ")");
    }

    public static void main(String[] args) {
        OrderHandlerAws aws = new OrderHandlerAws();
        OrderHandlerAzure azure = new OrderHandlerAzure();
        OrderHandlerGcf gcf = new OrderHandlerGcf();

        List<String> testInputs = List.of("order-A", "order-B", "order-C");

        for (String input : testInputs) {
            String expected = placeOrder.apply(input); // ground truth: the function itself, called directly
            assertEqual("AWS[" + input + "]", expected, aws.handleRequest(input));
            assertEqual("Azure[" + input + "]", expected, azure.run(input));
            assertEqual("GCF[" + input + "]", expected, gcf.service(input));
        }

        System.out.println("all three provider adapters produce IDENTICAL results for every input");
    }
}
```

How to run: `java ServerlessAdaptersLevel3.java`

For every one of the three test inputs, all three provider-shaped adapters are asserted equal to `placeOrder.apply(input)` called directly — this is precisely the portability test a team migrating (or hedging) between serverless providers wants: proof that the actual behavior is a property of the function bean alone, entirely independent of which platform-specific class happens to be invoking it.

## 6. Walkthrough

Trace the loop body in Level 3 for `input = "order-B"`.

1. `expected = placeOrder.apply("order-B")` runs `placeOrder`'s body directly: `"CONFIRMED:" + "order-B".toUpperCase()` evaluates to `"CONFIRMED:ORDER-B"`, establishing the ground-truth result with no adapter involved at all.
2. `assertEqual("AWS[order-B]", expected, aws.handleRequest("order-B"))` calls `aws.handleRequest`, which internally runs `placeOrder.apply("order-B")` again — the identical computation — producing `"CONFIRMED:ORDER-B"` once more; since this matches `expected`, `assertEqual` prints an `OK` line rather than throwing.
3. `assertEqual("Azure[order-B]", expected, azure.run("order-B"))` performs the same check through `OrderHandlerAzure.run`, which also just forwards to `placeOrder.apply` — again matching, again `OK`.
4. `assertEqual("GCF[order-B]", expected, gcf.service("order-B"))` performs the same check a third time through `OrderHandlerGcf.service` — again matching, again `OK`.
5. This same three-step check repeats for `"order-A"` and `"order-C"` on the loop's other iterations, and the final `println` confirms all nine assertions (three inputs times three providers) passed without any `AssertionError` being thrown.

```
input = "order-B"
  ground truth: placeOrder.apply("order-B") = "CONFIRMED:ORDER-B"
  AWS adapter:   handleRequest -> placeOrder.apply -> "CONFIRMED:ORDER-B"  == expected -> OK
  Azure adapter: run           -> placeOrder.apply -> "CONFIRMED:ORDER-B"  == expected -> OK
  GCF adapter:   service       -> placeOrder.apply -> "CONFIRMED:ORDER-B"  == expected -> OK
```

## 7. Gotchas & takeaways

> **Gotcha:** cold-start latency behaves differently per provider even though the function logic is identical — AWS Lambda's Spring Boot context initialization on a cold start can be a meaningful fraction of total invocation latency unless deliberately tuned (disabling unneeded auto-configuration, favoring `spring-cloud-function-adapter-aws`'s custom context initialization over the full Spring Boot bootstrap where supported), and this tuning is adapter- and provider-specific — portability of business logic does not automatically mean portability of performance characteristics.

- Every provider adapter's job is narrowly to translate that provider's own invocation contract into a call against a Spring Cloud Function bean — real business logic inside an adapter class is a sign the portability the pattern is meant to provide has been quietly given up.
- Testing the function bean directly (as `expected = placeOrder.apply(input)` does) rather than through any one provider's adapter is both simpler and provider-independent — most of a serverless application's actual test coverage should target the function bean, not the thin adapter wrapping it.
- Migrating between serverless providers, or between serverless and a containerized/web deployment, becomes primarily a matter of swapping the adapter dependency and packaging, precisely because the function bean itself carries zero provider-specific code.
- Provider-specific concerns that genuinely can't be abstracted away — cold-start tuning, provider-specific event payload shapes for non-HTTP triggers, IAM/permissions configuration — still belong in the adapter layer or in deployment configuration, not smuggled into the function bean where they'd undermine its portability.
