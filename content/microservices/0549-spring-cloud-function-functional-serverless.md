---
card: microservices
gi: 549
slug: spring-cloud-function-functional-serverless
title: "Spring Cloud Function (functional/serverless)"
---

## 1. What it is

**Spring Cloud Function** promotes plain Java `Function`, `Supplier`, and `Consumer` beans into a portable, adaptable unit of business logic that can run behind multiple different "front doors" — a standard web endpoint, a message broker binding (this is exactly the foundation [Spring Cloud Stream](0547-spring-cloud-stream-event-driven.md) is built on), or a serverless platform (AWS Lambda, Azure Functions, Google Cloud Functions) — without changing the function's own code. You write the logic once as a plain function; Spring Cloud Function's adapters handle translating whatever platform-specific invocation mechanism (an HTTP request, a broker message, a cloud provider's event payload) into a call to that same function.

## 2. Why & when

You reach for Spring Cloud Function whenever you want business logic to remain portable across different invocation mechanisms, or specifically when targeting a serverless platform from a Spring codebase:

- **Writing logic directly against a specific serverless platform's SDK (an AWS Lambda `RequestHandler` interface, for instance) couples that logic to AWS specifically** — moving to a different cloud provider, or to a traditional deployed server, would require rewriting the handler around that platform's own invocation contract.
- **A plain `Function<Input, Output>` has no dependency on any specific platform at all** — Spring Cloud Function's adapters are what translate an incoming AWS Lambda event, an HTTP POST body, or a Kafka message into a call to that same function, and translate its return value back into whatever response shape the invoking platform expects.
- **This is exactly the same underlying mechanism [Spring Cloud Stream](0547-spring-cloud-stream-event-driven.md) uses for message-driven functions** — Spring Cloud Function is the more general-purpose foundation; Stream specializes it specifically for message broker bindings, while Spring Cloud Function itself additionally supports serverless and plain HTTP invocation of the same function shape.
- **You reach for it specifically when deploying to a serverless platform from a Spring codebase**, or when you want a single piece of business logic to be invokable interchangeably as a web endpoint, a message handler, or a serverless function without rewriting it for each context — useful for logic that might start as a simple web endpoint but later need to also run as a background message consumer, or vice versa.

## 3. Core concept

Think of a specific, well-defined task — "given a document, produce a summary" — that could be performed by a human sitting at a desk (a traditional server), by someone answering an intercom whenever a document slides through a mail slot (a message-driven trigger), or by an on-call person who only gets paged and does the task once, then goes back to being unavailable, only paid for the moment they're actually working (a serverless invocation model). The task itself — "summarize this document" — doesn't change across any of these; only how the request for the task arrives, and how the summary is delivered back, differs. Spring Cloud Function keeps "summarize this document" as one unchanging piece of logic, and lets you plug in whichever "how it's triggered" adapter fits your current deployment target.

Concretely:

1. **A `Function<Input, Output>`, `Supplier<Output>`, or `Consumer<Input>` bean is the unit of portable logic** — declared with no reference to HTTP, message brokers, or any specific cloud provider's SDK anywhere in its code.
2. **The web adapter** exposes this same function as an HTTP endpoint automatically (POST body deserialized as input, function's return value serialized as the response body) — no `@RestController` or `@PostMapping` needed at all.
3. **The stream adapter** (what Spring Cloud Stream itself uses) wires the function to message broker input/output bindings, exactly as discussed for Stream.
4. **Cloud provider-specific adapters** (`spring-cloud-function-adapter-aws`, for Azure, for GCP) translate that platform's own specific event/context objects into a call to the same function, and its return value back into that platform's expected response shape — deploying the identical function as an AWS Lambda, an Azure Function, or a traditional web endpoint is a matter of which adapter dependency and deployment configuration you choose, not a rewrite of the function itself.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One plain Function bean can be invoked through several different adapters -- web, message broker, or serverless platform -- without changing the function's own code">
  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Function&lt;In, Out&gt;</text>

  <line x1="290" y1="70" x2="130" y2="110" stroke="#8b949e"/>
  <line x1="330" y1="70" x2="330" y2="110" stroke="#8b949e"/>
  <line x1="370" y1="70" x2="530" y2="110" stroke="#8b949e"/>

  <rect x="40" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">web adapter (HTTP)</text>
  <rect x="240" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">stream adapter (broker)</text>
  <rect x="440" y="110" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="530" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">serverless adapter (AWS/Azure/GCP)</text>
</svg>

The same function bean plugs into a web, message-broker, or serverless adapter without any change to its own code.

## 5. Runnable example

Scenario: a text-summarization function that needs to run identically across different invocation contexts. We start with a plain Java model of a platform-coupled handler, extend it to a portable function form, then show the real Spring Cloud Function shape and its adapters.

### Level 1 — Basic

```java
// File: PlatformCoupledHandler.java -- models being COUPLED to a
// specific serverless platform's handler interface directly.
public class PlatformCoupledHandler {
    // imagine this mirrors AWS Lambda's own RequestHandler<Input, Output> interface shape
    interface AwsLambdaRequestHandler<I, O> { O handleRequest(I input, Object awsLambdaContext); }

    static class SummarizeHandler implements AwsLambdaRequestHandler<String, String> {
        public String handleRequest(String document, Object awsLambdaContext) {
            return document.length() > 20 ? document.substring(0, 20) + "..." : document;
        }
    }

    public static void main(String[] args) {
        SummarizeHandler handler = new SummarizeHandler();
        System.out.println(handler.handleRequest("This is a long document that needs summarizing", null));
        System.out.println("Problem: this class implements AWS's OWN interface -- moving to Azure means rewriting it entirely.");
    }
}
```

How to run: `java PlatformCoupledHandler.java`

`SummarizeHandler` directly implements a stand-in for AWS Lambda's own specific handler interface — the business logic (truncating a document) is entangled with that one platform's exact method signature and context type, meaning a move to Azure Functions or a plain web endpoint would require an entirely separate implementation.

### Level 2 — Intermediate

```java
// File: PortableFunctionForm.java -- extracts the SAME logic into a
// PLAIN java.util.function.Function, with NO platform coupling at all.
import java.util.function.Function;

public class PortableFunctionForm {
    // pure business logic -- no AWS, Azure, or web-specific type anywhere
    static Function<String, String> summarize = document ->
        document.length() > 20 ? document.substring(0, 20) + "..." : document;

    // a GENERIC adapter, standing in for what Spring Cloud Function's real
    // adapters do: translate a platform-specific invocation into a plain function call
    static String invokeViaGenericAdapter(Function<String, String> function, String platformSpecificInput) {
        return function.apply(platformSpecificInput); // the SAME function works regardless of what called this
    }

    public static void main(String[] args) {
        System.out.println(invokeViaGenericAdapter(summarize, "This is a long document that needs summarizing"));
        System.out.println("summarize itself never referenced AWS, Azure, or HTTP -- ANY adapter can invoke it identically.");
    }
}
```

How to run: `java PortableFunctionForm.java`

`summarize` is a plain `Function<String, String>` with zero platform dependency — `invokeViaGenericAdapter` stands in for any of Spring Cloud Function's real adapters (web, stream, or a serverless platform's), all of which ultimately just call `function.apply(input)` after translating their own platform-specific invocation into that plain call.

### Level 3 — Advanced

```java
// File: SpringCloudFunctionRealShape.java -- the REAL Spring Cloud
// Function shape: ONE Function bean, invokable via web, stream, or
// serverless adapters depending purely on which dependency is on the classpath.
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.function.Function;

public class SpringCloudFunctionRealShape {

    @Configuration
    static class FunctionConfig {
        @Bean
        public Function<String, String> summarize() {
            return document -> document.length() > 20 ? document.substring(0, 20) + "..." : document;
        }
    }

    // WITH spring-cloud-function-web on the classpath:
    //   POST /summarize
    //   body: "This is a long document that needs summarizing"
    //   -> Spring Cloud Function automatically exposes this as an HTTP endpoint, NO @RestController needed

    // WITH spring-cloud-function-adapter-aws on the classpath, packaged as a Lambda:
    //   AWS Lambda invokes this SAME "summarize" function directly via the AWS adapter,
    //   translating the Lambda event payload into the function's input automatically

    // WITH spring-cloud-stream + a binder on the classpath:
    //   this SAME function is wired to a message broker's input/output bindings instead,
    //   exactly as discussed for Spring Cloud Stream
}
```

How to run: depending on which adapter dependency is added — `spring-cloud-function-web` (run via `mvn spring-boot:run` and `POST /summarize`), `spring-cloud-function-adapter-aws` (packaged and deployed as an AWS Lambda function), or `spring-cloud-stream` with a binder (deployed as a message-driven service) — the identical `summarize` bean above is invoked through that specific adapter, with zero change to the bean's own code across any of these three deployment choices.

`summarize()` is declared once, as a plain `Function<String, String>` bean — nothing about its declaration hints at which adapter will eventually invoke it. Whether it ends up exposed as a web endpoint, a message handler, or an AWS Lambda function is determined entirely by which adapter dependency is present on the classpath at build/deploy time, making this single piece of logic genuinely portable across all three deployment models without a rewrite.

## 6. Walkthrough

Trace what happens when the `summarize` function bean is invoked via two different adapters, contrasting their translation steps:

**Via the web adapter** (`spring-cloud-function-web` on the classpath):

1. **An HTTP `POST /summarize` request arrives** with body `"This is a long document that needs summarizing"` and `Content-Type: text/plain` (or similar).
2. **Spring Cloud Function's web adapter recognizes the URL path `/summarize` matches the bean name `summarize`**, and reads the request body as the function's input.
3. **It calls `summarize.apply("This is a long document that needs summarizing")`** — the exact same function object that would be called by any other adapter.
4. **The function's return value, `"This is a long docum..."`, is written as the HTTP response body**, with a `200 OK` status.

**Via the AWS Lambda adapter** (`spring-cloud-function-adapter-aws` on the classpath, deployed as a Lambda):

1. **AWS Lambda's own invocation infrastructure calls the deployed handler** with an AWS-specific event payload (JSON, wrapped in AWS's own request/context objects) representing the same input document.
2. **Spring Cloud Function's AWS adapter deserializes the relevant portion of that AWS-specific event payload into a plain `String`** (the function's declared input type), discarding or setting aside AWS-specific metadata not relevant to the function itself.
3. **It calls `summarize.apply(...)` with that extracted string** — again, the identical function object and call, unaware it's being invoked from within an AWS Lambda execution environment rather than a web server.
4. **The function's return value is wrapped back into whatever response shape AWS Lambda expects** and returned through AWS's own invocation response mechanism.

In both cases, step 3 — the actual call to `summarize.apply(...)` — is identical. Only the surrounding translation (steps 1, 2, and 4) differs, and that translation logic lives entirely within Spring Cloud Function's adapters, never inside the `summarize` function's own declaration.

## 7. Gotchas & takeaways

> **Gotcha:** serverless platforms typically have "cold start" latency — the time to initialize a fresh execution environment (including, for a Spring application, the Spring context itself) before the first invocation can be handled — and a full Spring Boot application context can add meaningfully more cold-start latency than a minimal, hand-written platform-specific handler would; Spring Cloud Function includes optimizations for this (like avoiding full auto-configuration scanning where possible), but it's worth measuring actual cold-start latency for your specific function before assuming portability comes entirely free of cost in a serverless deployment.

- Spring Cloud Function promotes plain `Function`/`Supplier`/`Consumer` beans into logic that's portable across web, message-broker, and serverless invocation contexts, without coupling the logic itself to any one of them.
- It's the general-purpose foundation [Spring Cloud Stream](0547-spring-cloud-stream-event-driven.md) itself builds on for message-driven functions — Stream specializes this same functional model specifically for broker bindings.
- Which adapter actually invokes a given function bean is determined by which adapter dependency is present at build/deploy time — not by anything declared in the function's own code.
- Weigh serverless cold-start latency against the convenience of portability when choosing this approach for a genuinely latency-sensitive serverless deployment — portability and raw cold-start performance are a real trade-off worth measuring, not assuming.
