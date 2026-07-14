---
card: microservices
gi: 461
slug: continuous-delivery-deployment-pipelines
title: "Continuous delivery / deployment pipelines"
---

## 1. What it is

A **continuous delivery (CD) pipeline** takes a build artifact that already passed [CI](0460-continuous-integration-per-service.md) and moves it through a series of environments — typically staging, then production — running further checks at each stage, so that the artifact is **always in a releasable state**. **Continuous deployment** is the further step where a passing pipeline automatically releases to production with no manual approval gate; continuous delivery stops one step short, requiring an explicit human decision to release.

## 2. Why & when

You build a CD pipeline once CI is producing trustworthy artifacts, because getting code merged is not the same as getting it safely running in front of users:

- **CI proves the code builds and its own tests pass; it doesn't prove the artifact behaves correctly in a realistic environment.** A CD pipeline adds stages — deploying to staging, running integration or smoke tests against a running instance — that CI alone can't cover.
- **Manual, ad-hoc releases are slow and error-prone.** A defined pipeline turns "get this into production" from a checklist someone might forget a step of into a repeatable, automated sequence that runs the same way every time.
- **You want every passing artifact to be releasable at any moment**, even if you choose not to release it immediately — that's the actual definition of continuous *delivery*: always ready, release is a business decision, not an engineering bottleneck.
- **Continuous deployment (no manual gate) fits when you have strong enough automated testing and monitoring to trust a pipeline's green light completely** — for early-stage services, regulated environments, or high-blast-radius changes, keeping a manual approval gate (continuous delivery, not deployment) is often the safer choice.

## 3. Core concept

Think of an assembly line with quality-control checkpoints: a part that fails inspection at any station is pulled off the line right there — it never reaches the next station, let alone the customer. A part that passes every checkpoint reaches the end of the line ready to ship; whether it actually ships that day is a separate decision from whether it *could*.

Concretely, a pipeline is a sequence of stages:

1. **Artifact intake.** The pipeline starts with the versioned build artifact CI already produced and tested — it does not rebuild from source at this point, it takes the same artifact forward.
2. **Deploy to staging.** The artifact is deployed to an environment that mirrors production as closely as practical.
3. **Run further checks.** Integration tests, smoke tests, and sometimes performance or security checks run against the actual running staging deployment — verifying things CI's unit-level tests can't.
4. **Gate.** If every check passes, the artifact is now proven releasable. From here, continuous delivery stops and waits for a human to trigger the production release; continuous deployment proceeds automatically.
5. **Deploy to production.** The same artifact — never rebuilt, never modified — is deployed using whatever strategy the team has chosen (e.g. a [rolling deployment](0450-rolling-deployment.md)).

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A pipeline moves one build artifact through staging checks and then to production, with an optional manual approval gate between delivery and deployment">
  <rect x="10" y="80" width="120" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CI artifact</text>

  <rect x="170" y="80" width="120" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="230" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">staging</text>
  <text x="230" y="121" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">integration checks</text>

  <rect x="330" y="80" width="140" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="4,2"/>
  <text x="400" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">gate</text>
  <text x="400" y="121" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">manual (delivery) or auto (deployment)</text>

  <rect x="510" y="80" width="150" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="585" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">production</text>
  <text x="585" y="121" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">same artifact deployed</text>

  <line x1="130" y1="107" x2="170" y2="107" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="290" y1="107" x2="330" y2="107" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="470" y1="107" x2="510" y2="107" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="335" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the SAME artifact moves through every stage -- never rebuilt from source</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The same build artifact flows through staging checks, an optional gate, and into production — continuous delivery stops at the gate; continuous deployment crosses it automatically.

## 5. Runnable example

Scenario: a pipeline moving one artifact through staging checks toward production. We start with a basic linear pipeline, extend it with a manual approval gate (continuous delivery), then handle the hard case: a staging check failing partway through, which must halt the pipeline before production is ever touched.

### Level 1 — Basic

```java
// File: PipelineBasic.java -- models ONE artifact moving through a
// LINEAR pipeline: build intake, staging deploy, staging checks,
// production deploy. No branching, everything succeeds.
public class PipelineBasic {
    static void deployTo(String environment, String artifactVersion) {
        System.out.println("[pipeline] deploying " + artifactVersion + " to " + environment);
    }

    static boolean runStagingChecks(String artifactVersion) {
        System.out.println("[pipeline] running integration checks against " + artifactVersion + " in staging");
        System.out.println("[pipeline] all staging checks PASSED");
        return true;
    }

    public static void main(String[] args) {
        String artifactVersion = "order-service:1.4.2";
        System.out.println("[pipeline] intake: " + artifactVersion + " (already built and unit-tested by CI)");

        deployTo("staging", artifactVersion);
        boolean stagingPassed = runStagingChecks(artifactVersion);

        if (stagingPassed) {
            deployTo("production", artifactVersion);
            System.out.println("[pipeline] " + artifactVersion + " is now live in production");
        }
    }
}
```

How to run: `java PipelineBasic.java`

`artifactVersion` is treated as a single, immutable value passed unchanged into every stage — `deployTo("staging", ...)` and `deployTo("production", ...)` both receive the exact same string, modeling the rule that a pipeline never rebuilds the artifact between stages, it only moves the same one forward.

### Level 2 — Intermediate

```java
// File: PipelineWithGate.java -- the SAME linear pipeline, now with a
// MANUAL APPROVAL GATE between a passing staging run and the production
// deploy -- modeling continuous DELIVERY (always releasable, release is
// a human decision) rather than continuous DEPLOYMENT (fully automatic).
public class PipelineWithGate {
    static void deployTo(String environment, String artifactVersion) {
        System.out.println("[pipeline] deploying " + artifactVersion + " to " + environment);
    }

    static boolean runStagingChecks(String artifactVersion) {
        System.out.println("[pipeline] running integration checks against " + artifactVersion + " in staging");
        System.out.println("[pipeline] all staging checks PASSED");
        return true;
    }

    // Models a human clicking "approve" -- separate from any automated check.
    static boolean waitForManualApproval(String artifactVersion) {
        System.out.println("[pipeline] " + artifactVersion + " is RELEASABLE -- awaiting manual approval to deploy");
        boolean approved = true; // stands in for a real human decision
        System.out.println("[pipeline] release manager approved: " + approved);
        return approved;
    }

    public static void main(String[] args) {
        String artifactVersion = "order-service:1.4.2";
        deployTo("staging", artifactVersion);

        if (!runStagingChecks(artifactVersion)) {
            System.out.println("[pipeline] staging checks failed -- pipeline halts, gate never reached");
            return;
        }

        if (waitForManualApproval(artifactVersion)) {
            deployTo("production", artifactVersion);
            System.out.println("[pipeline] " + artifactVersion + " is now live in production");
        } else {
            System.out.println("[pipeline] release manager declined -- artifact stays releasable but undeployed");
        }
    }
}
```

How to run: `java PipelineWithGate.java`

`waitForManualApproval` sits strictly between a passing `runStagingChecks` and the production `deployTo` call — it is a distinct decision point that a fully automated continuous-*deployment* pipeline simply wouldn't have. The artifact being "releasable" (staging passed) and "released" (approval given, then deployed) are modeled as two separate, sequential conditions.

### Level 3 — Advanced

```java
// File: PipelineHaltOnFailure.java -- the SAME gated pipeline, now
// handling the PRODUCTION-FLAVORED hard case: a STAGING CHECK FAILS. The
// pipeline must halt immediately -- production must never be touched, the
// approval gate must never even be reached, and the failure must be
// reported clearly enough for a team to act on it.
public class PipelineHaltOnFailure {
    static void deployTo(String environment, String artifactVersion) {
        System.out.println("[pipeline] deploying " + artifactVersion + " to " + environment);
    }

    // Simulates a specific integration test failing in staging.
    static boolean runStagingChecks(String artifactVersion) {
        System.out.println("[pipeline] running integration checks against " + artifactVersion + " in staging");
        boolean paymentIntegrationOk = false; // simulated real failure
        boolean inventoryIntegrationOk = true;
        if (!paymentIntegrationOk) {
            System.out.println("[pipeline] FAILED: payment-service integration check did not respond as expected");
        }
        if (!inventoryIntegrationOk) {
            System.out.println("[pipeline] FAILED: inventory-service integration check did not respond as expected");
        }
        return paymentIntegrationOk && inventoryIntegrationOk;
    }

    static boolean waitForManualApproval(String artifactVersion) {
        System.out.println("[pipeline] " + artifactVersion + " is RELEASABLE -- awaiting manual approval to deploy");
        return true;
    }

    public static void main(String[] args) {
        String artifactVersion = "order-service:1.4.3";
        deployTo("staging", artifactVersion);

        boolean stagingPassed = runStagingChecks(artifactVersion);
        if (!stagingPassed) {
            System.out.println("[pipeline] HALTED after staging: " + artifactVersion
                    + " will NOT reach the approval gate or production until the failing checks are fixed and re-run");
            return; // production deployTo is never reached
        }

        if (waitForManualApproval(artifactVersion)) {
            deployTo("production", artifactVersion);
            System.out.println("[pipeline] " + artifactVersion + " is now live in production");
        }
    }
}
```

How to run: `java PipelineHaltOnFailure.java`

`runStagingChecks` now models two independent integration checks, one of which (`paymentIntegrationOk`) is `false`. The method still runs and reports on both checks — so a team gets full diagnostic detail on every failure, not just the first one — but returns `false` overall since both checks must pass. Back in `main`, the `if (!stagingPassed)` branch returns out of `main` entirely: `waitForManualApproval` and the production `deployTo` call are both dead code for this run, never executed, exactly like a real pipeline stopping cold at a failed stage.

## 6. Walkthrough

Trace `PipelineHaltOnFailure.main` in order. **First**, `deployTo("staging", artifactVersion)` runs and prints the staging deployment line — this always happens, since staging deployment is what makes the checks possible in the first place.

**Next**, `runStagingChecks(artifactVersion)` runs. Inside it, `paymentIntegrationOk` is `false` and `inventoryIntegrationOk` is `true`. The first `if` prints the payment failure message; the second `if` is skipped since `inventoryIntegrationOk` is `true`. The method returns `paymentIntegrationOk && inventoryIntegrationOk`, which evaluates to `false` because one operand is `false`.

**Then**, back in `main`, `stagingPassed` holds `false`, so `if (!stagingPassed)` is `true`. The halt message prints, naming the artifact and explaining that neither the approval gate nor production will be reached until the failure is fixed.

**After that**, `return;` exits `main` immediately. `waitForManualApproval` is never called, and the production `deployTo` call is never reached — no line for it appears in the output at all, which is exactly the guarantee a CD pipeline is supposed to provide: a bad artifact simply cannot reach production through the normal path.

**Finally**, the program terminates having deployed to staging only, with a clear, actionable failure message and zero risk of the broken artifact having touched production.

```
[pipeline] deploying order-service:1.4.3 to staging
[pipeline] running integration checks against order-service:1.4.3 in staging
[pipeline] FAILED: payment-service integration check did not respond as expected
[pipeline] HALTED after staging: order-service:1.4.3 will NOT reach the approval gate or production until the failing checks are fixed and re-run
```

## 7. Gotchas & takeaways

> A pipeline that rebuilds the artifact at the production stage — instead of reusing the exact artifact that passed staging — breaks the entire guarantee of the pipeline: you're no longer deploying the thing you tested, you're deploying a fresh, unverified build that merely shares the same source commit. Always promote one immutable artifact through every stage.
- Continuous delivery and continuous deployment differ only at the gate: delivery stops for a human decision, deployment proceeds automatically — both require the same underlying pipeline discipline.
- A pipeline should halt hard and loud on any failing stage; letting a later stage run anyway (or silently skipping a failed check) defeats the purpose of having stages at all.
- [Independent service pipelines](0462-independent-service-pipelines.md) and [CI per service](0460-continuous-integration-per-service.md) are prerequisites — you can't have each service delivering independently if the CD pipeline itself is shared and coupled across services.
- Staging should mirror production closely enough that checks passing there is meaningful evidence, not just a formality on the way to a deploy that was going to happen anyway.
- The riskier or more regulated a service is, the stronger the case for keeping continuous *delivery*'s manual gate rather than moving to full continuous *deployment* — the pipeline mechanics stay identical either way.
