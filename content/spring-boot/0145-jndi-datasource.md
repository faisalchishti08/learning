---
card: spring-boot
gi: 145
slug: jndi-datasource
title: JNDI DataSource
---

## 1. What it is

**JNDI (Java Naming and Directory Interface)** is a standard Java API for looking up resources by name from a directory — typically an application server's (JBoss, WebLogic, GlassFish, Tomcat) resource registry. A **JNDI DataSource** is a database connection pool configured and managed by the application server rather than by Spring Boot. Spring Boot can look up an existing JNDI-bound DataSource at startup via `spring.datasource.jndi-name`, instead of creating its own pool.

## 2. Why & when

JNDI DataSources are primarily a legacy enterprise pattern from the Java EE / Jakarta EE world where the application server owns infrastructure resources (data sources, JMS queues) and deploys multiple applications that share them. You need JNDI DataSource support when:

- Deploying a Spring Boot WAR to a traditional application server (Tomcat standalone, JBoss, WebLogic).
- The DBA or operations team manages the connection pool in the server's admin console.
- Corporate policy requires a single, centrally configured connection pool shared by multiple applications.

For embedded-server Spring Boot apps (the fat-JAR model), JNDI is rarely needed — use `spring.datasource.*` properties with HikariCP instead.

## 3. Core concept

When `spring.datasource.jndi-name` is set, `JndiDataSourceAutoConfiguration` performs a JNDI lookup via `InitialContext.lookup(name)` and registers the result as the `DataSource` bean. Spring Boot creates no connection pool itself — it uses whatever the JNDI provider returns.

```
Application server JNDI registry
  └─ "java:comp/env/jdbc/myDS"  →  configured DataSource
         ↓
spring.datasource.jndi-name=java:comp/env/jdbc/myDS
         ↓
Spring Boot DataSource bean = JNDI lookup result
```

The embedded Tomcat in Spring Boot can also be configured as a simple JNDI provider — useful for mimicking the production JNDI environment in a self-contained fat JAR.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="155" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Spring Boot starts</text>
  <rect x="250" y="55" width="185" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="342" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">JNDI Registry</text>
  <text x="342" y="97" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">java:comp/env/jdbc/myDS</text>
  <rect x="250" y="125" width="185" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="342" y="147" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">DataSource bean</text>
  <text x="342" y="164" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">(from JNDI lookup)</text>
  <rect x="510" y="80" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="110" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Database</text>
  <line x1="177" y1="105" x2="246" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jn)"/>
  <line x1="342" y1="107" x2="342" y2="123" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jn2)"/>
  <line x1="437" y1="150" x2="506" y2="118" stroke="#8b949e" stroke-width="1.5" marker-end="url(#jn3)"/>
  <defs>
    <marker id="jn" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jn2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="jn3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Spring Boot looks up the JNDI name at startup; the registry returns a pre-configured `DataSource`; Spring Boot uses it as its own `DataSource` bean.

## 5. Runnable example

```java
// JndiDatasourceApp.java — Spring Boot project demonstrating embedded JNDI setup
// pom.xml: spring-boot-starter-jdbc, com.h2database:h2 (runtime)
// application.properties:
//   spring.datasource.jndi-name=java:comp/env/jdbc/myDS

import org.apache.catalina.startup.Tomcat;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.sql.DataSource;

@SpringBootApplication
public class JndiDatasourceApp {
    public static void main(String[] args) {
        SpringApplication.run(JndiDatasourceApp.class, args);
    }
}

// Register a DataSource in Tomcat's embedded JNDI before Spring looks it up
@Configuration
class JndiConfig {

    @Bean
    public WebServerFactoryCustomizer<TomcatServletWebServerFactory> jndiCustomizer() {
        return factory -> factory.addContextCustomizers(context -> {
            // Bind an H2 DataSource under the JNDI name Spring will look up
            org.apache.catalina.Context ctx = (org.apache.catalina.Context) context;
            ctx.getNamingResources(); // ensure JNDI resources exist
            try {
                // Register an H2 datasource programmatically as a JNDI resource
                DataSource ds = new EmbeddedDatabaseBuilder()
                        .setType(EmbeddedDatabaseType.H2)
                        .build();
                ctx.getServletContext()
                   .setAttribute("javax.sql.DataSource", ds);

                // Bind in JNDI directly for the lookup
                InitialContext ic = new InitialContext();
                try { ic.createSubcontext("java:comp"); } catch (NamingException ignored) {}
                try { ic.createSubcontext("java:comp/env"); } catch (NamingException ignored) {}
                try { ic.createSubcontext("java:comp/env/jdbc"); } catch (NamingException ignored) {}
                ic.rebind("java:comp/env/jdbc/myDS", ds);
            } catch (Exception e) {
                throw new RuntimeException("JNDI setup failed", e);
            }
        });
    }
}

@RestController
class PingController {

    private final JdbcTemplate jdbc;

    PingController(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    @GetMapping("/ping")
    public String ping() {
        return "JNDI DataSource OK — " +
               jdbc.queryForObject("SELECT CURRENT_TIMESTAMP", String.class);
    }
}
```

**How to run:** add `spring-boot-starter-jdbc` and H2 to `pom.xml`, set `spring.datasource.jndi-name=java:comp/env/jdbc/myDS` in `application.properties`, start the app, then `curl http://localhost:8080/ping`.

## 6. Walkthrough

- `spring.datasource.jndi-name=java:comp/env/jdbc/myDS` triggers `JndiDataSourceAutoConfiguration` instead of the normal `DataSourceAutoConfiguration`. Spring Boot skips HikariCP setup and calls `JndiDataSourceLookup.getDataSource(name)`.
- The `WebServerFactoryCustomizer` runs before the server starts. It binds an H2 `EmbeddedDatabase` into Tomcat's embedded JNDI context at `java:comp/env/jdbc/myDS` — simulating what a real application server would do.
- `ic.rebind(...)` overwrites any existing binding safely. The three `createSubcontext` calls ensure the parent JNDI contexts exist before the leaf binding.
- When Spring Boot calls `InitialContext.lookup("java:comp/env/jdbc/myDS")`, it finds the H2 datasource we registered and uses it as the `DataSource` bean.
- `JdbcTemplate` autowires from the JNDI-sourced `DataSource` exactly as it would from a HikariCP one.
- In a real external Tomcat, you'd configure the DataSource in `conf/context.xml` instead of this programmatic setup.

## 7. Gotchas & takeaways

> JNDI is not available in embedded-server fat-JAR deployments by default. To use JNDI in a fat JAR, you must either configure Tomcat's embedded JNDI (as above) or use Spring's `SimpleNamingContextBuilder` (deprecated in Spring 5.2; replaced by `SimpleJndiContextLoader`).

> `spring.datasource.jndi-name` takes full priority — if set, `spring.datasource.url`, `.username`, and `.password` are **ignored**. Connection pooling is entirely controlled by the JNDI provider, not Spring Boot.

- For WAR deployments to Tomcat: configure `<Resource>` in `META-INF/context.xml` inside the WAR; Spring Boot reads it automatically.
- Spring Boot's Actuator DataSource health check works with JNDI DataSources — it simply calls `connection.isValid()`.
- WAR deployments need `SpringBootServletInitializer` as the entry point; the `main` method is not used.
- If JNDI lookup fails at startup, Spring Boot throws `NamingException` immediately — fail-fast behaviour that prevents a broken DataSource from going unnoticed.
