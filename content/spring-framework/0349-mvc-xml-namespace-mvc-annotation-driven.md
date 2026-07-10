---
card: spring-framework
gi: 349
slug: mvc-xml-namespace-mvc-annotation-driven
title: "MVC XML namespace (<mvc:annotation-driven>)"
---

## 1. What it is

`<mvc:annotation-driven>` is the XML-configuration equivalent of `@EnableWebMvc` — an element from Spring's `mvc` XML namespace that, when placed in a Spring XML configuration file, activates the same core MVC infrastructure (handler mapping, message converters, validation support) needed for `@Controller`/`@RequestMapping` annotations to work. It's the pre-Java-config way (XML-based Spring configuration, common before Spring 3.1 popularized `@Configuration` classes) of bootstrapping Spring MVC.

```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:mvc="http://www.springframework.org/schema/mvc"
       xsi:schemaLocation="http://www.springframework.org/schema/mvc
           http://www.springframework.org/schema/mvc/spring-mvc.xsd">

    <mvc:annotation-driven/>
    <context:component-scan base-package="com.example.app"/>
</beans>
```

## 2. Why & when

You will not write `<mvc:annotation-driven>` in any new Spring Boot project — Java-based configuration (`@EnableWebMvc`/`WebMvcConfigurer`, or Boot's autoconfiguration) has fully superseded XML configuration for MVC setup since Spring 3.1, and Spring Boot doesn't use XML application context configuration by default at all.

You need to recognize and understand this element when:
- Maintaining a legacy Spring MVC application whose bean configuration is still XML-based (`applicationContext.xml`, `dispatcher-servlet.xml`) — a common pattern in codebases dating from the Spring 2.x–3.x era.
- Migrating a legacy XML-configured application to Java config or Spring Boot, where you need to map each XML `<mvc:...>` element to its `WebMvcConfigurer` equivalent.
- Working in large, older enterprise codebases where XML configuration remains institutionally entrenched even in otherwise actively maintained systems.

## 3. Core concept

```
XML namespace element           Java config equivalent
─────────────────────────────────────────────────────────────
<mvc:annotation-driven/>    ↔   @EnableWebMvc
                                 (or, in Spring Boot: nothing —
                                  WebMvcAutoConfiguration does this)

<mvc:interceptors>          ↔   WebMvcConfigurer.addInterceptors(...)
<mvc:resources>              ↔   WebMvcConfigurer.addResourceHandlers(...)
<mvc:cors>                   ↔   WebMvcConfigurer.addCorsMappings(...)
<mvc:view-controller>        ↔   WebMvcConfigurer.addViewControllers(...)
<mvc:default-servlet-handler/> ↔ WebMvcConfigurer.configureDefaultServletHandling(...)

Every XML <mvc:...> element in this namespace corresponds to
EXACTLY ONE WebMvcConfigurer override method (covered individually
in the following cards) — the XML namespace and the Java config
API were designed as parallel, feature-equivalent surfaces.
```

Understanding this 1-to-1 mapping is the fastest way to translate a legacy XML-configured Spring MVC application into modern Java config or Spring Boot.

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">XML mvc namespace mirrors WebMvcConfigurer, feature for feature</text>

  <rect x="20" y="50" width="320" height="140" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="180" y="70" text-anchor="middle" fill="#8b949e" font-size="11">dispatcher-servlet.xml</text>
  <text x="35" y="95" fill="#e6edf3" font-size="10">&lt;mvc:annotation-driven/&gt;</text>
  <text x="35" y="113" fill="#e6edf3" font-size="10">&lt;mvc:interceptors&gt;...&lt;/mvc:interceptors&gt;</text>
  <text x="35" y="131" fill="#e6edf3" font-size="10">&lt;mvc:resources .../&gt;</text>
  <text x="35" y="149" fill="#e6edf3" font-size="10">&lt;mvc:cors&gt;...&lt;/mvc:cors&gt;</text>

  <line x1="340" y1="120" x2="400" y2="120" stroke="#8b949e" marker-end="url(#a25)"/>
  <text x="370" y="112" text-anchor="middle" fill="#8b949e" font-size="9">equivalent</text>

  <rect x="400" y="50" width="300" height="140" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="550" y="70" text-anchor="middle" fill="#6db33f" font-size="11">WebConfig.java</text>
  <text x="415" y="95" fill="#e6edf3" font-size="10">@EnableWebMvc</text>
  <text x="415" y="113" fill="#e6edf3" font-size="10">addInterceptors(...)</text>
  <text x="415" y="131" fill="#e6edf3" font-size="10">addResourceHandlers(...)</text>
  <text x="415" y="149" fill="#e6edf3" font-size="10">addCorsMappings(...)</text>

  <defs>
    <marker id="a25" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Each XML `<mvc:...>` element has a direct, feature-equivalent `WebMvcConfigurer` method.*

## 5. Runnable example

### Level 1 — Basic

A minimal legacy XML-configured Spring MVC setup, deployed as a WAR:

```xml
<!-- WEB-INF/dispatcher-servlet.xml -->
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:mvc="http://www.springframework.org/schema/mvc"
       xmlns:context="http://www.springframework.org/schema/context"
       xsi:schemaLocation="
           http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd
           http://www.springframework.org/schema/mvc http://www.springframework.org/schema/mvc/spring-mvc.xsd
           http://www.springframework.org/schema/context http://www.springframework.org/schema/context/spring-context.xsd">

    <mvc:annotation-driven/>
    <context:component-scan base-package="com.example.app"/>
</beans>
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill");
    }
}
```

**How to run:**
```bash
mvn clean package
# deploy target/app.war to Tomcat

curl http://localhost:8080/app/products/1
# {"id":1,"name":"Drill"}
```

Without `<mvc:annotation-driven/>`, `@RequestMapping`-annotated methods would never be discovered — this single element activates the `RequestMappingHandlerMapping` and the default `HttpMessageConverter`s (including a JSON converter, if Jackson is on the classpath) that make the above controller functional.

### Level 2 — Intermediate

The equivalent modern Java configuration, side by side, demonstrating the direct translation:

```java
// WebConfig.java — Java config equivalent of the XML above
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

@Configuration
@EnableWebMvc                                    // <mvc:annotation-driven/>
@ComponentScan(basePackages = "com.example.app")  // <context:component-scan .../>
public class WebConfig {
}
```

```java
// WebAppInitializer.java — replaces web.xml
import org.springframework.web.servlet.support.AbstractAnnotationConfigDispatcherServletInitializer;

public class WebAppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer {
    @Override
    protected Class<?>[] getRootConfigClasses() { return null; }
    @Override
    protected Class<?>[] getServletConfigClasses() { return new Class[]{ WebConfig.class }; }
    @Override
    protected String[] getServletMappings() { return new String[]{ "/" }; }
}
```

```java
// ProductController.java — UNCHANGED
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public Product get(@PathVariable long id) {
        return new Product(id, "Drill");
    }
}
```

**How to run:**
```bash
mvn clean package
# deploy target/app.war to Tomcat

curl http://localhost:8080/app/products/1
# {"id":1,"name":"Drill"}         <- IDENTICAL behavior, zero XML files anywhere in the project
```

**What changed:** No `web.xml`, no `dispatcher-servlet.xml` — `WebAppInitializer` programmatically registers `DispatcherServlet` (replacing what `web.xml` used to declare), and `@EnableWebMvc` + `@ComponentScan` replace `<mvc:annotation-driven/>` + `<context:component-scan>` exactly. The controller itself required zero changes, since `@RequestMapping`-family annotations work identically regardless of how the surrounding infrastructure was bootstrapped.

### Level 3 — Advanced

Production migration pattern: a hybrid configuration during an incremental migration, where legacy XML beans coexist temporarily with new Java config — a realistic scenario for a large codebase migrating gradually rather than in one disruptive rewrite:

```xml
<!-- WEB-INF/legacy-beans.xml — KEPT temporarily during migration, contains beans not yet ported -->
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans.xsd">

    <bean id="legacyReportGenerator" class="com.example.app.legacy.ReportGenerator">
        <property name="templatePath" value="/WEB-INF/reports/"/>
    </bean>
</beans>
```

```java
// WebConfig.java — NEW Java config, imports the remaining legacy XML during migration
import org.springframework.context.annotation.*;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

@Configuration
@EnableWebMvc
@ComponentScan(basePackages = "com.example.app")
@ImportResource("classpath:WEB-INF/legacy-beans.xml")   // bridge: still-XML-defined beans remain available
public class WebConfig {
}
```

```java
// ReportController.java — NEW annotation-based controller, using the OLD XML-defined bean
import com.example.app.legacy.ReportGenerator;
import org.springframework.web.bind.annotation.*;

@RestController
public class ReportController {

    private final ReportGenerator legacyReportGenerator;   // injected from the imported XML bean definition

    public ReportController(ReportGenerator legacyReportGenerator) {
        this.legacyReportGenerator = legacyReportGenerator;
    }

    @GetMapping("/reports/{id}")
    public String generate(@PathVariable long id) {
        return legacyReportGenerator.generate(id);
    }
}
```

**How to run:**
```bash
mvn clean package
# deploy target/app.war to Tomcat

curl http://localhost:8080/app/reports/1
# output from the legacy ReportGenerator bean, wired into a brand-new @RestController
```

**What changed and why:**
- `@ImportResource` bridges the two configuration styles during migration — the new `WebConfig` is fully Java-based and uses `@EnableWebMvc`, but it explicitly imports the one remaining XML file containing beans not yet worth the effort to port (perhaps `ReportGenerator` has complex, rarely-touched configuration that isn't a migration priority).
- `ReportController` is a brand-new, modern `@RestController`, but its constructor injects `ReportGenerator` — a bean whose *definition* still lives in XML — completely transparently, because Spring's dependency injection doesn't care whether a bean was defined via XML, `@Bean` methods, or component scanning; it's all the same `ApplicationContext` underneath.
- This pattern lets a team migrate a large XML-configured application controller-by-controller and bean-by-bean, rather than requiring a single disruptive rewrite of the entire configuration at once — new code is written the modern way immediately, while legacy configuration is ported opportunistically.

## 6. Walkthrough

**Startup: the Level 3 hybrid-configuration WAR deploying to Tomcat.**

1. The servlet container loads `WebAppInitializer` (a `ServletContainerInitializer` implementation Spring provides, auto-detected via `META-INF/services` — the modern replacement for `web.xml`'s `<servlet>` declarations). It calls `getServletConfigClasses()`, receiving `WebConfig.class`.
2. Spring creates an `AnnotationConfigWebApplicationContext` and processes `WebConfig`. `@EnableWebMvc` triggers `DelegatingWebMvcConfiguration`, registering the core MVC infrastructure — `RequestMappingHandlerMapping`, default `HttpMessageConverter`s, and so on — exactly as `<mvc:annotation-driven/>` would have in the pure-XML setup.
3. `@ComponentScan(basePackages = "com.example.app")` triggers classpath scanning, discovering `ReportController` (and any other `@Component`/`@RestController`/`@Service` classes) and registering them as beans.
4. `@ImportResource("classpath:WEB-INF/legacy-beans.xml")` is processed: Spring's `XmlBeanDefinitionReader` parses the XML file, registering `legacyReportGenerator` as a bean definition in the *same* application context as everything discovered by component scanning — there is no separate "XML context" and "Java context"; it's one unified bean registry.
5. Spring's dependency injection resolves `ReportController`'s constructor parameter (`ReportGenerator legacyReportGenerator`) by type, finds the XML-defined `legacyReportGenerator` bean, and injects it — the controller has no idea, and doesn't need to know, that this dependency's definition originated from XML rather than a `@Bean` method or `@Component` scan.

**Request: `GET /reports/1`.**

1. `DispatcherServlet` (registered by `WebAppInitializer`) receives the request, consults `RequestMappingHandlerMapping` (activated in step 2 above), and matches it to `ReportController.generate(1)`.
2. Inside the handler: `legacyReportGenerator.generate(1)` is called — this executes whatever logic the legacy `ReportGenerator` class contains, using its `templatePath` property (set via the XML `<property>` element back in step 4) to locate report templates under `/WEB-INF/reports/`.
3. The generated report content is returned as a plain `String` from the `@RestController` method — because the class is `@RestController`, this is written directly as the response body (see the `@RestController` card).
4. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/plain;charset=UTF-8

   <report content produced by the legacy generator>
   ```

## 7. Gotchas & takeaways

> **Mixing `<mvc:annotation-driven/>` in one XML file with `@EnableWebMvc` in a Java config class within the same application context registers MVC infrastructure twice**, which can cause confusing duplicate-bean or unexpected-override errors. During a migration, ensure only one of the two mechanisms is active for MVC infrastructure — use `@ImportResource` to pull in *non-MVC* legacy beans while `@EnableWebMvc` (in Java config) remains the single source of truth for MVC setup itself.

> **`<context:component-scan>`'s `base-package` attribute and `@ComponentScan`'s `basePackages` must cover the exact same packages when migrating**, or newly-added `@Component`/`@Controller` classes can silently fail to be discovered if the migration accidentally narrows the scanned package tree.

> **XML namespace elements (`<mvc:interceptors>`, `<mvc:resources>`, etc.) are documented individually in Spring's reference documentation with their own attributes and nested elements** — this card covers only `<mvc:annotation-driven/>` itself; the following cards in this series cover the Java-config equivalents for interceptors, resources, CORS, and other specific `<mvc:...>` elements in more depth.

- `<mvc:annotation-driven/>` is XML config's equivalent of `@EnableWebMvc` — both activate the same core MVC infrastructure.
- Every `<mvc:...>` XML element maps to a specific `WebMvcConfigurer` override method — useful as a mental translation table when migrating.
- `@ImportResource` lets a Java-configured application still incorporate remaining legacy XML bean definitions during an incremental migration.
- New projects should never introduce XML-based Spring MVC configuration — this knowledge is purely for maintaining or migrating existing legacy applications.
