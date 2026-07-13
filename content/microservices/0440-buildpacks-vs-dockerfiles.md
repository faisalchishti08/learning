---
card: microservices
gi: 440
slug: buildpacks-vs-dockerfiles
title: "Buildpacks vs Dockerfiles"
---

## 1. What it is

A **Dockerfile** is a hand-written recipe of explicit instructions (`FROM`, `COPY`, `RUN`, `CMD`) that you author and maintain yourself to produce a container image. **Cloud Native Buildpacks** are a standardized, pluggable mechanism that *inspects your source code*, detects what it needs (a JDK, a Maven or Gradle build, the right JRE version), and *automatically* produces a well-layered, reasonably minimal, best-practices-following image — no `Dockerfile` required at all. Spring Boot ships first-class buildpacks support via the `bootBuildImage` Maven/Gradle task, so `./mvnw spring-boot:build-image` or `./gradlew bootBuildImage` produces a production-ready container image directly from your project, with no Docker knowledge needed to get a solid result.

## 2. Why & when

Both approaches produce a container image; the choice is about who's responsible for image-building expertise and how much control versus convenience you want:

- **Dockerfiles give full, explicit control.** Every instruction is visible and hand-authored — if you need an unusual base image, a specific system package, or a custom multi-stage layout, a Dockerfile can do exactly that, because you're writing the recipe yourself.
- **Buildpacks give consistency and reduced maintenance burden across many services.** In an organization with dozens of microservices, having every team hand-write and maintain their own Dockerfile means dozens of independently drifting sets of best practices (or anti-patterns). Buildpacks centralize that expertise: upgrade the buildpack, and every service that uses it picks up improved layering, updated base images, and security patches on its next build, without anyone editing a Dockerfile.
- **Buildpacks handle rebasing patches without rebuilding the application layer.** Because buildpacks separate the OS/runtime layers from the application layer more rigorously than most hand-written Dockerfiles do, a base-image security patch can sometimes be applied to already-built images by swapping just the base layer ("rebasing") — without recompiling or re-pushing the whole application.
- **Dockerfiles are the better fit when your build genuinely needs something non-standard** — an exotic system dependency, a language or framework buildpacks don't support well, or a build process that doesn't map cleanly onto "detect, build, layer."

You reach for buildpacks by default for standard Spring Boot services where "just give me a solid, production-ready image from my source" is the actual goal — which covers most microservices. You reach for a hand-written Dockerfile when you need control buildpacks don't expose, or when your build process is unusual enough that automatic detection doesn't fit.

## 3. Core concept

Think of a Dockerfile like cooking from a recipe you wrote yourself: you control every ingredient and every step, but if you want your dish to reflect the latest food-safety best practices, you have to learn them and update your recipe yourself. A buildpack is like using a well-run meal-kit service: you provide the raw ingredients (your source code), and the service's chefs (the buildpack authors) apply their accumulated expertise — the right technique, the right cooking time, food-safety practices baked in — producing a consistently good result without you needing to become an expert cook. You give up some control over exactly how the dish is prepared, in exchange for consistently good outcomes across every meal you order.

Concretely, a buildpack build works through phases, mirroring (but automating) what a hand-written Dockerfile does manually:

1. **Detect** — the buildpack inspects your source tree (a `pom.xml`, a `build.gradle`, a `.jar`) and decides which buildpacks apply (a JVM buildpack, in Spring Boot's case).
2. **Build** — the detected buildpacks compile the application if needed and gather everything it depends on: the right JRE version, native libraries, application dependencies.
3. **Export as layers** — the result is packaged into an OCI-compliant image (the same standard format a Dockerfile-built image uses), with the buildpack deciding the layer boundaries — typically separating dependencies, the application itself, and buildpack-specific metadata into distinct, independently cacheable layers, similar in spirit to [layered & minimal images](0439-layered-minimal-images.md) but chosen automatically rather than hand-tuned.

Both approaches ultimately produce a standard OCI image — an orchestrator, registry, or runtime can't tell whether an image came from a Dockerfile or a buildpack, and nothing about deployment changes based on which one built it.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Dockerfile is hand-authored by a developer and built with docker build; source code fed to a buildpack is automatically detected, built, and layered without a Dockerfile; both paths converge on a standard OCI image" >
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Dockerfile path</text>
  <rect x="50" y="35" width="200" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">developer hand-writes Dockerfile</text>
  <line x1="150" y1="69" x2="150" y2="95" stroke="#79c0ff"/>
  <rect x="50" y="95" width="200" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="117" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">docker build (explicit steps)</text>

  <text x="490" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Buildpacks path</text>
  <rect x="390" y="35" width="200" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">source code (pom.xml / build.gradle)</text>
  <line x1="490" y1="69" x2="490" y2="95" stroke="#6db33f"/>
  <rect x="390" y="95" width="200" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="117" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">bootBuildImage: detect -&gt; build -&gt; layer</text>

  <line x1="150" y1="129" x2="150" y2="160" stroke="#79c0ff"/>
  <line x1="490" y1="129" x2="490" y2="160" stroke="#6db33f"/>
  <line x1="150" y1="160" x2="320" y2="180" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="490" y1="160" x2="320" y2="180" stroke="#8b949e" stroke-dasharray="3,2"/>

  <rect x="240" y="180" width="160" height="40" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="320" y="204" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">standard OCI image</text>

  <text x="320" y="235" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">runtimes and registries can't tell which path produced it</text>
</svg>

Both paths produce a standard OCI image; the difference is who authors and maintains the build recipe, and how much of the best-practices burden is automated away.

## 5. Runnable example

Scenario: producing an image for `order-service` two ways. We model a hand-written Dockerfile-style build first, then a buildpack-style automatic detect/build/layer pipeline achieving the same result with far less manual specification, then a production-flavored case: a security patch to the base OS that must reach many services, comparing how many artifacts each approach requires touching.

### Level 1 — Basic

```java
// File: DockerfileBuildBasic.java -- models the CORE Dockerfile approach:
// every step is explicit and hand-specified by a developer.
import java.util.*;

public class DockerfileBuildBasic {
    record BuildStep(String instruction, String authoredBy) {}

    public static void main(String[] args) {
        List<BuildStep> dockerfile = List.of(
                new BuildStep("FROM eclipse-temurin:17-jre-alpine", "developer"),
                new BuildStep("WORKDIR /app", "developer"),
                new BuildStep("COPY target/order-service.jar app.jar", "developer"),
                new BuildStep("RUN addgroup -S app && adduser -S app -G app", "developer"),
                new BuildStep("USER app", "developer"),
                new BuildStep("CMD [\"java\",\"-jar\",\"app.jar\"]", "developer")
        );

        System.out.println("Dockerfile has " + dockerfile.size() + " manually authored steps:");
        for (BuildStep step : dockerfile) {
            System.out.println("  [" + step.authoredBy() + "] " + step.instruction());
        }
        System.out.println("Every best practice here (non-root user, slim base) had to be KNOWN and WRITTEN by the developer.");
    }
}
```

How to run: `java DockerfileBuildBasic.java`

Every line in `dockerfile` was authored by a developer who had to already know to use a slim base image and to create and switch to a non-root user — both real security best practices, but ones that only appear here because someone remembered to write them. Nothing enforces that every service's Dockerfile in an organization does this consistently.

### Level 2 — Intermediate

```java
// File: BuildpackDetectBuildLayerIntermediate.java -- the SAME result, now
// via the BUILDPACK model: detect what the source needs, build it, and
// layer the output automatically -- no hand-written recipe at all.
import java.util.*;

public class BuildpackDetectBuildLayerIntermediate {
    record ProjectSignal(String file, String meaning) {}
    record DetectedBuildpack(String name, String reason) {}
    record Layer(String name, boolean automaticallyIncluded) {}

    static List<DetectedBuildpack> detect(List<ProjectSignal> signals) {
        List<DetectedBuildpack> detected = new ArrayList<>();
        for (ProjectSignal s : signals) {
            if (s.file().equals("pom.xml")) detected.add(new DetectedBuildpack("Maven JVM Buildpack", "found pom.xml"));
            if (s.file().equals("build.gradle")) detected.add(new DetectedBuildpack("Gradle JVM Buildpack", "found build.gradle"));
        }
        return detected;
    }

    public static void main(String[] args) {
        List<ProjectSignal> project = List.of(new ProjectSignal("pom.xml", "Maven-based JVM project"));

        List<DetectedBuildpack> detected = detect(project);
        System.out.println("Detected buildpacks: " + detected);

        // The buildpack decides layering AND applies security best practices
        // automatically -- non-root user, minimal base -- without the
        // developer ever writing them down.
        List<Layer> layers = List.of(
                new Layer("base OS (distroless-equivalent)", true),
                new Layer("JRE, selected automatically based on project's target Java version", true),
                new Layer("dependency jars (cached separately from app code)", true),
                new Layer("application classes", true),
                new Layer("non-root user + entrypoint metadata", true)
        );
        System.out.println("Layers produced automatically (no Dockerfile authored):");
        layers.forEach(l -> System.out.println("  " + l.name() + " -- included: " + l.automaticallyIncluded()));
    }
}
```

How to run: `java BuildpackDetectBuildLayerIntermediate.java`

`detect` mirrors the buildpack "detect" phase: inspecting the project for signals (`pom.xml`) rather than requiring the developer to declare a base image at all. The resulting `layers` list includes the same security-conscious choices Level 1's developer had to know and write by hand — a non-root user, a minimal base — but here they're produced automatically by the buildpack's own logic, meaning every project using this buildpack gets them consistently, not just the ones whose author happened to know to add them.

### Level 3 — Advanced

```java
// File: BasePatchRolloutAdvanced.java -- the SAME two approaches, now
// handling a PRODUCTION-FLAVORED hard case: a critical CVE patch to the base
// OS layer must reach 40 services. Compare how many artifacts EACH approach
// requires someone to touch.
import java.util.*;

public class BasePatchRolloutAdvanced {
    record Service(String name, String buildApproach, String pinnedBaseImageInDockerfile) {}

    public static void main(String[] args) {
        List<Service> fleet = new ArrayList<>();
        // 25 services hand-maintain their own Dockerfile with a PINNED base image tag.
        for (int i = 1; i <= 25; i++) {
            fleet.add(new Service("service-" + i, "dockerfile", "eclipse-temurin:17-jre-alpine@sha256:oldpatch"));
        }
        // 15 services use Spring Boot's buildpacks integration -- no pinned
        // base image in any per-service file; the buildpack version controls it centrally.
        for (int i = 26; i <= 40; i++) {
            fleet.add(new Service("service-" + i, "buildpack", null));
        }

        long dockerfileServices = fleet.stream().filter(s -> s.buildApproach().equals("dockerfile")).count();
        long buildpackServices = fleet.stream().filter(s -> s.buildApproach().equals("buildpack")).count();

        System.out.println("Fleet: " + fleet.size() + " services (" + dockerfileServices + " Dockerfile-based, " + buildpackServices + " buildpack-based).");
        System.out.println();
        System.out.println("CVE announced in the base OS image -- rollout required:");
        System.out.println("  Dockerfile-based services: " + dockerfileServices
                + " separate Dockerfiles need editing (bump pinned digest), " + dockerfileServices + " separate rebuild + redeploy pipelines to trigger.");
        System.out.println("  Buildpack-based services:  0 Dockerfiles to edit -- bump ONE buildpack/builder version centrally,"
                + " then rebuild all " + buildpackServices + " with `bootBuildImage` to pick up the patched base automatically.");

        int dockerfileEditsNeeded = (int) dockerfileServices;
        int buildpackEditsNeeded = 1; // one central version bump
        System.out.println();
        System.out.println("Manual edits required: Dockerfile approach=" + dockerfileEditsNeeded + ", buildpack approach=" + buildpackEditsNeeded);
    }
}
```

How to run: `java BasePatchRolloutAdvanced.java`

The hard case is a fleet-wide base-image security patch — exactly the scenario where the two approaches' maintenance burden diverges sharply. The 25 Dockerfile-based services each pinned their own base image digest, meaning a CVE fix requires editing 25 separate files and re-triggering 25 separate pipelines. The 15 buildpack-based services never pinned a base image themselves at all — the buildpack/builder version is the single place that decision lives, so bumping it once and rebuilding is sufficient. This isn't a claim that buildpacks are strictly better; it's the concrete tradeoff: centralized control is easier to patch at scale, but harder to override case-by-case.

## 6. Walkthrough

Trace `BasePatchRolloutAdvanced.main` in order. **First**, `fleet` is populated with 25 `dockerfile`-approach services, each carrying its own `pinnedBaseImageInDockerfile` value (`"eclipse-temurin:17-jre-alpine@sha256:oldpatch"`), and 15 `buildpack`-approach services, whose `pinnedBaseImageInDockerfile` field is `null` — they never specify a base image themselves at all.

**Next**, `dockerfileServices` and `buildpackServices` are counted via `filter` and `count`, yielding `25` and `15` respectively, and the fleet composition is printed.

**Then**, the program reasons about what a CVE-driven base image patch requires under each approach. For the 25 Dockerfile-based services, each one's pinned digest (`sha256:oldpatch`) is baked into its own file — fixing the CVE means editing all 25 files individually to point at a patched digest, then re-running all 25 build pipelines. For the 15 buildpack-based services, no per-service file references a base image digest at all — the patched base ships as part of the buildpack or "builder" version, so bumping that single shared version and re-running `bootBuildImage` across the 15 services picks up the fix without touching any per-service source file.

**Finally**, `dockerfileEditsNeeded` is set to `25` (one edit per pinned Dockerfile) and `buildpackEditsNeeded` is set to `1` (one central version bump), and both are printed — making the scale of the maintenance-burden difference concrete rather than abstract.

```
Fleet: 40 services (25 Dockerfile-based, 15 buildpack-based).

CVE announced in the base OS image -- rollout required:
  Dockerfile-based services: 25 separate Dockerfiles need editing (bump pinned digest), 25 separate rebuild + redeploy pipelines to trigger.
  Buildpack-based services:  0 Dockerfiles to edit -- bump ONE buildpack/builder version centrally, then rebuild all 15 with `bootBuildImage` to pick up the patched base automatically.

Manual edits required: Dockerfile approach=25, buildpack approach=1
```

## 7. Gotchas & takeaways

> Buildpacks' automatic detection can surprise you when a project has ambiguous signals — for instance, a repository containing both a `pom.xml` and leftover build artifacts from a different language can cause the wrong buildpack to be detected, or detection to fail outright. Always verify what a buildpack actually detected and built (`docker inspect` the resulting image, check its layers) rather than assuming "it built successfully" means "it built the way you expected."

- Dockerfiles give explicit, auditable control at the cost of every service needing someone who knows and maintains image-building best practices; buildpacks centralize that expertise at the cost of less fine-grained control per service.
- Spring Boot's `bootBuildImage` (Maven or Gradle) is the buildpacks entry point for a typical Spring Boot service — it requires no `Dockerfile` and produces a layered, reasonably minimal, OCI-compliant image directly from the build.
- Both approaches produce the same kind of artifact — an OCI image — so nothing about deployment, registries (see [image registries & tagging](0441-image-registries-tagging.md)), or orchestration needs to know or care which one built a given image.
- A hybrid approach is common in practice: use buildpacks as the default for standard services, and reserve hand-written Dockerfiles for the few services with genuinely unusual build or runtime requirements.
- Whichever approach you use, the resulting image should still be reviewed against the same [layered & minimal images](0439-layered-minimal-images.md) goals — buildpacks make good defaults easy, not guaranteed for every possible project shape.
