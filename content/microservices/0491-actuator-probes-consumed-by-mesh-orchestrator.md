---
card: microservices
gi: 491
slug: actuator-probes-consumed-by-mesh-orchestrator
title: "Actuator probes consumed by mesh/orchestrator"
---

## 1. What it is

Once a service runs inside a mesh, its Spring Boot Actuator [liveness and readiness probes](0473-spring-boot-actuator-liveness-readiness-probes-for-kubernete.md) are consumed by **two** separate systems, not one: Kubernetes uses them exactly as before (restart on liveness failure, remove from Service endpoints on readiness failure), and the mesh's sidecar proxy *also* needs the application to be genuinely ready before it starts forwarding real traffic to it — meaning the readiness signal now has two consumers that both need to agree on what "ready" actually means.

## 2. Why & when

You need to think through this dual-consumer reality specifically once a mesh sidecar is added to the Pod, because a probe that was correctly configured for Kubernetes alone can behave subtly wrong once a sidecar is also involved:

- **The sidecar itself needs startup time, and the application shouldn't be marked ready before the sidecar can actually route to it.** If Kubernetes marks the Pod's readiness based purely on the application container's own probe, ignoring the sidecar's own readiness, traffic could be routed to a Pod whose sidecar isn't actually ready to forward it correctly yet.
- **Kubernetes' native sidecar container support (and most mesh implementations) coordinate Pod-level readiness across *all* containers, not just the application's.** A Pod's overall readiness should reflect the combined state of the application *and* its sidecar — not either one in isolation.
- **A probe that checks a downstream dependency the mesh itself manages resiliency for can create confusing double-layered failure signaling.** If the application's readiness probe fails because a downstream call (which the mesh would normally retry or route around) fails, and the mesh is also independently tracking that same downstream's health, you can end up with overlapping, sometimes contradictory pictures of what's actually wrong.
- **You verify this specifically when onboarding a service onto the mesh** — confirming that Pod-level readiness genuinely reflects "the application and its sidecar are both ready to participate in mesh traffic," not just "the application process itself started."

## 3. Core concept

Think of a restaurant that isn't truly open for business until both the kitchen (the application) is ready to cook *and* the host stand (the sidecar) is staffed and ready to seat customers — a kitchen that's ready but has no host to seat anyone isn't actually able to serve customers yet, even though the kitchen itself would happily report "I'm ready" if asked in isolation.

Concretely:

1. **Kubernetes' Pod readiness aggregates the readiness of every container in the Pod** (when using native sidecar support) — a Pod is only marked ready, and only added to a Service's routable endpoints, once *all* its containers, application and sidecar alike, report ready.
2. **The application's own Actuator readiness probe should reflect only what the application itself is responsible for** — its own internal state, its own required dependencies it directly manages — not attempt to also account for the sidecar's readiness, which is a separate container with its own probe.
3. **The sidecar has its own readiness signal**, checked independently by Kubernetes (or coordinated automatically by the mesh's own tooling), reflecting whether the proxy itself has established the connections and configuration it needs to correctly route traffic.
4. **The combined effect is what actually determines whether the Pod receives traffic** — even a perfectly healthy, ready application won't correctly receive or send mesh traffic if its sidecar isn't also ready, which is exactly why both signals matter and why conflating them (or checking only one) creates a real gap.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pod readiness requires both the application container's probe and the sidecar container's own readiness to pass before the Pod is added to Service endpoints">
  <rect x="20" y="20" width="270" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">app container readiness probe</text>
  <text x="155" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">application's own state</text>

  <rect x="370" y="20" width="270" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="505" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">sidecar readiness</text>
  <text x="505" y="65" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">proxy's own configuration state</text>

  <rect x="180" y="130" width="300" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="160" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Pod ready ONLY if BOTH pass</text>

  <line x1="155" y1="80" x2="280" y2="130" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="505" y1="80" x2="380" y2="130" stroke="#8b949e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Pod-level readiness requires both the application and its sidecar to independently report ready.

## 5. Runnable example

Scenario: a Pod-readiness aggregator combining an application probe and a sidecar probe. We start with a basic single-probe model (the pre-mesh world), extend it to combined two-probe aggregation, then handle the hard case: the application probe passing while the sidecar probe fails, which must still keep the Pod out of traffic overall, catching exactly the gap that checking only the application probe would miss.

### Level 1 — Basic

```java
// File: SingleProbeBasic.java -- models the PRE-MESH world: Pod readiness
// depends ONLY on the application container's own probe -- no sidecar
// exists yet to factor in.
public class SingleProbeBasic {
    static boolean applicationReady = true;

    static boolean checkPodReadiness() {
        System.out.println("[kubernetes] app container readiness: " + applicationReady);
        return applicationReady;
    }

    public static void main(String[] args) {
        boolean podReady = checkPodReadiness();
        System.out.println("[kubernetes] Pod added to Service endpoints: " + podReady);
    }
}
```

How to run: `java SingleProbeBasic.java`

`checkPodReadiness` reads only `applicationReady`, correctly modeling the pre-mesh world where the application container's own probe is the entire story — there's no second container's state to factor in yet.

### Level 2 — Intermediate

```java
// File: CombinedProbeReadiness.java -- the SAME readiness check, now
// EXTENDED to a mesh-enabled Pod: readiness requires BOTH the
// application's own probe AND the sidecar's own probe to pass.
public class CombinedProbeReadiness {
    static boolean applicationReady = true;
    static boolean sidecarReady = true;

    static boolean checkPodReadiness() {
        System.out.println("[kubernetes] app container readiness: " + applicationReady);
        System.out.println("[kubernetes] sidecar container readiness: " + sidecarReady);
        boolean podReady = applicationReady && sidecarReady;
        return podReady;
    }

    public static void main(String[] args) {
        boolean podReady = checkPodReadiness();
        System.out.println("[kubernetes] Pod added to Service endpoints: " + podReady + " (requires BOTH containers ready)");
    }
}
```

How to run: `java CombinedProbeReadiness.java`

`checkPodReadiness` now combines both signals with `&&` — `podReady` is only `true` if *both* `applicationReady` and `sidecarReady` are `true`, correctly modeling Kubernetes' aggregated Pod-level readiness once a sidecar container is present alongside the application.

### Level 3 — Advanced

```java
// File: SidecarNotReadyGap.java -- the SAME combined readiness check, now
// handling the PRODUCTION-FLAVORED hard case: the APPLICATION reports
// ready, but the SIDECAR is NOT yet ready (still establishing its mesh
// configuration). If Pod readiness were checked using ONLY the
// application's probe (the OLD, pre-mesh assumption), traffic would be
// routed to a Pod whose sidecar can't actually forward it correctly --
// this must be caught by the COMBINED check.
public class SidecarNotReadyGap {
    static boolean applicationReady = true; // the app itself is genuinely fine
    static boolean sidecarReady = false;    // sidecar still initializing its mesh config

    // The OLD, INCORRECT assumption: only check the app's own probe.
    static boolean oldIncorrectReadinessCheck() {
        System.out.println("[OLD/INCORRECT] checking ONLY app container readiness: " + applicationReady);
        return applicationReady;
    }

    // The CORRECT, mesh-aware check: BOTH containers must be ready.
    static boolean correctCombinedReadinessCheck() {
        System.out.println("[CORRECT] app container readiness: " + applicationReady + ", sidecar readiness: " + sidecarReady);
        return applicationReady && sidecarReady;
    }

    public static void main(String[] args) {
        System.out.println("--- using the OLD, pre-mesh readiness assumption ---");
        boolean oldResult = oldIncorrectReadinessCheck();
        System.out.println("[OLD] Pod would be added to Service endpoints: " + oldResult);
        if (oldResult) {
            System.out.println("[OLD] DANGER: traffic would be routed to this Pod, but its sidecar isn't ready to forward it correctly!");
        }

        System.out.println();
        System.out.println("--- using the CORRECT, mesh-aware combined check ---");
        boolean correctResult = correctCombinedReadinessCheck();
        System.out.println("[CORRECT] Pod added to Service endpoints: " + correctResult);
        if (!correctResult) {
            System.out.println("[CORRECT] Pod correctly held OUT of traffic until the sidecar finishes initializing");
        }
    }
}
```

How to run: `java SidecarNotReadyGap.java`

`oldIncorrectReadinessCheck` only reads `applicationReady`, which is `true`, so it incorrectly reports the Pod as ready to serve traffic — completely blind to `sidecarReady` being `false`. `correctCombinedReadinessCheck` reads both flags and combines them with `&&`; since `sidecarReady` is `false`, the whole expression evaluates to `false` regardless of `applicationReady`'s value, correctly holding the Pod out of the routable set until the sidecar catches up.

## 6. Walkthrough

Trace `SidecarNotReadyGap.main` in order. **First**, the "OLD" section calls `oldIncorrectReadinessCheck()`. Inside it, the method reads and prints only `applicationReady`, which is `true`, and returns that value directly — `sidecarReady` is never referenced anywhere inside this method at all.

**Next**, back in `main`, `oldResult` holds `true`, so the `if (oldResult)` branch runs, printing an explicit danger warning: under this old assumption, the Pod would be marked ready and added to Service endpoints, even though its sidecar genuinely isn't ready to correctly forward traffic yet.

**Then**, the "CORRECT" section calls `correctCombinedReadinessCheck()`. This method reads and prints *both* `applicationReady` (`true`) and `sidecarReady` (`false`), then returns `applicationReady && sidecarReady` — since one operand is `false`, the whole expression evaluates to `false`, regardless of the other operand's value.

**After that**, back in `main`, `correctResult` holds `false`, so the final `if (!correctResult)` branch runs, printing confirmation that the Pod is correctly being held out of traffic — the exact opposite outcome from the old, incorrect check, using the same underlying `applicationReady` value but correctly also accounting for `sidecarReady`.

**Finally**, the program has demonstrated, side by side, the exact same application state (genuinely healthy) producing two different Pod-readiness conclusions depending entirely on whether the sidecar's own readiness was factored into the decision — proving concretely why a mesh-aware Pod needs its readiness check to cover both containers, not just the application's.

```
--- using the OLD, pre-mesh readiness assumption ---
[OLD/INCORRECT] checking ONLY app container readiness: true
[OLD] Pod would be added to Service endpoints: true
[OLD] DANGER: traffic would be routed to this Pod, but its sidecar isn't ready to forward it correctly!

--- using the CORRECT, mesh-aware combined check ---
[CORRECT] app container readiness: true, sidecar readiness: false
[CORRECT] Pod added to Service endpoints: false
[CORRECT] Pod correctly held OUT of traffic until the sidecar finishes initializing
```

## 7. Gotchas & takeaways

> A Pod readiness configuration that was correct before a mesh sidecar was added can silently become incorrect the moment the sidecar is introduced, if nobody revisits it — the application's own probe hasn't changed and still reports accurately, but it's no longer the complete picture of whether the Pod is actually ready to participate in mesh traffic.
- Kubernetes' native sidecar container support (where available) handles this aggregation automatically — verify your cluster and mesh version actually use it, rather than assuming it's in place.
- Keep the application's own [Actuator readiness probe](0473-spring-boot-actuator-liveness-readiness-probes-for-kubernete.md) scoped to what the application itself is responsible for — resist the temptation to make it also try to check sidecar-specific state, which belongs to a separate, dedicated probe on the sidecar container itself.
- This is a specific, concrete instance of the coordination concerns raised in [running Spring Boot services inside a mesh](0488-running-spring-boot-services-inside-a-mesh.md) — that topic covers the broader lifecycle picture; this one focuses specifically on the readiness-probe aggregation piece of it.
- Test this explicitly during mesh onboarding: intentionally delay the sidecar's own readiness (or simulate it) and confirm the Pod genuinely stays out of Service endpoints until both signals agree, rather than assuming correct behavior from configuration alone.
