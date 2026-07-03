---
card: spring-framework
gi: 143
slug: resource-as-dependency
title: "Resource as dependency"
---

## 1. What it is

Spring can inject `Resource` objects directly into beans via `@Value` annotations or constructor/setter injection, converting a location string to a `Resource` automatically. The container uses the same prefix dispatch as `ResourceLoader` — no manual resource loading code needed.

```java
@Value("classpath:templates/email.html")
Resource emailTemplate;

@Value("file:/opt/app/certs/server.pem")
Resource serverCert;
```

Spring converts the `@Value` string to the appropriate `Resource` implementation via a built-in `PropertyEditor` (`ResourceEditor`).

## 2. Why & when

- **Zero boilerplate** — declare a `Resource` field, annotate with `@Value`, done. No `ResourceLoader`, no `ClassPathResource` constructor call.
- **Configurable paths** — combine `@Value` with `${...}` tokens: `@Value("${cert.path}")` injects a `Resource` from a configurable path.
- **Array injection** — `@Value("classpath:db/*.sql") Resource[] scripts` injects multiple resources from a wildcard pattern.
- **Spring MVC** — controller method parameters can be `Resource` when producing file downloads.

## 3. Core concept

How `Resource` injection works:

1. Container encounters `@Value("classpath:foo.txt")` on a `Resource`-typed field.
2. Spring evaluates the `@Value` string (resolves `${...}` tokens first).
3. `ResourceEditor` is invoked — it calls `ctx.getResource(locationString)`.
4. The resulting `Resource` object is injected.

For arrays and collections, `PathMatchingResourcePatternResolver` handles wildcard patterns via a `ResourceArrayPropertyEditor`.

```java
// Single resource
@Value("classpath:schema.sql")              Resource schema;

// Wildcard — injects all matching files
@Value("classpath:migrations/**/*.sql")     Resource[] migrations;

// Configurable path (from application.properties)
@Value("${cert.location:classpath:dev.pem}") Resource cert;
```

Constructor injection also works when the `Resource` parameter is wired from `@Configuration`:

```java
@Bean
public ReportGenerator reportGenerator(
        @Value("classpath:templates/report.html") Resource template) {
    return new ReportGenerator(template);
}
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- @Value string -->
  <rect x="10" y="30" width="220" height="45" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">@Value("classpath:config.yaml")</text>
  <text x="120" y="68" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Resource field or @Bean parameter</text>

  <!-- ResourceEditor -->
  <rect x="285" y="30" width="180" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="375" y="51" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ResourceEditor</text>
  <text x="375" y="67" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">ctx.getResource(string)</text>

  <!-- Resource object -->
  <rect x="525" y="30" width="165" height="45" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="607" y="51" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ClassPathResource</text>
  <text x="607" y="67" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">injected into bean field</text>

  <defs>
    <marker id="a143" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="b143" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="232" y1="52" x2="282" y2="52" stroke="#79c0ff" stroke-width="2" marker-end="url(#a143)"/>
  <line x1="467" y1="52" x2="522" y2="52" stroke="#6db33f" stroke-width="2" marker-end="url(#b143)"/>

  <!-- Wildcard path -->
  <rect x="10" y="110" width="220" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="132" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">@Value("classpath:sql/**/*.sql")</text>
  <text x="120" y="148" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Resource[] field</text>

  <rect x="285" y="110" width="180" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="375" y="131" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ResourceArrayPropertyEditor</text>
  <text x="375" y="147" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">PathMatchingResourcePatternResolver</text>

  <rect x="525" y="110" width="165" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="607" y="135" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Resource[] all matches</text>

  <line x1="232" y1="132" x2="282" y2="132" stroke="#79c0ff" stroke-width="2" marker-end="url(#a143)"/>
  <line x1="467" y1="132" x2="522" y2="132" stroke="#6db33f" stroke-width="2" marker-end="url(#b143)"/>

  <text x="350" y="182" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ResourceEditor handles single; ResourceArrayPropertyEditor handles wildcard arrays</text>
</svg>

`@Value` on a `Resource` field triggers `ResourceEditor`, which converts the location string to the correct `Resource` type automatically.

## 5. Runnable example

### Level 1 — Basic

Inject a single classpath resource; use `${...}` token for configurable path.

```java
// ResourceAsDependencyBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import java.nio.file.*;
import java.util.Properties;

class AppConfigLoader {
    @Value("classpath:injected-config.properties")
    Resource configResource;

    @Value("classpath:injected-schema.sql")
    Resource schemaResource;

    public void load() throws Exception {
        var props = new Properties();
        props.load(configResource.getInputStream());
        System.out.println("Config resource: " + configResource.getFilename() +
            " (" + configResource.contentLength() + " bytes)");
        System.out.println("  db.url: " + props.getProperty("db.url"));

        System.out.println("Schema resource: " + schemaResource.getFilename() +
            " exists=" + schemaResource.exists());
        System.out.println("  SQL: " +
            new String(schemaResource.getInputStream().readAllBytes()).trim());
    }
}

@Configuration
@ComponentScan(basePackageClasses = ResourceAsDependencyBasic.class)
class ResDep1Cfg {}

public class ResourceAsDependencyBasic {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("injected-config.properties"),
            "db.url=jdbc:h2:mem:basic\ndb.pool=3\n");
        Files.writeString(Path.of("injected-schema.sql"),
            "CREATE TABLE items (id INT PRIMARY KEY, name VARCHAR(100));\n");

        var ctx = new AnnotationConfigApplicationContext(ResDep1Cfg.class);
        ctx.getBean(AppConfigLoader.class).load();
        ctx.close();

        Files.deleteIfExists(Path.of("injected-config.properties"));
        Files.deleteIfExists(Path.of("injected-schema.sql"));
    }
}
```

How to run: `java ResourceAsDependencyBasic.java`

`@Value("classpath:...")` on `Resource` fields triggers `ResourceEditor`. No `ResourceLoader` is needed — Spring injects fully resolved `Resource` objects with all metadata available.

### Level 2 — Intermediate

Wildcard `Resource[]` injection; configurable path with `${...}`; `@Bean` parameter injection.

```java
// ResourceAsDependencyArray.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import java.nio.file.*;
import java.util.*;

class MigrationRunner {
    private final Resource[] scripts;
    private final Resource baselineScript;

    MigrationRunner(Resource[] scripts, Resource baselineScript) {
        this.scripts        = scripts;
        this.baselineScript = baselineScript;
    }

    public void run() throws Exception {
        System.out.println("Baseline: " + baselineScript.getFilename());
        System.out.println("  " + new String(baselineScript.getInputStream().readAllBytes()).trim());

        System.out.println("\nMigrations (" + scripts.length + " files):");
        Arrays.sort(scripts, Comparator.comparing(Resource::getFilename));
        for (Resource r : scripts) {
            System.out.println("  [" + r.getFilename() + "] " +
                new String(r.getInputStream().readAllBytes()).trim());
        }
    }
}

@Configuration
class MigCfg {
    @Bean
    public MigrationRunner migrationRunner(
            @Value("classpath:sql/migrations/*.sql") Resource[] migrations,
            @Value("${baseline.sql:classpath:sql/baseline.sql}") Resource baseline) {
        return new MigrationRunner(migrations, baseline);
    }
}

public class ResourceAsDependencyArray {
    public static void main(String[] args) throws Exception {
        Files.createDirectories(Path.of("sql/migrations"));
        Files.writeString(Path.of("sql/baseline.sql"),
            "CREATE SCHEMA IF NOT EXISTS app;");
        Files.writeString(Path.of("sql/migrations/001-users.sql"),
            "CREATE TABLE users (id INT, name TEXT);");
        Files.writeString(Path.of("sql/migrations/002-products.sql"),
            "CREATE TABLE products (id INT, sku TEXT, price DECIMAL);");
        Files.writeString(Path.of("sql/migrations/003-orders.sql"),
            "CREATE TABLE orders (id INT, user_id INT, total DECIMAL);");

        var ctx = new AnnotationConfigApplicationContext(MigCfg.class);
        ctx.getBean(MigrationRunner.class).run();
        ctx.close();

        for (String f : new String[]{
            "sql/migrations/001-users.sql","sql/migrations/002-products.sql",
            "sql/migrations/003-orders.sql","sql/baseline.sql"}) {
            Files.deleteIfExists(Path.of(f));
        }
        Files.deleteIfExists(Path.of("sql/migrations"));
        Files.deleteIfExists(Path.of("sql"));
    }
}
```

How to run: `java ResourceAsDependencyArray.java`

`@Value("classpath:sql/migrations/*.sql") Resource[]` injects all matching files. The `@Bean` factory parameter with `@Value` combines property resolution and resource loading in one step.

### Level 3 — Advanced

Multi-format resource loading (YAML, JSON, XML, SQL); default fallback resource; resource-as-template pattern.

```java
// ResourceAsDependencyAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import java.nio.file.*;

class TemplateEngine {
    @Value("${template.html:classpath:tpl/default.html}")    Resource htmlTemplate;
    @Value("${template.json:classpath:tpl/default.json}")    Resource jsonTemplate;
    @Value("${template.text:classpath:tpl/default.text}")    Resource textTemplate;

    @Value("classpath:tpl/partials/*.html")
    Resource[] partials;

    public void render(String format) throws Exception {
        Resource tpl = switch (format) {
            case "html" -> htmlTemplate;
            case "json" -> jsonTemplate;
            case "text" -> textTemplate;
            default     -> throw new IllegalArgumentException("Unknown format: " + format);
        };

        System.out.printf("[%s] template=%s exists=%b size=%d bytes%n",
            format, tpl.getFilename(), tpl.exists(),
            tpl.exists() ? tpl.contentLength() : 0);
        if (tpl.exists()) {
            System.out.println("  content: " +
                new String(tpl.getInputStream().readAllBytes()).trim());
        }
    }

    public void listPartials() {
        System.out.println("Partials (" + partials.length + "):");
        for (Resource p : partials) System.out.println("  " + p.getFilename());
    }
}

@Configuration
@ComponentScan(basePackageClasses = ResourceAsDependencyAdvanced.class)
class TplCfg {}

public class ResourceAsDependencyAdvanced {
    public static void main(String[] args) throws Exception {
        Files.createDirectories(Path.of("tpl/partials"));
        Files.writeString(Path.of("tpl/default.html"), "<html><body>{{content}}</body></html>");
        Files.writeString(Path.of("tpl/default.json"), "{\"content\":\"{{content}}\"}");
        Files.writeString(Path.of("tpl/default.text"), "{{content}}");
        Files.writeString(Path.of("tpl/partials/header.html"), "<header>App</header>");
        Files.writeString(Path.of("tpl/partials/footer.html"), "<footer>2026</footer>");

        var ctx = new AnnotationConfigApplicationContext(TplCfg.class);
        var engine = ctx.getBean(TemplateEngine.class);

        for (String fmt : new String[]{"html", "json", "text"}) {
            engine.render(fmt);
        }
        System.out.println();
        engine.listPartials();

        ctx.close();

        for (String f : new String[]{
            "tpl/partials/header.html","tpl/partials/footer.html",
            "tpl/default.html","tpl/default.json","tpl/default.text"}) {
            Files.deleteIfExists(Path.of(f));
        }
        Files.deleteIfExists(Path.of("tpl/partials"));
        Files.deleteIfExists(Path.of("tpl"));
    }
}
```

How to run: `java ResourceAsDependencyAdvanced.java`

Three `@Value` fields each inject a `Resource` from a configurable path with a classpath default. `${template.html:classpath:tpl/default.html}` resolves the token first (from system props / application.properties if set), falling back to the classpath default. The `Resource[]` partial scan finds all HTML partials automatically.

## 6. Walkthrough

Execution for Level 3:

1. **`TplCfg` processed** — `TemplateEngine` component scanned.
2. **`@Value("${template.html:classpath:tpl/default.html}")` on `htmlTemplate`** — PSPC resolves token: `template.html` absent → default `"classpath:tpl/default.html"`.
3. **`ResourceEditor`** converts `"classpath:tpl/default.html"` → `ClassPathResource("tpl/default.html")`.
4. **`@Value("classpath:tpl/partials/*.html") Resource[]`** — `ResourceArrayPropertyEditor` calls `PathMatchingResourcePatternResolver.getResources(...)` → `[header.html, footer.html]`.
5. **`engine.render("html")`** → `htmlTemplate.exists()=true`, reads template content.
6. **`engine.listPartials()`** → shows 2 files.

## 7. Gotchas & takeaways

> `@Value("classpath:foo.txt") Resource` injects the resource at context startup, not lazily. If the file doesn't exist at startup, the injection still succeeds — but `r.exists()` returns `false`. Spring does NOT throw for a missing resource when injecting it as a `Resource`. It throws only if you call `r.getInputStream()` and the file is absent.

> `Resource[]` wildcard injection via `@Value` uses `PathMatchingResourcePatternResolver` — it returns results in no guaranteed order. Sort explicitly before processing to ensure deterministic behavior.

- Use `@Value("${path.key:classpath:default.txt}") Resource` to make resource paths configurable without changing code.
- `@Bean` factory methods can accept `@Value`-annotated `Resource` parameters — this is the cleanest way to inject resources into beans that are not `@Component` candidates.
- For writable resources, inject `Resource` and cast to `WritableResource` only if `r instanceof WritableResource` — never cast blindly.
- Spring Boot's `spring.config.import=optional:classpath:extra.yml` uses the same mechanism but at the `Environment` level, not at the bean injection level.
