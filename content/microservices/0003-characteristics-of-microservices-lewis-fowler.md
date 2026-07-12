---
card: microservices
gi: 3
slug: characteristics-of-microservices-lewis-fowler
title: "Characteristics of microservices (Lewis & Fowler)"
---

## 1. What it is

In their 2014 article "Microservices," James Lewis and Martin Fowler didn't give a single crisp definition of the term — instead they described **nine common characteristics** that architectures calling themselves "microservices" tend to share: componentization via services, organization around business capabilities, being products not projects, smart endpoints and dumb pipes, decentralized governance, decentralized data management, infrastructure automation, design for failure, and evolutionary design. No single service needs every trait to be useful, but the more of them a system genuinely exhibits, the more confidently you can call it a microservice architecture rather than a monolith wearing a network boundary.

## 2. Why & when

Treat this list as a diagnostic, not a checklist to blindly satisfy. When a team says "we're doing microservices" but ships all their services together on one release train, shares one database, and routes every message through a central smart bus, the Lewis & Fowler characteristics tell you exactly which properties are missing and why the architecture isn't delivering the benefits people expect from the label. Use it when evaluating whether an existing system is genuinely microservices-shaped, or when designing a new system and deciding, deliberately, which of these nine properties you actually need.

## 3. Core concept

Each of the nine characteristics answers a different structural question:

| Characteristic | Question it answers |
|---|---|
| Componentization via services | Is a "unit of change" a deployable service, or just a library? |
| Business capabilities | Are teams organized around what the business does, or around technical layers? |
| Products not projects | Does the team that builds a service also run it in production? |
| Smart endpoints, dumb pipes | Does business logic live in the services, or in the messaging middleware? |
| Decentralized governance | Can teams choose their own tech stack, or is one stack mandated centrally? |
| Decentralized data management | Does each service own its data, or is there one shared database? |
| Infrastructure automation | Is deployment a scripted, repeatable pipeline, or a manual process? |
| Design for failure | Does the system expect and tolerate services failing, or assume they never will? |
| Evolutionary design | Can a service's API change over time without a coordinated big-bang release? |

The next nine tutorials in this section take each of these in turn; this one is the map.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Nine characteristics arranged around a central Microservices label">
  <circle cx="320" cy="130" r="50" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="126" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Lewis &amp;</text>
  <text x="320" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Fowler</text>

  <g font-family="sans-serif" font-size="8" fill="#79c0ff">
    <text x="90" y="30">Componentization</text>
    <text x="300" y="18">Business capabilities</text>
    <text x="510" y="30">Products not projects</text>
    <text x="40" y="130">Smart endpoints,</text>
    <text x="40" y="142">dumb pipes</text>
    <text x="560" y="130">Decentralized</text>
    <text x="560" y="142">governance</text>
    <text x="90" y="230">Decentralized data</text>
    <text x="290" y="245">Infra automation</text>
    <text x="470" y="230">Design for failure</text>
  </g>
  <text x="320" y="200" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+ Evolutionary design</text>
</svg>

Nine characteristics, no single mandatory checklist — the more a system exhibits, the more it earns the "microservices" label.

## 5. Runnable example

Scenario: an "architecture audit" tool that scores a service description against the nine Lewis & Fowler characteristics, growing from a flat checklist into a comparison across two real systems.

### Level 1 — Basic

```java
// File: ArchitectureAuditBasic.java
import java.util.*;

public class ArchitectureAuditBasic {
    public static void main(String[] args) {
        Map<String, Boolean> traits = new LinkedHashMap<>();
        traits.put("componentization via services", true);
        traits.put("organized around business capabilities", true);
        traits.put("products not projects", false);
        traits.put("smart endpoints, dumb pipes", true);
        traits.put("decentralized governance", false);
        traits.put("decentralized data management", true);
        traits.put("infrastructure automation", true);
        traits.put("design for failure", false);
        traits.put("evolutionary design", true);

        for (var entry : traits.entrySet()) {
            System.out.println((entry.getValue() ? "[x] " : "[ ] ") + entry.getKey());
        }
    }
}
```

**How to run:** `javac ArchitectureAuditBasic.java && java ArchitectureAuditBasic` (JDK 17+).

Expected output:
```
[x] componentization via services
[x] organized around business capabilities
[ ] products not projects
[x] smart endpoints, dumb pipes
[ ] decentralized governance
[x] decentralized data management
[x] infrastructure automation
[ ] design for failure
[x] evolutionary design
```

A flat, unordered map of boolean flags — useful as a checklist but it tells you nothing about *how strong* the overall architecture is, just which boxes are ticked.

### Level 2 — Intermediate

```java
// File: ArchitectureAuditScore.java -- add a maturity score out of 9
import java.util.*;

public class ArchitectureAuditScore {
    static int score(Map<String, Boolean> traits) {
        return (int) traits.values().stream().filter(Boolean::booleanValue).count();
    }

    public static void main(String[] args) {
        Map<String, Boolean> traits = new LinkedHashMap<>();
        traits.put("componentization via services", true);
        traits.put("organized around business capabilities", true);
        traits.put("products not projects", false);
        traits.put("smart endpoints, dumb pipes", true);
        traits.put("decentralized governance", false);
        traits.put("decentralized data management", true);
        traits.put("infrastructure automation", true);
        traits.put("design for failure", false);
        traits.put("evolutionary design", true);

        int score = score(traits);
        System.out.println("Microservices maturity: " + score + "/9");
        if (score >= 7) System.out.println("Verdict: genuinely microservices-shaped");
        else if (score >= 4) System.out.println("Verdict: partially there -- some monolith habits remain");
        else System.out.println("Verdict: distributed monolith -- mostly network overhead, few real benefits");
    }
}
```

**How to run:** `javac ArchitectureAuditScore.java && java ArchitectureAuditScore` (JDK 17+).

Expected output:
```
Microservices maturity: 6/9
Verdict: partially there -- some monolith habits remain
```

Turning the checklist into a single number makes it usable in conversation: "we're a 6/9, missing ownership, decentralized governance, and failure tolerance" is a concrete, actionable statement in a way "we have microservices" is not.

### Level 3 — Advanced

```java
// File: ArchitectureAuditCompare.java -- compare TWO real systems side by side
import java.util.*;

public class ArchitectureAuditCompare {
    record System_(String name, Map<String, Boolean> traits) {
        int score() { return (int) traits.values().stream().filter(Boolean::booleanValue).count(); }
    }

    public static void main(String[] args) {
        List<String> keys = List.of(
            "componentization via services", "organized around business capabilities",
            "products not projects", "smart endpoints, dumb pipes", "decentralized governance",
            "decentralized data management", "infrastructure automation", "design for failure",
            "evolutionary design");

        // "legacy bundle": several services, but always deployed together, one shared DB
        Map<String, Boolean> legacyTraits = new LinkedHashMap<>();
        for (String k : keys) legacyTraits.put(k, false);
        legacyTraits.put("componentization via services", true);
        legacyTraits.put("organized around business capabilities", true);
        System_ legacyBundle = new System_("legacy-bundle", legacyTraits);

        // "true-microservices": exhibits nearly all nine
        Map<String, Boolean> trueTraits = new LinkedHashMap<>();
        for (String k : keys) trueTraits.put(k, true);
        trueTraits.put("decentralized governance", false); // one deliberate exception: shared lint rules
        System_ trueMicroservices = new System_("true-microservices", trueTraits);

        for (System_ sys : List.of(legacyBundle, trueMicroservices)) {
            System.out.println(sys.name() + ": " + sys.score() + "/9");
            for (String k : keys) {
                if (!sys.traits().get(k)) System.out.println("  missing: " + k);
            }
        }
    }
}
```

**How to run:** `javac ArchitectureAuditCompare.java && java ArchitectureAuditCompare` (JDK 17+).

Expected output:
```
legacy-bundle: 2/9
  missing: products not projects
  missing: smart endpoints, dumb pipes
  missing: decentralized governance
  missing: decentralized data management
  missing: infrastructure automation
  missing: design for failure
  missing: evolutionary design
true-microservices: 8/9
  missing: decentralized governance
```

The production-flavored case: two systems, both technically "split into services," scored and diffed side by side. `legacy-bundle` reveals itself as a distributed monolith — components exist, but almost none of the operational benefits do. `true-microservices` shows that even a strong architecture can deliberately fall short of one characteristic (here, a shared lint/style standard) without that being a flaw — the audit surfaces the gap so the team can confirm it's intentional rather than accidental.

## 6. Walkthrough

1. `keys` establishes the fixed, ordered list of all nine Lewis & Fowler characteristics — the same list both systems will be measured against, so the comparison is apples-to-apples.
2. `legacyTraits` starts every key at `false`, then flips on only the two traits `legacy-bundle` genuinely has (componentized services, organized by business capability) — modeling a team that split a monolith into services without changing anything else about how it's run.
3. `trueTraits` starts every key at `true`, then flips off exactly one (`decentralized governance`) to model a team that made a deliberate, informed tradeoff rather than an accidental gap.
4. The final loop runs `sys.score()` for each system — counting `true` values — then iterates `keys` again, printing every characteristic that system is missing.
5. For `legacy-bundle`, the loop prints seven `missing:` lines — a long, specific list a team can act on directly, rather than a vague "this doesn't feel like microservices."
6. For `true-microservices`, only `decentralized governance` prints as missing — confirming the one intentional exception, and nothing else.

```
legacyTraits:  [T, T, F, F, F, F, F, F, F]  -> score 2, 7 gaps printed
trueTraits:    [T, T, T, T, F, T, T, T, T]  -> score 8, 1 gap printed (governance)
```

## 7. Gotchas & takeaways

> **Gotcha:** Lewis and Fowler explicitly described *common characteristics*, not a mandatory checklist. Chasing a perfect 9/9 score can push a team into premature complexity — for example, adopting full decentralized governance (every team picks its own language and database) when a small organization would be far better served by a couple of shared, sensible defaults.

- The nine characteristics are a diagnostic lens for evaluating an architecture, not a certification test it must pass in full.
- Scoring a system against all nine turns a vague feeling ("this isn't really microservices") into a specific, actionable list of gaps.
- A system missing several characteristics on purpose, with the tradeoff understood, is different from a system missing them by accident — the audit surfaces the gap either way, but the team's judgment decides whether it matters.
- The next nine tutorials in this section each take one characteristic and go deep on it individually.
