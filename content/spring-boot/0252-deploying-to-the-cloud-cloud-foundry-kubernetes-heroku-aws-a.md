---
card: spring-boot
gi: 252
slug: deploying-to-the-cloud-cloud-foundry-kubernetes-heroku-aws-a
title: Deploying to the cloud (Cloud Foundry, Kubernetes, Heroku, AWS, Azure, GCP)
---

## 1. What it is

Spring Boot is designed to run as a self-contained process on any platform that can execute a JVM (or a native binary). All major cloud platforms support it through different deployment models:

| Platform | Deployment unit | Main approach |
|---|---|---|
| **Kubernetes** | OCI container image | `kubectl apply` / Helm chart |
| **Cloud Foundry** | JAR or OCI image | `cf push` |
| **Heroku** | JAR (Buildpack auto-detected) | `git push heroku main` |
| **AWS** | JAR/container on EC2, ECS, Lambda, Elastic Beanstalk | Varies by service |
| **Azure** | JAR/container on App Service, AKS, Container Apps | `az webapp deploy` / AKS |
| **GCP** | Container on Cloud Run, GKE, App Engine | `gcloud run deploy` |

Spring Boot produces a single executable JAR (`spring-boot:repackage`) or an OCI image (`spring-boot:build-image`) — the same artifact works on all platforms.

## 2. Why & when

Cloud deployment matters when you move from a developer's laptop to a platform that provides:

- **Horizontal scaling** — multiple instances behind a load balancer.
- **Managed infrastructure** — the platform handles OS patches, networking, TLS, and auto-scaling.
- **Observability integration** — Kubernetes liveness/readiness probes, Cloud Foundry health checks, AWS CloudWatch, GCP Cloud Monitoring.

Spring Boot ships direct integration hooks for all of these: Actuator health endpoints map to probe URLs, graceful shutdown cooperates with platform drain signals, and `application.properties` separates environment concerns cleanly.

## 3. Core concept

Think of your Spring Boot JAR or container image as a **standardised shipping container**. The cloud platform is the **port and crane system** — it doesn't care what's inside, only that the container exposes the right interface (a TCP port, a health endpoint, an exit code). You package the app once and the platform handles distribution.

Key interfaces every platform expects:

1. **Process model** — the app runs as a process, reads config from environment variables or mounted files, and exits with code 0 on clean shutdown.
2. **Health / readiness endpoint** — `/actuator/health/liveness` and `/actuator/health/readiness` (Actuator).
3. **Log output** — write to `stdout`/`stderr`; the platform collects it.
4. **Config from environment** — Spring's `@Value("${DB_URL}")` and externalized config work with every platform's secret/config injection.
5. **Graceful drain** — the platform sends `SIGTERM`; Spring Boot 2.3+ handles it via `server.shutdown=graceful`.

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot app deployed to multiple cloud platforms via the same OCI image">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Central artifact -->
  <rect x="265" y="100" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="125" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Spring Boot</text>
  <text x="350" y="143" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">OCI Image / JAR</text>

  <!-- Platforms -->
  <rect x="10" y="20" width="110" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="65" y="43" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Kubernetes</text>

  <rect x="10" y="80" width="110" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="65" y="103" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Cloud Foundry</text>

  <rect x="10" y="140" width="110" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="65" y="163" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Heroku</text>

  <rect x="580" y="20" width="110" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="635" y="43" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">AWS ECS</text>

  <rect x="580" y="80" width="110" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="635" y="103" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Azure AKS</text>

  <rect x="580" y="140" width="110" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="635" y="163" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">GCP Cloud Run</text>

  <!-- Arrows left -->
  <line x1="120" y1="38" x2="263" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="120" y1="98" x2="263" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="120" y1="158" x2="263" y2="142" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Arrows right -->
  <line x1="437" y1="115" x2="578" y2="38" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="437" y1="128" x2="578" y2="98" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="437" y1="142" x2="578" y2="158" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same JAR/image, different deployment commands per platform</text>
  <text x="350" y="240" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Common interface: /actuator/health + SIGTERM + env-var config + stdout logging</text>
</svg>

One artifact; each platform uses its own deployment command and ingress but expects the same standard interfaces.

## 5. Runnable example

```java
// CloudDeployDemo.java — run with: java CloudDeployDemo.java
// Prints platform-specific deployment commands, required Actuator config,
// and the key application.properties settings for each cloud target.

public class CloudDeployDemo {

    record Platform(String name, String deployCmd, String healthProbe, String notes) {}

    public static void main(String[] args) {
        System.out.println("=== Spring Boot Cloud Deployment Cheat Sheet ===\n");

        Platform[] platforms = {
            new Platform(
                "Kubernetes",
                "kubectl apply -f k8s/deployment.yaml",
                "/actuator/health/liveness + /actuator/health/readiness",
                "Add livenessProbe and readinessProbe in pod spec"
            ),
            new Platform(
                "Cloud Foundry",
                "cf push myapp -p target/myapp.jar",
                "/actuator/health (CF uses it automatically)",
                "Set SPRING_PROFILES_ACTIVE via 'cf set-env'"
            ),
            new Platform(
                "Heroku",
                "git push heroku main  (Heroku detects Spring Boot via Buildpacks)",
                "/actuator/health",
                "Use $PORT env var: server.port=${PORT:8080}"
            ),
            new Platform(
                "AWS ECS / Fargate",
                "aws ecs update-service --force-new-deployment ...",
                "/actuator/health (ALB target group health check)",
                "Use Secrets Manager + Spring Cloud AWS for config"
            ),
            new Platform(
                "Azure App Service / AKS",
                "az webapp deploy --src-path target/myapp.jar",
                "/actuator/health (App Service health check path)",
                "APPLICATIONINSIGHTS_CONNECTION_STRING auto-wired by Spring"
            ),
            new Platform(
                "GCP Cloud Run",
                "gcloud run deploy myapp --image gcr.io/proj/myapp",
                "/actuator/health (Cloud Run startup probe)",
                "Reads PORT env var; use --min-instances=1 to avoid cold start"
            ),
        };

        for (Platform p : platforms) {
            System.out.printf("%-20s%n  Deploy : %s%n  Probe  : %s%n  Notes  : %s%n%n",
                p.name(), p.deployCmd(), p.healthProbe(), p.notes());
        }

        System.out.println("--- application.properties for all cloud platforms ---");
        System.out.println("""
            # Expose liveness + readiness separately (Kubernetes needs both)
            management.endpoint.health.probes.enabled=true
            management.health.livenessState.enabled=true
            management.health.readinessState.enabled=true

            # Graceful shutdown (cooperates with SIGTERM drain)
            server.shutdown=graceful
            spring.lifecycle.timeout-per-shutdown-phase=30s

            # Log to stdout (cloud platforms collect stdout)
            logging.file.name=   # empty = stdout only

            # Dynamic port (Heroku, Cloud Run inject PORT)
            server.port=${PORT:8080}
            """);
    }
}
```

**How to run:** `java CloudDeployDemo.java`

## 6. Walkthrough

- **`management.endpoint.health.probes.enabled=true`** — enables the `/actuator/health/liveness` and `/actuator/health/readiness` sub-paths. Kubernetes pod spec references these in `livenessProbe.httpGet.path` and `readinessProbe.httpGet.path`. Without separate probes, Kubernetes cannot distinguish "app is starting" from "app is broken".
- **`server.shutdown=graceful`** — when the platform sends `SIGTERM`, Spring stops accepting new requests, completes in-flight requests within the timeout, and then exits. Without this, active requests are interrupted mid-flight during rolling updates.
- **`server.port=${PORT:8080}`** — Heroku and GCP Cloud Run inject a `PORT` environment variable at runtime. Spring's `${PORT:8080}` expression reads it with a fallback of 8080 for local development.
- **Cloud Foundry** — `cf push -p app.jar` uploads the JAR and CF's Java buildpack creates a container. The `VCAP_SERVICES` environment variable injects bound service credentials; Spring Cloud Connectors or `spring-cloud-cloudfoundry-connector` parse it automatically.
- **AWS ECS / Fargate** — requires an OCI image pushed to ECR (`docker push ... && aws ecs update-service`). Application Load Balancer performs the health check against `/actuator/health`; ECS registers the container as healthy only after the health check passes.

## 7. Gotchas & takeaways

> **Cloud Run and Lambda have different cold-start constraints.** Cloud Run keeps at least one instance warm (`--min-instances=1`) but billing starts; Lambda has no persistent instance option in standard mode. For Lambda, consider GraalVM native images or SnapStart (AWS-managed CRaC snapshot) to keep cold-start tolerable.

> **Never embed credentials in the JAR.** Each platform has a secrets mechanism: AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, Kubernetes Secrets, CF `cf set-env`. Spring Boot's `spring-cloud-*` integrations pull secrets into the environment automatically — use them rather than property files with cleartext passwords.

- Build the OCI image once with `mvn -Pnative spring-boot:build-image` or `mvn spring-boot:build-image`, then push to a registry; all platforms pull from it.
- Test graceful shutdown locally: `kill -SIGTERM $(pgrep -f myapp)` and watch active requests complete.
- Use Spring Boot Actuator's `/actuator/info` endpoint to expose the build version — invaluable for verifying which version is deployed.
- For Kubernetes, add a `startupProbe` with a longer `failureThreshold` for apps with slow startup (e.g., large JVM apps on first boot).
- Enable distributed tracing (`spring-boot-starter-actuator` + `micrometer-tracing`) — all major clouds pick up trace IDs from `stdout` automatically.
