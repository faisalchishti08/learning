---
card: microservices
gi: 435
slug: service-instance-per-container
title: "Service instance per container"
---

## 1. What it is

**Service instance per container** is a deployment pattern where each running instance of a service is packaged and run as exactly one container — a lightweight, isolated process with its own filesystem, its own view of the network, and its own resource limits, but sharing the host operating system's kernel with every other container on that machine. Scale a service from three instances to six, and you run six containers, each independently schedulable, startable, and killable. This is the pattern most modern orchestrators (Kubernetes, ECS, Nomad) are built around, and it's the default assumption behind most cloud-native microservices tooling today.

## 2. Why & when

Container-per-instance became the dominant pattern because it solves several deployment problems at once, cheaply:

- **Consistent, reproducible environments.** A container image bundles the application together with its exact runtime, libraries, and OS-level dependencies — "works on my machine" mostly disappears, because the container that ran on a developer's laptop is bit-for-bit the same one that runs in production.
- **Fast start and stop.** Containers start in seconds (sometimes less), because there's no OS to boot — only a process to launch inside an already-running kernel. This makes rapid scaling, fast rollbacks, and quick restarts practical in a way that booting a full VM per instance is not.
- **Resource isolation without a full VM's overhead.** Container runtimes enforce CPU and memory limits via the host kernel's cgroups, giving most of the noisy-neighbor protection discussed in [service-per-host vs multiple-services-per-host](0434-service-per-host-vs-multiple-services-per-host.md) without needing a dedicated machine per instance.
- **A natural unit for orchestration.** Schedulers like Kubernetes treat a container (wrapped in a pod) as the atomic thing they place, scale, health-check, and replace — the whole ecosystem of rolling deployments, autoscaling, and self-healing assumes this granularity.

You reach for this pattern by default for any stateless or mostly-stateless service in a modern deployment pipeline. It's less of an active choice today and more of a baseline — the interesting decisions are what you put *inside* the container (see [container image building](0438-container-image-building.md) and [layered & minimal images](0439-layered-minimal-images.md)) and how many instances you run, not whether to containerize at all.

## 3. Core concept

Think of a container like a shipping container in the literal, physical sense the metaphor is named after: the crate has a standard shape, so it can be loaded onto any ship, train, or truck that knows how to handle standard crates — nobody on the dock needs to know or care whether the crate holds furniture or electronics. A service packaged as a container image is the same idea: any container runtime that speaks the standard image format can run it, without needing to know it's a Spring Boot app versus a Node.js app versus anything else. The orchestrator's job is just to move crates (containers) onto ships (hosts) efficiently and replace a damaged crate with a fresh one when needed.

Concretely, "service instance per container" means:

1. **One container = one running instance.** If a service needs to handle more traffic, you don't make the container bigger — you run more containers (horizontal scaling), each identical, each independently replaceable.
2. **The image is immutable; only the running container is transient.** The container image (built once, see [container image building](0438-container-image-building.md)) doesn't change while a container from it is running — see [immutable infrastructure](0437-immutable-infrastructure.md). If something's wrong, you don't patch the running container; you build a new image and replace the container.
3. **The orchestrator owns the container's lifecycle**, not the application. Kubernetes (or similar) decides which host runs which container, restarts a crashed one, and replaces one during a rolling deployment — the application inside just needs to start fast, shut down gracefully (see [graceful startup & shutdown](0444-graceful-startup-shutdown.md)), and expose health signals (see [health checks for orchestrators](0445-health-checks-for-orchestrators.md)) so the orchestrator can make good decisions about it.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single container image is used to run multiple independent container instances of a service, each isolated but sharing the host kernel, with an orchestrator managing how many run and where">
  <rect x="20" y="30" width="130" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="85" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="85" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">image:1.4.0</text>

  <line x1="150" y1="60" x2="220" y2="60" stroke="#79c0ff" stroke-width="2"/>
  <text x="185" y="50" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">runs as</text>

  <rect x="220" y="20" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="265" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">container 1</text>
  <text x="265" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Host X</text>

  <rect x="220" y="80" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="265" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">container 2</text>
  <text x="265" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Host X</text>

  <rect x="220" y="140" width="90" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="265" y="162" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">container 3</text>
  <text x="265" y="177" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Host Y</text>

  <rect x="360" y="60" width="180" height="90" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="450" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Orchestrator</text>
  <text x="450" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">decides count &amp; placement</text>
  <text x="450" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">restarts crashed containers</text>
  <text x="450" y="139" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">replaces during rollout</text>

  <line x1="310" y1="45" x2="360" y2="90" stroke="#f0883e" stroke-dasharray="3,2"/>
  <line x1="310" y1="105" x2="360" y2="100" stroke="#f0883e" stroke-dasharray="3,2"/>
  <line x1="310" y1="165" x2="360" y2="115" stroke="#f0883e" stroke-dasharray="3,2"/>

  <text x="320" y="215" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">one image, many disposable instances, orchestrator manages the fleet</text>
</svg>

One immutable image produces many independent container instances; the orchestrator decides how many run and where.

## 5. Runnable example

Scenario: an `order-service` that needs to scale under load. We model a fleet of containers spun up from one image, first with basic start/stop lifecycle, then adding per-container resource limits and independent crash/restart behavior, then handling a production-flavored rolling scale-up that must respect a max-unavailable constraint while replacing old-image containers with new ones.

### Level 1 — Basic

```java
// File: ContainerFleetBasic.java -- models the CORE idea: one image,
// many independently created/destroyed container instances.
import java.util.*;

public class ContainerFleetBasic {
    record ContainerImage(String name, String version) {}

    static class Container {
        final String id;
        final ContainerImage image;
        boolean running = false;

        Container(String id, ContainerImage image) { this.id = id; this.image = image; }
        void start() { running = true; System.out.println("[" + id + "] started from " + image.name() + ":" + image.version()); }
        void stop()  { running = false; System.out.println("[" + id + "] stopped"); }
    }

    public static void main(String[] args) {
        ContainerImage image = new ContainerImage("order-service", "1.4.0");
        List<Container> fleet = new ArrayList<>();
        for (int i = 1; i <= 3; i++) {
            Container c = new Container("order-service-" + i, image);
            c.start();
            fleet.add(c);
        }
        System.out.println("Fleet size: " + fleet.size() + ", all from the SAME image " + image.name() + ":" + image.version());
        fleet.get(1).stop(); // one instance goes away; the others are unaffected
        System.out.println("Instance 2 stopped independently; instances 1 and 3 keep running.");
    }
}
```

How to run: `java ContainerFleetBasic.java`

`ContainerImage` is the immutable blueprint; `Container` is a running instance created from it. Three containers are started from the same image, each with its own identity (`id`) but identical code and configuration. Stopping one (`fleet.get(1)`) has no effect on the others — each container's lifecycle is fully independent, which is the property that makes horizontal scaling and rolling restarts possible without downtime.

### Level 2 — Intermediate

```java
// File: ContainerFleetWithLimitsAndCrashes.java -- the SAME fleet idea, now
// with per-container resource limits and independent crash/restart handling,
// so one misbehaving container can't take down its siblings.
import java.util.*;

public class ContainerFleetWithLimitsAndCrashes {
    record ContainerImage(String name, String version) {}

    static class Container {
        final String id;
        final ContainerImage image;
        final int memoryLimitMb;
        boolean running = false;
        int memoryUsedMb = 0;

        Container(String id, ContainerImage image, int memoryLimitMb) {
            this.id = id; this.image = image; this.memoryLimitMb = memoryLimitMb;
        }

        void start() { running = true; memoryUsedMb = 0; System.out.println("[" + id + "] started, memory limit=" + memoryLimitMb + "Mi"); }

        // Simulates the container's process trying to allocate more memory;
        // the runtime enforces the limit by killing the container (OOMKilled).
        void allocate(int mb) {
            memoryUsedMb += mb;
            if (memoryUsedMb > memoryLimitMb) {
                System.out.println("[" + id + "] OOMKilled: used " + memoryUsedMb + "Mi > limit " + memoryLimitMb + "Mi");
                running = false;
            } else {
                System.out.println("[" + id + "] allocated " + mb + "Mi, total=" + memoryUsedMb + "Mi (ok)");
            }
        }
    }

    public static void main(String[] args) {
        ContainerImage image = new ContainerImage("order-service", "1.4.0");
        List<Container> fleet = new ArrayList<>();
        for (int i = 1; i <= 3; i++) {
            Container c = new Container("order-service-" + i, image, 256);
            c.start();
            fleet.add(c);
        }

        fleet.get(0).allocate(120);
        fleet.get(1).allocate(120);
        // Instance 3 has a leak and keeps allocating until it's killed.
        fleet.get(2).allocate(200);
        fleet.get(2).allocate(100); // pushes it over the 256Mi limit

        long stillRunning = fleet.stream().filter(c -> c.running).count();
        System.out.println("Still running: " + stillRunning + "/3 -- the OOMKilled instance did NOT affect its siblings' memory accounting.");
    }
}
```

How to run: `java ContainerFleetWithLimitsAndCrashes.java`

Each `Container` now carries a `memoryLimitMb` — a stand-in for a real container runtime's memory cgroup limit. `allocate` simulates memory pressure; when usage exceeds the limit, the runtime "OOMKills" the container (sets `running = false`) without touching any other container's state. Instance 3's leak crashes only instance 3 — instances 1 and 2 remain healthy and their `memoryUsedMb` accounting is untouched, demonstrating the isolation that per-container resource limits provide.

### Level 3 — Advanced

```java
// File: RollingScaleUpAdvanced.java -- the SAME fleet, now handling a
// PRODUCTION-FLAVORED hard case: rolling from image v1.4.0 to v1.5.0 while
// scaling the fleet from 3 to 5 instances, respecting a maxUnavailable
// constraint so the service never drops below a minimum healthy count.
import java.util.*;

public class RollingScaleUpAdvanced {
    record ContainerImage(String name, String version) {}

    static class Container {
        final String id;
        final ContainerImage image;
        boolean healthy = false;

        Container(String id, ContainerImage image) { this.id = id; this.image = image; }
        void start() { healthy = true; System.out.println("[" + id + "] running " + image.version() + " (healthy)"); }
        void terminate() { healthy = false; System.out.println("[" + id + "] terminated"); }
    }

    public static void main(String[] args) {
        ContainerImage oldImage = new ContainerImage("order-service", "1.4.0");
        ContainerImage newImage = new ContainerImage("order-service", "1.5.0");

        List<Container> fleet = new ArrayList<>();
        for (int i = 1; i <= 3; i++) {
            Container c = new Container("order-service-" + i, oldImage);
            c.start();
            fleet.add(c);
        }

        int desiredCount = 5;
        int maxUnavailable = 1; // never let more than 1 instance be down at once

        System.out.println("--- rolling update: 1.4.0 -> 1.5.0, scaling 3 -> " + desiredCount + " ---");
        int index = fleet.size() + 1;
        // Replace each old-image container one at a time, respecting maxUnavailable.
        List<Container> toReplace = new ArrayList<>(fleet);
        for (Container old : toReplace) {
            long currentlyHealthy = fleet.stream().filter(c -> c.healthy).count();
            long unavailableBudget = fleet.size() - currentlyHealthy;
            if (unavailableBudget >= maxUnavailable) {
                System.out.println("Skipping replacement this cycle -- unavailable budget exhausted.");
                continue;
            }
            old.terminate();
            fleet.remove(old);
            Container fresh = new Container("order-service-" + (index++), newImage);
            fresh.start();
            fleet.add(fresh);
        }
        // Scale up the remainder with the new image only.
        while (fleet.size() < desiredCount) {
            Container fresh = new Container("order-service-" + (index++), newImage);
            fresh.start();
            fleet.add(fresh);
        }

        long healthyCount = fleet.stream().filter(c -> c.healthy).count();
        long onNewImage = fleet.stream().filter(c -> c.image.version().equals("1.5.0")).count();
        System.out.println("Final fleet size: " + fleet.size() + ", healthy: " + healthyCount + ", on new image: " + onNewImage);
    }
}
```

How to run: `java RollingScaleUpAdvanced.java`

`maxUnavailable` models the safety constraint every real rolling deployment respects: the orchestrator never terminates an old instance before confirming it can immediately replace it, and it never lets more than the configured number of instances be simultaneously unavailable. The loop replaces each old-image container one at a time — never batching terminations — then scales the fleet up to `desiredCount` purely with the new image. This mirrors how Kubernetes `Deployment` rollouts and ECS rolling updates behave: containers are individually disposable, but the *fleet* as a whole maintains continuous availability throughout the transition.

## 6. Walkthrough

Trace `RollingScaleUpAdvanced.main` in order. **First**, three containers running image `1.4.0` are started and added to `fleet`; all are marked `healthy`.

**Next**, the rollout loop iterates over a snapshot of the original three containers (`toReplace`). For the first one, `currentlyHealthy` is `3` and `fleet.size()` is `3`, so `unavailableBudget` is `0` — below `maxUnavailable` (`1`), so replacement proceeds: the old container is terminated and removed, and a fresh container running `1.5.0` (`order-service-4`) is started and added. Fleet size stays at `3`, now with one `1.5.0` instance and two `1.4.0` instances.

**Then**, the same check runs for the second and third original containers. Each time, `currentlyHealthy` equals `fleet.size()` right before the check (because the previous replacement already restored full health), so `unavailableBudget` is `0` and replacement proceeds each time. By the end of this loop, all three original containers have been replaced one at a time, and the fleet holds three `1.5.0` containers (`order-service-4`, `-5`, `-6`).

**Finally**, the `while` loop scales the fleet from `3` up to the `desiredCount` of `5` by starting two more `1.5.0` containers directly (`order-service-7`, `-8`) — no replacement needed here, just growth. The final print confirms `fleet.size() == 5`, `healthyCount == 5`, and `onNewImage == 5`: every instance is healthy and running the new version, and at no point during the whole process did more than one instance become unavailable at once.

```
--- rolling update: 1.4.0 -> 1.5.0, scaling 3 -> 5 ---
[order-service-1] terminated
[order-service-4] running 1.5.0 (healthy)
[order-service-2] terminated
[order-service-5] running 1.5.0 (healthy)
[order-service-3] terminated
[order-service-6] running 1.5.0 (healthy)
[order-service-7] running 1.5.0 (healthy)
[order-service-8] running 1.5.0 (healthy)
Final fleet size: 5, healthy: 5, on new image: 5
```

## 7. Gotchas & takeaways

> Containers share the host kernel, which means container isolation is weaker than VM isolation: a kernel-level vulnerability or a severe cgroup misconfiguration can, in principle, let one container affect others on the same host in ways a hypervisor boundary would prevent. For most services this tradeoff is well worth the speed and density gains, but workloads with strict multi-tenant security requirements sometimes still need [service instance per VM](0436-service-instance-per-vm.md) or a gVisor/Kata-style sandboxed runtime instead.

- One container should run one service instance and, ideally, one primary process — packing multiple unrelated services into a single container reintroduces the noisy-neighbor and blast-radius problems containers exist to solve.
- Treat the running container as disposable and the image as the source of truth — never patch a running container in place; rebuild the image and replace the container, per [immutable infrastructure](0437-immutable-infrastructure.md).
- Resource limits (CPU, memory) on each container are what make dense multiple-services-per-host packing (see [service-per-host vs multiple-services-per-host](0434-service-per-host-vs-multiple-services-per-host.md)) safe — a container without limits can still starve its neighbors even though it's "isolated."
- For the orchestrator to make good rollout, restart, and scaling decisions, the application inside the container needs to start quickly, shut down gracefully, and expose accurate health signals — see [graceful startup & shutdown](0444-graceful-startup-shutdown.md) and [health checks for orchestrators](0445-health-checks-for-orchestrators.md).
- Smaller, well-layered images start faster and reduce the attack surface pulled into each container — see [layered & minimal images](0439-layered-minimal-images.md).
