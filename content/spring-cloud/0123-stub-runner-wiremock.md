---
card: spring-cloud
gi: 123
slug: stub-runner-wiremock
title: "Stub runner & WireMock"
---

## 1. What it is

Stub Runner is Spring Cloud Contract's mechanism for automatically downloading (from a Maven/Gradle artifact repository) and starting up the generated WireMock-backed stubs for a producer's contracts, wiring them into a consumer's own test context at a configured port — so a consumer's integration test can call `http://localhost:{stubRunnerPort}/orders/42` and receive exactly the response the producer's real contract promises, with zero manually-written mock server setup and zero dependency on the producer's actual service being deployed anywhere.

```java
@SpringBootTest
@AutoConfigureStubRunner(ids = "com.example:order-service:+:stubs:8090", stubsMode = StubRunnerProperties.StubsMode.LOCAL)
class PaymentServiceConsumerTest {
    @Test
    void shouldGetOrderDetails() {
        // calls http://localhost:8090/orders/42 -- served by the AUTOMATICALLY started stub, per the contract
    }
}
```

```xml
<!-- the producer's build publishes the generated stubs as a separate, downloadable artifact -->
<classifier>stubs</classifier>
```

## 2. Why & when

A consumer team wanting to test their integration against a producer's API traditionally faces a choice between running the real producer service (heavyweight, requires shared test infrastructure, potentially flaky) or hand-writing a mock (risks drifting out of sync with the producer's real behavior over time, as the earlier contract-testing card established). Stub Runner removes both problems: because the producer's build already publishes their generated, contract-derived WireMock stubs as a downloadable artifact, a consumer's test can declare a dependency on that artifact, and Stub Runner automatically fetches and starts a real WireMock server backed by those exact stubs — giving the consumer a lightweight, in-process, guaranteed-accurate fake of the producer's API, without either side needing to run the other's actual service during testing.

Reach for Stub Runner when:

- Writing a consumer-side integration test against a producer whose contracts are already published (as generated stub artifacts) — Stub Runner's `@AutoConfigureStubRunner` annotation handles the entire fetch-and-start lifecycle automatically within the test's Spring context.
- Local development needs a realistic, contract-accurate fake of a dependency service running without deploying that dependency locally at all — the stub is a full WireMock server, capable of realistic HTTP behavior, not merely a hand-rolled stand-in.
- CI pipelines need consumer-side tests to run reliably and quickly without provisioning the real producer service in the test environment — stubs are lightweight, fast to start, and require no network access beyond fetching the stub artifact itself (or none at all, if run in fully offline/local mode against locally-built stubs).

## 3. Core concept

```
 producer's build:
   generates contract-derived stubs -> publishes them as a Maven/Gradle artifact
     (com.example:order-service:VERSION:stubs)

 consumer's test:
   @AutoConfigureStubRunner(ids = "com.example:order-service:+:stubs:8090")
        |
        v
   Stub Runner fetches the stub artifact (or finds it locally, in LOCAL mode)
        |
        v
   starts a REAL WireMock server on port 8090, pre-loaded with the producer's contract-derived stub mappings
        |
        v
   consumer's test code calls http://localhost:8090/... -- gets EXACTLY the contracted response
```

The consumer never needs the producer's actual application running anywhere — only the small, pre-generated stub artifact, which Stub Runner turns into a live, locally-running fake server for the duration of the test.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A consumer test declares a stub runner dependency which fetches the producers published stub artifact and starts a local WireMock server the consumer test then calls directly with no real producer service involved anywhere">
  <rect x="20" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">consumer test</text>
  <text x="110" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@AutoConfigureStubRunner</text>

  <rect x="250" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="340" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Stub Runner</text>
  <text x="340" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">fetches + starts stub</text>

  <rect x="480" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="550" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">WireMock:8090</text>
  <text x="550" y="56" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">contract-accurate</text>

  <defs><marker id="a123" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="200" y1="43" x2="250" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a123)"/>
  <line x1="430" y1="43" x2="480" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a123)"/>
  <text x="320" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">consumer test calls localhost:8090 directly -- NO real producer service involved</text>
</svg>

Three steps, entirely automatic from the consumer's perspective — one annotation replaces manually standing up and configuring a mock server.

## 5. Runnable example

The scenario: model the Stub Runner lifecycle — fetching a published stub definition and starting an in-process fake server, then a consumer test calling it exactly as it would call the real producer. Start with manually starting a fake server (the pre-Stub-Runner baseline), then automate the fetch-and-start step, then add multiple stub mappings from a richer contract set, mirroring a real producer with several endpoints.

### Level 1 — Basic

A manually, explicitly started fake server — the tedious baseline Stub Runner automates away.

```java
import java.util.*;

public class StubRunnerLevel1 {
    static class FakeServer {
        Map<String, String> mappings = new HashMap<>();
        void stub(String url, String response) { mappings.put(url, response); }
        String call(String url) { return mappings.getOrDefault(url, "404 Not Found"); }
    }

    public static void main(String[] args) {
        // manually configuring the fake -- exactly the boilerplate Stub Runner exists to eliminate
        FakeServer server = new FakeServer();
        server.stub("/orders/42", "{\"id\":42,\"status\":\"CONFIRMED\"}");

        System.out.println("consumer test calls: " + server.call("/orders/42"));
    }
}
```

How to run: `java StubRunnerLevel1.java`

Every stub mapping is manually written by the consumer team, which is precisely the drift risk contract testing exists to eliminate — this hand-written mock has no structural guarantee of staying in sync with the producer's real contract.

### Level 2 — Intermediate

Automate fetching a stub definition (modeling downloading the producer's published stub artifact) and starting a server from it — the consumer no longer writes the mapping by hand.

```java
import java.util.*;

public class StubRunnerLevel2 {
    record StubMapping(String url, int status, String responseBody) {}

    // models fetching the producer's PUBLISHED, contract-derived stub artifact
    static List<StubMapping> fetchStubArtifact(String producerCoordinates) {
        System.out.println("Stub Runner fetching stub artifact: " + producerCoordinates);
        return List.of(new StubMapping("/orders/42", 200, "{\"id\":42,\"status\":\"CONFIRMED\"}"));
    }

    static class FakeServer {
        Map<String, StubMapping> mappings = new HashMap<>();
        void load(List<StubMapping> stubs) { for (StubMapping s : stubs) mappings.put(s.url(), s); }
        String call(String url) {
            StubMapping m = mappings.get(url);
            return m == null ? "404 Not Found" : m.status() + " " + m.responseBody();
        }
    }

    public static void main(String[] args) {
        List<StubMapping> stubs = fetchStubArtifact("com.example:order-service:+:stubs:8090");

        FakeServer server = new FakeServer();
        server.load(stubs); // automatically populated FROM the fetched artifact, not hand-written

        System.out.println("consumer test calls: " + server.call("/orders/42"));
    }
}
```

How to run: `java StubRunnerLevel2.java`

`server.load(stubs)` populates the fake server entirely from `fetchStubArtifact`'s output — no line of consumer code specifies what `/orders/42` should return; that mapping came directly from the (simulated) producer-published artifact, exactly mirroring how Stub Runner's `@AutoConfigureStubRunner` populates a real WireMock server from a downloaded stub artifact with zero manual mapping code from the consumer.

### Level 3 — Advanced

Add multiple stub mappings from a richer contract set (several endpoints, including one requiring a specific request body to match), mirroring a producer with more than one contract published.

```java
import java.util.*;

public class StubRunnerLevel3 {
    record StubMapping(String method, String url, String requiredBodyContains, int status, String responseBody) {}

    static List<StubMapping> fetchStubArtifact(String producerCoordinates) {
        System.out.println("Stub Runner fetching stub artifact: " + producerCoordinates);
        return List.of(
                new StubMapping("GET", "/orders/42", null, 200, "{\"id\":42,\"status\":\"CONFIRMED\"}"),
                new StubMapping("GET", "/orders/999", null, 404, "{\"error\":\"not found\"}"),
                new StubMapping("POST", "/orders", "customerEmail", 201, "{\"id\":43,\"status\":\"PENDING\"}")
        );
    }

    static class FakeServer {
        List<StubMapping> mappings = new ArrayList<>();
        void load(List<StubMapping> stubs) { mappings.addAll(stubs); }

        String call(String method, String url, String requestBody) {
            for (StubMapping m : mappings) {
                boolean methodMatches = m.method().equals(method);
                boolean urlMatches = m.url().equals(url);
                boolean bodyMatches = m.requiredBodyContains() == null
                        || (requestBody != null && requestBody.contains(m.requiredBodyContains()));
                if (methodMatches && urlMatches && bodyMatches) {
                    return m.status() + " " + m.responseBody();
                }
            }
            return "404 Not Found (no matching stub)";
        }
    }

    public static void main(String[] args) {
        FakeServer server = new FakeServer();
        server.load(fetchStubArtifact("com.example:order-service:+:stubs:8090"));

        System.out.println("GET /orders/42: " + server.call("GET", "/orders/42", null));
        System.out.println("GET /orders/999: " + server.call("GET", "/orders/999", null));
        System.out.println("POST /orders (valid body): " + server.call("POST", "/orders", "{\"customerEmail\":\"a@b.com\"}"));
        System.out.println("POST /orders (missing required field): " + server.call("POST", "/orders", "{\"amount\":10}"));
    }
}
```

How to run: `java StubRunnerLevel3.java`

The final call, missing `"customerEmail"` in its request body, matches no stub mapping's `requiredBodyContains` condition and correctly falls through to `"404 Not Found (no matching stub)"` — while the third call, which does include `"customerEmail"`, correctly matches the `POST /orders` stub and returns its `201` response — demonstrating that a real WireMock-backed stub genuinely matches on request content, not merely URL, allowing consumer tests to exercise both the success path and realistic not-matched/error paths against the exact same stub server.

## 6. Walkthrough

Trace the two `POST /orders` calls in Level 3.

1. `server.call("POST", "/orders", "{\"customerEmail\":\"a@b.com\"}")` iterates `mappings`, checking each `StubMapping` in order. For the third mapping (`POST /orders` with `requiredBodyContains="customerEmail"`), `methodMatches` is `true` (`"POST".equals("POST")`), `urlMatches` is `true`, and `bodyMatches` evaluates `requestBody.contains("customerEmail")`, which is `true` since the passed body literally contains that substring.
2. All three conditions are `true`, so this mapping is selected, and `"201 {\"id\":43,\"status\":\"PENDING\"}"` is returned — the consumer test sees exactly what the producer's contract for a successful order creation promises.
3. `server.call("POST", "/orders", "{\"amount\":10}")` again reaches the third mapping during iteration — `methodMatches` and `urlMatches` are still both `true`, but `bodyMatches` now evaluates `requestBody.contains("customerEmail")` against `"{\"amount\":10}"`, which does *not* contain that substring, so `bodyMatches` is `false`.
4. Because `bodyMatches` is `false`, the combined `if` condition fails for this mapping, and since no other mapping in the list matches `POST /orders` either, the loop finishes without finding a match, falling through to the final `return "404 Not Found (no matching stub)"`.
5. This correctly models a real WireMock stub's content-based matching: a request missing a field the contract requires simply doesn't match that stub's mapping, giving the consumer's test a realistic "your request was malformed" response rather than a false-positive success.

```
call("POST", "/orders", body WITH "customerEmail")
  mapping 3: method OK, url OK, body CONTAINS "customerEmail" -> MATCH -> 201 response

call("POST", "/orders", body WITHOUT "customerEmail")
  mapping 3: method OK, url OK, body does NOT contain "customerEmail" -> NO MATCH
  no other mapping matches either -> 404 Not Found (no matching stub)
```

## 7. Gotchas & takeaways

> **Gotcha:** a stub artifact reflects the producer's contracts *as of the version fetched* — if a consumer pins to an outdated stub version, their tests can keep passing against behavior the producer's real service no longer actually exhibits, silently reintroducing the exact staleness problem contract testing exists to prevent. Keeping stub dependency versions reasonably current (or intentionally testing against a specific, deliberately-pinned version for a known compatibility window) is a deliberate choice, not something to leave unconsidered indefinitely.

- Stub Runner's core value is automating the fetch-and-start lifecycle of contract-derived stubs, so a consumer's test declares a dependency and gets a fully running, contract-accurate fake server with no manual mock-writing involved.
- Because the stub server is a real WireMock instance (not a simplified hand-rolled fake), it supports realistic HTTP matching behavior — method, URL, and request body/header content — letting consumer tests exercise both success and structured failure paths against the same stub.
- Running consumer tests against stubs requires no real producer service anywhere in the test environment, making consumer-side test suites faster, more reliable, and independent of the producer team's own deployment or availability.
- The version of the stub artifact a consumer depends on determines exactly which contract snapshot their tests verify against — deliberately managing that version (rather than letting it silently go stale) keeps the consumer's tests meaningfully representative of the producer's actual current behavior.
