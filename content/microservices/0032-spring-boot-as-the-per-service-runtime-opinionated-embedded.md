---
card: microservices
gi: 32
slug: spring-boot-as-the-per-service-runtime-opinionated-embedded
title: "Spring Boot as the per-service runtime (opinionated, embedded server)"
---

## 1. What it is

**Spring Boot** is the most common runtime choice for an individual microservice in the Java ecosystem, specifically because of two properties that matter enormously once you're running many independent services rather than one application: it's **opinionated** (sensible defaults for almost everything, so a new service doesn't need bespoke configuration decisions made from scratch every time), and it **embeds its own server** (a service is a self-contained, directly-runnable `.jar` with an HTTP server built in — `java -jar service.jar` and it's listening — rather than a `.war` file that needs to be deployed into a separately-installed, separately-managed application server).

```java
@SpringBootApplication
public class OrderServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }
}
```

## 2. Why & when

Before embedded servers, deploying a Java web application meant installing and configuring a separate application server (Tomcat, JBoss, WebSphere) on the target machine, then deploying your application's `.war` file into it — a shared piece of infrastructure that had to be provisioned, versioned, and kept consistent across every machine, separately from your application code. That model is workable for one application; it becomes real friction once you have many independently deployed services, each potentially needing a different server version or configuration, all competing for space on shared infrastructure.

Spring Boot's embedded server flips this: the server (by default, an embedded Tomcat) is a dependency of your application, packaged inside the same `.jar` your build produces. Reach for Spring Boot as your default per-service runtime in a Java-based microservices system specifically because this matches the "one service, one independently deployable, self-contained unit" goal directly — no separately-managed server to provision, version, or keep in sync across services.

## 3. Core concept

The structural shift: a service's deployable artifact is no longer "code that gets deployed into a server" — it *is* the server, plus the code, in one file.

- **Old model:** `orders.war` gets deployed into a shared, separately-installed Tomcat instance. The server's lifecycle is independent of the application's.
- **Spring Boot model:** `orders-service.jar` contains the application code *and* an embedded Tomcat instance. Running `java -jar orders-service.jar` starts both together, as one process, with one lifecycle.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A WAR file deploys into a separately managed, shared Tomcat instance; a Spring Boot JAR bundles its own embedded server inside one self-contained artifact">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Traditional WAR</text>
  <rect x="30" y="60" width="80" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">orders.war</text>
  <line x1="110" y1="77" x2="150" y2="77" stroke="#8b949e" marker-end="url(#a32)"/>
  <rect x="160" y="40" width="120" height="75" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="220" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">shared Tomcat</text>
  <text x="220" y="82" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">separately installed</text>
  <text x="220" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">separately versioned</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Spring Boot JAR</text>
  <rect x="410" y="40" width="180" height="75" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">orders-service.jar</text>
  <text x="500" y="85" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">app code + embedded Tomcat</text>
  <text x="500" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ONE self-contained file</text>
  <defs><marker id="a32" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A WAR needs a separately managed server to deploy into; a Spring Boot JAR carries its own server inside it.

## 5. Runnable example

Scenario: modeling the two deployment approaches, first as a fragile shared-server dependency, then as a self-contained artifact, then extended to show two services each embedding their own independently-versioned server with zero shared infrastructure.

### Level 1 — Basic

```java
// File: SharedServerModel.java -- models the OLD approach: an app depends
// on a SEPARATELY managed, shared server instance to even start.
public class SharedServerModel {
    static class SharedTomcatInstance {
        String version;
        boolean running = false;
        SharedTomcatInstance(String version) { this.version = version; }
        void start() { running = true; System.out.println("Shared Tomcat " + version + " started"); }
    }

    static class OrdersWar {
        SharedTomcatInstance server; // depends on an EXTERNALLY provisioned server
        OrdersWar(SharedTomcatInstance server) { this.server = server; }
        void deploy() {
            if (!server.running) throw new IllegalStateException("Cannot deploy: shared Tomcat is not running yet");
            System.out.println("orders.war deployed into shared Tomcat " + server.version);
        }
    }

    public static void main(String[] args) {
        SharedTomcatInstance tomcat = new SharedTomcatInstance("9.0"); // must be provisioned FIRST, separately
        tomcat.start();
        new OrdersWar(tomcat).deploy();
    }
}
```

**How to run:** `javac SharedServerModel.java && java SharedServerModel` (JDK 17+).

Expected output:
```
Shared Tomcat 9.0 started
orders.war deployed into shared Tomcat 9.0
```

`OrdersWar.deploy()` explicitly requires an already-running `SharedTomcatInstance`, provisioned as a separate step before the application can even be deployed. If a second application (`PaymentsWar`) needed a different Tomcat version, this shared instance couldn't serve both — a genuine operational constraint of the old model.

### Level 2 — Intermediate

```java
// File: EmbeddedServerModel.java -- the Spring Boot approach: the server
// is BUNDLED with the application, one self-contained artifact.
public class EmbeddedServerModel {
    static class OrdersServiceJar {
        String embeddedTomcatVersion = "10.1"; // bundled AS PART OF this artifact, not externally provisioned
        boolean running = false;

        void run() { // models `java -jar orders-service.jar`
            System.out.println("Starting embedded Tomcat " + embeddedTomcatVersion + " (bundled inside this JAR)");
            running = true;
            System.out.println("orders-service.jar running -- application AND server started together, one process");
        }
    }

    public static void main(String[] args) {
        new OrdersServiceJar().run(); // ONE command, ONE artifact, no separate server provisioning step
    }
}
```

**How to run:** `javac EmbeddedServerModel.java && java EmbeddedServerModel` (JDK 17+).

Expected output:
```
Starting embedded Tomcat 10.1 (bundled inside this JAR)
orders-service.jar running -- application AND server started together, one process
```

There's no separate `SharedTomcatInstance` to provision first — `OrdersServiceJar.run()` starts its own embedded server as part of starting the application itself. This mirrors `java -jar orders-service.jar`, Spring Boot's actual deployment model: one command, one self-contained artifact.

### Level 3 — Advanced

```java
// File: TwoServicesIndependentServers.java -- TWO Spring-Boot-style
// services, each with its OWN embedded server version, with ZERO
// shared server infrastructure between them -- exactly what independent
// deployability requires.
public class TwoServicesIndependentServers {
    static class SpringBootStyleService {
        String serviceName;
        String embeddedTomcatVersion; // each service picks its OWN version, independently
        boolean running = false;

        SpringBootStyleService(String serviceName, String embeddedTomcatVersion) {
            this.serviceName = serviceName;
            this.embeddedTomcatVersion = embeddedTomcatVersion;
        }

        void run() {
            running = true;
            System.out.println(serviceName + ": running with embedded Tomcat " + embeddedTomcatVersion);
        }

        void upgradeEmbeddedServer(String newVersion) {
            // upgrading THIS service's server version affects ONLY this service --
            // no shared server instance for another service to accidentally be affected by.
            this.embeddedTomcatVersion = newVersion;
            System.out.println(serviceName + ": upgraded to embedded Tomcat " + newVersion + " -- independent redeploy, no other service touched");
        }
    }

    public static void main(String[] args) {
        SpringBootStyleService orders = new SpringBootStyleService("orders-service", "10.1");
        SpringBootStyleService payments = new SpringBootStyleService("payments-service", "10.1");

        orders.run();
        payments.run();

        orders.upgradeEmbeddedServer("10.2"); // OrdersTeam upgrades their embedded server version

        System.out.println("payments-service still on: " + payments.embeddedTomcatVersion + " -- completely unaffected");
    }
}
```

**How to run:** `javac TwoServicesIndependentServers.java && java TwoServicesIndependentServers` (JDK 17+).

Expected output:
```
orders-service: running with embedded Tomcat 10.1
payments-service: running with embedded Tomcat 10.1
orders-service: upgraded to embedded Tomcat 10.2 -- independent redeploy, no other service touched
payments-service still on: 10.1 -- completely unaffected
```

The production-flavored payoff: `orders.upgradeEmbeddedServer("10.2")` changes only `orders`'s own `embeddedTomcatVersion` field. `payments`'s embedded server version stays at `10.1`, completely untouched — because each service bundles its own server, there's no shared infrastructure instance whose version both services would otherwise be forced to agree on. This is independent deployability, applied specifically to the server layer itself.

## 6. Walkthrough

1. `orders.run()` and `payments.run()` each start, printing their own service name alongside their own `embeddedTomcatVersion` — both happen to be `"10.1"` at this point, but critically, each is a separate field on a separate object, not a reference to one shared instance.
2. `orders.upgradeEmbeddedServer("10.2")` runs, reassigning `orders.embeddedTomcatVersion` from `"10.1"` to `"10.2"` — this mutation touches only the `orders` object's own field.
3. `payments.embeddedTomcatVersion` was never referenced by `upgradeEmbeddedServer`'s call on `orders` — Java's object model guarantees these are entirely independent fields on entirely independent objects, so `payments`'s value stays `"10.1"`.
4. The final print confirms this directly: `payments-service still on: 10.1` — proof that upgrading one service's embedded server (a real, common operational task — bumping a dependency version) had zero effect on the other service, because there was never a shared server instance connecting them in the first place.

```
SharedServerModel (old):        OrdersWar --+
                                             +--> ONE SharedTomcatInstance (version must be agreed by all)
                                 PaymentsWar-+

EmbeddedServerModel (Spring Boot): orders-service.jar   [own embedded Tomcat 10.2]
                                    payments-service.jar [own embedded Tomcat 10.1]   <- fully independent
```

## 7. Gotchas & takeaways

> **Gotcha:** embedding a server per service does trade away one thing the shared-server model had: a single, centrally-patched server instance meant one security fix applied once, everywhere. With embedded servers, each service's bundled server version must be tracked and patched independently — a real operational responsibility (often automated via dependency-scanning tooling) that a shared-server model didn't require in the same way.

- Spring Boot is opinionated (sensible defaults reduce per-service configuration decisions) and embeds its own server, making a service's deployable artifact self-contained rather than dependent on a separately managed, shared application server.
- The concrete shift: `java -jar service.jar` starts both the application and its server together, as one process with one lifecycle — no separate server provisioning step required.
- Embedding the server per service is what makes upgrading or configuring one service's runtime environment fully independent of every other service — exactly matching the independent-deployability goal microservices are built around.
- The tradeoff: each service now owns responsibility for tracking and patching its own bundled server version, rather than relying on one centrally-managed, shared instance.
