---
card: spring-framework
gi: 142
slug: resourcepatternresolver-classpath
title: "ResourcePatternResolver (classpath*:)"
---

## 1. What it is

`ResourcePatternResolver` extends `ResourceLoader` with `getResources(String locationPattern)` — it accepts Ant-style wildcard patterns (`*`, `**`, `?`) and returns all matching `Resource` objects. The `classpath*:` prefix is the special form that searches ALL classpath entries (every JAR, every directory) rather than just the first match.

```java
// All .sql files anywhere under db/ on the classpath
Resource[] scripts = resolver.getResources("classpath*:db/**/*.sql");
```

## 2. Why & when

- **Multi-JAR scanning** — find all `META-INF/spring.factories`, all Hibernate mapping files, or all SQL migration scripts spread across multiple JARs.
- **Modular architecture** — each module JAR contributes its own resources (config files, SQL, XML) discoverable via one wildcard pattern.
- **Plugin systems** — discover contributed resources without compile-time coupling.
- **`classpath:` vs `classpath*:`** — `classpath:` returns the FIRST match on the classpath; `classpath*:` returns ALL matches across ALL classpath entries. This distinction is critical when resources appear in multiple JARs.

## 3. Core concept

Ant-style path patterns:

| Pattern | Matches |
|---|---|
| `db/*.sql` | All `.sql` files directly in `db/` |
| `db/**/*.sql` | All `.sql` files anywhere under `db/` |
| `**/schema.sql` | `schema.sql` at any depth |
| `db/migration-?.sql` | Single character wildcard |

`classpath:` vs `classpath*:`:

| Prefix | Behavior |
|---|---|
| `classpath:config/*.xml` | First classpath root only; wildcards within path ok |
| `classpath*:config/*.xml` | ALL classpath roots (all JARs + directories) |

`PathMatchingResourcePatternResolver` is the standard implementation:

1. For non-wildcard paths: delegates to `ResourceLoader.getResource()`.
2. For wildcard paths: enumerates classpath entries (via `ClassLoader.getResources()`), lists files in each directory, and matches names with `AntPathMatcher`.

`ApplicationContext` implements `ResourcePatternResolver` — inject it or use `ctx.getResources(pattern)` directly.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- Interface hierarchy -->
  <rect x="10" y="20"  width="165" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="92" y="39"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;&lt;ResourceLoader&gt;&gt;</text>

  <rect x="10" y="65"  width="165" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="92" y="81"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;&lt;ResourcePatternResolver&gt;&gt;</text>
  <text x="92" y="93"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getResources(pattern)</text>

  <rect x="10" y="115" width="165" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="92" y="131" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">PathMatchingResourcePattern</text>
  <text x="92" y="143" fill="#79c0ff" font-size="9"  text-anchor="middle" font-family="sans-serif">Resolver (standard impl)</text>

  <defs>
    <marker id="a142" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b142" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <line x1="92" y1="50" x2="92" y2="62" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a142)"/>
  <line x1="92" y1="102" x2="92" y2="112" stroke="#6db33f" stroke-width="1.5" marker-end="url(#b142)"/>

  <!-- classpath* explanation -->
  <rect x="235" y="20"  width="200" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="335" y="40"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">classpath*:db/**/*.sql</text>
  <text x="335" y="57"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">ALL JARs + dirs on classpath</text>

  <rect x="235" y="85"  width="200" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="105" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">classpath:db/**/*.sql</text>
  <text x="335" y="122" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">first classpath root only</text>

  <!-- Resources output -->
  <rect x="492" y="40"  width="200" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="592" y="58"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Resource[] — all matches</text>

  <line x1="437" y1="45"  x2="489" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a142)"/>
  <line x1="437" y1="110" x2="489" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b142)"/>

  <text x="350" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">classpath*: searches all JARs; classpath: stops at first match</text>
</svg>

`classpath*:` with Ant-style wildcards discovers resources across all JARs; `classpath:` stops at the first classpath root.

## 5. Runnable example

### Level 1 — Basic

Find all `.properties` files matching a wildcard on the classpath.

```java
// PatternResolverBasic.java
import org.springframework.core.io.*;
import org.springframework.core.io.support.*;
import java.io.*;
import java.nio.file.*;

public class PatternResolverBasic {
    public static void main(String[] args) throws Exception {
        // Create several config files in different classpath directories
        Files.createDirectories(Path.of("cfg"));
        Files.writeString(Path.of("cfg/dev.properties"),  "env=dev\nport=8080\n");
        Files.writeString(Path.of("cfg/prod.properties"), "env=prod\nport=443\n");
        Files.writeString(Path.of("cfg/test.properties"), "env=test\nport=9090\n");
        Files.writeString(Path.of("cfg/info.txt"), "not a properties file");

        var resolver = new PathMatchingResourcePatternResolver();

        // Match all .properties files under cfg/
        Resource[] resources = resolver.getResources("classpath:cfg/*.properties");
        System.out.println("Found " + resources.length + " .properties files:");
        for (Resource r : resources) {
            System.out.println("  " + r.getFilename() + " (" + r.contentLength() + " bytes)");
        }

        System.out.println();

        // Match any file containing "p" in the name
        Resource[] pResources = resolver.getResources("classpath:cfg/*p*.properties");
        System.out.println("Files matching *p*.properties:");
        for (Resource r : pResources) {
            System.out.println("  " + r.getFilename());
        }

        Files.deleteIfExists(Path.of("cfg/dev.properties"));
        Files.deleteIfExists(Path.of("cfg/prod.properties"));
        Files.deleteIfExists(Path.of("cfg/test.properties"));
        Files.deleteIfExists(Path.of("cfg/info.txt"));
        Files.deleteIfExists(Path.of("cfg"));
    }
}
```

How to run: `java PatternResolverBasic.java`

`classpath:cfg/*.properties` matches all `.properties` files directly inside `cfg/`. The `.txt` file is excluded. `*p*.properties` further filters to filenames containing `"p"`.

### Level 2 — Intermediate

`**` deep wildcard; load and merge all matched properties files; sort by filename.

```java
// PatternResolverDeep.java
import org.springframework.core.io.*;
import org.springframework.core.io.support.*;
import java.nio.file.*;
import java.util.*;

public class PatternResolverDeep {
    public static void main(String[] args) throws Exception {
        // Create a nested directory structure
        for (String dir : new String[]{"migrations/v1", "migrations/v2", "migrations/v3"}) {
            Files.createDirectories(Path.of(dir));
        }
        Files.writeString(Path.of("migrations/v1/001-create-tables.sql"),
            "CREATE TABLE users (id INT, name VARCHAR(100));\n");
        Files.writeString(Path.of("migrations/v1/002-add-index.sql"),
            "CREATE INDEX idx_users_name ON users(name);\n");
        Files.writeString(Path.of("migrations/v2/003-add-email.sql"),
            "ALTER TABLE users ADD COLUMN email VARCHAR(200);\n");
        Files.writeString(Path.of("migrations/v3/004-add-audit.sql"),
            "ALTER TABLE users ADD COLUMN created_at TIMESTAMP;\n");

        var resolver = new PathMatchingResourcePatternResolver();

        // Deep wildcard — all .sql files anywhere under migrations/
        Resource[] scripts = resolver.getResources("classpath:migrations/**/*.sql");

        // Sort by filename to ensure migration order
        Arrays.sort(scripts, Comparator.comparing(Resource::getFilename));

        System.out.println("SQL migration scripts (sorted):");
        for (Resource r : scripts) {
            System.out.println("  " + r.getFilename());
            System.out.println("    " + new String(r.getInputStream().readAllBytes()).trim());
        }

        // Total SQL length
        long totalBytes = Arrays.stream(scripts).mapToLong(r -> {
            try { return r.contentLength(); } catch (Exception e) { return 0; }
        }).sum();
        System.out.println("\nTotal migration SQL: " + totalBytes + " bytes");

        // Cleanup
        for (String f : new String[]{
            "migrations/v1/001-create-tables.sql", "migrations/v1/002-add-index.sql",
            "migrations/v2/003-add-email.sql", "migrations/v3/004-add-audit.sql"}) {
            Files.deleteIfExists(Path.of(f));
        }
        for (String d : new String[]{"migrations/v1","migrations/v2","migrations/v3","migrations"}) {
            Files.deleteIfExists(Path.of(d));
        }
    }
}
```

How to run: `java PatternResolverDeep.java`

`classpath:migrations/**/*.sql` recursively finds all `.sql` files. Sorting by filename enforces migration order. `contentLength()` gives byte counts for all matched resources.

### Level 3 — Advanced

`classpath*:` across multiple source roots; `ApplicationContext` as `ResourcePatternResolver`; collect unique resources from all matching JARs.

```java
// PatternResolverClasspathStar.java
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import org.springframework.core.io.support.*;
import java.nio.file.*;
import java.util.*;

public class PatternResolverClasspathStar {
    public static void main(String[] args) throws Exception {
        // Simulate two "module" directories, each contributing their own config
        for (String dir : new String[]{"module-a/META-INF", "module-b/META-INF"}) {
            Files.createDirectories(Path.of(dir));
        }
        Files.writeString(Path.of("module-a/META-INF/module.factories"),
            "processors=com.acme.module.a.Processor\n");
        Files.writeString(Path.of("module-b/META-INF/module.factories"),
            "processors=com.acme.module.b.Processor\n");
        // Also a factories file at the root level
        Files.createDirectories(Path.of("META-INF"));
        Files.writeString(Path.of("META-INF/module.factories"),
            "processors=com.acme.core.Processor\n");

        var resolver = new PathMatchingResourcePatternResolver();

        System.out.println("=== classpath: (first match only) ===");
        Resource[] single = resolver.getResources("classpath:META-INF/module.factories");
        System.out.println("Found: " + single.length);
        for (Resource r : single) System.out.println("  " + r.getURI());

        System.out.println("\n=== classpath*: (all matches) ===");
        Resource[] all = resolver.getResources("classpath*:META-INF/module.factories");
        System.out.println("Found: " + all.length);
        var processors = new ArrayList<String>();
        for (Resource r : all) {
            System.out.println("  " + r.getURI());
            var props = new java.util.Properties();
            props.load(r.getInputStream());
            processors.add(props.getProperty("processors"));
        }
        System.out.println("\nAll processors:");
        processors.forEach(p -> System.out.println("  " + p));

        // ApplicationContext also implements ResourcePatternResolver
        System.out.println("\n=== Via ApplicationContext ===");
        var ctx = new AnnotationConfigApplicationContext();
        ctx.register(Object.class);
        ctx.refresh();

        ResourcePatternResolver ctxResolver = (ResourcePatternResolver) ctx;
        Resource[] ctxAll = ctxResolver.getResources("classpath*:META-INF/module.factories");
        System.out.println("ApplicationContext found: " + ctxAll.length);

        ctx.close();

        // Cleanup
        Files.deleteIfExists(Path.of("module-a/META-INF/module.factories"));
        Files.deleteIfExists(Path.of("module-b/META-INF/module.factories"));
        Files.deleteIfExists(Path.of("META-INF/module.factories"));
        for (String d : new String[]{"module-a/META-INF","module-a","module-b/META-INF","module-b","META-INF"}) {
            Files.deleteIfExists(Path.of(d));
        }
    }
}
```

How to run: `java PatternResolverClasspathStar.java`

`classpath:META-INF/module.factories` returns only one file (the first match). `classpath*:META-INF/module.factories` returns all matches across all classpath entries. `ApplicationContext` implements `ResourcePatternResolver` and casts cleanly.

## 6. Walkthrough

Execution for Level 3 `classpath*:`:

1. **`resolver.getResources("classpath*:META-INF/module.factories")`** — `classpath*:` triggers `ClassLoader.getResources("META-INF/module.factories")` which enumerates all classpath entries.
2. Each entry where `META-INF/module.factories` exists produces a `URL`.
3. Each `URL` is wrapped in a `UrlResource` (or `FileSystemResource`).
4. Result: three `Resource` objects — one from the root `META-INF/`, one from `module-a/META-INF/`, one from `module-b/META-INF/`.
5. Each is loaded and the `processors` property collected.

## 7. Gotchas & takeaways

> `classpath*:` without a wildcard in the path DOES work for finding resources across multiple JARs — e.g., `classpath*:META-INF/module.factories` finds all occurrences. However, `classpath*:` combined with `**` wildcards inside a JAR may miss entries — `ClassLoader.getResources()` only lists directories, not all files inside a JAR. Always use the most specific pattern possible when scanning JARs.

> `PathMatchingResourcePatternResolver` requires a directory listing to resolve wildcards within a JAR. If the JAR doesn't include directory entries, wildcard scanning silently returns 0 results. Plain file: filesystem paths always work.

- Resource order returned by `getResources()` is not guaranteed — sort explicitly when order matters (e.g., SQL migrations, config loading priority).
- `classpath:` with a wildcard (`classpath:db/**/*.sql`) scans only the first classpath directory found — NOT all JARs. Use `classpath*:` when resources span multiple JARs.
- `ApplicationContext` implements `ResourcePatternResolver` so `ctx.getResources(pattern)` works without creating a separate `PathMatchingResourcePatternResolver`.
- Scanning is done at startup; for hot-reload scenarios, hold the `PathMatchingResourcePatternResolver` and call `getResources()` again when needed.
