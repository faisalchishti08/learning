---
card: microservices
gi: 464
slug: artifact-versioning-promotion
title: "Artifact versioning & promotion"
---

## 1. What it is

**Artifact versioning** gives every build artifact (a JAR, a container image) a unique, immutable identifier — usually a version number or a content hash — so it can be referenced unambiguously forever. **Promotion** is the act of taking that exact same identified artifact and moving it forward through environments (staging, then production) without rebuilding it — you promote a version, you don't rebuild one.

## 2. Why & when

You version and promote artifacts, rather than rebuilding from source at each pipeline stage, because "the thing you tested" and "the thing you deploy" must provably be the same thing:

- **Rebuilding at each stage risks deploying something you never actually tested.** Even with the same source commit, a rebuild can pull a different dependency version, use a different compiler, or hit a flaky build step — the artifact that reaches production is no longer guaranteed to be the one that passed staging.
- **Unambiguous references make debugging and rollback possible.** "Roll back to `order-service:1.4.1`" only works if `1.4.1` refers to one specific, permanent artifact — if the same version tag could point to different bytes on different days, rollback becomes a gamble.
- **Traceability requires it.** When an incident happens, you need to know exactly which artifact was running, which source commit it came from, and which tests it passed — a stable version identifier is what ties all of that together.
- **You need this from the very first pipeline you build** — even a single-environment deployment benefits from knowing precisely, permanently, what's running, rather than "whatever the last build happened to produce."

## 3. Core concept

Think of a sealed, numbered shipping container: once it's packed and sealed at the factory, its contents are fixed, and the container is simply moved — by truck, then ship, then truck again — from the factory to a warehouse to a store shelf. Nobody repacks the container at each stop; they move the *same* sealed container forward, and its serial number always refers to those exact original contents.

Concretely:

1. **The build stage produces one artifact and assigns it a version** — a semantic version (`1.4.2`), a build number, or a content hash (a container image digest is a common, especially strong choice since it's derived from the actual bytes).
2. **That version is recorded as immutable** — once `1.4.2` exists, it is never overwritten with different contents; a new build gets a new version, never the same one reused.
3. **Every later pipeline stage references that exact version**, not "the latest build" or "whatever's in the repo now" — staging deploys `1.4.2`, and if it passes, production deploys `1.4.2`, the identical bytes.
4. **Promotion is a metadata operation, not a rebuild** — moving an artifact from a "staging" designation to a "production-ready" designation (in an artifact registry, for example) changes a label, not the artifact's content.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One versioned artifact is promoted through staging and production labels without ever being rebuilt">
  <rect x="20" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">order-service:1.4.2</text>
  <text x="110" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">built once, sealed</text>

  <rect x="250" y="30" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">label: staging</text>

  <rect x="250" y="120" width="150" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="325" y="150" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">label: production</text>

  <line x1="200" y1="90" x2="250" y2="55" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="200" y1="110" x2="250" y2="145" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="480" y="90" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">same</text>
  <text x="480" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">bytes,</text>
  <text x="480" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">new label</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The same artifact, `1.4.2`, is promoted from a staging label to a production label — its content never changes.

## 5. Runnable example

Scenario: an in-memory artifact registry that versions builds and tracks their promotion labels. We start with a basic build-and-version step, extend it to promotion between environment labels, then handle the hard case: attempting to promote an artifact that never actually passed the required prior stage, which must be rejected.

### Level 1 — Basic

```java
// File: ArtifactVersioningBasic.java -- models building ONE artifact and
// assigning it an immutable version identifier.
import java.util.*;

public class ArtifactVersioningBasic {
    record Artifact(String name, String version, String contentHash) {}

    static Artifact build(String name, String version) {
        // A real build would hash the actual bytes; here we simulate it.
        String hash = "sha256:" + Integer.toHexString((name + version).hashCode());
        System.out.println("[build] produced " + name + ":" + version + " (" + hash + ")");
        return new Artifact(name, version, hash);
    }

    public static void main(String[] args) {
        Artifact artifact = build("order-service", "1.4.2");
        System.out.println("[registry] stored immutable artifact: " + artifact);
    }
}
```

How to run: `java ArtifactVersioningBasic.java`

`build` returns an immutable `Artifact` record pairing a version with a content hash derived from what was actually built. Once `artifact` exists, nothing in this program ever mutates its fields — `record` types are inherently immutable in Java, mirroring the rule that a version, once built, never changes its contents.

### Level 2 — Intermediate

```java
// File: ArtifactPromotion.java -- the SAME versioned artifact, now
// PROMOTED between environment labels in a simple in-memory registry --
// promotion changes a LABEL, it never rebuilds or re-hashes the artifact.
import java.util.*;

public class ArtifactPromotion {
    record Artifact(String name, String version, String contentHash) {}

    static Map<String, String> environmentLabels = new HashMap<>(); // label -> "name:version"
    static Map<String, Artifact> registry = new HashMap<>(); // "name:version" -> Artifact

    static Artifact build(String name, String version) {
        String hash = "sha256:" + Integer.toHexString((name + version).hashCode());
        Artifact artifact = new Artifact(name, version, hash);
        registry.put(name + ":" + version, artifact);
        System.out.println("[build] produced " + name + ":" + version + " (" + hash + ")");
        return artifact;
    }

    static void promote(String key, String toLabel) {
        Artifact artifact = registry.get(key);
        environmentLabels.put(toLabel, key);
        System.out.println("[promote] " + key + " labeled '" + toLabel + "' -- same content hash: " + artifact.contentHash());
    }

    public static void main(String[] args) {
        build("order-service", "1.4.2");
        promote("order-service:1.4.2", "staging");
        System.out.println("[staging checks] passed for order-service:1.4.2");
        promote("order-service:1.4.2", "production");

        System.out.println("[registry] currently in production: " + environmentLabels.get("production"));
    }
}
```

How to run: `java ArtifactPromotion.java`

`environmentLabels` maps a label (`"staging"`, `"production"`) to an artifact key, and `promote` only ever updates that map — it never calls `build` again or touches `registry`'s stored `Artifact` object. The same `order-service:1.4.2` key moves from the `"staging"` label to the `"production"` label with its `contentHash` unchanged and re-printed identically at each step, proving no rebuild occurred.

### Level 3 — Advanced

```java
// File: ArtifactPromotionGuarded.java -- the SAME promotion registry, now
// handling the PRODUCTION-FLAVORED hard case: someone (or some automation)
// attempts to promote an artifact to production that was NEVER actually
// promoted to, and verified in, staging first. This must be REJECTED --
// skipping the staging gate is exactly the failure a promotion system
// exists to prevent.
import java.util.*;

public class ArtifactPromotionGuarded {
    record Artifact(String name, String version, String contentHash) {}

    static Map<String, String> environmentLabels = new HashMap<>();
    static Map<String, Artifact> registry = new HashMap<>();
    static Set<String> stagingVerified = new HashSet<>(); // keys that passed staging checks

    static Artifact build(String name, String version) {
        String hash = "sha256:" + Integer.toHexString((name + version).hashCode());
        Artifact artifact = new Artifact(name, version, hash);
        registry.put(name + ":" + version, artifact);
        System.out.println("[build] produced " + name + ":" + version + " (" + hash + ")");
        return artifact;
    }

    static boolean promoteToStaging(String key) {
        if (!registry.containsKey(key)) {
            System.out.println("[promote] REJECTED: " + key + " does not exist in the registry");
            return false;
        }
        environmentLabels.put("staging", key);
        System.out.println("[promote] " + key + " labeled 'staging'");
        return true;
    }

    static boolean markStagingVerified(String key) {
        if (!key.equals(environmentLabels.get("staging"))) {
            System.out.println("[verify] REJECTED: " + key + " is not the artifact currently labeled 'staging'");
            return false;
        }
        stagingVerified.add(key);
        System.out.println("[verify] " + key + " passed staging checks");
        return true;
    }

    static boolean promoteToProduction(String key) {
        if (!stagingVerified.contains(key)) {
            System.out.println("[promote] REJECTED: " + key + " was never verified in staging -- cannot skip the gate");
            return false;
        }
        environmentLabels.put("production", key);
        System.out.println("[promote] " + key + " labeled 'production'");
        return true;
    }

    public static void main(String[] args) {
        build("order-service", "1.4.2");
        build("order-service", "1.4.3"); // a newer build that never goes through staging

        promoteToStaging("order-service:1.4.2");
        markStagingVerified("order-service:1.4.2");
        promoteToProduction("order-service:1.4.2"); // succeeds

        System.out.println();
        System.out.println("--- someone tries to shortcut 1.4.3 straight to production ---");
        promoteToProduction("order-service:1.4.3"); // must be rejected
    }
}
```

How to run: `java ArtifactPromotionGuarded.java`

`stagingVerified` is the guard: `promoteToProduction` checks membership in it before allowing the label update, and `markStagingVerified` only adds a key after confirming it's the artifact actually currently labeled `"staging"`. `order-service:1.4.3` is built but never passed through `promoteToStaging` or `markStagingVerified`, so the final call to `promoteToProduction("order-service:1.4.3")` fails the guard check and is rejected — no label update happens, and `environmentLabels.get("production")` still points at `1.4.2`.

## 6. Walkthrough

Trace `ArtifactPromotionGuarded.main` in order. **First**, two artifacts are built — `1.4.2` and `1.4.3` — both stored in `registry`, but neither yet appearing in `environmentLabels` or `stagingVerified`.

**Next**, `promoteToStaging("order-service:1.4.2")` runs: the key exists in `registry`, so `environmentLabels.put("staging", ...)` succeeds and prints confirmation. `markStagingVerified` then checks that `1.4.2` equals `environmentLabels.get("staging")` — it does — so `stagingVerified.add(...)` runs and the check passes.

**Then**, `promoteToProduction("order-service:1.4.2")` checks `stagingVerified.contains("order-service:1.4.2")`, which is now `true` (from the previous step), so the guard passes and `environmentLabels.put("production", ...)` succeeds — `1.4.2` is now labeled both `"staging"` (from earlier) and `"production"`.

**After that**, the attempt to shortcut `1.4.3` begins: `promoteToProduction("order-service:1.4.3")` checks `stagingVerified.contains("order-service:1.4.3")`. Since `1.4.3` was only ever built — `promoteToStaging` and `markStagingVerified` were never called for it — this check is `false`, so the guard rejects it, prints the rejection message, and `environmentLabels.put("production", ...)` never runs for `1.4.3`.

**Finally**, the program ends with `environmentLabels.get("production")` still pointing at `1.4.2`, proving `1.4.3` never made it into production despite the direct attempt — the staging gate held.

```
[build] produced order-service:1.4.2 (sha256:...)
[build] produced order-service:1.4.3 (sha256:...)
[promote] order-service:1.4.2 labeled 'staging'
[verify] order-service:1.4.2 passed staging checks
[promote] order-service:1.4.2 labeled 'production'

--- someone tries to shortcut 1.4.3 straight to production ---
[promote] REJECTED: order-service:1.4.3 was never verified in staging -- cannot skip the gate
```

## 7. Gotchas & takeaways

> A pipeline that rebuilds the artifact at each environment "just to be sure" defeats the entire point of versioning — you lose the guarantee that what passed staging is bit-for-bit identical to what runs in production. If you must verify integrity, compare hashes; never rebuild.
- Content-based identifiers (a container image digest) are stronger guarantees than human-assigned version numbers alone — a digest changes if even one byte changes, where a careless team could theoretically reuse a version number by mistake.
- Promotion should always be gated on the prior stage's actual verified outcome, as in Level 3 — a promotion system that trusts an unverified claim of "it passed staging" isn't really enforcing anything.
- This underpins [continuous delivery / deployment pipelines](0461-continuous-delivery-deployment-pipelines.md): "promote the same artifact through stages" is the mechanism, versioning is what makes "the same artifact" a provable statement rather than an assumption.
- Keep a permanent, queryable record of which version is running in which environment at all times — it's the first thing anyone needs during an incident, and the reason rollback ("redeploy the previous version") is even possible.
- Never reuse a version number for different content, even for a quick hotfix — always cut a new version, so every identifier remains permanently, unambiguously meaningful.
