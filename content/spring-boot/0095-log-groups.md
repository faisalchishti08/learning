---
card: spring-boot
gi: 95
slug: log-groups
title: Log groups
---

## 1. What it is

**Log groups** let you assign a single short name to a list of logger names, then control all of them with one `logging.level.*` property. You define a group with:

```properties
logging.group.web=org.springframework.core.codec,org.springframework.http,org.springframework.web
logging.level.web=DEBUG
```

The second line sets `DEBUG` on all three loggers at once — as if you had written all three `logging.level.*` lines individually.

Spring Boot ships with **two predefined groups** that are always available:

| Group name | Loggers included |
|---|---|
| `web` | `org.springframework.core.codec`, `org.springframework.http`, `org.springframework.web`, `org.springframework.boot.actuate.endpoint.web`, `org.springframework.boot.web.servlet.ServletContextInitializerBeans` |
| `sql` | `org.springframework.jdbc.core`, `org.hibernate.SQL`, `org.jooq.tools.LoggerListener` |

`logging.level.web=DEBUG` and `logging.level.sql=DEBUG` are the shortest ways to enable framework-level diagnostic logging for HTTP and SQL respectively.

## 2. Why & when

Diagnostic logging for a feature often requires enabling 3–8 individual loggers across multiple packages. Without groups, you'd write:

```properties
logging.level.org.springframework.core.codec=DEBUG
logging.level.org.springframework.http=DEBUG
logging.level.org.springframework.web=DEBUG
```

With a group, you write one line. Groups are useful when:
- You want a quick diagnostic toggle for HTTP request handling (`logging.level.web=DEBUG`).
- You want to see all SQL and bind parameters in one go (`logging.level.sql=DEBUG`).
- Your team has a set of application-specific loggers that are always tuned together (e.g. all payment-related packages).
- You are writing a Spring Boot library and want to expose a named logging group for your users.

## 3. Core concept

Groups are resolved before level assignment. The property processor:

1. Reads all `logging.group.*` definitions from `application.properties` (built-in groups are loaded from Spring Boot's `spring-configuration-metadata.json`).
2. When it sees `logging.level.<groupName>=<level>`, it expands `<groupName>` to the list of member loggers and sets `<level>` on each one.

You can also use group names with Actuator: `POST /actuator/loggers/web` with `{"configuredLevel":"DEBUG"}` sets all web loggers at runtime.

Custom group definition + usage:
```properties
# Define the group (your own packages)
logging.group.payment=com.example.payment,com.example.billing,com.example.audit

# Set a level for the whole group
logging.level.payment=TRACE

# Or set them individually to override
logging.level.com.example.audit=WARN
```

When you set a level on an individual logger that is also in a group, the most recent/specific wins (same as normal logger hierarchy rules).

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Log groups: one group name 'web' expands to five member loggers, all set to DEBUG with one property">
  <rect x="8" y="8" width="664" height="244" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Log Group Expansion</text>

  <!-- logging.level.web=DEBUG -->
  <rect x="30" y="50" width="250" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="155" y="66" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace" font-weight="bold">logging.level.web=DEBUG</text>
  <text x="155" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one property → 5 loggers</text>

  <!-- Arrow -->
  <defs><marker id="ga" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker></defs>
  <line x1="282" y1="70" x2="335" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>
  <text x="308" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">expands</text>

  <!-- Member loggers -->
  <rect x="338" y="48" width="316" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="496" y="67" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">org.springframework.core.codec → DEBUG</text>

  <rect x="338" y="82" width="316" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="496" y="101" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">org.springframework.http → DEBUG</text>

  <rect x="338" y="116" width="316" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="496" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">org.springframework.web → DEBUG</text>

  <rect x="338" y="150" width="316" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="496" y="169" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">…boot.actuate.endpoint.web → DEBUG</text>

  <rect x="338" y="184" width="316" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="496" y="203" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">…web.servlet.ServletContextInitializerBeans → DEBUG</text>

  <!-- Built-in note -->
  <rect x="30" y="218" width="290" height="24" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="175" y="234" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Built-in groups: "web" and "sql" — no definition needed</text>
</svg>

One property name, multiple loggers. Built-in `web` and `sql` groups are ready to use immediately.

## 5. Runnable example

```java
// LogGroups.java — run: java LogGroups.java  (JDK 17+)
// Simulates Spring Boot log group definition and expansion.

import java.util.*;

public class LogGroups {

    // Simulated built-in groups (from Spring Boot's metadata)
    static final Map<String, List<String>> BUILTIN_GROUPS = Map.of(
        "web", List.of(
            "org.springframework.core.codec",
            "org.springframework.http",
            "org.springframework.web",
            "org.springframework.boot.actuate.endpoint.web",
            "org.springframework.boot.web.servlet.ServletContextInitializerBeans"
        ),
        "sql", List.of(
            "org.springframework.jdbc.core",
            "org.hibernate.SQL",
            "org.jooq.tools.LoggerListener"
        )
    );

    static final Map<String, String> LEVEL_PROPS = new LinkedHashMap<>();
    static final Map<String, List<String>> USER_GROUPS = new LinkedHashMap<>();

    static void setProperty(String key, String value) {
        if (key.startsWith("logging.group.")) {
            String groupName = key.substring("logging.group.".length());
            USER_GROUPS.put(groupName, Arrays.asList(value.split(",")));
        } else if (key.startsWith("logging.level.")) {
            LEVEL_PROPS.put(key.substring("logging.level.".length()), value);
        }
    }

    static Map<String, String> resolve() {
        Map<String, String> allGroups = new LinkedHashMap<>(BUILTIN_GROUPS.entrySet().stream()
            .collect(java.util.stream.Collectors.toMap(Map.Entry::getKey,
                e -> String.join(",", e.getValue()))));
        USER_GROUPS.forEach((k, v) -> allGroups.put(k, String.join(",", v)));

        Map<String, String> resolved = new LinkedHashMap<>();
        LEVEL_PROPS.forEach((name, level) -> {
            if (allGroups.containsKey(name)) {
                // Expand group
                for (String member : allGroups.get(name).split(","))
                    resolved.put(member.trim(), level);
            } else {
                resolved.put(name, level);
            }
        });
        return resolved;
    }

    public static void main(String[] args) {
        // Simulated application.properties
        setProperty("logging.level.root", "WARN");
        setProperty("logging.level.web", "DEBUG");          // built-in group
        setProperty("logging.level.sql", "DEBUG");          // built-in group

        // Custom group
        setProperty("logging.group.payment",
                "com.example.payment,com.example.billing,com.example.audit");
        setProperty("logging.level.payment", "TRACE");      // custom group
        setProperty("logging.level.com.example.audit", "WARN");  // individual override

        System.out.println("=== Resolved logger levels ===");
        resolve().forEach((logger, level) ->
            System.out.printf("  %-60s = %s%n", logger, level));

        System.out.println("\n=== Built-in group: sql ===");
        System.out.println("logging.level.sql=DEBUG enables:");
        BUILTIN_GROUPS.get("sql").forEach(l -> System.out.println("  " + l));
    }
}
```

**How to run:** `java LogGroups.java`

## 6. Walkthrough

- `BUILTIN_GROUPS` maps the two predefined group names to their member logger lists. In Spring Boot, these are defined in `spring-configuration-metadata.json` and loaded by `LoggingApplicationListener`.
- `setProperty("logging.level.web", "DEBUG")` — the property processor sees `web` as a group name, expands it to all five member loggers, and records `DEBUG` for each.
- `setProperty("logging.group.payment", "…")` defines a custom group. Any name can be used as a group name as long as it doesn't collide with a logger package prefix.
- `setProperty("logging.level.payment", "TRACE")` — expands the `payment` group to `com.example.payment`, `com.example.billing`, and `com.example.audit`, all at `TRACE`.
- `setProperty("logging.level.com.example.audit", "WARN")` — a subsequent individual level property for a member logger overrides the group level. `resolve()` processes in property order; this line comes last, so `com.example.audit` ends up at `WARN` rather than `TRACE`.
- The final printout shows the effective per-logger levels — equivalent to what Actuator's `/actuator/loggers` shows after Spring Boot processes all `logging.level.*` properties.

## 7. Gotchas & takeaways

> **`logging.level.web=DEBUG` is a diagnostic tool, not a production setting.** It enables `DEBUG` on five Spring loggers, including `org.springframework.web` which logs every controller invocation and every request mapping decision. In a busy service this produces enormous output.

> **Group names must not match existing logger package prefixes.** If you create a group named `org.springframework`, the property processor may expand it differently than expected. Use short, clearly synthetic names (`web`, `sql`, `payment`, `myteam-auth`).

- `logging.level.sql=DEBUG` is the fastest way to enable SQL logging without remembering Hibernate's logger names.
- `logging.level.web=TRACE` is the nuclear option for HTTP debugging — includes request/response body codecs.
- Custom groups are defined with `logging.group.<name>=logger1,logger2,…` — define once, reuse across environments.
- Actuator accepts group names: `POST /actuator/loggers/web` with `{"configuredLevel":"DEBUG"}` expands the group at runtime.
- Group expansion is purely a convenience alias — it creates no additional abstraction at the Logback level. Each member logger still has its own independent effective level.
