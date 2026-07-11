---
card: spring-cloud
gi: 117
slug: kubernetes-native-load-balancing
title: "Kubernetes-native load balancing"
---

## 1. What it is

Kubernetes-native load balancing means letting a Kubernetes `Service`'s own virtual IP and kube-proxy routing handle distributing traffic across pod replicas, rather than the application performing client-side load balancing itself via Spring Cloud LoadBalancer — a call to `http://order-service:8080/orders` (the Service's cluster-DNS name) is transparently routed by the platform to one of the healthy backing pods, with the client application never seeing or choosing between individual pod IPs at all.

```java
// client-side load balancing (earlier cards): the CLIENT chooses among discovered instances
@LoadBalanced
RestTemplate restTemplate; // resolves "order-service" to one of several pod IPs, client-side

// Kubernetes-native: the client calls the Service's stable DNS name directly -- NO client-side choice at all
restTemplate.getForObject("http://order-service:8080/orders", Order[].class);
```

```yaml
apiVersion: v1
kind: Service
metadata: { name: order-service }
spec:
  selector: { app: order-service }
  ports: [{ port: 8080 }]
```

## 2. Why & when

Spring Cloud LoadBalancer's client-side load balancing (an earlier card) makes sense when the client is expected to choose among a set of individually-discovered instances itself, applying its own algorithm (round-robin, zone-aware, and so on) — this pattern is genuinely necessary against a discovery source like Eureka, which returns individual instance addresses. Kubernetes' own `Service` object already provides a stable virtual IP and DNS name that transparently load-balances across healthy backing pods at the platform/network layer (via kube-proxy or an equivalent), so an application inside the cluster can simply call the Service's DNS name directly and let the platform handle the distribution — no client-side instance list, no client-side balancing algorithm, and no `@LoadBalanced` annotation needed at all for calls staying purely within the cluster.

Reach for Kubernetes-native load balancing when:

- Both the calling application and the target service run inside the same Kubernetes cluster — calling the target's Service DNS name directly (`http://service-name:port/...`) is simpler and requires no Spring Cloud LoadBalancer configuration at all.
- The default kube-proxy load-balancing behavior (typically simple round-robin or random selection across ready pods) is sufficient for the traffic pattern — most internal service-to-service calls don't need the more sophisticated zone-aware or weighted balancing Spring Cloud LoadBalancer can provide.
- Simplicity and fewer moving parts matter more than fine-grained client-side balancing control — Kubernetes-native balancing removes an entire layer (client-side instance selection) from the application's own responsibility, delegating it entirely to infrastructure the platform already runs.

## 3. Core concept

```
 client-side load balancing (Spring Cloud LoadBalancer, against Eureka or Kubernetes discovery):
   client discovers [10.244.0.1, 10.244.0.2, 10.244.0.3]
   client's OWN algorithm picks ONE -- e.g. round-robin -> 10.244.0.2
   client connects DIRECTLY to 10.244.0.2

 Kubernetes-native load balancing (via a Service):
   client calls http://order-service:8080/orders  (ONE stable DNS name / virtual IP, never changes)
   kube-proxy (platform-level) routes the connection to ONE of the currently-ready backing pods
   client NEVER sees or chooses among individual pod IPs at all
```

The balancing decision moves from application-level code (an explicit `LoadBalancerClient` algorithm) to platform-level infrastructure (`kube-proxy`'s own routing rules) — both achieve the same end goal of spreading traffic across replicas, at different layers of the stack.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client calls a single stable Service DNS name and kube-proxy at the platform layer transparently routes the connection to one of several ready backing pods with the client never choosing among individual pod addresses">
  <rect x="20" y="60" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">client pod</text>

  <rect x="230" y="60" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="80" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">order-service:8080</text>
  <text x="320" y="94" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">stable virtual IP / DNS</text>

  <rect x="480" y="20" width="140" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="550" y="41" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">pod A</text>
  <rect x="480" y="65" width="140" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="550" y="86" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">pod B</text>
  <rect x="480" y="110" width="140" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="550" y="131" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">pod C</text>

  <defs><marker id="a117" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="160" y1="83" x2="230" y2="83" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a117)"/>
  <line x1="410" y1="75" x2="480" y2="38" stroke="#8b949e" stroke-width="1" marker-end="url(#a117)" stroke-dasharray="3,3"/>
  <line x1="410" y1="83" x2="480" y2="83" stroke="#8b949e" stroke-width="1" marker-end="url(#a117)" stroke-dasharray="3,3"/>
  <line x1="410" y1="90" x2="480" y2="127" stroke="#8b949e" stroke-width="1" marker-end="url(#a117)" stroke-dasharray="3,3"/>
</svg>

The client sees exactly one destination address; kube-proxy is what actually picks the specific pod, transparently.

## 5. Runnable example

The scenario: model a client calling a stable Service-name endpoint, with a simulated kube-proxy layer performing the actual pod selection — contrasted against explicit client-side load balancing where the client itself chooses. Start with client-side balancing (the pattern from earlier cards), then add a Kubernetes-native Service abstraction where the client makes one call to one name, then extend to show the platform-level routing automatically adapting as the backing pod set changes, with zero client-side awareness of that change.

### Level 1 — Basic

Client-side load balancing — the client itself picks among discovered instances (the pattern earlier LoadBalancer cards covered).

```java
import java.util.*;

public class K8sLoadBalancingLevel1 {
    static int roundRobinCounter = 0;

    static String clientSidePick(List<String> instances) {
        String chosen = instances.get(roundRobinCounter % instances.size());
        roundRobinCounter++;
        return chosen;
    }

    public static void main(String[] args) {
        List<String> instances = List.of("10.244.0.1", "10.244.0.2", "10.244.0.3");

        for (int i = 0; i < 4; i++) {
            String target = clientSidePick(instances); // the CLIENT decides which specific pod to call
            System.out.println("client calling: " + target);
        }
    }
}
```

How to run: `java K8sLoadBalancingLevel1.java`

The client explicitly holds the full instance list and its own round-robin counter — this is genuine client-side balancing, requiring the client to know about, and choose among, individual pod addresses directly.

### Level 2 — Intermediate

Add a Kubernetes-native Service abstraction: the client makes one call to one stable name, and a separate "kube-proxy" component performs the actual pod selection, entirely hidden from the client.

```java
import java.util.*;

public class K8sLoadBalancingLevel2 {
    // models kube-proxy: routes a Service call to one of its CURRENT backing pods
    static class KubeProxy {
        Map<String, List<String>> servicePods = new HashMap<>();
        int roundRobinCounter = 0;

        void registerService(String serviceName, List<String> pods) { servicePods.put(serviceName, pods); }

        String route(String serviceName) {
            List<String> pods = servicePods.get(serviceName);
            String chosen = pods.get(roundRobinCounter % pods.size());
            roundRobinCounter++;
            return chosen;
        }
    }

    // the CLIENT knows only the Service name -- NO instance list, NO balancing algorithm of its own
    static void clientCall(KubeProxy proxy, String serviceName) {
        String routedTo = proxy.route(serviceName); // platform-level routing, invisible to client logic
        System.out.println("client called '" + serviceName + "', kube-proxy routed to: " + routedTo);
    }

    public static void main(String[] args) {
        KubeProxy proxy = new KubeProxy();
        proxy.registerService("order-service", List.of("10.244.0.1", "10.244.0.2", "10.244.0.3"));

        for (int i = 0; i < 4; i++) {
            clientCall(proxy, "order-service"); // SAME call every time -- the client never varies its own code
        }
    }
}
```

How to run: `java K8sLoadBalancingLevel2.java`

`clientCall` is invoked identically on every iteration, with no round-robin counter or instance list anywhere in the client's own code — all of that logic lives entirely inside `KubeProxy`, exactly mirroring how a real application calling a Kubernetes Service's DNS name has no client-side balancing code at all; the platform's `kube-proxy` (or equivalent networking component) performs the actual routing decision transparently.

### Level 3 — Advanced

Extend to show the platform-level routing automatically adapting when the backing pod set changes (a pod is removed, a new one added) — with the client's calling code completely unchanged and unaware of the change.

```java
import java.util.*;

public class K8sLoadBalancingLevel3 {
    static class KubeProxy {
        List<String> pods = new ArrayList<>();
        int roundRobinCounter = 0;

        void updatePods(List<String> currentPods) {
            pods = new ArrayList<>(currentPods);
            System.out.println("kube-proxy's backing pod set updated to: " + pods);
        }

        String route() {
            if (pods.isEmpty()) throw new IllegalStateException("no ready pods to route to");
            String chosen = pods.get(roundRobinCounter % pods.size());
            roundRobinCounter++;
            return chosen;
        }
    }

    static void clientCall(KubeProxy proxy) {
        System.out.println("client called order-service, routed to: " + proxy.route()); // UNCHANGED across the whole run
    }

    public static void main(String[] args) {
        KubeProxy proxy = new KubeProxy();
        proxy.updatePods(List.of("10.244.0.1", "10.244.0.2"));

        clientCall(proxy);
        clientCall(proxy);

        // a rolling deployment: pod .1 is replaced by a new pod .4 -- kube-proxy's view updates, client code does NOT
        proxy.updatePods(List.of("10.244.0.2", "10.244.0.4"));

        clientCall(proxy); // client's OWN code is IDENTICAL to the calls above -- yet now reaches a NEW pod set
        clientCall(proxy);
    }
}
```

How to run: `java K8sLoadBalancingLevel3.java`

`clientCall(proxy)` is called four times with byte-for-byte identical code each time, yet the pods it actually reaches shift the moment `proxy.updatePods(...)` is called mid-run with a different pod set (`10.244.0.1` replaced by `10.244.0.4`) — this is precisely the operational benefit of platform-level load balancing during events like rolling deployments or pod rescheduling: the client's own code and configuration require zero updates, because it was never aware of individual pod identities to begin with.

## 6. Walkthrough

Trace the pod-set change and its effect on subsequent calls in Level 3.

1. `proxy.updatePods(List.of("10.244.0.1", "10.244.0.2"))` sets `proxy.pods` to a two-element list.
2. The first `clientCall(proxy)` calls `proxy.route()`, which computes `pods.get(0 % 2)` = `pods.get(0)` = `"10.244.0.1"`, then increments `roundRobinCounter` to `1`.
3. The second `clientCall(proxy)` calls `route()` again, computing `pods.get(1 % 2)` = `pods.get(1)` = `"10.244.0.2"`, incrementing the counter to `2`.
4. `proxy.updatePods(List.of("10.244.0.2", "10.244.0.4"))` replaces `proxy.pods` entirely with a new list — note `roundRobinCounter` is *not* reset by `updatePods`, it retains its value of `2` from before, modeling that a real load-balancing counter doesn't necessarily restart cleanly on every topology change.
5. The third `clientCall(proxy)` calls `route()`, computing `pods.get(2 % 2)` = `pods.get(0)` against the *new* `pods` list, which is now `"10.244.0.2"`.
6. The fourth `clientCall(proxy)` computes `pods.get(3 % 2)` = `pods.get(1)` = `"10.244.0.4"` — the client successfully reaches the brand-new pod `10.244.0.4`, despite `clientCall`'s own source code never having changed across any of the four calls; only `proxy`'s internal state evolved, entirely outside the client's awareness or control.

```
pods = [.1, .2]
  call 1: route() -> pods[0 % 2] = .1
  call 2: route() -> pods[1 % 2] = .2
updatePods([.2, .4])   <- pod .1 replaced by NEW pod .4, roundRobinCounter stays at 2 (not reset)
  call 3: route() -> pods[2 % 2] = pods[0] = .2  (against the NEW list)
  call 4: route() -> pods[3 % 2] = pods[1] = .4  (reaches the brand-new pod)

clientCall()'s own source: IDENTICAL across all 4 calls
```

## 7. Gotchas & takeaways

> **Gotcha:** Kubernetes-native load balancing (via a Service's virtual IP) typically only balances calls *within* the cluster, at a relatively simple level (commonly round-robin or connection-based, depending on the kube-proxy mode) — it lacks the more sophisticated zone-awareness, weighted routing, or custom algorithm support Spring Cloud LoadBalancer can provide client-side. For traffic patterns genuinely needing that finer control (cross-zone latency optimization, gradual canary weighting), client-side balancing still has a role even within Kubernetes, rather than assuming platform-native balancing alone is always sufficient.

- Kubernetes-native load balancing moves the balancing decision from application code to platform infrastructure — a client calling a Service's stable DNS name never needs to know about, or choose among, individual pod addresses at all.
- This significantly simplifies the common case of purely intra-cluster service-to-service calls, removing an entire layer of client-side configuration (`@LoadBalanced`, a `LoadBalancerClient` bean) that Spring Cloud LoadBalancer would otherwise require.
- Because the platform, not the client, tracks which pods are currently healthy and routes accordingly, topology changes (rolling deployments, pod rescheduling, scaling events) require zero client-side code or configuration changes to keep working correctly.
- Spring Cloud LoadBalancer and Kubernetes-native balancing aren't mutually exclusive within one system — an application might use Kubernetes-native balancing for simple intra-cluster calls while still reaching for Spring Cloud LoadBalancer's richer client-side algorithms for calls where zone-awareness or custom weighting genuinely matters.
