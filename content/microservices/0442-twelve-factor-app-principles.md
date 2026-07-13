---
card: microservices
gi: 442
slug: twelve-factor-app-principles
title: "Twelve-factor app principles"
---

## 1. What it is

The **twelve-factor app** is a widely adopted set of principles, originally articulated by developers at Heroku, for building applications that deploy cleanly and scale reliably on modern cloud platforms. It's not a framework or a library — it's a checklist of good habits: keep one codebase per app, declare dependencies explicitly, store configuration in the environment, treat backing services as attachable resources, build and run as strictly separate stages, run the app as stateless processes, export services via port binding, scale out via the process model, maximize robustness with fast startup and graceful shutdown, keep dev/staging/production as similar as possible, treat logs as event streams, and run admin tasks as one-off processes. Container orchestrators and microservices architectures assume most of these by default — they're less "advice" today and more "the baseline every containerized service is expected to satisfy."

## 2. Why & when

The principles matter because they describe exactly the properties an orchestrator, a CI/CD pipeline, and a horizontally scaled fleet all depend on being true:

- **Portability across environments.** An app that hardcodes environment-specific values or depends on local disk state can't move cleanly between a developer's laptop, staging, and production — the twelve-factor discipline is largely about removing every assumption that ties an app to one specific place it runs.
- **Horizontal scalability.** [Service instance per container](0435-service-instance-per-container.md) assumes you can start a fifth identical instance of a service at any moment and have it work correctly from the first request — which is only true if the process is stateless and gets its configuration from its environment, not from local files someone configured by hand on one specific machine.
- **Fast, reliable deploys and rollbacks.** Principles like strict build/run separation and disposability (fast startup, graceful shutdown) are exactly what makes rolling deployments, autoscaling, and rollback fast and safe — see [graceful startup & shutdown](0444-graceful-startup-shutdown.md).
- **Operational sanity at scale.** Treating logs as an event stream (writing to stdout, letting the platform aggregate them) rather than managing log files per instance is what makes centralized log aggregation across dozens of container instances tractable at all.

You apply these principles to essentially every microservice you build for containerized, cloud-native deployment — they're less a decision you make per project and more a baseline you check a new service against before it's considered production-ready.

## 3. Core concept

Think of the twelve factors as the rules a hotel imposes on every room so any guest can check into any room and have it work identically. A hotel room has no personal photos permanently glued to the wall (no baked-in, environment-specific state), the thermostat and lighting are controlled from outside sources the room itself doesn't hardcode (externalized configuration), housekeeping can fully reset a room between guests in minutes (fast startup, statelessness), and the room's "output" — noise, water usage — is metered externally by the hotel's systems rather than the room needing to track its own history (logs as an event stream, consumed by the platform). A guest who tried to make a specific room permanently "theirs" — storing things under the floorboards, rewiring the thermostat — would break the hotel's ability to swap rooms freely, exactly as a service that stores state on local disk breaks an orchestrator's ability to freely replace one instance with another.

The twelve factors, grouped by what they're actually protecting:

1. **Codebase** — one codebase tracked in version control, many deploys (dev, staging, prod all trace back to the same source).
2. **Dependencies** — explicitly declared and isolated (a `pom.xml`/`build.gradle`, not "whatever happens to be installed on this machine").
3. **Config** — stored in the environment (see [externalized config & stateless processes](0443-externalized-config-stateless-processes.md)), never hardcoded or checked into source control.
4. **Backing services** — treated as attached resources (a database, a message broker) swappable via configuration without code changes.
5. **Build, release, run** — strictly separated stages; a built artifact never mutates once released.
6. **Processes** — stateless and share-nothing; anything that must persist goes to a backing service, not local memory or disk.
7. **Port binding** — the app is self-contained and exports its service via a port, not dependent on a runtime-injected web server.
8. **Concurrency** — scale out via the process model (more instances), not by making one instance juggle more internally.
9. **Disposability** — fast startup, graceful shutdown (see [graceful startup & shutdown](0444-graceful-startup-shutdown.md)) — instances are cheap to create and destroy.
10. **Dev/prod parity** — keep environments as similar as possible to avoid "works here, breaks there" surprises.
11. **Logs** — treated as event streams written to stdout, not managed as files by the app itself.
12. **Admin processes** — one-off admin/maintenance tasks run in the same environment, using the same codebase and config, as the app itself.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Twelve factor principles cluster around four themes: source and dependencies, configuration and backing services, process behavior, and operability, all supporting the same goal of portable, horizontally scalable deployment" >
  <rect x="20" y="20" width="280" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="160" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Source &amp; dependencies</text>
  <text x="160" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1. codebase</text>
  <text x="160" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2. dependencies</text>
  <text x="160" y="86" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">5. build/release/run</text>

  <rect x="340" y="20" width="280" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="480" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Config &amp; backing services</text>
  <text x="480" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">3. config</text>
  <text x="480" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">4. backing services</text>
  <text x="480" y="86" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">10. dev/prod parity</text>

  <rect x="20" y="115" width="280" height="80" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="160" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Process behavior</text>
  <text x="160" y="153" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">6. stateless processes</text>
  <text x="160" y="167" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">7. port binding</text>
  <text x="160" y="181" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">8. concurrency (scale out)</text>

  <rect x="340" y="115" width="280" height="80" rx="8" fill="#f0883e" fill-opacity="0.15" stroke="#f0883e" stroke-width="2"/>
  <text x="480" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Operability</text>
  <text x="480" y="153" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">9. disposability</text>
  <text x="480" y="167" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">11. logs as event streams</text>
  <text x="480" y="181" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">12. admin processes</text>

  <text x="320" y="225" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">all twelve exist to make an instance portable, replaceable, and horizontally scalable</text>
</svg>

The twelve factors cluster around four themes, all in service of the same goal: an instance that can be created, replaced, or scaled anywhere without special handling.

## 5. Runnable example

Scenario: an `order-service` that starts life violating several twelve-factor principles, and gets fixed one factor at a time. We model a service with hardcoded config and local file state first (violating factors 3 and 6), then externalize config and remove local state, then handle a production-flavored case: verifying a fleet of "identical" instances actually behaves identically because none of them silently depend on local, instance-specific state.

### Level 1 — Basic

```java
// File: TwelveFactorViolationsBasic.java -- models a service VIOLATING
// factor 3 (config in the environment) and factor 6 (stateless processes),
// making it break the moment it's deployed to a second, different environment.
import java.util.*;

public class TwelveFactorViolationsBasic {
    static class OrderServiceViolating {
        // VIOLATION of factor 3: config hardcoded directly in source code.
        static final String DATABASE_URL = "jdbc:postgresql://localhost:5432/orders_dev";

        // VIOLATION of factor 6: in-memory state that only this ONE instance knows about.
        final Map<String, String> localSessionCache = new HashMap<>();

        void handleRequest(String sessionId, String orderId) {
            localSessionCache.put(sessionId, orderId);
            System.out.println("Handled request for session " + sessionId + " on THIS instance, using DB " + DATABASE_URL);
        }

        boolean sessionKnownHere(String sessionId) {
            return localSessionCache.containsKey(sessionId);
        }
    }

    public static void main(String[] args) {
        OrderServiceViolating instanceA = new OrderServiceViolating();
        instanceA.handleRequest("session-42", "order-1");

        OrderServiceViolating instanceB = new OrderServiceViolating(); // a second "instance" (e.g. scaled out)
        System.out.println("Does instance B know about session-42? " + instanceB.sessionKnownHere("session-42")
                + " -- a load balancer routing the NEXT request for session-42 to instance B would lose it entirely.");
        System.out.println("Would DATABASE_URL work outside 'dev'? No -- it's hardcoded, so staging/prod need a DIFFERENT BUILD to point elsewhere.");
    }
}
```

How to run: `java TwelveFactorViolationsBasic.java`

`DATABASE_URL` is baked into the source as a constant — deploying to staging or production would require a different compiled artifact per environment, directly violating factor 3 (config in the environment) and factor 10 (dev/prod parity, since environments now differ by more than just configuration). `localSessionCache` lives only in one instance's memory — `instanceB` has no knowledge of a session `instanceA` handled, which is exactly the kind of state that breaks horizontal scaling and load-balanced traffic.

### Level 2 — Intermediate

```java
// File: TwelveFactorFixedIntermediate.java -- the SAME service, now FIXED:
// config comes from the environment (factor 3), and session state moves to
// a shared backing service instead of local memory (factors 4 and 6).
import java.util.*;

public class TwelveFactorFixedIntermediate {
    // A stand-in for a real shared backing service (e.g. Redis) -- shared by
    // ALL instances, so no instance holds state the others can't see.
    static class SharedSessionStore {
        private final Map<String, String> sessions = new HashMap<>();
        void put(String sessionId, String orderId) { sessions.put(sessionId, orderId); }
        boolean contains(String sessionId) { return sessions.containsKey(sessionId); }
    }

    static class OrderServiceFixed {
        final String databaseUrl; // factor 3: injected, not hardcoded
        final SharedSessionStore sharedStore; // factor 4 + 6: externalized state

        OrderServiceFixed(Map<String, String> env, SharedSessionStore sharedStore) {
            this.databaseUrl = env.getOrDefault("DATABASE_URL", "jdbc:postgresql://localhost:5432/orders_dev");
            this.sharedStore = sharedStore;
        }

        void handleRequest(String sessionId, String orderId) {
            sharedStore.put(sessionId, orderId);
            System.out.println("Handled request for session " + sessionId + " using DB " + databaseUrl);
        }
    }

    public static void main(String[] args) {
        SharedSessionStore shared = new SharedSessionStore();

        Map<String, String> prodEnv = Map.of("DATABASE_URL", "jdbc:postgresql://prod-db.internal:5432/orders");
        OrderServiceFixed instanceA = new OrderServiceFixed(prodEnv, shared);
        OrderServiceFixed instanceB = new OrderServiceFixed(prodEnv, shared);

        instanceA.handleRequest("session-42", "order-1");
        System.out.println("Does instance B (via the SHARED store) know about session-42? " + shared.contains("session-42")
                + " -- because state lives outside any single instance, either instance can serve the next request correctly.");
        System.out.println("instanceA.databaseUrl == instanceB.databaseUrl: " + instanceA.databaseUrl.equals(instanceB.databaseUrl)
                + " -- SAME artifact, config supplied by the environment, works unchanged in prod.");
    }
}
```

How to run: `java TwelveFactorFixedIntermediate.java`

`databaseUrl` is now read from an injected `env` map (standing in for real OS environment variables) at construction time — the exact same class works in dev or prod depending only on what environment it's launched with, with zero code or artifact changes. `sharedStore` replaces per-instance local state with a shared backing service both instances read from and write to — `instanceB` correctly reports knowing about a session `instanceA` handled, because the state was never tied to either instance in the first place.

### Level 3 — Advanced

```java
// File: FleetConsistencyAuditAdvanced.java -- the SAME fixed service, now
// handling a PRODUCTION-FLAVORED hard case: auditing a whole FLEET to prove
// every instance is truly stateless and interchangeable, by routing the
// SAME session's requests to DIFFERENT instances and confirming consistency.
import java.util.*;

public class FleetConsistencyAuditAdvanced {
    static class SharedSessionStore {
        private final Map<String, String> sessions = new HashMap<>();
        void put(String sessionId, String orderId) { sessions.put(sessionId, orderId); }
        String get(String sessionId) { return sessions.get(sessionId); }
    }

    static class OrderServiceFixed {
        final String instanceId;
        final String databaseUrl;
        final SharedSessionStore sharedStore;

        OrderServiceFixed(String instanceId, Map<String, String> env, SharedSessionStore sharedStore) {
            this.instanceId = instanceId;
            this.databaseUrl = env.get("DATABASE_URL");
            this.sharedStore = sharedStore;
        }

        void handleRequest(String sessionId, String orderId) {
            sharedStore.put(sessionId, orderId);
            System.out.println("[" + instanceId + "] wrote session " + sessionId + " -> " + orderId);
        }

        String readRequest(String sessionId) {
            String value = sharedStore.get(sessionId);
            System.out.println("[" + instanceId + "] read session " + sessionId + " -> " + value);
            return value;
        }
    }

    public static void main(String[] args) {
        SharedSessionStore shared = new SharedSessionStore();
        Map<String, String> prodEnv = Map.of("DATABASE_URL", "jdbc:postgresql://prod-db.internal:5432/orders");

        // A fleet of five IDENTICAL instances, launched from the SAME image
        // with the SAME environment -- differing only in instanceId.
        List<OrderServiceFixed> fleet = new ArrayList<>();
        for (int i = 1; i <= 5; i++) fleet.add(new OrderServiceFixed("instance-" + i, prodEnv, shared));

        // A load balancer routes a session's write to one random instance,
        // then (as real load balancers do) routes the FOLLOW-UP read to a
        // DIFFERENT instance entirely.
        OrderServiceFixed writer = fleet.get(2);
        OrderServiceFixed reader = fleet.get(4);

        writer.handleRequest("session-99", "order-77");
        String readBack = reader.readRequest("session-99");

        boolean consistent = "order-77".equals(readBack);
        boolean allInstancesShareConfig = fleet.stream().allMatch(inst -> inst.databaseUrl.equals(prodEnv.get("DATABASE_URL")));

        System.out.println("Write/read routed to DIFFERENT instances, still consistent: " + consistent);
        System.out.println("Every instance in the fleet shares identical config: " + allInstancesShareConfig
                + " -- this is what makes it safe for a load balancer to route ANY request to ANY instance.");
    }
}
```

How to run: `java FleetConsistencyAuditAdvanced.java`

The hard case a real load balancer creates is that consecutive requests from the same client are not guaranteed to hit the same instance. `writer` (`instance-3`) handles the write; `reader` (`instance-5`) handles the follow-up read for the same session — a scenario Level 1's local-memory design would have silently broken. Because `sharedStore` is external to every instance and every instance's `databaseUrl` comes from the same injected environment, both the read-after-write consistency check and the config-uniformity check pass, concretely demonstrating that the fleet is safe to treat as a set of interchangeable, statelessly-behaving instances.

## 6. Walkthrough

Trace `FleetConsistencyAuditAdvanced.main` in order. **First**, `shared`, one `SharedSessionStore`, is created, and `fleet` is populated with five `OrderServiceFixed` instances, each constructed with the identical `prodEnv` map and a reference to the same `shared` store — only `instanceId` differs between them.

**Next**, `writer` is bound to `fleet.get(2)` (`instance-3`) and `reader` to `fleet.get(4)` (`instance-5`) — modeling a load balancer sending two related requests to two different physical instances, which is realistic behavior for any stateless round-robin or least-connections load-balancing strategy.

**Then**, `writer.handleRequest("session-99", "order-77")` calls `sharedStore.put("session-99", "order-77")` — the write lands in the shared store, not in `writer`'s own memory. `reader.readRequest("session-99")` then calls `sharedStore.get("session-99")` on the *same* shared store instance — since `reader` and `writer` both hold a reference to the identical `shared` object, the value written by one is immediately visible to the other.

**Finally**, `consistent` checks that the value read back (`"order-77"`) matches what was written, which is `true` — the read-after-write succeeded despite crossing instance boundaries. `allInstancesShareConfig` verifies every instance in `fleet` has the identical `databaseUrl`, which is `true` since they were all constructed from the same `prodEnv`. Both checks passing together is the concrete proof that this fleet satisfies factor 6 (stateless processes) and factor 3 (config in the environment): no instance carries private state or private configuration that would make it behave differently from its siblings.

```
[instance-3] wrote session session-99 -> order-77
[instance-5] read session session-99 -> order-77
Write/read routed to DIFFERENT instances, still consistent: true
Every instance in the fleet shares identical config: true -- this is what makes it safe for a load balancer to route ANY request to ANY instance.
```

## 7. Gotchas & takeaways

> Twelve-factor statelessness doesn't mean an instance can never hold anything in memory — request-scoped, transient state (a variable that lives only for the duration of handling one request) is completely fine. The violation is state that must *persist across requests or across instances* being kept only in one instance's local memory or local disk; the fix is always to externalize that specific state to a shared backing service, not to avoid using memory altogether.

- Config in the environment (factor 3) is what lets the exact same built artifact run correctly in dev, staging, and production — see [externalized config & stateless processes](0443-externalized-config-stateless-processes.md) for the concrete mechanics in Spring Boot.
- Statelessness (factor 6) is what makes horizontal scaling and load-balanced traffic safe — any instance must be able to handle any request without depending on what a different instance previously did.
- Disposability (factor 9) — fast startup and graceful shutdown — is what makes rolling deployments and autoscaling fast and safe; see [graceful startup & shutdown](0444-graceful-startup-shutdown.md).
- These principles aren't independent checkboxes — violating one (like hardcoding config) often forces violating another (like dev/prod parity, since environments now need different builds) as a side effect.
- Spring Boot's design leans heavily twelve-factor-native already: externalized `application.yml` properties overridable by environment variables, stateless `@RestController`s by convention, and Actuator endpoints for health and admin tasks all map directly onto specific factors.
