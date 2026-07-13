---
card: microservices
gi: 183
slug: service-registration-self-vs-third-party
title: "Service registration (self vs third-party)"
---

## 1. What it is

Self-registration is a service instance registering itself directly with the [service registry](0182-service-registry-concept.md) as part of its own startup code — the instance knows about the registry and actively announces its own presence. Third-party registration is a separate component (a registrar, often integrated with the deployment platform itself, like Kubernetes) that observes instances starting and stopping and registers or deregisters them on the instance's behalf, without the instance's own code needing any awareness of the registry at all.

## 2. Why & when

Self-registration is simple and direct — the instance that knows its own address and health best is the one responsible for announcing it — but it couples every service's own codebase to a specific registry client library and its configuration, and it depends on the instance's own code running correctly and completing that registration step (a crash before registration completes means the instance never appears, even though the process is technically running). Third-party registration removes that coupling entirely: services contain no registry-specific code at all, and the registrar, watching the platform's own view of instance lifecycle, handles registration and deregistration reliably from outside, based on events the platform itself already tracks.

Use self-registration when the registry client integrates simply and the coupling is acceptable, particularly common in the Spring Cloud ecosystem (a Spring Boot app with Eureka client dependencies self-registers via configuration). Use third-party registration when service code should remain completely registry-agnostic, or when the deployment platform already has a superior, independent view of instance lifecycle — Kubernetes' own service discovery is fundamentally third-party registration, since pods themselves contain no Kubernetes-registry-specific registration code at all.

## 3. Core concept

Self-registration puts registry calls directly inside the service's own startup and shutdown lifecycle; third-party registration puts those same calls inside a separate registrar component that watches the platform's instance lifecycle events (container started, container stopped, health check failed) and translates them into registry operations, with the service itself remaining unaware the registry exists.

```java
// SELF-REGISTRATION: the service's OWN code calls the registry directly
@PostConstruct
void onStartup() {
    registryClient.register("order-service", myHost, myPort); // the SERVICE knows about the registry
}

// THIRD-PARTY REGISTRATION: a SEPARATE registrar watches the platform, the service knows NOTHING about it
class PlatformRegistrar {
    void onContainerStarted(ContainerEvent event) {
        registryClient.register(event.serviceName(), event.host(), event.port()); // the SERVICE'S OWN CODE never runs this
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Self-registration: the service instance calls the registry directly during its own startup. Third-party registration: a separate registrar watches platform lifecycle events and calls the registry on the instance's behalf, with the instance's own code containing no registry awareness" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Self-registration</text>
  <rect x="40" y="45" width="140" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="110" y="69" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service instance</text>
  <rect x="40" y="115" width="140" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="110" y="139" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Registry</text>
  <line x1="110" y1="85" x2="110" y2="113" stroke="#8b949e" marker-end="url(#arr64)"/>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Third-party registration</text>
  <rect x="380" y="30" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="450" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service instance</text>
  <text x="450" y="20" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(no registry code at all)</text>
  <rect x="380" y="100" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="450" y="122" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Registrar (watches)</text>
  <rect x="380" y="155" width="140" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="450" y="177" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Registry</text>
  <line x1="450" y1="65" x2="450" y2="98" stroke="#8b949e" stroke-dasharray="2,2" marker-end="url(#arr64)"/>
  <line x1="450" y1="135" x2="450" y2="153" stroke="#8b949e" marker-end="url(#arr64)"/>

  <defs>
    <marker id="arr64" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Self-registration calls the registry directly; third-party registration observes lifecycle events externally and calls the registry on the instance's behalf.

## 5. Runnable example

Scenario: an order-service instance startup that starts with self-registration logic embedded directly in the service's own code, refactors to third-party registration where an external registrar handles it instead, and finally demonstrates the key resilience difference — a service that crashes before completing its own self-registration versus a third-party registrar that reliably registers based on the platform's own observed lifecycle events, unaffected by the service's internal registration logic failing.

### Level 1 — Basic

```java
// File: SelfRegistration.java -- the SERVICE'S OWN startup code calls the
// registry directly; the registry client is a DEPENDENCY of the service itself.
public class SelfRegistration {
    static class ServiceRegistry {
        void register(String serviceName, String host, int port) {
            System.out.println("[registry] " + serviceName + " registered at " + host + ":" + port);
        }
    }

    static class OrderServiceApp {
        ServiceRegistry registryClient; // the SERVICE holds a direct reference to the registry client
        OrderServiceApp(ServiceRegistry registryClient) { this.registryClient = registryClient; }

        void onStartup() { // called as PART of the service's OWN startup lifecycle
            System.out.println("[order-service] starting up...");
            registryClient.register("order-service", "10.0.1.5", 8080); // the SERVICE calls the registry ITSELF
            System.out.println("[order-service] ready to serve traffic");
        }
    }

    public static void main(String[] args) {
        OrderServiceApp app = new OrderServiceApp(new ServiceRegistry());
        app.onStartup();
        System.out.println("The service's OWN code contains registry-specific logic and a dependency on the registry client.");
    }
}
```

**How to run:** `javac SelfRegistration.java && java SelfRegistration` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ThirdPartyRegistration.java -- a SEPARATE registrar watches platform
// lifecycle events; the SERVICE'S OWN code contains ZERO registry awareness.
public class ThirdPartyRegistration {
    static class ServiceRegistry {
        void register(String serviceName, String host, int port) {
            System.out.println("[registry] " + serviceName + " registered at " + host + ":" + port);
        }
    }

    // the SERVICE: contains ONLY business startup logic, NO registry code at all
    static class OrderServiceApp {
        void onStartup() {
            System.out.println("[order-service] starting up...");
            System.out.println("[order-service] ready to serve traffic");
            // NOTHING here calls a registry -- this class has NEVER heard of one
        }
    }

    // the REGISTRAR: a SEPARATE component that watches the PLATFORM's lifecycle events
    record ContainerStartedEvent(String serviceName, String host, int port) {}
    static class PlatformRegistrar {
        ServiceRegistry registry;
        PlatformRegistrar(ServiceRegistry registry) { this.registry = registry; }
        void onContainerStarted(ContainerStartedEvent event) { // triggered by the PLATFORM, not by OrderServiceApp
            System.out.println("[platform] observed container started: " + event.serviceName());
            registry.register(event.serviceName(), event.host(), event.port()); // the REGISTRAR calls the registry, NOT the service
        }
    }

    public static void main(String[] args) {
        OrderServiceApp app = new OrderServiceApp();
        app.onStartup(); // the SERVICE starts up, unaware of registration entirely

        // the PLATFORM, having observed the container start, notifies the registrar SEPARATELY
        PlatformRegistrar registrar = new PlatformRegistrar(new ServiceRegistry());
        registrar.onContainerStarted(new ContainerStartedEvent("order-service", "10.0.1.5", 8080));

        System.out.println("OrderServiceApp's code has NO registry dependency at all -- registration happened ENTIRELY externally.");
    }
}
```

**How to run:** `javac ThirdPartyRegistration.java && java ThirdPartyRegistration` (JDK 17+).

Expected output:
```
[order-service] starting up...
[order-service] ready to serve traffic
[platform] observed container started: order-service
[registry] order-service registered at 10.0.1.5:8080
OrderServiceApp's code has NO registry dependency at all -- registration happened ENTIRELY externally.
```

### Level 3 — Advanced

```java
// File: ResilienceComparisonOnCrash.java -- self-registration FAILS to register
// if the service crashes BEFORE its own registration code runs; third-party
// registration, based on the PLATFORM's own observed lifecycle, is UNAFFECTED by that.
public class ResilienceComparisonOnCrash {
    static class ServiceRegistry {
        void register(String serviceName, String host, int port) {
            System.out.println("[registry] " + serviceName + " registered at " + host + ":" + port);
        }
    }

    // SELF-REGISTRATION: a crash in the service's OWN startup, BEFORE its registration
    // line runs, means it NEVER registers -- even though the process itself is UP
    static class SelfRegisteringApp {
        ServiceRegistry registryClient;
        SelfRegisteringApp(ServiceRegistry registryClient) { this.registryClient = registryClient; }
        void onStartup(boolean simulateCrashBeforeRegistration) {
            System.out.println("[order-service, self-reg] starting up...");
            if (simulateCrashBeforeRegistration) {
                System.out.println("[order-service, self-reg] *** CRASHED before reaching registryClient.register() ***");
                return; // registration NEVER HAPPENS -- the process may still be technically alive, but is INVISIBLE to the registry
            }
            registryClient.register("order-service", "10.0.1.5", 8080);
        }
    }

    // THIRD-PARTY REGISTRATION: the platform observes the CONTAINER started,
    // independent of whatever the service's OWN internal startup code does or doesn't do
    record ContainerStartedEvent(String serviceName, String host, int port) {}
    static class PlatformRegistrar {
        ServiceRegistry registry;
        PlatformRegistrar(ServiceRegistry registry) { this.registry = registry; }
        void onContainerStarted(ContainerStartedEvent event) {
            System.out.println("[platform] container process IS running -- registering regardless of its internal startup logic");
            registry.register(event.serviceName(), event.host(), event.port());
        }
    }

    public static void main(String[] args) {
        ServiceRegistry registry = new ServiceRegistry();

        System.out.println("=== self-registration, service crashes BEFORE its registration line ===");
        new SelfRegisteringApp(registry).onStartup(true);
        System.out.println("Result: order-service is RUNNING but INVISIBLE to the registry -- traffic will never reach it.");

        System.out.println("\n=== third-party registration, SAME underlying crash scenario ===");
        // the platform observed the CONTAINER PROCESS starting -- this happens regardless of
        // whether the SERVICE's internal application code has a bug in its OWN startup path
        new PlatformRegistrar(registry).onContainerStarted(new ContainerStartedEvent("order-service", "10.0.1.5", 8080));
        System.out.println("Result: registration happened based on the PLATFORM's observation, independent of the service's internal code.");
    }
}
```

**How to run:** `javac ResilienceComparisonOnCrash.java && java ResilienceComparisonOnCrash` (JDK 17+).

Expected output:
```
=== self-registration, service crashes BEFORE its registration line ===
[order-service, self-reg] starting up...
[order-service, self-reg] *** CRASHED before reaching registryClient.register() ***
Result: order-service is RUNNING but INVISIBLE to the registry -- traffic will never reach it.

=== third-party registration, SAME underlying crash scenario ===
[platform] container process IS running -- registering regardless of its internal startup logic
[registry] order-service registered at 10.0.1.5:8080
Result: registration happened based on the PLATFORM's observation, independent of the service's internal code.
```

## 6. Walkthrough

1. **Level 1** — `OrderServiceApp` holds a `ServiceRegistry registryClient` field directly, and `onStartup` calls `registryClient.register(...)` as an explicit step in its own startup sequence — the service's code is directly coupled to the concept and API of the registry.
2. **Level 2, removing the coupling** — `OrderServiceApp` (in this version) contains no reference to any `ServiceRegistry` at all; its `onStartup` method does nothing but print startup messages.
3. **Level 2, the registrar as a separate, external observer** — `PlatformRegistrar.onContainerStarted` is triggered by `main` directly (standing in for a real platform's own lifecycle event system), and it, not `OrderServiceApp`, holds the `ServiceRegistry` reference and calls `register`.
4. **Level 2, the architectural difference made visible** — the final printed statement is directly verifiable from the code: `OrderServiceApp`'s class definition literally contains no `ServiceRegistry` field or method call anywhere, unlike Level 1's version.
5. **Level 3, the self-registration failure mode** — `SelfRegisteringApp.onStartup(true)` deliberately returns *before* reaching its `registryClient.register(...)` call, modeling a realistic crash (an exception in application initialization code, occurring before the registration step) — the process might still technically be running afterward (or might have crashed entirely), but either way, the registry was never told about it.
6. **Level 3, third-party registration's independence from that failure** — `PlatformRegistrar.onContainerStarted` is triggered based on the *platform's* observation that a container process started — a fact that is entirely independent of whatever bugs might exist in that container's internal application startup code; the registrar successfully registers the instance regardless.
7. **Level 3, why this matters in practice** — the comparison demonstrates a genuine resilience advantage: with self-registration, any bug or crash occurring in application code *before* the registration call means the instance never becomes discoverable, a silent failure mode that can be hard to diagnose (the process might appear "up" in basic monitoring while being invisible to service discovery); with third-party registration, the registrar's trigger is the platform's own, simpler, and more reliable signal ("did this container process start"), decoupling registration correctness from the potentially much more complex and failure-prone application startup logic running inside that container.

## 7. Gotchas & takeaways

> **Gotcha:** third-party registration's advantage (registering based on "did the process start" rather than "did the application finish initializing") can become a liability if the platform's signal is too coarse — a container that started successfully but whose application inside is still initializing (not yet ready to serve traffic) could be registered and receive traffic prematurely unless the third-party registrar also incorporates a proper readiness signal (a health check, not just a process-alive check) before registering, or shortly after, marking the instance as ready.

- Self-registration has a service instance call the registry directly as part of its own startup code, coupling the service's codebase to the registry client.
- Third-party registration has a separate registrar observe platform-level lifecycle events (container started/stopped) and register or deregister instances on their behalf, keeping the service's own code entirely registry-agnostic.
- Self-registration is vulnerable to the service's own startup code failing before the registration step completes, leaving a technically-running process invisible to the registry.
- Third-party registration is more resilient to this specific failure mode, since it depends on the platform's own, typically simpler and more reliable process-lifecycle signal rather than the potentially more complex application startup logic.
- Third-party registration needs to incorporate genuine readiness, not just process-alive status, or instances risk receiving traffic before they're actually ready to serve it.
