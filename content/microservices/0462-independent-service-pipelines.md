---
card: microservices
gi: 462
slug: independent-service-pipelines
title: "Independent service pipelines"
---

## 1. What it is

**Independent service pipelines** means each microservice has its own complete [CI](0460-continuous-integration-per-service.md)-to-[CD](0461-continuous-delivery-deployment-pipelines.md) pipeline, end to end — build, test, staging deploy, staging checks, and production deploy — running and releasing on its own schedule, with no shared release train or synchronized release date binding it to any other service's pipeline.

## 2. Why & when

You want every service's pipeline to run and release independently because tying releases together destroys the core benefit microservices are supposed to provide:

- **A shared release train forces every service to wait for the slowest one.** If ten services all release together on a fixed schedule, one service's bug or one team's delay blocks the other nine from shipping anything, even work that's fully done and tested.
- **Deployment frequency should match a service's own pace of change**, not an artificial calendar. A service under active development might deploy many times a day; a stable, rarely-touched service might deploy once a month — forcing them onto the same cadence wastes effort in one direction or the other.
- **Team autonomy requires it.** A team that owns a service end-to-end, including its pipeline, can decide *when* to release without coordinating a cross-team release meeting first — that's the organizational payoff of [independent deployability](0013-independent-deployability.md), not just a technical nicety.
- **You need this as soon as more than one team owns more than one service** — a coordinated, synchronized release process is exactly the kind of cross-team dependency microservices architecture exists to eliminate.

## 3. Core concept

Think of a set of restaurants under the same parent company: each restaurant has its own kitchen, its own staff schedule, and decides on its own when to update its menu — one restaurant refreshing its menu on a Tuesday has zero effect on whether another restaurant, three blocks away, updates its own menu that same day or a month later. They share a brand, not a release calendar.

Concretely:

1. **Each service's pipeline is triggered independently** — usually by a commit to that service's own code, as established by [CI per service](0460-continuous-integration-per-service.md).
2. **Each service's pipeline runs its own staging deploy and checks**, against its own staging environment or its own slice of a shared one.
3. **Each service's pipeline decides independently whether it's ready to release** — its own tests, its own approval gate (if using continuous delivery), its own timing.
4. **Production deployment for one service happens without waiting for, or blocking, any other service's production deployment** — two services can deploy to production in the same hour, the same minute, or weeks apart, and neither situation requires any special coordination.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three services each run their own complete pipeline on their own independent timeline, with no shared release date">
  <rect x="10" y="20" width="640" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="30" y="50" fill="#e6edf3" font-size="10" font-family="sans-serif">order-service:  build -&gt; test -&gt; staging -&gt; deploy (Tue 9am)</text>

  <rect x="10" y="85" width="640" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="30" y="115" fill="#e6edf3" font-size="10" font-family="sans-serif">inventory-service:  build -&gt; test -&gt; staging -&gt; deploy (Tue 4pm, same day)</text>

  <rect x="10" y="150" width="640" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="30" y="180" fill="#e6edf3" font-size="10" font-family="sans-serif">payment-service:  build -&gt; test -&gt; staging -&gt; deploy (Thursday, two days later)</text>

  <text x="330" y="205" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no shared release date -- each pipeline runs on its own schedule</text>
</svg>

Each service's pipeline runs to completion and deploys on its own timeline, with no synchronized release date across services.

## 5. Runnable example

Scenario: a small scheduler simulating three services each deploying on their own independent schedule. We start with two services deploying on unrelated days, extend it to show many commits per service triggering many independent pipeline runs, then handle the hard case: one service's pipeline being mid-run when another service needs to deploy, proving neither blocks the other.

### Level 1 — Basic

```java
// File: IndependentPipelinesBasic.java -- models TWO services, each
// completing its OWN pipeline on its OWN schedule, with no shared release
// date connecting them.
public class IndependentPipelinesBasic {
    static void runFullPipeline(String serviceName, String releaseDay) {
        System.out.println("[" + serviceName + "] build -> test -> staging -> checks -> deploy");
        System.out.println("[" + serviceName + "] released on " + releaseDay + " -- independent of any other service");
    }

    public static void main(String[] args) {
        runFullPipeline("order-service", "Tuesday");
        runFullPipeline("payment-service", "Thursday");
        // Neither pipeline call above waited for, or referenced, the other.
    }
}
```

How to run: `java IndependentPipelinesBasic.java`

`runFullPipeline` is called twice with entirely different `releaseDay` values, and neither call reads any state produced by the other — there's no shared variable, no synchronization, no dependency between the two calls at all, which is exactly the property independent pipelines require.

### Level 2 — Intermediate

```java
// File: IndependentPipelinesMultipleCommits.java -- the SAME independent
// scheduling, now with EACH service deploying MULTIPLE times at its own
// pace -- order-service deploys three times in a week, payment-service
// deploys once, and the counts have nothing to do with each other.
import java.util.*;

public class IndependentPipelinesMultipleCommits {
    static void runFullPipeline(String serviceName, String commitId, String releaseDay) {
        System.out.println("[" + serviceName + "] commit " + commitId + " -> build -> test -> staging -> deploy on " + releaseDay);
    }

    public static void main(String[] args) {
        List<String[]> orderServiceCommits = List.of(
            new String[]{"a1b2c3", "Monday"},
            new String[]{"d4e5f6", "Tuesday"},
            new String[]{"g7h8i9", "Thursday"}
        );
        List<String[]> paymentServiceCommits = List.<String[]>of(
            new String[]{"x1y2z3", "Wednesday"}
        );

        for (String[] commit : orderServiceCommits) {
            runFullPipeline("order-service", commit[0], commit[1]);
        }
        for (String[] commit : paymentServiceCommits) {
            runFullPipeline("payment-service", commit[0], commit[1]);
        }
        System.out.println("[summary] order-service deployed " + orderServiceCommits.size()
                + " times, payment-service deployed " + paymentServiceCommits.size() + " time -- unrelated cadences");
    }
}
```

How to run: `java IndependentPipelinesMultipleCommits.java`

`orderServiceCommits` and `paymentServiceCommits` are separate lists of separate sizes, iterated by two completely separate loops. `order-service` runs its pipeline three times across the week while `payment-service` runs once — the loop for one list never reads from, waits on, or is triggered by anything in the other, modeling that deployment frequency is entirely a per-service property.

### Level 3 — Advanced

```java
// File: IndependentPipelinesConcurrent.java -- the SAME independent
// pipelines, now handling the PRODUCTION-FLAVORED hard case: two
// services' pipelines running literally AT THE SAME TIME, on separate
// threads, proving that one being mid-flight (e.g. slow staging checks)
// has NO effect on the other completing and deploying.
public class IndependentPipelinesConcurrent {
    static void runFullPipeline(String serviceName, long stagingCheckDurationMs) throws InterruptedException {
        System.out.println("[" + serviceName + "] build -> test -> deploying to staging");
        System.out.println("[" + serviceName + "] running staging checks (" + stagingCheckDurationMs + "ms)...");
        Thread.sleep(stagingCheckDurationMs); // simulates a slow or fast staging check
        System.out.println("[" + serviceName + "] staging checks passed -> deploying to production");
        System.out.println("[" + serviceName + "] LIVE in production");
    }

    public static void main(String[] args) throws InterruptedException {
        // order-service has a slow, thorough staging check; payment-service is fast.
        Thread orderServiceThread = new Thread(() -> {
            try { runFullPipeline("order-service", 150); } catch (InterruptedException ignored) {}
        });
        Thread paymentServiceThread = new Thread(() -> {
            try { runFullPipeline("payment-service", 20); } catch (InterruptedException ignored) {}
        });

        orderServiceThread.start();
        paymentServiceThread.start();

        orderServiceThread.join();
        paymentServiceThread.join();
        System.out.println("[summary] both pipelines finished -- payment-service reached production well before order-service, with no coordination required");
    }
}
```

How to run: `java IndependentPipelinesConcurrent.java`

`order-service`'s pipeline sleeps `150ms` to simulate a slower, more thorough staging check, while `payment-service`'s sleeps only `20ms`. Both run on separate `Thread` objects started back to back, so they execute concurrently rather than one waiting for the other — `payment-service` reaches "LIVE in production" while `order-service` is still mid-sleep in its own staging check, and neither thread's code references the other's state at all. `join()` on both simply waits for each to individually finish; it does not synchronize them with each other.

## 6. Walkthrough

Trace `IndependentPipelinesConcurrent.main` in order. **First**, two `Thread` objects are created, each wrapping a call to `runFullPipeline` with different service names and different `stagingCheckDurationMs` values — at this point neither thread has started running yet.

**Next**, `orderServiceThread.start()` and `paymentServiceThread.start()` run back to back. Both threads begin executing concurrently: `order-service` prints its "deploying to staging" and "running staging checks (150ms)" lines, and immediately after (on the other thread, not sequentially after), `payment-service` prints its own equivalent lines with `20ms`.

**Then**, because `payment-service`'s sleep is far shorter, its thread wakes up first — around the 20ms mark — and prints "staging checks passed" followed by "LIVE in production," while `order-service`'s thread is still sleeping through its own 150ms staging check, having made no progress in the meantime.

**After that**, around the 150ms mark, `order-service`'s thread finally wakes up and prints its own "staging checks passed" and "LIVE in production" lines — arriving in production noticeably later than `payment-service`, but that lateness had zero effect on `payment-service`, which had already finished and moved on.

**Finally**, `main`'s two `join()` calls block until both threads have completed (in whatever order they actually finish), and the summary line prints once both are done, confirming that the two pipelines ran to completion independently and finished at different times with no coordination between them.

```
[order-service] build -> test -> deploying to staging
[order-service] running staging checks (150ms)...
[payment-service] build -> test -> deploying to staging
[payment-service] running staging checks (20ms)...
[payment-service] staging checks passed -> deploying to production
[payment-service] LIVE in production
[order-service] staging checks passed -> deploying to production
[order-service] LIVE in production
[summary] both pipelines finished -- payment-service reached production well before order-service, with no coordination required
```

(Exact interleaving of the first four lines can vary slightly run to run, since both threads start almost simultaneously — but `payment-service` always reaches production before `order-service` given its shorter sleep.)

## 7. Gotchas & takeaways

> A "release train" that batches several services' changes into one synchronized deployment event reintroduces the exact coordination cost microservices are meant to remove — a single slow or broken service on the train can delay every other service's already-tested, already-ready release.
- Independent pipelines require independent [CI](0460-continuous-integration-per-service.md) as a foundation — you can't deploy independently what you can't already build and test independently.
- Deployment frequency is a per-service property, not a system-wide one; a service that changes rarely deploying rarely is not a problem to fix, it's the pipeline working correctly.
- Running pipelines concurrently (as in Level 3) is the normal case at any real scale — pipelines should be written assuming they may execute at the same time as any other service's pipeline, with no shared mutable state between them.
- Independent pipelines don't eliminate the need for cross-service compatibility checks (contract tests, API versioning) — they just mean those checks happen without forcing every service onto the same release calendar.
- The organizational payoff matters as much as the technical one: a team that can release the instant their own pipeline is green, without waiting on a shared schedule or another team's sign-off, is genuinely autonomous.
