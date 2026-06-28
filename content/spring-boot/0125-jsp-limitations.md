---
card: spring-boot
gi: 125
slug: jsp-limitations
title: JSP limitations
---

## 1. What it is

**JavaServer Pages (JSP)** is the classic Java view technology — `.jsp` files that mix HTML and Java code, compiled to servlets at runtime. Spring Boot supports JSP when using an embedded Tomcat or Jetty, but with significant restrictions that make it a poor fit for the embedded-jar deployment model. JSP is effectively unsupported with Undertow and reactive (WebFlux) apps.

## 2. Why & when

JSP was designed for WAR deployments: the Servlet container expands the WAR archive, finds `.jsp` files, and compiles them. Embedded Spring Boot apps package everything in a fat JAR — `.jsp` files inside a JAR cannot be served directly by the JSP compiler. The workarounds are awkward and brittle.

You'll hit JSP when:

- Migrating a legacy Spring MVC app to Spring Boot.
- A third-party library bundles JSP views.

For new projects, prefer **Thymeleaf**, **Freemarker**, or **Mustache** — they are first-class template engines with full Spring Boot auto-configuration and no such packaging restrictions.

## 3. Core concept

JSP limitations in embedded Spring Boot:

1. **JAR packaging doesn't work.** JSP requires files to be present on the filesystem, not inside a JAR. Embedded Tomcat can compile and serve JSPs only when they are on the file system, not when embedded.
2. **Must use WAR packaging or an exploded JAR.** Setting `<packaging>war</packaging>` in `pom.xml` and running in a directory (not from a fat JAR) is required.
3. **Undertow has no JSP support.** No workaround exists.
4. **WebFlux (reactive) has no JSP support.** JSP is blocking; it cannot work with the reactive stack.
5. **`spring-boot-starter-tomcat` must be in `provided` scope** if deploying to an external Tomcat, which complicates local development.
6. **JSTL must be added manually.** It's not included by default.

If you must use JSPs: set `spring.mvc.view.prefix=/WEB-INF/views/` and `spring.mvc.view.suffix=.jsp`, add `tomcat-embed-jasper` dependency, and use WAR packaging.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="40" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="70" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Fat JAR (spring-boot)</text>
  <rect x="20" y="140" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="165" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">WAR / Exploded</text>
  <text x="100" y="181" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">filesystem .jsp files</text>
  <rect x="280" y="40" width="140" height="50" rx="8" fill="#1c2430" stroke="#e05252" stroke-width="1.5"/>
  <text x="350" y="68" text-anchor="middle" fill="#e05252" font-size="12" font-family="sans-serif">JSP: FAILS</text>
  <rect x="280" y="100" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="128" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Thymeleaf/FTL: OK</text>
  <rect x="280" y="140" width="140" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="168" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">JSP: works</text>
  <rect x="510" y="85" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="580" y="108" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Embedded</text>
  <text x="580" y="124" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Tomcat/Jetty</text>
  <line x1="182" y1="65" x2="276" y2="63" stroke="#e05252" stroke-width="1.5" marker-end="url(#js)"/>
  <line x1="182" y1="68" x2="276" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#js2)"/>
  <line x1="182" y1="165" x2="276" y2="162" stroke="#8b949e" stroke-width="1.5" marker-end="url(#js3)"/>
  <line x1="422" y1="120" x2="506" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#js4)"/>
  <text x="350" y="36" fill="#e05252" font-size="10" font-family="sans-serif">JSP inside JAR = not accessible</text>
  <defs>
    <marker id="js" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e05252"/></marker>
    <marker id="js2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="js3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="js4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Fat JARs and JSP are incompatible. Thymeleaf/Freemarker work in any packaging; JSP requires WAR or an exploded archive.

## 5. Runnable example

```java
// This example shows a Thymeleaf alternative to JSP (the recommended approach)
// Add spring-boot-starter-thymeleaf to pom.xml

// ThymeleafApp.java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@SpringBootApplication
public class ThymeleafApp {
    public static void main(String[] args) {
        SpringApplication.run(ThymeleafApp.class, args);
    }
}

@Controller
class GreetController {

    @GetMapping("/greet")
    public String greet(Model model) {
        model.addAttribute("name", "World");
        return "greet";   // resolves to src/main/resources/templates/greet.html
    }
}

// src/main/resources/templates/greet.html:
// <!DOCTYPE html>
// <html xmlns:th="http://www.thymeleaf.org">
// <body>
//   <h1 th:text="'Hello, ' + ${name} + '!'">Hello!</h1>
// </body>
// </html>
```

**How to run:** add `spring-boot-starter-thymeleaf`, create the HTML template at `src/main/resources/templates/greet.html`, start the app, and visit `http://localhost:8080/greet`. Works from a fat JAR — no filesystem dependency.

## 6. Walkthrough

- Thymeleaf templates live in `src/main/resources/templates/` and are included inside the JAR as classpath resources. The template engine reads them from the classpath at request time — no filesystem access needed.
- `model.addAttribute("name", "World")` populates the Thymeleaf context; `th:text="'Hello, ' + ${name}"` in the HTML renders the value.
- Spring Boot auto-configures a `ThymeleafViewResolver` when `spring-boot-starter-thymeleaf` is present. The controller returns `"greet"` and the resolver finds `templates/greet.html`.
- Contrast with JSP: a JSP at `src/main/webapp/WEB-INF/views/greet.jsp` is NOT on the classpath and cannot be read from inside a JAR. The embedded Tomcat JSP compiler needs a real file path.
- If you truly need JSP, use `<packaging>war</packaging>` in `pom.xml`, add `tomcat-embed-jasper` (scope `provided`), set `spring.mvc.view.prefix=/WEB-INF/views/` and `spring.mvc.view.suffix=.jsp`, and run the WAR expanded (not from `java -jar`).

## 7. Gotchas & takeaways

> `tomcat-embed-jasper` must be `compile` scope (not `provided`) when running with the Spring Boot Maven plugin in embedded mode — counterintuitive because you'd mark it `provided` in an external Tomcat WAR.

> JSP error pages (mapped in `web.xml` or via `ErrorPage`) also fail inside a JAR for the same filesystem reason. Error pages must be moved to Thymeleaf or Freemarker templates when migrating.

- Use Thymeleaf for server-side templating in new Spring Boot projects; it has full auto-config and works in fat JARs.
- Undertow offers no JSP support at all — switching containers immediately breaks JSP-based apps.
- WebFlux (reactive) cannot use JSP because JSP compilation is inherently blocking.
- If migrating a JSP app, a WAR layout with embedded Tomcat (still runnable via `java -jar`) is the safest intermediate step before converting templates.
- JSTL (`jakarta.servlet.jsp.jstl`) is not included transitively; add it explicitly if you keep JSP.
