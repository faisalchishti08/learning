---
card: microservices
gi: 488
slug: running-spring-boot-services-inside-a-mesh
title: "Running Spring Boot services inside a mesh"
---

## 1. What it is

Running a Spring Boot service inside a service mesh means the application's container is deployed with a [sidecar proxy](0479-sidecar-proxy-envoy.md) injected into the same Pod, and several Spring Boot-specific behaviors need to be checked for compatibility with that setup — [graceful shutdown](0475-spring-boot-graceful-shutdown-for-rolling-deploys.md) ordering relative to the sidecar's own lifecycle, [health probe](0473-spring-boot-actuator-liveness-readiness-probes-for-kubernete.md) configuration accounting for the sidecar's presence, and port configuration so the sidecar can correctly intercept the application's traffic. None of this requires application code changes, but it does require deliberate Pod-level configuration.

## 2. Why & when

You need to think through these specifics whenever a Spring Boot service is deployed into a mesh-enabled Kubernetes cluster, because the sidecar's presence introduces real ordering and configuration concerns:

- **Sidecar startup and shutdown ordering can break the application if not handled correctly.** If the application container starts before its sidecar is ready to intercept traffic, early outbound calls can fail; if the sidecar shuts down before the application finishes its own [graceful shutdown](0475-spring-boot-graceful-shutdown-for-rolling-deploys.md) drain, in-flight requests can fail at the very last moment of an otherwise-clean shutdown.
- **Health probes need to account for the sidecar, not just the application.** A readiness probe hitting the application directly might report "ready" before the sidecar has actually finished establishing its own connections and is ready to route traffic correctly — Kubernetes' native sidecar container support (or careful probe configuration) addresses this.
- **The mesh needs to actually be able to intercept the application's traffic**, which depends on the application listening on expected ports and not doing anything unusual (like binding directly to a specific IP that bypasses the redirection rules) that would let traffic slip past the sidecar.
- **You address these specifics once, as part of onboarding a service onto the mesh** — they're a one-time Pod/deployment configuration concern, not something that needs revisiting on every code change afterward.

## 3. Core concept

Think of a stage performance where a spotlight operator (the sidecar) needs to be in position and ready *before* the performer (the application) walks on stage, and needs to stay in position until the performer has fully exited *after* their final bow — if the spotlight arrives late or leaves early, the performance looks broken from the audience's perspective, even though the performer themselves did nothing wrong.

Concretely, the specific coordination points:

1. **Startup ordering**: newer Kubernetes versions support native "sidecar containers" (an `initContainers` entry marked to run for the Pod's whole lifetime) that guarantee the sidecar starts and becomes ready *before* the application container starts — avoiding a window where the application is up but its outbound calls fail because the sidecar isn't ready yet.
2. **Shutdown ordering**: the sidecar must remain active until the application's own [graceful shutdown](0475-spring-boot-graceful-shutdown-for-rolling-deploys.md) drain completes — if the sidecar exits first, in-flight requests the application is still trying to finish (or receive) lose their network path entirely.
3. **Health probe configuration**: readiness probes should generally reflect the *combined* readiness of the application and its ability to actually communicate through the mesh, not just the application process being up in isolation.
4. **Port and traffic interception**: the application should listen on standard, expected ports so the mesh's traffic redirection rules correctly capture its inbound and outbound calls — application code generally doesn't need changes here, but non-standard networking choices can break mesh interception.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A correct Pod lifecycle: the sidecar starts before the app, and stays running until the app's graceful shutdown drain fully completes" >
  <line x1="40" y1="100" x2="620" y2="100" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="60" y="30" width="220" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="170" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">sidecar: starts and becomes ready FIRST</text>

  <rect x="300" y="130" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="410" y="155" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">app container: starts AFTER sidecar ready</text>

  <rect x="60" y="130" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="155" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">sidecar stays up during app's graceful drain</text>

  <text x="330" y="190" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">sidecar: up first, down last -- brackets the application's own lifecycle</text>
</svg>

The sidecar's lifecycle brackets the application's own — up before it starts, still up while it drains on shutdown.

## 5. Runnable example

Scenario: a Pod lifecycle coordinator managing sidecar-then-app startup and app-then-sidecar shutdown ordering. We start with a basic incorrect ordering (the problem), extend it to correct startup sequencing, then handle the hard case: correct shutdown sequencing where the sidecar must outlive the application's own graceful drain.

### Level 1 — Basic

```java
// File: WrongStartupOrder.java -- models the PROBLEM: the application
// container starting BEFORE its sidecar is ready, causing early outbound
// calls to fail because there's nothing yet to intercept and route them.
public class WrongStartupOrder {
    static boolean sidecarReady = false;

    static void startAppContainer() {
        System.out.println("[app container] starting immediately, not waiting for sidecar");
        // App tries an outbound call right at startup.
        if (!sidecarReady) {
            System.out.println("[app container] FAILED: outbound call has no sidecar to route through yet");
        } else {
            System.out.println("[app container] outbound call succeeded via sidecar");
        }
    }

    static void startSidecar() {
        System.out.println("[sidecar] starting...");
        sidecarReady = true;
        System.out.println("[sidecar] ready");
    }

    public static void main(String[] args) {
        // WRONG order: app starts before sidecar is even asked to start.
        startAppContainer();
        startSidecar();
    }
}
```

How to run: `java WrongStartupOrder.java`

`startAppContainer` runs and checks `sidecarReady` before `startSidecar` has even been called — `sidecarReady` is still `false` at that point, so the application's simulated outbound call fails, directly modeling the real-world failure mode of an application container starting before its sidecar is ready to route traffic.

### Level 2 — Intermediate

```java
// File: CorrectStartupOrder.java -- the SAME lifecycle, now with CORRECT
// ordering: the sidecar starts and becomes ready FIRST, and the app
// container only starts AFTER that -- exactly like Kubernetes' native
// sidecar container support guarantees.
public class CorrectStartupOrder {
    static boolean sidecarReady = false;

    static void startSidecar() {
        System.out.println("[sidecar] starting...");
        sidecarReady = true;
        System.out.println("[sidecar] ready -- can now intercept and route traffic");
    }

    static void startAppContainer() {
        if (!sidecarReady) {
            throw new IllegalStateException("app container must not start before the sidecar is ready");
        }
        System.out.println("[app container] starting -- sidecar already ready");
        System.out.println("[app container] outbound call succeeded via sidecar");
    }

    public static void main(String[] args) {
        // CORRECT order: sidecar first, app container only after it's confirmed ready.
        startSidecar();
        startAppContainer();
    }
}
```

How to run: `java CorrectStartupOrder.java`

`startAppContainer` now begins with a defensive check — `if (!sidecarReady) throw ...` — that would catch the wrong-order bug immediately if it ever recurred. `main` calls `startSidecar()` first, setting `sidecarReady = true`, and only then calls `startAppContainer()`, which passes its own check and proceeds to a successful simulated outbound call, correctly modeling Kubernetes' native sidecar container ordering guarantee.

### Level 3 — Advanced

```java
// File: CorrectShutdownOrder.java -- the SAME correctly-ordered startup,
// now handling the PRODUCTION-FLAVORED hard case: SHUTDOWN ordering. The
// sidecar must stay running until the app's OWN graceful shutdown drain
// (in-flight requests finishing) has FULLY completed -- if the sidecar
// exits first, in-flight requests lose their network path mid-drain,
// even though the app itself was shutting down correctly.
import java.util.concurrent.*;

public class CorrectShutdownOrder {
    static volatile boolean sidecarRunning = false;

    static void startSidecar() {
        sidecarRunning = true;
        System.out.println("[sidecar] started and ready");
    }

    static void stopSidecar() {
        sidecarRunning = false;
        System.out.println("[sidecar] stopped");
    }

    // Simulates the app's graceful shutdown drain: an in-flight request finishing.
    static void appGracefulShutdownDrain(ExecutorService inFlightRequests) throws InterruptedException {
        System.out.println("[app] SIGTERM received -- draining in-flight requests before exiting");
        inFlightRequests.shutdown();
        boolean finished = inFlightRequests.awaitTermination(300, TimeUnit.MILLISECONDS);
        System.out.println("[app] drain complete: " + finished);
    }

    public static void main(String[] args) throws InterruptedException {
        startSidecar();

        ExecutorService inFlightRequests = Executors.newFixedThreadPool(2);
        inFlightRequests.submit(() -> {
            System.out.println("[app] handling in-flight request, needs the sidecar to send its response");
            try { Thread.sleep(150); } catch (InterruptedException ignored) {}
            if (!sidecarRunning) {
                System.out.println("[app] FAILED to send response -- sidecar already stopped mid-drain!");
            } else {
                System.out.println("[app] response sent successfully via sidecar");
            }
        });

        Thread.sleep(20); // let the in-flight request actually start
        System.out.println("[shutdown sequence] SIGTERM arrives for the Pod");

        // CORRECT order: app drains FIRST, sidecar is stopped only AFTER the drain completes.
        appGracefulShutdownDrain(inFlightRequests);
        stopSidecar();

        System.out.println("[shutdown sequence] Pod fully terminated, in the correct order");
    }
}
```

How to run: `java CorrectShutdownOrder.java`

`appGracefulShutdownDrain` is called and fully completes — including `awaitTermination` blocking until the in-flight request's thread finishes — *before* `stopSidecar()` is ever called. The in-flight request's own logic checks `sidecarRunning` partway through its simulated work; because `stopSidecar()` hasn't run yet at that point, `sidecarRunning` is still `true`, so the response is reported as sent successfully, exactly matching the guarantee that the sidecar must outlive the application's own graceful drain.

## 6. Walkthrough

Trace `CorrectShutdownOrder.main` in order. **First**, `startSidecar()` runs, setting `sidecarRunning = true`. Then a thread pool is created and one task is submitted, representing an in-flight request the application is actively handling — this task begins running concurrently, sleeping `150ms` to simulate real work, and it will check `sidecarRunning` right after that sleep completes.

**Next**, after a brief `20ms` pause to let that task actually start, the simulated `SIGTERM` arrives, and `appGracefulShutdownDrain(inFlightRequests)` is called. Inside it, `inFlightRequests.shutdown()` stops the pool from accepting *new* tasks (there are none pending anyway), and `awaitTermination(300, TimeUnit.MILLISECONDS)` blocks, waiting for the already-running in-flight task to finish.

**Then**, at around the `150ms` mark (well within the `300ms` await window), the in-flight task's sleep completes, and it checks `sidecarRunning`. Since `stopSidecar()` has not been called yet — the program is still inside `appGracefulShutdownDrain`, which hasn't returned — `sidecarRunning` is still `true`, so the task prints the success message.

**After that**, `awaitTermination` returns `true` (the pool terminated within the deadline), `appGracefulShutdownDrain` prints its completion message, and the method returns control back to `main`.

**Finally**, only now, after the drain has fully and successfully completed, does `main` call `stopSidecar()`, setting `sidecarRunning = false` — by this point, no in-flight work depends on the sidecar being up anymore, so stopping it here causes no problem at all, and the final termination message confirms the whole sequence completed in the correct order.

```
[sidecar] started and ready
[app] handling in-flight request, needs the sidecar to send its response
[shutdown sequence] SIGTERM arrives for the Pod
[app] SIGTERM received -- draining in-flight requests before exiting
[app] response sent successfully via sidecar
[app] drain complete: true
[sidecar] stopped
[shutdown sequence] Pod fully terminated, in the correct order
```

## 7. Gotchas & takeaways

> Sidecars stopping before the application finishes draining is a well-known, historically common failure mode in mesh-enabled Kubernetes deployments — it produces exactly the kind of last-second, hard-to-reproduce request failures that are miserable to debug, because the application's own shutdown logic looks completely correct in isolation and the actual cause is a Pod-level ordering problem, not application code.
- Kubernetes' native sidecar container support (an `initContainers` entry with `restartPolicy: Always`) directly solves the startup-ordering half of this problem — check whether your cluster's Kubernetes version and mesh support it before reaching for older, more manual workarounds.
- The shutdown-ordering half often needs explicit attention even with native sidecar support — confirm your specific mesh's sidecar honors `preStop` hooks or an equivalent mechanism to delay its own termination until the application signals its drain is complete.
- None of this requires changing the Spring Boot application's own business logic — it's entirely Pod-level and deployment-level configuration, which is exactly why it's easy to overlook when a team is focused on application code.
- Test this specific ordering deliberately during mesh onboarding — trigger a rolling deployment under real (or realistic simulated) load and confirm zero request failures occur during the transition, rather than assuming correct configuration based on reading documentation alone.
