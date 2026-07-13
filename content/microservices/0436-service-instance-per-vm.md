---
card: microservices
gi: 436
slug: service-instance-per-vm
title: "Service instance per VM"
---

## 1. What it is

**Service instance per VM** is a deployment pattern where each running instance of a service gets its own full virtual machine — a complete, isolated operating system with its own kernel, running on top of a hypervisor that carves up physical hardware. This was the standard deployment unit before containers became widespread, and cloud tools like AWS EC2 Auto Scaling Groups, Azure VM Scale Sets, and machine images (AMIs) were all built around it. Scale a service from three instances to six, and you provision three more full VMs, each booting its own kernel, its own network stack, and its own copy of the application.

## 2. Why & when

VM-per-instance still earns its place in modern architectures, specifically where the isolation containers can't fully provide matters more than the overhead VMs cost:

- **Kernel-level isolation.** A VM has its own kernel, enforced by the hypervisor — a security boundary substantially stronger than a container's shared-kernel, cgroup-based isolation. Multi-tenant platforms, regulated workloads (PCI-DSS, HIPAA), or any scenario where you genuinely cannot trust co-located workloads often require this.
- **Different OS or kernel requirements per service.** If one service needs a specific kernel module, a different OS entirely, or kernel-level tuning that would affect every container sharing that host, a dedicated VM sidesteps the conflict entirely.
- **Legacy or non-containerized workloads.** Some applications were never adapted to run well in a container (odd licensing tied to a machine identity, kernel-dependent drivers) and are more practically run as a VM instance.
- **A stronger blast-radius boundary.** A vulnerability that escapes a container can, in the worst case, reach the host kernel and other containers on it; a VM escape is a categorically harder and rarer attack, because it has to defeat the hypervisor, not just the kernel's namespace/cgroup isolation.

You reach for VM-per-instance today mainly at the edges: as the layer *underneath* a container fleet (cloud Kubernetes nodes are themselves VMs), for workloads with genuine multi-tenant security requirements, or for legacy services not worth containerizing. For most stateless application services, [service instance per container](0435-service-instance-per-container.md) has replaced VM-per-instance as the default, because it delivers most of the isolation at a fraction of the boot time and resource cost.

## 3. Core concept

Picture the difference between renting a detached house and renting an apartment in a shared building. A detached house (a VM) has its own foundation, its own utilities, its own walls down to the studs — nothing about your house depends on your neighbor's house being built or maintained correctly, but building a new house from scratch takes real time. An apartment (a container) shares the building's foundation, plumbing, and structure — moving in is nearly instant, but the building's structural integrity (the shared kernel) is something every tenant depends on collectively.

Concretely, "service instance per VM" means:

1. **Each instance boots a full OS.** The VM includes its own kernel, its own init system, its own network interfaces — this is why VM boot times are measured in tens of seconds to minutes, versus a container's sub-second-to-few-seconds start.
2. **A machine image is the reusable artifact**, analogous to a container image but heavier: an AMI, a VM template, or a golden image bundles the OS, runtime, and application together, so a new instance is a clone of a known-good image rather than a machine configured by hand.
3. **The hypervisor, not a container runtime, enforces isolation.** CPU, memory, and I/O are partitioned by the hypervisor across VMs on the same physical host, and a compromise inside one VM has to break out of that hypervisor boundary to affect another VM — a much higher bar than breaking out of a container's namespace.
4. **Scaling means provisioning new machines, not just new processes.** An Auto Scaling Group launching a new EC2 instance from an AMI is doing the VM-era equivalent of what a Kubernetes `Deployment` does when it schedules a new pod — the concept (identical reusable instances that can be created and destroyed on demand) is the same; only the granularity and speed differ.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Physical hardware runs a hypervisor which hosts multiple VMs, each with its own full kernel; each VM runs one service instance, contrasted with containers which share a single kernel on one VM">
  <rect x="20" y="20" width="600" height="20" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="34" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Physical host</text>

  <rect x="20" y="50" width="600" height="20" rx="4" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="64" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Hypervisor</text>

  <rect x="40" y="90" width="160" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">VM 1</text>
  <text x="120" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">own kernel</text>
  <rect x="55" y="140" width="130" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="165" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="120" y="180" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">one instance</text>

  <rect x="240" y="90" width="160" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">VM 2</text>
  <text x="320" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">own kernel</text>
  <rect x="255" y="140" width="130" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="165" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="320" y="180" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">one instance</text>

  <rect x="440" y="90" width="160" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="520" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">VM 3 (for contrast)</text>
  <text x="520" y="124" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one kernel, many containers</text>
  <rect x="450" y="140" width="60" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="161" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">c1</text>
  <rect x="520" y="140" width="60" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="550" y="161" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">c2</text>
  <text x="520" y="195" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">shared kernel, faster start</text>

  <text x="320" y="240" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">VM boundary = hypervisor-enforced; container boundary = shared-kernel, cgroup-enforced</text>
</svg>

Each VM carries its own kernel and boots independently; containers on a single VM share one kernel and start far faster, at a lower isolation bar.

## 5. Runnable example

Scenario: an `order-service` fleet provisioned as VMs from a golden machine image. We model VM provisioning and its boot-time cost first, then add hypervisor-style resource partitioning across VMs on one physical host, then handle a production-flavored case: an Auto-Scaling-Group-style controller that must replace an unhealthy VM instance without violating a minimum-capacity constraint, accounting for realistic VM boot latency.

### Level 1 — Basic

```java
// File: VmProvisioningBasic.java -- models the CORE idea: a machine image
// (golden image) is cloned into full VM instances, each with real boot cost.
import java.util.*;

public class VmProvisioningBasic {
    record MachineImage(String name, String version) {}

    static class VmInstance {
        final String id;
        final MachineImage image;
        boolean running = false;

        VmInstance(String id, MachineImage image) { this.id = id; this.image = image; }

        void boot() {
            // Real VM boot is tens of seconds; we just simulate the STEPS involved.
            System.out.println("[" + id + "] hypervisor allocating CPU/RAM...");
            System.out.println("[" + id + "] kernel booting...");
            System.out.println("[" + id + "] application " + image.name() + ":" + image.version() + " starting...");
            running = true;
            System.out.println("[" + id + "] VM fully up");
        }
    }

    public static void main(String[] args) {
        MachineImage golden = new MachineImage("order-service-ami", "1.4.0");
        List<VmInstance> fleet = new ArrayList<>();
        for (int i = 1; i <= 2; i++) {
            VmInstance vm = new VmInstance("vm-" + i, golden);
            vm.boot();
            fleet.add(vm);
        }
        System.out.println("Fleet size: " + fleet.size() + ", each is a FULL VM cloned from " + golden.name());
    }
}
```

How to run: `java VmProvisioningBasic.java`

`MachineImage` is the golden-image equivalent of a container image, but heavier — it represents an entire bootable OS plus application. `VmInstance.boot()` walks through the stages a real VM goes through: hypervisor resource allocation, kernel boot, then the application itself starting — a multi-stage process that's inherently slower than a container's single-stage process start. Both VMs are cloned from the same image, so they're functionally identical, just as containers from the same image would be.

### Level 2 — Intermediate

```java
// File: VmResourcePartitioningIntermediate.java -- the SAME fleet, now
// showing how the HYPERVISOR partitions physical host resources across VMs,
// a stronger and more static form of isolation than container cgroups.
import java.util.*;

public class VmResourcePartitioningIntermediate {
    record MachineImage(String name, String version) {}

    static class VmInstance {
        final String id;
        final MachineImage image;
        final int allocatedVcpus;
        final int allocatedMemoryMb;

        VmInstance(String id, MachineImage image, int vcpus, int memoryMb) {
            this.id = id; this.image = image; this.allocatedVcpus = vcpus; this.allocatedMemoryMb = memoryMb;
        }
    }

    static class PhysicalHost {
        final int totalVcpus;
        final int totalMemoryMb;
        final List<VmInstance> vms = new ArrayList<>();

        PhysicalHost(int totalVcpus, int totalMemoryMb) { this.totalVcpus = totalVcpus; this.totalMemoryMb = totalMemoryMb; }

        boolean canPlace(VmInstance vm) {
            int usedVcpus = vms.stream().mapToInt(v -> v.allocatedVcpus).sum();
            int usedMemory = vms.stream().mapToInt(v -> v.allocatedMemoryMb).sum();
            return usedVcpus + vm.allocatedVcpus <= totalVcpus && usedMemory + vm.allocatedMemoryMb <= totalMemoryMb;
        }

        void place(VmInstance vm) {
            if (!canPlace(vm)) throw new IllegalStateException("Host cannot fit " + vm.id + " -- would exceed hard hypervisor allocation");
            vms.add(vm);
            System.out.println("Placed " + vm.id + " (" + vm.allocatedVcpus + " vCPU, " + vm.allocatedMemoryMb + "Mi) on host");
        }
    }

    public static void main(String[] args) {
        MachineImage golden = new MachineImage("order-service-ami", "1.4.0");
        PhysicalHost host = new PhysicalHost(8, 16384);

        host.place(new VmInstance("vm-1", golden, 2, 4096));
        host.place(new VmInstance("vm-2", golden, 2, 4096));
        host.place(new VmInstance("vm-3", golden, 2, 4096));

        VmInstance vm4 = new VmInstance("vm-4", golden, 4, 8192); // won't fit -- host is nearly full
        System.out.println("Can host place vm-4 (4 vCPU, 8192Mi)? " + host.canPlace(vm4)
                + " -- unlike containers, the hypervisor allocation is HARD; there's no throttling fallback, only rejection.");
    }
}
```

How to run: `java VmResourcePartitioningIntermediate.java`

`PhysicalHost` tracks total vCPU and memory capacity, and `canPlace` checks whether a new VM's *statically allocated* resources fit within what remains. Unlike container CPU limits (which can allow oversubscription with throttling as a fallback), a hypervisor's VM allocation is typically a hard reservation — three VMs each claiming 2 vCPU / 4096Mi consume 6 vCPU / 12288Mi of the host's 8 vCPU / 16384Mi, leaving no room for a fourth VM wanting 4 vCPU / 8192Mi. `canPlace` correctly reports `false`; a real hypervisor would refuse to schedule it rather than silently overcommitting.

### Level 3 — Advanced

```java
// File: VmAutoScalingGroupAdvanced.java -- the SAME fleet, now handling a
// PRODUCTION-FLAVORED hard case: an Auto-Scaling-Group-style controller must
// replace an unhealthy VM while respecting a minCapacity constraint AND
// accounting for realistic VM boot latency before a replacement counts as
// healthy -- unlike containers, you can't assume near-instant replacement.
import java.util.*;

public class VmAutoScalingGroupAdvanced {
    record MachineImage(String name, String version) {}

    static class VmInstance {
        final String id;
        final MachineImage image;
        boolean healthy;
        int bootSecondsRemaining;

        VmInstance(String id, MachineImage image) {
            this.id = id; this.image = image;
            this.bootSecondsRemaining = 45; // realistic full-VM boot time
            this.healthy = false;
        }

        // Advance simulated time; a VM only becomes healthy once fully booted.
        void tick(int seconds) {
            if (healthy) return;
            bootSecondsRemaining -= seconds;
            if (bootSecondsRemaining <= 0) {
                healthy = true;
                System.out.println("[" + id + "] boot complete, now healthy");
            }
        }
    }

    public static void main(String[] args) {
        MachineImage golden = new MachineImage("order-service-ami", "1.4.0");
        int minCapacity = 3;
        List<VmInstance> fleet = new ArrayList<>();
        for (int i = 1; i <= minCapacity; i++) {
            VmInstance vm = new VmInstance("vm-" + i, golden);
            vm.healthy = true; // assume already-warm at start of simulation
            vm.bootSecondsRemaining = 0;
            fleet.add(vm);
        }
        System.out.println("Fleet starts steady at minCapacity=" + minCapacity + ", all healthy.");

        // vm-2 fails a health check -- the controller must replace it WITHOUT
        // dropping below minCapacity, and a replacement takes real boot time.
        VmInstance failing = fleet.get(1);
        System.out.println("[" + failing.id + "] failed health check, marking unhealthy and terminating");
        failing.healthy = false;
        fleet.remove(failing);

        VmInstance replacement = new VmInstance("vm-4", golden);
        fleet.add(replacement);
        System.out.println("Launched replacement " + replacement.id + ", booting (not yet counted as capacity)...");

        int elapsed = 0;
        while (fleet.stream().filter(v -> v.healthy).count() < minCapacity) {
            elapsed += 15;
            for (VmInstance vm : fleet) vm.tick(15);
            long healthyNow = fleet.stream().filter(v -> v.healthy).count();
            System.out.println("t=" + elapsed + "s: healthy capacity=" + healthyNow + "/" + minCapacity
                    + (healthyNow < minCapacity ? " -- BELOW minCapacity during this window" : " -- capacity restored"));
        }
        System.out.println("Total time below full capacity: " + elapsed + "s -- this window is the real cost of VM-per-instance replacement.");
    }
}
```

How to run: `java VmAutoScalingGroupAdvanced.java`

The hard case a VM-based fleet has to accept, that a container-based one mostly avoids, is that replacing a failed instance is not instantaneous — a fresh VM must actually boot (`bootSecondsRemaining` starts at 45 simulated seconds) before it counts toward `minCapacity`. The controller removes the failing VM immediately (correctly, since it's already unhealthy) and launches a replacement, but the fleet spends real time below its target capacity while that replacement boots. This is a genuine operational tradeoff of VM-per-instance: stronger isolation, but slower self-healing.

## 6. Walkthrough

Trace `VmAutoScalingGroupAdvanced.main` in order. **First**, three VMs (`vm-1`, `vm-2`, `vm-3`) are created and marked already-healthy, simulating a steady-state fleet at `minCapacity = 3`.

**Next**, `vm-2` (`failing`) is marked unhealthy and removed from `fleet` — the fleet now has two healthy VMs (`vm-1`, `vm-3`), one below `minCapacity`. A replacement, `vm-4`, is created with `bootSecondsRemaining = 45` and added to `fleet`, but it starts `healthy = false`, so it does not yet count toward capacity.

**Then**, the `while` loop advances simulated time in 15-second increments as long as healthy capacity is below `minCapacity`. At `t=15s`, `vm-4.tick(15)` reduces `bootSecondsRemaining` to `30` — still not healthy — so healthy capacity remains `2/3`, printed as below `minCapacity`. At `t=30s`, `bootSecondsRemaining` drops to `15` — still not healthy. At `t=45s`, `bootSecondsRemaining` reaches `0`, `vm-4` flips to `healthy = true`, and healthy capacity returns to `3/3`.

**Finally**, the loop exits and the program reports `elapsed = 45` seconds as the total time the fleet spent below full capacity — the concrete cost of VM boot latency during a replacement, a cost a container-based fleet (with sub-second-to-few-second starts) would pay only a small fraction of.

```
Fleet starts steady at minCapacity=3, all healthy.
[vm-2] failed health check, marking unhealthy and terminating
Launched replacement vm-4, booting (not yet counted as capacity)...
t=15s: healthy capacity=2/3 -- BELOW minCapacity during this window
t=30s: healthy capacity=2/3 -- BELOW minCapacity during this window
[vm-4] boot complete, now healthy
t=45s: healthy capacity=3/3 -- capacity restored
Total time below full capacity: 45s -- this window is the real cost of VM-per-instance replacement.
```

## 7. Gotchas & takeaways

> Treating VM boot time as negligible is a common capacity-planning mistake: a 45-second (or longer) gap where the fleet runs below target capacity, multiplied across every failure and every scale-up event, adds up to real availability risk during traffic spikes. Auto-scaling policies for VM fleets typically need to scale out earlier and more conservatively than container-based autoscalers to absorb this latency.

- VM-per-instance gives hypervisor-enforced isolation, a materially stronger security boundary than a container's shared-kernel isolation — reach for it when tenant trust genuinely can't be assumed, not by default.
- The cost of that stronger isolation is boot latency and resource overhead: each VM boots its own kernel and reserves resources statically, which is why VM fleets self-heal and scale more slowly than container fleets.
- Compare against [service instance per container](0435-service-instance-per-container.md), which trades some isolation strength for dramatically faster start times and denser packing — most stateless services land there today, with VMs reserved for the layer underneath (cloud Kubernetes nodes are VMs) or for genuinely isolation-sensitive workloads.
- Whether you deploy on VMs or containers, the same [immutable infrastructure](0437-immutable-infrastructure.md) discipline applies: never hand-patch a running instance; build a new image and replace the instance.
- A machine image (AMI, VM template) plays the same role a container image plays — a versioned, reusable, immutable artifact — just at a much heavier granularity; see [container image building](0438-container-image-building.md) for the lighter-weight equivalent.
