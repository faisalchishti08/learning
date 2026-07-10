---
card: spring-framework
gi: 437
slug: testing-client-side-rest-mockrestserviceserver
title: "Testing client-side REST (MockRestServiceServer)"
---

## 1. What it is

`MockRestServiceServer` is the mirror image of `MockMvc`: instead of testing a server's controllers by mocking the HTTP transport, it tests a `RestTemplate`/`RestClient`-based *client* by intercepting the outbound calls it makes, letting you assert exactly what request was sent and script exactly what response comes back — without any real HTTP call ever leaving the JVM.

```java
RestTemplate restTemplate = new RestTemplate();
MockRestServiceServer server = MockRestServiceServer.createServer(restTemplate);

server.expect(requestTo("/products/42"))
        .andExpect(method(HttpMethod.GET))
        .andRespond(withSuccess("{\"id\":42,\"name\":\"Laptop\"}", MediaType.APPLICATION_JSON));

Product product = restTemplate.getForObject("/products/{id}", Product.class, 42);
```

## 2. Why & when

Code that calls an external HTTP API (a `RestTemplate`/`RestClient` client, potentially wrapped in a service class) is hard to test realistically without either hitting the real external service (slow, unreliable, possibly costly, and dependent on network availability) or replacing the entire client with a hand-written mock (which doesn't verify the *actual* HTTP request your code constructs — the right URL, method, headers, body). `MockRestServiceServer` solves this by intercepting at the `ClientHttpRequestFactory` level — your real `RestTemplate`/`RestClient` code runs completely unchanged, actually building and "sending" a real `ClientHttpRequest`, but the mock server both asserts on that request's exact shape and supplies a scripted response, all in-memory.

Reach for `MockRestServiceServer` when:

- Testing a client class that calls an external HTTP API, verifying it constructs the correct request (URL, method, headers, body) without needing the real external service running.
- Verifying your code's response-handling logic (deserialization, error handling for specific status codes) against precisely controlled, scripted responses — including ones simulating errors that would be hard to reliably reproduce against a real service.
- Testing retry or error-recovery logic by scripting a sequence of responses (a failure followed by a success) and confirming your code handles that sequence correctly.

## 3. Core concept

```
 RestTemplate restTemplate = new RestTemplate();
 MockRestServiceServer server = MockRestServiceServer.createServer(restTemplate);
        |
        | REPLACES restTemplate's ClientHttpRequestFactory internally
        v
 server.expect(requestTo(url)).andExpect(method(GET)).andRespond(withSuccess(body, contentType))
        |
        v
 restTemplate.getForObject(url, Type.class)   <- real RestTemplate code, unchanged
        |
        v
 intercepted by the mock factory -- checks the request against
 the expectation, then returns the scripted response instead of
 making a real network call
        |
        v
 server.verify()  -- confirms every expected request actually happened
```

Your client code never knows it isn't talking to a real server — exactly the same design philosophy `MockMvc` applies on the server side, just pointed at the opposite direction of an HTTP exchange.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client code calls RestTemplate, which is intercepted by MockRestServiceServer instead of reaching a real network">
  <rect x="10" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ProductClient</text>

  <rect x="240" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RestTemplate</text>
  <text x="315" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(real code, unchanged)</text>

  <rect x="470" y="70" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MockRestServiceServer</text>
  <text x="550" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">asserts + scripts response</text>

  <line x1="160" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="390" y1="95" x2="465" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

No real network call ever leaves the JVM; the mock intercepts at the request-factory level.

## 5. Runnable example

### Level 1 — Basic

Script a single successful response and verify the exact request URL and method a client method constructs.

```java
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

public class MockRestServiceServerBasic {

    record Product(long id, String name) {}

    static class ProductClient {
        private final RestTemplate restTemplate;
        ProductClient(RestTemplate restTemplate) { this.restTemplate = restTemplate; }
        Product getProduct(long id) {
            return restTemplate.getForObject("https://api.example.com/products/{id}", Product.class, id);
        }
    }

    public static void main(String[] args) {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.createServer(restTemplate);

        server.expect(requestTo("https://api.example.com/products/42"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess("{\"id\":42,\"name\":\"Laptop\"}", MediaType.APPLICATION_JSON));

        ProductClient client = new ProductClient(restTemplate);
        Product product = client.getProduct(42);

        System.out.println("Received: " + product);
        if (!product.name().equals("Laptop")) throw new AssertionError("Unexpected product name");

        server.verify(); // confirms the expected request genuinely happened
        System.out.println("Client request and scripted response verified -- PASS");
    }
}
```

How to run: add `spring-test`, `spring-web`, and Jackson to the classpath, then `java MockRestServiceServerBasic.java`.

`MockRestServiceServer.createServer(restTemplate)` replaces this `RestTemplate` instance's underlying request factory with a mock one — `client.getProduct(42)` runs completely real `RestTemplate` code (URL templating, JSON deserialization) against that mock, never touching a real network. `server.verify()` at the end confirms every `expect(...)` declaration was actually satisfied by a real request during the test — if `client.getProduct` had never been called, or called with a different URL, `verify()` would fail loudly.

### Level 2 — Intermediate

Verify a `POST` request's body content, and script an error response to test the client's error-handling behavior.

```java
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;

public class MockRestServiceServerIntermediate {

    record NewOrder(String sku, int quantity) {}
    record Order(long id, String status) {}

    static class OrderClient {
        private final RestTemplate restTemplate;
        OrderClient(RestTemplate restTemplate) { this.restTemplate = restTemplate; }

        Order createOrder(NewOrder newOrder) {
            return restTemplate.postForObject("https://api.example.com/orders", newOrder, Order.class);
        }

        String describeOrderOrError(long id) {
            try {
                Order order = restTemplate.getForObject("https://api.example.com/orders/{id}", Order.class, id);
                return "Found: " + order.status();
            } catch (HttpClientErrorException.NotFound e) {
                return "Order not found";
            }
        }
    }

    public static void main(String[] args) {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.createServer(restTemplate);

        server.expect(requestTo("https://api.example.com/orders"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(jsonPath("$.sku").value("SKU-1"))
                .andExpect(jsonPath("$.quantity").value(3))
                .andRespond(withSuccess("{\"id\":100,\"status\":\"CREATED\"}", MediaType.APPLICATION_JSON));

        OrderClient client = new OrderClient(restTemplate);
        Order created = client.createOrder(new NewOrder("SKU-1", 3));
        System.out.println("Created: " + created);
        if (created.id() != 100) throw new AssertionError("Expected id 100");

        server.expect(requestTo("https://api.example.com/orders/999"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withStatus(HttpStatus.NOT_FOUND));

        String result = client.describeOrderOrError(999);
        System.out.println("Result for missing order: " + result);
        if (!result.equals("Order not found")) throw new AssertionError("Expected the 404 to be handled gracefully");

        server.verify();
        System.out.println("POST body verification and error-handling test -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java MockRestServiceServerIntermediate.java`.

`jsonPath("$.sku").value("SKU-1")` verifies the *actual serialized request body* `RestTemplate` constructed from the `NewOrder` record — confirming the client sends the correct payload, not just that some `POST` happened. `withStatus(HttpStatus.NOT_FOUND)` scripts a 404 response with no body, letting the test verify `describeOrderOrError`'s `catch (HttpClientErrorException.NotFound e)` block correctly handles that specific status without needing a real backend that actually returns 404 for a nonexistent order.

### Level 3 — Advanced

Script a sequence of responses (a transient failure followed by success) to test retry logic, and use `expect(times(n), ...)` to assert exactly how many times a request should be made — verifying resilience behavior precisely.

```java
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.ExpectedCount;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;

import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;

public class MockRestServiceServerAdvanced {

    record Product(long id, String name) {}

    static class RetryingProductClient {
        private final RestTemplate restTemplate;
        RetryingProductClient(RestTemplate restTemplate) { this.restTemplate = restTemplate; }

        Product getProductWithRetry(long id, int maxAttempts) {
            HttpServerErrorException lastError = null;
            for (int attempt = 1; attempt <= maxAttempts; attempt++) {
                try {
                    return restTemplate.getForObject("https://api.example.com/products/{id}", Product.class, id);
                } catch (HttpServerErrorException e) {
                    lastError = e;
                    System.out.println("Attempt " + attempt + " failed with " + e.getStatusCode());
                }
            }
            throw lastError;
        }
    }

    public static void main(String[] args) {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.createServer(restTemplate);

        // Script: first two calls to this exact URL fail with 503, the third succeeds.
        server.expect(ExpectedCount.times(2), requestTo("https://api.example.com/products/42"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withStatus(HttpStatus.SERVICE_UNAVAILABLE));

        server.expect(ExpectedCount.once(), requestTo("https://api.example.com/products/42"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess("{\"id\":42,\"name\":\"Laptop\"}", MediaType.APPLICATION_JSON));

        RetryingProductClient client = new RetryingProductClient(restTemplate);
        Product product = client.getProductWithRetry(42, 3);

        System.out.println("Final result after retries: " + product);
        if (!product.name().equals("Laptop")) throw new AssertionError("Expected eventual success");

        server.verify(); // confirms ALL THREE expected requests happened, in the scripted sequence
        System.out.println("Retry-until-success behavior verified with a precise request-count script -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java MockRestServiceServerAdvanced.java`.

`server.expect(ExpectedCount.times(2), requestTo(...))` scripts that the *first two* matching requests receive a `503`, and the subsequent `expect(ExpectedCount.once(), ...)` scripts that the *third* matching request receives success — `MockRestServiceServer` consumes expectations in declaration order for requests matching the same criteria, letting you script an exact sequence of different responses to the same URL, precisely modeling a real transient-failure-then-recovery scenario. `server.verify()` at the end confirms all three scripted requests genuinely happened — if the client had given up after only two attempts (a bug in the retry loop), this verification would fail, catching that bug.

## 6. Walkthrough

Trace `MockRestServiceServerAdvanced.main`'s three-attempt sequence:

1. **Expectations registered.** Two `expect(...)` declarations are set up against the mock server: the first says "the next 2 matching requests get a 503," the second says "the request after that gets a success response" — both targeting the same URL, since a real flaky service would use the same endpoint for every retry attempt.
2. **First attempt.** `client.getProductWithRetry(42, 3)`'s loop calls `restTemplate.getForObject(...)` for `attempt = 1`. The mock server matches this against the first (still-unconsumed) expectation, returns `503 Service Unavailable`, and `RestTemplate` translates that into a thrown `HttpServerErrorException`.
3. **Caught and logged.** The `catch` block in `getProductWithRetry` catches the exception, prints `"Attempt 1 failed with 503 SERVICE_UNAVAILABLE"`, and the loop continues.
4. **Second attempt.** Same flow: the mock server's first expectation (`times(2)`) still has one more use remaining, returns another `503`, caught and logged as `"Attempt 2 failed..."`.
5. **Third attempt.** The first expectation is now fully consumed (both of its 2 scripted uses exhausted); the mock server moves to the second, `ExpectedCount.once()` expectation, which returns the success response — `restTemplate.getForObject(...)` this time returns successfully, deserializing to `Product(42, "Laptop")`, and `getProductWithRetry` returns it directly from inside the loop, without reaching the `throw lastError` line.
6. **Verification.** `server.verify()` checks that every registered expectation was satisfied by the actual requests made during the test — since all three scripted requests genuinely occurred (two 503s, one success), verification passes; had the client's retry loop had an off-by-one bug (say, only trying twice), the second expectation would never have been satisfied, and `verify()` would fail with a clear message about the unmet expectation.

```
Expectations: [503, 503, then success] for GET /products/42

attempt 1: GET /products/42 -> 503 -> caught, logged, loop continues
attempt 2: GET /products/42 -> 503 -> caught, logged, loop continues
attempt 3: GET /products/42 -> 200 {id:42, name:Laptop} -> returned directly

server.verify() -- all 3 scripted requests were made -- PASS
```

## 7. Gotchas & takeaways

> Gotcha: `MockRestServiceServer.createServer(restTemplate)` mutates the given `RestTemplate` instance's request factory — reusing the *same* `RestTemplate` instance across multiple independent test methods without resetting the mock server between them can cause expectations from one test to leak into (or fail to be satisfied by) another. Either create a fresh `RestTemplate`/`MockRestServiceServer` pair per test method, or explicitly call `server.reset()` between tests if reuse is intentional.

- `MockRestServiceServer` is the client-side mirror of `MockMvc` — it intercepts outbound `RestTemplate`/`RestClient` calls, letting real client code run unchanged against scripted, in-memory responses instead of a real network call.
- Use request matchers (`requestTo`, `method`, `jsonPath` on the request body) to verify your client code constructs the exact request you expect, not just that some request happened.
- `ExpectedCount.times(n)`/`.once()` let you script a precise sequence of different responses to the same endpoint, essential for testing retry, backoff, or failover logic against a controlled, repeatable scenario.
- Always call `server.verify()` at the end of a test — without it, an expectation that was never satisfied (a request your code should have made but didn't) silently passes rather than failing the test.
