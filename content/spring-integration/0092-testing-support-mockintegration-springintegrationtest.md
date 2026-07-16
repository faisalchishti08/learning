---
card: spring-integration
gi: 92
slug: testing-support-mockintegration-springintegrationtest
title: "Testing support (MockIntegration, @SpringIntegrationTest)"
---

## 1. What it is

Testing support (`@SpringIntegrationTest`, the `MockIntegration` factory methods, `MockMessageHandler`, and `MockIntegrationContext`) provides purpose-built tools for testing Spring Integration flows: intercepting a real flow's endpoints to substitute mock behavior, asserting on messages sent to a channel without needing a real downstream consumer, and replacing a poller's trigger to fire on demand from a test rather than waiting on a real schedule. Together they let a flow be tested in something close to its full wired form, without needing real external systems (a live database, a live message broker) behind every adapter.

## 2. Why & when

You reach for this testing support when a flow's correctness needs verifying in a way that a plain unit test of individual handler methods can't cover:

- **Verifying that a message reaches the correct channel after passing through routers and filters** — `@SpringIntegrationTest` loads the actual flow configuration, letting a test send a message in and assert on where it ends up, exercising the real routing logic rather than a hand-picked subset of it.
- **Testing a flow's behavior without depending on a real external system** — `MockIntegration.mockMessageSource(...)` or a substituted outbound gateway lets a test simulate what an FTP server, a database, or an HTTP client would produce or consume, without actually running one during the test.
- **Controlling a poller's timing deterministically** — replacing a poller's real time-based trigger with `MockIntegrationContext.substituteMessageHandlerFor(...)`-style control lets a test fire a poll cycle exactly once, on demand, rather than either waiting for a real timer or fighting with flaky timing-dependent assertions.

## 3. Core concept

Think of testing a fully-wired flow like testing a car on a rolling road (a dynamometer) instead of either disassembling it into individual parts (unit-testing handler methods in isolation, missing how they connect) or driving it on a real highway (a full integration test against real external systems, slow and environment-dependent). The rolling road lets the whole drivetrain run together — exactly like it would on the road — while giving the tester full control over conditions (simulated road load, no actual highway needed) and instrumentation to observe exactly what's happening at each point along the way.

```java
@SpringIntegrationTest
@SpringBootTest
class OrderFlowTest {

    @Autowired
    private MockIntegrationContext mockIntegrationContext;

    @Test
    void urgentOrdersRouteToFastTrackChannel() {
        MessageChannel fastTrackChannel = MockIntegration.mockMessageSource(); // simplified illustration
        // substitute the real fast-track handler with a mock to capture what arrives
        MockMessageHandler mockHandler = MockIntegration.mockMessageHandler()
            .handleNext(msg -> assertThat(msg.getPayload()).isEqualTo("urgent-order-1"));
        mockIntegrationContext.substituteMessageHandlerFor("fastTrackHandler.handler", mockHandler);

        orderInputChannel.send(MessageBuilder.withPayload("urgent-order-1").build());
    }
}
```

The test loads the real flow configuration and substitutes just one handler with a mock, letting the actual routing logic run unmodified while capturing what reaches the substituted point.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A flow test loads the real flow wiring but substitutes specific endpoints (like an outbound gateway to an external system) with mocks, exercising genuine routing and transformation logic without depending on real external systems" >
  <rect x="20" y="20" width="140" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Real input channel</text>

  <line x1="160" y1="42" x2="230" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a8)"/>
  <rect x="230" y="20" width="140" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Real router/filter</text>

  <line x1="370" y1="42" x2="440" y2="42" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a8)"/>
  <rect x="440" y="20" width="180" height="45" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">MockMessageHandler (test)</text>

  <text x="320" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Real routing logic exercised end to end; only the external-facing endpoint is substituted</text>
</svg>

The real logic that matters for the test stays real; only the boundary to an external system is faked.

## 5. Runnable example

The scenario: testing that urgent orders route to a fast-track handler while standard orders don't, simulated with a plain in-memory flow model standing in for `@SpringIntegrationTest`'s wiring (no real Spring test context needed to demonstrate the substitute-and-assert testing pattern), starting with a basic assertion against a mock handler, then adding a routing test exercising real filter logic, then adding a deterministic poller-trigger test that fires a poll cycle on demand rather than waiting on real timing.

### Level 1 — Basic

```java
// FlowTestingDemo.java
import java.util.*;

public class FlowTestingDemo {
    record Order(String id, boolean urgent) {}

    // Stand-in for MockMessageHandler: captures what arrives instead of doing real work.
    static class CapturingHandler {
        List<Order> captured = new ArrayList<>();
        void handle(Order order) { captured.add(order); }
    }

    public static void main(String[] args) {
        CapturingHandler mockFastTrackHandler = new CapturingHandler();
        mockFastTrackHandler.handle(new Order("ORD-1", true));

        assert mockFastTrackHandler.captured.size() == 1 : "expected exactly one captured order";
        assert mockFastTrackHandler.captured.get(0).id().equals("ORD-1") : "expected ORD-1";
        System.out.println("Test passed: mock handler captured " + mockFastTrackHandler.captured);
    }
}
```

How to run: `java -ea FlowTestingDemo.java` (the `-ea` flag enables assertions). Expected output: `Test passed: mock handler captured [Order[id=ORD-1, urgent=true]]` — a basic mock-capture assertion, the simplest form of substituting an endpoint to verify what reaches it.

### Level 2 — Intermediate

```java
// FlowTestingDemo.java
import java.util.*;
import java.util.function.*;

public class FlowTestingDemo {
    record Order(String id, boolean urgent) {}

    static class CapturingHandler {
        List<Order> captured = new ArrayList<>();
        void handle(Order order) { captured.add(order); }
    }

    // Real-world concern: the test should exercise the ACTUAL routing logic (the real filter
    // condition), substituting only the endpoints at the edges (the fast-track and standard
    // handlers), not reimplementing the routing decision inside the test itself.
    static void realRoutingLogic(Order order, CapturingHandler fastTrack, CapturingHandler standard) {
        if (order.urgent()) {
            fastTrack.handle(order);
        } else {
            standard.handle(order);
        }
    }

    public static void main(String[] args) {
        CapturingHandler fastTrackMock = new CapturingHandler();
        CapturingHandler standardMock = new CapturingHandler();

        realRoutingLogic(new Order("ORD-1", true), fastTrackMock, standardMock);
        realRoutingLogic(new Order("ORD-2", false), fastTrackMock, standardMock);

        System.out.println("Fast-track received: " + fastTrackMock.captured);
        System.out.println("Standard received: " + standardMock.captured);

        assert fastTrackMock.captured.size() == 1 && fastTrackMock.captured.get(0).id().equals("ORD-1");
        assert standardMock.captured.size() == 1 && standardMock.captured.get(0).id().equals("ORD-2");
        System.out.println("Routing test passed");
    }
}
```

How to run: `java -ea FlowTestingDemo.java`. Expected output: `Fast-track received: [Order[id=ORD-1, urgent=true]]`, `Standard received: [Order[id=ORD-2, urgent=false]]`, then `Routing test passed` — the real routing condition (`order.urgent()`) determined which mock handler received each order, exactly the kind of assertion `@SpringIntegrationTest` enables against a fully-wired flow with only the terminal handlers substituted.

### Level 3 — Advanced

```java
// FlowTestingDemo.java
import java.util.*;
import java.util.function.*;

public class FlowTestingDemo {
    record Order(String id, boolean urgent) {}

    static class CapturingHandler {
        List<Order> captured = new ArrayList<>();
        void handle(Order order) { captured.add(order); }
    }

    static void realRoutingLogic(Order order, CapturingHandler fastTrack, CapturingHandler standard) {
        if (order.urgent()) fastTrack.handle(order); else standard.handle(order);
    }

    // Production concern: rather than waiting on a real timer (flaky in CI, slow to test),
    // substitute the poller's trigger so the test fires exactly one poll cycle on demand --
    // the same idea behind MockIntegrationContext's trigger substitution for pollers.
    static class ManuallyTriggeredPoller {
        private final Queue<Order> source;
        private final Consumer<Order> downstream;

        ManuallyTriggeredPoller(Queue<Order> source, Consumer<Order> downstream) {
            this.source = source;
            this.downstream = downstream;
        }

        // Test calls this directly instead of waiting for a real Trigger to fire on a schedule.
        void firePollCycleManually() {
            Order next = source.poll();
            if (next != null) downstream.accept(next);
        }
    }

    public static void main(String[] args) {
        CapturingHandler fastTrackMock = new CapturingHandler();
        CapturingHandler standardMock = new CapturingHandler();

        Queue<Order> source = new LinkedList<>(List.of(
            new Order("ORD-1", true), new Order("ORD-2", false)));

        ManuallyTriggeredPoller poller = new ManuallyTriggeredPoller(source,
            order -> realRoutingLogic(order, fastTrackMock, standardMock));

        // The test controls exactly when each poll cycle happens -- no real timer, no sleep().
        poller.firePollCycleManually();
        poller.firePollCycleManually();

        System.out.println("Fast-track: " + fastTrackMock.captured);
        System.out.println("Standard: " + standardMock.captured);

        assert fastTrackMock.captured.size() == 1;
        assert standardMock.captured.size() == 1;
        System.out.println("Deterministic poller test passed, no real timing involved");
    }
}
```

How to run: `java -ea FlowTestingDemo.java`. Expected output: `Fast-track: [Order[id=ORD-1, urgent=true]]`, `Standard: [Order[id=ORD-2, urgent=false]]`, then `Deterministic poller test passed, no real timing involved` — each poll cycle fired exactly once, on demand from the test itself, exercising the same routing logic as Level 2 but with poller timing fully under the test's control rather than dependent on a real clock.

## 6. Walkthrough

Trace a flow test from setup through assertion, mirroring what `@SpringIntegrationTest` provides.

1. **Test context loads**: `@SpringIntegrationTest` (combined with `@SpringBootTest` or a similar context-loading annotation) starts the real Spring application context, wiring up the actual flow configuration exactly as it would run in production — channels, routers, filters, all genuinely instantiated.
2. **Substitution of external-facing endpoints**: before sending any test message, the test uses `MockIntegrationContext.substituteMessageHandlerFor(...)` to replace specific endpoints — typically ones that would otherwise reach a real external system — with `MockMessageHandler` instances that capture what they receive instead of performing real work.
3. **Message injection**: the test sends a message directly onto the flow's real input channel, exactly as a genuine caller would, using the actual `MessageChannel` bean from the loaded context.
4. **Real logic executes**: the message flows through every real, unsubstituted component — filters, routers, transformers — with their actual configured logic determining where the message goes, precisely as it would in production.
5. **Assertion against the mock**: once the message reaches a substituted endpoint, the test's `MockMessageHandler` captures it, and the test asserts on what arrived (or didn't arrive) there, confirming the real flow logic produced the expected routing outcome.
6. **Deterministic poller control (where relevant)**: for polling-based flows, the test can substitute the poller's trigger to fire manually on demand rather than waiting for a real time-based schedule, keeping the test both fast and free of timing-related flakiness.

```
@SpringIntegrationTest loads real flow context
  -> substitute external-facing endpoints with MockMessageHandler
    -> test sends message to real input channel
      -> real filters/routers/transformers execute genuinely
        -> message reaches substituted mock endpoint
          -> test asserts on what the mock captured
```

## 7. Gotchas & takeaways

> **Gotcha:** substituting too much of a flow with mocks (mocking the router itself, for instance, rather than only the terminal external-facing endpoints) defeats the purpose of this kind of test entirely — the value of `@SpringIntegrationTest` comes specifically from exercising the *real* routing and transformation logic; if that logic is mocked away too, the test no longer verifies anything meaningful about the flow's actual behavior.

- Substitute mocks at the boundary where a flow would otherwise touch a real external system (an outbound gateway, a database adapter), and leave the flow's internal logic (routers, filters, transformers) genuinely running — that's what distinguishes this kind of test from either a narrow unit test or a slow, environment-dependent full integration test.
- Controlling poller timing explicitly through trigger substitution avoids the classic flaky-test problem of asserting on a background poller's effects before it has actually fired, or waiting an arbitrarily long `Thread.sleep()` and hoping it was long enough.
- These testing tools work well specifically because Spring Integration flows are wired declaratively — the same dependency-injected structure that makes a flow easy to configure also makes it straightforward to substitute individual pieces of it for testing.
- Reserve `MockIntegration`/`@SpringIntegrationTest`-style tests for verifying flow-level behavior (routing, transformation, error handling across multiple components); simpler, pure unit tests are still the right tool for verifying an individual handler method's logic in isolation, without the overhead of loading the full flow context.
