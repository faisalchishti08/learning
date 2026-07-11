---
card: spring-cloud
gi: 131
slug: spring-cloud-deployer-abstraction
title: "Spring Cloud Deployer abstraction"
---

## 1. What it is

Spring Cloud Deployer is the interface (`AppDeployer`, `TaskLauncher`) that Skipper and Data Flow's task-launching logic call to actually deploy or launch an application onto some concrete target runtime, with separate implementations — `spring-cloud-deployer-kubernetes`, `spring-cloud-deployer-cloudfoundry`, `spring-cloud-deployer-local` — translating the same deployment request into that runtime's own native mechanism (creating a Kubernetes Deployment/Pod, pushing a Cloud Foundry app, or spawning a local process), so the same Data Flow stream/task DSL and Skipper release model work unmodified across genuinely different underlying infrastructure.

```java
public interface AppDeployer {
    String deploy(AppDeploymentRequest request); // implementation VARIES by target runtime
    void undeploy(String id);
}
```

```
spring-cloud-deployer-kubernetes   -> deploy() creates a Kubernetes Deployment + Service
spring-cloud-deployer-cloudfoundry -> deploy() pushes an app via the CF API
spring-cloud-deployer-local        -> deploy() spawns a local JVM process
```

## 2. Why & when

Data Flow and Skipper's stream/task DSL and release-management logic (earlier cards) are deliberately written without any awareness of a specific target infrastructure — the same `stream deploy` command needs to work whether the actual pipeline runs on Kubernetes in production, Cloud Foundry in a different environment, or locally during development, and hardcoding any one of those into the orchestration logic itself would make it impossible to support more than one target without a rewrite. Spring Cloud Deployer solves this with the same "depend on the interface, not the implementation" pattern seen throughout Spring Cloud (Discovery, LoadBalancer, and others) — Data Flow and Skipper call `AppDeployer.deploy(...)`, and whichever concrete deployer implementation is configured translates that generic request into the specific, native deployment mechanism the target platform actually understands.

Reach for understanding the Deployer abstraction when:

- Deploying Data Flow itself onto a new target platform — the choice of which `spring-cloud-deployer-*` dependency to include is what actually determines where stream/task applications end up running, with no change needed to the stream/task definitions or DSL themselves.
- Debugging a deployment failure specific to one target platform — since the actual deployment mechanics live entirely within the specific deployer implementation, a Kubernetes-specific deployment failure (a malformed Pod spec, an RBAC permission issue) is a `spring-cloud-deployer-kubernetes` concern, not a Data Flow or Skipper concern.
- Understanding why the same stream/task DSL commands behave identically regardless of target platform — this consistency is the direct payoff of the Deployer abstraction, exactly analogous to how `DiscoveryClient` calls work identically whether backed by Eureka or Kubernetes (an earlier card in this section).

## 3. Core concept

```
 Data Flow / Skipper:
   calls appDeployer.deploy(request)  -- IDENTICAL call, regardless of target platform

 WHICH deployer implementation actually runs depends purely on what's configured/on the classpath:

   spring-cloud-deployer-kubernetes.deploy(request):
     -> creates a Kubernetes Deployment object, a Service, wires ConfigMaps -- KUBERNETES-NATIVE mechanics

   spring-cloud-deployer-cloudfoundry.deploy(request):
     -> calls the Cloud Foundry API to push and start an application -- CLOUD-FOUNDRY-NATIVE mechanics

   spring-cloud-deployer-local.deploy(request):
     -> spawns a local JVM process directly -- SIMPLEST, for local development
```

Data Flow's and Skipper's own code contains zero platform-specific logic anywhere — every platform-specific detail is fully contained within whichever single deployer implementation is actually active.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Data Flow and Skipper call one neutral AppDeployer interface which is backed by exactly one of three interchangeable implementations that translate the same deployment request into Kubernetes Cloud Foundry or local process native mechanics">
  <rect x="220" y="20" width="200" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">AppDeployer interface</text>
  <text x="320" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Data Flow / Skipper call THIS</text>

  <rect x="30" y="120" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="115" y="148" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">deployer-kubernetes</text>

  <rect x="235" y="120" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="148" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">deployer-cloudfoundry</text>

  <rect x="440" y="120" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="525" y="148" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">deployer-local</text>

  <defs><marker id="a131" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="280" y1="66" x2="115" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a131)"/>
  <line x1="320" y1="66" x2="320" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a131)"/>
  <line x1="360" y1="66" x2="525" y2="120" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a131)"/>
</svg>

One neutral interface at the top; exactly one of the interchangeable implementations underneath is active for any given Data Flow deployment.

## 5. Runnable example

The scenario: model the `AppDeployer` interface with two different implementations, called identically by simulated Data Flow/Skipper orchestration logic, proving the orchestration code is platform-agnostic. Start with a single deployer implementation, then add a second, swappable implementation, then extend to a case where deployer-specific errors are surfaced without the orchestration logic itself needing platform-specific error handling.

### Level 1 — Basic

A single `AppDeployer` implementation and orchestration logic calling it through the interface.

```java
import java.util.*;

public class DeployerAbstractionLevel1 {
    record AppDeploymentRequest(String appName, Map<String, String> properties) {}

    interface AppDeployer {
        String deploy(AppDeploymentRequest request);
    }

    static class LocalDeployer implements AppDeployer {
        public String deploy(AppDeploymentRequest request) {
            System.out.println("LocalDeployer: spawning local process for '" + request.appName() + "'");
            return "local-process-" + request.appName();
        }
    }

    // models Data Flow / Skipper's own orchestration -- depends ONLY on the interface
    static void orchestrateDeployment(AppDeployer deployer, AppDeploymentRequest request) {
        String deploymentId = deployer.deploy(request);
        System.out.println("orchestration recorded deployment id: " + deploymentId);
    }

    public static void main(String[] args) {
        AppDeployer deployer = new LocalDeployer();
        orchestrateDeployment(deployer, new AppDeploymentRequest("order-pipeline-http", Map.of()));
    }
}
```

How to run: `java DeployerAbstractionLevel1.java`

`orchestrateDeployment` calls only `deployer.deploy(request)`, never anything `LocalDeployer`-specific — this is the exact decoupling that lets Data Flow's real orchestration logic remain unaware of which concrete deployer is actually running underneath it.

### Level 2 — Intermediate

Add a second deployer implementation (Kubernetes-style) and call the identical `orchestrateDeployment` method against both, proving orchestration code needs zero changes to target a different platform.

```java
import java.util.*;

public class DeployerAbstractionLevel2 {
    record AppDeploymentRequest(String appName, Map<String, String> properties) {}

    interface AppDeployer {
        String deploy(AppDeploymentRequest request);
    }

    static class LocalDeployer implements AppDeployer {
        public String deploy(AppDeploymentRequest request) {
            System.out.println("LocalDeployer: spawning local process for '" + request.appName() + "'");
            return "local-process-" + request.appName();
        }
    }

    static class KubernetesDeployer implements AppDeployer {
        public String deploy(AppDeploymentRequest request) {
            System.out.println("KubernetesDeployer: creating Deployment + Service for '" + request.appName() + "'");
            return "k8s-deployment-" + request.appName();
        }
    }

    // UNCHANGED from Level 1 -- this is the entire point
    static void orchestrateDeployment(AppDeployer deployer, AppDeploymentRequest request) {
        String deploymentId = deployer.deploy(request);
        System.out.println("orchestration recorded deployment id: " + deploymentId);
    }

    public static void main(String[] args) {
        AppDeploymentRequest request = new AppDeploymentRequest("order-pipeline-http", Map.of());

        System.out.println("-- targeting LOCAL --");
        orchestrateDeployment(new LocalDeployer(), request);

        System.out.println("-- targeting KUBERNETES (SAME orchestration code) --");
        orchestrateDeployment(new KubernetesDeployer(), request);
    }
}
```

How to run: `java DeployerAbstractionLevel2.java`

`orchestrateDeployment`'s source code is byte-for-byte identical across both calls — only the concrete `AppDeployer` implementation passed in differs, exactly mirroring how switching Data Flow's target platform from local development to a Kubernetes production deployment requires changing which `spring-cloud-deployer-*` dependency is active, with zero changes to Data Flow's own stream/task orchestration logic.

### Level 3 — Advanced

Add deployer-specific error handling surfaced through a uniform exception type, so orchestration code can react to deployment failures without needing platform-specific error handling logic of its own.

```java
import java.util.*;

public class DeployerAbstractionLevel3 {
    record AppDeploymentRequest(String appName, Map<String, String> properties) {}

    static class DeploymentException extends RuntimeException {
        DeploymentException(String message) { super(message); }
    }

    interface AppDeployer {
        String deploy(AppDeploymentRequest request);
    }

    static class KubernetesDeployer implements AppDeployer {
        public String deploy(AppDeploymentRequest request) {
            if (!request.properties().containsKey("image")) {
                // a Kubernetes-SPECIFIC failure mode: no container image specified
                throw new DeploymentException("Kubernetes deployment failed: no 'image' property specified for '" + request.appName() + "'");
            }
            return "k8s-deployment-" + request.appName();
        }
    }

    static class CloudFoundryDeployer implements AppDeployer {
        public String deploy(AppDeploymentRequest request) {
            if (!request.properties().containsKey("memory")) {
                // a DIFFERENT, Cloud-Foundry-SPECIFIC failure mode: no memory quota specified
                throw new DeploymentException("Cloud Foundry deployment failed: no 'memory' property specified for '" + request.appName() + "'");
            }
            return "cf-app-" + request.appName();
        }
    }

    // orchestration handles the UNIFORM DeploymentException -- no platform-specific catch blocks needed
    static void orchestrateDeployment(AppDeployer deployer, AppDeploymentRequest request) {
        try {
            String deploymentId = deployer.deploy(request);
            System.out.println("SUCCESS: deployment id " + deploymentId);
        } catch (DeploymentException e) {
            System.out.println("DEPLOYMENT FAILED: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        AppDeploymentRequest incompleteRequest = new AppDeploymentRequest("order-pipeline-http", Map.of());

        System.out.println("-- Kubernetes, missing 'image' --");
        orchestrateDeployment(new KubernetesDeployer(), incompleteRequest);

        System.out.println("-- Cloud Foundry, missing 'memory' --");
        orchestrateDeployment(new CloudFoundryDeployer(), incompleteRequest);
    }
}
```

How to run: `java DeployerAbstractionLevel3.java`

Both calls to `orchestrateDeployment` use the exact same `try`/`catch (DeploymentException e)` logic, yet each deployer throws for an entirely different, platform-specific reason (a missing `image` property for Kubernetes, a missing `memory` property for Cloud Foundry) — `orchestrateDeployment` never needs to know or check which specific platform-specific validation failed; it only needs to handle the uniform `DeploymentException` type, exactly mirroring how Data Flow's real error handling around deployment failures stays platform-agnostic even though the underlying causes of a deployment failure are often deeply platform-specific.

## 6. Walkthrough

Trace the Cloud Foundry deployment attempt in Level 3.

1. `orchestrateDeployment(new CloudFoundryDeployer(), incompleteRequest)` is called — inside, the `try` block calls `deployer.deploy(incompleteRequest)`, which dispatches to `CloudFoundryDeployer.deploy`.
2. Inside `deploy`, `request.properties().containsKey("memory")` checks `incompleteRequest`'s `properties` map, which is `Map.of()` (empty) — this returns `false`.
3. Because the check is `false`, the `if (!request.properties().containsKey("memory"))` condition is `true`, so `deploy` throws `new DeploymentException("Cloud Foundry deployment failed: no 'memory' property specified for 'order-pipeline-http'")`.
4. This exception propagates up out of `deploy` and is caught by the `catch (DeploymentException e)` block back in `orchestrateDeployment` — note this is the *same* catch block that would also handle `KubernetesDeployer`'s entirely different `"no 'image' property"` failure from the call just before it.
5. `println` prints `"DEPLOYMENT FAILED: Cloud Foundry deployment failed: no 'memory' property specified for 'order-pipeline-http'"` — the specific, platform-relevant error message originated entirely from within `CloudFoundryDeployer`'s own implementation, while the generic handling logic (catching `DeploymentException` and reporting it) in `orchestrateDeployment` remained completely unaware of, and unconcerned with, exactly what platform-specific validation had failed.

```
orchestrateDeployment(CloudFoundryDeployer, incompleteRequest):
  try: deployer.deploy(request)
    -> CloudFoundryDeployer.deploy checks properties.containsKey("memory") -> false
    -> throws DeploymentException("...no 'memory' property...")
  catch (DeploymentException e): prints "DEPLOYMENT FAILED: ..."

SAME catch block also handled KubernetesDeployer's UNRELATED "no 'image'" failure just before this
```

## 7. Gotchas & takeaways

> **Gotcha:** while `AppDeployer`'s interface is uniform, the *properties* a given deployment request needs to succeed are genuinely platform-specific (Kubernetes needs an `image`; Cloud Foundry needs a `memory` quota, as Level 3 modeled) — a deployment configuration that works perfectly against one target platform can fail validation entirely on another, purely because that platform's deployer implementation expects different required properties. Portability of the orchestration *code* (the Deployer abstraction's main benefit) does not automatically mean portability of the exact deployment *configuration* across every target platform without adjustment.

- Spring Cloud Deployer's `AppDeployer`/`TaskLauncher` interfaces are what let Data Flow's and Skipper's own orchestration and release-management logic remain entirely free of platform-specific code, following the same decoupling pattern seen throughout Spring Cloud (Discovery, LoadBalancer) applied here to deployment mechanics specifically.
- Switching Data Flow's target platform is a matter of which `spring-cloud-deployer-*` implementation is configured and active — the stream/task DSL, Skipper's release model, and Data Flow's own orchestration logic require zero changes to work against a different target.
- Deployment failures are often genuinely platform-specific in their root cause, even though they can be surfaced through a uniform exception type — understanding this distinction (uniform error *handling*, platform-specific error *causes*) helps correctly scope where to look when a deployment fails on one platform but not another.
- This card completes the orchestration-layer trio covered across this section: Data Flow provides the stream/task DSL and orchestration surface, Skipper provides versioned, rollback-capable deployment for streams, and Spring Cloud Deployer provides the pluggable, platform-agnostic mechanism both build on to actually realize a deployment on whatever target infrastructure is configured.
