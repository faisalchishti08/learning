---
card: system-design
gi: 220
slug: immutable-infrastructure-iac
title: Immutable infrastructure & IaC
---

## 1. What it is

**Immutable infrastructure** means servers (or containers, or images) are never modified after they are created — instead of SSHing in to patch a running server, you build a new server (or image) with the change and replace the old one entirely. **Infrastructure as Code (IaC)** is defining infrastructure — servers, networks, load balancers, databases — as version-controlled configuration files (e.g. Terraform, CloudFormation) rather than clicking through a cloud console or running manual commands.

## 2. Why & when

A fleet of servers that are individually patched, tweaked, and configured over months or years drifts — no two servers end up in exactly the same state, and nobody can fully reconstruct how any given server got the way it is ("configuration drift"). This makes debugging environment-specific issues extremely hard, and disaster recovery unreliable, because you cannot be certain a freshly built replacement server matches the one that failed.

Immutable infrastructure eliminates drift by construction: if servers are never modified in place, every server running a given version is, by definition, identical to every other server running that version — there is no history of individual tweaks to diverge. IaC makes the infrastructure itself reproducible and reviewable: the exact same configuration file that describes production can build an identical staging environment, and every infrastructure change goes through the same code review process as application code. Use both together for any system where consistency, reproducibility, and auditability of infrastructure changes matter — which is nearly every production system past a small, single-server hobby project.

## 3. Core concept

- **No in-place changes, ever.** A running server or container is treated as disposable. A configuration change means building a new image (see [containers & images](0216-containers-images.md) for the same idea applied to application packaging) and replacing the old instances with new ones running it — never `ssh`-ing in and editing a config file live.
- **Declarative configuration.** IaC tools describe the *desired end state* ("3 web servers, this load balancer, this database, these security rules"), not a sequence of imperative steps — the tool figures out what changes are needed to reach that state from wherever things currently are.
- **Plan before apply.** Most IaC tools compute and show a "plan" — exactly what will be created, changed, or destroyed — before actually applying it, so you can review the real effect of a change before it happens, the same discipline as reviewing a code diff before merging it.
- **State tracking.** The IaC tool keeps a record of what it last created, so it can compute an accurate diff between the desired configuration and the actual current infrastructure on the next run, rather than blindly reapplying everything every time.
- **Version-controlled and reviewable.** Because infrastructure is defined in text files, changes go through the same pull-request review, history, and rollback (`git revert`) as any other code change — a capability manual console changes never had.

## 4. Diagram

```
  MUTABLE (in-place patching)                 IMMUTABLE (replace, never patch)

  server-1 (patched 3 times,         vs        image v1.0 -> server-1, server-2, server-3
    manually, over 6 months)                     (all built from the SAME image, byte-identical)
  server-2 (patched differently,                 |
    missed one patch)                            | new change needed
  server-3 (never patched at all)                 v
                                                 image v1.1 -> new server-1, server-2, server-3
  -> three servers, three different                (old servers destroyed, not modified)
     actual states, none matching
     any documented configuration               -> three servers, GUARANTEED identical,
                                                    because none was ever hand-edited
```
*Caption: mutable infrastructure accumulates undocumented differences over time. Immutable infrastructure guarantees every instance of a given version is identical, because no instance is ever individually changed.*

## 5. Runnable example

This models the IaC workflow — declare desired state, compute a plan, apply it — and the immutable-replacement pattern, since a real IaC tool provisions actual cloud resources that a single file cannot run.

**Level 1 — Basic.** Declare a desired infrastructure state and compute a plan (create/update/destroy) against the current actual state.

**Level 2 — Intermediate.** Apply the plan, then show that re-running plan against the same desired state produces no changes (idempotent).

**Level 3 — Advanced.** Model immutable replacement: a config change replaces servers entirely rather than patching them in place, and show the state-tracking that makes repeated applies safe.

```java
// ImmutableInfraIacDemo.java
import java.util.*;

public class ImmutableInfraIacDemo {

    record ServerConfig(String name, String imageVersion, int cpuCores) {}

    // ---------- Level 1: desired state vs actual state -> a plan ----------
    static class Infrastructure {
        Map<String, ServerConfig> actualState = new LinkedHashMap<>(); // what IaC last created ("state tracking")

        List<String> plan(Map<String, ServerConfig> desiredState) {
            List<String> actions = new ArrayList<>();
            for (var entry : desiredState.entrySet()) {
                ServerConfig desired = entry.getValue();
                ServerConfig actual = actualState.get(entry.getKey());
                if (actual == null) {
                    actions.add("CREATE " + entry.getKey() + " (" + desired + ")");
                } else if (!actual.equals(desired)) {
                    // Level 3 will show this becomes REPLACE, not in-place edit, for immutable infra.
                    actions.add("REPLACE " + entry.getKey() + " (" + actual + " -> " + desired + ")");
                } else {
                    actions.add("NO CHANGE " + entry.getKey());
                }
            }
            for (String existingName : actualState.keySet()) {
                if (!desiredState.containsKey(existingName)) actions.add("DESTROY " + existingName);
            }
            return actions;
        }

        void apply(Map<String, ServerConfig> desiredState) {
            actualState.clear();
            actualState.putAll(desiredState); // after apply, actual matches desired exactly
        }
    }

    public static void main(String[] args) {
        Infrastructure infra = new Infrastructure();

        System.out.println("Level 1 - plan against empty actual state (first run):");
        Map<String, ServerConfig> desired = new LinkedHashMap<>();
        desired.put("web-1", new ServerConfig("web-1", "v1.0", 2));
        desired.put("web-2", new ServerConfig("web-2", "v1.0", 2));
        for (String action : infra.plan(desired)) System.out.println("  " + action);

        System.out.println("\nLevel 2 - apply the plan, then re-plan the SAME desired state (idempotent):");
        infra.apply(desired);
        System.out.println("  applied. actual state: " + infra.actualState.keySet());
        for (String action : infra.plan(desired)) System.out.println("  " + action);

        System.out.println("\nLevel 3 - change imageVersion in desired state -> REPLACE, not in-place patch:");
        Map<String, ServerConfig> updatedDesired = new LinkedHashMap<>();
        updatedDesired.put("web-1", new ServerConfig("web-1", "v1.1", 2)); // version bumped
        updatedDesired.put("web-2", new ServerConfig("web-2", "v1.1", 2)); // version bumped
        for (String action : infra.plan(updatedDesired)) System.out.println("  " + action);
        System.out.println("  applying...");
        infra.apply(updatedDesired);
        System.out.println("  actual state after apply: " + infra.actualState);

        System.out.println("\n  removing web-2 from desired state entirely:");
        Map<String, ServerConfig> scaleDown = new LinkedHashMap<>();
        scaleDown.put("web-1", new ServerConfig("web-1", "v1.1", 2));
        for (String action : infra.plan(scaleDown)) System.out.println("  " + action);
    }
}
```

**How to run:** `java ImmutableInfraIacDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `infra.plan(desired)` runs against an empty `actualState` (nothing has been provisioned yet). For each entry in `desired`, the loop finds `actual == null` and records a `"CREATE"` action — the plan for a first run is simply "create everything," which is what you would expect to review before the very first apply.
2. **Level 2:** `infra.apply(desired)` copies `desired` into `actualState`, simulating the servers actually being created. Calling `infra.plan(desired)` again — with the exact same desired state — now finds `actual.equals(desired)` true for both servers and records `"NO CHANGE"` for each. This idempotency (running the same plan twice does nothing the second time) is a core property of good IaC: you can safely re-run it without fear of duplicating or disrupting anything.
3. **Level 3:** `updatedDesired` changes `imageVersion` from `"v1.0"` to `"v1.1"` for both servers. `infra.plan(updatedDesired)` finds `actual` exists but `!actual.equals(desired)` (the version differs), and records `"REPLACE"` — the comment in the code and the printed action both make clear this means destroying the old server and creating a new one, never patching the running server's image version in place.
4. `infra.apply(updatedDesired)` runs, and `infra.actualState` now shows both servers at `v1.0`... actually at `v1.1` — the state was overwritten wholesale to match the new desired configuration, modeling the real replace-not-patch behavior.
5. The final `scaleDown` desired state omits `web-2` entirely. `infra.plan(scaleDown)` finds `web-1` unchanged (`"NO CHANGE"`) and then, in the second loop, finds `"web-2"` present in `actualState` but absent from `desiredState`, recording `"DESTROY web-2"` — this shows IaC handles removal the same declarative way as creation and modification: you simply stop declaring a resource, and the tool figures out it needs to be destroyed.

## 7. Gotchas & takeaways

> **Gotcha:** if someone makes a manual change directly against the actual infrastructure (a console click, a manual `ssh` fix) outside the IaC tool, the tool's tracked state no longer matches reality. The next plan can be surprising — either the tool "reverts" the manual change (destroying work someone thought was permanent) or the drift goes undetected until a plan behaves unexpectedly. Never make manual changes to infrastructure managed by IaC.

- Always review the plan output before applying — this is the infrastructure equivalent of reviewing a code diff before merging, and it is what catches an unintended destroy or replace before it happens.
- Immutable infrastructure and IaC reinforce each other: IaC's declarative "desired state" model is a natural fit for immutable infrastructure's "replace, never patch" discipline, as Level 3 shows directly.
- Store IaC configuration files in version control alongside (or referencing) the application code they provision infrastructure for, so infrastructure changes are reviewable, auditable, and revertible the same way code changes are.
- This discipline is what makes reliable [disaster recovery](0222-disaster-recovery-rpo-rto.md) possible — you can only be confident a rebuilt environment matches the original if the infrastructure that built it is fully captured as code, not as undocumented manual steps.
