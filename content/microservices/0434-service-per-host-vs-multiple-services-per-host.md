---
card: microservices
gi: 434
slug: service-per-host-vs-multiple-services-per-host
title: "Service-per-host vs multiple-services-per-host"
---

## 1. What it is

**Service-per-host** deploys exactly one service instance on each physical or virtual machine — that host runs nothing else. **Multiple-services-per-host** packs several unrelated service instances onto the same machine, sharing its CPU, memory, and disk. "Host" here means whatever unit of compute you're deploying onto: a bare-metal server, a virtual machine, or — as containers made cheap and common — a single container runtime instance. The choice between the two is really a choice about **isolation versus density**: how much do you want one service's problems to be able to leak into another's, versus how much idle capacity are you willing to pay for to prevent that?

## 2. Why & when

This decision shapes almost every other operational property of your system, so it's worth making deliberately rather than by default:

- **Noisy-neighbor risk.** On a shared host, one service with a memory leak or a runaway batch job can starve every other service on that machine of CPU or RAM — even though those services have nothing to do with each other. Service-per-host eliminates this by construction.
- **Resource utilization.** A host running one lightly-loaded service wastes most of its capacity. Multiple-services-per-host lets you bin-pack many services onto fewer machines, which is why container orchestrators exist — they automate safe, dense packing so you get isolation-like guarantees without the cost of one-service-one-host.
- **Blast radius of a host failure.** If a host with 20 services dies, 20 services go down at once. If a host runs one service, only that service is affected — but you now need 20 hosts instead of one.
- **Operational simplicity vs cost.** Service-per-host is the simplest mental model (and was the default before containers existed, when a "host" usually meant an actual VM). Multiple-services-per-host is cheaper at scale but requires something — a scheduler, resource limits, cgroups — to keep services from interfering with each other.

You face this decision at every layer: choosing VM sizing for a fleet of services, choosing whether to run multiple containers per VM node in a Kubernetes cluster, or choosing whether a background batch job shares a host with a latency-sensitive API. Cloud economics have pushed most teams toward multiple-services-per-host (packed via containers) as the default, reserving dedicated hosts for services with unusual resource, compliance, or noisy-neighbor sensitivity.

## 3. Core concept

Think of it like renting office space. Service-per-host is renting a whole building for one team: nobody else's fire drill, loud phone calls, or overloaded elevator ever affects you, but you're paying for empty floors most of the day. Multiple-services-per-host is an open-plan shared office: far cheaper per desk, but if the team next to you throws a loud party (consumes all the shared bandwidth or CPU) or leaves the printer jammed (fills shared disk), everyone nearby feels it — unless the building has rules (resource quotas, dedicated zones) that keep one team's activity from spilling into another's space.

The two axes that actually determine the tradeoff are:

1. **Isolation** — do host-level resource limits (CPU shares, memory limits, I/O quotas) exist and get enforced? Without them, "multiple services per host" degrades into "any service can starve any other."
2. **Packing efficiency** — how much idle capacity is acceptable? A host running one service at 5% average CPU utilization is safe but wasteful; a host running eight services scheduled so their peaks don't all coincide can run near capacity.

Containers reshaped this decision because they make **service instance per container** (see [service instance per container](0435-service-instance-per-container.md)) cheap and standard: you get most of the isolation benefits of separate hosts (separate filesystem, separate process namespace, enforceable CPU/memory limits) while an orchestrator still packs many containers densely onto each underlying host. That's why "multiple services per (physical) host" today usually really means "multiple *containers*, each with its own service, packed onto shared VM nodes" rather than services literally sharing a single OS process space unguarded.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Service-per-host isolates each service on its own machine at the cost of idle capacity; multiple-services-per-host packs several services onto one machine, saving cost but risking noisy-neighbor interference unless resource limits are enforced">
  <text x="150" y="24" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Service-per-host</text>
  <rect x="40" y="40" width="100" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Order</text>
  <text x="90" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Host A</text>

  <rect x="160" y="40" width="100" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="210" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Payment</text>
  <text x="210" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Host B</text>
  <text x="150" y="155" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">clean isolation, low utilization</text>

  <text x="480" y="24" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Multiple-services-per-host</text>
  <rect x="380" y="40" width="220" height="100" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <rect x="392" y="52" width="60" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="422" y="73" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order</text>
  <rect x="462" y="52" width="60" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="492" y="73" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Payment</text>
  <rect x="532" y="52" width="55" height="34" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="559" y="73" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Batch</text>
  <text x="559" y="98" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">runaway job!</text>
  <text x="490" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Host C (shared)</text>
  <text x="490" y="155" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">high utilization, needs limits</text>

  <text x="320" y="200" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">containers give most of the left side's isolation</text>
  <text x="320" y="216" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">while an orchestrator packs like the right side</text>
</svg>

Service-per-host trades utilization for isolation; multiple-services-per-host trades isolation for utilization unless resource limits fill the gap.

## 5. Runnable example

Scenario: a small platform team is capacity-planning three services (`order`, `payment`, `batch-reporting`) across hosts. We model host placement first without any resource accounting, then add CPU/memory accounting to reveal noisy-neighbor risk, then add enforced per-service limits (the containers-style fix) as the production-flavored resolution.

### Level 1 — Basic

```java
// File: HostPlacementBasic.java -- models the two placement STRATEGIES with
// no resource accounting yet: one service per host vs many per host.
import java.util.*;

public class HostPlacementBasic {
    record ServiceInstance(String name) {}
    record Host(String id, List<String> services) {}

    static List<Host> servicePerHost(List<ServiceInstance> services) {
        List<Host> hosts = new ArrayList<>();
        int i = 0;
        for (ServiceInstance s : services) {
            hosts.add(new Host("host-" + (i++), List.of(s.name())));
        }
        return hosts;
    }

    static List<Host> multipleServicesPerHost(List<ServiceInstance> services, int perHost) {
        List<Host> hosts = new ArrayList<>();
        List<String> bucket = new ArrayList<>();
        int hostIdx = 0;
        for (ServiceInstance s : services) {
            bucket.add(s.name());
            if (bucket.size() == perHost) {
                hosts.add(new Host("host-" + (hostIdx++), List.copyOf(bucket)));
                bucket.clear();
            }
        }
        if (!bucket.isEmpty()) hosts.add(new Host("host-" + (hostIdx++), List.copyOf(bucket)));
        return hosts;
    }

    public static void main(String[] args) {
        List<ServiceInstance> services = List.of(
                new ServiceInstance("order"), new ServiceInstance("payment"), new ServiceInstance("batch-reporting"));

        System.out.println("--- service-per-host ---");
        for (Host h : servicePerHost(services)) System.out.println(h.id() + " runs " + h.services());

        System.out.println("--- multiple-services-per-host (2 per host) ---");
        for (Host h : multipleServicesPerHost(services, 2)) System.out.println(h.id() + " runs " + h.services());
    }
}
```

How to run: `java HostPlacementBasic.java`

`servicePerHost` always allocates a fresh host per service, so three services need three hosts. `multipleServicesPerHost` packs services into hosts up to `perHost` capacity, so the same three services fit on two hosts. Neither strategy yet accounts for how much CPU or memory each service actually needs — that's the missing piece the next level adds.

### Level 2 — Intermediate

```java
// File: HostPlacementWithResourceAccounting.java -- the SAME two strategies,
// now tracking CPU/memory usage per service to reveal the noisy-neighbor
// risk that multiple-services-per-host introduces without limits.
import java.util.*;

public class HostPlacementWithResourceAccounting {
    record ServiceInstance(String name, int cpuPercentNormal, int cpuPercentPeak) {}

    static class Host {
        final String id;
        final List<ServiceInstance> services = new ArrayList<>();
        final int cpuCapacityPercent;
        Host(String id, int cpuCapacityPercent) { this.id = id; this.cpuCapacityPercent = cpuCapacityPercent; }

        int totalPeakDemand() {
            return services.stream().mapToInt(ServiceInstance::cpuPercentPeak).sum();
        }
        boolean isOverCommittedAtPeak() { return totalPeakDemand() > cpuCapacityPercent; }
    }

    public static void main(String[] args) {
        ServiceInstance order = new ServiceInstance("order", 10, 20);
        ServiceInstance payment = new ServiceInstance("payment", 8, 15);
        // batch-reporting is normally quiet but can spike hard during a nightly run.
        ServiceInstance batch = new ServiceInstance("batch-reporting", 5, 95);

        Host shared = new Host("host-shared", 100);
        shared.services.addAll(List.of(order, payment, batch));

        System.out.println("Shared host normal-load total demand: "
                + (order.cpuPercentNormal() + payment.cpuPercentNormal() + batch.cpuPercentNormal()) + "% -- looks fine");
        System.out.println("Shared host PEAK total demand: " + shared.totalPeakDemand() + "%");
        System.out.println("Over-committed at peak? " + shared.isOverCommittedAtPeak()
                + " -- when batch-reporting spikes, order & payment starve for CPU too, even though they didn't change.");
    }
}
```

How to run: `java HostPlacementWithResourceAccounting.java`

Each `ServiceInstance` now has a normal and a peak CPU demand. Under normal load, three services sharing one 100%-capacity host look comfortably packed (23% total). But `batch-reporting`'s nightly spike to 95% pushes the shared host's peak demand to 130% of its capacity — `isOverCommittedAtPeak` returns `true`. Because nothing separates the services' resource pools, `order` and `payment`, which did nothing wrong, get starved by their noisy neighbor. This is the concrete failure mode "multiple-services-per-host" warns about when isolation isn't enforced.

### Level 3 — Advanced

```java
// File: HostPlacementWithEnforcedLimits.java -- the SAME three services and
// the SAME shared host, now handling the PRODUCTION-FLAVORED fix: each
// service gets an enforced CPU limit (the containers-style resolution), so
// a noisy neighbor is capped rather than allowed to starve everyone else.
import java.util.*;

public class HostPlacementWithEnforcedLimits {
    record ServiceInstance(String name, int cpuPercentPeak, int cpuLimitPercent) {
        // Enforced usage is capped at the limit, no matter how much the
        // service actually wants -- this is what a container CPU quota does.
        int enforcedUsage() { return Math.min(cpuPercentPeak, cpuLimitPercent); }
        boolean isThrottled() { return cpuPercentPeak > cpuLimitPercent; }
    }

    public static void main(String[] args) {
        ServiceInstance order = new ServiceInstance("order", 20, 30);
        ServiceInstance payment = new ServiceInstance("payment", 15, 30);
        // Same spiky batch job, but now capped at a 25% CPU quota -- it can
        // still run, it just can't run AS FAST during its spike.
        ServiceInstance batch = new ServiceInstance("batch-reporting", 95, 25);

        List<ServiceInstance> onHost = List.of(order, payment, batch);
        int totalEnforced = onHost.stream().mapToInt(ServiceInstance::enforcedUsage).sum();

        System.out.println("Per-service enforced usage at peak:");
        for (ServiceInstance s : onHost) {
            System.out.printf("  %-16s wants=%3d%% limit=%3d%% enforced=%3d%% throttled=%s%n",
                    s.name(), s.cpuPercentPeak(), s.cpuLimitPercent(), s.enforcedUsage(), s.isThrottled());
        }
        System.out.println("Total enforced usage on host: " + totalEnforced + "% (capacity=100%)");
        System.out.println("Host over-committed? " + (totalEnforced > 100)
                + " -- batch-reporting is throttled instead of starving order/payment, so the shared host stays stable.");
    }
}
```

How to run: `java HostPlacementWithEnforcedLimits.java`

Each service now carries a `cpuLimitPercent` — a stand-in for a real container's CPU quota (a `cgroup` limit under Docker, or a Kubernetes `resources.limits.cpu`). `enforcedUsage` clamps actual usage to that limit regardless of demand, and `isThrottled` reports when a service wanted more than it was allowed. `batch-reporting`'s peak demand of 95% is capped to its 25% limit — it runs slower during its spike, but it no longer eats into `order` and `payment`'s share. This is the concrete mechanism that makes "multiple services per host" safe: not avoiding sharing, but bounding each tenant's consumption of the shared resource.

## 6. Walkthrough

Trace `HostPlacementWithEnforcedLimits.main` in order. **First**, three `ServiceInstance` records are created, each with a real peak CPU demand and an enforced limit: `order` (wants 20%, capped at 30% — never throttled), `payment` (wants 15%, capped at 30% — never throttled), and `batch-reporting` (wants 95%, capped at 25% — heavily throttled).

**Next**, the loop over `onHost` prints each service's `enforcedUsage()`. For `order`, `Math.min(20, 30)` is `20` — its limit never binds, so it runs at full demand. For `payment`, `Math.min(15, 30)` is `15` — same story. For `batch-reporting`, `Math.min(95, 25)` is `25` — the limit binds hard, and `isThrottled()` returns `true` because `95 > 25`.

**Then**, `totalEnforced` sums the three enforced values: `20 + 15 + 25 = 60`. This is well under the host's 100% capacity.

**Finally**, the program prints whether the host is over-committed: `60 > 100` is `false`. Compare this to Level 2, where the same three services' *unenforced* peak demand summed to 130% and blew past capacity — the only thing that changed between the two runs is that Level 3 clamps each service to a quota before summing, which is exactly what a container's resource limits do at the OS level.

```
Per-service enforced usage at peak:
  order            wants= 20% limit= 30% enforced= 20% throttled=false
  payment          wants= 15% limit= 30% enforced= 15% throttled=false
  batch-reporting  wants= 95% limit= 25% enforced= 25% throttled=true
Total enforced usage on host: 60% (capacity=100%)
Host over-committed? false -- batch-reporting is throttled instead of starving order/payment, so the shared host stays stable.
```

## 7. Gotchas & takeaways

> Sizing resource limits is itself a tradeoff, not a free safety net: set a limit too low and you throttle a service that legitimately needs the CPU (turning a noisy-neighbor problem into a self-inflicted slowdown), set it too high and multiple generous limits on one host can still collectively exceed real capacity — limits stop unbounded starvation, they don't guarantee every service gets all the resources it wants.

- Service-per-host gives the strongest isolation with the simplest mental model, but it's the most expensive option per unit of actual work performed, since most services don't use 100% of a dedicated host around the clock.
- Multiple-services-per-host is only safe with enforced resource limits — without them, one noisy or misbehaving service can silently degrade every other service sharing its host.
- Containers turned this from an all-or-nothing host decision into a per-service configuration knob: see [service instance per container](0435-service-instance-per-container.md) for how packaging a service instance as a container gets you host-like isolation while still allowing an orchestrator to pack many containers per physical machine.
- Compare against [service instance per VM](0436-service-instance-per-vm.md), which sits between the two extremes — VM-level isolation is stronger than container-level, but far heavier and slower to provision than a container.
- Whichever strategy you pick, [immutable infrastructure](0437-immutable-infrastructure.md) practices (never patching a live host in place) apply equally — the placement strategy answers "how many services share a host," not "how do we change what's running on it."
