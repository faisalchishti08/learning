---
card: microservices
gi: 188
slug: health-check-based-registration
title: "Health-check-based registration"
---

## 1. What it is

Health-check-based registration ties an instance's visibility in the [service registry](0182-service-registry-concept.md) to the outcome of an ongoing health check, not merely to whether the instance's process is running — an instance can be up, registered, and even sending heartbeats, but if its health check reports it unhealthy (a failing dependency, an overloaded internal queue, a degraded internal state), it's excluded from the pool of instances callers are routed to until the health check passes again.

## 2. Why & when

An instance's process being alive is a necessary but insufficient condition for it being safe to send traffic to — a process can be technically running while its database connection pool is exhausted, a critical dependency is unreachable, or its internal state is otherwise degraded enough that it would fail most requests sent its way. Registering purely based on process liveness (or even basic heartbeat presence) would route traffic to instances that are "up" but not actually able to serve it correctly. Health-check-based registration closes this gap by making an instance's *registered, routable* status conditional on an actual application-level health assessment, not just process existence.

Use health-check-based registration for any instance where "the process is running" and "the instance can actually serve requests correctly" are meaningfully different conditions — which describes essentially any real service with external dependencies (a database, another service, a cache). A trivial, dependency-free service might reasonably treat process liveness as sufficient, but this is the exception, not the default.

## 3. Core concept

A health check endpoint (or internal check function) reports the instance's current ability to serve traffic correctly, incorporating whatever dependency and internal-state checks are relevant; the registry (or a registrar polling that endpoint) uses this health status, not just process liveness, to decide whether the instance is included in the pool of routable instances.

```java
// health check reflects ACTUAL serviceability, not just "is the process running"
@GetMapping("/health")
HealthStatus checkHealth() {
    boolean dbReachable = databasePool.isHealthy();
    boolean dependencyReachable = paymentServiceClient.ping();
    return (dbReachable && dependencyReachable) ? HealthStatus.UP : HealthStatus.DOWN;
}

// the REGISTRY (or a registrar) polls this, and EXCLUDES the instance from routing when DOWN
if (healthCheck() != HealthStatus.UP) registry.markUnavailable(instanceId); // process is STILL running -- just not ROUTABLE
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An instance's process is running throughout, but its health check fails when its database connection is lost; during that period it remains registered but is excluded from routing, and becomes routable again once the health check passes" >
  <rect x="20" y="80" width="580" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="310" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">process running, entire time</text>

  <rect x="230" y="120" width="180" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="320" y="140" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">health check FAILS (DB down)</text>

  <text x="130" y="160" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">routable</text>
  <text x="320" y="160" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">EXCLUDED from routing</text>
  <text x="500" y="160" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">routable again</text>

  <defs>
    <marker id="arr69" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The process stays up throughout, but routability is governed entirely by the health check's ongoing verdict.

## 5. Runnable example

Scenario: an order-service instance that starts with liveness-only registration (showing traffic sent to a degraded but "alive" instance), adds a health check incorporating a real dependency (a database connection) so degraded instances are excluded from routing, and finally demonstrates automatic recovery — the instance becomes routable again the moment its health check starts passing, with no manual intervention.

### Level 1 — Basic

```java
// File: LivenessOnlyRegistration.java -- registered based on the PROCESS being
// alive; a DEGRADED instance (DB unreachable) still receives traffic.
public class LivenessOnlyRegistration {
    static boolean processIsRunning = true; // the process is TECHNICALLY alive
    static boolean databaseReachable = false; // but its DATABASE connection is DOWN

    static boolean isRegisteredAndRoutable() {
        return processIsRunning; // ONLY checks liveness -- ignores actual serviceability entirely
    }

    static String handleRequest() {
        if (!databaseReachable) throw new RuntimeException("500 Internal Server Error -- database unreachable");
        return "200 OK";
    }

    public static void main(String[] args) {
        System.out.println("Instance routable: " + isRegisteredAndRoutable());
        try {
            System.out.println(handleRequest());
        } catch (RuntimeException e) {
            System.out.println("Request FAILED: " + e.getMessage() + " -- but the instance is STILL considered 'routable' by this liveness-only check.");
        }
    }
}
```

**How to run:** `javac LivenessOnlyRegistration.java && java LivenessOnlyRegistration` (JDK 17+).

### Level 2 — Intermediate

```java
// File: HealthCheckBasedRouting.java -- a REAL health check incorporates the
// database dependency; a DEGRADED instance is EXCLUDED from routing.
public class HealthCheckBasedRouting {
    enum HealthStatus { UP, DOWN }

    static boolean processIsRunning = true;
    static boolean databaseReachable = false;

    static HealthStatus checkHealth() {
        // the health check reflects ACTUAL serviceability, not just process liveness
        return databaseReachable ? HealthStatus.UP : HealthStatus.DOWN;
    }

    static boolean isRoutable() {
        return processIsRunning && checkHealth() == HealthStatus.UP; // BOTH conditions matter now
    }

    public static void main(String[] args) {
        System.out.println("Process running: " + processIsRunning + ", health check: " + checkHealth());
        System.out.println("Instance routable: " + isRoutable());
        System.out.println("The registry EXCLUDES this instance from routing -- callers are directed to OTHER, genuinely healthy instances instead.");
    }
}
```

**How to run:** `javac HealthCheckBasedRouting.java && java HealthCheckBasedRouting` (JDK 17+).

Expected output:
```
Process running: true, health check: DOWN
Instance routable: false
The registry EXCLUDES this instance from routing -- callers are directed to OTHER, genuinely healthy instances instead.
```

### Level 3 — Advanced

```java
// File: AutomaticRecoveryOnHealthRestoration.java -- the instance becomes
// ROUTABLE AGAIN the MOMENT its health check starts passing -- NO manual
// intervention, NO restart, just the registry's ONGOING health polling doing its job.
public class AutomaticRecoveryOnHealthRestoration {
    enum HealthStatus { UP, DOWN }

    static boolean processIsRunning = true;
    static boolean databaseReachable = false;

    static HealthStatus checkHealth() { return databaseReachable ? HealthStatus.UP : HealthStatus.DOWN; }
    static boolean isRoutable() { return processIsRunning && checkHealth() == HealthStatus.UP; }

    // simulates the REGISTRY (or a registrar) POLLING this health check periodically
    static void registryHealthPoll(int pollNumber) {
        boolean routable = isRoutable();
        System.out.println("Poll #" + pollNumber + ": health=" + checkHealth() + ", routable=" + routable);
    }

    public static void main(String[] args) {
        registryHealthPoll(1); // database is down -- NOT routable

        System.out.println("...5 seconds pass, database connection is DOWN...");
        registryHealthPoll(2); // still down

        System.out.println("...database connection pool RECOVERS on its own (transient network blip resolved)...");
        databaseReachable = true; // NOTHING external intervened -- the dependency just came back

        registryHealthPoll(3); // health check now PASSES -- routable AGAIN, automatically
        System.out.println("Instance became routable again with ZERO manual action -- purely from the health check's own ongoing, automatic re-evaluation.");
    }
}
```

**How to run:** `javac AutomaticRecoveryOnHealthRestoration.java && java AutomaticRecoveryOnHealthRestoration` (JDK 17+).

Expected output:
```
Poll #1: health=DOWN, routable=false
...5 seconds pass, database connection is DOWN...
Poll #2: health=DOWN, routable=false
...database connection pool RECOVERS on its own (transient network blip resolved)...
Poll #3: health=UP, routable=true
Instance became routable again with ZERO manual action -- purely from the health check's own ongoing, automatic re-evaluation.
```

## 6. Walkthrough

1. **Level 1** — `isRegisteredAndRoutable` checks only `processIsRunning`, entirely ignoring `databaseReachable`; even though `handleRequest` would throw an exception for any real request (since `databaseReachable` is `false`), the instance is still reported as `"routable"`.
2. **Level 1, the resulting failure exposed to a caller** — `main`'s call to `handleRequest()` throws, and the caught exception's message makes explicit that this failure happened *despite* the instance being considered routable, directly demonstrating the gap liveness-only registration leaves open.
3. **Level 2, the health check incorporating the real dependency** — `checkHealth` returns `HealthStatus.UP` or `DOWN` based specifically on `databaseReachable`, meaning the health verdict now reflects the instance's actual ability to serve a request correctly, not merely its process state.
4. **Level 2, routability requiring both conditions** — `isRoutable` now checks `processIsRunning && checkHealth() == HealthStatus.UP`, meaning a process that's alive but has a failing health check is correctly excluded — printed as `Instance routable: false`, directly resolving Level 1's gap.
5. **Level 3, simulating ongoing health polling** — `registryHealthPoll` represents what a real registry (or a registrar polling a health endpoint) does continuously in the background: re-evaluate `isRoutable()` and report the current verdict, called here at three distinct points in time.
6. **Level 3, the dependency recovering independently** — `databaseReachable = true` is set with no corresponding call to any "re-register" or "mark healthy" method — this models a transient dependency issue resolving on its own, entirely outside the instance's or registry's own explicit control.
7. **Level 3, the automatic recovery observed** — the third call to `registryHealthPoll` shows `health=UP, routable=true`, purely as a consequence of `checkHealth()` now evaluating differently given the updated `databaseReachable` value — no code anywhere explicitly re-registered the instance or reset any flag related to routability; the health check's next scheduled evaluation simply produced a different, correct result, and the instance's routability followed automatically from that, exactly mirroring how a real health-check-based registry continuously and automatically reflects an instance's current, actual state without requiring manual re-registration after a transient issue resolves.

## 7. Gotchas & takeaways

> **Gotcha:** a health check that's too shallow (checking only "does the process respond to an HTTP request," without actually exercising the dependencies that matter) provides false confidence — it will report `UP` even while the instance is genuinely unable to serve real requests correctly, defeating the entire purpose of health-check-based registration; a health check needs to actually exercise the specific dependencies and internal conditions that determine real serviceability, not just confirm the process can respond to *some* request.

- Health-check-based registration ties an instance's routable status to an actual health assessment of its ability to serve requests correctly, not merely to whether its process is technically running.
- This closes the gap left by liveness-only registration, where a degraded instance (a failing dependency, exhausted resources) remains listed as available and continues receiving traffic it can't actually serve successfully.
- A well-designed health check exercises the specific dependencies and internal conditions that genuinely determine whether the instance can serve requests, not just whether the process responds to any request at all.
- Recovery is automatic: once a health check starts passing again, the instance becomes routable again on the registry's next evaluation, with no manual re-registration or restart required.
- A shallow health check that doesn't actually exercise real dependencies provides false confidence and undermines the entire mechanism — the specific checks performed matter as much as the fact that a health check exists at all.
