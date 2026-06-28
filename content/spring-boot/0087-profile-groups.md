---
card: spring-boot
gi: 87
slug: profile-groups
title: Profile groups
---

## 1. What it is

**Profile groups** (introduced in Spring Boot 2.4) let you define a single logical profile name that, when activated, automatically activates a fixed set of sub-profiles. You configure them in `application.properties` with the prefix `spring.profiles.group.<name>`:

```properties
spring.profiles.group.prod=proddb,prodmq,prodobs
```

Activating `prod` now activates `proddb`, `prodmq`, and `prodobs` as well — all their property files load and all their `@Profile`-annotated beans register.

Profile groups solve the problem of "I need to activate eight profiles to fully configure a production deployment" without forcing operators to remember and type all eight names.

## 2. Why & when

Before profile groups, teams solved "composite profiles" by chaining `spring.profiles.include` inside profile-specific files. That technique worked, but Spring Boot 2.4 banned setting `spring.profiles.active` inside profile-specific files for clarity. Profile groups are the sanctioned replacement.

Use profile groups when:
- A deployment environment (prod, staging) requires multiple fine-grained profiles to be simultaneously active.
- You want operators to activate one name (`prod`) while the implementation details (which DB profile, which messaging profile) remain in `application.properties`.
- You want to change which sub-profiles compose an environment without changing deployment scripts.

Profile groups are purely a **composition** tool — you are still writing individual `@Profile("proddb")` beans or `application-proddb.properties` files. Groups just automate the activation.

## 3. Core concept

```
spring.profiles.group.local=localdb,devtools,seed
spring.profiles.group.prod=proddb,prodmq,prodobs
```

Activation chain:
```
--spring.profiles.active=prod
    → prod is active
    → proddb is active   → loads application-proddb.properties
    → prodmq is active   → loads application-prodmq.properties
    → prodobs is active  → loads application-prodobs.properties
```

Key rules:
- Group expansion happens **before** profile-specific files are loaded.
- A group member can itself be a group (nested groups), but cycles are not allowed.
- `spring.profiles.include` still works alongside groups — groups are just a cleaner alternative for the "environment = set of sub-profiles" pattern.
- Groups are defined in `application.properties` (or any property source loaded before profiles expand); they are **not** defined in profile-specific files.

## 4. Diagram

<svg viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Profile group 'prod' expands to three sub-profiles: proddb, prodmq, prodobs, each loading its own properties file">
  <rect x="8" y="8" width="664" height="294" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Profile Group Expansion</text>

  <!-- Group definition box -->
  <rect x="30" y="48" width="300" height="56" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="180" y="67" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">application.properties</text>
  <text x="180" y="84" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">spring.profiles.group.prod=</text>
  <text x="180" y="97" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">  proddb,prodmq,prodobs</text>

  <!-- Activated group name -->
  <rect x="390" y="48" width="260" height="56" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="520" y="67" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">activation command</text>
  <text x="520" y="86" fill="#f0883e" font-size="12" text-anchor="middle" font-family="monospace" font-weight="bold">--spring.profiles.active=prod</text>

  <!-- Arrow down -->
  <defs>
    <marker id="g-arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="340" y1="120" x2="340" y2="145" stroke="#6db33f" stroke-width="2" marker-end="url(#g-arr)"/>
  <text x="340" y="140" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">group expands before profile files load</text>

  <!-- Expanded sub-profiles -->
  <rect x="50" y="155" width="170" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="135" y="176" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">proddb</text>
  <text x="135" y="193" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">application-proddb.properties</text>

  <rect x="255" y="155" width="170" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="176" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">prodmq</text>
  <text x="340" y="193" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">application-prodmq.properties</text>

  <rect x="460" y="155" width="170" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="176" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">prodobs</text>
  <text x="545" y="193" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">application-prodobs.properties</text>

  <!-- Connecting lines -->
  <line x1="340" y1="148" x2="135" y2="153" stroke="#8b949e" stroke-width="1"/>
  <line x1="340" y1="148" x2="340" y2="153" stroke="#8b949e" stroke-width="1"/>
  <line x1="340" y1="148" x2="545" y2="153" stroke="#8b949e" stroke-width="1"/>

  <!-- Result -->
  <rect x="30" y="230" width="620" height="42" rx="7" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="248" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">All three property files loaded + all @Profile("proddb/prodmq/prodobs") beans registered</text>
  <text x="340" y="264" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Operator only typed "prod" — implementation details hidden in application.properties</text>
</svg>

One name to activate; the group definition governs which sub-profiles expand behind the scenes.

## 5. Runnable example

```java
// ProfileGroupsDemo.java — run: java ProfileGroupsDemo.java  (JDK 17+)
// Simulates profile group expansion and shows which "beans" and "property files" load.

import java.util.*;

public class ProfileGroupsDemo {

    // Simulated group definitions (from application.properties)
    static final Map<String, List<String>> GROUPS = Map.of(
        "local", List.of("localdb", "devtools", "seed"),
        "prod",  List.of("proddb", "prodmq", "prodobs")
    );

    // Expand a single profile name, resolving group membership recursively
    static Set<String> expand(String profile, Set<String> visited) {
        if (!visited.add(profile)) return Set.of();   // cycle guard
        Set<String> result = new LinkedHashSet<>();
        result.add(profile);
        List<String> members = GROUPS.getOrDefault(profile, List.of());
        for (String m : members) result.addAll(expand(m, visited));
        return result;
    }

    static Set<String> expandAll(List<String> requested) {
        Set<String> all = new LinkedHashSet<>();
        for (String p : requested) all.addAll(expand(p, new HashSet<>()));
        return all;
    }

    static void simulate(String... requested) {
        List<String> req = Arrays.asList(requested);
        Set<String> active = expandAll(req);
        System.out.println("Requested : " + req);
        System.out.println("Expanded  : " + active);
        active.stream()
              .filter(p -> !GROUPS.containsKey(p))  // only leaf profiles
              .forEach(p -> System.out.println("  → loads application-" + p + ".properties"));
        System.out.println();
    }

    public static void main(String[] args) {
        System.out.println("=== Activating 'local' group ===");
        simulate("local");

        System.out.println("=== Activating 'prod' group ===");
        simulate("prod");

        System.out.println("=== Activating multiple groups + plain profile ===");
        simulate("prod", "cloud");

        System.out.println("=== Leaf profile (not a group) ===");
        simulate("proddb");
    }
}
```

**How to run:** `java ProfileGroupsDemo.java`

In real Spring Boot, the group definition lives in `application.properties`:
```properties
spring.profiles.group.local=localdb,devtools,seed
spring.profiles.group.prod=proddb,prodmq,prodobs
```

Then: `java -jar app.jar --spring.profiles.active=prod` activates all three sub-profiles automatically.

## 6. Walkthrough

- `GROUPS` map simulates `spring.profiles.group.*` entries from `application.properties`. Keys are group names; values are the member profiles they expand to.
- `expand(profile, visited)` recursively expands a profile, resolving nested groups. The `visited` set prevents infinite loops if a misconfigured group references itself.
- `expandAll` processes multiple requested profiles in order, preserving insertion order — which matters because when two sub-profiles define the same property key, the last-loaded one wins.
- The `simulate` method prints the expanded set, then lists only the *leaf* profiles (non-group members) to show which property files would actually load. Group-level names like `prod` itself don't have a corresponding `application-prod.properties` file — only their members do.
- **Scenario 3** (`prod,cloud`) shows that `cloud` is not in the groups map, so it passes through as-is. This means `application-cloud.properties` is also loaded alongside the three `prod` sub-profile files.
- In Spring Boot, group expansion happens inside `ConfigFileApplicationListener` before any profile-specific file is read — ensuring all sub-profiles are known when property files are resolved.

## 7. Gotchas & takeaways

> **Do not define profile groups inside profile-specific files.** `spring.profiles.group.*` must be in `application.properties` (or another base property source). If you put it in `application-dev.properties`, it only takes effect after `dev` is already active — which defeats the purpose.

> **Groups are not mutual exclusion.** Nothing prevents `--spring.profiles.active=prod,local`, which would activate all members of both groups simultaneously. Treat group names like enum values in your team conventions and document which are mutually exclusive.

- Profile groups are purely an activation shorthand — the actual work is still done by the individual sub-profile files and `@Profile`-annotated beans.
- Sub-profiles can be individual fine-grained profiles (`proddb`, `prodmq`), allowing mix-and-match when needed while still supporting one-word activation for standard environments.
- Available since Spring Boot 2.4; `spring.profiles.include` still works but groups are the preferred pattern for the "environment = bundle of profiles" use case.
- Group definitions are in `application.properties`, not in code — so DevOps can adjust which sub-profiles compose an environment without a code change.
- Test classes can use `@ActiveProfiles("prod")` and the group will still expand, because `@ActiveProfiles` sets `spring.profiles.active`, which triggers group resolution.
