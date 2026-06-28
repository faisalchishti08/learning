---
card: spring-boot
gi: 236
slug: building-war-files-traditional-deployment
title: Building WAR files (traditional deployment)
---

## 1. What it is

A WAR (Web Application Archive) packages a Spring Boot application so it can be deployed to a traditional servlet container (Tomcat, WildFly, WebLogic) as well as run standalone with the embedded server. Spring Boot supports both modes from the same WAR artifact by including the embedded server but marking it as `provided` so the external container's server takes precedence when present.

## 2. Why & when

Most modern deployments use executable JARs with embedded Tomcat. WAR is needed when your organisation enforces deployment to a managed application server — common in enterprises with existing Tomcat or JBoss infrastructure, shared server capacity management, or regulatory requirements around approved server configurations.

## 3. Core concept

Three steps convert a Spring Boot JAR project to a deployable WAR:

1. Change `<packaging>war</packaging>` in `pom.xml`.
2. Extend `SpringBootServletInitializer` and override `configure()` — this is the hook the servlet container calls instead of a `main()` method.
3. Mark `spring-boot-starter-tomcat` as `<scope>provided</scope>` so the embedded Tomcat is excluded when deploying to an external container (but still present for standalone `java -jar`).

`WarLauncher` in the manifest handles standalone mode; the servlet container's own bootstrap handles managed deployment.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="280" fill="#1c2430" rx="10"/>
  <!-- WAR structure -->
  <rect x="20" y="30" width="200" height="220" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="120" y="58" text-anchor="middle" fill="#79c0ff">myapp.war</text>
  <rect x="35" y="68" width="170" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="91" text-anchor="middle" fill="#6db33f" font-size="12">WEB-INF/lib/ (runtime deps)</text>
  <rect x="35" y="110" width="170" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="120" y="133" text-anchor="middle" fill="#8b949e" font-size="12">WEB-INF/lib-provided/</text>
  <text x="120" y="148" text-anchor="middle" fill="#8b949e" font-size="10">(embedded Tomcat, scope=provided)</text>
  <rect x="35" y="158" width="170" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="181" text-anchor="middle" fill="#6db33f" font-size="12">WEB-INF/classes/</text>
  <rect x="35" y="200" width="170" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="120" y="223" text-anchor="middle" fill="#8b949e" font-size="12">META-INF/MANIFEST.MF</text>
  <!-- Deployment paths -->
  <rect x="270" y="50" width="160" height="80" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="76" text-anchor="middle" fill="#6db33f">Standalone</text>
  <text x="350" y="96" text-anchor="middle" fill="#8b949e" font-size="11">java -jar myapp.war</text>
  <text x="350" y="114" text-anchor="middle" fill="#8b949e" font-size="11">WarLauncher + embedded Tomcat</text>
  <rect x="270" y="160" width="160" height="80" rx="6" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="186" text-anchor="middle" fill="#79c0ff">Managed deploy</text>
  <text x="350" y="206" text-anchor="middle" fill="#8b949e" font-size="11">Drop WAR into Tomcat/webapps/</text>
  <text x="350" y="224" text-anchor="middle" fill="#8b949e" font-size="11">SpringBootServletInitializer</text>
  <!-- arrows -->
  <line x1="222" y1="120" x2="268" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#aa)"/>
  <line x1="222" y1="150" x2="268" y2="195" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#aa)"/>
  <defs>
    <marker id="aa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_One WAR serves both standalone (`java -jar`) and traditional servlet-container deployment._

## 5. Runnable example

```java
// File: WarDeployDemo.java
// How to run: java WarDeployDemo.java
// Illustrates the key WAR packaging code patterns.
// Real WAR packaging requires a Spring Boot project (./mvnw package with war packaging).

public class WarDeployDemo {

    // ---- pom.xml snippet (NOT Java — shown for reference) ----
    // <packaging>war</packaging>
    //
    // <dependency>
    //   <groupId>org.springframework.boot</groupId>
    //   <artifactId>spring-boot-starter-tomcat</artifactId>
    //   <scope>provided</scope>   <!-- exclude embedded Tomcat from WEB-INF/lib -->
    // </dependency>

    // ---- SpringBootServletInitializer subclass ----
    // In a real project this is an @SpringBootApplication class:
    //
    // @SpringBootApplication
    // public class DemoApplication extends SpringBootServletInitializer {
    //
    //     @Override
    //     protected SpringApplicationBuilder configure(SpringApplicationBuilder builder) {
    //         return builder.sources(DemoApplication.class);
    //     }
    //
    //     public static void main(String[] args) {
    //         SpringApplication.run(DemoApplication.class, args);
    //     }
    // }

    public static void main(String[] args) {
        System.out.println("WAR packaging checklist:");
        String[] steps = {
            "1. Set <packaging>war</packaging> in pom.xml",
            "2. Add spring-boot-starter-tomcat with <scope>provided</scope>",
            "3. Extend SpringBootServletInitializer and override configure()",
            "4. Keep main() method for standalone java -jar mode",
            "5. Run: ./mvnw package  (produces target/myapp.war)",
            "6a. Standalone: java -jar target/myapp.war",
            "6b. Managed:    cp target/myapp.war $CATALINA_HOME/webapps/"
        };
        for (String s : steps) System.out.println(s);

        System.out.println("\nExpected WAR layout:");
        System.out.println("  WEB-INF/lib/           <- runtime dependency JARs");
        System.out.println("  WEB-INF/lib-provided/  <- embedded Tomcat (scope=provided)");
        System.out.println("  WEB-INF/classes/       <- your compiled classes");
        System.out.println("  META-INF/MANIFEST.MF   <- Main-Class: WarLauncher");
    }
}
```

**How to run:** `java WarDeployDemo.java` — prints the packaging checklist and WAR layout.

## 6. Walkthrough

1. `<packaging>war</packaging>` — tells Maven to produce a `.war` file and use the WAR plugin layout.
2. `spring-boot-starter-tomcat` with `scope=provided` — the embedded Tomcat JARs go into `WEB-INF/lib-provided/`. They are on the classpath for standalone execution but excluded from the managed-deploy classpath (the container provides its own Tomcat).
3. `SpringBootServletInitializer.configure()` — when a servlet container deploys the WAR, it looks for implementations of `WebApplicationInitializer`. Spring Boot's `SpringBootServletInitializer` implements this; `configure()` registers the application class so Spring Boot bootstraps correctly.
4. `main()` stays in the class — when running `java -jar myapp.war`, `WarLauncher` finds `Start-Class` in the manifest and calls `main()`, which starts the embedded Tomcat from `WEB-INF/lib-provided/`.

## 7. Gotchas & takeaways

> Forgetting `<scope>provided</scope>` on `spring-boot-starter-tomcat` causes class-loading conflicts when deploying to a real Tomcat — two Tomcat implementations compete on the classpath.

> Spring Boot 3.x requires a Servlet 5.0+ (Jakarta EE 9+) container. Older Tomcat 9 or JBoss EAP using `javax.servlet` will NOT work — you must use Tomcat 10+ for Boot 3.

> The context path in managed deployment is determined by the WAR file name (e.g., `myapp.war` → `/myapp`). Override `server.servlet.context-path` or rename the WAR to control this.

- Keep `main()` in the same class as `SpringBootServletInitializer` — one class, both entry points.
- Test the WAR in standalone mode locally before deploying to the managed server.
- Prefer executable JARs for new projects; use WAR only when an external server is a hard requirement.
- Use `mvn spring-boot:run` for development — it doesn't require packaging.
