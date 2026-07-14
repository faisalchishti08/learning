---
card: microservices
gi: 460
slug: continuous-integration-per-service
title: "Continuous integration per service"
---

## 1. What it is

**Continuous integration (CI) per service** means each microservice has its **own** CI pipeline — its own build, its own test suite, its own trigger — completely independent of every other service's pipeline. Committing to `order-service` runs only `order-service`'s CI; it does not build, test, or block on `inventory-service` or any other service in the system.

## 2. Why & when

You set up CI per service, rather than one shared CI pipeline for the whole system, because a single microservice's whole point is [independent deployability](0013-independent-deployability.md):

- **A shared, monolithic CI pipeline recreates monolith coupling at the build level.** If every commit to any service triggers a build-and-test of the *entire* system, teams are back to waiting on each other's code, exactly the coordination cost microservices were meant to remove.
- **Fast feedback requires a small, relevant test scope.** A CI run that only builds and tests the one service that actually changed finishes in minutes, not the hours a full-system build-and-test might take — and developers get feedback while the change is still fresh in their head.
- **Team autonomy depends on it.** A team owning one service should be able to change its language version, test framework, or build tool without needing sign-off from, or coordination with, every other team — which is only possible if each service's CI pipeline is genuinely separate.
- **You need it from day one of any real microservice system** — as soon as there's more than one service with more than one team touching it, a shared pipeline becomes the bottleneck that independent deployability was supposed to eliminate.

## 3. Core concept

Think of a shopping mall where each store manages its own inventory, staffing, and hours, rather than the entire mall opening and closing as one unit whenever any single store has a problem. Each store's operations are self-contained; a delay at one store doesn't stop customers from shopping at any other.

Concretely, CI per service means:

1. **Each service lives in its own repository (or a clearly isolated path in a monorepo)**, with its own CI configuration file.
2. **A commit to that path triggers exactly that service's pipeline** — checkout, build, run its own unit and component tests, produce its own build artifact.
3. **The pipeline's pass/fail status only reflects that one service.** A red build for `order-service` says nothing about whether `inventory-service`'s code is healthy.
4. **Nothing about another service's pipeline running, or failing, blocks this one from running.** Two teams can commit to two different services in the same minute and get two completely independent, parallel CI results.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each service has its own independent CI pipeline; a commit to one service triggers only that service's build and tests">
  <rect x="20" y="30" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">order-service commit</text>

  <rect x="20" y="150" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="180" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">inventory-service commit</text>

  <rect x="280" y="30" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">order-service CI</text>
  <text x="370" y="71" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">build + test only order-service</text>

  <rect x="280" y="150" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="175" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">inventory-service CI</text>
  <text x="370" y="191" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">build + test only inventory-service</text>

  <line x1="200" y1="55" x2="280" y2="55" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="200" y1="175" x2="280" y2="175" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="530" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" transform="rotate(90 530 115)">no dependency</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Two independent commits trigger two independent pipelines that run in parallel, with no shared build or shared pass/fail status.

## 5. Runnable example

Scenario: a small CI dispatcher that decides which service's pipeline to run based on which service's code changed. We start with a basic single-service trigger, extend it to correctly isolate pipelines for multiple, simultaneously-changed services, then handle the hard case: one service's pipeline failing must not stop, delay, or affect any other service's pipeline result.

### Level 1 — Basic

```java
// File: CiPerServiceBasic.java -- models a commit to ONE service
// triggering ONLY that service's own build-and-test pipeline.
public class CiPerServiceBasic {
    static void runPipelineFor(String serviceName) {
        System.out.println("[CI] " + serviceName + ": checking out code");
        System.out.println("[CI] " + serviceName + ": running build");
        System.out.println("[CI] " + serviceName + ": running unit + component tests");
        System.out.println("[CI] " + serviceName + ": PASSED -- artifact produced");
    }

    public static void main(String[] args) {
        String changedService = "order-service";
        System.out.println("[trigger] commit detected in " + changedService);
        runPipelineFor(changedService);
        // Note: inventory-service, payment-service, etc. are NOT touched at all.
    }
}
```

How to run: `java CiPerServiceBasic.java`

`runPipelineFor` represents one service's complete, self-contained pipeline. `main` only calls it for `changedService` — no other service's name ever appears, modeling the core guarantee that a commit to one service's code triggers exactly one pipeline.

### Level 2 — Intermediate

```java
// File: CiPerServiceMultiple.java -- the SAME per-service dispatch, now
// handling MULTIPLE services changing at once (e.g. two different teams
// committing around the same time). Each gets its OWN pipeline run,
// completely isolated from the other's build and test results.
import java.util.*;

public class CiPerServiceMultiple {
    static boolean runPipelineFor(String serviceName, boolean testsShouldPass) {
        System.out.println("[CI] " + serviceName + ": checking out code");
        System.out.println("[CI] " + serviceName + ": running build");
        System.out.println("[CI] " + serviceName + ": running unit + component tests");
        if (testsShouldPass) {
            System.out.println("[CI] " + serviceName + ": PASSED -- artifact produced");
        } else {
            System.out.println("[CI] " + serviceName + ": FAILED -- artifact NOT produced");
        }
        return testsShouldPass;
    }

    public static void main(String[] args) {
        // Two independent commits land around the same time.
        Map<String, Boolean> changedServices = new LinkedHashMap<>();
        changedServices.put("order-service", true);
        changedServices.put("inventory-service", true);

        Map<String, Boolean> results = new LinkedHashMap<>();
        for (Map.Entry<String, Boolean> entry : changedServices.entrySet()) {
            results.put(entry.getKey(), runPipelineFor(entry.getKey(), entry.getValue()));
        }
        System.out.println("[dashboard] results: " + results);
    }
}
```

How to run: `java CiPerServiceMultiple.java`

`changedServices` models two commits landing close together, and the loop runs `runPipelineFor` separately for each — nothing about `order-service`'s pipeline call affects the arguments or execution of `inventory-service`'s. `results` collects each pipeline's own outcome independently, which is exactly what an isolated per-service dashboard would show.

### Level 3 — Advanced

```java
// File: CiPerServiceIsolatedFailure.java -- the SAME multi-service
// dispatch, now handling the PRODUCTION-FLAVORED hard case: ONE service's
// pipeline FAILS. A shared, monolithic pipeline would stop the whole
// build; per-service CI must let every OTHER service's pipeline run to
// completion and report its own result, completely unaffected.
import java.util.*;

public class CiPerServiceIsolatedFailure {
    static boolean runPipelineFor(String serviceName, boolean testsShouldPass) {
        System.out.println("[CI] " + serviceName + ": checking out code");
        System.out.println("[CI] " + serviceName + ": running build");
        try {
            System.out.println("[CI] " + serviceName + ": running unit + component tests");
            if (!testsShouldPass) {
                throw new RuntimeException("2 tests failed in " + serviceName);
            }
            System.out.println("[CI] " + serviceName + ": PASSED -- artifact produced");
            return true;
        } catch (RuntimeException e) {
            System.out.println("[CI] " + serviceName + ": FAILED (" + e.getMessage() + ") -- artifact NOT produced");
            return false;
        }
    }

    public static void main(String[] args) {
        Map<String, Boolean> changedServices = new LinkedHashMap<>();
        changedServices.put("order-service", true);
        changedServices.put("inventory-service", false); // this one has a broken test
        changedServices.put("payment-service", true);

        Map<String, Boolean> results = new LinkedHashMap<>();
        for (Map.Entry<String, Boolean> entry : changedServices.entrySet()) {
            // Each pipeline runs regardless of any other pipeline's outcome so far.
            boolean passed = runPipelineFor(entry.getKey(), entry.getValue());
            results.put(entry.getKey(), passed);
        }

        System.out.println("[dashboard] final results: " + results);
        long passedCount = results.values().stream().filter(Boolean::booleanValue).count();
        System.out.println("[dashboard] " + passedCount + "/" + results.size() + " services passed independently");
    }
}
```

How to run: `java CiPerServiceIsolatedFailure.java`

`inventory-service` is marked to fail its tests. `runPipelineFor` catches its own `RuntimeException` internally and returns `false` rather than letting the exception propagate out of the loop in `main` — so `payment-service`, listed right after it in `changedServices`, still runs its full pipeline in the very next loop iteration and passes normally. The final `results` map shows one failure sitting right next to two successes, with no relationship between them.

## 6. Walkthrough

Trace `CiPerServiceIsolatedFailure.main` in order. **First**, `changedServices` is built as an ordered map of three services, with `inventory-service` deliberately set to fail.

**Next**, the loop's first iteration calls `runPipelineFor("order-service", true)`. It checks out, builds, runs tests, hits no exception since `testsShouldPass` is `true`, prints "PASSED," and returns `true`. `results` now holds `order-service -> true`.

**Then**, the loop's second iteration calls `runPipelineFor("inventory-service", false)`. It checks out and builds identically, but inside the `try` block the `if (!testsShouldPass)` check is `true`, so a `RuntimeException` is thrown. The `catch` block inside `runPipelineFor` itself handles it — prints the "FAILED" line — and returns `false`. Critically, this exception never reaches `main`'s loop at all; the loop simply receives `false` as an ordinary return value and continues.

**After that**, the loop's third iteration calls `runPipelineFor("payment-service", true)`, completely unaffected by what happened to `inventory-service` one iteration earlier — it runs its full pipeline and passes, exactly as if `inventory-service` didn't exist.

**Finally**, after the loop completes, `results` holds all three outcomes, and the dashboard summary line reports `2/3` passed — visually and functionally isolating the one real failure from the two successful, independent pipeline runs.

```
[CI] order-service: checking out code
[CI] order-service: running build
[CI] order-service: running unit + component tests
[CI] order-service: PASSED -- artifact produced
[CI] inventory-service: checking out code
[CI] inventory-service: running build
[CI] inventory-service: running unit + component tests
[CI] inventory-service: FAILED (2 tests failed in inventory-service) -- artifact NOT produced
[CI] payment-service: checking out code
[CI] payment-service: running build
[CI] payment-service: running unit + component tests
[CI] payment-service: PASSED -- artifact produced
[dashboard] final results: {order-service=true, inventory-service=false, payment-service=true}
[dashboard] 2/3 services passed independently
```

## 7. Gotchas & takeaways

> A single shared CI pipeline that builds and tests every service together quietly reintroduces monolith-style coupling at the build level — a broken test in one service now blocks a release-ready change in a completely unrelated service, exactly the friction independent deployability is meant to remove.
- CI per service is a *prerequisite* for [continuous delivery / deployment pipelines](0461-continuous-delivery-deployment-pipelines.md) further down the pipeline — you cannot deploy services independently if you can't even build and test them independently first.
- Path-based or repository-based triggers (only run this pipeline when files under this service's path change) are the mechanical way most CI systems implement per-service isolation in a monorepo.
- Isolation should extend to test failures, not just triggers: one service's failing pipeline must never block, delay, or appear in another service's pipeline status.
- Per-service CI does not mean *no* cross-service testing exists — [contract tests](0025-fallacies-of-distributed-computing-network-reliable-latency.md) and integration tests still verify services work together, but they run as their own separate, appropriately-scoped checks, not as part of forcing every service's CI into one shared pipeline.
- Fast, isolated feedback is the whole point: a developer changing `order-service` should see their own service's CI result in minutes, without waiting on, or being blocked by, work happening in any other service's codebase.
