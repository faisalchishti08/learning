---
card: spring-boot
gi: 67
slug: config-data-locations-spring-config-import
title: Config data locations & spring.config.import
---

## 1. What it is

Spring Boot searches for `application.properties` (or `.yml`) in a handful of well-known locations automatically. `spring.config.location` **replaces** that search list — you point Boot at a different directory or file. `spring.config.import` **adds** to whatever Boot already loaded — it pulls in one or more extra sources (files, URLs, or config-server entries) after the normal search is done.

In short:

- `spring.config.location` — "look here *instead*."
- `spring.config.import` — "also load this on top."

## 2. Why & when

The defaults work fine on a developer laptop. They stop working the moment you deploy:

- Your **Docker container** mounts a secrets file at `/run/secrets/db.properties`. That path is not on Spring Boot's default search list.
- Your **monorepo** has a shared `common-config.properties` that every micro-service should inherit.
- You run Spring Cloud Config Server and every application must pull remote properties at startup.

`spring.config.location` solves the "different root directory" case. `spring.config.import` solves the "one more source, please" case and is the preferred modern tool (introduced in Spring Boot 2.4) because it composes cleanly — you can import from your local file *and* a remote config server in the same line.

## 3. Core concept

Think of Spring Boot's config loading like a **book** assembled from chapters. By default Boot picks up its own chapters from the classpath and `./config/`. `spring.config.location` lets you swap the entire chapter list. `spring.config.import` lets you staple extra chapters onto the front.

Properties follow the usual **override order**: items imported *later* override items imported *earlier*, and command-line arguments override everything. The `optional:` prefix tells Boot "this chapter may not exist — skip it gracefully instead of crashing."

Key mechanics:

- `spring.config.location` accepts a comma-separated list of directories (end with `/`) or files.
- `spring.config.import` accepts a comma-separated list of `file:`, `configtree:`, `classpath:`, or custom scheme URIs.
- An `optional:` prefix on any import source disables the `ConfigDataLocationNotFoundException` if the source is absent.
- Relative paths in `spring.config.import` resolve relative to the *current config file*, making them portable.

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Config loading flow: default search vs spring.config.location vs spring.config.import">
  <rect width="680" height="270" rx="10" fill="#0d1117"/>

  <!-- Default search box -->
  <rect x="20" y="20" width="190" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="45" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Default locations</text>
  <text x="115" y="66" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">classpath:/</text>
  <text x="115" y="82" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">classpath:/config/</text>
  <text x="115" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">file:./ &amp; file:./config/</text>
  <text x="115" y="114" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(searched in order)</text>

  <!-- spring.config.location replaces -->
  <rect x="20" y="145" width="190" height="70" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="115" y="168" fill="#f85149" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">spring.config.location</text>
  <text x="115" y="188" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">REPLACES the list above</text>
  <text x="115" y="204" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">e.g. file:/etc/myapp/</text>

  <!-- Arrow from default to merged -->
  <line x1="215" y1="70" x2="290" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ga)"/>

  <!-- spring.config.import adds -->
  <rect x="245" y="20" width="210" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="45" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">spring.config.import</text>
  <text x="350" y="66" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ADDS on top</text>
  <text x="350" y="82" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">file:/run/secrets/db.props</text>
  <text x="350" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">optional:file:/opt/shared.yml</text>

  <!-- Arrow from import to merged -->
  <line x1="350" y1="114" x2="350" y2="150" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#gb)"/>

  <!-- Merged Environment box -->
  <rect x="245" y="155" width="210" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="183" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Merged Environment</text>
  <text x="350" y="203" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">later sources win on conflict</text>

  <!-- Application box -->
  <rect x="490" y="145" width="160" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="175" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Application</text>
  <text x="570" y="195" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Value / @ConfigurationProperties</text>

  <!-- Arrow merged -> app -->
  <line x1="458" y1="190" x2="488" y2="190" stroke="#6db33f" stroke-width="1.5" marker-end="url(#gc)"/>

  <defs>
    <marker id="ga" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="gb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="gc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`spring.config.location` replaces the default search list; `spring.config.import` appends additional sources that are merged into the final Environment. Later-loaded values win on key conflicts.

## 5. Runnable example

```java
// File: ConfigImportDemo.java
// JDK 17+, Spring Boot on classpath — run as a Spring Boot app
// Setup: mvn spring-boot:run  OR  ./gradlew bootRun
//
// Create these files before running:
//   src/main/resources/application.properties  (base config)
//   /tmp/extra.properties                       (external secrets file)

// ---- src/main/resources/application.properties ----
// app.name=MyService
// app.version=1.0
// spring.config.import=optional:file:/tmp/extra.properties

// ---- /tmp/extra.properties ----
// app.db.url=jdbc:postgresql://localhost/mydb
// app.db.password=s3cr3t

package com.example;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ConfigImportDemo implements CommandLineRunner {

    @Value("${app.name}")
    private String appName;

    @Value("${app.version}")
    private String appVersion;

    // Comes from the imported /tmp/extra.properties
    @Value("${app.db.url:NOT_LOADED}")
    private String dbUrl;

    @Value("${app.db.password:NOT_LOADED}")
    private String dbPassword;

    public static void main(String[] args) {
        SpringApplication.run(ConfigImportDemo.class, args);
    }

    @Override
    public void run(String... args) {
        System.out.println("App     : " + appName + " v" + appVersion);
        System.out.println("DB URL  : " + dbUrl);
        System.out.println("DB Pass : " + dbPassword);
    }
}
```

**How to run:**
1. Create `src/main/resources/application.properties` and `/tmp/extra.properties` with the content shown in the comments.
2. Run `./gradlew bootRun` (or `mvn spring-boot:run`).
3. Delete `/tmp/extra.properties` and rerun — thanks to `optional:`, Boot starts fine and prints `NOT_LOADED` for the DB values.

## 6. Walkthrough

- **`spring.config.import=optional:file:/tmp/extra.properties`** (in `application.properties`) — tells Boot to load `/tmp/extra.properties` after the base config. The `optional:` prefix means "don't fail if the file is missing." Without `optional:`, a missing file throws `ConfigDataLocationNotFoundException` at startup.
- **`@Value("${app.db.url:NOT_LOADED}")`** — the `:NOT_LOADED` is a **default value** fallback. It activates when the property is absent (i.e., when the optional file is missing).
- **Override order** — if both `application.properties` and `extra.properties` define the same key (e.g., `app.name`), the imported file wins because it is processed later. This mirrors the general Spring Boot rule: later sources override earlier ones.
- **`spring.config.location`** — if you instead set `spring.config.location=file:/etc/myapp/` (e.g., via an env var `SPRING_CONFIG_LOCATION`), Boot would only look in `/etc/myapp/` and ignore `classpath:/`. Use this when you want full control over the search path, not just an addition.
- **Combining both** — a common production pattern: set `spring.config.location` to point at a directory your ops team owns, then inside that file use `spring.config.import` to pull in a secrets file. The two properties compose cleanly.

## 7. Gotchas & takeaways

> `spring.config.location` is **replacing**, not appending. If you set it and forget to include `classpath:/` in the list, Boot will not find your `application.properties` on the classpath — your entire base config silently disappears. Always append the default locations if you still want them: `spring.config.location=file:/etc/myapp/,classpath:/`.

> The `optional:` prefix is not just cosmetic — without it, every environment where the file is absent will fail to start. Add `optional:` to any import that is not guaranteed to exist in all deployment targets.

- `spring.config.import` was added in Spring Boot 2.4 and is the modern way to pull in extra sources; prefer it over older workarounds.
- The `file:` scheme resolves from the filesystem root. Relative paths (no scheme) resolve from the importing config file's location.
- You can pass `spring.config.location` as a command-line argument (`--spring.config.location=...`) or environment variable (`SPRING_CONFIG_LOCATION=...`) — Boot reads it before it starts processing any other properties.
- Multiple imports are comma-separated: `spring.config.import=file:/a.props,optional:file:/b.props`.
- Profiles still work with imported files: Boot will also look for `extra-prod.properties` alongside `extra.properties` when the `prod` profile is active.
