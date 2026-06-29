---
card: spring-framework
gi: 5
slug: jakarta-ee-baseline-jakarta-namespace-migration-from-javax
title: Jakarta EE baseline (jakarta.* namespace migration from javax.*)
---

## 1. What it is

In 2017, Oracle transferred Java EE to the Eclipse Foundation, which renamed it **Jakarta EE**. As part of that transfer, Eclipse was not allowed to use the `javax.*` package namespace going forward. Starting with **Jakarta EE 9** (2020), every affected package was renamed from `javax.*` to `jakarta.*`.

Examples:

| Old (Java EE / Jakarta EE 8) | New (Jakarta EE 9+) |
|---|---|
| `javax.servlet.http.HttpServlet` | `jakarta.servlet.http.HttpServlet` |
| `javax.persistence.EntityManager` | `jakarta.persistence.EntityManager` |
| `javax.validation.Valid` | `jakarta.validation.Valid` |
| `javax.annotation.PostConstruct` | `jakarta.annotation.PostConstruct` |
| `javax.transaction.Transactional` | `jakarta.transaction.Transactional` |
| `javax.inject.Inject` | `jakarta.inject.Inject` |

**Spring Framework 6.0** (November 2022) made Jakarta EE 9+ the minimum baseline, removing all support for the old `javax.*` namespace. Spring Boot 3.x is built on Framework 6.x and therefore also requires Jakarta EE 9+.

## 2. Why & when

The namespace split is a hard breaking change. Code written against Spring 5.x / Spring Boot 2.x imports `javax.*` classes; that code does not compile against Spring 6.x / Spring Boot 3.x dependencies because the `javax.*` packages no longer exist in Jakarta EE 9+ JARs.

You must handle this when:
- Upgrading a Spring Boot 2.x application to Spring Boot 3.x.
- Adding a Spring Framework 6.x dependency to any project.
- Consuming a third-party library that still uses `javax.*` in a Spring 6.x project — the library must have a Jakarta-compatible release.

Not affected: packages that were never part of Java EE — `javax.swing`, `javax.crypto`, `java.util`, etc. stay as-is. Only the Jakarta EE APIs (servlet, persistence, validation, annotation, transaction, inject, mail, json, soap, XML bind, etc.) changed.

## 3. Core concept

The migration is mechanical but affects every source file that uses a Jakarta EE API. The rename pattern is always:

```
javax.<spec>.<Class>  →  jakarta.<spec>.<Class>
```

Tools available:
- **`spring-boot-properties-migrator`** flags property renames but not import renames.
- **OpenRewrite** (recipe `org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta`) rewrites all `javax.*` imports to `jakarta.*` automatically across the codebase.
- **IntelliJ IDEA** has a "Migrate packages and classes" refactor under Refactor → Migrate.

After the rename, dependencies must also change. Jakarta EE 9+ artifacts have different Maven coordinates:

| Technology | Old (javax) coordinate | New (jakarta) coordinate |
|---|---|---|
| Servlet | `javax.servlet:javax.servlet-api` | `jakarta.servlet:jakarta.servlet-api` |
| JPA | `javax.persistence:javax.persistence-api` | `jakarta.persistence:jakarta.persistence-api` |
| Bean Validation | `javax.validation:validation-api` | `jakarta.validation:jakarta.validation-api` |

Implementations also changed: Hibernate ORM 6.x supports `jakarta.persistence.*`; earlier Hibernate only supports `javax.persistence.*`.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Split between javax namespace for Java EE and Spring 5 versus jakarta namespace for Jakarta EE 9+ and Spring 6">
  <defs>
    <marker id="ja" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker>
    <marker id="jga" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Timeline bar -->
  <line x1="30" y1="120" x2="670" y2="120" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Left: javax era -->
  <rect x="10" y="40" width="280" height="65" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="63" fill="#f0883e" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Java EE / Jakarta EE ≤8</text>
  <text x="150" y="81" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">javax.servlet.*  javax.persistence.*</text>
  <text x="150" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Framework ≤5.x / Boot ≤2.x</text>

  <!-- Split point -->
  <line x1="350" y1="30" x2="350" y2="215" stroke="#6db33f" stroke-width="2" stroke-dasharray="6,3"/>
  <text x="350" y="22" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Jakarta EE 9 (2020)</text>
  <text x="350" y="210" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Spring 6 / Boot 3 baseline</text>

  <!-- Right: jakarta era -->
  <rect x="410" y="40" width="280" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="63" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Jakarta EE 9+</text>
  <text x="550" y="81" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">jakarta.servlet.*  jakarta.persistence.*</text>
  <text x="550" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Framework 6.x / Boot 3.x</text>

  <!-- Year labels -->
  <text x="80"  y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">~2003–2019</text>
  <text x="540" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2020 → present</text>

  <!-- Note -->
  <rect x="120" y="158" width="460" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="173" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">NOT affected: javax.crypto, javax.swing, java.*, all standard JDK packages</text>
  <text x="350" y="187" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Only Jakarta EE specification APIs changed namespace</text>
</svg>

The split is at Jakarta EE 9. Spring 6 / Boot 3 require the right side; Spring 5 / Boot 2 used the left.

## 5. Runnable example

We'll write a simple filter/validator that works in both namespaces — then progressively add the migration steps.

### Level 1 — Basic

A plain request filter showing both old and new import styles side by side, so you can see exactly what changes.

```java
// JakartaMigrationDemo.java — run with: java JakartaMigrationDemo.java
// Shows the import rename pattern without requiring a servlet container.

public class JakartaMigrationDemo {

    // --- Simulating javax.servlet style (Spring Boot 2.x / Spring 5.x) ---
    // In a real Boot 2 app:
    //   import javax.servlet.http.HttpServletRequest;
    //   import javax.servlet.Filter;
    //   import javax.persistence.Entity;
    //   import javax.validation.constraints.NotNull;

    // --- Simulating jakarta.servlet style (Spring Boot 3.x / Spring 6.x) ---
    // In a real Boot 3 app:
    //   import jakarta.servlet.http.HttpServletRequest;
    //   import jakarta.servlet.Filter;
    //   import jakarta.persistence.Entity;
    //   import jakarta.validation.constraints.NotNull;

    // Self-contained domain — no server imports needed to demonstrate the concept
    record OrderRequest(int id, String customer, double amount) {
        void validate() {
            // @NotNull → jakarta.validation.constraints.NotNull in Boot 3
            if (customer == null || customer.isBlank())
                throw new IllegalArgumentException("customer must not be null (jakarta.validation.@NotNull)");
            if (amount <= 0)
                throw new IllegalArgumentException("amount must be positive (jakarta.validation.@Positive)");
        }
    }

    // Simulated @Entity (JPA) — shows the field annotation rename
    static class OrderEntity {
        // Boot 2:  @javax.persistence.Id
        // Boot 3:  @jakarta.persistence.Id
        int id;
        String customer;
        double amount;

        OrderEntity(int id, String customer, double amount) {
            this.id = id; this.customer = customer; this.amount = amount;
        }

        @Override public String toString() {
            return "OrderEntity{id=" + id + ", customer='" + customer + "', amount=" + amount + "}";
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Jakarta EE Namespace Migration Demo ===");
        System.out.println();
        System.out.println("Spring Boot 2.x (javax.*):");
        System.out.println("  import javax.servlet.http.HttpServletRequest;");
        System.out.println("  import javax.persistence.Entity;");
        System.out.println("  import javax.validation.constraints.NotNull;");
        System.out.println("  import javax.annotation.PostConstruct;");
        System.out.println();
        System.out.println("Spring Boot 3.x (jakarta.*):        ← only the prefix changed");
        System.out.println("  import jakarta.servlet.http.HttpServletRequest;");
        System.out.println("  import jakarta.persistence.Entity;");
        System.out.println("  import jakarta.validation.constraints.NotNull;");
        System.out.println("  import jakarta.annotation.PostConstruct;");

        System.out.println("\n--- Validation (same logic, different import) ---");
        try {
            new OrderRequest(1, "alice", 99.99).validate();
            System.out.println("OrderRequest valid");
        } catch (IllegalArgumentException e) {
            System.out.println("Validation failed: " + e.getMessage());
        }

        try {
            new OrderRequest(2, "", 50.0).validate();
        } catch (IllegalArgumentException e) {
            System.out.println("Validation failed: " + e.getMessage());
        }
    }
}
```

How to run: `java JakartaMigrationDemo.java`

The business logic is identical. Only the import statements change. The compile error you get when upgrading is `cannot find symbol: javax.servlet.http.HttpServletRequest` because the `javax.servlet` JAR is no longer on the classpath — replaced by `jakarta.servlet`.

### Level 2 — Intermediate

Simulate the full migration checklist: detect stale imports, rename them, update Maven coordinates.

```java
// JakartaMigrationV2.java — run with: java JakartaMigrationV2.java
// Simulates what OpenRewrite / IDE migration tooling does.

import java.util.*;

public class JakartaMigrationV2 {

    record ImportMigration(String oldImport, String newImport, String artifactChange) {}

    static final List<ImportMigration> MIGRATIONS = List.of(
        new ImportMigration(
            "javax.servlet.http.HttpServletRequest",
            "jakarta.servlet.http.HttpServletRequest",
            "javax.servlet:javax.servlet-api → jakarta.servlet:jakarta.servlet-api:6.x"),
        new ImportMigration(
            "javax.persistence.EntityManager",
            "jakarta.persistence.EntityManager",
            "javax.persistence:javax.persistence-api → jakarta.persistence:jakarta.persistence-api:3.x"),
        new ImportMigration(
            "javax.validation.Valid",
            "jakarta.validation.Valid",
            "javax.validation:validation-api → jakarta.validation:jakarta.validation-api:3.x"),
        new ImportMigration(
            "javax.annotation.PostConstruct",
            "jakarta.annotation.PostConstruct",
            "javax.annotation:javax.annotation-api → jakarta.annotation:jakarta.annotation-api:2.x"),
        new ImportMigration(
            "javax.transaction.Transactional",
            "jakarta.transaction.Transactional",
            "javax.transaction:javax.transaction-api → jakarta.transaction:jakarta.transaction-api:2.x")
    );

    // Simulated source file with stale imports
    static final String BOOT2_SOURCE = """
        import javax.servlet.http.HttpServletRequest;
        import javax.servlet.http.HttpServletResponse;
        import javax.persistence.EntityManager;
        import javax.persistence.Entity;
        import javax.validation.Valid;
        import javax.annotation.PostConstruct;

        @Entity
        public class OrderController {
            @Valid
            private Order order;

            @PostConstruct
            public void init() { /* warm up */ }
        }
        """;

    public static void main(String[] args) {
        System.out.println("=== Simulated OpenRewrite migration ===\n");
        System.out.println("Source file before migration:");
        System.out.println(BOOT2_SOURCE);

        String migrated = BOOT2_SOURCE;
        List<String> changes = new ArrayList<>();
        List<String> artifactChanges = new ArrayList<>();

        for (ImportMigration m : MIGRATIONS) {
            String oldShort = m.oldImport().substring(m.oldImport().lastIndexOf('.') + 1);
            // Match both full and short-form occurrences
            if (migrated.contains("javax.")) {
                String before = migrated;
                migrated = migrated.replace(m.oldImport(), m.newImport());
                // Also handle the annotation/class name part (javax. prefix in annotations)
                migrated = migrated.replace(
                    "javax." + m.oldImport().split("\\.")[1],
                    "jakarta." + m.oldImport().split("\\.")[1]);
                if (!migrated.equals(before)) {
                    changes.add("  " + m.oldImport() + "\n  → " + m.newImport());
                    artifactChanges.add("  " + m.artifactChange());
                }
            }
        }

        System.out.println("Source file after migration:");
        System.out.println(migrated);

        System.out.println("Import renames applied (" + changes.size() + "):");
        changes.forEach(System.out::println);

        System.out.println("\nMaven/Gradle artifact changes needed:");
        artifactChanges.forEach(System.out::println);

        System.out.println("\nImplementation versions to update:");
        System.out.println("  Hibernate ORM: 5.x → 6.x  (jakarta.persistence support)");
        System.out.println("  Tomcat:        9.x → 10.x  (jakarta.servlet support)");
        System.out.println("  Spring Boot:   2.x → 3.x   (jakarta.* baseline)");
    }
}
```

How to run: `java JakartaMigrationV2.java`

The simulation shows exactly what a migration tool does: find every `javax.*` import, replace it with `jakarta.*`, then flag the Maven coordinates that must also change. The tool finds renames; the developer must also update `pom.xml` and verify that third-party libraries have Jakarta-compatible releases.

### Level 3 — Advanced

Full migration checklist with impact assessment, risk scoring, and verification steps — the kind of report you'd generate before a Spring Boot 2→3 upgrade.

```java
// JakartaMigrationV3.java — run with: java JakartaMigrationV3.java
// Full upgrade readiness assessment with risk scoring.

import java.util.*;

public class JakartaMigrationV3 {

    enum Risk { LOW, MEDIUM, HIGH }

    record MigrationTask(String area, String action, Risk risk, String verification) {}

    static final List<MigrationTask> TASKS = List.of(
        new MigrationTask("JDK",
            "Upgrade JDK to 17+ (Spring 6 minimum)",
            Risk.HIGH,
            "java --version must show 17+"),
        new MigrationTask("Spring Boot",
            "Bump spring-boot.version from 2.x to 3.x in pom.xml/build.gradle",
            Risk.HIGH,
            "./mvnw dependency:tree | grep spring-boot:3"),
        new MigrationTask("Jakarta imports",
            "Run OpenRewrite: org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta",
            Risk.MEDIUM,
            "grep -r 'javax\\.' src/ | grep import | wc -l == 0"),
        new MigrationTask("Servlet API",
            "Replace javax.servlet:javax.servlet-api with jakarta.servlet:jakarta.servlet-api:6.x",
            Risk.HIGH,
            "Tomcat 10.x (Boot 3 embedded) understands jakarta.servlet"),
        new MigrationTask("JPA",
            "Replace javax.persistence with jakarta.persistence; upgrade Hibernate to 6.x",
            Risk.HIGH,
            "EntityManager methods unchanged; column name defaults changed in Hibernate 6"),
        new MigrationTask("Bean Validation",
            "Replace javax.validation with jakarta.validation; Hibernate Validator 8.x",
            Risk.LOW,
            "All @NotNull, @Valid, @Positive annotations still work"),
        new MigrationTask("Spring Security",
            "Upgrade to Spring Security 6.x (required by Boot 3)",
            Risk.MEDIUM,
            "SecurityFilterChain API changed; no more WebSecurityConfigurerAdapter"),
        new MigrationTask("Third-party libs",
            "Audit all deps for jakarta-compatible releases (MapStruct, Lombok, OpenAPI, etc.)",
            Risk.MEDIUM,
            "Check release notes; most popular libs released jakarta versions by 2023"),
        new MigrationTask("Properties migrator",
            "Add spring-boot-properties-migrator; fix all WARN lines at startup",
            Risk.LOW,
            "Zero WARN lines from PropertiesMigrationListener at startup"),
        new MigrationTask("Tests",
            "Run full test suite; MockMvc + @SpringBootTest pick up context changes",
            Risk.LOW,
            "mvn test (zero failures)")
    );

    public static void main(String[] args) {
        System.out.println("=== Spring Boot 2.x → 3.x Migration Assessment ===\n");
        System.out.printf("%-18s %-6s %s%n", "Area", "Risk", "Action");
        System.out.println("-".repeat(90));

        Map<Risk, List<MigrationTask>> byRisk = new EnumMap<>(Risk.class);
        for (MigrationTask t : TASKS) {
            byRisk.computeIfAbsent(t.risk(), k -> new ArrayList<>()).add(t);
            System.out.printf("%-18s [%-6s] %s%n", t.area(), t.risk(), t.action());
        }

        System.out.println("\n=== By risk level ===");
        for (Risk r : new Risk[]{Risk.HIGH, Risk.MEDIUM, Risk.LOW}) {
            System.out.println("\n" + r + ":");
            byRisk.getOrDefault(r, List.of())
                  .forEach(t -> System.out.println("  • " + t.action()));
        }

        System.out.println("\n=== Verification commands ===");
        TASKS.forEach(t -> System.out.printf("  [%s] %s%n", t.area(), t.verification()));

        System.out.println("\n=== Key rule ===");
        System.out.println("  javax.* → jakarta.*: mechanical (tooling handles it)");
        System.out.println("  API behaviour changes (Hibernate 6 naming, Security config): manual review required");
        System.out.println("  Third-party libraries without jakarta releases: biggest blocking risk");
    }
}
```

How to run: `java JakartaMigrationV3.java`

The risk-ordered task list separates the mechanical rename (low-to-medium risk, tooling handles it) from the behavioural changes (Hibernate column naming, Spring Security API changes) that require manual review regardless of tooling.

## 6. Walkthrough

**Level 1 — why it fails:** When you bump `spring-boot-parent` from `2.7.x` to `3.0.x`, Maven resolves `jakarta.servlet:jakarta.servlet-api:6.x` instead of `javax.servlet:javax.servlet-api:4.x`. Any class that imports `javax.servlet.*` now produces a compile error because the old JAR is gone from the dependency graph.

**Level 2 — migration execution:**
1. `BOOT2_SOURCE` contains five `javax.*` imports.
2. The loop iterates `MIGRATIONS`, replacing each `javax.*` occurrence in the string.
3. For each replaced import, the corresponding Maven coordinate is added to `artifactChanges`.
4. The print shows the "before" source, the "after" source, and the artifact changes.

In real OpenRewrite, the recipe traverses the AST of every `.java` file in the project and produces a diff. The result is applied to disk before you run a build.

**Level 3 — risk assessment:**
- HIGH risk tasks block the build outright or cause runtime failure if missed (wrong JDK version, wrong servlet JAR, Hibernate version mismatch).
- MEDIUM risk tasks cause test failures or unexpected runtime behaviour but don't necessarily prevent startup.
- LOW risk tasks are mechanical with known, safe outcomes.

The verification column gives a command-line check for each task — these form a migration acceptance test.

**Concrete compile error before migration:**
```
[ERROR] OrderController.java:1: error: package javax.servlet.http does not exist
import javax.servlet.http.HttpServletRequest;
```

**After migration:**
```
import jakarta.servlet.http.HttpServletRequest;
```

Compilation succeeds once the `jakarta.servlet-api:6.x` JAR is on the classpath.

## 7. Gotchas & takeaways

> **The `javax.*` packages in the JDK itself (e.g., `javax.crypto`, `javax.swing`, `javax.sql`, `javax.naming`) did NOT change.** They are part of the JDK, not Jakarta EE. Only the standalone specification JARs (servlet, persistence, validation, annotation, transaction, inject, xml, etc.) moved to `jakarta.*`. Do not bulk-replace every `javax.` occurrence — you'll break JDK imports.

> **Hibernate 6 changed default column/table naming.** Even after the namespace rename, Hibernate ORM 6.x (required for `jakarta.persistence`) changed its `ImplicitNamingStrategy` defaults. Column names that were `camelCase` in Hibernate 5 are now `snake_case` by default in Hibernate 6. This causes silent data mapping failures. Check every `@Entity` class if you don't have explicit `@Column(name=...)` annotations.

- Most popular Spring ecosystem libraries (MapStruct 1.5+, Lombok, SpringDoc OpenAPI 2.x, Flyway 9+, Liquibase 4.x) have Jakarta-compatible releases. Check before upgrading.
- `javax.mail.*` → `jakarta.mail.*` (same pattern; Spring's `JavaMailSender` was updated accordingly).
- The OpenRewrite recipe `UpgradeSpringBoot_3_0` performs the jakarta rename + Boot 3 property renames + Spring Security API migration in one pass.
- `spring-boot-properties-migrator` is always a good first step: add it, start the app, fix every WARN, then remove it. Do this before tackling the namespace rename.
- After migration, run `grep -r 'javax\.' src/ --include='*.java' | grep 'import javax\.\(servlet\|persistence\|validation\|annotation\|transaction\)'` to verify zero stale imports remain.
