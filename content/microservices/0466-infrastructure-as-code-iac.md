---
card: microservices
gi: 466
slug: infrastructure-as-code-iac
title: "Infrastructure as Code (IaC)"
---

## 1. What it is

**Infrastructure as Code (IaC)** means defining infrastructure — servers, networks, databases, load balancers, Kubernetes clusters — as declarative, version-controlled files rather than provisioning it through manual clicks in a cloud console or one-off scripts run by hand. An IaC tool reads the definition and creates, updates, or destroys real infrastructure to match it.

## 2. Why & when

You adopt IaC as soon as infrastructure needs to be reproducible, reviewable, and recoverable, rather than a unique, undocumented snowflake:

- **Manually-clicked infrastructure is undocumented and irreproducible.** If a production environment was assembled by hand through a cloud console over months, nobody can reliably recreate it — for a new region, a disaster-recovery environment, or even just a second staging environment that's supposed to match.
- **Configuration drift between environments causes "works in staging, breaks in production" bugs.** If staging and production infrastructure are each hand-maintained separately, small undocumented differences accumulate until the two environments genuinely diverge, and nobody notices until something breaks.
- **You want infrastructure changes reviewed the same way code changes are.** A pull request changing a Terraform file lets a teammate see exactly what infrastructure change is proposed before it happens — a console click leaves no such review trail.
- **You want it as soon as more than a couple of resources exist**, or as soon as you'll ever need a second, matching environment — even a small system benefits from being able to say precisely, and reproducibly, what infrastructure it needs.

## 3. Core concept

Think of architectural blueprints versus a building that was extended and modified ad hoc over decades with no plans kept: with blueprints, you can hand them to any construction crew and get the same building; with an undocumented building, every renovation requires someone to first go figure out what's actually there. IaC is the blueprint — a precise, written specification that any tool (or any engineer) can use to produce the exact same infrastructure, repeatably.

Concretely:

1. **Infrastructure is described declaratively** — you state the desired end state ("a database with these settings," "a load balancer routing to these targets"), not a sequence of imperative setup steps.
2. **The definition lives in version control**, alongside application code or in its own repository, subject to the same review and history as any other source file.
3. **An IaC tool reads the definition and compares it to what actually exists**, then computes a plan: what needs to be created, changed, or destroyed to reach the desired state.
4. **The plan is applied**, and the tool tracks the resulting real-world resources against the declaration, so the next run can compute an accurate diff again.
5. **Changing infrastructure means changing the file and re-applying** — never manually adjusting the live resource directly, which is the infrastructure equivalent of the drift GitOps guards against.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A declarative infrastructure file is read by a tool, which computes and applies a plan to make real infrastructure match" >
  <rect x="20" y="70" width="160" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">infra.tf (declared)</text>
  <text x="100" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">desired state</text>

  <rect x="240" y="70" width="160" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">IaC tool</text>
  <text x="320" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">plan -&gt; apply</text>

  <rect x="460" y="70" width="160" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="540" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">real infrastructure</text>
  <text x="540" y="112" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">actual state</text>

  <line x1="180" y1="97" x2="240" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="400" y1="97" x2="460" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the file is the source of truth; the tool computes the diff and applies only what's needed</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

A declarative file describes the desired infrastructure; the tool computes and applies the plan to make reality match.

## 5. Runnable example

Scenario: a simplified IaC engine managing a set of declared resources against a simulated "real world" state. We start with a basic declare-and-apply step, extend it to a plan/apply split that only touches what actually changed, then handle the hard case: destroying a resource that was removed from the declaration, without touching resources that are unrelated and unchanged.

### Level 1 — Basic

```java
// File: IaCBasic.java -- models declaring ONE resource and applying it to
// a simulated "real world" so that reality matches the declaration.
import java.util.*;

public class IaCBasic {
    record Resource(String type, String name, Map<String, String> config) {}

    static Map<String, Resource> declaredState = new HashMap<>(); // key -> Resource
    static Map<String, Resource> realWorld = new HashMap<>();

    static void apply() {
        for (Map.Entry<String, Resource> entry : declaredState.entrySet()) {
            System.out.println("[apply] creating " + entry.getKey() + " (" + entry.getValue().type() + ")");
            realWorld.put(entry.getKey(), entry.getValue());
        }
    }

    public static void main(String[] args) {
        declaredState.put("db-primary", new Resource("database", "db-primary", Map.of("size", "medium")));
        apply();
        System.out.println("[real world] now contains: " + realWorld.keySet());
    }
}
```

How to run: `java IaCBasic.java`

`declaredState` models the infrastructure file, and `realWorld` models actual provisioned resources. `apply` walks every declared resource and creates it in `realWorld` — a direct, unconditional application, standing in for a first-ever `terraform apply` against an empty environment.

### Level 2 — Intermediate

```java
// File: IaCPlanApply.java -- the SAME declare-and-apply idea, now split
// into a PLAN step that computes exactly what's new or changed, and an
// APPLY step that only touches THOSE resources -- not everything declared.
import java.util.*;

public class IaCPlanApply {
    record Resource(String type, String name, Map<String, String> config) {}

    static Map<String, Resource> declaredState = new HashMap<>();
    static Map<String, Resource> realWorld = new HashMap<>();

    static List<String> plan() {
        List<String> toCreateOrUpdate = new ArrayList<>();
        for (Map.Entry<String, Resource> entry : declaredState.entrySet()) {
            Resource existing = realWorld.get(entry.getKey());
            if (existing == null) {
                toCreateOrUpdate.add(entry.getKey());
                System.out.println("[plan] + " + entry.getKey() + " will be CREATED");
            } else if (!existing.config().equals(entry.getValue().config())) {
                toCreateOrUpdate.add(entry.getKey());
                System.out.println("[plan] ~ " + entry.getKey() + " will be UPDATED");
            } else {
                System.out.println("[plan]   " + entry.getKey() + " unchanged, no action");
            }
        }
        return toCreateOrUpdate;
    }

    static void apply(List<String> keysToApply) {
        for (String key : keysToApply) {
            System.out.println("[apply] applying " + key);
            realWorld.put(key, declaredState.get(key));
        }
    }

    public static void main(String[] args) {
        realWorld.put("db-primary", new Resource("database", "db-primary", Map.of("size", "medium")));
        declaredState.put("db-primary", new Resource("database", "db-primary", Map.of("size", "large"))); // size changed
        declaredState.put("cache-cluster", new Resource("cache", "cache-cluster", Map.of("nodes", "3"))); // brand new

        List<String> changes = plan();
        apply(changes);
        System.out.println("[real world] final: " + realWorld);
    }
}
```

How to run: `java IaCPlanApply.java`

`plan` never modifies `realWorld` — it only reads both maps and returns a list of keys that actually differ. `db-primary` already exists but with a different `config`, so it's marked `UPDATED`; `cache-cluster` doesn't exist yet, so it's marked `CREATED`. `apply` is then called only with that returned list, meaning any resource that *hadn't* changed (none, in this run, but the logic supports it) would never even be touched.

### Level 3 — Advanced

```java
// File: IaCDestroyUnused.java -- the SAME plan/apply engine, now handling
// the PRODUCTION-FLAVORED hard case: a resource was REMOVED from the
// declaration entirely (someone deleted its block from the file). The
// plan must detect this and mark it for DESTRUCTION, while resources that
// are simply unchanged must be left completely untouched.
import java.util.*;

public class IaCDestroyUnused {
    record Resource(String type, String name, Map<String, String> config) {}

    static Map<String, Resource> declaredState = new HashMap<>();
    static Map<String, Resource> realWorld = new HashMap<>();

    static Map<String, String> plan() {
        // action -> resource key
        Map<String, String> actions = new LinkedHashMap<>();
        for (Map.Entry<String, Resource> entry : declaredState.entrySet()) {
            Resource existing = realWorld.get(entry.getKey());
            if (existing == null) {
                System.out.println("[plan] + " + entry.getKey() + " CREATE");
                actions.put(entry.getKey(), "CREATE");
            } else if (!existing.config().equals(entry.getValue().config())) {
                System.out.println("[plan] ~ " + entry.getKey() + " UPDATE");
                actions.put(entry.getKey(), "UPDATE");
            } else {
                System.out.println("[plan]   " + entry.getKey() + " no change");
            }
        }
        // Anything in realWorld but NOT in declaredState was removed from the file.
        for (String existingKey : realWorld.keySet()) {
            if (!declaredState.containsKey(existingKey)) {
                System.out.println("[plan] - " + existingKey + " DESTROY (removed from declaration)");
                actions.put(existingKey, "DESTROY");
            }
        }
        return actions;
    }

    static void apply(Map<String, String> actions) {
        for (Map.Entry<String, String> action : actions.entrySet()) {
            String key = action.getKey();
            switch (action.getValue()) {
                case "CREATE", "UPDATE" -> {
                    System.out.println("[apply] " + action.getValue() + " " + key);
                    realWorld.put(key, declaredState.get(key));
                }
                case "DESTROY" -> {
                    System.out.println("[apply] DESTROY " + key);
                    realWorld.remove(key);
                }
            }
        }
    }

    public static void main(String[] args) {
        realWorld.put("db-primary", new Resource("database", "db-primary", Map.of("size", "medium")));
        realWorld.put("legacy-cache", new Resource("cache", "legacy-cache", Map.of("nodes", "1"))); // no longer declared

        declaredState.put("db-primary", new Resource("database", "db-primary", Map.of("size", "medium"))); // unchanged
        // legacy-cache intentionally absent from declaredState -- removed from the file

        Map<String, String> actions = plan();
        apply(actions);
        System.out.println("[real world] final: " + realWorld.keySet());
    }
}
```

How to run: `java IaCDestroyUnused.java`

`plan`'s second loop is what makes this level realistic: it iterates `realWorld.keySet()` looking for any key that's *not* in `declaredState` — `legacy-cache` matches, since it exists in reality but was removed from the declaration file. `db-primary`, by contrast, exists identically in both maps, so the first loop's `equals` check finds no difference and takes no action for it at all — it's never added to `actions`, so `apply` never touches it.

## 6. Walkthrough

Trace `IaCDestroyUnused.main` in order. **First**, `realWorld` is seeded with two resources — `db-primary` and `legacy-cache` — modeling infrastructure that already exists from a previous apply. `declaredState` only declares `db-primary`, with identical config, modeling a file where `legacy-cache`'s block was deleted by an engineer.

**Next**, `plan()` runs its first loop over `declaredState`. For `db-primary`, `existing` is found in `realWorld` and `existing.config().equals(entry.getValue().config())` is `true` (both say `"medium"`), so the "no change" branch runs and nothing is added to `actions`.

**Then**, `plan()`'s second loop runs over `realWorld.keySet()`, checking each against `declaredState`. `db-primary` is found in `declaredState`, so it's skipped. `legacy-cache` is *not* found in `declaredState`, so the destroy branch runs, prints the plan line, and adds `legacy-cache -> "DESTROY"` to `actions`.

**After that**, `apply(actions)` runs. `actions` contains exactly one entry: `legacy-cache -> DESTROY`. The `switch` matches the `"DESTROY"` case, prints the apply line, and calls `realWorld.remove("legacy-cache")` — `db-primary`, never having appeared in `actions` at all, is never passed through `apply`'s switch statement in any form.

**Finally**, `main` prints `realWorld.keySet()`, showing only `db-primary` remaining — `legacy-cache` has been fully removed from the simulated real world, matching the fact that it was removed from the declared file, while `db-primary` was never even touched by `apply` despite being present in both maps throughout.

```
[plan]   db-primary no change
[plan] - legacy-cache DESTROY (removed from declaration)
[apply] DESTROY legacy-cache
[real world] final: [db-primary]
```

## 7. Gotchas & takeaways

> Removing a resource's block from an IaC file is a destructive action, even though it looks like "just deleting a few lines" — the next apply will genuinely destroy that real infrastructure, potentially including its data. Review IaC diffs with the same (or greater) care as application code diffs, especially deletions.
- The plan step existing separately from apply, and being human-reviewable before anything actually changes, is one of IaC's biggest safety advantages over manual console changes — always review a plan before applying it against production infrastructure.
- IaC and [GitOps](0465-gitops.md) solve adjacent problems: IaC provisions the infrastructure a workload runs *on*; GitOps typically manages what runs *within* that infrastructure — many real systems use both together.
- Manually changing IaC-managed infrastructure directly (a console click, a raw API call) causes drift exactly like it does under GitOps — the next plan will either try to "fix" the manual change back, or, worse, get confused about the resource's true state.
- Destructive actions (as in Level 3) deserve extra scrutiny in any real tool — production IaC tools typically require explicit confirmation before a destroy, precisely because the consequence is often irreversible.
- Keeping infrastructure definitions in the same review process as code (pull requests, approvals) is what actually delivers IaC's core promise: infrastructure changes become as visible, auditable, and reversible as any other code change.
