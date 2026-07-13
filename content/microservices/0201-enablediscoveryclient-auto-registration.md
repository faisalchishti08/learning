---
card: microservices
gi: 201
slug: enablediscoveryclient-auto-registration
title: "@EnableDiscoveryClient / auto-registration"
---

## 1. What it is

`@EnableDiscoveryClient` is the annotation that activates Spring Cloud's discovery integration on an application's main class, triggering automatic self-registration with whichever registry implementation ([Eureka](0196-spring-cloud-netflix-eureka-client.md), [Consul](0197-spring-cloud-consul-discovery.md), and others) is present on the classpath and configured — in modern Spring Cloud versions, this activation is often unnecessary to write explicitly, since Spring Boot's auto-configuration detects a discovery client dependency on the classpath and enables it automatically, without any annotation at all.

## 2. Why & when

Earlier Spring Cloud versions required `@EnableDiscoveryClient` explicitly on the application's main class to activate discovery integration, making the intent visible directly in the annotated code. As Spring Boot's auto-configuration mechanism matured, most discovery-client starters became capable of auto-activating themselves purely from the dependency's presence on the classpath, following Spring Boot's broader philosophy of "if the dependency is there and no explicit opt-out is configured, assume the developer wants it enabled" — reducing required boilerplate annotations while keeping the same underlying registration behavior.

Add `@EnableDiscoveryClient` explicitly when working with an older Spring Cloud version that requires it, or when the extra explicitness is valued for documentation purposes even if not strictly required by the specific starter in use. In modern Spring Cloud applications, simply adding the discovery-client starter dependency (`spring-cloud-starter-netflix-eureka-client`, for instance) is typically sufficient on its own, with auto-configuration handling activation.

## 3. Core concept

Once discovery is active (via the annotation, or via auto-configuration alone), the framework automatically performs self-registration on application startup — reading the instance's own network location and configured metadata, calling the registry's registration API, and beginning the heartbeat schedule — entirely without the application's own code calling any registration method directly.

```java
// EXPLICIT activation (older style, or when extra clarity is desired)
@SpringBootApplication
@EnableDiscoveryClient
public class OrderServiceApplication { ... }

// MODERN style: no annotation needed at all -- the dependency's PRESENCE is sufficient
@SpringBootApplication
public class OrderServiceApplication {
    // spring-cloud-starter-netflix-eureka-client on the classpath is ENOUGH --
    // auto-configuration detects it and activates registration automatically
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Older Spring Cloud versions require an explicit @EnableDiscoveryClient annotation to activate registration. Modern versions activate the identical registration behavior automatically, purely from the discovery-client dependency's presence on the classpath, with no annotation needed" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Explicit (older style)</text>
  <rect x="30" y="40" width="240" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@EnableDiscoveryClient</text>
  <text x="150" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">explicit annotation required</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Auto-configured (modern)</text>
  <rect x="360" y="40" width="240" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">dependency on classpath</text>
  <text x="480" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">activated automatically, no annotation</text>

  <text x="320" y="130" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">both result in IDENTICAL automatic registration behavior</text>

  <defs>
    <marker id="arr82" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Two activation styles, one identical underlying registration behavior once active.

## 5. Runnable example

Scenario: an order-service application that starts with fully manual, hand-written self-registration code (the baseline this activation replaces), models the explicit `@EnableDiscoveryClient` style triggering automatic registration, and finally demonstrates the modern classpath-presence-only activation style, confirming both approaches produce identical registration behavior with the second requiring even less code than the first.

### Level 1 — Basic

```java
// File: FullyManualRegistration.java -- the application EXPLICITLY calls
// registration itself, with NO framework activation of ANY kind.
public class FullyManualRegistration {
    static void registerWithRegistry(String appName, String host, int port) {
        System.out.println("[manual] registering " + appName + " at " + host + ":" + port);
    }

    public static void main(String[] args) {
        // the APPLICATION'S OWN main() method must remember to call this
        registerWithRegistry("order-service", "10.0.1.5", 8080);
        System.out.println("Registration is a MANUAL, explicit step written directly into application startup code.");
    }
}
```

**How to run:** `javac FullyManualRegistration.java && java FullyManualRegistration` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ExplicitAnnotationActivation.java -- models the OLDER style: an
// EXPLICIT @EnableDiscoveryClient-equivalent annotation TRIGGERS automatic
// registration -- the APPLICATION's own code contains NO registration call.
import java.lang.annotation.*;

public class ExplicitAnnotationActivation {
    @Retention(RetentionPolicy.RUNTIME) @interface EnableDiscoveryClient {} // stands in for the REAL annotation

    // simulates the FRAMEWORK's behavior: SCANNING for this annotation and
    // AUTOMATICALLY performing registration if found -- the application class
    // itself contains NO explicit registration call
    static void frameworkStartupSequence(Class<?> appClass, String appName, String host, int port) {
        boolean discoveryEnabled = appClass.isAnnotationPresent(EnableDiscoveryClient.class);
        System.out.println("Framework scanning " + appClass.getSimpleName() + " for @EnableDiscoveryClient: found=" + discoveryEnabled);
        if (discoveryEnabled) {
            System.out.println("  [framework, automatic] registering " + appName + " at " + host + ":" + port);
        }
    }

    @EnableDiscoveryClient
    static class OrderServiceApplication { /* NO registration code anywhere in this class */ }

    public static void main(String[] args) {
        frameworkStartupSequence(OrderServiceApplication.class, "order-service", "10.0.1.5", 8080);
        System.out.println("OrderServiceApplication contains ZERO registration code -- the ANNOTATION triggered the FRAMEWORK to do it automatically.");
    }
}
```

**How to run:** `javac ExplicitAnnotationActivation.java && java ExplicitAnnotationActivation` (JDK 17+).

Expected output:
```
Framework scanning OrderServiceApplication for @EnableDiscoveryClient: found=true
  [framework, automatic] registering order-service at 10.0.1.5:8080
OrderServiceApplication contains ZERO registration code -- the ANNOTATION triggered the FRAMEWORK to do it automatically.
```

### Level 3 — Advanced

```java
// File: ClasspathPresenceActivation.java -- the MODERN style: registration
// activates AUTOMATICALLY based purely on a DEPENDENCY's presence, with NO
// annotation required AT ALL -- and can be EXPLICITLY DISABLED if genuinely unwanted.
import java.util.*;

public class ClasspathPresenceActivation {
    // simulates a "classpath" -- the set of dependencies present in a real build
    static Set<String> simulatedClasspath = new HashSet<>();

    // simulates Spring Boot's auto-configuration: checks for the dependency's
    // PRESENCE, and for an EXPLICIT opt-out property, WITHOUT needing any annotation
    static void frameworkAutoConfiguration(String appName, String host, int port, boolean explicitlyDisabled) {
        boolean discoveryClientOnClasspath = simulatedClasspath.contains("spring-cloud-starter-netflix-eureka-client");
        boolean shouldActivate = discoveryClientOnClasspath && !explicitlyDisabled;

        System.out.println("Discovery client dependency on classpath: " + discoveryClientOnClasspath + ", explicitly disabled: " + explicitlyDisabled);
        if (shouldActivate) {
            System.out.println("  [auto-configuration] registering " + appName + " at " + host + ":" + port + " -- ZERO annotations needed");
        } else {
            System.out.println("  [auto-configuration] discovery NOT activated");
        }
    }

    public static void main(String[] args) {
        System.out.println("=== scenario 1: dependency present, no opt-out ===");
        simulatedClasspath.add("spring-cloud-starter-netflix-eureka-client");
        frameworkAutoConfiguration("order-service", "10.0.1.5", 8080, false);

        System.out.println("\n=== scenario 2: dependency present, but EXPLICITLY disabled via configuration ===");
        frameworkAutoConfiguration("order-service", "10.0.1.5", 8080, true); // spring.cloud.discovery.enabled=false, e.g.

        System.out.println("\n=== scenario 3: NO discovery dependency on classpath at all ===");
        simulatedClasspath.clear();
        frameworkAutoConfiguration("order-service", "10.0.1.5", 8080, false);

        System.out.println("\nNo @EnableDiscoveryClient annotation appeared ANYWHERE in this file -- the DEPENDENCY's presence (plus the absence of an opt-out) was the ONLY signal needed.");
    }
}
```

**How to run:** `javac ClasspathPresenceActivation.java && java ClasspathPresenceActivation` (JDK 17+).

Expected output:
```
=== scenario 1: dependency present, no opt-out ===
Discovery client dependency on classpath: true, explicitly disabled: false
  [auto-configuration] registering order-service at 10.0.1.5:8080 -- ZERO annotations needed

=== scenario 2: dependency present, but EXPLICITLY disabled via configuration ===
Discovery client dependency on classpath: true, explicitly disabled: true
  [auto-configuration] discovery NOT activated

=== scenario 3: NO discovery dependency on classpath at all ===
Discovery client dependency on classpath: false, explicitly disabled: false
  [auto-configuration] discovery NOT activated

No @EnableDiscoveryClient annotation appeared ANYWHERE in this file -- the DEPENDENCY's presence (plus the absence of an opt-out) was the ONLY signal needed.
```

## 6. Walkthrough

1. **Level 1** — `main` explicitly calls `registerWithRegistry(...)` directly, meaning registration is entirely dependent on this specific line of code existing and being reachable in the application's startup path — the baseline manual approach.
2. **Level 2, the annotation as a scannable marker** — `EnableDiscoveryClient` (the local stand-in for the real annotation) is applied to `OrderServiceApplication`, and `frameworkStartupSequence` uses reflection (`isAnnotationPresent`) to detect it, exactly mirroring how Spring's component scanning discovers and reacts to annotations present on application classes.
3. **Level 2, the application class containing no registration logic** — `OrderServiceApplication`'s body is empty (the comment makes this explicit); the actual registration call happens inside `frameworkStartupSequence`, representing framework-internal code triggered by finding the annotation, not application code.
4. **Level 2, the demonstrated automation** — the printed output shows the framework's scan finding the annotation and then automatically performing registration, all without `OrderServiceApplication` itself containing a single line related to the registry.
5. **Level 3, classpath presence as the sole trigger** — `frameworkAutoConfiguration` checks `simulatedClasspath.contains(...)` rather than looking for any annotation at all, modeling how modern Spring Boot auto-configuration activates discovery-client behavior purely based on which dependencies are present in the build.
6. **Level 3, the explicit opt-out path** — scenario 2 keeps the dependency present but sets `explicitlyDisabled = true` (representing a configuration property like `spring.cloud.discovery.enabled: false`), and the auto-configuration correctly respects this override, refusing to activate registration even though the dependency alone would normally trigger it.
7. **Level 3, the absence-of-dependency case and the overall conclusion** — scenario 3 clears the classpath entirely, and registration correctly doesn't activate since there's no discovery-client dependency present to trigger it at all; the final comment ties the three scenarios together — no annotation appeared anywhere in this file, yet registration behavior was correctly and predictably determined purely by dependency presence combined with an optional explicit override, which is precisely how modern Spring Cloud applications activate discovery integration without needing to write `@EnableDiscoveryClient` at all.

## 7. Gotchas & takeaways

> **Gotcha:** relying on implicit, classpath-presence-based activation means a dependency added transitively (pulled in indirectly by some other library, not deliberately added by the team) can silently activate discovery client behavior and trigger real registration calls to a registry the team never intended to register with — reviewing the actual dependency tree periodically (not just direct, explicitly-added dependencies) is worth doing specifically because this activation mechanism responds to *any* qualifying dependency on the classpath, direct or transitive.

- `@EnableDiscoveryClient` activates Spring Cloud's automatic self-registration behavior; in modern Spring Cloud versions, this activation often happens automatically based purely on the discovery-client starter dependency's presence on the classpath, with no annotation required.
- Both activation styles produce identical underlying registration behavior: automatic self-registration, heartbeat scheduling, and registry-facing API calls, entirely without application code calling any registration method directly.
- Use explicit `@EnableDiscoveryClient` when working with an older Spring Cloud version that requires it, or for documentation clarity even when not strictly necessary.
- Modern applications typically need only the appropriate starter dependency added to activate discovery integration automatically, following Spring Boot's broader auto-configuration philosophy.
- Because activation can be triggered by a dependency's mere presence (including transitively-pulled-in dependencies), periodically reviewing the actual dependency tree helps avoid unintentional discovery-client activation from a library the team didn't deliberately add for that purpose.
