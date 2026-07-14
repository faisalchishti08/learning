---
card: microservices
gi: 465
slug: gitops
title: "GitOps"
---

## 1. What it is

**GitOps** is an operational model where a **Git repository is the single source of truth** for what should be running in a cluster — the desired state of every deployment, service, and configuration lives as declarative files in Git, and an automated controller continuously reconciles the *actual* running state to match whatever's committed. You change the system by committing to Git, never by running imperative commands directly against the cluster.

## 2. Why & when

You adopt GitOps when you want deployments to be auditable, reproducible, and self-healing rather than a series of untracked, manual commands:

- **Every change has a full audit trail for free.** Since the desired state lives in Git, `git log` and `git blame` answer "who changed what, when, and why" for the entire cluster's configuration — no separate change-tracking system needed.
- **Rollback becomes `git revert`.** Because the last-known-good state is just an earlier commit, reverting a bad deployment is the same operation as reverting any other bad code change — no special deployment-specific rollback tooling required.
- **Manual `kubectl apply` commands drift and get lost.** An engineer fixing something directly against the live cluster, without committing the change, creates configuration drift — the cluster now differs from what anyone can see in source control, and the next automated sync can silently undo their fix.
- **You want it as soon as you're running anything on an orchestrator like Kubernetes with more than one person able to make changes** — the discipline of "the repo is truth" scales from a single small cluster to a large multi-team platform without changing the model.

## 3. Core concept

Think of a thermostat: you don't manually adjust the furnace every time the room gets cold — you set a target temperature (the desired state), and the thermostat continuously checks the actual temperature and adjusts the furnace to match. GitOps replaces "temperature" with "cluster configuration": you declare the target in Git, and a controller keeps nudging the live cluster to match it, indefinitely, without a human manually intervening each time.

Concretely:

1. **Desired state is declared in Git** — YAML manifests (or similar) describing what should be running: which images, how many replicas, what configuration.
2. **A change is made by committing to Git**, typically through a pull request that gets reviewed like any other code change.
3. **A GitOps controller, running in (or watching) the cluster, continuously compares the live state to the state declared in Git.**
4. **If they differ, the controller reconciles** — applying whatever changes are needed to make the live cluster match Git, whether that's deploying a new version, scaling a deployment, or reverting a manual change nobody committed.
5. **This reconciliation loop runs continuously**, not just once at deploy time — so even an out-of-band manual change to the live cluster gets automatically corrected back to whatever Git says, usually within seconds to minutes.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A GitOps controller continuously compares the live cluster state to Git and reconciles any difference">
  <rect x="20" y="30" width="170" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Git repo</text>
  <text x="105" y="72" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">desired state (YAML)</text>

  <rect x="240" y="30" width="170" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="325" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">GitOps controller</text>
  <text x="325" y="72" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">compares + reconciles</text>

  <rect x="460" y="30" width="160" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="540" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">live cluster</text>
  <text x="540" y="72" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">actual state</text>

  <line x1="190" y1="57" x2="240" y2="57" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="410" y1="50" x2="460" y2="50" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="460" y1="65" x2="410" y2="65" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="325" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">continuous loop: read desired state, read actual state, reconcile any difference, repeat</text>
  <text x="325" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">a manual, uncommitted change to the live cluster gets silently reverted on the next reconcile</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The controller reads Git as the target, compares it to the live cluster, and continuously reconciles any difference.

## 5. Runnable example

Scenario: a simplified GitOps reconciliation loop comparing a "Git" desired-state map to a "live cluster" state map. We start with a basic one-time sync, extend it to a continuous reconciliation loop that detects and corrects drift, then handle the hard case: someone manually changing the live cluster out-of-band, which the loop must detect and revert.

### Level 1 — Basic

```java
// File: GitOpsBasic.java -- models Git as the DESIRED state and the
// cluster as the ACTUAL state, with a controller doing ONE reconcile pass
// to make actual match desired.
import java.util.*;

public class GitOpsBasic {
    static Map<String, Integer> gitDesiredState = new HashMap<>(); // service -> replica count
    static Map<String, Integer> liveClusterState = new HashMap<>();

    static void reconcile() {
        for (Map.Entry<String, Integer> entry : gitDesiredState.entrySet()) {
            String service = entry.getKey();
            int desiredReplicas = entry.getValue();
            Integer actualReplicas = liveClusterState.get(service);
            if (!Integer.valueOf(desiredReplicas).equals(actualReplicas)) {
                System.out.println("[reconcile] " + service + ": actual=" + actualReplicas
                        + " desired=" + desiredReplicas + " -- applying change");
                liveClusterState.put(service, desiredReplicas);
            } else {
                System.out.println("[reconcile] " + service + ": already matches desired state (" + desiredReplicas + ")");
            }
        }
    }

    public static void main(String[] args) {
        gitDesiredState.put("order-service", 3);
        // liveClusterState starts empty -- nothing is running yet.
        reconcile();
        System.out.println("[cluster] live state now: " + liveClusterState);
    }
}
```

How to run: `java GitOpsBasic.java`

`gitDesiredState` and `liveClusterState` are two separate maps modeling two separate sources of truth — Git's declared intent, and what's actually running. `reconcile` never edits `gitDesiredState`; it only ever reads from it and writes into `liveClusterState`, which is the whole point: Git leads, the cluster follows.

### Level 2 — Intermediate

```java
// File: GitOpsContinuousLoop.java -- the SAME reconciliation, now run
// CONTINUOUSLY across multiple cycles, with a Git commit changing the
// desired state PARTWAY THROUGH -- modeling a real commit landing while
// the controller keeps polling.
import java.util.*;

public class GitOpsContinuousLoop {
    static Map<String, Integer> gitDesiredState = new HashMap<>();
    static Map<String, Integer> liveClusterState = new HashMap<>();

    static void reconcile(int cycle) {
        for (Map.Entry<String, Integer> entry : gitDesiredState.entrySet()) {
            String service = entry.getKey();
            int desiredReplicas = entry.getValue();
            Integer actualReplicas = liveClusterState.get(service);
            if (!Integer.valueOf(desiredReplicas).equals(actualReplicas)) {
                System.out.println("[cycle " + cycle + "] " + service + ": " + actualReplicas + " -> " + desiredReplicas);
                liveClusterState.put(service, desiredReplicas);
            } else {
                System.out.println("[cycle " + cycle + "] " + service + ": in sync (" + desiredReplicas + ")");
            }
        }
    }

    public static void main(String[] args) {
        gitDesiredState.put("order-service", 3);

        reconcile(1); // initial deploy
        reconcile(2); // nothing changed, should stay in sync

        System.out.println("[git] a commit lands: order-service scaled to 5 replicas");
        gitDesiredState.put("order-service", 5); // simulates a new commit

        reconcile(3); // controller picks up the new desired state on its next poll
    }
}
```

How to run: `java GitOpsContinuousLoop.java`

`reconcile` is called three times across simulated polling cycles, and `gitDesiredState` is mutated directly between cycle 2 and cycle 3 to model a new commit landing. Cycle 1 applies the initial state, cycle 2 finds everything already in sync and changes nothing, and cycle 3 detects the new desired value (`5`) differs from the live state (`3`) and reconciles it — the controller never needed to be told a commit happened, it simply noticed the difference on its next scheduled comparison.

### Level 3 — Advanced

```java
// File: GitOpsDriftCorrection.java -- the SAME continuous loop, now
// handling the PRODUCTION-FLAVORED hard case: someone runs a MANUAL,
// uncommitted change directly against the live cluster (a classic
// incident-response reflex, or just someone forgetting the GitOps rule).
// The controller must detect this DRIFT on its next reconcile and revert
// it back to whatever Git actually says, with no special-casing needed --
// the reconcile logic is identical to normal reconciliation.
import java.util.*;

public class GitOpsDriftCorrection {
    static Map<String, Integer> gitDesiredState = new HashMap<>();
    static Map<String, Integer> liveClusterState = new HashMap<>();

    static void reconcile(int cycle) {
        for (Map.Entry<String, Integer> entry : gitDesiredState.entrySet()) {
            String service = entry.getKey();
            int desiredReplicas = entry.getValue();
            Integer actualReplicas = liveClusterState.get(service);
            if (!Integer.valueOf(desiredReplicas).equals(actualReplicas)) {
                System.out.println("[cycle " + cycle + "] DRIFT DETECTED: " + service + " actual=" + actualReplicas
                        + " desired=" + desiredReplicas + " -- correcting");
                liveClusterState.put(service, desiredReplicas);
            } else {
                System.out.println("[cycle " + cycle + "] " + service + ": in sync (" + desiredReplicas + ")");
            }
        }
    }

    public static void main(String[] args) {
        gitDesiredState.put("order-service", 3);
        reconcile(1); // deploys the initial 3 replicas

        System.out.println();
        System.out.println("[incident] an engineer manually runs `kubectl scale --replicas=10`, bypassing Git entirely");
        liveClusterState.put("order-service", 10); // direct, UNCOMMITTED change to the live cluster

        reconcile(2); // controller's next poll notices the drift and reverts it

        System.out.println();
        System.out.println("[cluster] final live state: " + liveClusterState + " (matches Git, manual change was reverted)");
    }
}
```

How to run: `java GitOpsDriftCorrection.java`

The "incident" line mutates `liveClusterState` directly, completely bypassing `gitDesiredState` — exactly like a manual `kubectl` command against a real cluster, with nothing committed to Git. `reconcile(2)` runs the identical comparison logic as every other cycle: it finds `actualReplicas = 10` doesn't match `desiredReplicas = 3`, and — with no special "was this a manual change?" logic anywhere — corrects `liveClusterState` back to `3`, exactly as if `10` had been an ordinary deployment failure rather than a deliberate human action.

## 6. Walkthrough

Trace `GitOpsDriftCorrection.main` in order. **First**, `gitDesiredState.put("order-service", 3)` declares the desired state, and `reconcile(1)` runs: `liveClusterState` has no entry for `order-service` yet, so `actualReplicas` is `null`, which doesn't equal `3`, triggering the drift-detected branch and setting `liveClusterState.put("order-service", 3)`.

**Next**, the simulated incident runs: `liveClusterState.put("order-service", 10)` directly overwrites the live state to `10`, entirely outside of `reconcile` and with no corresponding change to `gitDesiredState` — Git still says `3`.

**Then**, `reconcile(2)` runs its normal comparison loop. It reads `desiredReplicas = 3` from `gitDesiredState` (unchanged) and `actualReplicas = 10` from `liveClusterState` (now drifted). Since `3` does not equal `10`, the same drift-detection branch that ran in cycle 1 runs again — printing the drift message and resetting `liveClusterState.put("order-service", 3)`.

**After that**, no further reconcile cycles run in this program, but in a real continuous controller, this exact comparison would keep running indefinitely, on a fixed interval, forever ready to catch the next drift the instant it occurs.

**Finally**, `main` prints the live cluster's final state, showing `order-service` back at `3` — the manual change was overwritten by the very next reconciliation pass, with the reconcile logic never needing to know or care that the drift came from a human command rather than, say, a crashed Pod.

```
[cycle 1] DRIFT DETECTED: order-service actual=null desired=3 -- correcting

[incident] an engineer manually runs `kubectl scale --replicas=10`, bypassing Git entirely
[cycle 2] DRIFT DETECTED: order-service actual=10 desired=3 -- correcting

[cluster] final live state: {order-service=3} (matches Git, manual change was reverted)
```

## 7. Gotchas & takeaways

> GitOps's automatic drift correction is a double-edged sword during an actual incident: an engineer who manually scales a service up to handle a traffic spike, without also committing that change to Git, will have their emergency fix silently reverted on the next reconcile cycle — sometimes seconds later. Emergency changes need to go through Git too, even under time pressure, or be made through an explicitly Git-aware emergency procedure.
- The core discipline is simple to state and easy to violate under pressure: never run an imperative, uncommitted change directly against a GitOps-managed cluster — it will not stick.
- Pull-request review on infrastructure changes is a natural fit for GitOps — since the desired state is just files in Git, the same review, approval, and audit tooling used for application code applies directly to deployment configuration.
- Rollback is exactly `git revert` plus waiting for the next reconcile cycle — no bespoke rollback tooling, no separate deployment history system to consult.
- GitOps pairs naturally with [Infrastructure as Code](0466-infrastructure-as-code-iac.md) — Git as the source of truth for *what* should exist, and IaC tooling as the mechanism for actually provisioning it.
- Reconciliation interval matters: a controller that only checks every ten minutes leaves a ten-minute window where drift, or a failed deployment, goes uncorrected — tune the interval to match how quickly you need the system to self-heal.
