---
card: spring-framework
gi: 299
slug: view-resolution-flow
title: "View resolution flow"
---

## 1. What it is

**View resolution** is the step where Spring MVC converts a logical view name (a `String` like `"users/list"`) returned by a controller into a `View` object that knows how to render an HTTP response.  `DispatcherServlet` delegates this to a chain of `ViewResolver` implementations; the first one that returns a non-null `View` wins.

Common implementations:

| Resolver | Resolves to |
|---|---|
| `InternalResourceViewResolver` | JSP / servlet resources via `prefix` + name + `suffix` |
| `ThymeleafViewResolver` | Thymeleaf templates |
| `FreeMarkerViewResolver` | FreeMarker templates |
| `ContentNegotiatingViewResolver` | delegates to other resolvers based on `Accept` header |
| `BeanNameViewResolver` | looks up a `View` bean by name in the application context |

---

## 2. Why & when

The controller returns a **logical** view name rather than a physical path.  This separation lets you:

- Swap template engines (JSP → Thymeleaf) without changing controller code.
- Configure path/suffix conventions centrally.
- Support content negotiation (HTML vs JSON vs XML) from one handler.

View resolution only applies when the handler returns a `ModelAndView` or a `String` view name.  When `@ResponseBody` / `@RestController` is used, the response is written directly by `HttpMessageConverter` — **view resolution is skipped entirely**.

---

## 3. Core concept

```
Controller returns "users/list"
  ↓
DispatcherServlet.render(ModelAndView)
  ↓
for each ViewResolver (in order):
  vr.resolveViewName("users/list", locale)
    → null  : try next resolver
    → View  : stop, call View.render(model, req, res)
  ↓
View.render() writes bytes to HttpServletResponse
```

`InternalResourceViewResolver` transforms the logical name:
```
prefix="/WEB-INF/views/"  + "users/list" + suffix=".jsp"
  → /WEB-INF/views/users/list.jsp
```
The resolved path is forwarded to the servlet container's `RequestDispatcher`.

---

## 4. Diagram

<svg viewBox="0 0 760 320" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="760" height="320" fill="#0d1117"/>

  <!-- Controller box -->
  <rect x="10" y="130" width="130" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="150" text-anchor="middle" fill="#79c0ff">Controller</text>
  <text x="75" y="168" text-anchor="middle" fill="#8b949e" font-size="10">returns "users/list"</text>

  <!-- arrow -->
  <line x1="140" y1="155" x2="185" y2="155" stroke="#8b949e" marker-end="url(#av)"/>

  <!-- DispatcherServlet -->
  <rect x="185" y="130" width="140" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="255" y="150" text-anchor="middle" fill="#79c0ff">DispatcherServlet</text>
  <text x="255" y="168" text-anchor="middle" fill="#8b949e" font-size="10">render(ModelAndView)</text>

  <!-- arrow to resolver chain -->
  <line x1="325" y1="155" x2="370" y2="155" stroke="#8b949e" marker-end="url(#av)"/>

  <!-- Resolver chain block -->
  <rect x="370" y="80" width="200" height="150" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="470" y="100" text-anchor="middle" fill="#6db33f" font-weight="bold">ViewResolver chain</text>
  <rect x="380" y="108" width="180" height="24" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="470" y="124" text-anchor="middle" fill="#6db33f" font-size="11">ContentNegotiatingViewResolver</text>
  <rect x="380" y="138" width="180" height="24" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="470" y="154" text-anchor="middle" fill="#6db33f" font-size="11">ThymeleafViewResolver</text>
  <rect x="380" y="168" width="180" height="24" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="470" y="184" text-anchor="middle" fill="#6db33f" font-size="11">BeanNameViewResolver</text>

  <!-- arrow to View -->
  <line x1="570" y1="155" x2="615" y2="155" stroke="#6db33f" marker-end="url(#av)"/>
  <text x="592" y="148" text-anchor="middle" fill="#6db33f" font-size="10">View</text>

  <!-- View box -->
  <rect x="615" y="130" width="130" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="680" y="150" text-anchor="middle" fill="#e6edf3">View.render()</text>
  <text x="680" y="168" text-anchor="middle" fill="#8b949e" font-size="10">writes response bytes</text>

  <!-- Model arrow down to View -->
  <line x1="255" y1="180" x2="255" y2="230" stroke="#8b949e" stroke-dasharray="4,2"/>
  <line x1="255" y1="230" x2="680" y2="230" stroke="#8b949e" stroke-dasharray="4,2"/>
  <line x1="680" y1="230" x2="680" y2="182" stroke="#8b949e" stroke-dasharray="4,2" marker-end="url(#av)"/>
  <text x="467" y="248" text-anchor="middle" fill="#8b949e" font-size="10">model (Map&lt;String,Object&gt;) passed to View.render()</text>

  <!-- caption -->
  <text x="380" y="290" text-anchor="middle" fill="#8b949e" font-size="11">First resolver returning a non-null View wins; View merges model + template → HTTP body</text>

  <defs>
    <marker id="av" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The resolver chain picks the right `View`; that view merges the model map with a template to produce the HTTP body.*

---

## 5. Runnable example

### Level 1 — Basic

A Thymeleaf controller that returns a logical view name, with `ThymeleafViewResolver` auto-configured by Spring Boot:

```java
// UserController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("/users")
public class UserController {

    @GetMapping("/{id}")
    public String getUser(@PathVariable long id, Model model) {
        model.addAttribute("userId", id);
        model.addAttribute("userName", "Alice");
        return "users/detail"; // logical view name
    }
}
```

```html
<!-- src/main/resources/templates/users/detail.html -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <h1 th:text="'User #' + ${userId}">User</h1>
  <p  th:text="${userName}">Name</p>
</body>
</html>
```

```properties
# application.properties (defaults, shown for clarity)
spring.thymeleaf.prefix=classpath:/templates/
spring.thymeleaf.suffix=.html
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/users/1
# <!DOCTYPE html><html><body><h1>User #1</h1><p>Alice</p></body></html>
```

`ThymeleafViewResolver.resolveViewName("users/detail", locale)` appends prefix + suffix, loads the template from the classpath, and returns a `ThymeleafView`.  `DispatcherServlet` calls `view.render(model, req, res)`, which merges `{userId=1, userName="Alice"}` into the HTML template and writes the result to the response output stream.

---

### Level 2 — Intermediate

Same scenario — view resolution — but now demonstrating **content negotiation**: the same controller returns HTML to browsers and JSON to API clients depending on the `Accept` header, using `ContentNegotiatingViewResolver`:

```java
// UserController.java (unchanged — same return type)
@Controller
@RequestMapping("/users")
public class UserController {

    @GetMapping("/{id}")
    public String getUser(@PathVariable long id, Model model) {
        model.addAttribute("userId", id);
        model.addAttribute("userName", "Alice");
        return "users/detail";
    }
}
```

```java
// MvcConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.servlet.view.*;
import org.springframework.web.servlet.view.json.MappingJackson2JsonView;

@Configuration
public class MvcConfig implements WebMvcConfigurer {

    @Bean
    public ContentNegotiatingViewResolver contentNegotiatingViewResolver(
            ThymeleafViewResolver thymeleaf) {
        ContentNegotiatingViewResolver cnvr = new ContentNegotiatingViewResolver();
        // Default views used when no specific resolver matches the Accept header
        cnvr.setDefaultViews(List.of(new MappingJackson2JsonView()));
        return cnvr;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Browser / HTML client:
curl -H "Accept: text/html" http://localhost:8080/users/1
# → HTML page

# API client:
curl -H "Accept: application/json" http://localhost:8080/users/1
# → {"userId":1,"userName":"Alice"}
```

**What changed:** `ContentNegotiatingViewResolver` sits at the front of the chain.  For `Accept: application/json` it selects `MappingJackson2JsonView`, which serialises the model `Map` directly to JSON — no template file needed.  For `Accept: text/html` it delegates to the next resolver (`ThymeleafViewResolver`).  The controller code is unchanged.

---

### Level 3 — Advanced

Production scenario: a custom `ViewResolver` that selects between a **cached** compiled view and a **dev-mode live-reload** view based on an environment flag, and logs resolution time:

```java
// TimedViewResolver.java
import org.springframework.core.Ordered;
import org.springframework.web.servlet.*;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class TimedViewResolver implements ViewResolver, Ordered {

    private final ViewResolver delegate;
    private final Map<String, View> cache = new ConcurrentHashMap<>();
    private final boolean cacheEnabled;

    public TimedViewResolver(ViewResolver delegate, boolean cacheEnabled) {
        this.delegate = delegate;
        this.cacheEnabled = cacheEnabled;
    }

    @Override
    public int getOrder() { return Ordered.LOWEST_PRECEDENCE - 1; } // just before default

    @Override
    public View resolveViewName(String viewName, Locale locale) throws Exception {
        if (cacheEnabled) {
            return cache.computeIfAbsent(viewName + "_" + locale, k -> {
                try { return delegate.resolveViewName(viewName, locale); }
                catch (Exception e) { throw new RuntimeException(e); }
            });
        }
        long start = System.nanoTime();
        View view = delegate.resolveViewName(viewName, locale);
        long ms = (System.nanoTime() - start) / 1_000_000;
        if (view != null) System.out.printf("[ViewResolver] '%s' resolved in %dms%n", viewName, ms);
        return view;
    }
}
```

```java
// MvcConfig.java (production config)
@Configuration
public class MvcConfig {

    @Value("${spring.thymeleaf.cache:true}")
    private boolean cacheEnabled;

    @Bean
    public TimedViewResolver timedViewResolver(ThymeleafViewResolver thymeleaf) {
        return new TimedViewResolver(thymeleaf, cacheEnabled);
    }
}
```

```properties
# application-dev.properties
spring.thymeleaf.cache=false
# TimedViewResolver will log resolution time and skip cache in dev mode
```

**How to run:**
```bash
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev
curl http://localhost:8080/users/1
# [ViewResolver] 'users/detail' resolved in 8ms
# → HTML page
```

**What changed and why:**

- In production (`cache=true`) `computeIfAbsent` prevents repeated template parsing — the `View` object is created once per view name and reused across millions of requests.
- In dev (`cache=false`) every request parses the template file fresh — hot-reload works without restart.
- Logging resolution time in dev mode surfaces slow templates before they reach production.
- `getOrder()` places this resolver just before the lowest-priority default, so content negotiation and bean-name resolvers still take priority.

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="200" fill="#0d1117"/>
  <!-- dev vs prod -->
  <rect x="20" y="30" width="300" height="130" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="170" y="52" text-anchor="middle" fill="#8b949e">dev (cache=false)</text>
  <rect x="40" y="62" width="260" height="30" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="170" y="81" text-anchor="middle" fill="#6db33f">resolveViewName() called every req</text>
  <rect x="40" y="100" width="260" height="30" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="170" y="119" text-anchor="middle" fill="#8b949e">template parsed fresh → live reload</text>
  <text x="170" y="147" text-anchor="middle" fill="#8b949e" font-size="10">logs: 'users/detail' resolved in 8ms</text>

  <rect x="370" y="30" width="300" height="130" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="52" text-anchor="middle" fill="#6db33f">prod (cache=true)</text>
  <rect x="390" y="62" width="260" height="30" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="520" y="81" text-anchor="middle" fill="#6db33f">computeIfAbsent → View from cache</text>
  <rect x="390" y="100" width="260" height="30" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="520" y="119" text-anchor="middle" fill="#8b949e">View object reused for all requests</text>
  <text x="520" y="147" text-anchor="middle" fill="#8b949e" font-size="10">no disk I/O after first resolution</text>

  <text x="350" y="185" text-anchor="middle" fill="#8b949e" font-size="10">Same resolver code, different cacheEnabled flag from spring.thymeleaf.cache property</text>
</svg>

---

## 6. Walkthrough

**Startup:**

1. Spring Boot auto-configures `ThymeleafViewResolver` (or `InternalResourceViewResolver` for JSPs) and `ContentNegotiatingViewResolver` if Jackson is on the classpath.
2. `DispatcherServlet` collects all `ViewResolver` beans, sorts them by `Ordered.getOrder()`, and stores the sorted list.
3. `ThymeleafViewResolver` scans `classpath:/templates/` at startup (cache=true) or defers template loading to first access (cache=false).

**Per-request view resolution (HTML path):**

4. `GET /users/1` arrives with `Accept: text/html`.
5. `UserController.getUser(1, model)` adds `{userId=1, userName="Alice"}` to the model, returns `"users/detail"`.
6. `DispatcherServlet.render()` calls `resolveViewName("users/detail", locale)` on each resolver in order.
7. **ContentNegotiatingViewResolver** — inspects `Accept: text/html`, finds `ThymeleafViewResolver` can serve HTML, delegates to it. Gets back a `ThymeleafView`. Returns it.
8. Chain stops. `DispatcherServlet` calls `view.render({userId=1, userName="Alice"}, req, res)`.
9. `ThymeleafView` opens `classpath:/templates/users/detail.html`, processes Thymeleaf expressions — `${userId}` → `1`, `${userName}` → `Alice` — and writes the result to `HttpServletResponse.getOutputStream()`.

**Per-request view resolution (JSON path):**

6b. `ContentNegotiatingViewResolver` sees `Accept: application/json`, selects `MappingJackson2JsonView`.
9b. `MappingJackson2JsonView.render()` serialises the model map `{userId=1, userName="Alice"}` to `{"userId":1,"userName":"Alice"}` and writes it.

**State transformation:**

| Stage | Data |
|---|---|
| Controller returns | `"users/detail"` (String) + Model `{userId=1, userName=Alice}` |
| ViewResolver lookup | `"users/detail"` → `ThymeleafView` |
| View.render() input | Model map merged into template |
| Response output | `<h1>User #1</h1><p>Alice</p>` |

---

## 7. Gotchas & takeaways

> **`@ResponseBody` / `@RestController` bypasses view resolution entirely.**  The `HandlerAdapter` writes the response directly via `HttpMessageConverter`, so `DispatcherServlet` never calls `resolveViewName`.  If a `@RestController` method returns a `String`, that string is written as plain text — not treated as a view name.

> **`InternalResourceViewResolver` should be the last resolver in the chain.**  It always returns a non-null `View` (it forward-resolves paths even when the JSP doesn't exist), so any resolver registered after it will never be reached.

> **View caching (`spring.thymeleaf.cache=true`) is the default.**  Never disable it in production — template parsing is expensive.  Use `spring.thymeleaf.cache=false` only in development (via a profile).

- View resolution is chain-based: first non-null `View` wins.
- `ContentNegotiatingViewResolver` is transparent to controllers — same return value, different rendered output based on `Accept` header.
- `Model` is a `Map<String, Object>`; every key becomes a template variable or JSON property.
- Custom `ViewResolver` implementing `Ordered` controls where in the chain it sits.
- `ThymeleafViewResolver` (or any caching resolver) caches the resolved `View` object — template disk I/O happens once per view name.
