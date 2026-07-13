---
card: microservices
gi: 437
slug: immutable-infrastructure
title: "Immutable infrastructure"
---

## 1. What it is

**Immutable infrastructure** is the practice of never modifying a running server, VM, or container after it's deployed — instead of patching, upgrading, or reconfiguring a live instance in place, you build a brand-new instance from an updated image and replace the old one entirely. The running instance becomes disposable: if something needs to change, you don't SSH in and edit it, you throw it away and deploy a fresh one from a new, versioned artifact. The opposite, **mutable infrastructure**, is a server that accumulates changes over its lifetime — patches applied by hand, configuration tweaked over SSH, packages upgraded piecemeal — until nobody is entirely sure what state it's actually in.

## 2. Why & when

Immutable infrastructure exists to eliminate a specific, painful class of problem: environments that have silently drifted from what anyone intended or can reproduce.

- **Configuration drift.** A server patched by hand a dozen times over two years accumulates changes nobody remembers making — an emergency `apt-get upgrade` here, a manually tweaked config file there. Eventually no one can confidently answer "if this server died right now, could we rebuild it identically?" Immutable infrastructure makes that question trivially answerable: yes, from the image.
- **"Works on my machine" at the infrastructure level.** If staging and production servers were provisioned identically once but patched independently since, subtle differences accumulate — a library version here, a missing config flag there — until a bug that "only happens in production" turns out to be an infrastructure difference, not a code difference.
- **Reproducibility for rollback.** If a deployment goes wrong, rolling back a mutable server means manually reversing whatever changes were applied — error-prone and slow. Rolling back an immutable deployment means redeploying the previous image, which is exactly as reliable as deploying the new one was.
- **Auditability.** An immutable image is built from a specific, versioned recipe (a Dockerfile, a Packer template) checked into source control — the entire history of what a given image contains is the commit history of that recipe, not a log of ad hoc SSH sessions.

You adopt immutable infrastructure as a default for any service deployed via containers or cloud VM images — which, for most modern microservices, means always. The exception is genuinely stateful infrastructure (a database's underlying storage volume, for instance) where the *data* must persist even though the *compute* around it is replaced — immutability applies to the deployable artifact, not necessarily to attached persistent storage.

## 3. Core concept

Think of the difference between a whiteboard and a printed poster. A whiteboard (mutable infrastructure) can be edited in place — erase a line, write a correction, erase again — but after enough edits, faint ghost marks and inconsistent handwriting make it hard to trust that what's on the board now matches what anyone actually intended, and there's no way to prove what it said yesterday. A printed poster (immutable infrastructure) can't be edited at all — if something's wrong, you print a new poster and replace the old one on the wall. You always know exactly what's on the wall, because the only way it changes is a full, deliberate replacement, and you can always go dig up the previous poster's file to reprint it if needed.

Concretely, immutable infrastructure rests on three practices working together:

1. **A versioned, buildable artifact** — a container image or machine image, built once from a checked-in recipe (see [container image building](0438-container-image-building.md)), tagged with an immutable identifier (see [image registries & tagging](0441-image-registries-tagging.md)).
2. **No in-place mutation after deploy.** Once an instance is running from that artifact, nothing SSHes in to change it. If a config value needs to change, it comes from an externalized source read at startup (see [externalized config & stateless processes](0443-externalized-config-stateless-processes.md)), not a file edited by hand on the running instance.
3. **Replace, don't repair.** Fixing a bug or applying a patch means: build a new image, deploy new instances from it, and terminate the old instances — exactly the mechanics behind [service instance per container](0435-service-instance-per-container.md) and rolling deployments.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mutable infrastructure accumulates ad hoc patches on a running server over time, leading to configuration drift; immutable infrastructure rebuilds a new versioned image and replaces the running instance entirely for every change" >
  <text x="150" y="24" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Mutable</text>
  <rect x="50" y="45" width="200" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="150" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">server-1 (patched in place)</text>
  <text x="150" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">v1 -&gt; +patch -&gt; +tweak -&gt; ???</text>
  <line x1="150" y1="105" x2="150" y2="130" stroke="#f0883e" stroke-dasharray="3,2"/>
  <text x="150" y="150" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">unknown actual state</text>

  <text x="480" y="24" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Immutable</text>
  <rect x="380" y="45" width="90" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="425" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">image v1</text>
  <rect x="490" y="45" width="90" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="535" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">image v2</text>

  <line x1="425" y1="100" x2="425" y2="130" stroke="#6db33f"/>
  <rect x="380" y="130" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="425" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance A</text>

  <line x1="535" y1="100" x2="535" y2="130" stroke="#6db33f"/>
  <rect x="490" y="130" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance B</text>

  <text x="425" y="195" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">terminated, never patched</text>
  <text x="535" y="195" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fresh, exactly = image v2</text>

  <text x="320" y="225" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">a change is a NEW image + a full replacement, never an edit to a running instance</text>
</svg>

Mutable infrastructure accumulates unverifiable state through in-place patches; immutable infrastructure always knows its exact state because a change is a full replacement.

## 5. Runnable example

Scenario: an `order-service` instance that needs a configuration fix. We model the mutable, patch-in-place approach first (showing how drift accumulates and becomes untrustworthy), then the immutable, image-replacement approach, then a production-flavored case: a rollback that must restore an exact, verifiable prior state — something only immutability makes reliable.

### Level 1 — Basic

```java
// File: MutableInfrastructureBasic.java -- models the MUTABLE approach:
// patches applied directly to a "running instance," accumulating drift.
import java.util.*;

public class MutableInfrastructureBasic {
    static class RunningInstance {
        final String id;
        final List<String> appliedChanges = new ArrayList<>();
        String baseVersion;

        RunningInstance(String id, String baseVersion) { this.id = id; this.baseVersion = baseVersion; }

        // Patches the LIVE instance directly -- nothing rebuilds it from scratch.
        void applyPatchInPlace(String description) {
            appliedChanges.add(description);
            System.out.println("[" + id + "] patched in place: " + description);
        }

        String describeActualState() {
            return baseVersion + " + " + appliedChanges.size() + " ad hoc patch(es): " + appliedChanges;
        }
    }

    public static void main(String[] args) {
        RunningInstance server = new RunningInstance("server-1", "1.4.0");
        server.applyPatchInPlace("bumped log level to DEBUG for an incident");
        server.applyPatchInPlace("manually upgraded a vulnerable library");
        server.applyPatchInPlace("forgot to revert the DEBUG log level");

        System.out.println("Actual state of " + server.id + ": " + server.describeActualState());
        System.out.println("Can we reproduce this EXACT state on a new server from source control alone? No -- "
                + "the patches only exist in this running instance's memory of what happened to it.");
    }
}
```

How to run: `java MutableInfrastructureBasic.java`

`RunningInstance` starts from a base version but accumulates `appliedChanges` directly on the live object — mirroring SSHing into a real server and running commands by hand. Nothing about `describeActualState()`'s output is derivable from a version-controlled recipe; it's only knowable by asking the instance itself what happened to it, and the forgotten DEBUG log level shows how such drift silently persists.

### Level 2 — Intermediate

```java
// File: ImmutableInfrastructureIntermediate.java -- the SAME fix, now via
// IMMUTABLE replacement: build a new versioned image, deploy a fresh
// instance from it, terminate the old one. No in-place patching at all.
import java.util.*;

public class ImmutableInfrastructureIntermediate {
    record Image(String version, List<String> bakedInChanges) {}

    static class RunningInstance {
        final String id;
        final Image image; // the instance IS exactly what its image says, nothing more
        boolean running = true;

        RunningInstance(String id, Image image) { this.id = id; this.image = image; }

        void terminate() { running = false; System.out.println("[" + id + "] terminated"); }
    }

    static Image buildNewImage(Image previous, String change) {
        List<String> changes = new ArrayList<>(previous.bakedInChanges());
        changes.add(change);
        String[] parts = previous.version().split("\\.");
        String newVersion = parts[0] + "." + parts[1] + "." + (Integer.parseInt(parts[2]) + 1);
        Image built = new Image(newVersion, changes);
        System.out.println("Built new image " + built.version() + " from recipe, baking in: " + change);
        return built;
    }

    public static void main(String[] args) {
        Image v1 = new Image("1.4.0", new ArrayList<>());
        RunningInstance instanceA = new RunningInstance("instance-A", v1);
        System.out.println("[" + instanceA.id + "] running image " + instanceA.image.version());

        // A vulnerable library needs upgrading -- NOT patched in place.
        Image v2 = buildNewImage(v1, "upgraded vulnerable library to patched version");
        RunningInstance instanceB = new RunningInstance("instance-B", v2);
        System.out.println("[" + instanceB.id + "] running image " + instanceB.image.version());
        instanceA.terminate();

        System.out.println("Actual state of " + instanceB.id + " = exactly image " + v2.version()
                + " = " + v2.bakedInChanges() + " -- fully reproducible from the image recipe alone.");
    }
}
```

How to run: `java ImmutableInfrastructureIntermediate.java`

`buildNewImage` never touches `previous` — it produces a brand-new `Image` with the change baked in and a bumped version. `instanceA` is never patched; instead, `instanceB` is created fresh from `v2` and `instanceA` is simply terminated. Unlike Level 1's `describeActualState()`, `instanceB`'s state is exactly and only what `v2` describes — no drift is possible because nothing ever mutated a running instance.

### Level 3 — Advanced

```java
// File: ImmutableRollbackAdvanced.java -- the SAME image-replacement model,
// now handling a PRODUCTION-FLAVORED hard case: a bad deployment must be
// rolled back to an EXACT prior state, verified byte-for-byte against a
// registry of known-good image digests -- something mutable infrastructure
// cannot reliably guarantee.
import java.util.*;

public class ImmutableRollbackAdvanced {
    record Image(String version, String digest, List<String> bakedInChanges) {}

    static class ImageRegistry {
        final Map<String, Image> byVersion = new LinkedHashMap<>();
        void publish(Image img) { byVersion.put(img.version(), img); System.out.println("Registry: published " + img.version() + " (digest=" + img.digest() + ")"); }
        Image get(String version) {
            Image img = byVersion.get(version);
            if (img == null) throw new NoSuchElementException("No image found for version " + version);
            return img;
        }
    }

    static class RunningInstance {
        final String id;
        Image image;
        boolean healthy = true;

        RunningInstance(String id, Image image) { this.id = id; this.image = image; }

        // Replacing the instance means swapping which immutable image backs
        // it -- this is a NEW deploy, not a patch, even during a rollback.
        RunningInstance replacedWith(Image newImage) {
            System.out.println("[" + id + "] replacing running image " + image.version() + " -> " + newImage.version());
            return new RunningInstance(id, newImage);
        }
    }

    public static void main(String[] args) {
        ImageRegistry registry = new ImageRegistry();
        Image v1 = new Image("1.4.0", "sha256:aaa111", List.of("baseline"));
        Image v2 = new Image("1.5.0", "sha256:bbb222", List.of("baseline", "new checkout flow"));
        registry.publish(v1);
        registry.publish(v2);

        RunningInstance instance = new RunningInstance("instance-A", v1);
        instance = instance.replacedWith(v2); // deploy v2
        System.out.println("[" + instance.id + "] now running " + instance.image.version() + " digest=" + instance.image.digest());

        // v2 turns out to be broken in production.
        instance.healthy = false;
        System.out.println("[" + instance.id + "] health check FAILED on " + instance.image.version() + " -- rolling back");

        Image rollbackTarget = registry.get("1.4.0"); // the EXACT prior image, by version
        instance = instance.replacedWith(rollbackTarget);
        instance.healthy = true;

        boolean digestMatchesOriginal = instance.image.digest().equals(v1.digest());
        System.out.println("[" + instance.id + "] rolled back to " + instance.image.version()
                + ", digest matches original v1 exactly: " + digestMatchesOriginal);
    }
}
```

How to run: `java ImmutableRollbackAdvanced.java`

The hard case immutability solves cleanly is rollback correctness: `ImageRegistry` keeps every published image, each with an immutable `digest` (a stand-in for a real container registry's content-addressable SHA-256 digest). Rolling back doesn't mean "try to undo whatever changed" — it means fetching `v1` from the registry by its exact identifier and deploying it again, byte-for-byte identical to what ran before `v2` was ever deployed. `digestMatchesOriginal` confirms this: the rolled-back instance's digest is provably, not just probably, identical to the original.

## 6. Walkthrough

Trace `ImmutableRollbackAdvanced.main` in order. **First**, `v1` (`1.4.0`, digest `sha256:aaa111`) and `v2` (`1.5.0`, digest `sha256:bbb222`) are published to `registry`, each retrievable later by exact version string.

**Next**, `instance` starts running `v1`, then `replacedWith(v2)` is called: this doesn't mutate `instance`'s image field on a still-running object — it constructs and returns a *new* `RunningInstance` with the same `id` but a different `image`. The reassignment `instance = instance.replacedWith(v2)` makes this the new instance under tracking; conceptually, the old `v1`-backed instance is gone and a new `v2`-backed one exists in its place.

**Then**, `instance.healthy` is set to `false`, simulating a failed health check on `v2` in production — the new checkout flow it shipped has a bug. The rollback path calls `registry.get("1.4.0")`, retrieving `v1` exactly as it was published, and `replacedWith(rollbackTarget)` again constructs a fresh instance, this time backed by `v1`.

**Finally**, `digestMatchesOriginal` compares the rolled-back instance's `image.digest()` against the original `v1.digest()` and finds them equal — `sha256:aaa111 == sha256:aaa111`. This is the guarantee immutable infrastructure provides that a mutable, patch-in-place rollback cannot: the rolled-back instance isn't an approximation of the old state reconstructed by reversing changes, it's the literal same artifact, redeployed.

```
Registry: published 1.4.0 (digest=sha256:aaa111)
Registry: published 1.5.0 (digest=sha256:bbb222)
[instance-A] replacing running image 1.4.0 -> 1.5.0
[instance-A] now running 1.5.0 digest=sha256:bbb222
[instance-A] health check FAILED on 1.5.0 -- rolling back
[instance-A] replacing running image 1.5.0 -> 1.4.0
[instance-A] rolled back to 1.4.0, digest matches original v1 exactly: true
```

## 7. Gotchas & takeaways

> Immutable infrastructure applies to the compute artifact, not to persistent data — replacing a database instance's container doesn't and shouldn't wipe its attached storage volume. Conflating the two (treating a stateful service exactly like a stateless one, or worse, baking mutable data into an image) is a common and costly mistake; keep state in externally attached, independently managed storage, and keep only the application and its runtime in the immutable image.

- The core discipline is simple to state and easy to violate under pressure: never SSH into a running production instance to "just fix this one thing" — build a new image and redeploy, even when it feels slower in the moment.
- Immutability is what makes rollback trustworthy: rolling back means redeploying a previously published, exact artifact, not attempting to reverse a series of undocumented live changes.
- This practice depends on [container image building](0438-container-image-building.md) producing a real, versioned artifact, and on [image registries & tagging](0441-image-registries-tagging.md) making that artifact retrievable by an exact, immutable identifier later.
- Configuration that legitimately varies between environments (dev, staging, prod) must come from outside the image at startup — see [externalized config & stateless processes](0443-externalized-config-stateless-processes.md) — rather than being baked in per-environment, which would defeat the "one image, many environments" benefit.
- Immutable infrastructure and [service instance per container](0435-service-instance-per-container.md) reinforce each other: containers make "replace, don't patch" cheap enough to do routinely, which is precisely what makes the discipline practical at scale.
