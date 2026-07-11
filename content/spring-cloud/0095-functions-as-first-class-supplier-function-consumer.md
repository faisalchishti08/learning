---
card: spring-cloud
gi: 95
slug: functions-as-first-class-supplier-function-consumer
title: "Functions as first-class (Supplier/Function/Consumer)"
---

## 1. What it is

Spring Cloud Function lets a plain `java.util.function.Supplier`, `Function`, or `Consumer` bean — with no Spring Cloud Stream or web framework annotations at all — become invokable over HTTP, over a message broker, or from the command line, purely by being registered as a Spring bean; the same function business logic runs unmodified in each of those transports, because the framework adapts to the function's shape rather than the function being written against any particular transport's API.

```java
@Bean
public Function<String, String> uppercase() {
    return value -> value.toUpperCase();
}
```

```bash
curl -H "Content-Type: text/plain" http://localhost:8080/uppercase -d "hello"
# -> HELLO
```

## 2. Why & when

Writing business logic directly against a transport's API (a `@RestController` method for HTTP, a `@StreamListener`/binding method for messaging) ties that logic to how it's currently invoked — porting the same logic to also run as a serverless function, or over a message broker instead of HTTP, traditionally meant rewriting it against a different API. Spring Cloud Function inverts this: the function is written once, as the plainest possible Java functional interface, with zero framework-specific code inside it, and the *adapter* (web, stream, AWS Lambda, Azure Functions, standalone) is what varies — swapping deployment targets is a matter of adding a different adapter dependency, not touching the function body.

Reach for first-class functions when:

- The same business logic genuinely needs to run in more than one context over its lifetime — locally for testing, behind HTTP for one deployment, on a message broker for another, or as a serverless function for a third — and duplicating the logic per transport is wasteful and error-prone.
- Keeping business logic maximally decoupled from any specific framework API is a goal in itself — a `Function<String, String>` is testable with zero mocking of Spring machinery, unlike a `@RestController` method that typically needs at least a slice test context.
- Composing multiple small functions together (a later card covers function composition) benefits from every piece being the same uniform shape, rather than a mix of controller methods, stream listeners, and plain methods that don't naturally chain.

## 3. Core concept

```
                    Function<String, String> uppercase = v -> v.toUpperCase();
                                       |
              -------------------------------------------------
              |                       |                       |
              v                       v                       v
        web adapter             stream adapter          AWS Lambda adapter
        POST /uppercase         Kafka/RabbitMQ topic     Lambda invocation
        body -> function -> response   msg -> function -> msg    event -> function -> response

        SAME function body, THREE different invocation mechanisms wrapped around it
```

`Supplier<T>` (a source with no input, like a scheduled data poll), `Function<T, R>` (transform input to output), and `Consumer<T>` (a sink with no output, like a side-effecting write) cover the three fundamental data-flow shapes a function-based architecture needs.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One plain Function bean is wrapped by a web adapter a stream adapter and a serverless adapter each invoking the same unmodified function body through a different transport">
  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">Function&lt;String,String&gt;</text>

  <rect x="30" y="120" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="105" y="144" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">web adapter (HTTP)</text>
  <rect x="245" y="120" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="144" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">stream adapter (broker)</text>
  <rect x="460" y="120" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="535" y="144" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">serverless adapter</text>

  <defs><marker id="a95" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="66" x2="120" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a95)"/>
  <line x1="320" y1="66" x2="320" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a95)"/>
  <line x1="360" y1="66" x2="520" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a95)"/>
</svg>

The function bean itself never references HTTP, a broker, or a cloud provider — every transport-specific concern lives entirely in the adapter.

## 5. Runnable example

The scenario: a price-formatting function, exercised first as a plain Java function, then invoked through two different simulated "adapters" (a web-style request handler and a message-style consumer loop) with zero changes to the function body, then composed with a second function to show functions chaining cleanly because they share one uniform shape.

### Level 1 — Basic

A plain `Function<Double, String>`, invoked directly — no transport at all, just the function itself.

```java
import java.util.function.Function;

public class FirstClassFunctionsLevel1 {
    public static void main(String[] args) {
        Function<Double, String> formatPrice = price -> String.format("$%.2f", price);

        System.out.println(formatPrice.apply(19.5));
        System.out.println(formatPrice.apply(3.0));
    }
}
```

How to run: `java FirstClassFunctionsLevel1.java`

`formatPrice` has no knowledge of HTTP, messaging, or any framework — it is exactly the shape Spring Cloud Function expects a bean to have, callable with `.apply` and nothing else.

### Level 2 — Intermediate

Wrap the same, unmodified function with two different adapter-style invokers — a "web" one that simulates handling an HTTP request body, and a "stream" one that simulates consuming messages off a queue.

```java
import java.util.*;
import java.util.function.Function;

public class FirstClassFunctionsLevel2 {
    // simulates a minimal web adapter: takes a "request body" string, parses it, calls the function, returns a "response body"
    static String webAdapter(Function<Double, String> fn, String requestBody) {
        double price = Double.parseDouble(requestBody);
        return fn.apply(price); // the function itself is completely unaware this came from "HTTP"
    }

    // simulates a minimal stream adapter: pulls messages off a queue, calls the SAME function for each
    static List<String> streamAdapter(Function<Double, String> fn, List<Double> queue) {
        List<String> results = new ArrayList<>();
        for (Double msg : queue) results.add(fn.apply(msg)); // same function, different invocation loop
        return results;
    }

    public static void main(String[] args) {
        Function<Double, String> formatPrice = price -> String.format("$%.2f", price);

        System.out.println("web adapter: " + webAdapter(formatPrice, "19.5"));
        System.out.println("stream adapter: " + streamAdapter(formatPrice, List.of(3.0, 42.99, 7.25)));
    }
}
```

How to run: `java FirstClassFunctionsLevel2.java`

`formatPrice` is passed, unmodified, into both `webAdapter` and `streamAdapter` — each adapter handles its own transport-specific concern (parsing one request body vs. looping over a queue) and calls `fn.apply` identically, proving the same function body genuinely works under either invocation style.

### Level 3 — Advanced

Compose `formatPrice` with a second function (applying a discount) using `Function.andThen`, and route through both adapters again — demonstrating that composed functions remain just as transport-agnostic as a single one.

```java
import java.util.*;
import java.util.function.Function;

public class FirstClassFunctionsLevel3 {
    static String webAdapter(Function<Double, String> fn, String requestBody) {
        return fn.apply(Double.parseDouble(requestBody));
    }

    static List<String> streamAdapter(Function<Double, String> fn, List<Double> queue) {
        List<String> results = new ArrayList<>();
        for (Double msg : queue) results.add(fn.apply(msg));
        return results;
    }

    public static void main(String[] args) {
        Function<Double, Double> applyDiscount = price -> price * 0.9; // 10% off
        Function<Double, String> formatPrice = price -> String.format("$%.2f", price);

        // composition: ONE function chained from two smaller ones, still just a Function<Double, String>
        Function<Double, String> discountedAndFormatted = applyDiscount.andThen(formatPrice);

        System.out.println("direct call: " + discountedAndFormatted.apply(20.0));
        System.out.println("via web adapter: " + webAdapter(discountedAndFormatted, "50.0"));
        System.out.println("via stream adapter: " + streamAdapter(discountedAndFormatted, List.of(10.0, 100.0)));
    }
}
```

How to run: `java FirstClassFunctionsLevel3.java`

Neither `webAdapter` nor `streamAdapter` needed a single line changed to accept `discountedAndFormatted` instead of `formatPrice` — both parameters are typed as `Function<Double, String>`, and `applyDiscount.andThen(formatPrice)` produces exactly that shape, which is the entire point of building on `java.util.function` interfaces: composition and transport-adaptation both work uniformly, with no special-casing for "this one is composed" anywhere in the adapters.

## 6. Walkthrough

Trace `webAdapter(discountedAndFormatted, "50.0")` in Level 3.

1. `webAdapter` receives `fn = discountedAndFormatted` and `requestBody = "50.0"`.
2. `Double.parseDouble("50.0")` produces the primitive-boxed `50.0`, modeling the deserialization step a real Spring Cloud Function web adapter performs on an incoming HTTP request body.
3. `fn.apply(50.0)` is called — because `fn` is `applyDiscount.andThen(formatPrice)`, this first invokes `applyDiscount.apply(50.0)`, which computes `50.0 * 0.9 = 45.0`.
4. `andThen` then feeds that intermediate result, `45.0`, into `formatPrice.apply(45.0)`, which produces the string `"$45.00"`.
5. `webAdapter` returns `"$45.00"` — modeling the value that would become the real HTTP response body.
6. The `streamAdapter` call proceeds analogously but loops: for the queue `[10.0, 100.0]`, each element passes through the identical two-stage composed function independently, producing `["$9.00", "$90.00"]`.

```
input: 50.0
  applyDiscount.apply(50.0)  -> 45.0        (stage 1 of the composed function)
  formatPrice.apply(45.0)    -> "$45.00"    (stage 2, fed the OUTPUT of stage 1)
webAdapter returns "$45.00" as the (simulated) HTTP response body
```

## 7. Gotchas & takeaways

> **Gotcha:** keeping a function bean genuinely transport-agnostic means resisting the temptation to reach into framework-specific request/response types (a `ServerHttpRequest`, a `Message<T>` with broker-specific headers) from inside the function body — doing so silently re-couples the function to one adapter, defeating the entire "write once, deploy anywhere" premise, even though the code will still compile and run under whichever single adapter it was written against.

- `Supplier<T>` (no input, produces values — a data source), `Function<T,R>` (transforms input to output), and `Consumer<T>` (accepts input, no output — a sink) are the three shapes Spring Cloud Function builds its entire adapter model around; nearly any business operation fits one of the three.
- The same function bean, unmodified, can be exposed over HTTP, a message broker, or a serverless platform purely by which adapter dependency is on the classpath and which configuration selects it — a later card covers exactly this deployment-target switch.
- Because these are plain `java.util.function` types, they compose using the standard library's own `andThen`/`compose` methods, with no framework-specific composition API needed — a following card covers function composition and routing in more depth.
- Testing a function bean requires no Spring context, no mock web layer, and no embedded broker — a plain unit test calling `.apply` directly is sufficient, which is a significant testability advantage over transport-coupled code.
