---
card: spring-boot
gi: 49
slug: customizing-the-banner
title: Customizing the banner
---

## 1. What it is

The **Spring Boot banner** is the text or image printed to the console when the application starts — the famous ASCII-art "Spring" logo by default. You can customise it, replace it entirely, or disable it.

Three ways to customise:

**1. Text file** — create `src/main/resources/banner.txt` with any ASCII art or text. Spring Boot reads it automatically.

**2. Image file** — create `src/main/resources/banner.png` (or `.gif`, `.jpg`). Spring Boot converts it to ASCII art on the fly.

**3. Programmatic** — implement the `Banner` interface:
```java
app.setBanner((environment, sourceClass, out) ->
    out.println("My Custom App v" + environment.getProperty("spring.application.version")));
```

**Disable entirely:**
```properties
spring.main.banner-mode=off   # values: console, log, off
```

## 2. Why & when

The banner has no functional impact but has practical value:
- **Identify the service** in a terminal full of log output when running multiple services.
- **Display build information** — version, build date, Git commit hash — using `${spring.application.version}` or `${application.version}` variable substitution in `banner.txt`.
- **Suppress the banner** in tests and production to reduce log noise.

Customise the banner when you want service identity visible at startup, or suppress it when logs feed into structured log aggregators (Elasticsearch, Splunk) where the ASCII art appears as junk.

## 3. Core concept

`SpringApplication` prints the banner during stage 4 of the launch sequence (before the `ApplicationContext` is created). The `Banner` interface has one method:

```java
void printBanner(Environment environment, Class<?> sourceClass, PrintStream out);
```

Spring Boot resolves which banner to print using this priority order:
1. `SpringApplication.setBanner(Banner)` — programmatic override (highest priority).
2. `banner.gif` / `banner.jpg` / `banner.png` on the classpath.
3. `banner.txt` on the classpath.
4. Spring Boot's default `SpringBootBanner` (the ASCII Spring logo).

`banner.txt` supports variable substitution from the environment:
- `${spring.boot.version}` — Spring Boot version.
- `${spring.application.version}` — value of `Implementation-Version` in `MANIFEST.MF`.
- `${application.title}` — value of `Implementation-Title` in `MANIFEST.MF`.
- Any `${...}` expression resolvable from `application.properties`.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Banner resolution priority order from programmatic to default Spring Boot banner">
  <!-- Priority ladder -->
  <rect x="20" y="20" width="620" height="46" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="40" y="38" fill="#6db33f" font-size="11" font-family="monospace">Priority 1 (highest): app.setBanner(myBanner)</text>
  <text x="40" y="56" fill="#8b949e" font-size="10" font-family="monospace">    → prints whatever your Banner implementation returns</text>

  <rect x="20" y="76" width="620" height="46" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="40" y="94" fill="#79c0ff" font-size="11" font-family="monospace">Priority 2: banner.png / banner.gif / banner.jpg on classpath</text>
  <text x="40" y="112" fill="#8b949e" font-size="10" font-family="monospace">    → image converted to ASCII art and printed</text>

  <rect x="20" y="132" width="620" height="46" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="40" y="150" fill="#79c0ff" font-size="11" font-family="monospace">Priority 3: banner.txt on classpath</text>
  <text x="40" y="168" fill="#8b949e" font-size="10" font-family="monospace">    → text printed with ${...} variable substitution</text>

  <rect x="20" y="188" width="620" height="46" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="40" y="206" fill="#8b949e" font-size="11" font-family="monospace">Priority 4 (fallback): Spring Boot default banner</text>
  <text x="40" y="224" fill="#8b949e" font-size="10" font-family="monospace">    → the standard "  .   ____  Spring Boot" ASCII art</text>
</svg>

Spring Boot checks in priority order and uses the first source it finds; if `spring.main.banner-mode=off`, nothing prints regardless.

## 5. Runnable example

```java
// BannerDemo.java
// How to run: java BannerDemo.java  (JDK 17+)
// Demonstrates the Banner interface and resolution priority without Spring on the classpath.

import java.io.*;
import java.util.*;

public class BannerDemo {

    // Simulated environment (wraps application.properties values)
    static Map<String, String> env = new LinkedHashMap<>();
    static {
        env.put("spring.boot.version", "3.3.0");
        env.put("spring.application.name", "my-service");
        env.put("app.version", "1.4.2");
    }

    @FunctionalInterface
    interface Banner { void print(PrintStream out); }

    // ── banner.txt content (would be src/main/resources/banner.txt) ─
    static final String BANNER_TXT = """
            __  __        ____                  _
           |  \\/  |_   _ / ___|  ___ _ ____   _(_) ___ ___
           | |\\/| | | | |\\___ \\ / _ \\ '__\\ \\ / / |/ __/ _ \\
           | |  | | |_| | ___) |  __/ |   \\ V /| | (_|  __/
           |_|  |_|\\__, ||____/ \\___|_|    \\_/ |_|\\___\\___|
                   |___/
           App: ${spring.application.name}  v${app.version}
           Spring Boot: ${spring.boot.version}
        """;

    // ── programmatic banner (highest priority) ──────────────────────
    static Banner programmaticBanner = out ->
        out.println(">>> " + resolve("${spring.application.name}")
            + " v" + resolve("${app.version}") + " <<<");

    public static void main(String[] args) {
        System.out.println("=== Priority 1: Programmatic banner (setBanner()) ===");
        programmaticBanner.print(System.out);

        System.out.println("\n=== Priority 3: banner.txt with variable substitution ===");
        System.out.println(resolve(BANNER_TXT));

        System.out.println("=== spring.main.banner-mode=off ===");
        System.out.println("(nothing printed — banner suppressed)");
    }

    static String resolve(String template) {
        String result = template;
        for (Map.Entry<String, String> e : env.entrySet()) {
            result = result.replace("${" + e.getKey() + "}", e.getValue());
        }
        return result;
    }
}
```

**How to run:** `java BannerDemo.java`

Expected output:
```
=== Priority 1: Programmatic banner (setBanner()) ===
>>> my-service v1.4.2 <<<

=== Priority 3: banner.txt with variable substitution ===
        __  __        ____                  _
       |  \/  |_   _ / ___|  ___ _ ____   _(_) ___ ___
       | |\/| | | | |\___ \ / _ \ '__\ \ / / |/ __/ _ \
       | |  | | |_| | ___) |  __/ |   \ V /| | (_|  __/
       |_|  |_|\__, ||____/ \___|_|    \_/ |_|\___\___|
               |___/
       App: my-service  v1.4.2
       Spring Boot: 3.3.0

=== spring.main.banner-mode=off ===
(nothing printed — banner suppressed)
```

## 6. Walkthrough

- `env` simulates the Spring `Environment` — in a real app, values come from `application.properties`, `MANIFEST.MF`, and system properties.
- `programmaticBanner` is a `Banner` functional interface — it receives the `PrintStream` and can print anything. Set via `SpringApplication.setBanner(...)`.
- `BANNER_TXT` is the content of a `banner.txt` file. The `${...}` syntax is Spring's property substitution notation; `resolve()` substitutes values from the environment map.
- The demo shows priorities 1 and 3. Priority 2 (image) is skipped because it requires a graphics library to convert pixels to ASCII; the mechanism is the same.
- `banner-mode=off` is shown as commentary — in a real Spring Boot app `spring.main.banner-mode=off` in `application.properties` suppresses all output regardless of which banner sources are present.

## 7. Gotchas & takeaways

> Using `${spring.application.version}` in `banner.txt` requires that the JAR's `MANIFEST.MF` contains an `Implementation-Version` entry. Spring Boot Maven/Gradle plugins add this automatically when you run `mvn package` or `gradle bootJar`, but it is **not** present when running directly from the IDE — you'll see a blank version.

> Image banners (`.png`, `.gif`) require `com.twelvemonkeys.imageio:imageio-core` on the classpath in Spring Boot 3.x; it is no longer bundled. If the dependency is missing, Spring Boot silently skips the image banner and falls back to the text banner or default.

- Place `banner.txt` in `src/main/resources/` — it is automatically on the classpath and read by Spring Boot.
- `AnsiColor` and `AnsiStyle` constants are available in `banner.txt`: `${AnsiColor.GREEN}my text${AnsiColor.DEFAULT}` prints coloured output on ANSI terminals.
- Use `spring.banner.location` to load a banner from a non-default path: `spring.banner.location=classpath:/branding/banner.txt`.
- In tests, add `spring.main.banner-mode=off` to `src/test/resources/application.properties` to eliminate banner noise from test output.
- The banner is printed before the logging system is fully initialised — this is why it always goes to `System.out` regardless of log configuration.
