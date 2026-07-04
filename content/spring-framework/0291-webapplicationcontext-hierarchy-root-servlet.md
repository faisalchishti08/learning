---
card: spring-framework
gi: 291
slug: webapplicationcontext-hierarchy-root-servlet
title: "WebApplicationContext Hierarchy: Root & Servlet"
---

## 1. What it is

A Spring web application typically uses **two nested `WebApplicationContext` instances**:

- **Root context** (parent): contains shared infrastructure beans — services, repositories, transaction managers, security config, data sources. Started by `ContextLoaderListener`.
- **Servlet context** (child): contains `DispatcherServlet`-specific beans — controllers, `HandlerMapping`, `ViewResolver`, `HandlerAdapter`. Started by `DispatcherServlet`.

```
Root WebApplicationContext
  (services, repos, @Transactional, DataSource …)
     ↑ parent lookup
Servlet WebApplicationContext
  (@Controller, ViewResolver, MVC config …)
```

Child context beans can see parent beans; parent context beans cannot see child beans.

## 2. Why & when

The hierarchy separates concerns:
- **Root context** is shared across the whole app — including multiple `DispatcherServlet` instances (e.g., API v1 and API v2), `ContextLoaderListener`-started integrations, and background jobs.
- **Servlet context** is specific to one `DispatcherServlet` — controllers and MVC config that should be isolated.

If you put a `@Service` in the servlet context, it's invisible to other servlets and to background threads started from the root context. Common mistake: `@Transactional` on a bean in the servlet context — the `PlatformTransactionManager` may be in the root context and the AOP proxy isn't applied correctly.

In modern Spring Boot apps, there's only **one application context** — no hierarchy. The root/servlet split is a pre-Spring-Boot pattern used with `web.xml` or `WebApplicationInitializer`.

## 3. Core concept

```
Container startup:
  1. ContextLoaderListener.contextInitialized()
      → creates Root WebApplicationContext (from context-param: contextClass/contextConfigLocation)
      → refreshes → beans created, @Transactional proxied, etc.
      → stored in: ServletContext attribute "org.springframework.web.context.WebApplicationContext.ROOT"

  2. DispatcherServlet.init()
      → creates Servlet WebApplicationContext
      → sets parent = root context
      → refreshes → @Controller beans, MVC strategy beans
      → stored in: ServletContext attribute "dispatcher.DISPATCHER_SERVLET_CONTEXT_ATTRIBUTE"

Lookup:
  childCtx.getBean("taskService")
    → not found in servlet ctx
    → delegates to parent (root ctx)
    → found: returns TaskService @Service bean

  rootCtx.getBean("taskController")
    → not found in root ctx
    → no parent to delegate to
    → throws NoSuchBeanDefinitionException
```

`WebApplicationContext` extends `ApplicationContext` and adds:
- `getServletContext()` — access to `jakarta.servlet.ServletContext`.
- `getServletConfig()` — access to `jakarta.servlet.ServletConfig` (servlet context only).

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Root context -->
  <rect x="10" y="10" width="680" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="35" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Root WebApplicationContext  (started by ContextLoaderListener)</text>
  <line x1="20" y1="42" x2="680" y2="42" stroke="#8b949e" stroke-width="0.5"/>
  <text x="350" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Service, @Repository, @Transactional, DataSource, TransactionManager, Security</text>
  <text x="350" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Visible to ALL child contexts and background threads</text>
  <text x="350" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Registered in ServletContext attribute under ROOT key</text>

  <!-- Connector arrow -->
  <line x1="350" y1="102" x2="350" y2="128" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="365" y="119" fill="#8b949e" font-size="8" font-family="sans-serif">parent lookup</text>

  <!-- Servlet context -->
  <rect x="60" y="130" width="560" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="153" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Servlet WebApplicationContext  (started by DispatcherServlet)</text>
  <line x1="70" y1="159" x2="610" y2="159" stroke="#8b949e" stroke-width="0.5"/>
  <text x="340" y="177" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Controller, @ControllerAdvice, HandlerMapping, ViewResolver, MVC config</text>
  <text x="340" y="193" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Visible only within this DispatcherServlet</text>
</svg>

## 5. Runnable example

Scenario: a **task management app** — demonstrate context hierarchy with a root service bean used by a servlet-context controller.

### Level 1 — Basic

Root context service + servlet context controller.

```java
// WebAppContextHierarchyDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

// === Root context beans ===
@Service
class TaskService {
    private final Map<Long,String> tasks = new LinkedHashMap<>();
    private long seq = 1;
    public long add(String title){ long id=seq++; tasks.put(id,title); return id; }
    public Map<Long,String> all(){ return Collections.unmodifiableMap(tasks); }
}

@Configuration @ComponentScan(basePackageClasses=TaskService.class)
class RootConfig {}

// === Servlet context beans ===
@RestController @RequestMapping("/tasks")
class TaskController {
    private final TaskService svc;  // bean from parent (root) context
    TaskController(TaskService s){ svc=s; }

    @GetMapping       public Map<Long,String> list() { return svc.all(); }
    @PostMapping("/{title}") public long create(@PathVariable String title) { return svc.add(title); }
}

@Configuration @EnableWebMvc @ComponentScan(basePackageClasses=TaskController.class)
class WebConfig {}

// Programmatic hierarchy setup (simulated for demo)
public class WebAppContextHierarchyDemo {
    public static void main(String[] args) {
        // Root context
        var root = new org.springframework.context.annotation.AnnotationConfigApplicationContext(RootConfig.class);
        System.out.println("Root context beans: " + Arrays.toString(
            Arrays.stream(root.getBeanDefinitionNames())
                  .filter(n->!n.startsWith("org."))
                  .toArray()));

        // Simulate servlet context as child
        var servlet = new org.springframework.context.annotation.AnnotationConfigApplicationContext();
        servlet.setParent(root);
        servlet.register(WebConfig.class);
        servlet.refresh();
        System.out.println("Servlet context beans: " + Arrays.toString(
            Arrays.stream(servlet.getBeanDefinitionNames())
                  .filter(n->!n.startsWith("org."))
                  .toArray()));

        // Controller in servlet context can see TaskService from root context
        TaskController ctrl = servlet.getBean(TaskController.class);
        System.out.println("Controller got TaskService from root: " + ctrl.list());

        // Root context cannot see controller
        try {
            root.getBean(TaskController.class);
        } catch (org.springframework.beans.factory.NoSuchBeanDefinitionException e) {
            System.out.println("Root cannot see controller: " + e.getClass().getSimpleName());
        }

        servlet.close(); root.close();
    }
}
```

How to run: `java -cp spring-webmvc.jar:spring-context.jar:spring-web.jar:jackson-databind.jar:jakarta.servlet-api.jar:. WebAppContextHierarchyDemo.java`

Setting `servlet.setParent(root)` replicates what `DispatcherServlet` does internally when a root context is present. `TaskController` finds `TaskService` via parent-context delegation. `root.getBean(TaskController.class)` throws — parent context cannot look up child beans.

---

### Level 2 — Intermediate

`WebApplicationInitializer` wiring — explicit `ContextLoaderListener` + `DispatcherServlet`.

```java
// WebAppContextHierarchyDemo.java
import jakarta.servlet.*;
import org.springframework.context.annotation.*;
import org.springframework.web.*;
import org.springframework.web.context.*;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.servlet.DispatcherServlet;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import java.util.*;

// Root beans
@Repository
class TaskRepository {
    private final Map<Long,String> store = new LinkedHashMap<>();
    private long seq = 1;
    public long save(String t){ long id=seq++; store.put(id,t); return id; }
    public Map<Long,String> findAll(){ return Map.copyOf(store); }
}

@Service
class TaskService2 {
    private final TaskRepository repo;
    TaskService2(TaskRepository r){ repo=r; }
    public long addTask(String title){ return repo.save(title); }
    public Map<Long,String> getTasks(){ return repo.findAll(); }
}

@Configuration
@ComponentScan(basePackageClasses = {TaskRepository.class, TaskService2.class})
class RootConfig2 {}

// Servlet beans
@RestController @RequestMapping("/api/tasks")
class TaskApiController {
    private final TaskService2 svc;
    TaskApiController(TaskService2 s){ svc=s; }
    @GetMapping              public Map<Long,String> list() { return svc.getTasks(); }
    @PostMapping("/{title}") public long add(@PathVariable String title){ return svc.addTask(title); }
}

@Configuration @EnableWebMvc @ComponentScan(basePackageClasses = TaskApiController.class)
class WebConfig3 {}

// WebApplicationInitializer: replaces web.xml
class MyWebAppInit implements WebApplicationInitializer {
    @Override
    public void onStartup(ServletContext sc) throws ServletException {
        // Root context
        var rootCtx = new AnnotationConfigWebApplicationContext();
        rootCtx.register(RootConfig2.class);
        sc.addListener(new ContextLoaderListener(rootCtx));  // starts + stops root ctx

        // Servlet context
        var servletCtx = new AnnotationConfigWebApplicationContext();
        servletCtx.register(WebConfig3.class);
        // DispatcherServlet sets parent = rootCtx automatically (WebApplicationContextUtils)
        var ds = new DispatcherServlet(servletCtx);
        var reg = sc.addServlet("dispatcher", ds);
        reg.setLoadOnStartup(1);
        reg.addMapping("/");
    }
}

public class WebAppContextHierarchyDemo {
    public static void main(String[] args) {
        System.out.println("With ContextLoaderListener:");
        System.out.println("  Root context starts first (RootConfig2) — TaskRepository, TaskService2");
        System.out.println("  DispatcherServlet starts second (WebConfig3) — TaskApiController");
        System.out.println("  DispatcherServlet.init() calls WebApplicationContextUtils.initWebApplicationContext()");
        System.out.println("  which finds the root ctx in ServletContext → sets it as parent of servlet ctx");
    }
}
```

How to run: deploy to embedded Tomcat

`ContextLoaderListener` detects `AnnotationConfigWebApplicationContext` registered under `WebApplicationContext.ROOT_WEB_APPLICATION_CONTEXT_ATTRIBUTE` in `ServletContext`. `DispatcherServlet.init()` calls `WebApplicationContextUtils.initWebApplicationContext(sc)` which retrieves the root context and sets it as the parent.

---

### Level 3 — Advanced

Two `DispatcherServlet` instances sharing one root context.

```java
// WebAppContextHierarchyDemo.java (concept)
import jakarta.servlet.*;
import org.springframework.context.annotation.*;
import org.springframework.web.*;
import org.springframework.web.context.*;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.servlet.DispatcherServlet;

// Shared root: services, repos
@Configuration @ComponentScan(basePackageClasses = {TaskRepository.class, TaskService2.class})
class SharedRootConfig {}

// Servlet 1: public API
@Configuration @EnableWebMvc @ComponentScan(basePackageClasses = TaskApiController.class)
class PublicApiConfig {}

// Servlet 2: admin API (different controllers, same underlying services)
@RestController @RequestMapping("/admin/tasks")
class AdminTaskController {
    private final TaskService2 svc;
    AdminTaskController(TaskService2 s){ svc=s; }
    @org.springframework.web.bind.annotation.GetMapping
    public String info(){ return "Admin: " + svc.getTasks().size() + " tasks"; }
}

@Configuration @EnableWebMvc @ComponentScan(basePackageClasses = AdminTaskController.class)
class AdminConfig {}

class MultiServletInit implements WebApplicationInitializer {
    @Override
    public void onStartup(ServletContext sc) throws ServletException {
        // Shared root context
        var root = new AnnotationConfigWebApplicationContext(); root.register(SharedRootConfig.class);
        sc.addListener(new ContextLoaderListener(root));

        // Public API servlet — /api/*
        var apiCtx = new AnnotationConfigWebApplicationContext(); apiCtx.register(PublicApiConfig.class);
        var api = new DispatcherServlet(apiCtx);
        var r1 = sc.addServlet("api", api); r1.setLoadOnStartup(1); r1.addMapping("/api/*");

        // Admin servlet — /admin/*
        var adminCtx = new AnnotationConfigWebApplicationContext(); adminCtx.register(AdminConfig.class);
        var admin = new DispatcherServlet(adminCtx);
        var r2 = sc.addServlet("admin", admin); r2.setLoadOnStartup(2); r2.addMapping("/admin/*");
    }
}

public class WebAppContextHierarchyDemo {
    public static void main(String[] args) {
        System.out.println("Two DispatcherServlets, one shared root:");
        System.out.println("  Root: TaskRepository, TaskService2");
        System.out.println("  /api/*  → PublicApiConfig  → TaskApiController  (uses TaskService2 from root)");
        System.out.println("  /admin/* → AdminConfig     → AdminTaskController (uses TaskService2 from root)");
        System.out.println("  Each servlet has its own child context; both share the root context.");
    }
}
```

How to run: deploy to embedded Tomcat

Both `DispatcherServlet` instances find `TaskService2` from the shared root context via parent delegation. Admin controllers are isolated to `/admin/*` and invisible to the public API servlet context — and vice versa.

## 6. Walkthrough

**Level 1 — `servlet.getBean(TaskController.class)` lookup:**

1. `servlet.getBean(TaskController.class)` → search own bean definitions.
2. `TaskController` found in servlet context (registered via `@ComponentScan`) → returns instance.
3. `TaskController` constructor injection: needs `TaskService`.
4. `TaskService` NOT in servlet context → parent delegation → root context.
5. `root.getBean(TaskService.class)` → found → returned to servlet context.
6. `TaskController` created with injected `TaskService` from root context.

**`root.getBean(TaskController.class)` → `NoSuchBeanDefinitionException`:**
Root context has no parent; `TaskController` not in its definitions; throws immediately.

## 7. Gotchas & takeaways

> **Putting `@Service` beans in the servlet context works but breaks multi-servlet sharing.** If your service is in the servlet context, a second `DispatcherServlet` or a `ContextLoaderListener`-loaded job scheduler can't access it. Always put services/repositories in the root context.

> **`@Transactional` in the servlet context misses the AOP proxy** if `<tx:annotation-driven/>` or `@EnableTransactionManagement` is configured in the root context. AOP proxy creation happens at refresh time in the context where `@EnableTransactionManagement` is declared. Put transactional beans and transaction management config in the same (root) context.

> **Spring Boot merges root + servlet contexts into a single context.** There's no hierarchy in Spring Boot. This is fine for single-app deployments; the hierarchy exists for legacy multi-servlet / multi-war deployments.

- Root context = parent; servlet context = child.
- Child sees parent beans; parent cannot see child beans.
- Services/repos/tx config → root context. Controllers/MVC config → servlet context.
- `ContextLoaderListener` starts root; `DispatcherServlet` starts child; child auto-detects root as parent.
- Spring Boot uses one unified context — no hierarchy needed.
