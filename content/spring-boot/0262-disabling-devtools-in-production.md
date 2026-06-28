---
card: spring-boot
gi: 262
slug: disabling-devtools-in-production
title: Disabling DevTools in production
---

## 1. What it is

Spring Boot DevTools is designed to be **completely absent from production deployments**. There are two layers of protection:

1. **Automatic detection** — DevTools detects when it is running from a "production" JAR (a fat JAR executed via `java -jar`) and silently disables itself. Specifically, it checks whether its own classes were loaded by the application classloader (fat JAR mode) or by a parent classloader (IDE/development mode). In fat JAR mode it deactivates.

2. **Optional dependency scope** — declaring DevTools with `<optional>true</optional>` (Maven) or `developmentOnly` (Gradle) prevents it from being included in the fat JAR or in dependent library JARs. Other projects that use your project as a library won't accidentally inherit DevTools.

Even with both protections, it's good practice to understand exactly how and why DevTools self-disables.

## 2. Why & when

Accidentally running DevTools in production causes:

- **Security risk** — if `spring.devtools.remote.secret` is set, the remote restart endpoint is active and accepts class uploads over the network.
- **Performance hit** — the file-system watcher thread and LiveReload server consume resources.
- **Instability** — if any classpath file changes (e.g., log rotation creates a `.log` file in a classpath directory), DevTools may attempt a restart of a production server.
- **Misleading config** — DevTools' property overrides (`thymeleaf.cache=false`, `log level DEBUG`) make the production server behave unexpectedly.

Understanding the disabling mechanisms ensures you don't need to rely on runtime guards — but knowing how to add explicit guards is useful for belt-and-suspenders security.

## 3. Core concept

DevTools' self-disabling check in `DevToolsEnablementDeducer`:

```java
// Simplified pseudocode of DevTools' internal check
ClassLoader appClassLoader   = Thread.currentThread().getContextClassLoader();
ClassLoader devToolsClassLoader = DevToolsEnablementDeducer.class.getClassLoader();

if (appClassLoader == devToolsClassLoader) {
    // fat JAR — DevTools is loaded by same loader as app → disable
    return false;
}
// IDE launch — DevTools loaded by parent/separate loader → enable
return true;
```

In a fat JAR, all classes (including DevTools) are loaded by the same classloader — the JAR launcher. DevTools detects this and disables itself.

In IDE/Maven `spring-boot:run` mode, DevTools classes are loaded by a parent classloader while your application classes use a child restart classloader — the mismatch signals "development mode".

The `<optional>true</optional>` Maven scope is the compile-time guarantee: the fat JAR simply doesn't contain DevTools classes, so the runtime check is irrelevant.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DevTools disabling: fat JAR detection vs IDE mode classloader difference">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- IDE mode -->
  <rect x="10" y="20" width="300" height="190" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">IDE / mvn spring-boot:run</text>

  <rect x="25" y="60" width="270" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Parent ClassLoader</text>
  <text x="160" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DevTools classes here</text>

  <rect x="25" y="115" width="270" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="160" y="133" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Restart ClassLoader (child)</text>
  <text x="160" y="149" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Your app classes here</text>

  <text x="160" y="195" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Different loaders → DevTools ACTIVE</text>

  <!-- Fat JAR mode -->
  <rect x="390" y="20" width="300" height="190" rx="8" fill="#0d1117" stroke="#8b1a1a" stroke-width="1.5"/>
  <text x="540" y="45" fill="#ff7b72" font-size="12" text-anchor="middle" font-family="sans-serif">java -jar myapp.jar (production)</text>

  <rect x="405" y="60" width="270" height="95" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="540" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Single ClassLoader (JarLauncher)</text>
  <text x="540" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DevTools classes (if present)</text>
  <text x="540" y="119" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Your app classes</text>
  <text x="540" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Both in same loader</text>

  <text x="540" y="195" fill="#ff7b72" font-size="11" text-anchor="middle" font-family="sans-serif">Same loader → DevTools DISABLED</text>
</svg>

DevTools is active when loaded by a parent classloader (IDE); disabled when loaded by the same classloader as app code (fat JAR).

## 5. Runnable example

```java
// DisablingDevToolsDemo.java — run with: java DisablingDevToolsDemo.java
// Shows how to verify DevTools is disabled and how to add
// explicit production guards if you want belt-and-suspenders protection.

public class DisablingDevToolsDemo {

    public static void main(String[] args) {
        System.out.println("=== Disabling DevTools in Production ===\n");

        printDependencySetup();
        printRuntimeVerification();
        printExplicitDisable();
        printChecklist();
    }

    static void printDependencySetup() {
        System.out.println("--- Primary mechanism: scope (compile-time) ---");
        System.out.println("""
            <!-- Maven: excluded from fat JAR automatically -->
            <dependency>
              <groupId>org.springframework.boot</groupId>
              <artifactId>spring-boot-devtools</artifactId>
              <optional>true</optional>    ← NOT included in repackaged JAR
            </dependency>

            // Gradle: 'developmentOnly' configuration
            developmentOnly 'org.springframework.boot:spring-boot-devtools'
            // Also excluded from fat JAR by bootJar task automatically

            Verify with:
              jar tf target/myapp.jar | grep devtools
              (should return nothing)
            """);
    }

    static void printRuntimeVerification() {
        System.out.println("--- Runtime verification: check from running app ---");
        System.out.println("""
            // Add this bean to log DevTools status at startup:
            @Component
            class DevToolsStatusLogger implements ApplicationListener<ApplicationReadyEvent> {
                private static final Logger log = LoggerFactory.getLogger(DevToolsStatusLogger.class);

                @Override
                public void onApplicationEvent(ApplicationReadyEvent event) {
                    boolean devtoolsPresent = isDevToolsPresent();
                    log.info("DevTools active: {}", devtoolsPresent);
                    if (devtoolsPresent && isProductionProfile()) {
                        throw new IllegalStateException(
                            "DevTools must not run in production profile!");
                    }
                }

                private boolean isDevToolsPresent() {
                    try {
                        Class.forName("org.springframework.boot.devtools.settings.DevToolsSettings");
                        return true;
                    } catch (ClassNotFoundException e) {
                        return false;
                    }
                }

                private boolean isProductionProfile() {
                    // Check active profiles via Environment — simplified here
                    return false; // replace with actual check
                }
            }
            """);
    }

    static void printExplicitDisable() {
        System.out.println("--- Belt-and-suspenders: explicit disable in application.properties ---");
        System.out.println("""
            # Disable all DevTools features at runtime (even if on classpath):
            spring.devtools.restart.enabled=false
            spring.devtools.livereload.enabled=false
            spring.devtools.add-properties=false

            # Or use a Spring profile:
            # application-prod.properties:
            spring.devtools.restart.enabled=false
            spring.devtools.livereload.enabled=false
            """);
    }

    static void printChecklist() {
        System.out.println("--- Production DevTools checklist ---");
        String[] items = {
            "Maven: <optional>true</optional> on spring-boot-devtools dependency",
            "Gradle: developmentOnly scope (not implementation)",
            "CI: verify 'jar tf app.jar | grep devtools' returns empty",
            "No spring.devtools.remote.secret in production config",
            "spring.devtools.add-properties=false if devtools somehow sneaks in",
            "Port 35729 (LiveReload) blocked at firewall for prod servers",
        };
        for (var item : items) System.out.println("  [ ] " + item);
    }
}
```

**How to run:** `java DisablingDevToolsDemo.java`

## 6. Walkthrough

- **`<optional>true</optional>` vs `<scope>provided</scope>`** — `optional` marks the dependency as non-transitive and also excluded from the repackaged fat JAR by `spring-boot-maven-plugin`. `provided` would still be excluded from the repackaged JAR but *would* be included in a WAR's `WEB-INF/lib-provided/`. Use `optional` for DevTools.
- **`jar tf target/myapp.jar | grep devtools`** — the most reliable CI check. If this returns any output, DevTools made it into the production artifact and the pipeline should fail.
- **`Class.forName(...)` detection** — a programmatic way to check if DevTools is on the classpath at runtime. If the class is not found, DevTools is not present. This pattern is useful in `ApplicationReadyEvent` listeners that enforce environment constraints.
- **`spring.devtools.add-properties=false`** — even if DevTools is accidentally on the classpath, setting this property disables its property overrides (template cache, debug logging, etc.). It does not disable restart or LiveReload; for those, set their own flags.

## 7. Gotchas & takeaways

> **If you use `spring-boot-maven-plugin` with `repackage`, DevTools is automatically excluded from the fat JAR** when `<optional>true</optional>` is set. You don't need to configure exclusions in the plugin. The repackage goal reads the dependency scope and skips optional dependencies.

> **Gradle's `developmentOnly` is not the same as `compileOnly`.** `compileOnly` would exclude DevTools from the classpath at runtime but not from the fat JAR (if it were somehow included). `developmentOnly` is a custom configuration Spring Boot's Gradle plugin adds that excludes the JAR from the `bootJar` task output. Use `developmentOnly`.

- The automatic fat-JAR self-detection is reliable but a CI JAR content check is a defence-in-depth measure.
- If `remote.secret` is set, DevTools registers a servlet endpoint in the application — confirm this endpoint doesn't exist in production with a `curl /.~~spring-boot!~/restart` → expect 404.
- DevTools self-disables but leaves no log message by default; use the `Class.forName` probe in a startup event if you want explicit logging.
- One common accident: copying an `application.properties` from dev to prod and accidentally including `spring.devtools.remote.secret`. Audit config files in the CD pipeline.
