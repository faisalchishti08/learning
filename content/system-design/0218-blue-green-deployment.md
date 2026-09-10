---
card: system-design
gi: 218
slug: blue-green-deployment
title: Blue-green deployment
---

## 1. What it is

**Blue-green deployment** runs two identical, full-size production environments — "blue" (currently live) and "green" (the new version) — at the same time. Traffic is routed entirely to blue while green is deployed and tested; the cutover to the new version is a single switch of the router from blue to green, and rolling back is switching it right back.

## 2. Why & when

A deployment that upgrades a running environment in place (stopping the old version, starting the new one on the same machines) has an unavoidable window of downtime, and if the new version has a problem, rolling back means redeploying the old version — which takes time and itself risks failure. Blue-green removes both problems: the new version is fully deployed and can be tested against real production infrastructure *before* any real user traffic reaches it, and the cutover itself is just a routing change — effectively instant, and instantly reversible.

Use blue-green when you need the fastest possible rollback (a routing switch, not a redeploy) and can afford to run two full production-sized environments simultaneously, at least briefly. The doubled infrastructure cost during the switch is the real tradeoff — for cost-sensitive systems, or for changes you want to expose gradually rather than all-at-once, [canary release](0219-canary-release-feature-flags.md) is often a better fit.

## 3. Core concept

- **Two full environments, one live.** "Blue" and "green" are both complete, independently running copies of the whole production environment — not a partial deployment. Only one of them receives real traffic at any given time.
- **The router (or load balancer) is the single switch point.** Cutting over is changing where the router sends traffic — from all-blue to all-green — with no changes needed to either environment itself.
- **Pre-cutover validation on the idle environment.** Before switching, you can run smoke tests, synthetic traffic, and manual checks against the green environment directly (using its own internal address, bypassing the router) — real production infrastructure, zero real user exposure.
- **Instant rollback.** If a problem appears after cutover, switching the router back to blue is the rollback — no redeploy, no rebuild, just the same routing change in reverse. This is the core risk-reduction benefit over an in-place update.
- **Database and shared-state compatibility.** Both blue and green typically point at the same database. Any schema change deployed with the new version must remain compatible with the old version's code too, for as long as blue could still be switched back to — this is the hardest part of blue-green in practice.

## 4. Diagram

```
  BEFORE CUTOVER                              AFTER CUTOVER

   Users                                       Users
     |                                           |
     v                                           v
  +--------+                                  +--------+
  | Router |                                   | Router |
  +---+----+                                   +---+----+
      | all traffic                                 | all traffic
      v                                              v
  +---------+        +---------+              +---------+        +---------+
  |  BLUE    |        |  GREEN   |             |  BLUE    |        |  GREEN   |
  |  v1.0    |        |  v1.1     |             |  v1.0    |        |  v1.1     |
  |  (LIVE)  |        |  (idle,   |             | (idle,   |        |  (LIVE)   |
  |          |        |  smoke-   |             |  kept as |        |           |
  |          |        |  tested   |             |  instant |        |           |
  |          |        |  directly)|             |  rollback)|       |           |
  +---------+        +---------+              +---------+        +---------+
        \                  /                          \                  /
         \________________/                            \________________/
              same database                                  same database
```
*Caption: cutover is purely a router change. Blue stays fully deployed and ready as an instant rollback target until you are confident enough to decommission it.*

## 5. Runnable example

**Level 1 — Basic.** A router pointing entirely at blue or entirely at green, with a cutover switch.

**Level 2 — Intermediate.** Smoke-test the idle (green) environment directly, bypassing the router, before cutting over.

**Level 3 — Advanced.** Cut over, detect a problem in green, and roll back instantly by switching the router back — no redeploy involved.

```java
// BlueGreenDemo.java
import java.util.*;
import java.util.function.*;

public class BlueGreenDemo {

    static class Environment {
        String name, version;
        boolean healthy;
        Environment(String name, String version, boolean healthy) {
            this.name = name; this.version = version; this.healthy = healthy;
        }
        String handleRequest(String request) {
            if (!healthy) throw new RuntimeException(name + " (" + version + ") failed to handle: " + request);
            return name + " (" + version + ") handled: " + request;
        }
    }

    // ---------- Level 1: router with a single cutover switch ----------
    static class Router {
        Environment blue, green;
        Environment live; // whichever one currently receives real traffic

        Router(Environment blue, Environment green) {
            this.blue = blue; this.green = green; this.live = blue; // blue starts live
        }

        String route(String request) { return live.handleRequest(request); }

        void cutover(Environment target) {
            live = target;
            System.out.println("  [router] cutover complete - now routing to " + target.name + " (" + target.version + ")");
        }
    }

    public static void main(String[] args) {
        Environment blue = new Environment("blue", "v1.0", true);
        Environment green = new Environment("green", "v1.1", true);
        Router router = new Router(blue, green);

        System.out.println("Level 1 - blue is live, green is deployed but idle:");
        System.out.println("  " + router.route("GET /orders"));

        System.out.println("\nLevel 2 - smoke-test green directly, bypassing the router entirely:");
        System.out.println("  " + green.handleRequest("smoke-test: GET /health"));
        System.out.println("  " + green.handleRequest("smoke-test: GET /orders/1"));
        System.out.println("  smoke tests passed - blue still serves all real user traffic during this check:");
        System.out.println("  " + router.route("GET /orders (real user traffic)"));

        System.out.println("\nLevel 3 - cutover to green, detect a problem, roll back instantly:");
        router.cutover(green);
        System.out.println("  " + router.route("GET /orders (real user traffic, now on green)"));

        // Simulate green developing a real problem shortly after cutover.
        green.healthy = false;
        System.out.println("  green is now failing under real traffic...");
        try {
            router.route("GET /orders (real user traffic)");
        } catch (RuntimeException e) {
            System.out.println("  request failed: " + e.getMessage());
            System.out.println("  rolling back - blue was never touched, so this is instant:");
            router.cutover(blue);
            System.out.println("  " + router.route("GET /orders (real user traffic, back on blue)"));
        }
    }
}
```

**How to run:** `java BlueGreenDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `Router`'s constructor sets `live = blue`, so `router.route("GET /orders")` calls `blue.handleRequest(...)` and returns a response tagged `"blue (v1.0)"`. `green`, running `v1.1`, exists and is fully started but receives nothing from `router.route(...)` yet.
2. **Level 2:** `green.handleRequest(...)` is called directly, twice, bypassing `router` entirely — this models running smoke tests against green's own internal address. Both calls succeed because `green.healthy` is still `true` at this point. A call to `router.route(...)` right after still returns a `"blue"`-tagged response, proving these smoke tests against green had zero effect on real user traffic, which is the whole point of testing the idle environment before cutover.
3. **Level 3:** `router.cutover(green)` sets `live = green`. The very next `router.route(...)` call now returns a `"green (v1.1)"`-tagged response — the cutover is immediate and total, with no gradual transition (that gradual-transition behavior is what [canary release](0219-canary-release-feature-flags.md) provides instead).
4. `green.healthy` is then set to `false`, simulating a problem that only appears under real production traffic, after cutover — a common real-world scenario smoke tests do not always catch. The next `router.route(...)` call throws, since `green.handleRequest` checks `healthy` first.
5. The `catch` block runs `router.cutover(blue)` — because `blue` was never redeployed, stopped, or modified during any of this, switching back to it is immediate. The final `router.route(...)` call succeeds again, tagged `"blue (v1.0)"`, confirming the rollback restored exactly the environment that was serving traffic before any of this began.

## 7. Gotchas & takeaways

> **Gotcha:** if blue and green share a database and the green version's deployment includes a schema change that blue's code cannot handle, rolling back to blue after cutover can break blue immediately — the "instant rollback" promise only holds if every deployed change stays backward compatible with the environment you might roll back to.

- Keep blue fully intact and untouched during green's deployment and testing — its value as a rollback target depends entirely on it still being exactly what was running before.
- Test the idle environment directly, bypassing the router, before ever cutting real traffic over to it — Level 2 shows this is possible precisely because both environments exist simultaneously and independently.
- Plan for the doubled infrastructure cost, even if only for the (typically short) window between cutover and decommissioning the old environment.
- Any database or shared-state change deployed with the new version must remain compatible with the old version's code, for as long as you want rollback to remain genuinely instant.
