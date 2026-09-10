---
card: system-design
gi: 216
slug: containers-images
title: Containers & images
---

## 1. What it is

A **container image** is a packaged, read-only snapshot of an application and everything it needs to run — code, runtime, libraries, configuration — built once and run identically anywhere. A **container** is a running instance of that image, isolated from other containers on the same machine using the host operating system's own isolation features (namespaces and cgroups on Linux), without needing a full separate operating system per container like a virtual machine does.

## 2. Why & when

"It works on my machine but not in production" happens because the running environment (OS version, installed libraries, environment variables) differs between where code was built and where it runs. A container image bundles the exact environment the application needs, so the same image runs identically on a developer's laptop, in a CI pipeline, and in production — removing that whole class of environment-mismatch bugs.

Containers are lighter than virtual machines because they share the host's kernel instead of running a full guest OS each, so you can run far more containers than VMs on the same hardware, and they start in seconds rather than minutes. Use containers as the standard deployment unit for any service in a modern system — especially one built as [microservices](0196-microservices.md), where many small, independently deployable units benefit most from fast, consistent packaging. A container is unnecessary overhead only for the simplest static-file hosting or a single script with no dependency concerns.

## 3. Core concept

- **Image layers.** An image is built from a stack of read-only layers, each one a diff from the layer below (a `Dockerfile` instruction like `RUN apt-get install ...` creates one layer). Layers are cached and shared across images, so rebuilding an image after a small code change only rebuilds the layers after that change, not the whole image.
- **The container is a writable layer on top of the image.** When a container starts, a thin writable layer is added on top of the image's read-only layers. Anything the container writes at runtime goes there; the underlying image itself is never modified, which is why the same image can start many independent containers.
- **Isolation via namespaces and cgroups.** Linux namespaces give each container its own view of processes, network interfaces, and filesystem mounts, so containers cannot see each other's processes. Control groups (cgroups) limit how much CPU and memory each container can use, so one container cannot starve the others on the same host.
- **A registry stores and distributes images.** You build an image once, push it to a registry (like Docker Hub or a private registry), and any host that can reach that registry can pull and run the exact same image — this is what makes an image portable across environments.
- **Tags identify specific versions.** An image reference like `myapp:1.4.2` (or `myapp:latest`) pins which version of the image to run — using `latest` in production is risky, because it can silently point to a different image tomorrow than it does today.

## 4. Diagram

```
   IMAGE (read-only, layered)                CONTAINER (running instance)

   layer 4: COPY app.jar /app                +--------------------------+
   layer 3: RUN apt-get install openjdk       |  writable layer (this     |
   layer 2: FROM ubuntu:22.04 (base layers)   |  container's own changes  |
   layer 1: (ubuntu base filesystem)          |  at runtime)               |
                                               +--------------------------+
        |                                      | layer 4 (shared, read-only)
        |  docker run myapp:1.4.2               | layer 3 (shared, read-only)
        +-------------------------------------->| layer 2 (shared, read-only)
                                                 | layer 1 (shared, read-only)
                                                 +--------------------------+
                                                      isolated via namespaces
                                                      limited via cgroups

   Ten containers from the SAME image share the read-only layers on disk -
   only their thin writable layers differ.
```
*Caption: the image's layers are shared and never modified; each running container only adds its own small writable layer on top, which is why starting a new container is fast and cheap.*

## 5. Runnable example

This models the concepts a container runtime implements — layered images, isolation of resource limits, and registry-based distribution — in one file, since real container tooling (Docker, containerd) is not something a single Java file can run directly.

**Level 1 — Basic.** Build a layered image (a list of instructions) and "run" it as a container with its own writable layer.

**Level 2 — Intermediate.** Show layer caching: rebuilding an image after a late-layer change reuses earlier, unchanged layers.

**Level 3 — Advanced.** Simulate cgroup-style resource limits: a container that tries to exceed its allotted memory is stopped, while other containers on the same "host" are unaffected.

```java
// ContainersImagesDemo.java
import java.util.*;

public class ContainersImagesDemo {

    record Layer(String instruction, String contentHash) {}

    // ---------- Level 1: build a layered image, run it as a container ----------
    static class Image {
        String name;
        List<Layer> layers = new ArrayList<>();
        Image(String name) { this.name = name; }

        void addLayer(String instruction) {
            String hash = "sha:" + Integer.toHexString((name + instruction + layers.size()).hashCode());
            layers.add(new Layer(instruction, hash));
        }
    }

    static class Container {
        String id;
        Image image;
        Map<String, String> writableLayer = new HashMap<>(); // this container's own runtime changes
        Container(String id, Image image) { this.id = id; this.image = image; }

        void writeAtRuntime(String key, String value) {
            writableLayer.put(key, value); // never touches the image's read-only layers
        }
    }

    // ---------- Level 2: layer caching on rebuild ----------
    static Image rebuildWithCache(Image previous, List<String> newInstructions) {
        Image rebuilt = new Image(previous.name);
        for (int i = 0; i < newInstructions.size(); i++) {
            String instruction = newInstructions.get(i);
            if (i < previous.layers.size() && previous.layers.get(i).instruction().equals(instruction)) {
                rebuilt.layers.add(previous.layers.get(i)); // CACHE HIT: reuse the unchanged layer
                System.out.println("    layer " + i + " CACHE HIT: \"" + instruction + "\"");
            } else {
                rebuilt.addLayer(instruction); // CACHE MISS: this and every later layer must rebuild
                System.out.println("    layer " + i + " CACHE MISS (rebuilt): \"" + instruction + "\"");
            }
        }
        return rebuilt;
    }

    // ---------- Level 3: cgroup-style memory limits, isolated per container ----------
    static class ResourceLimitedHost {
        Map<String, Integer> memoryLimitMb = new HashMap<>();
        Map<String, Integer> memoryUsedMb = new HashMap<>();

        void setLimit(String containerId, int limitMb) { memoryLimitMb.put(containerId, limitMb); }

        String allocate(String containerId, int mb) {
            int used = memoryUsedMb.getOrDefault(containerId, 0);
            int limit = memoryLimitMb.getOrDefault(containerId, Integer.MAX_VALUE);
            if (used + mb > limit) {
                return "[cgroup] container " + containerId + " OOM-killed: tried to use " +
                    (used + mb) + "MB, limit is " + limit + "MB";
            }
            memoryUsedMb.put(containerId, used + mb);
            return "[cgroup] container " + containerId + " now using " + (used + mb) + "MB / " + limit + "MB";
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - build a layered image, run two containers from it:");
        Image image = new Image("myapp");
        image.addLayer("FROM ubuntu:22.04");
        image.addLayer("RUN apt-get install openjdk");
        image.addLayer("COPY app.jar /app");
        System.out.println("  image " + image.name + " has " + image.layers.size() + " layers");

        Container c1 = new Container("container-1", image);
        Container c2 = new Container("container-2", image);
        c1.writeAtRuntime("session-cache", "user-42-data");
        c2.writeAtRuntime("session-cache", "user-77-data");
        System.out.println("  c1 writable layer: " + c1.writableLayer);
        System.out.println("  c2 writable layer: " + c2.writableLayer);
        System.out.println("  both share the SAME " + image.layers.size() + " read-only image layers underneath");

        System.out.println("\nLevel 2 - rebuild after changing only the LAST instruction:");
        Image rebuilt = rebuildWithCache(image,
            List.of("FROM ubuntu:22.04", "RUN apt-get install openjdk", "COPY app-v2.jar /app"));
        System.out.println("  rebuilt image has " + rebuilt.layers.size() + " layers, 2 reused from cache");

        System.out.println("\nLevel 3 - cgroup-style memory isolation, one container hits its limit:");
        ResourceLimitedHost host = new ResourceLimitedHost();
        host.setLimit("container-1", 512);
        host.setLimit("container-2", 256);
        System.out.println("  " + host.allocate("container-1", 300));
        System.out.println("  " + host.allocate("container-2", 200));
        System.out.println("  " + host.allocate("container-1", 300)); // container-1 exceeds its own limit
        System.out.println("  " + host.allocate("container-2", 50) + "  <- container-2 unaffected by container-1's limit");
    }
}
```

**How to run:** `java ContainersImagesDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `image.addLayer(...)` is called three times, each adding one instruction as a `Layer` with a computed hash. `Container c1` and `Container c2` are both created **from the same `image`** — neither copies the image's layers, they only reference it.
2. `c1.writeAtRuntime(...)` and `c2.writeAtRuntime(...)` each write to their own private `writableLayer` map. The printed output shows each container has different data in its writable layer, while both still point at the identical three-layer image underneath — this is exactly how many containers from one image stay isolated from each other while sharing the same underlying image data.
3. **Level 2:** `rebuildWithCache` compares each new instruction against the corresponding layer in the previous image. The first two instructions (`FROM ubuntu:22.04`, `RUN apt-get install openjdk`) are unchanged, so both print `"CACHE HIT"` and reuse the existing `Layer` object rather than recomputing it. The third instruction changed (`app.jar` to `app-v2.jar`), so it prints `"CACHE MISS"` and a new layer is built.
4. This is exactly why changing a line near the *end* of a `Dockerfile` rebuilds quickly (only that last layer changes) while changing a line near the *beginning* forces every layer after it to rebuild too — the code's `if` check only hits cache while instructions match position-by-position from the start.
5. **Level 3:** `host.allocate("container-1", 300)` succeeds, bringing container-1 to 300MB out of its 512MB limit. `host.allocate("container-2", 200)` succeeds independently, using its own separate 256MB limit. The **second** `host.allocate("container-1", 300)` call would push container-1 to 600MB, over its 512MB limit — the method detects `used + mb > limit` and returns an "OOM-killed" message instead of allocating. The final call, `host.allocate("container-2", 50)`, succeeds normally, proving container-1 hitting its limit had zero effect on container-2's independent budget.

## 7. Gotchas & takeaways

> **Gotcha:** an image tagged `latest` (or any mutable tag) can point to a different actual image tomorrow than it does today — a redeploy that just says "pull `myapp:latest`" is not reproducible. Pin production deployments to an immutable tag or digest (a specific version or content hash) so "the same deployment" always means the same bytes.

- Order `Dockerfile`-style instructions from least-often-changed to most-often-changed, so layer caching gives you the fastest possible rebuilds — put dependency installation before application code copy.
- Containers share the host kernel, so they are not as strongly isolated as virtual machines — treat container isolation as a resource and namespace boundary, not a full security boundary against a truly hostile workload on the same host.
- Always set explicit resource limits (CPU and memory) per container in production — an unbounded container can starve every other container on the same host, exactly as Level 3 demonstrates for one container hitting its own limit.
- Containers are the standard deployment unit that [Kubernetes](0217-kubernetes-pods-deployments-services.md) orchestrates — understanding images and containers is the prerequisite for understanding what a pod actually runs.
