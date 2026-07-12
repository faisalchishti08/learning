---
card: microservices
gi: 10
slug: infrastructure-automation
title: Infrastructure automation
---

## 1. What it is

**Infrastructure automation** is the Lewis & Fowler characteristic that says building, testing, and deploying a service should be a scripted, repeatable pipeline — not a set of manual steps a human runs by hand. In a system with many independently deployable services, manual deploys don't just scale poorly; they become the actual bottleneck that undermines every other benefit microservices are supposed to provide. If deploying one service still takes a human an afternoon of careful manual steps, having ten independently deployable services just means ten afternoons of risk instead of one.

## 2. Why & when

A single monolith can survive with a manual, careful, occasional deploy process — it happens rarely enough that care compensates for the lack of automation. Microservices flip that assumption: deploys become frequent, done by many different teams, on independent schedules, and every one of them risks a mistake if done by hand. Infrastructure automation — scripted builds, scripted tests, scripted deploys, scripted rollbacks — is what makes frequent, independent, low-risk releases actually possible.

Automate the pipeline as early as you introduce a second independently deployable service — the coordination cost of manual deploys grows with every service you add, and retrofitting automation onto an already-large fleet of manually-deployed services is far more painful than building it in from the second service onward.

## 3. Core concept

A pipeline is a sequence of automated stages, each of which can fail and stop the process before anything unsafe reaches production:

1. **Build** — compile the code into a deployable artifact.
2. **Test** — run automated checks against that artifact; a failure here must block the next stage.
3. **Deploy** — push the artifact to an environment, automatically, without manual file copying or manual configuration.
4. **Rollback** — if a deploy causes trouble, automatically (or with one command) revert to the previous known-good artifact.

The test for genuine infrastructure automation: can a new, unfamiliar team member deploy a service correctly on their first day, by running one command, without private knowledge of manual steps?

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An automated pipeline runs Build then Test then Deploy in sequence, with automatic rollback if a stage fails">
  <rect x="20" y="50" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Build</text>
  <rect x="180" y="50" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="240" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Test</text>
  <rect x="340" y="50" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="400" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Deploy</text>
  <rect x="500" y="50" width="120" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="560" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Rollback</text>

  <line x1="140" y1="75" x2="175" y2="75" stroke="#8b949e" marker-end="url(#a10)"/>
  <line x1="300" y1="75" x2="335" y2="75" stroke="#8b949e" marker-end="url(#a10)"/>
  <line x1="460" y1="75" x2="495" y2="75" stroke="#8b949e" marker-end="url(#a10)"/>
  <text x="400" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">any stage failing stops the pipeline, triggers rollback automatically</text>
  <defs><marker id="a10" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each stage gates the next; a failure at any point halts the pipeline before an unsafe artifact reaches production.

## 5. Runnable example

Scenario: deploying a service, first through hardcoded manual print-statement "steps," then as a real automated pipeline chaining stages, then with automatic rollback on deploy failure.

### Level 1 — Basic

```java
// File: ManualDeploy.java -- represents a HUMAN doing each step by hand
public class ManualDeploy {
    public static void main(String[] args) {
        System.out.println("Step 1 (manual): engineer runs `mvn package` on their laptop");
        System.out.println("Step 2 (manual): engineer manually SCPs the jar to the server");
        System.out.println("Step 3 (manual): engineer SSHes in and manually restarts the process");
        System.out.println("Deploy 'done' -- no automated verification that any step actually succeeded");
    }
}
```

**How to run:** `javac ManualDeploy.java && java ManualDeploy` (JDK 17+).

Expected output:
```
Step 1 (manual): engineer runs `mvn package` on their laptop
Step 2 (manual): engineer manually SCPs the jar to the server
Step 3 (manual): engineer SSHes in and manually restarts the process
Deploy 'done' -- no automated verification that any step actually succeeded
```

Nothing here is scripted or repeatable — it's a narration of manual steps. There's no automatic check that the build actually succeeded, that tests passed, or that the deployed process is actually healthy.

### Level 2 — Intermediate

```java
// File: AutomatedPipeline.java -- Build, Test, Deploy chained as automated
// stages; a failure at any stage halts the pipeline before it can continue.
import java.util.*;
import java.util.function.Supplier;

public class AutomatedPipeline {
    record StageResult(boolean success, String message) {}

    static StageResult build() {
        System.out.println("[build] compiling...");
        return new StageResult(true, "artifact built: service-1.0.jar");
    }

    static StageResult test(StageResult buildResult) {
        if (!buildResult.success()) return new StageResult(false, "skipped: build failed");
        System.out.println("[test] running automated test suite...");
        return new StageResult(true, "42 tests passed");
    }

    static StageResult deploy(StageResult testResult) {
        if (!testResult.success()) return new StageResult(false, "skipped: tests failed");
        System.out.println("[deploy] pushing artifact to production...");
        return new StageResult(true, "deployed and healthy");
    }

    public static void main(String[] args) {
        StageResult buildResult = build();
        System.out.println("build: " + buildResult.message());

        StageResult testResult = test(buildResult);
        System.out.println("test: " + testResult.message());

        StageResult deployResult = deploy(testResult);
        System.out.println("deploy: " + deployResult.message());
    }
}
```

**How to run:** `javac AutomatedPipeline.java && java AutomatedPipeline` (JDK 17+).

Expected output:
```
[build] compiling...
build: artifact built: service-1.0.jar
[test] running automated test suite...
test: 42 tests passed
[deploy] pushing artifact to production...
deploy: deployed and healthy
```

Each stage is now a function that both does its work and reports whether it succeeded; `test` and `deploy` each explicitly check the previous stage's result before proceeding. This is a real, if simplified, automated pipeline — one command drives all three stages in sequence.

### Level 3 — Advanced

```java
// File: PipelineWithRollback.java -- add AUTOMATIC rollback when deploy fails,
// so a bad release never sits in production waiting for a human to notice.
import java.util.*;

public class PipelineWithRollback {
    record StageResult(boolean success, String message) {}

    static String currentProductionVersion = "1.0"; // the last known-good version

    static StageResult build(String version) {
        System.out.println("[build] compiling version " + version + "...");
        return new StageResult(true, "artifact built: service-" + version + ".jar");
    }

    static StageResult test(StageResult buildResult) {
        if (!buildResult.success()) return new StageResult(false, "skipped: build failed");
        System.out.println("[test] running automated test suite...");
        return new StageResult(true, "tests passed");
    }

    static StageResult deploy(StageResult testResult, String version, boolean simulateHealthCheckFailure) {
        if (!testResult.success()) return new StageResult(false, "skipped: tests failed");
        System.out.println("[deploy] pushing version " + version + " to production...");
        if (simulateHealthCheckFailure) {
            System.out.println("[deploy] post-deploy health check FAILED for version " + version);
            return new StageResult(false, "deploy failed health check");
        }
        currentProductionVersion = version;
        return new StageResult(true, "deployed and healthy");
    }

    static void rollback() {
        System.out.println("[rollback] AUTOMATICALLY reverting to last known-good version: " + currentProductionVersion);
    }

    static void runPipeline(String version, boolean simulateHealthCheckFailure) {
        StageResult buildResult = build(version);
        StageResult testResult = test(buildResult);
        StageResult deployResult = deploy(testResult, version, simulateHealthCheckFailure);

        if (deployResult.success()) {
            System.out.println("Pipeline for " + version + ": SUCCESS -- now serving production traffic");
        } else {
            System.out.println("Pipeline for " + version + ": FAILED (" + deployResult.message() + ")");
            rollback(); // NO human needed to decide this -- the pipeline reacts automatically
        }
    }

    public static void main(String[] args) {
        runPipeline("1.1", false); // a healthy release
        System.out.println("---");
        runPipeline("1.2", true);  // a broken release -- health check fails, pipeline rolls back on its own
        System.out.println("production is now running version: " + currentProductionVersion);
    }
}
```

**How to run:** `javac PipelineWithRollback.java && java PipelineWithRollback` (JDK 17+).

Expected output:
```
[build] compiling version 1.1...
[test] running automated test suite...
[deploy] pushing version 1.1 to production...
Pipeline for 1.1: SUCCESS -- now serving production traffic
---
[build] compiling version 1.2...
[test] running automated test suite...
[deploy] pushing version 1.2 to production...
[deploy] post-deploy health check FAILED for version 1.2
Pipeline for 1.2: FAILED (deploy failed health check)
[rollback] AUTOMATICALLY reverting to last known-good version: 1.1
production is now running version: 1.1
```

The production-flavored hard case: version `1.2` builds and passes tests, but fails its post-deploy health check. `deploy` returns a failed `StageResult`, `runPipeline` detects that and calls `rollback()` **automatically** — no human had to notice a dashboard, page anyone, or manually run a rollback command. `currentProductionVersion` was never updated past `1.1`, so the final state correctly reflects that `1.1`, the last known-good version, is what's actually serving traffic.

## 6. Walkthrough

1. `runPipeline("1.2", true)` calls `build("1.2")` first, which prints its compiling message and returns a successful `StageResult` — the artifact itself is fine.
2. `test(buildResult)` runs next; since the build succeeded, it runs the (simulated) automated test suite and returns success too — the code compiles and passes its tests.
3. `deploy(testResult, "1.2", true)` runs the actual deploy step, printing `"pushing version 1.2 to production..."`, but because `simulateHealthCheckFailure` is `true`, it then simulates a post-deploy health check failing, prints that failure, and returns `new StageResult(false, "deploy failed health check")` — crucially, it does **not** update `currentProductionVersion`, so the "database of truth" for what's live in production never advances to `1.2`.
4. Back in `runPipeline`, `deployResult.success()` is `false`, so the `else` branch runs: it prints the failure message and calls `rollback()`.
5. `rollback()` prints a message reverting to `currentProductionVersion`, which is still `"1.1"` from the prior successful pipeline run — the rollback isn't really "moving backward," it's simply the fact that nothing ever moved forward past `1.1` in the first place, made explicit and visible.
6. The final `System.out.println` confirms `currentProductionVersion` is still `"1.1"` — proving the broken `1.2` release never became what customers actually experience, and no human had to intervene to make that true.

```
build(1.2) -> ok -> test(1.2) -> ok -> deploy(1.2) -> health check FAILS
                                                              |
                                                     currentProductionVersion stays "1.1"
                                                              |
                                                        rollback() logs it, no human paged
```

## 7. Gotchas & takeaways

> **Gotcha:** automating the *happy path* (build, test, deploy) without automating failure handling (rollback, alerting) only gets you halfway — a pipeline that automatically ships a broken build because no stage checks the *result* of deployment itself (not just whether the deploy command ran) can make bad releases worse, not better, by shipping them faster and with less human scrutiny.

- Infrastructure automation turns build, test, deploy, and rollback into a scripted, repeatable pipeline — not manual steps a human performs by hand.
- Each stage should gate the next: a build failure must prevent tests from running against a broken artifact, and a test failure must prevent a deploy from happening at all.
- Automatic rollback on deploy failure is what makes frequent, independent deploys genuinely safe — waiting for a human to notice a bad release and manually revert it is exactly the bottleneck automation is meant to remove.
- The concrete test for "is this automated": can an unfamiliar engineer deploy correctly on day one by running a single command, with no private manual knowledge required?
