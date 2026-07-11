---
card: spring-cloud
gi: 62
slug: custom-configuration-encoder-decoder-contract
title: "Custom configuration (encoder/decoder/contract)"
---

## 1. What it is

Feign's request/response handling is built from swappable components: an `Encoder` (turns a request body object into bytes to send), a `Decoder` (turns response bytes back into an object), and a `Contract` (interprets which annotations on the client interface mean what — by default, Spring MVC's own annotations, but swappable for Feign's native `@RequestLine`-style annotations or a custom scheme). Each can be overridden per-client via `@FeignClient(configuration = ...)`.

```java
@FeignClient(name = "legacy-billing-service", configuration = LegacyBillingFeignConfig.class)
public interface LegacyBillingClient {
    @GetMapping("/invoices/{id}")
    Invoice getInvoice(@PathVariable String id);
}

@Configuration
class LegacyBillingFeignConfig {
    @Bean
    Decoder feignDecoder() {
        return new XmlDecoder(); // this legacy service returns XML, not JSON -- override just for this client
    }
}
```

## 2. Why & when

Most services in a Spring Cloud system speak JSON and expect Spring MVC-style mapping annotations, so Feign's defaults handle them without any extra configuration. But real systems aren't always uniform — a legacy service might return XML, a third-party API might use a different serialization format or an unconventional annotation style, or a client might need custom error-handling logic (an `ErrorDecoder`) beyond Feign's defaults. Per-client configuration lets these exceptions be handled surgically, without changing Feign's defaults for every other, perfectly ordinary client.

Reach for custom Feign configuration when:

- A specific downstream service returns a non-JSON format (XML, a custom binary format) — a custom `Decoder` (and `Encoder`, for requests) handles that one client's needs without affecting any other.
- Error responses need specific handling beyond Feign's default exception-throwing behavior — a custom `ErrorDecoder` can inspect the response status/body and throw a more specific, meaningful exception type.
- The target API wasn't designed with Spring MVC conventions in mind, and using Feign's *native* contract (`@RequestLine`, `@Param`) fits its shape better than pretending it's a Spring MVC-style API.

## 3. Core concept

```
 Feign client call:
   method call -> Contract interprets annotations -> build request
                -> Encoder serializes the request body (if any)
                -> [ actual HTTP call ]
                -> Decoder deserializes the response body
                -> ErrorDecoder handles non-2xx responses
                -> return value

 each piece is independently swappable per-client via:
   @FeignClient(configuration = SomeConfig.class)
```

Every stage of building and interpreting the HTTP exchange is a pluggable component, not a hardcoded behavior.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Feign call flows through a Contract that interprets annotations, an Encoder that serializes the request, and a Decoder or ErrorDecoder that interprets the response, each independently swappable per client">
  <rect x="20" y="70" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="75" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Contract</text>

  <rect x="165" y="70" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="220" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Encoder</text>

  <rect x="310" y="70" width="110" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="365" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">HTTP call</text>

  <rect x="455" y="40" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="530" y="65" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Decoder (2xx)</text>

  <rect x="455" y="100" width="150" height="40" rx="6" fill="#e6494930" stroke="#e64949" stroke-width="1.2"/>
  <text x="530" y="125" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ErrorDecoder (non-2xx)</text>

  <line x1="130" y1="90" x2="163" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a62)"/>
  <line x1="275" y1="90" x2="308" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a62)"/>
  <line x1="420" y1="80" x2="453" y2="60" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a62)"/>
  <line x1="420" y1="100" x2="453" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a62)"/>

  <defs><marker id="a62" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each stage is independently pluggable — swap the `Decoder` for XML support without touching the `Encoder`, `Contract`, or anything else.

## 5. Runnable example

The scenario: `LegacyBillingClient` talks to a service that returns XML instead of JSON, and needs custom error handling. Start with the default JSON-only decoding (which fails against this service), then add a custom decoder for the actual format, then add a custom error decoder for meaningful failure handling.

### Level 1 — Basic

The default JSON decoder fails against a service returning XML.

```java
public class FeignConfigLevel1 {
    static String jsonDecode(String responseBody) {
        if (!responseBody.trim().startsWith("{")) {
            throw new IllegalStateException("expected JSON, got: " + responseBody);
        }
        return "parsed JSON: " + responseBody;
    }

    public static void main(String[] args) {
        String xmlResponse = "<invoice><id>42</id><amount>199.99</amount></invoice>";
        try {
            System.out.println(jsonDecode(xmlResponse));
        } catch (IllegalStateException e) {
            System.out.println("decode failed: " + e.getMessage());
        }
    }
}
```

How to run: `java FeignConfigLevel1.java`

The default decoder assumes JSON and fails outright against this legacy service's actual XML response — exactly the situation a per-client custom `Decoder` configuration exists to fix.

### Level 2 — Intermediate

Add a custom decoder that correctly handles this client's actual (XML) response format, configured only for this specific client.

```java
import java.util.*;
import java.util.regex.*;

public class FeignConfigLevel2 {
    record Invoice(String id, double amount) {}

    interface Decoder {
        Invoice decode(String responseBody);
    }

    static Decoder jsonDecoder = body -> {
        // a simplified stand-in for real JSON deserialization
        Matcher m = Pattern.compile("\"id\":\"(.*?)\".*\"amount\":([0-9.]+)").matcher(body);
        if (!m.find()) throw new IllegalStateException("not valid JSON for Invoice: " + body);
        return new Invoice(m.group(1), Double.parseDouble(m.group(2)));
    };

    static Decoder xmlDecoder = body -> { // custom decoder, configured only for the legacy client
        Matcher m = Pattern.compile("<id>(.*?)</id>.*<amount>(.*?)</amount>").matcher(body);
        if (!m.find()) throw new IllegalStateException("not valid XML for Invoice: " + body);
        return new Invoice(m.group(1), Double.parseDouble(m.group(2)));
    };

    public static void main(String[] args) {
        String jsonResponse = "{\"id\":\"42\",\"amount\":199.99}";
        String xmlResponse = "<invoice><id>77</id><amount>350.00</amount></invoice>";

        System.out.println("normal client (jsonDecoder): " + jsonDecoder.decode(jsonResponse));
        System.out.println("legacy client (xmlDecoder): " + xmlDecoder.decode(xmlResponse));
    }
}
```

How to run: `java FeignConfigLevel2.java`

`jsonDecoder` and `xmlDecoder` both produce the same `Invoice` type from their respective, differently-formatted responses — this mirrors how `@FeignClient(configuration = LegacyBillingFeignConfig.class)` swaps just the `Decoder` bean for `LegacyBillingClient` while every other client in the same application keeps using Feign's default JSON decoder, completely unaffected.

### Level 3 — Advanced

Add a custom `ErrorDecoder` alongside the custom decoder, turning a generic non-2xx response into a specific, meaningful exception type based on the response status and body.

```java
import java.util.*;
import java.util.regex.*;

public class FeignConfigLevel3 {
    record Invoice(String id, double amount) {}
    record Response(int status, String body) {}

    static class InvoiceNotFoundException extends RuntimeException {
        InvoiceNotFoundException(String id) { super("invoice " + id + " does not exist"); }
    }
    static class LegacyServiceUnavailableException extends RuntimeException {
        LegacyServiceUnavailableException() { super("legacy billing service is temporarily down"); }
    }

    interface Decoder { Invoice decode(String body); }
    interface ErrorDecoder { RuntimeException decode(Response response, String requestedId); }

    static Decoder xmlDecoder = body -> {
        Matcher m = Pattern.compile("<id>(.*?)</id>.*<amount>(.*?)</amount>").matcher(body);
        if (!m.find()) throw new IllegalStateException("not valid XML for Invoice: " + body);
        return new Invoice(m.group(1), Double.parseDouble(m.group(2)));
    };

    static ErrorDecoder legacyErrorDecoder = (response, requestedId) -> switch (response.status()) {
        case 404 -> new InvoiceNotFoundException(requestedId);
        case 503 -> new LegacyServiceUnavailableException();
        default -> new RuntimeException("unexpected legacy service error: " + response.status());
    };

    static Invoice getInvoice(String id, Response response) {
        if (response.status() >= 200 && response.status() < 300) {
            return xmlDecoder.decode(response.body());
        }
        throw legacyErrorDecoder.decode(response, id);
    }

    public static void main(String[] args) {
        Response success = new Response(200, "<invoice><id>77</id><amount>350.00</amount></invoice>");
        System.out.println("success: " + getInvoice("77", success));

        Response notFound = new Response(404, "");
        try { getInvoice("999", notFound); }
        catch (InvoiceNotFoundException e) { System.out.println("caught: " + e.getMessage()); }

        Response down = new Response(503, "");
        try { getInvoice("77", down); }
        catch (LegacyServiceUnavailableException e) { System.out.println("caught: " + e.getMessage()); }
    }
}
```

How to run: `java FeignConfigLevel3.java`

`getInvoice` routes a successful response through `xmlDecoder` as before, but any non-2xx response instead goes through `legacyErrorDecoder`, which maps specific status codes to specific, meaningfully-named exception types — `404` becomes `InvoiceNotFoundException`, `503` becomes `LegacyServiceUnavailableException`. Calling code can now catch these specific exception types and handle each situation appropriately, instead of catching a generic HTTP-error exception and having to inspect a raw status code itself.

## 6. Walkthrough

Trace the three calls in Level 3.

1. `getInvoice("77", success)` runs first — `success.status()` is `200`, within the `[200, 300)` success range, so `xmlDecoder.decode(response.body())` runs, parsing the XML into `Invoice("77", 350.00)`, which is returned and printed directly.
2. `getInvoice("999", notFound)` runs next inside a `try` block — `notFound.status()` is `404`, outside the success range, so `legacyErrorDecoder.decode(response, "999")` runs instead. The `switch` matches `case 404`, constructing and returning a new `InvoiceNotFoundException("999")`. `getInvoice` throws this exception, which the `catch (InvoiceNotFoundException e)` block catches and prints — the caller gets a specific, actionable exception type naming exactly which invoice ID was missing.
3. `getInvoice("77", down)` runs last, also inside a `try` block — `down.status()` is `503`, so `legacyErrorDecoder` matches `case 503` and returns a `LegacyServiceUnavailableException`. This is thrown and caught by its own specific `catch` block, distinct from the `404` case, letting calling code apply different handling — perhaps triggering a circuit breaker or fallback (the earlier Gateway `CircuitBreaker` card's client-side counterpart) specifically for service-unavailable errors, while treating "invoice not found" as a normal, expected business outcome rather than an infrastructure problem.

```
status 200 -> success range -> xmlDecoder.decode(body) -> Invoice returned
status 404 -> error range   -> legacyErrorDecoder -> InvoiceNotFoundException(id)
status 503 -> error range   -> legacyErrorDecoder -> LegacyServiceUnavailableException()
```

## 7. Gotchas & takeaways

> **Gotcha:** custom `Encoder`/`Decoder`/`ErrorDecoder`/`Contract` beans registered inside a `@FeignClient(configuration = ...)` class must **not** themselves be annotated `@Component`/`@Bean`-scanned into the *main* application context — if they are, Spring applies them globally to every Feign client in the application, not just the one they were intended for, since Feign client configuration classes are deliberately excluded from normal component scanning specifically to prevent this kind of accidental global override.

- Encoder, Decoder, Contract, and ErrorDecoder are independently swappable, letting exceptions to the "everything is JSON, everything follows Spring MVC conventions" default be handled per-client without disturbing every other, ordinary client.
- A custom `ErrorDecoder` turns generic HTTP failure status codes into specific, meaningfully-named exception types — a real improvement in how calling code can distinguish and handle different failure modes.
- Reach for Feign's *native* `Contract` (instead of the default Spring MVC-style one) when the target API's shape genuinely doesn't map cleanly onto Spring MVC conventions — it's a different annotation vocabulary (`@RequestLine`, `@Param`) suited to APIs that weren't designed with Spring in mind.
- Keep custom configuration classes scoped specifically to the clients that need them (via `@FeignClient(configuration = ...)`, not global component scanning) — this is the mechanism that keeps one legacy client's XML handling from silently breaking every other, perfectly ordinary JSON client in the same application.
