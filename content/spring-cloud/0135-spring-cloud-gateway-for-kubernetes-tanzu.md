---
card: spring-cloud
gi: 135
slug: spring-cloud-gateway-for-kubernetes-tanzu
title: "Spring Cloud Gateway for Kubernetes / Tanzu"
---

## 1. What it is

Spring Cloud Gateway for Kubernetes is a VMware Tanzu commercial product that runs Spring Cloud Gateway as a Kubernetes-native API gateway, configured declaratively through Kubernetes Custom Resource Definitions (`SpringCloudGatewayMapping`, `SpringCloudGatewayRouteConfig`) instead of the `application.yml` route configuration earlier Gateway cards covered — letting platform teams manage gateway routing the same way they manage every other Kubernetes resource (via `kubectl apply`, GitOps pipelines, and Kubernetes RBAC), rather than through gateway-application-specific configuration files.

```yaml
apiVersion: tanzu.vmware.com/v1
kind: SpringCloudGatewayMapping
metadata:
  name: order-service-mapping
spec:
  routes:
    - predicates:
        - Path=/orders/**
      filters:
        - StripPrefix=1
      uri: http://order-service
```

```bash
kubectl apply -f order-service-mapping.yaml   # route change deployed via ordinary Kubernetes tooling
```

## 2. Why & when

The open-source Spring Cloud Gateway (earlier cards) is typically configured through an `application.yml` file baked into (or externally supplied to) one specific gateway application instance — perfectly workable, but it means every route change requires touching and redeploying that gateway application's own configuration, which doesn't naturally fit a Kubernetes-native operational model where routing is commonly expected to be managed as its own set of declarative, version-controlled Kubernetes resources, independently of the gateway application's own deployment lifecycle. Spring Cloud Gateway for Kubernetes addresses this specifically: routes become Kubernetes Custom Resources, so adding, changing, or removing a route is a `kubectl apply`/GitOps operation against a CRD, decoupled from redeploying the gateway pod itself, and subject to the same RBAC, audit, and GitOps workflows already governing every other Kubernetes resource in the cluster.

Reach for Spring Cloud Gateway for Kubernetes when:

- Running on Kubernetes and wanting gateway routing configuration to be managed as native Kubernetes resources (via GitOps, `kubectl`, Kubernetes RBAC) rather than as an application-specific configuration file requiring a gateway redeploy for every route change.
- Different teams need to independently manage their own services' routes without needing write access to a shared, centralized `application.yml` — Kubernetes RBAC can scope which teams can create/modify `SpringCloudGatewayMapping` resources for their own namespaces, decoupling route ownership across teams.
- Already invested in (or considering) VMware Tanzu's broader commercial platform tooling — this Gateway variant is one specific commercial offering within that ecosystem, distinct from the open-source Spring Cloud Gateway and Spring Cloud Gateway MVC covered in earlier cards.

## 3. Core concept

```
 open-source Spring Cloud Gateway (earlier cards):
   routes defined in application.yml, baked into or supplied to ONE gateway application
   route change -> requires touching that config, typically redeploying the gateway app

 Spring Cloud Gateway for Kubernetes (this card):
   routes defined as Kubernetes Custom Resources (SpringCloudGatewayMapping / RouteConfig)
   route change -> kubectl apply / GitOps commit -- the GATEWAY POD itself is NOT redeployed
                   a Kubernetes controller watches these CRDs and reconfigures the running gateway dynamically
```

The underlying routing engine is still Spring Cloud Gateway — what changes is where route definitions live and how they're managed: application configuration versus Kubernetes-native declarative resources.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A kubectl apply of a SpringCloudGatewayMapping custom resource is watched by a controller which dynamically reconfigures the running gateway pods routing without requiring the gateway application itself to be redeployed">
  <rect x="20" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="110" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">kubectl apply</text>
  <text x="110" y="56" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">SpringCloudGatewayMapping</text>

  <rect x="250" y="20" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="335" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Kubernetes controller</text>
  <text x="335" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">watches the CRD</text>

  <rect x="470" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">running gateway pod</text>
  <text x="545" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">reconfigured, NOT redeployed</text>

  <defs><marker id="a135" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="200" y1="43" x2="250" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a135)"/>
  <line x1="420" y1="43" x2="470" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a135)"/>
</svg>

The gateway pod's own lifecycle (start, stop, redeploy) is entirely decoupled from route configuration changes — routing updates dynamically in response to CRD changes alone.

## 5. Runnable example

The scenario: model the Kubernetes controller pattern — a running gateway's route table dynamically reconfigured in response to Custom Resource changes, without the gateway process itself restarting. Start with static, application-config-style routing (the baseline being replaced), then add CRD-watch-driven dynamic reconfiguration, then add multiple teams independently managing their own routes via separately-applied resources, without needing to coordinate through one shared configuration file.

### Level 1 — Basic

Static, application-config-style routing — the baseline this Kubernetes-native approach replaces.

```java
import java.util.*;

public class GatewayForK8sLevel1 {
    record Route(String path, String targetUri) {}

    static class Gateway {
        List<Route> routes; // fixed at CONSTRUCTION -- a route change requires REBUILDING this gateway instance
        Gateway(List<Route> routes) { this.routes = routes; }
        String route(String path) {
            for (Route r : routes) if (path.startsWith(r.path())) return "routed to " + r.targetUri();
            return "404 Not Found";
        }
    }

    public static void main(String[] args) {
        // routes baked in at startup, mirroring application.yml-based configuration
        Gateway gateway = new Gateway(List.of(new Route("/orders", "http://order-service")));

        System.out.println(gateway.route("/orders/42"));
    }
}
```

How to run: `java GatewayForK8sLevel1.java`

`Gateway.routes` is fixed once, at construction — adding a new route would require constructing an entirely new `Gateway` instance, mirroring how an open-source Spring Cloud Gateway's `application.yml`-defined routes traditionally require a redeploy to change.

### Level 2 — Intermediate

Add a Kubernetes-controller-style mechanism: route changes are applied to a separate, watched resource store, and the running gateway's route table updates dynamically in response, without the gateway object itself being reconstructed.

```java
import java.util.*;
import java.util.function.Consumer;

public class GatewayForK8sLevel2 {
    record Route(String path, String targetUri) {}

    // models the running gateway pod -- its route table is MUTABLE and updated LIVE, never reconstructed
    static class Gateway {
        List<Route> routes = new ArrayList<>();
        void updateRoutes(List<Route> newRoutes) {
            routes = new ArrayList<>(newRoutes);
            System.out.println("gateway route table RECONFIGURED (no restart): " + routes.size() + " route(s) active");
        }
        String route(String path) {
            for (Route r : routes) if (path.startsWith(r.path())) return "routed to " + r.targetUri();
            return "404 Not Found";
        }
    }

    // models the Kubernetes controller watching SpringCloudGatewayMapping CRDs
    static class GatewayMappingController {
        Gateway gateway;
        List<Route> currentCrdState = new ArrayList<>();
        GatewayMappingController(Gateway gateway) { this.gateway = gateway; }

        void applyMapping(Route route) { // models "kubectl apply" of a SpringCloudGatewayMapping
            currentCrdState.add(route);
            System.out.println("kubectl apply: mapping for " + route.path() + " -> " + route.targetUri());
            gateway.updateRoutes(currentCrdState); // controller reconciles the RUNNING gateway to match the CRD state
        }
    }

    public static void main(String[] args) {
        Gateway gateway = new Gateway(); // starts with ZERO routes -- nothing baked in at construction
        GatewayMappingController controller = new GatewayMappingController(gateway);

        System.out.println(gateway.route("/orders/42")); // 404 -- no routes applied yet

        controller.applyMapping(new Route("/orders", "http://order-service")); // a kubectl apply, LIVE, no gateway restart

        System.out.println(gateway.route("/orders/42")); // now routes correctly, with NO gateway reconstruction
    }
}
```

How to run: `java GatewayForK8sLevel2.java`

The `gateway` object referenced by both calls to `gateway.route(...)` is the exact same instance throughout — it was never reconstructed, only its internal `routes` field was mutated via `updateRoutes`, triggered by `applyMapping` — this models exactly the value proposition of Spring Cloud Gateway for Kubernetes: applying a new route mapping reconfigures the running gateway live, with no redeploy of the gateway application itself.

### Level 3 — Advanced

Add multiple teams independently applying their own route mappings via separate resources, without needing to coordinate through one shared configuration file, and confirm the controller correctly reconciles all of them into one combined, live route table.

```java
import java.util.*;

public class GatewayForK8sLevel3 {
    record Route(String path, String targetUri, String ownerTeam) {}

    static class Gateway {
        List<Route> routes = new ArrayList<>();
        void updateRoutes(List<Route> newRoutes) { routes = new ArrayList<>(newRoutes); }
        String route(String path) {
            for (Route r : routes) if (path.startsWith(r.path())) return "routed to " + r.targetUri() + " (owned by " + r.ownerTeam() + ")";
            return "404 Not Found";
        }
    }

    static class GatewayMappingController {
        Gateway gateway;
        Map<String, Route> mappingsByName = new LinkedHashMap<>(); // keyed by CRD resource name, like real Kubernetes objects
        GatewayMappingController(Gateway gateway) { this.gateway = gateway; }

        void applyMapping(String resourceName, Route route) {
            mappingsByName.put(resourceName, route); // each team applies THEIR OWN named resource, independently
            reconcile();
        }

        void removeMapping(String resourceName) {
            mappingsByName.remove(resourceName);
            reconcile();
        }

        void reconcile() {
            gateway.updateRoutes(new ArrayList<>(mappingsByName.values()));
        }
    }

    public static void main(String[] args) {
        Gateway gateway = new Gateway();
        GatewayMappingController controller = new GatewayMappingController(gateway);

        // team A applies their own mapping resource -- no coordination needed with team B
        controller.applyMapping("order-service-mapping", new Route("/orders", "http://order-service", "team-orders"));

        // team B applies THEIRS, entirely independently, in a completely separate kubectl apply
        controller.applyMapping("payment-service-mapping", new Route("/payments", "http://payment-service", "team-payments"));

        System.out.println(gateway.route("/orders/42"));
        System.out.println(gateway.route("/payments/99"));

        // team A later removes their mapping -- team B's mapping is COMPLETELY UNAFFECTED
        controller.removeMapping("order-service-mapping");
        System.out.println(gateway.route("/orders/42")); // now 404 -- team A's route is gone
        System.out.println(gateway.route("/payments/99")); // team B's route STILL works, untouched
    }
}
```

How to run: `java GatewayForK8sLevel3.java`

Team A's and Team B's route mappings are applied through entirely independent `applyMapping` calls (modeling separate `kubectl apply` operations against separate CRD resource names), and removing Team A's mapping later has zero effect on Team B's — `mappingsByName` correctly retains Team B's entry throughout, and `reconcile()` rebuilds the gateway's combined route table from whatever the current full set of applied mappings happens to be, exactly mirroring how multiple teams in a real Kubernetes cluster can independently manage their own services' `SpringCloudGatewayMapping` resources without needing coordinated access to one shared gateway configuration file.

## 6. Walkthrough

Trace the sequence after Team A removes their mapping in Level 3.

1. Before removal, `mappingsByName` holds two entries: `"order-service-mapping"` (Team A's route) and `"payment-service-mapping"` (Team B's route) — `reconcile()` was called after each `applyMapping`, so `gateway.routes` currently reflects both.
2. `controller.removeMapping("order-service-mapping")` calls `mappingsByName.remove("order-service-mapping")`, which removes exactly that one entry — `mappingsByName` now holds only `"payment-service-mapping"`.
3. `removeMapping` then calls `reconcile()`, which calls `gateway.updateRoutes(new ArrayList<>(mappingsByName.values()))` — since `mappingsByName` now contains only Team B's route, `gateway.routes` is rebuilt to contain exactly that one route, with Team A's route no longer present anywhere in it.
4. `gateway.route("/orders/42")` is called — the loop over `gateway.routes` finds no route whose `path()` matches (`"/orders"` was Team A's, now gone), so it falls through to `"404 Not Found"`.
5. `gateway.route("/payments/99")` is called — the loop finds Team B's route (`path="/payments"`), whose `path` is a prefix of `"/payments/99"`, so it returns the successful routing message, confirming Team B's route continued working correctly, completely unaffected by Team A's independent removal.

```
mappingsByName before removal: {order-service-mapping: teamA-route, payment-service-mapping: teamB-route}
removeMapping("order-service-mapping"):
  mappingsByName.remove(...) -> {payment-service-mapping: teamB-route}   (ONLY teamA's entry removed)
  reconcile() -> gateway.routes rebuilt from CURRENT mappingsByName -> [teamB-route only]

route("/orders/42")   -> no match -> 404   (teamA's route genuinely gone)
route("/payments/99") -> matches teamB-route -> routed correctly   (UNAFFECTED by teamA's removal)
```

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud Gateway for Kubernetes is a commercial VMware Tanzu product, distinct from and requiring a separate license/subscription from the open-source Spring Cloud Gateway covered in earlier cards — confirming licensing and support requirements before committing an architecture to this specific product (versus the open-source Gateway, self-managed on Kubernetes with the same declarative-CRD pattern potentially achievable through custom tooling) is a deliberate decision worth making explicitly, not something to assume is freely available simply because "Spring Cloud Gateway" is open source.

- The core architectural shift this product makes over open-source Spring Cloud Gateway is moving route configuration from application-level config files to Kubernetes-native Custom Resources, decoupling route changes from the gateway application's own deployment lifecycle.
- A Kubernetes controller watching these CRDs and dynamically reconfiguring the running gateway (rather than requiring a redeploy per route change) is what makes this decoupling actually work — the underlying Spring Cloud Gateway routing engine itself is unchanged, only how its configuration is sourced and updated.
- Independent teams managing their own services' routes via separately-applied, separately-owned CRD resources (rather than all teams needing write access to one shared configuration file) is a direct, practical consequence of this Kubernetes-native model, enabled by ordinary Kubernetes RBAC scoping which teams can modify which resources.
- This card closes out the Spring Cloud tutorial series — from foundational service discovery and configuration, through resilience, messaging, observability, security/Vault/Kubernetes integration, contract testing, task orchestration, and finally the cloud-provider-specific integrations (AWS, Azure, GCP) and this Kubernetes-native commercial Gateway variant, the series has covered the full breadth of what Spring Cloud provides for building, deploying, and operating distributed Spring applications.
