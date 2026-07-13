---
card: microservices
gi: 439
slug: layered-minimal-images
title: "Layered & minimal images"
---

## 1. What it is

**Layered images** organize a container image's filesystem as a stack of independently cacheable, independently shareable layers rather than one monolithic blob. **Minimal images** deliberately strip an image down to only what the running application actually needs — a small base OS (or none at all), a runtime, and the application itself, leaving out compilers, package managers, shells, and debugging tools that a full-featured OS image would normally include. The two ideas reinforce each other: good layering makes an image fast to build and pull, and minimalism makes each layer, and the whole image, smaller and safer.

## 2. Why & when

These two properties matter because image size and composition directly drive deployment speed, cost, and security exposure, all of which compound at microservices scale:

- **Faster pulls, faster scaling.** Every time an orchestrator schedules a new container on a host that doesn't already have the image cached, it must pull every layer not already present. A 900Mi image with a bloated base pulls dramatically slower than a 120Mi minimal one — directly slowing down autoscaling response time and rolling deployments.
- **Smaller attack surface.** A shell, a package manager, or a compiler baked into a production image is a tool an attacker who gains any foothold can use to explore, download more tools, or pivot — none of which they can do if those binaries simply aren't present. Minimal (and especially "distroless") images remove this tooling entirely.
- **Shared layers save bandwidth and disk across services.** If many of your services share the same base image layer, hosts that already have that layer cached from one service's image don't need to re-pull it for another — layering turns "the base image" into a one-time cost amortized across your whole fleet, not a per-service cost.
- **Fewer things to patch.** Every package in an image is a package that might have a CVE announced against it someday. Fewer packages means fewer CVE scan hits and fewer things you need to track and rebuild for.

You care about layering and minimalism on every image you build for production, but the payoff is largest in high-scale, frequently-scaling, or security-sensitive environments — a rarely-deployed internal tool can tolerate a bloated image more comfortably than a public-facing service that autoscales aggressively under load.

## 3. Core concept

Picture packing a suitcase for a work trip versus packing a moving truck for a full house relocation. A minimal, well-layered image is the suitcase: you bring exactly the shirt, the charger, the toothbrush you need, nothing more, and everything is organized in labeled, separable pouches so airport security (or anyone inspecting it) can see exactly what's there and nothing is buried under things you don't need. A bloated image is the moving truck packed by throwing everything from the house in indiscriminately — technically it contains what you need too, but finding it, moving it, and securing it all is far more expensive than it has to be.

Concretely, the two ideas work through mechanisms already touched on in [container image building](0438-container-image-building.md):

1. **Layer sharing across images.** If `order-service` and `payment-service` both build `FROM eclipse-temurin:17-jre-alpine`, a host that already has that base layer cached from running `order-service` doesn't need to pull it again for `payment-service` — the registry and runtime both recognize layers by content digest, not by which image "owns" them.
2. **Minimal base images strip the OS down.** Options range from a full OS distribution (large, includes a shell and package manager), to a slim distribution (`-slim`, `-alpine` variants — smaller, still has a shell), to "distroless" (no shell, no package manager, just the runtime and its direct C library dependencies), to `FROM scratch` (nothing at all — only works for fully static binaries).
3. **Multi-stage builds keep build-time tooling out of the final layers entirely** — the mechanism described in [container image building](0438-container-image-building.md) is what makes "small final image, however large the build process needs to be" possible.
4. **Layer ordering affects both cache reuse and final size** — combining multiple `RUN` instructions that each leave behind temporary files into one instruction (cleaning up in the same layer they were created in) avoids a layer that adds bytes another layer merely marks as deleted; deleted files in an earlier layer still occupy space in the image because layers are additive and immutable.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bloated image built on a full OS base carries a shell, package manager, and unused tools in large layers; a minimal distroless image strips those out, leaving small layers with only the runtime and application, resulting in a much smaller total size" >
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Bloated image</text>
  <rect x="60" y="35" width="180" height="26" fill="#1c2430" stroke="#f85149"/>
  <text x="150" y="53" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">full OS + shell + pkg mgr (~700Mi)</text>
  <rect x="60" y="61" width="180" height="26" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="79" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">build tools left behind (~300Mi)</text>
  <rect x="60" y="87" width="180" height="26" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">app + deps (~120Mi)</text>
  <text x="150" y="135" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">total: ~1120Mi</text>

  <text x="480" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Minimal, layered image</text>
  <rect x="390" y="35" width="180" height="20" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="49" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">distroless base (~25Mi)</text>
  <rect x="390" y="55" width="180" height="20" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="69" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JRE runtime (~60Mi)</text>
  <rect x="390" y="75" width="180" height="20" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">app + deps (~45Mi)</text>
  <text x="480" y="115" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">total: ~130Mi</text>

  <text x="320" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no shell, no package manager, no build tools = smaller pulls</text>
  <text x="320" y="178" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">and a much smaller surface for an attacker to exploit</text>
</svg>

Stripping unnecessary OS tooling and keeping build artifacts out of the shipped layers shrinks both image size and attack surface dramatically.

## 5. Runnable example

Scenario: shrinking `order-service`'s image. We model computing total image size from its layers first, then compare base-image choices and their effect on both size and attack surface, then handle a production-flavored case: verifying a "minimal" image genuinely removed dangerous tooling, not just shrunk in size coincidentally.

### Level 1 — Basic

```java
// File: ImageSizeBasic.java -- models the CORE idea: an image's total size
// is the sum of its layer sizes, and swapping layers changes the total.
import java.util.*;

public class ImageSizeBasic {
    record Layer(String description, int sizeMb) {}

    static int totalSize(List<Layer> layers) {
        return layers.stream().mapToInt(Layer::sizeMb).sum();
    }

    public static void main(String[] args) {
        List<Layer> bloated = List.of(
                new Layer("full OS base (ubuntu:22.04)", 77),
                new Layer("apt-get install build tools", 310),
                new Layer("JRE runtime", 200),
                new Layer("app + dependencies", 120));

        List<Layer> minimal = List.of(
                new Layer("distroless base", 25),
                new Layer("JRE runtime (slim)", 60),
                new Layer("app + dependencies", 45));

        System.out.println("Bloated image total: " + totalSize(bloated) + "Mi");
        System.out.println("Minimal image total: " + totalSize(minimal) + "Mi");
        System.out.println("Reduction: " + (totalSize(bloated) - totalSize(minimal)) + "Mi");
    }
}
```

How to run: `java ImageSizeBasic.java`

`totalSize` simply sums each layer's declared size, mirroring how a registry reports an image's total pull size. Swapping a full OS base and its build tooling for a distroless base and a slim runtime cuts the total from `707Mi` to `130Mi` — the same application code, a very different image.

### Level 2 — Intermediate

```java
// File: BaseImageComparisonIntermediate.java -- the SAME sizing idea, now
// modeling the FULL vs SLIM vs DISTROLESS base image spectrum, tracking
// which tooling (shell, package manager, compiler) each option carries.
import java.util.*;

public class BaseImageComparisonIntermediate {
    record BaseImage(String name, int sizeMb, Set<String> includedTools) {}

    static final BaseImage FULL = new BaseImage("ubuntu:22.04", 77, Set.of("bash", "apt", "curl", "python3"));
    static final BaseImage SLIM = new BaseImage("eclipse-temurin:17-jre-alpine", 85, Set.of("sh", "apk"));
    static final BaseImage DISTROLESS = new BaseImage("gcr.io/distroless/java17-debian12", 25, Set.of());

    static void describe(BaseImage base) {
        System.out.println(base.name() + " (" + base.sizeMb() + "Mi base)");
        System.out.println("  shell available:            " + base.includedTools().stream().anyMatch(t -> t.equals("bash") || t.equals("sh")));
        System.out.println("  package manager available:  " + base.includedTools().stream().anyMatch(t -> t.equals("apt") || t.equals("apk")));
        System.out.println("  an attacker who gets a foothold could use: " + base.includedTools());
    }

    public static void main(String[] args) {
        describe(FULL);
        describe(SLIM);
        describe(DISTROLESS);
    }
}
```

How to run: `java BaseImageComparisonIntermediate.java`

`BaseImage` tracks not just size but *which tools ship inside*. `FULL` carries a shell and multiple utilities an attacker could use to explore or exfiltrate; `SLIM` still carries a minimal shell and package manager; `DISTROLESS` carries neither — its `includedTools()` set is empty. This makes the attack-surface tradeoff concrete: even where `DISTROLESS` and `SLIM` are close in size, the *absence* of a shell entirely (not just a smaller one) is the qualitatively different security property distroless images provide.

### Level 3 — Advanced

```java
// File: MinimalImageVerificationAdvanced.java -- the SAME comparison, now
// handling a PRODUCTION-FLAVORED hard case: verifying, layer by layer, that
// a "minimal" image build genuinely excludes dangerous tooling and doesn't
// accidentally reintroduce it via a later, careless layer.
import java.util.*;

public class MinimalImageVerificationAdvanced {
    record Layer(String instruction, int sizeMb, Set<String> introducedTools) {}

    static final Set<String> DANGEROUS_TOOLS = Set.of("bash", "sh", "curl", "wget", "apt", "apk", "python", "gcc");

    static List<String> auditImage(List<Layer> layers) {
        List<String> findings = new ArrayList<>();
        Set<String> cumulativeTools = new TreeSet<>();
        int cumulativeSize = 0;
        for (Layer layer : layers) {
            cumulativeSize += layer.sizeMb();
            cumulativeTools.addAll(layer.introducedTools());
            Set<String> dangerousHere = new TreeSet<>(layer.introducedTools());
            dangerousHere.retainAll(DANGEROUS_TOOLS);
            if (!dangerousHere.isEmpty()) {
                findings.add("Layer '" + layer.instruction() + "' introduces dangerous tooling: " + dangerousHere);
            }
        }
        System.out.println("Cumulative image size: " + cumulativeSize + "Mi");
        System.out.println("Cumulative tools present in final image: " + cumulativeTools);
        return findings;
    }

    public static void main(String[] args) {
        // A build that LOOKS minimal (distroless base) but accidentally
        // reintroduces a shell via a later "just for debugging" layer that
        // never got removed before shipping.
        List<Layer> accidentallyBloated = List.of(
                new Layer("FROM gcr.io/distroless/java17-debian12", 25, Set.of()),
                new Layer("COPY app.jar app.jar", 45, Set.of()),
                new Layer("RUN apt-get install -y curl # left in from debugging a startup issue", 40, Set.of("apt", "curl")),
                new Layer("CMD [\"java\",\"-jar\",\"app.jar\"]", 0, Set.of())
        );

        List<String> findings = auditImage(accidentallyBloated);
        System.out.println();
        if (findings.isEmpty()) {
            System.out.println("Audit PASSED: no dangerous tooling found.");
        } else {
            System.out.println("Audit FAILED:");
            findings.forEach(f -> System.out.println("  - " + f));
        }
    }
}
```

How to run: `java MinimalImageVerificationAdvanced.java`

The hard case is that starting from a genuinely minimal base doesn't guarantee the *final* image stays minimal — a later, seemingly innocuous layer (installing `curl` "just for debugging" and forgetting to remove it before shipping) silently reintroduces exactly the tooling a distroless base was chosen to avoid. `auditImage` walks every layer, not just the base, checking each one's `introducedTools` against a `DANGEROUS_TOOLS` set — catching drift a size-only check would miss, since the added layer is small (`40Mi`) and wouldn't obviously stand out in a size report alone.

## 6. Walkthrough

Trace `MinimalImageVerificationAdvanced.main` in order. **First**, `accidentallyBloated` is built as four layers: a distroless base (`25Mi`, no tools), copying the app jar (`45Mi`, no tools), a `RUN apt-get install -y curl` layer left over from debugging (`40Mi`, introduces `apt` and `curl`), and the `CMD` instruction (`0Mi`, no tools).

**Next**, `auditImage` iterates the layers in order. For the base layer, `cumulativeSize` becomes `25`, `cumulativeTools` stays empty, and `dangerousHere` (the intersection of this layer's tools with `DANGEROUS_TOOLS`) is empty — no finding. For the `COPY app.jar` layer, `cumulativeSize` becomes `70`, still no tools introduced, no finding.

**Then**, for the `RUN apt-get install -y curl` layer, `cumulativeSize` becomes `110`, `cumulativeTools` gains `apt` and `curl`. `dangerousHere` computes the intersection of `{apt, curl}` with `DANGEROUS_TOOLS`, which is `{apt, curl}` — non-empty, so a finding is appended: `"Layer 'RUN apt-get install -y curl # left in from debugging a startup issue' introduces dangerous tooling: [apt, curl]"`. The final `CMD` layer adds nothing further.

**Finally**, `main` prints the cumulative size (`110Mi`) and cumulative tools (`[apt, curl]`), then reports the audit as `FAILED`, printing the one finding — even though the image *started* from a genuinely distroless, tool-free base, and even though its total size is still fairly small, the audit correctly flags that a shell-adjacent package manager and network tool made it into the shipped image.

```
Cumulative image size: 110Mi
Cumulative tools present in final image: [apt, curl]

Audit FAILED:
  - Layer 'RUN apt-get install -y curl # left in from debugging a startup issue' introduces dangerous tooling: [apt, curl]
```

## 7. Gotchas & takeaways

> A layer that deletes a file does not shrink the image: because layers are additive and immutable, deleting a file in a later `RUN` only adds a "this file is gone" marker on top — the bytes from the earlier layer that created the file are still present in the image and still get pulled. Anything you don't want in the final image must never be written in an earlier layer that ships, which is exactly why multi-stage builds (see [container image building](0438-container-image-building.md)) exist: the discarded stage's layers never become part of the final image at all.

- Distroless (or `scratch`, for statically linked binaries) images remove the shell and package manager entirely — a qualitatively stronger security property than merely using a smaller base image that still includes them.
- Combine related `RUN` instructions and clean up temporary files within the *same* layer they were created in; cleaning up in a later layer doesn't reduce image size, only cache behavior.
- Multiple services sharing the same base image layer pull and cache that layer once per host, not once per service — standardizing on a small set of base images across your fleet compounds the size benefit.
- Periodically re-audit "minimal" images, not just at initial build time — debugging tools added temporarily and forgotten are a common, easy-to-miss way minimalism erodes over time.
- Buildpacks (see [buildpacks vs Dockerfiles](0440-buildpacks-vs-dockerfiles.md)) and Spring Boot's layered JAR support both automate producing well-layered, reasonably minimal images without hand-tuning a `Dockerfile` yourself.
