---
card: system-design
gi: 43
slug: spring-cloud-loadbalancer-for-client-side-balancing
title: Spring Cloud LoadBalancer for client-side balancing
---

## 1. What it is

**Spring Cloud LoadBalancer** performs **client-side load balancing**: instead of every request going through a separate, centralized load balancer server, the *calling service itself* looks up the list of available instances of the service it wants to call (via service discovery) and picks one directly, before making the request. This is the mechanism behind the `lb://service-name` URI scheme used by Spring Cloud Gateway, and it can also be used directly by any service calling another.

## 2. Why & when

A traditional (server-side) load balancer is a separate component every request must pass through, adding a network hop and a potential bottleneck. Client-side load balancing removes that extra hop: the calling service already knows the full list of healthy instances (from service discovery) and picks one itself, calling it directly. This fits naturally inside a microservices architecture, where services already register themselves with a discovery mechanism (like Eureka or Kubernetes-native discovery) for other reasons.

## 3. Core concept

**How it works, step by step:**
1. Each instance of a service registers itself with a **service registry** on startup (e.g. "order-service instance running at `10.0.1.5:8080`").
2. A calling service, wanting to reach `order-service`, asks the registry for the current list of healthy instances, instead of using one fixed, hardcoded address.
3. Spring Cloud LoadBalancer applies a load-balancing algorithm (by default, round-robin) across that list, on the client's own side, to pick one instance for this specific call.
4. The call goes directly from the calling service to the chosen instance — no separate load balancer server sits in between.

**How it plugs into HTTP clients you already use:** a `RestClient` or `WebClient` bean configured with `@LoadBalanced` automatically resolves a logical service name (like `http://order-service/orders/42`) into an actual instance address using this mechanism, so calling code stays almost identical to a normal HTTP call — the load-balancing and service-discovery lookup happen transparently underneath.

**Client-side vs server-side load balancing — the key tradeoff:**

| | Server-side (traditional LB) | Client-side (Spring Cloud LoadBalancer) |
|---|---|---|
| Extra network hop | Yes — every request passes through the LB | No — caller connects directly to the chosen instance |
| Where the instance list lives | On the load balancer | On each individual calling service |
| Failure mode | LB itself must be made highly available | Each caller depends on service discovery being available |

## 4. Diagram

```
 SERVER-SIDE (traditional)              CLIENT-SIDE (Spring Cloud LoadBalancer)
 Caller -> [LB server] -> Instance1      Caller: "who are order-service's instances?"
                        -> Instance2               |
                        -> Instance3      Service Registry: "Instance1, Instance2, Instance3"
   (every call passes through                       |
    a separate LB hop)                    Caller picks Instance2 itself (round-robin)
                                                     |
                                                     v
                                              connects DIRECTLY to Instance2
                                            (no separate LB hop in the path)
```
*Caption: client-side load balancing removes the separate load-balancer hop by letting the caller pick an instance itself, using service discovery.*

## 5. Runnable example

### Artifact: a minimal Java sketch of client-side load balancing over a discovered instance list

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class ClientSideLoadBalancerSim {

    // Stands in for a service registry lookup (e.g. Eureka).
    static List<String> discoverInstances(String serviceName) {
        return List.of("10.0.1.5:8080", "10.0.1.6:8080", "10.0.1.7:8080");
    }

    static class RoundRobinClientLoadBalancer {
        AtomicInteger counter = new AtomicInteger(0);

        String chooseInstance(String serviceName) {
            List<String> instances = discoverInstances(serviceName);
            int index = counter.getAndIncrement() % instances.size();
            return instances.get(index);
        }
    }

    public static void main(String[] args) {
        RoundRobinClientLoadBalancer loadBalancer = new RoundRobinClientLoadBalancer();

        System.out.println("Calling code asks for 'order-service', gets a chosen instance directly:");
        for (int i = 0; i < 4; i++) {
            String instance = loadBalancer.chooseInstance("order-service");
            System.out.println("  Call " + (i + 1) + " -> connects directly to " + instance);
        }
    }
}
```

**How to run:** save as `ClientSideLoadBalancerSim.java`, run `java ClientSideLoadBalancerSim.java` (JDK 17+). A real Spring Cloud application uses `spring-cloud-starter-loadbalancer` together with a discovery client (like `spring-cloud-starter-netflix-eureka-client`), and the `@LoadBalanced` annotation on a `RestClient`/`WebClient` bean handles this transparently, rather than requiring manual instance selection code.

## 6. Walkthrough

1. `discoverInstances` stands in for a real service registry lookup, returning the current list of healthy `order-service` instances — in a real app, this list changes dynamically as instances start, stop, or fail health checks.
2. `RoundRobinClientLoadBalancer.chooseInstance` fetches that instance list fresh, then applies a simple round-robin index to pick one — this is the client-side balancing decision, made entirely by the caller, with no separate load balancer server involved.
3. `main` simulates the calling service making 4 separate calls to `order-service`, each one independently resolving and picking an instance.
4. Output:
```
Calling code asks for 'order-service', gets a chosen instance directly:
  Call 1 -> connects directly to 10.0.1.5:8080
  Call 2 -> connects directly to 10.0.1.6:8080
  Call 3 -> connects directly to 10.0.1.7:8080
  Call 4 -> connects directly to 10.0.1.5:8080
```
5. Each call connects to a *different, specific instance address*, chosen entirely by the caller's own logic — there is no intermediate load balancer server in this path at all, which is the defining characteristic of client-side load balancing versus the traditional server-side approach.

## 7. Gotchas & takeaways

> **Gotcha:** assuming client-side load balancing removes the need for service discovery to be reliable. If the service registry itself is unavailable or returns a stale instance list, every calling service loses the ability to find healthy instances — client-side load balancing shifts the dependency from "the load balancer must be up" to "service discovery must be up and accurate", not eliminating that dependency entirely.

- Client-side load balancing lets the calling service pick a target instance itself, using service discovery, removing the extra hop through a separate load balancer server.
- `@LoadBalanced` on a `RestClient`/`WebClient` bean makes this transparent to calling code, resolving a logical service name into a real instance address automatically.
- It trades a centralized load balancer's single point of failure for a distributed dependency on service discovery being available and accurate everywhere.
