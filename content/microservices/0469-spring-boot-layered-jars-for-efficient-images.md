---
card: microservices
gi: 469
slug: spring-boot-layered-jars-for-efficient-images
title: "Spring Boot layered JARs for efficient images"
---

## 1. What it is

A **layered JAR** is Spring Boot's alternative packaging mode that splits a [fat JAR's](0468-spring-boot-executable-fat-jar.md) contents into separate, independently-extractable **layers** — grouped by how often their contents actually change (dependencies vs. your own application code) — so that a container image built from it can cache the rarely-changing layers and only rebuild the layer containing your own code, dramatically shrinking the image layers that need rebuilding and re-pushing on every deploy.

## 2. Why & when

You switch to layered JARs whenever a Spring Boot service is packaged into a container image, which for most microservices is essentially always:

- **A plain fat JAR is one opaque blob to Docker.** If a `Dockerfile` just does `COPY app.jar /app.jar`, then *any* code change — even a one-line fix — invalidates that entire `COPY` layer, forcing Docker to re-transfer the whole JAR (dependencies and all) on every build and every deploy, even though the dependencies themselves didn't change.
- **Dependencies change far less often than your own code.** A typical service's dependency set is stable for weeks or months, while its own code changes on every commit — layering by "how often does this change" lets Docker's layer cache do its job: reuse the unchanged dependency layers, rebuild only the small application-code layer.
- **Smaller, more cacheable layers mean faster builds and faster deploys.** Less data to re-transfer to a registry, less data for a Kubernetes node to pull when scheduling a new Pod — directly speeding up the [rolling deployment](0450-rolling-deployment.md)s that happen on every release.
- **You want this as the default packaging for any containerized Spring Boot service** — `spring-boot-maven-plugin` and `spring-boot-gradle-plugin` both produce layered JARs by default in modern Spring Boot versions, and a companion `spring-boot-jarmode-layertools` mechanism lets a `Dockerfile` extract those layers into separate `COPY` instructions.

## 3. Core concept

Think of packing for a long trip using labeled boxes instead of one giant duffel bag: a box of "things I rarely need" (winter gear) versus a box of "things I use every day" (toiletries) can each be handled, replaced, or repacked independently. If you only need to swap out your toiletries, you don't have to touch the winter-gear box at all. A layered JAR groups a Spring Boot application's contents the same way — separating rarely-changing dependency layers from the frequently-changing application-code layer, so touching one doesn't force re-touching the other.

Concretely, Spring Boot's default layering groups a fat JAR's contents into (typically) four layers, ordered from least to most frequently changing:

1. **`dependencies`** — third-party libraries whose versions are stable (not snapshot builds).
2. **`spring-boot-loader`** — the launcher classes themselves (like `JarLauncher`), which almost never change.
3. **`snapshot-dependencies`** — any dependency using a `-SNAPSHOT` version, which changes more often than a released dependency.
4. **`application`** — your own compiled classes and resources, the layer that changes on essentially every commit.

A `Dockerfile` using `spring-boot-jarmode-layertools` extracts these layers into separate directories, then issues one `COPY` instruction per layer, ordered least-to-most-frequently-changing — so Docker's own layer cache can reuse every layer above the one that actually changed, only rebuilding (and only needing to re-transfer) the `application` layer on a typical code-only change.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A layered JAR's four layers, ordered from least to most frequently changing, mapped onto separate Docker image layers">
  <rect x="20" y="20" width="620" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">dependencies -- changes rarely -- Docker layer almost always cached</text>

  <rect x="20" y="80" width="620" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot-loader -- almost never changes</text>

  <rect x="20" y="130" width="620" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">snapshot-dependencies -- changes occasionally</text>

  <rect x="20" y="180" width="620" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="200" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">application -- YOUR code, changes on every commit</text>
  <text x="330" y="216" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">only THIS layer is typically rebuilt and re-pushed</text>
</svg>

Layers stack from least-frequently-changing at the top to most-frequently-changing at the bottom; only the bottom layer is usually touched by a routine code change.

## 5. Runnable example

Layer extraction is normally done by `java -Djarmode=layertools -jar app.jar extract`, a real Spring Boot mechanism — but the underlying idea (grouping files into named buckets by change frequency, then only "rebuilding" the bucket that actually changed) is a plain concept we can demonstrate directly. We start with a basic two-group split, extend it to the realistic four-layer model with a simulated cache check, then handle the hard case: computing exactly which layers a given code change actually invalidates, and confirming the others are reused untouched.

### Level 1 — Basic

```java
// File: LayeredJarBasic.java -- models splitting a JAR's contents into
// TWO layers: dependencies (rarely change) and application code
// (changes often) -- the core idea before adding the full four-layer model.
import java.util.*;

public class LayeredJarBasic {
    static Map<String, List<String>> layers = new LinkedHashMap<>();

    static void addToLayer(String layerName, String fileName) {
        layers.computeIfAbsent(layerName, k -> new ArrayList<>()).add(fileName);
    }

    public static void main(String[] args) {
        addToLayer("dependencies", "spring-core-6.1.jar");
        addToLayer("dependencies", "jackson-databind-2.16.jar");
        addToLayer("application", "OrderService.class");
        addToLayer("application", "OrderController.class");

        System.out.println("[layers] extracted into separate directories:");
        for (Map.Entry<String, List<String>> layer : layers.entrySet()) {
            System.out.println("  " + layer.getKey() + "/: " + layer.getValue());
        }
    }
}
```

How to run: `java LayeredJarBasic.java`

`addToLayer` groups file names under a layer name in `layers`, an ordered map. Dependency JARs and application classes are added to entirely separate buckets, modeling the first, most basic split a layered JAR makes — before any consideration of caching or rebuilds yet.

### Level 2 — Intermediate

```java
// File: LayeredJarWithCache.java -- the SAME layer grouping, now EXTENDED
// to the full four-layer model, with a simulated Docker-style layer
// cache: a layer is only "rebuilt" if its CONTENT HASH differs from what
// was cached on the previous build.
import java.util.*;

public class LayeredJarWithCache {
    static Map<String, List<String>> layers = new LinkedHashMap<>();
    static Map<String, Integer> previousBuildHashes = new HashMap<>(); // layer -> content hash
    static Map<String, Integer> cacheHits = new HashMap<>();

    static void addToLayer(String layerName, String fileName) {
        layers.computeIfAbsent(layerName, k -> new ArrayList<>()).add(fileName);
    }

    static void buildImage() {
        for (Map.Entry<String, List<String>> layer : layers.entrySet()) {
            String layerName = layer.getKey();
            int contentHash = layer.getValue().hashCode();
            Integer previousHash = previousBuildHashes.get(layerName);
            if (previousHash != null && previousHash.equals(contentHash)) {
                System.out.println("[docker] " + layerName + ": CACHE HIT -- reused, not re-transferred");
            } else {
                System.out.println("[docker] " + layerName + ": CACHE MISS -- rebuilt and pushed");
            }
            previousBuildHashes.put(layerName, contentHash);
        }
    }

    public static void main(String[] args) {
        addToLayer("dependencies", "spring-core-6.1.jar");
        addToLayer("dependencies", "jackson-databind-2.16.jar");
        addToLayer("spring-boot-loader", "JarLauncher.class");
        addToLayer("snapshot-dependencies", "internal-shared-lib-1.0-SNAPSHOT.jar");
        addToLayer("application", "OrderService.class");

        System.out.println("--- build 1 (first build, nothing cached yet) ---");
        buildImage();
    }
}
```

How to run: `java LayeredJarWithCache.java`

`buildImage` computes a content hash per layer and compares it to `previousBuildHashes` from a prior run — on this very first build, `previousBuildHashes` is empty, so every layer reports a cache miss, exactly like a fresh image build with no existing cache to reuse.

### Level 3 — Advanced

```java
// File: LayeredJarSelectiveRebuild.java -- the SAME cached, four-layer
// build, now handling the PRODUCTION-FLAVORED case that's the whole point
// of layering: a SECOND build happens after ONLY the application code
// changed. The dependency, loader, and snapshot-dependency layers must
// report CACHE HITS (untouched, not re-transferred); only the application
// layer's hash should differ and get rebuilt.
import java.util.*;

public class LayeredJarSelectiveRebuild {
    static Map<String, List<String>> layers = new LinkedHashMap<>();
    static Map<String, Integer> previousBuildHashes = new HashMap<>();

    static void addToLayer(String layerName, String fileName) {
        layers.computeIfAbsent(layerName, k -> new ArrayList<>()).add(fileName);
    }

    static List<String> buildImage() {
        List<String> rebuiltLayers = new ArrayList<>();
        for (Map.Entry<String, List<String>> layer : layers.entrySet()) {
            String layerName = layer.getKey();
            int contentHash = layer.getValue().hashCode();
            Integer previousHash = previousBuildHashes.get(layerName);
            if (previousHash != null && previousHash.equals(contentHash)) {
                System.out.println("[docker] " + layerName + ": CACHE HIT -- reused, not re-transferred");
            } else {
                System.out.println("[docker] " + layerName + ": CACHE MISS -- rebuilt and pushed");
                rebuiltLayers.add(layerName);
            }
            previousBuildHashes.put(layerName, contentHash);
        }
        return rebuiltLayers;
    }

    public static void main(String[] args) {
        // Build 1: initial state.
        addToLayer("dependencies", "spring-core-6.1.jar");
        addToLayer("dependencies", "jackson-databind-2.16.jar");
        addToLayer("spring-boot-loader", "JarLauncher.class");
        addToLayer("snapshot-dependencies", "internal-shared-lib-1.0-SNAPSHOT.jar");
        addToLayer("application", "OrderService.class (v1)");

        System.out.println("--- build 1 ---");
        buildImage();

        // Build 2: a developer fixes a bug in OrderService -- ONLY the application layer's content changes.
        layers.put("application", new ArrayList<>(List.of("OrderService.class (v2, bugfix)")));

        System.out.println();
        System.out.println("--- build 2 (after a code-only change) ---");
        List<String> rebuilt = buildImage();

        System.out.println();
        System.out.println("[summary] layers rebuilt in build 2: " + rebuilt);
        System.out.println("[summary] dependency, loader, and snapshot-dependency layers were fully reused");
    }
}
```

How to run: `java LayeredJarSelectiveRebuild.java`

Between build 1 and build 2, only `layers.put("application", ...)` changes the map — `dependencies`, `spring-boot-loader`, and `snapshot-dependencies` are left completely untouched. Because `buildImage` computes each layer's hash independently, the three untouched layers hash identically to their `previousBuildHashes` entries on build 2 and report cache hits, while `application`'s new content hashes differently and is the only entry added to `rebuiltLayers` — directly demonstrating the layered JAR's payoff: one small, changed layer rebuilt, three larger, unchanged layers reused as-is.

## 6. Walkthrough

Trace `LayeredJarSelectiveRebuild.main` in order. **First**, all four layers are populated and `buildImage()` runs as build 1. Since `previousBuildHashes` starts empty, every layer's `previousHash` lookup returns `null`, so all four report `CACHE MISS` and get their hashes recorded into `previousBuildHashes` for the first time.

**Next**, `layers.put("application", ...)` replaces only the `application` entry's list with a new one containing `"OrderService.class (v2, bugfix)"` instead of `"OrderService.class (v1)"` — no other layer's entry in the `layers` map is touched at all.

**Then**, build 2 calls `buildImage()` again, iterating the same four layers in the same order. For `dependencies`, `spring-boot-loader`, and `snapshot-dependencies`, each layer's `List<String>` content is byte-for-byte identical to build 1, so `contentHash` matches `previousBuildHashes.get(layerName)` exactly, and each reports `CACHE HIT`.

**After that**, when the loop reaches `application`, its list now contains different content (`"v2, bugfix"` instead of `"v1"`), so `contentHash` differs from the hash recorded during build 1 — the comparison fails, `CACHE MISS` is reported, and `"application"` is appended to `rebuiltLayers`.

**Finally**, `main` prints the summary: `rebuiltLayers` contains exactly one entry, `application` — confirming that a routine, code-only change caused exactly one of the four layers to be rebuilt, while the other three, larger layers (all the actual dependency JARs) were reused untouched, which is the entire efficiency gain layered JARs exist to deliver.

```
--- build 1 ---
[docker] dependencies: CACHE MISS -- rebuilt and pushed
[docker] spring-boot-loader: CACHE MISS -- rebuilt and pushed
[docker] snapshot-dependencies: CACHE MISS -- rebuilt and pushed
[docker] application: CACHE MISS -- rebuilt and pushed

--- build 2 (after a code-only change) ---
[docker] dependencies: CACHE HIT -- reused, not re-transferred
[docker] spring-boot-loader: CACHE HIT -- reused, not re-transferred
[docker] snapshot-dependencies: CACHE HIT -- reused, not re-transferred
[docker] application: CACHE MISS -- rebuilt and pushed

[summary] layers rebuilt in build 2: [application]
[summary] dependency, loader, and snapshot-dependency layers were fully reused
```

## 7. Gotchas & takeaways

> Layer ordering in the `Dockerfile` matters as much as the layering itself: if the `application` layer's `COPY` instruction comes *before* the `dependencies` layer's `COPY` instruction, Docker's cache invalidation cascades downward and defeats the whole purpose — always order `COPY` instructions from least-frequently-changing to most-frequently-changing, exactly as the layer names above are ordered.
- Layered JARs don't change what's *in* the JAR — it's the same fat JAR content as before, just organized so a `Dockerfile` can extract and `COPY` it in separately-cacheable pieces, via `spring-boot-jarmode-layertools`.
- Keep `-SNAPSHOT` dependencies (which change more often than released ones) in their own `snapshot-dependencies` layer, separate from stable `dependencies` — mixing them would force the whole dependency layer to rebuild whenever any snapshot updates.
- This is a build-and-deploy-time optimization layered on top of the [executable fat JAR](0468-spring-boot-executable-fat-jar.md) mechanism — the JAR still runs the same way at runtime; only how it gets *built into an image* changes.
- Faster image builds compound across a fleet: every service benefiting from smaller, cacheable layers means faster CI pipelines and faster, smaller image pulls during a [rolling deployment](0450-rolling-deployment.md) across every node in a cluster.
- Verify layering is actually working by checking image build times and registry push sizes before and after a code-only change — if the dependency layers are still being re-pushed on every deploy, something in the `Dockerfile`'s `COPY` ordering or the layer configuration is wrong.
