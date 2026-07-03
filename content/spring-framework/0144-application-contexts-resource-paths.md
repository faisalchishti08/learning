---
card: spring-framework
gi: 144
slug: application-contexts-resource-paths
title: "Application contexts & resource paths"
---

## 1. What it is

Each `ApplicationContext` subclass interprets path strings without a prefix differently — the prefix-less resolution strategy is context-specific. When you pass a resource location to a context constructor or `getResource()` without a prefix, the context decides whether to treat it as a classpath path, a filesystem path, or a URL.

```java
// ClassPathXmlApplicationContext: no-prefix → classpath
var ctx1 = new ClassPathXmlApplicationContext("config/app.xml");

// FileSystemXmlApplicationContext: no-prefix → filesystem
var ctx2 = new FileSystemXmlApplicationContext("config/app.xml");

// AnnotationConfigApplicationContext: no-prefix → ClassPathResource
var ctx3 = new AnnotationConfigApplicationContext();
Resource r = ctx3.getResource("config/app.xml");  // ClassPathResource
```

## 2. Why & when

Understanding context-specific path resolution is essential when:

- A path that works in unit tests (loaded from filesystem) fails in production (inside a JAR).
- You're migrating from XML-based to annotation-based contexts and resource loading behavior changes.
- You use wildcard patterns in `ClassPathXmlApplicationContext` constructors.
- You need to load a resource at a predictable location regardless of context type — use explicit prefixes.

The rule: **always use explicit prefixes (`classpath:`, `file:`, `http:`) in code that must work across different context types.**

## 3. Core concept

Context resolution strategy for paths without a prefix:

| `ApplicationContext` subclass | No-prefix path resolves to |
|---|---|
| `ClassPathXmlApplicationContext` | `ClassPathResource` |
| `ClassPathXmlApplicationContext` (array) | Relative to current class location |
| `FileSystemXmlApplicationContext` | `FileSystemResource` (working directory) |
| `AnnotationConfigApplicationContext` | `ClassPathResource` (via `DefaultResourceLoader`) |
| `AnnotationConfigWebApplicationContext` | `ServletContextResource` |
| `GenericApplicationContext` | `ClassPathResource` (via `DefaultResourceLoader`) |

Explicit prefix always overrides context default:

```
classpath:path/to/file  → ClassPathResource  (always)
file:path/to/file       → FileSystemResource (always)
http://host/path        → UrlResource        (always)
/path/from/root         → FileSystemResource (absolute filesystem path)
```

The context's own default strategy only applies when no prefix is present.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Context types -->
  <rect x="10" y="20"  width="220" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="39"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ClassPathXmlApplicationContext</text>

  <rect x="10" y="57"  width="220" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="76"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">FileSystemXmlApplicationContext</text>

  <rect x="10" y="94"  width="220" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="113" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">AnnotationConfigApplicationContext</text>

  <rect x="10" y="131" width="220" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">WebApplicationContext subtypes</text>

  <!-- No-prefix resolution -->
  <rect x="295" y="20"  width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="385" y="39"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">→ ClassPathResource</text>

  <rect x="295" y="57"  width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="385" y="76"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">→ FileSystemResource</text>

  <rect x="295" y="94"  width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="385" y="113" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">→ ClassPathResource</text>

  <rect x="295" y="131" width="180" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="385" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">→ ServletContextResource</text>

  <defs>
    <marker id="a144" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="232" y1="35"  x2="292" y2="35"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a144)"/>
  <line x1="232" y1="72"  x2="292" y2="72"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a144)"/>
  <line x1="232" y1="109" x2="292" y2="109" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a144)"/>
  <line x1="232" y1="146" x2="292" y2="146" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a144)"/>

  <text x="350" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Always use explicit prefixes (classpath:/file:) for context-independent resource loading</text>
</svg>

No-prefix resource paths resolve differently per context type; explicit prefixes always override the default strategy.

## 5. Runnable example

### Level 1 — Basic

`AnnotationConfigApplicationContext` vs `DefaultResourceLoader` for no-prefix path resolution.

```java
// ContextResourcePathBasic.java
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import java.nio.file.*;

public class ContextResourcePathBasic {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("ctx-test.txt"), "context resource path test");

        var ctx = new AnnotationConfigApplicationContext();
        ctx.register(Object.class);
        ctx.refresh();

        // AnnotationConfigApplicationContext: no-prefix → ClassPathResource
        Resource noPrefix = ctx.getResource("ctx-test.txt");
        System.out.println("no-prefix:");
        System.out.println("  type: " + noPrefix.getClass().getSimpleName());
        System.out.println("  exists: " + noPrefix.exists());

        // Explicit classpath: prefix — same result here since WD is on classpath
        Resource withPrefix = ctx.getResource("classpath:ctx-test.txt");
        System.out.println("classpath:");
        System.out.println("  type: " + withPrefix.getClass().getSimpleName());
        System.out.println("  exists: " + withPrefix.exists());

        // Explicit file: prefix — FileSystemResource regardless of context type
        Resource fileRes = ctx.getResource("file:" + Path.of("ctx-test.txt").toAbsolutePath());
        System.out.println("file:");
        System.out.println("  type: " + fileRes.getClass().getSimpleName());
        System.out.println("  exists: " + fileRes.exists());
        System.out.println("  content: " +
            new String(fileRes.getInputStream().readAllBytes()));

        ctx.close();
        Files.deleteIfExists(Path.of("ctx-test.txt"));
    }
}
```

How to run: `java ContextResourcePathBasic.java`

No-prefix in `AnnotationConfigApplicationContext` defaults to `ClassPathResource`. `"file:..."` always produces `FileSystemResource` regardless of context type.

### Level 2 — Intermediate

Contrast `ClassPathXmlApplicationContext` (classpath-default) with `GenericApplicationContext` (also classpath-default via `DefaultResourceLoader`); demonstrate constructor vs `getResource`.

```java
// ContextResourcePathContrast.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.support.*;
import org.springframework.core.io.*;
import java.nio.file.*;

public class ContextResourcePathContrast {
    static void probe(ApplicationContext ctx, String location) {
        Resource r = ctx.getResource(location);
        System.out.printf("  getResource(%-45s) → [%s]%n",
            "\"" + location + "\")", r.getClass().getSimpleName());
    }

    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("path-test.txt"), "test");

        // GenericApplicationContext (annotation-based, no XML)
        var generic = new GenericApplicationContext();
        generic.refresh();

        System.out.println("=== GenericApplicationContext ===");
        probe(generic, "path-test.txt");                       // ClassPathResource
        probe(generic, "classpath:path-test.txt");             // ClassPathResource (explicit)
        probe(generic, "file:path-test.txt");                  // FileSystemResource (explicit)
        generic.close();

        // AnnotationConfigApplicationContext (most common modern context)
        var annot = new AnnotationConfigApplicationContext();
        annot.register(Object.class);
        annot.refresh();

        System.out.println("\n=== AnnotationConfigApplicationContext ===");
        probe(annot, "path-test.txt");
        probe(annot, "classpath:path-test.txt");
        probe(annot, "file:path-test.txt");
        annot.close();

        // Both behave identically — both extend AbstractApplicationContext → DefaultResourceLoader
        System.out.println("\n(both use DefaultResourceLoader: no-prefix → ClassPathResource)");

        Files.deleteIfExists(Path.of("path-test.txt"));
    }
}
```

How to run: `java ContextResourcePathContrast.java`

Both `GenericApplicationContext` and `AnnotationConfigApplicationContext` inherit `DefaultResourceLoader` behavior: no-prefix → `ClassPathResource`. This is the modern Spring default.

### Level 3 — Advanced

Dynamic context selection based on a location prefix; resource loading across child contexts; demonstrate that prefix always wins.

```java
// ContextResourcePathAdvanced.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import java.nio.file.*;
import java.util.*;

public class ContextResourcePathAdvanced {

    // A service that accepts a configurable resource location
    static class ConfigurableService {
        private final String content;
        ConfigurableService(Resource resource) throws Exception {
            this.content = resource.exists()
                ? new String(resource.getInputStream().readAllBytes()).trim()
                : "(not found: " + resource.getDescription() + ")";
        }
        void show() { System.out.println("  content: " + content); }
    }

    public static void main(String[] args) throws Exception {
        // Setup files
        Files.writeString(Path.of("file-config.txt"),    "from filesystem");
        Files.writeString(Path.of("classpath-cfg.txt"),  "from classpath");

        var ctx = new AnnotationConfigApplicationContext();
        ctx.register(Object.class);
        ctx.refresh();

        // Demonstrate that explicit prefix always determines Resource type
        var testCases = Map.of(
            "file:" + Path.of("file-config.txt").toAbsolutePath(), "file: prefix",
            "classpath:classpath-cfg.txt",                         "classpath: prefix",
            "classpath-cfg.txt",                                   "no prefix (→ classpath)"
        );

        for (var entry : testCases.entrySet()) {
            Resource r = ctx.getResource(entry.getKey());
            System.out.printf("%-55s [%s] exists=%b%n",
                entry.getValue() + ":", r.getClass().getSimpleName(), r.exists());
        }

        // Child context inherits resource loading from parent
        var childCtx = new AnnotationConfigApplicationContext();
        childCtx.setParent(ctx);
        childCtx.register(Object.class);
        childCtx.refresh();

        System.out.println("\nChild context getResource:");
        Resource fromChild = childCtx.getResource("classpath:classpath-cfg.txt");
        System.out.println("  " + fromChild.getClass().getSimpleName() +
            " exists=" + fromChild.exists());
        System.out.println("  content: " +
            new String(fromChild.getInputStream().readAllBytes()));

        // ConfigurableService accepting different resource types
        System.out.println("\nConfigurableService with different sources:");

        var svcFile = new ConfigurableService(
            ctx.getResource("file:" + Path.of("file-config.txt").toAbsolutePath()));
        System.out.print("  file: source  →");
        svcFile.show();

        var svcCp = new ConfigurableService(
            ctx.getResource("classpath:classpath-cfg.txt"));
        System.out.print("  classpath: source →");
        svcCp.show();

        var svcMem = new ConfigurableService(
            new ByteArrayResource("in-memory data".getBytes()));
        System.out.print("  ByteArrayResource →");
        svcMem.show();

        childCtx.close();
        ctx.close();
        Files.deleteIfExists(Path.of("file-config.txt"));
        Files.deleteIfExists(Path.of("classpath-cfg.txt"));
    }
}
```

How to run: `java ContextResourcePathAdvanced.java`

Explicit prefixes pin the `Resource` type regardless of context. A child context inherits the parent's `ResourceLoader` strategy. `ConfigurableService` demonstrates the open/closed principle: the same service works with filesystem files, classpath entries, or in-memory data.

## 6. Walkthrough

Execution for Level 3 child context:

1. **`childCtx.setParent(ctx)`** — child context is wired to parent.
2. **`childCtx.getResource("classpath:classpath-cfg.txt")`** — child inherits `DefaultResourceLoader` behavior.
3. **`ClassPathResource("classpath-cfg.txt")`** created.
4. **`exists()`** → `true` (file in working directory = classpath root).
5. **`getInputStream()`** → reads `"from classpath"`.

## 7. Gotchas & takeaways

> **The most common mistake**: passing a no-prefix path to `FileSystemXmlApplicationContext` and expecting classpath resolution, then wondering why the same path fails when the app is packaged as a JAR. The solution: always use `classpath:` prefix in production configs that ship inside JARs.

> `ctx.getResource("config/app.yml")` behaves differently in `FileSystemXmlApplicationContext` (resolves to working directory filesystem) versus `AnnotationConfigApplicationContext` (resolves to classpath). This is a subtle behavior change when migrating XML contexts to annotation-based ones.

- Always use explicit prefixes (`classpath:` / `file:`) in `@PropertySource`, `@Value`, and any resource string that might run under different context types.
- `/absolute/path` (starting with `/`) resolves to `FileSystemResource` for absolute filesystem paths — but only in contexts where the `DefaultResourceLoader` is not the base; prefer `file:` prefix for clarity.
- Spring Boot's `SpringApplication` always uses `AnnotationConfigApplicationContext` (or `AnnotationConfigServletWebApplicationContext`) — so in Boot apps, no-prefix defaults to `ClassPathResource`.
- When writing library code, never assume no-prefix context behavior — your library might be used in multiple context types. Accept `Resource` directly or require explicit prefixes.
