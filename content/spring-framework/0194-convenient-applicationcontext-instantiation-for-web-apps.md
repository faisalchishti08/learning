---
card: spring-framework
gi: 194
slug: convenient-applicationcontext-instantiation-for-web-apps
title: "Convenient ApplicationContext instantiation for web apps"
---

## 1. What it is

Spring provides `WebApplicationContext` and its loading infrastructure so that a web application automatically creates and destroys a Spring container alongside the servlet lifecycle. Rather than manually calling `new AnnotationConfigApplicationContext(...)`, a web app declares `ContextLoaderListener` (or lets Spring Boot's `SpringApplication` do it) and Spring starts the context at servlet-container startup.

```xml
<!-- web.xml (traditional) -->
<listener>
  <listener-class>org.springframework.web.context.ContextLoaderListener</listener-class>
</listener>
<context-param>
  <param-name>contextClass</param-name>
  <param-value>org.springframework.web.context.support.AnnotationConfigWebApplicationContext</param-value>
</context-param>
<context-param>
  <param-name>contextConfigLocation</param-name>
  <param-value>com.example.AppConfig</param-value>
</context-param>
```

Or programmatically (Servlet 3.0+ without `web.xml`):

```java
// Implements WebApplicationInitializer — detected by SpringServletContainerInitializer via SPI
public class AppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer {
    @Override protected Class<?>[] getRootConfigClasses()   { return new Class[]{RootConfig.class}; }
    @Override protected Class<?>[] getServletConfigClasses(){ return new Class[]{WebMvcConfig.class}; }
    @Override protected String[]   getServletMappings()     { return new String[]{"/"}; }
}
```

Spring Boot replaces all of this with `SpringApplication.run()` — it auto-creates `AnnotationConfigServletWebServerApplicationContext` and embeds Tomcat/Jetty/Undertow.

## 2. Why & when

- **Traditional WAR deployment** — `ContextLoaderListener` + `web.xml` or `WebApplicationInitializer` is the standard approach for Spring MVC apps deployed to external servlet containers (Tomcat, WildFly, Jetty).
- **Root + child context hierarchy** — a root `WebApplicationContext` holds service/repository beans; `DispatcherServlet` creates a child context for MVC beans (controllers, view resolvers). Beans in child can see parent but not vice versa.
- **Servlet 3.0 no-XML** — `AbstractAnnotationConfigDispatcherServletInitializer` is the zero-`web.xml` alternative, detected via Java SPI.
- **Spring Boot** eliminates all of this; use `SpringApplication.run()` — context creation is fully automatic.
- **Don't use** `ContextLoaderListener` in a Spring Boot app — Boot's embedded server sets up the context differently; manually adding `ContextLoaderListener` would create a duplicate context.

## 3. Core concept

A web app can have a **context hierarchy**:

```
Root WebApplicationContext           ← ContextLoaderListener creates at app startup
  ├── Services, Repositories, DataSource beans
  └── shared by all servlets
       ↓ parent
  Servlet WebApplicationContext      ← DispatcherServlet creates per-servlet
    ├── Controllers, ViewResolvers, HandlerMappings
    └── can see root context beans, but root cannot see servlet-level beans
```

**Loading chain:**

1. `ContextLoaderListener.contextInitialized(ServletContextEvent)` — Spring's `ServletContextListener`; reads `contextConfigLocation` and `contextClass` params; creates and refreshes the root `ApplicationContext`; stores it in `ServletContext` attribute.
2. `DispatcherServlet.init()` — each `DispatcherServlet` creates its own child `WebApplicationContext`, sets the root as parent, refreshes.

**`WebApplicationContext` implementations:**

| Class | Config style |
|---|---|
| `XmlWebApplicationContext` | XML `<beans/>` (classic) |
| `AnnotationConfigWebApplicationContext` | `@Configuration` classes or component-scan packages |

**Programmatic (no web.xml) via `WebApplicationInitializer`:**
`SpringServletContainerInitializer` is a `javax.servlet.ServletContainerInitializer` registered via SPI in `spring-web.jar`. The container calls it at startup; it discovers all `WebApplicationInitializer` implementations on the classpath and delegates to them.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="waia" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="waib" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Servlet Container -->
  <rect x="5" y="5" width="690" height="185" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="20" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Servlet Container (Tomcat / Jetty)</text>

  <!-- Root Context -->
  <rect x="20" y="30" width="290" height="145" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="165" y="48" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Root WebApplicationContext</text>
  <text x="165" y="64" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Created by ContextLoaderListener</text>
  <text x="165" y="78" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Stores in ServletContext attribute</text>
  <rect x="35" y="88" width="260" height="75" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1" opacity="0.7"/>
  <text x="165" y="104" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Services, Repositories</text>
  <text x="165" y="118" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">DataSource, TransactionManager</text>
  <text x="165" y="132" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Security beans</text>
  <text x="165" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(shared by all DispatcherServlets)</text>

  <!-- Servlet Context -->
  <rect x="370" y="30" width="305" height="145" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="522" y="48" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Servlet WebApplicationContext</text>
  <text x="522" y="64" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Created by DispatcherServlet.init()</text>
  <text x="522" y="78" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Parent = Root context</text>
  <rect x="385" y="88" width="275" height="75" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1" opacity="0.7"/>
  <text x="522" y="104" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Controllers, ViewResolvers</text>
  <text x="522" y="118" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">HandlerMappings, MessageConverters</text>
  <text x="522" y="132" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">MVC-specific beans</text>
  <text x="522" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(can see root beans; root cannot see these)</text>

  <!-- Parent arrow -->
  <line x1="312" y1="100" x2="368" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#waib)" stroke-dasharray="4 3"/>
  <text x="340" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">parent</text>
</svg>

Root context holds shared beans; each `DispatcherServlet` owns a child context for MVC beans. Child can see root; root cannot see child.

## 5. Runnable example

Scenario: **product catalogue web service** — root context loads services; MVC context loads controllers.

### Level 1 — Basic

Programmatic `AnnotationConfigWebApplicationContext` without a servlet container — simulates what `ContextLoaderListener` does.

```java
// WebContextBasic.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.web.context.support.*;
import org.springframework.stereotype.*;

// Root configuration (service layer)
@Configuration @ComponentScan("services")
class RootConfig { }

// Simulate a service bean
@org.springframework.stereotype.Service
class ProductService {
    public String describe(String sku) { return "Product[" + sku + "] — available"; }
}

public class WebContextBasic {
    public static void main(String[] args) {
        // AnnotationConfigWebApplicationContext is the annotation-based web context
        var rootCtx = new AnnotationConfigWebApplicationContext();
        rootCtx.register(RootConfig.class);
        rootCtx.scan("com.example"); // or inline — just demonstrate the API
        rootCtx.refresh();

        System.out.println("Root context started: " + rootCtx.getDisplayName());
        System.out.println("Active profiles: " + java.util.Arrays.toString(rootCtx.getEnvironment().getActiveProfiles()));

        // Simulate service lookup
        var svc = new ProductService();
        System.out.println(svc.describe("SKU-001"));

        rootCtx.close();
        System.out.println("Context closed.");
    }
}
```

How to run: `java WebContextBasic.java`

`AnnotationConfigWebApplicationContext` is the programmatic equivalent of what `ContextLoaderListener` creates when `contextClass=AnnotationConfigWebApplicationContext` is set in `web.xml`. Unlike `AnnotationConfigApplicationContext`, it implements `ConfigurableWebApplicationContext` with `setServletContext()` support.

### Level 2 — Intermediate

Root + child context hierarchy demonstrating bean visibility rules.

```java
// WebContextIntermediate.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.web.context.support.*;
import org.springframework.stereotype.*;

// Root: services (shared across servlets)
@Configuration
class RootCfg {
    @Bean ProductRepo productRepo() { return new ProductRepo(); }
    @Bean ProductSvc  productSvc()  { return new ProductSvc(productRepo()); }
}

class ProductRepo {
    String find(String sku) { return "Fetched:" + sku; }
}

class ProductSvc {
    private final ProductRepo repo;
    ProductSvc(ProductRepo repo) { this.repo = repo; }
    public String get(String sku) { return repo.find(sku); }
}

// Child: controllers (see root beans; root does not see these)
@Configuration
class ChildCfg {
    // Controller can autowire ProductSvc from parent context
    @Bean ProductController controller(ProductSvc svc) {
        return new ProductController(svc);
    }
}

class ProductController {
    private final ProductSvc svc;
    ProductController(ProductSvc svc) { this.svc = svc; }
    public String handleGet(String sku) {
        return "[Controller] " + svc.get(sku);
    }
}

public class WebContextIntermediate {
    public static void main(String[] args) {
        // Root context
        var rootCtx = new AnnotationConfigWebApplicationContext();
        rootCtx.register(RootCfg.class);
        rootCtx.refresh();
        System.out.println("Root beans: " + java.util.Arrays.toString(
            rootCtx.getBeanDefinitionNames()));

        // Child context — root is parent
        var childCtx = new AnnotationConfigWebApplicationContext();
        childCtx.setParent(rootCtx);
        childCtx.register(ChildCfg.class);
        childCtx.refresh();

        var ctrl = childCtx.getBean(ProductController.class);
        System.out.println(ctrl.handleGet("SKU-7"));

        // Root cannot see child beans
        System.out.println("Root has 'controller': "
            + rootCtx.containsBean("controller"));
        // Child CAN see root beans
        System.out.println("Child has 'productSvc': "
            + childCtx.containsBean("productSvc"));

        childCtx.close();
        rootCtx.close();
    }
}
```

How to run: `java WebContextIntermediate.java`

`childCtx.setParent(rootCtx)` wires the parent chain. `ChildCfg` autowires `ProductSvc` which is defined in the parent — Spring resolves it via the parent context. `rootCtx.containsBean("controller")` returns `false`; `childCtx.containsBean("productSvc")` returns `true`.

### Level 3 — Advanced

`WebApplicationInitializer`-based no-XML setup (for WAR deployment) — the full production pattern.

```java
// WebContextAdvanced.java  (for a WAR project; Spring Boot replaces this)
import org.springframework.web.WebApplicationInitializer;
import org.springframework.web.context.*;
import org.springframework.web.context.support.*;
import org.springframework.web.servlet.*;
import javax.servlet.*;

// Detected via SPI by SpringServletContainerInitializer at container startup
public class WebContextAdvanced implements WebApplicationInitializer {

    @Override
    public void onStartup(ServletContext servletContext) throws ServletException {

        // 1. Create root WebApplicationContext
        var rootCtx = new AnnotationConfigWebApplicationContext();
        rootCtx.register(RootConfig.class);      // services, repositories, security

        // 2. Register ContextLoaderListener — starts root context on app init
        servletContext.addListener(new ContextLoaderListener(rootCtx));

        // 3. Create DispatcherServlet with its own child context
        var dispatcherCtx = new AnnotationConfigWebApplicationContext();
        dispatcherCtx.register(WebMvcConfig.class);   // controllers, view resolvers

        var dispatcher = new DispatcherServlet(dispatcherCtx);
        var registration = servletContext.addServlet("dispatcher", dispatcher);
        registration.setLoadOnStartup(1);
        registration.addMapping("/");

        System.out.println("App initialised: root + dispatcher contexts registered.");
    }
}

// Standalone demo (demonstrates the API without a real servlet container)
class StandaloneDemo {
    public static void main(String[] args) {
        // Show equivalent manual wiring
        var root = new AnnotationConfigWebApplicationContext();
        root.register(RootConfig.class);
        root.refresh();

        var child = new AnnotationConfigWebApplicationContext();
        child.setParent(root);
        // child.register(WebMvcConfig.class);  // would need Spring MVC deps
        child.refresh();

        System.out.println("Root context:  " + root.getDisplayName());
        System.out.println("Child context: " + child.getDisplayName());
        System.out.println("Child parent:  " + child.getParent().getDisplayName());

        child.close();
        root.close();
    }
}

@Configuration class RootConfig { }
@Configuration class WebMvcConfig { }

public class WebContextAdvanced {
    public static void main(String[] args) { StandaloneDemo.main(args); }
}
```

How to run (standalone): `java WebContextAdvanced.java`. For WAR: deploy to Tomcat 9+ — `SpringServletContainerInitializer` detects `WebApplicationInitializer` via SPI.

`WebApplicationInitializer.onStartup()` is called by the container at deployment. Steps: create root context → register `ContextLoaderListener` → create `DispatcherServlet` with its own child context → register servlet mapping. This replaces `web.xml` entirely for Servlet 3.0+ containers.

## 6. Walkthrough

Tracing a WAR startup with `WebContextAdvanced`:

**Step 1 — Container startup detects `SpringServletContainerInitializer`** via `META-INF/services/javax.servlet.ServletContainerInitializer` in `spring-web.jar`.

**Step 2 — `SpringServletContainerInitializer.onStartup` scans classpath** for classes implementing `WebApplicationInitializer`. Finds `WebContextAdvanced`.

**Step 3 — `WebContextAdvanced.onStartup(servletContext)` called:**
- Creates `rootCtx` (AnnotationConfigWebApplicationContext) registered with `RootConfig`.
- Adds `ContextLoaderListener(rootCtx)` to `servletContext`.

**Step 4 — Servlet container fires `ServletContextListener.contextInitialized`:**
- `ContextLoaderListener.contextInitialized` called.
- Calls `rootCtx.refresh()` — loads service and repository beans.
- Stores context in `servletContext.setAttribute("ROOT_WEB_APPLICATION_CONTEXT_ATTRIBUTE", rootCtx)`.

**Step 5 — `DispatcherServlet` initialises (loadOnStartup=1):**
- Creates `dispatcherCtx` with `WebMvcConfig`.
- Retrieves root context from `ServletContext`.
- Sets root as parent of `dispatcherCtx`.
- Calls `dispatcherCtx.refresh()` — loads MVC beans; controller beans can see root beans.

**Step 6 — App serves requests.** Each HTTP request goes through `DispatcherServlet`, which uses beans from `dispatcherCtx` (and root via parent chain).

**Shutdown:** container fires `contextDestroyed` → `ContextLoaderListener` calls `rootCtx.close()`.

## 7. Gotchas & takeaways

> **Don't use `ContextLoaderListener` in a Spring Boot application.** Spring Boot creates and manages the `ApplicationContext` itself via `SpringApplication`. Adding `ContextLoaderListener` creates a second, parallel context — bean definitions are duplicated, beans are initialised twice, and lifecycle is broken.

> **Root vs child context bean visibility is one-way.** A `@Controller` bean in the child context can inject a `@Service` from the root, but a `@Service` in the root cannot inject a `@Controller` from the child. If you accidentally define a `@Service` in `WebMvcConfig` (child) and try to use it from the root, it won't be found.

- **`AbstractAnnotationConfigDispatcherServletInitializer`** is the convenience superclass — override `getRootConfigClasses()` and `getServletConfigClasses()` for the common case without manually wiring `ContextLoaderListener` and `DispatcherServlet`.
- **Spring Boot equivalent:** `SpringApplication.run(App.class)` auto-creates `AnnotationConfigServletWebServerApplicationContext`, starts the embedded server, and manages the full lifecycle. The root/child context split still exists internally but is handled by `DispatcherServletRegistrationBean`.
- **Multiple `DispatcherServlet` instances:** each can have its own child context with separate MVC configuration (e.g., one for REST API, one for HTML views). Both share the same root context beans.
- **`contextConfigLocation` parameter:** in `web.xml`, this is a comma/whitespace-separated list of configuration classes (for `AnnotationConfigWebApplicationContext`) or XML files (for `XmlWebApplicationContext`).
