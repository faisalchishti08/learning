---
card: spring-integration
gi: 54
slug: http-support-inbound-outbound
title: "HTTP support (inbound/outbound)"
---

## 1. What it is

Spring Integration's HTTP support provides `Http.inboundGateway(...)` (exposing a flow as an HTTP endpoint that receives requests and returns responses — a concrete inbound gateway, card 0034) and `Http.outboundGateway(...)` (having a flow call out to another HTTP endpoint and wait for its response — a concrete outbound gateway). There's also `Http.inboundChannelAdapter(...)`/`Http.outboundChannelAdapter(...)` for one-way variants (a plain inbound/outbound adapter, card 0033) when no reply is needed. Together, they're the concrete HTTP realization of the general gateway and adapter concepts covered earlier in this section.

## 2. Why & when

You reach for HTTP support specifically when a flow's external boundary is HTTP — by far the most common integration protocol for modern web-facing and service-to-service communication:

- **You want a message flow directly exposed as a REST-style HTTP endpoint** — `Http.inboundGateway` lets an external HTTP client's request enter the flow, be processed, and receive an HTTP response, all through Spring Integration's messaging machinery rather than a traditional `@RestController` — useful when the endpoint's actual logic is more naturally expressed as a flow (filters, transformers, routers) than a single controller method.
- **A flow needs to call another HTTP service and use its response** — `Http.outboundGateway` performs that call and blocks for the response, exactly the outbound gateway pattern from card 0034, specialized for HTTP's request/response semantics (status codes, headers, body).
- **A one-way HTTP interaction is all that's needed** — a webhook receiver that only needs to accept incoming POST requests with no meaningful response body, or an outbound "fire an HTTP notification" with no response the flow cares about — the channel-adapter variants handle these simpler, one-way cases.

## 3. Core concept

Think of `Http.inboundGateway` like a receptionist who accepts a visitor's request form (an HTTP request), routes it through the internal department that actually handles it (the flow), and hands back whatever response that department produces (an HTTP response) to the visitor before they leave. `Http.outboundGateway` is the mirror: it's your own organization filling out a request form and sending it to *another* company's receptionist, then waiting at the door for that company's response before continuing your own work.

```java
@Bean
public IntegrationFlow httpInboundFlow() {
    return IntegrationFlow.from(Http.inboundGateway("/orders")
            .requestMapping(m -> m.methods(HttpMethod.POST))
            .requestPayloadType(Order.class))
        .handle((Order order, headers) -> orderService.process(order)) // return value becomes the HTTP response body
        .get();
}

@Bean
public IntegrationFlow httpOutboundFlow() {
    return IntegrationFlow.from("chargeRequests")
        .handle(Http.outboundGateway("https://payments.example.com/charge")
            .httpMethod(HttpMethod.POST)
            .expectedResponseType(ChargeResult.class))
        .channel("chargeResults")
        .get();
}
```

Both are directly using the request/reply mechanics from card 0034's general gateway coverage, with HTTP-specific concerns (method, headers, status codes, request/response body serialization) layered on top.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTTP inbound gateway: an external client's HTTP request enters the flow and the flow's result becomes the HTTP response. HTTP outbound gateway: the flow issues an HTTP request to another service and waits for its response.">
  <text x="150" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Http.inboundGateway</text>
  <rect x="20" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">HTTP client</text>
  <line x1="130" y1="47" x2="190" y2="47" stroke="#6db33f" stroke-width="2" marker-end="url(#ht1)"/>
  <line x1="190" y1="65" x2="130" y2="65" stroke="#79c0ff" stroke-width="2" marker-end="url(#ht2)"/>
  <rect x="200" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="255" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">flow</text>

  <text x="490" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Http.outboundGateway</text>
  <rect x="360" y="135" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="415" y="159" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">flow</text>
  <line x1="470" y1="147" x2="530" y2="147" stroke="#6db33f" stroke-width="2" marker-end="url(#ht1)"/>
  <line x1="530" y1="165" x2="470" y2="165" stroke="#79c0ff" stroke-width="2" marker-end="url(#ht2)"/>
  <rect x="540" y="135" width="90" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="585" y="159" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">API</text>

  <defs>
    <marker id="ht1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ht2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Both directions preserve the full HTTP request/response round trip; who initiates (external client vs. the flow itself) distinguishes inbound from outbound, exactly as in card 0034's general gateway coverage.

## 5. Runnable example

The scenario: an order-submission HTTP endpoint, using the JDK's built-in `HttpServer`/`HttpClient` (genuinely runnable locally, no external dependencies), starting with a basic inbound-style endpoint, then an outbound-style call to another service, and finally both composed so an inbound request triggers an outbound call before replying.

### Level 1 — Basic

```java
// BasicHttpInboundDemo.java
import com.sun.net.httpserver.*;
import java.net.*;
import java.net.http.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class BasicHttpInboundDemo {
    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        int port = server.getAddress().getPort();

        // what Http.inboundGateway("/orders") does for you: receive request, run the flow, produce the response
        server.createContext("/orders", exchange -> {
            String requestBody = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            System.out.println("[inbound gateway] received request body: " + requestBody);

            String responseBody = "{\"status\":\"CONFIRMED\",\"order\":" + requestBody + "}"; // "the flow's result"
            exchange.sendResponseHeaders(201, responseBody.length());
            try (OutputStream os = exchange.getResponseBody()) { os.write(responseBody.getBytes(StandardCharsets.UTF_8)); }
        });
        server.start();

        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("http://localhost:" + port + "/orders"))
            .POST(HttpRequest.BodyPublishers.ofString("{\"id\":\"ORD-1\",\"amount\":199.99}"))
            .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("[client] status=" + response.statusCode() + ", body=" + response.body());
        server.stop(0);
    }
}
```

How to run: `java BasicHttpInboundDemo.java`. Expected output: `[inbound gateway] received request body: {"id":"ORD-1","amount":199.99}` then `[client] status=201, body={"status":"CONFIRMED","order":{"id":"ORD-1","amount":199.99}}` — a real HTTP POST request was received, "processed" (here, simply wrapped), and its result became the actual HTTP response body and status code, exactly what `Http.inboundGateway`'s flow-to-response translation does.

### Level 2 — Intermediate

An outbound-style call, where "the flow" itself acts as an HTTP client calling another service and waiting for its response — mirroring `Http.outboundGateway`'s request/reply behavior from the calling side.

```java
// BasicHttpOutboundDemo.java
import com.sun.net.httpserver.*;
import java.net.*;
import java.net.http.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class BasicHttpOutboundDemo {
    public static void main(String[] args) throws Exception {
        // stands in for an EXTERNAL payment service
        HttpServer paymentService = HttpServer.create(new InetSocketAddress(0), 0);
        int port = paymentService.getAddress().getPort();
        paymentService.createContext("/charge", exchange -> {
            String body = "{\"approved\":true,\"transactionId\":\"TXN-99\"}";
            exchange.sendResponseHeaders(200, body.length());
            try (OutputStream os = exchange.getResponseBody()) { os.write(body.getBytes(StandardCharsets.UTF_8)); }
        });
        paymentService.start();

        // what Http.outboundGateway(...) does for you: the FLOW calling OUT, waiting for the response
        HttpClient outboundGatewayClient = HttpClient.newHttpClient();
        HttpRequest chargeRequest = HttpRequest.newBuilder()
            .uri(URI.create("http://localhost:" + port + "/charge"))
            .POST(HttpRequest.BodyPublishers.ofString("{\"orderId\":\"ORD-1\",\"amount\":199.99}"))
            .build();

        System.out.println("[outbound gateway] calling external payment service...");
        HttpResponse<String> chargeResponse = outboundGatewayClient.send(chargeRequest, HttpResponse.BodyHandlers.ofString());
        System.out.println("[outbound gateway] received response: " + chargeResponse.body());

        paymentService.stop(0);
    }
}
```

How to run: `java BasicHttpOutboundDemo.java`. Expected output: `[outbound gateway] calling external payment service...` then `[outbound gateway] received response: {"approved":true,"transactionId":"TXN-99"}` — the flow's own code initiated an HTTP call and blocked for the response, exactly `Http.outboundGateway`'s role, using the same request/reply mechanics as the generic outbound gateway from card 0034, specialized for HTTP.

### Level 3 — Advanced

Composing both: an inbound HTTP request triggers the flow to make its own outbound HTTP call to a payment service, and the inbound response is only sent back to the original client once that internal outbound call completes — directly mirroring card 0034's composed inbound/outbound gateway example, here using real HTTP end to end.

```java
// ComposedHttpGatewaysDemo.java
import com.sun.net.httpserver.*;
import java.net.*;
import java.net.http.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class ComposedHttpGatewaysDemo {
    public static void main(String[] args) throws Exception {
        HttpServer paymentService = HttpServer.create(new InetSocketAddress(0), 0);
        int paymentPort = paymentService.getAddress().getPort();
        paymentService.createContext("/charge", exchange -> {
            String body = "{\"approved\":true}";
            exchange.sendResponseHeaders(200, body.length());
            try (OutputStream os = exchange.getResponseBody()) { os.write(body.getBytes(StandardCharsets.UTF_8)); }
        });
        paymentService.start();

        HttpServer orderService = HttpServer.create(new InetSocketAddress(0), 0);
        int orderPort = orderService.getAddress().getPort();
        HttpClient internalClient = HttpClient.newHttpClient();

        // this IS the flow: an inbound gateway whose handling makes an OUTBOUND gateway call before replying
        orderService.createContext("/orders", exchange -> {
            System.out.println("[inbound] order request received — calling payment service before replying");

            HttpRequest chargeRequest = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:" + paymentPort + "/charge"))
                .POST(HttpRequest.BodyPublishers.ofString("{}"))
                .build();
            HttpResponse<String> chargeResponse = internalClient.send(chargeRequest, HttpResponse.BodyHandlers.ofString());
            System.out.println("[inbound] payment service responded: " + chargeResponse.body());

            String finalResponse = "{\"status\":\"CONFIRMED\",\"paymentResult\":" + chargeResponse.body() + "}";
            exchange.sendResponseHeaders(201, finalResponse.length());
            try (OutputStream os = exchange.getResponseBody()) { os.write(finalResponse.getBytes(StandardCharsets.UTF_8)); }
        });
        orderService.start();

        HttpClient externalClient = HttpClient.newHttpClient();
        HttpRequest orderRequest = HttpRequest.newBuilder()
            .uri(URI.create("http://localhost:" + orderPort + "/orders"))
            .POST(HttpRequest.BodyPublishers.ofString("{\"id\":\"ORD-1\"}"))
            .build();
        HttpResponse<String> orderResponse = externalClient.send(orderRequest, HttpResponse.BodyHandlers.ofString());

        System.out.println("[external caller] final response: " + orderResponse.body());
        paymentService.stop(0);
        orderService.stop(0);
    }
}
```

How to run: `java ComposedHttpGatewaysDemo.java`. Expected output: `[inbound] order request received — calling payment service before replying`, `[inbound] payment service responded: {"approved":true}`, then `[external caller] final response: {"status":"CONFIRMED","paymentResult":{"approved":true}}` — the external caller's HTTP request wasn't answered until the flow's own nested outbound HTTP call to the payment service had fully completed, exactly the chained-gateway behavior detailed generically in card 0034, here demonstrated with two real, independent local HTTP servers.

## 6. Walkthrough

Tracing `ComposedHttpGatewaysDemo` in execution order:

1. The `externalClient` sends a real HTTP POST to `orderService`'s `/orders` endpoint and blocks (via `client.send(...)`, a synchronous call) waiting for the HTTP response.
2. `orderService`'s handler for `/orders` fires, printing confirmation that the request arrived — this is the inbound gateway role: an external HTTP request has entered "the flow" (here, this handler's own code).
3. Instead of responding immediately, the handler itself becomes an HTTP *client*, building and sending its own separate request to `paymentService`'s `/charge` endpoint via `internalClient.send(...)` — this call also blocks, waiting for `paymentService`'s response, exactly the outbound gateway role.
4. `paymentService`'s handler for `/charge` fires independently, constructing and returning its own response body.
5. The blocked `internalClient.send(...)` call inside `orderService`'s handler unblocks with that response; the handler prints confirmation and incorporates the payment result into its own final response body.
6. Only now does `orderService`'s handler call `exchange.sendResponseHeaders(...)` and write the final response body — which is what finally unblocks the *original* external caller's `client.send(...)` call from step 1, delivering the combined result all the way back to where the whole chain started.

```
externalClient: POST /orders [BLOCKS waiting for orderService's response]
  orderService handler: request received
  orderService handler: POST /charge to paymentService [BLOCKS waiting for paymentService's response]
    paymentService handler: processes, responds {"approved":true}
  orderService handler: unblocks, builds combined response, sends it
externalClient: unblocks with the FINAL combined response
```

## 7. Gotchas & takeaways

> Just as with chained gateways generally (card 0034), an inbound HTTP endpoint whose handling makes its own outbound HTTP call inherits that call's full latency and failure modes — a slow or down payment service directly makes the original external caller's request slow or fail too. Always configure explicit timeouts on outbound HTTP calls made from within an inbound gateway's handling, and decide deliberately how a failed internal call should affect the response sent back to the original external caller (a specific error status, a fallback response, or a genuine failure) rather than letting an unhandled exception produce an unclear 500 error.

- `Http.inboundGateway` exposes a flow as an HTTP endpoint, translating an incoming request into the flow and the flow's result back into an HTTP response — the concrete HTTP realization of the general inbound gateway pattern (card 0034).
- `Http.outboundGateway` has the flow itself act as an HTTP client, calling another service and waiting for its response — the concrete HTTP realization of the general outbound gateway pattern.
- Channel-adapter variants (`Http.inboundChannelAdapter`/`Http.outboundChannelAdapter`) handle one-way HTTP interactions where no meaningful reply is needed, mirroring the plain adapter pattern from card 0033.
- HTTP gateways can be composed: an inbound request's handling can trigger its own outbound HTTP calls before producing a final response, exactly like the chained-gateway pattern from card 0034, just specialized for HTTP request/response semantics.
- Always set explicit timeouts and deliberate failure-handling for any outbound HTTP call made as part of an inbound gateway's response path, since its latency and failures directly propagate to whoever is waiting on the original external request.
