---
card: spring-cloud
gi: 124
slug: producer-consumer-side-testing
title: "Producer & consumer side testing"
---

## 1. What it is

Producer-side testing means Spring Cloud Contract generating a real test (a `MockMvc`-based or full HTTP test) from each contract and running it against the producer's *actual* implementation as part of the producer's own build, failing that build the moment behavior diverges; consumer-side testing means a consumer team writing their integration tests against the Stub Runner-provided fake (the previous card), asserting their own code correctly handles the response the contract promises — these are deliberately two separate test suites, owned by two separate teams, verifying two separate things, both derived from the same underlying set of contracts.

```java
// PRODUCER side -- generated automatically, runs against the REAL controller
// (typically found in target/generated-test-sources, not hand-written)
public class ContractVerifierTest extends BaseTestClass {
    @Test
    public void validate_shouldReturnOrder() throws Exception {
        mockMvc.perform(get("/orders/42"))
               .andExpect(status().isOk())
               .andExpect(jsonPath("$.status").value("CONFIRMED"));
    }
}
```

```java
// CONSUMER side -- hand-written by the consumer team, runs against the STUB
@Test
void shouldHandleConfirmedOrder() {
    Order order = orderClient.getOrder(42); // calls the Stub Runner-provided fake
    assertThat(order.isReadyToShip()).isTrue(); // asserts the CONSUMER's OWN logic reacts correctly
}
```

## 2. Why & when

These two test suites intentionally test different things and belong to different teams, and conflating them (or assuming one substitutes for the other) misses the actual value of the whole approach: the producer-side test's job is narrowly "does my real implementation actually produce what I promised in the contract" — it says nothing about whether any consumer's own logic handles that response correctly. The consumer-side test's job is narrowly "does my code correctly handle the response the contract promises" — it says nothing about whether the producer's real implementation actually delivers that response, since it never talks to the real producer at all. Both tests passing together is what gives genuine end-to-end confidence; either one alone leaves a real gap the other exists specifically to close.

Reach for understanding this split explicitly when:

- Setting up Spring Cloud Contract for the first time and deciding what belongs in the producer's test suite versus the consumer's — producer-side tests are (mostly) auto-generated from contracts and verify implementation correctness; consumer-side tests are hand-written and verify the consumer's own business logic against the contracted response shape.
- Debugging a production issue where an integration appeared correctly tested but still failed — checking whether the failure falls in the producer's actual behavior (should have been caught by producer-side tests) or the consumer's handling logic (should have been caught by consumer-side tests) usually reveals which test suite had a gap.
- Onboarding a new team onto contract testing and needing to clarify who owns what — the producer team owns and maintains the contracts and their own generated verification tests; the consumer team owns their own stub-based tests, entirely independently, without needing write access to the producer's codebase at all.

## 3. Core concept

```
 PRODUCER-SIDE test (generated from the contract, runs against the REAL implementation):
   verifies: "does MY implementation actually produce what the contract promises?"
   catches:  a producer regression that breaks a documented, contracted behavior

 CONSUMER-SIDE test (hand-written, runs against the STUB):
   verifies: "does MY code correctly handle the response the contract promises?"
   catches:  a consumer bug in how they process a correctly-shaped response

 NEITHER test alone verifies the FULL, real, live producer-to-consumer interaction --
 BOTH together give confidence the interaction genuinely works end to end, without ever
 needing both services running simultaneously against each other in a single test
```

Each test suite verifies exactly its own side's obligation against the shared contract — the contract itself is what keeps both obligations aligned with each other, without either side needing direct visibility into the other's actual code.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A producer side test verifies the real implementation against the contract while a separate consumer side test verifies consumer logic against a stub with both tests independently owned by different teams yet both anchored to the same shared contract">
  <rect x="230" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">shared contract</text>

  <rect x="30" y="110" width="220" height="56" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="140" y="130" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">producer-side test</text>
  <text x="140" y="144" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">generated, runs vs REAL impl</text>
  <text x="140" y="157" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">owned by producer team</text>

  <rect x="390" y="110" width="220" height="56" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="500" y="130" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">consumer-side test</text>
  <text x="500" y="144" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">hand-written, runs vs STUB</text>
  <text x="500" y="157" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">owned by consumer team</text>

  <defs><marker id="a124" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="60" x2="150" y2="110" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a124)"/>
  <line x1="360" y1="60" x2="490" y2="110" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a124)"/>
</svg>

Two independently owned, independently running test suites, both anchored to one shared contract — neither directly depends on the other's codebase.

## 5. Runnable example

The scenario: model both test suites for one contract, run against a correct implementation and correct consumer logic first, then break each side independently to show each test suite catches only its own side's failure — proving the split responsibility concretely. Start with both suites passing, then break the producer implementation only, then break the consumer logic only, confirming each failure is caught by exactly the corresponding test suite.

### Level 1 — Basic

Both test suites, passing, against a correct producer implementation and correct consumer logic.

```java
import java.util.*;

public class ProducerConsumerTestingLevel1 {
    record OrderResponse(int id, String status) {}

    // PRODUCER's real implementation
    static OrderResponse realImplementation(int orderId) { return new OrderResponse(orderId, "CONFIRMED"); }

    // PRODUCER-SIDE test: verifies the REAL implementation against the contract
    static void producerSideTest() {
        OrderResponse actual = realImplementation(42);
        if (!actual.status().equals("CONFIRMED")) throw new AssertionError("producer implementation violates contract");
        System.out.println("PRODUCER-SIDE TEST PASSED");
    }

    // CONSUMER's own business logic, reacting to the CONTRACTED response shape
    static boolean isReadyToShip(OrderResponse order) { return order.status().equals("CONFIRMED"); }

    // CONSUMER-SIDE test: verifies CONSUMER logic against a stub (here, the contracted shape directly)
    static void consumerSideTest() {
        OrderResponse stubResponse = new OrderResponse(42, "CONFIRMED"); // what the STUB returns, per the contract
        if (!isReadyToShip(stubResponse)) throw new AssertionError("consumer logic mishandles a CONFIRMED order");
        System.out.println("CONSUMER-SIDE TEST PASSED");
    }

    public static void main(String[] args) {
        producerSideTest();
        consumerSideTest();
    }
}
```

How to run: `java ProducerConsumerTestingLevel1.java`

Both tests pass — `producerSideTest` calls the real implementation directly, `consumerSideTest` calls the consumer's own logic against the contracted shape directly (standing in for the stub) — two entirely separate assertions, both currently satisfied.

### Level 2 — Intermediate

Break the producer's real implementation only, and confirm the producer-side test catches it while the consumer-side test (unaffected, since it never touches the real implementation) still passes.

```java
public class ProducerConsumerTestingLevel2 {
    record OrderResponse(int id, String status) {}

    // PRODUCER implementation has REGRESSED -- now returns the wrong status
    static OrderResponse brokenImplementation(int orderId) { return new OrderResponse(orderId, "PENDING"); }

    static void producerSideTest() {
        OrderResponse actual = brokenImplementation(42);
        if (!actual.status().equals("CONFIRMED")) throw new AssertionError("producer implementation violates contract: got " + actual.status());
        System.out.println("PRODUCER-SIDE TEST PASSED");
    }

    static boolean isReadyToShip(OrderResponse order) { return order.status().equals("CONFIRMED"); }

    static void consumerSideTest() {
        OrderResponse stubResponse = new OrderResponse(42, "CONFIRMED"); // the STUB is UNAFFECTED by the producer's bug
        if (!isReadyToShip(stubResponse)) throw new AssertionError("consumer logic mishandles a CONFIRMED order");
        System.out.println("CONSUMER-SIDE TEST PASSED (unaffected by producer's bug)");
    }

    public static void main(String[] args) {
        try {
            producerSideTest();
        } catch (AssertionError e) {
            System.out.println("PRODUCER-SIDE TEST FAILED (correctly caught): " + e.getMessage());
        }

        consumerSideTest(); // still passes -- it never talks to the broken real implementation at all
    }
}
```

How to run: `java ProducerConsumerTestingLevel2.java`

`producerSideTest` correctly fails, catching the regression in `brokenImplementation`; `consumerSideTest` still passes, because it was testing against `stubResponse` (standing in for the contract-derived stub), which is entirely unaffected by whatever the producer's real, currently-broken implementation does — this is exactly the intended isolation: a producer bug is caught by the producer's own test suite, without needing the consumer's test suite to somehow also detect it.

### Level 3 — Advanced

Break the consumer's own logic only, this time confirming the consumer-side test catches it while the producer-side test (testing an entirely correct producer) still passes — demonstrating both directions of the isolation.

```java
public class ProducerConsumerTestingLevel3 {
    record OrderResponse(int id, String status) {}

    static OrderResponse realImplementation(int orderId) { return new OrderResponse(orderId, "CONFIRMED"); } // CORRECT

    static void producerSideTest() {
        OrderResponse actual = realImplementation(42);
        if (!actual.status().equals("CONFIRMED")) throw new AssertionError("producer implementation violates contract");
        System.out.println("PRODUCER-SIDE TEST PASSED");
    }

    // CONSUMER'S logic has a BUG -- checks for the wrong status value entirely
    static boolean isReadyToShipBuggy(OrderResponse order) { return order.status().equals("SHIPPED"); } // WRONG check

    static void consumerSideTest() {
        OrderResponse stubResponse = new OrderResponse(42, "CONFIRMED"); // the stub correctly reflects the contract
        if (!isReadyToShipBuggy(stubResponse)) {
            throw new AssertionError("consumer logic mishandles a CONFIRMED order (checked for wrong status)");
        }
        System.out.println("CONSUMER-SIDE TEST PASSED");
    }

    public static void main(String[] args) {
        producerSideTest(); // passes -- the REAL producer implementation is entirely correct

        try {
            consumerSideTest();
        } catch (AssertionError e) {
            System.out.println("CONSUMER-SIDE TEST FAILED (correctly caught): " + e.getMessage());
        }
    }
}
```

How to run: `java ProducerConsumerTestingLevel3.java`

`producerSideTest` passes cleanly — the real producer implementation is entirely correct and matches the contract; `consumerSideTest` fails, because `isReadyToShipBuggy` checks for `"SHIPPED"` instead of `"CONFIRMED"`, a bug entirely within the consumer's own logic that has nothing to do with the producer at all — the stub correctly delivered `"CONFIRMED"` exactly as contracted, and the consumer's own code simply mishandled it; this is the mirror-image isolation to Level 2, together demonstrating that each test suite independently and correctly catches failures specific to its own side.

## 6. Walkthrough

Trace `consumerSideTest()` in Level 3.

1. `stubResponse = new OrderResponse(42, "CONFIRMED")` is constructed — this represents exactly what a real Stub Runner-provided WireMock stub would return for this contract, since the contract promises `status: "CONFIRMED"` for this scenario, and the stub is derived directly from that promise.
2. `isReadyToShipBuggy(stubResponse)` is called — inside, `order.status().equals("SHIPPED")` checks `"CONFIRMED".equals("SHIPPED")`, which evaluates `false`.
3. Because `isReadyToShipBuggy` returns `false`, the `if (!isReadyToShipBuggy(stubResponse))` check in `consumerSideTest` is `true`, so `AssertionError` is thrown with a message specifically describing the consumer logic's mishandling.
4. This exception propagates to the `catch` block in `main`, printing the failure — critically, nothing about this failure involved the real producer implementation at all; `producerSideTest()`, called just before in `main`, already ran and passed cleanly against `realImplementation`, entirely independently of this later, unrelated consumer-side failure.
5. In a real CI setup, these would be two entirely separate test runs in two entirely separate codebases/pipelines — the producer team's pipeline would show a green producer-side test run, while the consumer team's own pipeline would show this specific consumer-side test failing, correctly pointing them directly at their own buggy `isReadyToShipBuggy` logic rather than mistakenly suspecting the producer's API.

```
producerSideTest(): realImplementation returns CONFIRMED, matches contract -> PASSES

consumerSideTest():
  stubResponse = CONFIRMED (contract-accurate, from the stub)
  isReadyToShipBuggy(stubResponse) checks status == "SHIPPED" -> false (WRONG check, consumer's own bug)
  -> AssertionError thrown -> consumer-side test correctly FAILS, isolated entirely to the consumer's own logic
```

## 7. Gotchas & takeaways

> **Gotcha:** consumer-side tests passing does not mean the producer's real service currently behaves as contracted, and producer-side tests passing does not mean any consumer's actual logic correctly handles that behavior — a common misunderstanding is treating either test suite's green result as proof of the full end-to-end integration working; genuine end-to-end confidence requires *both* suites passing (each independently verifying its own side against the shared contract), not either one in isolation.

- Producer-side tests, mostly auto-generated from contracts, verify that the real implementation actually satisfies what's promised — they run entirely within the producer's own build and codebase, with no consumer code involved.
- Consumer-side tests, hand-written by the consumer team, verify that the consumer's own logic correctly handles the contracted response shape — they run against a stub, never against the real producer, entirely within the consumer's own build and codebase.
- This deliberate separation is what allows both teams to work, test, and deploy independently, without either needing direct access to or a running instance of the other's actual service — the shared contract, not a shared running service, is what keeps both sides honestly aligned.
- When a real production integration issue occurs despite both test suites passing, the contract itself is the first place to check — a gap between what the contract actually specifies and what either side genuinely needs is a more likely root cause than either individual test suite having a bug.
