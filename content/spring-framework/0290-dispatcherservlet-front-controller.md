---
card: spring-framework
gi: 290
slug: dispatcherservlet-front-controller
title: "DispatcherServlet: Front Controller"
---

## 1. What it is

`DispatcherServlet` is Spring MVC's **front controller** — a single `HttpServlet` registered at the root URL (`/`) that centralises all request routing, handler invocation, exception handling, and response writing for a Spring web application.

```java
// Registered programmatically (no web.xml)
public class WebAppInitializer extends AbstractAnnotationConfigDispatcherServletInitializer {
    @Override protected Class<?>[] getRootConfigClasses() { return new Class[]{RootConfig.class}; }
    @Override protected Class<?>[] getServletConfigClasses() { return new Class[]{WebConfig.class}; }
    @Override protected String[] getServletMappings() { return new String[]{"/"}; }
}
```

On startup, `DispatcherServlet` creates its own `WebApplicationContext` and discovers its **strategy beans** (HandlerMapping, HandlerAdapter, ViewResolver, etc.) — either from your `@Configuration` classes or from the defaults defined in `DispatcherServlet.properties`.

## 2. Why & when

Without a front controller, every URL needs its own `Servlet` or `Filter`. Request dispatch, error handling, and content-negotiation logic are duplicated everywhere.

`DispatcherServlet` centralises:
- URL-to-handler mapping (`HandlerMapping`).
- Handler invocation (`HandlerAdapter`) — including parameter binding, data binding, validation.
- Exception handling (`HandlerExceptionResolver`).
- View resolution (`ViewResolver`) and rendering.
- Content negotiation (`ContentNegotiationManager`).

Every Spring MVC application has at least one `DispatcherServlet`. Spring Boot registers one automatically at `/` via `DispatcherServletAutoConfiguration`.

## 3. Core concept

Request processing pipeline (executed by `DispatcherServlet.doDispatch()`):

```
HttpServletRequest
  ↓
1. ApplicationEvent: RequestHandledEvent (fired on completion)
2. LocaleResolver.resolveLocale()     → request locale for i18n
3. ThemeResolver.resolveTheme()       → theme (rarely used)
4. HandlerMapping.getHandler()        → HandlerExecutionChain
     (Handler + list of HandlerInterceptors)
5. HandlerInterceptor.preHandle()     → may abort
6. HandlerAdapter.handle()            → ModelAndView (or writes response directly)
     includes: argument resolvers, return value handlers, data binding, @Valid
7. HandlerInterceptor.postHandle()    → may modify ModelAndView
8. If exception: HandlerExceptionResolver.resolveException()
9. ViewResolver.resolveViewName()     → View
10. View.render(model, request, response) → writes to HttpServletResponse
11. HandlerInterceptor.afterCompletion()
```

Strategy beans (`DispatcherServlet.properties` defaults):
```
HandlerMapping:         RequestMappingHandlerMapping   (reads @RequestMapping)
HandlerAdapter:         RequestMappingHandlerAdapter   (invokes @RequestMapping methods)
HandlerExceptionResolver: ExceptionHandlerExceptionResolver (@ControllerAdvice)
ViewResolver:           InternalResourceViewResolver   (JSP / Thymeleaf if configured)
LocaleResolver:         AcceptHeaderLocaleResolver
```

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Client -->
  <rect x="5" y="93" width="65" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="37" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Client</text>
  <line x1="72" y1="110" x2="100" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DispatcherServlet box -->
  <rect x="102" y="30" width="430" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="317" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">DispatcherServlet</text>
  <line x1="112" y1="58" x2="522" y2="58" stroke="#8b949e" stroke-width="0.5"/>

  <!-- Steps inside -->
  <text x="122" y="78" fill="#8b949e" font-size="8" font-family="monospace">1. HandlerMapping</text>
  <text x="122" y="93" fill="#8b949e" font-size="8" font-family="monospace">2. HandlerInterceptor.preHandle</text>
  <text x="122" y="108" fill="#8b949e" font-size="8" font-family="monospace">3. HandlerAdapter.handle()</text>
  <text x="122" y="123" fill="#8b949e" font-size="8" font-family="monospace">4. HandlerInterceptor.postHandle</text>
  <text x="122" y="138" fill="#8b949e" font-size="8" font-family="monospace">5. ExceptionResolver (if exception)</text>
  <text x="122" y="153" fill="#8b949e" font-size="8" font-family="monospace">6. ViewResolver / @ResponseBody</text>
  <text x="122" y="168" fill="#8b949e" font-size="8" font-family="monospace">7. afterCompletion</text>

  <!-- Arrow to controller -->
  <line x1="448" y1="108" x2="490" y2="108" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Controller -->
  <rect x="537" y="80" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="612" y="101" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@Controller</text>
  <text x="612" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@RequestMapping</text>
  <text x="612" y="129" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">returns view / body</text>

  <!-- Response arrow -->
  <line x1="537" y1="150" x2="72" y2="130" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="300" y="185" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">HttpServletResponse written → back to client</text>
</svg>

## 5. Runnable example

Scenario: a **task tracker** — build a Spring MVC app with `DispatcherServlet` wiring at three levels.

### Level 1 — Basic

Programmatic `DispatcherServlet` registration and a minimal `@Controller`.

```java
// DispatcherServletDemo.java
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.context.annotation.*;
import org.springframework.web.WebApplicationInitializer;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.bind.annotation.*;
import java.io.*;
import java.util.*;

record Task(long id, String title) {}

@RestController @RequestMapping("/tasks")
class TaskController {
    private final Map<Long,Task> db = new LinkedHashMap<>();
    private long seq = 1;

    @GetMapping                   public Collection<Task> list() { return db.values(); }
    @PostMapping                  public Task create(@RequestBody Task t) {
        Task saved = new Task(seq++, t.title()); db.put(saved.id(), saved); return saved; }
    @GetMapping("/{id}")          public Task get(@PathVariable long id) { return db.get(id); }
    @DeleteMapping("/{id}")       public void delete(@PathVariable long id) { db.remove(id); }
}

@Configuration @EnableWebMvc @ComponentScan
class WebConfig {}

// WebApplicationInitializer is detected by SpringServletContainerInitializer (SCI)
// and called by the Servlet container during startup instead of web.xml
class AppInit implements WebApplicationInitializer {
    @Override
    public void onStartup(ServletContext ctx) {
        var webCtx = new AnnotationConfigWebApplicationContext();
        webCtx.register(WebConfig.class);

        // Register DispatcherServlet
        var ds = new DispatcherServlet(webCtx);
        var reg = ctx.addServlet("dispatcher", ds);
        reg.setLoadOnStartup(1);
        reg.addMapping("/");   // map to all URLs
    }
}

public class DispatcherServletDemo {
    public static void main(String[] args) {
        System.out.println("Deploy to embedded Tomcat to test:");
        System.out.println("  POST /tasks  {\"id\":0,\"title\":\"Buy milk\"}  → {\"id\":1,\"title\":\"Buy milk\"}");
        System.out.println("  GET  /tasks                               → [{\"id\":1,...}]");
        System.out.println("  DispatcherServlet maps '/' → routes all requests to registered handlers.");
    }
}
```

How to run: `java -cp spring-webmvc.jar:spring-context.jar:spring-web.jar:jackson-databind.jar:jakarta.servlet-api.jar:tomcat-embed-core.jar:. DispatcherServletDemo.java`

`DispatcherServlet` is created with a `WebApplicationContext`. The `WebApplicationInitializer` is the Java-code replacement for `web.xml`. The mapping `"/"` routes ALL requests through `DispatcherServlet`.

---

### Level 2 — Intermediate

`WebApplicationContext` hierarchy — separate root and servlet contexts.

```java
// DispatcherServletDemo.java (concept + code excerpt)
import org.springframework.context.annotation.*;
import org.springframework.web.WebApplicationInitializer;
import org.springframework.web.context.ContextLoaderListener;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.servlet.DispatcherServlet;
import jakarta.servlet.*;

// Root context: services, repositories, transactional beans
@Configuration @ComponentScan(basePackages = "com.example.service")
class RootConfig {}

// Servlet context: controllers, MVC config
@Configuration @EnableWebMvc @ComponentScan(basePackages = "com.example.web")
class WebConfig2 {}

class AppInit2 implements WebApplicationInitializer {
    @Override
    public void onStartup(ServletContext sc) {
        // 1. Root context (parent) — loaded by ContextLoaderListener
        var rootCtx = new AnnotationConfigWebApplicationContext();
        rootCtx.register(RootConfig.class);
        sc.addListener(new ContextLoaderListener(rootCtx));

        // 2. Servlet context (child) — loaded by DispatcherServlet
        var servletCtx = new AnnotationConfigWebApplicationContext();
        servletCtx.register(WebConfig2.class);

        var ds = new DispatcherServlet(servletCtx);  // child ctx; rootCtx = parent
        var reg = sc.addServlet("dispatcher", ds);
        reg.setLoadOnStartup(1);
        reg.addMapping("/");
    }
}

public class DispatcherServletDemo {
    public static void main(String[] args) {
        System.out.println("Context hierarchy:");
        System.out.println("  Root context (RootConfig):   service beans, repositories, TX config");
        System.out.println("  Servlet context (WebConfig): controllers, MVC beans");
        System.out.println("  Servlet ctx can see root ctx beans; root ctx CANNOT see servlet ctx beans.");
        System.out.println("  DispatcherServlet uses the servlet context for handler discovery.");
    }
}
```

How to run: same classpath

`ContextLoaderListener` starts the root `WebApplicationContext`. `DispatcherServlet` creates the child servlet `WebApplicationContext`. The child can access root beans (services, repositories) via parent delegation. Controllers should stay in the servlet context; services in the root context.

---

### Level 3 — Advanced

Multiple `DispatcherServlet` instances for API versioning.

```java
// DispatcherServletDemo.java (concept)
import org.springframework.context.annotation.*;
import org.springframework.web.WebApplicationInitializer;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.servlet.DispatcherServlet;
import jakarta.servlet.*;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/v1/products")
class ProductControllerV1 {
    @GetMapping public String list() { return "v1: Widget, Gadget"; }
}

@RestController @RequestMapping("/v2/products")
class ProductControllerV2b {
    @GetMapping public String list() { return "[{\"name\":\"Widget\"},{\"name\":\"Gadget\"}]"; }
}

@Configuration @EnableWebMvc @ComponentScan(basePackageClasses = ProductControllerV1.class)
class WebConfigV1 {}

@Configuration @EnableWebMvc @ComponentScan(basePackageClasses = ProductControllerV2b.class)
class WebConfigV2 {}

class MultiDispatcherInit implements WebApplicationInitializer {
    @Override
    public void onStartup(ServletContext sc) {
        // Servlet 1 — handles /v1/*
        var ctx1 = new AnnotationConfigWebApplicationContext(); ctx1.register(WebConfigV1.class);
        var ds1 = new DispatcherServlet(ctx1);
        var r1 = sc.addServlet("v1", ds1); r1.setLoadOnStartup(1); r1.addMapping("/v1/*");

        // Servlet 2 — handles /v2/*
        var ctx2 = new AnnotationConfigWebApplicationContext(); ctx2.register(WebConfigV2.class);
        var ds2 = new DispatcherServlet(ctx2);
        var r2 = sc.addServlet("v2", ds2); r2.setLoadOnStartup(2); r2.addMapping("/v2/*");
    }
}

public class DispatcherServletDemo {
    public static void main(String[] args) {
        System.out.println("Two DispatcherServlet instances:");
        System.out.println("  /v1/*  → v1 dispatcher → WebConfigV1 context → ProductControllerV1");
        System.out.println("  /v2/*  → v2 dispatcher → WebConfigV2 context → ProductControllerV2");
        System.out.println("Each has its own WebApplicationContext and strategy beans.");
        System.out.println("URL pattern-based routing directs traffic to the correct dispatcher.");
    }
}
```

How to run: same classpath + servlet container

Multiple `DispatcherServlet` instances are valid. Each has its own `WebApplicationContext` with its own set of controllers and MVC beans. Servlet container URL pattern-based routing (`/v1/*` vs `/v2/*`) directs traffic to the correct dispatcher before it even reaches Spring.

## 6. Walkthrough

**Level 1 — `POST /tasks` execution path:**

1. HTTP `POST /tasks` with body `{"id":0,"title":"Buy milk"}` → Tomcat.
2. Tomcat finds `DispatcherServlet` mapped to `/` → calls `ds.service(request, response)`.
3. `DispatcherServlet.doDispatch(request, response)`:
   - `getHandler(request)` → `RequestMappingHandlerMapping` → finds `TaskController.create()` for `POST /tasks`.
   - Returns `HandlerExecutionChain(handler=create, interceptors=[])`.
4. No interceptors → `HandlerAdapter` = `RequestMappingHandlerAdapter`.
5. `adapter.handle(request, response, handler)`:
   - Reads `Content-Type: application/json` → `MappingJackson2HttpMessageConverter.read()` → `Task(0,"Buy milk")`.
   - Injects as `@RequestBody Task t`.
   - Invokes `TaskController.create(task)` → returns `Task(1,"Buy milk")`.
6. Return value: `Task` object with `@ResponseBody` (from `@RestController`).
7. `RequestResponseBodyMethodProcessor.handleReturnValue()` → `MappingJackson2HttpMessageConverter.write()` → writes `{"id":1,"title":"Buy milk"}` to `HttpServletResponse`.
8. Response sent to client.

## 7. Gotchas & takeaways

> **`DispatcherServlet` mapped to `"/"` takes ownership of ALL requests**, including static resources. You must register `DefaultServletHttpRequestHandler` or configure `mvc:resources` / `ResourceHandlerRegistry` to serve `/static/**` files, otherwise static assets return 404.

> **`setLoadOnStartup(1)` makes `DispatcherServlet` start at container startup**, not lazily on first request. Without it, the first request pays the startup cost (context refresh, bean creation). Always set it to 1 in production.

> **Each `DispatcherServlet` has its own `WebApplicationContext`.** Beans in one context are invisible to another. Share services/repositories via a root context (`ContextLoaderListener`).

- `DispatcherServlet` = front controller; registered at `"/"` to intercept all requests.
- Strategy beans (HandlerMapping, HandlerAdapter, ViewResolver) are auto-configured via `DispatcherServlet.properties`.
- Root context (services) + servlet context (controllers) hierarchy for separation of concerns.
- `setLoadOnStartup(1)` — always set in production.
- Static resources: register `ResourceHandlerRegistry` when `DispatcherServlet` maps to `"/"`.
