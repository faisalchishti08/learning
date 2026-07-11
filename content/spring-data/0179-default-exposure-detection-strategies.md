---
card: spring-data
gi: 179
slug: default-exposure-detection-strategies
title: "Default exposure & detection strategies"
---

## 1. What it is

`RepositoryDetectionStrategy` controls, application-wide, *which* repositories Spring Data REST considers exposable in the first place, before any per-repository `@RepositoryRestResource` override is even consulted. Its `RepositoryDetectionStrategies` enum offers four policies: `DEFAULT`, `ALL`, `ANNOTATED`, and `VISIBILITY`.

```java
@Configuration
class RestConfig implements RepositoryRestConfigurer {
    public void configureRepositoryRestConfiguration(RepositoryRestConfiguration config, CorsRegistry cors) {
        config.setRepositoryDetectionStrategy(RepositoryDetectionStrategies.ANNOTATED);
    }
}
```

## 2. Why & when

The previous card's `@RepositoryRestResource(exported = false)` controls exposure *per repository*, opting individual ones out. Detection strategy flips the default the other way around for the *entire application*: instead of "everything exposed unless explicitly hidden," you can require every repository to explicitly opt *in* to exposure. For an application with many internal-only repositories, this inverted default is both safer and less repetitive.

Reach for a non-default detection strategy when:

- Most repositories in the application are internal, and only a handful should ever be public REST endpoints — `ANNOTATED` mode makes "exposed" the exception rather than the rule.
- You want exposure driven by visibility (`public` vs. package-private interfaces) rather than by an annotation — `VISIBILITY` mode.
- The application genuinely wants every repository exposed automatically and doesn't want to think about it per-repository — `ALL` mode, closest to Spring Data REST's historical default behavior.

## 3. Core concept

```
 DEFAULT     -- exposes every public repository UNLESS @RepositoryRestResource(exported = false)
 ALL          -- exposes every repository, public or not, ignoring visibility entirely
 ANNOTATED    -- exposes ONLY repositories explicitly marked @RepositoryRestResource(exported = true)
 VISIBILITY   -- exposes a repository only if BOTH it and its entity are public

 config.setRepositoryDetectionStrategy(RepositoryDetectionStrategies.ANNOTATED)
   -> CustomerRepository (no annotation)        -> NOT exposed
   -> ProductRepository (@RepositoryRestResource) -> exposed
```

The strategy decides the *default* exposure outcome application-wide; `@RepositoryRestResource` on a specific repository still layers its own path/relation customization on top, once a repository has passed the detection strategy's baseline check.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four detection strategies each answer the question of whether a repository is exposed by default, differently">
  <rect x="20" y="20" width="280" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">DEFAULT: public + not excluded</text>

  <rect x="340" y="20" width="280" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="480" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ALL: everything, unconditionally</text>

  <rect x="20" y="70" width="280" height="35" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="92" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ANNOTATED: explicit opt-in only</text>

  <rect x="340" y="70" width="280" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="92" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">VISIBILITY: repo + entity both public</text>
</svg>

Four policies for the same underlying question: is this repository a candidate for REST exposure by default?

## 5. Runnable example

The scenario: deciding which of several repositories get exposed as REST, evolving from the `DEFAULT` strategy's opt-out model, to the `ANNOTATED` strategy's opt-in model, to a full detection engine that applies any of the four strategies against a set of repository metadata — showing how the same repositories produce different exposure results under different policies.

### Level 1 — Basic

Model the `DEFAULT` strategy: every repository is exposed unless explicitly marked `exported = false`.

```java
import java.util.*;

public class DetectionStrategyLevel1 {
    public static void main(String[] args) {
        List<RepoMeta> repos = List.of(
            new RepoMeta("CustomerRepository", true, null),   // no annotation -> DEFAULT exposes it
            new RepoMeta("AuditLogRepository", true, false)    // @RepositoryRestResource(exported = false)
        );

        for (RepoMeta r : repos) {
            boolean exposed = detectDefault(r);
            System.out.println(r.name + " -> " + (exposed ? "exposed" : "hidden"));
        }
    }

    static boolean detectDefault(RepoMeta r) {
        if (r.explicitExported != null) return r.explicitExported; // annotation always wins if present
        return r.isPublic; // otherwise: exposed if the repository interface is public
    }
}

class RepoMeta {
    String name; boolean isPublic; Boolean explicitExported;
    RepoMeta(String name, boolean isPublic, Boolean explicitExported) {
        this.name = name; this.isPublic = isPublic; this.explicitExported = explicitExported;
    }
}
```

How to run: `java DetectionStrategyLevel1.java`

`detectDefault` mirrors `RepositoryDetectionStrategies.DEFAULT`: absent an explicit annotation, a public repository is exposed automatically — `CustomerRepository` gets exposed, `AuditLogRepository` doesn't, because its explicit `exported = false` overrides the public-by-default behavior.

### Level 2 — Intermediate

Add the `ANNOTATED` strategy: the opposite default — nothing exposed unless explicitly annotated `exported = true`.

```java
import java.util.*;

public class DetectionStrategyLevel2 {
    public static void main(String[] args) {
        List<RepoMeta> repos = List.of(
            new RepoMeta("CustomerRepository", true, null),         // no annotation
            new RepoMeta("ProductRepository", true, true),           // @RepositoryRestResource(exported = true)
            new RepoMeta("AuditLogRepository", true, false)          // @RepositoryRestResource(exported = false)
        );

        System.out.println("Under DEFAULT strategy:");
        for (RepoMeta r : repos) System.out.println("  " + r.name + " -> " + (detectDefault(r) ? "exposed" : "hidden"));

        System.out.println("Under ANNOTATED strategy:");
        for (RepoMeta r : repos) System.out.println("  " + r.name + " -> " + (detectAnnotated(r) ? "exposed" : "hidden"));
    }

    static boolean detectDefault(RepoMeta r) {
        if (r.explicitExported != null) return r.explicitExported;
        return r.isPublic;
    }
    static boolean detectAnnotated(RepoMeta r) {
        // Only exposed if EXPLICITLY annotated exported = true -- absence of annotation means hidden.
        return Boolean.TRUE.equals(r.explicitExported);
    }
}

class RepoMeta {
    String name; boolean isPublic; Boolean explicitExported;
    RepoMeta(String name, boolean isPublic, Boolean explicitExported) {
        this.name = name; this.isPublic = isPublic; this.explicitExported = explicitExported;
    }
}
```

How to run: `java DetectionStrategyLevel2.java`

Under `ANNOTATED`, `CustomerRepository` flips from exposed (under `DEFAULT`) to hidden — it has no explicit `@RepositoryRestResource(exported = true)`, so the annotated strategy treats it as internal by default, inverting the safety posture of the whole application in one configuration line.

### Level 3 — Advanced

Build a small detection engine supporting all four strategies, including `VISIBILITY` (repository *and* entity must both be public), and run the same repository set through each to see how the results diverge.

```java
import java.util.*;
import java.util.function.*;

public class DetectionStrategyLevel3 {
    enum Strategy { DEFAULT, ALL, ANNOTATED, VISIBILITY }

    public static void main(String[] args) {
        List<RepoMeta> repos = List.of(
            new RepoMeta("CustomerRepository", true, true, null),   // public repo, public entity, no annotation
            new RepoMeta("ProductRepository", true, true, true),     // public repo, public entity, exported=true
            new RepoMeta("AuditLogRepository", true, true, false),   // public repo, public entity, exported=false
            new RepoMeta("InternalCacheRepository", true, false, null) // public repo, PACKAGE-PRIVATE entity
        );

        for (Strategy strategy : Strategy.values()) {
            System.out.println("Strategy " + strategy + ":");
            for (RepoMeta r : repos) System.out.println("  " + r.name + " -> " + (detect(strategy, r) ? "exposed" : "hidden"));
        }
    }

    static boolean detect(Strategy strategy, RepoMeta r) {
        return switch (strategy) {
            case ALL -> true; // everything, unconditionally
            case ANNOTATED -> Boolean.TRUE.equals(r.explicitExported);
            case VISIBILITY -> r.repositoryIsPublic && r.entityIsPublic;
            case DEFAULT -> r.explicitExported != null ? r.explicitExported : r.repositoryIsPublic;
        };
    }
}

class RepoMeta {
    String name; boolean repositoryIsPublic, entityIsPublic; Boolean explicitExported;
    RepoMeta(String name, boolean repositoryIsPublic, boolean entityIsPublic, Boolean explicitExported) {
        this.name = name; this.repositoryIsPublic = repositoryIsPublic;
        this.entityIsPublic = entityIsPublic; this.explicitExported = explicitExported;
    }
}
```

How to run: `java DetectionStrategyLevel3.java`

`InternalCacheRepository` is a public repository interface but its entity is package-private — under `DEFAULT` and `ALL` it's still exposed (they don't check entity visibility), but under `VISIBILITY` it's hidden, because that strategy specifically requires *both* the repository and its entity to be public before considering it a candidate for exposure.

## 6. Walkthrough

Execution starts in `main` for Level 3. Four repositories are defined with varying combinations of repository visibility, entity visibility, and explicit annotation. The outer loop runs each of the four `Strategy` values against all four repositories.

```
Strategy DEFAULT:
  CustomerRepository -> exposed
  ProductRepository -> exposed
  AuditLogRepository -> hidden
  InternalCacheRepository -> exposed
Strategy ALL:
  CustomerRepository -> exposed
  ProductRepository -> exposed
  AuditLogRepository -> exposed
  InternalCacheRepository -> exposed
Strategy ANNOTATED:
  CustomerRepository -> hidden
  ProductRepository -> exposed
  AuditLogRepository -> hidden
  InternalCacheRepository -> hidden
Strategy VISIBILITY:
  CustomerRepository -> exposed
  ProductRepository -> exposed
  AuditLogRepository -> exposed
  InternalCacheRepository -> hidden
```

Notice `AuditLogRepository`'s explicit `exported = false` is respected by both `DEFAULT` and `ANNOTATED` (both consult the annotation), completely ignored by `ALL` (which exposes unconditionally), and irrelevant to `VISIBILITY` (which only checks visibility, not the annotation, and happens to expose it here since both repo and entity are public). This is the core lesson: the detection strategy and the per-repository annotation interact differently depending on which strategy is active — the annotation isn't universally authoritative, its weight depends on the chosen strategy.

## 7. Gotchas & takeaways

> Gotcha: `RepositoryDetectionStrategies.ALL` — the module's historical default in older Spring Data REST versions — ignores `exported = false` entirely; an application relying on the annotation to hide sensitive repositories while still on `ALL` mode is not actually protected, since `ALL` overrides that annotation's intent completely.

> Gotcha: switching an established application's detection strategy (e.g. from `DEFAULT` to `ANNOTATED`) after other clients already depend on auto-exposed endpoints is a breaking change for every repository that was relying on implicit exposure — audit which endpoints are actually in use before flipping the application-wide default.

- Detection strategy sets the application-wide default for whether a repository is a REST-exposure candidate at all, before any per-repository `@RepositoryRestResource` customization is applied.
- `DEFAULT` (opt-out) and `ANNOTATED` (opt-in) treat the `exported` annotation attribute with opposite defaults; `ALL` ignores it entirely; `VISIBILITY` ignores it in favor of Java visibility modifiers.
- Choosing `ANNOTATED` for an application with mostly internal repositories is generally safer than relying on remembering `exported = false` on every one that shouldn't be public.
- Changing the detection strategy on an existing application is a breaking change for any client depending on the previous exposure defaults — treat it with the same care as any public API change.
