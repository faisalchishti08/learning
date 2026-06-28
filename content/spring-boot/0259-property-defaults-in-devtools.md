---
card: spring-boot
gi: 259
slug: property-defaults-in-devtools
title: Property defaults in DevTools
---

## 1. What it is

When `spring-boot-devtools` is on the classpath, it automatically applies a set of **development-friendly property overrides** — settings that make debugging easier but would be inappropriate in production. These apply on top of your `application.properties` without requiring you to write anything.

The most significant overrides:

| Property | DevTools value | Why |
|---|---|---|
| `spring.thymeleaf.cache` | `false` | See template changes without restart |
| `spring.freemarker.cache` | `false` | Same for Freemarker |
| `spring.mustache.cache` | `false` | Same for Mustache |
| `spring.web.resources.cache.period` | `0` | Disable static resource HTTP caching |
| `spring.web.resources.chain.cache` | `false` | Disable resource chain caching |
| `server.error.include-stacktrace` | `always` | See full stack trace in browser error pages |
| `logging.level.web` | `DEBUG` | Log every HTTP request/response |
| `spring.mvc.log-request-details` | `true` | Log request parameters and headers |
| `spring.jpa.open-in-view` | (unchanged, but warns) | DevTools logs a warning if true |

## 2. Why & when

Production-appropriate defaults are bad for development:

- **Template caching** (`spring.thymeleaf.cache=true`) is correct in production — you don't want the JVM reading the file system on every request. But during development, every template edit requires a JVM restart to see the change. DevTools disables caching so the template is re-read on each request.
- **DEBUG logging for web** helps you see the request/response cycle during development — which routes are being hit, what parameters arrived, what headers were sent. In production this log would be enormous.
- **Stack traces in error pages** (`server.error.include-stacktrace=always`) shows the full Java stack in the browser's `/error` response. Crucial for debugging; a security issue in production.

These overrides **disappear automatically** in production because DevTools disables itself when not present in a "full" classpath (fat JAR, production mode). You don't need to reset them.

## 3. Core concept

DevTools uses `DevToolsPropertyDefaultsPostProcessor` — a `EnvironmentPostProcessor` that runs very early in the application startup, before `application.properties` is loaded. It adds a low-priority `PropertySource` to the environment called `devtools`.

Because this source has **low priority**, any property you explicitly set in `application.properties` overrides the DevTools default. If you explicitly set `spring.thymeleaf.cache=true`, that wins over DevTools' `false`.

This gives you a clean hierarchy:
```
your application.properties  ← highest priority
  DevTools defaults           ← overridden by your explicit settings
    Spring Boot defaults      ← baseline
```

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DevTools property defaults injected as low-priority property source in Spring Environment">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Priority stack (high at top) -->
  <text x="350" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Environment — property sources (high priority first)</text>

  <rect x="100" y="35" width="500" height="38" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="57" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">application.properties / env vars / CLI args</text>
  <text x="630" y="57" fill="#6db33f" font-size="9" text-anchor="right" font-family="sans-serif">highest</text>

  <rect x="100" y="83" width="500" height="38" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="105" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">DevTools defaults  (DevToolsPropertyDefaultsPostProcessor)</text>

  <rect x="100" y="131" width="500" height="38" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="153" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Boot autoconfiguration defaults</text>
  <text x="630" y="153" fill="#8b949e" font-size="9" text-anchor="right" font-family="sans-serif">lowest</text>

  <!-- Example override -->
  <text x="350" y="200" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">If application.properties has spring.thymeleaf.cache=true  →  DevTools value ignored</text>
  <text x="350" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">If not set  →  DevTools default (false) applies automatically</text>
</svg>

DevTools injects a low-priority property source; your explicit settings always win over DevTools defaults.

## 5. Runnable example

```java
// PropertyDefaultsDemo.java — run with: java PropertyDefaultsDemo.java
// Prints all DevTools property overrides and explains each one.

import java.util.LinkedHashMap;
import java.util.Map;

public class PropertyDefaultsDemo {

    record Override(String devValue, String prodDefault, String reason) {}

    public static void main(String[] args) {
        System.out.println("=== DevTools Property Defaults ===\n");

        Map<String, Override> overrides = new LinkedHashMap<>();

        // Template caching
        overrides.put("spring.thymeleaf.cache",
            new Override("false", "true",
                "Re-read templates on each request (no restart needed)"));
        overrides.put("spring.freemarker.cache",
            new Override("false", "true", "Same for Freemarker"));
        overrides.put("spring.mustache.servlet.cache",
            new Override("false", "true", "Same for Mustache"));
        overrides.put("spring.groovy.template.cache",
            new Override("false", "true", "Same for Groovy templates"));

        // Static resources
        overrides.put("spring.web.resources.cache.period",
            new Override("0s", "unset (browser caches)", "Browser always fetches latest CSS/JS"));
        overrides.put("spring.web.resources.chain.cache",
            new Override("false", "true", "Disable resource chain version fingerprinting"));

        // Error pages
        overrides.put("server.error.include-stacktrace",
            new Override("always", "never",
                "Show full stack trace in /error page during development"));
        overrides.put("server.error.include-binding-errors",
            new Override("always", "never", "Show validation errors in /error page"));
        overrides.put("server.error.include-message",
            new Override("always", "never", "Show exception message in /error page"));
        overrides.put("server.error.include-exception",
            new Override("true", "false", "Show exception class name in /error page"));

        // Logging
        overrides.put("logging.level.web",
            new Override("DEBUG", "(unset)", "Log every HTTP request + response"));
        overrides.put("spring.mvc.log-request-details",
            new Override("true", "false", "Log request params and headers at DEBUG"));
        overrides.put("spring.web.mvc.problemdetails.enabled",
            new Override("(unchanged)", "(unchanged)", "RFC 9457 errors — no DevTools override"));

        // H2 console
        overrides.put("spring.h2.console.enabled",
            new Override("true", "false",
                "Enable H2 web console at /h2-console for in-memory DB inspection"));

        System.out.printf("%-50s  %-15s  %-15s  %s%n",
            "Property", "DevTools", "Prod default", "Reason");
        System.out.println("-".repeat(130));
        overrides.forEach((k, v) ->
            System.out.printf("%-50s  %-15s  %-15s  %s%n",
                k, v.devValue(), v.prodDefault(), v.reason()));

        System.out.println("\n--- How to override a DevTools default ---");
        System.out.println("""
            # application.properties (your explicit setting always wins):
            spring.thymeleaf.cache=true    # even with devtools present, cache is ON

            # Or disable ALL DevTools property defaults at once:
            spring.devtools.add-properties=false
            """);
    }
}
```

**How to run:** `java PropertyDefaultsDemo.java`

## 6. Walkthrough

- **Template cache disabled** — Thymeleaf's default `spring.thymeleaf.cache=true` means the template is compiled once and kept in memory. With DevTools, `false` makes Thymeleaf re-parse the template on every HTTP request. This costs a few milliseconds per request but means you see edits instantly without any restart.
- **Static resource cache period = 0** — sets `Cache-Control: no-cache` on static resources. Without this, your browser might cache `app.css` and show you the old styles even after you've edited the file.
- **`server.error.include-stacktrace=always`** — the default Spring Boot error response to a browser (`/error`) includes exception type and message. DevTools adds the full stack trace so you can debug in the browser without opening the server log. Never use this in production.
- **`spring.h2.console.enabled=true`** — DevTools enables the H2 web console automatically when H2 is on the classpath. Navigate to `/h2-console` to browse the in-memory database interactively during development.
- **`spring.devtools.add-properties=false`** — escape hatch to disable all DevTools property injection while keeping automatic restart and LiveReload. Useful when you want to test production-like property behaviour in a local dev environment.

## 7. Gotchas & takeaways

> **`logging.level.web=DEBUG` makes logs very verbose.** On an app with frequent polling (e.g., a UI that polls every second), your console will be flooded with request logs. Set `logging.level.web=INFO` in `application.properties` to override the DevTools default if the noise is too high.

> **The H2 console (`/h2-console`) enabled by DevTools has no security by default.** If you expose a dev server on a non-loopback interface (e.g., `server.address=0.0.0.0`), anyone on the network can access the database. Add Spring Security or set `spring.h2.console.settings.web-allow-others=false` (the default) and only bind to localhost.

- You don't need to write any of these overrides yourself — DevTools applies them automatically.
- They disappear automatically in production (fat JAR execution or when devtools is not on the classpath).
- Override any of them in `application.properties` or `application-dev.properties` — your explicit value always wins.
- Check the full list: `DevToolsPropertyDefaultsPostProcessor` source code (Spring Boot GitHub).
- The `add-properties=false` escape hatch is useful for integration tests that should behave like production.
