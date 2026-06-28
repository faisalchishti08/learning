---
card: spring-boot
gi: 261
slug: global-devtools-settings
title: Global DevTools settings
---

## 1. What it is

Spring Boot DevTools supports a **global configuration file** that applies to *all* Spring Boot projects on a developer's machine — without needing to add the settings to each project's `application.properties`.

The file location:

- **Spring Boot 2.6+**: `~/.config/spring-boot/spring-boot-devtools.properties`
- **Spring Boot < 2.6**: `~/.spring-boot-devtools.properties` (home directory)

On Windows the paths use the user home directory (`%USERPROFILE%`).

Any property from the `spring.devtools.*` namespace is valid here. Settings in the global file have lower priority than project-level `application.properties`, so projects can always override the global defaults.

## 2. Why & when

Global settings are for developer preferences that should apply everywhere:

- You always want restart quiet-period to be 200 ms (faster feedback) regardless of project.
- You always want to exclude a certain folder from restart triggers.
- You always want LiveReload on a non-standard port (because another tool uses 35729).
- You never want the H2 console enabled globally.

Without a global file, you'd repeat the same `spring.devtools.*` properties in every project's `application.properties` — or forget to add them and wonder why behavior differs across projects.

Global settings are a developer-machine concern, not a project concern. They belong in your dotfiles, not in source control.

## 3. Core concept

The global DevTools properties file is discovered by `DevToolsHomePropertiesPostProcessor`, which runs before any application-specific `EnvironmentPostProcessor`. It adds the global properties as a `PropertySource` with **lower priority than project-level** sources.

Priority order (highest to lowest):

```
1. CLI args / env vars
2. application.properties in project
3. application-devtools.properties (project-level)
4. DevTools default property overrides (template cache=false etc.)
5. ~/.config/spring-boot/spring-boot-devtools.properties  ← global
6. Spring Boot framework defaults
```

If the global file says `spring.devtools.restart.poll-interval=500ms` and the project's `application.properties` says `spring.devtools.restart.poll-interval=2s`, the project wins.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Global DevTools file scope: applies to all projects, overridden by project-level settings">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Global file -->
  <rect x="10" y="80" width="200" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Global Config</text>
  <text x="110" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">~/.config/spring-boot/</text>
  <text x="110" y="137" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">spring-boot-devtools.properties</text>

  <!-- Projects -->
  <rect x="280" y="30" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Project A</text>
  <text x="370" y="73" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no devtools properties</text>
  <text x="370" y="84" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">→ global settings apply</text>

  <rect x="280" y="110" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="135" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Project B</text>
  <text x="370" y="153" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">poll-interval=2s (project)</text>
  <text x="370" y="164" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">→ overrides global 500ms</text>

  <rect x="280" y="190" width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="210" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Project C … N (same)</text>

  <line x1="210" y1="100" x2="278" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="210" y1="115" x2="278" y2="140" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="210" y1="130" x2="278" y2="205" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="218" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" dy="12">Project settings override global — global is the fallback for all projects</text>
</svg>

The global file is a machine-wide fallback; any project-level property wins over it.

## 5. Runnable example

```java
// GlobalDevToolsDemo.java — run with: java GlobalDevToolsDemo.java
// Shows how to create the global config file and what settings
// make sense as machine-wide vs project-specific.

import java.io.IOException;
import java.nio.file.*;

public class GlobalDevToolsDemo {

    public static void main(String[] args) throws Exception {
        System.out.println("=== Global DevTools Settings ===\n");

        printFilePaths();
        printRecommendedGlobalSettings();
        printWhatShouldStayProjectLevel();
        demonstrateCreation();
    }

    static void printFilePaths() {
        String home = System.getProperty("user.home");
        System.out.println("--- File location by OS ---");
        System.out.printf("  macOS / Linux : %s/.config/spring-boot/spring-boot-devtools.properties%n", home);
        System.out.printf("  Windows       : %s\\.config\\spring-boot\\spring-boot-devtools.properties%n", home);
        System.out.printf("  Legacy (<2.6) : %s/.spring-boot-devtools.properties%n", home);
        System.out.println();
    }

    static void printRecommendedGlobalSettings() {
        System.out.println("--- Recommended global settings ---");
        System.out.println("""
            # Faster restart feedback (default: 1s / 400ms)
            spring.devtools.restart.poll-interval=500ms
            spring.devtools.restart.quiet-period=200ms

            # LiveReload on alternate port (if 35729 conflicts)
            # spring.devtools.livereload.port=35730

            # Always use trigger-file for restart control
            # spring.devtools.restart.trigger-file=.restart

            # Disable H2 console globally (enable per-project if needed)
            # spring.h2.console.enabled=false

            # Exclude IDE metadata dirs from restart
            spring.devtools.restart.exclude=.idea/**,.vscode/**,*.iml,**/*.swp
            """);
    }

    static void printWhatShouldStayProjectLevel() {
        System.out.println("--- Settings that belong in project application.properties ---");
        System.out.println("""
            # Project-specific restart trigger:
            spring.devtools.restart.trigger-file=.restart-myproject

            # Project-specific additional paths:
            spring.devtools.restart.additional-paths=config/,scripts/

            # Remote DevTools secret (NEVER global — project-specific):
            spring.devtools.remote.secret=...
            """);
    }

    static void demonstrateCreation() throws IOException {
        String home = System.getProperty("user.home");
        Path dir  = Path.of(home, ".config", "spring-boot");
        Path file = dir.resolve("spring-boot-devtools.properties");

        System.out.println("--- Check / create global config ---");
        System.out.println("  Config dir:  " + dir);
        System.out.println("  Config file: " + file);
        System.out.println("  Exists:      " + Files.exists(file));

        if (!Files.exists(file)) {
            System.out.println();
            System.out.println("  To create it:");
            System.out.println("    mkdir -p " + dir);
            System.out.println("    cat > " + file + " << 'EOF'");
            System.out.println("    spring.devtools.restart.poll-interval=500ms");
            System.out.println("    spring.devtools.restart.quiet-period=200ms");
            System.out.println("    EOF");
        } else {
            System.out.println("  File already exists — showing content:");
            Files.readAllLines(file).forEach(l -> System.out.println("    " + l));
        }
    }
}
```

**How to run:** `java GlobalDevToolsDemo.java`

## 6. Walkthrough

- **`printFilePaths()`** — reads `user.home` (the JVM system property for the home directory) and constructs the path. The `~/.config/spring-boot/` directory follows the XDG Base Directory Specification used on Linux/macOS; Windows uses the same relative path under `%USERPROFILE%`.
- **`poll-interval=500ms`** — halves the time between checking for changed files. On fast machines with SSDs this is safe; on slow machines or networked filesystems you may prefer the default 1 s.
- **`quiet-period=200ms`** — reduces the post-change settling time from 400 ms to 200 ms. Works well when your IDE saves atomically; less suitable when it writes large file sets (each partial write triggers the quiet period timer reset).
- **`spring.devtools.restart.exclude`** — adding IDE metadata directories prevents spurious restarts when IntelliJ reorganises `.idea/` indexes or VS Code updates `.vscode/settings.json`. These directories are not on the Java classpath but can be accidentally included if `additional-paths` is too broad.
- **`remote.secret` should NOT be global** — a global secret would apply to all your projects, meaning compromising one project's remote endpoint compromises all. Always set it per-project and never commit it to source control.

## 7. Gotchas & takeaways

> **The global file is silently ignored if it contains invalid properties.** Unlike Spring's main property loading, which throws on unknown properties, the DevTools global loader skips unrecognised keys. If a setting doesn't seem to take effect, check the property name spelling carefully — `spring.devtools.restart.poll-interval` (singular "poll") not `polling-interval`.

> **The global file is not loaded during tests** (`@SpringBootTest`). DevTools is disabled in test mode (classpath signature detection). Test speed is controlled separately via `spring.test.context.cache.maxSize`.

- Keep the global file in your dotfiles repo (version-controlled machine setup) — it's a personal developer tool, not project infrastructure.
- Prefer `~/.config/spring-boot/` over the legacy `~/.spring-boot-devtools.properties` for Spring Boot 2.6+ compatibility.
- Global settings are loaded very early (before application context); changes take effect on next app start.
- Document your global settings in team onboarding docs — new developers will appreciate knowing why your setup feels faster.
