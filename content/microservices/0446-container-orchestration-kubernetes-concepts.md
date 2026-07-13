---
card: microservices
gi: 446
slug: container-orchestration-kubernetes-concepts
title: "Container orchestration (Kubernetes) concepts"
---

## 1. What it is

**Container orchestration** is the automated management of where and how many copies of a containerized service run, how they're networked together, and how the system recovers when something breaks — without a human manually starting, stopping, or replacing containers by hand. **Kubernetes** is the dominant orchestrator implementing this idea: you tell it a **desired state** ("I want three healthy replicas of `order-service` running"), and a set of background **control loops** continuously compares that desired state to the **actual state** of the cluster, taking whatever action closes the gap — scheduling a new container, killing a misbehaving one, or moving work off a dead machine.

## 2. Why & when

You need an orchestrator the moment you're running enough service instances, across enough machines, that manually tracking "which containers are running where, and are they healthy" stops being feasible — which in a microservices system is almost immediately, since [service instance per container](0435-service-instance-per-container.md) already means dozens of independently deployed units before you've added any redundancy.

- **Manual container management doesn't scale.** With one service and one instance, SSH-ing in to restart a crashed process is fine. With dozens of services, each with several replicas, spread across many machines, that becomes a full-time job an orchestrator does continuously and instantly instead.
- **Machines fail; the desired state shouldn't care which machine a pod happens to be on.** An orchestrator reschedules work from a dead node onto healthy ones automatically, because the declaration was "three replicas of this service," not "these three specific machines."
- **Declarative beats imperative at scale.** Instead of scripting the exact sequence of commands to reach a state ("start this container, then that one, then check this one didn't crash..."), you declare the end state you want and let a control loop figure out and continuously re-verify the steps — this is what makes the system self-healing rather than a one-time setup script.
- **You need this as soon as you deploy to more than a handful of long-lived servers**, or as soon as "a service crashed and nobody noticed for an hour" becomes a real risk to availability.

## 3. Core concept

A useful analogy is a home thermostat. You don't manually turn the furnace on and off all day — you declare a desired temperature, and the thermostat continuously measures the actual temperature and turns the furnace on or off to close the gap, on its own, forever, without further instruction. Kubernetes control loops work exactly the same way, just applied to "how many healthy copies of this container are running" instead of degrees.

Concretely, a few pieces make this work:

1. **Desired state, declared, not scripted.** You submit a specification (for example, "run 3 replicas of image `order-service:2.1`") to the cluster's API rather than issuing step-by-step commands.
2. **A reconciliation control loop** runs continuously in the background, observing the actual state (how many replicas are actually running and healthy right now) and comparing it to the desired state, taking corrective action whenever they diverge — this is the same reconciliation pattern used throughout Kubernetes, from pod counts to network rules.
3. **Scheduling** decides *where* new work runs: the orchestrator picks a machine (node) with enough free capacity, rather than a human deciding by hand.
4. **Self-healing** falls directly out of the loop running continuously: a crashed pod, an unhealthy pod (see [health checks for orchestrators](0445-health-checks-for-orchestrators.md)), or a dead node all just look like "actual state diverged from desired state," and the same loop that handles first-time scheduling also handles recovery — no separate "disaster recovery" code path is needed.
5. **Backoff prevents the loop from thrashing.** A pod that crashes immediately every time it's restarted would otherwise be recreated in a tight, resource-burning loop; real orchestrators track restart counts and back off, eventually giving up on immediate retries rather than hammering a pod that can never succeed.

The building blocks the control loop actually manages — Pods, Deployments, Services, Ingress — are covered next in [Pods, Deployments, Services, Ingress](0447-pods-deployments-services-ingress.md); this topic is about the reconciliation idea that powers all of them.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A control loop continuously compares desired state to actual state and takes action to close any gap, the same mechanism used for scheduling, self-healing, and recovery from node failure">
  <rect x="30" y="30" width="200" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="130" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Desired state</text>
  <text x="130" y="75" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">"3 healthy replicas"</text>

  <rect x="30" y="170" width="200" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="130" y="195" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Actual state</text>
  <text x="130" y="215" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">"1 running, 1 crashed"</text>

  <rect x="290" y="95" width="200" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="390" y="120" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Control loop</text>
  <text x="390" y="138" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">compare, then act</text>
  <text x="390" y="153" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">schedule / kill / reschedule</text>

  <line x1="230" y1="60" x2="290" y2="115" stroke="#79c0ff" marker-end="url(#arrow1)"/>
  <line x1="230" y1="200" x2="290" y2="145" stroke="#f0883e" marker-end="url(#arrow2)"/>

  <path d="M 490 130 C 560 130 560 30 390 30 L 300 30" fill="none" stroke="#6db33f" stroke-dasharray="4,3" marker-end="url(#arrow3)"/>
  <text x="500" y="20" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">schedules a replacement pod</text>

  <defs>
    <marker id="arrow1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker>
    <marker id="arrow2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
    <marker id="arrow3" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
  </defs>

  <text x="390" y="245" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the same loop handles first-time scheduling AND recovery from failure</text>
</svg>

The control loop never stops running: it compares desired to actual state on every cycle and takes whatever action closes the gap, whether that's initial scheduling or recovering from a crash.

## 5. Runnable example

Scenario: a simplified reconciliation control loop for a service that should always have a fixed number of healthy pods running. We start with the bare desired-vs-actual comparison, add health as a second reconciliation signal, then handle the hard case: a pod that crashes immediately every time it restarts, which must trigger backoff rather than an infinite recreate loop.

### Level 1 — Basic

```java
// File: ReconciliationBasic.java -- models the CORE idea of an orchestrator:
// you declare a DESIRED state, and a control loop repeatedly compares it to
// the ACTUAL state, taking action to close any gap.
import java.util.*;

public class ReconciliationBasic {
    public static void main(String[] args) {
        int desiredReplicas = 3;
        List<String> actualPods = new ArrayList<>(List.of("pod-1")); // only 1 running

        System.out.println("Desired replicas: " + desiredReplicas);
        System.out.println("Actual pods before reconcile: " + actualPods);

        int nextId = 2;
        while (actualPods.size() < desiredReplicas) {
            String newPod = "pod-" + nextId++;
            actualPods.add(newPod);
            System.out.println("Control loop: actual (" + (actualPods.size() - 1) + ") < desired (" + desiredReplicas + ") -- scheduling " + newPod);
        }

        System.out.println("Actual pods after reconcile: " + actualPods);
        System.out.println("Converged: " + (actualPods.size() == desiredReplicas));
    }
}
```

How to run: `java ReconciliationBasic.java`

`desiredReplicas` is the declared state; `actualPods` is what's really running. The `while` loop is the control loop itself: it keeps comparing the two and scheduling new pods until they match, then stops — there's no separate "first deploy" code path, just the loop converging from a starting state of 1 pod to the desired 3.

### Level 2 — Intermediate

```java
// File: ReconciliationWithHealth.java -- the SAME control loop, now also
// reconciling on POD HEALTH, not just pod COUNT: an unhealthy pod is
// removed and replaced even though the count already matches desired.
import java.util.*;

public class ReconciliationWithHealth {
    static class Pod {
        final String name;
        boolean healthy;
        Pod(String name, boolean healthy) { this.name = name; this.healthy = healthy; }
        public String toString() { return name + (healthy ? "(ok)" : "(unhealthy)"); }
    }

    public static void main(String[] args) {
        int desiredReplicas = 3;
        List<Pod> pods = new ArrayList<>(List.of(
                new Pod("pod-1", true),
                new Pod("pod-2", false), // crashed
                new Pod("pod-3", true)));
        int nextId = 4;

        System.out.println("Before reconcile: " + pods);

        Iterator<Pod> it = pods.iterator();
        while (it.hasNext()) {
            Pod p = it.next();
            if (!p.healthy) {
                System.out.println("Control loop: " + p.name + " is unhealthy -- terminating it");
                it.remove();
            }
        }
        while (pods.size() < desiredReplicas) {
            Pod fresh = new Pod("pod-" + nextId++, true);
            pods.add(fresh);
            System.out.println("Control loop: actual (" + (pods.size() - 1) + ") < desired (" + desiredReplicas + ") -- scheduling " + fresh.name);
        }

        System.out.println("After reconcile: " + pods);
    }
}
```

How to run: `java ReconciliationWithHealth.java`

The loop now runs two reconciliation passes: first it removes any pod whose health signal (see [health checks for orchestrators](0445-health-checks-for-orchestrators.md)) is failing, then it re-runs the same "schedule until desired is met" logic from Level 1. Note that `pod-count == desired` was already true going in (3 pods existed) — reconciliation still acts, because the *count* being right doesn't mean the *state* is right if one of those three is broken.

### Level 3 — Advanced

```java
// File: ReconciliationWithBackoff.java -- the SAME control loop, now
// handling a PRODUCTION-FLAVORED hard case: a pod that crashes immediately
// after every restart. Naive reconciliation would recreate it in a tight
// infinite loop; a real orchestrator applies exponential backoff and
// eventually stops hammering it (CrashLoopBackOff) instead of burning
// scheduler capacity on a pod that can never succeed.
import java.util.*;

public class ReconciliationWithBackoff {
    static final int MAX_RESTARTS_BEFORE_BACKOFF = 3;
    // restart counts persist ACROSS reconcile cycles, keyed by logical pod name.
    static final Map<String, Integer> restartCounts = new HashMap<>();
    static final Set<String> present = new LinkedHashSet<>(); // pods currently running

    public static void main(String[] args) {
        present.add("pod-stable");
        present.add("pod-crashy");

        for (int cycle = 1; cycle <= 6; cycle++) {
            System.out.println("--- reconcile cycle " + cycle + " ---");

            // Simulate health: pod-crashy always crashes right after it starts.
            boolean crashyIsUnhealthy = present.contains("pod-crashy");

            if (crashyIsUnhealthy) {
                int restarts = restartCounts.getOrDefault("pod-crashy", 0);
                if (restarts >= MAX_RESTARTS_BEFORE_BACKOFF) {
                    System.out.println("pod-crashy: restartCount=" + restarts
                            + " >= " + MAX_RESTARTS_BEFORE_BACKOFF + " -- CrashLoopBackOff, NOT recreating this cycle");
                    present.remove("pod-crashy");
                } else {
                    present.remove("pod-crashy");
                    restartCounts.put("pod-crashy", restarts + 1);
                    present.add("pod-crashy");
                    System.out.println("pod-crashy: unhealthy, recreated (restartCount now " + (restarts + 1) + ")");
                }
            }

            if (!present.contains("pod-stable")) {
                present.add("pod-stable");
                System.out.println("pod-stable: recreated");
            }

            System.out.println("End of cycle " + cycle + ": present=" + present
                    + ", pod-crashy restartCount=" + restartCounts.getOrDefault("pod-crashy", 0));
        }

        System.out.println();
        System.out.println("Final outcome: the orchestrator stopped recreating pod-crashy after "
                + MAX_RESTARTS_BEFORE_BACKOFF + " failed restarts, avoiding a reconciliation storm, "
                + "while pod-stable remained healthy and present throughout.");
    }
}
```

How to run: `java ReconciliationWithBackoff.java`

`restartCounts` persists across cycles, modeling the fact that a real orchestrator remembers how many times it has already tried to fix a given pod. `pod-crashy` fails every single cycle it's present, so it accumulates restarts; once `restartCounts` reaches `MAX_RESTARTS_BEFORE_BACKOFF`, the loop deliberately stops recreating it rather than looping forever, while `pod-stable` (which never fails) is left alone entirely — reconciliation only acts where actual state has actually diverged from desired.

## 6. Walkthrough

Trace `ReconciliationWithBackoff.main` in order. **First**, `present` starts with both `pod-stable` and `pod-crashy`, and `restartCounts` is empty.

**Next**, in cycle 1, `crashyIsUnhealthy` is `true` (it always crashes). `restarts` reads `0` from the empty map, which is below the threshold of `3`, so the loop removes and re-adds `pod-crashy` and records `restartCounts.put("pod-crashy", 1)`. `pod-stable` is already present, so nothing happens to it.

**Then**, cycles 2 and 3 repeat the same pattern: `pod-crashy` is unhealthy again each time, its restart count is still below `3`, so it's recreated again, pushing the count to `2` then `3`.

**In cycle 4**, `restarts` now reads `3`, which is no longer less than `MAX_RESTARTS_BEFORE_BACKOFF`. The loop takes the backoff branch instead: it prints the CrashLoopBackOff message and removes `pod-crashy` from `present` *without* re-adding it. From this point on, `pod-crashy` simply stays absent — cycles 5 and 6 don't even attempt to touch it, because `present.contains("pod-crashy")` is now `false`.

**Finally**, the summary print confirms the outcome: the control loop tried three times, then stopped, rather than looping forever — exactly the backoff behavior that keeps a genuinely broken pod from consuming scheduler capacity indefinitely.

```
--- reconcile cycle 1 ---
pod-crashy: unhealthy, recreated (restartCount now 1)
End of cycle 1: present=[pod-stable, pod-crashy], pod-crashy restartCount=1
--- reconcile cycle 2 ---
pod-crashy: unhealthy, recreated (restartCount now 2)
End of cycle 2: present=[pod-stable, pod-crashy], pod-crashy restartCount=2
--- reconcile cycle 3 ---
pod-crashy: unhealthy, recreated (restartCount now 3)
End of cycle 3: present=[pod-stable, pod-crashy], pod-crashy restartCount=3
--- reconcile cycle 4 ---
pod-crashy: restartCount=3 >= 3 -- CrashLoopBackOff, NOT recreating this cycle
End of cycle 4: present=[pod-stable], pod-crashy restartCount=3
--- reconcile cycle 5 ---
End of cycle 5: present=[pod-stable], pod-crashy restartCount=3
--- reconcile cycle 6 ---
End of cycle 6: present=[pod-stable], pod-crashy restartCount=3

Final outcome: the orchestrator stopped recreating pod-crashy after 3 failed restarts, avoiding a reconciliation storm, while pod-stable remained healthy and present throughout.
```

## 7. Gotchas & takeaways

> Reconciliation loops are eventually consistent, not instant. Between the moment actual state diverges from desired state and the moment the next reconcile cycle notices and acts, the system is knowingly "wrong" — designing around this (via health checks, timeouts, and idempotent actions) matters more than trying to make the loop run infinitely fast.

- Kubernetes concepts read as complex mostly because there are many resource *types* — but almost all of them share this same one idea: declare desired state, reconcile continuously, self-heal as a side effect of the loop running forever.
- Backoff on repeated failures isn't optional polish — without it, a single bad deploy can turn into a resource-exhausting recreate storm across the whole cluster, as shown in Level 3.
- Self-healing only works as well as the health signal driving it; a pod that reports healthy while actually broken will never get reconciled away, which is exactly why [health checks for orchestrators](0445-health-checks-for-orchestrators.md) matter so much.
- The building blocks this control loop actually manipulates — Pods, Deployments, Services, Ingress — are covered next in [Pods, Deployments, Services, Ingress](0447-pods-deployments-services-ingress.md).
- Scaling decisions (how many replicas *should* be desired) build on this same reconciliation idea — see [Horizontal Pod Autoscaling](0448-horizontal-pod-autoscaling.md).
