---
card: spring-cloud
gi: 8
slug: endpoints-refresh-restart-pause-resume
title: "Endpoints (/refresh, /restart, /pause, /resume)"
---

## 1. What it is

Spring Cloud Context exposes its lifecycle operations as Spring Boot Actuator endpoints: `POST /actuator/refresh` triggers the refresh covered in the previous two cards, while `/actuator/restart`, `/actuator/pause`, and `/actuator/resume` (from the `spring-cloud-context` restart-context feature) control a coarser application-lifecycle state — restarting the whole `ApplicationContext`, or pausing/resuming a `Lifecycle` bean's activity, without a process restart.

```
POST /actuator/refresh   -> { "rate.limit.perMinute" }         (returns changed property keys)
POST /actuator/restart   -> restarts the ApplicationContext in-process
POST /actuator/pause     -> calls Lifecycle.stop() on lifecycle-aware beans
POST /actuator/resume    -> calls Lifecycle.start() on lifecycle-aware beans
```

## 2. Why & when

The previous two cards explained *what* refresh does and *which* beans respond to it. This card is about the operational surface: how a running application is actually told to refresh, restart, pause, or resume — typically triggered by an operator, a CI/CD pipeline step, or a Config Server webhook, rather than from inside the application's own code.

Reach for these endpoints when:

- Config changes at the source (a Config Server's Git repo, say) need to be pushed to running instances — a webhook or pipeline step calling `/actuator/refresh` on each instance is the standard integration point.
- An application-level (not process-level) restart is useful — re-running the full startup sequence, re-establishing connections, without the cost of a full process/container restart.
- A specific `Lifecycle`-implementing component (a message listener, a scheduled poller) needs to be temporarily halted and later resumed without touching anything else in the running application.

## 3. Core concept

```
 /actuator/refresh   -- SELECTIVE: only @RefreshScope beans + property sources affected
                          fast, cheap, safe to call frequently

 /actuator/restart    -- BROAD: closes and re-creates the entire ApplicationContext
                          slower, heavier, resets EVERYTHING including non-refresh-scoped state

 /actuator/pause      -- targets Lifecycle beans specifically, calling .stop()
 /actuator/resume     -- targets the SAME Lifecycle beans, calling .start()
                          useful for temporarily halting a specific subsystem (a consumer, a poller)
                          without touching the rest of the running application
```

Each endpoint operates at a different granularity — refresh is the lightest touch, restart the heaviest, pause/resume the most targeted.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three endpoints act at different scopes: refresh scoped beans only, restart the whole context, pause and resume specific lifecycle beans">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">/refresh -- narrowest</text>

  <rect x="230" y="20" width="180" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">/pause + /resume -- targeted</text>

  <rect x="440" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="530" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">/restart -- broadest</text>

  <rect x="20" y="90" width="600" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">increasing scope of what gets affected, left to right</text>
</svg>

Refresh, pause/resume, and restart each touch a progressively wider slice of the running application.

## 5. Runnable example

The scenario: an operations team managing a running service, evolving from a naive "just restart the whole process" approach to every configuration or subsystem change, to using refresh for lightweight config updates, to a full simulation distinguishing all three lifecycle operations and which parts of the application each one actually affects.

### Level 1 — Basic

Show the naive baseline: full process restart for every kind of change, even a small config tweak.

```java
public class LifecycleEndpointsLevel1 {
    public static void main(String[] args) {
        Application app = new Application();
        app.start();
        System.out.println("Rate limit: " + app.rateLimiter.limit);

        // Only ONE property changed, but the ENTIRE process has to restart to pick it up.
        System.out.println("Restarting entire process just to change one rate limit...");
        app = new Application(); // simulates killing and restarting the whole JVM
        app.start();
        System.out.println("New rate limit after full restart: " + app.rateLimiter.limit);
    }
}

class Application {
    RateLimiter rateLimiter = new RateLimiter(250); // pretend this changed in config between "restarts"
    void start() { System.out.println("Full application startup..."); }
}
class RateLimiter { int limit; RateLimiter(int limit) { this.limit = limit; } }
```

How to run: `java LifecycleEndpointsLevel1.java`

Every change, however small, pays the cost of a complete restart — connections re-established, caches rebuilt, every bean recreated — for what might be a single tunable number.

### Level 2 — Intermediate

Add a `/refresh`-style operation targeting only the affected refresh-scoped bean, contrasted with a `/restart`-style operation affecting everything.

```java
import java.util.*;

public class LifecycleEndpointsLevel2 {
    public static void main(String[] args) {
        Application app = new Application();
        app.start();

        System.out.println("--- Simulating POST /actuator/refresh ---");
        app.config.discountPercent = 25; // config source changes
        app.refresh(); // only refresh-scoped state is affected
        System.out.println("Discount after refresh: " + app.config.discountPercent + "% -- rest of app untouched");
        System.out.println("Database connection still open: " + app.databaseConnectionOpen);

        System.out.println("--- Simulating POST /actuator/restart ---");
        app.restart(); // EVERYTHING resets, including things refresh wouldn't touch
        System.out.println("Database connection after restart: " + app.databaseConnectionOpen); // re-established
    }
}

class Config { int discountPercent = 10; }

class Application {
    Config config = new Config();
    boolean databaseConnectionOpen = false;

    void start() {
        System.out.println("Full startup: opening database connection...");
        databaseConnectionOpen = true;
    }
    void refresh() {
        System.out.println("Refresh: only re-reading configuration, connections untouched.");
        // In a real app: re-read property sources, recreate ONLY @RefreshScope beans.
    }
    void restart() {
        System.out.println("Restart: closing everything, running full startup again.");
        databaseConnectionOpen = false; // closed as part of context shutdown
        start(); // full startup sequence runs again
    }
}
```

How to run: `java LifecycleEndpointsLevel2.java`

`refresh()` leaves `databaseConnectionOpen` untouched — it only concerns itself with configuration-driven state — while `restart()` closes and reopens the connection as part of tearing down and rebuilding the entire application context, exactly matching the difference between calling `/actuator/refresh` and `/actuator/restart` on a real Spring Cloud application.

### Level 3 — Advanced

Add `/pause` and `/resume`, targeting a specific `Lifecycle`-style component (a message listener) independently of both refresh and restart — the third, most targeted lifecycle operation.

```java
public class LifecycleEndpointsLevel3 {
    public static void main(String[] args) {
        Application app = new Application();
        app.start();

        System.out.println("--- Normal operation ---");
        app.messageListener.processIfActive();

        System.out.println("--- Simulating POST /actuator/pause ---");
        app.pause(); // stops JUST the message listener -- everything else keeps running
        app.messageListener.processIfActive(); // no-op now
        System.out.println("Database connection still open during pause: " + app.databaseConnectionOpen);

        System.out.println("--- Simulating POST /actuator/resume ---");
        app.resume(); // restarts JUST the message listener
        app.messageListener.processIfActive();
    }
}

class MessageListener {
    private boolean active = true;
    void stop() { active = false; System.out.println("Message listener stopped."); }
    void start() { active = true; System.out.println("Message listener started."); }
    void processIfActive() {
        if (active) System.out.println("Processing incoming messages...");
        else System.out.println("(message listener paused -- nothing processed)");
    }
}

class Application {
    MessageListener messageListener = new MessageListener();
    boolean databaseConnectionOpen = false;

    void start() {
        System.out.println("Full startup: opening database connection, starting listener...");
        databaseConnectionOpen = true;
    }
    // Pause/resume target Lifecycle beans specifically -- NOT the database connection, NOT configuration.
    void pause() { messageListener.stop(); }
    void resume() { messageListener.start(); }
}
```

How to run: `java LifecycleEndpointsLevel3.java`

`pause()` calls `messageListener.stop()` and nothing else — `databaseConnectionOpen` remains `true` throughout, demonstrating that pause/resume targets specifically `Lifecycle`-implementing beans, leaving the rest of the running application (including config values and other connections) completely untouched, unlike either `refresh()` or `restart()`.

## 6. Walkthrough

Execution starts in `main` for Level 3. `app.start()` opens the database connection and starts the message listener. The first `processIfActive()` call finds `active = true` and processes normally:

```
--- Normal operation ---
Processing incoming messages...
```

`app.pause()` calls `messageListener.stop()`, setting `active = false`. The next `processIfActive()` call now takes the "paused" branch, printing a no-op message instead — and the check right after confirms `databaseConnectionOpen` is still `true`, since `pause()` never touched it:

```
--- Simulating POST /actuator/pause ---
Message listener stopped.
(message listener paused -- nothing processed)
Database connection still open during pause: true
```

`app.resume()` calls `messageListener.start()`, flipping `active` back to `true`, and the final `processIfActive()` call processes normally again:

```
--- Simulating POST /actuator/resume ---
Message listener started.
Processing incoming messages...
```

In a real Spring Cloud application, `/actuator/pause` and `/actuator/resume` call `stop()`/`start()` on every Spring-managed bean implementing the `Lifecycle` interface (or `SmartLifecycle`) — commonly used for message listener containers (Kafka, RabbitMQ consumers) that an operator wants to temporarily halt (during a maintenance window, say) without restarting the entire application or losing its established database connections and other state.

## 7. Gotchas & takeaways

> Gotcha: `/actuator/restart` is disabled by default in current Spring Cloud versions and requires explicit opt-in (adding the restart context configuration) — many teams intentionally leave it disabled, since an in-process context restart can behave subtly differently from a genuine process restart (some static state, thread-locals, or native resources may not be cleanly reset), making it a less predictable operation than it might seem.

> Gotcha: these actuator endpoints are, by default, sensitive operations — exposing `/actuator/refresh`, `/actuator/restart`, `/actuator/pause`, or `/actuator/resume` on a publicly reachable management port without authentication lets anyone trigger configuration reloads or application restarts; production deployments should secure or restrict access to Actuator's management endpoints.

- `/actuator/refresh` is the lightest-touch operation, affecting only refresh-scoped beans and property sources.
- `/actuator/restart` is the heaviest, tearing down and rebuilding the entire application context in-process — powerful, but disabled by default and worth using deliberately.
- `/actuator/pause`/`/actuator/resume` target `Lifecycle`-implementing beans specifically, useful for halting one subsystem (a message consumer) without affecting anything else running in the application.
- All of these are typically operator- or pipeline-triggered, and should be secured appropriately since they can materially change a running application's behavior.
