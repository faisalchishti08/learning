---
card: microservices
gi: 6
slug: products-not-projects-you-build-it-you-run-it
title: "Products not projects (you build it, you run it)"
---

## 1. What it is

**Products not projects** is the Lewis & Fowler characteristic that says a team should own a service for its whole lifetime, not hand it off to a separate operations team once it's "done." A **project** mindset treats software as a task with an end date: a team builds it, ships it over the wall, and moves on. A **product** mindset treats software as something with an ongoing relationship to its users: the same team that wrote it keeps improving it, and — crucially — keeps *operating* it, watching how it behaves in production and fixing it when it breaks. This is the origin of Amazon's well-known phrase "you build it, you run it": the people who write the code also carry the pager for it.

## 2. Why & when

When a separate operations team runs software they didn't write, a structural gap opens up: the people best equipped to understand *why* something broke (the authors) aren't the ones woken up at 3 a.m. to fix it, and the people who get paged have limited ability to actually change the code. That gap tends to produce defensive, overly cautious operations processes and code that's easier to write than to run, because the people writing it never feel the operational pain of their own decisions.

Adopt "you build it, you run it" once a service has a real, ongoing production life — accept the tradeoff that developers now need at least basic operational skills (reading logs, understanding alerts, responding to incidents), and that on-call responsibility becomes part of the job. This is less about a specific tool and more about where the accountability boundary sits: does the team that changes the code also see the consequences of that change in production, directly and quickly?

## 3. Core concept

Ownership shows up concretely in what a service exposes about itself and how it responds to its own trouble:

- **Project mindset:** the service just does its job; if it starts failing, some other team's dashboard, some other team's runbook, some other team's judgment call decides what happens next.
- **Product mindset:** the service exposes its own health, and the same code (owned by the same team) that implements the feature also implements watching over that feature — detecting trouble and reacting to it.

The concrete artifact this produces is usually a health/status endpoint plus some self-monitoring logic living right next to the business logic, not bolted on externally by a different team.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Project mindset hands a finished service to a separate ops team; product mindset keeps the same team owning build and run together via a self-monitoring loop">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Project</text>
  <rect x="30" y="35" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Dev team builds</text>
  <rect x="220" y="35" width="150" height="50" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="295" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Ops team runs</text>
  <line x1="180" y1="60" x2="220" y2="60" stroke="#8b949e" marker-end="url(#a6)"/>
  <text x="200" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">hand-off, one time</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Product</text>
  <rect x="430" y="35" width="180" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Same team</text>
  <text x="520" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">builds AND runs</text>
  <text x="520" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">owns health checks</text>
  <text x="520" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">carries the pager</text>
  <defs><marker id="a6" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Ownership either stops at hand-off, or continues into production as one continuous responsibility.

## 5. Runnable example

Scenario: a service that starts as a bare feature with no self-awareness, then gains a health endpoint its own team maintains, then gains self-monitoring that detects and reacts to its own failure — all owned by the same code.

### Level 1 — Basic

```java
// File: ServiceNoOwnership.java -- does its job, exposes nothing about its own health
public class ServiceNoOwnership {
    static int failureCount = 0;

    static String processOrder(String item) {
        if (item.equals("bad-item")) { failureCount++; throw new RuntimeException("cannot process " + item); }
        return "processed: " + item;
    }

    public static void main(String[] args) {
        System.out.println(processOrder("widget"));
        try {
            processOrder("bad-item");
        } catch (RuntimeException e) {
            System.out.println("failed silently -- no one but this process even knows: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac ServiceNoOwnership.java && java ServiceNoOwnership` (JDK 17+).

Expected output:
```
processed: widget
failed silently -- no one but this process even knows: cannot process bad-item
```

The failure is caught locally and printed, but nothing about the service's health is exposed anywhere — a separate operations team watching this service from outside would have no way to know it just failed.

### Level 2 — Intermediate

```java
// File: ServiceWithHealth.java -- the SAME team that wrote the feature
// also exposes its health, over an endpoint they own end to end.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class ServiceWithHealth {
    static int failureCount = 0;
    static int successCount = 0;

    static String processOrder(String item) {
        if (item.equals("bad-item")) { failureCount++; throw new RuntimeException("cannot process " + item); }
        successCount++;
        return "processed: " + item;
    }

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8094), 0);
        server.createContext("/health", ex -> {
            String status = failureCount == 0 ? "UP" : "DEGRADED";
            String body = status + " (success=" + successCount + ", failures=" + failureCount + ")";
            ex.sendResponseHeaders(200, body.length());
            ex.getResponseBody().write(body.getBytes());
            ex.close();
        });
        server.start();

        processOrder("widget");
        try { processOrder("bad-item"); } catch (RuntimeException ignored) {}

        var client = java.net.http.HttpClient.newHttpClient();
        var request = java.net.http.HttpRequest.newBuilder(java.net.URI.create("http://localhost:8094/health")).build();
        var response = client.send(request, java.net.http.HttpResponse.BodyHandlers.ofString());
        System.out.println("health check: " + response.body());
        server.stop(0);
    }
}
```

**How to run:** `javac ServiceWithHealth.java && java ServiceWithHealth` (JDK 17+).

Expected output:
```
health check: DEGRADED (success=1, failures=1)
```

The feature code (`processOrder`) and the health-exposing code (`/health`) live in the same class, written and owned by the same team — this is what "you build it" and "you expose its status" both meeting in one place looks like, rather than a separate monitoring team bolting metrics onto a service they don't understand.

### Level 3 — Advanced

```java
// File: ServiceSelfHealing.java -- the owning team's code doesn't just
// report trouble, it REACTS to it, since they carry the pager for it.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class ServiceSelfHealing {
    static int consecutiveFailures = 0;
    static boolean circuitOpen = false;

    static String processOrder(String item) {
        if (circuitOpen) return "REJECTED (self-protection mode): " + item;
        if (item.equals("bad-item")) {
            consecutiveFailures++;
            if (consecutiveFailures >= 3) {
                circuitOpen = true; // the SAME team's code decides to protect itself
                System.out.println("  [self-healing] 3 consecutive failures -- entering self-protection mode");
            }
            throw new RuntimeException("cannot process " + item);
        }
        consecutiveFailures = 0;
        return "processed: " + item;
    }

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8094), 0);
        server.createContext("/health", ex -> {
            String status = circuitOpen ? "SELF-PROTECTING" : (consecutiveFailures == 0 ? "UP" : "DEGRADED");
            ex.sendResponseHeaders(200, status.length());
            ex.getResponseBody().write(status.getBytes());
            ex.close();
        });
        server.start();

        for (String item : new String[]{"bad-item", "bad-item", "bad-item", "widget"}) {
            try {
                System.out.println(processOrder(item));
            } catch (RuntimeException e) {
                System.out.println("failed: " + e.getMessage());
            }
        }
        server.stop(0);
    }
}
```

**How to run:** `javac ServiceSelfHealing.java && java ServiceSelfHealing` (JDK 17+).

Expected output:
```
failed: cannot process bad-item
failed: cannot process bad-item
  [self-healing] 3 consecutive failures -- entering self-protection mode
failed: cannot process bad-item
REJECTED (self-protection mode): widget
```

The production-flavored case: the code that owns the feature also owns the *reaction* to that feature repeatedly failing — after three consecutive failures, it flips into a self-protection mode and starts rejecting further work immediately, rather than continuing to fail slowly and quietly. This is the "run it" half of "build it, run it" expressed directly in code owned by the same team that wrote `processOrder` in the first place.

## 6. Walkthrough

1. The loop calls `processOrder("bad-item")` three times in a row. Each call increments `consecutiveFailures` and throws, and the `catch` block in `main` prints `"failed: cannot process bad-item"` each time.
2. On the third failure, inside `processOrder`, the check `consecutiveFailures >= 3` becomes true. The method sets `circuitOpen = true` and prints the `[self-healing]` line — this is the owning team's own logic deciding, without any external operator, that this service needs to protect itself.
3. The fourth loop iteration calls `processOrder("widget")` — normally a perfectly valid item. But because `circuitOpen` is now `true`, the very first line of `processOrder` short-circuits and returns `"REJECTED (self-protection mode): widget"` without even looking at the item.
4. If an external health check hit `/health` at this point, it would read `circuitOpen` and report `"SELF-PROTECTING"` — a status a genuinely separate ops team could see from outside, but that the *code itself* already reacted to internally, before any human needed to intervene.

```
bad-item -> fail (1)
bad-item -> fail (2)
bad-item -> fail (3) -> circuitOpen = true, self-healing triggered
widget   -> REJECTED (self-protection engaged, even for valid input)
```

## 7. Gotchas & takeaways

> **Gotcha:** "you build it, you run it" without matching authority is worse than a clean project hand-off — if a team carries the pager for a service but doesn't have the ability to change its deployment, scale it, or roll it back, they're accountable for outcomes they can't actually control. Ownership only works when it comes paired with the operational authority to act on what you observe.

- A "product" service is owned by one team for its whole lifecycle — build, deploy, monitor, and fix — rather than handed off to a separate operations team after launch.
- The concrete signal in code: does the same class or module that implements the feature also expose and react to that feature's health, or is monitoring bolted on externally by people who didn't write it?
- Self-healing logic (like the circuit above) is a natural extension of ownership: the team that understands the failure mode best is best placed to encode the right automatic reaction to it.
- This characteristic has a real cost: developers on a "you build it, you run it" team need genuine operational skills, and on-call responsibility becomes part of the job, not someone else's.
