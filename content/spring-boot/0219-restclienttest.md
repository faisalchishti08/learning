---
card: spring-boot
gi: 219
slug: restclienttest
title: "@RestClientTest"
---

## 1. What it is

`@RestClientTest` is a Spring Boot test slice for testing **HTTP client code** — classes that use `RestTemplate`, `RestClient`, or a custom `HttpInterface` client. It auto-configures a `MockRestServiceServer` (for `RestTemplate` / `RestClient`) that intercepts HTTP calls and returns stubbed responses. No real network requests are made. It loads only the client configuration and Jackson — no web layer, no JPA.

## 2. Why & when

Use `@RestClientTest` when you have a service that calls an external REST API and you want to verify:
- The correct URL, method, and request body are sent.
- The response is correctly deserialized into your domain objects.
- Error responses (4xx, 5xx) are handled correctly (e.g., retries, fallback).
- Custom HTTP headers (auth tokens, correlation IDs) are included.

Without `@RestClientTest`, you'd need to either start a real HTTP server (slow) or mock the `RestTemplate` at the object level (brittle). `MockRestServiceServer` gives you a clean contract: "expect this request, respond with this body."

## 3. Core concept

```java
@RestClientTest(PaymentClient.class)
class PaymentClientTest {

    @Autowired PaymentClient paymentClient;
    @Autowired MockRestServiceServer server;

    @Test
    void chargeCard_successResponse() throws Exception {
        server.expect(requestTo("/payments/charge"))
              .andExpect(method(HttpMethod.POST))
              .andRespond(withSuccess(
                  "{\"txId\":\"TX-1\",\"status\":\"APPROVED\"}",
                  MediaType.APPLICATION_JSON));

        PaymentResponse resp = paymentClient.charge("4111111111111111", 99.99);

        assertThat(resp.txId()).isEqualTo("TX-1");
        assertThat(resp.status()).isEqualTo("APPROVED");
        server.verify(); // all expected requests were made
    }

    @Test
    void chargeCard_serverError_throws() {
        server.expect(requestTo("/payments/charge"))
              .andRespond(withServerError()); // 500

        assertThatThrownBy(() -> paymentClient.charge("...", 50.0))
            .isInstanceOf(HttpServerErrorException.class);
    }
}
```

`server.verify()` fails if any expected request was not made — validates that your client actually sent the request.

## 4. Diagram

<svg viewBox="0 0 680 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@RestClientTest: test sets expectations on MockRestServiceServer; PaymentClient sends request to MockRestServiceServer which returns stubbed response; no real network call; server.verify() confirms all expectations were met">
  <!-- Test -->
  <rect x="10" y="45" width="145" height="100" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="82" y="67" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Test Class</text>
  <text x="82" y="84" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">server.expect(</text>
  <text x="82" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">  requestTo("/payments/"))</text>
  <text x="82" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.andRespond(withSuccess(</text>
  <text x="82" y="123" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">  json, APPLICATION_JSON))</text>
  <text x="82" y="138" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">server.verify()</text>

  <!-- MockRestServiceServer -->
  <rect x="205" y="55" width="185" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="297" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">MockRestServiceServer</text>
  <text x="297" y="96" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">intercepts RestTemplate calls</text>
  <text x="297" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">matches request vs expectation</text>
  <text x="297" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">returns stubbed response body</text>

  <!-- PaymentClient -->
  <rect x="440" y="55" width="140" height="80" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="510" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">PaymentClient</text>
  <text x="510" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">RestTemplate.postForObject(</text>
  <text x="510" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">  "/payments/charge", ...)</text>
  <text x="510" y="122" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">real code, fake server</text>

  <!-- Arrows -->
  <line x1="157" y1="95" x2="203" y2="95" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#rca)"/>
  <text x="179" y="88" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">expectations</text>

  <line x1="583" y1="95" x2="393" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#rcb)"/>
  <text x="490" y="88" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">HTTP request (intercepted)</text>

  <line x1="393" y1="110" x2="583" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rca)"/>
  <text x="490" y="125" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">stubbed response</text>

  <text x="340" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">No real network — requests intercepted in-process by MockRestServiceServer</text>

  <defs>
    <marker id="rca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rcb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`PaymentClient` calls its real `RestTemplate`; `MockRestServiceServer` intercepts the call and returns a stubbed JSON response — no real HTTP.

## 5. Runnable example

```java
// RestClientTestDemo.java — simulates @RestClientTest and MockRestServiceServer patterns
// How to run: java RestClientTestDemo.java  (JDK 17+, no dependencies)
// Real use: @RestClientTest(PaymentClient.class) + @Autowired MockRestServiceServer

import java.util.*;

public class RestClientTestDemo {

    // Domain types
    record PaymentRequest(String cardNumber, double amount) {}
    record PaymentResponse(String txId, String status, String errorMessage) {
        static PaymentResponse success(String txId) { return new PaymentResponse(txId, "APPROVED", null); }
        static PaymentResponse error(String msg)    { return new PaymentResponse(null, "FAILED", msg); }
    }

    // Simulates MockRestServiceServer: register expectations, intercept calls
    static class MockRestServiceServer {
        record Expectation(String method, String url, String responseBody, int responseStatus) {}

        private final Queue<Expectation> expectations = new LinkedList<>();
        private final List<String>       actualCalls  = new ArrayList<>();

        MockRestServiceServer expect(String method, String url, String body, int status) {
            expectations.offer(new Expectation(method, url, body, status));
            return this;
        }

        // Simulate RestTemplate call interception
        PaymentResponse dispatch(String method, String url, Object requestBody) {
            actualCalls.add(method + " " + url);
            System.out.println("  [intercept] " + method + " " + url);

            if (expectations.isEmpty())
                throw new RuntimeException("Unexpected call: " + method + " " + url);

            Expectation exp = expectations.poll();
            if (!exp.url().equals(url) || !exp.method().equals(method))
                throw new AssertionError("Expected " + exp.method() + " " + exp.url()
                        + " but got " + method + " " + url);

            System.out.println("  [stub]      " + exp.responseStatus() + " body=" + exp.responseBody());
            if (exp.responseStatus() >= 500)
                throw new RuntimeException("500 Internal Server Error");
            if (exp.responseStatus() >= 400)
                throw new RuntimeException("400 Client Error");

            // Deserialize simulated JSON
            if (exp.responseBody().contains("APPROVED"))
                return PaymentResponse.success(exp.responseBody().replaceAll(".*\"txId\":\"([^\"]+)\".*", "$1"));
            return PaymentResponse.error("Payment declined");
        }

        void verify() {
            if (!expectations.isEmpty())
                throw new AssertionError("Not all expectations were met: " + expectations.size() + " remaining");
            System.out.println("  ✓ server.verify() — all expectations met");
        }

        void reset() { expectations.clear(); actualCalls.clear(); }
    }

    // The class under test
    static class PaymentClient {
        private final MockRestServiceServer server;
        private final String baseUrl = "https://api.payments.example.com";

        PaymentClient(MockRestServiceServer server) { this.server = server; }

        PaymentResponse charge(String cardNumber, double amount) {
            return server.dispatch("POST", baseUrl + "/payments/charge",
                    new PaymentRequest(cardNumber, amount));
        }

        PaymentResponse refund(String txId) {
            return server.dispatch("POST", baseUrl + "/payments/refund/" + txId, null);
        }
    }

    static void expect(boolean c, String m) {
        if (!c) throw new AssertionError("FAIL: " + m);
        System.out.println("  ✓ " + m);
    }

    public static void main(String[] args) {
        System.out.println("=== @RestClientTest / MockRestServiceServer Demo ===\n");

        MockRestServiceServer server = new MockRestServiceServer();
        PaymentClient client = new PaymentClient(server);

        // Test 1: successful charge
        System.out.println("--- Test 1: charge — 200 APPROVED ---");
        server.expect("POST", "https://api.payments.example.com/payments/charge",
                "{\"txId\":\"TX-100\",\"status\":\"APPROVED\"}", 200);

        PaymentResponse resp = client.charge("4111111111111111", 99.99);
        expect("APPROVED".equals(resp.status()), "status is APPROVED");
        expect("TX-100".equals(resp.txId()),     "txId returned");
        server.verify();
        server.reset();

        // Test 2: 500 server error
        System.out.println("\n--- Test 2: charge — 500 server error ---");
        server.expect("POST", "https://api.payments.example.com/payments/charge",
                "{\"error\":\"gateway timeout\"}", 500);

        try {
            client.charge("4111111111111111", 50.0);
            throw new AssertionError("Expected exception");
        } catch (RuntimeException e) {
            expect(e.getMessage().contains("500"), "500 error thrown");
        }
        server.verify();
        server.reset();

        // Test 3: refund
        System.out.println("\n--- Test 3: refund TX-100 ---");
        server.expect("POST", "https://api.payments.example.com/payments/refund/TX-100",
                "{\"txId\":\"TX-100\",\"status\":\"APPROVED\"}", 200);

        PaymentResponse refund = client.refund("TX-100");
        expect("APPROVED".equals(refund.status()), "refund approved");
        server.verify();

        System.out.println("\n--- Real @RestClientTest ---");
        System.out.println("""
@RestClientTest(PaymentClient.class)
class PaymentClientTest {
    @Autowired PaymentClient client;
    @Autowired MockRestServiceServer server;

    @Test void charge_success() {
        server.expect(requestTo("/payments/charge"))
              .andExpect(method(POST))
              .andExpect(jsonPath("$.amount").value(99.99))
              .andRespond(withSuccess(
                  "{\\"txId\\":\\"TX-1\\",\\"status\\":\\"APPROVED\\"}",
                  APPLICATION_JSON));

        var resp = client.charge("4111111111111111", 99.99);
        assertThat(resp.txId()).isEqualTo("TX-1");
        server.verify();
    }

    @Test void charge_500_throws() {
        server.expect(requestTo("/payments/charge"))
              .andRespond(withServerError());
        assertThatThrownBy(() -> client.charge("...", 1.0))
              .isInstanceOf(HttpServerErrorException.class);
    }
}""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java RestClientTestDemo.java`

## 6. Walkthrough

- **Test 1 (success)**: `server.expect(...)` registers what URL/method the client should call and what response to return. `client.charge(...)` calls the real `PaymentClient` code which internally calls `RestTemplate.postForObject`. The server intercepts it and returns the stubbed JSON. `server.verify()` confirms the call was actually made.
- **Test 2 (500 error)**: stub returns a `500` status. The `PaymentClient` should throw an exception (in real Spring: `HttpServerErrorException`). The test asserts that the exception is thrown — critical for testing error-handling code paths.
- **Test 3 (refund)**: tests a different endpoint with a URL path parameter. `server.expect(requestTo(containsString("TX-100")))` would be the real matcher — here simplified to exact URL.
- **`server.verify()`**: the most important call — if you remove `verify()`, you might not catch the case where the client never made the HTTP call at all (e.g., due to a logic bug that short-circuits before calling the API).

## 7. Gotchas & takeaways

> `server.verify()` must be called at the end of every test that registers expectations. Without it, you won't detect the case where the client skips the HTTP call entirely. Always pair `server.expect(...)` with `server.verify()`.

> `@RestClientTest` works with `RestTemplate` and (Spring Boot 3.2+) `RestClient`. For `WebClient` (reactive), use `@WebClientTest` or configure a `MockWebServer` (OkHttp) manually — `MockRestServiceServer` does not intercept `WebClient` calls.

- `@RestClientTest(MyClient.class)` loads only `MyClient` and its dependencies. If `MyClient` depends on a `@Service` bean, add it via `@MockitoBean`.
- Request matchers: `requestTo()`, `method()`, `header()`, `jsonPath()`, `content()` — all from `MockRestRequestMatchers`.
- Response builders: `withSuccess()`, `withNoContent()`, `withStatus()`, `withServerError()`, `withUnauthorizedRequest()` — from `MockRestResponseCreators`.
- `server.reset()` clears expectations between logical tests (or just let Spring reset it between `@Test` methods automatically).
