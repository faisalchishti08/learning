---
card: microservices
gi: 226
slug: configuration-precedence-overrides
title: "Configuration precedence & overrides"
---

## 1. What it is

Configuration precedence is the defined order in which multiple, potentially overlapping configuration sources — defaults baked into code, config files, environment variables, command-line arguments, a config server — are consulted, so that when the same setting is specified in more than one place, there's a deterministic, well-known rule for which value actually wins.

## 2. Why & when

A real application typically pulls configuration from several sources at once: sensible built-in defaults, a base config file, environment-specific overrides, environment variables set by the deployment platform, and possibly command-line flags for one-off overrides during debugging. Without an explicit, well-understood precedence order, it becomes unclear — and inconsistent across team members' mental models — which source actually determines the final, effective value when two sources disagree, leading to "why is this using the wrong setting?" debugging sessions that are really about precedence confusion, not a genuinely broken value.

Establish and document explicit precedence whenever more than one configuration source is in play — which is nearly always true beyond the simplest single-file setup. A well-known precedence convention (like the one Spring Boot itself defines, covered in [Spring Boot externalized configuration](0228-spring-boot-externalized-configuration-properties-yaml-env-a.md)) lets a value's origin be reasoned about predictably, without needing to trace every source by hand each time.

## 3. Core concept

Precedence is implemented by resolving a setting through an ordered list of sources, taking the first (highest-priority) source that actually defines a value for that setting, and falling through to lower-priority sources — ultimately a built-in default — only when higher-priority sources don't specify it.

```java
// sources, ORDERED from highest to lowest precedence
List<Map<String, String>> sourcesInPrecedenceOrder = List.of(
    commandLineArgs,       // HIGHEST -- explicit, one-off overrides win over everything
    environmentVariables,  // deployment-platform-supplied
    profileSpecificFile,   // e.g. application-production.yaml
    baseConfigFile,        // e.g. application.yaml
    builtInDefaults         // LOWEST -- only used if nothing else specifies the value
);

static String resolve(String key, List<Map<String, String>> sources) {
    for (Map<String, String> source : sources) {
        if (source.containsKey(key)) return source.get(key); // FIRST source defining it WINS
    }
    throw new NoSuchElementException("no source defines: " + key);
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A configuration lookup walks sources from highest precedence to lowest -- command-line args, environment variables, profile-specific file, base config file, built-in defaults -- stopping at the first source that defines the requested key" >
  <rect x="20" y="15" width="600" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="35" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Command-line args (HIGHEST precedence)</text>

  <rect x="20" y="55" width="600" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="75" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Environment variables</text>

  <rect x="20" y="95" width="600" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Profile-specific config file</text>

  <rect x="20" y="135" width="600" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="155" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Base config file</text>

  <rect x="20" y="175" width="600" height="20" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="189" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Built-in defaults (LOWEST precedence)</text>

  <line x1="320" y1="45" x2="320" y2="53" stroke="#8b949e"/>
  <line x1="320" y1="85" x2="320" y2="93" stroke="#8b949e"/>
  <line x1="320" y1="125" x2="320" y2="133" stroke="#8b949e"/>
  <line x1="320" y1="165" x2="320" y2="173" stroke="#8b949e"/>
</svg>

Resolution stops at the first (topmost) source that actually defines a given key.

## 5. Runnable example

Scenario: a service reading a single setting from an ambiguous mix of sources with no defined precedence (unpredictable which one "wins"), refactors to an explicitly ordered precedence chain (deterministic, documented resolution), and finally demonstrates diagnosing *why* a specific value won by reporting which source it actually came from — a common real debugging need when precedence confusion is suspected.

### Level 1 — Basic

```java
// File: AmbiguousSources.java -- THREE sources define the SAME setting,
// with NO defined rule for which one wins -- picking one is arbitrary.
import java.util.*;

public class AmbiguousSources {
    public static void main(String[] args) {
        Map<String, String> envVars = Map.of("timeout.ms", "5000");
        Map<String, String> configFile = Map.of("timeout.ms", "3000");
        Map<String, String> defaults = Map.of("timeout.ms", "1000");

        // WHICH one is correct?? Nothing here defines an answer.
        System.out.println("envVars says: " + envVars.get("timeout.ms"));
        System.out.println("configFile says: " + configFile.get("timeout.ms"));
        System.out.println("defaults says: " + defaults.get("timeout.ms"));
        System.out.println("With no defined precedence, which value SHOULD actually be used is ambiguous.");
    }
}
```

**How to run:** `javac AmbiguousSources.java && java AmbiguousSources` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ExplicitPrecedenceChain.java -- sources are ORDERED explicitly;
// resolution deterministically picks the FIRST source that defines the key.
import java.util.*;

public class ExplicitPrecedenceChain {
    static String resolve(String key, List<Map<String, String>> sourcesHighToLow) {
        for (Map<String, String> source : sourcesHighToLow) {
            if (source.containsKey(key)) return source.get(key); // FIRST match wins, deterministically
        }
        throw new NoSuchElementException("no source defines: " + key);
    }

    public static void main(String[] args) {
        Map<String, String> envVars = Map.of("timeout.ms", "5000");
        Map<String, String> configFile = Map.of("timeout.ms", "3000");
        Map<String, String> defaults = Map.of("timeout.ms", "1000");

        List<Map<String, String>> precedenceOrder = List.of(envVars, configFile, defaults); // env WINS, by DESIGN

        String resolved = resolve("timeout.ms", precedenceOrder);
        System.out.println("Resolved timeout.ms = " + resolved + " (env vars take precedence over config file and defaults)");
    }
}
```

**How to run:** `javac ExplicitPrecedenceChain.java && java ExplicitPrecedenceChain` (JDK 17+).

Expected output:
```
Resolved timeout.ms = 5000 (env vars take precedence over config file and defaults)
```

### Level 3 — Advanced

```java
// File: SourceOriginDiagnostics.java -- resolves a setting AND reports
// WHICH source it came from -- essential for debugging "why is this
// using the wrong value" reports that are really precedence confusion.
import java.util.*;

public class SourceOriginDiagnostics {
    record NamedSource(String name, Map<String, String> values) {}
    record ResolvedValue(String value, String fromSource) {}

    static ResolvedValue resolveWithOrigin(String key, List<NamedSource> sourcesHighToLow) {
        for (NamedSource source : sourcesHighToLow) {
            if (source.values().containsKey(key)) return new ResolvedValue(source.values().get(key), source.name());
        }
        throw new NoSuchElementException("no source defines: " + key);
    }

    public static void main(String[] args) {
        List<NamedSource> sources = List.of(
            new NamedSource("command-line-args", Map.of()), // present in the chain, but does NOT define this key
            new NamedSource("environment-variables", Map.of("timeout.ms", "5000")),
            new NamedSource("profile-config-file", Map.of("timeout.ms", "3000")),
            new NamedSource("base-config-file", Map.of("timeout.ms", "2000")),
            new NamedSource("built-in-defaults", Map.of("timeout.ms", "1000"))
        );

        ResolvedValue resolved = resolveWithOrigin("timeout.ms", sources);
        System.out.println("timeout.ms = " + resolved.value() + ", sourced from: " + resolved.fromSource());

        // now simulate the SAME key missing from command-line AND env -- profile file should win instead
        List<NamedSource> withoutEnvOverride = List.of(
            new NamedSource("command-line-args", Map.of()),
            new NamedSource("environment-variables", Map.of()), // no longer defines it
            new NamedSource("profile-config-file", Map.of("timeout.ms", "3000")),
            new NamedSource("base-config-file", Map.of("timeout.ms", "2000")),
            new NamedSource("built-in-defaults", Map.of("timeout.ms", "1000"))
        );
        ResolvedValue fallenThrough = resolveWithOrigin("timeout.ms", withoutEnvOverride);
        System.out.println("timeout.ms = " + fallenThrough.value() + ", sourced from: " + fallenThrough.fromSource());
    }
}
```

**How to run:** `javac SourceOriginDiagnostics.java && java SourceOriginDiagnostics` (JDK 17+).

Expected output:
```
timeout.ms = 5000, sourced from: environment-variables
timeout.ms = 3000, sourced from: profile-config-file
```

## 6. Walkthrough

1. **Level 1, the ambiguity problem** — `envVars`, `configFile`, and `defaults` each independently claim `timeout.ms` has a different value (`5000`, `3000`, `1000`), and nothing in this program states which one should actually be used — a reader has no way to determine the "correct" effective value from the code alone.
2. **Level 2, an explicit ordered chain** — `precedenceOrder` lists the three sources in a specific, deliberate sequence (`envVars` first), and `resolve` iterates that list, returning the value from the *first* source in the list that contains the key — this makes the winning rule explicit and inspectable rather than implicit and guessed at.
3. **Level 2, the deterministic result** — because `envVars` is first in `precedenceOrder` and does contain `timeout.ms`, `resolve` returns `"5000"` immediately without even consulting `configFile` or `defaults` — the same input sources, run through this ordered resolution, always produce the same, predictable answer.
4. **Level 3, naming the sources for diagnosis** — `NamedSource` pairs each source's actual values with a human-readable name, and `resolveWithOrigin` returns both the resolved value *and* which named source it came from, rather than just the bare value.
5. **Level 3, the first diagnostic case** — `command-line-args` is checked first but is empty for this key, so resolution falls through to `environment-variables`, which does define it; the reported origin, `"environment-variables"`, tells a debugging engineer precisely which layer to go check or override if this value is unexpected.
6. **Level 3, the fallthrough case** — in `withoutEnvOverride`, both `command-line-args` and `environment-variables` are empty for this key, so resolution falls through two levels to `profile-config-file`; the reported origin correctly shows `"profile-config-file"` rather than `"environment-variables"`, demonstrating that origin reporting tracks the *actual* resolution path for the given input, not a fixed assumption about which source normally wins — exactly the kind of diagnostic real configuration frameworks (including Spring Boot's own resolution, covered next) need to expose when a team is debugging an unexpected effective value.

## 7. Gotchas & takeaways

> **Gotcha:** precedence order is a design decision that must be documented and consistently understood by everyone touching configuration — an engineer who assumes config files override environment variables (when the actual system does the opposite) will "fix" a value in the wrong place and be confused when nothing changes; when adopting a framework's built-in precedence (like Spring Boot's), read and internalize its documented order rather than guessing from experience with a different system.

- Configuration precedence defines a deterministic order among multiple overlapping sources, so the same setting specified in more than one place has one clear, predictable winner.
- Resolution walks the ordered sources from highest to lowest priority, returning the value from the first source that actually defines the requested key.
- Reporting *which* source a resolved value actually came from is a valuable diagnostic capability, turning "why is this using the wrong value" into a quick, direct lookup rather than a manual trace through every source.
- Explicit, documented precedence matters as soon as more than one configuration source is in play, which is nearly always true beyond a trivial single-file setup.
- Adopting a framework's own precedence convention (such as Spring Boot's, covered in [Spring Boot externalized configuration](0228-spring-boot-externalized-configuration-properties-yaml-env-a.md)) requires understanding that specific framework's documented order, not assuming it matches a different system's convention.
