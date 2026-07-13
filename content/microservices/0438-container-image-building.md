---
card: microservices
gi: 438
slug: container-image-building
title: "Container image building"
---

## 1. What it is

**Container image building** is the process of turning source code and its dependencies into a **container image** — a self-contained, immutable, layered filesystem snapshot that a container runtime can start as a running container anywhere, with no additional setup. The most common way to build one is a `Dockerfile`: a text recipe of instructions (base image, copy files, run commands, set the startup command) that a build tool (`docker build`, Kaniko, Buildpacks) executes step by step, producing a tagged image you can push to a registry and run identically on a laptop, a CI runner, or a production cluster.

## 2. Why & when

Building images well matters because the image is the artifact everything downstream depends on — a badly built image causes slow deploys, security exposure, and confusing "works in the image, fails in the container" bugs:

- **Reproducibility.** A `Dockerfile` checked into source control is a precise, versioned recipe — anyone, anywhere, running `docker build` against the same commit produces a functionally identical image. This is what makes [immutable infrastructure](0437-immutable-infrastructure.md) practical: the image *is* the reproducible unit.
- **Startup speed depends on build choices.** How you order instructions, what base image you choose, and how many layers you create all affect image size and how much of it needs to be pulled before a container can start — directly affecting deployment speed and autoscaling responsiveness.
- **Security depends on what ends up in the image.** Every package, tool, and file baked into an image is something that ships to production and something an attacker could potentially exploit — build-time choices are the first and cheapest place to shrink that surface (see [layered & minimal images](0439-layered-minimal-images.md)).
- **Build caching affects developer iteration speed.** A well-ordered `Dockerfile` lets Docker reuse cached layers for unchanged steps (like dependency installation) and only rebuild what actually changed (application code), turning a multi-minute rebuild into a few seconds.

You build a container image any time you need to package a service for containerized deployment — which, given [service instance per container](0435-service-instance-per-container.md) as the modern default, means essentially every microservice, built fresh on every commit that passes CI, tagged, and pushed to a registry as part of the deployment pipeline.

## 3. Core concept

Think of building an image like assembling a sandwich in a specific, deliberate order because some ingredients keep, and some don't. You put the bread down first (a stable, rarely-changing base), then spread the condiments (installed dependencies, which change occasionally), and put the ingredient that changes every single day — today's fresh filling, your actual application code — on top, last. If you assemble it in the wrong order (fresh filling first, bread last), you'd have to redo the whole sandwich every time, but assembling it in *this* order means yesterday's identical bread-and-condiments layers can be reused, and only the top layer needs remaking.

Concretely, a `Dockerfile` build works through these mechanics:

1. **`FROM`** picks the base image — the starting filesystem layer, typically an OS plus a language runtime (e.g., `eclipse-temurin:17-jre`).
2. **Each instruction (`RUN`, `COPY`, `ADD`) creates a new layer**, stacked on top of the previous one. Docker caches each layer; if an instruction and everything above it in the file hasn't changed since the last build, Docker reuses the cached layer instead of re-executing it.
3. **Instruction order should go from least-frequently-changing to most-frequently-changing** — dependency manifests and installation first (changes rarely), application code last (changes on every commit) — to maximize cache reuse and keep rebuilds fast.
4. **`CMD`/`ENTRYPOINT`** defines what process starts when a container is run from the finished image — for a Spring Boot service, typically `java -jar app.jar` or an equivalent launch command.
5. **Multi-stage builds** use one stage (with build tools like Maven or a JDK) to compile the application, then copy only the compiled output into a second, leaner final stage — so the shipped image doesn't carry the build toolchain at all.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Dockerfile is built layer by layer from base image through dependency installation to application code, with unchanged layers reused from cache, producing a final tagged image" >
  <rect x="40" y="30" width="200" height="180" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="140" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Dockerfile instructions</text>
  <rect x="55" y="45" width="170" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">FROM eclipse-temurin:17-jre</text>
  <rect x="55" y="82" width="170" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">COPY pom.xml . / RUN deps</text>
  <rect x="55" y="119" width="170" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="140" y="139" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">COPY src ./src</text>
  <rect x="55" y="156" width="170" height="30" rx="4" fill="#1c2430" stroke="#f0883e"/>
  <text x="140" y="176" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">CMD ["java","-jar","app.jar"]</text>

  <line x1="240" y1="60" x2="300" y2="60" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="240" y1="97" x2="300" y2="97" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="240" y1="134" x2="300" y2="134" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="240" y1="171" x2="300" y2="171" stroke="#8b949e" stroke-dasharray="3,2"/>

  <text x="380" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Layered image (bottom-up)</text>
  <rect x="310" y="156" width="140" height="30" rx="0" fill="#1c2430" stroke="#f0883e"/>
  <text x="380" y="176" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">entrypoint layer</text>
  <rect x="310" y="119" width="140" height="30" rx="0" fill="#1c2430" stroke="#f0883e"/>
  <text x="380" y="139" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">app code (changes often)</text>
  <rect x="310" y="82" width="140" height="30" rx="0" fill="#1c2430" stroke="#79c0ff"/>
  <text x="380" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">dependencies (cached)</text>
  <rect x="310" y="45" width="140" height="30" rx="0" fill="#1c2430" stroke="#6db33f"/>
  <text x="380" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">base image (cached)</text>

  <text x="520" y="90" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">unchanged</text>
  <text x="520" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">layers reused</text>
  <text x="520" y="140" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">changed layers</text>
  <text x="520" y="155" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">rebuilt</text>

  <text x="320" y="230" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">instruction order (rarely-changing first) maximizes cache reuse on rebuild</text>
</svg>

Each Dockerfile instruction produces a stacked layer; ordering rarely-changing instructions first lets Docker reuse cached layers and only rebuild what actually changed.

## 5. Runnable example

Scenario: building an image for `order-service`. Since there's no literal Docker daemon to invoke from plain Java, we model the *build process itself* — layers, caching, and multi-stage builds — as data structures and logic, reasoning about it exactly as a real builder would. We start with a naive single-stage build, add layer-cache-aware ordering, then handle a production-flavored multi-stage build that keeps the final image free of build tooling.

### Level 1 — Basic

```java
// File: ImageBuildBasic.java -- models the CORE idea: a Dockerfile is a
// sequence of instructions, each producing a stacked layer.
import java.util.*;

public class ImageBuildBasic {
    record Instruction(String kind, String detail) {}
    record Layer(Instruction instruction, String digest) {}

    static List<Layer> build(List<Instruction> dockerfile) {
        List<Layer> layers = new ArrayList<>();
        for (Instruction ins : dockerfile) {
            // A real builder hashes the instruction + its inputs; we simulate a digest.
            String digest = "sha256:" + Integer.toHexString((ins.kind() + ins.detail()).hashCode());
            layers.add(new Layer(ins, digest));
            System.out.println("Built layer: " + ins.kind() + " " + ins.detail() + " -> " + digest);
        }
        return layers;
    }

    public static void main(String[] args) {
        List<Instruction> dockerfile = List.of(
                new Instruction("FROM", "eclipse-temurin:17-jre"),
                new Instruction("COPY", "target/order-service.jar app.jar"),
                new Instruction("CMD", "java -jar app.jar"));

        List<Layer> image = build(dockerfile);
        System.out.println("Final image has " + image.size() + " layers.");
    }
}
```

How to run: `java ImageBuildBasic.java`

Each `Instruction` becomes exactly one `Layer`, stacked in order. This is the naive version: every layer is rebuilt every time regardless of whether its inputs changed — there's no caching yet, which means every build, even one that only changed a comment, redoes everything from `FROM` onward.

### Level 2 — Intermediate

```java
// File: ImageBuildWithCaching.java -- the SAME build process, now with
// LAYER CACHING: a layer is reused if its instruction and every layer
// beneath it are unchanged since the last build.
import java.util.*;

public class ImageBuildWithCaching {
    record Instruction(String kind, String detail) {}
    record Layer(Instruction instruction, String digest) {}

    static Map<String, Layer> cache = new HashMap<>(); // digest -> layer, simulating Docker's build cache

    static List<Layer> build(List<Instruction> dockerfile) {
        List<Layer> layers = new ArrayList<>();
        StringBuilder cacheKeyChain = new StringBuilder();
        for (Instruction ins : dockerfile) {
            cacheKeyChain.append(ins.kind()).append(ins.detail());
            String digest = "sha256:" + Integer.toHexString(cacheKeyChain.toString().hashCode());
            if (cache.containsKey(digest)) {
                System.out.println("CACHE HIT:  " + ins.kind() + " " + ins.detail() + " -> " + digest);
                layers.add(cache.get(digest));
            } else {
                System.out.println("CACHE MISS: " + ins.kind() + " " + ins.detail() + " -> " + digest + " (rebuilding)");
                Layer built = new Layer(ins, digest);
                cache.put(digest, built);
                layers.add(built);
            }
        }
        return layers;
    }

    public static void main(String[] args) {
        List<Instruction> dockerfileV1 = List.of(
                new Instruction("FROM", "eclipse-temurin:17-jre"),
                new Instruction("COPY", "pom.xml ."),
                new Instruction("RUN", "mvn dependency:go-offline"),
                new Instruction("COPY", "src ./src"),
                new Instruction("CMD", "java -jar app.jar"));

        System.out.println("--- first build ---");
        build(dockerfileV1);

        // Only the application source changed; the dependency manifest and
        // base image did not.
        List<Instruction> dockerfileV2 = List.of(
                new Instruction("FROM", "eclipse-temurin:17-jre"),
                new Instruction("COPY", "pom.xml ."),
                new Instruction("RUN", "mvn dependency:go-offline"),
                new Instruction("COPY", "src ./src-v2"), // source changed
                new Instruction("CMD", "java -jar app.jar"));

        System.out.println("--- second build (only app code changed) ---");
        build(dockerfileV2);
    }
}
```

How to run: `java ImageBuildWithCaching.java`

`cacheKeyChain` accumulates every prior instruction's text before hashing the current one — exactly how Docker's layer cache works: a layer's cache key depends on everything beneath it, so a change anywhere invalidates every layer above it, not just the changed one. In the second build, the `FROM`, `COPY pom.xml`, and `RUN mvn dependency:go-offline` layers are all cache hits (their inputs and everything beneath them are unchanged), but `COPY src ./src-v2` is a cache miss, and — critically — `CMD` after it is also a miss, purely because it comes after a changed layer, even though its own text didn't change.

### Level 3 — Advanced

```java
// File: MultiStageBuildAdvanced.java -- the SAME build model, now handling
// a PRODUCTION-FLAVORED hard case: a MULTI-STAGE build, where a heavy build
// stage (with Maven + JDK) compiles the app, and only the compiled artifact
// is copied into a lean final stage -- the build tools never ship.
import java.util.*;

public class MultiStageBuildAdvanced {
    record Instruction(String kind, String detail, int approxSizeMb) {}
    record Stage(String name, List<Instruction> instructions) {}

    static int stageSizeMb(Stage stage) {
        return stage.instructions().stream().mapToInt(Instruction::approxSizeMb).sum();
    }

    public static void main(String[] args) {
        Stage buildStage = new Stage("build", List.of(
                new Instruction("FROM", "maven:3.9-eclipse-temurin-17 AS build", 650),
                new Instruction("COPY", "pom.xml .", 0),
                new Instruction("RUN", "mvn dependency:go-offline", 180),
                new Instruction("COPY", "src ./src", 2),
                new Instruction("RUN", "mvn package -DskipTests", 45) // produces target/order-service.jar
        ));

        // The final stage starts from a FRESH, minimal base -- it does NOT
        // inherit anything from buildStage except the one artifact we
        // explicitly COPY --from=build.
        Stage finalStage = new Stage("final", List.of(
                new Instruction("FROM", "eclipse-temurin:17-jre-alpine", 85),
                new Instruction("COPY --from=build", "/app/target/order-service.jar app.jar", 45),
                new Instruction("CMD", "java -jar app.jar", 0)
        ));

        int buildStageSize = stageSizeMb(buildStage);
        int finalImageSize = stageSizeMb(finalStage);

        System.out.println("Build stage total footprint: " + buildStageSize + "Mi (includes Maven + JDK + deps -- NEVER shipped)");
        System.out.println("Final shipped image size:    " + finalImageSize + "Mi (JRE + the compiled jar only)");
        System.out.println("Size reduction vs shipping the build stage: "
                + Math.round(100.0 * (buildStageSize - finalImageSize) / buildStageSize) + "%");

        boolean buildToolsInFinalImage = finalStage.instructions().stream()
                .anyMatch(i -> i.detail().contains("mvn") || i.detail().contains("maven"));
        System.out.println("Build tools present in shipped image: " + buildToolsInFinalImage
                + " -- the attack surface and size of the SHIPPED artifact are independent of the BUILD toolchain's size.");
    }
}
```

How to run: `java MultiStageBuildAdvanced.java`

The hard case multi-stage builds solve is that compiling a JVM application typically needs Maven, a full JDK, and every resolved dependency on disk — hundreds of megabytes that have nothing to do with what the *running* service needs. `buildStage` models that heavy toolchain; `finalStage` starts completely fresh from a minimal JRE base and pulls in only the one compiled artifact via `COPY --from=build`. The final image never sees Maven, the JDK compiler, or any intermediate build output — only the `.jar` it needs to run, which is the mechanism behind [layered & minimal images](0439-layered-minimal-images.md).

## 6. Walkthrough

Trace `MultiStageBuildAdvanced.main` in order. **First**, `buildStage` is defined with five instructions: a heavy Maven+JDK base (`650Mi`), an empty `COPY pom.xml` (`0Mi`, just metadata), dependency resolution (`180Mi` of downloaded `.jar` dependencies), copying source (`2Mi`), and running `mvn package` (`45Mi`, the compiled artifact and intermediate build state). `stageSizeMb(buildStage)` sums these to `650 + 0 + 180 + 2 + 45 = 877`.

**Next**, `finalStage` is defined separately, starting `FROM eclipse-temurin:17-jre-alpine` (`85Mi`, a minimal JRE-only base with no compiler or build tools), then `COPY --from=build` pulls in just the compiled `.jar` (`45Mi`) from the build stage's filesystem — not the whole build stage, just that one named artifact. `CMD` adds `0Mi`. `stageSizeMb(finalStage)` sums to `85 + 45 + 0 = 130`.

**Then**, the program prints both totals: the build stage's `877Mi` footprint (which existed only transiently during the build and is discarded afterward) versus the final shipped image's `130Mi`. The reduction is computed as `round(100 * (877 - 130) / 877)`, which is approximately `85%`.

**Finally**, `buildToolsInFinalImage` checks whether any instruction in `finalStage` references Maven — it doesn't, so this is `false`, confirming that the heavy build toolchain genuinely never makes it into what ships to production.

```
Build stage total footprint: 877Mi (includes Maven + JDK + deps -- NEVER shipped)
Final shipped image size:    130Mi (JRE + the compiled jar only)
Size reduction vs shipping the build stage: 85%
Build tools present in shipped image: false -- the attack surface and size of the SHIPPED artifact are independent of the BUILD toolchain's size.
```

## 7. Gotchas & takeaways

> A `.dockerignore` file (analogous to `.gitignore`) is easy to forget and expensive when you do: without it, `COPY . .` can pull your entire `.git` history, local `target/` build output, or IDE configuration into the build context and, worse, into a layer — bloating the image and occasionally leaking files (like a locally cached credentials file) that were never meant to ship.

- Order `Dockerfile` instructions from least-frequently-changing to most-frequently-changing (base image, then dependencies, then application code) to maximize layer cache reuse and keep everyday rebuilds fast.
- Multi-stage builds are the standard way to keep a heavy build toolchain (Maven, a full JDK, native compilers) out of the image that actually ships — only `COPY --from=<stage>` the compiled artifact forward.
- The image produced here is the artifact [immutable infrastructure](0437-immutable-infrastructure.md) depends on — build it once per version, never patch a running container derived from it.
- Once built, an image needs a stable, versioned identity to be deployed reliably — see [image registries & tagging](0441-image-registries-tagging.md) for how images are published and referenced afterward.
- For Spring Boot specifically, the framework's own layered JAR support and Cloud Native Buildpacks integration can generate a well-layered, cache-friendly image without hand-writing a `Dockerfile` at all — see [buildpacks vs Dockerfiles](0440-buildpacks-vs-dockerfiles.md) for that tradeoff.
