---
card: microservices
gi: 411
slug: test-pyramid-for-microservices
title: "Test pyramid for microservices"
---

## 1. What it is

The **test pyramid** is a model for how a healthy test suite should be shaped: many fast, cheap **unit tests** at the base, a smaller number of **integration** and **component tests** in the middle, and a thin layer of slow, expensive **end-to-end tests** at the top. The shape is a deliberate investment strategy, not an accident — you write far more of the tests that are fast and pinpoint failures precisely, and far fewer of the tests that are slow, brittle, and only tell you "something, somewhere, is broken." In a microservices system, the pyramid gets an extra rung between unit and end-to-end: tests that check how one service talks to its own database or broker, and tests that check how one service's published API stays compatible with the services that consume it.

## 2. Why & when

You need this model the moment a system has more than one service, because the pyramid is what keeps a growing test suite affordable. Without it, teams drift toward an **ice-cream cone** shape — few unit tests, few integration tests, and a huge pile of end-to-end tests — because end-to-end tests feel the most "real." That drift is expensive:

- **Feedback speed collapses.** A unit test runs in milliseconds; a full end-to-end test that spins up five services, a database, and a broker can take minutes. Multiply that by thousands of tests and a build that used to take two minutes now takes two hours.
- **Failures become hard to localize.** When an end-to-end test fails, you don't know which of the five services in the chain caused it — you have to go dig. A unit test failure points at one method.
- **Flakiness compounds.** Each extra service, network hop, or shared piece of infrastructure in a test is another chance for the test to fail for reasons that have nothing to do with the code being tested — see [end-to-end testing & its fragility](0417-end-to-end-testing-its-fragility.md).
- **Ownership gets blurry.** A monolith has one test suite one team can run. In microservices, each team owns its own service's tests, so the pyramid has to be applied *per service*, with a thin, shared layer of cross-service tests on top — not one giant shared end-to-end suite that everyone is afraid to touch.

You reach for the pyramid as a planning tool at every stage: when deciding what kind of test to write for a new change, and when auditing an existing suite that has become slow or unreliable, to see which layer has grown too large.

## 3. Core concept

Picture a suite of tests as a diet. Unit tests are the vegetables: cheap, you should eat a lot of them, and they form the bulk of what keeps the system healthy day to day. Integration and component tests are the protein: fewer of them, but each one confirms something a vegetable can't — that a real database query works, or that a whole service behaves correctly at its boundary. End-to-end tests are dessert: valuable in small amounts to confirm the whole meal actually satisfies, but a diet made mostly of dessert will fail you, and it costs the most for the least nutritional value.

For a single microservice, the layers typically look like this, from base to tip:

1. **[Unit tests](0412-unit-testing-services.md)** — a single class or function, all collaborators faked or mocked, no network or database, running in milliseconds. The vast majority of tests live here.
2. **[Integration tests](0413-integration-testing-service-its-db-broker.md)** — the service talking to a real (often containerized) instance of its own database or message broker, verifying the plumbing actually works, not just the logic.
3. **[Component tests](0414-component-testing-single-service-in-isolation.md)** — the whole service exercised through its real API boundary, with everything *outside* the service stubbed out, verifying the service behaves correctly as a unit.
4. **[Contract tests](0415-contract-testing-consumer-driven-contracts.md)** — a thin, fast layer that verifies two services agree on the shape of their API, without either one needing to run the other for real.
5. **[End-to-end tests](0417-end-to-end-testing-its-fragility.md)** — a handful of tests exercising a full user journey across several real, running services, confirming the pieces actually fit together.

The pyramid's shape is a claim about proportions, not a claim that any layer is optional: as you move up, tests get slower, more expensive to maintain, and better at catching integration mistakes; as you move down, tests get faster, cheaper, and better at catching logic mistakes precisely. A healthy suite has an order of magnitude more tests at each layer than the layer above it.

## 4. Diagram

<svg viewBox="0 0 640 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A healthy test pyramid has many fast unit tests at the base, fewer integration and component tests in the middle, fewer contract tests above that, and very few slow end-to-end tests at the top; an inverted ice-cream-cone shape has the opposite proportions and is slow and hard to debug">
  <text x="160" y="20" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Healthy pyramid</text>
  <polygon points="160,40 100,80 220,80" fill="none" stroke="#f0883e" stroke-width="1.5"/>
  <text x="160" y="65" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">E2E (few)</text>
  <polygon points="160,80 80,120 240,120" fill="none" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">contract</text>
  <polygon points="160,120 60,160 260,160" fill="none" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="145" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">component / integration</text>
  <polygon points="160,160 30,220 290,220" fill="none" stroke="#6db33f" stroke-width="2"/>
  <text x="160" y="200" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">unit tests (many, fast)</text>

  <text x="480" y="20" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Inverted (ice-cream cone)</text>
  <polygon points="480,220 350,160 610,160" fill="none" stroke="#f85149" stroke-width="2"/>
  <text x="480" y="200" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">huge slow E2E suite</text>
  <polygon points="480,160 400,120 560,120" fill="none" stroke="#f0883e" stroke-width="1.5"/>
  <text x="480" y="145" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">some integration</text>
  <polygon points="480,120 440,80 520,80" fill="none" stroke="#8b949e" stroke-width="1.5"/>
  <text x="480" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">few unit tests</text>
  <text x="480" y="250" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">slow, flaky, hard to localize failures</text>
</svg>

A healthy suite is broad at the fast, cheap base and narrow at the slow, expensive tip; an inverted "ice-cream cone" suite pays the cost of slow tests without the confidence a solid base would give it.

## 5. Runnable example

Scenario: we model a service's test suite as counts of tests per pyramid layer, plus a rough cost-per-run in milliseconds for each layer, and compute whether the suite's shape is healthy or inverted, then estimate total suite runtime under each shape.

### Level 1 — Basic

```java
// File: PyramidLayerCounts.java -- represent a test suite as counts of
// tests at each pyramid layer, and print the total test count.
public class PyramidLayerCounts {
    public static void main(String[] args) {
        int unitTests = 240;
        int integrationTests = 40;
        int componentTests = 20;
        int contractTests = 15;
        int endToEndTests = 8;

        int total = unitTests + integrationTests + componentTests + contractTests + endToEndTests;
        System.out.println("unit=" + unitTests + " integration=" + integrationTests
                + " component=" + componentTests + " contract=" + contractTests
                + " e2e=" + endToEndTests + " total=" + total);
    }
}
```

How to run: `java PyramidLayerCounts.java`

This just tallies a suite's shape as five numbers, one per pyramid layer, from the base (`unitTests`) to the tip (`endToEndTests`). On its own this doesn't tell us whether the shape is healthy — for that we need to compare the layers to each other, which the next level adds.

### Level 2 — Intermediate

```java
// File: PyramidShapeCheck.java -- the SAME layer counts, now with a rule
// that flags an unhealthy (inverted) shape: each layer moving toward the
// tip should have meaningfully fewer tests than the layer below it.
public class PyramidShapeCheck {
    record Layer(String name, int count) {}

    static boolean isHealthyShape(Layer[] layersBaseToTip) {
        for (int i = 1; i < layersBaseToTip.length; i++) {
            // Each layer should have FEWER tests than the layer directly below it.
            if (layersBaseToTip[i].count() >= layersBaseToTip[i - 1].count()) {
                System.out.println("SHAPE VIOLATION: " + layersBaseToTip[i].name()
                        + " (" + layersBaseToTip[i].count() + ") is not smaller than "
                        + layersBaseToTip[i - 1].name() + " (" + layersBaseToTip[i - 1].count() + ")");
                return false;
            }
        }
        return true;
    }

    public static void main(String[] args) {
        Layer[] healthySuite = {
            new Layer("unit", 240), new Layer("integration", 40),
            new Layer("component", 20), new Layer("contract", 15), new Layer("e2e", 8)
        };
        System.out.println("Healthy suite shape OK: " + isHealthyShape(healthySuite));

        Layer[] invertedSuite = {
            new Layer("unit", 30), new Layer("integration", 25),
            new Layer("component", 20), new Layer("contract", 15), new Layer("e2e", 60)
        };
        System.out.println("Inverted suite shape OK: " + isHealthyShape(invertedSuite));
    }
}
```

How to run: `java PyramidShapeCheck.java`

`isHealthyShape` walks the layers from base to tip and checks that each layer is strictly smaller than the one beneath it — the structural definition of a pyramid. The `healthySuite` passes cleanly. The `invertedSuite` fails specifically because `e2e` (60) is larger than `contract` (15) — the ice-cream-cone pattern where a team has piled up end-to-end tests instead of pushing coverage down into cheaper layers.

### Level 3 — Advanced

```java
// File: PyramidCostEstimate.java -- the SAME two suites, now with a
// realistic per-test cost (in milliseconds) per layer, computing total
// suite runtime AND flagging both the shape violation and its cost impact --
// the production-flavored question: "why did our CI build get slow?"
public class PyramidCostEstimate {
    record Layer(String name, int count, int msPerTest) {
        long totalMs() { return (long) count * msPerTest; }
    }

    static void report(String label, Layer[] layersBaseToTip) {
        long totalMs = 0;
        boolean healthy = true;
        for (int i = 0; i < layersBaseToTip.length; i++) {
            Layer l = layersBaseToTip[i];
            totalMs += l.totalMs();
            if (i > 0 && l.count() >= layersBaseToTip[i - 1].count()) healthy = false;
            System.out.printf("  %-12s count=%-4d msPerTest=%-5d layerTotalMs=%d%n",
                    l.name(), l.count(), l.msPerTest(), l.totalMs());
        }
        System.out.println(label + " -> shape healthy=" + healthy
                + ", total suite runtime=" + totalMs + "ms (" + (totalMs / 1000.0) + "s)");
    }

    public static void main(String[] args) {
        // Realistic per-test costs: unit tests are near-free; each layer up gets
        // dramatically slower because it involves more real infrastructure.
        Layer[] healthySuite = {
            new Layer("unit", 240, 2),
            new Layer("integration", 40, 300),
            new Layer("component", 20, 800),
            new Layer("contract", 15, 150),
            new Layer("e2e", 8, 5000)
        };
        report("Healthy suite", healthySuite);

        // Same TOTAL test count (323), but shaped like an ice-cream cone:
        // most of the tests moved into the slow e2e layer.
        Layer[] invertedSuite = {
            new Layer("unit", 30, 2),
            new Layer("integration", 25, 300),
            new Layer("component", 20, 800),
            new Layer("contract", 15, 150),
            new Layer("e2e", 60, 5000)
        };
        report("Inverted suite", invertedSuite);
    }
}
```

How to run: `java PyramidCostEstimate.java`

Each `Layer` now carries a realistic `msPerTest` cost that grows sharply as you move toward the tip, because each higher layer involves progressively more real infrastructure: a unit test just runs code, an integration test starts a real database connection, a component test boots a whole service, and an end-to-end test coordinates several running services. `report` sums each layer's `count * msPerTest` into a total suite runtime and separately flags shape health, so the two problems — "is the shape wrong" and "is the suite slow" — are visible independently, and the example shows they are closely related: the same total test count (323) costs vastly different amounts of CI time purely because of *where* those tests live in the pyramid.

## 6. Walkthrough

Trace `PyramidCostEstimate.main` in order. **First**, `report("Healthy suite", healthySuite)` runs. It loops over the five layers base to tip. For `unit` (240 tests, 2ms each), `layerTotalMs` is 480ms — negligible. For `integration` (40 tests, 300ms each), `layerTotalMs` is 12,000ms. For `component` (20 tests, 800ms each), it's 16,000ms. For `contract` (15 tests, 150ms each), it's 2,250ms. For `e2e` (8 tests, 5000ms each), it's 40,000ms. The shape check passes at every step because each count is smaller than the one before it. Summed, `totalMs` comes to 480 + 12,000 + 16,000 + 2,250 + 40,000 = 70,730ms, roughly **71 seconds**.

**Next**, `report("Inverted suite", invertedSuite)` runs with the same total test count (323) but redistributed toward the tip. The shape check fails as soon as it compares `e2e` (60) against `contract` (15) — 60 is not smaller, so `healthy` becomes `false`. But the more striking number is the runtime: `unit` contributes only 60ms (30 tests are nearly free), `integration` contributes 7,500ms, `component` contributes 16,000ms, `contract` contributes 2,250ms, and `e2e` — now holding 60 tests instead of 8 — contributes 300,000ms on its own. **Then**, summing gives 60 + 7,500 + 16,000 + 2,250 + 300,000 = 325,810ms, roughly **326 seconds**, over **4.5 times slower** than the healthy suite, for the *same number of total tests*.

**Finally**, both `report` calls print their per-layer breakdown followed by the shape verdict and total runtime, making the cost of an inverted pyramid concrete rather than abstract.

```
Healthy suite:
  unit         count=240  msPerTest=2     layerTotalMs=480
  integration  count=40   msPerTest=300   layerTotalMs=12000
  component    count=20   msPerTest=800   layerTotalMs=16000
  contract     count=15   msPerTest=150   layerTotalMs=2250
  e2e          count=8    msPerTest=5000  layerTotalMs=40000
Healthy suite -> shape healthy=true, total suite runtime=70730ms (70.73s)

Inverted suite:
  unit         count=30   msPerTest=2     layerTotalMs=60
  integration  count=25   msPerTest=300   layerTotalMs=7500
  component    count=20   msPerTest=800   layerTotalMs=16000
  contract     count=15   msPerTest=150   layerTotalMs=2250
  e2e          count=60   msPerTest=5000  layerTotalMs=300000
Inverted suite -> shape healthy=false, total suite runtime=325810ms (325.81s)
```

## 7. Gotchas & takeaways

> Teams often "fix" a slow, flaky end-to-end suite by adding *more* end-to-end tests to cover edge cases they're afraid the existing ones miss. This makes the ice-cream cone worse, not better — each new edge case belongs in a fast unit test near the code that implements it, not in a slow test that has to boot the whole system to exercise one `if` branch.

- The pyramid is a proportion, not a mandate to skip any layer — unit, integration/component, contract, and end-to-end tests each catch mistakes the others structurally cannot.
- In microservices specifically, contract tests (see [contract testing](0415-contract-testing-consumer-driven-contracts.md)) let you catch cross-service breakage without paying for a full end-to-end run, which is why the pyramid gets an extra rung compared to a monolith's pyramid.
- Audit an existing suite by asking "how many tests live at each layer, and how long does each layer take in CI" — a slow build is almost always a shape problem before it's a hardware problem.
- Push coverage down: if an end-to-end test is the only thing exercising a particular business rule, that's a signal a [unit test](0412-unit-testing-services.md) or [component test](0414-component-testing-single-service-in-isolation.md) is missing, not that the end-to-end suite needs to grow.
- Keep the tip genuinely thin — a handful of end-to-end tests covering your most critical user journeys is far more valuable, and far more maintainable, than dozens trying to cover every edge case (see [end-to-end testing & its fragility](0417-end-to-end-testing-its-fragility.md)).
