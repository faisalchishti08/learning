---
card: microservices
gi: 223
slug: dynamic-runtime-configuration-refresh
title: "Dynamic / runtime configuration refresh"
---

## 1. What it is

Dynamic configuration refresh is the ability for a running application to pick up a changed configuration value without being restarted — the new value takes effect in the live process, as opposed to static configuration that's read once at startup and stays fixed for the process's entire lifetime.

## 2. Why & when

Configuration read once at startup means any change to it requires restarting every instance of the affected service to take effect — acceptable for values that rarely change, but a real operational cost for values that need to change often or urgently (a timeout that needs tuning under live load, an emergency [feature flag](0225-feature-flags-feature-toggles.md) that needs flipping off *right now*, without waiting for a full redeploy cycle across every instance). Dynamic refresh closes this gap by having the application re-read (or be pushed) an updated value while it continues running, applying the new value to subsequent operations without a restart.

Use dynamic refresh for values that genuinely benefit from being changed without a restart — tunable thresholds, feature flags, log levels during an incident. Values that are safe to change only alongside a full redeploy (a database schema-affecting setting, for instance) should stay static and not be made dynamically refreshable, since applying them mid-flight could leave the running process in an inconsistent state.

## 3. Core concept

Dynamic refresh works by having configuration live behind an indirection — a holder object, a supplier, a scoped bean — that application code reads from on each use, rather than capturing the value once into a plain field at startup; updating the holder's contents is then immediately visible to every subsequent read, with no restart needed.

```java
// STATIC -- value captured ONCE at startup; changing it later has NO effect on the running process
int timeoutMs = loadConfig().get("timeout.ms"); // frozen at startup

// DYNAMIC -- reads happen THROUGH a holder, on every use; updating the holder takes effect IMMEDIATELY
class ConfigHolder { volatile int timeoutMs = 3000; }
ConfigHolder config = new ConfigHolder();
// ... elsewhere, at any later point, WITHOUT a restart:
config.timeoutMs = 5000; // the NEXT read anywhere in the running process sees this new value
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A static configuration read captures a value once at startup and never changes; a dynamic configuration read goes through a live holder, so an external update to that holder is reflected on the very next read, without restarting the process" >
  <rect x="20" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Static: read ONCE at startup</text>
  <text x="155" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">later changes have NO effect</text>

  <rect x="20" y="100" width="270" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="122" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Dynamic: read through a live holder</text>
  <text x="155" y="138" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">update reflected on NEXT read</text>
  <text x="155" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no restart needed</text>

  <rect x="380" y="100" width="230" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="495" y="125" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">External update event</text>
  <text x="495" y="142" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">config server push / poll</text>

  <line x1="378" y1="130" x2="292" y2="130" stroke="#8b949e" marker-end="url(#arr223)"/>

  <defs>
    <marker id="arr223" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

An external update reaches a live holder that every subsequent read consults, bypassing the need for a restart.

## 5. Runnable example

Scenario: a request-handling loop that starts reading a static, startup-frozen timeout value (immune to any later change), refactors to read from a live, updatable holder (an external update takes effect on the next request), and finally adds a background poller that periodically checks a simulated config source and applies changes automatically, mirroring how real dynamic-refresh mechanisms detect and apply updates without any manual trigger.

### Level 1 — Basic

```java
// File: StaticFrozenConfig.java -- the timeout is captured ONCE, at
// startup; changing the "source" afterward has NO effect on requests
// already using the frozen local value.
public class StaticFrozenConfig {
    static int loadTimeoutFromSource() { return 3000; } // simulates reading config ONCE

    public static void main(String[] args) {
        int timeoutMs = loadTimeoutFromSource(); // FROZEN at this point, forever, for this process
        System.out.println("Request 1 uses timeout: " + timeoutMs);

        // imagine the "source" changes here (e.g. an ops engineer updates a config file) --
        // but `timeoutMs` was already captured, so it CANNOT see that change
        System.out.println("Request 2 uses timeout: " + timeoutMs); // STILL 3000, even if the source changed
        System.out.println("A restart would be required to pick up any change to the source.");
    }
}
```

**How to run:** `javac StaticFrozenConfig.java && java StaticFrozenConfig` (JDK 17+).

### Level 2 — Intermediate

```java
// File: LiveHolderConfig.java -- requests now read THROUGH a live holder;
// an external update to the holder is visible on the VERY NEXT read,
// with NO restart involved.
public class LiveHolderConfig {
    static class ConfigHolder { volatile int timeoutMs = 3000; } // "volatile" so updates are visible across reads

    static ConfigHolder config = new ConfigHolder();

    static void handleRequest(int requestNumber) {
        System.out.println("Request " + requestNumber + " uses timeout: " + config.timeoutMs); // reads LIVE, every time
    }

    public static void main(String[] args) {
        handleRequest(1);
        config.timeoutMs = 5000; // an EXTERNAL update -- e.g. triggered by a config server push -- NO restart
        handleRequest(2); // sees the NEW value immediately
    }
}
```

**How to run:** `javac LiveHolderConfig.java && java LiveHolderConfig` (JDK 17+).

Expected output:
```
Request 1 uses timeout: 3000
Request 2 uses timeout: 5000
```

### Level 3 — Advanced

```java
// File: BackgroundPollingRefresh.java -- a background poller periodically
// checks a simulated external config source and applies changes to the
// live holder AUTOMATICALLY, mirroring a real dynamic-refresh mechanism.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class BackgroundPollingRefresh {
    static class ConfigHolder { volatile int timeoutMs = 3000; }
    static ConfigHolder config = new ConfigHolder();
    static AtomicInteger simulatedExternalSource = new AtomicInteger(3000); // the "config server's" current value

    static void handleRequest(String label) {
        System.out.println(label + " uses timeout: " + config.timeoutMs);
    }

    public static void main(String[] args) throws InterruptedException {
        ScheduledExecutorService poller = Executors.newSingleThreadScheduledExecutor();
        // POLL the external source every 50ms and apply any change to the live holder -- fully automatic
        poller.scheduleAtFixedRate(() -> {
            int latest = simulatedExternalSource.get();
            if (config.timeoutMs != latest) {
                System.out.println("  [poller] detected change: " + config.timeoutMs + " -> " + latest + " -- applying");
                config.timeoutMs = latest;
            }
        }, 0, 50, TimeUnit.MILLISECONDS);

        handleRequest("Request A");
        Thread.sleep(20);

        simulatedExternalSource.set(5000); // an OPS ENGINEER updates the external config source
        Thread.sleep(80); // give the poller time to detect and apply it

        handleRequest("Request B"); // picks up the change AUTOMATICALLY, with no manual trigger
        poller.shutdown();
    }
}
```

**How to run:** `javac BackgroundPollingRefresh.java && java BackgroundPollingRefresh` (JDK 17+).

Expected output (timing-dependent, but the sequence is deterministic):
```
Request A uses timeout: 3000
  [poller] detected change: 3000 -> 5000 -- applying
Request B uses timeout: 5000
```

## 6. Walkthrough

1. **Level 1, capturing once** — `loadTimeoutFromSource()` is called exactly once, and its return value is stored in a plain local variable `timeoutMs`; nothing in this program re-reads the source afterward, so a hypothetical later change to that source is completely invisible to this running process — the comment marks precisely where a real change would occur and be missed.
2. **Level 2, reading through a holder** — `ConfigHolder.timeoutMs` is a field on a shared, mutable object, and `handleRequest` reads `config.timeoutMs` fresh on every call rather than from a locally captured copy; the `volatile` modifier ensures a write from one thread (like an update triggered externally) is visible to reads happening on other threads.
3. **Level 2, the update taking effect** — `config.timeoutMs = 5000` is a direct mutation of the shared holder, standing in for what a real dynamic-refresh mechanism (a config server push, a `@RefreshScope` bean refresh) would trigger; the second `handleRequest` call immediately reflects this new value, with no restart of `main` or any part of the program.
4. **Level 3, the automated detection loop** — `poller`, a `ScheduledExecutorService`, runs a check every 50 milliseconds comparing `config.timeoutMs` against `simulatedExternalSource.get()`; when they differ, it logs the detected change and applies it to `config.timeoutMs` — this loop runs entirely independently of and concurrently with the request-handling code.
5. **Level 3, the external change and its automatic propagation** — `simulatedExternalSource.set(5000)` stands in for an operator changing a value at its source (a config server, a config file); no code anywhere calls `config.timeoutMs = 5000` directly this time — the poller running in the background is solely responsible for detecting the discrepancy and applying it.
6. **Level 3, request B sees the change with no manual intervention** — by the time `handleRequest("Request B")` runs (after a `Thread.sleep(80)` giving the poller at least one full 50ms cycle to run), the poller has already detected and applied the external change, so `config.timeoutMs` reads `5000` without `main` ever explicitly updating it — this mirrors how a real dynamic-refresh setup (like [`@RefreshScope`](0234-refreshscope-for-runtime-refresh.md), covered later in this section) detects and applies configuration server changes automatically, in the background, without requiring the application's business logic to poll for updates itself.

## 7. Gotchas & takeaways

> **Gotcha:** not every value is safe to change dynamically — a setting that other in-flight logic assumes is stable for the duration of an operation (for example, a value baked into a connection pool's initial sizing) can cause subtle bugs if changed mid-flight; reserve dynamic refresh for values that are genuinely safe to change at any moment, and leave structurally significant settings static, requiring a deliberate restart to change.

- Dynamic configuration refresh lets a running process pick up changed values without a restart, by reading configuration through a live, updatable holder rather than a value captured once at startup.
- It matters most for values needing frequent or urgent changes — tunable thresholds, feature flags, incident-response settings — where waiting for a full redeploy cycle is a real operational cost.
- The mechanism requires application code to read configuration on each use (or through a mechanism that re-injects updated values), not to capture it once into a plain field.
- A background poller (or a push-based notification) is what typically drives the detection of external changes and their application to the live holder, entirely independent of the application's normal request-handling logic.
- Not every setting is safe to make dynamically refreshable — values that other logic assumes are stable for an operation's duration should stay static, requiring an explicit restart to change.
