---
card: microservices
gi: 441
slug: image-registries-tagging
title: "Image registries & tagging"
---

## 1. What it is

An **image registry** (Docker Hub, Amazon ECR, Google Artifact Registry, GitHub Container Registry, a self-hosted Harbor instance) is a versioned storage service for container images — the place a built image gets pushed to and later pulled from by any host that needs to run it. **Tagging** is how a specific image build gets a human-readable name (`order-service:1.5.0`, `order-service:latest`), while under the hood every image also has an immutable **digest** — a content hash (`sha256:...`) that uniquely and unambiguously identifies the exact bytes of that image, regardless of what tag currently points to it.

## 2. Why & when

Registries and disciplined tagging matter because they're the handoff point between "an image was built" and "an image can be reliably deployed anywhere, later, by anyone":

- **A registry is what makes an image portable.** A locally built image only exists on the machine that built it; pushing it to a registry makes it retrievable by any orchestrator, any host, any CI pipeline that has pull access — this is the actual mechanism behind "build once, deploy anywhere."
- **Tags are mutable pointers; digests are not.** A tag like `order-service:latest` can be reassigned to point at a different image tomorrow — that's convenient during active development but dangerous in production, because two deployments both referencing `latest` can silently end up running different code. A digest always refers to one exact, unchangeable set of bytes.
- **Version tags enable reliable rollback.** Tagging every build with a specific, meaningful version (a semantic version, a Git commit SHA, or both) means "roll back to the previous release" has an unambiguous answer: redeploy the image at the previous tag — the same mechanism [immutable infrastructure](0437-immutable-infrastructure.md) depends on for rollback correctness.
- **Registries are also a security control point.** Vulnerability scanning, access control (who can push, who can pull), and image signing/verification typically happen at the registry layer — making the registry a natural gate before an image is allowed into production.

You push to and pull from a registry on every single deployment in a containerized system — it's not an optional step. The judgment calls are in *how* you tag (see below) and which registry you trust for which environments (a public registry for open-source base images, a private, access-controlled registry for your own application images).

## 3. Core concept

Think of an image registry like a library, tags like the labels on a book's spine, and the digest like the book's exact printed text. Two different editions of the same book title (`order-service:1.5.0` and a re-tagged `order-service:latest` pointing at that same build, or later repointed at a different build) can share a label on the shelf, but only the actual printed pages — the content itself — definitively tell you what you're reading. If the library relabels a shelf spot to point at a revised edition without telling anyone, someone citing "the book at that shelf spot" yesterday and someone citing it today might be talking about genuinely different content, even though they used the same label.

Concretely, registries and tags work through:

1. **Push** — after a build (see [container image building](0438-container-image-building.md)), `docker push registry.example.com/order-service:1.5.0` uploads the image's layers (only layers the registry doesn't already have, by digest) and records the tag.
2. **Tag** — a mutable, human-friendly name mapped to a specific image digest at the time of tagging. Re-tagging (`docker tag ... order-service:latest` pointed at a new build) reassigns the name to a different digest; anyone who already pulled the old `latest` doesn't automatically get the new one until they pull again.
3. **Digest** — an immutable, content-derived identifier (`sha256:abc123...`) computed from the image's actual content. Pulling by digest (`order-service@sha256:abc123...`) always gets the exact same bytes, forever — this is what production deployments should reference for reproducibility, even if a human-readable tag is used for convenience in dashboards and change logs.
4. **Tagging strategy** — common conventions include semantic version tags (`1.5.0`), Git-commit-SHA tags (`git-a1b2c3d`) for exact traceability back to source, and moving tags like `latest` or `stable` that are convenient for humans but should never be what a production deployment pins to.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A registry stores images identified by immutable digests; multiple tags can point at a digest, and a tag can be reassigned to a different digest later, while the digest itself never changes" >
  <rect x="30" y="30" width="580" height="190" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Registry: registry.example.com/order-service</text>

  <rect x="60" y="55" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="150" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">digest sha256:aaa111</text>
  <text x="150" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">the actual, immutable bytes</text>

  <rect x="330" y="55" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="420" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">digest sha256:bbb222</text>
  <text x="420" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">the actual, immutable bytes</text>

  <text x="150" y="130" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">tag: 1.4.0</text>
  <line x1="150" y1="105" x2="150" y2="120" stroke="#79c0ff"/>

  <text x="420" y="130" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">tag: 1.5.0</text>
  <line x1="420" y1="105" x2="420" y2="120" stroke="#79c0ff"/>

  <text x="420" y="155" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">tag: latest (moved here)</text>
  <line x1="420" y1="105" x2="420" y2="145" stroke="#f0883e" stroke-dasharray="3,2"/>
  <line x1="150" y1="180" x2="420" y2="150" stroke="#f0883e" stroke-dasharray="3,2" opacity="0.5"/>
  <text x="285" y="195" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">latest used to point HERE (sha256:aaa111) before 1.5.0 shipped</text>

  <text x="320" y="235" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">tags move; the digest a tag pointed at yesterday may not be what it points at today</text>
</svg>

Digests are immutable content identifiers; tags are mutable pointers that can be reassigned to a different digest at any time.

## 5. Runnable example

Scenario: pushing and referencing `order-service` images. We model a registry as a digest-keyed store with mutable tag pointers first, then show why pulling by a moving tag is unsafe for reproducible deployment, then handle a production-flavored case: pinning a deployment manifest to an exact digest and detecting drift if the underlying tag later moves.

### Level 1 — Basic

```java
// File: RegistryTaggingBasic.java -- models the CORE idea: a registry
// stores images by DIGEST, and TAGS are separate, reassignable pointers.
import java.util.*;

public class RegistryTaggingBasic {
    static class Registry {
        final Map<String, byte[]> imagesByDigest = new HashMap<>(); // digest -> "content"
        final Map<String, String> tagToDigest = new HashMap<>();    // tag -> digest

        String push(String content) {
            String digest = "sha256:" + Integer.toHexString(content.hashCode());
            imagesByDigest.put(digest, content.getBytes());
            System.out.println("Pushed image content, digest=" + digest);
            return digest;
        }

        void tag(String tagName, String digest) {
            tagToDigest.put(tagName, digest);
            System.out.println("Tag '" + tagName + "' now points to " + digest);
        }

        String resolve(String tagName) {
            return tagToDigest.get(tagName);
        }
    }

    public static void main(String[] args) {
        Registry registry = new Registry();

        String digestV1 = registry.push("order-service build #1 content");
        registry.tag("1.4.0", digestV1);
        registry.tag("latest", digestV1);

        String digestV2 = registry.push("order-service build #2 content");
        registry.tag("1.5.0", digestV2);
        registry.tag("latest", digestV2); // "latest" moves; "1.4.0" does NOT

        System.out.println("1.4.0 resolves to: " + registry.resolve("1.4.0"));
        System.out.println("1.5.0 resolves to: " + registry.resolve("1.5.0"));
        System.out.println("latest resolves to: " + registry.resolve("latest") + " (moved to match 1.5.0)");
    }
}
```

How to run: `java RegistryTaggingBasic.java`

`imagesByDigest` stores content keyed by its immutable digest; `tagToDigest` is a separate map of human-friendly names to whatever digest they currently point at. Tagging `"latest"` a second time simply overwrites its entry in `tagToDigest` — `"1.4.0"` still correctly resolves to `digestV1` because nothing re-tagged it, but `"latest"` now resolves to `digestV2`, demonstrating that a tag is just a pointer that can be silently reassigned.

### Level 2 — Intermediate

```java
// File: MovingTagRiskIntermediate.java -- the SAME registry model, now
// showing the CONCRETE risk of deploying by a moving tag: two "identical"
// deployments referencing the same tag can end up running different code.
import java.util.*;

public class MovingTagRiskIntermediate {
    static class Registry {
        final Map<String, String> tagToDigest = new HashMap<>();
        void tag(String tagName, String digest) { tagToDigest.put(tagName, digest); }
        String resolve(String tagName) { return tagToDigest.get(tagName); }
    }

    public static void main(String[] args) {
        Registry registry = new Registry();
        registry.tag("latest", "sha256:aaa111"); // build #1

        // Deployment A pulls "latest" NOW.
        String deploymentADigest = registry.resolve("latest");
        System.out.println("Deployment A pulled 'latest' -> " + deploymentADigest);

        // A new build ships and "latest" is reassigned, as CI commonly does automatically.
        registry.tag("latest", "sha256:bbb222"); // build #2
        System.out.println("CI pushed a new build and moved 'latest' -> " + registry.resolve("latest"));

        // Deployment B, minutes later, ALSO pulls "latest" -- but a new host
        // scaling up for Deployment A's OWN fleet, restarted after the CI push,
        // pulls "latest" too and gets a DIFFERENT digest than its siblings.
        String deploymentBDigest = registry.resolve("latest");
        System.out.println("A new host scaling up the SAME fleet pulled 'latest' -> " + deploymentBDigest);

        boolean fleetIsConsistent = deploymentADigest.equals(deploymentBDigest);
        System.out.println("Is the fleet running one consistent image? " + fleetIsConsistent
                + " -- two hosts in the SAME fleet are now running DIFFERENT code, purely because 'latest' moved between pulls.");
    }
}
```

How to run: `java MovingTagRiskIntermediate.java`

`deploymentADigest` is resolved before a new build moves `"latest"`; `deploymentBDigest` is resolved after. Even though both "deployments" referenced the identical tag name `"latest"`, they resolve to different digests because the tag moved in between — exactly the scenario that causes mysterious, hard-to-debug inconsistency across a fleet when new instances scale up mid-rollout and pull a tag that's actively being reassigned by CI.

### Level 3 — Advanced

```java
// File: PinnedDigestDeploymentAdvanced.java -- the SAME registry, now
// handling the PRODUCTION-FLAVORED fix: a deployment manifest pins an EXACT
// digest, not a moving tag, and the system can detect if a tag has since
// drifted away from what was actually deployed -- useful for audits.
import java.util.*;

public class PinnedDigestDeploymentAdvanced {
    record DeploymentManifest(String serviceName, String pinnedDigest) {}

    static class Registry {
        final Map<String, String> tagToDigest = new HashMap<>();
        final Map<String, String> digestToVersionLabel = new HashMap<>();

        void tag(String tagName, String digest, String versionLabel) {
            tagToDigest.put(tagName, digest);
            digestToVersionLabel.put(digest, versionLabel);
        }
        String resolve(String tagName) { return tagToDigest.get(tagName); }
    }

    public static void main(String[] args) {
        Registry registry = new Registry();
        registry.tag("1.5.0", "sha256:bbb222", "1.5.0");
        registry.tag("latest", "sha256:bbb222", "1.5.0");

        // The deployment manifest pins the EXACT digest at deploy time --
        // NOT a tag -- so what's running is fully reproducible and auditable.
        DeploymentManifest manifest = new DeploymentManifest("order-service", registry.resolve("1.5.0"));
        System.out.println("Deployed " + manifest.serviceName() + " pinned to digest " + manifest.pinnedDigest()
                + " (was version " + registry.digestToVersionLabel.get(manifest.pinnedDigest()) + " at deploy time)");

        // Time passes. A new build ships; "latest" moves; "1.5.0" tag itself
        // is untouched (semantic version tags should never be reassigned).
        registry.tag("1.6.0", "sha256:ccc333", "1.6.0");
        registry.tag("latest", "sha256:ccc333", "1.6.0");

        // Audit: is the running deployment still exactly what its manifest says?
        boolean stillMatchesPinnedDigest = manifest.pinnedDigest().equals("sha256:bbb222");
        String currentLatestDigest = registry.resolve("latest");
        boolean deploymentMatchesLatest = manifest.pinnedDigest().equals(currentLatestDigest);

        System.out.println("Running deployment still matches its OWN pinned digest: " + stillMatchesPinnedDigest + " (always true -- digests never drift)");
        System.out.println("Running deployment matches CURRENT 'latest': " + deploymentMatchesLatest
                + " -- expected 'false' after a new release; this is fine BECAUSE the manifest never depended on 'latest' in the first place.");
    }
}
```

How to run: `java PinnedDigestDeploymentAdvanced.java`

The hard case is auditability over time: `manifest.pinnedDigest()` is fixed at deploy time to the exact digest `1.5.0` resolved to, `sha256:bbb222`. Later, `1.6.0` ships and `"latest"` moves to `sha256:ccc333`. `stillMatchesPinnedDigest` is always `true` — the manifest's own record of what it deployed can never drift, because it never referenced a tag, only a digest. `deploymentMatchesLatest` correctly comes back `false`, which is expected and harmless: the running deployment was never supposed to track `"latest"` automatically, so a mismatch here isn't decay, it's simply confirmation the pin is doing its job.

## 6. Walkthrough

Trace `PinnedDigestDeploymentAdvanced.main` in order. **First**, `registry.tag("1.5.0", "sha256:bbb222", "1.5.0")` and `registry.tag("latest", "sha256:bbb222", "1.5.0")` both point at the same digest, since `1.5.0` is the newest build at this moment.

**Next**, `manifest` is created by resolving `"1.5.0"` right now and storing the resulting digest, `sha256:bbb222`, directly in `manifest.pinnedDigest`. From this point on, `manifest` has no reference to the tag `"1.5.0"` at all — only to the resolved digest. The deployment is printed as pinned to `sha256:bbb222`, version `1.5.0`.

**Then**, a new build, `1.6.0`, is tagged with digest `sha256:ccc333`, and `"latest"` is reassigned to point at it. The tag `"1.5.0"` itself is untouched — semantic version tags are conventionally never reassigned once published, unlike `"latest"`, which is expected to move.

**Finally**, the audit checks run. `stillMatchesPinnedDigest` compares `manifest.pinnedDigest()` against the literal string `"sha256:bbb222"` — trivially `true`, since nothing about the manifest's own stored value could have changed. `currentLatestDigest` resolves `"latest"` right now, getting `sha256:ccc333`; comparing that against `manifest.pinnedDigest()` (`sha256:bbb222`) correctly yields `false`. The print statements make explicit that this mismatch is expected and not a bug — it's the direct, intended consequence of having pinned to a digest instead of a moving tag.

```
Deployed order-service pinned to digest sha256:bbb222 (was version 1.5.0 at deploy time)
Running deployment still matches its OWN pinned digest: true (always true -- digests never drift)
Running deployment matches CURRENT 'latest': false -- expected 'false' after a new release; this is fine BECAUSE the manifest never depended on 'latest' in the first place.
```

## 7. Gotchas & takeaways

> Never deploy production workloads pinned to `latest` or any other moving tag — an orchestrator that re-pulls an image on restart (which Kubernetes does under certain `imagePullPolicy` settings) can pull a *different* image than what was originally deployed, purely because the tag moved in the meantime, causing an unplanned, invisible version change across only some of your fleet's instances.

- A tag is a convenient, human-readable pointer; a digest is the actual, immutable identity of an image's content — production deployments should pin to a digest (or, at minimum, an immutable, never-reassigned version tag) for reproducibility.
- Registries deduplicate by digest, so pushing the same content twice, or having multiple tags point at the same build, doesn't multiply storage — this is what makes frequent, small, layer-cached builds cheap to push.
- Semantic version tags (`1.5.0`) or commit-SHA tags (`git-a1b2c3d`) should be treated as immutable by convention once published — reassigning them defeats the reproducibility they're meant to provide, even though the registry technically allows it.
- This all builds directly on [immutable infrastructure](0437-immutable-infrastructure.md): the registry and its digests are what make "redeploy the exact previous artifact" a reliable rollback strategy rather than a best-effort one.
- Registries are also where image scanning and access control typically live — treat push access as a security boundary, since anyone who can push to a registry your production deploys pull from can effectively ship code to production.
