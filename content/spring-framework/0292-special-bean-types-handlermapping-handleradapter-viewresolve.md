---
card: spring-framework
gi: 292
slug: special-bean-types-handlermapping-handleradapter-viewresolve
title: "Special Bean Types: HandlerMapping, HandlerAdapter, ViewResolver"
---

## 1. What it is

`DispatcherServlet` delegates all request-processing decisions to **strategy beans** discovered from its `WebApplicationContext`. These are called "special bean types" because `DispatcherServlet` looks for them by interface, not by name.

The six most important:

| Interface | Responsibility |
|---|---|
| `HandlerMapping` | Map requests to handler objects (URL → method/bean) |
| `HandlerAdapter` | Invoke the handler (converts request to method args, calls it) |
| `HandlerExceptionResolver` | Handle exceptions thrown from handlers |
| `ViewResolver` | Resolve logical view names to concrete `View` objects |
| `LocaleResolver` | Determine request locale for i18n |
| `MultipartResolver` | Parse file upload requests |

## 2. Why & when

`DispatcherServlet` itself has no knowledge of `@RequestMapping`, JSPs, or JSON. It delegates everything. This design lets you replace or extend any piece independently:
- Different `HandlerMapping` for different routing strategies (path-based, header-based).
- Custom `HandlerAdapter` to support your own controller type.
- Multiple `ViewResolver`s with `order` priority for template fallback.
- Custom `HandlerExceptionResolver` for domain-specific error handling.

`@EnableWebMvc` (or Spring Boot auto-configuration) registers the default implementations:
- `RequestMappingHandlerMapping` — scans `@RequestMapping` annotations.
- `RequestMappingHandlerAdapter` — resolves `@RequestParam`, `@RequestBody`, `@Valid`, etc.
- `ExceptionHandlerExceptionResolver` — processes `@ExceptionHandler` in `@ControllerAdvice`.
- `BeanNameViewResolver` — resolves view names to beans with matching names.

## 3. Core concept

`DispatcherServlet.doDispatch()` in condensed form:

```java
// 1. Find handler
HandlerExecutionChain chain = null;
for (HandlerMapping mapping : handlerMappings) {
    chain = mapping.getHandler(request);   // returns handler + interceptors
    if (chain != null) break;
}

// 2. Find adapter for this handler type
HandlerAdapter adapter = null;
for (HandlerAdapter ha : handlerAdapters) {
    if (ha.supports(chain.getHandler())) { adapter = ha; break; }
}

// 3. Run pre-interceptors
for (HandlerInterceptor i : chain.getInterceptors()) i.preHandle(req, res, handler);

// 4. Invoke handler
ModelAndView mv = adapter.handle(request, response, chain.getHandler());

// 5. Resolve view
if (mv != null && mv.getViewName() != null) {
    View view = null;
    for (ViewResolver vr : viewResolvers) {
        view = vr.resolveViewName(mv.getViewName(), locale);
        if (view != null) break;
    }
    view.render(mv.getModel(), request, response);
}
```

`HandlerMapping.getHandler()` returns a `HandlerExecutionChain` — the handler + interceptors. The handler itself may be a `HandlerMethod` (for `@RequestMapping`), a `Servlet`, or any object that has a matching `HandlerAdapter`.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- DispatcherServlet -->
  <rect x="10" y="75" width="150" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="85" y="97" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DispatcherServlet</text>
  <text x="85" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">doDispatch(req, res)</text>

  <line x1="162" y1="97" x2="195" y2="50" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="162" y1="97" x2="195" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="162" y1="97" x2="195" y2="145" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- HandlerMapping -->
  <rect x="197" y="25" width="170" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="282" y="46" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">HandlerMapping</text>
  <text x="282" y="61" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">RequestMappingHandlerMapping</text>

  <!-- HandlerAdapter -->
  <rect x="197" y="75" width="170" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="282" y="96" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">HandlerAdapter</text>
  <text x="282" y="111" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">RequestMappingHandlerAdapter</text>

  <!-- ViewResolver -->
  <rect x="197" y="125" width="170" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="282" y="146" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ViewResolver</text>
  <text x="282" y="161" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">ContentNegotiatingViewResolver</text>

  <line x1="369" y1="47" x2="420" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="369" y1="97" x2="420" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="369" y1="147" x2="420" y2="140" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Result -->
  <rect x="422" y="50" width="265" height="90" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="554" y="72" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Request Handled</text>
  <line x1="432" y1="78" x2="677" y2="78" stroke="#8b949e" stroke-width="0.5"/>
  <text x="554" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">HandlerMethod (your @Controller)</text>
  <text x="554" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">invoked, args resolved, return processed</text>
  <text x="554" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">view rendered or body written</text>
</svg>

## 5. Runnable example

Scenario: a **bookstore API** — inspect HandlerMapping, register a custom ViewResolver.

### Level 1 — Basic

Default strategy beans auto-configured by `@EnableWebMvc`.

```java
// SpecialBeanTypesDemo.java
import org.springframework.context.annotation.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

record Book(long id, String title, String author) {}

@RestController @RequestMapping("/books")
class BookController {
    private final Map<Long,Book> db = Map.of(
        1L, new Book(1L,"Clean Code","Martin"),
        2L, new Book(2L,"Effective Java","Bloch")
    );
    @GetMapping           public Collection<Book> list()              { return db.values(); }
    @GetMapping("/{id}")  public Book get(@PathVariable long id)       { return db.get(id); }
}

@Configuration @EnableWebMvc @ComponentScan
class WebConfig {
    // @EnableWebMvc registers:
    //   RequestMappingHandlerMapping   (ordered 0)
    //   RequestMappingHandlerAdapter   (argument resolvers, message converters)
    //   ExceptionHandlerExceptionResolver (@ControllerAdvice)
    //   HttpRequestHandlerAdapter      (for HttpRequestHandler beans)
    //   SimpleControllerHandlerAdapter (for Controller-interface beans)
}

public class SpecialBeanTypesDemo {
    public static void main(String[] args) throws Exception {
        // Simulate context to list strategy beans
        var ctx = new org.springframework.web.context.support.AnnotationConfigWebApplicationContext();
        ctx.register(WebConfig.class);
        ctx.refresh();

        System.out.println("HandlerMappings: ");
        ctx.getBeansOfType(HandlerMapping.class).forEach((k,v) ->
            System.out.println("  " + k + " = " + v.getClass().getSimpleName()));

        System.out.println("HandlerAdapters: ");
        ctx.getBeansOfType(HandlerAdapter.class).forEach((k,v) ->
            System.out.println("  " + k + " = " + v.getClass().getSimpleName()));

        System.out.println("ViewResolvers: ");
        ctx.getBeansOfType(ViewResolver.class).forEach((k,v) ->
            System.out.println("  " + k + " = " + v.getClass().getSimpleName()));

        ctx.close();
    }
}
```

How to run: `java -cp spring-webmvc.jar:spring-context.jar:spring-web.jar:jackson-databind.jar:jakarta.servlet-api.jar:. SpecialBeanTypesDemo.java`

`@EnableWebMvc` registers all standard strategy beans. `ctx.getBeansOfType(HandlerMapping.class)` reveals `RequestMappingHandlerMapping` (primary) and `BeanNameUrlHandlerMapping` (fallback). Multiple `HandlerMapping` beans coexist — `DispatcherServlet` iterates them in `order` value.

---

### Level 2 — Intermediate

Custom `ViewResolver` with `order` + `HandlerExceptionResolver`.

```java
// SpecialBeanTypesDemo.java
import jakarta.servlet.http.*;
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.Order;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.servlet.view.*;
import java.util.*;

// Custom view — returns plain text "view" for any logical view name starting with "text:"
class PlainTextView implements View {
    private final String content;
    PlainTextView(String c){ content=c; }
    @Override public String getContentType(){ return "text/plain"; }
    @Override public void render(Map<String,?> model, HttpServletRequest req, HttpServletResponse res) throws Exception {
        res.setContentType("text/plain"); res.getWriter().write(content + " | model=" + model);
    }
}

// Custom resolver: handles "text:..." view names
class PlainTextViewResolver implements ViewResolver {
    @Override public View resolveViewName(String viewName, Locale locale) {
        if (viewName != null && viewName.startsWith("text:"))
            return new PlainTextView(viewName.substring(5));
        return null;  // null = not handled, try next resolver
    }
}

// Custom exception resolver: maps RuntimeException → 500 with message
class DomainExceptionResolver implements HandlerExceptionResolver {
    @Override
    public ModelAndView resolveException(HttpServletRequest req, HttpServletResponse res,
                                         Object handler, Exception ex) {
        if (ex instanceof IllegalArgumentException) {
            res.setStatus(400);
            try { res.getWriter().write("Bad request: " + ex.getMessage()); } catch (Exception ignored){}
            return new ModelAndView();  // handled — empty MAV signals complete
        }
        return null;  // not handled — delegate to next resolver
    }
}

@Controller @RequestMapping("/view-demo")
class ViewDemoController {
    @GetMapping("/text")
    public ModelAndView textView() {
        ModelAndView mav = new ModelAndView("text:Hello from custom resolver");
        mav.addObject("key","value");
        return mav;  // view name "text:Hello..." → PlainTextViewResolver
    }
    @GetMapping("/error")
    public void error(@RequestParam String msg) {
        throw new IllegalArgumentException(msg);  // → DomainExceptionResolver
    }
}

@Configuration @EnableWebMvc @ComponentScan
class WebConfig2 implements WebMvcConfigurer {
    @Bean @Order(1) PlainTextViewResolver plainTextViewResolver(){ return new PlainTextViewResolver(); }
    @Bean DomainExceptionResolver domainExceptionResolver(){ return new DomainExceptionResolver(); }
}

public class SpecialBeanTypesDemo {
    public static void main(String[] args) {
        System.out.println("DispatcherServlet discovers strategy beans from ApplicationContext:");
        System.out.println("  PlainTextViewResolver  → @Bean @Order(1) resolves 'text:...' view names");
        System.out.println("  DomainExceptionResolver → @Bean resolves IllegalArgumentException → 400");
    }
}
```

How to run: same classpath + deploy

`ViewResolver` beans are discovered and ordered by `Ordered`/`@Order`. `PlainTextViewResolver` at order 1 is tried first; returning `null` defers to the next resolver. `HandlerExceptionResolver` beans are similarly ordered — return `null` to pass to the next, return `new ModelAndView()` (empty but non-null) to signal handled.

---

### Level 3 — Advanced

`ContentNegotiatingViewResolver` + `RequestMappingHandlerMapping` introspection.

```java
// SpecialBeanTypesDemo.java
import org.springframework.context.annotation.*;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.method.*;
import org.springframework.web.servlet.*;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.servlet.mvc.method.RequestMappingInfo;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;
import java.util.*;

// (Book and BookController same as Level 1)

@Configuration @EnableWebMvc @ComponentScan
class WebConfig3 implements WebMvcConfigurer {
    @Bean
    ContentNegotiatingViewResolver viewResolver(List<ViewResolver> resolvers) {
        var cv = new ContentNegotiatingViewResolver();
        // When client sends Accept: application/json  → MappingJackson2JsonView
        // When client sends Accept: application/xml   → custom xml view (fallback)
        cv.setDefaultViews(List.of(new org.springframework.web.servlet.view.json.MappingJackson2JsonView()));
        return cv;
    }
}

public class SpecialBeanTypesDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.web.context.support.AnnotationConfigWebApplicationContext();
        ctx.register(WebConfig3.class);
        ctx.refresh();

        // Inspect registered @RequestMapping methods
        RequestMappingHandlerMapping mapping = ctx.getBean(RequestMappingHandlerMapping.class);
        Map<RequestMappingInfo, HandlerMethod> methods = mapping.getHandlerMethods();
        System.out.println("Registered @RequestMapping methods:");
        methods.forEach((info, method) ->
            System.out.println("  " + info + " → " + method));

        ctx.close();
    }
}
```

How to run: same classpath

`RequestMappingHandlerMapping.getHandlerMethods()` returns a map of all `@RequestMapping` methods registered in the context. This is used by Spring Boot Actuator's `/mappings` endpoint. `ContentNegotiatingViewResolver` selects the view based on the `Accept` header — `Accept: application/json` → `MappingJackson2JsonView`.

## 6. Walkthrough

**Level 2 — `GET /view-demo/text` (custom resolver flow):**

1. `DispatcherServlet` → `RequestMappingHandlerMapping` → finds `ViewDemoController.textView()`.
2. `RequestMappingHandlerAdapter` invokes `textView()` → returns `ModelAndView("text:Hello...", {key:value})`.
3. Resolve view name `"text:Hello..."`:
   - Try `PlainTextViewResolver` (order 1): `viewName.startsWith("text:")` → true → returns `PlainTextView("Hello from custom resolver")`.
   - (Would try next resolvers if null returned.)
4. `PlainTextView.render(model, req, res)` → writes `Hello from custom resolver | model={key=value}` as `text/plain`.

**`GET /view-demo/error?msg=bad` (exception resolver flow):**

1. Handler throws `IllegalArgumentException("bad")`.
2. `DispatcherServlet` catches it → iterates `HandlerExceptionResolver` beans:
   - `DomainExceptionResolver.resolveException(...)` → `IllegalArgumentException` matches → sets 400, writes body, returns empty `ModelAndView`.
   - Non-null return → exception handled, stop iterating.
3. Response committed with `400 Bad request: bad`.

## 7. Gotchas & takeaways

> **Multiple `HandlerMapping` beans are ordered by `Ordered` / `@Order`.** `RequestMappingHandlerMapping` has order `0` by default. `BeanNameUrlHandlerMapping` has order `2`. Lower order = higher priority. If you add a custom `HandlerMapping`, set its `order` to control priority.

> **A `ViewResolver` returning `null` passes to the next resolver.** Returning a `View` (even one that produces an error response) signals that this resolver owns the request. Never return `null` for "no suitable view" from a `ViewResolver` that should be authoritative.

> **`@EnableWebMvc` replaces ALL defaults.** When you annotate `@Configuration` with `@EnableWebMvc`, it resets the strategy beans to Spring MVC defaults and applies your `WebMvcConfigurer` customisations. If you partially configure, missing converters or resolvers may not be registered. Use `WebMvcConfigurer` methods to ADD to defaults rather than replace.

- `HandlerMapping` → URL-to-handler; `HandlerAdapter` → handler invocation; `ViewResolver` → view lookup.
- Strategy beans discovered by `DispatcherServlet` from `WebApplicationContext` by type.
- Return `null` from `ViewResolver`/`HandlerExceptionResolver` to defer to the next one.
- `@EnableWebMvc` registers all defaults; customize via `WebMvcConfigurer` (additive, not replacing).
- `RequestMappingHandlerMapping.getHandlerMethods()` lists all registered endpoints.
