---
card: microservices
gi: 471
slug: spring-boot-docker-support
title: "Spring Boot Docker support"
---

## 1. What it is

**Spring Boot Docker support** refers to the built-in tooling Spring Boot provides for containerizing an application without leaving the ecosystem — this includes `docker-compose` file generation for local development (spinning up a database or message broker alongside your app), and the plugin support for `bootBuildImage` covered separately. Where [Cloud Native Buildpacks](0470-spring-boot-cloud-native-buildpacks-bootbuildimage.md) focus on producing the production image, "Docker support" more broadly covers Spring Boot's integration points with Docker as a development and packaging tool.

## 2. Why & when

You lean on Spring Boot's Docker support whenever local development needs to closely mirror the production environment, and setting that up manually would be repetitive:

- **Local development needs real dependencies, not mocks, for a realistic dev loop.** Spring Boot's Docker Compose support can automatically start a real PostgreSQL, Redis, or Kafka container when you run your application locally, and stop it when you're done — so `./gradlew bootRun` gives you the actual database, not a stand-in.
- **"Works on my machine" problems shrink when the machine runs the same containers CI and production use.** A developer running the exact same container image (or `docker-compose.yml`-declared service) locally that production eventually uses removes a whole category of environment-specific bugs.
- **You want zero-configuration service discovery for local dependencies.** Spring Boot's Docker Compose integration automatically wires up connection details (host, port, credentials) for detected services into your application's configuration — no manually copying a connection string into `application.properties` every time a container restarts with a new port.
- **You reach for this at the very start of local development on any service with external dependencies** — it's meant to remove the "first, go install and configure Postgres locally" friction every new contributor otherwise faces.

## 3. Core concept

Think of a stagehand who, the moment you start rehearsing a scene, automatically wheels out exactly the props your scene needs (a table, two chairs) and wires up the lighting to match — and wheels them away again the instant rehearsal ends — versus you having to manually fetch, set up, and later put away every prop yourself before you can even start practicing. Spring Boot's Docker support is that stagehand for local development dependencies.

Concretely:

1. **A `docker-compose.yml` (or Spring Boot's Compose support) declares the services your application depends on** — a database, a cache, a message broker — each with an image and configuration.
2. **When you start the application locally, Spring Boot detects the compose file** and, if the declared services aren't already running, starts them automatically as containers.
3. **Spring Boot inspects the running containers** to extract their actual connection details (the container's assigned host and port), and **automatically configures your application's `DataSource` (or equivalent) to point at them** — no manual property file editing.
4. **When you stop the application, Spring Boot can automatically stop the containers it started**, cleaning up after itself so your machine isn't left running services you're not actively using.
5. **This is purely a development-time convenience** — the production image (built via `bootBuildImage` or a `Dockerfile`) has no dependency on Docker Compose at all; it's an entirely separate, unrelated deployment artifact.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Starting a Spring Boot application locally automatically starts declared Docker Compose services and wires their connection details into the application">
  <rect x="20" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="100" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">./gradlew bootRun</text>
  <text x="100" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">detects docker-compose.yml</text>

  <rect x="240" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">postgres container</text>
  <text x="320" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">auto-started</text>

  <rect x="460" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="540" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DataSource config</text>
  <text x="540" y="112" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">auto-wired, no manual edit</text>

  <line x1="180" y1="100" x2="240" y2="100" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="400" y1="100" x2="460" y2="100" stroke="#8b949e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Starting the application starts its declared dependency containers automatically, and their real connection details are wired into the application without manual configuration.

## 5. Runnable example

We can't launch real Docker containers here, but the specific mechanic worth demonstrating — a running service's dependencies being auto-detected, auto-configured, and auto-cleaned-up on shutdown — is a plain lifecycle we can simulate directly. We start with a basic auto-start of one declared dependency, extend it to auto-wiring its connection details into application config, then handle the hard case: a dependency container that's already running from a previous session, which must be reused rather than started twice.

### Level 1 — Basic

```java
// File: DockerComposeAutoStartBasic.java -- models starting an
// application and having its ONE declared dependency container
// AUTOMATICALLY started, with no manual docker command run by the developer.
import java.util.*;

public class DockerComposeAutoStartBasic {
    record ComposeService(String name, String image) {}

    static Map<String, Boolean> runningContainers = new HashMap<>();

    static void startDeclaredServices(List<ComposeService> services) {
        for (ComposeService service : services) {
            System.out.println("[compose] starting container for " + service.name() + " (" + service.image() + ")");
            runningContainers.put(service.name(), true);
        }
    }

    public static void main(String[] args) {
        List<ComposeService> declaredServices = List.of(new ComposeService("postgres", "postgres:16"));

        System.out.println("[app] starting application -- detected docker-compose.yml");
        startDeclaredServices(declaredServices);
        System.out.println("[app] application started, dependency containers: " + runningContainers);
    }
}
```

How to run: `java DockerComposeAutoStartBasic.java`

`startDeclaredServices` is called automatically as part of application startup in `main`, with no separate manual step — the developer runs one command (`bootRun`, modeled here as the whole `main` method), and the dependency container comes up as a side effect, exactly like Spring Boot's real Compose integration.

### Level 2 — Intermediate

```java
// File: DockerComposeAutoWireBasic.java -- the SAME auto-start, now
// EXTENDED to auto-WIRE the started container's connection details
// directly into application configuration -- no manual property editing.
import java.util.*;

public class DockerComposeAutoWireBasic {
    record ComposeService(String name, String image) {}
    record ContainerInfo(String host, int port) {}

    static Map<String, ContainerInfo> runningContainers = new HashMap<>();
    static Map<String, String> appConfig = new HashMap<>();

    static void startDeclaredServices(List<ComposeService> services) {
        int assignedPort = 54320; // simulated: Docker assigns an ephemeral host port
        for (ComposeService service : services) {
            ContainerInfo info = new ContainerInfo("localhost", assignedPort++);
            System.out.println("[compose] started " + service.name() + " at " + info.host() + ":" + info.port());
            runningContainers.put(service.name(), info);
        }
    }

    static void autoWireConfig() {
        for (Map.Entry<String, ContainerInfo> entry : runningContainers.entrySet()) {
            ContainerInfo info = entry.getValue();
            String jdbcUrl = "jdbc:postgresql://" + info.host() + ":" + info.port() + "/appdb";
            appConfig.put("spring.datasource.url", jdbcUrl);
            System.out.println("[app] auto-wired spring.datasource.url = " + jdbcUrl);
        }
    }

    public static void main(String[] args) {
        List<ComposeService> declaredServices = List.of(new ComposeService("postgres", "postgres:16"));
        startDeclaredServices(declaredServices);
        autoWireConfig();
        System.out.println("[app] using config: " + appConfig);
    }
}
```

How to run: `java DockerComposeAutoWireBasic.java`

`startDeclaredServices` records each container's actual assigned host and port in `runningContainers`, and `autoWireConfig` reads that same map to construct the real JDBC URL, writing it into `appConfig` — the developer never typed `spring.datasource.url` anywhere; it was derived entirely from the container's actual, just-started state.

### Level 3 — Advanced

```java
// File: DockerComposeReuseExisting.java -- the SAME auto-start-and-wire
// flow, now handling the PRODUCTION-FLAVORED hard case: a dependency
// container is ALREADY RUNNING from a previous session (the developer
// stopped their app but left the container up, or restarted quickly).
// Starting a SECOND postgres container would waste resources and cause
// port conflicts -- the logic must detect the existing container and
// REUSE it instead of starting a duplicate.
import java.util.*;

public class DockerComposeReuseExisting {
    record ComposeService(String name, String image) {}
    record ContainerInfo(String host, int port, boolean reused) {}

    static Map<String, ContainerInfo> runningContainers = new HashMap<>();

    // Simulates querying Docker for already-running containers matching a compose service.
    static ContainerInfo findExistingContainer(String serviceName) {
        if (serviceName.equals("postgres")) {
            // Simulates: a postgres container from a previous session is still up.
            return new ContainerInfo("localhost", 54320, true);
        }
        return null;
    }

    static void startOrReuse(List<ComposeService> services) {
        int nextNewPort = 54330;
        for (ComposeService service : services) {
            ContainerInfo existing = findExistingContainer(service.name());
            if (existing != null) {
                System.out.println("[compose] found EXISTING container for " + service.name()
                        + " at " + existing.host() + ":" + existing.port() + " -- reusing, not starting a new one");
                runningContainers.put(service.name(), existing);
            } else {
                ContainerInfo fresh = new ContainerInfo("localhost", nextNewPort++, false);
                System.out.println("[compose] no existing container for " + service.name() + " -- starting new one at " + fresh.host() + ":" + fresh.port());
                runningContainers.put(service.name(), fresh);
            }
        }
    }

    public static void main(String[] args) {
        List<ComposeService> declaredServices = List.of(
            new ComposeService("postgres", "postgres:16"),
            new ComposeService("redis", "redis:7")
        );

        startOrReuse(declaredServices);

        System.out.println();
        System.out.println("[summary] final container state:");
        for (Map.Entry<String, ContainerInfo> entry : runningContainers.entrySet()) {
            ContainerInfo info = entry.getValue();
            System.out.println("  " + entry.getKey() + ": " + info.host() + ":" + info.port()
                    + (info.reused() ? " (REUSED existing container)" : " (freshly started)"));
        }
    }
}
```

How to run: `java DockerComposeReuseExisting.java`

`findExistingContainer` simulates checking Docker's actual state before starting anything — for `"postgres"`, it returns a non-null `ContainerInfo` marked `reused = true`, standing in for a container left running from a prior session. `startOrReuse` branches on that result: when `existing` is non-null it's reused directly with no new container started; only when it's `null` (as for `"redis"`, which has no matching case in `findExistingContainer`) does the code assign a fresh port and start a genuinely new container.

## 6. Walkthrough

Trace `DockerComposeReuseExisting.main` in order. **First**, `declaredServices` lists two services, `postgres` and `redis`, and `startOrReuse` begins iterating them.

**Next**, for `postgres`, `findExistingContainer("postgres")` runs its `if` check, matches, and returns a `ContainerInfo` with `reused = true` at port `54320` — simulating Docker reporting that a container matching this service is already up. Back in `startOrReuse`, `existing` is non-null, so the reuse branch runs: it prints the "found EXISTING container" message and stores that same `ContainerInfo` directly into `runningContainers`, with `nextNewPort` left completely untouched.

**Then**, for `redis`, `findExistingContainer("redis")` falls through the `if` (which only matches `"postgres"`) and returns `null`. Back in `startOrReuse`, `existing` is `null`, so the fresh-start branch runs instead: a new `ContainerInfo` is constructed at `nextNewPort` (`54330`), marked `reused = false`, printed, and stored — and `nextNewPort` increments for any subsequent service that might need a fresh container.

**After that**, the loop ends having processed both services through two different paths within the same method, based entirely on what `findExistingContainer` reported for each.

**Finally**, `main`'s summary loop prints both entries from `runningContainers`, clearly labeling `postgres` as reused and `redis` as freshly started — demonstrating that the exact same `startOrReuse` call correctly handled a mix of already-running and not-yet-running dependencies in a single pass, without wasting resources on a duplicate `postgres` container.

```
[compose] found EXISTING container for postgres at localhost:54320 -- reusing, not starting a new one
[compose] no existing container for redis -- starting new one at localhost:54330

[summary] final container state:
  postgres: localhost:54320 (REUSED existing container)
  redis: localhost:54330 (freshly started)
```

## 7. Gotchas & takeaways

> Forgetting to check for an already-running container before starting a "new" one is a subtle but real cost multiplier in local development — repeatedly starting duplicate database containers across restarts wastes memory and, worse, can leave a developer debugging against a *stale* container while writing data into a fresh, empty one they didn't realize was newly created.
- Docker Compose support is strictly a development-time convenience — it has no bearing on how the production image is built or deployed; that's the separate concern [Cloud Native Buildpacks](0470-spring-boot-cloud-native-buildpacks-bootbuildimage.md) or a `Dockerfile` handles.
- Auto-wiring connection details removes an entire class of "I forgot to update my local `application.properties` after the container restarted on a new port" bugs — the configuration is always derived from the container's actual current state.
- Reuse logic (Level 3) matters for a smooth developer loop — being able to stop and restart an application repeatedly without repeatedly tearing down and rebuilding a database container (and losing its data) each time is a real productivity win.
- This tooling is meant to lower the barrier for new contributors: cloning a repo and running one command should be enough to get a fully working local environment, dependencies included, with zero manual setup steps documented in a README.
- Keep the `docker-compose.yml` used for local development honest about what production actually depends on — a local setup missing a dependency production has (or including one it doesn't) undermines the entire "dev mirrors prod" benefit this tooling exists to provide.
