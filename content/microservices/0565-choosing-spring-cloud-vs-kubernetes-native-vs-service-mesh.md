---
card: microservices
gi: 565
slug: choosing-spring-cloud-vs-kubernetes-native-vs-service-mesh
title: "Choosing Spring Cloud vs Kubernetes-native vs service mesh"
---

## 1. What it is

Discovery, load balancing, resiliency, and configuration — the concerns Spring Cloud modules address — can also be provided by two other layers: **Kubernetes-native** capabilities (Services for discovery, ConfigMaps for configuration, as discussed for [Spring Cloud Kubernetes](0554-spring-cloud-kubernetes.md)), and a **service mesh** (like Istio or Linkerd, which inject a sidecar proxy alongside every service instance, handling discovery, load balancing, retries, circuit breaking, and mutual TLS entirely outside the application process, in the network layer). All three can solve overlapping problems; choosing between them — or combining them deliberately — is an architectural decision with real trade-offs, not a question with one universally correct answer.

## 2. Why & when

You need to choose deliberately between these three layers (or some combination) because each pushes the same responsibilities to a different place, with different costs:

- **Spring Cloud modules solve these concerns in the application layer** — a `@LoadBalanced` client, a circuit breaker annotation, a `DiscoveryClient` call are all library code running inside your application's own process. This means the logic is visible in your codebase, testable in your application's own test suite, and works identically regardless of deployment platform — but it also means every service needs the relevant Spring Cloud dependencies, and every language/framework in a polyglot fleet needs its own equivalent library, since this logic doesn't exist outside the Spring application itself.
- **Kubernetes-native capabilities solve a subset of these concerns (discovery, configuration, health-check-driven traffic routing) at the platform layer**, requiring no application-level library code at all for those specific concerns — but Kubernetes doesn't natively provide circuit breaking, retries, or mutual TLS between services, so resiliency concerns still need to be solved elsewhere if you're relying purely on Kubernetes-native discovery and configuration.
- **A service mesh solves discovery, load balancing, retries, circuit breaking, and mutual TLS entirely outside the application**, via a sidecar proxy intercepting all network traffic to and from each Pod — this means these concerns work identically across every service regardless of language or framework (a Python service and a Java service get the same mesh-provided resiliency, with zero library code in either), at the cost of a real new infrastructure layer to operate, additional latency per hop (traffic now passes through two sidecar proxies per call), and a genuinely different, sometimes more complex debugging experience when something goes wrong in the mesh itself.
- **You choose based on your fleet's actual composition and constraints**: a homogeneous, all-Spring fleet already comfortable with Spring Cloud may see little added value from a service mesh's cross-language benefit; a genuinely polyglot fleet (services in multiple languages/frameworks) benefits more from pushing these concerns to a mesh, since it avoids needing an equivalent library in every language; teams without service mesh operational experience may reasonably prefer Spring Cloud's more familiar, in-process debugging model, at least initially.

## 3. Core concept

Think of three different ways a company could provide translation services between departments speaking different languages. Every employee could individually learn a shared second language well enough to communicate directly (Spring Cloud: logic lives inside each participant, requiring every participant to individually adopt it). The building itself could provide translated signage and a shared company-wide directory in every language automatically (Kubernetes-native: the platform handles a specific subset of concerns — like knowing where things are — without every individual needing their own translation skill). Or the company could station a dedicated interpreter next to every employee's desk, silently translating every conversation in real time regardless of what language either party actually speaks (service mesh: a sidecar handling the concern entirely externally, transparent to every participant, working identically no matter which language/framework each side happens to use).

Concretely, mapping specific concerns to each layer:

1. **Discovery**: Spring Cloud (`DiscoveryClient` backed by Eureka/Consul/etc.), Kubernetes-native (Service/Endpoints), or mesh (sidecar-intercepted, using the mesh's own service registry) — all three can solve this; Kubernetes-native and mesh both work without any application-level discovery library.
2. **Load balancing**: Spring Cloud LoadBalancer (client-side, in-process), Kubernetes Service (server-side, via kube-proxy), or mesh sidecar (client-side, but external to the application process) — each intercepts and balances traffic at a different point in the stack.
3. **Resiliency (circuit breaking, retries, timeouts)**: Spring Cloud Circuit Breaker (in-process, Resilience4j-backed), or mesh-level policies (configured declaratively at the mesh layer, enforced by the sidecar, with zero application code) — Kubernetes itself provides no native equivalent for this specific concern.
4. **mTLS and fine-grained traffic policy (canary routing, fault injection for testing)**: primarily a service mesh capability, not something Spring Cloud or plain Kubernetes natively provides — if you need this specifically, a mesh is likely necessary regardless of your other choices.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same concerns -- discovery, load balancing, resiliency -- can be solved in the application layer (Spring Cloud), the platform layer (Kubernetes-native), or the network layer (service mesh sidecar), each with different trade-offs">
  <text x="150" y="20" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Cloud (in-process)</text>
  <rect x="20" y="35" width="260" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">library code inside your app</text>
  <text x="150" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">visible, testable, per-framework</text>

  <text x="510" y="20" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Service mesh (sidecar)</text>
  <rect x="380" y="35" width="260" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="510" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">proxy outside your app, per-pod</text>
  <text x="510" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">language-agnostic, extra hop + infra</text>

  <text x="330" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Kubernetes-native (platform)</text>
  <rect x="200" y="135" width="260" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="155" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Services + ConfigMaps, no library needed</text>
  <text x="330" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">discovery + config only, no resiliency layer</text>
</svg>

The same concerns can be solved at different layers of the stack, each with a different trade-off between visibility, cross-language reach, and infrastructure cost.

## 5. Runnable example

Scenario: modeling how the same "call a downstream service safely" concern is satisfied differently at each layer. We start with a plain Java model of in-process (Spring Cloud-style) resiliency, extend it to a model of platform-level discovery without resiliency, then show the conceptual shape of mesh-level policy applied transparently.

### Level 1 — Basic

```java
// File: InProcessResiliency.java -- models the SPRING CLOUD approach:
// resiliency logic lives INSIDE the application's own code, explicit
// and visible in the codebase.
public class InProcessResiliency {
    static int failureCount = 0;
    static boolean circuitOpen = false;

    static String callDownstreamWithResiliency(boolean simulateFailure) {
        if (circuitOpen) return "FALLBACK: circuit open, in-process logic caught this";
        if (simulateFailure) {
            failureCount++;
            if (failureCount >= 3) circuitOpen = true;
            return "FALLBACK: call failed, in-process logic caught this";
        }
        return "real response";
    }

    public static void main(String[] args) {
        for (int i = 0; i < 4; i++) System.out.println(callDownstreamWithResiliency(true));
        System.out.println("ALL resiliency logic lives in THIS application's own code -- visible, testable, but must be replicated per-service/per-language.");
    }
}
```

How to run: `java InProcessResiliency.java`

Every bit of the circuit-breaking logic — failure counting, threshold checking, fallback — is written directly in this application's own code, exactly the Spring Cloud Circuit Breaker approach: visible and unit-testable, but a Python or Go service in the same fleet would need its own, separately-implemented equivalent logic, since none of this exists outside this specific application's process.

### Level 2 — Intermediate

```java
// File: PlatformDiscoveryOnly.java -- models KUBERNETES-NATIVE
// discovery: the PLATFORM tracks healthy instances, requiring NO
// application-level discovery library -- but provides NO resiliency layer.
import java.util.*;

public class PlatformDiscoveryOnly {
    // models Kubernetes' OWN Endpoints tracking -- the application doesn't implement this itself
    static List<String> kubernetesTrackedEndpoints = List.of("10.1.2.3", "10.1.2.4");

    static String callViaKubernetesServiceDns(String serviceName) {
        // in REAL Kubernetes, this would just be a DNS lookup + kube-proxy routing --
        // no discovery LIBRARY code needed in the application at all
        System.out.println("Resolving " + serviceName + " via Kubernetes Service DNS -> platform picks from: " + kubernetesTrackedEndpoints);
        return "real response (but if THIS call fails, there's NO built-in retry/circuit-breaker here)";
    }

    public static void main(String[] args) {
        System.out.println(callViaKubernetesServiceDns("order-service"));
        System.out.println("Discovery handled by the PLATFORM, zero library code -- but resiliency (retries, circuit breaking) is NOT provided natively by Kubernetes itself.");
    }
}
```

How to run: `java PlatformDiscoveryOnly.java`

`callViaKubernetesServiceDns` needs no discovery library at all — Kubernetes' own Service/DNS/kube-proxy machinery handles instance resolution and load balancing entirely at the platform layer. But note what's *missing* here compared to Level 1: there's no circuit breaker, no retry logic — Kubernetes alone doesn't provide these; they'd need to come from Spring Cloud Circuit Breaker (application layer) or a service mesh (network layer) if this specific failure mode matters for your system.

### Level 3 — Advanced

```java
// File: MeshLevelPolicyConceptual.java -- models the SERVICE MESH
// approach: resiliency policy is declared EXTERNALLY (not in application
// code) and enforced by a sidecar TRANSPARENTLY, regardless of the
// calling application's language or framework.
public class MeshLevelPolicyConceptual {

    // this is NOT application code -- it's an illustrative representation of a
    // mesh configuration resource (e.g. an Istio DestinationRule / VirtualService)
    static final String MESH_POLICY_YAML = """
        apiVersion: networking.istio.io/v1beta1
        kind: DestinationRule
        metadata:
          name: pricing-service-circuit-breaker
        spec:
          host: pricing-service
          trafficPolicy:
            outlierDetection:
              consecutiveErrors: 3
              interval: 30s
              baseEjectionTime: 60s
        """;

    // the APPLICATION code calling pricing-service, UNAWARE any of this policy exists:
    static String applicationCallsPricingService() {
        System.out.println("[application] calling pricing-service normally, no resiliency code written here at all");
        return "response (sidecar transparently enforces the circuit-breaking policy above, OUTSIDE this process)";
    }

    public static void main(String[] args) {
        System.out.println(MESH_POLICY_YAML);
        System.out.println(applicationCallsPricingService());
        System.out.println("This SAME mesh policy applies identically whether the caller is Java, Python, Go, or anything else.");
    }
}
```

How to run: `java MeshLevelPolicyConceptual.java` prints the illustrative mesh policy and the calling application's behavior; in a real Istio-meshed Kubernetes cluster, this `DestinationRule` resource (applied via `kubectl apply`) would cause the sidecar proxy injected alongside every Pod calling `pricing-service` to automatically eject an unhealthy backend after 3 consecutive errors, for 60 seconds — entirely outside any application's own code, and identically for a Java, Python, or Go caller alike.

`applicationCallsPricingService` contains zero resiliency logic — no failure counting, no threshold checking, no fallback code at all. The `DestinationRule` YAML, applied separately at the mesh/platform layer, is what actually enforces this policy, intercepted and enacted by the sidecar proxy that sits transparently between this application and the network, regardless of what language or framework wrote the calling code.

## 6. Walkthrough

Trace the same downstream-call-protection concern being satisfied by each of the three approaches, contrasting exactly where the enforcement happens:

**Spring Cloud (Level 1):** the call to `callDownstreamWithResiliency` executes inside the application's own JVM; failure counting and circuit state (`failureCount`, `circuitOpen`) are fields inside this same process; a stack trace during debugging shows this application's own code directly implementing the protection logic — visible and directly debuggable, but this exact code (or its equivalent) must be written separately for every different language/framework in the fleet.

**Kubernetes-native discovery (Level 2):** `callViaKubernetesServiceDns` resolves `order-service` via a DNS lookup that Kubernetes' internal DNS server answers based on the current `Endpoints`/`EndpointSlice` state — no library code executes inside the application for this resolution step at all; but if the resolved instance's actual HTTP call fails, nothing in this flow retries it or protects future calls from repeating the failure, since Kubernetes' native discovery doesn't extend to that concern.

**Service mesh (Level 3):** `applicationCallsPricingService` issues what looks like an entirely ordinary network call from the application's point of view — but before that call actually leaves the Pod, it's intercepted by the sidecar proxy (injected automatically by the mesh's control plane into every Pod in the mesh), which enforces the `DestinationRule`'s circuit-breaking policy: if `pricing-service` has recently returned 3 consecutive errors, the sidecar itself ejects that specific backend from consideration for the configured `baseEjectionTime`, without the calling application's code ever being aware this happened — a debugging session for a request stalled or rejected due to this policy would need to inspect the *sidecar's* logs and the mesh's own observability tooling, not just the calling application's own logs, since the enforcement genuinely happened outside the application process.

## 7. Gotchas & takeaways

> **Gotcha:** combining all three layers without a clear division of responsibility (say, both a Spring Cloud circuit breaker *and* an equivalent mesh-level circuit breaker protecting the identical call) can produce confusing, hard-to-reason-about behavior — two independent circuit breakers tracking failures separately might trip at different times, and a request failure might be masked or retried at a layer you weren't expecting, making root-cause analysis significantly harder; if you adopt a service mesh for resiliency, seriously consider whether the equivalent Spring Cloud-level resiliency for the same call is still needed, rather than assuming "more layers of protection" is automatically better.

- Spring Cloud, Kubernetes-native capabilities, and a service mesh can all address overlapping discovery, load-balancing, and resiliency concerns, but at different layers of the stack, with different visibility, cross-language reach, and operational cost trade-offs.
- Kubernetes-native discovery and configuration require no application-level library code, but Kubernetes alone provides no native circuit-breaking or retry capability — that still needs to come from Spring Cloud or a mesh if your system requires it.
- A service mesh's biggest advantage is language-agnostic enforcement of resiliency and traffic policy, at the cost of a genuinely new infrastructure layer, added per-hop latency, and a different debugging experience when something goes wrong in the mesh itself.
- If you layer more than one of these approaches together, be deliberate about which layer owns which specific concern for which specific call path — redundant, uncoordinated protection at multiple layers can obscure root cause rather than adding genuine safety.
