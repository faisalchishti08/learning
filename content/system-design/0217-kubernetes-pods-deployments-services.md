---
card: system-design
gi: 217
slug: kubernetes-pods-deployments-services
title: Kubernetes (pods, deployments, services)
---

## 1. What it is

**Kubernetes** is a system that runs and manages [containers](0216-containers-images.md) across a cluster of machines. A **pod** is the smallest deployable unit — one or more tightly coupled containers that always run together on the same machine. A **deployment** manages a set of identical pods, keeping the desired number running and handling rolling updates. A **service** gives a stable network address to a group of pods, even as individual pods are created and destroyed underneath it.

## 2. Why & when

Running containers directly on individual machines means you must manually decide which machine runs which container, restart containers that crash, and update your own tracking of which machine currently has a healthy copy of each service — none of which scales past a handful of containers. Kubernetes automates all of it: you declare what you want ("run 5 copies of this container, spread across machines"), and Kubernetes continuously works to keep that true, restarting failed pods and rescheduling them onto healthy machines automatically.

Use Kubernetes once you are running enough containers, across enough machines, that manually tracking placement and health becomes impractical — a common threshold for teams running real [microservices](0196-microservices.md) at scale. For a single service or a small number of containers, simpler tools (a managed container platform, or even direct container hosting) may be enough, and Kubernetes' own operational complexity is a real cost to weigh against the automation it buys you.

## 3. Core concept

- **Pod.** One or more containers that share networking (the same IP address) and storage, always scheduled onto the same machine, and always created or destroyed together. Most pods run exactly one container; a second container in the same pod is usually a helper (a "sidecar") that supports the main one.
- **Deployment.** Declares the desired state — "run 5 replicas of this pod spec." Kubernetes' **control loop** continuously compares the actual state (how many healthy pods exist right now) against this desired state, and creates or removes pods to close any gap.
- **Rolling update.** When a deployment's pod spec changes (a new image version), Kubernetes replaces old pods with new ones gradually — a few at a time — rather than all at once, so the service keeps running throughout the update with no downtime.
- **Service.** Pods are ephemeral — they get a new IP address every time they are recreated. A service gives a group of pods (selected by a label) one stable virtual IP and DNS name; traffic to the service is load-balanced across whichever pods currently match that label, so nothing else in the cluster needs to track individual pod IPs.
- **Labels and selectors.** A deployment tags its pods with labels (e.g. `app: orders`); a service selects pods by matching those labels (`selector: app: orders`). This label-based matching, not a hardcoded list of pod names, is what lets the service keep working automatically as pods are replaced.

## 4. Diagram

```
                        +-----------------+
   Client traffic ----->|    Service        |
                        |  orders-service    |
                        |  (stable virtual IP)|
                        +---------+---------+
                                  |  selector: app=orders
                     load-balances across matching pods
                                  |
         +-------------------------+-------------------------+
         v                         v                         v
   +-----------+             +-----------+             +-----------+
   | Pod        |             | Pod        |             | Pod        |
   | app=orders |             | app=orders |             | app=orders |
   | (container)|             | (container)|             | (container)|
   +-----------+             +-----------+             +-----------+
         ^                         ^                         ^
         |                         |                         |
   +-------------------------------------------------------------+
   |                      Deployment: orders-deployment              |
   |   desired replicas: 3    control loop keeps actual = desired    |
   +-------------------------------------------------------------+

   If a pod crashes, the deployment's control loop notices actual < desired
   and creates a REPLACEMENT pod - the service automatically includes it,
   because it matches the same label, with no manual reconfiguration.
```
*Caption: the service is the stable address clients depend on; the deployment is what keeps the right number of healthy pods running behind it, replacing failures automatically.*

## 5. Runnable example

This models the deployment's control loop and the service's label-based routing — the core mechanics Kubernetes implements — since a real cluster is not something a single file can run.

**Level 1 — Basic.** A deployment's control loop: observe actual pod count, create pods until it matches the desired count.

**Level 2 — Intermediate.** A service routes traffic to whichever pods currently match its label selector, and correctly excludes an unhealthy pod.

**Level 3 — Advanced.** A rolling update: replace old-version pods with new-version pods a few at a time, keeping enough healthy pods available throughout.

```java
// KubernetesDemo.java
import java.util.*;

public class KubernetesDemo {

    record Pod(String id, String label, String imageVersion, boolean healthy) {}

    // ---------- Level 1: deployment control loop ----------
    static class Deployment {
        String label;
        int desiredReplicas;
        List<Pod> pods = new ArrayList<>();
        int nextPodId = 1;
        String imageVersion;

        Deployment(String label, int desiredReplicas, String imageVersion) {
            this.label = label; this.desiredReplicas = desiredReplicas; this.imageVersion = imageVersion;
        }

        void reconcile() {
            long actualHealthy = pods.stream().filter(Pod::healthy).count();
            while (actualHealthy < desiredReplicas) {
                Pod newPod = new Pod("pod-" + (nextPodId++), label, imageVersion, true);
                pods.add(newPod);
                actualHealthy++;
                System.out.println("    [control loop] actual < desired, created " + newPod.id());
            }
        }

        void crashPod(String podId) {
            pods.removeIf(p -> p.id().equals(podId));
            System.out.println("    " + podId + " crashed and was removed");
        }
    }

    // ---------- Level 2: service routes by label, skipping unhealthy pods ----------
    static class Service {
        String selectorLabel;
        List<Pod> route(List<Pod> allPods) {
            return allPods.stream().filter(p -> p.label().equals(selectorLabel) && p.healthy()).toList();
        }
        Service(String selectorLabel) { this.selectorLabel = selectorLabel; }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - deployment control loop creates pods to match desired replicas:");
        Deployment deployment = new Deployment("app=orders", 3, "v1.0");
        deployment.reconcile();
        System.out.println("  pods now: " + deployment.pods.stream().map(Pod::id).toList());

        System.out.println("\n  a pod crashes:");
        deployment.crashPod("pod-2");
        System.out.println("  control loop notices actual (2) < desired (3), reconciles:");
        deployment.reconcile();
        System.out.println("  pods now: " + deployment.pods.stream().map(Pod::id).toList());

        System.out.println("\nLevel 2 - service routes only to healthy pods matching its label:");
        Service ordersService = new Service("app=orders");
        // Mark one pod unhealthy without removing it (simulates a failing health check).
        deployment.pods.set(0, new Pod(deployment.pods.get(0).id(), "app=orders", "v1.0", false));
        List<Pod> routable = ordersService.route(deployment.pods);
        System.out.println("  all pods: " + deployment.pods);
        System.out.println("  service routes traffic only to: " + routable.stream().map(Pod::id).toList());

        System.out.println("\nLevel 3 - rolling update: replace v1.0 pods with v2.0, a few at a time:");
        Deployment rollingDeployment = new Deployment("app=orders", 4, "v1.0");
        rollingDeployment.reconcile();
        System.out.println("  before update: " + summarize(rollingDeployment.pods));
        rollingUpdate(rollingDeployment, "v2.0", 2); // max 2 old pods replaced at a time
    }

    static String summarize(List<Pod> pods) {
        Map<String, Long> byVersion = new TreeMap<>();
        for (Pod p : pods) byVersion.merge(p.imageVersion(), 1L, Long::sum);
        return byVersion.toString();
    }

    static void rollingUpdate(Deployment deployment, String newVersion, int maxUnavailable) {
        List<Pod> oldPods = new ArrayList<>(deployment.pods.stream().filter(p -> !p.imageVersion().equals(newVersion)).toList());
        while (!oldPods.isEmpty()) {
            int batchSize = Math.min(maxUnavailable, oldPods.size());
            for (int i = 0; i < batchSize; i++) {
                Pod old = oldPods.remove(0);
                deployment.pods.remove(old);
                Pod replacement = new Pod("pod-" + (deployment.nextPodId++), deployment.label, newVersion, true);
                deployment.pods.add(replacement);
            }
            System.out.println("  after batch: " + summarize(deployment.pods) +
                "  (never fewer than " + (deployment.desiredReplicas - maxUnavailable) + " pods available)");
        }
    }
}
```

**How to run:** `java KubernetesDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `deployment.reconcile()` is called with zero existing pods and `desiredReplicas = 3`. The `while (actualHealthy < desiredReplicas)` loop runs three times, creating `pod-1`, `pod-2`, `pod-3` — this is the control loop closing the gap between actual (0) and desired (3).
2. `deployment.crashPod("pod-2")` removes that pod from the list, dropping the actual healthy count to 2. Calling `reconcile()` again immediately detects `actualHealthy (2) < desiredReplicas (3)` and creates one new pod (`pod-4`) — the deployment never needed to be told a pod crashed; it simply re-evaluated the gap and closed it, which is how Kubernetes self-heals in practice.
3. **Level 2:** one pod is replaced with an otherwise-identical copy that has `healthy = false`, simulating a failed health check without actually removing the pod (a real cluster keeps a failing pod around briefly for diagnostics before removing it). `ordersService.route(deployment.pods)` filters by both the label match **and** `healthy()` — the unhealthy pod is excluded from the returned list even though it still exists and still carries the matching label.
4. This is the mechanism that keeps a service from routing traffic to a broken pod: the selector alone is not enough, health also gates whether a pod receives traffic.
5. **Level 3:** `rollingUpdate` builds a list of pods still running the old version and processes them in batches of `maxUnavailable = 2` at a time. Each iteration removes up to 2 old-version pods and adds the same number of new-version pods, then prints a version-count summary. The comment on each printed line notes the desired replica count minus `maxUnavailable` is always available — because at most 2 of the 4 total pods are ever mid-replacement at once, at least 2 pods are always serving traffic throughout the whole update, which is exactly what makes a rolling update avoid downtime.

## 7. Gotchas & takeaways

> **Gotcha:** a deployment's control loop only checks pod *existence and basic health*, not whether the pod is actually able to serve traffic correctly (e.g. it started but its dependencies are not ready yet). Configure real readiness and liveness health checks — without them, a service can route traffic to a pod that is technically "running" but not actually able to handle a request.

- Design pods around one main container plus, if needed, tightly coupled sidecars only — a pod is the unit that scales, restarts, and gets scheduled together, so unrelated processes should be separate pods, not squeezed into one.
- Trust the deployment's control loop to self-heal crashed pods automatically — this is the core value Kubernetes provides over manually managing containers, as shown directly in Level 1.
- Services decouple "what address do I call" from "which specific pods are currently running" — nothing in the rest of the system needs to track individual pod IPs, only the stable service name.
- Rolling updates, combined with a low `maxUnavailable`, give you zero-downtime deployments by default — this pairs naturally with the [blue-green](0218-blue-green-deployment.md) and [canary release](0219-canary-release-feature-flags.md) strategies for even finer control over rollout risk.
