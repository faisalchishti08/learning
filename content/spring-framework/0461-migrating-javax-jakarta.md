---
card: spring-framework
gi: 461
slug: migrating-javax-jakarta
title: "Migrating javax → jakarta"
---

## 1. What it is

Starting with Spring Framework 6 (and Spring Boot 3), every API that used to live under the `javax.*` package namespace — `javax.servlet`, `javax.persistence`, `javax.validation`, `javax.annotation`, and more — moved to `jakarta.*` instead: `javax.servlet.http.HttpServletRequest` became `jakarta.servlet.http.HttpServletRequest`, `javax.persistence.Entity` became `jakarta.persistence.Entity`, and so on. This wasn't a Spring-specific decision; it followed the Jakarta EE project itself renaming its packages after Oracle transferred Java EE to the Eclipse Foundation and Oracle retained rights to the `javax` trademark, forcing the rename as a condition of continued development.

```java
// Before (Spring Framework 5.x, Java EE / javax)
import javax.servlet.http.HttpServletRequest;
import javax.persistence.Entity;
import javax.annotation.PostConstruct;

// After (Spring Framework 6.x, Jakarta EE / jakarta)
import jakarta.servlet.http.HttpServletRequest;
import jakarta.persistence.Entity;
import jakarta.annotation.PostConstruct;
```

## 2. Why & when

This matters to every Spring 6/Boot 3 codebase because it's a hard compatibility boundary, not a gradual deprecation: Spring Framework 6 dropped `javax.*` support entirely for these APIs, meaning code compiled against `javax.servlet.*` simply will not compile or run against Spring 6 without the import (and the corresponding dependency) being changed to `jakarta.servlet.*`. There's no compatibility shim inside Spring itself — the packages are genuinely different types at the JVM level, even though most of them are otherwise near-identical in API shape.

This affects you specifically when:

- You're upgrading an existing Spring Framework 5.x or Spring Boot 2.x application to Spring Framework 6.x / Spring Boot 3.x — this rename is very often the single largest mechanical change required, touching potentially every file that imports a Servlet, JPA, Bean Validation, or common-annotations type.
- You depend on a third-party library that hasn't yet migrated to `jakarta.*` — mixing a `javax`-based library with a `jakarta`-based Spring 6 application under the same servlet container will not work, since a `javax.servlet.Filter` and a `jakarta.servlet.Filter` are unrelated types to the container.
- You're deciding whether to adopt Spring Boot 3 for a new project — there's no reason to start on `javax.*` today, since Spring Boot 3 is the current major line, but understanding the split explains why some tutorials, Stack Overflow answers, and library documentation you find will look subtly wrong for a Spring 6 project.

## 3. Core concept

```
 Java EE (up to EE 8, under Oracle)              Jakarta EE (EE 9+, under Eclipse Foundation)
 ---------------------------------                ------------------------------------------
 javax.servlet.*                                   jakarta.servlet.*
 javax.persistence.*                                jakarta.persistence.*
 javax.validation.*                                 jakarta.validation.*
 javax.annotation.*  (a subset -- see gotcha)         jakarta.annotation.*

 Spring Framework 5.x / Boot 2.x                    Spring Framework 6.x / Boot 3.x
 targets javax.*, runs on Servlet 4 / EE 8            targets jakarta.*, runs on Servlet 5+ / EE 9+
        |                                                    |
        v                                                    v
  compiled bytecode references javax.servlet.Filter    compiled bytecode references jakarta.servlet.Filter
        |                                                    |
        +----------------- INCOMPATIBLE, NOT INTERCHANGEABLE -+
```

`javax.servlet.Filter` and `jakarta.servlet.Filter` are different classes with different fully-qualified names — a class implementing one does not implement the other, even though the method signatures inside them are usually identical.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring 5 targets javax packages, Spring 6 targets jakarta packages, and the two are not binary compatible">
  <rect x="10" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="150" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Framework 5.x / Boot 2.x</text>
  <text x="150" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">javax.servlet.*, javax.persistence.*</text>

  <rect x="350" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Framework 6.x / Boot 3.x</text>
  <text x="490" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">jakarta.servlet.*, jakarta.persistence.*</text>

  <line x1="290" y1="50" x2="345" y2="50" stroke="#79c0ff" stroke-width="2"/>
  <text x="320" y="42" fill="#79c0ff" font-size="16" text-anchor="middle" font-family="sans-serif">✗</text>
  <text x="320" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">not binary compatible -- must migrate imports + deps together</text>
</svg>

There is no shim: a Spring 6 application must use `jakarta.*` types throughout, including in every dependency it pulls in.

## 5. Runnable example

The scenario: a small servlet-style filter and a validated data class, first shown compiling against `jakarta.*` (the only option under Spring 6, since `javax.servlet`/`javax.validation` aren't on a Spring 6 classpath at all), then evolved to show the exact mechanical diff a real migration performs, then to a defensive check that fails fast if a `javax.*` type accidentally leaks back onto the classpath.

### Level 1 — Basic

Write a `jakarta.annotation.PostConstruct`-using bean the way it looks under Spring 6, and confirm it initializes correctly — establishing the "after" state before comparing it to the "before."

```java
import jakarta.annotation.PostConstruct;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

public class JakartaMigrationLevel1 {

    public static class StartupBanner {
        private String message;

        @PostConstruct
        void init() {
            message = "Application started (jakarta.annotation.PostConstruct)";
            System.out.println(message);
        }

        public String getMessage() { return message; }
    }

    @Configuration
    public static class AppConfig {
        @Bean public StartupBanner startupBanner() { return new StartupBanner(); }
    }

    public static void main(String[] args) {
        AnnotationConfigApplicationContext ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        StartupBanner banner = ctx.getBean(StartupBanner.class);
        System.out.println("retrieved message = " + banner.getMessage());

        if (!banner.getMessage().contains("jakarta.annotation"))
            throw new AssertionError("Expected @PostConstruct to have run via the jakarta package");
        System.out.println("jakarta.annotation.PostConstruct worked under Spring 6 -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context` (Spring Framework 6.x) and `jakarta.annotation-api` on the classpath, then `java JakartaMigrationLevel1.java` on JDK 17+.

`import jakarta.annotation.PostConstruct;` is the only option here — Spring Framework 6's `spring-context` doesn't process `javax.annotation.PostConstruct` at all, since that package doesn't exist on a Spring-6-compatible classpath. The bean initializes exactly as `@PostConstruct` always has; only the import statement's package changed from what it would have been under Spring 5.

### Level 2 — Intermediate

Simulate the actual migration mechanically: define the "before" (`javax`-shaped) code as a string, apply the same find-and-replace a real migration tool (like OpenRewrite's Jakarta EE migration recipe) would perform, and confirm the transformed source compiles and behaves identically to Level 1 — making the mechanical nature of the change concrete.

```java
import java.util.List;
import java.util.Map;

public class JakartaMigrationLevel2 {

    // The core package renames a real Spring 5 -> 6 migration must apply.
    static final Map<String, String> PACKAGE_RENAMES = Map.of(
        "javax.servlet.", "jakarta.servlet.",
        "javax.persistence.", "jakarta.persistence.",
        "javax.validation.", "jakarta.validation.",
        "javax.transaction.", "jakarta.transaction.",
        "javax.annotation.PostConstruct", "jakarta.annotation.PostConstruct",
        "javax.annotation.PreDestroy", "jakarta.annotation.PreDestroy",
        "javax.annotation.Resource", "jakarta.annotation.Resource"
    );

    static String migrateImports(String javaSource) {
        String migrated = javaSource;
        for (Map.Entry<String, String> rename : PACKAGE_RENAMES.entrySet()) {
            migrated = migrated.replace(rename.getKey(), rename.getValue());
        }
        return migrated;
    }

    public static void main(String[] args) {
        String beforeSource = """
            import javax.servlet.http.HttpServletRequest;
            import javax.persistence.Entity;
            import javax.persistence.Id;
            import javax.validation.constraints.NotNull;
            import javax.annotation.PostConstruct;

            @Entity
            public class Order {
                @Id private Long id;
                @NotNull private String item;
            }
            """;

        String afterSource = migrateImports(beforeSource);
        System.out.println("--- migrated source ---");
        System.out.println(afterSource);

        boolean noJavaxLeft = !afterSource.contains("javax.servlet")
            && !afterSource.contains("javax.persistence")
            && !afterSource.contains("javax.validation")
            && !afterSource.contains("javax.annotation");
        boolean allJakartaPresent = afterSource.contains("jakarta.servlet.http.HttpServletRequest")
            && afterSource.contains("jakarta.persistence.Entity")
            && afterSource.contains("jakarta.validation.constraints.NotNull")
            && afterSource.contains("jakarta.annotation.PostConstruct");

        if (!noJavaxLeft) throw new AssertionError("Migration left a javax.* import behind");
        if (!allJakartaPresent) throw new AssertionError("Migration did not produce all expected jakarta.* imports");
        System.out.println("Mechanical javax -> jakarta rename completed cleanly -- PASS");
    }
}
```

How to run: no external dependencies beyond the JDK, `java JakartaMigrationLevel2.java` on JDK 17+.

`PACKAGE_RENAMES` mirrors the actual set of prefix substitutions real migration tooling (OpenRewrite's `org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta` recipe, or Eclipse Transformer) applies across an entire codebase — this example runs the same substitution logic directly on a source string to make visible exactly what changes and what doesn't (`javax.sql.DataSource`, notably, does *not* rename — see the gotcha below, and this replacement map correctly omits it).

### Level 3 — Advanced

Add a build-time guard: scan a set of "dependency" class names for the codebase and fail loudly if any `javax.*` type from the migrated set is still present, simulating a CI check a real migration would add to prevent regressions — someone adding a new file that still imports the old package.

```java
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class JakartaMigrationLevel3 {

    static final Pattern MIGRATED_JAVAX_IMPORT = Pattern.compile(
        "^import\\s+(javax\\.(?:servlet|persistence|validation|transaction)\\..+|" +
        "javax\\.annotation\\.(?:PostConstruct|PreDestroy|Resource));\\s*$", Pattern.MULTILINE);

    record SourceFile(String name, String content) {}

    static List<String> findForbiddenImports(SourceFile file) {
        Matcher m = MIGRATED_JAVAX_IMPORT.matcher(file.content());
        return m.results().map(r -> file.name() + ": " + r.group().trim()).toList();
    }

    public static void main(String[] args) {
        List<SourceFile> codebase = List.of(
            new SourceFile("OrderController.java", """
                import jakarta.servlet.http.HttpServletRequest;
                public class OrderController {}
                """),
            new SourceFile("Order.java", """
                import jakarta.persistence.Entity;
                @Entity
                public class Order {}
                """),
            new SourceFile("LegacyFilter.java", """
                import javax.servlet.Filter;
                import javax.servlet.FilterChain;
                public class LegacyFilter implements Filter {}
                """) // deliberately un-migrated, to prove the check catches it
        );

        List<String> violations = codebase.stream()
            .flatMap(f -> findForbiddenImports(f).stream())
            .toList();

        System.out.println("scanned " + codebase.size() + " files");
        violations.forEach(v -> System.out.println("[FORBIDDEN] " + v));

        if (violations.isEmpty())
            throw new AssertionError("Expected the check to catch LegacyFilter.java's javax.servlet imports");
        if (violations.size() != 2)
            throw new AssertionError("Expected exactly 2 forbidden imports in LegacyFilter.java, found " + violations.size());

        System.out.println("CI-style guard correctly detected leftover javax.* imports -- PASS");
        System.out.println("(in a real CI pipeline, this would now exit non-zero to fail the build)");
    }
}
```

How to run: no external dependencies, `java JakartaMigrationLevel3.java` on JDK 17+.

`MIGRATED_JAVAX_IMPORT` matches only the specific `javax.*` subpackages that actually moved to `jakarta.*` (servlet, persistence, validation, transaction, and the three renamed `javax.annotation` types) — this precision matters, because a blanket "flag any `javax.*` import" check would produce false positives on packages like `javax.sql` or `javax.crypto` that never moved. `LegacyFilter.java` is deliberately left un-migrated to prove the scanner actually catches a real violation rather than trivially passing; a genuine CI job would call `System.exit(1)` when `violations` is non-empty instead of just printing.

## 6. Walkthrough

Trace Level 3's scan end-to-end.

1. **Codebase setup**: three `SourceFile` records represent a snapshot of a project mid-migration — two files already updated to `jakarta.*`, one (`LegacyFilter.java`) still using `javax.servlet.*`, simulating a file someone forgot to migrate or a newly-added file that copied an old pattern.
2. **Pattern definition**: `MIGRATED_JAVAX_IMPORT` is a regex anchored to line starts (`^import ...;$` with `MULTILINE`) matching exactly the `javax` subpackages known to have moved — deliberately narrow, not a blanket `javax\..*` match, to avoid flagging legitimately-still-`javax` packages.
3. **Per-file scan**: `findForbiddenImports` runs the pattern against each file's content via `Matcher.results()` (a stream of all non-overlapping matches), prefixing each hit with the file name for a useful error message.
4. **Aggregation**: `codebase.stream().flatMap(...)` runs the scan across all three files and flattens the per-file violation lists into one combined list.
5. **`OrderController.java` and `Order.java`** produce zero matches each — their `jakarta.*` imports don't match a pattern that only looks for `javax.*`.
6. **`LegacyFilter.java`** produces two matches — its `import javax.servlet.Filter;` and `import javax.servlet.FilterChain;` lines both match the `javax\.servlet\..+` branch of the pattern.
7. **Reporting**: the program prints how many files were scanned, lists every forbidden import found (in a real CI job, formatted as an actionable error pointing at the exact file and line), then asserts the violation count matches expectations before declaring the check itself correct.

```
 scan OrderController.java  -> 0 matches (already jakarta.*)
 scan Order.java            -> 0 matches (already jakarta.*)
 scan LegacyFilter.java     -> 2 matches: javax.servlet.Filter, javax.servlet.FilterChain
                                    |
                                    v
                          CI check FAILS the build (non-empty violations)
```

## 7. Gotchas & takeaways

> **Gotcha:** not every `javax.*` package moved to `jakarta.*` — only the ones owned by the Jakarta EE specification project did (`servlet`, `persistence`, `validation`, `transaction`, `websocket`, `mail`, and a handful of `javax.annotation` types like `PostConstruct`/`PreDestroy`/`Resource`). Core JDK packages like `javax.sql.DataSource`, `javax.crypto.*`, and `javax.net.ssl.*` are part of the Java SE standard library itself, not Jakarta EE, and were never renamed — a blind find-and-replace of `javax.` → `jakarta.` across a codebase will break these imports rather than fix them.

- The `javax` → `jakarta` rename is a binary compatibility break, not a deprecation — there is no dual-support window inside Spring Framework 6 itself; every dependency in the classpath must agree on which namespace it uses for a given API.
- Automated migration tooling exists specifically because this is a mechanical, codebase-wide change — OpenRewrite's Spring Boot 3 migration recipe and the Eclipse Transformer project both exist to avoid doing this rename by hand across a large codebase.
- When a build fails after upgrading to Spring Boot 3 with errors like `NoClassDefFoundError: javax/servlet/...`, the near-certain cause is a dependency (often a servlet container, a library, or hand-written code) that still targets `javax.*` and hasn't been upgraded to a `jakarta.*`-compatible version.
- This rename is a one-time, well-documented step in the broader "upgrading to Spring 6.x" process — see the next card for the fuller checklist it fits into.
