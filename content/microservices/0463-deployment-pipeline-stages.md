---
card: microservices
gi: 463
slug: deployment-pipeline-stages
title: "Deployment pipeline stages"
---

## 1. What it is

**Deployment pipeline stages** are the ordered, named steps a build artifact passes through on its way from source code to running in production — typically something like *build → unit test → package → deploy-to-staging → integration test → deploy-to-production* — where each stage has a clear pass/fail outcome, and an artifact only advances to the next stage if the current one passes.

## 2. Why & when

You break a pipeline into explicit, named stages rather than one undifferentiated "build and ship it" script because stages give you control, visibility, and fast failure:

- **Fast failure needs cheap checks first.** A stage ordering that runs a two-minute unit-test suite before a twenty-minute integration-test suite catches most bugs cheaply — you don't want to wait twenty minutes to learn a unit test failed.
- **Each stage answers a different question**, and mixing them together makes failures ambiguous. "Does it compile" (build), "does the logic work in isolation" (unit test), "does it work with real dependencies" (integration test), and "does it work as a running deployment" (staging) are genuinely different questions that deserve genuinely different, separately-reportable stages.
- **You need clear failure attribution.** When a pipeline fails, a named stage ("integration test" failed, not "build" or "deploy") tells the team exactly where to look, instead of forcing someone to dig through one giant log to find out what actually went wrong.
- **You want it for every pipeline, from the very first one** — even a single-service, single-developer project benefits from separating "did it build" from "did it pass tests" from "did it deploy," because each failure mode needs a different fix.

## 3. Core concept

Think of an assembly line with distinct inspection stations, each checking one specific thing — welds at station one, paint at station two, electronics at station three — rather than one giant room where a car either comes out perfect or the whole thing is scrapped with no idea which part actually failed. Each station's pass or fail is recorded separately, so a failure is immediately traceable to its cause.

A typical pipeline's stages, in order:

1. **Build/compile** — turn source into a runnable artifact; fails on syntax errors or compilation problems.
2. **Unit test** — run fast, isolated tests against the code with no external dependencies; fails on broken logic.
3. **Package** — bundle the artifact (a JAR, a container image) into its deployable, versioned form.
4. **Deploy to staging** — actually run the packaged artifact in a realistic environment.
5. **Integration/smoke test** — verify the running deployment behaves correctly against real (or realistic) dependencies.
6. **Deploy to production** — the same artifact, now proven at every prior stage, goes live.

Each stage only starts once the previous one has fully passed — a failure at any stage halts the pipeline right there, and later stages simply never run for that pipeline execution.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A pipeline is a sequence of named stages, each running only if the previous stage passed">
  <rect x="10" y="70" width="100" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="60" y="102" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">build</text>

  <rect x="130" y="70" width="100" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="180" y="102" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">unit test</text>

  <rect x="250" y="70" width="100" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="102" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">package</text>

  <rect x="370" y="70" width="110" height="55" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="425" y="102" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">staging</text>

  <rect x="500" y="70" width="90" height="55" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="545" y="94" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">integration</text>
  <text x="545" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">test</text>

  <rect x="610" y="70" width="80" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="650" y="102" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">prod</text>

  <line x1="110" y1="97" x2="130" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="230" y1="97" x2="250" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="350" y1="97" x2="370" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="480" y1="97" x2="500" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="590" y1="97" x2="610" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="350" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">a failure at any stage halts the pipeline right there -- later stages never run</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Six named stages run in strict order, each gating the next.

## 5. Runnable example

Scenario: a pipeline runner that executes named stages in order. We start with a basic three-stage sequence, extend it to a realistic six-stage pipeline that reports per-stage timing, then handle the hard case: a stage failing partway through must halt everything after it while still reporting exactly which stages ran and which didn't.

### Level 1 — Basic

```java
// File: PipelineStagesBasic.java -- models THREE named stages running in
// strict order, each only starting if the previous one passed.
public class PipelineStagesBasic {
    static boolean runStage(String name) {
        System.out.println("[stage] " + name + ": running...");
        System.out.println("[stage] " + name + ": PASSED");
        return true;
    }

    public static void main(String[] args) {
        if (!runStage("build")) return;
        if (!runStage("unit test")) return;
        if (!runStage("package")) return;
        System.out.println("[pipeline] all stages passed");
    }
}
```

How to run: `java PipelineStagesBasic.java`

Each `if (!runStage(...)) return;` line is a gate: the next stage's call only executes if the current line's `runStage` call returned `true`. With every stage passing, execution falls through all three gates and reaches the final summary line.

### Level 2 — Intermediate

```java
// File: PipelineStagesTimed.java -- the SAME staged pipeline, now
// EXTENDED to the full six-stage sequence, with each stage reporting how
// long it took -- realistic pipeline output a team would actually read.
public class PipelineStagesTimed {
    static boolean runStage(String name, long simulatedMs) throws InterruptedException {
        long start = System.currentTimeMillis();
        System.out.println("[stage] " + name + ": running...");
        Thread.sleep(simulatedMs);
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("[stage] " + name + ": PASSED (" + elapsed + "ms)");
        return true;
    }

    public static void main(String[] args) throws InterruptedException {
        long pipelineStart = System.currentTimeMillis();
        String[] stages = {"build", "unit test", "package", "deploy-to-staging", "integration test", "deploy-to-production"};
        long[] durations = {30, 15, 10, 25, 40, 20};

        for (int i = 0; i < stages.length; i++) {
            if (!runStage(stages[i], durations[i])) {
                System.out.println("[pipeline] halted at stage: " + stages[i]);
                return;
            }
        }
        long totalElapsed = System.currentTimeMillis() - pipelineStart;
        System.out.println("[pipeline] all " + stages.length + " stages passed in " + totalElapsed + "ms total");
    }
}
```

How to run: `java PipelineStagesTimed.java`

`stages` and `durations` are parallel arrays walked by index in a single loop, each iteration calling `runStage` with that stage's name and simulated duration. Every stage passes in this run, so the loop completes all six iterations and `main` prints the total elapsed time — a realistic shape for what a CI dashboard's per-stage timing view would show.

### Level 3 — Advanced

```java
// File: PipelineStagesFailureReport.java -- the SAME six-stage timed
// pipeline, now handling the PRODUCTION-FLAVORED hard case: a stage FAILS
// partway through (integration test). The pipeline must halt immediately,
// but the FINAL REPORT must clearly show exactly which stages passed,
// which one failed, and which never ran -- full diagnostic clarity, not
// just a bare "pipeline failed" message.
import java.util.*;

public class PipelineStagesFailureReport {
    enum StageResult { PASSED, FAILED, NOT_RUN }

    static boolean runStage(String name, boolean shouldPass) {
        System.out.println("[stage] " + name + ": running...");
        if (shouldPass) {
            System.out.println("[stage] " + name + ": PASSED");
        } else {
            System.out.println("[stage] " + name + ": FAILED");
        }
        return shouldPass;
    }

    public static void main(String[] args) {
        String[] stages = {"build", "unit test", "package", "deploy-to-staging", "integration test", "deploy-to-production"};
        // integration test is the one that fails; everything before it passes.
        boolean[] willPass = {true, true, true, true, false, true};

        Map<String, StageResult> report = new LinkedHashMap<>();
        for (String stage : stages) {
            report.put(stage, StageResult.NOT_RUN);
        }

        boolean halted = false;
        for (int i = 0; i < stages.length; i++) {
            if (halted) break;
            boolean passed = runStage(stages[i], willPass[i]);
            report.put(stages[i], passed ? StageResult.PASSED : StageResult.FAILED);
            if (!passed) {
                halted = true;
            }
        }

        System.out.println("[pipeline] final report:");
        for (Map.Entry<String, StageResult> entry : report.entrySet()) {
            System.out.println("  " + entry.getKey() + ": " + entry.getValue());
        }
    }
}
```

How to run: `java PipelineStagesFailureReport.java`

`report` is initialized up front with every stage marked `NOT_RUN`, then updated to `PASSED` or `FAILED` as each stage actually executes. The loop sets `halted = true` the moment `integration test` fails, and the `if (halted) break;` at the top of the next iteration stops the loop before `deploy-to-production` ever runs — but because `report` was pre-populated, that stage still shows up in the final printout as `NOT_RUN` rather than being silently absent, giving a complete picture of the whole pipeline's state.

## 6. Walkthrough

Trace `PipelineStagesFailureReport.main` in order. **First**, `report` is built with all six stage names mapped to `NOT_RUN` — this happens before any stage actually runs, so the report structure always reflects every stage that *could* run, regardless of what actually happens.

**Next**, the loop runs stages `build`, `unit test`, `package`, and `deploy-to-staging` in sequence. Each one has `willPass[i] = true`, so `runStage` prints its running/passed lines, returns `true`, and `report` is updated to `PASSED` for each — `halted` stays `false` throughout.

**Then**, the loop reaches index `4`, `integration test`, where `willPass[4]` is `false`. `runStage` prints "running..." followed by "FAILED," and returns `false`. Back in the loop body, `report.put("integration test", StageResult.FAILED)` runs, and since `passed` is `false`, `halted` is set to `true`.

**After that**, the loop's next iteration begins with `i = 5` (`deploy-to-production`), but the `if (halted) break;` check at the top fires immediately — the loop exits before `runStage("deploy-to-production", ...)` is ever called. That stage's entry in `report` remains exactly what it was initialized to: `NOT_RUN`.

**Finally**, `main` prints the final report by iterating `report` in its original insertion order (a `LinkedHashMap` preserves that), showing all six stages with their true, distinct outcomes — four `PASSED`, one `FAILED`, one `NOT_RUN` — giving a team reading this output the exact failure point at a glance.

```
[stage] build: running...
[stage] build: PASSED
[stage] unit test: running...
[stage] unit test: PASSED
[stage] package: running...
[stage] package: PASSED
[stage] deploy-to-staging: running...
[stage] deploy-to-staging: PASSED
[stage] integration test: running...
[stage] integration test: FAILED
[pipeline] final report:
  build: PASSED
  unit test: PASSED
  package: PASSED
  deploy-to-staging: PASSED
  integration test: FAILED
  deploy-to-production: NOT_RUN
```

## 7. Gotchas & takeaways

> A pipeline log that only ever shows "build succeeded" or "pipeline failed" with no per-stage breakdown forces whoever's debugging to re-run the whole thing locally just to find out which step actually broke. Naming and reporting each stage separately, as in Level 3, turns a failure into an immediately actionable signal instead of a mystery.
- Order stages cheapest-and-fastest first — unit tests before integration tests, integration tests before a full production deploy — so failures are caught with the least wasted time.
- A `NOT_RUN` (or equivalent "skipped") state is worth modeling explicitly; conflating "didn't run" with "failed" in a report hides useful information about exactly how far the pipeline got.
- Stages map naturally onto [continuous delivery / deployment pipeline](0461-continuous-delivery-deployment-pipelines.md) concepts — "deploy-to-staging" and "deploy-to-production" are stages within the larger CD flow, not a separate concern.
- Each stage should test one specific thing and fail for one specific reason — a stage that mixes concerns (say, compiling *and* running integration tests in one step) makes failures harder to diagnose, defeating the purpose of having stages at all.
- Keep the stage list itself version-controlled alongside the code — the pipeline definition is part of the service, and changes to it should go through the same review process as any other code change.
