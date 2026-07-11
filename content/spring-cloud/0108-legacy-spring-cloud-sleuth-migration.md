---
card: spring-cloud
gi: 108
slug: legacy-spring-cloud-sleuth-migration
title: "Legacy Spring Cloud Sleuth migration"
---

## 1. What it is

Migrating a Spring Boot 2 application using Spring Cloud Sleuth to Spring Boot 3 means replacing the `spring-cloud-starter-sleuth` dependency with `micrometer-tracing-bridge-brave` (or `-otel`) plus a reporter/exporter, updating a handful of renamed configuration properties (`spring.sleuth.*` to `management.tracing.*`), and, if any code directly used Sleuth's `Tracer`/`Span` API, updating those call sites to Micrometer Tracing's equivalent (differently-packaged, mostly similarly-shaped) API — since Sleuth itself is in maintenance mode and was effectively superseded by Micrometer Tracing starting with Spring Boot 3.

```xml
<!-- REMOVE -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-sleuth</artifactId>
</dependency>

<!-- ADD -->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing-bridge-brave</artifactId>
</dependency>
<dependency>
    <groupId>io.zipkin.reporter2</groupId>
    <artifactId>zipkin-reporter-brave</artifactId>
</dependency>
```

```properties
# spring.sleuth.sampler.probability=0.1   (OLD)
management.tracing.sampling.probability=0.1  # (NEW)
```

## 2. Why & when

Any Spring Boot 2 application already using Sleuth for tracing needs a deliberate migration path when upgrading to Spring Boot 3, since Sleuth's own auto-configuration and starters are not the recommended path forward on Boot 3 — Micrometer Tracing is. The good news is that most of the *behavior* Sleuth provided (automatic span creation for web/messaging/scheduling, correlation IDs in logs, propagation) carries over conceptually unchanged, because Micrometer Tracing was designed as Sleuth's direct successor covering the same core capabilities; the migration work is largely mechanical — dependency swaps and property renames — rather than a redesign, except where application code directly called Sleuth's own `Tracer` or `Span` types.

Reach for this migration checklist when:

- Upgrading an existing Spring Boot 2 + Sleuth application to Spring Boot 3 — this migration is effectively mandatory as part of that broader upgrade, since Sleuth's Boot 3 compatibility is limited to maintenance-mode support at best.
- Auditing an application for direct Sleuth API usage before starting the migration — `@NewSpan`, manually injected `brave.Tracer`/`Tracer` from `org.springframework.cloud.sleuth`, or Sleuth-specific annotations all need identifying up front, since these are the parts requiring actual code changes rather than pure configuration/dependency changes.
- Deciding which bridge to adopt as Sleuth's replacement — since Sleuth itself was built on Brave, choosing `micrometer-tracing-bridge-brave` (rather than switching straight to OpenTelemetry) minimizes the number of simultaneous changes during the migration, with a possible later, separate migration to OpenTelemetry if desired.

## 3. Core concept

```
 Sleuth (Spring Boot 2):
   dependency: spring-cloud-starter-sleuth
   properties: spring.sleuth.*
   API: org.springframework.cloud.sleuth.Tracer / Span
   -- built ON TOP of Brave internally, but exposed its OWN wrapper API

 Micrometer Tracing (Spring Boot 3):
   dependency: micrometer-tracing-bridge-brave (or -otel) + a reporter/exporter
   properties: management.tracing.*
   API: io.micrometer.tracing.Tracer / Span
   -- Brave (or OTel) still does the actual work underneath, same as before

 MOST auto-instrumented behavior (web, messaging, scheduling spans, log correlation) --
 CARRIES OVER CONCEPTUALLY UNCHANGED, because Micrometer Tracing was built to replace Sleuth's role directly
```

The underlying tracer (Brave, in the most common migration path) often doesn't even change — what changes is the facade/API layer sitting on top of it, plus the configuration property namespace.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sleuth on Spring Boot 2 wraps Brave with its own API and spring dot sleuth properties while Micrometer Tracing on Spring Boot 3 wraps the same Brave tracer with a new neutral API and management dot tracing properties leaving the underlying Brave tracer itself unchanged across the migration">
  <rect x="20" y="20" width="270" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="155" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Spring Boot 2: Sleuth</text>
  <text x="155" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">org.springframework.cloud.sleuth.Tracer</text>
  <text x="155" y="72" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">spring.sleuth.*</text>

  <rect x="350" y="20" width="270" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Spring Boot 3: Micrometer Tracing</text>
  <text x="485" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">io.micrometer.tracing.Tracer</text>
  <text x="485" y="72" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">management.tracing.*</text>

  <rect x="180" y="130" width="280" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="154" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">Brave tracer -- UNCHANGED underneath both</text>

  <defs><marker id="a108" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="155" y1="90" x2="280" y2="130" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a108)"/>
  <line x1="485" y1="90" x2="360" y2="130" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a108)"/>
</svg>

The facade above changes; the tracer implementation below often stays exactly the same, which is why the migration is mostly mechanical.

## 5. Runnable example

The scenario: model a small application's tracing call sites first written against a Sleuth-shaped API, then migrated to a Micrometer-Tracing-shaped API, with the underlying tracer implementation left untouched — demonstrating the migration is a call-site and configuration-key change, not a tracer replacement. Start with the "before" (Sleuth-style) code, then the "after" (Micrometer Tracing-style) code, then a config-key translation utility useful for auditing a real properties file during migration.

### Level 1 — Basic

Application code written against a Sleuth-shaped `Tracer`/`Span` API — the "before" state.

```java
public class SleuthMigrationLevel1 {
    // models org.springframework.cloud.sleuth.Tracer / Span -- the OLD, Boot-2-era API shape
    static class SleuthStyleTracer {
        static class SleuthSpan {
            String name;
            SleuthSpan(String name) { this.name = name; System.out.println("[Sleuth] span started: " + name); }
            void end() { System.out.println("[Sleuth] span ended: " + name); }
        }
        SleuthSpan nextSpan(String name) { return new SleuthSpan(name); }
    }

    static void processOrder(SleuthStyleTracer tracer) {
        SleuthStyleTracer.SleuthSpan span = tracer.nextSpan("processOrder");
        // ... business logic ...
        span.end();
    }

    public static void main(String[] args) {
        processOrder(new SleuthStyleTracer());
    }
}
```

How to run: `java SleuthMigrationLevel1.java`

This is the shape of code a Boot-2-era application directly using Sleuth's own `Tracer` might have — `processOrder` calls Sleuth-specific types by name, which is exactly the coupling that needs updating during migration.

### Level 2 — Intermediate

Migrate `processOrder` to Micrometer Tracing's API shape — same conceptual operations (start a span, end a span), different (Micrometer-native) types.

```java
public class SleuthMigrationLevel2 {
    // models io.micrometer.tracing.Tracer / Span -- the NEW, Boot-3-era API shape
    static class MicrometerTracer {
        static class MicrometerSpan {
            String name;
            MicrometerSpan(String name) { this.name = name; System.out.println("[Micrometer] span started: " + name); }
            void end() { System.out.println("[Micrometer] span ended: " + name); }
        }
        MicrometerSpan nextSpan() { return new MicrometerSpan("unnamed"); } // Micrometer's nextSpan() takes no name arg; name() is set separately
        MicrometerSpan nextSpan(String name) { MicrometerSpan s = nextSpan(); s.name = name; return s; }
    }

    // MIGRATED: same operations (start, end), updated to the new API's types and method shapes
    static void processOrder(MicrometerTracer tracer) {
        MicrometerTracer.MicrometerSpan span = tracer.nextSpan("processOrder");
        // ... business logic UNCHANGED ...
        span.end();
    }

    public static void main(String[] args) {
        processOrder(new MicrometerTracer());
    }
}
```

How to run: `java SleuthMigrationLevel2.java`

The structure of `processOrder` — get a span, do work, end the span — is unchanged from Level 1; only the concrete types (`SleuthStyleTracer`/`SleuthSpan` versus `MicrometerTracer`/`MicrometerSpan`) differ, which is representative of how most direct Sleuth API usage translates: a mechanical type/import update rather than a logic rewrite.

### Level 3 — Advanced

Add a configuration-key translation utility auditing a Sleuth-era properties file and reporting the Micrometer Tracing equivalents, useful for systematically catching every `spring.sleuth.*` key that needs renaming during a real migration.

```java
import java.util.*;

public class SleuthMigrationLevel3 {
    // a small, representative mapping of common Sleuth properties to their Micrometer Tracing equivalents
    static Map<String, String> keyTranslations = Map.of(
            "spring.sleuth.sampler.probability", "management.tracing.sampling.probability",
            "spring.sleuth.baggage.remote-fields", "management.tracing.baggage.remote-fields",
            "spring.sleuth.propagation.type", "management.tracing.propagation.type",
            "spring.sleuth.enabled", "management.tracing.enabled",
            "spring.zipkin.base-url", "management.zipkin.tracing.endpoint"
    );

    static List<String> auditProperties(Map<String, String> oldProperties) {
        List<String> report = new ArrayList<>();
        for (Map.Entry<String, String> entry : oldProperties.entrySet()) {
            String oldKey = entry.getKey();
            String value = entry.getValue();
            if (keyTranslations.containsKey(oldKey)) {
                report.add(oldKey + "=" + value + "  ->  " + keyTranslations.get(oldKey) + "=" + value);
            } else if (oldKey.startsWith("spring.sleuth") || oldKey.startsWith("spring.zipkin")) {
                report.add(oldKey + "=" + value + "  ->  NO KNOWN TRANSLATION -- needs manual review");
            }
        }
        return report;
    }

    public static void main(String[] args) {
        Map<String, String> legacyProperties = new LinkedHashMap<>();
        legacyProperties.put("spring.sleuth.sampler.probability", "0.1");
        legacyProperties.put("spring.zipkin.base-url", "http://localhost:9411");
        legacyProperties.put("spring.sleuth.trace-id128", "true"); // deliberately NOT in the translation map

        for (String line : auditProperties(legacyProperties)) System.out.println(line);
    }
}
```

How to run: `java SleuthMigrationLevel3.java`

The first two properties are found in `keyTranslations` and reported with their exact Micrometer Tracing equivalents, ready to paste into the new configuration; the third (`spring.sleuth.trace-id128`, a deliberately obscure property not covered in this small sample map) falls through to the "NO KNOWN TRANSLATION" branch, correctly flagging it for manual research rather than silently dropping it — exactly the systematic auditing approach a real migration should apply against a complete properties file, backed by the full Sleuth-to-Micrometer-Tracing mapping in Spring's own migration documentation.

## 6. Walkthrough

Trace `auditProperties` processing `"spring.sleuth.trace-id128"` in Level 3.

1. The `for` loop reaches the entry `oldKey = "spring.sleuth.trace-id128"`, `value = "true"`.
2. `keyTranslations.containsKey("spring.sleuth.trace-id128")` checks the small sample map — this key was deliberately never added to it, so this returns `false`.
3. The `else if` branch checks `oldKey.startsWith("spring.sleuth")`, which is `true` (the key does start with that prefix), so this branch executes.
4. `report.add(...)` appends a line reading `"spring.sleuth.trace-id128=true  ->  NO KNOWN TRANSLATION -- needs manual review"` — flagging this specific property for a human to research, rather than either silently ignoring it (which would risk losing configuration during migration) or guessing at an incorrect translation.
5. Contrast this with `"spring.sleuth.sampler.probability"`, processed earlier in the same loop: `keyTranslations.containsKey(...)` returns `true` for that key, so the first `if` branch runs instead, producing a direct, confident translation line rather than a manual-review flag.
6. The printed report cleanly separates "confidently translated" entries from "needs manual review" entries, giving whoever performs the real migration a prioritized, actionable checklist rather than requiring them to already know every Sleuth property's Micrometer Tracing equivalent from memory.

```
"spring.sleuth.sampler.probability" in keyTranslations?  YES -> confident translation line
"spring.zipkin.base-url"            in keyTranslations?  YES -> confident translation line
"spring.sleuth.trace-id128"         in keyTranslations?  NO, but starts with "spring.sleuth" -> flagged for manual review
```

## 7. Gotchas & takeaways

> **Gotcha:** some Sleuth behavior does not have a pure one-to-one Micrometer Tracing equivalent — certain Sleuth-specific conveniences or defaults changed subtly during the transition, and blindly renaming every `spring.sleuth.*` key to a mechanically-guessed `management.tracing.*` equivalent without checking Spring's official migration guide for that specific property risks silently misconfiguring tracing behavior rather than raising an obvious error. Treat automated key-translation tooling (as Level 3 modeled) as a first-pass audit aid, not a substitute for verifying each translated property against current documentation.

- The migration from Sleuth to Micrometer Tracing is primarily mechanical — a dependency swap, a configuration property namespace change, and (only where present) direct Sleuth API call sites updated to Micrometer Tracing's equivalent types — because Micrometer Tracing was purpose-built as Sleuth's successor covering the same core responsibilities.
- Auto-instrumented behavior (spans for web requests, messages, scheduled methods; correlation IDs in logs) carries over conceptually unchanged across the migration, since both Sleuth and Micrometer Tracing hook into the same underlying framework boundaries.
- Choosing to keep Brave as the underlying tracer (via `micrometer-tracing-bridge-brave`) during the Sleuth migration, rather than simultaneously switching to OpenTelemetry, reduces the number of moving parts changing at once — a separate, later migration to OpenTelemetry (if desired) can then be undertaken independently, with tracing already stable on the new Micrometer Tracing facade.
- Systematically auditing every `spring.sleuth.*` and `spring.zipkin.*` property against Spring's official migration mapping (rather than assuming a simple, uniform prefix rename covers every case) is essential to avoid silently losing or misconfiguring tracing behavior during the upgrade.
