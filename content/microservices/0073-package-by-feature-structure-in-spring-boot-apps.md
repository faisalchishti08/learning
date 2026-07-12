---
card: microservices
gi: 73
slug: package-by-feature-structure-in-spring-boot-apps
title: "Package-by-feature structure in Spring Boot apps"
---

## 1. What it is

Package-by-feature organizes a Spring Boot application's source tree around business capabilities — one package per feature (`orders`, `shipping`, `billing`), each containing everything that feature needs: its controller, service, repository, and DTOs together — instead of the more common **package-by-layer** structure, where the top-level packages are technical layers (`controllers`, `services`, `repositories`) and each one contains a file for every feature mixed together. It is the file-system-level habit that makes a [Spring Modulith](0070-spring-modulith-for-modular-monoliths-as-a-stepping-stone.md) module boundary, or eventually a real microservice boundary, a natural fit rather than a painful re-sort of scattered files.

## 2. Why & when

Package-by-layer scatters a single feature's code across `controllers/OrderController.java`, `services/OrderService.java`, and `repositories/OrderRepository.java` — three files, three different top-level packages, no directory boundary keeping them together or keeping other features' code out. Understanding "everything about Orders" requires jumping across the whole tree; and critically, extracting Orders into a separate module or service means hunting down every Orders-related file scattered through every layer package. Package-by-feature fixes both problems structurally: everything about Orders lives under `orders/`, so understanding the feature means reading one directory, and extracting the feature means moving one directory.

Adopt package-by-feature from the start of any new Spring Boot service, and especially in a codebase that expects to grow toward [Spring Modulith](0070-spring-modulith-for-modular-monoliths-as-a-stepping-stone.md) or eventual microservices extraction — the package structure is what those tools' automatic module-boundary detection actually scans.

## 3. Core concept

Compare the two layouts for the exact same three features: package-by-layer groups files by their technical role; package-by-feature groups files by the business capability they belong to.

```
PACKAGE-BY-LAYER                        PACKAGE-BY-FEATURE
-----------------                       -------------------
controllers/                            orders/
  OrderController.java                    OrderController.java
  ShippingController.java                 OrderService.java
services/                                 OrderRepository.java
  OrderService.java                     shipping/
  ShippingService.java                    ShippingController.java
repositories/                             ShippingService.java
  OrderRepository.java                    ShippingRepository.java
  ShippingRepository.java
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Package-by-layer scatters Order and Shipping files across three technical-layer directories; package-by-feature groups each feature's files into one directory">
  <rect x="20" y="20" width="270" height="180" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">package-by-layer</text>
  <rect x="35" y="55" width="110" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="76" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">controllers/</text>
  <rect x="35" y="100" width="110" height="35" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="121" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">services/</text>
  <rect x="35" y="145" width="110" height="35" rx="4" fill="#1c2430" stroke="#c9820a"/>
  <text x="90" y="166" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">repositories/</text>
  <text x="220" y="80" fill="#8b949e" font-size="6.5" font-family="sans-serif">Order + Shipping</text>
  <text x="220" y="122" fill="#8b949e" font-size="6.5" font-family="sans-serif">files mixed in</text>
  <text x="220" y="164" fill="#8b949e" font-size="6.5" font-family="sans-serif">EVERY directory</text>

  <rect x="330" y="20" width="290" height="180" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">package-by-feature</text>
  <rect x="345" y="55" width="120" height="65" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="405" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">orders/</text>
  <text x="405" y="90" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">Controller, Service,</text>
  <text x="405" y="102" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">Repository -- ALL together</text>
  <rect x="480" y="55" width="120" height="65" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">shipping/</text>
  <text x="540" y="90" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">Controller, Service,</text>
  <text x="540" y="102" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">Repository -- ALL together</text>
</svg>

Package-by-feature groups everything one feature needs into a single directory, ready to move as a unit.

## 5. Runnable example

Scenario: model a small Spring-flavored app (a `Controller`/`Service`/`Repository` trio per feature) first laid out package-by-layer, showing how spread-out and cross-feature-tangled it is programmatically, then re-laid-out package-by-feature, then extended to simulate the actual benefit — a script that "extracts" one feature's directory wholesale, which only works cleanly under the feature-based layout.

### Level 1 — Basic

```java
// File: PackageByLayer.java -- simulate a package-by-layer app: classes
// are grouped by TECHNICAL ROLE (Controller/Service/Repository), with
// Order and Shipping code interleaved inside each role.
import java.util.*;

public class PackageByLayer {
    // "controllers" package -- Order and Shipping controllers side by side
    static class OrderController { String handle() { return "OrderController"; } }
    static class ShippingController { String handle() { return "ShippingController"; } }
    // "services" package
    static class OrderServiceImpl { String handle() { return "OrderService"; } }
    static class ShippingServiceImpl { String handle() { return "ShippingService"; } }
    // "repositories" package
    static class OrderRepository { String handle() { return "OrderRepository"; } }
    static class ShippingRepository { String handle() { return "ShippingRepository"; } }

    public static void main(String[] args) {
        // to understand "everything about Orders," you must visit THREE separate groupings:
        System.out.println("Orders feature spans: " + new OrderController().handle()
                + ", " + new OrderServiceImpl().handle() + ", " + new OrderRepository().handle());
    }
}
```

**How to run:** `javac PackageByLayer.java && java PackageByLayer` (JDK 17+).

Expected output:
```
Orders feature spans: OrderController, OrderService, OrderRepository
```

In a real project, these three classes would live in three different top-level directories (`controllers/`, `services/`, `repositories/`), each also containing `Shipping*` equivalents — Orders and Shipping code interleaved everywhere.

### Level 2 — Intermediate

```java
// File: PackageByFeature.java -- the SAME three classes per feature, now
// modeled as belonging to a FEATURE group, not a technical-layer group.
import java.util.*;

public class PackageByFeature {
    interface FeatureComponent { String describe(); }

    // "orders" feature -- everything Orders needs, together
    static class OrdersFeature {
        static class Controller implements FeatureComponent { public String describe() { return "OrderController"; } }
        static class Service implements FeatureComponent { public String describe() { return "OrderService"; } }
        static class Repository implements FeatureComponent { public String describe() { return "OrderRepository"; } }
        static List<FeatureComponent> components() {
            return List.of(new Controller(), new Service(), new Repository());
        }
    }

    // "shipping" feature -- everything Shipping needs, together, SEPARATELY
    static class ShippingFeature {
        static class Controller implements FeatureComponent { public String describe() { return "ShippingController"; } }
        static class Service implements FeatureComponent { public String describe() { return "ShippingService"; } }
        static class Repository implements FeatureComponent { public String describe() { return "ShippingRepository"; } }
        static List<FeatureComponent> components() {
            return List.of(new Controller(), new Service(), new Repository());
        }
    }

    public static void main(String[] args) {
        System.out.println("orders/ contains: " + OrdersFeature.components().stream().map(FeatureComponent::describe).toList());
        System.out.println("shipping/ contains: " + ShippingFeature.components().stream().map(FeatureComponent::describe).toList());
    }
}
```

**How to run:** `javac PackageByFeature.java && java PackageByFeature` (JDK 17+).

Expected output:
```
orders/ contains: [OrderController, OrderService, OrderRepository]
shipping/ contains: [ShippingController, ShippingService, ShippingRepository]
```

Now "everything about Orders" is one call — `OrdersFeature.components()` — and nothing about Shipping ever appears mixed in.

### Level 3 — Advanced

```java
// File: ExtractFeatureDirectory.java -- simulate the REAL payoff:
// extracting a feature into its own module/service is now "move one
// directory" -- modeled here as a function that takes a whole feature's
// component list and successfully relocates it, versus the SAME attempt
// under package-by-layer, which requires hunting across multiple groups.
import java.util.*;

public class ExtractFeatureDirectory {
    interface FeatureComponent { String describe(); }

    static class OrdersFeature {
        static class Controller implements FeatureComponent { public String describe() { return "OrderController"; } }
        static class Service implements FeatureComponent { public String describe() { return "OrderService"; } }
        static class Repository implements FeatureComponent { public String describe() { return "OrderRepository"; } }
        static List<FeatureComponent> components() {
            return List.of(new Controller(), new Service(), new Repository());
        }
    }

    // extraction under package-by-feature: trivial -- the feature's components ARE the extraction unit
    static List<String> extractFeature(String featureName, List<FeatureComponent> components) {
        List<String> moved = new ArrayList<>();
        for (FeatureComponent c : components) moved.add(c.describe());
        System.out.println("Extracted '" + featureName + "' module with " + moved.size() + " classes, zero cross-feature files touched.");
        return moved;
    }

    // extraction under package-by-layer: must search EVERY layer group for feature-matching classes
    static List<String> extractFeatureFromLayers(String featurePrefix, Map<String, List<String>> layeredClasses) {
        List<String> moved = new ArrayList<>();
        int layersSearched = 0;
        for (var entry : layeredClasses.entrySet()) {
            layersSearched++;
            for (String className : entry.getValue()) {
                if (className.startsWith(featurePrefix)) moved.add(className);
            }
        }
        System.out.println("Extracted '" + featurePrefix + "*' by searching " + layersSearched + " separate layer directories.");
        return moved;
    }

    public static void main(String[] args) {
        List<String> viaFeature = extractFeature("orders", OrdersFeature.components());
        System.out.println("Moved: " + viaFeature);

        Map<String, List<String>> layers = new LinkedHashMap<>(); // LinkedHashMap: preserves insertion order below
        layers.put("controllers", List.of("OrderController", "ShippingController"));
        layers.put("services", List.of("OrderService", "ShippingService"));
        layers.put("repositories", List.of("OrderRepository", "ShippingRepository"));
        List<String> viaLayers = extractFeatureFromLayers("Order", layers);
        System.out.println("Moved: " + viaLayers);
    }
}
```

**How to run:** `javac ExtractFeatureDirectory.java && java ExtractFeatureDirectory` (JDK 17+).

Expected output:
```
Extracted 'orders' module with 3 classes, zero cross-feature files touched.
Moved: [OrderController, OrderService, OrderRepository]
Extracted 'Order*' by searching 3 separate layer directories.
Moved: [OrderController, OrderService, OrderRepository]
```

## 6. Walkthrough

1. **Level 1** — `PackageByLayer.main` calls `handle()` on three separate classes that would, in a real project, sit in three different top-level directories. `main` still manages to print "everything about Orders" because it explicitly names each of the three classes — but note that gathering this list required the *developer* to already know, from memory, which class in each layer belongs to Orders. Nothing in the file structure itself groups them.
2. **Level 2 — restructuring by feature** — `OrdersFeature` and `ShippingFeature` each become a single grouping (in a real project, a single top-level package) exposing a `components()` method that returns everything belonging to that feature. `main` prints each feature's full component list with one call each — `OrdersFeature.components()` and `ShippingFeature.components()` — with no manual cross-referencing needed, because the grouping itself carries that information.
3. **Level 3 — measuring the extraction cost difference** — `extractFeature` (feature-based) simply iterates the `components()` list already scoped to one feature and reports success immediately — the "extraction" is trivially just handing over a list that was already fully scoped to Orders, printing that zero cross-feature files were touched. `extractFeatureFromLayers` (layer-based) instead has to iterate a `Map` keyed by layer name (`"controllers"`, `"services"`, `"repositories"`), and for *each* layer's class list, filter for names starting with the feature prefix `"Order"` — meaning it must visit and search every single layer directory just to reassemble the same three classes.
4. **Tracing `main`'s two calls** — the first call, `extractFeature("orders", OrdersFeature.components())`, immediately returns the three Orders class names, having done no searching at all — the print statement's `layersSearched` concept doesn't even apply here because there was nothing to search. The second call, `extractFeatureFromLayers("Order", layers)`, loops over all three map entries (`layersSearched` reaches 3), filtering each layer's list for the `"Order"` prefix, and arrives at the *same final list* of three classes — but only after touching three separate groupings instead of one.
5. **What this demonstrates about real refactoring cost** — both approaches, in this simulation, end up with the correct three classes. But the *work* required to get there differs starkly: under package-by-feature, the classes were already colocated, so extraction is "hand over the directory." Under package-by-layer, extraction requires knowing (or grepping for) every feature-prefixed class across every layer directory — exactly the tedious, error-prone hunt that makes real monolith decomposition slower and riskier than it needs to be.

## 7. Gotchas & takeaways

> **Gotcha:** package-by-feature can tempt teams into making every class inside a feature package `public`, since Java's default (package-private) visibility no longer separates "this feature" from "that feature" the way separate top-level packages did under package-by-layer. Keep implementation classes (repositories, internal helpers) package-private or under a nested `internal` sub-package — see [Spring Modulith for modular monoliths](0070-spring-modulith-for-modular-monoliths-as-a-stepping-stone.md) — so the feature package itself still has a controlled public surface.

- Package-by-layer groups files by technical role; package-by-feature groups files by business capability — the same files, organized around a different axis.
- Package-by-feature makes "read everything about this feature" and "extract this feature" both a matter of visiting one directory, rather than hunting across every technical layer.
- This structural habit is what makes Spring Modulith's automatic module detection (see [application modules & verification](0071-spring-modulith-application-modules-verification.md)) work naturally out of the box — the tool scans top-level packages, and those packages are already features.
- Adopt package-by-feature early; restructuring a large, mature package-by-layer codebase later is itself a significant, risky refactor — exactly the kind of hunt-across-every-layer work Level 3's `extractFeatureFromLayers` simulates.
- Package-by-feature and tactical DDD patterns combine naturally: a feature package is a very reasonable place to also apply [aggregates](0052-aggregates-and-aggregate-roots.md), value objects, and repositories scoped to that one feature.
