---
card: microservices
gi: 372
slug: actuator-loggers-for-runtime-log-level-changes
title: "Actuator /loggers for runtime log-level changes"
---

## 1. What it is

Spring Boot Actuator's **`/actuator/loggers`** endpoint is the concrete mechanism for [dynamic log level changes](0362-log-levels-dynamic-log-level-changes.md) in a Spring Boot application: a `GET /actuator/loggers` request lists every logger and its currently configured level; a `POST /actuator/loggers/{logger-name}` request with a body like `{"configuredLevel": "DEBUG"}` changes that specific logger's level immediately, on a live, already-running instance, with no restart.

## 2. Why & when

Earlier, [dynamic log level changes](0362-log-levels-dynamic-log-level-changes.md) explained the general need: temporarily raising verbosity on a specific, live service instance while investigating an active issue, without a redeploy. `/actuator/loggers` is exactly the built-in Spring Boot feature that provides this, requiring no custom code — just enabling the Actuator endpoint (and, in production, restricting who can call it, since it's a mutating operation).

Use `/actuator/loggers` during an active incident to bump a specific package or class's logger to `DEBUG` on the specific instance(s) that need investigating, gather the detailed output you need, and then set it back to its normal level afterward via the same endpoint — this whole cycle takes seconds and requires no deployment pipeline at all. Restrict write access to this endpoint (it's a mutating operation, unlike read-only endpoints like `/health`) to authorized operators, since letting anyone freely change any service's log verbosity is both a security concern (potentially leaking sensitive debug output) and an operational one (accidentally flooding logs).

## 3. Core concept

Spring's `LoggingSystem` abstraction maintains the effective level for every logger; `/actuator/loggers`'s `GET` handler reads and reports that state, while its `POST` handler for a specific logger name calls `LoggingSystem.setLogLevel(loggerName, newLevel)` directly, which takes effect immediately for any subsequent log statement in that logger — no restart, no redeploy, because the change is applied directly to the live logging framework's runtime configuration.

```java
// GET /actuator/loggers/com.example.payment
// -> {"configuredLevel": "INFO", "effectiveLevel": "INFO"}

// POST /actuator/loggers/com.example.payment
// body: {"configuredLevel": "DEBUG"}
// -> subsequent log.debug(...) calls in that package are now emitted, IMMEDIATELY, no restart
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An operator sends a POST to /actuator/loggers/com.example.payment with configuredLevel DEBUG; the running application's LoggingSystem updates immediately; subsequent debug log statements in that package are now emitted, with no restart">
  <rect x="20" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Operator POSTs new level</text>

  <line x1="200" y1="80" x2="270" y2="80" stroke="#8b949e" marker-end="url(#a372)"/>
  <rect x="280" y="60" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Live app's LoggingSystem</text>

  <line x1="460" y1="80" x2="530" y2="80" stroke="#8b949e" marker-end="url(#a372)"/>
  <rect x="540" y="60" width="90" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="585" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DEBUG now on</text>

  <text x="320" y="140" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Applied immediately to the running instance -- no restart, no redeploy.</text>

  <defs><marker id="a372" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A POST to /actuator/loggers changes a logger's level on the live, running instance immediately, with no restart.

## 5. Runnable example

Scenario: investigating a payment issue, first shown requiring a redeploy just to see debug output (slow, risky during an incident), then fixed with a simulated `/actuator/loggers` endpoint changing the level live, and finally extended to restrict this mutating endpoint to authorized operators only.

### Level 1 — Basic

```java
// File: RedeployRequiredForDebug.java -- the log level is baked into
// deployed configuration; seeing DEBUG output means editing config,
// REBUILDING, and REDEPLOYING -- slow and risky mid-incident.
import java.util.*;

public class RedeployRequiredForDebug {
    static String deployedConfigLogLevel = "INFO"; // baked into the deployed artifact/config

    static void logDebug(String message) {
        if (deployedConfigLogLevel.equals("DEBUG")) System.out.println("[DEBUG] " + message);
    }

    public static void main(String[] args) {
        logDebug("attempting payment charge, retry 1 of 3");
        System.out.println("Nothing printed -- to see this, we'd need to edit config to DEBUG, rebuild, and REDEPLOY the whole service.");
        System.out.println("During an ACTIVE incident, that redeploy cycle could take many minutes -- far too slow.");
    }
}
```

How to run: `java RedeployRequiredForDebug.java`

`deployedConfigLogLevel` is fixed at deploy time; seeing the `DEBUG` line requires editing configuration, rebuilding, and redeploying the entire service — a process that could take many minutes, during which the very issue being investigated might resolve itself or worsen, with the team unable to gather the detail they need in time.

### Level 2 — Intermediate

```java
// File: ActuatorLoggersLiveChange.java -- simulates the /actuator/loggers
// endpoint: a POST request changes the level on the LIVE, RUNNING
// instance immediately -- no restart involved.
import java.util.*;

public class ActuatorLoggersLiveChange {
    static Map<String, String> liveLoggerLevels = new HashMap<>(); // the running LoggingSystem's current state

    static void logDebug(String loggerName, String message) {
        if ("DEBUG".equals(liveLoggerLevels.getOrDefault(loggerName, "INFO"))) {
            System.out.println("[" + loggerName + "][DEBUG] " + message);
        }
    }

    // Simulates: POST /actuator/loggers/{loggerName} { "configuredLevel": "DEBUG" }
    static void postLoggerLevel(String loggerName, String newLevel) {
        liveLoggerLevels.put(loggerName, newLevel);
        System.out.println("POST /actuator/loggers/" + loggerName + " -> level set to " + newLevel + " (LIVE, no restart)");
    }

    public static void main(String[] args) {
        logDebug("com.example.payment", "attempting payment charge, retry 1 of 3"); // SKIPPED, still INFO

        postLoggerLevel("com.example.payment", "DEBUG"); // operator calls the endpoint DURING the incident

        logDebug("com.example.payment", "attempting payment charge, retry 2 of 3"); // NOW emitted -- SAME running process
        System.out.println("The level changed on the LIVE process -- no rebuild, no redeploy, took effect immediately.");
    }
}
```

How to run: `java ActuatorLoggersLiveChange.java`

`postLoggerLevel` simulates the `POST /actuator/loggers/{loggerName}` request, updating `liveLoggerLevels` on the already-running process. The first `logDebug` call is skipped (level still `INFO`), but after `postLoggerLevel` runs, the second identical-shaped call is emitted — all within the same running program, with no restart or rebuild anywhere in between, exactly demonstrating the real endpoint's live, immediate effect.

### Level 3 — Advanced

```java
// File: RestrictedLoggerEndpointAccess.java -- restricts WHO can call the
// mutating POST endpoint, mirroring production practice of NOT letting
// arbitrary callers change log verbosity (a security AND operational risk).
import java.util.*;

public class RestrictedLoggerEndpointAccess {
    static Map<String, String> liveLoggerLevels = new HashMap<>();
    static Set<String> authorizedOperators = Set.of("alice", "bob"); // only THESE users may mutate log levels

    static void logDebug(String loggerName, String message) {
        if ("DEBUG".equals(liveLoggerLevels.getOrDefault(loggerName, "INFO"))) {
            System.out.println("[" + loggerName + "][DEBUG] " + message);
        }
    }

    static String postLoggerLevel(String requestingUser, String loggerName, String newLevel) {
        if (!authorizedOperators.contains(requestingUser)) {
            return "403 Forbidden -- '" + requestingUser + "' is not authorized to change log levels";
        }
        liveLoggerLevels.put(loggerName, newLevel);
        return "200 OK -- level set to " + newLevel + " by authorized operator '" + requestingUser + "'";
    }

    public static void main(String[] args) {
        System.out.println(postLoggerLevel("mallory", "com.example.payment", "DEBUG")); // UNAUTHORIZED attempt
        logDebug("com.example.payment", "should NOT print -- unauthorized change was rejected");

        System.out.println(postLoggerLevel("alice", "com.example.payment", "DEBUG")); // AUTHORIZED
        logDebug("com.example.payment", "should print -- authorized change succeeded");
    }
}
```

How to run: `java RestrictedLoggerEndpointAccess.java`

`postLoggerLevel` checks `authorizedOperators.contains(requestingUser)` before making any change. When `"mallory"` (not in the allowlist) attempts the change, the method returns a `403 Forbidden` and `liveLoggerLevels` is left untouched — the subsequent `logDebug` call correctly stays silent. When `"alice"` (an authorized operator) makes the identical request, the change succeeds, and the subsequent `logDebug` call correctly emits — demonstrating why production deployments restrict this mutating endpoint to authorized operators, since unrestricted access would let anyone remotely trigger potentially sensitive or high-volume debug logging on a live production service.

## 6. Walkthrough

Trace `RestrictedLoggerEndpointAccess.main` in order. **First**, `postLoggerLevel("mallory", "com.example.payment", "DEBUG")` runs: `authorizedOperators.contains("mallory")` is `false`, so the `if` branch fires, returning the `403 Forbidden` string without ever touching `liveLoggerLevels`.

**Next**, `logDebug("com.example.payment", ...)` runs: `liveLoggerLevels.getOrDefault("com.example.payment", "INFO")` still returns `"INFO"` (nothing was ever set), so the condition `"DEBUG".equals("INFO")` is `false`, and the message is correctly not printed.

**Then**, `postLoggerLevel("alice", "com.example.payment", "DEBUG")` runs: `authorizedOperators.contains("alice")` is `true`, so the `if` branch is skipped; the method proceeds to `liveLoggerLevels.put("com.example.payment", "DEBUG")` and returns a `200 OK` success message.

**Finally**, `logDebug("com.example.payment", ...)` runs again: this time `liveLoggerLevels.getOrDefault("com.example.payment", "INFO")` returns `"DEBUG"` (set by Alice's successful call), so `"DEBUG".equals("DEBUG")` is `true`, and the message correctly prints.

```
postLoggerLevel(mallory, ...)  -> NOT authorized -> 403, liveLoggerLevels UNCHANGED
logDebug(...)                  -> level still INFO -> correctly SKIPPED
postLoggerLevel(alice, ...)    -> authorized -> 200 OK, liveLoggerLevels updated to DEBUG
logDebug(...)                  -> level now DEBUG -> correctly EMITTED
```

## 7. Gotchas & takeaways

> Leaving `/actuator/loggers` writable without authentication or authorization on a production service is a real, exploitable risk — an attacker (or an accidental internal misuse) could remotely force verbose debug logging across a service, potentially exposing sensitive data in logs or degrading performance through excessive log volume. Always restrict write access to this endpoint via Spring Security or network-level controls.

- `/actuator/loggers` is Spring Boot's built-in mechanism for [dynamic log level changes](0362-log-levels-dynamic-log-level-changes.md): `GET` lists current levels, `POST` changes a specific logger's level on the live, running instance immediately.
- This makes it practical to temporarily raise verbosity during an active incident investigation without any redeploy, and to revert it just as quickly afterward.
- Because it's a mutating operation, restrict who can call it (unlike read-only endpoints like `/health`) to avoid both security risks (leaked debug data) and operational risks (accidental log flooding).
- This endpoint is one specific, concrete example of the broader operational value [Spring Boot Actuator](0365-spring-boot-actuator-endpoints-health-info-metrics-env-etc.md) provides across a whole microservices fleet.
