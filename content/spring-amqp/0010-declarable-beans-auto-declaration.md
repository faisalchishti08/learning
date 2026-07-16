---
card: spring-amqp
gi: 10
slug: declarable-beans-auto-declaration
title: "Declarable beans & auto-declaration"
---

## 1. What it is

`Declarable` is the common interface `Queue`, `Exchange`, and `Binding` all implement, marking them as things `RabbitAdmin` should discover and declare automatically. Auto-declaration is the behavior this enables: by default, `RabbitAdmin` listens for the application context's refresh event and automatically declares every `Declarable` bean it finds, with no explicit wiring required beyond simply defining the beans — this is what makes cards 0008 and 0009's examples work without any extra "please declare these now" step anywhere in application code.

## 2. Why & when

Understanding `Declarable` and auto-declaration specifically matters for controlling exactly what gets created automatically and when:

- **Selectively opting a resource out of auto-declaration** — `Declarable` exposes a `shouldDeclare()` flag; setting it false on a bean means that bean exists as a Spring-managed object (useful for referencing its name or properties elsewhere in configuration) without `RabbitAdmin` actually creating it on the broker, useful when a queue is intentionally managed by a separate process.
- **Scoping which broker(s) a declaration applies to** — in a multi-broker setup, `Declarable` supports associating a resource with specific named `RabbitAdmin` instances via `setDeclaringAdmins(...)`, so a queue meant only for a secondary broker doesn't get mistakenly declared against the primary one.
- **Understanding startup ordering and timing** — because auto-declaration happens in response to a context-refresh event, knowing this timing matters when diagnosing why a bean that looks correctly declared doesn't yet exist on the broker at some other bean's own initialization time (a classic startup-ordering pitfall).

## 3. Core concept

Think of `Declarable` as a nametag every `Queue`, `Exchange`, and `Binding` bean wears, marking it as something the facilities crew (`RabbitAdmin`) should notice and act on during their move-in-day walkthrough (the context-refresh event). Most beans keep their nametag's "please set me up" flag turned on by default, but a bean can flip that flag off — still wearing the nametag, still recognized as belonging to this category of object, but explicitly telling the crew "skip this one, someone else is already handling its physical setup."

```java
@Bean
public Queue managedElsewhereQueue() {
    Queue queue = new Queue("externallyManagedQueue", true);
    queue.setShouldDeclare(false); // exists as a bean for reference, but RabbitAdmin won't create it
    return queue;
}

@Bean
public Queue normalQueue() {
    return new Queue("orderProcessingQueue", true); // shouldDeclare defaults to true -- auto-declared
}
```

Both are valid `Declarable` beans the context manages, but only one actually gets created on the broker automatically.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RabbitAdmin listens for the application context refresh event and iterates every Declarable bean, declaring each one whose shouldDeclare flag is true and skipping those explicitly opted out" >
  <rect x="20" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Context refresh event</text>

  <line x1="200" y1="42" x2="270" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a12)"/>
  <rect x="270" y="20" width="140" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">RabbitAdmin scans</text>

  <line x1="410" y1="35" x2="480" y2="20" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a12)"/>
  <rect x="480" y="0" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="24" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">shouldDeclare=true -&gt; declared</text>

  <line x1="410" y1="50" x2="480" y2="80" stroke="#8b949e" stroke-width="1.2"/>
  <rect x="480" y="65" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="550" y="89" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">shouldDeclare=false -&gt; skipped</text>
</svg>

The flag on each `Declarable` bean determines its fate during the automatic scan.

## 5. Runnable example

The scenario: selectively auto-declaring some resources while skipping externally-managed ones, simulated with a plain in-memory model standing in for `Declarable`'s `shouldDeclare` flag and `RabbitAdmin`'s scanning behavior (no real Spring application context needed to demonstrate the opt-out mechanism), starting with a basic scan declaring everything, then adding the opt-out flag, then adding multi-admin scoping to show how a resource can be restricted to a specific named admin in a multi-broker setup.

### Level 1 — Basic

```java
// DeclarableDemo.java
import java.util.*;

public class DeclarableDemo {
    static class DeclarableResource {
        String name;
        DeclarableResource(String name) { this.name = name; }
    }

    // Stand-in for RabbitAdmin's context-refresh-triggered scan: declares everything found.
    static void declareAll(List<DeclarableResource> resources) {
        for (DeclarableResource r : resources) {
            System.out.println("Declared: " + r.name);
        }
    }

    public static void main(String[] args) {
        List<DeclarableResource> resources = List.of(
            new DeclarableResource("orderProcessingQueue"),
            new DeclarableResource("order.exchange"));
        declareAll(resources);
    }
}
```

How to run: `java DeclarableDemo.java`. Expected output: both resources print as declared — the default auto-declaration behavior with no opt-outs configured.

### Level 2 — Intermediate

```java
// DeclarableDemo.java
import java.util.*;

public class DeclarableDemo {
    static class DeclarableResource {
        String name;
        boolean shouldDeclare = true; // defaults to true, matching real Declarable's default
        DeclarableResource(String name) { this.name = name; }
    }

    // Real-world concern: some Declarable beans exist purely for reference (their name is used
    // elsewhere in config) without RabbitAdmin actually creating them -- perhaps because a
    // separate provisioning process or a different application owns that resource's lifecycle.
    static void declareAll(List<DeclarableResource> resources) {
        for (DeclarableResource r : resources) {
            if (r.shouldDeclare) {
                System.out.println("Declared: " + r.name);
            } else {
                System.out.println("Skipped (shouldDeclare=false): " + r.name);
            }
        }
    }

    public static void main(String[] args) {
        DeclarableResource managedElsewhere = new DeclarableResource("externallyManagedQueue");
        managedElsewhere.shouldDeclare = false;

        List<DeclarableResource> resources = List.of(
            new DeclarableResource("orderProcessingQueue"),
            managedElsewhere);

        declareAll(resources);
    }
}
```

How to run: `java DeclarableDemo.java`. Expected output: `Declared: orderProcessingQueue` then `Skipped (shouldDeclare=false): externallyManagedQueue` — the opted-out resource remains a recognized Spring bean (its name is still available for other configuration to reference) without `RabbitAdmin` attempting to create it on the broker.

### Level 3 — Advanced

```java
// DeclarableDemo.java
import java.util.*;

public class DeclarableDemo {
    static class DeclarableResource {
        String name;
        boolean shouldDeclare = true;
        Set<String> restrictedToAdmins = new HashSet<>(); // empty = applies to every admin
        DeclarableResource(String name) { this.name = name; }
    }

    // Production concern: in a multi-broker setup, each RabbitAdmin instance is scoped to one
    // broker connection. A resource should only be declared by the admin(s) it's actually meant
    // for -- declaring a secondary-broker-only queue against the primary broker's admin would be
    // a genuine misconfiguration.
    static void declareForAdmin(String adminName, List<DeclarableResource> resources) {
        for (DeclarableResource r : resources) {
            if (!r.shouldDeclare) continue;
            boolean appliesToThisAdmin = r.restrictedToAdmins.isEmpty() || r.restrictedToAdmins.contains(adminName);
            if (appliesToThisAdmin) {
                System.out.println("[" + adminName + "] declared: " + r.name);
            }
        }
    }

    public static void main(String[] args) {
        DeclarableResource primaryQueue = new DeclarableResource("orderProcessingQueue"); // applies everywhere

        DeclarableResource secondaryOnlyQueue = new DeclarableResource("analyticsEventsQueue");
        secondaryOnlyQueue.restrictedToAdmins.add("secondaryBrokerAdmin");

        List<DeclarableResource> allResources = List.of(primaryQueue, secondaryOnlyQueue);

        System.out.println("-- primaryBrokerAdmin's scan --");
        declareForAdmin("primaryBrokerAdmin", allResources);

        System.out.println("-- secondaryBrokerAdmin's scan --");
        declareForAdmin("secondaryBrokerAdmin", allResources);
    }
}
```

How to run: `java DeclarableDemo.java`. Expected output: `primaryBrokerAdmin`'s scan declares only `orderProcessingQueue` (since `analyticsEventsQueue` is restricted to the other admin); `secondaryBrokerAdmin`'s scan declares both `orderProcessingQueue` (unrestricted, applies everywhere) and `analyticsEventsQueue` (explicitly scoped to it) — demonstrating how a resource restricted to a specific admin avoids being mistakenly declared against the wrong broker in a multi-broker application.

## 6. Walkthrough

Trace the full auto-declaration sequence from context startup to selective, scoped declaration.

1. **Bean definitions loaded**: as the Spring application context initializes, every `Queue`, `Exchange`, and `Binding` bean gets constructed and registered — at this point, nothing has been declared against any actual broker yet, since bean construction and broker declaration are separate steps.
2. **Context refresh event fires**: once the application context finishes its initial setup, it publishes a context-refreshed event, which every registered `RabbitAdmin` instance is listening for.
3. **RabbitAdmin scans for Declarable beans**: each `RabbitAdmin` iterates over every bean in the context implementing `Declarable`, checking two things per resource — whether `shouldDeclare()` is true, and (in a multi-admin setup) whether this particular resource is scoped to this particular admin or applies universally.
4. **Selective declaration**: for each resource passing both checks, the admin issues the corresponding broker command to create it if missing; resources failing either check are skipped by this particular admin, whether because they're opted out entirely (`shouldDeclare=false`) or scoped to a different admin.
5. **Skipped-but-present beans remain useful**: a bean with `shouldDeclare=false` still exists as a fully valid Spring bean — other configuration can still reference its `getName()` or other properties (for wiring a listener container to consume from it, for instance) even though `RabbitAdmin` never created it itself, since some other process is presumably responsible for its actual existence on the broker.
6. **Multi-admin scoping prevents cross-broker mistakes**: in an application with more than one `RabbitAdmin` (one per distinct broker connection), scoping resources explicitly to the admin(s) they belong to is what prevents, say, a queue meant only for an analytics-specific secondary broker from being mistakenly declared against the primary transactional broker as well.

```
context refresh event fires
  -> each RabbitAdmin scans all Declarable beans in the context
    for each resource:
      shouldDeclare == false?              -> skip
      restrictedToAdmins excludes this one? -> skip
      otherwise                             -> declare on this admin's broker
```

## 7. Gotchas & takeaways

> **Gotcha:** auto-declaration is triggered by the context-refresh event, which fires once during normal application startup — a `Declarable` bean registered dynamically *after* that point (through some unusual programmatic bean-registration mechanism) will not automatically get declared unless the application explicitly triggers `RabbitAdmin.initialize()` again itself; the "just define the bean and it gets created" convenience specifically depends on normal, startup-time bean registration.

- `Declarable`'s `shouldDeclare` flag defaults to `true`, meaning auto-declaration is the default, opt-out behavior — most applications never need to touch this flag at all, and reaching for it is specifically for resources intentionally managed by something other than this application's own `RabbitAdmin`.
- Multi-admin scoping (`setDeclaringAdmins(...)`) only becomes relevant once an application genuinely has more than one `RabbitAdmin` bean, which itself only happens in multi-broker setups — a single-broker application (the overwhelming majority) never needs to think about this at all.
- Because declaration is idempotent (card 0008) and happens automatically for every `Declarable` bean by default, the practical day-to-day experience for most Spring AMQP applications is simply "define the `Queue`/`Exchange`/`Binding` beans you need, and they exist on the broker by the time your application finishes starting" — the mechanics covered in this card mostly matter for the less common cases where that default needs adjusting.
- When troubleshooting a resource that "should have been declared but wasn't," checking `shouldDeclare` and any admin-scoping configuration on that specific bean is a reasonable first diagnostic step, ahead of assuming something more exotic (a broker permissions issue, a network problem) is at fault.
