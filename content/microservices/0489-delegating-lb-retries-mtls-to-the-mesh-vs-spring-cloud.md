---
card: microservices
gi: 489
slug: delegating-lb-retries-mtls-to-the-mesh-vs-spring-cloud
title: "Delegating LB/retries/mTLS to the mesh vs Spring Cloud"
---

## 1. What it is

This is the concrete migration decision that follows from [knowing where Spring Cloud ends and the mesh begins](0487-where-spring-cloud-ends-and-the-mesh-begins.md): for each of load balancing, retries, and mTLS, actually **turning off** the Spring Cloud mechanism and **delegating** that responsibility to the mesh, rather than leaving both active. This is a deliberate, auditable migration with a clear before-and-after, not a passive architectural observation.

## 2. Why & when

You perform this migration explicitly, service by service, once a mesh is confirmed running correctly in your cluster:

- **Leaving both layers active is the default if nobody acts, and it's the worst option.** Spring Cloud's client-side load balancer, retry logic, and TLS configuration don't disable themselves just because a mesh sidecar was injected — someone has to deliberately turn them off, or they keep running, duplicated and uncoordinated, indefinitely.
- **Doing this migration one concern at a time, one service at a time, keeps it safe and observable.** Disabling client-side load balancing, watching for issues, then disabling retries, then mTLS — rather than flipping everything at once — makes it far easier to attribute any regression to a specific, recent change.
- **The order matters: verify the mesh is actually providing equivalent behavior before removing the Spring Cloud equivalent.** Disabling application-level mTLS before confirming the mesh's mTLS is actually enforced would leave a window of *unencrypted* traffic — the mesh capability must be proven first, in each case.
- **You do this as a deliberate rollout across your service fleet**, typically starting with a low-risk service to validate the approach before applying it broadly — not as a single big-bang change across every service simultaneously.

## 3. Core concept

Think of decommissioning a building's old, individually-owned generators once a reliable central power grid connection is confirmed working — you don't rip out every generator the instant the grid cable is plugged in; you verify the grid supplies power reliably first, then decommission each generator deliberately, one at a time, watching for any issue at each step, keeping a way to fall back if something goes wrong.

Concretely, the migration for each concern follows the same shape:

1. **Confirm the mesh capability is actually active and correctly configured** for this specific service — e.g., verify mTLS is genuinely being enforced on this service's traffic before touching anything in the application.
2. **Disable the corresponding Spring Cloud mechanism** — remove or disable the client-side load balancer configuration, the retry annotations for baseline (non-business-aware) retries, or the application-level TLS configuration for internal calls.
3. **Verify behavior is unchanged (or improved) from the outside** — the service should behave identically to callers, just with the underlying mechanism now provided by the mesh instead of duplicated application code.
4. **Repeat for the next concern, and then the next service**, building confidence incrementally rather than making one large, hard-to-diagnose change.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A migration sequence: verify mesh capability, disable the Spring Cloud equivalent, verify behavior unchanged, repeat for the next concern">
  <rect x="20" y="70" width="140" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1. verify mesh capability active</text>

  <rect x="190" y="70" width="140" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="260" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">2. disable Spring Cloud equivalent</text>

  <rect x="360" y="70" width="140" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="430" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">3. verify behavior unchanged</text>

  <rect x="530" y="70" width="110" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="585" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">repeat, next concern</text>

  <line x1="160" y1="97" x2="190" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="330" y1="97" x2="360" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="500" y1="97" x2="530" y2="97" stroke="#8b949e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each concern migrates through the same sequence: verify, disable, verify again — one concern at a time.

## 5. Runnable example

Scenario: a migration controller stepping a service through disabling three Spring Cloud mechanisms one at a time, verifying the mesh equivalent at each step. We start with a basic single-concern migration, extend it to all three concerns in the correct order, then handle the hard case: a verification step failing partway through, which must halt the migration for that concern rather than proceeding to disable something the mesh isn't actually ready to replace.

### Level 1 — Basic

```java
// File: MigrateSingleConcern.java -- models migrating ONE concern
// (client-side load balancing) from Spring Cloud to the mesh: verify the
// mesh does it, THEN disable the Spring Cloud equivalent.
public class MigrateSingleConcern {
    static boolean meshLoadBalancingActive = true; // confirmed via mesh configuration inspection
    static boolean springCloudLoadBalancerEnabled = true; // the OLD mechanism, still on

    static boolean verifyMeshCapability(String capability, boolean active) {
        System.out.println("[migration] verifying mesh provides: " + capability + " -- " + (active ? "CONFIRMED" : "NOT ACTIVE"));
        return active;
    }

    static void disableSpringCloudMechanism(String mechanism) {
        springCloudLoadBalancerEnabled = false;
        System.out.println("[migration] disabled Spring Cloud mechanism: " + mechanism);
    }

    public static void main(String[] args) {
        if (verifyMeshCapability("client-side load balancing", meshLoadBalancingActive)) {
            disableSpringCloudMechanism("Spring Cloud LoadBalancer");
        }
        System.out.println("[state] springCloudLoadBalancerEnabled = " + springCloudLoadBalancerEnabled);
    }
}
```

How to run: `java MigrateSingleConcern.java`

`main` only calls `disableSpringCloudMechanism` *inside* the `if` guarding on `verifyMeshCapability`'s result — the Spring Cloud mechanism is never disabled unless the mesh's equivalent capability was confirmed active first, enforcing the correct verify-then-disable order for this single concern.

### Level 2 — Intermediate

```java
// File: MigrateAllThreeConcerns.java -- the SAME migration pattern, now
// EXTENDED across ALL THREE concerns (load balancing, retries, mTLS),
// each migrated independently in the SAME verify-then-disable order.
import java.util.*;

public class MigrateAllThreeConcerns {
    static Map<String, Boolean> meshCapabilities = Map.of(
        "load-balancing", true,
        "retries", true,
        "mtls", true
    );

    static Map<String, Boolean> springCloudMechanisms = new LinkedHashMap<>(Map.of(
        "load-balancing", true,
        "retries", true,
        "mtls", true
    ));

    static void migrateConcern(String concern) {
        boolean meshReady = meshCapabilities.getOrDefault(concern, false);
        System.out.println("[migration] " + concern + ": mesh capability active = " + meshReady);
        if (meshReady) {
            springCloudMechanisms.put(concern, false);
            System.out.println("[migration] " + concern + ": Spring Cloud mechanism DISABLED");
        } else {
            System.out.println("[migration] " + concern + ": SKIPPED, mesh not ready yet -- Spring Cloud mechanism stays ON");
        }
    }

    public static void main(String[] args) {
        for (String concern : List.of("load-balancing", "retries", "mtls")) {
            migrateConcern(concern);
        }
        System.out.println();
        System.out.println("[final state] Spring Cloud mechanisms still enabled: " + springCloudMechanisms);
    }
}
```

How to run: `java MigrateAllThreeConcerns.java`

`migrateConcern` is called once per concern, independently, using the same verify-then-disable logic each time — `springCloudMechanisms` tracks each concern's own on/off state separately, so this models three genuinely independent migration decisions rather than one all-or-nothing switch.

### Level 3 — Advanced

```java
// File: MigrateWithVerificationFailure.java -- the SAME per-concern
// migration, now handling the PRODUCTION-FLAVORED hard case: ONE
// concern's mesh capability is NOT actually confirmed active (mTLS isn't
// really enforced yet, perhaps still being rolled out). That concern's
// Spring Cloud mechanism MUST stay enabled -- disabling it anyway would
// leave a genuine security gap (unencrypted traffic). The OTHER two
// concerns, which ARE verified, must still migrate normally and
// independently.
import java.util.*;

public class MigrateWithVerificationFailure {
    static Map<String, Boolean> meshCapabilities = Map.of(
        "load-balancing", true,
        "retries", true,
        "mtls", false // NOT actually confirmed active yet -- still rolling out
    );

    static Map<String, Boolean> springCloudMechanisms = new LinkedHashMap<>();
    static List<String> migrationWarnings = new ArrayList<>();

    static void migrateConcern(String concern) {
        springCloudMechanisms.putIfAbsent(concern, true); // starts enabled
        boolean meshReady = meshCapabilities.getOrDefault(concern, false);
        System.out.println("[migration] " + concern + ": mesh capability active = " + meshReady);
        if (meshReady) {
            springCloudMechanisms.put(concern, false);
            System.out.println("[migration] " + concern + ": Spring Cloud mechanism DISABLED, delegated to mesh");
        } else {
            String warning = concern + ": mesh NOT confirmed ready -- Spring Cloud mechanism REMAINS ENABLED to avoid a coverage gap";
            migrationWarnings.add(warning);
            System.out.println("[migration] WARNING: " + warning);
        }
    }

    public static void main(String[] args) {
        for (String concern : List.of("load-balancing", "retries", "mtls")) {
            migrateConcern(concern);
        }

        System.out.println();
        System.out.println("[final state] Spring Cloud mechanism status: " + springCloudMechanisms);
        System.out.println("[migration] outstanding warnings requiring follow-up: " + migrationWarnings);
    }
}
```

How to run: `java MigrateWithVerificationFailure.java`

`meshCapabilities` deliberately sets `"mtls"` to `false`, modeling a mesh where mTLS enforcement isn't actually confirmed yet. When `migrateConcern("mtls")` runs, `meshReady` evaluates to `false`, so the `else` branch runs instead of disabling anything — `springCloudMechanisms.get("mtls")` stays `true` (still enabled), and a specific warning is recorded in `migrationWarnings` naming exactly which concern needs follow-up, while `"load-balancing"` and `"retries"`, both confirmed ready, migrate normally and independently in the same run.

## 6. Walkthrough

Trace `MigrateWithVerificationFailure.main` in order. **First**, the loop's first iteration calls `migrateConcern("load-balancing")`. `springCloudMechanisms.putIfAbsent(...)` initializes it to `true`, and `meshReady` reads `true` from `meshCapabilities`. The `if (meshReady)` branch runs: `springCloudMechanisms.put("load-balancing", false)` disables it, and the confirmation prints.

**Next**, the second iteration calls `migrateConcern("retries")`, behaving identically — `meshReady` is `true`, so it's disabled and delegated to the mesh, exactly like `load-balancing`.

**Then**, the third iteration calls `migrateConcern("mtls")`. This time `meshCapabilities.getOrDefault("mtls", false)` returns `false`, so `meshReady` is `false` — the `else` branch runs instead: a specific warning string is constructed, appended to `migrationWarnings`, and printed, while `springCloudMechanisms.put("mtls", ...)` is never called at all in this branch, meaning it retains the `true` value `putIfAbsent` set at the start of this same method call.

**After that**, the loop ends having processed all three concerns independently, with two migrated and one deliberately left in place.

**Finally**, `main` prints `springCloudMechanisms`, showing `load-balancing` and `retries` both `false` (delegated to the mesh) while `mtls` remains `true` (still Spring Cloud's responsibility) — and prints `migrationWarnings`, containing exactly one entry that clearly flags `mtls` as needing follow-up before that concern can safely migrate, ensuring the security-sensitive gap doesn't get silently missed.

```
[migration] load-balancing: mesh capability active = true
[migration] load-balancing: Spring Cloud mechanism DISABLED, delegated to mesh
[migration] retries: mesh capability active = true
[migration] retries: Spring Cloud mechanism DISABLED, delegated to mesh
[migration] mtls: mesh capability active = false
[migration] WARNING: mtls: mesh NOT confirmed ready -- Spring Cloud mechanism REMAINS ENABLED to avoid a coverage gap

[final state] Spring Cloud mechanism status: {load-balancing=false, retries=false, mtls=true}
[migration] outstanding warnings requiring follow-up: [mtls: mesh NOT confirmed ready -- Spring Cloud mechanism REMAINS ENABLED to avoid a coverage gap]
```

## 7. Gotchas & takeaways

> Disabling an application-level security mechanism (like mTLS configuration) based on an *assumption* that the mesh is already handling it, without explicit verification, can create a genuine security gap — a brief or ongoing window of unencrypted or unauthenticated traffic that's easy to miss because everything still "works" from a functional standpoint.
- Migrate one concern at a time and verify the mesh's capability is genuinely active *before* disabling the Spring Cloud equivalent — never the reverse order, and never both at once without individual verification.
- Security-sensitive concerns (mTLS) deserve the most conservative migration approach — when in doubt, leave the application-level mechanism active a little longer than strictly necessary rather than risk a coverage gap, exactly as the third concern's handling demonstrates.
- Track outstanding migration warnings explicitly, as `migrationWarnings` does — a migration that silently leaves some concerns unfinished, with no visible record of what's left, is easy to lose track of over time.
- This process pairs directly with [where Spring Cloud ends and the mesh begins](0487-where-spring-cloud-ends-and-the-mesh-begins.md) — that topic identifies *what* should move; this one is the concrete, careful *how* of actually making the move safely.
