---
card: spring-cloud
gi: 130
slug: spring-cloud-skipper-deployment
title: "Spring Cloud Skipper (deployment)"
---

## 1. What it is

Spring Cloud Skipper is the component Spring Cloud Data Flow delegates actual stream deployment to, and it adds versioned, rollback-capable deployment on top of what a plain deploy operation would offer — every `stream deploy` (or `stream update`) creates a new numbered release of that stream, Skipper tracks the full history of releases for a given stream, and `stream rollback` can revert to any previous release's exact configuration, giving stream deployments the same kind of release history and rollback safety net a well-run application deployment pipeline provides for ordinary services.

```
dataflow:> stream deploy --name order-pipeline --properties "app.filter.threshold=100"
# Skipper creates release #1

dataflow:> stream update --name order-pipeline --properties "app.filter.threshold=200"
# Skipper creates release #2 (the running pipeline now uses the NEW threshold)

dataflow:> stream rollback --name order-pipeline --releaseVersion 1
# Skipper redeploys EXACTLY release #1's configuration
```

## 2. Why & when

Updating a running stream pipeline's configuration or upgrading one of its stages to a new application version is inherently risky — the new configuration or version might behave unexpectedly once actually deployed, and without any tracked history of prior working configurations, reverting to "whatever it was before" requires an operator to manually remember or reconstruct the previous settings. Skipper solves this by treating every deployment as an immutable, versioned release: updating a stream's configuration doesn't overwrite anything, it creates a brand new release on top of the release history, so the exact previous configuration remains available, tracked, and one command away from being restored if the new release turns out to be problematic.

Reach for understanding Skipper's release model when:

- Updating a running stream's configuration or upgrading a stage's application version and wanting a safety net — knowing `stream rollback` exists, and understanding it reverts to an exact prior release rather than requiring manual reconstruction of old settings, changes the risk calculus of making the update in the first place.
- Diagnosing when a stream's behavior changed — release history gives a concrete, timestamped record of exactly what configuration was deployed when, useful for correlating a behavior change with a specific deployment rather than guessing.
- Understanding the relationship between Data Flow and Skipper — Data Flow provides the higher-level stream/task DSL and orchestration surface, while Skipper specifically handles the versioned deployment mechanics underneath stream operations (tasks, being run-to-completion rather than continuously deployed, don't go through Skipper's release-versioning model in the same way).

## 3. Core concept

```
 stream deploy (properties A)     -> Skipper creates RELEASE #1 (properties A) -- currently ACTIVE
 stream update (properties B)     -> Skipper creates RELEASE #2 (properties B) -- currently ACTIVE, #1 STILL RECORDED
 stream update (properties C)     -> Skipper creates RELEASE #3 (properties C) -- currently ACTIVE, #1 and #2 STILL RECORDED

 stream rollback --releaseVersion 1
   -> Skipper does NOT delete releases #2 or #3
   -> Skipper creates a NEW release (#4) that REDEPLOYS release #1's EXACT properties
   -> the running pipeline now reflects release #1's configuration again, via this new release #4
```

Rollback is itself implemented as a new release, not a destructive rewind — the full history (every release ever created) remains intact and inspectable, even after multiple updates and rollbacks.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three sequential stream updates create three tracked releases and a rollback to release one creates a fourth new release that redeploys release ones exact configuration without deleting any prior release history">
  <rect x="20" y="20" width="130" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="85" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">release #1 (A)</text>
  <rect x="180" y="20" width="130" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="245" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">release #2 (B)</text>
  <rect x="340" y="20" width="130" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="405" y="38" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">release #3 (C)</text>
  <text x="405" y="52" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">was ACTIVE</text>

  <rect x="500" y="20" width="130" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="38" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">release #4 (=A)</text>
  <text x="565" y="52" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">NOW active (rollback)</text>

  <text x="320" y="110" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">rollback --releaseVersion 1 creates release #4, redeploying release #1's properties -- #1, #2, #3 all STILL recorded</text>

  <defs><marker id="a130" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="150" y1="40" x2="180" y2="40" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a130)"/>
  <line x1="310" y1="40" x2="340" y2="40" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a130)"/>
  <line x1="470" y1="40" x2="500" y2="40" stroke="#79c0ff" stroke-width="1.3" marker-end="url(#a130)"/>
</svg>

Every release remains in the timeline permanently — rollback adds a new entry rather than erasing anything already recorded.

## 5. Runnable example

The scenario: model Skipper's release history for a stream — each update creating a new tracked release, with a rollback creating yet another release that redeploys an earlier one's exact configuration. Start with a single deployment creating release #1, then add multiple updates building release history, then add rollback demonstrating the full history remains intact even after reverting.

### Level 1 — Basic

A single stream deployment, creating the first tracked release.

```java
import java.util.*;

public class SkipperDeploymentLevel1 {
    record Release(int version, Map<String, String> properties) {}

    static class Skipper {
        String streamName;
        List<Release> releaseHistory = new ArrayList<>();
        Skipper(String streamName) { this.streamName = streamName; }

        void deploy(Map<String, String> properties) {
            Release release = new Release(releaseHistory.size() + 1, properties);
            releaseHistory.add(release);
            System.out.println("deployed release #" + release.version() + " with properties: " + properties);
        }
    }

    public static void main(String[] args) {
        Skipper skipper = new Skipper("order-pipeline");
        skipper.deploy(Map.of("threshold", "100"));
    }
}
```

How to run: `java SkipperDeploymentLevel1.java`

`deploy` creates release `#1` — the first entry in what will become an ongoing, permanently-tracked release history for this stream.

### Level 2 — Intermediate

Add multiple updates, each creating a new release, building up a full history of configuration changes over time.

```java
import java.util.*;

public class SkipperDeploymentLevel2 {
    record Release(int version, Map<String, String> properties) {}

    static class Skipper {
        String streamName;
        List<Release> releaseHistory = new ArrayList<>();
        Skipper(String streamName) { this.streamName = streamName; }

        Release currentRelease() { return releaseHistory.get(releaseHistory.size() - 1); }

        void deploy(Map<String, String> properties) {
            Release release = new Release(releaseHistory.size() + 1, properties);
            releaseHistory.add(release);
            System.out.println("deployed release #" + release.version() + " with properties: " + properties);
        }
    }

    public static void main(String[] args) {
        Skipper skipper = new Skipper("order-pipeline");

        skipper.deploy(Map.of("threshold", "100"));   // release #1
        skipper.deploy(Map.of("threshold", "200"));   // release #2 -- an UPDATE, not an overwrite of #1
        skipper.deploy(Map.of("threshold", "150"));   // release #3

        System.out.println("total releases tracked: " + skipper.releaseHistory.size());
        System.out.println("currently active release: #" + skipper.currentRelease().version()
                + " with properties " + skipper.currentRelease().properties());
    }
}
```

How to run: `java SkipperDeploymentLevel2.java`

`releaseHistory` grows to three entries across the three `deploy` calls, and `currentRelease()` correctly identifies release `#3` (the most recently created) as active — but critically, releases `#1` and `#2` remain fully intact within `releaseHistory`, exactly mirroring how Skipper never discards prior release records simply because a newer one has since been deployed.

### Level 3 — Advanced

Add rollback: reverting to an earlier release's configuration creates a brand-new release rather than deleting or rewinding history, and confirm the full history (including the rollback itself) remains completely intact and inspectable.

```java
import java.util.*;

public class SkipperDeploymentLevel3 {
    record Release(int version, Map<String, String> properties, boolean isRollback) {}

    static class Skipper {
        String streamName;
        List<Release> releaseHistory = new ArrayList<>();
        Skipper(String streamName) { this.streamName = streamName; }

        Release currentRelease() { return releaseHistory.get(releaseHistory.size() - 1); }

        void deploy(Map<String, String> properties) {
            Release release = new Release(releaseHistory.size() + 1, properties, false);
            releaseHistory.add(release);
        }

        void rollback(int targetVersion) {
            Release target = releaseHistory.stream()
                    .filter(r -> r.version() == targetVersion)
                    .findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("no such release: " + targetVersion));

            // rollback creates a NEW release with the TARGET's properties -- it does NOT delete or rewind anything
            Release newRelease = new Release(releaseHistory.size() + 1, target.properties(), true);
            releaseHistory.add(newRelease);
            System.out.println("rollback to release #" + targetVersion + " created NEW release #" + newRelease.version()
                    + " with properties " + newRelease.properties());
        }
    }

    public static void main(String[] args) {
        Skipper skipper = new Skipper("order-pipeline");
        skipper.deploy(Map.of("threshold", "100")); // release #1
        skipper.deploy(Map.of("threshold", "200")); // release #2
        skipper.deploy(Map.of("threshold", "150")); // release #3 -- turns out to be problematic

        skipper.rollback(1); // revert to release #1's properties -- creates release #4

        System.out.println("full release history (nothing deleted):");
        for (Release r : skipper.releaseHistory) {
            System.out.println("  #" + r.version() + " properties=" + r.properties() + (r.isRollback() ? " (via rollback)" : ""));
        }
        System.out.println("currently active: #" + skipper.currentRelease().version()
                + " properties=" + skipper.currentRelease().properties());
    }
}
```

How to run: `java SkipperDeploymentLevel3.java`

`skipper.rollback(1)` creates release `#4`, whose `properties` exactly match release `#1`'s (`threshold=100`) — the full printed history shows all four releases intact, `#1` through `#3` unchanged and still present, with `#4` clearly marked as having arrived via rollback; `currentRelease()` correctly reports `#4` as active, with the pipeline's effective configuration back to `threshold=100`, achieved without ever deleting or overwriting `#2` or `#3`'s historical records.

## 6. Walkthrough

Trace `skipper.rollback(1)` in Level 3.

1. `releaseHistory.stream().filter(r -> r.version() == 1).findFirst()` searches the current three-element `releaseHistory` for the release whose `version` field equals `1` — it finds the very first release created, whose `properties` is `{threshold: "100"}`, and assigns it to `target`.
2. A new `Release` object is constructed: `version = releaseHistory.size() + 1` evaluates to `3 + 1 = 4` (since `releaseHistory` has three elements at this point), `properties = target.properties()` copies release `#1`'s exact property map, and `isRollback = true` marks this release as having originated from a rollback operation.
3. `releaseHistory.add(newRelease)` appends this new, fourth release to the list — `releaseHistory` now has four elements total; nothing was removed or modified for releases `#1`, `#2`, or `#3`.
4. The `println` reports the rollback action and the new release's properties, confirming they match release `#1`'s original `threshold=100`.
5. The subsequent `for` loop over the full `releaseHistory` prints all four releases in order — `#1` (`threshold=100`), `#2` (`threshold=200`), `#3` (`threshold=150`), and `#4` (`threshold=100`, marked "via rollback") — demonstrating that every release, including the ones that predate and postdate the rollback, remains fully present and inspectable in the history.
6. `currentRelease()` returns `releaseHistory.get(3)` (the last element, index `3`, zero-indexed), which is release `#4` — confirming the pipeline's currently-active configuration is now, correctly, back to `threshold=100`, achieved via a new release rather than any destructive undo operation.

```
releaseHistory before rollback: [#1(threshold=100), #2(threshold=200), #3(threshold=150)]

rollback(1):
  find release #1 -> properties {threshold: 100}
  create NEW release #4 with THOSE properties, isRollback=true
  releaseHistory.add(#4)

releaseHistory after rollback: [#1, #2, #3, #4]   <- ALL FOUR present, nothing removed
currentRelease() -> #4 (threshold=100)             <- pipeline's active config reverted, via a NEW release
```

## 7. Gotchas & takeaways

> **Gotcha:** rolling back reverts the stream's *configuration* to match an earlier release, but it does not undo any external side effects that occurred while the problematic release was active — if release `#3`'s bad configuration caused messages to be processed incorrectly (written to a database with wrong values, for instance) during the time it was active, rolling back to release `#1`'s configuration does not retroactively fix or reprocess that already-mishandled data; rollback addresses the deployment's ongoing configuration going forward, not the historical consequences of the configuration that was active in between.

- Skipper's release model treats every deployment or update as an immutable, permanently-recorded release rather than an overwrite — this is what makes the full deployment history always available for inspection and what makes rollback possible at all.
- Rollback is implemented as creating a new release with an earlier release's configuration, not as a destructive rewind — the release that was active before the rollback (and every release before it) remains fully intact in the history, simply no longer the currently active one.
- This versioned release model is specifically how Skipper handles *stream* deployments — Data Flow's task lifecycle (the previous card) doesn't go through this same release-versioning mechanism, since a task's discrete, repeatable launches are a fundamentally different operational pattern from a stream's single, ongoing, updatable deployment.
- Understanding that rollback only affects ongoing configuration, not historical side effects already produced while a bad release was active, is essential to correctly assessing what a rollback actually fixes versus what might still need separate remediation after the fact.
