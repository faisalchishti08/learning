---
card: spring-cloud
gi: 2
slug: release-trains-version-naming-calendar-versions
title: "Release trains & version naming (calendar versions)"
---

## 1. What it is

Spring Cloud ships as a "release train" — a coordinated set of independently versioned sub-projects (Spring Cloud Config, Spring Cloud Gateway, Spring Cloud OpenFeign, and dozens more) released together under one umbrella name, historically alphabetic code names (Hoxton, Greenwich) and now calendar-based versions (`2023.0.x`, `2024.0.x`), guaranteeing that the specific versions bundled together are tested to work with each other.

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-dependencies</artifactId>
            <version>2024.0.0</version> <!-- the release train version -->
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

## 2. Why & when

Spring Cloud isn't one library — it's dozens of separately developed, separately versioned projects. Without coordination, picking compatible versions of Spring Cloud Config, Spring Cloud Gateway, and Spring Cloud LoadBalancer by hand would mean checking a compatibility matrix for every possible combination. The release train exists to remove that problem entirely: pick one train version, and every sub-project version it pulls in is guaranteed to have been tested together.

Reach for release-train version management when:

- Starting or upgrading any Spring Cloud-based project — the train version is the single number that determines every sub-project's compatible version.
- Ensuring a Spring Boot version and a Spring Cloud train version are compatible — each Spring Cloud release train targets specific Spring Boot major/minor versions, and mismatches are a common source of startup failures.
- Reading Spring Cloud release notes or migration guides — they're organized by train name/version, not by individual sub-project version.

## 3. Core concept

```
 Release train "2024.0.0" bundles compatible versions of:
   - spring-cloud-config          (some specific version)
   - spring-cloud-gateway          (some specific version)
   - spring-cloud-openfeign         (some specific version)
   - spring-cloud-loadbalancer       (some specific version)
   - ... dozens more

 Your pom.xml/build.gradle declares ONE train version via the BOM (next card)
   -> every spring-cloud-* dependency you add resolves to its train-compatible version automatically
   -> no need to specify individual sub-project versions yourself
```

One version number picks a whole compatible constellation of sub-project versions, rather than each being chosen independently.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One release train version fans out to compatible versions of several independent Spring Cloud sub-projects">
  <rect x="250" y="20" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">2024.0.0</text>

  <line x1="280" y1="60" x2="100" y2="100" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="320" y1="60" x2="320" y2="100" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="360" y1="60" x2="540" y2="100" stroke="#8b949e" stroke-width="1.2"/>

  <rect x="20" y="105" width="160" height="35" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="127" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">spring-cloud-config</text>

  <rect x="240" y="105" width="160" height="35" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">spring-cloud-gateway</text>

  <rect x="460" y="105" width="160" height="35" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="127" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">spring-cloud-openfeign</text>
</svg>

One train version resolves to a whole set of mutually compatible sub-project versions.

## 5. Runnable example

The scenario: modeling how a build resolves Spring Cloud dependency versions, evolving from manually picking each sub-project version independently (the error-prone baseline), to a train-version-driven resolution mapping one train to many sub-project versions, to a check that rejects an incompatible Spring Boot/Spring Cloud train pairing before the build even proceeds.

### Level 1 — Basic

Show the manual, error-prone baseline: picking each sub-project's version independently, with no guarantee they actually work together.

```java
import java.util.*;

public class ReleaseTrainLevel1 {
    public static void main(String[] args) {
        Map<String, String> manuallyChosenVersions = new LinkedHashMap<>();
        manuallyChosenVersions.put("spring-cloud-config", "4.1.0");
        manuallyChosenVersions.put("spring-cloud-gateway", "4.0.9"); // picked independently -- maybe incompatible!
        manuallyChosenVersions.put("spring-cloud-openfeign", "4.1.1"); // also picked independently

        System.out.println("Manually chosen versions (compatibility unverified):");
        manuallyChosenVersions.forEach((project, version) -> System.out.println("  " + project + " -> " + version));
        // Nothing here confirms these three versions were ever tested together.
    }
}
```

How to run: `java ReleaseTrainLevel1.java`

Each version is chosen in isolation — nothing here verifies `spring-cloud-gateway:4.0.9` was ever tested alongside `spring-cloud-config:4.1.0`, which is exactly the coordination gap release trains close.

### Level 2 — Intermediate

Add a release-train resolver: one train version maps to a known-compatible set of sub-project versions, mirroring what the Spring Cloud BOM provides.

```java
import java.util.*;

public class ReleaseTrainLevel2 {
    public static void main(String[] args) {
        ReleaseTrainCatalog catalog = new ReleaseTrainCatalog();
        catalog.registerTrain("2024.0.0", Map.of(
            "spring-cloud-config", "4.1.3",
            "spring-cloud-gateway", "4.1.5",
            "spring-cloud-openfeign", "4.1.3"
        ));

        Map<String, String> resolved = catalog.resolve("2024.0.0"); // ONE version picks the whole set
        System.out.println("Resolved from train 2024.0.0:");
        resolved.forEach((project, version) -> System.out.println("  " + project + " -> " + version));
    }
}

// Stands in for the spring-cloud-dependencies BOM's version resolution.
class ReleaseTrainCatalog {
    private final Map<String, Map<String, String>> trains = new HashMap<>();
    void registerTrain(String trainVersion, Map<String, String> subProjectVersions) {
        trains.put(trainVersion, subProjectVersions);
    }
    Map<String, String> resolve(String trainVersion) {
        return trains.getOrDefault(trainVersion, Map.of());
    }
}
```

How to run: `java ReleaseTrainLevel2.java`

`resolve("2024.0.0")` returns a full, mutually-tested set of sub-project versions from a single input — exactly what declaring one `spring-cloud-dependencies` BOM version does in a real Maven or Gradle build, instead of specifying each sub-project's version by hand.

### Level 3 — Advanced

Add a Spring Boot compatibility check: reject a train/Boot version pairing that isn't supported, the way a real build fails fast on an incompatible combination rather than surfacing confusing errors deep into startup.

```java
import java.util.*;

public class ReleaseTrainLevel3 {
    public static void main(String[] args) {
        ReleaseTrainCatalog catalog = new ReleaseTrainCatalog();
        catalog.registerTrain("2024.0.0", Map.of("spring-cloud-gateway", "4.1.5"), "3.4");
        catalog.registerTrain("2023.0.0", Map.of("spring-cloud-gateway", "4.0.9"), "3.2");

        System.out.println(tryResolve(catalog, "2024.0.0", "3.4")); // compatible pairing
        System.out.println(tryResolve(catalog, "2024.0.0", "3.1"));  // INCOMPATIBLE -- old Boot with new train
    }

    static String tryResolve(ReleaseTrainCatalog catalog, String trainVersion, String bootVersion) {
        try {
            Map<String, String> resolved = catalog.resolveChecked(trainVersion, bootVersion);
            return "OK: train " + trainVersion + " + Boot " + bootVersion + " -> " + resolved;
        } catch (IllegalStateException e) {
            return "REJECTED: " + e.getMessage();
        }
    }
}

class ReleaseTrainCatalog {
    private final Map<String, Map<String, String>> trainDependencies = new HashMap<>();
    private final Map<String, String> trainRequiredBoot = new HashMap<>();

    void registerTrain(String trainVersion, Map<String, String> subProjectVersions, String requiredBootVersion) {
        trainDependencies.put(trainVersion, subProjectVersions);
        trainRequiredBoot.put(trainVersion, requiredBootVersion);
    }

    Map<String, String> resolveChecked(String trainVersion, String bootVersion) {
        String requiredBoot = trainRequiredBoot.get(trainVersion);
        if (requiredBoot == null) throw new IllegalStateException("unknown train: " + trainVersion);
        if (!bootVersion.equals(requiredBoot)) {
            throw new IllegalStateException(
                "train " + trainVersion + " requires Spring Boot " + requiredBoot + ", got " + bootVersion);
        }
        return trainDependencies.get(trainVersion);
    }
}
```

How to run: `java ReleaseTrainLevel3.java`

The first call succeeds because `2024.0.0` was registered as requiring Boot `3.4`, exactly what's supplied. The second call fails fast with a clear, specific message identifying the actual mismatch — mirroring how a real Spring Cloud/Spring Boot version incompatibility is best caught at build-configuration time, rather than discovered later through a confusing runtime failure.

## 6. Walkthrough

Execution starts in `main` for Level 3. Two release trains are registered, each tied to a specific required Spring Boot version. `tryResolve(catalog, "2024.0.0", "3.4")` calls `resolveChecked`, which finds `requiredBoot = "3.4"` for that train, compares it against the supplied `"3.4"`, finds a match, and returns the resolved dependency map:

```
OK: train 2024.0.0 + Boot 3.4 -> {spring-cloud-gateway=4.1.5}
```

`tryResolve(catalog, "2024.0.0", "3.1")` repeats the same check, but this time `"3.1"` doesn't match the registered `"3.4"` requirement — `resolveChecked` throws `IllegalStateException` with a message naming both the expected and actual Boot versions, caught and reported by the calling `tryResolve`:

```
REJECTED: train 2024.0.0 requires Spring Boot 3.4, got 3.1
```

In a real project, this exact kind of mismatch — an old Spring Boot version paired with a Spring Cloud train that targets a newer one — is one of the most common sources of confusing startup failures (missing beans, `NoSuchMethodError`s from incompatible transitive dependencies). Checking the official Spring Cloud release train compatibility table before upgrading either Boot or the Cloud train independently avoids exactly this class of problem.

## 7. Gotchas & takeaways

> Gotcha: upgrading a Spring Boot version without also checking whether the currently-declared Spring Cloud train version still supports it (or vice versa) is one of the most common sources of hard-to-diagnose startup failures in Spring Cloud projects — always check the compatibility table when bumping either version independently.

> Gotcha: calendar versioning (`2024.0.x`) replaced the earlier alphabetic code-name scheme (Hoxton, Greenwich, ...) — older documentation, blog posts, and Stack Overflow answers referencing code names can be confusing for newcomers who only know the newer numeric scheme; the underlying concept (a coordinated, compatible bundle of sub-project versions) is unchanged.

- A Spring Cloud release train bundles independently developed sub-projects at mutually tested, compatible versions under one umbrella version number.
- Declaring the train version once (via the BOM, next card) resolves every `spring-cloud-*` dependency's version automatically, removing the need to hand-pick compatible sub-project versions.
- Each release train targets specific Spring Boot versions — pairing an incompatible train and Boot version is a common source of confusing startup failures.
- Calendar versioning (`YYYY.0.x`) is the current naming scheme, having replaced the earlier alphabetic code names, though both refer to the same underlying release-train concept.
