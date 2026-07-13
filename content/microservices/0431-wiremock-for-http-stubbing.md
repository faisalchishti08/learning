---
card: microservices
gi: 431
slug: wiremock-for-http-stubbing
title: "WireMock for HTTP stubbing"
---

## 1. What it is

**WireMock** is the standard Java library for [service virtualization](0419-service-virtualization-stubbing-dependencies.md): it runs an actual small HTTP server — in-process, as a JUnit extension, or standalone — that you configure with request-matching rules and scripted responses. Your code under test makes a genuine HTTP call, over a real socket (or an in-process equivalent), to what it believes is a real dependency; WireMock intercepts it, checks the request against its configured stubs, and returns exactly the response you scripted: a specific status code, headers, body, and optionally a simulated delay or fault. It's the concrete tool most of the Spring ecosystem's higher-level testing conventions — [web layer tests](0425-web-layer-tests-webmvctest-webfluxtest.md), the [Spring Cloud Contract stub runner](0430-spring-cloud-contract-stub-runner.md) — are ultimately built on top of.

## 2. Why & when

You reach for WireMock specifically whenever a test needs to control the behavior of an HTTP dependency without that dependency actually running:

- **You need to test error handling you can't reliably trigger against a real dependency.** A third-party payment gateway's sandbox rarely lets you reliably force a 500, a malformed JSON body, or a specific timeout on demand — WireMock lets you script exactly that, deterministically, every single run.
- **Real dependencies make tests slow, flaky, and hard to run offline.** A real network call — even to a service you own — adds latency and a chance of failing for reasons unrelated to the code under test, exactly the fragility [end-to-end testing](0417-end-to-end-testing-its-fragility.md) suffers from at larger scale.
- **You need request verification, not just response scripting.** WireMock can assert that your code sent a request matching specific criteria (the right headers, the right body shape, the right number of times) — proving your code makes the calls it's supposed to, not just that it handles responses correctly.
- **It integrates directly with JUnit 5** via `WireMockExtension`, and with Spring Boot test slices, so a stub server's lifecycle is managed automatically alongside the test's own lifecycle — no separate process to start and stop by hand.

You reach for WireMock as the default tool whenever a dependency is reached over HTTP and you don't already have a Spring Cloud Contract-generated stub for it (see [Spring Cloud Contract stub runner](0430-spring-cloud-contract-stub-runner.md) for when that's the better fit) — third-party APIs, dependencies without a contract-testing setup, or any HTTP call you want to script deterministically in a test.

## 3. Core concept

Picture a stunt double on a film set standing in for the lead actor during a dangerous scene. The camera (your code under test) films a genuinely real person doing genuinely real physical actions — nothing about the footage is faked at the level of "did a person actually move through that space" — but the specific person, and the specific outcome (the stunt double survives the fall exactly as scripted), is entirely controlled by the production. WireMock is that stunt double for an HTTP dependency: your code makes a completely real HTTP call, but the specific server answering it, and the specific outcome, is entirely scripted by the test.

Concretely, a WireMock stub configuration has three parts:

1. **A request matcher** — `stubFor(post(urlEqualTo("/charge")).withRequestBody(matchingJsonPath("$.amount")))` — which requests this rule applies to, matched by URL, method, headers, or body content.
2. **A scripted response** — `.willReturn(aResponse().withStatus(200).withBody("{\"approved\":true}"))` — the exact status, headers, and body to return.
3. **Optional behavior and verification** — `withFixedDelay(3000)` for simulated latency, `.inScenario(...)` for stateful multi-call sequences (fail once, then succeed), and `verify(postRequestedFor(urlEqualTo("/charge")))` to assert your code actually made the expected call.

```java
@RegisterExtension
static WireMockExtension wm = WireMockExtension.newInstance()
        .options(wireMockConfig().dynamicPort())
        .build();

@Test
void chargesPaymentGatewayWithCorrectBody() {
    wm.stubFor(post(urlEqualTo("/charge"))
            .willReturn(aResponse().withStatus(200).withBody("{\"approved\":true}")));

    paymentClient.charge(49.99);

    wm.verify(postRequestedFor(urlEqualTo("/charge"))
            .withRequestBody(matchingJsonPath("$.amount", equalTo("49.99"))));
}
```

`dynamicPort()` avoids hard-coding a port that might collide with another process; the test both scripts the response *and* verifies the outgoing request shape, checking both directions of the interaction in one test.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Code under test makes a real HTTP request; WireMock's request matcher checks it against configured stub rules; a matching rule returns a scripted response; WireMock also records every request received so the test can verify what was actually sent">
  <rect x="30" y="70" width="150" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="98" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Code under test</text>
  <text x="105" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">real HTTP call</text>

  <line x1="180" y1="105" x2="250" y2="105" stroke="#79c0ff" stroke-width="2"/>

  <rect x="250" y="30" width="180" height="150" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">WireMock server</text>
  <rect x="265" y="65" width="150" height="30" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="340" y="84" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">request matcher</text>
  <rect x="265" y="100" width="150" height="30" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="340" y="119" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">scripted response</text>
  <rect x="265" y="135" width="150" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="340" y="154" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">recorded requests (for verify)</text>

  <line x1="340" y1="180" x2="340" y2="200" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="340" y="212" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">test asserts on request AND response</text>
</svg>

WireMock matches incoming requests against configured rules, returns scripted responses, and records every request so tests can verify outgoing calls too.

## 5. Runnable example

Scenario: a `PaymentClient` calling an external `/charge` endpoint. We model WireMock's request-matching and response-scripting behavior in plain Java first, then show the real `WireMockExtension` shape, then handle a production-flavored stateful scenario: a gateway that fails once and succeeds on retry.

### Level 1 — Basic

```java
// File: WireMockCoreConceptBasic.java -- models WireMock's CORE behavior:
// a stub server matches incoming requests against configured rules and
// returns a scripted response, before any real WireMock dependency is used.
public class WireMockCoreConceptBasic {
    record ScriptedResponse(int status, String body) {}

    static class StubServer {
        private ScriptedResponse configured = new ScriptedResponse(404, "{\"error\":\"no stub configured\"}");

        void stubFor(int status, String body) { configured = new ScriptedResponse(status, body); }

        ScriptedResponse handle(String method, String path, String requestBody) {
            System.out.println("[StubServer] received " + method + " " + path + " body=" + requestBody);
            return configured;
        }
    }

    static String callPaymentGateway(StubServer server, double amount) {
        ScriptedResponse response = server.handle("POST", "/charge", "{\"amount\":" + amount + "}");
        return "status=" + response.status() + " body=" + response.body();
    }

    public static void main(String[] args) {
        StubServer server = new StubServer();
        server.stubFor(200, "{\"approved\":true}");
        System.out.println(callPaymentGateway(server, 49.99));
    }
}
```

How to run: `java WireMockCoreConceptBasic.java`

`StubServer.handle` mirrors WireMock's essential job: receive a request, check it against configured rules, return the scripted response. `callPaymentGateway` behaves exactly as real client code would — it has no idea it's talking to a stub rather than a real gateway, which is the property that makes WireMock-based tests meaningful.

### Level 2 — Intermediate

```java
// File: WireMockRealShapeIntermediate.java -- the SAME scenario, now in its
// REAL WireMock form using WireMockExtension, request matching, and
// verification, as it would really be written and run under Maven/Gradle
// with the wiremock-jre8 (or com.github.tomakehurst:wiremock) and JUnit 5
// dependencies on the classpath.
import com.github.tomakehurst.wiremock.junit5.WireMockExtension;
import org.junit.jupiter.api.RegisterExtension;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClient;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static org.assertj.core.api.Assertions.assertThat;

public class WireMockRealShapeIntermediate {

    static class PaymentClient {
        private final RestClient restClient;
        PaymentClient(String baseUrl) { this.restClient = RestClient.create(baseUrl); }

        String charge(double amount) {
            return restClient.post().uri("/charge")
                    .contentType(org.springframework.http.MediaType.APPLICATION_JSON)
                    .body("{\"amount\":" + amount + "}")
                    .retrieve().body(String.class);
        }
    }

    @RegisterExtension
    static WireMockExtension wireMock = WireMockExtension.newInstance()
            .options(wireMockConfig().dynamicPort())
            .build();

    @Test
    void chargesPaymentGatewayAndVerifiesRequestShape() {
        wireMock.stubFor(post(urlEqualTo("/charge"))
                .willReturn(aResponse().withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody("{\"approved\":true}")));

        PaymentClient client = new PaymentClient(wireMock.baseUrl());
        String response = client.charge(49.99);

        assertThat(response).contains("\"approved\":true");

        // Verify our OWN code sent the request we expect, not just that we
        // handled the response correctly.
        wireMock.verify(postRequestedFor(urlEqualTo("/charge"))
                .withRequestBody(matchingJsonPath("$.amount", equalTo("49.99"))));
    }
}
```

How to run: requires `wiremock-jre8` (or `wiremock`), `spring-boot-starter-web`, and JUnit 5 on the classpath; run as a JUnit 5 test via `mvn test` or your IDE's test runner.

`WireMockExtension` with `dynamicPort()` starts a real HTTP server on an available port and tears it down automatically after the test. `wireMock.baseUrl()` gives `PaymentClient` a real URL to call — the client code is identical to what would call a real gateway. `wireMock.verify(...)` closes the loop by checking the *outgoing* request shape, proving `PaymentClient.charge` builds its request body correctly, not just that it can parse a scripted response.

### Level 3 — Advanced

```java
// File: WireMockStatefulScenarioAdvanced.java -- the SAME payment client,
// now handling a PRODUCTION-FLAVORED hard case: a gateway that fails with a
// transient error on the FIRST call and succeeds on a RETRY, using
// WireMock's stateful scenario feature to script a realistic, order-
// dependent sequence of responses -- something a single static stub cannot express.
import com.github.tomakehurst.wiremock.junit5.WireMockExtension;
import org.junit.jupiter.api.RegisterExtension;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.HttpServerErrorException;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static org.assertj.core.api.Assertions.assertThat;

public class WireMockStatefulScenarioAdvanced {

    static class PaymentClient {
        private final RestClient restClient;
        PaymentClient(String baseUrl) { this.restClient = RestClient.create(baseUrl); }

        // Retries ONCE on a 503, mirroring realistic client resilience logic.
        String chargeWithRetry(double amount) {
            try {
                return doCharge(amount);
            } catch (HttpServerErrorException.ServiceUnavailable e) {
                System.out.println("[PaymentClient] first attempt got 503, retrying once...");
                return doCharge(amount);
            }
        }

        private String doCharge(double amount) {
            return restClient.post().uri("/charge")
                    .contentType(org.springframework.http.MediaType.APPLICATION_JSON)
                    .body("{\"amount\":" + amount + "}")
                    .retrieve().body(String.class);
        }
    }

    @RegisterExtension
    static WireMockExtension wireMock = WireMockExtension.newInstance()
            .options(wireMockConfig().dynamicPort())
            .build();

    @Test
    void retriesOnTransientFailureAndSucceedsOnSecondAttempt() {
        String scenario = "gateway-flakiness";

        // FIRST call in this scenario: return 503 (transient failure).
        wireMock.stubFor(post(urlEqualTo("/charge"))
                .inScenario(scenario)
                .whenScenarioStateIs(com.github.tomakehurst.wiremock.stubbing.Scenario.STARTED)
                .willReturn(aResponse().withStatus(503).withBody("{\"error\":\"temporarily unavailable\"}"))
                .willSetStateTo("failed-once"));

        // SECOND call in this scenario (only reached after the state transition above): succeed.
        wireMock.stubFor(post(urlEqualTo("/charge"))
                .inScenario(scenario)
                .whenScenarioStateIs("failed-once")
                .willReturn(aResponse().withStatus(200).withBody("{\"approved\":true}")));

        PaymentClient client = new PaymentClient(wireMock.baseUrl());
        String response = client.chargeWithRetry(49.99);

        assertThat(response).contains("\"approved\":true");
        // Confirm the gateway was actually called TWICE -- proving the retry genuinely happened.
        wireMock.verify(2, postRequestedFor(urlEqualTo("/charge")));
    }
}
```

How to run: requires the same WireMock and Spring Web dependencies as Level 2; run as a JUnit 5 test via `mvn test` or your IDE's test runner.

`inScenario`/`whenScenarioStateIs`/`willSetStateTo` script a stateful sequence: the *first* matching request returns a 503 and transitions WireMock's internal scenario state to `"failed-once"`; the *second* stub only matches once that state is active, and returns a success. This is something a single static stub structurally cannot express — it requires WireMock to remember state across calls within the test, exactly modeling a flaky real dependency that fails transiently and recovers, which is precisely the class of scenario a real third-party sandbox would rarely let you reproduce reliably on demand.

## 6. Walkthrough

Trace `retriesOnTransientFailureAndSucceedsOnSecondAttempt` in order. **First**, two stubs are registered in the same named scenario, `"gateway-flakiness"`, WireMock's internal state machine starting in the built-in `STARTED` state. The first stub matches only while state is `STARTED` and, when matched, both returns a 503 *and* transitions the state to `"failed-once"`.

**Next**, `client.chargeWithRetry(49.99)` calls `doCharge`, sending the first POST `/charge`. WireMock's scenario state is currently `STARTED`, so the first stub matches, returning a 503 with body `{"error":"temporarily unavailable"}` — and, as a side effect, WireMock's internal scenario state transitions to `"failed-once"`.

**Then**, `RestClient` throws `HttpServerErrorException.ServiceUnavailable` for the 503 response. `chargeWithRetry`'s `catch` block logs the retry and calls `doCharge` a second time, sending a second POST `/charge`. This time, WireMock's scenario state is `"failed-once"`, so the *second* stub matches instead of the first, returning `200` with `{"approved":true}`.

**Finally**, `chargeWithRetry` returns that successful response to the test. `assertThat(response).contains(...)` confirms the retry ultimately succeeded, and `wireMock.verify(2, postRequestedFor(...))` confirms the gateway endpoint was actually called exactly twice — proof that the retry logic genuinely executed a second real request, not just that the final result happened to look correct.

```
POST /charge (attempt 1) -> scenario state=STARTED -> 503 {"error":"temporarily unavailable"}
  [PaymentClient] first attempt got 503, retrying once...
POST /charge (attempt 2) -> scenario state=failed-once -> 200 {"approved":true}

Test result: retriesOnTransientFailureAndSucceedsOnSecondAttempt PASSED
  response contains "approved":true -- OK
  verify(2, postRequestedFor(/charge)) -- OK (exactly 2 calls recorded)
```

## 7. Gotchas & takeaways

> A stub that only scripts the *response* but never verifies the *request* can pass even when your code sends a malformed or wrong request, because WireMock will happily match a loosely-specified rule (like matching on URL alone) and return the scripted body regardless of what was actually sent. Always pair response scripting with request verification (`withRequestBody`, `verify(postRequestedFor(...))`) whenever the shape of the outgoing request is part of what you're actually testing.

- WireMock runs a genuine HTTP server your code talks to over real (or in-process) sockets, so the code under test cannot distinguish it from a real dependency at the protocol level — this is what makes the test meaningful.
- Scenario-based stateful stubs (`inScenario`, `whenScenarioStateIs`, `willSetStateTo`) are the right tool for testing retry, circuit-breaker, and recovery logic — a single static stub can't express "fail once, then succeed."
- `verify(...)` checks the outgoing request shape and call count, closing the loop on testing both directions of an HTTP interaction, not just the response-handling side.
- WireMock underlies the [Spring Cloud Contract stub runner](0430-spring-cloud-contract-stub-runner.md) — the stub runner's value is generating WireMock stub definitions automatically from a verified contract instead of hand-writing them.
- For dependencies without a published contract, WireMock remains the direct, general-purpose tool for [service virtualization](0419-service-virtualization-stubbing-dependencies.md) — reach for the stub runner instead only when the provider already publishes Spring Cloud Contract stubs.
